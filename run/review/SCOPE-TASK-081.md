# TASK-081: the program release's stamp, 2026.11.23a (R-102)

Round cause: records - Review A's round 1 rejected the whole-range trace clause neither met nor reported; the fix is records and two CHANGELOG sentences, no program.

## The increment
The supervisor's records, no builder brief. Its brief is the plan entry docs/BUILD_PLAN.md "### TASK-081 — The stamp and the install run sheet (R-102)", its Done when up to "after the merge" (the run sheet, the demonstration and the close follow the merge), and the register row R-102. It follows release B2's stamp (tests/test_release_b2_stamp.py, the 2026.11.11a entry).

## The change, run/review/REVIEW-TASK-081-r1.diff (git diff origin/main..HEAD, the review files excepted)
- The accept commit: bridge/cursor-bridge/VERSION 2026.11.23a; the CHANGELOG entry above 2026.11.12a (What changed by row, Running projects must phase-marked, If rolled back with lines observed by the installed 2026.11.12a programs on a scratch copy at eccc484, Field acceptance, For the maintainer); MANIFEST.json regenerated; project.json's version and state.bridge; R-102 built; tests/test_program_stamp.py (names R-102), 8 failed on the checkpoint, 8 passed on the stamp.
- The records commit: docs/HARDENING.md (stage P4's review, round 1; TASK-081); docs/INVENTORY.md (the documentation-service row's outbound trigger); docs/PROJECT_STATUS.md (Bridge version with the stamp, Change cycle, Next).
- Round 2, after Review A's round 1 (REJECT): the whole-range `trace-check.py --moves --base d211e33` recorded with its three findings and their cause, a deviation on the status file's Deviations line; the CHANGELOG's R-082 item (inline aliases) and If rolled back item 2 (up to the stamp); HARDENING's round note. Review A's round 2 approved.

## Before it
Stage P4's review by both, one round, approved (tag stage-review/P4-1); one stripped whole suite on eccc484, "7413 passed, 49 skipped" (run/agent/STAGE-P4-suite.out). Outputs: run/supervisor/task081_rollback_observe.out, run/supervisor/task081_trace_pinned.out, run/agent/task081-moves-whole.out, run/agent/task081-tests2.out, run/agent/task081-r2-tests.out.

## Threat models
docs/INVENTORY.md, the documentation-service row (its trigger cell changed here) and the bridge's threat model as a whole. The stamp changes no program.

## What to read for
Whether every sentence of the CHANGELOG entry is true of the tree and of 2026.11.12a (what a rollback restores), whether the entry carries every item the plan names, whether tests/test_program_stamp.py holds what it says, and whether the records state their counts truly. Review B, round 1: REJECT on one finding (the R-102 item's clause on release S's rows); one Should fix (R-090), two Considers.

## Round 2
Round cause: records - one sentence of the CHANGELOG entry false of the tree; no program changes.

The commit after "Review files for round TASK-081-r1" (4b95806), whose diff is run/review/REVIEW-TASK-081-r2.diff: the R-102 item now says that where a row above changes one of release S's programs or texts, that row says so, and names them (R-089, R-077 and R-083, R-078 and R-080); the R-090 item names the lists the cache does not serve; the R-087 item says a git before 2.40 refuses the scan (`CANNOT SCAN`); HARDENING records the round; MANIFEST.json regenerated after the last edit; run/review/REVIEW-TASK-081-r1.diff removed. Check each against round 1's findings and that nothing else moved. This is Review B's round 2.
