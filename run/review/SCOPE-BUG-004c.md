# SCOPE — BUG-004, round 3

BUG-004 is the supervisor's own branch answering stage B2's stage review, round 3: tests, fixtures, two sentences of bridge/cursor-bridge/workflow/open-list.md and the records; no program changed (MANIFEST.json regenerated for the open-list.md edit, VERSION unchanged). Its round-1 scope, with every test and the paragraph it enforces, is in git: `git show 4786f3a:run/review/SCOPE-BUG-004.md` (one correction: the no-carriage-return assertions read the text with newline translation off, `newline=""`, not the bytes).

## Rounds so far
- Round 1 (head 4786f3a): Review A APPROVE 0/1/3, Review B APPROVE 0/2/0; converged on docs/HARDENING.md's backslash sentence. Round 2 (0fdf601) fixed it and took the considers.
- Round 2 (head eb811e3): Review A APPROVE 0/1/1, Review B APPROVE 0/1/0; converged on docs/HARDENING.md's new reserved-values lead (it said a head equal to `not yet classified` is skipped; only a whole rest reading exactly that is).

## Round 3 (this review): run/review/DELTA-BUG-004c.diff (eb811e3 to HEAD, run/review/ excluded); the whole branch is run/review/REVIEW-BUG-004c.diff
- docs/HARDENING.md, the reserved-values bullet: one value is reserved by position, a trait Name `none` (check_traits); `not yet classified` reserves no name, since only a whole rest reading exactly that is skipped and a classified line carries `; traits: ` (Review A and Review B, converged).
- tests/test_workflows_line_check.py::test_r015_inventory_no_status_file_no_check asserts inventory-check's whole output (four lines: the status note, the resources note for a folder that is not a git repository, the absent inventory, RESULT), so nothing about the line can be said in any words; enforces handoff/TASK-008.md Requirement 4 (Review A's round-2 consider: a note worded "Workflow line" or "status line" survived the keyword check).
- run/supervisor/mutate_workflows_line.py (local, the supervisor's): a mutant adding the note "status line: not judged"; 40 of 40 killed.
- Round 2's review files removed.

## Out of scope
Every program under bridge/cursor-bridge/; CI; leads routed in HARDENING to later increments.
