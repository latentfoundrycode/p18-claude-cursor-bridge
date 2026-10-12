# SCOPE-007b — TASK-007 round 2, the `Workflows:` status line

Supervisor-authored governance text (no builder run). Round 2; a new head, re-reviewed whole.

## Files
- run/review/REVIEW-007b.diff — the whole branch against origin/main (read it whole; it is the review's subject).
- run/review/REVIEW-007b-round.diff — round 2 alone (f84c390..HEAD), for orientation only; it includes the removal of round 1's review files.
- run/review/PLAN-6-007b.md — the plan's §6, now from §6.1 (§6.2's `Workflows:` sentence is its line 24), then §6.3 onward as before (22,280 bytes).
- run/review/ASSUMPTIONS-007b.md — extra places to look.

## The increment (docs/BUILD_PLAN.md, TASK-007)
- Scope: bridge/commands/supervisor.md; bridge/cursor-bridge/MANIFEST.json; tests/test_workflows_line_text.py
- Satisfies: R-015. Done when: the status template carries a `Workflows:` line per part (product type → sub-type; traits) beside `Phase:`, its grammar defined; `test_workflows_line_text.py` (names R-015) asserts the template and grammar are present.
- Where it ends: the line and its grammar only. TASK-008 (builder) reads and checks it in `inventory-check.py` / `conformance-check.py`; TASK-006 the workflow check; TASK-015 the hook. R-015 stays `planned`. Design for later increments is not this diff's defect.

## What round 1 found and what changed (docs/DESIGN_CRITIQUE.md, "TASK-007 round 1")
Round 1: Review A APPROVE 0/1/6, Review B APPROVE 0/0/1.
1. Should fix (A): "`<part>: ` … begins a line" contradicted the grammar line, which puts it after `Workflows: `. Now "follows `Workflows: `"; the checker refuses `<part>: Workflows: …`.
2. Consider (A), taken: a part's name contains no `:`, `;` or `→`; with several parts the lines stand together right after `Phase:`, one per part, in the order of the project's parts, which is the order the core's "for each part in the order the status file lists them" (in "Main and conditional workflows") reads; the line is written at intake with the proposed traits and rewritten at the design gate if they changed; the pause is anchored "At intake" (§6.7).
3. Consider (A + B), taken in the test: each refusal of the reference checker names its fault; added cases — repeated trait, an unknown Sub-workflow name (the plain Name), a prefixed `not yet classified`, a missing prefix with several parts, and `External services, Performance budgets` (alphabetical, yet out of the Traits table's order) refused while the reverse passes; the bridge's own status line is checked to be the line right after `Phase:`.
4. Consider (A), taken in the records: the status file's Next names TASK-008 beside TASK-009; Remote sync names PR #20.
5. Consider (A), routed: TASK-008's check reads form and name membership, never the Written flag (every open-list entry is unwritten until its workflow is written, the bridge's own type included), and its brief says which copy of the open list it reads → the supervisor's carry list for TASK-008's brief (not in this diff). task-002's status copy (not in the repository) takes main's form when main is merged into it.
6. Consider (A): the plan excerpt now carries §6.1–6.2.

## Choices to check
- The ordering sentence reuses the core's existing phrase rather than defining a new order.
- "rewritten then if they changed" — the design gate is where traits are settled (open-list.md, Traits; R-035).
- The forbidden characters in a part's name are exactly the grammar's separators.

## Tests the supervisor wrote (tests/test_workflows_line_text.py, names R-015)
- enforces BUILD_PLAN TASK-007 Done when; plan §6.2, §6.6, §6.7 as the open list states it.
- Run against round 1's files (f84c390's supervisor.md and status file): the 2 tests whose pins were rewritten fail there; the other 7 pass there (the checker's refinements read only the open list; round 1's status line already stood right after `Phase:`).
- Full suite: 927 passed, 20 skipped. Secret scan CLEAR.

## Expected bookkeeping and record files in the diff
- bridge/cursor-bridge/MANIFEST.json (supervisor.md's hash; VERSION unchanged); docs/PROJECT_STATUS.md; docs/DESIGN_CRITIQUE.md (TASK-005 round 6 and TASK-007 round 1 records); docs/REQUIREMENTS.md (R-015 Evidence); docs/INVENTORY.md (a feature row); run/review/ (these files).

## Out of scope
- The compaction digest; any program; the open list; the registry.
