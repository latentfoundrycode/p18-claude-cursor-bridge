# SCOPE - TASK-023 (PR #85)

TASK-023 — Calibration aware of conditional workflows (text). Author: supervisor (governance text, §15 condition 3); no builder run. Satisfies R-027's text half; the program half is TASK-024's.

## Scope (docs/BUILD_PLAN.md, TASK-023)
bridge/commands/calibrate-bridge.md; bridge/cursor-bridge/MANIFEST.json; tests/test_calibrate_text.py

## Done when (docs/BUILD_PLAN.md, TASK-023, quoted)
calibrate-bridge.md applies a conditional workflow to a running project of that type by phase, reopens no gate, states the applied text takes effect from the next design phase or change cycle, **adds a running project's `Workflows:` line from its recorded §6.3 classification and confirms it with the owner** (the A2 precedent: calibration added `project.json`), and keeps the project's existing `Phase:` value (mapped by the hook's shared table); and calibrate-bridge.md's re-read list names, beside the core, the current phase's modules with their sub-files and variant files as the hook's table gives them, and says the core is read in parts to its end (it is past the Read tool's one-call cap; stage B3's review, round 3, placed here by the pace plan revision); `test_calibrate_text.py` (names R-027) asserts those statements.

## Out of scope
- conformance-check.py's run of workflow-check at calibration (TASK-024).
- Any phase module, the core, the hook, or a conditional workflow's file.

## Tests the supervisor wrote, and the paragraph each enforces
tests/test_calibrate_text.py, every literal taken from the edited file with the tests' own readers (run/supervisor/task023_test.py):
- test_r027_the_core_is_read_in_parts_with_the_phase_modules_and_the_conditional_workflows: step 2's re-read item 1, held whole (the core in parts to its end; the phase's modules with their sub-files and variant files; the conditional workflows).
- test_r027_the_re_read_table_is_the_hooks_table: step 2's table equals bridge/cursor-bridge/session-start.py's PHASE_MODULES, every Phase: value with its modules in order; a module's "and its sub-file" or "and its variant files" stands exactly where the module has a Sub-files: or Variants: line (Review A round 1; one mutant, the building row's "and its sub-file" dropped, killed by run/supervisor/task023_mutant.py).
- test_r027_a_conditional_workflow_is_applied_by_phase_reopening_no_gate: step 4b held whole (by phase, no gate reopened; the Workflows: line from the recorded classification, checked, confirmed with the owner; the Phase: value kept; the text in effect from the next design phase or change cycle).
- test_r027_the_step_stands_between_the_delta_and_the_record: 4b between steps 4 and 5.

Against origin/main's text all four fail (the checkpoint run in ../Worktrees/old-TASK-023, torn down).

## Expected files
- The records: docs/REQUIREMENTS.md (R-027's evidence, its text half; status stays planned until TASK-024), docs/INVENTORY.md (a Features row; a Decisions row for the owner's answer of 2026-10-25 to stage B4's traits question, No), docs/HARDENING.md (stage B4's least-confident item 3 settled by that answer; a Stage B5 section with Review A's two leads for stage B6), docs/PROJECT_STATUS.md (as at this pull request's merge, ISS-009, rebased onto HOTFIX-002's PR #84; the conformance count after that merge corrected to 22 OK / 1 MISSING / 6 NOTE).
- bridge/cursor-bridge/MANIFEST.json and VERSION as make-manifest.py writes them.
- docs/ROSTER.resolved.json, the roster stamp before Review B (bookkeeping).
- run/review/, the review files.

## Round 2 (Review A, round 1: APPROVE, 0 Blocking / 2 Should fix / 4 Consider, all taken)
- Should fix 1: step 4b reads the conditional workflows a newly written Workflows: line names that touch the current phase, before step 4 applies anything.
- Should fix 2: a project past intake is never paused for its classification; a failed check or an unwritten type leaves `not yet classified` and makes the report's single decision line.
- Consider: project-end.md's timing in item 1 and the changing row; the table test checks the pointer-line words; the report's first line orders its claims; the template's Re-read line names the modules and the conditional workflows.
- Two notes became HARDENING leads for stage B6.

## Round 3 (Review A, round 2: APPROVE, 0 Blocking / 1 Should fix, taken)
- Step 4 opens with one sentence sending a project whose status file has no Workflows: line to step 4b first, before anything is sorted; 4b's sentence points back to it (4b stands after step 4 in the file).

## After round 3 (Review A, round 3: APPROVE, 0 Blocking / 0 Should fix / 1 Consider)
- A records commit only: the Consider (no test pins step 4's new opening sentence) is a docs/HARDENING.md lead under "Stage B5", "TASK-023", for the stage-close pass's test-infrastructure lane. No text or test changed after Review A's round-3 read.
