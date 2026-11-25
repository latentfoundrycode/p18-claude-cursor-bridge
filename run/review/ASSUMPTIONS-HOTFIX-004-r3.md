# Assumptions: HOTFIX-004 r3

The branch's commit messages carry no `Assumptions:` section. The builders' reports list:

- Round 1 (`handoff/HOTFIX-004-r1-report.md`, its `Assumed, not verified` section): read it there; its fourth item (what a waiter prints when it moves from the folder wait to the slot wait) stays as built, a Known limit.
- Round 2: `Assumed, not verified: none`. Review A noted one it relied on: `os.fstat(fd).st_nlink` reports the true link count on Windows (settled by `test_hotfix24a_r2_a_linked_lock_file_is_refused` passing on Windows).
- Round 3: `Assumed, not verified: none`.
- Round 4: `Assumed, not verified: none`. Review A noted one: on Windows, `os.open(O_CREAT|O_EXCL)` on a folder at the pid file's name raises `PermissionError` rather than `FileExistsError`; both answers meet requirement 37, and the test accepts both.
- The CI fix: the status file's `Bridge version:` and `project.json`'s `state.bridge` name the stamped release ahead of the owner's install, as the program release's stamp did (its Calibrated line records it).

These are extra places to look, never the review's scope.
