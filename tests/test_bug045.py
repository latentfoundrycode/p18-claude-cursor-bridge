"""BUG-045 (R-082): a -h or --help word anywhere among git's words exempts every git refusal of the permission guard.

The supervisor's reproduction tests, written before the builder's run (docs/debug/BUG-045.md). Each runs
permission-guard.py as the hook runs it (the hook's JSON on standard input, the Bash tool), from a scratch folder that
is no bridge Workspace, and reads the exit code (2 refuses, 0 lets through) and the reason on standard error.

The cause: permission-guard.py sets `helpful = "--help" in w[1:] or "-h" in w[1:]` and skips the hooksPath, hook-skipper,
force-push and worktree-removal refusals when it holds, though git reads a help word as its help option only where it
stands as an option of its own; as an option's value (`-m -h`, `-o -h`) or after `--` it is an argument, and git does
what the rest of the command says. The premise test below shows git committing with its hooks skipped under such a form.

enforces: docs/DESIGN.md, "Change: the program release", "The permission guard, permission-guard.py (C5)"; R-082;
docs/INVENTORY.md, Decisions, the permission guard's threat-model row (a refused action named in the command's own words).
"""
import json
import os
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
PROG = os.path.join(HERE, os.pardir, "bridge", "cursor-bridge", "permission-guard.py")


def guard(command, cwd):
    payload = {"tool_name": "Bash", "tool_input": {"command": command}, "permission_mode": "auto", "cwd": str(cwd)}
    p = subprocess.run([sys.executable, PROG], input=json.dumps(payload), capture_output=True, text=True, timeout=120, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    return p.returncode, p.stderr


@pytest.fixture
def plain(tmp_path):
    """A folder that is no bridge Workspace."""
    d = tmp_path / "plain"
    d.mkdir()
    return d


# A help word that git reads as an argument: an option's value, or a word after `--`. Each is refused (red on b05fbc8).
HELP_AS_AN_ARGUMENT = [
    ("commit-no-verify-message-h", "git commit --no-verify -a -m -h", "--no-verify"),
    ("commit-no-verify-message-help", "git commit --no-verify -a -m --help", "--no-verify"),
    ("commit-n-message-h", "git commit -n -a -m -h", "-n"),
    ("commit-no-verify-pathspec-h-after-dashdash", "git commit --no-verify -m x -- -h", "--no-verify"),
    ("commit-hookspath-message-h", "git -c core.hooksPath=/dev/null commit -m -h", "core.hooksPath"),
    ("push-force-push-option-h", "git push --force -o -h origin main", "--force"),
    ("push-force-help-after-dashdash", "git push --force -- --help", "--force"),
    ("worktree-remove-help-after-dashdash", "git worktree remove -- --help", "worktree remove"),
    ("worktree-remove-h-after-dashdash", "git worktree remove -- -h", "worktree remove"),
]


@pytest.mark.parametrize("command,reason", [(c, r) for _, c, r in HELP_AS_AN_ARGUMENT], ids=[n for n, _, _ in HELP_AS_AN_ARGUMENT])
def test_bug045_a_help_word_git_reads_as_an_argument_exempts_no_refusal(plain, command, reason):
    rc, err = guard(command, plain)
    assert rc == 2 and "refused" in err and reason in err, (command, rc, err)


# A lone help word after the subcommand is git's help option: git prints its help and does nothing else. Each passes.
HELP_CALLS = [
    ("worktree-remove-help", "git worktree remove --help"),
    ("worktree-remove-h", "git worktree remove -h"),
    ("commit-h", "git commit -h"),
    ("commit-help", "git commit --help"),
    ("push-help", "git push --help"),
    ("push-h", "git push -h"),
]


@pytest.mark.parametrize("command", [c for _, c in HELP_CALLS], ids=[n for n, _ in HELP_CALLS])
def test_bug045_a_lone_help_word_after_the_subcommand_still_passes(plain, command):
    rc, err = guard(command, plain)
    assert rc == 0, (command, rc, err)


def test_bug045_premise_git_takes_a_help_word_as_the_message_and_skips_the_hooks(tmp_path):
    """The premise of the defect, on git itself: a failing pre-commit hook stops `-m x`, and `--no-verify -m -h` commits."""
    repo = str(tmp_path / "repo")

    def git(*args):
        return subprocess.run(["git", "-C", repo, "-c", "core.hooksPath=.git/hooks", "-c", "user.email=probe@example.invalid", "-c", "user.name=probe"] + list(args), capture_output=True, text=True, timeout=60, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))

    os.makedirs(repo)
    assert git("init", "-q").returncode == 0
    with open(os.path.join(repo, "a.txt"), "w") as fh:
        fh.write("1\n")
    git("add", "a.txt")
    assert git("commit", "-q", "--no-verify", "-m", "base").returncode == 0
    hook = os.path.join(repo, ".git", "hooks", "pre-commit")
    with open(hook, "w", newline="\n") as fh:
        fh.write("#!/bin/sh\nexit 1\n")
    os.chmod(hook, 0o755)
    with open(os.path.join(repo, "a.txt"), "a") as fh:
        fh.write("2\n")
    assert git("commit", "-a", "-m", "x").returncode != 0, "the hook did not stop the commit"
    assert git("commit", "-a", "--no-verify", "-m", "-h").returncode == 0
    assert git("log", "-1", "--format=%s").stdout.strip() == "-h"


# ---------------------------------------------------------------- the builder adds its cases below this line and edits nothing above it
