"""Release B — TASK-003: the conditional-workflow model stands in the core of supervisor.md.

enforces: docs/BUILD_PLAN.md TASK-003 Done when; the Restructuring Plan §6.2 (the five layers,
inheritance, read-when) and §6.5 (add / replace / set, the floor, sub-workflows, siblings, two
levels, additions applied together in a stated order). Satisfies R-007, R-008, R-009, R-034.
The section is core text: it sits after the division of labour and before the project layout,
outside the compaction digest, which keeps its limits.
"""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
SV = os.path.join(HERE, os.pardir, "bridge", "commands", "supervisor.md")
TEXT = open(SV, encoding="utf-8").read()
HEADING = "## Main and conditional workflows"


def model():
    a = TEXT.index(HEADING)
    b = TEXT.index("\n## ", a + len(HEADING))
    return TEXT[a:b]


def flat(s):
    """The section with its emphasis marks and line breaks removed, for phrase matching."""
    return re.sub(r"\s+", " ", s.replace("**", ""))


def layer_rows():
    rows = [r for r in model().split("\n") if r.startswith("| **")]
    return [[c.strip() for c in r.strip("|").split("|")] for r in rows]


def test_r007_the_section_is_core_text_between_the_division_of_labour_and_the_layout():
    """R-007: the model belongs to the core, which is read whole at every start."""
    i = TEXT.index(HEADING)
    assert TEXT.index("## The division of labour") < i < TEXT.index("## The project layout")
    assert i > TEXT.index("<!-- digest:end -->"), "the model is core text, not part of the digest"
    assert TEXT.count(HEADING) == 1


def test_r007_five_layers_in_order_each_with_what_it_holds_and_when_it_is_read():
    """R-007 (plan §6.2): main core, phase modules, type workflow, sub-workflow, trait additions."""
    rows = layer_rows()
    names = [re.sub(r"\*\*(.+?)\*\*.*", r"\1", r[0]) for r in rows]
    assert names == ["The main workflow's core", "Phase modules", "Type workflow", "Sub-workflow", "Trait additions"], names
    assert all(len(r) == 3 and r[1] and r[2] for r in rows), "every layer says what it holds and when it is read"
    holds = [r[1] for r in rows]
    assert holds[0] == ("The roles and the division of labour; the founding rules; the loop's shape; "
                        "escalation and reporting; project state; the standing rules that hold in every phase")
    assert holds[1] == ("The procedure for one phase each: intake, design, the interface phase, planning, "
                        "run parameters, configuration, the delegation loop, the change cycle, reflection points "
                        "and project end")
    assert holds[2] == "For one product type: its changes at named extension points"
    assert holds[3] == ("For one sub-type: a more detailed version of its type workflow, changing only what "
                        "differs for that sub-type")
    assert holds[4] == "For one trait: what it adds, whatever the product type"
    read_when = [r[2] for r in rows]
    assert read_when[0] == "Always, whole, at every start and calibration"
    assert read_when[1] == ("The current phase's module or modules, whole, on entering the phase and at every calibration; "
                            "a module read outside its own phase when \"The phase modules\" says")
    assert read_when[2] == "Its changes to the current phase, whole, alongside the phase's module or modules"
    assert read_when[3] == "Alongside its type workflow, when the part has a sub-type"
    assert read_when[4] == "Their additions to the current phase, when the part has the trait"


def test_r007_each_layer_inherits_what_it_does_not_mention_and_is_read_only_when_it_applies():
    """R-007, as carved (TASK-010): the core is read whole at every start, resume and calibration, and with it the
    current phase's module or modules and the conditional workflows that apply; after a compaction or resume, what
    the session-start hook names (rule 28)."""
    s = flat(model())
    assert "each inheriting everything it does not mention from the layers above it" in s
    assert ("This file, the core, is read whole at every start, resume and calibration, and with it the current "
            "phase's module or modules and the conditional workflows that apply; after every compaction or resume you "
            "read what the session-start hook names before your next action (rule 28)") in s, "the core stays whole; phases and conditionals add"
    # the exception names where the modules read outside their own phase are listed (PR #52's gate, Review A)
    assert ("You never read a phase you are not in or a conditional workflow that does not apply, except a module "
            "\"The phase modules\" says is read outside its own phase") in s
    assert "reading only the current phase" not in s, "the core is never replaced by a phase-only read"
    assert "Until the phases are moved into files of their own" not in s, "the transitional reading is gone with the carve"


def test_r007_each_phase_module_is_a_file_the_core_names():
    """R-007, as carved (TASK-010): the plan's phase names map to module files, each keeping its heading from this
    file, and the core's table names each one."""
    s = flat(model())
    assert ("Each phase's procedure is its phase module, one file per phase (see \"The phase modules\"): the interface "
            "phase is Phase 3, which today holds only the mockup variant; planning is Phase 4, configuration is Phase 5, "
            "the delegation loop is Phase 6; project end, once part of the reflection points, is a module of its own") in s
    phases = os.path.join(HERE, os.pardir, "bridge", "cursor-bridge", "workflow", "phases")
    for name, heading in (("intake", "## Phase 1 — Intake"), ("design", "## Phase 2 — Design"),
                          ("interface", "## Phase 3 — UI mockups"), ("planning", "## Phase 4 — Build plan"),
                          ("run-parameters", "## Run parameters"), ("configuration", "## Phase 5 — Configure"),
                          ("delegation-loop", "## Phase 6 — The delegation loop"), ("change-cycle", "## The change cycle"),
                          ("reflection", "## Reflection points"), ("project-end", "## Project end")):
        module = open(os.path.join(phases, name + ".md"), encoding="utf-8").read()
        assert module.startswith(heading), name
        assert "`~/.claude/cursor-bridge/workflow/phases/%s.md`" % name in TEXT, name
        assert "\n" + heading + "\n" not in TEXT and "\n" + heading + " " not in TEXT, "the core keeps no phase: " + name
    assert "only at the extension points" in s, "a conditional workflow changes the procedure only at declared points"


def test_r008_three_kinds_of_change_and_who_may_make_each():
    """R-008 (plan §6.5): add, replace, set; only types and sub-workflows replace or set."""
    s = flat(model())
    for kind in ("- Add —", "- Replace —", "- Set —"):
        assert kind in s, kind
    assert "only where the phase declares that it may be replaced" in s
    assert "Only type workflows and sub-workflows may replace or set; trait additions may only add." in s


def test_r008_no_conditional_workflow_touches_the_floor():
    """R-008: no founding rule removed, merge gate weakened, register / inventory / reviews skipped."""
    s = flat(model())
    floor = s[s.index("A conditional workflow can never"):]
    floor = floor[:floor.index(".") + 1]
    for item in ("remove a founding rule", "weaken the merge gate", "the requirements register", "the inventory", "the reviews"):
        assert item in floor, item
    assert "not extension points" in s
    assert "a conditional workflow's text that would do any of these does not apply, and on these points the core governs" in s


def test_r009_sub_workflow_inheritance_exclusive_siblings_two_levels():
    """R-009 (plan §6.5): a sub-workflow inherits and may override; siblings exclusive; two levels."""
    s = flat(model())
    assert "A sub-workflow inherits its type workflow" in s
    assert "may override its type workflow's replacement or setting" in s
    assert "Siblings are exclusive: a part has at most one sub-type of its product type" in s
    assert "Two levels only" in s and "a third level needs evidence from a real project" in s


def test_r034_additions_apply_together_in_a_stated_order():
    """R-034 (plan §6.5): additions from several workflows apply together, in a stated order."""
    s = flat(model())
    order = s[s.index("The order additions apply in."):]
    order = order[:order.index("A conditional workflow can never")]
    assert "apply together" in order and "never one in place of another" in order
    assert "at each extension point" in order, "the order holds where the additions land, not after the phase"
    assert "the open list governs this order and places a trait added later at its end" in order
    assert ("In a phase that covers several parts, at each extension point the phase module's own content there comes "
            "once, first; then, for each part in the order the status file lists them, that part's type workflow's, "
            "sub-workflow's and traits' additions, each applying to that part") in order
    assert ("A conditional workflow two parts share is read once, but its additions apply to every part that has it, "
            "in each part's own place in this order") in order, "a shared trait's work is done for every part"
    seq = ["the phase module's own", "the type workflow's", "the sub-workflow's", "each trait's"]
    pos = [order.index(p) for p in seq]
    assert pos == sorted(pos), "phase module, then type, then sub-workflow, then traits"
    traits = ["has screens", "installable", "performance budgets", "external services", "spends money",
              "long-running process", "AI models", "personal data", "multiplayer"]
    tpos = [order.index(t) for t in traits]
    assert tpos == sorted(tpos), "the traits in the order the open list gives them (plan §6.3)"
    assert "added later" in order, "a trait added later has a place in the order"
    assert "keep the order it writes them in" in order, "within one workflow its own order holds"


def test_the_digest_keeps_its_limits():
    """The new section must not push the digest past the hook's cap or out of a compaction's reach."""
    a, b = TEXT.find("<!-- digest:start -->"), TEXT.find("<!-- digest:end -->")
    assert 0 < a < b < 20000
    assert len(TEXT[a:b]) <= 9500
