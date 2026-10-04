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
  everything else in it is the owner's and is ignored;
- the cursor-agent shim at %LOCALAPPDATA%/cursor-agent/cursor-agent must equal
  cursor-bridge/cursor-agent.shim (Windows only).

Usage:  python ~/.claude/cursor-bridge/bridge-check.py [--root <path-to-.claude>] [--quiet]
Exit:   0 = every manifest file OK; 1 = at least one STALE or MISSING;
        2 = manifest unreadable.  ASCII-only on purpose (cp1252 consoles).
"""
import hashlib
import json
import os
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
    if missing:
        return "STALE", "missing bridge entries: " + "; ".join(missing)
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
    verdict, detail = check_settings(root)
    if verdict == "OK":
        ok += 1
    elif verdict == "MISSING":
        missing += 1; problems.append(("MISSING", "settings.json"))
    else:
        stale += 1; problems.append(("STALE", "settings.json (%s)" % detail))
    if detail and verdict == "OK" and not quiet:
        print("  note     settings.json: %s" % detail)
    # the cursor-agent shim (Windows): must equal the release's copy
    verdict, detail = check_shim()
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
    if extras and not quiet:
        for rel in sorted(extras):
            print("  EXTRA    %s  (not in manifest; a local addition or a leftover)" % rel)
    print("bridge-check: %d OK, %d STALE, %d MISSING, %d EXTRA" % (ok, stale, missing, len(extras)))
    if stale or missing:
        print("RESULT: NOT CALIBRATED - run the release's bridge-install.py (it copies the files, merges settings.json and installs the shim), then re-run.")
        return 1
    print("RESULT: INSTALLED TREE MATCHES bridge %s" % manifest.get("version", "?"))
    return 0


if __name__ == "__main__":
    for _s in (sys.stdout, sys.stderr):      # never crash on a character the console lacks
        if hasattr(_s, "reconfigure"):
            _s.reconfigure(errors="backslashreplace")
    sys.exit(main())
