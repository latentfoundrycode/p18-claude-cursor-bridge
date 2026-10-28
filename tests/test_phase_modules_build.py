"""TASK-013: the run-parameters, configuration and delegation-loop modules enriched (R-004, R-006, R-032).

enforces: docs/REQUIREMENTS.md R-004 (each phase module opens with the short list of what must survive a compaction),
R-006 (each phase module declares the points the registry names it as declaring), R-032 (each module read whole: the
delegation-loop module, at 94% of the bound's characters before this increment, is split, its step 9 in a sub-file under
workflow/phases/delegation-loop/ that the module's own `Sub-files:` line names and the session-start hook follows);
docs/BUILD_PLAN.md TASK-013's Done when, and the pointer sweep for the split (the core's module table)."""
import json
import os
import re
import shutil
import subprocess
import sys

import pytest

from phase_modules import read, module, flat, headings, section, registry_points

HERE = os.path.dirname(os.path.abspath(__file__))
BRIDGE = os.path.abspath(os.path.join(HERE, os.pardir, "bridge"))
CB = os.path.join(BRIDGE, "cursor-bridge")
PHASES = os.path.join(CB, "workflow", "phases")
REGISTRY = os.path.join(CB, "workflow", "extension-points.md")
CORE = os.path.join(BRIDGE, "commands", "supervisor.md")
HOOK = os.path.join(CB, "session-start.py")

SUB = "delegation-loop/refactoring-pass.md"
STEP9 = "9. Refactoring and optimization pass (at stage close)"
DECIDE = "delegation-loop/decide.md"
STEP7 = "7. Decide (accept the increment)"
SUBS = [DECIDE, SUB]


# the loop's steps as the module holds them, each with the sub-sections TASK-030 adds (step 7 itself in its sub-file,
# the module keeping a pointer section under the step's number)
LOOP_HEADINGS = [(3, "1. Checkpoint"), (3, "2. Package the brief"), (3, "3. Delegate to Cursor"),
                 (4, "The model, the timeout and the limit"),
                 (3, "3b. A model fails mid-step — switch automatically, restart the step, never wait"),
                 (4, "Waiting for the slot, and a mutation run cut short"), (3, "4. Inspect"),
                 (4, "The tests before the first reviewer"), (4, "The reviewers"), (3, "5. Scan"),
                 (3, "5b. Dependency-admission gate"), (3, "6. Benchmarks and observability"),
                 (3, "7. Decide — in a sub-file"), (3, "8. Merge (the verified gate)")]

STRUCTURE = {
    "run-parameters": [(2, "Run parameters — asked once, after the plan is approved, before configuration"),
                       (3, "What must survive a compaction"), (3, "The procedure"), (3, "Writing the answers down"),
                       (2, "Extension points")],
    "configuration": [(2, "Phase 5 — Configure the Cursor build environment"), (3, "What must survive a compaction"),
                      (3, "The procedure"), (3, "The windowless test suite"), (3, "Keeping the position"),
                      (2, "Extension points")],
    "delegation-loop": [(2, "Phase 6 — The delegation loop"), (3, "What must survive a compaction"), (3, "The procedure")]
                       + LOOP_HEADINGS + [(2, "Extension points")],
}

INTRO = {
    "run-parameters": "After a compaction or a resume in this step, read these before your next action:",
    "configuration": "After a compaction or a resume in this phase, read these before your next action:",
    "delegation-loop": "After a compaction or a resume in this phase, read these before your next action:",
}

SURVIVAL = {
    "run-parameters": [
        "this module, whole;",
        "`docs/RUN_PARAMETERS.md` as written so far, whole: each answer is written there as the owner gives it "
        "(\"Writing the answers down\"), so the questions still to ask are the parameters it does not yet hold;",
        "`docs/BUILD_PLAN.md`, the approved plan, whole: a refactoring answer may name its stages, and parallel "
        "increments apply only where the plan marks increments `Parallel: yes`;",
        "`docs/PROJECT_STATUS.md`, whole: its `Workflows:` line names each part's conditional workflows, which add "
        "parameters at `run-parameters.parameters` and show whether a part is installable, as installer verification "
        "needs, and its `Awaiting user on:` line names the question that waits for the owner.",
    ],
    "configuration": [
        "this module, whole, with `~/.claude/cursor-bridge/Cursor-Project-Configuration.md` and "
        "`~/.claude/cursor-bridge/Known-Pitfalls.md`, each whole (the session-start hook names both for this phase);",
        "the approved design and plan: `docs/DESIGN.md`, `docs/REQUIREMENTS.md`, `docs/BUILD_PLAN.md` and "
        "`docs/RUN_PARAMETERS.md`, whole: only the items that are load-bearing for this project are applied;",
        "`docs/PROJECT_STATUS.md`, whole: its `Next:` line names the items configured so far and the next one (\"Keeping "
        "the position\"), its `Awaiting user on:` line an escalation that waits for the owner, and its `Workflows:` line "
        "the conditional workflows that add items at `configuration.items`;",
        "`docs/INVENTORY.md`, whole: its Resources rows record each pinned tool and version, each mode in force and each "
        "spending limit as the items are configured.",
    ],
    "delegation-loop": [
        "this module and its sub-files, each whole (the session-start hook names them), with "
        "`~/.claude/cursor-bridge/Merge-Verification-Policy.md` and `~/.claude/cursor-bridge/Known-Pitfalls.md`, each "
        "whole, and the other files the hook names;",
        "`docs/PROJECT_STATUS.md` and `docs/INVENTORY.md`, whole (rule 41), and the last entries of "
        "`run/supervisor/in-flight.md` where it exists: the increment in hand, its branch and its checkpoint, the "
        "background runs that will wake you and what waits for the owner; while Review B runs the status file is not "
        "written and the position is kept in `in-flight.md` (step 8), and at the launch you write there the snapshot's "
        "hash `review-guard.py snapshot` printed, since the hash `verify` prints must equal it (this list is where "
        "that write is asked for);",
        "the increment's entry in `docs/BUILD_PLAN.md`, its brief `handoff/TASK-<nnn>.md` and every numbered brief after "
        "it (`handoff/<ID>-r<N>.md`, step 3), and each builder report `handoff/TASK-<nnn>-r<N>-report.md`, whole: the "
        "brief bounds the increment, and the report "
        "holds the `Assumed, not verified` list whose every item takes a disposition (rule 42);",
        "for a fix (step 7, the `root-cause-first` procedure), `docs/debug/BUG-<nnn>.md`, whole: its hypotheses and the "
        "diagnostic rounds counted toward a resolution round; the fix brief, `handoff/<ID>-r<N>.md` inside an "
        "increment's gate or `handoff/BUG-<nnn>.md` for a defect found after a merge (step 7), with its reports, as for "
        "a task; and `git grep DEBUG-BUG-<nnn>` for instrumentation not yet removed;",
        "`docs/RUN_PARAMETERS.md` and `docs/ROSTER.resolved.json`: who completes a merge, whether the refactoring pass "
        "runs and whether increments run in parallel, and the models the delegate command and Review B name;",
        "the increment's verdicts, kept in `run/supervisor/in-flight.md`: Review A's, each auditor's and Review B's "
        "reply, each written there as it returns, and the mutation run's cuts and estimate (step 7);",
        "the runs' files: `run/agent/TASK-<nnn>.err`, which step 3b reads after a failed call, "
        "`run/agent/TASK-<nnn>.assumptions.md`, the only copy of a list the builder printed only in its last message "
        "(step 4), `run/agent/TASK-<nnn>-suite.out`, which `test-runner` reads after a suite run in the background, and "
        "the increment's mutants file `run/supervisor/<id>-mutants.json` with its runs' output files "
        "`run/agent/<id>-checkpoint.out` (step 4) and `run/agent/<id>-mutation.out` (step 7); "
        "and, while a gate is open, its files under `run/review/` (the round's `REVIEW-<ID>-r<N>.diff`, "
        "`ASSUMPTIONS-<ID>-r<N>.md` and `REVIEW-<ID>-r<N>.err`, whose first line is the launch time "
        "`pr-activity-check.py` needs, and the increment's `SCOPE-<ID>.md`), whole, with the review guard's count of rounds opened for the increment, which "
        "names the next snapshot `<ID>-r<N>` (step 8) and says whether the round is above the ceiling (step 7, \"The "
        "review ceiling\");",
        "while step 9 runs, its position: `run/supervisor/refactor-<stage>-candidates.md` (the sub-file's \"Keeping the "
        "pass's position\"), the detector's report under `docs/refactor/<stage>`, each `handoff/REFAC-<nnn>.md` brief "
        "with its report, the commits on `refactor/<stage>`, and `docs/HARDENING.md`'s section for the stage.",
    ],
}

KEYS = ["run-parameters", "configuration", "delegation-loop"]


@pytest.mark.parametrize("key", KEYS)
def test_r004_the_module_opens_with_its_compaction_survival_list(key):
    """R-004: the module's first section, straight after its heading, is the compaction-survival list, and the list is
    exactly what a resumed session in that phase reads before its next action."""
    text = module(key)
    assert headings(text) == STRUCTURE[key], headings(text)
    lines = text.split("\n")
    assert lines[1] == "" and lines[2] == "### What must survive a compaction", lines[:3]
    body = section(text, "What must survive a compaction", 3).strip().split("\n")
    assert body[0] == INTRO[key]
    assert all(l.startswith("- ") for l in body[1:] if l), body
    assert [l[2:] for l in body[1:] if l] == SURVIVAL[key]


@pytest.mark.parametrize("key", KEYS)
def test_r006_the_module_declares_exactly_its_registry_points_in_the_registrys_order(key):
    """R-006 and the registry's "How a phase module declares its points": a `## Extension points` section, one line
    per point giving its key, exactly the points the registry names this module as declaring, in the table's order."""
    body = section(module(key), "Extension points", 2).strip().split("\n")
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
    assert "may set" not in "\n".join(body)


POINTS = {
    "run-parameters.parameters": "parameters a conditional workflow adds to the five above, each asked as a question of "
                                 "its own in the same form with its default named first, and written as a line of its "
                                 "own in `docs/RUN_PARAMETERS.md`; made once for the whole project.",
    "configuration.items": "configuration items, tools and checks a conditional workflow adds to those above, each "
                           "worked as they are: written by **cursor-configurator** on your instruction, each tool's "
                           "pinned version recorded in `docs/INVENTORY.md` (Resources), and committed with the "
                           "configuration's checkpoint; made once for the whole project.",
    "delegation-loop.inspect-checks": "checks and reviews a conditional workflow adds to the inspect step, on every "
                                      "change of the part the loop checks (an increment, a fix, a refactoring "
                                      "candidate, or the refactoring branch's gate pass in step 9), each placed at the "
                                      "step that runs it: beside the scope and design-conformance checks or among the "
                                      "reviewer passes (step 4), or with the secret scan and the dependency admission "
                                      "(steps 5 and 5b); a finding is handled as that step handles its own: a blocking "
                                      "one re-delegates (step 7), a builder's objection goes to \"Objections — bottom-up "
                                      "escalation\", and a consequence the owner bears goes to the owner (rule 56).",
    "delegation-loop.test-checks": "tests and checks run with the tests of every change of the part the loop checks "
                                   "(step 4: the change's tests, the suite, the new tests against the checkpoint), such "
                                   "as the observability tests of a part with screens or the benchmark floor (step 6); a "
                                   "failing one is a correctness-class block, re-delegated like any defect (step 7).",
    "delegation-loop.brief-constraints": "constraints every brief for the part carries beside spec-packager's template, "
                                         "such as a frozen rule the builder must follow, written into the brief at step "
                                         "2 and checked by `diff-reviewer` with the rest of the brief.",
}


def registry_applies():
    text = read(REGISTRY)
    table = text.split("\n## Extension points\n", 1)[1].split("\n## ", 1)[0]
    rows = [l for l in table.split("\n") if l.startswith("|")]
    header = [c.strip() for c in rows[0].strip("|").split("|")]
    return {cells["Key"]: cells["Applies"] for cells in
            (dict(zip(header, [c.strip() for c in row.strip("|").split("|")])) for row in rows[2:])}


@pytest.mark.parametrize("key", KEYS)
def test_r006_each_point_says_where_its_additions_are_made(key):
    """R-006 and the registry's "How a phase module declares its points": each point's line places the additions a
    conditional workflow makes there, and says what the registry's Applies cell states: a point that applies per
    project is made once for the whole project; one that applies per part names the part (Review A, round 1, S5)."""
    applies = registry_applies()
    body = section(module(key), "Extension points", 2).strip().split("\n")
    for line in [l for l in body if l.startswith("- ")]:
        k = re.match(r"^- `([a-z0-9.-]+)` — ", line).group(1)
        assert line == "- `%s` — %s" % (k, POINTS[k]), line
        if applies[k] == "project":
            assert line.endswith("; made once for the whole project."), (k, line)
        else:
            assert applies[k] == "part" and re.search(r"\b(of|for) the part\b", line), (k, applies[k], line)
            assert "whole project" not in line, line


def test_r006_the_inspect_point_spans_every_step_the_registry_gives_it():
    """R-006 and the registry's paragraph on the inspect and test steps (extension-points.md): the inspect step is
    every check or review that is not the running of the tests (the reviewer passes, the secret scan and the dependency
    admission among them), on every change the loop checks, and an addition is placed at the step that runs it; its
    findings keep the routes their step gives them (Review A, round 1, B2, convergent with the security audit)."""
    line = flat(section(module("delegation-loop"), "Extension points", 2)).split("- `delegation-loop.inspect-checks`")[1]
    line = line.split("- `delegation-loop.test-checks`")[0]
    for part in ("among the reviewer passes (step 4)", "with the secret scan and the dependency admission (steps 5 and 5b)",
                 "a refactoring candidate, or the refactoring branch's gate pass in step 9",
                 "each placed at the step that runs it", "a builder's objection goes to \"Objections — bottom-up escalation\"",
                 "a consequence the owner bears goes to the owner (rule 56)"):
        assert part in line, part
    assert "before the first reviewer" not in line and "never to the owner" not in line
    registry = flat(read(REGISTRY))
    assert ("the reviewer passes (such as the design auditor the trait *has screens* carries), the secret scan and the "
            "dependency admission") in registry
    assert "An addition at either point is placed in the delegation loop's text at the step that runs it." in registry


def pointer_lines(text):
    return [l for l in text.split("\n") if l.startswith("Sub-files: ") or l.startswith("Variants: ")]


def test_r032_the_delegation_loop_names_its_sub_files_on_its_pointer_line():
    """R-032: the delegation-loop module names its two sub-files, step 7's (TASK-030) and step 9's (TASK-013), on one
    `Sub-files:` line, in the grammar session-start.py reads (a line at column 0, paths relative to workflow/phases/
    separated by `; `), in its procedure; every file under workflow/phases/delegation-loop/ is named there, so no
    sub-file goes unread."""
    text = module("delegation-loop")
    line = "Sub-files: " + "; ".join(SUBS)
    assert pointer_lines(text) == [line], pointer_lines(text)
    proc = section(text, "The procedure", 3)
    assert "\n" + line + "\n" in proc
    assert flat(proc).strip() == ("Steps 1 to 8 below run for every increment, step 7 in a sub-file of this module; step "
                                  "9, the refactoring and optimization pass at a stage's close, is in another. Each "
                                  "sub-file is read whole with the module wherever the module is read: " + line
                                  + " For each increment, in order:")
    folder = os.path.join(PHASES, "delegation-loop")
    assert sorted(os.listdir(folder)) == sorted(os.path.basename(s) for s in SUBS)


def test_r032_step_7_is_in_its_sub_file_whole_and_nowhere_else():
    """R-032 (TASK-030): the module grew past what its bound allowed with TASK-030's text, so step 7 moved into a
    sub-file, as step 9 did (TASK-013): the sub-file opens with its own heading and a paragraph that says it is part of
    the module and when its step runs, holds step 7 under its heading, then the review ceiling (TASK-034) and the
    mutation run; the module keeps a
    pointer section under the step's number, and no other file under workflow/phases/ holds the step's heading."""
    sub = module(DECIDE)
    assert headings(sub) == [(2, "The decision (Phase 6, step 7)"), (3, "Where this sub-file belongs"), (3, STEP7),
                             (4, "The review ceiling"), (4, "The mutation run")], headings(sub)
    assert flat(section(sub, "Where this sub-file belongs", 3)).strip() == (
        "This file is a sub-file of the delegation-loop module (`delegation-loop.md`, \"The procedure\"), read whole "
        "with it. It holds the loop's step 7, which runs for every increment after step 6 and before step 8, the "
        "merge: the decision on the increment, and the mutation run each pass through the step launches before step "
        "8's snapshot. It stands in a file of its own to keep the module within its size bound.")
    assert flat(section(module("delegation-loop"), "7. Decide — in a sub-file", 3)).strip() == (
        "Step 7, the decision on the increment with the mutation run its last pass launches, stands in the sub-file "
        "`delegation-loop/decide.md` (\"The procedure\" names it), read whole with this module; step 8 follows it.")
    for root, _dirs, files in os.walk(PHASES):
        for f in files:
            rel = os.path.relpath(os.path.join(root, f), PHASES).replace(os.sep, "/")
            if rel != DECIDE:
                assert "### " + STEP7 not in read(os.path.join(root, f)).split("\n"), rel


# sha256 of step 7 as the sub-file holds it after TASK-034 (from its heading to the line before "The review ceiling",
# LF, trailing whitespace stripped; 7,641 characters). TASK-030 moved the step verbatim from the module (then 6,967
# characters at origin/main 02f0ab5, sha256 70a1aacaca66592b...), its mutation run added after it under a heading of its own;
# TASK-034 reworded its Iterate and Re-delegate bullets (a new numbered brief), the root-cause-first paragraph's fix
# brief (`<ID>-r<N>` inside a gate, BUG after a merge) and the brake's by-class bullet (the five classes, the class
# the defect, for the increment or the stage), and added "The review ceiling" between the step and the mutation run (R-042)
STEP7_SHA256 = "dcf588e45b134ec855bfc9da83ab356d4ab82b15f294426c849e35c01f9ae261"


def test_r032_step_7_is_verbatim():
    """R-032 (TASK-030, TASK-034): the sub-file's step 7, up to its review ceiling, is the step as TASK-030 moved it
    and TASK-034 reworded it, character for character."""
    import hashlib
    sub = module(DECIDE)
    step = sub[sub.index("### " + STEP7):sub.index("#### The review ceiling")].rstrip()
    assert len(step) == 7641 and hashlib.sha256(step.encode("utf-8")).hexdigest() == STEP7_SHA256, len(step)


def test_r032_step_9_is_in_the_sub_file_whole_and_nowhere_else():
    """R-032: the sub-file opens with its own heading and a paragraph that says it is part of the module and when its
    step runs; it holds step 9 under its heading as the core had it, and no other file under workflow/phases/ holds
    the step's heading or its passages."""
    sub = module(SUB)
    assert headings(sub) == [(2, "The refactoring pass (Phase 6, step 9)"), (3, "Where this sub-file belongs"),
                             (3, STEP9), (3, "Keeping the pass's position")], headings(sub)
    assert flat(section(sub, "Where this sub-file belongs", 3)).strip() == (
        "This file is a sub-file of the delegation-loop module (`delegation-loop.md`, \"The procedure\"), read whole "
        "with it. It holds the loop's step 9, which runs at a stage's close, before the stage's reflection point "
        "(`reflection.md`), when `docs/RUN_PARAMETERS.md` turns the refactoring pass on for the stage. When the scout "
        "returns its lists (item 2), write them down as \"Keeping the pass's position\", after the step, says.")
    fs = flat(sub)
    passages = (
        "When the last increment of a stage has merged and `docs/RUN_PARAMETERS.md` says **Refactoring pass: on** for "
        "that stage, run one refactoring pass **before** the stage's reflection point.",
        "**Scout.** Delegate to **refactor-scout** with the stage base commit",
        "**Purity check — deterministic, before any reviewer:**",
        "python ~/.claude/cursor-bridge/refactor-check.py main --max-lines 400",
        "**Beyond budget** candidates go to `docs/HARDENING.md` under the stage name",
        "At **project end** no pass of its own runs: the last stage's close runs this pass, as every stage's close "
        "does under the refactoring parameter, and project end adds none, since a merge after project end's strict "
        "sync check would void that check.",
    )
    for p in passages:
        assert p in fs, p
    for root, _dirs, files in os.walk(PHASES):
        for f in files:
            rel = os.path.relpath(os.path.join(root, f), PHASES).replace(os.sep, "/")
            if rel == SUB:
                continue
            text = read(os.path.join(root, f))
            assert "### " + STEP9 not in text.split("\n"), rel
            for p in passages:
                assert p not in flat(text), (rel, p)


# sha256 of step 9 as TASK-035 leaves it (from its heading to its last line, LF, trailing whitespace stripped; 5,695
# characters): the project-end sentence reworded under its `reword` and `new` entries; before it the step as the
# delegation-loop module held it at origin/main 5bed396 (5,542 characters), moved verbatim. trace-check, which would
# see a change, has no CI step (INVENTORY Decisions), so CI holds the step's text here; a later reword updates this
# with its record
STEP9_SHA256 = "01eeaa1d78aff824728143fe4a6a2976fac2c400c05f13997ef3578d87e3e355"


def test_r032_step_9_is_verbatim():
    """R-032 (Review A, round 1, C1): the sub-file's step 9 is the module's step 9 as it was before the split, character
    for character, but the project-end sentence TASK-035 rewords (R-003; INVENTORY, Decisions: project end adds no
    pass of its own)."""
    import hashlib
    sub = module(SUB)
    step = sub[sub.index("### " + STEP9):sub.index("### Keeping the pass's position")].rstrip()
    assert len(step) == 5695 and hashlib.sha256(step.encode("utf-8")).hexdigest() == STEP9_SHA256, len(step)


def test_the_refactoring_passs_position_is_written_down():
    """R-004 (Review A, round 1, S3): the delegation loop's survival list names the pass's candidates file, so the
    sub-file writes the scout's lists there as they arrive and marks each candidate as the pass reaches it."""
    s = flat(section(module(SUB), "Keeping the pass's position", 3)).strip()
    assert s == ("Write the scout's two ranked lists to `run/supervisor/refactor-<stage>-candidates.md` as it returns "
                 "them, and mark each candidate there as committed, dropped or beyond budget as the pass reaches it; name "
                 "the file on the status file's `Working files:` line (rule 54). The lists are in the scout's reply "
                 "alone, which a compaction does not keep, and the detector's report, the briefs and the branch's "
                 "commits do not say which candidates remain.")


def test_the_run_parameters_are_written_as_each_answer_is_given():
    """R-004: the survival list names docs/RUN_PARAMETERS.md as written so far, so the procedure writes each answer as
    it arrives (as intake writes its notes, TASK-011); a parameter that does not apply is written n/a so a resume does
    not ask it (Review A, round 1, C2); and, as intake's and the interface phase's notes, no key and no computer path
    is written there (the security audit, round 1, rules 53 and 54)."""
    s = flat(section(module("run-parameters"), "Writing the answers down", 3))
    assert s.strip() == ("Write each answer into `docs/RUN_PARAMETERS.md` as the owner gives it, in the form above, the "
                         "`Set:` line with the first: a compaction between two questions then loses no answer, and a "
                         "resume asks only the parameters the file does not yet hold. A parameter that does not apply to "
                         "the project, such as installer verification for software that installs nothing, is written as "
                         "`n/a` when it is passed over, so a resume does not ask it. A parameter a conditional workflow "
                         "adds at `run-parameters.parameters` is asked and written the same way. A parameter is a "
                         "setting, never a key: a key, token or password the owner pastes in an answer is never written "
                         "to the file, rule 53 applies to it, and no path on this computer is written there either "
                         "(rule 54).")


def test_the_configurations_position_is_kept_on_next():
    """R-004: the survival list names the status file's Next: line, so the procedure keeps it while the phase runs; not
    In flight:, whose grammar the core's template fixes for a running increment or agent (Review A, round 1, S4); each
    item by its name only (the security audit, round 1, rules 53 and 54); and the final record named."""
    s = flat(section(module("configuration"), "Keeping the position", 3))
    assert s.strip() == ("While the phase runs, keep the status file's `Next:` line naming the items configured so far "
                         "and the next one, rewritten as each is finished, so that a resume after a compaction neither "
                         "redoes an item nor skips one. It names each item by its name only, never a key's value or a "
                         "path on this computer (rules 53 and 54). Once the configuration's checkpoint is committed, the "
                         "line names the first increment, and what was configured stands in the status file, as \"Commit "
                         "the configuration as its own checkpoint\" above asks, with each tool's pinned version in "
                         "`docs/INVENTORY.md` (Resources).")
    assert "Commit the configuration as its own checkpoint before `TASK-001`, and record in" in module("configuration")
    assert "`In flight:`" not in module("configuration")


@pytest.mark.parametrize("rel", ["run-parameters.md", "configuration.md", "delegation-loop.md", DECIDE, SUB])
def test_r032_the_module_and_its_sub_file_are_read_whole(rel):
    """R-032: each enriched module and the sub-file stay within the bound a module is read whole by."""
    text = module(rel)
    assert text.count("\n") <= 1500 and len(text) <= 60000, (rel, text.count("\n"), len(text))


def test_r005_the_hook_names_the_delegation_loop_and_its_sub_file(tmp_path):
    """R-005 with R-032, the first real Sub-files: line: for `Phase: building` the installed hook names
    delegation-loop.md, then its sub-file, then the reflection and project-end modules."""
    home = tmp_path / "home"
    shutil.copytree(os.path.join(BRIDGE, "commands"), str(home / ".claude" / "commands"))
    shutil.copytree(CB, str(home / ".claude" / "cursor-bridge"), ignore=shutil.ignore_patterns("__pycache__"))
    ws = tmp_path / "proj" / "Workspace"
    (ws / "docs").mkdir(parents=True)
    (ws / "docs" / "PROJECT_STATUS.md").write_text(
        "# Project Status\nPhase: building\nWorkflows: not yet classified\nAwaiting user on: nothing\n", encoding="utf-8")
    env = dict(os.environ, HOME=str(home), USERPROFILE=str(home))
    data = {"cwd": str(ws), "hook_event_name": "SessionStart", "source": "compact"}
    p = subprocess.run([sys.executable, HOOK, "--part", "pointers"], input=json.dumps(data), capture_output=True,
                       text=True, encoding="utf-8", env=env)
    assert p.returncode == 0 and p.stderr == "", p.stderr
    w = "~/.claude/cursor-bridge/workflow/phases/"
    named = [re.match(r"  - (\S+)", l).group(1) for l in p.stdout.split("\n") if l.startswith("  - " + w)]
    assert named == [w + "delegation-loop.md", w + DECIDE, w + SUB, w + "reflection.md", w + "project-end.md"], p.stdout


def test_the_core_names_the_delegation_loops_sub_file():
    """The pointer sweep for the split: the core's module table names the delegation loop's sub-file folder, and the
    sentence under the table says where a split module's step keeps its heading."""
    core = flat(read(CORE))
    assert ("| The delegation loop (Phase 6) | `~/.claude/cursor-bridge/workflow/phases/delegation-loop.md` and its "
            "sub-files under `~/.claude/cursor-bridge/workflow/phases/delegation-loop/` |") in core
    assert ("A step a module keeps in a sub-file keeps its heading there: the delegation loop's step 7 is in "
            "`delegation-loop/decide.md` and its step 9 in `delegation-loop/refactoring-pass.md`.") in core
