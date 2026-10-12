# TASK-003 — scope of the review (round 4)

Branch `task-003`, from `origin/main` 9e181e6. The diff is `run/review/REVIEW-003d.diff` — the branch's whole change against `origin/main`. The plan's §6.2–6.5 are at `run/review/PLAN-6-003d.md`.

## Round 4 — what changed since round 3

Round 3 (head e4818f5): Review A APPROVE, Review B REJECT. Commit ac6ee03 applies the findings; the disposition is in `docs/DESIGN_CRITIQUE.md` ("TASK-003 round 3 — disposition"). Check that each fix holds and introduced nothing new:
- the transitional reading sentence (supervisor.md, the paragraph after the layer table) now defers to rule 28 unchanged: read whole at every start, resume and calibration; after every compaction or resume, read the sections the session-start hook names. Once the phases are modules, the core is still read whole at those points, with the current phase's module(s) and the applicable conditional workflows read alongside it. Check against rule 28 (its text near "On every start or resume, and whenever the owner runs `/calibrate-bridge`"), the core's Read-when cell, and `bridge/cursor-bridge/session-start.py`. The old phase-only wording is forbidden by a test;
- the parts sentence restates "at each extension point"; "a conditional workflow two parts share is read once, but its additions apply to every part that has it, in each part's own place in this order" (pinned);
- the crosswalk test checks every phase heading the Holds cell names (intake, design, interface, planning, run parameters, configuration, delegation loop, change cycle, reflection points);
- the round-1 note in DESIGN_CRITIQUE names the round that pinned the Holds cells; the status file's Remote sync names PR #17.

## Round 3 — what changed since round 2 (kept for the record)

Round 2 (head 8907e8e): Review A and Review B both APPROVE. The latest TASK-003 fix commit applies their findings; the disposition is in `docs/DESIGN_CRITIQUE.md` ("TASK-003 round 2 — disposition"). Check that each fix holds and introduced nothing new:
- every Holds cell is pinned by equality;
- "still read whole at every start and calibration (after a compaction, re-read what the hook names, rule 28)" — consistent with rule 28 and the session-start hook (pinned);
- the heading crosswalk is pinned and each named heading checked to exist; Phase 3 "today holds only the mockup variant";
- the type workflow's Read-when says "the phase's module or modules";
- parts × extension point nesting: the phase module's own content once, first; then each part's type, sub-workflow and trait additions in status-file order; a trait two parts share applied once, at the first part that has it (pinned);
- the status file's Next line is current.

## Round 2 — what changed since round 1 (kept for the record)

Round 1 (head 18e9f57): Review A and Review B both APPROVE. Commit 58ed1d2 applies their findings; the disposition is recorded in `docs/DESIGN_CRITIQUE.md` ("TASK-003 round 1 — disposition"). Check that each fix holds and that it introduced nothing new:
- the meaning of "Siblings are exclusive" ("a part has at most one sub-type of its product type") is asserted;
- the floor's precedence is scoped: "a conditional workflow's text that would do any of these does not apply, and on these points the core governs" (pinned);
- the additions order holds "at each extension point"; the open list governs the trait order and places a later trait at its end; several parts are taken in the status file's order (all pinned);
- "module or modules"; the transitional sentence maps the plan's phase names to this file's headings and says this file "is still read whole" until the phases move into modules (pinned);
- the Holds and Read-when cells of the five layers are pinned exactly.
Items deferred to later increments are listed there and are not this diff's defect.

## What this increment is

Supervisor-authored governance text, not a builder run: release B's plan (docs/BUILD_PLAN.md, TASK-003, "Author: supervisor") assigns governance text to the supervisor and gates it by the two-critic design review (§15 condition 3). This round serves as both that design review and the merge gate. Grade findings as **Blocking**, **Should fix** or **Consider**, then give one verdict: APPROVE, REJECT or ESCALATE-INTENT.

## Scope (from docs/BUILD_PLAN.md, TASK-003)

- Scope: `bridge/commands/supervisor.md; bridge/cursor-bridge/MANIFEST.json; tests/test_workflow_model.py`
- Satisfies: R-007, R-008, R-009, R-034
- Done when: the core describes the five layers, inheritance, read-when, replace/set/add ("only type/sub-workflows may replace or set; trait additions only add"), the founding-rule/merge-gate/register floor, and the stated order several traits' additions compose in (R-034); `test_workflow_model.py` (names R-007, R-008, R-009, R-034) asserts those statements and that the digest stays within its limit.
- Standing constraints: MANIFEST.json regenerated (`python tools/make-manifest.py`) on any `bridge/` edit; tests name their R-IDs; no hard line wraps in Markdown.

## Out of scope (later increments; not this diff's defect)

- The open list of types/sub-types/traits as a file (TASK-004). This text states the trait order by naming the open list's order and listing today's traits; TASK-004 will make the file canonical.
- The extension-point registry and each phase's declared points (TASK-005, TASK-014); the workflow check program (TASK-006); the `Workflows:` status line template (TASK-007); splitting the phases into module files (TASK-010 onward); the hook naming files in the R-034 order (TASK-015); the first trait files (TASK-017 onward).
- The compaction digest is not extended: it is at 9,490 of its 9,500-character cap, so the model lives in the core body only (the full text governs).

## Source the text must match

The plan's §6.2–6.5 are copied verbatim to `run/review/PLAN-6-003d.md` (the plan itself lives outside the Workspace). `Documents/Claude-Cursor Bridge Restructuring Plan.md` §6.2 (layers table, inheritance, read-when), §6.4 (extension points), §6.5 (add/replace/set; only types/sub-workflows replace or set; sub-workflow inheritance; siblings exclusive; two levels; the floor). The plan leaves R-034's order unstated ("in a stated order"); this text states it: phase module, type, sub-workflow, then traits in the open list's order (§6.3's trait table), later traits appended, each workflow's own order kept. Copies of the relevant docs records are in `docs/` (REQUIREMENTS.md rows R-007/008/009/034, BUILD_PLAN.md TASK-003, DESIGN_CRITIQUE.md).

## Tests the supervisor wrote

`tests/test_workflow_model.py` — enforces docs/BUILD_PLAN.md TASK-003 Done when and plan §6.2/§6.5:
- placement in the core, outside the digest (R-007);
- the five layers in order, each with Holds and Read-when (R-007);
- inheritance, read-only-when-applies, changes only at extension points (R-007);
- add/replace/set, replace only where declared, the "only type workflows and sub-workflows may replace or set" sentence (R-008);
- the floor sentence: founding rule, merge gate, requirements register, inventory, reviews (R-008);
- sub-workflow inherits and may override, siblings exclusive, two levels (R-009);
- the stated order: phase module → type → sub-workflow → traits, traits in §6.3's order, later traits, a workflow's own order (R-034);
- the digest keeps its 9,500 / 20,000 limits.
Against `origin/main` the file fails (the heading is absent). No mutation driver (text test).

## Expected bookkeeping in the diff

`docs/PROJECT_STATUS.md` (position rewrite), `docs/DESIGN_CRITIQUE.md` (the round-1 record), `docs/REQUIREMENTS.md` (R-007/008/009/034 → built with the test as evidence; R-001 → built, a correction of TASK-001's row, which its merge left at planned), `bridge/cursor-bridge/MANIFEST.json` (regenerated hash of supervisor.md), `run/review/` (these review files).
