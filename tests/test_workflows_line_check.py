"""The Workflows status line enforced (TASK-008), the supervisor's tests, written from handoff/TASK-008.md before the
delegation.

enforces: docs/REQUIREMENTS.md R-015 (the status file records a `Workflows:` line per part, beside the `Phase:` line):
inventory-check.py and conformance-check.py report a missing line, a malformed line and lines that do not stand together
right after `Phase:`, judging the grammar by workflow-check.py's check_status and the placement by its new
check_placement; a rule file that cannot be loaded is a failure; output stays ASCII; lines are split only at a line feed
(TASK-006's lesson). Special characters are built with chr() so no editing tool can turn an escape into the character.
"""
import os
import pathlib
import shutil
import subprocess
import sys

import pytest

from test_conformance_check import VERSION, make_workspace, verdict

REPO = pathlib.Path(__file__).resolve().parent.parent
BRIDGE = REPO / "bridge" / "cursor-bridge"
INVENTORY_CHECK = BRIDGE / "inventory-check.py"
CONFORMANCE_CHECK = BRIDGE / "conformance-check.py"
FF = chr(12)
LSEP = chr(0x2028)
ARROW = chr(0x2192)

HEAD = "# Project Status\nBridge version: %s\nPhase: building\n" % VERSION
BRIDGE_LINE = "Workflows: Host Extension Development " + ARROW + " Claude Code Extension; traits: Installable\n"
UNCLASSIFIED = "Workflows: not yet classified\n"

VALID = {
    "bridge-line": HEAD + BRIDGE_LINE,
    "not-yet-classified": HEAD + UNCLASSIFIED,
}
MISSING = {
    "no-line": HEAD,
    "joined-by-form-feed": HEAD.rstrip("\n") + FF + UNCLASSIFIED,
    "joined-by-line-separator": HEAD.rstrip("\n") + LSEP + UNCLASSIFIED,
}
MALFORMED = {
    # (status text, the reason that must be named)
    "no-traits": (HEAD + "Workflows: Host Extension Development\n", "Workflows line must contain '; traits: ' exactly once"),
    "unknown-name": (HEAD + "Workflows: Nonexistent Development; traits: none\n", "name is not in the open list"),
    "line-between": ("# Project Status\nPhase: building\nBridge version: %s\n" % VERSION + UNCLASSIFIED,
                     "Workflows lines do not stand together right after the Phase line"),
    "above-phase": ("# Project Status\nBridge version: %s\n" % VERSION + UNCLASSIFIED + "Phase: building\n",
                    "Workflows lines do not stand together right after the Phase line"),
    "no-phase-line": ("# Project Status\nBridge version: %s\n" % VERSION + UNCLASSIFIED, "status file has no Phase line"),
}


def write_status(path, text):
    path.write_text(text, encoding="utf-8", newline="\n")


def inventory(cwd, status, program=INVENTORY_CHECK):
    """inventory-check.py on one status file, with no inventory or change log, from a folder of its own."""
    p = subprocess.run([sys.executable, str(program), "--inventory", "absent-inventory.md", "--changes", "absent-changes.md",
                        "--status", str(status)], cwd=str(cwd), capture_output=True, text=True, encoding="utf-8",
                       errors="replace", creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    return p.returncode, p.stdout.splitlines(), p.stdout, p.stderr


def workflows_lines(lines):
    return [line for line in lines if line.startswith("WORKFLOWS LINE:")]


def conformance(root, program=CONFORMANCE_CHECK):
    p = subprocess.run([sys.executable, str(program), str(root), "--offline"], capture_output=True, text=True, encoding="utf-8",
                       errors="replace", creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    return p.returncode, p.stdout, p.stderr


def workspace(tmp_path, status_text):
    root = tmp_path / "proj"
    root.mkdir()
    make_workspace(root)
    write_status(root / "docs" / "PROJECT_STATUS.md", status_text)
    return root


# --- check_placement, the one new function in workflow-check.py --------------------------------------------------

def test_r015_placement_function(program):
    mod = program("workflow-check")
    assert mod.check_placement("s.md", HEAD) == [], "no Workflows line: missing is check_status's finding"
    assert mod.check_placement("s.md", HEAD + UNCLASSIFIED) == []
    two = "Phase: building\nWorkflows: app: not yet classified\nWorkflows: site: not yet classified\nOther: x\n"
    assert mod.check_placement("s.md", two) == []
    apart = "Phase: building\nWorkflows: app: not yet classified\nOther: x\nWorkflows: site: not yet classified\n"
    assert mod.check_placement("d\\s.md", apart) == [("place", "d/s.md", "-", "Workflows lines do not stand together right after the Phase line")]
    assert mod.check_placement("s.md", "Workflows: not yet classified\n") == [("place", "s.md", "-", "status file has no Phase line")]
    assert mod.check_placement("s.md", "Phase: building" + FF + "x\n" + UNCLASSIFIED) == [], "a form feed does not end the Phase line"
    assert mod.check_placement("s.md", "Phase: a\nPhase: b\n" + UNCLASSIFIED) == [("place", "s.md", "-", "Workflows lines do not stand together right after the Phase line")], "the first Phase line counts"


# --- inventory-check.py --------------------------------------------------------------------------------------------

@pytest.mark.parametrize("case", sorted(VALID))
def test_r015_inventory_valid_line_reports_nothing(tmp_path, case):
    status = tmp_path / "PROJECT_STATUS.md"
    write_status(status, VALID[case])
    rc, lines, out, err = inventory(tmp_path, status)
    assert "Traceback" not in err, err
    assert workflows_lines(lines) == [], lines


@pytest.mark.parametrize("case", sorted(MISSING))
def test_r015_inventory_missing_line(tmp_path, case):
    status = tmp_path / "PROJECT_STATUS.md"
    write_status(status, MISSING[case])
    rc, lines, out, err = inventory(tmp_path, status)
    assert rc == 1, lines
    shown = str(status).replace("\\", "/")
    assert workflows_lines(lines) == [f"WORKFLOWS LINE: missing: {shown} has no Workflows line"], lines


@pytest.mark.parametrize("case", sorted(MALFORMED))
def test_r015_inventory_malformed_line(tmp_path, case):
    text, reason = MALFORMED[case]
    status = tmp_path / "PROJECT_STATUS.md"
    write_status(status, text)
    rc, lines, out, err = inventory(tmp_path, status)
    assert rc == 1, lines
    found = workflows_lines(lines)
    assert found and all(line.startswith("WORKFLOWS LINE: malformed: ") for line in found), lines
    assert any(line.endswith(" - " + reason) for line in found), lines


def test_r015_inventory_unwritten_types_are_not_malformed(tmp_path):
    """Codes f and FLAG (unwritten type, sub-type, trait) are workflow-check.py's concern, not a failure here."""
    status = tmp_path / "PROJECT_STATUS.md"
    write_status(status, VALID["bridge-line"])
    rc, lines, out, err = inventory(tmp_path, status)
    assert not [line for line in lines if "not written" in line], lines


def test_r015_inventory_counts_each_finding_as_a_problem(tmp_path):
    """A malformed line is a failure line, counted in RESULT."""
    status = tmp_path / "PROJECT_STATUS.md"
    write_status(status, VALID["not-yet-classified"])
    rc_ok, lines_ok, *_ = inventory(tmp_path, status)
    write_status(status, MALFORMED["no-traits"][0])
    rc_bad, lines_bad, *_ = inventory(tmp_path, status)

    def count(lines):
        last = lines[-1]
        return 0 if last == "RESULT: OK" else int(last.split()[1])

    assert count(lines_bad) == count(lines_ok) + len(workflows_lines(lines_bad)), (lines_ok, lines_bad)


def test_r015_inventory_output_is_ascii(tmp_path):
    status = tmp_path / "PROJECT_STATUS.md"
    write_status(status, HEAD + "Workflows: " + chr(0xDC) + "nknown" + chr(0x1B) + "[31m; traits: none\n")
    rc, lines, out, err = inventory(tmp_path, status)
    assert rc == 1
    assert out.isascii(), repr(out)
    assert "\\xdc" in out and "\\x1b" in out, out


def test_r015_inventory_no_status_file_no_check(tmp_path):
    rc, lines, out, err = inventory(tmp_path, tmp_path / "absent-status.md")
    assert workflows_lines(lines) == [], lines


def _bridge_copy(tmp_path, with_checker=True, with_rules=True):
    """The two programs, in a folder of their own, with or without workflow-check.py and its rule files."""
    folder = tmp_path / "bin"
    folder.mkdir()
    for name in ("inventory-check.py", "conformance-check.py"):
        shutil.copyfile(BRIDGE / name, folder / name)
    if with_checker:
        shutil.copyfile(BRIDGE / "workflow-check.py", folder / "workflow-check.py")
    if with_rules:
        shutil.copytree(BRIDGE / "workflow", folder / "workflow")
    return folder


@pytest.mark.parametrize("missing", ["checker", "rules"])
def test_r015_inventory_rule_files_not_loadable_is_a_failure(tmp_path, missing):
    folder = _bridge_copy(tmp_path, with_checker=(missing != "checker"), with_rules=(missing != "rules"))
    status = tmp_path / "PROJECT_STATUS.md"
    write_status(status, VALID["not-yet-classified"])
    rc, lines, out, err = inventory(tmp_path, status, program=folder / "inventory-check.py")
    assert "Traceback" not in err and "Traceback" not in out, (out, err)
    assert rc == 1, lines
    found = workflows_lines(lines)
    assert found and all(line.startswith("WORKFLOWS LINE: not checked: ") for line in found), lines
    if missing == "checker":
        assert any("cannot be loaded" in line for line in found), lines


# --- conformance-check.py ------------------------------------------------------------------------------------------

@pytest.mark.parametrize("case", sorted(VALID))
def test_r015_conformance_valid_line_is_ok(tmp_path, case):
    rc, out, err = conformance(workspace(tmp_path, VALID[case]))
    assert verdict(out, "Workflows line") == ("OK", "Workflows line"), out
    assert rc == 0 and "RESULT: CONFORMANT" in out, out


@pytest.mark.parametrize("case", sorted(MISSING))
def test_r015_conformance_missing_line(tmp_path, case):
    rc, out, err = conformance(workspace(tmp_path, MISSING[case]))
    v, text = verdict(out, "Workflows line")
    assert v == "MISSING" and text == "Workflows line  - missing: docs/PROJECT_STATUS.md has no Workflows line", out
    assert rc == 1


@pytest.mark.parametrize("case", sorted(MALFORMED))
def test_r015_conformance_malformed_line(tmp_path, case):
    text_in, reason = MALFORMED[case]
    rc, out, err = conformance(workspace(tmp_path, text_in))
    v, text = verdict(out, "Workflows line")
    assert v == "MISSING" and text.startswith("Workflows line  - malformed: "), out
    assert reason in text, out
    assert rc == 1


def test_r015_conformance_output_is_ascii(tmp_path):
    rc, out, err = conformance(workspace(tmp_path, HEAD + "Workflows: " + chr(0xDC) + "nknown; traits: none\n"))
    assert rc == 1 and out.isascii(), repr(out)
    assert "\\xdc" in out, out


@pytest.mark.parametrize("missing", ["checker", "rules"])
def test_r015_conformance_rule_files_not_loadable_is_missing(tmp_path, missing):
    folder = _bridge_copy(tmp_path, with_checker=(missing != "checker"), with_rules=(missing != "rules"))
    rc, out, err = conformance(workspace(tmp_path, VALID["not-yet-classified"]), program=folder / "conformance-check.py")
    assert "Traceback" not in err and "Traceback" not in out, (out, err)
    v, text = verdict(out, "Workflows line")
    assert v == "MISSING" and text.startswith("Workflows line  - not checked: "), out
