#!/usr/bin/env python3
"""bridge-install: install or update the bridge into ~/.claude from a release folder.

  python <release>/.claude/cursor-bridge/bridge-install.py [--target <path-to-.claude>] [--dry-run]

The release folder is the one this file lives in (its parent's parent is the `.claude`
tree of the release). The program:

  1. copies commands/, agents/, skills/ and cursor-bridge/ into the target, file by file,
     overwriting the bridge's files and leaving every other file alone;
  2. MERGES the bridge-owned settings (cursor-bridge/settings.bridge.json) into the target's
     settings.json: every allow and deny entry and every hook the bridge needs is added if
     missing, and every key the owner or Claude Code wrote there is kept untouched (KP-030).
     The previous settings.json is saved beside it as settings.json.bak-<date> first;
  3. installs the cursor-agent shim (cursor-bridge/cursor-agent.shim) at
     %LOCALAPPDATA%/cursor-agent/cursor-agent, the file Claude Code's Bash tool runs for
     `cursor-agent` on Windows (KP-032), when that folder exists;
  4. runs bridge-check.py on the result and prints its verdict.

Exit 0 = installed and verified; 1 = verification failed; 2 = could not install.
ASCII-only on purpose (cp1252 consoles).
"""
import datetime
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RELEASE = os.path.abspath(os.path.join(HERE, os.pardir))
SUBDIRS = ("commands", "agents", "skills", "cursor-bridge")
NO_WINDOW = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0


def load_json(path):
    with open(path, encoding="utf-8-sig") as f:
        return json.load(f)


def hook_commands(groups):
    out = []
    for g in groups or []:
        for h in (g.get("hooks") or []):
            if h.get("command"):
                out.append(h["command"])
    return out


def merge_settings(target_settings, bridge_settings):
    """Return (merged, changes): the owner's settings with the bridge's entries added."""
    merged = json.loads(json.dumps(target_settings))  # deep copy
    changes = []
    perms = merged.setdefault("permissions", {})
    for key in ("allow", "deny"):
        want = (bridge_settings.get("permissions") or {}).get(key) or []
        have = perms.setdefault(key, [])
        for entry in want:
            if entry not in have:
                have.append(entry)
                changes.append("permissions.%s += %s" % (key, entry))
    hooks = merged.setdefault("hooks", {})
    for event, groups in (bridge_settings.get("hooks") or {}).items():
        existing = hooks.setdefault(event, [])
        present = set(hook_commands(existing))
        for g in groups:
            cmds = hook_commands([g])
            if any(c not in present for c in cmds):
                existing.append(g)
                present.update(cmds)
                changes.append("hooks.%s += %s" % (event, ", ".join(cmds)))
    return merged, changes


def copy_tree(src, dst, dry):
    copied = 0
    for dirpath, dirs, names in os.walk(src):
        if "__pycache__" in dirpath:
            continue
        rel = os.path.relpath(dirpath, src)
        out_dir = dst if rel == "." else os.path.join(dst, rel)
        if not dry:
            os.makedirs(out_dir, exist_ok=True)
        for n in names:
            if n.endswith(".pyc"):
                continue
            s = os.path.join(dirpath, n)
            d = os.path.join(out_dir, n)
            if not dry:
                shutil.copyfile(s, d)
            copied += 1
    return copied


def install_shim(dry):
    src = os.path.join(HERE, "cursor-agent.shim")
    if sys.platform != "win32" or not os.path.isfile(src):
        return "shim: skipped (not Windows or no shim in the release)"
    folder = os.path.join(os.environ.get("LOCALAPPDATA", ""), "cursor-agent")
    if not os.path.isdir(folder):
        return "shim: NOT installed - %s does not exist (is the Cursor CLI installed?)" % folder
    dst = os.path.join(folder, "cursor-agent")
    data = open(src, "rb").read().replace(b"\r\n", b"\n")
    if not dry:
        with open(dst, "wb") as f:
            f.write(data)
        try:
            os.chmod(dst, 0o755)
        except OSError:
            pass
    return "shim: installed at %s" % dst


def main():
    argv = sys.argv[1:]
    dry = "--dry-run" in argv
    target = os.path.join(os.path.expanduser("~"), ".claude")
    if "--target" in argv:
        target = os.path.abspath(argv[argv.index("--target") + 1])
    if os.path.abspath(target) == RELEASE:
        print("bridge-install: the release folder is the target; nothing to do")
        return 2
    for sub in SUBDIRS:
        if not os.path.isdir(os.path.join(RELEASE, sub)):
            print("bridge-install: %s has no %s/ folder; is this a bridge release?" % (RELEASE, sub))
            return 2
    bridge_settings_path = os.path.join(HERE, "settings.bridge.json")
    try:
        bridge_settings = load_json(bridge_settings_path)
    except Exception as e:
        print("bridge-install: cannot read %s (%s)" % (bridge_settings_path, e))
        return 2

    print("bridge-install: %s -> %s%s" % (RELEASE, target, " (dry run)" if dry else ""))
    total = 0
    for sub in SUBDIRS:
        n = copy_tree(os.path.join(RELEASE, sub), os.path.join(target, sub), dry)
        total += n
        print("  %-14s %d files" % (sub + "/", n))

    settings_path = os.path.join(target, "settings.json")
    existing = {}
    if os.path.isfile(settings_path):
        try:
            existing = load_json(settings_path)
        except Exception as e:
            print("bridge-install: %s is not valid JSON (%s); fix it by hand first" % (settings_path, e))
            return 2
    merged, changes = merge_settings(existing, bridge_settings)
    if changes and not dry:
        if os.path.isfile(settings_path):
            bak = settings_path + ".bak-" + datetime.date.today().isoformat()
            shutil.copyfile(settings_path, bak)
            print("  settings.json  backup at %s" % bak)
        os.makedirs(target, exist_ok=True)
        with open(settings_path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(merged, f, indent=2)
            f.write("\n")
    kept = sorted(k for k in existing if k not in ("permissions", "hooks"))
    print("  settings.json  %d bridge entries added, %d owner keys kept%s" % (
        len(changes), len(kept), (" (" + ", ".join(kept) + ")") if kept else ""))
    for c in changes:
        print("    + " + c)

    print("  " + install_shim(dry))
    if dry:
        return 0
    check = os.path.join(target, "cursor-bridge", "bridge-check.py")
    try:
        p = subprocess.run([sys.executable, check, "--root", target], capture_output=True, text=True, creationflags=NO_WINDOW)
    except OSError as e:
        print("bridge-install: cannot run the install check (%s)" % e)
        return 1
    sys.stdout.write(p.stdout)
    return 0 if p.returncode == 0 else 1


if __name__ == "__main__":
    for _s in (sys.stdout, sys.stderr):      # never crash on a character the console lacks
        if hasattr(_s, "reconfigure"):
            _s.reconfigure(errors="backslashreplace")
    sys.exit(main())
