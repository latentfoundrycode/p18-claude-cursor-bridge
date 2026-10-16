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
import re

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
    """R-001: project.json parses and carries the fundamentals."""
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


SETTLED_ELSEWHERE = ("r-038", "second checkout", "second-checkout")


def _deferred_rows(inv):
    """The Deferred table's rows below its header, the "(none)" placeholder left out."""
    assert "## Deferred" in inv, "R-001: INVENTORY.md has no Deferred section"
    section = inv.split("## Deferred", 1)[1].split("\n## ", 1)[0]
    rows = [line.strip() for line in section.splitlines() if line.strip().startswith("|")]
    assert len(rows) >= 2 and "Item" in rows[0], "R-001: the Deferred table has no header row"
    cells = [[c.strip() for c in r.strip("|").split("|")] for r in rows[2:]]
    return [c for c in cells if c and c[0] != "(none)"]


OWNER_DATED = re.compile(r"\bowner\b.*\b\d{4}-\d{2}-\d{2}\b", re.I)  # completion-check.py's convention


def _deferral_fault(cells):
    """Why a Deferred row is not a settled owner deferral, or None. The template's last cell is
    `<yes — the question · no>`: a deferral the owner made reads `no` there and names the owner with a date in the row."""
    item = cells[0].lower()
    if any(s in item for s in SETTLED_ELSEWHERE):
        return "a settled decision sits in Deferred"
    if cells[-1].strip().lower() != "no":
        return "an owner decision is still open on it"
    if not OWNER_DATED.search(" | ".join(cells[1:-1])):
        return "the row does not name the owner with a date"
    return None


def test_r001_deferred_rows_parse():
    """R-001: the row parser reads a real row and skips the placeholder, and the row rule accepts a deferral written to
    the template and refuses the open forms (a negative test must show its precondition)."""
    table = "## Deferred\n| Item | Why deferred | Since | Owner decision needed |\n|---|---|---|---|\n| (none) | — | — | — |\n| R-038 install | x | 2026-10-11 | yes |\n"
    assert _deferred_rows(table) == [["R-038 install", "x", "2026-10-11", "yes"]]
    assert _deferred_rows(table.split("| R-038")[0]) == []
    assert _deferral_fault(["a later feature", "deferred by the owner", "2026-11-01", "no"]) is None
    for row in (["a later feature", "not yet", "2026-10-16", "yes"],
                ["a later feature", "not yet", "2026-10-16", "yes — the owner asked 2026-10-16"],
                ["a later feature", "not yet", "2026-10-16", "yes — does the owner defer it? (asked 2026-10-16)"],
                ["a later feature", "not yet", "2026-10-16", "no"],
                ["R-038 second checkout", "deferred by the owner", "2026-10-11", "no"]):
        assert _deferral_fault(row), row


def test_r001_no_deferred_row_reopens_a_settled_decision():
    """R-001 (docs/BUILD_PLAN.md TASK-001 Done when: no Deferred row contradicts a Decision): no Deferred row is about a
    question the Decisions table settled (R-038, the second-checkout question), and every row is a deferral the owner
    has made — its decision cell reads `no` and the row names the owner with a date (supervisor.md rule 44; the
    template's `<yes — the question · no>`; completion-check's owner-dated convention; TASK-027 plans one at B6).
    An open owner question waits on the status file's Awaiting line, not here."""
    for cells in _deferred_rows(_read("docs/INVENTORY.md")):
        fault = _deferral_fault(cells)
        assert fault is None, f"R-001: {fault}: {cells[0]!r}"


def test_r001_phase_matches_status():
    """R-001: project.json's state.phase is the phase the status file states."""
    pj = json.loads(_read("project.json"))
    m = re.search(r"^Phase:\s*(\S+)", _read("docs/PROJECT_STATUS.md"), re.M)
    assert m, "R-001: PROJECT_STATUS.md has no Phase: line"
    assert m.group(1) == pj["state"]["phase"], f"R-001: project.json phase {pj['state']['phase']!r} differs from the status file's {m.group(1)!r}"


def test_r001_run_parameters_authoritative():
    """R-001: RUN_PARAMETERS.md is the authoritative run-parameter record and is complete."""
    rp = _read("docs/RUN_PARAMETERS.md").lower()
    assert "stage pause:" in rp
    assert "merge authority:" in rp
    assert "refactoring pass:" in rp
    assert "parallel increments:" in rp
