# SCOPE - BUG-047: the evaluation's pace paragraph counts as the report does, and the timeout tests time out a mutant

The fix of stage P3's review, round 1 (snapshot STAGE-P3-r1, `git diff 618292e origin/main` at 5a00ed7, both reviewers once). No finding asked for a program change, so this is a fix of text and tests alone, the supervisor's (no builder brief), which closes the stage at its merge with no further whole pass (reflection.md, step 7). Pull request #198, branch bug-047 from origin/main 5a00ed7.

## The two findings it fixes
1. Review B, blocking (behaviour against R-089): bridge/commands/evaluate-reports.md's pace paragraph said an increment is an ID with a tracked brief, so one built without a brief is not counted, and that a project tracking only builder reports counts none; bridge/cursor-bridge/pace-report.py counts a guard rounds record, a tagged pass line and `PR-<n>` (TASK-069). The paragraph's increment sentence now reads the counted names as the program's module docstring states them, and its last sentence the window's one `Round causes` line and the per-week passes lines. tests/test_loop_text_pace.py (`test_bug031_evaluate_reports_says_what_the_pace_report_counts`) pins both sentences, the old ones' absence and four clauses of the docstring.
2. Review A (tests part 1), blocking (a weakened older claim): since TASK-070's baseline, tests/test_mutation_run.py's timeout cases hung on the unmutated code and ended in the baseline, so the mutant loop's own timeout path was untested. `test_r041_timeout_error_continues`, `test_r041_grandchild_holding_pipes_times_out` and `test_r041_pytest_survives_kill_stops_run` now hang only on the mutated code (the mutant flips `HANG`, `HOLD`, `LOOP` to True) and assert the mutant's own `(ran)` timeout; the pipe holder outside the tree keeps the unmutated hang, now asserted `(not run)`; the new `test_r041_baseline_pytest_survives_kill_stops_run` keeps the baseline pytest that outlives its kill (exit 3, `(not run)`, no mutant run, the stderr line).

## Rounds before this one
Review A round 1 (the fix's first commit) REJECTED: the paragraph's last sentence said each week prints a cause line and a passes line by name, kind and round (blocking, behaviour); the baseline-alive branch was left untested and the pipe holder's `(not run)` unpinned (should fix). Round 2 (the second commit) fixed all three and reworded the increment sentence for PR-<n>; Review A round 2 APPROVED. This is the guard's Review B round 1.

## The mutants (run/supervisor/BUG-047-mutants.json and BUG-047-r2-mutants.json, the supervisor's; not in the diff)
m1 the pytest-still-alive mutant read as killed; m2 a timed-out mutant read as killed; m3 the baseline-alive branch not stopping the run; m4 the baseline-timed mutant tagged as cached. Round 1's run (m1, m2): 2 killed of 2. Round 2's run (m1 to m4) on the final code: 4 killed of 4.

## Expected bookkeeping and records in the diff
bridge/cursor-bridge/MANIFEST.json (the generated stamp and the command's hash only); docs/TRACE_MOVES.md (one entry excusing the rewritten passage; trace --moves OK, 1 excused; pinned OK, 0 dropped); records as at this pull request's merge (ISS-009): docs/HARDENING.md (the section on stage P3's review and BUG-047, every finding not fixed recorded there), docs/PROJECT_STATUS.md; run/review/ (this round's files).

## What to check
- Every clause of the paragraph true to pace-report.py's docstring and code (`_pace_names`, `_format_cause_line`, the pass lines), nothing it states that the program does not do.
- The timeout tests: the baseline passes where the claim is the mutant's, the assertions match mutation-run.py's real output lines, and the baseline's own timeout and pytest-outlives-kill paths stay covered.
- No test, assertion or CI step weakened; the tests check what their docstrings say.
- The HARDENING section true to the review's findings; the records agree with each other and with the change; no key and no computer path or user name in a tracked file (rule 54).

The considers and notes of the stage review are recorded in HARDENING, not fixed; they are later work, not this fix's defect. R-093 and R-094's status, TASK-077's HARDENING lines and the INVENTORY row are the stage close's records, after this merge.
