# Assumptions, TASK-070 round 2

The builder's `Assumed, not verified` list (handoff/TASK-070-r2-report.md) and the supervisor's, each with its disposition. Extra places to look, never the review's scope. Round 1's list (ASSUMPTIONS-TASK-070-r1.md, in the round 1 review commit) stands.

## Round 2
- The second copy_tracked puts back the bytes mutant_keys read, although run_resolution_check ran between -> accepted, checked by Review A in code: the program writes nothing into the copy in that window (its plugin, results and ini files go to the scratch subfolder; the collect-only run has PYTHONDONTWRITEBYTECODE=1); only a project's import-time code writing a tracked file could break it (HARDENING lead 8).

## The supervisor's
- The narrowed assertion of test_r090_r2_baseline_that_rewrites_the_mutated_file_leaves_it_pristine keeps the case's claim -> accepted, Review A: exit 0, the killed line, the killed cache line, the cached second run and the untouched Workspace file carry it; the rebuild removed (H6) still fails the case.
- A rebuild after a list that only timed out is harmless on an ordinary layout -> accepted for the tested holder case (test_r041_pipe_holder_outside_tree_cwd_in_copy_times_out passes with the rebuild); a holder inside an untracked directory is HARDENING lead 7.
