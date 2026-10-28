"""TASK-011: the intake and design modules enriched (R-004, R-006, R-013, R-032, R-035, R-036).

enforces: docs/REQUIREMENTS.md R-004 (each phase module opens with the short list of what must survive a compaction),
R-006 (each phase module declares the points the registry names it as declaring), R-013 (a part that fits no product
type, two equally, or one not yet written pauses the project at intake and sends the owner to the maintainer), R-032
(each module read whole), R-035 (traits proposed at intake, settled at the design gate, a type's default traits
likewise), R-036 (a new or unwritten trait written into the design and flagged at the design gate, where the owner may
still pause; the promotion-pass half is TASK-014's); docs/BUILD_PLAN.md TASK-011's Done when, and its Scope's pointer
sweep (docs/HARDENING.md, Stage B3)."""
import os
import re

import pytest

from phase_modules import read, module, flat, headings, section, registry_points

HERE = os.path.dirname(os.path.abspath(__file__))
BRIDGE = os.path.abspath(os.path.join(HERE, os.pardir, "bridge"))
REGISTRY = os.path.join(BRIDGE, "cursor-bridge", "workflow", "extension-points.md")
POLICY = os.path.join(BRIDGE, "cursor-bridge", "Merge-Verification-Policy.md")
PLAN_CRITIC = os.path.join(BRIDGE, "agents", "plan-critic.md")
CHECK = "`python ~/.claude/cursor-bridge/workflow-check.py --status docs/PROJECT_STATUS.md`"


STRUCTURE = {
    "intake": [(2, "Phase 1 — Intake"), (3, "What must survive a compaction"), (3, "The procedure"),
               (3, "The intake notes"), (3, "Classifying each part"), (3, "The gate"), (2, "Extension points")],
    "design": [(2, "Phase 2 — Design"), (3, "What must survive a compaction"), (3, "The procedure"),
               (4, "A part without screens"), (3, "The delivery kind"), (3, "Traits at the design gate"), (3, "The gate"), (2, "Extension points")],
}

SURVIVAL = {
    "intake": [
        "this module, whole;",
        "the owner's Initial Design Draft in `Documents/`, whole, if they wrote one, and every requirements document "
        "they supplied;",
        "`run/supervisor/intake-notes.md`: every question asked so far and the owner's answer to it, written there as "
        "each answer arrives, because the conversation that held them does not survive a compaction (rule 54);",
        "the open list, `~/.claude/cursor-bridge/workflow/open-list.md`, whole, until every part is classified;",
        "`docs/PROJECT_STATUS.md`, whole: its `Workflows:` line and its `Awaiting user on:` line say how far the "
        "classification and the questions have gone;",
        "once this phase's gate is approved, its reflection point: `~/.claude/cursor-bridge/workflow/phases/reflection.md`, "
        "whole, and the last entries of `run/supervisor/in-flight.md`, the items it has finished (\"Keeping the "
        "position\"), until the reflection point is done.",
    ],
    "design": [
        "this module, `~/.claude/cursor-bridge/Diagram-Planning-Conventions.md` and `~/.claude/cursor-bridge/Glossary.md`, "
        "each whole (the session-start hook names all three);",
        "what the design has written so far: `docs/DESIGN.md`, `docs/diagrams/INDEX.md` and every diagram it lists, and "
        "`docs/REQUIREMENTS.md` and `docs/INVENTORY.md` once written;",
        "`docs/DESIGN_CRITIQUE.md`, whole, while the critique runs: its rounds and its accepted list are what the stop "
        "rule and the four-round ceiling count, so that a resumed session never runs a round twice or raises an accepted "
        "finding again; with it `docs/RUN_PARAMETERS.md`, where an owner's `Design rounds above five:` line lifts the "
        "ceiling, and the round's files under `run/review/` (`DESIGN-<subject>-<round>.md` and its `REVIEW-DESIGN-` "
        "files) while a round is in flight;",
        "the owner's Initial Design Draft, every requirements document they supplied and "
        "`run/supervisor/intake-notes.md`, whole: the design and the requirements register answer them;",
        "`docs/PROJECT_STATUS.md`, whole: its `Workflows:` line holds the traits proposed at intake, which this phase's "
        "gate settles;",
        "`~/.claude/cursor-bridge/workflow/phases/delegation-loop.md`'s steps 3b and 8, while a critique round is in "
        "flight or a launch has failed: a round is snapshotted and verified as step 8 says, the snapshot's hash "
        "written to `run/supervisor/in-flight.md` at the launch and each critic's verdict there as it returns, "
        "both read from that file mid-round, and a failed launch is handled as step 3b says;",
        "once this phase's gate is approved, its reflection point: `~/.claude/cursor-bridge/workflow/phases/reflection.md`, "
        "whole, and the last entries of `run/supervisor/in-flight.md`, the items it has finished (\"Keeping the "
        "position\"), until the reflection point is done.",
    ],
}


@pytest.mark.parametrize("key", ["intake", "design"])
def test_r004_the_module_opens_with_its_compaction_survival_list(key):
    """R-004: the module's first section, straight after its heading, is the compaction-survival list (the Glossary's
    term), and the list is exactly what a resumed session in that phase reads before its next action."""
    text = module(key)
    assert headings(text) == STRUCTURE[key], headings(text)
    lines = text.split("\n")
    assert lines[1] == "" and lines[2] == "### What must survive a compaction", lines[:3]
    body = section(text, "What must survive a compaction", 3).strip().split("\n")
    assert body[0] == "After a compaction or a resume in this phase, read these before your next action:"
    items = [l[2:] for l in body[1:] if l]
    assert all(l.startswith("- ") for l in body[1:] if l), body
    assert items == SURVIVAL[key], items


@pytest.mark.parametrize("key", ["intake", "design"])
def test_r006_the_module_declares_exactly_its_registry_points_in_the_registrys_order(key):
    """R-006 and the registry's "How a phase module declares its points": a `## Extension points` section, one line
    per point giving its key, exactly the points the registry names this module as declaring, in the table's order;
    each line says where in the module an addition there is made."""
    text = module(key)
    body = section(text, "Extension points", 2).strip().split("\n")
    lines = [l for l in body if l.startswith("- ")]
    keys = [re.match(r"^- `([a-z0-9.-]+)` — \S", l).group(1) for l in lines]
    want = registry_points(key)
    assert want and keys == want, (keys, want)
    prose = flat(" ".join(l for l in body if l and not l.startswith("- ")))
    assert prose == ("This module offers the points below, each by its key in the extension-point registry "
                     "(`~/.claude/cursor-bridge/workflow/extension-points.md`), which states the kinds of change each "
                     "accepts and whether it applies per part or per project. A conditional workflow's additions at a "
                     "point are made where the point's line places them, in the order the core states in \"Main and "
                     "conditional workflows\".")


def test_r006_the_set_points_say_who_may_set_them():
    """R-006: the three intake points whose Changes include `set` say a type workflow or sub-workflow may set them;
    the delivery kind says what holds where none does (the registry's paragraph on the delivery kinds)."""
    body = section(module("intake"), "Extension points", 2)
    for point in ("intake.target-environment", "intake.budget-kind", "intake.delivery-kind"):
        line = [l for l in body.split("\n") if l.startswith("- `%s`" % point)][0]
        assert "a type workflow or sub-workflow may set it" in line, point
    for point in ("intake.questions", "intake.requirement-sources"):
        line = [l for l in body.split("\n") if l.startswith("- `%s`" % point)][0]
        assert "may set" not in line, point
    assert "where none does, the kind you confirm with the owner is the part's." in body
    assert "may set" not in section(module("design"), "Extension points", 2)


def test_r013_a_part_that_does_not_fit_pauses_the_project_at_intake():
    """R-013 (§6.7): every case that pauses (no fit, two equally, an unwritten type, two sub-types equally, an unwritten
    sub-type), the stop before design, the status line, the owner sent to the maintainer with the reasons as a run
    sheet, and the resume after the release and the calibration."""
    s = flat(section(module("intake"), "Classifying each part", 3))
    assert ("**A part that does not fit pauses the project before design.** When a part fits no product type, fits two "
            "equally, fits one whose workflow is not yet written, fits two sub-types of its type equally, or fits a "
            "sub-type whose sub-workflow is not yet written (its open-list row reads `no` under Written, and the check "
            "prints `FAIL (f)`), the project stops before design: no design work starts for any part.") in s
    assert ("A part that fits no entry, or two equally, keeps `not yet classified` on its line; a part that fits an "
            "entry not yet written is named by it, so the check shows the pause.") in s
    # the questions end before the status line is written, so that an answer is never read as the word to resume
    assert ("Finish intake's questions first, then write `Awaiting user on: paused at intake — <the part> needs a "
            "workflow the bridge has not written`, and put the pause at the head of your report as a run sheet (rule "
            "27); it is not a choice put to the owner but a step they take: the owner takes your reasons to the bridge's "
            "maintainer, in the maintainer's own session (the part, the definitions you weighed it against, and why none "
            "fits, which two fit equally, or which workflow is not yet written)") in s
    assert "then run " + CHECK in s


def test_r013_the_resume_classifies_the_part_before_the_gate():
    """R-013 (PR gate, Review A should-fix): a part kept `not yet classified` passes the check at once, so the resume
    classifies it against the open list as it then stands and runs the check before the gate; no part reaches the gate
    unclassified."""
    s = flat(section(module("intake"), "Classifying each part", 3))
    assert ("The release goes out, the project calibrates (`/calibrate-bridge`), and you resume on the owner's word: "
            "classify the part again against the open list as it now stands, write its `Workflows:` line, and run the "
            "check; only when it passes does intake go on to its gate. No part goes to the gate `not yet "
            "classified`.") in s


def test_r004_the_intake_answers_are_kept_on_disk_and_no_key_among_them():
    """R-004 (the survival list names the intake notes) and Review A's should-fix: writing the notes is an instruction
    of the procedure, the file is named on Working files: (rule 54), and the security audit's advisory: no key, token
    or password is written there."""
    s = flat(section(module("intake"), "The intake notes", 3))
    assert ("Write every question you ask and the owner's answer to it to `run/supervisor/intake-notes.md` as each "
            "answer arrives, and name the file on the status file's `Working files:` line (rule 54)") in s
    assert ("A key, token or password the owner gives is never written there: note only that one was given and where it "
            "now lives") in s


def test_r006_the_delivery_kind_is_confirmed_for_every_part_and_recorded():
    """R-006, `intake.delivery-kind` (the registry: where nothing sets a part's kind, the kind confirmed at intake is
    the part's, recorded by its key; Review A's should-fix): confirmed for every part, not only installable software,
    by a key from the registry's list, and recorded by the design as a `Delivery kind:` Decisions row."""
    intake = flat(section(module("intake"), "Classifying each part", 3))
    assert ("confirm with the owner the kind of delivery the part ends in, by its key from the delivery kinds the "
            "extension-point registry lists (`~/.claude/cursor-bridge/workflow/extension-points.md`), for every part "
            "and not only for installable software") in intake
    assert "`store-package`" not in intake, "intake points at the registry's list, holding no copy of it (TASK-035)"
    registry = read(REGISTRY)
    for kind in ("installer", "install-script", "package", "web-deployment", "store-package", "host-installation"):
        assert "`%s`" % kind in registry, kind
    design = flat(section(module("design"), "The delivery kind", 3))
    assert ("When you create `docs/INVENTORY.md`, record each part's delivery kind as a Decisions row that begins "
            "`Delivery kind:`, naming each part and its kind's key from the extension-point registry") in design


def test_r035_traits_are_proposed_at_intake_and_settled_at_the_design_gate():
    """R-035 (§6.3 "When they are decided"): the product type and sub-type fixed at intake; traits, and a type's
    default traits, proposed at intake and settled at the design gate, as a decision of their own there."""
    intake = flat(section(module("intake"), "Classifying each part", 3))
    assert ("its product type and, where one fits, its sub-type, which are fixed here because every phase that follows "
            "depends on them; and its traits, which are proposed here and settled at the design gate") in intake
    assert ("The default traits the open list gives a product type or sub-type are proposals too, settled at the same "
            "gate.") in intake
    design = flat(section(module("design"), "Traits at the design gate", 3)).strip()
    assert design.startswith("The traits proposed at intake, the default traits of each part's product type and "
                             "sub-type among them, are settled at this gate")
    assert ("At the gate each part's traits are a decision of their own, asked in the question form beside the separate "
            "decisions the gate below lists: each trait with its definition in one line and, in plain words, the work it "
            "adds.") in design
    assert "rewrite the part's `Workflows:` line if they changed, and run " + CHECK + " again." in design


def test_r036_a_new_or_unwritten_trait_is_flagged_at_the_design_gate_with_the_owners_pause():
    """R-036, its design-gate half (§6.7): the trait's handling written into the design, flagged at the gate where the
    owner may still pause, a pause going to the maintainer as an unwritten type does, and the flag recorded where the
    promotion pass at project end finds it."""
    s = flat(section(module("design"), "Traits at the design gate", 3))
    assert "**A new or unwritten trait is flagged, and the work continues.**" in s
    assert ("a trait whose open-list row reads `no` under Written (the check's `FLAG (trait)`) is defined but not yet "
            "written") in s
    assert ("write the extra handling into `docs/DESIGN.md`, a section of its own for each such trait saying what it "
            "adds and in which phases, and flag it at the gate as a decision of its own, saying plainly that until the "
            "bridge writes the trait's additions the design's section is the only handling it has: the work continues "
            "with the handling in the design, or the owner may still choose to pause the project.") in s
    assert "`Awaiting user on: paused at the design gate — <the trait> needs additions the bridge has not written`" in s
    # Review A's should-fix: after the pause, a new trait joins the line and the check runs, or its additions never apply
    # Review B's should-fix at PR #53, taken in TASK-012: an unwritten trait already on the line resumes the same way
    assert ("On resuming, a new trait, now in the open list, is added to each part's `Workflows:` line that has it; for "
            "a new trait and for an unwritten one already on the line alike, the check is run again, and the trait's "
            "additions, now written, take the place of the design's section.") in s
    assert ("Record each flagged trait in `docs/INVENTORY.md` → Decisions as a row that begins `Flagged trait:`, naming "
            "the trait, the parts that have it and the design section that handles it, so that the promotion pass at "
            "project end puts it forward") in s
    assert "once the trait's additions are written and apply, the row is removed." in s
    intake = flat(section(module("intake"), "Classifying each part", 3))
    assert "A `FLAG (trait)` line names a trait whose additions are not yet written: the work continues" in intake


@pytest.mark.parametrize("key", ["intake", "design"])
def test_r032_the_module_is_read_whole(key):
    """R-032: the enriched module stays within the bound a module is read whole by (1,500 lines, 60,000 characters)."""
    text = module(key)
    assert text.count("\n") <= 1500 and len(text) <= 60000, (key, text.count("\n"), len(text))


def test_the_design_phase_is_named_by_its_module_outside_the_core():
    """The carve's pointer sweep for the design module (docs/HARDENING.md, Stage B3): the merge policy and the plan
    critic named the design critique's bound as `supervisor.md`'s Phase 2, which now lives in design.md."""
    for path in (POLICY, PLAN_CRITIC):
        text = read(path)
        assert "(`supervisor.md`, Phase 2)" not in text, path
        assert "(`~/.claude/cursor-bridge/workflow/phases/design.md`, Phase 2)" in text, path
    assert read(POLICY).count("(`~/.claude/cursor-bridge/workflow/phases/design.md`, Phase 2)") == 2
