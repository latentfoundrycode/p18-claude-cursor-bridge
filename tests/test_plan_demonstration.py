"""plan-check.py (release A1b, the 2026.10.06b review's finding 6): a stage of the build plan
names what is demonstrated live at its close; a stage with increments and no such line is noted."""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROG = os.path.join(HERE, os.pardir, "bridge", "cursor-bridge", "plan-check.py")

PLAN = """# Build plan

## Overview

Two stages.

## Stage 1 - skeleton

Demonstration: the app starts from a cold start and shows an empty list.

### TASK-001 - first
- Kind: increment
- Depends on: none
- Parallel: no
- Satisfies: R-001
- Diagrams: none
- Scope: app/

## Stage 2 - search

### TASK-002 - second
- Depends on: TASK-001
- Satisfies: R-002
- Diagrams: none
- Scope: app/search.py
"""


def run(cwd, plan):
    p = subprocess.run([sys.executable, PROG, "--no-git", "--plan", plan], capture_output=True, text=True, cwd=str(cwd))
    return p.returncode, p.stdout + p.stderr


def test_a_stage_without_a_demonstration_line_is_noted_and_the_others_are_not(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "BUILD_PLAN.md").write_text(PLAN, encoding="utf-8")
    rc, out = run(tmp_path, "docs/BUILD_PLAN.md")
    assert rc == 0 and "RESULT: OK" in out, out
    notes = [l for l in out.splitlines() if "names no Demonstration" in l]
    assert len(notes) == 1 and "Stage 2 - search" in notes[0], out
    assert "Overview" not in notes[0], "a heading without increments is not a stage"
    (tmp_path / "docs" / "BUILD_PLAN.md").write_text(PLAN.replace("## Stage 2 - search\n", "## Stage 2 - search\n\n- **Demonstration:** a search for 'x' returns the seeded row.\n"), encoding="utf-8")
    rc, out = run(tmp_path, "docs/BUILD_PLAN.md")
    assert rc == 0 and "names no Demonstration" not in out, out
