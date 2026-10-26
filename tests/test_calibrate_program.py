"""Calibration program grades for conditional workflows (TASK-024).

enforces: docs/REQUIREMENTS.md R-027 (calibration applies conditional workflows by phase) and R-033 (workflow check
at every calibration).
"""
import pathlib

from test_conformance_check import VERSION, verdict
from test_workflows_line_check import (
    ARROW,
    BRIDGE_LINE,
    HEAD,
    VALID,
    _bridge_copy,
    _load_copy,
    conformance,
    workspace,
)

REPO = pathlib.Path(__file__).resolve().parent.parent
BRIDGE_STATUS = REPO / "docs" / "PROJECT_STATUS.md"


def rows_for_floor(out, floor):
    return [line for line in out.splitlines() if line.strip().startswith(("OK", "MISSING", "NOTE")) and floor in line]


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
    notes = rows_for_floor(out, "Workflows classification")
    assert len(notes) == 1 and "(Phase: building)" in notes[0], out
    lines = out.splitlines()
    wf_ix = next(i for i, line in enumerate(lines) if line.strip().startswith("OK") and "Workflows line" in line)
    class_ix = next(i for i, line in enumerate(lines) if "Workflows classification" in line)
    assert wf_ix < class_ix, out
    assert rc == 0


def test_r027_r033_phase_first_word_only(tmp_path):
    """R-027 R-033 (d): Phase: building (Stage 2) — only building is printed in the NOTE."""
    text = "# Project Status\nBridge version: %s\nPhase: building (Stage 2)\nWorkflows: not yet classified\n" % VERSION
    rc, out, err = conformance(workspace(tmp_path, text))
    notes = rows_for_floor(out, "Workflows classification")
    assert len(notes) == 1 and "(Phase: building)" in notes[0] and "Stage" not in notes[0], out
    assert rc == 0


def test_r027_r033_unwritten_product_type(tmp_path):
    """R-027 R-033 (e): unwritten product type — MISSING with Requirement 1 detail."""
    text = HEAD + "Workflows: Website Development; traits: none\n"
    rc, out, err = conformance(workspace(tmp_path, text))
    v, text_row = verdict(out, "Workflows line")
    assert v == "MISSING" and text_row == (
        "Workflows line  - names an unwritten workflow: Website Development - product type is not written"), out
    assert rc == 1


def test_r027_r033_unwritten_sub_type(tmp_path):
    """R-027 R-033 (f): written type and unwritten sub-type — MISSING naming the sub-type."""
    line = "Workflows: Own-Computer Software Development " + ARROW + " CLI Software; traits: none\n"
    rc, out, err = conformance(workspace(tmp_path, HEAD + line))
    v, text_row = verdict(out, "Workflows line")
    assert v == "MISSING" and "CLI Software - sub-type is not written" in text_row, out
    assert rc == 1


def test_r027_r033_unwritten_trait_on_written_names(tmp_path):
    """R-027 R-033 (g): unwritten trait — Workflows line OK, Unwritten trait NOTE, exit 0."""
    text = HEAD + "Workflows: Web App Development " + ARROW + " Local Web App; traits: Personal data\n"
    rc, out, err = conformance(workspace(tmp_path, text))
    assert verdict(out, "Workflows line") == ("OK", "Workflows line"), out
    notes = rows_for_floor(out, "Unwritten trait")
    assert len(notes) == 1 and "Personal data" in notes[0] and "work continues" in notes[0], out
    assert rc == 0


def test_r027_r033_multipart_mixed(tmp_path):
    """R-027 R-033 (h): written part with unwritten trait, unclassified part past intake — rows in order."""
    text = (
        "# Project Status\nBridge version: %s\nPhase: building\n"
        "Workflows: app: Web App Development %s Local Web App; traits: Personal data\n"
        "Workflows: side: not yet classified\n" % (VERSION, ARROW)
    )
    rc, out, err = conformance(workspace(tmp_path, text))
    assert verdict(out, "Workflows line") == ("OK", "Workflows line"), out
    lines = [l for l in out.splitlines() if l.strip().startswith("NOTE")]
    trait_ix = next(i for i, l in enumerate(lines) if "Unwritten trait" in l)
    class_ix = next(i for i, l in enumerate(lines) if "Workflows classification" in l)
    assert trait_ix < class_ix, out
    assert rc == 0


def test_r027_r033_unwritten_finding_output_is_escaped_ascii(tmp_path):
    """R-027 R-033 (i): non-ASCII and escape characters in an unwritten finding reach output escaped."""
    folder = _bridge_copy(tmp_path)
    open_list = folder / "workflow" / "open-list.md"
    special = "Z" + chr(0xDC) + "test; comma"
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
    codes = [item[0] for item in mod.check_status("s.md", status_line, tables)]
    assert "f" in codes, codes
    rc, out, err = conformance(workspace(tmp_path, status_line), program=folder / "conformance-check.py")
    assert rc == 1 and out.isascii(), out
    assert "\\xdc" in out, out


def test_r027_r033_bridge_own_status_file(tmp_path):
    """R-027 R-033 (j): the bridge's own status file — Workflows line OK, no new NOTE rows."""
    text = BRIDGE_STATUS.read_text(encoding="utf-8")
    rc, out, err = conformance(workspace(tmp_path, text))
    assert verdict(out, "Workflows line") == ("OK", "Workflows line"), out
    assert rows_for_floor(out, "Unwritten trait") == [], out
    assert rows_for_floor(out, "Workflows classification") == [], out
    assert rc == 0
