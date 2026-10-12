# TASK-005 — scope of the review (round 5)

Branch `task-005`, from `origin/main` f40bf82. The diff is `run/review/REVIEW-005e.diff`, the branch's whole change against `origin/main` (rounds 1 to 4's fixes included). The plan's §6.3–§6.11 are copied verbatim to `run/review/PLAN-6-005e.md` (the plan itself lives outside the Workspace). `bridge/commands/supervisor.md` is in the tree: its "Main and conditional workflows" section is the core text the registry must agree with; its Phase 1 settles the performance budgets and the delivery kind; its Phase 5 sets up the project environment.

## What this increment is

Supervisor-authored governance text, not a builder run: release B's plan (docs/BUILD_PLAN.md, TASK-005, "Author: supervisor") assigns governance text to the supervisor and gates it by the two-critic design review (§15 condition 3). This round serves as both that design review and the merge gate. Grade findings as **Blocking**, **Should fix** or **Consider**, then give one verdict: APPROVE, REJECT or ESCALATE-INTENT.

## What round 4 found and what changed (this round's focus)

Round 4: Review A APPROVE (0 Blocking / 1 Should fix / 1 Consider), Review B APPROVE (nothing). The record and disposition are in `docs/DESIGN_CRITIQUE.md`, "TASK-005 round 4 — disposition" (in the diff); Review A's items were taken before the merge, because the registry is in no later increment's Scope. Round 5's change is one commit; check each fix is present and sound:
- the inspect and test points divide every check of an increment between them, wherever the module's text places it: the test step is the running of the increment's tests and the suite and the checks that run with them (the benchmark floor, which the trait *performance budgets* carries); the inspect step is every other check or review of the diff before the accept decision, before the tests (the scope check, the diagram check, the boundary log) or after them (a reviewer pass such as the design auditor, which the trait *has screens* carries; TASK-017). Rounds 2 to 4 defined the points by today's placement, and each left a check out; check that no check of the delegation loop (`supervisor.md` Phase 6 steps 4 to 6, the routing table) is now without a point;
- the kind the supervisor confirms at intake is recorded by its key from the delivery-kinds list;
- the tests: one rewritten (`test_r006_the_inspect_and_test_steps_divide_every_check`), one assertion extended (the recorded key); 21 pass; against the round-4 file exactly those 2 fail (run by the supervisor).

Earlier rounds' fixes were confirmed by both reviewers in round 4; settled, do not raise them again unless a round-5 fix itself is wrong.

## Scope (from docs/BUILD_PLAN.md, TASK-005)

- Scope: `bridge/cursor-bridge/workflow/extension-points.md; bridge/cursor-bridge/MANIFEST.json; tests/test_extension_points.py`
- Depends on: TASK-003. Satisfies: R-006 (its registry half; the per-module declarations are TASK-011–014, so R-006 stays `planned`).
- Done when: the registry lists the §6.4 points per phase, including Definition of done and Delivery, each naming the module that declares it and whether its phase is replaceable (the interface phase is, per §6.4); `test_extension_points.py` (names R-006) asserts every §6.4 point is present, names a declaring module, and carries a replaceable flag.
- Standing constraints: MANIFEST.json regenerated on any `bridge/` edit; tests name their R-IDs; no hard line wraps in Markdown.

## Choices rounds 1 to 4 accepted (settled; do not raise again unless a fix itself is wrong)

The ten module keys in TASK-010's order; the replaceable flag on the module row, read through the declaring module; Definition of done and Delivery declared by `project-end`; inspect and test checks as two points; `intake.budget-kind` as a stated refinement; the `Add at` / `Set at` / `Replace` headings.

## Out of scope (later increments; not this diff's defect)

- The phase modules and their `## Extension points` sections (TASK-010 carves; TASK-011–014 declare; TASK-014's cross-check).
- `workflow-check.py` (TASK-006); its brief carries the replacement, set-at-a-non-settable-point and delivery-kind checks, and the form in which an addition names its kind; TASK-020's brief, its kind confirmed at intake.
- The core's sentence on shared workflows is reconciled when the core is carved (TASK-010).
- Any conditional workflow file (TASK-017 onward).

## Tests the supervisor wrote

`tests/test_extension_points.py` — enforces docs/BUILD_PLAN.md TASK-005 (Scope path, Done when) and plan §6.4, §6.5, §6.6, §6.11; names R-006. Round 1's tests (see the diff), plus: the two refinements in S64 and their sentence; SETTABLE the three intake values; the Applies column pinned whole (`PROJECT_WIDE`, `configuration.items` included); the first-part placement and the per-part/project rule; a replacement keeps the replaced module's points; what the workflow check fails (the three cases); an addition at a value point; a completion condition entering at intake; the phases' path statement and the change cycle's missing section; in round 3, the delivery-kind tie and the test step; in round 4, the kinds list and the unset kind; in round 5, the two points dividing every check, and the recorded key. 21 pass; against the round-4 file exactly the 2 round-5 tests fail, against the round-3 file the round-4 tests fail, against the round-2 file the round-3 tests fail, against the round-1 file the round-2 assertions fail, and against `origin/main` the file is absent, so every test fails. No mutation driver (a text test).

## Expected bookkeeping in the diff

`docs/PROJECT_STATUS.md` (position: TASK-004 merged at f40bf82, TASK-005 round 5, PR #19, ISS-004 off Open issues, the owner's Socket-slug question), `docs/DESIGN_CRITIQUE.md` (TASK-004's round-3 record, TASK-005's round-1 to round-4 records), `docs/REQUIREMENTS.md` (R-006 evidence, still `planned`), `docs/INVENTORY.md` (the registry's feature row), `bridge/cursor-bridge/MANIFEST.json` (the file's hash), `run/review/` (these review files).
