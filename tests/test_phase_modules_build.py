"""TASK-013: the run-parameters, configuration and delegation-loop modules enriched (R-004, R-006, R-032).

enforces: docs/REQUIREMENTS.md R-004 (each phase module opens with the short list of what must survive a compaction),
R-006 (each phase module declares the points the registry names it as declaring), R-032 (each module read whole: the
delegation-loop module, at 94% of the bound's characters before this increment, is split, its step 9 in a sub-file under
workflow/phases/delegation-loop/ that the module's own `Sub-files:` line names and the session-start hook follows);
docs/BUILD_PLAN.md TASK-013's Done when, and the pointer sweep for the split (the core's module table)."""
import os

import pytest

from phase_modules import (read, module, flat, headings, section, assert_declares_registry_points,
                           assert_points_placed, hook_named)

HERE = os.path.dirname(os.path.abspath(__file__))
BRIDGE = os.path.abspath(os.path.join(HERE, os.pardir, "bridge"))
CB = os.path.join(BRIDGE, "cursor-bridge")
PHASES = os.path.join(CB, "workflow", "phases")
REGISTRY = os.path.join(CB, "workflow", "extension-points.md")
CORE = os.path.join(BRIDGE, "commands", "supervisor.md")

SUB = "delegation-loop/refactoring-pass.md"
STEP9 = "9. Refactoring and optimization pass (at stage close)"
DECIDE = "delegation-loop/decide.md"
STEP7 = "7. Decide (accept the increment)"
MERGE = "delegation-loop/merge.md"
SUBS = [DECIDE, SUB, MERGE]


KEYS = ["run-parameters", "configuration", "delegation-loop"]


@pytest.mark.parametrize("key", KEYS)
def test_r006_the_module_declares_exactly_its_registry_points_in_the_registrys_order(key):
    """R-006 and the registry's "How a phase module declares its points": a `## Extension points` section, one line
    per point giving its key, exactly the points the registry names this module as declaring, in the table's order."""
    assert_declares_registry_points(key)


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


@pytest.mark.parametrize("key", KEYS)
def test_r006_each_point_says_where_its_additions_are_made(key):
    """R-006 and the registry's "How a phase module declares its points": each point's line places the additions a
    conditional workflow makes there, and says what the registry's Applies cell states: a point that applies per
    project is made once for the whole project; one that applies per part names the part (Review A, round 1, S5)."""
    assert_points_placed(key, POINTS)


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
    folder = os.path.join(PHASES, "delegation-loop")
    assert sorted(os.listdir(folder)) == sorted(os.path.basename(s) for s in SUBS)


def test_r032_step_7_is_in_its_sub_file_whole_and_nowhere_else():
    """R-032 (TASK-030): step 7 stands in a sub-file, as step 9 does (TASK-013): the sub-file opens with its own
    heading, holds step 7 under its heading, then the review ceiling (TASK-034) and the mutation run, and no other file
    under workflow/phases/ holds the step's heading. The two paragraphs' own words are no longer held (release S)."""
    sub = module(DECIDE)
    assert headings(sub) == [(2, "The decision (Phase 6, step 7)"), (3, "Where this sub-file belongs"), (3, STEP7),
                             (4, "The review ceiling"), (4, "The mutation run")], headings(sub)
    for root, _dirs, files in os.walk(PHASES):
        for f in files:
            rel = os.path.relpath(os.path.join(root, f), PHASES).replace(os.sep, "/")
            if rel != DECIDE:
                assert "### " + STEP7 not in read(os.path.join(root, f)).split("\n"), rel


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


def test_r005_the_hook_names_the_delegation_loop_and_its_sub_file(tmp_path):
    """R-005 with R-032, the first real Sub-files: line: for `Phase: building` the installed hook names
    delegation-loop.md, then its sub-file, then the reflection and project-end modules."""
    w = "~/.claude/cursor-bridge/workflow/phases/"
    named = hook_named(tmp_path, "building")
    assert named == [w + "delegation-loop.md", w + DECIDE, w + SUB, w + MERGE, w + "reflection.md",
                     w + "project-end.md"], named


def test_the_core_names_the_delegation_loops_sub_file():
    """The pointer sweep for the split: the core's module table names the delegation loop's sub-file folder, and the
    sentence under the table says where a split module's step keeps its heading."""
    core = flat(read(CORE))
    assert ("| The delegation loop (Phase 6) | `~/.claude/cursor-bridge/workflow/phases/delegation-loop.md` and its "
            "sub-files under `~/.claude/cursor-bridge/workflow/phases/delegation-loop/` |") in core
    assert ("A step a module keeps in a sub-file keeps its heading there: the delegation loop's step 7 is in "
            "`delegation-loop/decide.md`, its step 8 in `delegation-loop/merge.md` and its step 9 in "
            "`delegation-loop/refactoring-pass.md`.") in core
