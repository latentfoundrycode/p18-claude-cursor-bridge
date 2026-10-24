# SCOPE - PLAN-PACE (a records-only pull request: the pace plan revision)

## What this pull request is

The supervisor's plan revision for the pace update (the maintainer's request of 2026-10-20, placed by the owner on 2026-10-22 in stage B5 beside TASK-028 to TASK-031), designed through the two-critic design critique (subject `pace`: four rounds and a confirming read, both critics' findings taken or accepted with a reason, recorded in docs/DESIGN_CRITIQUE.md) and approved by the owner at the gate on 2026-10-24 with the ceiling at three rounds ("I choose three"). It changes records only; no program and no module changes.

## Scope (what the diff may touch)

- docs/REQUIREMENTS.md: the revision note; R-041 reworded; R-042, R-043, R-044 new (planned).
- docs/BUILD_PLAN.md: the revision note; TASK-032, TASK-033, TASK-035, TASK-034 new in stage B5; TASK-017, TASK-023, TASK-025, TASK-030, TASK-031 amended; stage B5's demonstration extended.
- docs/INVENTORY.md: Decisions rows (the code gate's round ceiling, R-003's conservative reading, no project-end refactoring pass, stage B3's review leads carried as HARDENING leads).
- docs/HARDENING.md: "Placed by the pace plan revision" under Stage B3.
- docs/DESIGN_CRITIQUE.md: the subject `pace` block (Accepted, Rounds, Resolution, Gate).
- docs/PROJECT_STATUS.md and project.json: the position as at this pull request's merge (ISS-009).
- run/review/: the critique's round files DESIGN-pace-1.md to -5.md were committed on the branch and removed again (`git rm`); REVIEW-PLAN-PACE.diff, SCOPE-PLAN-PACE.md and ASSUMPTIONS-PLAN-PACE.md are this review's files, removed before the merge.

## Out of scope

Everything else: bridge/, tests/, .github/, handoff/, Documents/. A change there is a defect of this pull request.

## Tests the supervisor wrote

None: the pull request changes records. The record checks that gate it: plan-check.py, completion-check.py --mode plan, inventory-check.py, conformance-check.py, and tests/test_plan_demonstration.py, test_release_b_bootstrap.py, test_text_consistency.py, test_plan_check.py (all green on the branch).

## Expected bookkeeping

No builder ran; no builder report, no BUILDER_NOTES change. Commits on the branch: the records per round (f23b111, 23c0401, fd821ad, 2eaac4c, aeac207, dfde3a5, the gate commit) and the round files' add/remove.

## What to judge

Whether the records are consistent with each other (the register, the plan, the inventory, the critique record, the status file) and with the programs and modules as they stand on main where the plan makes claims about them; whether an increment's Done when is buildable and testable as written; whether the status file reads as at this pull request's merge. Design for later increments is the plan's content here, so a judgment on the design is in scope; a finding the critique record lists as Accepted is settled.
