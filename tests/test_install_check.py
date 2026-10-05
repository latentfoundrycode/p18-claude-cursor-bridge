"""bridge-install.py and bridge-check.py: the owner's settings survive an install, the
bridge's entries are added once and retired ones removed, the shim is installed with a
backup, and the check verifies entries rather than bytes (KP-030). LOCALAPPDATA points at
a temporary folder in every run, so nothing touches the real profile (review F4)."""
import json
import os
import shutil
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
RELEASE = os.path.abspath(os.path.join(HERE, os.pardir, "bridge"))
INSTALL = os.path.join(RELEASE, "cursor-bridge", "bridge-install.py")
CHECK = os.path.join(RELEASE, "cursor-bridge", "bridge-check.py")
BRIDGE_SETTINGS = json.load(open(os.path.join(RELEASE, "cursor-bridge", "settings.bridge.json"), encoding="utf-8"))
SHIM_SRC = open(os.path.join(RELEASE, "cursor-bridge", "cursor-agent.shim"), "rb").read().replace(b"\r\n", b"\n")

OWNER_SETTINGS = {
    "switchModelsOnFlag": True,
    "fastMode": False,
    "modelSettings": {"claude-opus-4-8": {"effort": "high"}},
    "permissions": {"allow": ["Bash(ls:*)", "Bash(git status:*)", "Bash(npx --yes jscpd:*)"], "additionalDirectories": ["E:/somewhere"]},
    "hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [{"type": "command", "command": "echo hi"}]}]},
}


def run(prog, tmp_path, *args):
    env = dict(os.environ)
    env["LOCALAPPDATA"] = str(tmp_path / "localappdata")
    if prog == INSTALL:                       # the repository's tree is a checkout on a branch while the tests run
        args += ("--anyway",)
    p = subprocess.run([sys.executable, str(prog)] + list(args), capture_output=True, text=True, env=env)
    return p.returncode, p.stdout + p.stderr


def git(folder, *args):
    p = subprocess.run(["git", "-C", str(folder), "-c", "user.name=test", "-c", "user.email=test@example.invalid", "-c", "core.autocrlf=false",
                        "-c", "core.hooksPath=" + os.devnull, "-c", "commit.gpgsign=false"] + list(args), capture_output=True, text=True)
    assert p.returncode == 0, p.stdout + p.stderr
    return p.stdout.strip()


def test_merge_keeps_owner_keys_adds_bridge_entries_and_retires_old_ones(program):
    bi = program("bridge-install")
    merged, changes = bi.merge_settings(OWNER_SETTINGS, BRIDGE_SETTINGS)
    assert merged["switchModelsOnFlag"] is True and merged["modelSettings"] == OWNER_SETTINGS["modelSettings"]
    assert merged["permissions"]["additionalDirectories"] == ["E:/somewhere"]
    assert merged["permissions"]["allow"][:2] == ["Bash(ls:*)", "Bash(git status:*)"], "the owner's entries keep their place"
    assert "Bash(npx --yes jscpd:*)" not in merged["permissions"]["allow"], "a retired entry is removed"
    for entry in BRIDGE_SETTINGS["permissions"]["allow"]:
        assert entry in merged["permissions"]["allow"]
    for entry in BRIDGE_SETTINGS["permissions"]["deny"]:
        assert entry in merged["permissions"]["deny"]
    assert merged["hooks"]["PreToolUse"][0] == OWNER_SETTINGS["hooks"]["PreToolUse"][0], "the owner's hook group stays first"
    assert any("permission-guard" in h["command"] for g in merged["hooks"]["PreToolUse"] for h in g["hooks"])
    assert any("loop-guard" in h["command"] for g in merged["hooks"]["Stop"] for h in g["hooks"])
    assert changes
    again, changes2 = bi.merge_settings(merged, BRIDGE_SETTINGS)
    assert again == merged and changes2 == [], "a second merge changes nothing"


def test_install_into_a_fresh_target_passes_the_check(tmp_path):
    target = tmp_path / ".claude"
    rc, out = run(INSTALL, tmp_path, "--target", str(target))
    assert rc == 0, out
    assert (target / "commands" / "supervisor.md").is_file()
    assert (target / "cursor-bridge" / "permission-guard.py").is_file()
    assert "RESULT: INSTALLED TREE MATCHES" in out
    settings = json.load(open(target / "settings.json", encoding="utf-8"))
    assert settings["permissions"]["deny"] == BRIDGE_SETTINGS["permissions"]["deny"]
    assert not (tmp_path / "localappdata" / "cursor-agent").exists(), "no Cursor CLI folder, so no shim is written"


def test_install_over_owner_settings_keeps_them_and_backs_up(tmp_path):
    target = tmp_path / ".claude"
    target.mkdir()
    (target / "settings.json").write_text(json.dumps(OWNER_SETTINGS, indent=2), encoding="utf-8")
    rc, out = run(INSTALL, tmp_path, "--target", str(target))
    assert rc == 0, out
    settings = json.load(open(target / "settings.json", encoding="utf-8"))
    assert settings["switchModelsOnFlag"] is True and settings["permissions"]["additionalDirectories"] == ["E:/somewhere"]
    assert any(p.name.startswith("settings.json.bak-") for p in target.iterdir())
    assert "owner keys kept" in out and "(retired)" in out


@pytest.mark.skipif(sys.platform != "win32", reason="the shim is installed on Windows only")
def test_shim_is_installed_where_the_cli_lives_with_a_backup(tmp_path):
    cli = tmp_path / "localappdata" / "cursor-agent"
    cli.mkdir(parents=True)
    (cli / "cursor-agent").write_bytes(b'#!/bin/sh\ncursor-agent.cmd "$@"\n')      # the setup guide's one-liner
    rc, out = run(INSTALL, tmp_path, "--target", str(tmp_path / ".claude"))
    assert rc == 0, out
    assert (cli / "cursor-agent").read_bytes() == SHIM_SRC
    assert any(p.name.startswith("cursor-agent.bak-") for p in cli.iterdir()), "the previous shim is kept"
    assert "shim: installed" in out
    rc, out = run(CHECK, tmp_path, "--root", str(tmp_path / ".claude"))
    assert rc == 0 and "0 STALE" in out
    (cli / "cursor-agent").write_bytes(b"#!/bin/sh\necho tampered\n")
    rc, out = run(CHECK, tmp_path, "--root", str(tmp_path / ".claude"))
    assert rc == 1 and "cursor-agent shim" in out


def test_check_reports_missing_bridge_entry_and_ignores_owner_keys(tmp_path):
    target = tmp_path / ".claude"
    rc, out = run(INSTALL, tmp_path, "--target", str(target))
    assert rc == 0, out
    path = target / "settings.json"
    settings = json.load(open(path, encoding="utf-8"))
    settings["switchModelsOnFlag"] = True                      # an owner key: must not matter
    path.write_text(json.dumps(settings, indent=2), encoding="utf-8")
    rc, out = run(CHECK, tmp_path, "--root", str(target))
    assert rc == 0 and "owner keys kept: switchModelsOnFlag" in out, out
    settings["permissions"]["allow"].remove("Bash(cursor-agent:*)")
    path.write_text(json.dumps(settings, indent=2), encoding="utf-8")
    rc, out = run(CHECK, tmp_path, "--root", str(target))
    assert rc == 1 and "STALE    settings.json" in out and "Bash(cursor-agent:*)" in out, out


def test_check_reports_a_hook_that_runs_a_bridge_program_which_is_not_installed(tmp_path):
    """Such a hook fails with exit status 2, which Claude Code reads as "block"."""
    target = tmp_path / ".claude"
    rc, out = run(INSTALL, tmp_path, "--target", str(target))
    assert rc == 0, out
    path = target / "settings.json"
    settings = json.load(open(path, encoding="utf-8"))
    settings["hooks"]["PreToolUse"].append({"matcher": "Bash", "hooks": [
        {"type": "command", "command": 'python "$HOME/.claude/cursor-bridge/gone.py"'},
        {"type": "command", "command": "python my-own-hook.py"}]})
    path.write_text(json.dumps(settings, indent=2), encoding="utf-8")
    rc, out = run(CHECK, tmp_path, "--root", str(target))
    assert rc == 1 and "STALE    settings.json" in out and "PreToolUse runs gone.py" in out, out
    assert "my-own-hook" not in out, "the owner's own hooks are not the check's business"


def test_dry_run_writes_nothing(tmp_path):
    target = tmp_path / ".claude"
    rc, out = run(INSTALL, tmp_path, "--target", str(target), "--dry-run")
    assert rc == 0 and not target.exists(), out


def test_programs_survive_a_character_the_console_lacks(tmp_path):
    """Review R17: scope-check, plan-check and others crashed printing an arrow under cp1252."""
    target = tmp_path / ".claude"
    rc, out = run(INSTALL, tmp_path, "--target", str(target))
    assert rc == 0, out
    (target / "cursor-bridge" / "note \u2192 extra.md").write_text("x", encoding="utf-8")
    env = dict(os.environ, LOCALAPPDATA=str(tmp_path / "localappdata"), PYTHONIOENCODING="cp1252")
    p = subprocess.run([sys.executable, CHECK, "--root", str(target)], capture_output=True, text=True, env=env, errors="replace")
    assert "Traceback" not in p.stderr and "EXTRA" in p.stdout


def test_the_source_tree_is_checked_against_its_manifest_only(tmp_path):
    """Release A1a: the sources have no settings.json of their own; --sources checks the
    files against the manifest and skips what belongs to an installed machine."""
    rc, out = run(CHECK, tmp_path, "--root", RELEASE, "--sources", "--quiet")
    assert rc == 0 and "RESULT: SOURCES MATCH bridge" in out, out
    rc, out = run(CHECK, tmp_path, "--root", RELEASE, "--quiet")
    assert rc == 1 and "MISSING  settings.json" in out, "without --sources a tree without settings.json is not an installed bridge"


def test_an_unlisted_file_fails_the_check_of_a_source_tree(tmp_path):
    """It would be installed, never kept as part of a previous release and never removed."""
    tree = tmp_path / "bridge"
    shutil.copytree(RELEASE, tree, ignore=shutil.ignore_patterns("__pycache__"))
    (tree / "cursor-bridge" / "left-behind.md").write_text("x", encoding="utf-8")
    rc, out = run(tree / "cursor-bridge" / "bridge-check.py", tmp_path, "--root", str(tree), "--sources", "--quiet")
    assert rc == 1 and "EXTRA    cursor-bridge/left-behind.md" in out and "SOURCES DO NOT MATCH" in out, out


def test_a_folder_that_is_not_the_release_as_stamped_is_not_installed(tmp_path):
    tree = tmp_path / "bridge"
    shutil.copytree(RELEASE, tree, ignore=shutil.ignore_patterns("__pycache__"))
    target = tmp_path / ".claude"
    (tree / "cursor-bridge" / "left-behind.md").write_text("x", encoding="utf-8")
    rc, out = run(tree / "cursor-bridge" / "bridge-install.py", tmp_path, "--target", str(target), "--anyway")
    assert rc == 2 and "left-behind.md (not in the manifest)" in out and not target.exists(), out
    (tree / "cursor-bridge" / "left-behind.md").unlink()
    with open(tree / "commands" / "supervisor.md", "a", encoding="utf-8") as f:
        f.write("\nedited after the stamp\n")
    rc, out = run(tree / "cursor-bridge" / "bridge-install.py", tmp_path, "--target", str(target), "--anyway")
    assert rc == 2 and "commands/supervisor.md (changed)" in out and "as stamped" in out and not target.exists(), out
    (tree / "cursor-bridge" / "MANIFEST.json").unlink()
    rc, out = run(tree / "cursor-bridge" / "bridge-install.py", tmp_path, "--target", str(target))
    assert rc == 2 and "no readable manifest" in out and not target.exists(), out


def test_a_checkout_is_installed_only_as_main_as_merged(tmp_path):
    """Review finding 1: the install check passes on any stamped branch, so nothing else
    would tell a merged release from one still under review."""
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    shutil.copytree(RELEASE, repo / "bridge", ignore=shutil.ignore_patterns("__pycache__"))
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "a release")
    git(repo, "update-ref", "refs/remotes/origin/main", "HEAD")
    installer, target = repo / "bridge" / "cursor-bridge" / "bridge-install.py", tmp_path / ".claude"
    git(repo, "switch", "-q", "-c", "work")
    rc, out = run(installer, tmp_path, "--target", str(target))
    assert rc == 2 and "it is on 'work', not on main" in out and "nothing was changed" in out and not target.exists(), out
    git(repo, "switch", "-q", "main")
    git(repo, "commit", "-q", "--allow-empty", "-m", "never merged")
    rc, out = run(installer, tmp_path, "--target", str(target))
    assert rc == 2 and "differs from origin/main" in out and not target.exists(), out
    git(repo, "reset", "-q", "--hard", "origin/main")
    manifest = repo / "bridge" / "cursor-bridge" / "MANIFEST.json"
    manifest.write_bytes(manifest.read_bytes() + b"\n")
    rc, out = run(installer, tmp_path, "--target", str(target))
    assert rc == 2 and "not committed" in out and not target.exists(), "a change the fingerprints do not see (the manifest itself) is still not the merged state: " + out
    git(repo, "checkout", "-q", "--", ".")
    rc, out = run(installer, tmp_path, "--target", str(target))
    assert rc == 0 and "RESULT: INSTALLED TREE MATCHES" in out, out
    git(repo, "switch", "-q", "work")
    rc, out = run(installer, tmp_path, "--target", str(target), "--anyway")
    assert rc == 0, "the maintainer's rehearsals install a branch on purpose: " + out


def test_the_stamp_program_writes_nothing_for_an_argument_it_does_not_know():
    """The reviewer of 2026.10.05a ran it with --help to read its usage, and it stamped."""
    stamp = os.path.join(RELEASE, os.pardir, "tools", "make-manifest.py")
    manifest = os.path.join(RELEASE, "cursor-bridge", "MANIFEST.json")
    before = open(manifest, "rb").read()
    for args in (["--help"], ["--version"], ["--dry-run", "--version", "2026.01.01a"]):
        p = subprocess.run([sys.executable, stamp] + args, capture_output=True, text=True)
        assert p.returncode == 2 and "nothing was written" in p.stdout, p.stdout + p.stderr
    assert open(manifest, "rb").read() == before
