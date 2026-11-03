# SCOPE - TASK-045, the stamp of release T (R-056)

Round 1 by the guard's count (no brief, no builder round; the supervisor's text and test). Below the ceiling.

## The increment's Scope and Done when

`docs/BUILD_PLAN.md`, section "TASK-045 - The stamp, the install run sheet and the trial's calibration (R-056)", read it there whole. Scope: bridge/cursor-bridge/VERSION; bridge/cursor-bridge/CHANGELOG.md; bridge/cursor-bridge/MANIFEST.json; tests/test_release_t_stamp.py; docs/REQUIREMENTS.md (R-056's flip and Evidence); project.json; the records in their own commits: docs/PROJECT_STATUS.md, docs/INVENTORY.md. No trace-exceptions.md or calibrate-bridge.md change was needed.

Out of scope: any program file under bridge/; no `.py` file there changes in this diff. The install itself is the owner's, from a run sheet after this merge; stage T2's demonstration, its reflection and project end follow it. Design for later releases is not this diff's defect.

## Also in the diff, on purpose

- docs/HARDENING.md: stage T2's review, round 3 (snapshot STAGE-T2-r3, tag stage-review/T2-3 at 5264fa9), with its leads, the convergent mark on project.json's stage words; BUG-043's closing verdict; TASK-045's section. The stage's review findings are recorded here, as the reflection module's step 7 says.
- docs/DESIGN.md: :11 program changes four; rule 43's wording; R-055's test list, with tests/test_bug039.py and tests/test_bug041.py; R-056's words; the CHANGELOG's program items; the Data model's in-flight remedy, conditioned as the entry is.
- docs/diagrams/INDEX.md: D-003's row gains tests/test_bug041.py, which names D-003.
- docs/INVENTORY.md: the stamp's Features row; OTHER_API_KEY's homes.
- docs/PROJECT_STATUS.md as at PR #133's merge (ISS-009); docs/archive/STATUS_HISTORY.md holds the lines moved from it, word for word, to stay under its cap.
- project.json: version, state.bridge, and state.stage moved (the convergent finding).
- run/review/ files of this round.

## Where the entry departs from the plan's words, recorded in HARDENING

1. If rolled back does not say a by-hand `--strip` falls to the classifier: TASK-041 wrote no `--strip` form, its observed launch running on the heavy-launch rules, which stay. A test holds it.
2. The Done when's in-flight remedy is unconditioned in the plan. The entry and DESIGN condition it, since `verify` puts HEAD, every local branch and tag and the tree back to the snapshot. Review A's first read and the audit's confirming read reproduced the loss.
3. The accept commit carries the status file's `Bridge version:` line, which the stamp test reads; R-056's Requirement cell gained BUG-041's stale hash copy and its rewording.
4. The weekly scan's item is marked *(configuration)*.
5. The entry adds a fifth part, **For the maintainer**, after `rolled_back_note`'s stop; the test holds that every If rolled back item reaches the installer's note.

## The tests and the paragraph each enforces

All in tests/test_release_t_stamp.py, supervisor-written, each against docs/BUILD_PLAN.md TASK-045's Done when (its docstring lists them one by one): version, entry, manifest and project agree; the version's form and order; the parts and the installer's note; What changed by row; Running projects must, phase-marked, its items named; If rolled back as the rollback does it; the six allow and two deny rules; the program items and the three halves; the grammar on the plan's four examples; every row built with Evidence in the grammar; `completion-check.py --mode done`.

**A skip to read, gate-integrity by shape:** `test_r056_the_completion_check_passes_in_done_mode` skips where no `.git` exists, asserting first that `GITHUB_ACTIONS` is not set. The reason: mutation-run.py's copy holds no repository and `completion-check.py` reads `git ls-files`, so the test failed on every mutant at baseline (65 errors, exit 3, on the first run). It runs on CI and in this checkout. Judge whether this narrows anything.

The checkpoint: `run/agent/TASK-045-checkpoint.out`, against 2e35552, exit 0: 7 failing, the done-mode test `not run` there. The other 3 tests are invariants of a stamp that hold on every release and are not listed.

## The mutants

`run/supervisor/TASK-045-mutants.json`, written by `run/supervisor/task045_mutants.py`; both gitignored, read here on purpose. 67 mutants, 67 killed, exit 0 (`run/agent/TASK-045-mutation.out`). No driver of mine beyond the program.

## What the supervisor's reviews said

Review A, three reads: REJECT (B1, data integrity, reproduced), REJECT (the same defect's remainder, convergent with the audit), APPROVE on 8a0f9aa. The security audit: PASS WITH FINDINGS, FAIL (the same remainder), PASS WITH FINDINGS, none of the five. The last words taken after those reads, which neither read: 7a59fd6 (work counted from the snapshot, the held branch, the snapshot file's `git` section, the sibling path) and 0201271 (the skip above). Read those two first. HARDENING's TASK-045 section has the rest and the leads not taken.

## Threat model

docs/INVENTORY.md, Decisions: the row beginning "The strip reaches only what goes through the launcher" and the row on the review guard's threat model. A finding is judged by the five blocking classes on an ordinary layout, a security finding by whether untrusted input can reach it.

## Checks to run with the source tree's program

`python bridge/cursor-bridge/bridge-check.py --sources --quiet`, never the installed one, which reads the installed tree (2026.10.30d). Note the installed bridge is older than this stamp, so an installed program's view of the status file's `Bridge version:` differs on purpose.

## Bookkeeping expected in the diff

run/review/REVIEW-TASK-045-r1.diff, ASSUMPTIONS-TASK-045-r1.md, SCOPE-TASK-045.md (removed before the merge).
