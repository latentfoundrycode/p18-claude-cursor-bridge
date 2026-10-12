# SCOPE-007 — TASK-007, the `Workflows:` status line: template and semantics

Supervisor-authored governance text (no builder run; §15 condition 3). Round 1.

## The increment (docs/BUILD_PLAN.md, TASK-007)
- Scope: bridge/commands/supervisor.md; bridge/cursor-bridge/MANIFEST.json; tests/test_workflows_line_text.py
- Satisfies: R-015 ("The status file records a `Workflows:` line per part (product type, sub-type, traits) beside the `Phase:` line.")
- Done when: the status template carries a `Workflows:` line per part (product type → sub-type; traits) beside `Phase:`, its grammar defined; `test_workflows_line_text.py` (names R-015) asserts the template and grammar are present.

## Where it ends
- This increment states the line and its grammar only. Reading and checking the line is TASK-008 (`inventory-check.py` / `conformance-check.py`, a builder increment); the workflow check's rules on the line (one type, at most one sub-type, names in the open list, unwritten type fails) are TASK-006 (`workflow-check.py`). R-015 therefore stays `planned`; its Evidence cell names this test and TASK-008.
- The session-start hook reading the line to name conditional-workflow files is TASK-015's.
- Design for later increments is not this diff's defect.

## The plan's text this must match (run/review/PLAN-6-007.md)
- §6.2 (line 191 of the plan): "A project's status file records, for each part (section 7), its product type, sub-type and traits on a `Workflows:` line, and the project's phase on the `Phase:` line; together they name exactly what a resumed session must read. A project with one part has one `Workflows:` line."
- §6.6: the check verifies one product type, at most one of its sub-types, and traits, all in the open list; an unwritten type or sub-type fails.
- The open list (bridge/cursor-bridge/workflow/open-list.md, merged in TASK-004) says its Workflow name / Sub-workflow name are "used in the status file's `Workflows:` line" and a trait "is named by [its Name] on a `Workflows:` line".

## Choices to check
1. Names: Workflow name for the type, Sub-workflow name for the sub-type, Name for a trait (the open list's own column notes).
2. Traits written in the Traits table's order (one spelling per set), `none` when there is none.
3. The `<part>: ` prefix only when the project has several parts; one part, one line without it (the plan's form).
4. `not yet classified` before intake classifies a part.
5. The paragraph sits after the template, after the "Awaiting user on" paragraph and before "Terms fixed" — core text, outside the compaction digest (whose character limit is enforced and which is not touched).
6. The pause/flag sentence restates the open list's §6.7 rule; it adds no new behaviour.

## Tests the supervisor wrote (tests/test_workflows_line_text.py, names R-015)
- enforces BUILD_PLAN TASK-007 Done when; plan §6.2, §6.6, §6.7 as the open list states it.
- The template: `Workflows:` is the line right after `Phase:`, once.
- The grammar line and each rule's sentence are pinned; the paragraph's place (after "Project state", before "Terms fixed", after the digest end).
- A checker built from the stated rules validates the example line and this project's own docs/PROJECT_STATUS.md line against the open list's tables, and refuses malformed lines (keys for names, another type's sub-type, traits out of order, a missing traits part, a prefix with one part).
- Run against origin/main's supervisor.md and status file: 8 of 9 fail; the ninth (the checker's own refusals) passes there by construction, as it reads only the open list.

## Expected bookkeeping and record files in the diff
- bridge/cursor-bridge/MANIFEST.json (regenerated hash of supervisor.md; VERSION unchanged).
- docs/PROJECT_STATUS.md (TASK-005 merged at 82f0e44; Increment TASK-007; the bridge's `Workflows:` line rewritten in the new grammar and moved beside `Phase:`).
- docs/DESIGN_CRITIQUE.md (TASK-005 round-6 record: Considers not taken, routed to later briefs and the stage-close test lane).
- docs/REQUIREMENTS.md (R-015 Evidence; status stays planned).
- docs/INVENTORY.md (a feature row).
- run/review/ (this file, the diff, PLAN-6-007.md, ASSUMPTIONS-007.md).

## Out of scope
- The compaction digest (at its cap); any program; the open list; the registry.
