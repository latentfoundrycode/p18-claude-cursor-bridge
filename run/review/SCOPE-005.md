# TASK-005 — scope of the review (round 1)

Branch `task-005`, from `origin/main` f40bf82. The diff is `run/review/REVIEW-005.diff`, the branch's whole change against `origin/main`. The plan's §6.3–§6.11 are copied verbatim to `run/review/PLAN-6-005.md` (the plan itself lives outside the Workspace). `bridge/commands/supervisor.md` is in the tree: its "Main and conditional workflows" section (TASK-003) is the core text this registry must agree with, and its Phase 1 holds the performance budgets.

## What this increment is

Supervisor-authored governance text, not a builder run: release B's plan (docs/BUILD_PLAN.md, TASK-005, "Author: supervisor") assigns governance text to the supervisor and gates it by the two-critic design review (§15 condition 3). This round serves as both that design review and the merge gate. Grade findings as **Blocking**, **Should fix** or **Consider**, then give one verdict: APPROVE, REJECT or ESCALATE-INTENT.

## Scope (from docs/BUILD_PLAN.md, TASK-005)

- Scope: `bridge/cursor-bridge/workflow/extension-points.md; bridge/cursor-bridge/MANIFEST.json; tests/test_extension_points.py`
- Depends on: TASK-003. Satisfies: R-006 (its registry half; the per-module declarations are TASK-011–014, so R-006 stays `planned`).
- Done when: the registry lists the §6.4 points per phase, including Definition of done and Delivery, each naming the module that declares it and whether its phase is replaceable (the interface phase is, per §6.4); `test_extension_points.py` (names R-006) asserts every §6.4 point is present, names a declaring module, and carries a replaceable flag.
- Standing constraints: MANIFEST.json regenerated on any `bridge/` edit; tests name their R-IDs; no hard line wraps in Markdown.
- Carried here from earlier rounds (docs/DESIGN_CRITIQUE.md): how a replaced phase and a trait's attachment point are declared (TASK-003 round 3 → TASK-005); a project-wide addition from a conditional workflow two parts share, asked once or per part (TASK-003 round 4 → TASK-005).

## Choices the text makes that the plan leaves open (check them)

- **Module keys and the module list.** The ten modules and their file names follow BUILD_PLAN TASK-010's Scope (`workflow/phases/<module>.md`), in that order.
- **The replaceable flag sits on the module's row,** and a point's phase is replaceable exactly when its declaring module is; the flag is stated once, not repeated per point. The Done-when's "each [point] ... whether its phase is replaceable" is met through the declaring module (the test reads it that way).
- **Definition of done and Delivery are both declared by `project-end`.** TASK-014's Done when says "reflection/project-end declare Definition of done and Delivery"; the supervisor read that as the pair of modules TASK-014 writes, with both points in project-end, where the completion check and delivery run today.
- **Inspect and test checks are two points,** one per step, so that a check names the step it runs at.
- **One point added to §6.4's list: `intake.budget-kind`.** §6.5 names "the kind of performance budget (page load, frame time)" as a value a type workflow or sub-workflow sets, but §6.4 has no point for it; the core settles budgets in Phase 1 (Intake). §6.4 calls its list initial, "to be refined during implementation"; the file states the refinement.
- **The settable points** (`add, set`): the target environment, the budget kind and the delivery procedure (the delivery kind the value set). Every point accepts additions.
- **Applies** (`part` / `project`): the supervisor's reading of which additions exist once per project (the diagram catalogue, the plan critic's lenses, run parameters, reflection items) and which per part. This answers the deferred question of a project-wide addition two parts share: made once.
- **How a conditional workflow names a point:** `## Add at <point key>`, `## Set at <point key>`, `## Replace <module key>` headings; a trait has only `Add at`.

## Out of scope (later increments; not this diff's defect)

- The phase modules themselves and their `## Extension points` sections (TASK-010 carves the files; TASK-011–014 add the declarations; TASK-014 adds the tree-wide registry↔module cross-check).
- `workflow-check.py` and its reading of these tables (TASK-006).
- Any conditional workflow file (TASK-017 onward).
- TASK-004's round-3 Consider items placed elsewhere (see its record in the diff).

## Tests the supervisor wrote

`tests/test_extension_points.py` — enforces docs/BUILD_PLAN.md TASK-005 Done when and plan §6.4, §6.5, §6.6, §6.11; names R-006:
- the file at the §6.11 path, bounded, no CR characters;
- both tables parse with exactly the stated columns, one heading each; first table after the heading, rows to the first non-table line, the separator one cell per column, every row one cell per column;
- every phase module listed once in TASK-010's order with `yes`/`no`; only `interface` replaceable;
- every §6.4 point present in §6.4's order (plus the one stated refinement), with its §6.4 phase, a phrase of its §6.4 text, and its declaring module; Definition of done and Delivery present;
- every key `<module>.<name>`, its module the declaring one and a listed module;
- every point carries its phase's replaceable flag through its declaring module; only `interface.variants` is in a replaceable phase; the sentence stating that is pinned;
- Changes always starts with `add`, `set` exactly on the settable points; Applies ∈ {part, project};
- the change cycle declares no point;
- the table shape stated for the reader;
- the Add at / Set at / Replace headings, who may set or replace, a trait only adds;
- a shared project-wide addition made once; two project-level points pinned;
- how a phase module declares its points;
- points change only in a bridge release by the maintainer; the core's closed guarantees.
Against `origin/main` the file is absent, so every test fails. No mutation driver (a text test).

## Expected bookkeeping in the diff

`docs/PROJECT_STATUS.md` (position: TASK-004 merged at f40bf82, TASK-005 in progress, ISS-004 off Open issues, the owner's Socket-slug question), `docs/DESIGN_CRITIQUE.md` (TASK-004's round-3 record), `docs/REQUIREMENTS.md` (R-006 evidence, still `planned`), `docs/INVENTORY.md` (the registry's feature row), `bridge/cursor-bridge/MANIFEST.json` (the file's hash), `run/review/` (these review files).
