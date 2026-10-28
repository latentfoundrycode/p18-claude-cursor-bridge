"""TASK-035: stage B3's review leads taken in the core and its modules (R-003).

enforces: docs/REQUIREMENTS.md R-003 (the core holds what every phase needs, the phase modules each phase's procedure,
every passage with one home); docs/BUILD_PLAN.md TASK-035's Done when (the leads docs/HARDENING.md, Stage B3, keys to
the pace plan revision, "Placed by the pace plan revision"; the maintainer's T23, the change cycle's intake confirmation
not a gate; FB-036, the core read in parts to its last line); docs/INVENTORY.md, Decisions (R-003's ruling that the 58
standing rules stay in the core; project end adds no refactoring pass of its own)."""
import os
import re

from phase_modules import read, module, flat, section

HERE = os.path.dirname(os.path.abspath(__file__))
BRIDGE = os.path.abspath(os.path.join(HERE, os.pardir, "bridge"))
CORE = os.path.join(BRIDGE, "commands", "supervisor.md")
GLOSSARY = os.path.join(BRIDGE, "cursor-bridge", "Glossary.md")
REGISTRY = os.path.join(BRIDGE, "cursor-bridge", "workflow", "extension-points.md")
EXCEPTIONS = os.path.join(BRIDGE, "cursor-bridge", "workflow", "trace-exceptions.md")

IN_PARTS = "in parts to its last line, each part starting where the last ended"


def core():
    return read(CORE)


def core_section(title):
    """The core's `## <title>` section, to the next `## ` heading."""
    text = core()
    start = text.index("\n## " + title + "\n")
    end = text.find("\n## ", start + 1)
    return text[start:end if end != -1 else len(text)]


def test_r003_project_end_adds_no_refactoring_pass_of_its_own():
    """R-003; TASK-035's Done when (refactoring-pass.md's project-end sentence; INVENTORY, Decisions): the last stage's
    close runs the pass and project end adds none, since project end's items follow the strict sync check."""
    s = flat(module("delegation-loop/refactoring-pass.md"))
    assert ("At **project end** no pass of its own runs: the last stage's close runs this pass, as every stage's close does "
            "under the refactoring parameter, and project end adds none, since a merge after project end's strict sync "
            "check would void that check.") in s
    assert "run one final pass over the whole tree" not in s
    assert "final pass" not in flat(module("project-end")), "project end names no pass of its own"


def test_r003_the_pointers_go_direct():
    """R-003; TASK-035's Done when (the two extra-hop pointers, Stage B3 round 1; run-parameters.md's "(below)", round
    3's C6): planning names project-end.md, intake names the file whose "Project state" holds the `Workflows:` grammar,
    and the run parameters name the core's escalation list, each by its file."""
    planning = flat(module("planning"))
    assert ("**the close of the last stage is project end** (see `~/.claude/cursor-bridge/workflow/phases/project-end.md` "
            "— it is a defined trigger, not a judgement).") in planning
    assert "(see \"Reflection points\" — it is a defined trigger" not in planning
    assert ("its close is a **reflection point** (see \"Reflection points\", "
            "`~/.claude/cursor-bridge/workflow/phases/reflection.md`).") in planning
    intake = flat(section(module("intake"), "Classifying each part", 3))
    assert ("Write each part's classification on the status file's `Workflows:` line, in the grammar the core's \"Project "
            "state\" gives it (`~/.claude/commands/supervisor.md`), with the traits proposed") in intake
    assert "A line has this grammar:" in core_section("Project state"), "the grammar the pointer names is there"
    params = flat(module("run-parameters"))
    assert ("Only the core's escalation list (\"Escalate to the user when\", `~/.claude/commands/supervisor.md`) and project "
            "end stop the loop.") in params
    assert "escalation list (below)" not in params
    assert "\n## Escalate to the user when\n" in core()


def test_r003_intake_points_at_the_registrys_delivery_kinds():
    """R-003; TASK-035's Done when (intake.md's third copy of the delivery kinds becomes a pointer at the registry):
    intake names the registry's list and holds no copy of its keys; the registry holds every key."""
    intake = flat(section(module("intake"), "Classifying each part", 3))
    assert ("by its key from the delivery kinds the extension-point registry lists "
            "(`~/.claude/cursor-bridge/workflow/extension-points.md`), for every part") in intake
    for key in ("`installer`", "`install-script`", "`package`", "`web-deployment`", "`store-package`",
                "`host-installation`"):
        assert key not in intake, key
        assert key in read(REGISTRY), key


def test_r003_a_critique_rounds_verdicts_and_hash_are_read_from_in_flight_md():
    """R-003; TASK-035's Done when (design.md's and planning.md's snapshot-hash bullets; Stage B3 round 4, modules):
    a resumed session reads the round's hash and each critic's verdict from run/supervisor/in-flight.md mid-round."""
    bullet = ("a round is snapshotted and verified as step 8 says, the snapshot's hash written to "
              "`run/supervisor/in-flight.md` at the launch and each critic's verdict there as it returns, both read from "
              "that file mid-round, and a failed launch is handled as step 3b says;")
    for key in ("design", "planning"):
        survival = flat(section(module(key), "What must survive a compaction", 3))
        assert bullet in survival, key


def test_r003_the_founding_rules_and_the_layout_name_the_modules():
    """R-003; TASK-035's Done when (supervisor.md's "Every procedure in this file" and "every path below"; Stage B3
    round 1 and round 4, core): what the core says of its own procedures and paths it says of the modules too."""
    assert ("Every procedure in this file and in its phase modules serves them, no run parameter loosens them"
            in flat(core_section("Founding rules")))
    layout = flat(core_section("The project layout"))
    assert "every path below and in the phase modules is relative to `Workspace/`." in layout
    assert "every path below is relative to" not in layout


def test_r003_the_status_template_has_a_deferred_increments_field():
    """R-003; TASK-035's Done when (the core's "Project state" template gains `Deferred increments:`, the list
    project-end.md names): the field stands in the template, and project end lists deferred increments in the status
    file."""
    template = core_section("Project state")
    fence = template[template.index("```markdown\n"):template.index("\n```\n", template.index("```markdown\n"))]
    lines = fence.split("\n")
    assert ("Deferred increments: <none | TASK-<nnn> — <title> — deferred by the owner on <date>; one per line>"
            in lines)
    assert lines.index([l for l in lines if l.startswith("Deferred increments:")][0]) == \
        lines.index([l for l in lines if l.startswith("Stage:")][0]) + 1
    assert "listed as deferred in the report and in `PROJECT_STATUS.md`" in flat(module("project-end"))


def test_r003_the_standing_rules_stay_in_the_core():
    """R-003; TASK-035's Done when (the R-003 ruling recorded in the core's "The phase modules"; INVENTORY, Decisions):
    all 58 rules stay in the core, numbered 1 to 58, and the section says why."""
    assert ("All 58 standing rules stay in this file, the phase-specific ones (29, 31 and 33) included: the digest cites "
            "them by number, and a rule moved to a module would leave a number the digest names pointing at nothing."
            in flat(core_section("The phase modules")))
    rules = core_section("Standing rules")
    numbers = [int(n) for n in re.findall(r"(?m)^(\d+)\. ", rules)]
    assert numbers == list(range(1, 59)), numbers


def test_r003_rule_34s_reword_has_its_own_increments_entry():
    """R-003; TASK-035's Done when (trace-exceptions.md's entry for rule 34's reword labelled TASK-014; Stage B3 round 4,
    core): TASK-014's reword of the Standing rules section has an entry under its own label, beside TASK-015's."""
    entries = read(EXCEPTIONS).split("\n")
    assert "- reword TASK-014 bridge/commands/supervisor.md Standing rules" in entries
    assert "- reword TASK-015 bridge/commands/supervisor.md Standing rules" in entries


def test_r003_the_change_cycles_intake_ends_with_a_confirmation_not_a_gate():
    """R-003; TASK-035's Done when (FB-032; the maintainer's T23): item 1 holds no `Gate:` token and ends with intake's
    closing confirmation, outside the three gates rule 34 names; the procedure's closing paragraph says the three are
    the only gates, its first sentence unchanged; the survival list's status bullet names an intake question."""
    text = module("change-cycle")
    proc = section(text, "The procedure", 3)
    item1 = proc[proc.index("1. **Intake of the change**"):proc.index("2. **Design revision**")]
    assert "Gate:" not in item1
    assert ("The item ends with a confirmation inside intake, not a gate: `intake.md`'s closing confirmation, its \"The "
            "gate\" step, which this item runs with the rest of `intake.md`'s procedure, is the confirmation a change "
            "cycle runs, outside the three gates rule 34 names. Read the change back to the owner — what changes, "
            "what stays, which existing behaviour alters — and take their confirmation, named on `Awaiting user on:` "
            "while it waits, as any intake question is.") in flat(item1)
    closing = flat(proc)
    assert ("The gates of a change cycle are the same approvals the original build had — the change design, the "
            "artifact of each interface variant the change runs, the plan addendum. They are the only gates a change "
            "cycle has, and whether the workflow applies is never a question.") in closing
    assert "They are the only questions a change cycle asks the owner" not in closing
    survival = flat(section(text, "What must survive a compaction", 3))
    assert "and `Awaiting user on:` a gate, or an intake question, that waits for the owner;" in survival
    assert "### The gate" in module("intake"), "the step item 1 names exists"


def test_r003_the_core_is_read_in_parts_to_its_last_line():
    """R-003; TASK-035's Done when (FB-036: the core is past the Read tool's one-call cap): the four statements that the
    core is read whole say it is read in parts to its last line, each part starting where the last ended; the
    Glossary entry's other words stand."""
    model = core_section("Main and conditional workflows")
    row = [l for l in model.split("\n") if l.startswith("| **The main workflow's core** |")][0]
    assert row.rstrip().endswith("| Always, " + IN_PARTS + ", at every start, resume and calibration |"), row
    assert ("This file, the core, is read " + IN_PARTS + ", at every start, resume and calibration, and with it the "
            "current phase's module or modules") in flat(model)
    assert "This file, the core, is read whole" not in flat(model)
    rules = flat(core_section("Standing rules"))
    assert "re-read the governing files whole, the core " + IN_PARTS + ", and apply the `CHANGELOG.md` delta" in rules
    glossary = [l for l in read(GLOSSARY).split("\n") if l.startswith("| **Main workflow core** |")]
    assert len(glossary) == 1
    entry = glossary[0]
    assert ("The part of the main workflow every project reads " + IN_PARTS + ", at every start, resume and "
            "calibration: the roles and the division of labour, the founding rules, the loop's shape, escalation and "
            "reporting, project state, and the standing rules that hold in every phase.") in entry
    assert "It is not an extension point; no conditional workflow changes it." in entry
    assert "reads whole" not in entry


def test_task022_lead_the_glossary_names_the_contract_a_part_offers():
    """Not R-003's: docs/HARDENING.md, Stage B4, TASK-022's lead (consider 7: a glossary row at the glossary's next
    edit), which TASK-035's edit of the glossary takes:
    the contract a part offers and its contract file have a term apart from the service contract."""
    rows = [l for l in read(GLOSSARY).split("\n") if l.startswith("| **Offered contract** |")]
    assert len(rows) == 1
    assert "the contract file" in rows[0] and "`docs/design/CONTRACT.md`" in rows[0]
    assert "Not a *service contract*" in rows[0]
