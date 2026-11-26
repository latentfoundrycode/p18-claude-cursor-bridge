# SCOPE: TASK-087c (Review B, round 2)

Increment: TASK-087c, "Stage I1's texts: the reviewers' one sentence, the report's outputs, an exhausted pool (R-107, R-108)". Round 1 (your own) approved the branch at f141b1d. Since then one records commit, read in run/review/DELTA-TASK-087c-r2.diff (git diff f141b1d HEAD -- docs); the whole branch against origin/main is run/review/REVIEW-TASK-087c-r2.diff.

## Why a second round
CI's first run on pull request #212 failed one test, tests/test_program_own_records.py::test_r101_inventory_check_passes_over_this_repository_s_records: STATUS TOO LONG: docs/PROJECT_STATUS.md is 28 lines / 12778 chars (cap 120 / 12000). The records commit's added sentences crossed the cap.

## The delta
- docs/PROJECT_STATUS.md: the Deviations accepted line keeps TASK-087c's told deviation; the program release's told deviations move out, the line pointing to docs/archive/STATUS_HISTORY.md.
- docs/archive/STATUS_HISTORY.md: one section appended, "Moved 2026-11-26 (TASK-087c): the program release's deviations told to the owner (rule 58)", holding the moved text unchanged.
- docs/HARDENING.md: one bullet in TASK-087c's section on the failure, its cause and the lead.

## What to check
That the moved text is moved whole and unchanged, nothing else of the status file changed, the status file now passes python bridge/cursor-bridge/inventory-check.py (status: 28 lines / 11101 chars, RESULT: OK), and the HARDENING bullet says what happened. Records only; the five blocking classes and records findings.

## Proofs
inventory-check.py RESULT: OK; tests/test_program_own_records.py with the status tests and this pull request's variables: 293 passed.

## Round
Review B's second round for this increment (the guard's count 1).
