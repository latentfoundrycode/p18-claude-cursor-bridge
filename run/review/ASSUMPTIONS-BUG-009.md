# ASSUMPTIONS — BUG-009

From the branch's commit messages (`git log origin/main..HEAD --format=%B`), section `Assumptions:`:

- none: no builder ran on this branch; the tests and fixtures are the supervisor's.

Places to look all the same: the expected outputs of the new tests were taken from the check's output and then read against the rule each case names; a wrong rule would make a wrong expected line look right. Which white-space variants are (form) and which are prose follows the program's heading-candidate rule (R3-6) and change-heading rule (R3-4); the widened sweep's survivors are recorded in docs/HARDENING.md by class, and each class is the supervisor's reasoning, not a test.
