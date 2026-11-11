"""Release B2's text, TASK-052 (R-062): every template of the eight records shows its header, the core's "Project
state" states the rule, calibrate-bridge.md's step 4 carries the migration item, and the delegation loop's step 3b
names the header refusal among the stops.

enforces: docs/BUILD_PLAN.md, TASK-052, Done when; docs/DESIGN.md, "Change: release B2", "The records and their
headers"; R-062 (its text half; the program half is tests/test_records_migrate.py).

Each template's header is read by bridge_env.read_header and checked by bridge_env.check_header for its kind, so a
header copied from a template into a new project's record is never malformed; where the template's prose is written
in the record's own shape, the header agrees with it as the record's checker reads it."""
import os
import re
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "bridge", "cursor-bridge"))
import bridge_env  # noqa: E402

CORE = "bridge/commands/supervisor.md"
DESIGN = "bridge/cursor-bridge/workflow/phases/design.md"
PLANNING = "bridge/cursor-bridge/workflow/phases/planning.md"
PACKAGER = "bridge/agents/spec-packager.md"
DIAGRAMS = "bridge/cursor-bridge/Diagram-Planning-Conventions.md"
RUNPARAMS = "bridge/cursor-bridge/workflow/phases/run-parameters.md"
CALIBRATE = "bridge/commands/calibrate-bridge.md"
LOOP = "bridge/cursor-bridge/workflow/phases/delegation-loop.md"


def read(rel):
    with open(os.path.join(ROOT, *rel.split("/")), encoding="utf-8") as fh:
        return fh.read().replace("\r\n", "\n")


def markdown_fences(text):
    """The contents of every ```markdown fence, in order."""
    out, lines, i = [], text.split("\n"), 0
    while i < len(lines):
        if lines[i].strip() == "```markdown":
            j = i + 1
            while j < len(lines) and lines[j].strip() != "```":
                j += 1
            out.append("\n".join(lines[i + 1:j]) + "\n")
            i = j
        i += 1
    return out


def fence_with(rel, marker):
    """The one ```markdown fence of the file that holds a line starting with marker."""
    found = [f for f in markdown_fences(read(rel)) if any(l.startswith(marker) for l in f.split("\n"))]
    assert len(found) == 1, "%s: %d fences hold a line starting %r" % (rel, len(found), marker)
    return found[0]


# (label, file, marker line of the template's prose, kind)
TEMPLATES = [
    ("status", CORE, "# Project Status", "project-status"),
    ("inventory", CORE, "# Inventory", "inventory"),
    ("register", DESIGN, "# Requirements", "requirements"),
    ("plan", PLANNING, "### TASK-001", "build-plan"),
    ("brief", PACKAGER, "# TASK-<nnn>: <title>", "brief"),
    ("index", DIAGRAMS, "| ID | Level | Kind |", "diagram-index"),
    ("deviations", DIAGRAMS, "| Diagram | From | To |", "deviations"),
    ("run-parameters", RUNPARAMS, "# Run parameters", "run-parameters"),
]


def template_header(rel, marker):
    fence = fence_with(rel, marker)
    assert fence.startswith("---\n"), "%s: the template for %r does not open with its header" % (rel, marker)
    header, body = bridge_env.read_header(fence)
    assert header is not None, "%s: no header read from the template for %r" % (rel, marker)
    return header, body


@pytest.mark.parametrize("label,rel,marker,kind", TEMPLATES, ids=[t[0] for t in TEMPLATES])
def test_r062_each_template_shows_a_header_the_reader_reads_and_the_schema_accepts(label, rel, marker, kind):
    """R-062: each template shows the header for its record, read by read_header and checked by check_header for its
    kind, with every key of its kind and the template's prose kept beneath it."""
    header, body = template_header(rel, marker)
    assert bridge_env.check_header(kind, header) == [], (label, bridge_env.check_header(kind, header))
    assert set(header) == set(bridge_env.HEADER_SCHEMAS[kind]), (label, sorted(header))
    assert any(l.startswith(marker) for l in body.split("\n")), "%s: the prose is not beneath the header" % label


def test_r062_the_status_template_shows_a_workflows_entry_in_block_form():
    """R-062: the status template's workflows is a list of mappings written in block form, one entry shown."""
    fence = fence_with(CORE, "# Project Status")
    header, _ = bridge_env.read_header(fence)
    assert isinstance(header["workflows"], list) and len(header["workflows"]) == 1, header["workflows"]
    assert set(header["workflows"][0]) == {"type", "subtype", "traits"}
    assert "\nworkflows:\n  - type: " in fence


def test_r062_the_plan_template_header_agrees_with_its_prose():
    """R-062: the plan template's header holds one stage and one increment, and agrees with the template's prose as
    plan-check reads it (the fallback reader)."""
    header, body = template_header(PLANNING, "### TASK-001")
    stages = header["stages"]
    assert len(stages) == 1 and len(stages[0]["increments"]) == 1, stages
    fallback = bridge_env.plan_prose_fallback(body)
    assert bridge_env.header_agrees("build-plan", header, fallback) == [], bridge_env.header_agrees(
        "build-plan", header, fallback)


@pytest.mark.parametrize("label,rel,marker,kind,fallback", [
    ("register", DESIGN, "# Requirements", "requirements", "register_fallback"),
    ("index", DIAGRAMS, "| ID | Level | Kind |", "diagram-index", "diagram_index_fallback"),
    ("deviations", DIAGRAMS, "| Diagram | From | To |", "deviations", "deviations_fallback"),
    ("inventory", CORE, "# Inventory", "inventory", "inventory_fallback"),
], ids=["register", "index", "deviations", "inventory"])
def test_r062_each_tabular_template_header_declares_its_table_s_columns(label, rel, marker, kind, fallback):
    """R-062: a tabular template's header declares the columns of the table beneath it, in order (the record's checker
    fails a difference, HEADER DISAGREES: columns)."""
    header, body = template_header(rel, marker)
    findings = bridge_env.header_agrees(kind, header, getattr(bridge_env, fallback)(body))
    if kind == "inventory":
        # the template's Decisions table shows a placeholder row, not a Development data row, and its Reflected
        # through line a placeholder: only the tables' declared shape is compared here
        findings = [f for f in findings if str(f).startswith("tables")]
    assert findings == [], (label, findings)


def test_r062_the_brief_template_header_carries_the_name_s_id_and_round_and_the_scope_bullets():
    """R-062: the brief template's header has id and round as a plain name gives them (round 1) and one scope entry
    per Scope bullet of the template."""
    fence = fence_with(PACKAGER, "# TASK-<nnn>: <title>")
    header, body = bridge_env.read_header(fence)
    assert header["id"] == "TASK-<nnn>" and header["round"] == 1, (header["id"], header["round"])
    lines = body.split("\n")
    start = lines.index("## Scope")
    end = next(i for i in range(start + 1, len(lines)) if lines[i].startswith("## "))
    bullets = [l[2:].strip() for l in lines[start:end] if l.startswith("- ")]
    assert header["scope"] == bullets, (header["scope"], bullets)


def paragraphs(text):
    return [p for p in re.split(r"\n\s*\n", text) if p.strip()]


def section_text(rel, heading):
    lines = read(rel).split("\n")
    start = lines.index(heading)
    level = len(heading) - len(heading.lstrip("#"))
    end = next((i for i in range(start + 1, len(lines))
                if lines[i].startswith("#") and len(lines[i]) - len(lines[i].lstrip("#")) <= level
                and lines[i][len(lines[i]) - len(lines[i].lstrip("#")):].startswith(" ")), len(lines))
    return "\n".join(lines[start:end])


def test_r062_the_core_s_project_state_states_the_rule_in_one_paragraph():
    """R-062: the core's "Project state" states the rule in one paragraph: a program reads the header first, falls back
    to the prose for a record without one, the record's checker fails a disagreement; and it names records-migrate.py
    as the way a record gets its header."""
    sec = section_text(CORE, "## Project state")
    want = ("reads the header first", "falls back to the prose for a record without one", "HEADER DISAGREES",
            "HEADER MALFORMED", "`python ~/.claude/cursor-bridge/records-migrate.py`")
    hits = [p for p in paragraphs(sec) if all(w in p for w in want)]
    assert len(hits) == 1, [w for w in want if w not in sec]


def test_r062_calibrate_bridge_step_4_carries_the_migration_item():
    """R-062: calibrate-bridge.md's step 4 carries the migration item as a record-keeping addition: the one --check
    command from the Workspace root first, its lines in the report, each repairable cannot read repaired in its prose, a
    merged brief never (left header-less and named in the report), each cannot write status file trimmed before the run,
    the result committed as the calibration's checkpoint in a records-only commit, reopening no gate."""
    sec = section_text(CALIBRATE, "## 4. Apply the delta by phase \u2014 reopen nothing")
    want = ("`python ~/.claude/cursor-bridge/records-migrate.py --check`", "from the Workspace root",
            "in the calibration's report", "`cannot read`", "repaired in its prose", "a merged brief never",
            "header-less", "`cannot write`", "trimmed", "records-only commit", "calibration's checkpoint",
            "record-keeping addition", "reopens no gate")
    hits = [p for p in paragraphs(sec) if all(w in p for w in want)]
    assert len(hits) == 1, [w for w in want if w not in sec]


def test_r062_step_3b_names_the_header_refusal_among_the_stops():
    """R-062: the delegation loop's step 3b names the launcher's and the guard's `header: ` refusal among the stops that
    are no model's failure."""
    text = read(LOOP)
    start = text.index("(The exceptions: every exit 125")
    end = text.index("is read and fixed as its message says.)", start)
    para = text[start:end]
    assert "the launcher's and the guard's `header: ` refusal" in para, "step 3b does not name the header refusal"
    tail = para[para.index("`header: ` refusal"):]
    assert "never a failed launch" in tail and "model's failure" in tail
