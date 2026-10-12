"""Release B — TASK-005: the extension-point registry.

enforces: docs/BUILD_PLAN.md TASK-005 Done when; the Restructuring Plan §6.4 (the initial points per
phase, Definition of done and Delivery included; the interface phase replaceable), §6.5 (add,
replace, set; only type workflows and sub-workflows replace or set) and §6.11 (the phase modules'
paths). Satisfies R-006.
The two tables are the shape `workflow-check.py` (TASK-006) reads: each found by its heading, the
first Markdown table after it (its rows running to the first line that is not a table line), one row
per entry, cells split on `|`, columns found by their header names.
"""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
EP = os.path.join(HERE, os.pardir, "bridge", "cursor-bridge", "workflow", "extension-points.md")
TEXT = open(EP, encoding="utf-8").read()

KEY = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
POINT_KEY = re.compile(r"^([a-z0-9]+(?:-[a-z0-9]+)*)\.([a-z0-9]+(?:-[a-z0-9]+)*)$")

MODULE_COLS = ["Module", "Phase", "Replaceable"]
POINT_COLS = ["Key", "Phase", "Point", "Declared by", "Changes", "Applies"]

# §6.11 / supervisor.md "Main and conditional workflows": the phase modules, in the core's order.
MODULES = ["intake", "design", "interface", "planning", "run-parameters", "configuration",
           "delegation-loop", "change-cycle", "reflection", "project-end"]
# §6.4: the interface phase is the one a type workflow or sub-workflow may replace.
REPLACEABLE = {"interface"}

# §6.4, row by row: (the §6.4 phase, a phrase of the point's text) -> the point's key and declaring
# module. Definition of done and Delivery are §6.4 rows of their own, declared by project end.
S64 = [
    ("Intake", "Additional questions", "intake.questions"),
    ("Intake", "Additional requirement sources", "intake.requirement-sources"),
    ("Intake", "target environment", "intake.target-environment"),
    # The one refinement of §6.4's list: §6.5 names the kind of performance budget as a value a
    # type workflow or sub-workflow sets, and the budgets are settled at intake (supervisor.md, Phase 1).
    ("Intake", "kind of performance budget", "intake.budget-kind"),
    ("Design", "Additional design sections", "design.sections"),
    ("Design", "diagram catalogue", "design.diagram-catalogue"),
    ("Design", "Mandatory diagram kinds", "design.mandatory-diagrams"),
    ("Interface phase", "variants", "interface.variants"),
    ("Planning", "Mandatory stages", "planning.stages"),
    ("Planning", "plan critic's lenses", "planning.critic-lenses"),
    ("Run parameters", "Additional run parameters", "run-parameters.parameters"),
    ("Configuration", "Additional configuration items, tools and checks", "configuration.items"),
    ("The delegation loop", "inspect step", "delegation-loop.inspect-checks"),
    ("The delegation loop", "test step", "delegation-loop.test-checks"),
    ("The delegation loop", "Additional brief constraints", "delegation-loop.brief-constraints"),
    ("Definition of done", "Additional completion conditions", "project-end.completion-conditions"),
    ("Delivery", "delivery procedure", "project-end.delivery"),
    ("Reflection points", "Additional reflection items", "reflection.items"),
]
# §6.5: the values the main workflow leaves open for a type workflow or sub-workflow to set — its
# two examples, the kind of performance budget and the delivery kind, and §6.4's target environment.
SETTABLE = {"intake.target-environment", "intake.budget-kind", "project-end.delivery"}


def table(heading):
    """The first Markdown table after `heading`, to the first non-table line: (header cells, rows)."""
    a = TEXT.index("\n" + heading + "\n")
    b = TEXT.find("\n## ", a + 1)
    section = TEXT[a:b if b != -1 else len(TEXT)].split("\n")
    start = next(i for i, l in enumerate(section) if l.startswith("|"))
    lines = []
    for l in section[start:]:
        if not l.startswith("|"):
            break
        lines.append(l)
    cells = [[c.strip() for c in l.strip().strip("|").split("|")] for l in lines]
    head, sep, body = cells[0], cells[1], cells[2:]
    assert all(set(c) <= set("-:") and c for c in sep), "the second table line is the separator"
    assert len(sep) == len(head), "the separator has one cell per column"
    rows = []
    for r in body:
        assert len(r) == len(head), "every row has one cell per column: %r" % (r,)
        rows.append(dict(zip(head, r)))
    return head, rows


def modules():
    return table("## Phase modules")


def points():
    return table("## Extension points")


def test_r006_the_file_sits_at_the_s6_11_path_and_is_bounded():
    """R-006, §6.11: `workflow/extension-points.md` beside the open list; a bounded reference text."""
    assert os.path.isfile(EP)
    assert "\r" not in TEXT
    assert len(TEXT) < 20000


def test_r006_both_tables_parse_with_exactly_the_stated_columns():
    """R-006: the shape `workflow-check.py` reads — one heading each, the stated columns."""
    for heading, cols in (("## Phase modules", MODULE_COLS), ("## Extension points", POINT_COLS)):
        assert TEXT.count("\n" + heading + "\n") == 1, heading
        head, rows = table(heading)
        assert head == cols, heading
        assert rows, heading


def test_r006_every_phase_module_is_listed_once_with_a_replaceable_flag():
    """R-006, §6.4, §6.11: every phase module, each with `yes`/`no`; only the interface phase replaceable."""
    _, rows = modules()
    assert [r["Module"] for r in rows] == MODULES
    for r in rows:
        assert KEY.match(r["Module"]), r
        assert r["Phase"], r
        assert r["Replaceable"] in ("yes", "no"), r
    assert {r["Module"] for r in rows if r["Replaceable"] == "yes"} == REPLACEABLE


def test_r006_every_s6_4_point_is_present_with_its_declaring_module():
    """R-006, §6.4 (BUILD_PLAN TASK-005): every §6.4 point present, Definition of done and Delivery
    included, each naming the module that declares it — and nothing beyond them unexplained."""
    _, rows = points()
    by_key = {r["Key"]: r for r in rows}
    assert len(by_key) == len(rows), "keys are unique"
    assert [r["Key"] for r in rows] == [k for _, _, k in S64], "the §6.4 points and the one refinement, in §6.4's order"
    for phase, phrase, key in S64:
        r = by_key[key]
        assert r["Phase"] == phase, key
        assert phrase.lower() in r["Point"].lower(), key
        assert r["Declared by"] == key.split(".")[0], key
    assert {"Definition of done", "Delivery"} <= {r["Phase"] for r in rows}
    assert "One point is added to §6.4's list: `intake.budget-kind`, because §6.5 names the kind of performance budget" in TEXT


def test_r006_every_point_is_well_formed_and_names_a_listed_module():
    """R-006: the key is `<module>.<name>`; the declaring module is a listed phase module."""
    listed = {r["Module"]: r for r in modules()[1]}
    for r in points()[1]:
        m = POINT_KEY.match(r["Key"])
        assert m, r
        assert m.group(1) == r["Declared by"], r
        assert r["Declared by"] in listed, r
        assert r["Point"], r


def test_r006_every_point_carries_its_phases_replaceable_flag():
    """BUILD_PLAN TASK-005 Done when: each point carries whether its phase is replaceable — read
    through its declaring module's row, so the flag is stated once and cannot disagree with itself."""
    flag = {r["Module"]: r["Replaceable"] for r in modules()[1]}
    for r in points()[1]:
        assert flag[r["Declared by"]] in ("yes", "no"), r
    assert {r["Key"] for r in points()[1] if flag[r["Declared by"]] == "yes"} == {"interface.variants"}
    assert "A point's phase is replaceable exactly when the module that declares it is" in TEXT


def test_r006_every_point_carries_its_kinds_and_where_it_applies():
    """§6.5: every point accepts additions; only the values §6.5 leaves open accept a setting."""
    for r in points()[1]:
        kinds = [k.strip() for k in r["Changes"].split(",")]
        assert kinds[0] == "add" and set(kinds) <= {"add", "set"} and len(kinds) == len(set(kinds)), r
        assert ("set" in kinds) == (r["Key"] in SETTABLE), r
        assert r["Applies"] in ("part", "project"), r


def test_r006_the_change_cycle_declares_no_point_of_its_own():
    """The change cycle runs the other modules again; their points apply there."""
    assert "change-cycle" not in {r["Declared by"] for r in points()[1]}
    assert "The change cycle declares no points of its own" in TEXT


def test_r006_the_tables_shape_is_stated_for_the_reader():
    """The shape the check reads is stated in the file, as the open list states its own."""
    assert "`workflow-check.py` reads the two tables below and nothing else in this file" in TEXT
    assert "Each table is the first table after its heading (`## Phase modules`, `## Extension points`)" in TEXT
    assert "its columns are found by their header names; no cell contains a `|`" in TEXT


def test_r006_how_a_conditional_workflow_names_a_point():
    """§6.5 and TASK-003's deferral: how a replacement and a trait's attachment point are declared;
    only type workflows and sub-workflows replace or set; traits only add."""
    assert "`## Add at <point key>`" in TEXT
    assert "`## Set at <point key>`" in TEXT
    assert "`## Replace <module key>`" in TEXT
    assert "Only a type workflow or a sub-workflow may set." in TEXT
    assert "Only a type workflow or a sub-workflow may replace." in TEXT
    assert "A trait attaches to the main workflow only through its `Add at` headings" in TEXT
    assert "A trait never replaces (§6.5)." in TEXT


def test_r006_a_shared_addition_at_a_project_point_is_made_once():
    """TASK-003's deferral: a project-wide addition from a conditional workflow two parts share."""
    assert "so an addition two parts share is made once" in TEXT
    assert "`part` where an addition is made for each part that has the conditional workflow" in TEXT
    applies = {r["Key"]: r["Applies"] for r in points()[1]}
    assert applies["run-parameters.parameters"] == "project"
    assert applies["planning.critic-lenses"] == "project"


def test_r006_how_a_phase_module_declares_its_points():
    """R-006's second half: in each phase module, the points that phase offers (written TASK-011–014)."""
    assert "in a section headed `## Extension points`, one line per point" in TEXT
    assert "A module declares exactly the points this registry names it as declaring" in TEXT


def test_r006_points_change_only_in_a_bridge_release_and_the_core_stays_closed():
    """§6.6: a renamed point fails loudly; §6.5: the core's guarantees are not extension points."""
    assert "only by the bridge's maintainer, in a bridge release" in TEXT
    assert "A project's supervisor never changes this file." in TEXT
    assert "can never remove a founding rule, weaken the merge gate, or skip the requirements register, the inventory or the reviews" in TEXT
