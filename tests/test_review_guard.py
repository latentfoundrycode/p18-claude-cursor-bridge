"""review-guard.py (0b review, finding 2): the checkpoint Review B runs on is snapshotted,
verified and restored; a moved HEAD, a commit, a new ref, a changed .git/config or .env is a
gate-integrity flag; the merge head must descend from the reviewed head."""
import os
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
PROG = os.path.join(HERE, os.pardir, ".claude", "cursor-bridge", "review-guard.py")
ENV = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@x", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@x",
           GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_SYSTEM=os.devnull)


def git(repo, *args):
    p = subprocess.run(["git"] + list(args), cwd=repo, capture_output=True, text=True, env=ENV)
    assert p.returncode == 0, p.stderr
    return p.stdout.strip()


def guard(repo, *args):
    p = subprocess.run([sys.executable, PROG] + list(args), cwd=repo, capture_output=True, text=True, env=ENV)
    return p.returncode, p.stdout


@pytest.fixture
def repo(tmp_path):
    r = tmp_path / "ws"
    r.mkdir()
    git(r, "init", "-q", "-b", "main")
    (r / ".gitignore").write_text(".env\nparked/\n", encoding="utf-8")
    (r / "a.py").write_text("x = 1\n", encoding="utf-8")
    (r / "run" / "review").mkdir(parents=True)
    (r / "run" / "review" / "REVIEW-001.diff").write_text("diff\n", encoding="utf-8")
    (r / ".env").write_text("KEY=1\n", encoding="utf-8")
    git(r, "add", "-A")
    git(r, "commit", "-q", "-m", "base")
    git(r, "checkout", "-q", "-b", "task-001")
    (r / "a.py").write_text("x = 2\n", encoding="utf-8")
    git(r, "commit", "-q", "-am", "TASK-001")
    return r


def test_snapshot_refuses_a_dirty_tree(repo):
    (repo / "a.py").write_text("dirty\n", encoding="utf-8")
    rc, out = guard(repo, "snapshot", "001")
    assert rc == 2 and "not clean" in out


def test_clean_review_is_ok_and_leftovers_are_restored(repo):
    rc, out = guard(repo, "snapshot", "001")
    assert rc == 0 and "snapshot" in out
    (repo / "a.py").write_text("mutated for a check\n", encoding="utf-8")       # a temporary mutation
    (repo / "repro.py").write_text("print(1)\n", encoding="utf-8")              # a throwaway reproduction
    rc, out = guard(repo, "verify", "001")
    assert rc == 0, out
    assert "OK" in out and "restored:" in out and "repro.py" in out
    assert (repo / "a.py").read_text(encoding="utf-8") == "x = 2\n" and not (repo / "repro.py").exists()


def test_a_commit_during_the_review_is_a_flag_and_head_is_put_back(repo):
    guard(repo, "snapshot", "001")
    sha = git(repo, "rev-parse", "HEAD")
    (repo / "a.py").write_text("x = 3\n", encoding="utf-8")
    git(repo, "commit", "-q", "-am", "reviewer commit")
    rc, out = guard(repo, "verify", "001")
    assert rc == 1 and "HEAD moved" in out
    assert git(repo, "rev-parse", "HEAD") == sha and git(repo, "symbolic-ref", "HEAD") == "refs/heads/task-001"


def test_a_checkout_of_another_branch_is_a_flag_and_does_not_move_that_branch(repo):
    guard(repo, "snapshot", "001")
    main_sha = git(repo, "rev-parse", "main")
    task_sha = git(repo, "rev-parse", "HEAD")
    git(repo, "checkout", "-q", "main")                                        # "does it fail on the base too?"
    rc, out = guard(repo, "verify", "001")
    assert rc == 1 and "branch changed" in out
    assert git(repo, "rev-parse", "main") == main_sha, "local main must not move"
    assert git(repo, "rev-parse", "HEAD") == task_sha and git(repo, "symbolic-ref", "HEAD") == "refs/heads/task-001"


def test_a_new_ref_or_stash_is_a_flag(repo):
    guard(repo, "snapshot", "001")
    git(repo, "tag", "reviewer-tag")
    rc, out = guard(repo, "verify", "001")
    assert rc == 1 and "new ref" in out and "refs/tags/reviewer-tag" in out


def test_a_changed_git_config_is_a_flag_and_git_is_not_run(repo):
    guard(repo, "snapshot", "001")
    with open(repo / ".git" / "config", "a", encoding="utf-8") as f:
        f.write("[core]\n\tfsmonitor = evil\n")
    (repo / "a.py").write_text("still dirty\n", encoding="utf-8")
    rc, out = guard(repo, "verify", "001")
    assert rc == 1 and ".git/config changed" in out and "NOT restored" in out
    assert (repo / "a.py").read_text(encoding="utf-8") == "still dirty\n", "nothing may run git before the config is inspected"


def test_env_change_is_a_flag_and_other_ignored_leftovers_are_noted(repo):
    guard(repo, "snapshot", "001")
    (repo / "parked").mkdir()
    (repo / "parked" / "x.txt").write_text("parked\n", encoding="utf-8")
    rc, out = guard(repo, "verify", "001")
    assert rc == 0 and "LEFT BEHIND" in out and "parked/" in out
    guard(repo, "snapshot", "002")
    with open(repo / ".env", "a", encoding="utf-8") as f:
        f.write("MORE=2\n")
    rc, out = guard(repo, "verify", "002")
    assert rc == 1 and ".env changed" in out


def test_premerge_accepts_only_the_review_files_removal(repo):
    guard(repo, "snapshot", "001")
    git(repo, "rm", "-q", "run/review/REVIEW-001.diff")
    git(repo, "commit", "-q", "-m", "remove review files")
    rc, out = guard(repo, "premerge", "001")
    assert rc == 0 and "differs only under run/review/" in out
    (repo / "a.py").write_text("x = 9\n", encoding="utf-8")
    git(repo, "commit", "-q", "-am", "sneaked in")
    rc, out = guard(repo, "premerge", "001")
    assert rc == 1 and "a.py" in out


def test_premerge_rejects_a_head_that_does_not_descend_from_the_reviewed_one(repo):
    guard(repo, "snapshot", "001")
    git(repo, "reset", "-q", "--hard", "HEAD~1")
    (repo / "b.py").write_text("y\n", encoding="utf-8")
    git(repo, "add", "b.py")
    git(repo, "commit", "-q", "-m", "rewritten history")
    rc, out = guard(repo, "premerge", "001")
    assert rc == 1 and "does not descend" in out


def test_missing_snapshot_cannot_verify(repo):
    rc, out = guard(repo, "verify", "009")
    assert rc == 2 and "no snapshot" in out
