# SCOPE-TASK-009b — the glossary gains the plan's terms (PR #25), review round 2

The diff is `run/review/REVIEW-TASK-009b.diff` (`git diff bcd3bb4...HEAD`, bcd3bb4 being origin/main, TASK-008's merge). TASK-009 is supervisor-authored governance text (docs/BUILD_PLAN.md: "Author: supervisor"), so there is no builder brief and no builder report; the increment is defined by the build plan, quoted:

## The increment (quoted from docs/BUILD_PLAN.md)
- Scope: bridge/cursor-bridge/Glossary.md; bridge/cursor-bridge/MANIFEST.json; tests/test_glossary_terms.py
- Satisfies: R-028 (the glossary gains the terms of this plan)
- Done when: the glossary defines the closed set — conditional workflow, type workflow, sub-workflow, trait, trait addition, extension point, phase module, main workflow core, product type, sub-type, replace, set, add, open list, workflow check, workflow name, sub-workflow name, compaction-survival list; and its existing "Phase" entry lists all eight template values (intake, design, mockups, planning, configuration, building, done, changing); `test_glossary_terms.py` (names R-028) asserts each has a definition.

The sources the definitions must agree with: the plan's term table (Documents/Claude-Cursor Bridge Restructuring Plan.md, section 1, outside the Workspace: not needed, its terms are restated in the core), the core's "Main and conditional workflows" section (bridge/commands/supervisor.md), the status template's Phase line (supervisor.md, "Project state"), workflow/open-list.md and workflow/extension-points.md. Check each definition against them: a definition that contradicts the core or the open list is a defect.

## Round 2: what changed since round 1's reviewed head (9500879)
Round 1: Review A REJECT (3/2/5), Review B REJECT (2/2/0), four items converging; the disposition is in docs/DESIGN_CRITIQUE.md, "TASK-009 round 1 — disposition". `run/review/DELTA-TASK-009b.diff` (`git diff 9500879 HEAD`, review files left out) shows exactly what changed:
- d43f7df — round 1's review files removed.
- e20cded — Glossary.md: Sub-workflow name (named for the kind of product), Open list (only types and sub-types carry default traits and workflow names), Phase (points to phase modules; no second sense), Phase module (a registry-listed procedure file selected by the phase's value), Main workflow core (the non-phase sections of supervisor.md), Extension point (add or set; a replacement targets a whole module), Sub-type (a narrower kind), Add/Replace/Set (scoped as kinds of change), Compaction-survival list (no claim about the hook). Tests: the own-term check compares the term's full length of words; the Phase entry's list must equal the template's eight values in order, and the template its order; the no-bytecode test runs inventory-check on a malformed line and requires the malformed line. Manifest regenerated.
- cbc21d8 — records: round 1's grades and disposition.
Probes: a multi-word tautology, a ninth phase value and a reordered list each fail the glossary test; the TASK-008 driver's 35 mutants are all killed, its check-not-run mutant now also running the no-bytecode test.

## The supervisor's tests
- `tests/test_glossary_terms.py` — enforces docs/REQUIREMENTS.md R-028 and the plan's Done-when: each of the 18 terms is a table row of its own, defined exactly once, with a definition of at least eight words that does not open with the term; the Phase entry's first sentence lists all eight values; the eight values equal the status template's Phase line. 19 of its 21 tests fail against origin/main's glossary.

## Also on this branch: TASK-008's follow-ups (merged PR #24's review, round 2)
- `tests/test_workflows_line_check.py` — Review A's five round-2 items, all in the supervisor's tests: the no-bytecode test drops PYTHONPYCACHEPREFIX, checks each run judged the line and carries a positive control; a check that exits after a successful load is a not-loadable case in both programs; the no-escape-field cause names AttributeError; the symlink test fails on a crash; `test_r015_the_bytecode_switch_is_restored` calls judge_workflows_line in-process. Enforces R-015 and handoff/TASK-008-r2.md R2-1, R2-3, R2-4. The supervisor's mutation driver (run/supervisor/mutate_workflows_line.py, not in the diff) now holds 35 mutants, all killed.
- `docs/DESIGN_CRITIQUE.md` — TASK-008 round 2's grades and disposition.

## Expected record files in the diff
- `docs/REQUIREMENTS.md` (R-028 built), `docs/INVENTORY.md` (the feature row), `docs/PROJECT_STATUS.md`, `docs/DESIGN_CRITIQUE.md`
- `bridge/cursor-bridge/MANIFEST.json` (regenerated: Glossary.md's hash and the stamp)
- `run/review/` (these review files)

Test results at the head: the two test files 63 passed, 2 skipped (the symlink tests, WinError 1314; run on CI's ubuntu leg); full suite 1140 passed, 23 skipped; bridge-check --sources SOURCES MATCH; secret-sentinel CLEAR (round 1; round 2 changes only the glossary text and the two test files).
