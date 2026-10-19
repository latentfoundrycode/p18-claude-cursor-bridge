"""Stage B2's least-confident items 2 and 3 (docs/HARDENING.md, "Stage B2 — least confident"), settled by tests before
stage B3's first plan delegation (FIX-002).

enforces: docs/REQUIREMENTS.md R-015 (the status file records a `Workflows:` line per part, right after `Phase:`, judged
by inventory-check.py and conformance-check.py through workflow-check.py) on status files shaped like the other
projects' real ones, and the bridge's own status line failing for the stated reasons only (docs/BUILD_PLAN.md:84; the
reasons go when TASK-017 writes Installable and TASK-021 the type and sub-type, BUILD_PLAN.md:242).

Item 2's shapes are built here, not copied: the other projects' status files hold their own records and computer
paths, and this repository is public. Each shape keeps what the judges could trip on, read from the real file on
2026-10-19 by the supervisor (counts and field names only): its line endings, its field names in their order, its
headed sections, its size, and non-ASCII text. The content is invented. Supervisor-authored.
"""
import pathlib
import subprocess
import sys

import pytest

from test_conformance_check import make_workspace, verdict
from test_workflows_line_check import conformance, inventory, workflows_lines

REPO = pathlib.Path(__file__).resolve().parent.parent
WORKFLOW_CHECK = REPO / "bridge" / "cursor-bridge" / "workflow-check.py"
ARROW = chr(0x2192)
DASH = chr(0x2014)

# The field names of each project's status file in their order, and its other traits (read 2026-10-19).
SHAPES = {
    "reangle": {
        "newline": "\r\n",
        "chars": 10400,
        "fields": ["Last updated", "Phase", "Change cycle", "Increment", "Last accepted", "Awaiting user on", "Next",
                   "Deviations accepted", "Terms fixed", "Software name", "Layout", "Worktrees", "In flight",
                   "Working files", "Delegated gates", "Remote sync", "Stage", "Open issues", "Bridge version",
                   "Calibrated", "Maintainer requests", "Calibration pending", "Run parameters", "Budget", "Model roster",
                   "Verify under Linux CI", "Read at resume"],
        "sections": ["Essentials for a fresh resume"],
        "workflows": ["Web App Development " + ARROW + " Local Web App; traits: Has screens, Installable, Long-running process"],
    },
    "tdp": {
        "newline": "\n",
        "chars": 11800,
        "fields": ["Last updated", "Phase", "Change cycle", "Increment", "Last accepted", "Awaiting user on", "Next",
                   "Deviations accepted", "Terms fixed", "Software name", "Layout", "Worktrees", "In flight",
                   "Working files", "Delegated gates", "Remote sync", "Stage", "Open issues", "Maintainer requests",
                   "Bridge version", "Calibrated", "Calibration pending", "Run parameters", "Model roster", "Lock command",
                   "Migration regime"],
        "sections": ["Product state (current)"],
        "workflows": ["Own-Computer Software Development " + ARROW + " Local Service Software; traits: Installable, "
                      "Long-running process"],
    },
    "video-factory": {
        "newline": "\n",
        "chars": 9500,
        "fields": ["Last updated", "Phase", "Change cycle", "Increment", "Last accepted", "Awaiting user on", "Next",
                   "Deviations accepted", "Terms fixed", "Software name", "Layout", "Worktrees", "In flight",
                   "Working files", "Remote sync", "Stage", "Open issues", "Bridge version", "Calibrated",
                   "Calibration pending", "Delegated gates", "Roster", "Run parameters"],
        "sections": ["Where the product stands vs its PRD", "Fresh-session pickup"],
        "workflows": ["Web App Development " + ARROW + " Local Web App; traits: Has screens, Installable, Long-running process"],
    },
}
VERSION_VALUE = "2026.10.18a"
FILLER = ("an invented value " + DASH + " it names a stage, an increment and a pull request (#12), says what is next "
          "and why; it holds colons: and semicolons; and the words Phase and Workflows in the middle of a sentence")


LONG_FIELDS = ("Last accepted", "Next", "Working files")


def _value(field, repeat):
    if field == "Phase":
        return "building"
    if field == "Bridge version":
        return VERSION_VALUE
    if field == "Layout":
        return "Workspace=<project root>\\Workspace  Documents=<project root>\\Documents"
    return "; ".join([FILLER] * (repeat if field in LONG_FIELDS else 1))


def shaped_status(shape, workflows=None, workflows_after="Phase"):
    """A status file in one project's shape: its fields in order, a `Workflows:` line per part right after the field
    named by workflows_after (Phase by default; None leaves it out), its sections with bullets that start like fields.
    The three long fields are repeated until the file has about the real file's size."""
    spec = SHAPES[shape]
    base = len(_build(spec, 1, workflows, workflows_after))
    repeat = 1 + max(0, spec["chars"] - base) // (len(LONG_FIELDS) * (len(FILLER) + 2))
    return _build(spec, repeat, workflows, workflows_after)


def _build(spec, repeat, workflows, workflows_after):
    lines = ["# Project Status"]
    for field in spec["fields"]:
        lines.append("%s: %s" % (field, _value(field, repeat)))
        if field == workflows_after:
            lines.extend("Workflows: " + w for w in (spec["workflows"] if workflows is None else workflows))
    for heading in spec["sections"]:
        lines += ["", "## " + heading, "- Phase: a bullet that starts like a field " + DASH + " not one",
                  "- Workflows: a bullet that starts like the line " + DASH + " not one", "- " + FILLER]
    return spec["newline"].join(lines) + spec["newline"]


def write_bytes(path, text):
    path.write_bytes(text.encode("utf-8"))


def other_findings(lines):
    """inventory-check.py's findings that are not about the Workflows line: every line but its notes, its RESULT and
    the absent inventory the shared helper passes on purpose (test_workflows_line_check.inventory)."""
    return [l for l in lines if not l.startswith(("note:", "RESULT: ", "WORKFLOWS LINE: "))
            and l != "MISSING: absent-inventory.md does not exist"]


@pytest.mark.parametrize("shape", sorted(SHAPES))
def test_fix002_each_shape_holds_what_the_judges_could_trip_on(shape):
    """The fixtures keep the traits named in the docstring, so the tests below test them."""
    text = shaped_status(shape)
    newline = SHAPES[shape]["newline"]
    assert text.count(newline) == len(text.splitlines())
    assert ("\r\n" in text) is (newline == "\r\n")
    assert any(ord(c) > 127 for c in text)
    assert abs(len(text) - SHAPES[shape]["chars"]) < 600 and len(text) < 12000, len(text)
    lines = text.splitlines()
    assert lines[lines.index("Phase: building") + 1].startswith("Workflows: ")
    assert [l.split(":")[0] for l in lines[1:] if ": " in l and not l.startswith(("- ", "## ", "Workflows: "))] == \
        SHAPES[shape]["fields"]


@pytest.mark.parametrize("shape", sorted(SHAPES))
def test_fix002_inventory_check_judges_a_shaped_status_file_by_its_line_alone(tmp_path, shape):
    """A valid constructed line in each project's shape: no Workflows finding and no other finding about the file."""
    status = tmp_path / "PROJECT_STATUS.md"
    write_bytes(status, shaped_status(shape))
    rc, lines, out, err = inventory(tmp_path, status)
    assert "Traceback" not in err, err
    assert workflows_lines(lines) == [], lines
    assert other_findings(lines) == [], lines
    assert "MISSING: absent-inventory.md does not exist" in lines and lines[-1] == "RESULT: 1 problem(s)", lines


@pytest.mark.parametrize("shape", sorted(SHAPES))
def test_fix002_conformance_check_judges_a_shaped_status_file_by_its_line_alone(tmp_path, shape):
    root = tmp_path / "proj"
    root.mkdir()
    make_workspace(root)
    write_bytes(root / "docs" / "PROJECT_STATUS.md", shaped_status(shape))
    rc, out, err = conformance(root)
    assert "Traceback" not in err, err
    assert verdict(out, "Workflows line") == ("OK", "Workflows line"), out
    assert rc == 0 and out.splitlines()[-1] == "RESULT: CONFORMANT", out


BROKEN = {
    # (the Workflows lines, the field they follow, the reason each judge must name)
    "unknown-name": (["Nonexistent Development; traits: none"], "Phase", "name is not in the open list"),
    "placed-after-another-field": (None, "Change cycle", "Workflows lines do not stand together right after the Phase line"),
    "no-traits": (["Web App Development"], "Phase", "Workflows line must contain '; traits: ' exactly once"),
}


@pytest.mark.parametrize("case", sorted(BROKEN))
@pytest.mark.parametrize("shape", sorted(SHAPES))
def test_fix002_a_broken_line_in_a_shaped_file_is_the_one_finding(tmp_path, shape, case):
    """The shapes do not hide a broken line: each judge reports it, with the reason named, and nothing else about the
    file (an unknown name is also a part with no product type: two findings, both about the line)."""
    workflows, after, reason = BROKEN[case]
    text = shaped_status(shape, workflows=workflows, workflows_after=after)
    status = tmp_path / "PROJECT_STATUS.md"
    write_bytes(status, text)
    rc, lines, out, err = inventory(tmp_path, status)
    found = workflows_lines(lines)
    assert rc == 1 and found and reason in found[0], lines
    assert other_findings(lines) == [], lines
    assert lines[-1] == "RESULT: %d problem(s)" % (len(found) + 1), lines
    root = tmp_path / "proj"
    root.mkdir()
    make_workspace(root)
    write_bytes(root / "docs" / "PROJECT_STATUS.md", text)
    rc, out, err = conformance(root)
    v, shown = verdict(out, "Workflows line")
    assert v == "MISSING" and reason in shown, out
    assert [l for l in out.splitlines() if l.strip().startswith("MISSING")] == [l for l in out.splitlines()
                                                                                 if "Workflows line" in l], out


def test_fix002_the_bridge_status_line_fails_for_the_stated_reasons_only():
    """Item 3: the bridge's own status file, run through workflow-check.py --status, gives exactly the two (f) findings
    and the FLAG the plan expects. TASK-017 (Installable written: the FLAG goes) and TASK-021 (the type and sub-type
    written: RESULT OK) take this test into their Scope and change the pin."""
    p = subprocess.run([sys.executable, str(WORKFLOW_CHECK), "--status", "docs/PROJECT_STATUS.md"], cwd=str(REPO),
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert p.stderr == "", p.stderr
    assert p.returncode == 1
    assert p.stdout.splitlines() == [
        "FAIL (f) docs/PROJECT_STATUS.md: Host Extension Development - product type is not written",
        "FAIL (f) docs/PROJECT_STATUS.md: Claude Code Extension - sub-type is not written",
        "FLAG (trait) docs/PROJECT_STATUS.md: Installable - trait not yet written; flagged, work continues (non-fatal)",
        "RESULT: 2 problem(s)",
    ]
