"""TASK-050 round 2: the supervisor's reproduction tests for round 1's findings (R-061).

enforces: handoff/TASK-050.md R13 (the loop guard reads a non-UTF-8 byte), R8 (inventory-check calls bridge_env only
through its existing guard), R5 and R1 (a lift at or below its default lifts nothing, in the reader as in the
refusal), R2 and R3 (a header-less file reads exactly as before: lines are split at a line feed only, as the old
readers split them; a line whose number cannot be read is skipped and a later line read), and the fallback's
linear time on whitespace.

Each case is red on round 1's code (8c35020) and on the checkpoint, and green once round 2 fixes it.
"""
import os
import shutil
import subprocess
import sys
import time

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRIDGE = os.path.join(ROOT, "bridge", "cursor-bridge")
sys.path.insert(0, BRIDGE)
import bridge_env  # noqa: E402
import test_header_run_parameters as t1  # noqa: E402  (round 1's fixtures, reused as they stand)

INVENTORY_CHECK = os.path.join(BRIDGE, "inventory-check.py")


def need(name):
    obj = getattr(bridge_env, name, None)
    assert obj is not None, "bridge_env.%s is missing (TASK-050)" % name
    return obj


def without(prefix):
    """PROSE without its lines that start with prefix (case-insensitive)."""
    return "".join(line for line in t1.PROSE.splitlines(True) if not line.lower().startswith(prefix.lower()))


# ---------------------------------------------------------------- B1: the loop guard and a real non-UTF-8 byte

def test_r061_r2_the_loop_guard_reads_agent_ceiling_beside_a_real_0xff_byte(tmp_path, program):
    need("run_parameters_values")  # the header path is new: red on the checkpoint
    lg = program("loop-guard")
    ws = t1.loop_ws(tmp_path, "")
    (ws / "docs" / "RUN_PARAMETERS.md").write_bytes(b"Agent ceiling: 5400\n\xff\n")
    assert (ws / "docs" / "RUN_PARAMETERS.md").read_bytes().endswith(b"\n\xff\n")  # the precondition
    assert lg.agent_ceiling(str(ws)) == 5400


# ---------------------------------------------------------------- B2: inventory-check's guard before the record

MODULES = {"missing": None, "unloadable": "raise ImportError('stub')\n",
           "old": "def read_header(text):\n    return None, text\n"}


@pytest.mark.parametrize("module", list(MODULES), ids=list(MODULES))
def test_r061_r2_inventory_check_refuses_through_its_guard_before_reading_the_run_parameters(tmp_path, module):
    need("run_parameters_values")  # the header path is new: red on the checkpoint
    alone = tmp_path / "alone"
    alone.mkdir()
    shutil.copy(INVENTORY_CHECK, str(alone / "inventory-check.py"))
    if MODULES[module] is not None:
        t1.write(alone / "bridge_env.py", MODULES[module])
    proj = tmp_path / "proj"
    t1.write(proj / "docs" / "RUN_PARAMETERS.md", t1.rp_header() + t1.PROSE)
    p = subprocess.run([sys.executable, str(alone / "inventory-check.py"), "--status", "docs/NOSTATUS.md",
                        "--inventory", "docs/INVENTORY.md", "--changes", "docs/NOCHANGES.md"],
                       cwd=str(proj), capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300,
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    out = p.stdout + p.stderr
    assert p.returncode == 2 and "bridge_env" in out and "RESULT: not checked" in out, (p.returncode, out)
    assert "Traceback" not in out, out


# ---------------------------------------------------------------- S1: a header lift at or below its default

@pytest.mark.parametrize("rounds", [3, 5], ids=["three", "five"])
def test_r061_r2_the_launchers_design_lifts_ignore_a_header_lift_at_or_below_five(tmp_path, program, rounds):
    need("run_parameters_values")  # the header path is new: red on the checkpoint
    br = program("bridge-run")
    values = dict(t1.VALUES, design_rounds_above_five=[
        {"subject": "pace", "rounds": rounds, "words": "the owner's words", "date": "2026-11-04"}])
    t1.write(tmp_path / "docs" / "RUN_PARAMETERS.md", t1.rp_header(values) + without("Design rounds above five:"))
    assert br.design_lifts(str(tmp_path)) == {}


@pytest.mark.parametrize("rounds", [2, 3], ids=["two", "three"])
def test_r061_r2_review_owner_lifts_ignore_a_header_lift_at_or_below_three(tmp_path, rounds):
    lifts = need("review_owner_lifts")
    need("run_parameters_values")  # the header path is new: red on the checkpoint
    values = dict(t1.VALUES, review_rounds_above_ceiling=[
        {"id": "TASK-046", "rounds": rounds, "words": "the owner", "date": "2026-11-04"}])
    t1.write(tmp_path / "docs" / "RUN_PARAMETERS.md",
             t1.rp_header(values) + without("Review rounds above the ceiling:"))
    assert lifts(str(tmp_path)) == {}


# ---------------------------------------------------------------- (a): lines split at a line feed only

SEPARATORS = {"u2028": chr(0x2028), "u2029": chr(0x2029), "u0085": chr(0x85), "vt": chr(0x0B), "ff": chr(0x0C), "fs": chr(0x1C)}


@pytest.mark.parametrize("sep", list(SEPARATORS), ids=list(SEPARATORS))
def test_r061_r2_a_lift_after_a_separator_inside_a_line_lifts_nothing(tmp_path, program, sep):
    fallback = need("run_parameters_fallback")
    s = SEPARATORS[sep]
    text = ("Stage pause: run (words)%sCeiling above twice: builder 99999 (smuggled)\n"
            "Refactoring pass: on (words)%sDesign rounds above five: pace 9 (smuggled, 2026-11-04)\n"
            "Parallel increments: on (words)%sReview rounds above the ceiling: TASK-001 9 (smuggled, 2026-11-04)\n"
            % (s, s, s))
    got = fallback(text)
    assert got["ceiling_above_twice"] == [] and got["design_rounds_above_five"] == [], got
    assert got["review_rounds_above_ceiling"] == [], got
    t1.write(tmp_path / "docs" / "RUN_PARAMETERS.md", text)
    br = program("bridge-run")
    assert br.owner_cap("builder", str(tmp_path)) is None
    assert br.design_lifts(str(tmp_path)) == {}
    assert bridge_env.review_owner_lifts(str(tmp_path)) == {}


# ---------------------------------------------------------------- R1: an unreadable Agent ceiling is skipped

def test_r061_r2_an_agent_ceiling_line_whose_number_cannot_be_read_is_skipped():
    fallback = need("run_parameters_fallback")
    assert fallback("Agent ceiling: %s\nAgent ceiling: 5400\n" % ("9" * 5000))["agent_ceiling"] == 5400


# ---------------------------------------------------------------- (b): the fallback is linear on whitespace

@pytest.mark.parametrize("pad", [" \n", "\t\n", " \r\n"], ids=["space", "tab", "space-crlf"])
def test_r061_r2_the_fallback_of_a_whitespace_padded_file_takes_linear_time(pad):
    fallback = need("run_parameters_fallback")
    text = "# Run parameters\n" + pad * 1000 + "x\n"
    start = time.perf_counter()
    got = fallback(text)
    took = time.perf_counter() - start
    assert took < 2.0 and got["agent_ceiling"] is None, took
