"""Release S (S5): plan-check.py notes an increment too large to converge, before its first brief.

An unmerged increment whose `Done when:` field holds more than twelve acceptance items, or whose Scope names more than twelve
paths, gets one `note: large increment: ...` line. It is a note and never a failure: the exit code and the RESULT line are
those of the same plan without it. Scratch repositories.

Register: R-070 is held by this file."""
import os
import subprocess
import sys

import pytest

from test_plan_check import ENV, git

HERE = os.path.dirname(os.path.abspath(__file__))
PROG = os.path.join(HERE, os.pardir, "bridge", "cursor-bridge", "plan-check.py")

HEAD = "# Plan\n\n## Stage 1\nDemonstration: the parser runs.\n\n"


def increment(tid, done_when, scope="src/a.py", more=""):
    return "### %s — an increment\nSatisfies: R-001\nScope: %s\n%sDone when: %s\n\n" % (tid, scope, more, done_when)


def run(tmp_path, plan, *subjects):
    r = tmp_path / "ws"
    (r / "docs").mkdir(parents=True)
    (r / "docs" / "BUILD_PLAN.md").write_text(HEAD + plan, encoding="utf-8")
    git(r, "init", "-q", "-b", "main")
    git(r, "add", "-A")
    git(r, "commit", "-q", "-m", "scratch")
    for s in subjects:
        git(r, "commit", "-q", "--allow-empty", "-m", s)
    p = subprocess.run([sys.executable, PROG, "--base", "main"], cwd=str(r), capture_output=True, text=True, env=ENV, timeout=120)
    return p.returncode, p.stdout + p.stderr


def large(out):
    return [l for l in out.splitlines() if l.startswith("note: large increment: ")]


CLAUSES = "; ".join("clause %d holds" % i for i in range(1, 14))
BULLETS = "all of these hold\n" + "".join("- item %d\n" % i for i in range(1, 14))
LETTERED = " ".join("(%s) part %s holds," % (c, c) for c in "abcdefghijklmn")


@pytest.mark.parametrize("done_when,count", [(CLAUSES, 13), (BULLETS.rstrip("\n"), 13), (LETTERED, 14)])
def test_more_than_twelve_acceptance_items_are_noted_in_each_form(tmp_path, done_when, count):
    rc, out = run(tmp_path, increment("TASK-001", done_when))
    assert rc == 0 and "RESULT: OK" in out, out
    assert large(out) == ["note: large increment: TASK-001 has %d acceptance item(s) in its Done when and 1 Scope path(s); above 12 of either an increment "
                          "tends to need more rounds than the ceiling gives: consider splitting it before its first brief (a note, never a failure)" % count], out


def test_twelve_items_and_twelve_paths_are_not_noted_and_thirteen_paths_are(tmp_path):
    twelve = "; ".join("clause %d holds" % i for i in range(1, 13))
    paths12 = ", ".join("src/f%d.py" % i for i in range(12))
    rc, out = run(tmp_path, increment("TASK-001", twelve, scope=paths12))
    assert rc == 0 and large(out) == [], out
    rc, out = run(tmp_path / "second", increment("TASK-001", "it works", scope=paths12 + ", src/f12.py"))
    assert rc == 0 and len(large(out)) == 1 and "TASK-001 has 1 acceptance item(s) in its Done when and 13 Scope path(s)" in out, out


def test_the_field_ends_at_the_next_field_heading_or_empty_line(tmp_path):
    """Thirteen semicolons after the field's end, in a field that follows, in prose after an empty line and in the next
    increment's own short field, are not this field's items."""
    after = "Notes: " + CLAUSES + "\n"
    plan = ("### TASK-001 — an increment\nSatisfies: R-001\nScope: src/a.py\nDone when: it works; it is tested\n" + after + "\n"
            "Prose after an empty line: " + CLAUSES + "\n\n" + increment("TASK-002", "it works", scope="src/b.py"))
    rc, out = run(tmp_path, plan)
    assert rc == 0 and large(out) == [], out


def test_a_merged_or_deferred_increment_is_not_noted(tmp_path):
    """The note is for work not yet briefed: what is merged is done, and what the owner deferred is not being built."""
    plan = (increment("TASK-001", CLAUSES) + increment("TASK-002", CLAUSES, scope="src/b.py", more="Deferred: owner 2026-11-11\n")
            + increment("TASK-003", CLAUSES, scope="src/c.py"))
    rc, out = run(tmp_path, plan, "TASK-001: merged (#1)")
    assert rc == 0 and [l.split(":")[2].split()[0] for l in large(out)] == ["TASK-003"], out


def test_the_note_changes_neither_the_exit_code_nor_a_failing_result(tmp_path):
    plan = increment("TASK-001", CLAUSES) + "### TASK-002 — no scope\nSatisfies: R-002\nDone when: " + CLAUSES + "\n"
    rc, out = run(tmp_path, plan)
    assert rc == 1 and "SHAPE: TASK-002 has no Scope" in out and "RESULT: 1 problem(s)" in out and len(large(out)) == 2, out
