# SCOPE - PLAN-TEXT (a records-only pull request: the plan revision `maintainer-text`)

## What this pull request is

The supervisor's plan revision at stage B5's plan revision point (after TASK-031 merged, before TASK-030 starts) placing the four text items of the maintainer's evaluation of 2026-10-25 that the owner integrated into release B on 2026-10-26 (decision D4: T14, T23, FB-036, FB-040) into the increments whose Scope already holds the text each amends, designed through the two-critic design critique (subject `maintainer-text`: four rounds and a confirming read; Review B grok-4.7-medium in design mode and the plan critic; every finding taken, or accepted with a reason, recorded in docs/DESIGN_CRITIQUE.md) and approved by the owner at the gate on 2026-10-27. It changes records only; no program and no module changes; no increment added.

## Scope (what the diff may touch)

- docs/BUILD_PLAN.md: the revision note's last sentence; TASK-030's Done when (FB-040: the duplicates cut from the mutants file and the process count estimated at step 7); TASK-034's Done when (T14: the class is the defect, not the operator; the stage arms of reflection.md's step 7; rule 6's outcomes; the convergence clause's bearing); TASK-035's Scope and Done when (T23: the change cycle's item 1 ends with an intake confirmation, not a gate; FB-036: the three "read whole" statements made to say in parts); TASK-026's clause and Depends on (now on TASK-035).
- docs/REQUIREMENTS.md: the revision note's last sentence; R-042 extended (the stage arms, the class sentence); R-043 extended (the cuts and the estimate clause).
- docs/INVENTORY.md: one Decisions row (D4's four text items placed) after the owner's integration row of 2026-10-26.
- docs/DESIGN_CRITIQUE.md: the subject `maintainer-text` block (Accepted, Rounds, Resolution, Gate).
- docs/PROJECT_STATUS.md and project.json: the position as at this pull request's merge (ISS-009).
- run/review/: the critique's round files DESIGN-maintainer-text-1.md to -5.md were committed on the branch and removed again (`git rm`); REVIEW-PLAN-TEXT.diff, SCOPE-PLAN-TEXT.md and ASSUMPTIONS-PLAN-TEXT.md are this review's files, removed before the merge.

## Out of scope

Everything else: bridge/, tests/, .github/, handoff/, Documents/. A change there is a defect of this pull request.

## Tests the supervisor wrote

None: the pull request changes records. The record checks that gate it: plan-check.py, completion-check.py --mode plan, inventory-check.py, invisible-check.py, and tests/test_plan_demonstration.py, test_release_b_bootstrap.py, test_text_consistency.py, test_plan_check.py (all green on the branch).

## Expected bookkeeping

No builder ran; no builder report, no BUILDER_NOTES change, no `Assumptions:` section in any commit. Commits on the branch: the records per round and the round files' add and removal, then the gate commit.

## What to judge

Whether the records are consistent with each other (the register, the plan, the inventory, the critique record, the status file) and with the programs, modules and tests as they stand on main where the plan makes claims about them (the pins the Done when lines name exist and pin what they are said to pin; the modules hold the passages the sentences amend); whether each amended Done when is buildable and testable as written; whether the status file reads as at this pull request's merge. Design for later increments is the plan's content here, so a judgment on the design is in scope; a finding the critique record lists as Accepted is settled. Write no file anywhere in the checkout; run the record checks and the tests named above if you wish, nothing that writes under docs/, handoff/ or run/review/.
