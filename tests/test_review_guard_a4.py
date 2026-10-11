"""review-guard.py (release A4, the plan review's second pass P3): verify never rewinds a branch that
another checkout holds. When the recorded branch has moved to another worktree during the review,
the restore stops with GATE-INTEGRITY before any reset, and the branch the checkout is on now keeps
its commit."""
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
PROG = os.path.join(HERE, os.pardir, "bridge", "cursor-bridge", "review-guard.py")
ENV = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.invalid", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@example.invalid")


def git(repo, *args):
    p = subprocess.run(["git"] + list(args), cwd=str(repo), capture_output=True, text=True, env=ENV)
    assert p.returncode == 0, p.stderr
    return p.stdout.strip()


def guard(repo, *args):
    p = subprocess.run([sys.executable, PROG] + list(args), cwd=str(repo), capture_output=True, text=True, env=ENV)
    return p.returncode, p.stdout + p.stderr


def test_verify_never_rewinds_a_branch_another_checkout_holds(tmp_path):
    r = tmp_path / "ws"
    r.mkdir()
    git(r, "init", "-q", "-b", "main")
    (r / ".gitignore").write_text("run/\n", encoding="utf-8")
    (r / "a.py").write_text("x = 1\n", encoding="utf-8")
    git(r, "add", "-A")
    git(r, "commit", "-q", "-m", "base")
    git(r, "checkout", "-q", "-b", "task-001")
    (r / "a.py").write_text("x = 2\n", encoding="utf-8")
    git(r, "commit", "-q", "-am", "TASK-001")
    (r / "run" / "review").mkdir(parents=True)
    rc, out = guard(r, "snapshot", "001")
    assert rc == 0, out
    stamp = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(time.time() + 1))
    (r / "run" / "review" / "REVIEW-001.err").write_text("bridge-run: started %sZ\nreview\nbridge-run: exit 0\n" % stamp, encoding="utf-8")
    # during the review the checkout moved to another branch, and task-001 was taken by a second worktree
    git(r, "checkout", "-q", "-b", "other")
    (r / "a.py").write_text("x = 3\n", encoding="utf-8")
    git(r, "commit", "-q", "-am", "work on other")
    other_head = git(r, "rev-parse", "other")
    wt = tmp_path / "wt"
    git(r, "worktree", "add", "-q", str(wt), "task-001")
    task_head = git(r, "rev-parse", "task-001")
    rc, out = guard(r, "verify", "001")
    assert rc == 1 and "GATE-INTEGRITY" in out and "another" in out and "wt" in out, out
    assert git(r, "rev-parse", "other") == other_head, "the branch the checkout was on was rewound (P3): " + out
    assert git(r, "rev-parse", "task-001") == task_head, out
    assert git(r, "symbolic-ref", "-q", "HEAD") == "refs/heads/other", "the checkout was moved although the restore was refused"
    git(r, "worktree", "remove", str(wt))
