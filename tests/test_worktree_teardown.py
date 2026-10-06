"""worktree-teardown.py (release A1b, rule 19): a worktree is removed without --force, and
never while a junction or symbolic link is inside it. Temporary repositories only."""
import os
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
PROG = os.path.join(HERE, os.pardir, "bridge", "cursor-bridge", "worktree-teardown.py")


def git(repo, *args):
    p = subprocess.run(["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@example.invalid", "-c", "core.autocrlf=false",
                        "-c", "core.hooksPath=" + os.devnull] + list(args), capture_output=True, text=True)
    assert p.returncode == 0, p.stdout + p.stderr
    return p.stdout.strip()


def run(repo, *args):
    p = subprocess.run([sys.executable, PROG] + list(args), capture_output=True, text=True, cwd=str(repo))
    return p.returncode, p.stdout + p.stderr


def remove_link(path):
    if os.path.islink(path):
        os.unlink(path)
    else:
        os.rmdir(path)                                 # a junction


def link(path, target):
    if os.name == "nt":
        subprocess.run(["cmd", "/c", "mklink", "/J", str(path), str(target)], capture_output=True)
    else:
        os.symlink(str(target), str(path))


@pytest.fixture
def repo(tmp_path):
    repo = tmp_path / "Workspace"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    (repo / "a.txt").write_text("a\n", encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "init")
    (tmp_path / "Worktrees").mkdir()
    git(repo, "worktree", "add", "-q", "-b", "task-1", str(tmp_path / "Worktrees" / "TASK-001"))
    return repo


def test_a_clean_worktree_is_removed_and_pruned(repo, tmp_path):
    wt = tmp_path / "Worktrees" / "TASK-001"
    rc, out = run(repo, str(wt), "--dry-run")
    assert rc == 0 and "would run git worktree remove" in out and wt.is_dir(), out
    rc, out = run(repo, str(wt))
    assert rc == 0 and "removed" in out and not wt.exists(), out
    assert "TASK-001" not in git(repo, "worktree", "list")


def test_a_link_inside_refuses_the_teardown_and_the_target_survives(repo, tmp_path):
    wt = tmp_path / "Worktrees" / "TASK-001"
    target = repo / "node_modules"
    target.mkdir()
    (target / "keep.txt").write_text("keep\n", encoding="utf-8")
    link(wt / "node_modules", target)
    rc, out = run(repo, str(wt))
    assert rc == 2 and "link(s) inside" in out and "node_modules" in out and "never through it" in out, out
    assert wt.is_dir() and (target / "keep.txt").is_file(), "nothing was removed, nothing was followed"
    remove_link(wt / "node_modules")                      # the link itself
    rc, out = run(repo, str(wt))
    assert rc == 0 and not wt.exists() and (target / "keep.txt").is_file(), out


@pytest.mark.skipif(os.name != "nt", reason="the hazard is Git for Windows following a junction")
def test_why_the_plain_removal_is_refused_by_the_guard(repo, tmp_path):
    """Review of 2026.10.06b, finding 1: an ordinary `git worktree remove` deletes what a
    gitignored junction points to, exactly as --force does. This test keeps the reason on
    record; the guard refuses the command and the program refuses the link."""
    wt = tmp_path / "Worktrees" / "TASK-001"
    target = tmp_path / "elsewhere"
    target.mkdir()
    (target / "keep.txt").write_text("keep\n", encoding="utf-8")
    (wt / ".gitignore").write_text("node_modules/\n", encoding="utf-8")
    git(wt, "add", ".gitignore")
    git(wt, "commit", "-q", "-m", "ignore")
    link(wt / "node_modules", target)
    rc, out = run(repo, str(wt))
    assert rc == 2 and (target / "keep.txt").is_file(), "the program refuses and touches nothing: " + out
    p = subprocess.run(["git", "-C", str(repo), "worktree", "remove", str(wt)], capture_output=True, text=True)
    version = subprocess.run(["git", "--version"], capture_output=True, text=True).stdout.strip()
    if (target / "keep.txt").exists():
        # Observed on Git for Windows 2.53: the target is emptied. The CI runner's 2.55 exited 0 and
        # left the folder (second pass, S1). The guard and the program do not depend on either.
        pytest.skip("%s: plain removal exit %d, worktree %s, target intact; the premise is not shown on this git" % (
            version, p.returncode, "gone" if not wt.exists() else "left behind"))
    print("%s: plain removal exit %d, worktree %s, target emptied; this is why only the program removes worktrees" % (
        version, p.returncode, "gone" if not wt.exists() else "left behind"))


def test_a_leftover_folder_is_checked_for_links_whether_git_lists_it_or_not(repo, tmp_path):
    """Second pass, S7: after a failed removal git drops the registration but leaves the folder;
    the program still refuses with the list when a link is inside, and says so when none is."""
    leftover = tmp_path / "Worktrees" / "LEFTOVER"
    leftover.mkdir()
    (leftover / "a.txt").write_text("a\n", encoding="utf-8")
    target = tmp_path / "elsewhere"
    target.mkdir()
    link(leftover / "node_modules", target)
    rc, out = run(repo, str(leftover))
    assert rc == 2 and "link(s) inside" in out and "node_modules" in out and target.is_dir(), out
    remove_link(leftover / "node_modules")
    rc, out = run(repo, str(leftover))
    assert rc == 2 and "not a worktree of this repository" in out and "this leftover may go" in out and leftover.is_dir(), out
    # third pass, T4: the advice is for leftovers only, never for a folder that holds a live worktree or any other folder
    rc, out = run(repo, str(tmp_path / "Worktrees"))
    assert rc == 2 and "holds a registered worktree" in out and "may go" not in out, out
    rc, out = run(repo, str(repo / "docs")) if (repo / "docs").is_dir() else run(repo, str(tmp_path))
    assert rc == 2 and "may go" not in out, out


def test_a_locked_worktree_is_named_as_such(repo, tmp_path):
    wt = tmp_path / "Worktrees" / "TASK-001"
    git(repo, "worktree", "lock", str(wt))
    rc, out = run(repo, str(wt))
    assert rc == 1 and "git worktree unlock" in out and wt.is_dir(), out


def test_a_dirty_worktree_is_left_to_git_and_never_forced(repo, tmp_path):
    wt = tmp_path / "Worktrees" / "TASK-001"
    (wt / "new.txt").write_text("x\n", encoding="utf-8")
    rc, out = run(repo, str(wt))
    assert rc == 1 and "git refused" in out and "never --force" in out and wt.is_dir(), out


def test_only_a_worktree_of_this_repository_is_accepted(repo, tmp_path):
    other = tmp_path / "elsewhere"
    other.mkdir()
    rc, out = run(repo, str(other))
    assert rc == 2 and "not a worktree of this repository" in out and other.is_dir(), out
    rc, out = run(repo, str(repo))
    assert rc == 2 and "main checkout" in out, out
    rc, out = run(repo)
    assert rc == 2 and "usage" in out
