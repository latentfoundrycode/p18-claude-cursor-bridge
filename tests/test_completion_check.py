"""completion-check.py (release A4, R17 and 13.1): only an increment's `Satisfies:` field counts as
planned; a built requirement whose Evidence names no test fails in plan mode too; `--only` limits
the run to part of the register. Scratch repositories."""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROG = os.path.join(HERE, os.pardir, "bridge", "cursor-bridge", "completion-check.py")
ENV = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.invalid", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@example.invalid")

REGISTER = """| ID | Requirement | Source | Status | Evidence |
|---|---|---|---|---|
| R-001 | parse the file | owner | built | tests/test_parse.py |
| R-002 | write the file | owner | built | - |
| R-003 | show a graph | owner | planned | - |
| R-004 | old thing | owner | built | tests/test_old.py |
"""
PLAN = """# Plan

## Stage 1
Demonstration: the parser runs.

### TASK-001 — parser
Satisfies: R-001, R-004
Scope: src/parse.py

### TASK-002 — writer, which also mentions R-003 in prose but does not satisfy it
Satisfies: R-002
Scope: src/write.py
"""


def make(tmp_path):
    r = tmp_path / "ws"
    (r / "docs").mkdir(parents=True)
    (r / "tests").mkdir()
    (r / "src").mkdir()
    (r / "docs" / "REQUIREMENTS.md").write_text(REGISTER, encoding="utf-8")
    (r / "docs" / "BUILD_PLAN.md").write_text(PLAN, encoding="utf-8")
    (r / "tests" / "test_parse.py").write_text("def test_r001():  # R-001\n    assert True\n", encoding="utf-8")
    (r / "tests" / "test_old.py").write_text("def test_r004():  # R-004\n    assert True\n", encoding="utf-8")
    (r / "src" / "parse.py").write_text("X = 1\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=str(r), check=True, env=ENV)
    subprocess.run(["git", "add", "-A"], cwd=str(r), check=True, env=ENV)
    subprocess.run(["git", "commit", "-q", "-m", "scratch"], cwd=str(r), check=True, env=ENV)
    return r


def run(repo, *args):
    p = subprocess.run([sys.executable, PROG] + list(args), cwd=str(repo), capture_output=True, text=True, env=ENV)
    return p.returncode, p.stdout + p.stderr


def test_only_the_satisfies_field_counts_as_planned(tmp_path):
    r = make(tmp_path)
    rc, out = run(r, "--mode", "plan")
    assert "UNPLANNED: R-003" in out, "a mention in prose counted as planned (R17): " + out


def test_a_built_requirement_without_a_test_in_its_evidence_fails(tmp_path):
    r = make(tmp_path)
    rc, out = run(r, "--mode", "plan")
    assert rc == 1 and "NO EVIDENCE: R-002" in out, "marked built, evidence names no test (13.1): " + out
    assert "R-001" not in "\n".join(l for l in out.splitlines() if l.startswith("NO EVIDENCE")), out


def test_only_limits_the_run_to_part_of_the_register(tmp_path):
    r = make(tmp_path)
    rc, out = run(r, "--mode", "done", "--only", "R-001,R-004")
    assert rc == 0 and "R-002" not in out and "R-003" not in out and "limited to" in out, out
    rc, out = run(r, "--mode", "done", "--only", "R-002")
    assert rc == 1 and "NO EVIDENCE: R-002" in out and "NOT BUILT: R-003" not in out, out
