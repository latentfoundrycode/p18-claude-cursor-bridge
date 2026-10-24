# SCOPE - PLAN-TRAITS (a records-only pull request: the stage B4 plan revision, subject `traits`)

## What this pull request is

The supervisor's revision of stage B4's plan, made before TASK-017's first edit, after the reality check of the text as built (the delegation loop's step 2 rule applied to the supervisor's own increment) found passages no extension point places, paragraphs two traits share, and source and pin files outside the increments' Scopes. Designed through the two-critic design critique (subject `traits`: four rounds, the confirming read and a resolution round, both critics' findings taken or accepted with a reason, recorded in docs/DESIGN_CRITIQUE.md) and approved by the owner at the gate on 2026-10-24 ("I approve of the plan"). It changes records only; no program and no module changes.

## Scope (what the diff may touch)

- docs/BUILD_PLAN.md: the revision note; TASK-017's Scope and Done when; TASK-018's Depends on and Done when; TASK-019 to TASK-021's Scopes and Done when (delivery kinds by key, `project-end.delivery` procedures, the trace entries' tail); TASK-034's Done when gains the gloss clause (the subject's lead, carried at Review A round 1).
- docs/INVENTORY.md: five Decisions rows (the moving rule and what stays; the two §6.4 refinements; the `Installer verification` parameter; external services' new checks; the plan critic's conditional lenses).
- docs/HARDENING.md: "Placed by the stage B4 plan revision" under Stage B4 (the stay list; the leads).
- docs/DESIGN_CRITIQUE.md: the subject `traits` block (What is criticised, Accepted, Rounds 1 to 5, Resolution, Gate).
- docs/ROSTER.resolved.json: re-resolved at the revision's start (native profile).
- docs/PROJECT_STATUS.md and project.json: the position as at this pull request's merge (ISS-009).
- run/review/: the critique's round files DESIGN-traits-1.md to -5.md, DESIGN-traits-R1.md and REVIEW-DESIGN-traits-R1.md were committed on the branch and removed again (`git rm`); REVIEW-PLAN-TRAITS.diff, SCOPE-PLAN-TRAITS.md and ASSUMPTIONS-PLAN-TRAITS.md are this review's files, removed before the merge.

## Out of scope

Everything else: bridge/, tests/, .github/, handoff/, Documents/. A change there is a defect of this pull request.

## Tests the supervisor wrote

None: the pull request changes records. The record checks that gate it: plan-check.py, completion-check.py --mode plan, inventory-check.py, and tests/test_plan_demonstration.py, test_release_b_bootstrap.py, test_text_consistency.py, test_plan_check.py (all green on the branch).

## Expected bookkeeping

No builder ran; no builder report, no BUILDER_NOTES change. Commits on the branch: the records per round, the round files' add and remove, the gate commit and the status commit.

## What to judge

Whether the records are consistent with each other (the plan, the inventory, the hardening leads, the critique record, the status file) and with the modules, the registry, the trace exceptions, trace-check.py and the tests as they stand on main where the plan makes claims about them (which unit a passage is, which heading it sits under, which pin reads it); whether TASK-017's to TASK-021's Done when are buildable and testable as written; whether the status file reads as at this pull request's merge. Design for later increments is the plan's content here, so a judgment on the design is in scope; a finding the critique record lists as Accepted, or settled by its resolution round, is settled.
