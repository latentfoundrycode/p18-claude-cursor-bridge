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


def _table_rows(text, heading):
    """The cells of each row of the first table under `heading`, its header and separator rows left out."""
    assert heading in text, f"R-001: no {heading} section"
    section = text.split(heading, 1)[1].split("\n## ", 1)[0]
    rows = [line.strip() for line in section.splitlines() if line.strip().startswith("|")]
    assert len(rows) >= 2, f"R-001: the {heading} table has no header row"
    return [[c.strip() for c in r.strip("|").split("|")] for r in rows[2:]]


def _register_faults(text):
    """Why the register's ID column does not carry R-001..R-038 each once, as a list (empty when it does). An ID counts
    only as the first cell of a table row, so an introduction naming the range stands in for no row."""
    ids = [line.strip().strip("|").split("|")[0].strip() for line in text.splitlines() if line.strip().startswith("|")]
    if "ID" not in ids:
        return ["no table with an ID column"]
    return [f"R-{n:03d} {ids.count(f'R-{n:03d}')} times" for n in range(1, 39) if ids.count(f"R-{n:03d}") != 1]


def test_r001_requirements_register_complete():
    """R-001: the register's ID column carries R-001..R-038, each once (read from the table's first cells, not the
    text, where an introduction naming a range would stand in for a row: stage B1's review round 2, Review A)."""
    assert _register_faults(_read("docs/REQUIREMENTS.md")) == [], "R-001: the register's ID column"


def test_r001_requirements_register_parse():
    """R-001: the register reader passes a complete register and refuses a missing row whose ID the introduction still
    names, a row given twice and a table without an ID column (a negative test must show its precondition)."""
    rows = "".join(f"| R-{n:03d} | a requirement |\n" for n in range(1, 39))
    text = "The register holds R-001 to R-038.\n\n| ID | Requirement |\n|---|---|\n" + rows
    assert _register_faults(text) == []
    assert _register_faults(text.replace("| R-038 | a requirement |\n", "")) == ["R-038 0 times"]
    assert _register_faults(text + "| R-007 | again |\n") == ["R-007 2 times"]
    assert _register_faults(text.replace("| ID |", "| Key |")) == ["no table with an ID column"]


DATED = r"[0-9]{4}-[0-9]{2}-[0-9]{2}"
# Each record TASK-001's Done when names, by the start of its Decisions row, and who its Settled cell must name.
DECIDED = (("R-038:", "owner"), ("Decision 6 confirmed", "owner"), ("Baseline measurement", "maintainer"))


def _decision_faults(rows):
    """Why the Decisions rows do not record R-038 and decision 6 as owner-answered with the date and the baseline as
    met, as a list (empty when they do). Each is the one row whose first cell begins with it; its Settled cell (the
    third) holds a date and who decided."""
    faults = []
    for start, who in DECIDED:
        found = [cells for cells in rows if cells[0].startswith(start)]
        if len(found) != 1:
            faults.append(f"{len(found)} Decisions rows start {start!r} (one row each, edited in place)")
            continue
        settled = found[0][2] if len(found[0]) > 2 else ""
        if not (re.search(DATED, settled) and who in settled):
            faults.append(f"{start!r}: the Settled cell lacks a date or {who!r}: {settled!r}")
        if start == "Baseline measurement" and not re.match(r"Baseline measurement [(]precondition 3[)] met", found[0][0]):
            faults.append(f"the baseline is not recorded as met: {found[0][0][:80]!r}")
    return faults


def test_r001_inventory_decisions_recorded():
    """R-001 (docs/BUILD_PLAN.md TASK-001 Done when): decision 6 and R-038 are recorded as owner-answered with the date in
    INVENTORY Decisions, and the baseline-measurement precondition as met. Each is a row of the Decisions table whose
    first cell begins with it and whose Settled cell (the third) holds the date and who decided; a mention elsewhere in
    the file does not count (stage B1's review round 2, Review A: the R-038 and decision-6 rows deleted, and the baseline
    row rewritten as not met, each passed the earlier substring test)."""
    assert _decision_faults(_table_rows(_read("docs/INVENTORY.md"), "## Decisions")) == [], "R-001: INVENTORY Decisions"


DECISIONS = """## Decisions
| Decision | Reason | Settled | Revisit only if |
|---|---|---|---|
| R-038: install at B6 | x | 2026-10-11, owner | — |
| Decision 6 confirmed: the classifications | x | 2026-10-11, owner | — |
| Baseline measurement (precondition 3) met before release B | x | 2026-10-11, maintainer | — |

## Deferred
see Decisions: R-038, Decision 6 confirmed, Baseline measurement
"""


def test_r001_inventory_decisions_parse():
    """R-001: the Decisions reader passes the three records and refuses each way of losing one: a row gone while the
    text still names it, a row twice, the wrong decider, no date, the baseline not met (a negative test must show its
    precondition)."""
    assert _decision_faults(_table_rows(DECISIONS, "## Decisions")) == []
    for old, new in (("| R-038: install at B6", "| Other: install at B6"),
                     ("| Decision 6", "| R-038: again | x | 2026-10-12, owner | — |\n| Decision 6"),
                     ("classifications | x | 2026-10-11, owner", "classifications | x | 2026-10-11, supervisor"),
                     ("B6 | x | 2026-10-11, owner", "B6 | x | owner"),
                     ("(precondition 3) met", "(precondition 3) NOT met"),
                     ("2026-10-11, maintainer", "2026-10-11, supervisor")):
        assert DECISIONS.count(old) == 1, old
        assert len(_decision_faults(_table_rows(DECISIONS.replace(old, new), "## Decisions"))) == 1, old


SETTLED_ELSEWHERE = ("r-038", "second checkout", "second-checkout")


def _deferred_rows(inv):
    """The Deferred table's rows below its header, the "(none)" placeholder left out."""
    assert "## Deferred" in inv, "R-001: INVENTORY.md has no Deferred section"
    section = inv.split("## Deferred", 1)[1].split("\n## ", 1)[0]
    rows = [line.strip() for line in section.splitlines() if line.strip().startswith("|")]
    assert len(rows) >= 2 and "Item" in rows[0], "R-001: the Deferred table has no header row"
    cells = [[c.strip() for c in r.strip("|").split("|")] for r in rows[2:]]
    return [c for c in cells if c and c[0] != "(none)"]




def _deferral_fault(cells):
    """Why a Deferred row is not a settled owner deferral, or None. The template's last cell is
    `<yes — the question · no>`: a deferral the owner made reads `no` there and names the owner with a date in the row."""
    item = cells[0].lower()
    if any(s in item for s in SETTLED_ELSEWHERE):
        return "a settled decision sits in Deferred"
    if not re.match(r"no\b", cells[-1].strip().lower()):
        return "an owner decision is still open on it"
    row = " | ".join(cells[1:])
    if not (re.search(r"\bowner\b", row, re.I) and re.search(r"\b\d{4}-\d{2}-\d{2}\b", row)):
        return "the row does not name the owner with a date"
    return None


def test_r001_deferred_rows_parse():
    """R-001: the row parser reads a real row and skips the placeholder, and the row rule accepts a deferral written to
    the template and refuses the open forms (a negative test must show its precondition)."""
    table = "## Deferred\n| Item | Why deferred | Since | Owner decision needed |\n|---|---|---|---|\n| (none) | — | — | — |\n| R-038 install | x | 2026-10-11 | yes |\n"
    assert _deferred_rows(table) == [["R-038 install", "x", "2026-10-11", "yes"]]
    assert _deferred_rows(table.split("| R-038")[0]) == []
    assert _deferral_fault(["a later feature", "deferred by the owner", "2026-11-01", "no"]) is None
    assert _deferral_fault(["a later feature", "not needed for B", "2026-11-01", "no — the owner, 2026-11-01"]) is None
    assert _deferral_fault(["a later feature", "not needed for B", "2026-11-01", "no — deferred by the owner"]) is None
    assert _deferral_fault(["a later feature", "deferred by the owner", "—", "no"])
    for row in (["a later feature", "not yet", "2026-10-16", "yes"],
                ["a later feature", "not yet", "2026-10-16", "yes — the owner asked 2026-10-16"],
                ["a later feature", "not yet", "2026-10-16", "yes — does the owner defer it? (asked 2026-10-16)"],
                ["a later feature", "not yet", "2026-10-16", "no"],
                ["R-038 second checkout", "deferred by the owner", "2026-10-11", "no"]):
        assert _deferral_fault(row), row


def test_r001_no_deferred_row_reopens_a_settled_decision():
    """R-001 (docs/BUILD_PLAN.md TASK-001 Done when: no Deferred row contradicts a Decision): no Deferred row is about a
    question the Decisions table settled (R-038, the second-checkout question), and every row is a deferral the owner
    has made — its decision cell begins `no` and the row names the owner and a date, in either order (supervisor.md
    rule 44; TASK-027 plans one at B6; completion-check.py reads the register, not this table, and wants the owner
    before the date there). This project narrows the template's
    `<yes — the question · no>`: an open owner question waits on the status file's Awaiting line, not in Deferred."""
    for cells in _deferred_rows(_read("docs/INVENTORY.md")):
        fault = _deferral_fault(cells)
        assert fault is None, f"R-001: {fault}: {cells[0]!r}"


def test_r001_phase_matches_status():
    """R-001: project.json's state.phase is the phase the status file states."""
    pj = json.loads(_read("project.json"))
    m = re.search(r"^Phase:\s*(\S+)", _read("docs/PROJECT_STATUS.md"), re.M)
    assert m, "R-001: PROJECT_STATUS.md has no Phase: line"
    assert m.group(1) == pj["state"]["phase"], f"R-001: project.json phase {pj['state']['phase']!r} differs from the status file's {m.group(1)!r}"


# The run parameters and the values each may take (supervisor.md, "Run parameters", the file's template).
RUN_PARAMETERS = {
    "Stage pause": r"(run|pause)",
    "Merge authority": r"(supervisor|owner)",
    "Refactoring pass": r"(on|off)",
    "Installer verification": r"(local|ci-only|n/a)",
    "Parallel increments": r"(off|on)",
}


def _parameter_faults(text):
    faults = []
    for key, value in RUN_PARAMETERS.items():
        lines = [line for line in text.splitlines() if line.startswith(key + ": ")]
        if len(lines) != 1:
            faults.append(f"{key}: {len(lines)} lines")
        elif not re.match(value + r"( |$)", lines[0][len(key) + 2:]):
            faults.append(f"{key}: {lines[0][len(key) + 2:][:40]!r}")
    return faults


def test_r001_run_parameters_authoritative():
    """R-001: RUN_PARAMETERS.md is the authoritative run-parameter record and is complete: each of the five parameters
    of supervisor.md's template stands on one line of its own, with one of its values (stage B1's review round 2,
    Review A: the file lacking a parameter, or with a value blanked, passed the earlier substring test)."""
    assert _parameter_faults(_read("docs/RUN_PARAMETERS.md")) == []


def test_r001_run_parameters_parse():
    """R-001: the parameter reader refuses a missing line, a blank value and a value outside the template (a negative
    test must show its precondition)."""
    good = "".join(f"{k}: {v.strip('()').split('|')[0]}\n" for k, v in RUN_PARAMETERS.items())
    assert _parameter_faults(good) == []
    assert _parameter_faults(good.replace("Installer verification: local\n", "")) == ["Installer verification: 0 lines"]
    assert _parameter_faults(good.replace("Merge authority: supervisor", "Merge authority: ")) == ["Merge authority: ''"]
    assert _parameter_faults(good.replace("Stage pause: run", "Stage pause: later")) == ["Stage pause: 'later'"]
