# TASK-005 — assumptions on the branch (round 2)

Collected from the `Assumptions:` sections of the branch's commit messages (`git log origin/main..HEAD`). Extra places to look, never the review's scope. The builder did not run: this is supervisor-authored text, so every item is the supervisor's own.

## From the first commit (the registry)
- §6.4's "additional checks at the inspect and test steps" is two points, one per step → stated in the file; accepted in round 1.
- One point added to §6.4's list, `intake.budget-kind` → accepted in round 1; now one of two refinements.
- Definition of done and Delivery are both declared by `project-end` → accepted in round 1.
- A point's replaceable flag is read through its declaring module's row → test.
- The settable points → test (now the three intake values).
- Applies per point is the supervisor's reading → test (pinned whole in round 2).

## From round 1's fixes (this round)
- The delivery kind is settled at intake (`supervisor.md` Phase 1, the installable-software paragraph) → review.
- `configuration.items` adds to one project environment → review.
