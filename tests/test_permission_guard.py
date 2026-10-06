"""permission-guard.py: refuses the override merge and every form of force-push, through
chains, wrappers and both shells; lets everything else through; fails open on bad input."""
import json
import os
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
PROG = os.path.join(HERE, os.pardir, "bridge", "cursor-bridge", "permission-guard.py")


def run(tool, command):
    payload = {"tool_name": tool, "tool_input": {"command": command}, "permission_mode": "auto"}
    p = subprocess.run([sys.executable, PROG], input=json.dumps(payload), capture_output=True, text=True)
    return p.returncode, p.stderr


@pytest.mark.parametrize("cmd", [
    "git push --force origin main",
    "git push -f origin task-12",
    "git push origin main -f",
    "git push -fu origin task-12",
    "git push --force-with-lease",
    "git push --force-if-includes origin main",
    "git push --mirror",
    "git push origin +task-12",
    "git push origin +HEAD:main",
    "git -C . push --force",
    "git -C Workspace push origin +main",
    "timeout 30 git push --force",
    "cd Workspace && git push --force",
    "git status; git push -f",
    "FOO=1 git push --force",
    "gh pr merge 187 --squash --admin --delete-branch",
    "gh pr merge --admin 12",
    "cd x && gh pr merge 5 --squash --admin",
    "gh api -X PUT repos/o/r/pulls/12/merge -f merge_method=squash",
    "gh api --method PUT /repos/o/r/pulls/12/merge",
    'agent -p "do the task"',
    "agent.cmd -p x",
    "cursor-agent.cmd -p --force x",
    "C:/Users/o/AppData/Local/cursor-agent/cursor-agent.ps1 -p x",
    "cmd /c cursor-agent.cmd -p x",
    "powershell -NoProfile -Command agent -p x",
    "cd Workspace && agent -p x",
    "C:/Users/o/AppData/Local/cursor-agent/agent -p x",
    "pwsh -File C:/Users/o/AppData/Local/cursor-agent/cursor-agent.ps1 -p x",
    "gh api repos/o/r/pulls/12/merge -f merge_method=squash",
])
@pytest.mark.parametrize("tool", ["Bash", "PowerShell"])
def test_refused(tool, cmd):
    rc, err = run(tool, cmd)
    assert rc == 2 and "refused" in err, (tool, cmd, rc, err)


@pytest.mark.parametrize("cmd", [
    'cursor-agent -p --force "Read handoff/TASK-001.md"',
    "python ~/.claude/cursor-bridge/bridge-run.py --limit 7200 -- cursor-agent -p --force x",
    "ssh-agent -s",
    "git commit -m \"start the agent as agent.cmd\"",
    "./agent --help",
    "dist/agent.exe --version",
    "cmd /c dir agent",
    "pwsh -File build.ps1 agent",
    "echo agent",
    "git push -u origin task-012",
    "git push origin fix-123",
    "git push --follow-tags origin main",
    "git commit -m \"docs: never push with --force\"",
    "git commit -m 'why -f is forbidden'",
    "gh pr merge 12 --squash --auto",
    "gh pr merge 12 --squash",
    "gh api repos/o/r/pulls/12/merge",
    "gh api repos/o/r/pulls/12 --jq .mergeable",
    "gh pr view 12 --json comments",
    "cursor-agent -p --force --model x \"Read handoff/TASK-012.md\"",
    "python ~/.claude/cursor-bridge/bridge-run.py --limit 7200 -- cursor-agent -p --force --model x \"Read handoff/TASK-012.md and implement; do not git push\"",
    "git fetch --force origin",
    "git worktree remove ../Worktrees/TASK-012",
    "echo hello",
])
@pytest.mark.parametrize("tool", ["Bash", "PowerShell"])
def test_allowed(tool, cmd):
    rc, err = run(tool, cmd)
    assert rc == 0, (tool, cmd, err)


def test_other_tools_and_bad_input_pass():
    p = subprocess.run([sys.executable, PROG], input=json.dumps({"tool_name": "Edit", "tool_input": {"file_path": "x"}}), capture_output=True, text=True)
    assert p.returncode == 0
    p = subprocess.run([sys.executable, PROG], input="not json", capture_output=True, text=True)
    assert p.returncode == 0
