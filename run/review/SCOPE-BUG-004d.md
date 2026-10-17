# SCOPE — BUG-004, round 4

BUG-004 is the supervisor's own branch answering stage B2's stage review, round 3: tests, fixtures, two sentences of bridge/cursor-bridge/workflow/open-list.md and the records; no program changed. Its round-1 scope is in git (`git show 4786f3a:run/review/SCOPE-BUG-004.md`); round 3's at `git show 5789e10:run/review/SCOPE-BUG-004c.md`.

## Rounds so far
- Round 1 (4786f3a): A 0/1/3, B 0/2/0, both APPROVE; converged on HARDENING's backslash sentence.
- Round 2 (eb811e3): A 0/1/1, B 0/1/0, both APPROVE; converged on HARDENING's reserved-values lead.
- Round 3 (5789e10): A 0/1/3, B 0/1/0, both APPROVE; converged on test_r015_inventory_no_status_file_no_check not holding standard error.

## Round 4 (this review): run/review/DELTA-BUG-004d.diff (5789e10 to HEAD, run/review/ excluded); the whole branch is run/review/REVIEW-BUG-004d.diff
- tests/test_workflows_line_check.py::test_r015_inventory_no_status_file_no_check (handoff/TASK-008.md Requirement 4: no status file, nothing printed about the line): asserts an empty standard error (replacing the Traceback check it subsumes) and exit 1, beside the exact standard output it already held (Review A and Review B, converged; the exit code is Review A's consider).
- docs/HARDENING.md, the reserved-values bullet: "whose rest, after any part prefix, reads exactly that" (Review A consider).
- run/supervisor/mutate_workflows_line.py (local): a mutant printing a word about the line to standard error; 41 of 41 killed.
- Not taken: GIT_CEILING_DIRECTORIES for the resources note (Review A consider); tmp_path is outside any repository here and on both CI runners.
- Round 3's review files removed.
