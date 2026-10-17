# ASSUMPTIONS-BUG-002

From the branch's commit messages (`git log origin/main..HEAD --format=%B`):

- (builder, BUG-002 r1) none listed. The reviewers hunt unaided.
- (supervisor) The fixtures, tests and the bridge's own status file use the grammar's exact separators everywhere, so tightening the check changes no other finding (spec-packager's reality check walked every fixture; the full suite agrees).
- (supervisor) The real open list's Written cells are the only `| yes |` cells, so replacing `| yes |` with `| no |` marks every entry unwritten (the same rule as test_workflows_line_check's `_unwritten_copy`).
