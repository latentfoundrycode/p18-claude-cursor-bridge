"""R-042: review-guard holds the code gate's round ceiling (docs/REQUIREMENTS.md line 48)."""
import json
import os
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
PROG = os.path.join(HERE, os.pardir, "bridge", "cursor-bridge", "review-guard.py")
ENV = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@x", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@x",
           GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_SYSTEM=os.devnull)


def git(repo, *args):
    p = subprocess.run(["git"] + list(args), cwd=repo, capture_output=True, text=True, env=ENV)
    assert p.returncode == 0, p.stderr
    return p.stdout.strip()


def guard(repo, *args):
    p = subprocess.run([sys.executable, PROG] + list(args), cwd=repo, capture_output=True, text=True, env=ENV, timeout=120)
    return p.returncode, p.stdout + p.stderr


@pytest.fixture
def repo(tmp_path):
    r = tmp_path / "ws"
    r.mkdir()
    git(r, "init", "-q", "-b", "main")
    (r / ".gitignore").write_text("run/\n", encoding="utf-8")
    (r / "a.py").write_text("1\n", encoding="utf-8")
    (r / "run" / "review").mkdir(parents=True)
    (r / "run" / "review" / "REVIEW-TASK-001.diff").write_text("d\n", encoding="utf-8")
    git(r, "add", "-A")
    git(r, "commit", "-q", "-m", "base")
    git(r, "checkout", "-q", "-b", "task-001")
    git(r, "add", "-f", "run/review/REVIEW-TASK-001.diff")
    git(r, "commit", "-q", "-am", "TASK-001")
    return r


def test_r042_grammar_refuses_bare_number(repo):
    rc, out = guard(repo, "snapshot", "001")
    assert rc == 125 and "grammar" in out


def test_r042_rounds_one_two_three(repo):
    for name in ("TASK-001", "TASK-001-r2", "TASK-001-r3"):
        rc, out = guard(repo, "snapshot", name)
        assert rc == 0, out
        (repo / "run" / "review" / ("REVIEW-%s.err" % name)).write_text(
            "bridge-run: started 2026-10-04T10:00:00Z\nbridge-run: exit 0\n", encoding="utf-8"
        )
        rc, out = guard(repo, "verify", name)
        assert rc == 0, out


def test_r042_fourth_round_refused_without_scope_line(repo):
    for name in ("TASK-001", "TASK-001-r2", "TASK-001-r3"):
        guard(repo, "snapshot", name)
        (repo / "run" / "review" / ("REVIEW-%s.err" % name)).write_text(
            "bridge-run: started 2026-10-04T10:00:00Z\nbridge-run: exit 0\n", encoding="utf-8"
        )
        guard(repo, "verify", name)
    rc, out = guard(repo, "snapshot", "TASK-001-r4")
    assert rc == 125 and out.startswith("review-guard: refused - review ceiling:")


def test_r042_class_line_in_scope_allows_fourth(repo):
    for name in ("TASK-001", "TASK-001-r2", "TASK-001-r3"):
        guard(repo, "snapshot", name)
        (repo / "run" / "review" / ("REVIEW-%s.err" % name)).write_text(
            "bridge-run: started 2026-10-04T10:00:00Z\nbridge-run: exit 0\n", encoding="utf-8"
        )
        guard(repo, "verify", name)
    (repo / "run" / "review" / "SCOPE-TASK-001.md").write_text(
        "Blocking class: security - found issue\n", encoding="utf-8"
    )
    git(repo, "add", "-f", "run/review/SCOPE-TASK-001.md")
    git(repo, "commit", "-q", "-m", "scope")
    rc, out = guard(repo, "snapshot", "TASK-001-r4")
    assert rc == 0, out
    data = json.loads((repo / ".git" / "bridge" / "rounds-TASK-001.json").read_text(encoding="utf-8"))
    assert any(r.get("round") == 4 for r in data.get("rounds", []))


def test_r042_design_name_not_grammar_blocked(repo):
    rc, out = guard(repo, "snapshot", "DESIGN-plan-1")
    assert rc == 0, out


def test_r042_refused_snapshot_writes_no_rounds_file(repo):
    rc, out = guard(repo, "snapshot", "TASK-001-r9")
    assert rc == 125
    assert not (repo / ".git" / "bridge" / "rounds-TASK-001.json").exists()
    assert not (repo / ".git" / "bridge" / "review-TASK-001-r9.json").exists()
