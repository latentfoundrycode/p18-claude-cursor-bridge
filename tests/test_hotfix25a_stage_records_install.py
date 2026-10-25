"""Hotfix 2026.10.25a: stage-diff.py writes an interleaved stage's change from its own squash
commits (2026-10-25 C7; FB-005, FB-017); records-check.py finds a merged id without its
CHANGES.md line (2026-10-18 C1); bridge-install.py installs a release/* branch as merged and
nothing else it refused (2026-10-25 C11; FB-016). Scratch repositories and targets only."""
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, os.pardir))
RELEASE = os.path.join(ROOT, "bridge")
STAGE_DIFF = os.path.join(RELEASE, "cursor-bridge", "stage-diff.py")
RECORDS = os.path.join(RELEASE, "cursor-bridge", "records-check.py")
ENV = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.invalid", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@example.invalid")


def git(folder, *args):
    p = subprocess.run(["git", "-C", str(folder), "-c", "core.autocrlf=false", "-c", "core.hooksPath=" + os.devnull,
                        "-c", "commit.gpgsign=false"] + list(args), capture_output=True, text=True, env=ENV)
    assert p.returncode == 0, p.stdout + p.stderr
    return p.stdout.strip()


def run(prog, cwd, *args, env=None):
    p = subprocess.run([sys.executable, str(prog)] + list(args), capture_output=True, text=True, cwd=str(cwd), env=env or ENV)
    return p.returncode, p.stdout + p.stderr


def commit(repo, message, **files):
    for name, text in files.items():
        stem, ext = name.replace("__", "/").rsplit("_", 1)     # docs__CHANGES_md is docs/CHANGES.md
        path = repo / (stem + "." + ext)
        path.parent.mkdir(parents=True, exist_ok=True)
        if text is None:
            path.unlink()
        else:
            path.write_text(text, encoding="utf-8", newline="\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "--allow-empty", "-m", message)
    return git(repo, "rev-parse", "HEAD")


def new_repo(tmp_path, **files):
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    commit(repo, "base", **files)
    return repo


# --- 2026-10-25 C7: stage-diff.py ------------------------------------------------------------

def interleaved(tmp_path):
    """Stage A's two increments with stage B's between them on main."""
    repo = new_repo(tmp_path, a_txt="a1\n", b_txt="b1\n", shared_txt="s1\n")
    s1 = commit(repo, "TASK-001: stage A one (#1)", a_txt="a2\n")
    f1 = commit(repo, "TASK-003: stage B one (#2)", b_txt="b2\n", new_txt="from B\n")
    s2 = commit(repo, "TASK-002: stage A two (#3)", a_txt="a3\n", a2_txt="added by A\n")
    git(repo, "update-ref", "refs/remotes/origin/main", "HEAD")
    return repo, s1, f1, s2


def test_an_interleaved_stage_s_change_holds_its_own_commits_only(tmp_path):
    repo, s1, f1, s2 = interleaved(tmp_path)
    rc, out = run(STAGE_DIFF, repo, s2, s1, "--out", "run/review", "--name", "A")
    assert rc == 0, out
    review = repo / "run" / "review"
    whole = (review / "STAGE-A.diff").read_text(encoding="utf-8")
    assert "a.txt" in whole and "a2.txt" in whole, whole
    assert "b.txt" not in whole and "new.txt" not in whole, "the later stage's merge is in the stage's change: " + whole
    base = git(repo, "rev-parse", s1 + "^")
    assert whole.strip() == git(repo, "diff", "--no-color", base, s2, "--", "a.txt", "a2.txt"), "the whole change is not the union of the stage's commits"
    part1 = review / ("STAGE-A-01-%s.diff" % s1[:7])
    part2 = review / ("STAGE-A-02-%s.diff" % s2[:7])
    assert part1.read_text(encoding="utf-8").strip() == git(repo, "diff", "--no-color", base, s1), "the parts are not in main's order, or not each commit's own diff"
    assert part2.read_text(encoding="utf-8").strip() == git(repo, "diff", "--no-color", f1, s2)
    assert "commit " not in whole, "a log line inside the diff (FB-017)"
    assert "TASK-001: stage A one" in out and "TASK-002: stage A two" in out and "left out  %s" % f1[:7] in out and "2 path(s) set back" in out, out
    assert git(repo, "status", "--porcelain", "--untracked-files=no") == "", "the checkout or the index was changed"


def test_the_commits_can_come_from_a_file_and_a_former_run_s_parts_go(tmp_path):
    repo, s1, f1, s2 = interleaved(tmp_path)
    rc, out = run(STAGE_DIFF, repo, s1, f1, s2, "--out", "out")
    assert rc == 0 and (repo / "out" / ("STAGE-03-%s.diff" % s2[:7])).is_file(), out
    (repo / "list.txt").write_text("# stage A\n%s  TASK-001\n\n%s\n" % (s1[:9], s2), encoding="utf-8")
    rc, out = run(STAGE_DIFF, repo, "--from-file", "list.txt", "--out", "out")
    assert rc == 0, out
    names = sorted(os.listdir(repo / "out"))
    assert names == ["STAGE-01-%s.diff" % s1[:7], "STAGE-02-%s.diff" % s2[:7], "STAGE.diff"], names


def test_a_path_the_stage_changed_again_after_another_merge_is_named_overlap(tmp_path):
    repo, s1, f1, s2 = interleaved(tmp_path)
    f2 = commit(repo, "TASK-004: stage B two (#4)", shared_txt="s2 by B\n")
    s3 = commit(repo, "TASK-005: stage A three (#5)", shared_txt="s3 by A\n")
    git(repo, "update-ref", "refs/remotes/origin/main", "HEAD")
    rc, out = run(STAGE_DIFF, repo, s1, s2, s3, "--out", "out")
    assert rc == 1 and "OVERLAP  shared.txt" in out and f2[:7] in out and s3[:7] in out, out
    assert "b.txt" not in (repo / "out" / "STAGE.diff").read_text(encoding="utf-8")


def test_a_commit_that_is_not_a_squash_on_main_writes_nothing(tmp_path):
    repo, s1, f1, s2 = interleaved(tmp_path)
    git(repo, "switch", "-q", "-c", "side")
    side = commit(repo, "TASK-009: never merged", a_txt="side\n")
    git(repo, "switch", "-q", "main")
    rc, out = run(STAGE_DIFF, repo, s1, side, "--out", "out")
    assert rc == 2 and "not on origin/main's first-parent line" in out and not (repo / "out").exists(), out
    rc, out = run(STAGE_DIFF, repo, "--out", "out")
    assert rc == 2 and "no commit given" in out, out


# --- 2026-10-18 C1: records-check.py ---------------------------------------------------------

def test_a_merged_id_without_its_changes_line_is_missing(tmp_path):
    repo = new_repo(tmp_path, docs__CHANGES_md="# Changes\n")
    since = git(repo, "rev-parse", "HEAD")
    commit(repo, "TASK-001: one (#1)")
    commit(repo, "BUG-002: a fix (#2)")
    commit(repo, "TASK-059e: a lettered increment (#3)")
    commit(repo, "docs: plan split TASK-003 out of TASK-004")
    commit(repo, "feat(x): a thing (FIX-007) (#4)")
    commit(repo, "records", docs__CHANGES_md="# Changes\n- TASK-001: one\n- TASK-059: not the lettered one\n")
    git(repo, "update-ref", "refs/remotes/origin/main", "HEAD")
    rc, out = run(RECORDS, repo, "--since", since)
    assert rc == 1, out
    missing = sorted(l.split()[2] for l in out.splitlines() if l.startswith("MISSING"))
    assert missing == ["BUG-002", "FIX-007", "TASK-059e"], out
    (repo / "docs" / "CHANGES.md").write_text("# Changes\n- TASK-001\n- BUG-002\n- TASK-059e\n- FIX-007\n", encoding="utf-8")
    rc, out = run(RECORDS, repo, "--since", since)
    assert rc == 1, "a line not yet merged on origin/main was counted: " + out
    commit(repo, "supervisor: records")
    git(repo, "update-ref", "refs/remotes/origin/main", "HEAD")
    rc, out = run(RECORDS, repo, "--since", since)
    assert rc == 0 and "0 without a line" in out, out


def test_records_check_says_when_it_cannot_read(tmp_path):
    repo = new_repo(tmp_path, readme_md="x\n")
    git(repo, "update-ref", "refs/remotes/origin/main", "HEAD")
    rc, out = run(RECORDS, repo, "--since", "HEAD")
    assert rc == 2 and "not readable" in out, out
    rc, out = run(RECORDS, repo, "--since", "no-such-commit")
    assert rc == 2 and "names no commit" in out, out


# --- 2026-10-25 C11: bridge-install.py on a release/* branch ---------------------------------

def stamped_checkout(tmp_path):
    """A checkout of the bridge with its tree stamped as it is now (other changes of the
    hotfix included), merged on main."""
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    shutil.copytree(RELEASE, repo / "bridge", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    (repo / "tools").mkdir()
    shutil.copy(os.path.join(ROOT, "tools", "make-manifest.py"), repo / "tools" / "make-manifest.py")
    p = subprocess.run([sys.executable, str(repo / "tools" / "make-manifest.py")], capture_output=True, text=True, cwd=str(repo))
    assert p.returncode == 0, p.stdout + p.stderr
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "a release")
    git(repo, "update-ref", "refs/remotes/origin/main", "HEAD")
    return repo


def test_a_release_branch_as_merged_is_installed_and_nothing_else_it_refused(tmp_path):
    repo = stamped_checkout(tmp_path)
    installer, target = repo / "bridge" / "cursor-bridge" / "bridge-install.py", tmp_path / ".claude"
    env = dict(ENV, LOCALAPPDATA=str(tmp_path / "localappdata"))
    git(repo, "switch", "-q", "-c", "release/2026.10.11")
    rc, out = run(installer, tmp_path, "--target", str(target), env=env)
    assert rc == 2 and "origin/release/2026.10.11 cannot be read" in out and not target.exists(), "a release branch never pushed was installed: " + out
    git(repo, "commit", "-q", "--allow-empty", "-m", "pushed straight to the release branch")
    git(repo, "update-ref", "refs/remotes/origin/release/2026.10.11", "HEAD")
    rc, out = run(installer, tmp_path, "--target", str(target), env=env)
    assert rc == 2 and "not a pull request's merge" in out and not target.exists(), "a release branch is not protected: a push alone is not a merge: " + out
    p = subprocess.run(["git", "-C", str(repo), "-c", "commit.gpgsign=false", "commit", "-q", "--allow-empty", "-m", "FIX-001: the hotfix (#9)"],
                       capture_output=True, text=True, env=dict(ENV, GIT_COMMITTER_NAME="GitHub", GIT_COMMITTER_EMAIL="noreply@github.com"))
    assert p.returncode == 0, p.stderr
    git(repo, "update-ref", "refs/remotes/origin/release/2026.10.11", "HEAD")
    git(repo, "commit", "-q", "--allow-empty", "-m", "never merged")
    rc, out = run(installer, tmp_path, "--target", str(target), env=env)
    assert rc == 2 and "differs from origin/release/2026.10.11" in out and not target.exists(), out
    git(repo, "reset", "-q", "--hard", "origin/release/2026.10.11")
    manifest = repo / "bridge" / "cursor-bridge" / "MANIFEST.json"
    manifest.write_bytes(manifest.read_bytes() + b"\n")
    rc, out = run(installer, tmp_path, "--target", str(target), env=env)
    assert rc == 2 and "not committed" in out and not target.exists(), out
    git(repo, "checkout", "-q", "--", ".")
    rc, out = run(installer, tmp_path, "--target", str(target), env=env)
    assert rc == 0 and "RESULT: INSTALLED TREE MATCHES" in out, "a release branch as merged was refused (FB-016): " + out
    git(repo, "switch", "-q", "-c", "hotfix/2026.10.25a")
    git(repo, "update-ref", "refs/remotes/origin/hotfix/2026.10.25a", "HEAD")
    rc, out = run(installer, tmp_path, "--target", str(tmp_path / "other"), env=env)
    assert rc == 2 and "not on main or a release/* branch" in out and not (tmp_path / "other").exists(), "a branch that is neither main nor release/* was installed: " + out
