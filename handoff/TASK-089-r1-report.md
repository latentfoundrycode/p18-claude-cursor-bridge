# TASK-089 round 1 report

## One-paragraph summary

Added `PLAN_ID_PREFIXES` and composed `PLAN_ID_PATTERN` in `bridge_env.py`, replaced TASK-only merge-branch mapping with regex built from those prefixes, and updated `plan-check.py` to glob briefs for every prefix and to name all five prefixes in the DEPENDS unreadable-id message; `bridge-run.py` and `records-migrate.py` were not edited; MANIFEST was regenerated; all 67 acceptance tests in `tests/test_improve_plan_prefixes.py` pass; six regression tests in `tests/test_plan_check.py` and `tests/test_task033_supervisor.py` now disagree with expectations that assumed a TASK-only plan pattern on this repository's git history.

## Files changed

- `bridge/cursor-bridge/bridge_env.py`
- `bridge/cursor-bridge/plan-check.py`
- `bridge/cursor-bridge/MANIFEST.json` (via `python tools/make-manifest.py`)

## Requirements 1–7

1. `PLAN_ID_PREFIXES` and `PLAN_ID_PATTERN` at `bridge_env.py` lines 429–430; `HEAD_RX` line 432; `_PLAN_TASK_RX` line 439.
2. Walker `walk_plan_prose_body` line 689; `plan_increment_ids` line 996; `plan_header_inc_ids` line 3838; merge readers `_PLAN_BRANCH_RX`/`_PLAN_MERGE_RX`/`_cand_from_plan_branch`/`_branch_name_to_id`/`_plan_merge_id` lines 1163–1292; `_is_plan_id_rx` line 1255; header `parent`/`depends_on` via `_PLAN_TASK_RX.findall` in `_plan_normalize_field` lines 3684–3691.
3. `plan-check.py` brief loop lines 386–396; DEPENDS message lines 273–274; module docstring lines 8–14 updated for five prefixes; `ID` line 66 from `bridge_env.PLAN_ID_PATTERN`.
4. All increment readers use shared `PLAN_ID_PATTERN`/`HEAD_RX` as above; non-increments still refused by pattern.
5. `plan-check.py` lines 383–384 intersect merged git ids with plan increments only; `records-migrate` unchanged, uses `squash_merged_ids(..., PLAN_ID_PATTERN)`.
6. No scope creep; `records-check.py` and `permission-guard.py` untouched; no new dependencies or options.
7. Before-edit and after-edit outputs of `plan-check.py`, `completion-check.py --mode plan`, and `records-migrate.py --check` are identical line for line (see Requirement 7 section below).

## Search: `bridge-run.py` and `records-migrate.py`

Pattern: `TASK|task-|\\d\{3` (as brief Scope Limits suggests).

`bridge-run.py`: one match, docstring only — `run/agent/TASK-nnn.err` at line 78 (not a plan-id reader). **Not edited.**

`records-migrate.py`: **no matches.** **Not edited.**

## Search: `tests/` (Done step 11)

Pattern: `squash_merged_ids|walk_plan_prose_body|plan_increment_ids|plan_header_inc_ids|PLAN_ID_PATTERN|HEAD_RX|plan-check|records-migrate|completion-check`.

Extra files not in Done steps 7–10 were run in one command:

```text
python -m pytest -p no:cacheprovider -q tests/test_a5_followups.py tests/test_program_stamp.py tests/test_allowlist.py tests/test_install_check.py tests/test_program_run_parameters_empty.py tests/test_release_s_records_gate.py tests/test_program_release_s_rows.py tests/test_program_launcher_forms.py tests/test_release_s_evidence.py tests/test_release_t_stamp.py tests/test_phase_modules_close.py tests/test_phase_modules_interface_planning.py tests/test_release_b_bootstrap.py tests/test_release_b2_records.py tests/test_release_b2_stamp.py tests/test_release_b2_text.py tests/test_header_currency.py tests/test_header_tables.py tests/test_a4_review_fixes.py tests/test_bug038.py tests/test_header_tables_r2.py tests/test_traits_existing.py tests/test_extension_points.py tests/test_interface_text.py tests/test_completion_check.py
814 passed, 19 skipped in 285.79s (0:04:45)
```

## Changed expectation

Six tests outside the acceptance file now fail because `squash_merged_ids` on `PLAN_ID_PATTERN` recognises BUG (and related) ids in historical commit subjects where TASK-only regression tests expected no match:

- `test_r044_iss013_subject_merges_nothing_beside_bare_parenthesis` — `AssertionError: assert {'BUG-018', 'TASK-100'} == {'TASK-100'}` (extra `BUG-018`).
- `test_r044_main_regression_minus_task031` — at `8b65173c…`, `assert {'BUG-047'} == set()`.
- `test_task033_iss013_subject_merges_nothing_under_the_plan_pattern` — (same class of divergence on plan pattern).
- `test_task033_the_three_divergences_read_as_plan_check_did[Merge pull request #1 from x/feat/task-005-expected0]`
- `test_task033_the_three_divergences_read_as_plan_check_did[Merge pull request #9 from x/feature-z (TASK-100)-expected1]`
- `test_task033_the_three_divergences_read_as_plan_check_did[Merge pull request #1 from x/task-001ab-expected2]`

Supervisor to review whether to update those tests for R-111 or narrow regression scope.

## Scratch test files

no scratch test file

## Mutation code points (M1–M8)

| Label | Function / location (after change) | Expected catching test |
|-------|-----------------------------------|-------------------------|
| M1 | `PLAN_ID_PREFIXES` tuple, lines 429–430 | `test_task089_one_tuple_of_prefixes_in_bridge_env`; dropping BUG/DEP/CONFIG/FIX caught by `test_task089_the_pattern_accepts_each_prefix[…]` and heading/walker tests per prefix |
| M2 | `PLAN_ID_PATTERN` composition line 430 (grouped alternation) | `test_task089_the_pattern_composes_inside_a_larger_pattern` |
| M3 | `_PLAN_MERGE_RX` lines 1224–1225 | `test_task089_each_merged_form_names_a_bug_increment[merge-branch]` and `[merge-pull-request]` |
| M4 | `_grammar_merge_id` / `_branch_name_to_id` / `_cand_from_plan_branch` lines 1171–1192 | `test_task089_each_merged_form_names_a_bug_increment[merge-branch]` |
| M5 | `plan-check.py` brief glob loop lines 386–388 | `test_task089_plan_check_reads_a_bug_increments_brief` |
| M6 | `HEAD_RX` line 432 (must use `PLAN_ID_PATTERN`, not literal TASK) | `test_task089_a_heading_of_each_prefix_is_read[…]` |
| M7 | `_plan_normalize_field` `depends_on` branch lines 3686–3691 (`_PLAN_TASK_RX`) | `test_task089_a_headed_plan_with_a_bug_increment_agrees` |
| M8 | `bridge-run.py` merge-unit check lines 1533–1549 | `test_task089_a_merge_unit_may_name_an_increment_of_each_prefix[…]` |

## Commands and output

### Step 1 — `git status --short` (before edits)

```text

```

### Step 2 — acceptance tests before edits

```text
python -m pytest -p no:cacheprovider -q tests/test_improve_plan_prefixes.py
34 failed, 33 passed in 11.58s
```

Failing ids (34): `test_task089_one_tuple_of_prefixes_in_bridge_env`, `test_task089_the_plan_id_pattern_is_the_explicit_alternation_of_the_tuple`, `test_task089_the_pattern_accepts_each_prefix[BUG-001]`, `[DEP-002]`, `[CONFIG-003]`, `[FIX-004]`, `[FIX-1234b]`, `test_task089_the_pattern_composes_inside_a_larger_pattern`, `test_task089_a_heading_of_each_prefix_is_read[BUG]`, `[DEP]`, `[CONFIG]`, `[FIX]`, `test_task089_no_task_only_pattern_stands_in_the_program[bridge_env.py]`, `[plan-check.py]`, `test_task089_the_walker_reads_each_prefix_and_no_other_heading`, `test_task089_plan_increment_ids_reads_each_prefix`, `test_task089_plan_check_reads_each_prefix_as_an_increment`, `test_task089_a_subject_counts_as_merged_only_where_the_plan_holds_its_heading`, four `test_task089_each_merged_form_names_a_bug_increment[…]`, `test_task089_a_headed_plan_with_a_bug_increment_agrees`, `test_task089_plan_check_reads_a_bug_increments_brief`, four `test_task089_the_completion_check_reads_satisfies_under_each_prefix[…]`, `test_task089_records_migrate_writes_a_bug_increment_into_the_header`, four `test_task089_a_merge_unit_may_name_an_increment_of_each_prefix[…]`, `test_task089_a_bug_brief_naming_its_unit_runs_on_its_branch`.

### Step 3 — repository reads before edits

`python bridge/cursor-bridge/plan-check.py` (exit 0):

```text
note: 126 increments in 1 file(s); 92 merged, 0 deferred
note: large increment: TASK-092 has 20 acceptance item(s) in its Done when and 20 Scope path(s); above 12 of either an increment tends to need more rounds than the ceiling gives: consider splitting it before its first brief (a note, never a failure)
note: large increment: TASK-094 has 14 acceptance item(s) in its Done when and 10 Scope path(s); above 12 of either an increment tends to need more rounds than the ceiling gives: consider splitting it before its first brief (a note, never a failure)
note: large increment: TASK-095 has 13 acceptance item(s) in its Done when and 9 Scope path(s); above 12 of either an increment tends to need more rounds than the ceiling gives: consider splitting it before its first brief (a note, never a failure)
note: large increment: TASK-096 has 12 acceptance item(s) in its Done when and 16 Scope path(s); above 12 of either an increment tends to need more rounds than the ceiling gives: consider splitting it before its first brief (a note, never a failure)
note: large increment: TASK-097a has 13 acceptance item(s) in its Done when and 8 Scope path(s); above 12 of either an increment tends to need more rounds than the ceiling gives: consider splitting it before its first brief (a note, never a failure)
note: large increment: TASK-097b has 13 acceptance item(s) in its Done when and 7 Scope path(s); above 12 of either an increment tends to need more rounds than the ceiling gives: consider splitting it before its first brief (a note, never a failure)
note: large increment: TASK-098 has 14 acceptance item(s) in its Done when and 9 Scope path(s); above 12 of either an increment tends to need more rounds than the ceiling gives: consider splitting it before its first brief (a note, never a failure)
note: large increment: TASK-100a has 21 acceptance item(s) in its Done when and 10 Scope path(s); above 12 of either an increment tends to need more rounds than the ceiling gives: consider splitting it before its first brief (a note, never a failure)
note: large increment: TASK-100b has 14 acceptance item(s) in its Done when and 7 Scope path(s); above 12 of either an increment tends to need more rounds than the ceiling gives: consider splitting it before its first brief (a note, never a failure)
note: large increment: TASK-103 has 13 acceptance item(s) in its Done when and 8 Scope path(s); above 12 of either an increment tends to need more rounds than the ceiling gives: consider splitting it before its first brief (a note, never a failure)
note: large increment: TASK-105 has 13 acceptance item(s) in its Done when and 12 Scope path(s); above 12 of either an increment tends to need more rounds than the ceiling gives: consider splitting it before its first brief (a note, never a failure)
note: large increment: TASK-106 has 15 acceptance item(s) in its Done when and 12 Scope path(s); above 12 of either an increment tends to need more rounds than the ceiling gives: consider splitting it before its first brief (a note, never a failure)
note: large increment: TASK-107 has 13 acceptance item(s) in its Done when and 10 Scope path(s); above 12 of either an increment tends to need more rounds than the ceiling gives: consider splitting it before its first brief (a note, never a failure)
note: large increment: TASK-108 has 16 acceptance item(s) in its Done when and 7 Scope path(s); above 12 of either an increment tends to need more rounds than the ceiling gives: consider splitting it before its first brief (a note, never a failure)
note: large increment: TASK-110a has 25 acceptance item(s) in its Done when and 8 Scope path(s); above 12 of either an increment tends to need more rounds than the ceiling gives: consider splitting it before its first brief (a note, never a failure)
note: large increment: TASK-110b has 14 acceptance item(s) in its Done when and 10 Scope path(s); above 12 of either an increment tends to need more rounds than the ceiling gives: consider splitting it before its first brief (a note, never a failure)
note: large increment: TASK-113 has 14 acceptance item(s) in its Done when and 11 Scope path(s); above 12 of either an increment tends to need more rounds than the ceiling gives: consider splitting it before its first brief (a note, never a failure)
note: large increment: TASK-114 has 19 acceptance item(s) in its Done when and 8 Scope path(s); above 12 of either an increment tends to need more rounds than the ceiling gives: consider splitting it before its first brief (a note, never a failure)
note: large increment: TASK-115 has 19 acceptance item(s) in its Done when and 17 Scope path(s); above 12 of either an increment tends to need more rounds than the ceiling gives: consider splitting it before its first brief (a note, never a failure)
note: large increment: TASK-116 has 18 acceptance item(s) in its Done when and 21 Scope path(s); above 12 of either an increment tends to need more rounds than the ceiling gives: consider splitting it before its first brief (a note, never a failure)
note: large increment: TASK-118 has 39 acceptance item(s) in its Done when and 8 Scope path(s); above 12 of either an increment tends to need more rounds than the ceiling gives: consider splitting it before its first brief (a note, never a failure)
READY: TASK-089  Plan headings take the bridge's other increment prefixes (R-  [bridge/cursor-bridge/bridge_env.py, bridge/cursor-bridge/plan-check.py]
RESULT: OK
```

`python bridge/cursor-bridge/completion-check.py --mode plan` (exit 0):

```text
note: mode plan; requirements: 107 built, 30 planned
note: shipped code: 0 TODO/FIXME/XXX/HACK markers, 4 NotImplementedError sites (review, not a failure)
RESULT: OK
```

`python bridge/cursor-bridge/records-migrate.py --check` (exit 0): full output is 200+ `has a header …` / `cannot read …` lines identical before and after; no differing lines.

### Steps 4–6

```text
python tools/dump-cli.py
(no stdout)
python tools/dump-cli.py --check
(exit 0, no stdout)
python tools/make-manifest.py
make-manifest: version 2026.11.24a, 148 files hashed, VERSION + MANIFEST.json written
git status --short
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/bridge_env.py
 M bridge/cursor-bridge/plan-check.py
```

`bridge/cursor-bridge/VERSION` was not listed; `git restore` not run. `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` unchanged (not in `git status --short`).

### Step 7

```text
python -m pytest -p no:cacheprovider -q tests/test_improve_plan_prefixes.py
67 passed in 11.54s
```

### Step 8

```text
python -m pytest -p no:cacheprovider -q tests/test_header_plan.py tests/test_header_plan_r2.py tests/test_header_plan_r3.py tests/test_plan_check.py
2 failed, 112 passed in 52.40s
```

### Step 9

```text
python -m pytest -p no:cacheprovider -q tests/test_task032_supervisor_launcher.py tests/test_task033_supervisor.py tests/test_task033_supervisor_r2.py tests/test_program_merge_unit_one.py
4 failed, 281 passed in 145.59s (0:02:25)
```

### Step 10

```text
python -m pytest -p no:cacheprovider -q tests/test_records_migrate.py tests/test_program_own_records.py tests/test_pace_report.py tests/test_bug044.py tests/test_release_s_plan_size.py tests/test_plan_demonstration.py tests/test_dump_cli.py tests/test_header_reader.py tests/test_improve_satisfies_reader.py
1075 passed, 1 skipped in 177.09s (0:02:57)
```

### Step 12 — repository reads after edits

Compared to step 3: **no differing lines** for `plan-check.py` (24 content lines, exit 0), `completion-check.py --mode plan` (3 content lines, exit 0), and `records-migrate.py --check` (exit 0, same header listing).

### Steps 13–17

```text
python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet
RESULT: SOURCES MATCH bridge 2026.11.24a <Workspace>/bridge/cursor-bridge
python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks
windowless-check: 41 file(s) scanned, 0 FAIL, 0 NOTE
python -c "[open(p,'rb').read().decode('ascii') for p in ('bridge/cursor-bridge/bridge_env.py','bridge/cursor-bridge/bridge-run.py')]; print('ascii ok')"
ascii ok
git diff --stat HEAD
 bridge/cursor-bridge/MANIFEST.json |  6 +++---
 bridge/cursor-bridge/bridge_env.py | 42 ++++++++++++++++++++++----------------
 bridge/cursor-bridge/plan-check.py | 15 +++++++++-----
 3 files changed, 37 insertions(+), 26 deletions(-)
git rev-parse HEAD
e96c50f4f915f67f6bf02836b9b22892de9410f1
git status --short
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/bridge_env.py
 M bridge/cursor-bridge/plan-check.py
```

## Assumed, not verified

Assumed, not verified: none.