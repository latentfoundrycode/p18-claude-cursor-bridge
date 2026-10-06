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


def run(cwd, plan, *extra):
    p = subprocess.run([sys.executable, PROG, "--plan", plan] + (list(extra) or ["--no-git"]), capture_output=True, text=True, cwd=str(cwd))
    return p.returncode, p.stdout + p.stderr


def git(repo, *args):
    p = subprocess.run(["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@example.invalid"] + list(args), capture_output=True, text=True)
    assert p.returncode == 0, p.stdout + p.stderr


def test_a_closed_stage_is_not_noted(tmp_path):
    """Second pass of the 2026.10.06b review, S9: only a stage with an unmerged increment is noted."""
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "BUILD_PLAN.md").write_text(PLAN.replace("Demonstration: the app starts from a cold start and shows an empty list.\n", ""), encoding="utf-8")
    git(tmp_path, "init", "-q", "-b", "main")
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-q", "-m", "TASK-001 - first")
    rc, out = run(tmp_path, "docs/BUILD_PLAN.md", "--base", "main")
    notes = [l for l in out.splitlines() if "names no Demonstration" in l]
    assert len(notes) == 1 and "Stage 2 - search" in notes[0], "Stage 1 is closed (its increment merged): " + out
    git(tmp_path, "commit", "-q", "--allow-empty", "-m", "TASK-002 - second")
    rc, out = run(tmp_path, "docs/BUILD_PLAN.md", "--base", "main")
    assert "names no Demonstration" not in out, out


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
