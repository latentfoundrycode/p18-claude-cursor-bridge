"""plan-check.py (release A4, R17 and 13.1): a commit marks an increment merged only when its subject
starts with the ID (or a merge commit's branch does); a dependency the parser cannot read fails
instead of vanishing; each brief is compared with its increment; a dated addendum is read with the
plan. Scratch repositories."""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROG = os.path.join(HERE, os.pardir, "bridge", "cursor-bridge", "plan-check.py")
ENV = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.invalid", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@example.invalid")

PLAN = """# Plan

## Stage 1
Demonstration: the parser runs.

### TASK-001 — parser
Satisfies: R-001
Scope: src/parse.py

### TASK-002 — writer
Depends on: TASK-001
Satisfies: R-002
Scope: src/write.py

### TASK-003 — graph
Depends on: TASK-002
Satisfies: R-003, R-004
Scope: src/graph/

### TASK-004 — export
Depends on: TASK-003
Satisfies: R-005
Scope: src/export.py

### TASK-006a — lettered one
Satisfies: R-010
Scope: src/l1.py

### TASK-006b — lettered two
Satisfies: R-011
Scope: src/l2.py

### TASK-007 — exporter, merged under the TDP's subject form
Depends on: TASK-006a, TASK-006b (TASK-006b added 2026-10-03: the pair ships together; see the note)
Satisfies: R-009
Scope: src/exp/

### TASK-008 — merged by a records commit's Merges: trailer
Satisfies: R-012
Scope: src/rec.py
"""


def git(repo, *args):
    p = subprocess.run(["git"] + list(args), cwd=str(repo), capture_output=True, text=True, env=ENV)
    assert p.returncode == 0, p.stderr
    return p.stdout.strip()


def make(tmp_path, plan=PLAN):
    r = tmp_path / "ws"
    (r / "docs").mkdir(parents=True)
    (r / "handoff").mkdir()
    (r / "docs" / "BUILD_PLAN.md").write_text(plan, encoding="utf-8")
    git(r, "init", "-q", "-b", "main")
    git(r, "add", "-A")
    git(r, "commit", "-q", "-m", "scratch")
    git(r, "commit", "-q", "--allow-empty", "-m", "TASK-001: the parser")
    git(r, "commit", "-q", "--allow-empty", "-m", "Merge pull request #5 from owner/task-002-writer")
    git(r, "commit", "-q", "--allow-empty", "-m", "docs: plan split TASK-003 out of TASK-004")
    git(r, "commit", "-q", "--allow-empty", "-m", "TASK-006a TASK-006b: the lettered pair (#7)")
    git(r, "commit", "-q", "--allow-empty", "-m", "feat(export): the exporter (TASK-007, R-009) - v0.2.0 (#8)")
    git(r, "commit", "-q", "--allow-empty", "-m", "records: the stage close\n\nMerges: TASK-008")
    return r


def run(repo, *args):
    p = subprocess.run([sys.executable, PROG, "--base", "main"] + list(args), cwd=str(repo), capture_output=True, text=True, env=ENV)
    return p.returncode, p.stdout + p.stderr


def test_a_commit_that_mentions_two_increments_merges_neither(tmp_path):
    r = make(tmp_path)
    rc, out = run(r)
    assert rc == 0 and "6 merged" in out and "READY: TASK-003" in out and "READY: TASK-004" not in out, "the docs commit marked TASK-003 and TASK-004 merged (R17): " + out
    for tid in ("TASK-006a", "TASK-006b", "TASK-007", "TASK-008"):
        assert "READY: %s" % tid not in out, "%s is merged: a lettered ID keeps its case, several IDs at the start all count, the IDs in parentheses at the end count, a Merges: trailer counts (first pass, F1 and F4): %s" % (tid, out)
    assert "DEPENDS" not in out, "a dated note in parentheses on a Depends on line is not an ID (first pass, F3): " + out


def test_an_unreadable_dependency_fails_instead_of_vanishing(tmp_path):
    r = make(tmp_path, PLAN.replace("Depends on: TASK-002", "Depends on: TASK-02"))
    rc, out = run(r)
    assert rc == 1 and "DEPENDS: TASK-003" in out and "TASK-02" in out, "`Depends on: TASK-02` was silently dropped (R17): " + out


def test_each_brief_is_compared_with_its_increment(tmp_path):
    r = make(tmp_path)
    (r / "handoff" / "TASK-003.md").write_text("# TASK-003\nSatisfies: R-003 graph\n\n## Scope\n- src/graph/draw.py\n- src/export.py\n- docs/BUILDER_NOTES.md\n\n## Constraints\n- none\n", encoding="utf-8")
    rc, out = run(r)
    assert rc == 1 and "BRIEF: handoff/TASK-003.md" in out and "src/export.py" in out and "R-004" in out, "a brief that drops a requirement and reaches outside its increment (13.1): " + out
    (r / "handoff" / "TASK-003.md").write_text("# TASK-003\nSatisfies: R-003, R-004\n\n## Scope\n- src/graph/draw.py\n- docs/BUILDER_NOTES.md\n\n## Constraints\n- none\n", encoding="utf-8")
    rc, out = run(r)
    assert rc == 0, "the bookkeeping file every brief names is not a BRIEF finding (first pass, F2): " + out


def test_a_dated_addendum_is_read_with_the_plan(tmp_path):
    r = make(tmp_path)
    (r / "docs" / "BUILD_PLAN-2026-10-11-addendum.md").write_text("# Addendum 2026-10-11\n\n## Change cycle: colours\nDemonstration: the graph in colour.\n\n### TASK-005 — colours\nDepends on: TASK-002\nSatisfies: R-006\nScope: src/colour.py\n", encoding="utf-8")
    rc, out = run(r)
    assert rc == 0 and "READY: TASK-005" in out and "addendum" in out.lower(), out
