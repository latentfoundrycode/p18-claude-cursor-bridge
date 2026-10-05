#!/usr/bin/env python3
"""bridge-install: install or update the bridge into ~/.claude from a release folder, and
take a release back.

  python <release>/cursor-bridge/bridge-install.py [--target <path-to-.claude>] [--dry-run]
  python ~/.claude/cursor-bridge/bridge-install.py --rollback [--target <path-to-.claude>] [--dry-run]

The release folder is the one this file lives in (its parent is the release tree: commands/,
agents/, skills/, cursor-bridge/; in the bridge's repository that tree is `bridge/`).

Installing:

  1. KEEPS THE PREVIOUS RELEASE: when the target holds a bridge of another version, the
     files its manifest lists are saved to <target>/cursor-bridge-previous/<that version>/
     first (one previous release is kept; an older saved one is removed; a kept copy of
     the same version is never written twice, see save_previous);
  2. REPLACES the installed release by this one (replace_release): the allow and deny
     rules and the hooks only the replaced release owned leave the target's settings.json,
     the files its manifest listed that this release no longer ships are removed,
     commands/, agents/, skills/ and cursor-bridge/ are copied file by file (every other
     file is left alone), and the bridge-owned settings (cursor-bridge/settings.bridge.json)
     are MERGED into settings.json: every allow and deny entry and every hook the bridge
     needs is added if missing, entries the bridge has RETIRED (its "retired" list) are
     removed, and every key the owner or Claude Code wrote there is kept untouched
     (KP-030). The previous settings.json is saved beside it as
     settings.json.bak-<date>-<time> before its first change;
  3. installs the cursor-agent shim (cursor-bridge/cursor-agent.shim) at
     %LOCALAPPDATA%/cursor-agent/cursor-agent, the file Claude Code's Bash tool runs for
     `cursor-agent` on Windows (KP-032), when that folder exists, keeping a different
     previous file as cursor-agent.bak-<date>-<time>;
  4. runs bridge-check.py on the result and prints its verdict.

Taking a release back (--rollback) is the same replacement with the kept release as its
source, so every install exercises the way back: the files, the allow and deny entries and
the hooks only the newer release added go, the owner's keys stay, the kept release's shim
is installed. The "If rolled back" items of the release taken back are written to
cursor-bridge/ROLLED-BACK.md for /calibrate-bridge (the restored changelog no longer holds
them; the next install removes the note), the kept copy is used up, and bridge-check.py
runs on the result. A kept copy that is not complete is refused before anything changes.

The bridge is installed once per computer, so an install and a rollback reach every project:
the release's changelog entry says what a project that had calibrated forward must restore
("If rolled back"), and /calibrate-bridge applies it.

Exit 0 = installed (or rolled back) and verified; 1 = verification failed; 2 = could not
install or nothing to roll back to. ASCII-only on purpose (cp1252 consoles).
"""
import datetime
import json
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RELEASE = os.path.abspath(os.path.join(HERE, os.pardir))
SUBDIRS = ("commands", "agents", "skills", "cursor-bridge")
PREVIOUS = "cursor-bridge-previous"
ROLLED_BACK = os.path.join("cursor-bridge", "ROLLED-BACK.md")
NO_WINDOW = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0


def load_json(path):
    with open(path, encoding="utf-8-sig") as f:
        return json.load(f)


def manifest_of(tree):
    """(version, set of relative file paths) of the bridge in `tree`, or (None, set())."""
    p = os.path.join(tree, "cursor-bridge", "MANIFEST.json")
    try:
        m = load_json(p)
    except (OSError, ValueError):
        return None, set()
    return m.get("version"), set(m.get("files") or {}) | {"cursor-bridge/MANIFEST.json"}


def bridge_settings_of(tree):
    """The bridge-owned settings of the release in `tree`, or None when it has none readable."""
    try:
        return load_json(os.path.join(tree, "cursor-bridge", "settings.bridge.json"))
    except (OSError, ValueError):
        return None


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
    retired = set(bridge_settings.get("retired") or [])
    for key in ("allow", "deny"):
        want = (bridge_settings.get("permissions") or {}).get(key) or []
        have = perms.setdefault(key, [])
        for entry in list(have):
            if entry in retired and entry not in want:
                have.remove(entry)
                changes.append("permissions.%s -= %s (retired)" % (key, entry))
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


def remove_settings(target_settings, leaving, staying):
    """Return (settings, changes) with the entries only the `leaving` release owns taken out:
    its allow and deny rules and its hook commands that the `staying` release does not have."""
    out = json.loads(json.dumps(target_settings))
    changes = []
    perms = out.get("permissions") or {}
    for key in ("allow", "deny"):
        gone = set((leaving.get("permissions") or {}).get(key) or []) - set((staying.get("permissions") or {}).get(key) or [])
        have = perms.get(key) or []
        for entry in list(have):
            if entry in gone:
                have.remove(entry)
                changes.append("permissions.%s -= %s" % (key, entry))
    hooks = out.get("hooks") or {}
    for event, groups in (leaving.get("hooks") or {}).items():
        gone = set(hook_commands(groups)) - set(hook_commands((staying.get("hooks") or {}).get(event)))
        if not gone or event not in hooks:
            continue
        kept_groups = []
        for g in hooks[event]:
            inner = [h for h in (g.get("hooks") or []) if h.get("command") not in gone]
            for h in (g.get("hooks") or []):
                if h.get("command") in gone:
                    changes.append("hooks.%s -= %s" % (event, h.get("command")))
            if inner:
                g = dict(g)
                g["hooks"] = inner
                kept_groups.append(g)
        if kept_groups:
            hooks[event] = kept_groups
        else:
            del hooks[event]
    return out, changes


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


def remove_files(target, rels, dry):
    """Remove bridge-owned files by relative path; prune folders this leaves empty."""
    removed = 0
    for rel in sorted(rels):
        p = os.path.join(target, rel.replace("/", os.sep))
        if os.path.isfile(p):
            if not dry:
                os.remove(p)
                d = os.path.dirname(p)
                while os.path.normcase(d) != os.path.normcase(target) and os.path.isdir(d) and not os.listdir(d):
                    os.rmdir(d)
                    d = os.path.dirname(d)
            removed += 1
    return removed


def save_previous(target, version, files, dry):
    """Copy the installed release's own files to <target>/cursor-bridge-previous/<version>/.

    A kept copy of that version is never written twice: after an interrupted install the
    target holds files of both releases, and saving it again on the repeated run would
    spoil the way back. The copy is written under another name and renamed when it is
    complete, so a folder with the version's name is always a whole one."""
    base = os.path.join(target, PREVIOUS)
    dest = os.path.join(base, version)
    if dry or os.path.isdir(dest):
        return dest
    shutil.rmtree(base, ignore_errors=True)        # one previous release is kept
    tmp = dest + ".partial"
    for rel in sorted(files):
        src = os.path.join(target, rel.replace("/", os.sep))
        if os.path.isfile(src):
            out = os.path.join(tmp, rel.replace("/", os.sep))
            os.makedirs(os.path.dirname(out), exist_ok=True)
            shutil.copyfile(src, out)
    os.rename(tmp, dest)
    return dest


def rolled_back_note(leaving_changelog, cur_version, prev_version):
    """(text of ROLLED-BACK.md, whether an entry was found): the 'If rolled back' parts of
    every changelog entry newer than `prev_version`. Versions (YYYY.MM.DD plus a letter)
    sort as text."""
    try:
        with open(leaving_changelog, encoding="utf-8-sig") as f:
            text = f.read()
    except OSError:
        text = ""
    parts = re.split(r"(?m)^## (\d{4}\.\d{2}\.\d{2}[a-z]?)[ \t]*$", text)
    out = ["# Rolled back: %s -> %s" % (cur_version or "?", prev_version), "",
           "Written by bridge-install.py --rollback on %s. /calibrate-bridge applies the items below in a project whose `Bridge version:` is newer than the installed one, then records the installed version. The next install removes this file." % datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), ""]
    found = False
    for i in range(1, len(parts) - 1, 2):
        version, body = parts[i], parts[i + 1]
        if version <= prev_version:
            continue
        m = re.search(r"(?ms)^\*\*If rolled back\*\*[ \t]*\n(.*?)(?=^\*\*[A-Z]|^---[ \t]*$|\Z)", body)
        out.append("## %s" % version)
        out.append("")
        out.append(m.group(1).strip() if m else "- *(all phases)* This release's entry names nothing to restore.")
        out.append("")
        found = True
    if not found:
        out.append("No changelog entry newer than %s was found; nothing to restore." % prev_version)
        out.append("")
    return "\n".join(out), found


def install_shim(source_dir, dry):
    src = os.path.join(source_dir, "cursor-agent.shim")
    if sys.platform != "win32" or not os.path.isfile(src):
        return "shim: skipped (not Windows or no shim in the release)"
    folder = os.path.join(os.environ.get("LOCALAPPDATA", ""), "cursor-agent")
    if not os.path.isdir(folder):
        return "shim: NOT installed - %s does not exist (is the Cursor CLI installed?)" % folder
    dst = os.path.join(folder, "cursor-agent")
    data = open(src, "rb").read().replace(b"\r\n", b"\n")
    if not dry:
        if os.path.isfile(dst) and open(dst, "rb").read().replace(b"\r\n", b"\n") != data:
            bak = dst + ".bak-" + datetime.datetime.now().strftime("%Y-%m-%d-%H%M")
            shutil.copyfile(dst, bak)
        with open(dst, "wb") as f:
            f.write(data)
        try:
            os.chmod(dst, 0o755)
        except OSError:
            pass
    return "shim: installed at %s" % dst


def backup_settings(settings_path, dry):
    if dry or not os.path.isfile(settings_path):
        return
    bak = settings_path + ".bak-" + datetime.datetime.now().strftime("%Y-%m-%d-%H%M%S")
    shutil.copyfile(settings_path, bak)
    print("  settings.json  backup at %s" % bak)


def write_settings(settings_path, new, dry):
    """Write settings.json whole or not at all (a half-written file would stop every session)."""
    if dry:
        return
    os.makedirs(os.path.dirname(settings_path), exist_ok=True)
    tmp = settings_path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(new, f, indent=2)
        f.write("\n")
    os.replace(tmp, settings_path)


def read_inputs(target, source):
    """(the owner's settings, the source release's settings list), or None with a message
    when either cannot be read; nothing has been changed at that point."""
    settings_path = os.path.join(target, "settings.json")
    try:
        existing = load_json(settings_path) if os.path.isfile(settings_path) else {}
    except Exception as e:
        print("bridge-install: %s is not valid JSON (%s); fix it by hand first" % (settings_path, e))
        return None
    new_settings = bridge_settings_of(source)
    if new_settings is None:
        print("bridge-install: cannot read %s" % os.path.join(source, "cursor-bridge", "settings.bridge.json"))
        return None
    return existing, new_settings


def replace_release(target, source, existing, new_settings, dry):
    """Put the release in `source` where the installed one is. Installing and taking a
    release back are this one operation.

    The order keeps settings.json from naming a hook whose program is not there, also when
    a run is interrupted and repeated. (A hook that runs a missing program fails with exit
    status 2, which Claude Code reads as "block": every matching tool call, or the end of
    every turn, in every session on the computer.) So the entries only the replaced
    release owned leave settings.json first, then its files go, then the source's files
    arrive, and only then are the source's entries merged in."""
    settings_path = os.path.join(target, "settings.json")
    old_version, old_files = manifest_of(target)
    new_version, new_files = manifest_of(source)
    old_settings = bridge_settings_of(target) or {}
    stripped, removed = remove_settings(existing, old_settings, new_settings)
    merged, added = merge_settings(stripped, new_settings)
    changes = removed + added
    if changes:
        backup_settings(settings_path, dry)
    if removed:
        write_settings(settings_path, stripped, dry)
    dropped = remove_files(target, old_files - new_files, dry) if new_files else 0
    for sub in SUBDIRS:
        if os.path.isdir(os.path.join(source, sub)):
            n = copy_tree(os.path.join(source, sub), os.path.join(target, sub), dry)
            print("  %-14s %d files" % (sub + "/", n))
    if dropped:
        print("  removed        %d file(s) that %s shipped and %s does not" % (dropped, old_version or "the replaced release", new_version or "this one"))
    if added:
        write_settings(settings_path, merged, dry)
    kept = sorted(k for k in existing if k not in ("permissions", "hooks"))
    taken = sum(1 for c in changes if " -= " in c)
    print("  settings.json  %d bridge entries added, %d removed, %d owner keys kept%s" % (
        len(changes) - taken, taken, len(kept), (" (" + ", ".join(kept) + ")") if kept else ""))
    for c in changes:
        print("    " + ("- " if " -= " in c else "+ ") + c)
    print("  " + install_shim(os.path.join(source, "cursor-bridge"), dry))


def run_check(target):
    check = os.path.join(target, "cursor-bridge", "bridge-check.py")
    try:
        p = subprocess.run([sys.executable, check, "--root", target], capture_output=True, text=True, creationflags=NO_WINDOW)
    except OSError as e:
        print("bridge-install: cannot run the install check (%s)" % e)
        return 1
    sys.stdout.write(p.stdout)
    return 0 if p.returncode == 0 else 1


def install(target, dry):
    if os.path.abspath(target) == RELEASE:
        print("bridge-install: the release folder is the target; nothing to do")
        return 2
    for sub in SUBDIRS:
        if not os.path.isdir(os.path.join(RELEASE, sub)):
            print("bridge-install: %s has no %s/ folder; is this a bridge release?" % (RELEASE, sub))
            return 2
    inputs = read_inputs(target, RELEASE)
    if inputs is None:
        return 2
    new_version, _ = manifest_of(RELEASE)
    old_version, old_files = manifest_of(target)
    print("bridge-install: %s -> %s%s" % (RELEASE, target, " (dry run)" if dry else ""))
    if old_version and old_version != new_version:
        dest = save_previous(target, old_version, old_files, dry)
        print("  previous       %s kept at %s (take this release back with --rollback)" % (old_version, dest))
    replace_release(target, RELEASE, inputs[0], inputs[1], dry)
    if dry:
        return 0
    stale_note = os.path.join(target, ROLLED_BACK)
    if os.path.isfile(stale_note):
        os.remove(stale_note)
    return run_check(target)


def rollback(target, dry):
    base = os.path.join(target, PREVIOUS)
    saved = sorted(n for n in (os.listdir(base) if os.path.isdir(base) else [])
                   if os.path.isdir(os.path.join(base, n)) and not n.endswith(".partial"))
    if not saved:
        print("bridge-install: nothing to roll back to (%s holds no previous release)" % base)
        return 2
    prev_tree = os.path.join(base, saved[-1])
    prev_version, prev_files = manifest_of(prev_tree)
    if not prev_version:
        print("bridge-install: %s has no readable manifest; cannot roll back" % prev_tree)
        return 2
    absent = sorted(rel for rel in prev_files if not os.path.isfile(os.path.join(prev_tree, rel.replace("/", os.sep))))
    if absent:
        print("bridge-install: the kept copy of %s is not complete (%d of its %d files are missing, first: %s); nothing was changed. "
              "Install that release from the bridge's repository instead: check out its commit there and run its bridge-install.py."
              % (prev_version, len(absent), len(prev_files), absent[0]))
        return 2
    inputs = read_inputs(target, prev_tree)
    if inputs is None:
        return 2
    cur_version, _ = manifest_of(target)
    note, found = rolled_back_note(os.path.join(target, "cursor-bridge", "CHANGELOG.md"), cur_version, prev_version)
    print("bridge-install: rolling back %s -> %s at %s%s" % (cur_version or "?", prev_version, target, " (dry run)" if dry else ""))
    note_path = os.path.join(target, ROLLED_BACK)
    # Written before the files change: a repeated run after an interruption finds the
    # previous changelog already restored and could no longer say what was taken back.
    if not dry and (found or not os.path.isfile(note_path)):
        with open(note_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(note)
    replace_release(target, prev_tree, inputs[0], inputs[1], dry)
    if dry:
        return 0
    shutil.rmtree(prev_tree, ignore_errors=True)
    try:
        if not os.listdir(base):
            os.rmdir(base)
    except OSError:
        pass
    print("  note           every project on this computer now runs %s; a project that had calibrated to %s applies that release's \"If rolled back\" items (kept in %s) at its next /calibrate-bridge" % (prev_version, cur_version or "the newer release", ROLLED_BACK.replace(os.sep, "/")))
    return run_check(target)


def main():
    argv = sys.argv[1:]
    dry = "--dry-run" in argv
    target = os.path.join(os.path.expanduser("~"), ".claude")
    if "--target" in argv:
        target = os.path.abspath(argv[argv.index("--target") + 1])
    if "--rollback" in argv:
        return rollback(target, dry)
    return install(target, dry)


if __name__ == "__main__":
    for _s in (sys.stdout, sys.stderr):      # never crash on a character the console lacks
        if hasattr(_s, "reconfigure"):
            _s.reconfigure(errors="backslashreplace")
    sys.exit(main())
