"""bridge-install.py: a release can be taken back (release A1a). Installing over another
version keeps that version; --rollback puts it back, removes what only the newer release
shipped (files, allow and deny entries, hooks), keeps the owner's settings, restores the
shim, and passes the install check; installing again works. Installing and taking back are
one replacement, and whatever point it is stopped at, settings.json names no hook whose
program is missing and the same command can be run again. LOCALAPPDATA points at a
temporary folder in every run. The repository's tree is a checkout on a branch while the
tests run, so installs from it pass --anyway."""
import importlib.util
import json
import os
import shutil
import stat
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
RELEASE = os.path.abspath(os.path.join(HERE, os.pardir, "bridge"))
NEW_INSTALLER = os.path.join(RELEASE, "cursor-bridge", "bridge-install.py")
NEW_VERSION = open(os.path.join(RELEASE, "cursor-bridge", "VERSION"), encoding="utf-8").read().strip()
OLD_VERSION = "2026.01.01a"
GUARD_RULE = "Bash(python ~/.claude/cursor-bridge/review-guard.py:*)"
OWNER = {"switchModelsOnFlag": True, "permissions": {"allow": ["Bash(ls:*)"], "additionalDirectories": ["E:/somewhere"]},
         "hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [{"type": "command", "command": "echo owner"}]}]}}
CANNOT_ROLL_BACK = 'import sys\nprint("bridge-install: the release folder is the target; nothing to do")\nsys.exit(2)\n'


def run(prog, tmp_path, *args):
    env = dict(os.environ, LOCALAPPDATA=str(tmp_path / "localappdata"))
    p = subprocess.run([sys.executable, str(prog)] + list(args), capture_output=True, text=True, env=env)
    return p.returncode, p.stdout + p.stderr


def install_new(tmp_path, target, *args):
    return run(NEW_INSTALLER, tmp_path, "--target", str(target), "--anyway", *args)


def install_old(tmp_path, old, target):
    return run(old / "cursor-bridge" / "bridge-install.py", tmp_path, "--target", str(target))


def roll_back(tmp_path, target, *args):
    """A release is taken back with a release folder's installer, never the installed copy."""
    return run(NEW_INSTALLER, tmp_path, "--rollback", "--target", str(target), *args)


def load_installer(release):
    """The install program of `release` as a module; its RELEASE is that folder."""
    spec = importlib.util.spec_from_file_location("bridge_install_under_test", os.path.join(str(release), "cursor-bridge", "bridge-install.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def make_old_release(old, program, installer=None):
    """An older release made from the current tree: it has a file the new one lacks, lacks
    review-guard.py with its allow rule and session-start.py with its hooks, and has
    another shim. With `installer`, its install program is replaced by that text."""
    shutil.copytree(RELEASE, old, ignore=shutil.ignore_patterns("__pycache__"))
    cb = old / "cursor-bridge"
    (cb / "VERSION").write_text(OLD_VERSION + "\n", encoding="utf-8", newline="\n")
    (cb / "old-only.md").write_text("shipped by the old release only\n", encoding="utf-8")
    (cb / "review-guard.py").unlink()
    (cb / "session-start.py").unlink()
    if installer:
        (cb / "bridge-install.py").write_text(installer, encoding="utf-8")
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
def old_release(tmp_path, program):
    return make_old_release(tmp_path / "old-release", program)


@pytest.fixture
def installed_old_then_new(tmp_path, old_release):
    target = tmp_path / ".claude"
    target.mkdir()
    (target / "settings.json").write_text(json.dumps(OWNER, indent=2), encoding="utf-8")
    rc, out = install_old(tmp_path, old_release, target)
    assert rc == 0 and "MATCHES bridge " + OLD_VERSION in out, out
    rc, out = install_new(tmp_path, target)
    assert rc == 0 and "MATCHES bridge " + NEW_VERSION in out, out
    return target, out


def settings_of(target):
    return json.load(open(target / "settings.json", encoding="utf-8"))


def hook_commands(settings, event):
    return [h["command"] for g in settings.get("hooks", {}).get(event, []) for h in g.get("hooks", [])]


def version_of(target):
    return (target / "cursor-bridge" / "VERSION").read_text(encoding="utf-8").strip()


def hooks_without_a_program(target):
    s = settings_of(target)
    out = []
    for event in s.get("hooks", {}):
        for c in hook_commands(s, event):
            name = c.split("/cursor-bridge/")[-1].split('"')[0].split()[0] if "/cursor-bridge/" in c else None
            if name and not (target / "cursor-bridge" / name).is_file():
                out.append("%s: %s" % (event, name))
    return out


def test_installing_over_another_version_keeps_it_and_drops_its_leftovers(installed_old_then_new):
    target, out = installed_old_then_new
    saved = target / "cursor-bridge-previous" / OLD_VERSION
    assert (saved / "cursor-bridge" / "old-only.md").is_file() and (saved / "commands" / "supervisor.md").is_file()
    assert (saved / "cursor-bridge" / "MANIFEST.json").is_file()
    assert not (target / "cursor-bridge" / "old-only.md").exists(), "a file the new release does not ship is removed"
    assert (target / "cursor-bridge" / "review-guard.py").is_file()
    assert "previous       " + OLD_VERSION in out and "WARNING" not in out
    assert "way back       python %s --rollback" % NEW_INSTALLER.replace("\\", "/") in out, "the way back is the release folder's installer"
    s = settings_of(target)
    assert GUARD_RULE in s["permissions"]["allow"] and any("session-start.py" in c for c in hook_commands(s, "SessionStart"))


def test_rollback_restores_the_previous_release_and_only_what_was_the_bridges(tmp_path, installed_old_then_new):
    target, _ = installed_old_then_new
    rc, out = roll_back(tmp_path, target)
    assert rc == 0, out
    assert "rolling back %s -> %s" % (NEW_VERSION, OLD_VERSION) in out and "MATCHES bridge " + OLD_VERSION in out
    assert (target / "cursor-bridge" / "old-only.md").is_file(), "the old release's own file is back"
    assert not (target / "cursor-bridge" / "review-guard.py").exists(), "a file only the newer release shipped is gone"
    assert version_of(target) == OLD_VERSION
    s = settings_of(target)
    assert GUARD_RULE not in s["permissions"]["allow"], "an allow rule only the newer release added is taken out"
    assert not any("session-start.py" in c for c in hook_commands(s, "SessionStart")), "its hooks are taken out"
    assert any("loop-guard" in c for c in hook_commands(s, "Stop")), "a hook both releases have stays"
    assert s["switchModelsOnFlag"] is True and "Bash(ls:*)" in s["permissions"]["allow"]
    assert s["permissions"]["additionalDirectories"] == ["E:/somewhere"]
    assert "echo owner" in hook_commands(s, "PreToolUse"), "the owner's own hook stays"
    assert not (target / "cursor-bridge-previous").exists(), "the saved copy is used up once the check has passed"
    assert "If rolled back" in out
    note = (target / "cursor-bridge" / "ROLLED-BACK.md").read_text(encoding="utf-8")
    assert "# Rolled back: %s -> %s" % (NEW_VERSION, OLD_VERSION) in note
    assert "## " + NEW_VERSION in note and "Bridge version:" in note, "the newer release's own 'If rolled back' items are kept for calibration"
    rc, out = roll_back(tmp_path, target)
    assert rc == 2 and "nothing to roll back to" in out


def test_rollback_from_the_installed_copy_is_refused(tmp_path, installed_old_then_new):
    """The installed copy is replaced during a rollback; one that was interrupted could not
    be finished with it when the restored installer does not know the command (2026.10.04e)."""
    target, _ = installed_old_then_new
    rc, out = run(target / "cursor-bridge" / "bridge-install.py", tmp_path, "--rollback", "--target", str(target))
    assert rc == 2 and "release folder" in out and "Nothing was changed" in out, out
    assert version_of(target) == NEW_VERSION and (target / "cursor-bridge-previous" / OLD_VERSION).is_dir()


def test_reinstalling_after_a_rollback_works(tmp_path, installed_old_then_new):
    target, _ = installed_old_then_new
    rc, out = roll_back(tmp_path, target)
    assert rc == 0, out
    rc, out = install_new(tmp_path, target)
    assert rc == 0 and "MATCHES bridge " + NEW_VERSION in out, out
    assert (target / "cursor-bridge-previous" / OLD_VERSION / "cursor-bridge" / "old-only.md").is_file()
    assert GUARD_RULE in settings_of(target)["permissions"]["allow"]
    assert not (target / "cursor-bridge" / "ROLLED-BACK.md").exists(), "an install removes the stale note"


def test_reinstalling_the_same_version_keeps_the_saved_previous(tmp_path, installed_old_then_new):
    target, _ = installed_old_then_new
    rc, out = install_new(tmp_path, target)
    assert rc == 0, out
    assert (target / "cursor-bridge-previous" / OLD_VERSION).is_dir(), "a repeated install must not overwrite the way back"


def test_rollback_dry_run_changes_nothing(tmp_path, installed_old_then_new):
    target, _ = installed_old_then_new
    before = sorted(str(p.relative_to(target)) for p in target.rglob("*"))
    rc, out = roll_back(tmp_path, target, "--dry-run")
    assert rc == 0 and "(dry run)" in out
    assert sorted(str(p.relative_to(target)) for p in target.rglob("*")) == before
    assert version_of(target) == NEW_VERSION


@pytest.mark.skipif(sys.platform != "win32", reason="the shim is installed on Windows only")
def test_rollback_restores_the_previous_shim(tmp_path, old_release):
    cli = tmp_path / "localappdata" / "cursor-agent"
    cli.mkdir(parents=True)
    target = tmp_path / ".claude"
    assert install_old(tmp_path, old_release, target)[0] == 0
    assert install_new(tmp_path, target)[0] == 0
    assert b"# old release" not in (cli / "cursor-agent").read_bytes()
    rc, out = roll_back(tmp_path, target)
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


def test_the_installer_and_the_check_fingerprint_a_file_alike(tmp_path, program):
    f = tmp_path / "x.md"
    f.write_bytes(b"\xef\xbb\xbfone\r\ntwo\r\n")
    assert program("bridge-install").norm_hash(str(f)) == program("bridge-check").norm_hash(str(f))


def test_a_repeated_install_after_an_interruption_does_not_spoil_the_kept_copy(tmp_path, installed_old_then_new):
    """A run that died before the manifest was replaced leaves new files under the old
    manifest; saving that tree again as "the previous release" would spoil the way back."""
    target, _ = installed_old_then_new
    kept = target / "cursor-bridge-previous" / OLD_VERSION
    for name in ("MANIFEST.json", "VERSION"):
        shutil.copyfile(kept / "cursor-bridge" / name, target / "cursor-bridge" / name)
    rc, out = install_new(tmp_path, target)
    assert rc == 0 and "MATCHES bridge " + NEW_VERSION in out, out
    assert (kept / "cursor-bridge" / "old-only.md").is_file(), "the kept copy is the first one"
    assert (kept / "cursor-bridge" / "cursor-agent.shim").read_bytes().endswith(b"# old release\n")
    assert not (kept / "cursor-bridge" / "review-guard.py").exists()
    assert not any(p.name.endswith(".partial") for p in (target / "cursor-bridge-previous").iterdir())


def test_rollback_refuses_a_kept_copy_that_is_not_complete(tmp_path, installed_old_then_new):
    target, _ = installed_old_then_new
    (target / "cursor-bridge-previous" / OLD_VERSION / "commands" / "supervisor.md").unlink()
    before = settings_of(target)
    rc, out = roll_back(tmp_path, target)
    assert rc == 2 and "is not complete" in out and "commands/supervisor.md (missing)" in out, out
    assert version_of(target) == NEW_VERSION
    assert settings_of(target) == before and not (target / "cursor-bridge" / "ROLLED-BACK.md").exists()
    rc, out = run(target / "cursor-bridge" / "bridge-check.py", tmp_path, "--root", str(target))
    assert rc == 0, out


def test_a_file_changed_on_this_computer_is_named_when_kept_and_the_way_back_refuses_it(tmp_path, old_release):
    """The kept copy is the installed tree as it was. One that is not the release as shipped
    would come back as a mixture, so the install says so and the rollback changes nothing."""
    target = tmp_path / ".claude"
    assert install_old(tmp_path, old_release, target)[0] == 0
    with open(target / "commands" / "supervisor.md", "a", encoding="utf-8") as f:
        f.write("\nedited on this computer\n")
    rc, out = install_new(tmp_path, target)
    assert rc == 0 and "WARNING" in out and "commands/supervisor.md (changed)" in out, out
    rc, out = roll_back(tmp_path, target)
    assert rc == 2 and "not that release as shipped" in out and "commands/supervisor.md (changed)" in out, out
    assert version_of(target) == NEW_VERSION and (target / "cursor-bridge-previous" / OLD_VERSION).is_dir()
    assert not (target / "cursor-bridge" / "ROLLED-BACK.md").exists()


def test_the_kept_copy_stays_when_the_check_after_a_rollback_does_not_pass(tmp_path, installed_old_then_new, monkeypatch, capsys):
    target, _ = installed_old_then_new
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "localappdata"))
    bi = load_installer(RELEASE)
    with monkeypatch.context() as m:
        m.setattr(bi, "run_check", lambda target: 1)
        assert bi.rollback(str(target), False) == 1
    assert "the kept copy of %s stays" % OLD_VERSION in capsys.readouterr().out
    assert (target / "cursor-bridge-previous" / OLD_VERSION / "cursor-bridge" / "old-only.md").is_file()
    rc, out = roll_back(tmp_path, target)
    assert rc == 0 and "MATCHES bridge " + OLD_VERSION in out, out
    assert not (target / "cursor-bridge-previous").exists()


def test_installing_an_older_release_over_a_newer_one_takes_the_newer_entries_out(tmp_path, old_release):
    """Installing and taking back are one replacement: an install also removes the rules
    and hooks only the replaced release owned, so no hook is left to run a removed program."""
    target = tmp_path / ".claude"
    assert install_new(tmp_path, target)[0] == 0
    rc, out = install_old(tmp_path, old_release, target)
    assert rc == 0 and "MATCHES bridge " + OLD_VERSION in out, out
    s = settings_of(target)
    assert GUARD_RULE not in s["permissions"]["allow"] and not hook_commands(s, "SessionStart")
    assert not (target / "cursor-bridge" / "session-start.py").exists()
    assert (target / "cursor-bridge-previous" / NEW_VERSION / "cursor-bridge" / "session-start.py").is_file()
    rc, out = roll_back(tmp_path, target)
    assert rc == 0 and "MATCHES bridge " + NEW_VERSION in out, out
    assert any("session-start.py" in c for c in hook_commands(settings_of(target), "SessionStart"))


def test_a_program_an_owner_hook_runs_is_not_removed(tmp_path, old_release):
    """The guarantee covers every hook in settings.json, not only the bridge's own: a
    program the next release drops stays while a hook the owner wrote still runs it."""
    target = tmp_path / ".claude"
    assert install_new(tmp_path, target)[0] == 0
    s = settings_of(target)
    s["hooks"]["PostToolUse"] = [{"matcher": "Bash", "hooks": [{"type": "command", "command": 'python "$HOME/.claude/cursor-bridge/review-guard.py" snapshot 1'}]}]
    (target / "settings.json").write_text(json.dumps(s, indent=2), encoding="utf-8")
    rc, out = install_old(tmp_path, old_release, target)
    assert rc == 0 and "MATCHES bridge " + OLD_VERSION in out, out
    assert "kept           cursor-bridge/review-guard.py" in out and "EXTRA    cursor-bridge/review-guard.py" in out
    assert (target / "cursor-bridge" / "review-guard.py").is_file() and not (target / "cursor-bridge" / "session-start.py").exists()
    assert hooks_without_a_program(target) == []


def test_settings_of_an_unexpected_shape_are_refused_before_anything_changes(tmp_path, old_release):
    target = tmp_path / ".claude"
    assert install_old(tmp_path, old_release, target)[0] == 0
    for text, word in (('{"permissions": null}', "shape"), ('{"hooks": {"Stop": "x"}}', "shape"), ("{ not json", "not valid JSON")):
        (target / "settings.json").write_text(text, encoding="utf-8")
        rc, out = install_new(tmp_path, target)
        assert rc == 2 and word in out and "nothing was changed" in out and "Traceback" not in out, out
        assert version_of(target) == OLD_VERSION and not (target / "cursor-bridge-previous").exists()
        assert (target / "settings.json").read_text(encoding="utf-8") == text


def test_a_file_that_cannot_be_written_ends_in_a_sentence_and_the_run_can_be_repeated(tmp_path, old_release):
    target = tmp_path / ".claude"
    assert install_old(tmp_path, old_release, target)[0] == 0
    locked = target / "agents" / "diff-reviewer.md"
    os.chmod(locked, stat.S_IREAD)
    try:
        rc, out = install_new(tmp_path, target)
    finally:
        os.chmod(locked, stat.S_IREAD | stat.S_IWRITE)
    if rc == 0:
        pytest.skip("this account may write a read-only file")
    assert rc == 2 and "stopped, because a file could not be read or written" in out and "Traceback" not in out, out
    assert hooks_without_a_program(target) == []
    rc, out = install_new(tmp_path, target)
    assert rc == 0 and "MATCHES bridge " + NEW_VERSION in out, out
    assert (target / "cursor-bridge-previous" / OLD_VERSION / "cursor-bridge" / "old-only.md").is_file()


@pytest.mark.parametrize("direction", ["older over newer", "newer over older"])
@pytest.mark.parametrize("dies_in", ["write_settings", "remove_files", "copy_tree"])
def test_an_interrupted_replacement_never_leaves_a_hook_without_its_program(tmp_path, old_release, program, monkeypatch, direction, dies_in):
    """A hook that runs a missing program fails with exit status 2, which blocks its event
    in every session; so whatever step a replacement dies in, settings.json names only
    programs that are there."""
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "localappdata"))
    target = tmp_path / ".claude"
    first, second = (install_new, lambda: install_old(tmp_path, old_release, target)) if direction == "older over newer" else (None, lambda: install_new(tmp_path, target))
    assert (install_new(tmp_path, target) if first else install_old(tmp_path, old_release, target))[0] == 0
    assert hooks_without_a_program(target) == []
    source = str(old_release) if direction == "older over newer" else RELEASE
    bi = program("bridge-install")

    def dies(*args, **kwargs):
        raise OSError("the disk is full")
    existing, new_settings = bi.read_inputs(str(target), source)
    with monkeypatch.context() as m:
        m.setattr(bi, dies_in, dies)
        with pytest.raises(OSError):
            bi.replace_release(str(target), source, existing, new_settings, False)
    assert hooks_without_a_program(target) == []
    json.load(open(target / "settings.json", encoding="utf-8"))
    rc, out = second()
    assert rc == 0 and "RESULT: INSTALLED TREE MATCHES" in out, "the repeated run completes the replacement: " + out
    assert hooks_without_a_program(target) == []


@pytest.mark.parametrize("direction", ["older over newer", "newer over older"])
@pytest.mark.parametrize("nth", [1, 40, 98, 99, 140, 196])
def test_an_install_killed_at_the_nth_copied_file_can_be_repeated(tmp_path, old_release, monkeypatch, direction, nth):
    """The first hundred copies or so are the keeping of the previous release, the rest the
    replacement itself: stopped after any of them, the settings name no missing program, a
    kept copy is whole, and the same command finishes the install."""
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "localappdata"))
    target = tmp_path / ".claude"
    if direction == "newer over older":
        assert install_old(tmp_path, old_release, target)[0] == 0
        bi, kept_version, repeat = load_installer(RELEASE), OLD_VERSION, lambda: install_new(tmp_path, target)
    else:
        assert install_new(tmp_path, target)[0] == 0
        bi, kept_version, repeat = load_installer(old_release), NEW_VERSION, lambda: install_old(tmp_path, old_release, target)
    real, calls = bi.shutil.copyfile, [0]

    def copyfile(src, dst, **kwargs):
        calls[0] += 1
        if calls[0] == nth:
            raise OSError("killed at file %d" % nth)
        return real(src, dst, **kwargs)
    with monkeypatch.context() as m:
        m.setattr(bi.shutil, "copyfile", copyfile)
        try:
            bi.install(str(target), False, anyway=True)
        except OSError:
            pass
    assert hooks_without_a_program(target) == []
    json.load(open(target / "settings.json", encoding="utf-8"))
    kept = target / "cursor-bridge-previous" / kept_version
    marker = "old-only.md" if kept_version == OLD_VERSION else "session-start.py"
    assert not kept.is_dir() or (kept / "cursor-bridge" / marker).is_file()
    rc, out = repeat()
    assert rc == 0 and "RESULT: INSTALLED TREE MATCHES" in out and "WARNING" not in out, out
    assert hooks_without_a_program(target) == []
    assert (kept / "cursor-bridge" / marker).is_file(), "the way back is the release that was installed before, whole"
    assert bi.not_as_released(str(kept), bi.fingerprints_of(str(kept))[1]) == []


def test_a_rollback_killed_part_way_is_finished_with_the_release_folders_installer(tmp_path, program, monkeypatch):
    """Review finding 5: the release taken back to may have an installer that does not know
    --rollback (2026.10.04e). Once a rollback has restored that file, the installed copy
    cannot finish the rollback; the release folder's installer can, at any point."""
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "localappdata"))
    old = make_old_release(tmp_path / "old-release", program, installer=CANNOT_ROLL_BACK)
    target = tmp_path / ".claude"
    first = load_installer(RELEASE)
    first.RELEASE, first.HERE = str(old), str(old / "cursor-bridge")       # the old release cannot install itself
    assert first.install(str(target), False, anyway=True) == 0
    assert install_new(tmp_path, target)[0] == 0
    bi = load_installer(RELEASE)
    real, restored = bi.shutil.copyfile, []

    def copyfile(src, dst, **kwargs):
        if restored:
            raise OSError("killed after the installer was restored")
        if str(dst).endswith("bridge-install.py"):
            restored.append(dst)
        return real(src, dst, **kwargs)
    with monkeypatch.context() as m:
        m.setattr(bi.shutil, "copyfile", copyfile)
        with pytest.raises(OSError):
            bi.rollback(str(target), False)
    assert (target / "cursor-bridge" / "bridge-install.py").read_text(encoding="utf-8") == CANNOT_ROLL_BACK
    assert hooks_without_a_program(target) == []
    rc, out = roll_back(tmp_path, target)
    assert rc == 0 and "MATCHES bridge " + OLD_VERSION in out, out
    note = (target / "cursor-bridge" / "ROLLED-BACK.md").read_text(encoding="utf-8")
    assert "## " + NEW_VERSION in note, "the note written before the files changed survives the repeated run"
    assert not (target / "cursor-bridge-previous").exists()
