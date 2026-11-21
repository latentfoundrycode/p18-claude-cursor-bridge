# SCOPE for TASK-070 (Review B, round 3, the review ceiling's round)

Round cause: defect

## What changed since round 2
Review B round 2 rejected (data integrity): round 2's rebuild of the mutants' copy over itself could not undo every change a baseline test makes; a tracked file a baseline test replaced with a folder got the original copied inside the folder. The commits since: "TASK-070 r3: Review B's round 2 finding as tests" (two supervisor cases test_r090_r3_*, a test replacing its own file with a folder and a test adding a conftest that skips every test, and one Windows assertion of tests/test_mutation_run.py::test_r041_pipe_holder_outside_tree_cwd_in_copy_times_out moved from work_sub/tree to work_sub/base, where the timed-out baseline's holder now keeps its working folder; red on round 2's code: 3 failed); "TASK-070 r3: the brief" (handoff/TASK-070-r3.md); "TASK-070 r3: the builder's work, accepted" (mutation-run.py:1630-1636: the baselines run in a copy of their own at work_sub/base, built by copy_tracked as the mutants' copy is, only when a list runs, left for the finally; round 2's rebuild removed; MANIFEST regenerated; after Review A the supervisor added a base/.env assertion to the moved test and a case test_r090_r3_baseline_copy_holds_env_and_untracked_entries; HARDENING round 3 and leads 10 to 12). Review A round 3: APPROVE. The three mutation-run test files stripped: 178 passed, 2 skipped; the two changed tests: 3 passed. This is the review guard's third round: only the five blocking classes send work back (behaviour against the plan or the register, security, data integrity, a defeated safety mechanism, a failing test). The leads recorded under TASK-070 in docs/HARDENING.md, 1 to 12, are not this diff's defects; lead 8's remainder (the baseline copy is a second read of the Workspace after the keys) and lead 11 (the folder name base under prepend import mode or a module named base) among them.

## Round 2's SCOPE, as it stood

## What changed since round 1
Review B round 1 rejected (data integrity): the baseline ran its tests in the scratch copy the mutants then run on, after the cache keys read the copy and before the mutant loop read a mutated file's original bytes, so a baseline test that rewrites a file of the copy changed what the mutants ran on and what the cache recorded. The commits since: "TASK-070 r2: Review B's finding as tests" (two supervisor cases, test_r090_r2_*, red on round 1's code: m1 not applied, exit 1; m1 survived, exit 1); "TASK-070 r2: the brief" (handoff/TASK-070-r2.md); "TASK-070 r2: the builder's work, accepted" (mutation-run.py:1645-1646, copy_tracked builds the copy again over itself after the baselines when a list ran and the loop runs, never on exit 5 or after a baseline pytest that outlived its kill, never removing the copy folder; MANIFEST regenerated; the supervisor narrowed its own r2 assertion that could never pass, the counts line always reading not applied=0, to the m1 line; HARDENING's round 2 and leads 7 to 9). Round cause: defect. Review A round 2: APPROVE. The acceptance file stripped: 15 passed. Round 2's leads 7 to 9 (a rebuild after a timed-out list that a leftover holder in an untracked directory makes raise, exit 3 through run_main; the rebuild reading the Workspace again rather than the copy the keys read; files a baseline test adds staying) are recorded, not this diff's defects.

## Round 1's SCOPE, as it stood

TASK-070 is the mutation run's ids and its baseline (R-090): mutation-run.py's outcomes record replaces backslashes in a node id's file part only, so a parametrized id holding an escape matches its expect_fail and new_tests entries in both modes; before the mutant loop each distinct tests list of the mutants not served from the cache runs once on the unmutated copy, a failure or an error ending the run with exit 5, no mutant run, the cache untouched. Branch task-070 from main 9499612 (PR #186's merge, TASK-069). One builder round; this is the review guard's first round for TASK-070, below the code gate's ceiling: there is no Blocking class line.

Round cause: unstated

Where the increment ends: bridge/cursor-bridge/mutation-run.py, MANIFEST.json and the command reference (two files) through their generators, the builder's report, the supervisor's acceptance tests (tests/test_program_mutation_baseline.py), the supervisor's rewrite of three existing fixtures (tests/test_mutation_run.py and tests/test_mutation_run_supervisor.py) and the records. The reviews' leads (HARDENING, TASK-070, leads 1 to 6) are recorded, not this diff's defects: overlapping lists print a failing id twice; a failure line for exit 1 with a clean record names no reason; an id kept raw under pytest's escaping opt-out can carry a line break; a redundant condition; no test reaches a baseline pytest exit other than 0 or 1; exit 5 named in step 7 by TASK-078. The INVENTORY order row's section 9a is the owner's decision of 2026-11-21 on a later item, unrelated to the code.

Read the commit messages (git log, the full bodies) for the quoted lines.

## The plan entry, quoted (docs/BUILD_PLAN.md, TASK-070)
Scope: bridge/cursor-bridge/mutation-run.py; bridge/cursor-bridge/MANIFEST.json; docs/cli-reference.json; docs/CLI_REFERENCE.md; tests/test_program_mutation_baseline.py; tests/test_mutation_run.py; tests/test_mutation_run_supervisor.py; docs/BUILDER_NOTES.md; handoff/TASK-070-r<N>-report.md
Satisfies: R-090
Done when: read it whole in docs/BUILD_PLAN.md under the heading TASK-070: the cause reproduced before the brief; the file-part-only replacement in both modes; each distinct tests list of the mutants about to run, the cached left out, once on the unmutated copy under a mutant's limit and environment, a failure or error ending the run with exit 5 and one line per list naming it and its failing ids, no mutant run, the cache untouched; an expect_fail test failing unmutated such a failure; no baseline when every mutant is cached; the three timeout tests read before the order and the limit are fixed, and green; the test file names R-090; the exit list names exit 5; reference and MANIFEST regenerated; no new dependency.

## The supervisor's rulings (handoff/TASK-070.md, R1-R9)
- The replacement on the file part only, before the first ::, for the test id and the collection-error id, in both modes.
- The baseline in the ordinary mode only, after the resolution check and the cache keys; distinct lists compared as lists; the cached mutants' lists left out.
- A failure, an error, a collection error, a pytest exit other than 0 or 1, or a missing record without a timeout: exit 5.
- A list that times out is no failure: its mutants are reported error (timed out) (not run), counted as error, no cache line, exit 3, so the four timeout tests of tests/test_mutation_run.py stay green unedited; a baseline pytest that outlives its kill stops the run.
- Three existing fixtures that failed, errored or waited on unmutated code by design were rewritten by the supervisor before the brief to do so only on mutated code, each test's claim kept.

## The supervisor's tests
- tests/test_program_mutation_baseline.py (names R-090; thirteen cases; commit 4763d95, on the checkpoint stripped "9 failed, 4 passed"): the escaped id in the ordinary mode, in the checkpoint mode failing and passing on old code, with an ASCII control; the baseline's failing list, erroring list, expect_fail failing unmutated, every mutant cached, cached lists left out, --all, a green control, each distinct list run once, two failing lists on their own lines.
- The fixture rewrite (its own commit before the brief): both files stripped on the old code "161 passed, 2 skipped".

## Evidence
- Review A: round 1 APPROVE, no blocking finding
- security audit: round 1 PASS, two advisories (HARDENING leads 2 and 3)
- every test file that runs mutation-run.py, sixteen, stripped: 714 passed, 22 skipped; record tests stripped: 175 passed
- completion-check.py --mode plan OK (89 built, 2 deferred, 14 planned); inventory-check.py OK

## Expected bookkeeping and records in the diff
handoff/TASK-070.md and its report, docs/HARDENING.md, docs/INVENTORY.md, docs/PROJECT_STATUS.md (as at this pull request's merge), and run/review/ (these files).
