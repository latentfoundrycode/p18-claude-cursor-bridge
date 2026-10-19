# ASSUMPTIONS - FIX-002

From the branch's commit messages (`git log 944e64b..HEAD --format=%B`), sections `Assumptions:`:

Assumptions: none

Assumptions: none (supervisor-written tests; no builder run)

Assumptions: none

Assumptions: none (supervisor-written tests; no builder run)

Places to look all the same: whether the shapes in tests/test_b2_least_confident.py keep what the judges could trip on (line endings, field order, sections, size, non-ASCII text, bullets that start like fields); whether each assertion fails on the defect it names; the item-3 pin on Linux CI (the bridge's own status file read from the checkout); whether the records claim more than the tests show; any computer path or other project's record in a committed file.
