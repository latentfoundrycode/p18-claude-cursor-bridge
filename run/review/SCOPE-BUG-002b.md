# SCOPE-BUG-002b — BUG-002 round 2 (PR #27)

The whole diff is `run/review/REVIEW-BUG-002b.diff` (`git diff origin/main...HEAD`, base 9bb26e0). What changed since round 1's reviewed head 7327ef4 is `run/review/DELTA-BUG-002b.diff` (`git diff 7327ef4 HEAD`, run/review excluded); read the delta first, then the whole.

## Round 1's outcome
Review A APPROVE (0 blocking, 0 should fix, 6 considers), Review B APPROVE (0/0/0), security auditor PASS. Two of them, Review A and the security auditor, named the same leftover independently: `traits_in_head` in `check_head` (workflow-check.py:607, :618) was filled and never read after round 1's exact comparison. Converged, so blocking: round 2.

## The builder's part (handoff/BUG-002.md, revised in place for round 2; report handoff/BUG-002-r2-report.md)
Scope: bridge/cursor-bridge/workflow-check.py (only the name loop of `check_head`), MANIFEST.json (regenerated), docs/BUILDER_NOTES.md, the report. Out of scope: every test, fixture and text; every other line of workflow-check.py. The change: the list is gone; the trait branch stays in effect as `elif name not in tables["trait_by_name"]:` before the `unknown` finding. Behaviour-preserving: every finding keeps its code, name, reason and order. The builder's `Assumed, not verified` list: none.

## The supervisor's part (commit 8e23d2a, before the checkpoint 49e6834) — Review A's considers taken
- tests/test_workflow_check.py: `test_r015_separators_are_exact` now requires the shape finding's own reason ("Workflows head is not the product type, then at most its sub-type"), not any `FAIL (form)` line (enforces supervisor.md "Project state", R-015); the docstring of `test_r014_link_under_an_unknown_type_folder_is_form` says the check reads no file under an unknown type folder (it does walk it).
- bridge/cursor-bridge/workflow/open-list.md line 3: the empty "until then" dropped; MANIFEST.json regenerated.
- docs/BUILD_PLAN.md: TASK-004's Done when carries a dated note that no default-traits check exists yet (routed to TASK-019 in docs/HARDENING.md).
- Not taken here: Review A's sixth consider (the per-part lead also in the Restructuring Plan's §16) is a Documents/ write, made at stage B2's reflection point.

Checks on HEAD: scope-check SCOPE CLEAN from 49e6834; suite 1151 passed, 23 skipped (the three skips in the increment's files are environmental: a non-root POSIX user, a symlink privilege; they run on CI's Linux leg); the supervisor's mutation driver (run/supervisor/mutate_workflow_check.py, temporary copies) 81 of 81 killed; secret-sentinel CLEAR; bridge-check SOURCES MATCH.

## Round 1's scope, for reference (unchanged)

# SCOPE-BUG-002 — stage B2's review fixes (PR #27)

The diff is `run/review/REVIEW-BUG-002.diff` (`git diff origin/main...HEAD`, base 9bb26e0). Stage B2's review, round 1 (2026-10-17), rejected: Review B (one blocking item) and Review A's tests part (two blocking items); Review A's texts, programs and fixtures parts approved with should-fix items, two of which converged across parts (so blocking). Every finding and how it was taken is in the commit messages and in docs/HARDENING.md, "Stage B2 — the stage review (round 1, 2026-10-17)".

## The builder's part (handoff/BUG-002.md; report handoff/BUG-002-r1-report.md)
Scope: bridge/cursor-bridge/workflow-check.py (`check_head` only), MANIFEST.json (regenerated), docs/BUILDER_NOTES.md, the report. Out of scope: every test and fixture, every text, inventory-check.py and conformance-check.py.
The defect (converged, Review A's texts C4 and programs C2): `check_head` stripped each `→` segment and compared the stripped names, so `A→B`, doubled spaces around the arrow, after `Workflows: ` or `<part>: `, and a space before `; traits: ` passed, against supervisor.md's grammar ("Project state", **Workflows**). The fix: the head as written equals the type's Workflow name, or that name, ` → `, and its Sub-workflow name; anything else is the existing `form` finding. The builder's `Assumed, not verified` list: none.

## The supervisor's part (commit 2e52140, before the checkpoint 8b1aec9)
Tests (each carries the finding it answers):
- tests/test_workflow_check.py: `test_r015_separators_are_exact` (6 cases; enforces supervisor.md "Project state", R-015) failed against the checkpoint's program and passes now; `test_r015_exact_separators_pass` is its control. `test_r014_unwritten_type_fails_against_the_real_open_list` runs on a copy of the real open list with every flag `no` (it read the live list, which TASK-021 changes; blocking). `test_r014_missing_layer_folder_is_not_a_link` and `test_r014_missing_layer_is_skipped_before_the_link_test` use roots built in the test (they read the live workflow folder, which TASK-017 changes; blocking). The BOM, trailing-space and tab fixtures assert their bytes (`test_r014_bom_fixtures_carry_their_bom`, two preconditions); the BOM status fixture is renamed `bom-workflows-line.md` (no `Phase:` line, so not a whole status file); the column-0 fence pair is asserted; the vacuous "not read" clause of the unknown-folder link test is dropped.
- tests/test_extension_points.py: the new heading form and set-value sentence pinned; the replacement sentence re-pinned; the CI route, the inspect step's members and the placement sentence pinned (HARDENING's carry from TASK-005 round 6); `test_r006_the_checks_delivery_kinds_are_the_registrys` ties DELIVERY_KINDS to the registry's list.
- tests/test_open_list.py: the default-traits sentence re-pinned (and the old claim refused); "filled, including" and the supervisor's not changing the list pinned; the stale comment corrected (HARDENING's carry from TASK-004 round 3).
Texts: extension-points.md (the `## Add at project-end.delivery for <delivery kind>` form, required there and refused elsewhere; a set value is the section's first non-blank line; a replaced module keeps every conditional workflow's additions, in the core's order); open-list.md (no default-traits check exists yet; the form and its check come together; a project's supervisor never changes the list); Glossary.md (Workflow check: the two programs use its grammar; the pause is the check's own). MANIFEST.json regenerated.
Mutation driver (run/supervisor/mutate_workflow_check.py, supervisor-side, temporary copies): 81 mutants, all killed, two new for BUG-002 (the head stripped before the comparison; the arrow spacing loose).

## Records (expected bookkeeping)
docs/DESIGN_CRITIQUE.md (REFAC-B2 round 2's grades and disposition), docs/HARDENING.md (the stage review's routing; the test-lane carry marked done), docs/INVENTORY.md (the jscpd row corrected), docs/PROJECT_STATUS.md, docs/BUILDER_NOTES.md, handoff/BUG-002.md and its report.

## Decided, not taken
Review B's blocking item (an omitted part's `Workflows:` line is not detected): nothing declares a project's parts besides the status file's own lines; several-part projects are the Restructuring Plan's §7 (product aggregates), a later release that gives parts a declaration. Recorded as that release's lead in HARDENING. Design for later stages and releases is not this diff's defect.
