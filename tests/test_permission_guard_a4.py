"""permission-guard.py (release A4, 13.1 and the 2026.10.06a review's S2): inside a bridge Workspace a
chain of commands carrying a state-changing git or gh command, or a command wrapped in cd, is
refused (rule 8); a commit that skips its checks is refused; a wrapper's quoted string is read."""
import json
import os
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
PROG = os.path.join(HERE, os.pardir, "bridge", "cursor-bridge", "permission-guard.py")


def run(command, cwd=None, tool="Bash"):
    payload = {"tool_name": tool, "tool_input": {"command": command}, "permission_mode": "auto"}
    if cwd:
        payload["cwd"] = str(cwd)
    p = subprocess.run([sys.executable, PROG], input=json.dumps(payload), capture_output=True, text=True)
    return p.returncode, p.stderr


@pytest.fixture
def workspace(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "PROJECT_STATUS.md").write_text("Phase: building\n", encoding="utf-8")
    return tmp_path


@pytest.mark.parametrize("command", [
    "git add -A && git commit -m 'TASK-001' && git push",
    "git add -A; git commit -m x",
    "cd ../Worktrees/TASK-001 && git commit -am x",
    "cd src && python build.py",
    "git switch main || git checkout main",
    "bash -c 'git add -A && git commit -m x'",
    "gh pr create -t x -b y && gh pr merge 5 --match-head-commit abc",
])
def test_a_chain_carrying_a_state_change_is_refused_inside_a_workspace(workspace, command):
    rc, err = run(command, workspace)
    assert rc == 2 and "rule 8" in err, (command, err)


@pytest.mark.parametrize("command", [
    "git log --oneline | head -5",
    "git status --porcelain && git diff --stat",
    "python -m pytest tests -q",
    "python a.py && python b.py",
    "gh pr view 5 --json state && gh pr checks 5",
])
def test_reading_chains_and_plain_commands_pass(workspace, command):
    rc, err = run(command, workspace)
    assert rc == 0, (command, err)


def test_outside_a_workspace_chains_are_not_the_guards_business(tmp_path):
    rc, err = run("git add -A && git commit -m x", tmp_path)
    assert rc == 0, err


@pytest.mark.parametrize("command", [
    "git commit --no-verify -m x",
    "git commit -n -m x",
    "git -c core.hooksPath=/dev/null commit -m x",
    "git push --no-verify origin task-001",
    "powershell -Command \"git commit --no-verify -m x\"",
])
def test_a_commit_that_skips_its_checks_is_refused(tmp_path, command):
    rc, err = run(command, tmp_path)
    assert rc == 2 and ("skips its checks" in err or "hooksPath" in err), (command, err)


@pytest.mark.parametrize("command", [
    "git push -n origin task-001",
    'git commit --no-verify -m "checkpoint before TASK-001"',
    'git commit --no-verify --message="checkpoint before TASK-001"',
    "git commit --no-verify -m \"$(cat <<'EOF'\ncheckpoint before TASK-003\n\nthe tree as delegated\nEOF\n)\"",
    'git -C ../Worktrees/TASK-001 commit --no-verify -m "TASK-001 builder hand-off"',
])
def test_the_snapshots_the_policy_allows_and_a_dry_run_pass(tmp_path, command):
    """The pre-delegation checkpoint (its exact subject, in any of the app's commit forms) and a builder's hand-off
    snapshot inside a worktree may skip the hook (merge policy); the accept commit on top runs it."""
    rc, err = run(command, tmp_path)
    assert rc == 0, (command, err)


@pytest.mark.parametrize("command", [
    'git commit -n -m "checkpoint: accept TASK-003 with the increment"',
    'git commit -n -m "TASK-003 accept, hand-off to review"',
    'git commit --no-verify -m "TASK-001 builder hand-off"',
    "HUSKY=0 git commit -m x",
    "git config core.hooksPath /dev/null",
    "git config --unset core.hooksPath",
])
def test_the_words_alone_do_not_open_the_exemption(tmp_path, command):
    """First pass, F6 and F14: the exemption is the policy's exact subject, the hand-off only inside a worktree;
    the hook runner's own switches are refused too."""
    rc, err = run(command, tmp_path)
    assert rc == 2, (command, err)


@pytest.mark.parametrize("command", [
    'gh pr create --title "TASK-003 parser" \\\n  --body "text"',
    'git commit -m "x" \\\n  -m "y"',
    "git branch --show-current && git status --short",
    "git worktree list && git status",
    "git stash list && git status",
    "git tag -l && git fetch origin",
    "git config core.hooksPath .githooks",
])
def test_continued_lines_and_read_forms_pass(workspace, command):
    """First pass, F5 and F13: a line continued with a backslash is one command; the read forms of branch, stash,
    worktree, tag and fetch are reads."""
    rc, err = run(command, workspace)
    assert rc == 0, (command, err)


@pytest.mark.parametrize("command", [
    "git add -A & git commit -m x",
    "(git add -A) && (git commit -m x)",
    'eval "git add -A && git commit -m x"',
])
def test_the_remaining_chain_spellings_are_refused(workspace, command):
    """First pass, F14: a single &, parentheses and eval do not hide a chain."""
    rc, err = run(command, workspace)
    assert rc == 2 and "rule 8" in err, (command, err)


@pytest.mark.parametrize("command", [
    'cmd /c "git push --force origin main"',
    'powershell -Command "git push --force origin main"',
    'bash -c "git push -f origin main"',
    "bash -lc 'git worktree remove ../Worktrees/x'",
])
def test_a_wrappers_quoted_string_is_read(tmp_path, command):
    rc, err = run(command, tmp_path)
    assert rc == 2, (command, err)
