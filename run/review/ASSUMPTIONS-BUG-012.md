# ASSUMPTIONS — BUG-012

From the branch's commit messages (`git log origin/main..HEAD --format=%B`), section `Assumptions:`:

Assumptions:
- none (no builder run; supervisor's tests only)

Places to look all the same: the expected line of the new cell was taken from the check's output and then read against the `set` finding's text; the claim that the mutant fails it rests on the supervisor's own run.
