# The builder's assumptions, TASK-050 (from the branch's commit messages)

Extra places to look, never the review's scope.

## 7b45aa1 TASK-050: round 2, round 1's confirmed findings fixed (R-061)

Assumptions:
- CR and CRLF normalized before the line-feed split -> test (the space-crlf linear case; the currency and round-1 CRLF fixtures).
- run_parameters_values removed from the guard's names -> test (test_r061_r2_inventory_check_refuses_through_its_guard_before_reading_the_run_parameters).
- R6 by per-line match with [ \t]* -> test (test_r061_r2_the_fallback_of_a_whitespace_padded_file_takes_linear_time).

## 8c35020 TASK-050: round 1, the run parameters' header read first (R-061)

Assumptions (the builder's): none listed.
