#!/usr/bin/env python3
"""bridge-check: verify that the installed bridge tree matches its manifest.

The maintainer ships MANIFEST.json (file -> sha256, plus the version) with every
bridge release. This script hashes the live tree it is installed in and reports,
per file: OK, STALE (content differs), MISSING (not installed), and any EXTRA
governance files not in the manifest (informational). Line endings are normalized
before hashing, so a CRLF copy of an LF file is still OK.

Two files are not fingerprinted but compared by content (KP-030, KP-032):
- settings.json is shared with Claude Code and the owner, so only the bridge-owned entries
  (cursor-bridge/settings.bridge.json: allow and deny rules, hooks) must be present;
  everything else in it is the owner's and is ignored, except a hook that runs a
  cursor-bridge program which is not installed: that is reported, because it blocks;
- the cursor-agent shim at %LOCALAPPDATA%/cursor-agent/cursor-agent must equal
  cursor-bridge/cursor-agent.shim (Windows only).

Usage:  python ~/.claude/cursor-bridge/bridge-check.py [--root <path-to-.claude>] [--quiet]
        python bridge/cursor-bridge/bridge-check.py --root bridge --sources [--quiet]

--sources checks a source tree (the `bridge/` folder of the bridge's repository) against its
own manifest and nothing more: a source tree has no settings.json, since the owner's file is
not part of it, and the shim is a matter of the machine a release is installed on. In a
source tree a file the manifest does not list (EXTRA) fails the check as well.
Exit:   0 = every manifest file OK; 1 = at least one STALE or MISSING;
        2 = manifest unreadable.  ASCII-only on purpose (cp1252 consoles).
"""
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def norm_hash(path):
    with open(path, "rb") as f:
        data = f.read()
    data = data.replace(b"\r\n", b"\n")
    if data.startswith(b"\xef\xbb\xbf"):
        data = data[3:]
    return hashlib.sha256(data).hexdigest()


def hook_commands(groups):
    out = []
    for g in groups or []:
        for h in (g.get("hooks") or []):
            if h.get("command"):
                out.append(h["command"])
    return out


def check_settings(root):
    """Return (verdict, detail) for settings.json against settings.bridge.json."""
    want_path = os.path.join(HERE, "settings.bridge.json")
    have_path = os.path.join(root, "settings.json")
    try:
        with open(want_path, encoding="utf-8-sig") as f:
            want = json.load(f)
    except Exception as e:
        return "STALE", "cannot read settings.bridge.json (%s)" % e
    if not os.path.isfile(have_path):
        return "MISSING", ""
    try:
        with open(have_path, encoding="utf-8-sig") as f:
            have = json.load(f)
    except Exception as e:
        return "STALE", "not valid JSON (%s)" % e
    missing = []
    perms = have.get("permissions") or {}
    for key in ("allow", "deny"):
        got = perms.get(key) or []
        for entry in (want.get("permissions") or {}).get(key) or []:
            if entry not in got:
                missing.append("%s: %s" % (key, entry))
    have_hooks = have.get("hooks") or {}
    for event, groups in (want.get("hooks") or {}).items():
        present = hook_commands(have_hooks.get(event))
        for cmd in hook_commands(groups):
            if cmd not in present:
                missing.append("hook %s: %s" % (event, cmd))
    # A hook that runs a bridge program which is not installed fails with exit status 2,
    # which Claude Code reads as "block": every matching tool call, or the end of every turn.
    orphans = []
    for event, groups in sorted(have_hooks.items()):
        for cmd in hook_commands(groups):
            for name in re.findall(r"cursor-bridge[/\\]([\w.-]+\.py)", cmd):
                if not os.path.isfile(os.path.join(root, "cursor-bridge", name)):
                    orphans.append("%s runs %s" % (event, name))
    if missing or orphans:
        return "STALE", "; ".join((["missing bridge entries: " + "; ".join(missing)] if missing else [])
                                  + (["hooks that run a bridge program which is not installed (remove the hook or install the bridge again): " + "; ".join(orphans)] if orphans else []))
    owner_keys = sorted(k for k in have if k not in ("permissions", "hooks"))
    return "OK", ("owner keys kept: " + ", ".join(owner_keys)) if owner_keys else ""


def check_shim():
    """Return (verdict, detail) for the installed cursor-agent shim (Windows only)."""
    if sys.platform != "win32":
        return "SKIP", "not Windows"
    src = os.path.join(HERE, "cursor-agent.shim")
    if not os.path.isfile(src):
        return "SKIP", "no shim in this release"
    folder = os.path.join(os.environ.get("LOCALAPPDATA", ""), "cursor-agent")
    if not os.path.isdir(folder):
        return "SKIP", "the Cursor CLI is not installed here (%s)" % folder
    dst = os.path.join(folder, "cursor-agent")
    if not os.path.isfile(dst):
        return "MISSING", dst
    if norm_hash(src) != norm_hash(dst):
        return "STALE", dst + " differs from cursor-bridge/cursor-agent.shim"
    return "OK", dst


def main():
    argv = sys.argv[1:]
    root = os.path.abspath(os.path.join(HERE, os.pardir))
    quiet = "--quiet" in argv
    sources = "--sources" in argv
    if "--root" in argv:
        root = os.path.abspath(argv[argv.index("--root") + 1])
    manifest_path = os.path.join(HERE, "MANIFEST.json")
    try:
        with open(manifest_path, encoding="utf-8") as f:
            manifest = json.load(f)
    except Exception as e:
        print("bridge-check: cannot read %s (%s)" % (manifest_path, e))
        return 2

    files = manifest.get("files", {})
    ok = stale = missing = 0
    problems = []
    for rel, expected in sorted(files.items()):
        if rel == "settings.json":
            continue                                   # compared by entries below, never by hash
        p = os.path.join(root, *rel.split("/"))
        if not os.path.isfile(p):
            missing += 1
            problems.append(("MISSING", rel))
            continue
        if norm_hash(p) != expected:
            stale += 1
            problems.append(("STALE", rel))
        else:
            ok += 1

    # settings.json: the bridge-owned entries must be present; the rest is the owner's
    verdict, detail = ("SKIP", "") if sources else check_settings(root)
    if verdict == "SKIP":
        pass
    elif verdict == "OK":
        ok += 1
    elif verdict == "MISSING":
        missing += 1; problems.append(("MISSING", "settings.json"))
    else:
        stale += 1; problems.append(("STALE", "settings.json (%s)" % detail))
    if detail and verdict == "OK" and not quiet:
        print("  note     settings.json: %s" % detail)
    # the cursor-agent shim (Windows): must equal the release's copy
    verdict, detail = ("SKIP", "") if sources else check_shim()
    if verdict == "OK":
        ok += 1
    elif verdict == "MISSING":
        missing += 1; problems.append(("MISSING", "cursor-agent shim (%s)" % detail))
    elif verdict == "STALE":
        stale += 1; problems.append(("STALE", "cursor-agent shim (%s)" % detail))

    extras = []
    for sub in ("commands", "agents", "skills", "cursor-bridge"):
        base = os.path.join(root, sub)
        for dirpath, dirs, names in os.walk(base):
            for n in names:
                rel = os.path.relpath(os.path.join(dirpath, n), root).replace("\\", "/")
                if rel not in files and not rel.endswith("MANIFEST.json") and "__pycache__" not in rel:
                    extras.append(rel)

    print("bridge-check: version %s (%s) at %s" % (
        manifest.get("version", "?"), manifest.get("generated", "?"), root))
    for kind, rel in problems:
        print("  %-8s %s" % (kind, rel))
    if extras and (sources or not quiet):
        for rel in sorted(extras):
            print("  EXTRA    %s  (not in manifest; %s)" % (rel, "stamp the release again, or remove the file" if sources else "a local addition or a leftover"))
    print("bridge-check: %d OK, %d STALE, %d MISSING, %d EXTRA" % (ok, stale, missing, len(extras)))
    if sources and (stale or missing or extras):
        # An unlisted file in a release folder would be installed, never kept as part of a
        # previous release and never removed by a later one.
        print("RESULT: SOURCES DO NOT MATCH their stamp - run tools/make-manifest.py after the last edit, then re-run.")
        return 1
    if stale or missing:
        print("RESULT: NOT CALIBRATED - run the release's bridge-install.py (it copies the files, merges settings.json and installs the shim), then re-run.")
        return 1
    print("RESULT: %s bridge %s" % ("SOURCES MATCH" if sources else "INSTALLED TREE MATCHES", manifest.get("version", "?")))
    return 0


if __name__ == "__main__":
    for _s in (sys.stdout, sys.stderr):      # never crash on a character the console lacks
        if hasattr(_s, "reconfigure"):
            _s.reconfigure(errors="backslashreplace")
    sys.exit(main())
