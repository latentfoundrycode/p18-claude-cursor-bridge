# TASK-005 — assumptions on the branch (round 1)

Collected from the `Assumptions:` section of the branch's commit message (`git log origin/main..HEAD`). Extra places to look, never the review's scope. The builder did not run: this is supervisor-authored text, so every item is the supervisor's own.

- §6.4's "additional checks at the inspect and test steps" is two points, one per step → stated in the file; review.
- One point added to §6.4's list, `intake.budget-kind`, for §6.5's "kind of performance budget" (budgets are settled at intake) → stated in the file and pinned by test; review.
- Definition of done and Delivery are both declared by `project-end` (TASK-014 says "reflection/project-end") → review.
- A point's replaceable flag is read through its declaring module's row, stated once → test.
- The settable points are the target environment, the budget kind and the delivery kind → test.
- Applies (`part` / `project`) per point is the supervisor's reading → review.
