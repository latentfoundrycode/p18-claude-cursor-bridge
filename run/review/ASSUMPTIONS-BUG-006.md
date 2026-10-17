# ASSUMPTIONS — BUG-006

From the branch's commit messages (`git log origin/main..HEAD --format=%B`), section `Assumptions:`:

- none: no builder ran on this branch; the tests, fixtures and registry text are the supervisor's.

Places to look all the same: the expected outputs in FILE_EXACT and STATUS_EXACT were taken from the check's output and then read against the rule each case names; a wrong rule would make a wrong expected line look right.
