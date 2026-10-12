# TASK-005 — scope of the review (round 3)

Branch `task-005`, from `origin/main` f40bf82. The diff is `run/review/REVIEW-005c.diff`, the branch's whole change against `origin/main` (rounds 1 and 2's fixes included). The plan's §6.3–§6.11 are copied verbatim to `run/review/PLAN-6-005c.md` (the plan itself lives outside the Workspace). `bridge/commands/supervisor.md` is in the tree: its "Main and conditional workflows" section is the core text the registry must agree with; its Phase 1 settles the performance budgets and the delivery kind; its Phase 5 sets up the project environment.

## What this increment is

Supervisor-authored governance text, not a builder run: release B's plan (docs/BUILD_PLAN.md, TASK-005, "Author: supervisor") assigns governance text to the supervisor and gates it by the two-critic design review (§15 condition 3). This round serves as both that design review and the merge gate. Grade findings as **Blocking**, **Should fix** or **Consider**, then give one verdict: APPROVE, REJECT or ESCALATE-INTENT.

## What round 2 found and what changed (this round's focus)

Round 2: Review A APPROVE (0 Blocking / 1 Should fix / 3 Consider), Review B APPROVE (0 / 1 / 0). The record and disposition are in `docs/DESIGN_CRITIQUE.md`, "TASK-005 round 2 — disposition" (in the diff); every finding was taken. Round 3's change is one commit; check each fix is present and sound:
- each addition at `project-end.delivery` names the delivery kind it is for and applies only to a part whose kind, set at `intake.delivery-kind`, is that kind (so a sub-workflow that sets another kind leaves its type's procedure behind; §6.9, TASK-019, TASK-021);
- the test step is the run of the increment's tests and the suite in step 4 (Inspect); step 6 adds the benchmark floor and is not this point;
- a replacement keeps the replaced module's points without declaring them again under its `## Replace` heading;
- the intake copy of a completion condition names that condition as its source;
- the tests: two new tests (the delivery-kind tie, the test step), two assertions updated to the new wording; 20 pass.

Rounds 1 and 2's other fixes were confirmed by both reviewers in round 2; settled, do not raise them again unless a round-3 fix itself is wrong.

## Scope (from docs/BUILD_PLAN.md, TASK-005)

- Scope: `bridge/cursor-bridge/workflow/extension-points.md; bridge/cursor-bridge/MANIFEST.json; tests/test_extension_points.py`
- Depends on: TASK-003. Satisfies: R-006 (its registry half; the per-module declarations are TASK-011–014, so R-006 stays `planned`).
- Done when: the registry lists the §6.4 points per phase, including Definition of done and Delivery, each naming the module that declares it and whether its phase is replaceable (the interface phase is, per §6.4); `test_extension_points.py` (names R-006) asserts every §6.4 point is present, names a declaring module, and carries a replaceable flag.
- Standing constraints: MANIFEST.json regenerated on any `bridge/` edit; tests name their R-IDs; no hard line wraps in Markdown.

## Choices rounds 1 and 2 accepted (settled; do not raise again unless a fix itself is wrong)

The ten module keys in TASK-010's order; the replaceable flag on the module row, read through the declaring module; Definition of done and Delivery declared by `project-end`; inspect and test checks as two points; `intake.budget-kind` as a stated refinement; the `Add at` / `Set at` / `Replace` headings.

## Out of scope (later increments; not this diff's defect)

- The phase modules and their `## Extension points` sections (TASK-010 carves; TASK-011–014 declare; TASK-014's cross-check).
- `workflow-check.py` (TASK-006); its brief carries the replacement, set-at-a-non-settable-point and delivery-kind checks, and the form in which an addition names its kind.
- The core's sentence on shared workflows is reconciled when the core is carved (TASK-010).
- Any conditional workflow file (TASK-017 onward).

## Tests the supervisor wrote

`tests/test_extension_points.py` — enforces docs/BUILD_PLAN.md TASK-005 (Scope path, Done when) and plan §6.4, §6.5, §6.6, §6.11; names R-006. Round 1's tests (see the diff), plus: the two refinements in S64 and their sentence; SETTABLE the three intake values; the Applies column pinned whole (`PROJECT_WIDE`, `configuration.items` included); the first-part placement and the per-part/project rule; a replacement keeps the replaced module's points; what the workflow check fails (the three cases); an addition at a value point; a completion condition entering at intake; the phases' path statement and the change cycle's missing section; in round 3, the delivery-kind tie and the test step. 20 pass; against the round-2 file exactly the 4 new or changed round-3 tests fail (run by the supervisor), against the round-1 file the round-2 assertions fail, and against `origin/main` the file is absent, so every test fails. No mutation driver (a text test).

## Expected bookkeeping in the diff

`docs/PROJECT_STATUS.md` (position: TASK-004 merged at f40bf82, TASK-005 round 3, PR #19, ISS-004 off Open issues, the owner's Socket-slug question), `docs/DESIGN_CRITIQUE.md` (TASK-004's round-3 record, TASK-005's round-1 and round-2 records), `docs/REQUIREMENTS.md` (R-006 evidence, still `planned`), `docs/INVENTORY.md` (the registry's feature row), `bridge/cursor-bridge/MANIFEST.json` (the file's hash), `run/review/` (these review files).
