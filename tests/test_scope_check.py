"""scope-check.py (release A4, plan review R17 and 13.1): the brief's Scope is read as written and the
changeset as git sees it. Each case failed on the old program. Scratch repositories; the brief is
committed with the checkpoint, as the loop does."""
import os
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
PROG = os.path.join(HERE, os.pardir, "bridge", "cursor-bridge", "scope-check.py")
ENV = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.invalid", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@example.invalid")


def git(repo, *args):
    p = subprocess.run(["git"] + list(args), cwd=str(repo), capture_output=True, text=True, env=ENV)
    assert p.returncode == 0, p.stderr
    return p.stdout.strip()


def run(repo, *args):
    p = subprocess.run([sys.executable, PROG] + list(args), cwd=str(repo), capture_output=True, text=True, env=ENV)
    return p.returncode, p.stdout + p.stderr


def drift_list(out):
    return [l.strip()[2:] for l in out.splitlines() if l.startswith("  - ")]


@pytest.fixture
def repo(tmp_path):
    r = tmp_path / "ws"
    (r / "src" / "core").mkdir(parents=True)
    (r / ".github" / "workflows").mkdir(parents=True)
    (r / "docs").mkdir()
    (r / "handoff").mkdir()
    (r / "src" / "core" / "a.py").write_text("A = 1\n", encoding="utf-8")
    (r / "src" / "core" / "b.py").write_text("B = 1\n", encoding="utf-8")
    (r / "src" / "other.py").write_text("O = 1\n", encoding="utf-8")
    (r / ".github" / "workflows" / "ci.yml").write_text("on: push\n", encoding="utf-8")
    (r / "docs" / "BUILDER_NOTES.md").write_text("# notes\n", encoding="utf-8")
    git(r, "init", "-q", "-b", "main")
    git(r, "add", "-A")
    git(r, "commit", "-q", "-m", "scratch")
    return r


def brief(repo, scope_lines, name="TASK-001.md"):
    """The brief, committed as the checkpoint commit."""
    path = repo / "handoff" / name
    path.write_text("# TASK-001\n\n## Scope\n" + "\n".join(scope_lines) + "\n\n## Constraints\n- none\n", encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "checkpoint: " + name)
    return "handoff/" + name


def test_a_sub_heading_under_scope_is_not_scope(repo):
    b = brief(repo, ["- src/core/a.py", "", "### Out of scope", "- src/other.py"])
    (repo / "src" / "other.py").write_text("O = 2\n", encoding="utf-8")
    rc, out = run(repo, b)
    assert rc == 1 and drift_list(out) == ["src/other.py"], "a bullet under `### Out of scope` was read as scope: " + out


def test_a_rename_shows_the_deleted_path(repo):
    b = brief(repo, ["- src/core/new.py"])
    git(repo, "mv", "src/core/a.py", "src/core/new.py")
    rc, out = run(repo, b)
    assert rc == 1 and "src/core/a.py" in drift_list(out), "a staged rename hid the out-of-scope deletion: " + out


def test_a_builder_commit_is_not_an_empty_pass(repo):
    b = brief(repo, ["- src/core/a.py"])
    (repo / "src" / "other.py").write_text("O = 2\n", encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "builder committed")
    rc, out = run(repo, b)
    assert rc == 1 and "src/other.py" in drift_list(out) and "checkpoint" in out.lower(), "the default base is the commit that committed the brief, so a builder's commit is inside the diff: " + out
    rc, out = run(repo, b, "--base", "HEAD")
    assert rc == 0, out


def test_a_dotted_folder_name_is_kept(repo):
    b = brief(repo, ["- .github/workflows/"])
    (repo / ".github" / "workflows" / "ci.yml").write_text("on: [push]\n", encoding="utf-8")
    rc, out = run(repo, b)
    assert rc == 0, ".github/ was normalised to github/: " + out


def test_an_ellipsis_cannot_be_verified(repo):
    b = brief(repo, ["- src/core/...", "- src/..."])
    rc, out = run(repo, b)
    assert rc == 2 and "ellipsis" in out.lower(), out


def test_several_paths_in_one_bullet_and_quoted_paths(repo):
    b = brief(repo, ["- `src/core/a.py`, `src/core/b.py` and \"src/other.py\""])
    for f in ("src/core/a.py", "src/core/b.py", "src/other.py"):
        (repo / f).write_text("X = 2\n", encoding="utf-8")
    rc, out = run(repo, b)
    assert rc == 0, out


def test_bracketed_folder_names_are_literal(repo):
    (repo / "src" / "[id]").mkdir()
    (repo / "src" / "[id]" / "page.py").write_text("P = 1\n", encoding="utf-8")
    b = brief(repo, ["- src/[id]/page.py"])
    (repo / "src" / "[id]" / "page.py").write_text("P = 2\n", encoding="utf-8")
    rc, out = run(repo, b)
    assert rc == 0, "a bracketed folder name was read as a glob class: " + out


def test_prose_after_a_path_is_dropped(repo):
    b = brief(repo, ["- src/core/a.py which holds the parser", "- src/core/b.py: the writer (new)"])
    for f in ("src/core/a.py", "src/core/b.py"):
        (repo / f).write_text("X = 2\n", encoding="utf-8")
    rc, out = run(repo, b)
    assert rc == 0, out


def test_the_bookkeeping_files_are_never_drift(repo):
    b = brief(repo, ["- src/core/a.py"])
    (repo / "docs" / "BUILDER_NOTES.md").write_text("# notes\n- 2026-10-11 a line\n", encoding="utf-8")
    (repo / "docs" / "BOUNDARY_VIOLATIONS.md").write_text("none\n", encoding="utf-8")
    (repo / "run").mkdir()
    (repo / "run" / "x.log").write_text("log\n", encoding="utf-8")
    rc, out = run(repo, b)
    assert rc == 0 and "BOOKKEEPING (3)" in out, out
