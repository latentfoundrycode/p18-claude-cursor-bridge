# ASSUMPTIONS - BUG-036-r1

From the `Assumptions:` sections of the branch's commit messages, whole, by commit (extra places to look, never the review's scope).

## 518e600 BUG-036: the review guard seeds no Review B round from a builder round release B's launcher logged

- a lettered report of a logged round is that round's -> test (tests/test_bug036.py, the lettered-report test)
- an earlier launcher's builder row (no brief, no round) never matches -> test (tests/test_bug036.py, the earlier launcher's rows test)
- a missing log counts every report -> test (test_task032_guard_r14_five_report_files_outrank_two_snapshots, no log)

