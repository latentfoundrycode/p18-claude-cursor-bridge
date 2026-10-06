"""permission-guard.py: refuses the override merge and every form of force-push, through
chains, wrappers and both shells; lets everything else through; fails open on bad input."""
import json
import os
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
PROG = os.path.join(HERE, os.pardir, "bridge", "cursor-bridge", "permission-guard.py")


SHA = "0123456789abcdef0123456789abcdef01234567"


def run(tool, command, cwd=None):
    payload = {"tool_name": tool, "tool_input": {"command": command}, "permission_mode": "auto"}
    if cwd:
        payload["cwd"] = str(cwd)
    p = subprocess.run([sys.executable, PROG], input=json.dumps(payload), capture_output=True, text=True)
    return p.returncode, p.stderr


@pytest.fixture
def recorded_repo(tmp_path):
    """A repository in which review-guard.py premerge has recorded SHA (the file it writes)."""
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
    folder = repo / ".git" / "bridge" / "premerge"
    folder.mkdir(parents=True)
    (folder / SHA).write_text('{"pr": 12}', encoding="utf-8")
    return repo


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
    "git worktree remove --force ../Worktrees/TASK-012",
    "git worktree remove -f ../Worktrees/TASK-012",
    "git worktree remove ../Worktrees/TASK-012 --force",
    "git -C Workspace worktree remove -ff ../Worktrees/TASK-012",
    "git worktree remove ../Worktrees/TASK-012",
    "git worktree remove --forc ../Worktrees/TASK-012",
    "& git worktree remove ../Worktrees/TASK-012",
    "bash -c 'git worktree remove --force ../Worktrees/TASK-012'",
    'cmd /c "git worktree remove ../Worktrees/TASK-012"',
    'powershell -Command "git worktree remove ../Worktrees/TASK-012"',
    "git -c alias.wr='worktree remove --force' wr ../Worktrees/TASK-012",
    "git push --forc origin main",
    "gh pr merge 12 --squash",
    "gh pr merge --squash --auto",
    "gh pr merge 12 --squash --delete-branch",
    'gh pr merge 12 --squash --match-head-commit ""',
    "gh pr merge 12 --squash --match-head-commit=",
    "gh pr merge 12 --squash --match-head-commit " + SHA,
    "& gh pr merge 12 --squash",
    "bash -c 'gh pr merge 12 --squash'",
    "gh api graphql -f query='mutation { mergePullRequest(input: {pullRequestId: \"x\"}) { clientMutationId } }'",
    "gh api graphql -f query='mutation { enablePullRequestAutoMerge(input: {pullRequestId: \"x\"}) { clientMutationId } }'",
    "gh api graphql -f query='mutation { enqueuePullRequest(input: {pullRequestId: \"x\"}) { clientMutationId } }'",
    "gh api graphql -F query=@merge.graphql",
    "gh api graphql --input merge.json",
    "cmd /c gh pr merge 12 --squash",
    "cmd /c git worktree remove ../Worktrees/TASK-012",
    "cmd.exe /C git worktree remove ../Worktrees/TASK-012",
    "powershell -Command gh pr merge 12 --squash",
    "powershell -Command git worktree remove ../Worktrees/TASK-012",
    "bash -lc 'gh pr merge 12 --squash'",
    "&gh pr merge 12 --squash",
    "&git worktree remove ../Worktrees/TASK-012",
    "git fetch & gh pr merge 12 --squash",
    "git status & git worktree remove ../Worktrees/TASK-012",
    'cmd /c "cd .. & git worktree remove Worktrees/TASK-012"',
    "{ git worktree remove ../Worktrees/TASK-012; }",
    "if true; then git worktree remove ../Worktrees/TASK-012; fi",
    "echo ../Worktrees/TASK-012 | xargs git worktree remove",
    "echo ../Worktrees/TASK-012 | xargs -n 1 git worktree remove",
    "git -c alias.wt=worktree wt remove ../Worktrees/TASK-012",
    "gh pr -R owner/repo merge 12 --squash",
    "gh pr merge 12 --squash --subject --help",
    "gh pr merge 12 --squash -t -h",
    "bash <<'EOF'\ngh pr merge 12 --squash\nEOF",
    "bash -s <<'EOF'\ngit worktree remove ../Worktrees/TASK-012\nEOF",
    "sh <<EOF\ngit worktree remove ../Worktrees/TASK-012\nEOF",
    "cmd <<EOF\ngit worktree remove ../Worktrees/TASK-012\nEOF",
    "powershell -Command - <<'EOF'\ngh pr merge 12 --squash\nEOF",
    "gh api -XPUT repos/o/r/pulls/12/merge",
    "gh api -X=PUT repos/o/r/pulls/12/merge",
    "echo ../Worktrees/TASK-012 | xargs -I % git worktree remove %",
    "nice -n 10 git worktree remove ../Worktrees/TASK-012",
    "timeout -s KILL 60 git worktree remove ../Worktrees/TASK-012",
    "powershell gh pr merge 12 --squash",
    "powershell -NoProfile -ExecutionPolicy Bypass gh pr merge 12 --squash",
    'powershell -com "gh pr merge 12 --squash"',
    ". gh pr merge 12 --squash",
    'bash -ce "gh pr merge 12 --squash"',
    "find ../Worktrees -maxdepth 1 -name 'TASK-*' -exec git worktree remove {} ;",
    'gh api graphql -f query="$(cat merge.graphql)"',
    "gh alias set pm 'pr merge'",
    "gh alias set -s m 'api graphql -f query=x'",
    "powershell -EncodedCommand ZwBoACAAcAByACAAbQBlAHIAZwBlAA==",
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
    "python ~/.claude/cursor-bridge/worktree-teardown.py ../Worktrees/TASK-012",
    "git worktree prune",
    "git worktree list",
    "git worktree add ../Worktrees/TASK-012 task-012",
    "git worktree remove --help",
    "gh pr merge 12 --disable-auto",
    "gh pr merge --help",
    "gh pr view 12",
    "gh api graphql -f query='query { repository(owner: \"o\", name: \"r\") { pullRequest(number: 12) { mergeable } } }'",
    "git push origin HEAD",
    "bash -c 'git status'",
    "gh pr merge 12 --squash --help",
    "git commit -F - <<'EOF'\nfix the guard\n\ngh pr merge 12 --squash is refused without the record\nEOF",
    'echo "a & b"',
    "python x.py 2>&1",
    "cmd /c echo agent",
    "powershell -NoProfile -Command Get-ChildItem",
    "powershell Get-ChildItem",
    "nice -n 10 python x.py",
    "timeout -s KILL 60 python x.py",
    "find . -name '*.pyc' -delete",
    "find . -name '*.log' -exec rm {} ;",
    "gh alias set co 'pr checkout'",
    "git commit -F - <<'EOF'\nfix\n\nbash <<EOF2 is not what this message runs\nEOF",
    "dist/agent.exe --version",
    "cmd /c dir agent",
    "pwsh -File build.ps1 agent",
    "echo agent",
    "git push -u origin task-012",
    "git push origin fix-123",
    "git push --follow-tags origin main",
    "git commit -m \"docs: never push with --force\"",
    "git commit -m 'why -f is forbidden'",
    "gh api repos/o/r/pulls/12/merge",
    "gh api repos/o/r/pulls/12 --jq .mergeable",
    "gh pr view 12 --json comments",
    "cursor-agent -p --force --model x \"Read handoff/TASK-012.md\"",
    "python ~/.claude/cursor-bridge/bridge-run.py --limit 7200 -- cursor-agent -p --force --model x \"Read handoff/TASK-012.md and implement; do not git push\"",
    "git fetch --force origin",
    "echo hello",
])
@pytest.mark.parametrize("tool", ["Bash", "PowerShell"])
def test_allowed(tool, cmd):
    rc, err = run(tool, cmd)
    assert rc == 0, (tool, cmd, err)


@pytest.mark.parametrize("tool", ["Bash", "PowerShell"])
def test_a_merge_with_the_premerge_record_passes_and_one_without_is_refused(tool, recorded_repo, tmp_path):
    """Review of 2026.10.06b, finding 3: the sha alone proves nothing; the record that
    review-guard.py premerge writes when it prints OK is the confirmation."""
    rc, err = run(tool, "gh pr merge 12 --squash --match-head-commit " + SHA, cwd=recorded_repo)
    assert rc == 0, err
    rc, err = run(tool, "gh pr merge 12 --squash --auto --match-head-commit " + SHA, cwd=recorded_repo)
    assert rc == 0, err
    rc, err = run(tool, "gh pr merge 12 --squash --match-head-commit " + SHA[:12], cwd=recorded_repo)
    assert rc == 0, "an abbreviated sha that matches the record passes: " + err
    other = "fedcba9876543210fedcba9876543210fedcba98"
    rc, err = run(tool, "gh pr merge 12 --squash --match-head-commit " + other, cwd=recorded_repo)
    assert rc == 2 and "premerge" in err, "a sha without a record is refused: " + err
    rc, err = run(tool, "gh pr merge 12 --squash --match-head-commit " + SHA, cwd=tmp_path)
    assert rc == 2, "outside the repository there is no record: " + err


def test_other_tools_and_bad_input_pass():
    p = subprocess.run([sys.executable, PROG], input=json.dumps({"tool_name": "Edit", "tool_input": {"file_path": "x"}}), capture_output=True, text=True)
    assert p.returncode == 0
    p = subprocess.run([sys.executable, PROG], input="not json", capture_output=True, text=True)
    assert p.returncode == 0
