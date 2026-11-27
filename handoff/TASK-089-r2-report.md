# TASK-089 round 2 report

## One-paragraph summary

Round 2 adds a left-letter-or-digit boundary for plan-id extraction (`_PLAN_ID_WORD_RX` and `plan_ids_in_text` in `bridge_env.py`, used from `_plan_normalize_field` and from `plan-check.py` `ids_in` / `unreadable`) so values like `HOTFIX-004` do not yield inner `FIX-004` ids, and adds grammar-style branch mapping step `_cand_from_prefix_rest` in `_branch_name_to_id` so each plan prefix keeps the suffix letter case (`task-03x` → `TASK-03x`, `task-12-fix` → `TASK-12-fix`). All 91 acceptance tests pass; `bridge-run.py` and `records-migrate.py` unchanged; MANIFEST regenerated; the three repository reads are unchanged line for line.

## Files changed

- `bridge/cursor-bridge/bridge_env.py`
- `bridge/cursor-bridge/plan-check.py`
- `bridge/cursor-bridge/MANIFEST.json` (via `python tools/make-manifest.py`)

## Requirements R1–R4

R1. `PLAN_ID_PATTERN` unchanged at lines 429–430; `_PLAN_ID_WORD_RX` line 440 and `plan_ids_in_text` lines 443–445; `_plan_normalize_field` parent/depends_on at lines 3707–3714 use `plan_ids_in_text`; `plan-check.py` `ids_in` line 77 and `unreadable` line 132 use the shared word-boundary regex from `bridge_env`.

R2. `_cand_from_prefix_rest` lines 1187–1194; `_branch_name_to_id` lines 1197–1213 tries digit-prefix match, then rest-as-written, then prior fallbacks; plan-style `_cand_from_plan_branch` unchanged.

R3. Repository reads quoted below (steps 3 and 12); each before/after pair identical.

R4. See section `Assumed, not verified`.

## Search: `bridge-run.py` and `records-migrate.py`

Pattern: `TASK|task-|\\d\{3`.

`bridge-run.py`: one match, docstring only — `run/agent/TASK-nnn.err` at line 78. **Not edited.**

`records-migrate.py`: **no matches.** **Not edited.**

## Changed expectation

no changed expectation

## Scratch test files

no scratch test file

## Mutation code points (M1–M8, round 1 labels)

| Label | Function / location (after change) | Expected catching test |
|-------|-----------------------------------|-------------------------|
| M1 | `PLAN_ID_PREFIXES` lines 429–430 | `test_task089_one_tuple_of_prefixes_in_bridge_env` |
| M2 | `PLAN_ID_PATTERN` line 430 | `test_task089_the_pattern_composes_inside_a_larger_pattern` |
| M3 | `_PLAN_MERGE_RX` lines 1244–1245 | `test_task089_each_merged_form_names_a_bug_increment[merge-branch]` |
| M4 | `_cand_from_prefix_rest` / `_branch_name_to_id` lines 1187–1213 | `test_task089_r2_the_grammar_style_maps_a_branch_of_each_prefix_as_task[task-03x]` |
| M5 | `plan-check.py` brief loop lines 386–388 | `test_task089_plan_check_reads_a_bug_increments_brief` |
| M6 | `HEAD_RX` line 432 | `test_task089_a_heading_of_each_prefix_is_read[BUG]` |
| M7 | `_plan_normalize_field` depends_on lines 3709–3714 | `test_task089_r2_the_headers_field_reading_keeps_a_longer_word_whole[task-and-hotfix]` |
| M8 | `bridge-run.py` merge-unit check lines 1533–1549 | `test_task089_a_merge_unit_may_name_an_increment_of_each_prefix[BUG]` |

## Mutation code points (N1–N5, round 2 labels)

| Label | Function / location (after change) | Expected catching test |
|-------|-----------------------------------|-------------------------|
| N1 | `_plan_normalize_field` reverts to `_PLAN_TASK_RX.findall` lines 3707–3714 | `test_task089_r2_the_headers_field_reading_keeps_a_longer_word_whole[task-and-hotfix]` |
| N2 | `plan-check.py` `ids_in` line 77 uses `ID_RX.findall` | `test_task089_r2_an_id_inside_a_longer_word_is_read_whole_by_plan_check` |
| N3 | `plan-check.py` `unreadable` line 132 uses `ID_RX.sub` | `test_task089_r2_an_id_inside_a_longer_word_is_read_whole_by_plan_check` |
| N4 | remove `_cand_from_prefix_rest` call in `_branch_name_to_id` lines 1202–1204 | `test_task089_r2_the_grammar_style_maps_a_branch_of_each_prefix_as_task[task-03x]` |
| N5 | call `_cand_from_prefix_rest` before `_cand_from_plan_branch` in `_branch_name_to_id` | `test_task089_r2_the_grammar_style_maps_a_branch_of_each_prefix_as_task[bug-001-x]` |

## Commands and output

### Step 1 — `git status --short` (before edits)

```text

```

### Step 2 — acceptance tests before edits

```text
python -m pytest -p no:cacheprovider -q tests/test_improve_plan_prefixes.py
8 failed, 83 passed in 11.38s
```

Failing ids: `test_task089_r2_an_id_inside_a_longer_word_is_read_whole_by_plan_check`, `test_task089_r2_the_headers_field_reading_keeps_a_longer_word_whole[hotfix]`, `[task-and-hotfix]`, `[subtask]`, `[debug-parent]`, `test_task089_r2_the_grammar_style_maps_a_branch_of_each_prefix_as_task[task-03x]`, `[task-12-fix]`, `[bug-12-fix]`.

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

`python bridge/cursor-bridge/records-migrate.py --check` (exit 0): output listed in step 12 (identical before and after).

### Steps 4–6 (after edits)

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

`bridge/cursor-bridge/VERSION` was not listed; `git restore` not run.

### Step 7

```text
python -m pytest -p no:cacheprovider -q tests/test_improve_plan_prefixes.py
91 passed in 13.88s
```

### Step 8

```text
python -m pytest -p no:cacheprovider -q tests/test_header_plan.py tests/test_header_plan_r2.py tests/test_header_plan_r3.py tests/test_plan_check.py
114 passed in 56.29s
```

### Step 9

```text
python -m pytest -p no:cacheprovider -q tests/test_task032_supervisor_launcher.py tests/test_task033_supervisor.py tests/test_task033_supervisor_r2.py tests/test_program_merge_unit_one.py
285 passed in 146.94s (0:02:26)
```

### Step 10

```text
python -m pytest -p no:cacheprovider -q tests/test_records_migrate.py tests/test_program_own_records.py tests/test_pace_report.py tests/test_bug044.py tests/test_release_s_plan_size.py tests/test_plan_demonstration.py tests/test_dump_cli.py tests/test_header_reader.py tests/test_improve_satisfies_reader.py
1075 passed, 1 skipped in 187.72s (0:03:07)
```

### Step 11 — search and extra tests

Search pattern: `squash_merged_ids|walk_plan_prose_body|plan_increment_ids|plan_header_inc_ids|PLAN_ID_PATTERN|HEAD_RX|plan-check|records-migrate|completion-check`.

```text
python -m pytest -p no:cacheprovider -q tests/test_a5_followups.py tests/test_program_stamp.py tests/test_allowlist.py tests/test_install_check.py tests/test_program_run_parameters_empty.py tests/test_release_s_records_gate.py tests/test_program_release_s_rows.py tests/test_program_launcher_forms.py tests/test_release_s_evidence.py tests/test_release_t_stamp.py tests/test_phase_modules_close.py tests/test_phase_modules_interface_planning.py tests/test_release_b_bootstrap.py tests/test_release_b2_records.py tests/test_release_b2_stamp.py tests/test_release_b2_text.py tests/test_header_currency.py tests/test_header_tables.py tests/test_a4_review_fixes.py tests/test_bug038.py tests/test_header_tables_r2.py tests/test_traits_existing.py tests/test_extension_points.py tests/test_interface_text.py tests/test_completion_check.py tests/test_task033_supervisor_r3.py
882 passed, 19 skipped in 307.35s (0:05:07)
```

### Step 12 — repository reads after edits (R3)

Before vs after: compared checkpoint-tree output to post-change output with `diff` on all three commands; **no differing lines** for any of the three.

`python bridge/cursor-bridge/plan-check.py` after edits — identical to step 3 block above (exit 0).

`python bridge/cursor-bridge/completion-check.py --mode plan` after edits — identical to step 3 block above (exit 0).

`python bridge/cursor-bridge/records-migrate.py --check` before and after (exit 0, 244 lines, **identical**):

```text
has a header docs/PROJECT_STATUS.md
has a header docs/BUILD_PLAN.md
has a header handoff/BUG-001.md
has a header handoff/BUG-002.md
has a header handoff/BUG-003.md
has a header handoff/BUG-010.md
has a header handoff/BUG-020.md
has a header handoff/BUG-029.md
has a header handoff/BUG-030-r2.md
has a header handoff/BUG-030-r3.md
has a header handoff/BUG-030.md
has a header handoff/BUG-032-r2.md
has a header handoff/BUG-032-r3.md
has a header handoff/BUG-032-r4.md
has a header handoff/BUG-032.md
has a header handoff/BUG-034-r2.md
has a header handoff/BUG-034.md
has a header handoff/BUG-036.md
has a header handoff/BUG-038-r2.md
has a header handoff/BUG-038-r3.md
has a header handoff/BUG-038.md
has a header handoff/BUG-041.md
has a header handoff/BUG-042-r2.md
has a header handoff/BUG-042.md
has a header handoff/BUG-044.md
has a header handoff/BUG-045-r2.md
has a header handoff/BUG-045-r3.md
has a header handoff/BUG-045-r4.md
has a header handoff/BUG-045.md
has a header handoff/BUG-046-r2.md
has a header handoff/BUG-046-r3.md
has a header handoff/BUG-046.md
has a header handoff/CONFIG-B3b-r2.md
has a header handoff/CONFIG-B3b-r3.md
has a header handoff/CONFIG-B3b-r4.md
has a header handoff/CONFIG-B3b.md
has a header handoff/FIX-003-r2.md
has a header handoff/FIX-003.md
has a header handoff/HOTFIX-001.md
has a header handoff/HOTFIX-002-r2.md
has a header handoff/HOTFIX-002-r3.md
has a header handoff/HOTFIX-002.md
has a header handoff/HOTFIX-004-r2.md
has a header handoff/HOTFIX-004-r3.md
has a header handoff/HOTFIX-004-r4.md
has a header handoff/HOTFIX-004.md
has a header handoff/REFAC-001.md
has a header handoff/REFAC-002.md
has a header handoff/REFAC-003.md
has a header handoff/REFAC-004.md
has a header handoff/REFAC-005.md
has a header handoff/REFAC-006.md
has a header handoff/REFAC-007.md
has a header handoff/REFAC-008.md
has a header handoff/REFAC-009.md
has a header handoff/REFAC-010.md
has a header handoff/REFAC-011.md
has a header handoff/REFAC-012.md
has a header handoff/REFAC-013.md
has a header handoff/REFAC-014.md
has a header handoff/REFAC-015.md
has a header handoff/REFAC-016.md
has a header handoff/REFAC-017.md
cannot read handoff/TASK-002-r2.md: empty
cannot read handoff/TASK-002-r3.md: empty
cannot read handoff/TASK-002-r4.md: empty
has a header handoff/TASK-002-r5.md
has a header handoff/TASK-002-r6.md
has a header handoff/TASK-002.md
has a header handoff/TASK-006-r2.md
has a header handoff/TASK-006-r3.md
has a header handoff/TASK-006-r4.md
has a header handoff/TASK-006-r5.md
has a header handoff/TASK-006-r6.md
has a header handoff/TASK-006.md
has a header handoff/TASK-008-r2.md
has a header handoff/TASK-008.md
has a header handoff/TASK-015-r2.md
has a header handoff/TASK-015-r3.md
has a header handoff/TASK-015-r4.md
has a header handoff/TASK-015-r5.md
has a header handoff/TASK-015-r6.md
has a header handoff/TASK-015-r7.md
has a header handoff/TASK-015.md
has a header handoff/TASK-016-r2.md
has a header handoff/TASK-016-r3.md
has a header handoff/TASK-016-r4.md
has a header handoff/TASK-016.md
has a header handoff/TASK-024-r2.md
has a header handoff/TASK-024.md
has a header handoff/TASK-028-r2.md
has a header handoff/TASK-028-r3.md
has a header handoff/TASK-028-r4.md
has a header handoff/TASK-028-r5.md
has a header handoff/TASK-028.md
has a header handoff/TASK-029-r2.md
has a header handoff/TASK-029-r3.md
has a header handoff/TASK-029-r4.md
has a header handoff/TASK-029.md
has a header handoff/TASK-031-r10.md
has a header handoff/TASK-031-r11.md
has a header handoff/TASK-031-r12.md
has a header handoff/TASK-031-r13.md
has a header handoff/TASK-031-r14.md
has a header handoff/TASK-031-r2.md
has a header handoff/TASK-031-r3.md
has a header handoff/TASK-031-r4.md
has a header handoff/TASK-031-r5.md
has a header handoff/TASK-031-r6.md
has a header handoff/TASK-031-r7.md
has a header handoff/TASK-031-r8.md
has a header handoff/TASK-031-r9.md
has a header handoff/TASK-031.md
has a header handoff/TASK-032-r2.md
has a header handoff/TASK-032-r3.md
has a header handoff/TASK-032-r4.md
has a header handoff/TASK-032.md
has a header handoff/TASK-033-r2.md
has a header handoff/TASK-033-r3.md
has a header handoff/TASK-033-r4.md
has a header handoff/TASK-033.md
has a header handoff/TASK-043-r2.md
has a header handoff/TASK-043-r3.md
has a header handoff/TASK-043.md
has a header handoff/TASK-046-r2.md
has a header handoff/TASK-046-r3.md
has a header handoff/TASK-046.md
has a header handoff/TASK-047-r2.md
has a header handoff/TASK-047-r3.md
has a header handoff/TASK-047-r4.md
has a header handoff/TASK-047.md
has a header handoff/TASK-048-r2.md
has a header handoff/TASK-048-r3.md
has a header handoff/TASK-048.md
has a header handoff/TASK-049-r2.md
has a header handoff/TASK-049.md
has a header handoff/TASK-050-r2.md
has a header handoff/TASK-050.md
has a header handoff/TASK-051-r2.md
has a header handoff/TASK-051-r3.md
has a header handoff/TASK-051.md
has a header handoff/TASK-057-r2.md
has a header handoff/TASK-057.md
has a header handoff/TASK-059-r2.md
has a header handoff/TASK-059-r3.md
has a header handoff/TASK-059-r4.md
has a header handoff/TASK-059-r5.md
has a header handoff/TASK-059-r6.md
has a header handoff/TASK-059-r7.md
has a header handoff/TASK-059.md
has a header handoff/TASK-060-r2.md
has a header handoff/TASK-060.md
has a header handoff/TASK-061-r2.md
has a header handoff/TASK-061-r3.md
has a header handoff/TASK-061-r4.md
has a header handoff/TASK-061.md
has a header handoff/TASK-062-r2.md
has a header handoff/TASK-062.md
has a header handoff/TASK-063-r10.md
has a header handoff/TASK-063-r2.md
has a header handoff/TASK-063-r3.md
has a header handoff/TASK-063-r4.md
has a header handoff/TASK-063-r5.md
has a header handoff/TASK-063-r6.md
has a header handoff/TASK-063-r7.md
has a header handoff/TASK-063-r8.md
has a header handoff/TASK-063-r9.md
has a header handoff/TASK-063.md
has a header handoff/TASK-064-r2.md
has a header handoff/TASK-064-r3.md
has a header handoff/TASK-064-r4.md
has a header handoff/TASK-064.md
has a header handoff/TASK-065-r2.md
has a header handoff/TASK-065-r3.md
has a header handoff/TASK-065.md
has a header handoff/TASK-066.md
has a header handoff/TASK-067-r10.md
has a header handoff/TASK-067-r2.md
has a header handoff/TASK-067-r3.md
has a header handoff/TASK-067-r4.md
has a header handoff/TASK-067-r5.md
has a header handoff/TASK-067-r6.md
has a header handoff/TASK-067-r7.md
has a header handoff/TASK-067-r8.md
has a header handoff/TASK-067-r9.md
has a header handoff/TASK-067.md
has a header handoff/TASK-068-r2.md
has a header handoff/TASK-068-r3.md
has a header handoff/TASK-068.md
has a header handoff/TASK-069-r2.md
has a header handoff/TASK-069-r3.md
has a header handoff/TASK-069.md
has a header handoff/TASK-070-r2.md
has a header handoff/TASK-070-r3.md
has a header handoff/TASK-070.md
has a header handoff/TASK-071.md
has a header handoff/TASK-072-r2.md
has a header handoff/TASK-072-r3.md
has a header handoff/TASK-072-r4.md
has a header handoff/TASK-072.md
has a header handoff/TASK-073-r2.md
has a header handoff/TASK-073-r3.md
has a header handoff/TASK-073.md
has a header handoff/TASK-074-r2.md
has a header handoff/TASK-074-r3.md
has a header handoff/TASK-074.md
has a header handoff/TASK-075-r2.md
has a header handoff/TASK-075-r3.md
has a header handoff/TASK-075.md
has a header handoff/TASK-077-r2.md
has a header handoff/TASK-077-r3.md
has a header handoff/TASK-077-r4.md
has a header handoff/TASK-077.md
has a header handoff/TASK-083-r2.md
has a header handoff/TASK-083-r3.md
has a header handoff/TASK-083-r4.md
has a header handoff/TASK-083.md
has a header handoff/TASK-084-r2.md
has a header handoff/TASK-084.md
has a header handoff/TASK-085-r2.md
has a header handoff/TASK-085-r3.md
has a header handoff/TASK-085.md
has a header handoff/TASK-086a-r2.md
has a header handoff/TASK-086a-r3.md
has a header handoff/TASK-086a-r4.md
has a header handoff/TASK-086a.md
has a header handoff/TASK-086b-r2.md
has a header handoff/TASK-086b-r3.md
has a header handoff/TASK-086b.md
has a header handoff/TASK-087b-r2.md
has a header handoff/TASK-087b.md
has a header handoff/TASK-087d-r2.md
has a header handoff/TASK-087d-r3.md
has a header handoff/TASK-087d.md
has a header handoff/TASK-088-r2.md
has a header handoff/TASK-088-r3.md
has a header handoff/TASK-088.md
has a header handoff/TASK-089-r2.md
has a header handoff/TASK-089.md
has a header docs/INVENTORY.md
has a header docs/REQUIREMENTS.md
has a header docs/diagrams/INDEX.md
has a header docs/diagrams/DEVIATIONS.md
has a header docs/RUN_PARAMETERS.md
```

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
 bridge/cursor-bridge/bridge_env.py | 27 ++++++++++++++++++++++++---
 bridge/cursor-bridge/plan-check.py |  4 ++--
 3 files changed, 29 insertions(+), 8 deletions(-)
git rev-parse HEAD
0e744c46873899d3ae678ba60740173b248a6e39
git status --short
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/bridge_env.py
 M bridge/cursor-bridge/plan-check.py
?? handoff/TASK-089-r2-report.md
```

Commit for test counts: `0e744c46873899d3ae678ba60740173b248a6e39` with uncommitted changes as listed above (`handoff/TASK-089-r2-report.md` untracked when counts were taken; report added before supervisor handoff).

## Assumed, not verified

A plan id immediately followed by more ASCII letters without a separator still matches when the optional trailing `[a-z]?` on the plan pattern does not consume those letters (e.g. `TASK-001extra`) · R1 specifies only a left boundary (not letter or digit before the id), not a right boundary · a dedicated acceptance case or explicit requirement text would confirm.

Whether `_`, U+2014 em dash, or U+2013 en dash before an id should block or allow a match counts as a letter/digit boundary only for ASCII alphanumerics · `(?<![A-Za-z0-9])` lets those characters act as separators · tests cover comma, space, and longer words (hotfix/debug/subtask); punctuation-before-id cases were not run.

Merge branch names containing `/` (pull-request path form) beyond the tested `someone/bug-001` shapes · grammar `_GRAMMAR_MERGE_RX` and plan `_PLAN_MERGE_RX` still follow round-1 tests; slash-heavy branch tails were not in round-2 acceptance.

Round 1 brief examples such as `bug-001-x` → `BUG-001`, five-prefix tuple composition, and plan-only merged set intersection are settled · round-1 and round-2 tests in `tests/test_improve_plan_prefixes.py` pin them · no assumption listed for those.