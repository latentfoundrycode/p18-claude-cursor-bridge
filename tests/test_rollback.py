"""bridge-install.py: a release can be taken back (release A1a). Installing over another
version keeps that version; --rollback puts it back, removes what only the newer release
shipped (files, allow and deny entries, hooks), keeps the owner's settings, restores the
shim, and passes the install check; installing again works. LOCALAPPDATA points at a
temporary folder in every run."""
import json
import os
import shutil
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
RELEASE = os.path.abspath(os.path.join(HERE, os.pardir, "bridge"))
NEW_VERSION = open(os.path.join(RELEASE, "cursor-bridge", "VERSION"), encoding="utf-8").read().strip()
OLD_VERSION = "2026.01.01a"
GUARD_RULE = "Bash(python ~/.claude/cursor-bridge/review-guard.py:*)"
OWNER = {"switchModelsOnFlag": True, "permissions": {"allow": ["Bash(ls:*)"], "additionalDirectories": ["E:/somewhere"]},
         "hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [{"type": "command", "command": "echo owner"}]}]}}


def run(prog, tmp_path, *args):
    env = dict(os.environ, LOCALAPPDATA=str(tmp_path / "localappdata"))
    p = subprocess.run([sys.executable, str(prog)] + list(args), capture_output=True, text=True, env=env)
    return p.returncode, p.stdout + p.stderr


@pytest.fixture
def old_release(tmp_path, program):
    """An older release made from the current tree: it has a file the new one lacks, lacks
    review-guard.py with its allow rule and session-start.py with its hooks, and has
    another shim."""
    old = tmp_path / "old-release"
    shutil.copytree(RELEASE, old, ignore=shutil.ignore_patterns("__pycache__"))
    cb = old / "cursor-bridge"
    (cb / "VERSION").write_text(OLD_VERSION + "\n", encoding="utf-8", newline="\n")
    (cb / "old-only.md").write_text("shipped by the old release only\n", encoding="utf-8")
    (cb / "review-guard.py").unlink()
    (cb / "session-start.py").unlink()
    settings = json.loads((cb / "settings.bridge.json").read_text(encoding="utf-8"))
    settings["permissions"]["allow"].remove(GUARD_RULE)
    del settings["hooks"]["SessionStart"]
    (cb / "settings.bridge.json").write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
    with open(cb / "cursor-agent.shim", "ab") as f:
        f.write(b"# old release\n")
    norm_hash = program("bridge-check").norm_hash
    files = {}
    for dirpath, dirs, names in os.walk(old):
        for n in names:
            p = os.path.join(dirpath, n)
            rel = os.path.relpath(p, old).replace("\\", "/")
            if rel != "cursor-bridge/MANIFEST.json":
                files[rel] = norm_hash(p)
    (cb / "MANIFEST.json").write_text(json.dumps({"version": OLD_VERSION, "generated": "test", "files": files}, indent=2), encoding="utf-8")
    return old


@pytest.fixture
def installed_old_then_new(tmp_path, old_release):
    target = tmp_path / ".claude"
    target.mkdir()
    (target / "settings.json").write_text(json.dumps(OWNER, indent=2), encoding="utf-8")
    rc, out = run(old_release / "cursor-bridge" / "bridge-install.py", tmp_path, "--target", str(target))
    assert rc == 0 and "MATCHES bridge " + OLD_VERSION in out, out
    rc, out = run(os.path.join(RELEASE, "cursor-bridge", "bridge-install.py"), tmp_path, "--target", str(target))
    assert rc == 0 and "MATCHES bridge " + NEW_VERSION in out, out
    return target, out


def settings_of(target):
    return json.load(open(target / "settings.json", encoding="utf-8"))


def hook_commands(settings, event):
    return [h["command"] for g in settings.get("hooks", {}).get(event, []) for h in g.get("hooks", [])]


def test_installing_over_another_version_keeps_it_and_drops_its_leftovers(installed_old_then_new):
    target, out = installed_old_then_new
    saved = target / "cursor-bridge-previous" / OLD_VERSION
    assert (saved / "cursor-bridge" / "old-only.md").is_file() and (saved / "commands" / "supervisor.md").is_file()
    assert (saved / "cursor-bridge" / "MANIFEST.json").is_file()
    assert not (target / "cursor-bridge" / "old-only.md").exists(), "a file the new release does not ship is removed"
    assert (target / "cursor-bridge" / "review-guard.py").is_file()
    assert "previous       " + OLD_VERSION in out and "--rollback" in out
    s = settings_of(target)
    assert GUARD_RULE in s["permissions"]["allow"] and any("session-start.py" in c for c in hook_commands(s, "SessionStart"))


def test_rollback_restores_the_previous_release_and_only_what_was_the_bridges(tmp_path, installed_old_then_new):
    target, _ = installed_old_then_new
    rc, out = run(target / "cursor-bridge" / "bridge-install.py", tmp_path, "--rollback", "--target", str(target))
    assert rc == 0, out
    assert "rolling back %s -> %s" % (NEW_VERSION, OLD_VERSION) in out and "MATCHES bridge " + OLD_VERSION in out
    assert (target / "cursor-bridge" / "old-only.md").is_file(), "the old release's own file is back"
    assert not (target / "cursor-bridge" / "review-guard.py").exists(), "a file only the newer release shipped is gone"
    assert (target / "cursor-bridge" / "VERSION").read_text(encoding="utf-8").strip() == OLD_VERSION
    s = settings_of(target)
    assert GUARD_RULE not in s["permissions"]["allow"], "an allow rule only the newer release added is taken out"
    assert not any("session-start.py" in c for c in hook_commands(s, "SessionStart")), "its hooks are taken out"
    assert any("loop-guard" in c for c in hook_commands(s, "Stop")), "a hook both releases have stays"
    assert s["switchModelsOnFlag"] is True and "Bash(ls:*)" in s["permissions"]["allow"]
    assert s["permissions"]["additionalDirectories"] == ["E:/somewhere"]
    assert "echo owner" in hook_commands(s, "PreToolUse"), "the owner's own hook stays"
    assert not (target / "cursor-bridge-previous").exists(), "the saved copy is used up"
    assert "If rolled back" in out
    note = (target / "cursor-bridge" / "ROLLED-BACK.md").read_text(encoding="utf-8")
    assert "# Rolled back: %s -> %s" % (NEW_VERSION, OLD_VERSION) in note
    assert "## " + NEW_VERSION in note and "Bridge version:" in note, "the newer release's own 'If rolled back' items are kept for calibration"
    rc, out = run(target / "cursor-bridge" / "bridge-install.py", tmp_path, "--rollback", "--target", str(target))
    assert rc == 2 and "nothing to roll back to" in out


def test_reinstalling_after_a_rollback_works(tmp_path, installed_old_then_new):
    target, _ = installed_old_then_new
    rc, out = run(target / "cursor-bridge" / "bridge-install.py", tmp_path, "--rollback", "--target", str(target))
    assert rc == 0, out
    rc, out = run(os.path.join(RELEASE, "cursor-bridge", "bridge-install.py"), tmp_path, "--target", str(target))
    assert rc == 0 and "MATCHES bridge " + NEW_VERSION in out, out
    assert (target / "cursor-bridge-previous" / OLD_VERSION / "cursor-bridge" / "old-only.md").is_file()
    assert GUARD_RULE in settings_of(target)["permissions"]["allow"]
    assert not (target / "cursor-bridge" / "ROLLED-BACK.md").exists(), "an install removes the stale note"


def test_reinstalling_the_same_version_keeps_the_saved_previous(tmp_path, installed_old_then_new):
    target, _ = installed_old_then_new
    rc, out = run(os.path.join(RELEASE, "cursor-bridge", "bridge-install.py"), tmp_path, "--target", str(target))
    assert rc == 0, out
    assert (target / "cursor-bridge-previous" / OLD_VERSION).is_dir(), "a repeated install must not overwrite the way back"


def test_rollback_dry_run_changes_nothing(tmp_path, installed_old_then_new):
    target, _ = installed_old_then_new
    before = sorted(str(p.relative_to(target)) for p in target.rglob("*"))
    version = (target / "cursor-bridge" / "VERSION").read_text(encoding="utf-8")
    rc, out = run(target / "cursor-bridge" / "bridge-install.py", tmp_path, "--rollback", "--dry-run", "--target", str(target))
    assert rc == 0 and "(dry run)" in out
    assert sorted(str(p.relative_to(target)) for p in target.rglob("*")) == before
    assert (target / "cursor-bridge" / "VERSION").read_text(encoding="utf-8") == version


@pytest.mark.skipif(sys.platform != "win32", reason="the shim is installed on Windows only")
def test_rollback_restores_the_previous_shim(tmp_path, old_release):
    cli = tmp_path / "localappdata" / "cursor-agent"
    cli.mkdir(parents=True)
    target = tmp_path / ".claude"
    assert run(old_release / "cursor-bridge" / "bridge-install.py", tmp_path, "--target", str(target))[0] == 0
    assert run(os.path.join(RELEASE, "cursor-bridge", "bridge-install.py"), tmp_path, "--target", str(target))[0] == 0
    assert b"# old release" not in (cli / "cursor-agent").read_bytes()
    rc, out = run(target / "cursor-bridge" / "bridge-install.py", tmp_path, "--rollback", "--target", str(target))
    assert rc == 0, out
    assert (cli / "cursor-agent").read_bytes().endswith(b"# old release\n")


def test_remove_settings_takes_out_only_what_the_leaving_release_owns(program):
    bi = program("bridge-install")
    leaving = {"permissions": {"allow": ["A", "B", "NEW"], "deny": ["D", "NEWDENY"]},
               "hooks": {"Stop": [{"hooks": [{"type": "command", "command": "stop-cmd"}]}],
                         "SessionStart": [{"matcher": "compact", "hooks": [{"type": "command", "command": "new-hook-1"}, {"type": "command", "command": "new-hook-2"}]}]}}
    staying = {"permissions": {"allow": ["A", "B"], "deny": ["D"]}, "hooks": {"Stop": [{"hooks": [{"type": "command", "command": "stop-cmd"}]}]}}
    owner = {"theme": "dark", "permissions": {"allow": ["OWN", "A", "B", "NEW"], "deny": ["D", "NEWDENY", "OWNDENY"]},
             "hooks": {"Stop": [{"hooks": [{"type": "command", "command": "stop-cmd"}]}],
                       "SessionStart": [{"matcher": "startup", "hooks": [{"type": "command", "command": "owner-hook"}]},
                                        {"matcher": "compact", "hooks": [{"type": "command", "command": "new-hook-1"}, {"type": "command", "command": "new-hook-2"}]}]}}
    out, changes = bi.remove_settings(owner, leaving, staying)
    assert out["permissions"]["allow"] == ["OWN", "A", "B"] and out["permissions"]["deny"] == ["D", "OWNDENY"]
    assert out["hooks"]["SessionStart"] == [{"matcher": "startup", "hooks": [{"type": "command", "command": "owner-hook"}]}]
    assert out["hooks"]["Stop"] == owner["hooks"]["Stop"] and out["theme"] == "dark"
    assert len(changes) == 4
    assert owner["permissions"]["allow"] == ["OWN", "A", "B", "NEW"], "the input is not modified"


def test_a_repeated_install_after_an_interruption_does_not_spoil_the_kept_copy(tmp_path, installed_old_then_new):
    """A run that died before the manifest was replaced leaves new files under the old
    manifest; saving that tree again as "the previous release" would spoil the way back."""
    target, _ = installed_old_then_new
    kept = target / "cursor-bridge-previous" / OLD_VERSION
    for name in ("MANIFEST.json", "VERSION"):
        shutil.copyfile(kept / "cursor-bridge" / name, target / "cursor-bridge" / name)
    rc, out = run(os.path.join(RELEASE, "cursor-bridge", "bridge-install.py"), tmp_path, "--target", str(target))
    assert rc == 0 and "MATCHES bridge " + NEW_VERSION in out, out
    assert (kept / "cursor-bridge" / "old-only.md").is_file(), "the kept copy is the first one"
    assert (kept / "cursor-bridge" / "cursor-agent.shim").read_bytes().endswith(b"# old release\n")
    assert not (kept / "cursor-bridge" / "review-guard.py").exists()
    assert not any(p.name.endswith(".partial") for p in (target / "cursor-bridge-previous").iterdir())


def test_rollback_refuses_a_kept_copy_that_is_not_complete(tmp_path, installed_old_then_new):
    target, _ = installed_old_then_new
    (target / "cursor-bridge-previous" / OLD_VERSION / "commands" / "supervisor.md").unlink()
    before = settings_of(target)
    rc, out = run(target / "cursor-bridge" / "bridge-install.py", tmp_path, "--rollback", "--target", str(target))
    assert rc == 2 and "is not complete" in out and "commands/supervisor.md" in out, out
    assert (target / "cursor-bridge" / "VERSION").read_text(encoding="utf-8").strip() == NEW_VERSION
    assert settings_of(target) == before and not (target / "cursor-bridge" / "ROLLED-BACK.md").exists()
    rc, out = run(target / "cursor-bridge" / "bridge-check.py", tmp_path, "--root", str(target))
    assert rc == 0, out


def test_installing_an_older_release_over_a_newer_one_takes_the_newer_entries_out(tmp_path, old_release):
    """Installing and taking back are one replacement: an install also removes the rules
    and hooks only the replaced release owned, so no hook is left to run a removed program."""
    target = tmp_path / ".claude"
    new_installer = os.path.join(RELEASE, "cursor-bridge", "bridge-install.py")
    assert run(new_installer, tmp_path, "--target", str(target))[0] == 0
    rc, out = run(old_release / "cursor-bridge" / "bridge-install.py", tmp_path, "--target", str(target))
    assert rc == 0 and "MATCHES bridge " + OLD_VERSION in out, out
    s = settings_of(target)
    assert GUARD_RULE not in s["permissions"]["allow"] and not hook_commands(s, "SessionStart")
    assert not (target / "cursor-bridge" / "session-start.py").exists()
    assert (target / "cursor-bridge-previous" / NEW_VERSION / "cursor-bridge" / "session-start.py").is_file()
    rc, out = run(target / "cursor-bridge" / "bridge-install.py", tmp_path, "--rollback", "--target", str(target))
    assert rc == 0 and "MATCHES bridge " + NEW_VERSION in out, out
    assert any("session-start.py" in c for c in hook_commands(settings_of(target), "SessionStart"))


def hooks_without_a_program(target):
    s = settings_of(target)
    out = []
    for event in s.get("hooks", {}):
        for c in hook_commands(s, event):
            name = c.split("/cursor-bridge/")[-1].split('"')[0].split()[0] if "/cursor-bridge/" in c else None
            if name and not (target / "cursor-bridge" / name).is_file():
                out.append("%s: %s" % (event, name))
    return out


@pytest.mark.parametrize("direction", ["older over newer", "newer over older"])
@pytest.mark.parametrize("dies_in", ["write_settings", "remove_files", "copy_tree"])
def test_an_interrupted_replacement_never_leaves_a_hook_without_its_program(tmp_path, old_release, program, monkeypatch, direction, dies_in):
    """A hook that runs a missing program fails with exit status 2, which blocks its event
    in every session; so whatever step a replacement dies in, settings.json names only
    programs that are there."""
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "localappdata"))
    target = tmp_path / ".claude"
    first, second = (RELEASE, str(old_release)) if direction == "older over newer" else (str(old_release), RELEASE)
    assert run(os.path.join(first, "cursor-bridge", "bridge-install.py"), tmp_path, "--target", str(target))[0] == 0
    assert hooks_without_a_program(target) == []
    bi = program("bridge-install")

    def dies(*args, **kwargs):
        raise OSError("the disk is full")
    monkeypatch.setattr(bi, dies_in, dies)
    existing, new_settings = bi.read_inputs(str(target), second)
    with pytest.raises(OSError):
        bi.replace_release(str(target), second, existing, new_settings, False)
    assert hooks_without_a_program(target) == []
    json.load(open(target / "settings.json", encoding="utf-8"))
    monkeypatch.undo()
    rc, out = run(os.path.join(second, "cursor-bridge", "bridge-install.py"), tmp_path, "--target", str(target))
    assert rc == 0 and "RESULT: INSTALLED TREE MATCHES" in out, "the repeated run completes the replacement: " + out
    assert hooks_without_a_program(target) == []
