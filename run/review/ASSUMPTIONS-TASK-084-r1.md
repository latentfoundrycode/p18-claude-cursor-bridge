# Assumptions of TASK-084's branch (Review B, round 1)

From the Assumptions sections of the branch's commit messages (git log origin/main..HEAD). These are extra places to look, never the review's scope.

From d075d5f (checkpoint before TASK-084-r2), round 1's builder list:
- none listed -> the report's own omission, noted by Review A
- the one-space bullet (unlisted) -> test (the supervisor's added case, failing on round 1)

From 27387f5 (round 2's code):
- round 1, none listed -> the helper's one-space bullet was an unlisted assumption: test (the supervisor's tab cases; fixed in round 2)
- bridge-run.py still calls brief_merge_unit_one_side in round 1's order -> test (the launcher cases green; git diff shows bridge-run.py unchanged in round 2)
- the two-or-more alternative, with no end anchor, counts every line of three or more words -> accepted (match anchors at the start; Review A's 200,000-line comparison found no mismatch)
- MERGE_UNIT_RE.pattern unchanged -> test (test_r105_merge_unit_re_keeps_the_checkpoints_text)
