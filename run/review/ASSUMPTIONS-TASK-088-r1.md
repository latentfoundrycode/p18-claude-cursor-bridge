# TASK-088 - the branch's assumption lists (from its commit messages)

Extra places to look, never the review's scope.

## TASK-088: one reader for a brief's Satisfies ids (R-110)
- r1: none matched case-insensitively -> test (test_task088_r2_none_is_matched_as_a_word[upper-case])
- r1: a bullet without an R-id beneath the line does not end the bullets -> accepted (the design reads the bullet lines directly beneath; such a bullet adds no id)
- r2: none listed -> test (the round-3 tests; both reviewers found unlisted readings, recorded in docs/HARDENING.md)
- r3: none listed -> accepted (the reviewers' one item, the underscore-emphasised none, is in docs/HARDENING.md)
