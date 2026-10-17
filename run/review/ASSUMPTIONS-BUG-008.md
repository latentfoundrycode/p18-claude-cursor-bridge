# ASSUMPTIONS — BUG-008

From the branch's commit messages (`git log origin/main..HEAD --format=%B`), section `Assumptions:`:

- none: no builder ran on this branch; the tests, fixtures and text sentences are the supervisor's.

Places to look all the same: the expected outputs in FILE_EXACT, STATUS_EXACT and the new tests were taken from the check's output and then read against the rule each case names; a wrong rule would make a wrong expected line look right. The widened sweep's 213 survivors are recorded in docs/HARDENING.md by class; each class is the supervisor's reasoning, not a test.
