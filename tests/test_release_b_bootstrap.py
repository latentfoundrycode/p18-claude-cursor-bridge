"""Release B — TASK-001 (intake and configuration records) structural test.

enforces: docs/BUILD_PLAN.md TASK-001 Done when; satisfies R-001.
The bridge is a supervised project (plan section 15 condition 6); this test
asserts the supervised-project records exist and are internally consistent on
their authoritative files (project.json, docs/REQUIREMENTS.md, docs/INVENTORY.md,
docs/RUN_PARAMETERS.md). It deliberately does not assert on the PROJECT_STATUS
run-parameters digest line, which is a human-readable pointer to the authoritative
docs/RUN_PARAMETERS.md.
"""
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"


def _read(p):
    return (ROOT / p).read_text(encoding="utf-8")


def test_r001_records_exist():
    """R-001: the supervised-project records are present."""
    for rel in [
        "project.json",
        "docs/PROJECT_STATUS.md",
        "docs/REQUIREMENTS.md",
        "docs/INVENTORY.md",
        "docs/RUN_PARAMETERS.md",
        "docs/BUILD_PLAN.md",
        "docs/DESIGN_CRITIQUE.md",
        "docs/ROSTER.json",
        "docs/ROSTER.resolved.json",
    ]:
        assert (ROOT / rel).is_file(), f"R-001: missing {rel}"


def test_r001_project_json_wellformed():
    """R-001: project.json parses and carries the fundamentals; phase matches state."""
    pj = json.loads(_read("project.json"))
    for key in ("name", "purpose", "kind", "version", "state"):
        assert key in pj, f"R-001: project.json lacks {key}"
    assert pj["kind"] == "private"
    for key in ("phase", "stage", "bridge", "updated"):
        assert key in pj["state"], f"R-001: project.json state lacks {key}"


def test_r001_requirements_register_complete():
    """R-001: the register carries R-001..R-038."""
    reqs = _read("docs/REQUIREMENTS.md")
    for n in range(1, 39):
        assert f"R-{n:03d}" in reqs, f"R-001: register lacks R-{n:03d}"


def test_r001_inventory_decisions_recorded():
    """R-001: decision 6, R-038, and the met baseline precondition are recorded."""
    inv = _read("docs/INVENTORY.md")
    assert "Decision 6" in inv or "decision 6" in inv, "R-001: decision 6 not recorded"
    assert "R-038" in inv, "R-001: R-038 not recorded"
    assert "aseline measurement" in inv, "R-001: baseline precondition not recorded"


def test_r001_no_open_deferred_contradicts_a_decision():
    """R-001: the Deferred table carries no open row (the R-038 question was settled)."""
    inv = _read("docs/INVENTORY.md")
    deferred = inv.split("## Deferred", 1)[1] if "## Deferred" in inv else ""
    # the only table row is the "(none)" placeholder
    assert "owner decision needed" not in deferred.lower() or "(none)" in deferred, \
        "R-001: an open Deferred row remains"
    assert "second checkout" not in deferred.lower() or "none" in deferred.lower(), \
        "R-001: the settled R-038 item still sits in Deferred"


def test_r001_run_parameters_authoritative():
    """R-001: RUN_PARAMETERS.md is the authoritative run-parameter record and is complete."""
    rp = _read("docs/RUN_PARAMETERS.md").lower()
    assert "stage pause:" in rp
    assert "merge authority:" in rp
    assert "refactoring pass:" in rp
    assert "parallel increments:" in rp
