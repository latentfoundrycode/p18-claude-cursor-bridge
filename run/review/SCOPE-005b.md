# TASK-005 — scope of the review (round 2)

Branch `task-005`, from `origin/main` f40bf82. The diff is `run/review/REVIEW-005b.diff`, the branch's whole change against `origin/main` (round 1's fixes included). The plan's §6.3–§6.11 are copied verbatim to `run/review/PLAN-6-005b.md` (the plan itself lives outside the Workspace). `bridge/commands/supervisor.md` is in the tree: its "Main and conditional workflows" section is the core text the registry must agree with; its Phase 1 settles the performance budgets and the delivery kind; its Phase 5 sets up the project environment.

## What this increment is

Supervisor-authored governance text, not a builder run: release B's plan (docs/BUILD_PLAN.md, TASK-005, "Author: supervisor") assigns governance text to the supervisor and gates it by the two-critic design review (§15 condition 3). This round serves as both that design review and the merge gate. Grade findings as **Blocking**, **Should fix** or **Consider**, then give one verdict: APPROVE, REJECT or ESCALATE-INTENT.

## What round 1 found and what changed (this round's focus)

Round 1: Review A REJECT (1 Blocking / 3 Should fix / 5 Consider), Review B APPROVE (0 / 2 / 1). The record and disposition are in `docs/DESIGN_CRITIQUE.md`, "TASK-005 round 1 — disposition" (in the diff); every finding was taken. Check each fix is present and sound:
- the delivery kind is set at `intake.delivery-kind` (`add, set`); `project-end.delivery` holds the procedure and is `add` only; both refinements of §6.4 stated in one sentence;
- Applies: the core's order governs every point, its per-part rule for a shared workflow is the rule for `part` points, and a `project` point is the one exception, made once in the place of the first part in the status file's order that has the workflow (converged finding);
- `configuration.items` is `project` (REVIEWERS DISAGREE in round 1, settled for Review B);
- a replacement declares the same points as the module it replaces; a set at a point opening no value fails the check;
- the change cycle's module has no `## Extension points` section; a completion condition the plan builds toward also enters at intake; an addition at a value point never sets a second value; where the test step runs today;
- the tests: the two refinements, the settable set, Applies pinned whole, the new statements pinned, the file's path cited from BUILD_PLAN's Scope; the status file names PR #19.

## Scope (from docs/BUILD_PLAN.md, TASK-005)

- Scope: `bridge/cursor-bridge/workflow/extension-points.md; bridge/cursor-bridge/MANIFEST.json; tests/test_extension_points.py`
- Depends on: TASK-003. Satisfies: R-006 (its registry half; the per-module declarations are TASK-011–014, so R-006 stays `planned`).
- Done when: the registry lists the §6.4 points per phase, including Definition of done and Delivery, each naming the module that declares it and whether its phase is replaceable (the interface phase is, per §6.4); `test_extension_points.py` (names R-006) asserts every §6.4 point is present, names a declaring module, and carries a replaceable flag.
- Standing constraints: MANIFEST.json regenerated on any `bridge/` edit; tests name their R-IDs; no hard line wraps in Markdown.

## Choices round 1 accepted (settled; do not raise again unless a fix itself is wrong)

The ten module keys in TASK-010's order; the replaceable flag on the module row, read through the declaring module; Definition of done and Delivery declared by `project-end`; inspect and test checks as two points; `intake.budget-kind` as a stated refinement; the `Add at` / `Set at` / `Replace` headings.

## Out of scope (later increments; not this diff's defect)

- The phase modules and their `## Extension points` sections (TASK-010 carves; TASK-011–014 declare; TASK-014's cross-check).
- `workflow-check.py` (TASK-006); its brief carries the replacement and set-at-a-non-settable-point checks.
- The core's sentence on shared workflows is reconciled when the core is carved (TASK-010).
- Any conditional workflow file (TASK-017 onward).

## Tests the supervisor wrote

`tests/test_extension_points.py` — enforces docs/BUILD_PLAN.md TASK-005 (Scope path, Done when) and plan §6.4, §6.5, §6.6, §6.11; names R-006. Round 1's tests (see the diff), plus: the two refinements in S64 and their sentence; SETTABLE the three intake values; the Applies column pinned whole (`PROJECT_WIDE`); the first-part placement and the per-part/project rule; a replacement keeps the replaced module's points; what the workflow check fails (the three cases); an addition at a value point; a completion condition entering at intake; the phases' path statement and the change cycle's missing section. 18 pass; against the round-1 file 8 fail (each new or changed assertion), and against `origin/main` the file is absent, so every test fails. No mutation driver (a text test).

## Expected bookkeeping in the diff

`docs/PROJECT_STATUS.md` (position: TASK-004 merged at f40bf82, TASK-005 round 2, PR #19, ISS-004 off Open issues, the owner's Socket-slug question), `docs/DESIGN_CRITIQUE.md` (TASK-004's round-3 record, TASK-005's round-1 record), `docs/REQUIREMENTS.md` (R-006 evidence, still `planned`), `docs/INVENTORY.md` (the registry's feature row), `bridge/cursor-bridge/MANIFEST.json` (the file's hash), `run/review/` (these review files).
