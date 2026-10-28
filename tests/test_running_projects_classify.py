"""TASK-025: the four running projects classify under §6.3 on the committed fixtures, none pausing (R-031).

enforces: docs/REQUIREMENTS.md R-031 and docs/BUILD_PLAN.md TASK-025's Done when ("`test_running_projects_classify.py`
asserts the bridge, reAngle, the video factory, and the TDP each classify per §6.3 on the committed fixtures (TASK-019-021)
with `workflow-check` green"). §6.3's classifications are read from their record in this repository, docs/INVENTORY.md's
Decisions row "Decision 6 confirmed" (the Restructuring Plan itself lies outside the Workspace); the open list
(bridge/cursor-bridge/workflow/open-list.md) gives the names, the written flags, each sub-type's type and the default
traits; "none pausing" is the workflow check passing with no FAIL and no FLAG and the conformance check's calibration
grades (calibration_workflows_grades, calibrate-bridge.md step 1b) giving no MISSING and no NOTE. Supervisor-written;
no builder run."""
import importlib.util
import os
import re
import sys

import pytest

from phase_modules import read
from workflow_files import BRIDGE, FIXTURES, REPO, rows, run_check, traits_of

ARROW = "→"
# each running project's committed fixture (TASK-019 to TASK-021) and how the Decisions row names the project
PROJECTS = {
    "bridge": ("bridge.status.md", "the bridge"),
    "reangle": ("reangle.status.md", "video factory & reAngle"),
    "video-factory": ("video-factory.status.md", "video factory & reAngle"),
    "tdp": ("tdp.status.md", "TDP"),
}


def decision_6():
    """§6.3's classifications as the Decisions row records them: {how the row names the project: (type, sub-type)},
    by the open list's Name column, in lower case."""
    row = [l for l in read(os.path.join(REPO, "docs", "INVENTORY.md")).split("\n")
           if l.startswith("| Decision 6 confirmed:")]
    assert len(row) == 1, row
    cell = row[0].split("|")[1]
    listed = cell.split(" — ", 1)[1].split(". Note")[0]
    got = {}
    for item in listed.split("; "):
        who, what = item.split(" = ")
        typ, sub = what.split(" %s " % ARROW)
        got[who.strip()] = (typ.strip().lower(), sub.strip().lower())
    return got


def workflows_line(name):
    lines = [l for l in read(os.path.join(FIXTURES, name)).split("\n") if l.startswith("Workflows: ")]
    assert len(lines) == 1, (name, lines)
    m = re.fullmatch(r"Workflows: (.+) %s (.+); traits: (.+)" % ARROW, lines[0])
    assert m, lines[0]
    # `none` is the grammar's word for no traits ("Project state"), never a trait's name
    traits = [] if m.group(3) == "none" else [t.strip() for t in m.group(3).split(",")]
    return m.group(1), m.group(2), traits


def by(table, column, value):
    got = [r for r in rows(table).values() if r[column] == value]
    assert len(got) == 1, (table, column, value, got)
    return got[0]


def test_r031_the_decision_names_all_four_projects():
    """The record of §6.3's classifications covers the four projects R-031 names, two of them in one entry."""
    assert set(decision_6()) == {who for _name, who in PROJECTS.values()}


@pytest.mark.parametrize("project", sorted(PROJECTS))
def test_r031_each_project_is_classified_as_section_6_3_decided(project):
    """The fixture's `Workflows:` line names, by the open list's workflow names, the type and sub-type §6.3 gave the
    project; both are written, the sub-type is of that type, every trait named is written and in the open list's order,
    and the sub-type's default traits are among them (proposed at intake, settled at the design gate)."""
    name, who = PROJECTS[project]
    want_type, want_sub = decision_6()[who]
    type_wf, sub_wf, traits = workflows_line(name)
    typ = by("Product types", "Workflow name", type_wf)
    sub = by("Sub-types", "Sub-workflow name", sub_wf)
    assert (typ["Name"].lower(), sub["Name"].lower()) == (want_type, want_sub), (project, typ["Name"], sub["Name"])
    assert typ["Written"] == "yes" and sub["Written"] == "yes", project
    assert sub["Of type"] == typ["Key"], project
    trait_rows = rows("Traits")
    order = list(trait_rows)
    keys = []
    for t in traits:
        r = by("Traits", "Name", t)
        assert r["Written"] == "yes", (project, t)
        keys.append(r["Key"])
    assert keys == sorted(keys, key=order.index), (project, keys)
    assert traits_of(sub["Default traits"]) <= set(keys), (project, sub["Default traits"], keys)


@pytest.mark.parametrize("project", sorted(PROJECTS))
def test_r031_the_workflow_check_passes_each_fixture(project):
    """workflow-check.py --status on the fixture prints RESULT: OK alone: no FAIL (a part whose type or sub-type is not
    written pauses the project) and no FLAG (an unwritten trait)."""
    r = run_check("--status", os.path.join(FIXTURES, PROJECTS[project][0]))
    assert r.returncode == 0 and r.stdout.strip().split("\n") == ["RESULT: OK"], r.stdout + r.stderr


def conformance():
    path = os.path.join(BRIDGE, "cursor-bridge", "conformance-check.py")
    spec = importlib.util.spec_from_file_location("conformance_check_t025", path)
    mod = importlib.util.module_from_spec(spec)
    before = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.dont_write_bytecode = before
    return mod


@pytest.mark.parametrize("project", sorted(PROJECTS))
def test_r031_calibration_grades_each_fixture_with_nothing_to_pause_or_note(project):
    """The conformance check's calibration grades of the fixture's `Workflows:` line, which calibration step 1b reads:
    OK, with no NOTE (no unwritten trait, no part left unclassified past intake), so the project calibrates onto the new
    structure and resumes without pausing (calibrate-bridge.md step 4b)."""
    name = PROJECTS[project][0]
    verdict, detail, notes = conformance().calibration_workflows_grades(name, read(os.path.join(FIXTURES, name)))
    assert (verdict, detail, notes) == ("OK", "", []), (project, verdict, detail, notes)


def test_r031_the_bridges_own_status_file_carries_its_fixtures_line():
    """The bridge is classified by running the release: its own status file's `Workflows:` line is the fixture's."""
    status = [l for l in read(os.path.join(REPO, "docs", "PROJECT_STATUS.md")).split("\n") if l.startswith("Workflows: ")]
    fixture = [l for l in read(os.path.join(FIXTURES, "bridge.status.md")).split("\n") if l.startswith("Workflows: ")]
    assert status == fixture and len(status) == 1, (status, fixture)
