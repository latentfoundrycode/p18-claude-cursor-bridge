# Assumptions, TASK-070

The builder's `Assumed, not verified` list (handoff/TASK-070-r1-report.md) and the supervisor's, each with its disposition. Extra places to look, never the review's scope.

## Round 1
- The escaped parametrized id has the same form on Linux -> accepted, settled by Review A (pytest's ascii_escaped is platform-independent) and by CI's ubuntu job.
- A tests list whose every test is skipped exits 0 and passes the baseline -> accepted (a skip is no failure; probed by Review A).
- Exit 1 with a clean outcomes record is a failure (exit 5) -> accepted, the brief's own wording; reachable only by a conftest that changes the exit.

## The supervisor's
- A list that times out is no failure, its mutants reported unrun -> accepted, the plan's "the three timeout tests ... stay green".
- The three rewritten fixtures still prove their claims -> accepted, each claim restated in its docstring; both files green on the old code.
- The acceptance tests fix no wording of the exit-5 line beyond its naming the list's files and failing ids -> accepted.
