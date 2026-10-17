"""Release B — TASK-005: the extension-point registry.

enforces: docs/BUILD_PLAN.md TASK-005 (its Scope path and Done when); the Restructuring Plan §6.4
(the initial points per phase, Definition of done and Delivery included; the interface phase
replaceable), §6.5 (add, replace, set; only type workflows and sub-workflows replace or set) and
§6.11 (the phase modules' paths, `workflow/phases/<phase>.md`). Satisfies R-006.
The two tables are the shape `workflow-check.py` (TASK-006) reads: each found by its heading, the
first Markdown table after it (its rows running to the first line that is not a table line), one row
per entry, cells split on `|`, columns found by their header names.
"""
import os
import re

from test_open_list import table as open_list_table

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
    # The two refinements of §6.4's list: §6.5 names the kind of performance budget and the delivery
    # kind as values a type workflow or sub-workflow sets, and the core settles both at intake
    # (supervisor.md, Phase 1), before design and planning act on them.
    ("Intake", "kind of performance budget", "intake.budget-kind"),
    ("Intake", "kind of delivery", "intake.delivery-kind"),
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
# two examples, the kind of performance budget and the delivery kind, and §6.4's target environment;
# all three at intake, where the core settles them. Project end's delivery point holds the procedure.
SETTABLE = {"intake.target-environment", "intake.budget-kind", "intake.delivery-kind"}
# Which additions exist once for the whole project rather than per part (the round-1 record ratifies it).
PROJECT_WIDE = {"design.diagram-catalogue", "planning.critic-lenses", "run-parameters.parameters",
                "configuration.items", "reflection.items"}


def table(heading):
    """The first Markdown table after `heading` in the registry, parsed as test_open_list parses the open list's."""
    return open_list_table(heading, TEXT)


def modules():
    return table("## Phase modules")


def points():
    return table("## Extension points")


def test_r006_the_file_sits_at_its_planned_path_and_is_bounded():
    """R-006, BUILD_PLAN TASK-005 Scope: `workflow/extension-points.md` beside the open list; a bounded
    reference text."""
    assert os.path.isfile(EP)
    raw = open(EP, encoding="utf-8", newline="").read()
    assert "\r" not in raw.replace("\r\n", "\n"), "no lone carriage return (a CRLF checkout is fine; stage B2 review, round 3)"
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
    assert [r["Key"] for r in rows] == [k for _, _, k in S64], "the §6.4 points and the two refinements, in §6.4's order"
    for phase, phrase, key in S64:
        r = by_key[key]
        assert r["Phase"] == phase, key
        assert phrase.lower() in r["Point"].lower(), key
        assert r["Declared by"] == key.split(".")[0], key
    assert {"Definition of done", "Delivery"} <= {r["Phase"] for r in rows}
    assert "Two points are added to §6.4's list, both at intake, because §6.5 names their kinds as values a type workflow or sub-workflow sets and the core settles both at intake, before design and planning act on them" in TEXT
    assert "`project-end.delivery` holds the procedure for the kind set there" in TEXT


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
    assert "`## Add at project-end.delivery for <delivery kind>`" in TEXT
    assert ("At that point this form is required and the plain `## Add at project-end.delivery` fails; at every "
            "other point a heading ending `for <kind>` fails.") in TEXT
    assert "The value is the section's first non-blank line" in TEXT
    assert "Only a type workflow or a sub-workflow may set." in TEXT
    assert "Only a type workflow or a sub-workflow may replace." in TEXT
    assert "A trait attaches to the main workflow only through its `Add at` headings" in TEXT
    assert "A trait never replaces (§6.5)." in TEXT


def test_r006_a_shared_addition_at_a_project_point_is_made_once():
    """TASK-003's deferral: a project-wide addition from a conditional workflow two parts share."""
    assert "so an addition two parts share is made once" in TEXT
    assert "`part` where an addition is made for each part that has the conditional workflow" in TEXT
    assert "in the place of the first part, in the status file's order, that has the conditional workflow" in TEXT
    assert "is the rule for `part` points, and a `project` point is the one exception, as stated here" in TEXT
    applies = {r["Key"]: r["Applies"] for r in points()[1]}
    assert {k for k, v in applies.items() if v == "project"} == PROJECT_WIDE


def test_r006_how_a_phase_module_declares_its_points():
    """R-006's second half: in each phase module, the points that phase offers (written TASK-011–014)."""
    assert "in a section headed `## Extension points`, one line per point" in TEXT
    assert "A module declares exactly the points this registry names it as declaring" in TEXT


def test_r006_points_change_only_in_a_bridge_release_and_the_core_stays_closed():
    """§6.6: a renamed point fails loudly; §6.5: the core's guarantees are not extension points."""
    assert "only by the bridge's maintainer, in a bridge release" in TEXT
    assert "A project's supervisor never changes this file." in TEXT
    assert "can never remove a founding rule, weaken the merge gate, or skip the requirements register, the inventory or the reviews" in TEXT


def test_r006_a_replacement_keeps_the_points_of_the_module_it_replaces():
    """§6.5 ("Today's interface conditions stay together") and TASK-003's deferral: additions from the
    layers below still land on a replaced phase."""
    assert "A replacement keeps the points of the module it replaces, without declaring them again under its `## Replace` heading" in TEXT
    assert ("so every conditional workflow's additions at those points still apply to it, in the core's order: "
            "the type workflow's, the sub-workflow's and each trait's") in TEXT
    assert "such as the trait *has screens* adding the mockup variant at `interface.variants`" in TEXT


def test_r006_what_the_workflow_check_fails():
    """§6.5/§6.6: an unlisted point, a set where no value is open, a replace of a fixed phase."""
    assert ("A conditional workflow that changes anything at a point not listed here, sets a value at a point whose "
            "Changes do not include `set`, or replaces a phase not marked replaceable here, fails `workflow-check.py`") in TEXT


def test_r006_an_addition_at_a_value_point_never_sets_a_second_value():
    """§6.5: only type workflows and sub-workflows set; a trait's addition at a value point adds to it."""
    assert "at a point that holds a value, an addition adds to what is asked or recorded about that value" in TEXT
    assert "never a second value" in TEXT


def test_r006_a_completion_condition_the_plan_builds_toward_enters_at_intake():
    """The plan is checked against the register (completion-check --mode plan); a condition read only at
    project end would never shape it."""
    assert ("a condition the plan must build toward is also added at intake (`intake.requirement-sources`), "
            "naming that completion condition as its source") in TEXT


def test_r006_a_delivery_procedure_applies_only_to_its_kind():
    """§6.9 (an installer in place of a deployment) and BUILD_PLAN TASK-019/021: with the procedure
    add-only, an addition must name its kind, or a type's procedure would reach a sub-type of another kind."""
    assert "Each addition at `project-end.delivery` names the delivery kind it is for and applies only to a part of that kind" in TEXT
    assert "a sub-workflow that sets another kind leaves its type workflow's procedure behind" in TEXT


def test_r006_the_delivery_kinds_are_one_list_and_an_unset_kind_is_intakes():
    """Delivery-Conventions.md §1 and §6.4's kinds as one list; a part no workflow sets a kind for (the TDP's
    path, BUILD_PLAN TASK-020) takes the kind confirmed at intake, so a trait's procedure still reaches it."""
    for kind in ("installer", "install-script", "package", "web-deployment", "store-package", "host-installation"):
        assert "`%s` (" % kind in TEXT, kind
    assert ("the value set at `intake.delivery-kind` and the kind an addition at `project-end.delivery` names "
            "are both drawn from it") in TEXT
    assert ("Where no type workflow or sub-workflow sets a part's kind, the kind the supervisor confirms with the "
            "owner at intake (Phase 1) is the part's kind, recorded by its key from this list") in TEXT


def test_r006_the_inspect_and_test_steps_divide_every_check():
    """supervisor.md Phase 6 (steps 4 to 6 and step 9) and BUILD_PLAN TASK-017: every check the loop makes of
    any change has one point — the benchmark floor (performance budgets, §6.8) at the test step, the design
    auditor's pass (has screens), which runs after the tests, at the inspect step, the refactoring pass included;
    the merge gate is the core's."""
    assert ("The two points divide between them every check and review the delegation loop makes of a change, "
            "wherever the module's text places it and whatever the change is: an increment, a fix, a refactoring "
            "candidate, or the gate pass of a stage's refactoring branch") in TEXT
    assert "the checks that run with them, such as the observability tests and the benchmark floor" in TEXT
    assert "step 6 runs no tests of its own, the tests having run in step 4" in TEXT
    assert "the trait *performance budgets* carries the floor (§6.8)" in TEXT
    assert "The inspect step is every other check or review, before the tests or after them" in TEXT
    assert "the reviewer passes (such as the design auditor the trait *has screens* carries)" in TEXT
    assert "The merge gate's conditions (step 8) belong to the core and offer no point" in TEXT
    assert "a CI check a conditional workflow needs is added at `configuration.items`" in TEXT
    assert ("the scope check, the diagram check, the boundary log, the triage of the builder's assumptions, the "
            "reviewer passes (such as the design auditor the trait *has screens* carries), the secret scan and the "
            "dependency admission") in TEXT
    assert "An addition at either point is placed in the delegation loop's text at the step that runs it." in TEXT


def test_r006_the_checks_delivery_kinds_are_the_registrys(program):
    """The list lives in this text and in workflow-check.py's DELIVERY_KINDS; they change together (stage B2
    review)."""
    start = TEXT.index("The delivery kinds are one list")
    paragraph = TEXT[start:TEXT.index("\n", start)]  # to the paragraph's end, not the file's (stage B2 review, round 4)
    listed = re.findall(r"`([a-z-]+)` \((?:a |an )", paragraph)
    assert tuple(listed) == program("workflow-check").DELIVERY_KINDS, listed


def test_r006_the_registry_names_the_change_words_the_check_reads(program):
    """A prose heading that reads like a change fails; the registry names the words and the stripped
    punctuation workflow-check.py's CHANGE_FIRST and TRAILING_PUNCT hold, and the one-per-target rule (stage
    B2 review, round 4)."""
    start = TEXT.index("Any other `##` heading is prose")
    paragraph = TEXT[start:TEXT.index("\n", start)]
    words_text = paragraph[paragraph.index("ignored, is ") + len("ignored, is "):paragraph.index(", or whose second")]
    words = set(re.findall(r"[a-z]+", words_text)) - {"or"}
    wc = program("workflow-check")
    assert words == set(wc.CHANGE_FIRST), words
    punct = paragraph[paragraph.index("any trailing ") + len("any trailing "):paragraph.index(" ignored")]
    assert set(re.findall(r"`(.)`", punct)) == set(wc.TRAILING_PUNCT), punct
    assert "or whose second word is `at` in any case, fails as a malformed change heading" in paragraph
    assert "A file sets each point, and replaces each module, at most once." in paragraph
    assert ("A `##` line inside a fenced code block (opened by three or more backticks or tildes) is not a heading and "
            "changes nothing.") in paragraph


def test_r006_the_phase_modules_paths_and_the_change_cycles_empty_declaration():
    """§6.11: each module is `workflow/phases/<module>.md`; TASK-014's two-way cross-check needs one answer
    for the change cycle."""
    assert "`workflow/phases/<module>.md` (§6.11)" in TEXT
    assert "its module has no `## Extension points` section" in TEXT
    assert "Each phase module that declares points does so in a section headed `## Extension points`" in TEXT
