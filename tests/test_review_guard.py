"""review-guard.py (0b review, finding 2 and its second pass S2-S7): the checkpoint Review B
runs on is snapshotted, verified and restored; a moved HEAD, a commit, a new or moved local
ref, a changed .git/config, hook, .env or ignored record is a gate-integrity flag; the guard
never runs a hook of the repository; the launcher's .err file survives; the merge head must
descend from the reviewed head."""
import os
import re
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
PROG = os.path.join(HERE, os.pardir, "bridge", "cursor-bridge", "review-guard.py")
ENV = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@x", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@x",
           GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_SYSTEM=os.devnull)
HOOK = "#!/bin/sh\necho ran > \"$(git rev-parse --show-toplevel)/HOOK-RAN\"\n"


def git(repo, *args):
    p = subprocess.run(["git"] + list(args), cwd=repo, capture_output=True, text=True, env=ENV)
    assert p.returncode == 0, p.stderr
    return p.stdout.strip()


def guard(repo, *args):
    p = subprocess.run([sys.executable, PROG] + list(args), cwd=repo, capture_output=True, text=True, env=ENV)
    return p.returncode, p.stdout


@pytest.fixture
def repo(tmp_path):
    """A checkout like the projects': core.hooksPath=.githooks (tracked), .env and run/ ignored,
    a gitignored record, a task branch off main."""
    r = tmp_path / "ws"
    r.mkdir()
    git(r, "init", "-q", "-b", "main")
    git(r, "config", "core.hooksPath", ".githooks")
    (r / ".gitignore").write_text(".env\nrun/\ndocs/RUN_PARAMETERS.md\nparked/\n", encoding="utf-8")
    (r / ".githooks").mkdir()
    (r / ".githooks" / "pre-commit").write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    (r / "a.py").write_text("x = 1\n", encoding="utf-8")
    (r / "docs").mkdir()
    (r / "docs" / "DESIGN.md").write_text("design\n", encoding="utf-8")
    (r / "docs" / "RUN_PARAMETERS.md").write_text("Merge authority: owner\n", encoding="utf-8")
    (r / "run" / "review").mkdir(parents=True)
    (r / "run" / "hold").mkdir()
    (r / "run" / "hold" / "test_x.py").write_text("parked test\n", encoding="utf-8")
    (r / ".env").write_text("KEY=1\n", encoding="utf-8")
    git(r, "add", "-A")
    git(r, "commit", "-q", "-m", "base")
    git(r, "checkout", "-q", "-b", "task-001")
    (r / "a.py").write_text("x = 2\n", encoding="utf-8")
    (r / "run" / "review" / "REVIEW-001.diff").write_text("diff\n", encoding="utf-8")
    git(r, "add", "-f", "run/review/REVIEW-001.diff")
    git(r, "commit", "-q", "-am", "TASK-001")
    return r


def test_snapshot_refuses_a_dirty_tree(repo):
    (repo / "a.py").write_text("dirty\n", encoding="utf-8")
    rc, out = guard(repo, "snapshot", "001")
    assert rc == 2 and "not clean" in out


def test_clean_review_is_ok_leftovers_restored_and_hash_printed_twice(repo):
    rc, out = guard(repo, "snapshot", "001")
    assert rc == 0 and "snapshot" in out
    h1 = re.search(r"snapshot hash ([0-9a-f]{16})", out).group(1)
    (repo / "a.py").write_text("mutated for a check\n", encoding="utf-8")       # a temporary mutation
    (repo / "repro.py").write_text("print(1)\n", encoding="utf-8")              # a throwaway reproduction
    (repo / "run" / "review" / "REVIEW-001.err").write_text("bridge-run: started 2026-10-04T10:00:00Z\nmore\n", encoding="utf-8")
    rc, out = guard(repo, "verify", "001")
    assert rc == 0, out
    assert "OK" in out and "restored:" in out and "repro.py" in out
    assert re.search(r"snapshot hash ([0-9a-f]{16})", out).group(1) == h1
    assert (repo / "a.py").read_text(encoding="utf-8") == "x = 2\n" and not (repo / "repro.py").exists()
    # S4: the launcher's own .err file survives and its first line is printed
    assert (repo / "run" / "review" / "REVIEW-001.err").exists()
    assert "launch time line kept" in out and "bridge-run: started 2026-10-04T10:00:00Z" in out


def test_a_commit_during_the_review_is_a_flag_and_head_is_put_back(repo):
    guard(repo, "snapshot", "001")
    sha = git(repo, "rev-parse", "HEAD")
    (repo / "a.py").write_text("x = 3\n", encoding="utf-8")
    git(repo, "commit", "-q", "-am", "reviewer commit")
    rc, out = guard(repo, "verify", "001")
    assert rc == 1 and "HEAD moved" in out
    assert git(repo, "rev-parse", "HEAD") == sha and git(repo, "symbolic-ref", "HEAD") == "refs/heads/task-001"


def test_a_commit_on_main_is_flagged_and_main_is_repaired(repo):
    guard(repo, "snapshot", "001")
    main_sha = git(repo, "rev-parse", "main")
    task_sha = git(repo, "rev-parse", "HEAD")
    git(repo, "checkout", "-q", "main")                                        # "does it fail on the base too?"
    (repo / "a.py").write_text("on main\n", encoding="utf-8")
    git(repo, "commit", "-q", "-am", "reviewer on main")
    rc, out = guard(repo, "verify", "001")
    assert rc == 1 and "branch changed" in out and "ref moved during the review: refs/heads/main" in out
    assert "repaired: refs/heads/main back to" in out
    assert git(repo, "rev-parse", "main") == main_sha, "local main is put back"
    assert git(repo, "rev-parse", "HEAD") == task_sha and git(repo, "symbolic-ref", "HEAD") == "refs/heads/task-001"


def test_a_new_tag_is_flagged_and_deleted_but_a_fetched_remote_ref_is_only_a_note(repo):
    guard(repo, "snapshot", "001")
    git(repo, "tag", "reviewer-tag")
    rc, out = guard(repo, "verify", "001")
    assert rc == 1 and "new ref during the review: refs/tags/reviewer-tag" in out and "repaired: refs/tags/reviewer-tag deleted" in out
    assert "reviewer-tag" not in git(repo, "tag", "-l")
    guard(repo, "snapshot", "002")
    git(repo, "update-ref", "refs/remotes/origin/main", git(repo, "rev-parse", "HEAD"))   # what a fetch does
    rc, out = guard(repo, "verify", "002")
    assert rc == 0 and "NOTE remote-tracking ref appeared" in out


def test_a_changed_git_config_is_a_flag_and_git_is_not_run(repo):
    guard(repo, "snapshot", "001")
    with open(repo / ".git" / "config", "a", encoding="utf-8") as f:
        f.write("[core]\n\tfsmonitor = evil\n")
    (repo / "a.py").write_text("still dirty\n", encoding="utf-8")
    rc, out = guard(repo, "verify", "001")
    assert rc == 1 and ".git/config changed" in out and "NOT restored" in out
    assert (repo / "a.py").read_text(encoding="utf-8") == "still dirty\n", "nothing may run git before the config is inspected"


def test_a_planted_hook_never_runs_inside_the_guard(repo):
    """S2: the active hooks folder is .githooks; an untracked post-checkout left there must
    not run when the guard switches the branch back - and it is reported before git runs."""
    guard(repo, "snapshot", "001")
    (repo / ".githooks" / "post-checkout").write_text(HOOK, encoding="utf-8")
    os.chmod(repo / ".githooks" / "post-checkout", 0o755)
    git(repo, "switch", "-q", "main")
    if (repo / "HOOK-RAN").exists():
        (repo / "HOOK-RAN").unlink()
    rc, out = guard(repo, "verify", "001")
    assert rc == 1 and "hook files changed in the active hooks folder" in out and "post-checkout" in out
    assert not (repo / "HOOK-RAN").exists(), "the guard ran the reviewer's hook"
    assert "no git command was run" in out


def test_a_modified_tracked_hook_is_a_flag_before_git_runs(repo):
    guard(repo, "snapshot", "001")
    (repo / ".githooks" / "pre-commit").write_text(HOOK, encoding="utf-8")
    rc, out = guard(repo, "verify", "001")
    assert rc == 1 and "pre-commit" in out and "no git command was run" in out


def test_detached_snapshot_with_a_planted_hook(repo):
    git(repo, "checkout", "-q", "--detach")
    guard(repo, "snapshot", "001")
    (repo / ".githooks" / "post-checkout").write_text(HOOK, encoding="utf-8")
    git(repo, "switch", "-q", "main")                                          # the reviewer's own switch may run it
    if (repo / "HOOK-RAN").exists():
        (repo / "HOOK-RAN").unlink()
    rc, out = guard(repo, "verify", "001")
    assert rc == 1 and not (repo / "HOOK-RAN").exists(), "the guard ran the reviewer's hook"


def test_ignored_records_are_flagged_and_other_ignored_changes_noted(repo):
    """S3: a gitignored record (the video factory's RUN_PARAMETERS.md) or a brief changed by
    the reviewer is a flag; a parked test inside an ignored folder is seen and noted."""
    guard(repo, "snapshot", "001")
    (repo / "run" / "hold" / "test_x.py").write_text("parked test, edited\n", encoding="utf-8")
    (repo / "parked").mkdir()
    (repo / "parked" / "x.txt").write_text("parked\n", encoding="utf-8")
    rc, out = guard(repo, "verify", "001")
    assert rc == 0 and "LEFT BEHIND (ignored, changed): run/hold/test_x.py" in out and "parked/x.txt" in out
    guard(repo, "snapshot", "002")
    (repo / "docs" / "RUN_PARAMETERS.md").write_text("Merge authority: supervisor\n", encoding="utf-8")
    rc, out = guard(repo, "verify", "002")
    assert rc == 1 and "docs/RUN_PARAMETERS.md changed during the review" in out
    guard(repo, "snapshot", "003")
    with open(repo / ".env", "a", encoding="utf-8") as f:
        f.write("MORE=2\n")
    rc, out = guard(repo, "verify", "003")
    assert rc == 1 and ".env changed" in out


def test_cache_folders_are_skipped(repo):
    (repo / ".gitignore").write_text(".env\nrun/\ndocs/RUN_PARAMETERS.md\n.venv/\n", encoding="utf-8")
    git(repo, "commit", "-q", "-am", "ignore venv")
    (repo / ".venv" / "lib").mkdir(parents=True)
    (repo / ".venv" / "lib" / "big.py").write_text("x\n", encoding="utf-8")
    rc, out = guard(repo, "snapshot", "001")
    assert rc == 0
    (repo / ".venv" / "lib" / "big.py").write_text("changed\n", encoding="utf-8")
    rc, out = guard(repo, "verify", "001")
    assert rc == 0 and "big.py" not in out


GUARD = os.path.join(HERE, os.pardir, "bridge", "cursor-bridge", "permission-guard.py")


def launched(repo, nnn="001", offset=1, exit_code=0):
    """The launcher's stderr as a Review B run leaves it: the launch line, offset seconds from
    now, and the exit line (None: the run has not ended)."""
    import time
    stamp = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(time.time() + offset))
    text = "bridge-run: started %sZ\nsome output of the reviewer\n" % stamp
    if exit_code is not None:
        text += "bridge-run: exit %d\n" % exit_code
    (repo / "run" / "review").mkdir(parents=True, exist_ok=True)
    (repo / "run" / "review" / ("REVIEW-%s.err" % nnn)).write_text(text, encoding="utf-8")


def reviewed(repo, nnn="001"):
    """snapshot, a Review B launch after it, verify OK: what every merge needs first."""
    rc, out = guard(repo, "snapshot", nnn)
    assert rc == 0, out
    launched(repo, nnn)
    rc, out = guard(repo, "verify", nnn)
    assert rc == 0 and "verified mark written" in out, out


def test_premerge_refuses_a_snapshot_without_its_verified_mark(repo):
    """Second pass of the 2026.10.06b review, S2: snapshot then premerge, no Review B between."""
    guard(repo, "snapshot", "001")
    rc, out = guard(repo, "premerge", "001")
    assert rc == 2 and "no verified mark" in out, out
    assert not (repo / ".git" / "bridge" / "premerge").exists(), "no record was written"
    launched(repo, "001", offset=-120)                   # a launch BEFORE the snapshot is not a review of it
    rc, out = guard(repo, "verify", "001")
    assert rc == 0 and "verified mark written" in out, out
    rc, out = guard(repo, "premerge", "001")
    assert rc == 2 and "before the snapshot" in out, out
    launched(repo, "001")
    rc, out = guard(repo, "verify", "001")
    assert rc == 0, out
    git(repo, "rm", "-q", "run/review/REVIEW-001.diff")
    git(repo, "commit", "-q", "-m", "remove review files")
    rc, out = guard(repo, "premerge", "001")
    assert rc == 0 and "verified mark for 001" in out, out
    rc, out = guard(repo, "snapshot", "001")              # a new snapshot needs a new review round
    assert rc == 0, out
    rc, out = guard(repo, "premerge", "001")
    assert rc == 2 and "no verified mark" in out, "the snapshot removed the older mark: " + out


def test_a_failed_review_run_or_a_flagged_verify_leaves_no_usable_mark(repo):
    """Third pass of the 2026.10.06b review, T2: the mark proves a Review B that ended with exit
    0 and a clean verify; a failed run, a run still going, or a later GATE-INTEGRITY withdraws it."""
    guard(repo, "snapshot", "001")
    launched(repo, "001", exit_code=3)                     # a usage limit: no verdict
    rc, out = guard(repo, "verify", "001")
    assert rc == 0 and "exit 3" in out, out
    rc, out = guard(repo, "premerge", "001")
    assert rc == 2 and "exit 3" in out, out
    launched(repo, "001", exit_code=None)                  # still running
    guard(repo, "verify", "001")
    rc, out = guard(repo, "premerge", "001")
    assert rc == 2 and "exit None" in out, out
    launched(repo, "001")
    rc, out = guard(repo, "verify", "001")
    assert rc == 0, out
    git(repo, "branch", "left-by-the-reviewer")            # a second run leaves a ref behind
    rc, out = guard(repo, "verify", "001")
    assert rc == 1 and "GATE-INTEGRITY" in out, out
    rc, out = guard(repo, "premerge", "001")
    assert rc == 2 and "no verified mark" in out, "the flagged verify withdrew the mark: " + out


def test_premerge_and_the_permission_guard_agree_end_to_end(repo, tmp_path):
    """Second pass, S9: the record premerge writes is the one the guard reads, from the checkout,
    a subfolder and a linked worktree; not from a folder outside the repository."""
    import json
    reviewed(repo)
    git(repo, "rm", "-q", "run/review/REVIEW-001.diff")
    git(repo, "commit", "-q", "-m", "remove review files")
    rc, out = guard(repo, "premerge", "001")
    assert rc == 0, out
    sha = re.search(r"--match-head-commit ([0-9a-f]{40})", out).group(1)
    wt = tmp_path / "Worktrees" / "TASK-002"
    git(repo, "worktree", "add", "-q", "-b", "task-002", str(wt))

    def allowed(cwd):
        payload = {"tool_name": "Bash", "tool_input": {"command": "gh pr merge 12 --squash --match-head-commit " + sha}, "cwd": str(cwd)}
        p = subprocess.run([sys.executable, GUARD], input=json.dumps(payload), capture_output=True, text=True)
        return p.returncode == 0
    assert allowed(repo) and allowed(repo / "docs") and allowed(wt)
    assert not allowed(tmp_path), "outside the repository there is no record"


def test_premerge_accepts_only_the_review_files_removal(repo):
    reviewed(repo)
    git(repo, "rm", "-q", "run/review/REVIEW-001.diff")
    rc, out = guard(repo, "premerge", "001")
    assert rc == 2 and "not clean" in out, "an uncommitted git rm must not pass"
    git(repo, "commit", "-q", "-m", "remove review files")
    rc, out = guard(repo, "premerge", "001")
    assert rc == 0 and "differs only under run/review/" in out
    assert re.search(r"gh pr merge --squash --match-head-commit [0-9a-f]{40}", out)
    (repo / "a.py").write_text("x = 9\n", encoding="utf-8")
    git(repo, "commit", "-q", "-am", "sneaked in")
    rc, out = guard(repo, "premerge", "001")
    assert rc == 1 and "a.py" in out


def test_premerge_rejects_a_head_that_does_not_descend_from_the_reviewed_one(repo):
    reviewed(repo)
    git(repo, "reset", "-q", "--hard", "HEAD~1")
    (repo / "b.py").write_text("y\n", encoding="utf-8")
    git(repo, "add", "b.py")
    git(repo, "commit", "-q", "-m", "rewritten history")
    rc, out = guard(repo, "premerge", "001")
    assert rc == 1 and "does not descend" in out


def test_missing_snapshot_cannot_verify(repo):
    rc, out = guard(repo, "verify", "009")
    assert rc == 2 and "no snapshot" in out
