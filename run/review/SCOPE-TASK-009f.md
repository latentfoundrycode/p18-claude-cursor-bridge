# SCOPE-TASK-009f — the glossary gains the plan's terms (PR #25), review round 6

The diff is `run/review/REVIEW-TASK-009f.diff` (`git diff bcd3bb4...HEAD`, bcd3bb4 being origin/main, TASK-008's merge). TASK-009 is supervisor-authored governance text (docs/BUILD_PLAN.md: "Author: supervisor"), so there is no builder brief and no builder report; the increment is defined by the build plan, quoted:

## The increment (quoted from docs/BUILD_PLAN.md)
- Scope: bridge/cursor-bridge/Glossary.md; bridge/cursor-bridge/MANIFEST.json; tests/test_glossary_terms.py
- Satisfies: R-028 (the glossary gains the terms of this plan)
- Done when: the glossary defines the closed set — conditional workflow, type workflow, sub-workflow, trait, trait addition, extension point, phase module, main workflow core, product type, sub-type, replace, set, add, open list, workflow check, workflow name, sub-workflow name, compaction-survival list; and its existing "Phase" entry lists all eight template values (intake, design, mockups, planning, configuration, building, done, changing); `test_glossary_terms.py` (names R-028) asserts each has a definition.

The sources the definitions must agree with: the plan's term table (Documents/Claude-Cursor Bridge Restructuring Plan.md, section 1, outside the Workspace: not needed, its terms are restated in the core), the core's "Main and conditional workflows" section (bridge/commands/supervisor.md), the status template's Phase line (supervisor.md, "Project state"), workflow/open-list.md and workflow/extension-points.md. Check each definition against them: a definition that contradicts the core or the open list is a defect.

## Round 6: what changed since round 5's reviewed head (aa3dec1)
Round 5: Review A APPROVE (0/1/2), Review B REJECT (1/0/0), converging on the status file's Terms fixed sense of extension point ("a conditional workflow may add or set"); the disposition is in docs/DESIGN_CRITIQUE.md, "TASK-009 round 5 — disposition". `run/review/DELTA-TASK-009f.diff` (`git diff aa3dec1 HEAD`, review files left out) shows exactly what changed. The rule (round 5's section below) is now checked over the glossary section and the Terms fixed line of docs/PROJECT_STATUS.md before each commit.
- round 5's review files removed.
- Glossary.md: Conditional workflow, Type workflow and Sub-workflow qualify setting with "where a point accepts it", as Extension point and Set do. Manifest regenerated.
- records: round 5's disposition; Terms fixed's extension point now says any type, sub-type or trait file may add and only a type or sub-type file may set, where the point allows; the HARDENING lead names open-list.md's "adds, replaces or sets at each"; the round 3 disposition's first wording restored, with a correction note beside it (Review A's note on the after-the-fact edit).
Tests at the head: test_glossary_terms, test_text_consistency and test_workflows_line_check 74 passed, 2 skipped; bridge-check SOURCES MATCH.

## Round 5: what changed since round 4's reviewed head (4fbcc49)
Round 4: Review A REJECT (1/1/3), Review B REJECT (1/0/0), converging on the status file's Terms fixed; the disposition is in docs/DESIGN_CRITIQUE.md, "TASK-009 round 4 — disposition". `run/review/DELTA-TASK-009e.diff` (`git diff 4fbcc49 HEAD`, review files left out) shows exactly what changed.

**The rule every entry about who may change what is written from** (supervisor.md "Main and conditional workflows": "Only type workflows and sub-workflows may replace or set; trait additions may only add"; extension-points.md "How a conditional workflow names a point"): any conditional workflow adds at extension points; only a type workflow or a sub-workflow also sets, at a point whose Changes cell includes set, or replaces a whole phase module the registry marks replaceable; a trait addition only adds. Check every entry of the section against it: Main workflow core, Extension point, Conditional workflow, Type workflow, Sub-workflow, Trait addition, Add, Replace, Set.

- round 4's review files removed.
- Glossary.md: Extension point (any conditional workflow adds; a type workflow or sub-workflow may set where the point accepts it), Conditional workflow (adds at extension points; a type workflow or sub-workflow also sets or replaces), Sub-workflow (adds and sets, may replace a module the registry marks replaceable, overriding its type's replacement or setting), Set (at a point that accepts it). tests/test_glossary_terms.py: curly quotes join the own-term strip (probed). Manifest regenerated.
- records: round 4's disposition; docs/PROJECT_STATUS.md Terms fixed: conditional workflow realigned with the rule and marked Risky; the HARDENING lead names the core's layer-table Type workflow row and inheritance sentence; the round 3 disposition's paraphrase corrected.
Tests at the head: test_glossary_terms, test_text_consistency and test_workflows_line_check 74 passed, 2 skipped (the symlink tests); bridge-check SOURCES MATCH.

## Round 4: what changed since round 3's reviewed head (12860f2)
Round 3: Review A APPROVE (0/0/3), Review B REJECT (1/0/0); the disposition is in docs/DESIGN_CRITIQUE.md, "TASK-009 round 3 — disposition". `run/review/DELTA-TASK-009d.diff` (`git diff 12860f2 HEAD`, review files left out) shows exactly what changed:
- round 3's review files removed.
- Glossary.md: Conditional workflow, Type workflow and Sub-workflow say a conditional workflow adds and sets at extension points and, for a type workflow or sub-workflow, may replace a whole phase module the registry marks replaceable (no longer "every change at extension points", which contradicted the Extension point entry and extension-points.md's naming rule). tests/test_glossary_terms.py: the own-term check also strips quotes (a quoted tautology fails, probed). Manifest regenerated.
- records: round 3's grades and disposition; the two revised Terms fixed entries marked Risky; the HARDENING lead widened to the core's "only at the extension points" sentence and the glossary's "the interface phase".
Tests at the head: the glossary-reading test files (test_glossary_terms, test_text_consistency) 32 passed; test_workflows_line_check unchanged since round 2 (with test_glossary_terms, 63 passed, 2 skipped); bridge-check SOURCES MATCH; round 3's full suite 1140 passed, 23 skipped, and round 4 changes only glossary text and one character of the glossary test.

## Round 3: what changed since round 2's reviewed head (3109504)
Round 2: Review A REJECT (1/1/3), Review B APPROVE (0/1/0); the disposition is in docs/DESIGN_CRITIQUE.md, "TASK-009 round 2 — disposition". `run/review/DELTA-TASK-009c.diff` (`git diff 3109504 HEAD`, review files left out) shows exactly what changed:
- 8b24cd2 — round 2's review files removed.
- 8c2a4f7 — Glossary.md: the Phase module entry no longer counts modules per phase (it contradicted TASK-015's table); several phases take more than one, as the session-start hook's table maps them; project end is today part of the Reflection points section; the core is the sections other than those that are phase modules. tests/test_glossary_terms.py: the own-term check strips Markdown emphasis and code marks (a bold-wrapped tautology fails, probed). Manifest regenerated.
- a39465b — records: round 2's grades and disposition; the status file's Terms fixed senses of phase module and extension point realigned with the glossary; a HARDENING lead for TASK-010 and TASK-014 (extension-points.md's Phase column and two sentences of the core use "phase" in the module sense; those increments rewrite them).
Tests at the head: the two test files 63 passed, 2 skipped (the symlink tests); full suite 1140 passed, 23 skipped; bridge-check SOURCES MATCH.

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
- `docs/REQUIREMENTS.md` (R-028 built), `docs/INVENTORY.md` (the feature row), `docs/PROJECT_STATUS.md`, `docs/DESIGN_CRITIQUE.md`, `docs/HARDENING.md` (the lead for TASK-010 and TASK-014)
- `bridge/cursor-bridge/MANIFEST.json` (regenerated: Glossary.md's hash and the stamp)
- `run/review/` (these review files)

Test results at the head: the two test files 63 passed, 2 skipped (the symlink tests, WinError 1314; run on CI's ubuntu leg); full suite 1140 passed, 23 skipped; bridge-check --sources SOURCES MATCH; secret-sentinel CLEAR (round 1; round 2 changes only the glossary text and the two test files).
