"""Calibration program grades for conditional workflows (TASK-024).

enforces: docs/REQUIREMENTS.md R-027 (calibration applies conditional workflows by phase) and R-033 (workflow check
at every calibration).
"""
import importlib.util
import pathlib
import sys

import pytest

from test_conformance_check import VERSION, verdict
from test_workflows_line_check import (
    ARROW,
    BRIDGE_LINE,
    HEAD,
    VALID,
    _bridge_copy,
    _load_copy,
    _unwritten_copy,
    conformance,
    workspace,
)

REPO = pathlib.Path(__file__).resolve().parent.parent
BRIDGE = REPO / "bridge" / "cursor-bridge"
BRIDGE_STATUS = REPO / "docs" / "PROJECT_STATUS.md"

CLASSIFICATION_BUILDING = (
    "Workflows classification  - unclassified past intake (Phase: building); calibration step 4b classifies it, "
    "the project running on the main workflow alone meanwhile"
)
TRAIT_NOTE_PERSONAL = (
    "Unwritten trait  - Personal data - trait not yet written; flagged, work continues (non-fatal)"
)
TRAIT_NOTE_INSTALLABLE = (
    "Unwritten trait  - Installable - trait not yet written; flagged, work continues (non-fatal)"
)


def rows_for_floor(out, floor):
    return [line for line in out.splitlines() if line.strip().startswith(("OK", "MISSING", "NOTE")) and floor in line]


def _ascii_field(mod, value):
    text = mod.escape_field(value)
    return text.encode("ascii", "backslashreplace").decode("ascii")


def _load_workflow_checker():
    spec = importlib.util.spec_from_file_location("workflow_check_ws", BRIDGE / "workflow-check.py")
    mod = importlib.util.module_from_spec(spec)
    before = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.dont_write_bytecode = before
    return mod


def _load_conformance_copy(folder):
    spec = importlib.util.spec_from_file_location("conformance_check_copy", folder / "conformance-check.py")
    mod = importlib.util.module_from_spec(spec)
    before = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.dont_write_bytecode = before
    return mod


def _assert_check_status_precondition(mod, status_text, expected):
    open_text, _, open_err = mod.read_utf8(mod.DEFAULT_OPEN)
    reg_text, _, reg_err = mod.read_utf8(mod.DEFAULT_REGISTRY)
    assert open_err is None and reg_err is None
    tables, errors = mod.load_tables(open_text, mod.DEFAULT_OPEN, reg_text, mod.DEFAULT_REGISTRY)
    assert not errors
    findings = mod.check_status("s.md", status_text, tables)
    assert findings == expected, findings
    return tables


def test_r027_r033_classified_written_workflows_only(tmp_path):
    """R-027 R-033 (a): written workflows only — Workflows line OK, no calibration NOTE rows."""
    rc, out, err = conformance(workspace(tmp_path, HEAD + BRIDGE_LINE))
    assert "Traceback" not in err, err
    assert verdict(out, "Workflows line") == ("OK", "Workflows line"), out
    assert rows_for_floor(out, "Unwritten trait") == [], out
    assert rows_for_floor(out, "Workflows classification") == [], out
    assert rc == 0


def test_r027_r033_not_yet_classified_at_intake(tmp_path):
    """R-027 R-033 (b): not yet classified at Phase: intake — OK, no Workflows classification row."""
    text = "# Project Status\nBridge version: %s\nPhase: intake\nWorkflows: not yet classified\n" % VERSION
    rc, out, err = conformance(workspace(tmp_path, text))
    assert verdict(out, "Workflows line") == ("OK", "Workflows line"), out
    assert rows_for_floor(out, "Workflows classification") == [], out
    assert rc == 0


def test_r027_r033_not_yet_classified_past_intake(tmp_path):
    """R-027 R-033 (c): not yet classified at Phase: building — Workflows line OK, classification NOTE."""
    rc, out, err = conformance(workspace(tmp_path, VALID["not-yet-classified"]))
    assert verdict(out, "Workflows line") == ("OK", "Workflows line"), out
    assert rows_for_floor(out, "Workflows classification") == [
        "  NOTE     " + CLASSIFICATION_BUILDING,
    ], out
    lines = out.splitlines()
    wf_ix = next(i for i, line in enumerate(lines) if line.strip().startswith("OK") and "Workflows line" in line)
    class_ix = next(i for i, line in enumerate(lines) if "Workflows classification" in line)
    assert wf_ix < class_ix, out
    assert rc == 0


def test_r027_r033_phase_first_word_only(tmp_path):
    """R-027 R-033 (d): Phase: building (Stage 2) — only building is printed in the NOTE."""
    text = "# Project Status\nBridge version: %s\nPhase: building (Stage 2)\nWorkflows: not yet classified\n" % VERSION
    rc, out, err = conformance(workspace(tmp_path, text))
    assert verdict(out, "Workflows line") == ("OK", "Workflows line"), out
    assert rows_for_floor(out, "Workflows classification") == [
        "  NOTE     " + CLASSIFICATION_BUILDING,
    ], out
    assert rc == 0


def test_r027_r033_unwritten_product_type(tmp_path):
    """R-027 R-033 (e): unwritten product type — MISSING with Requirement 1 detail."""
    folder = _bridge_copy(tmp_path)
    open_list = folder / "workflow" / "open-list.md"
    raw = open_list.read_text(encoding="utf-8")
    open_list.write_text(
        raw.replace(
            "| Website Development | has-screens | yes |",
            "| Website Development | has-screens | no |",
        ),
        encoding="utf-8",
        newline="",
    )
    text = HEAD + "Workflows: Website Development; traits: none\n"
    mod = _load_copy(folder)
    _assert_check_status_precondition(
        mod,
        text,
        [("f", "s.md", "Website Development", "product type is not written")],
    )
    rc, out, err = conformance(workspace(tmp_path, text), program=folder / "conformance-check.py")
    assert verdict(out, "Workflows line") == (
        "MISSING",
        "Workflows line  - names an unwritten workflow: Website Development - product type is not written",
    ), out
    assert rc == 1


def test_r027_r033_unwritten_sub_type(tmp_path):
    """R-027 R-033 (f): written type and unwritten sub-type — MISSING naming the sub-type."""
    folder = _bridge_copy(tmp_path)
    open_list = folder / "workflow" / "open-list.md"
    raw = open_list.read_text(encoding="utf-8")
    open_list.write_text(
        raw.replace(
            "| CLI Software | installable | yes |",
            "| CLI Software | installable | no |",
        ),
        encoding="utf-8",
        newline="",
    )
    line = "Workflows: Own-Computer Software Development " + ARROW + " CLI Software; traits: none\n"
    text = HEAD + line
    mod = _load_copy(folder)
    _assert_check_status_precondition(
        mod,
        text,
        [("f", "s.md", "CLI Software", "sub-type is not written")],
    )
    rc, out, err = conformance(workspace(tmp_path, text), program=folder / "conformance-check.py")
    assert verdict(out, "Workflows line") == (
        "MISSING",
        "Workflows line  - names an unwritten workflow: CLI Software - sub-type is not written",
    ), out
    assert rc == 1


def test_r027_r033_unwritten_trait_on_written_names(tmp_path):
    """R-027 R-033 (g): unwritten trait — Workflows line OK, Unwritten trait NOTE, exit 0."""
    folder = _bridge_copy(tmp_path)
    open_list = folder / "workflow" / "open-list.md"
    raw = open_list.read_text(encoding="utf-8")
    open_list.write_text(
        raw.replace(
            "| personal-data | Personal data | Holds data about people: accounts, sign-in, privacy, deletion | yes |",
            "| personal-data | Personal data | Holds data about people: accounts, sign-in, privacy, deletion | no |",
        ),
        encoding="utf-8",
        newline="",
    )
    text = HEAD + "Workflows: Web App Development " + ARROW + " Local Web App; traits: Personal data\n"
    mod = _load_copy(folder)
    _assert_check_status_precondition(
        mod,
        text,
        [("FLAG", "s.md", "Personal data", "trait not yet written; flagged, work continues (non-fatal)")],
    )
    rc, out, err = conformance(workspace(tmp_path, text), program=folder / "conformance-check.py")
    assert verdict(out, "Workflows line") == ("OK", "Workflows line"), out
    assert rows_for_floor(out, "Unwritten trait") == ["  NOTE     " + TRAIT_NOTE_PERSONAL], out
    lines = out.splitlines()
    wf_ix = next(i for i, line in enumerate(lines) if line.strip().startswith("OK") and "Workflows line" in line)
    trait_ix = next(i for i, line in enumerate(lines) if "Unwritten trait" in line)
    assert wf_ix < trait_ix, out
    assert rc == 0


def test_r027_r033_multipart_mixed(tmp_path):
    """R-027 R-033 (h): written part with unwritten trait, unclassified part past intake — rows in order."""
    folder = _bridge_copy(tmp_path)
    open_list = folder / "workflow" / "open-list.md"
    open_list.write_text(
        open_list.read_text(encoding="utf-8").replace(
            "| personal-data | Personal data | Holds data about people: accounts, sign-in, privacy, deletion | yes |",
            "| personal-data | Personal data | Holds data about people: accounts, sign-in, privacy, deletion | no |",
        ),
        encoding="utf-8",
        newline="",
    )
    text = (
        "# Project Status\nBridge version: %s\nPhase: building\n"
        "Workflows: tool: Host Extension Development %s Claude Code Extension; traits: Installable\n"
        "Workflows: app: Web App Development %s Local Web App; traits: Personal data\n"
        "Workflows: side: not yet classified\n" % (VERSION, ARROW, ARROW)
    )
    mod = _load_copy(folder)
    _assert_check_status_precondition(
        mod,
        text,
        [("FLAG", "s.md", "Personal data", "trait not yet written; flagged, work continues (non-fatal)")],
    )
    rc, out, err = conformance(workspace(tmp_path, text), program=folder / "conformance-check.py")
    assert rows_for_floor(out, "Workflows line") == ["  OK       Workflows line"], out
    assert rows_for_floor(out, "Unwritten trait") == ["  NOTE     " + TRAIT_NOTE_PERSONAL], out
    assert rows_for_floor(out, "Workflows classification") == ["  NOTE     " + CLASSIFICATION_BUILDING], out
    lines = [l for l in out.splitlines() if l.strip().startswith(("OK", "NOTE")) and (
        "Workflows line" in l or "Unwritten trait" in l or "Workflows classification" in l)]
    assert lines == [
        "  OK       Workflows line",
        "  NOTE     " + TRAIT_NOTE_PERSONAL,
        "  NOTE     " + CLASSIFICATION_BUILDING,
    ], out
    assert rc == 0


def test_r027_r033_unwritten_finding_output_is_escaped_ascii(tmp_path):
    """R-027 R-033 (i): non-ASCII and escape characters in an unwritten finding reach output escaped."""
    folder = _bridge_copy(tmp_path)
    open_list = folder / "workflow" / "open-list.md"
    special = "Z" + chr(0xDC) + chr(0x1B) + "test; comma"
    open_list.write_text(
        open_list.read_text(encoding="utf-8").replace(
            "| Website Development | has-screens | no |",
            "| %s | has-screens | no |" % special,
        ),
        encoding="utf-8",
        newline="",
    )
    mod = _load_copy(folder)
    open_text, _, open_err = mod.read_utf8(mod.DEFAULT_OPEN)
    reg_text, _, reg_err = mod.read_utf8(mod.DEFAULT_REGISTRY)
    assert open_err is None and reg_err is None
    tables, errors = mod.load_tables(open_text, mod.DEFAULT_OPEN, reg_text, mod.DEFAULT_REGISTRY)
    assert not errors
    status_line = HEAD + "Workflows: %s; traits: none\n" % special
    findings = mod.check_status("s.md", status_line, tables)
    f_findings = [item for item in findings if item[0] == "f"]
    assert len(f_findings) == 1 and f_findings[0][2] == special, findings
    escaped_name = _ascii_field(mod, special)
    rc, out, err = conformance(workspace(tmp_path, status_line), program=folder / "conformance-check.py")
    assert verdict(out, "Workflows line") == (
        "MISSING",
        "Workflows line  - names an unwritten workflow: %s - product type is not written" % escaped_name,
    ), out
    assert "\\xdc" in out and "\\x1b" in out, out
    assert chr(0x1B) not in out
    assert out.isascii()
    assert rc == 1


def test_r027_r033_phase_word_escaped_in_classification_note(tmp_path):
    """R-027 R-033: Phase first word with non-ASCII and ESC is escaped in the Workflows classification row only."""
    phase_word = "stage" + chr(0xFC) + "x" + chr(0x1B) + "y"
    text = (
        "# Project Status\nBridge version: %s\nPhase: %s more text\nWorkflows: not yet classified\n"
        % (VERSION, phase_word)
    )
    escaped_phase = _ascii_field(_load_workflow_checker(), phase_word)
    rc, out, err = conformance(workspace(tmp_path, text))
    assert verdict(out, "Workflows line") == ("OK", "Workflows line"), out
    class_rows = rows_for_floor(out, "Workflows classification")
    assert len(class_rows) == 1, out
    expected_detail = (
        "unclassified past intake (Phase: %s); calibration step 4b classifies it, the project running on the main "
        "workflow alone meanwhile" % escaped_phase
    )
    assert class_rows[0] == "  NOTE     Workflows classification  - " + expected_detail, out
    assert chr(0x1B) not in class_rows[0]
    assert class_rows[0].isascii()
    assert rc == 0


def test_r027_r033_unwritten_trait_name_escaped(tmp_path):
    """R-027 R-033: unwritten trait name with non-ASCII and ESC is escaped in the Unwritten trait row."""
    folder = _bridge_copy(tmp_path)
    trait_name = "trait" + chr(0xDC) + "n" + chr(0x1B) + "m"
    open_list = folder / "workflow" / "open-list.md"
    open_list.write_text(
        open_list.read_text(encoding="utf-8").replace(
            "| personal-data | Personal data | Holds data about people: accounts, sign-in, privacy, deletion | no |",
            "| personal-data | %s | Holds data about people: accounts, sign-in, privacy, deletion | no |" % trait_name,
        ),
        encoding="utf-8",
        newline="",
    )
    text = HEAD + "Workflows: Web App Development " + ARROW + " Local Web App; traits: " + trait_name + "\n"
    mod = _load_copy(folder)
    _assert_check_status_precondition(
        mod,
        text,
        [("FLAG", "s.md", trait_name, "trait not yet written; flagged, work continues (non-fatal)")],
    )
    escaped_trait = _ascii_field(mod, trait_name)
    rc, out, err = conformance(workspace(tmp_path, text), program=folder / "conformance-check.py")
    assert verdict(out, "Workflows line") == ("OK", "Workflows line"), out
    expected_trait_row = (
        "Unwritten trait  - %s - trait not yet written; flagged, work continues (non-fatal)" % escaped_trait
    )
    assert rows_for_floor(out, "Unwritten trait") == ["  NOTE     " + expected_trait_row], out
    assert chr(0x1B) not in out
    assert out.isascii()
    assert rc == 0


@pytest.mark.parametrize(
    "phase_line,phase_in_note",
    [
        ("intakes", "intakes"),
        ("intake-review", "intake-review"),
    ],
)
def test_r027_r033_intake_comparison_is_exact(tmp_path, phase_line, phase_in_note):
    """R-027 R-033: only Phase: intake suppresses the classification NOTE; intakes and intake-review do not."""
    text = (
        "# Project Status\nBridge version: %s\nPhase: %s\nWorkflows: not yet classified\n"
        % (VERSION, phase_line)
    )
    rc, out, err = conformance(workspace(tmp_path, text))
    assert verdict(out, "Workflows line") == ("OK", "Workflows line"), out
    expected = (
        "Workflows classification  - unclassified past intake (Phase: %s); calibration step 4b classifies it, "
        "the project running on the main workflow alone meanwhile" % phase_in_note
    )
    assert rows_for_floor(out, "Workflows classification") == ["  NOTE     " + expected], out
    assert rc == 0


def test_r027_r033_grades_match_check_status_on_three_part_file(tmp_path):
    """R-027 R-033: calibration_workflows_grades FLAG and f findings match check_status; NOTE order follows parts."""
    folder = _unwritten_copy(tmp_path)
    text = (
        "# Project Status\nBridge version: %s\nPhase: building\n"
        "Workflows: tool: Host Extension Development %s Claude Code Extension; traits: Installable\n"
        "Workflows: side: not yet classified\n"
        "Workflows: app: Web App Development %s Local Web App; traits: Personal data\n" % (VERSION, ARROW, ARROW)
    )
    wmod = _load_copy(folder)
    open_text, _, open_err = wmod.read_utf8(wmod.DEFAULT_OPEN)
    reg_text, _, reg_err = wmod.read_utf8(wmod.DEFAULT_REGISTRY)
    assert open_err is None and reg_err is None
    tables, errors = wmod.load_tables(open_text, wmod.DEFAULT_OPEN, reg_text, wmod.DEFAULT_REGISTRY)
    assert not errors
    findings = wmod.check_status("s.md", text, tables)
    f_items = [item for item in findings if item[0] == "f"]
    flag_items = [item for item in findings if item[0] == "FLAG"]

    cmod = _load_conformance_copy(folder)
    wv, wdetail, wnotes = cmod.calibration_workflows_grades("s.md", text)
    assert wv == "MISSING"
    expected_detail = "names an unwritten workflow: " + "; ".join(
        "%s - %s" % (_ascii_field(wmod, item[2]), _ascii_field(wmod, item[3])) for item in f_items
    )
    assert wdetail == expected_detail
    trait_notes = [detail for floor, detail in wnotes if floor == "Unwritten trait"]
    assert trait_notes == [
        "%s - %s" % (_ascii_field(wmod, item[2]), _ascii_field(wmod, item[3])) for item in flag_items
    ]
    assert wnotes == [
        ("Unwritten trait", "Installable - trait not yet written; flagged, work continues (non-fatal)"),
        (
            "Workflows classification",
            "unclassified past intake (Phase: building); calibration step 4b classifies it, the project running on the main workflow alone meanwhile",
        ),
        ("Unwritten trait", "Personal data - trait not yet written; flagged, work continues (non-fatal)"),
    ]


def test_r027_r033_bridge_own_status_file(tmp_path):
    """R-027 R-033 (j): the bridge's own status file — Workflows line OK, no new NOTE rows."""
    text = BRIDGE_STATUS.read_text(encoding="utf-8")
    rc, out, err = conformance(workspace(tmp_path, text))
    assert verdict(out, "Workflows line") == ("OK", "Workflows line"), out
    assert rows_for_floor(out, "Unwritten trait") == [], out
    assert rows_for_floor(out, "Workflows classification") == [], out
    assert rc == 0
