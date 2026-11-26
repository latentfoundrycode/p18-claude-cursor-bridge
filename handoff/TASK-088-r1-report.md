# TASK-088 round 1 report

## Summary paragraph

Implemented `bridge_env.brief_satisfies_ids(body)` as the sole reader of a brief's `Satisfies` ids (line plus bullets beneath, deduplicated in first-seen order, with a `none_carries_ids` flag), wired `_brief_fallback_from_body` and `brief_satisfies` through it, compared brief header `satisfies` as sets in `header_agrees`, extended `brief_header_refusal` with ASCII refusal text for `none` carrying ids and for set disagreements (both lists plus the shared-rows remedy), and taught `plan-check.py` `brief_findings` to emit matching `BRIEF` lines. All 21 tests in `tests/test_improve_satisfies_reader.py` pass; step 6 passes 278 tests; one step-7 failure in `test_records_migrate.py` is caused by deduplicated satisfies in migration read-back (reported below, test not edited). `bridge-run.py` unchanged; launcher refusals use the new strings from `brief_header_refusal` through existing `_ascii_refusal` calls.

## Files changed

- `bridge/cursor-bridge/bridge_env.py`
- `bridge/cursor-bridge/plan-check.py`
- `bridge/cursor-bridge/MANIFEST.json` (via `python tools/make-manifest.py`)
- `docs/cli-reference.json` (via `python tools/dump-cli.py`)
- `docs/CLI_REFERENCE.md` (via `python tools/dump-cli.py`)
- `handoff/TASK-088-r1-report.md`

## Requirements (functions and lines)

1. **The one reader.** `brief_satisfies_ids` at lines 577–621 (`_BRIEF_SAT_BULLET_RX` at 574–575).
2. **No second copy.** `_brief_fallback_from_body` lines 632–636 call `brief_satisfies_ids`; `brief_satisfies` lines 3598–3605 call `brief_satisfies_ids`.
3. **Sets.** `header_agrees` brief branch, `satisfies` at lines 2746–2749.
4. **Design seven rows.** Satisfied via the above plus `brief_header_refusal` refusal helpers (launcher acceptance tests).
5. **Launcher refusals.** `_brief_none_carries_refusal` 3752–3757, `_brief_satisfies_disagree_refusal` 3760–3767, used in `brief_header_refusal` 3770–3793; `bridge-run.py` `builder_review_refusal` still wraps with `_ascii_refusal` at 1491–1508.
6. **What stands.** `brief_header_refusal` `check_satisfies` gates none and detailed satisfies refusals (3781–3790); guard keys omitting `satisfies` unchanged in behaviour.
7. **plan-check BRIEF lines.** `brief_findings` lines 163–176 in `plan-check.py`.
8. **Nothing else.** No new dependencies; ASCII helpers added only as ASCII strings in `bridge_env.py`.

## Mutation code points (M1–M12)

| Label | Function / lines | Test id |
|-------|------------------|---------|
| M1 | `brief_satisfies_ids` bullet collection 592–603 | `test_task088_the_reader_reads_the_line_and_the_bullets_directly_beneath` |
| M2 | `brief_satisfies_ids` blank-line continue 596–598 | `test_task088_the_reader_reads_the_line_and_the_bullets_directly_beneath` |
| M3 | `brief_satisfies_ids` break on non-bullet 604 | `test_task088_the_reader_reads_the_line_and_the_bullets_directly_beneath` |
| M4 | `brief_satisfies_ids` `_add` / `seen` 612–616 | `test_task088_the_reader_names_each_id_once_in_first_seen_order` |
| M5 | `header_agrees` set branch 2746–2749 | `test_task088_row4_the_same_set_in_another_order_is_launched` |
| M6 | `brief_satisfies_ids` `first_none` block 605–608 | `test_task088_the_reader_flags_a_none_that_carries_ids[none-carries-an-id-on-the-line]` |
| M7 | `brief_header_refusal` 3783–3784, `_brief_none_carries_refusal` 3752–3757 | `test_task088_row6_a_none_that_carries_ids_is_refused_with_the_remedy` |
| M8 | `_brief_satisfies_disagree_refusal` 3760–3767 | `test_task088_row7_a_disagreeing_list_is_refused_with_both_lists` |
| M9 | `bridge-run.py` `_ascii_refusal` on `builder_review_refusal` 1495 (unchanged) | `test_task088_a_none_with_a_non_ascii_line_is_refused_in_ascii` |
| M10 | `plan-check.py` `brief_findings` 170–176 | `test_task088_plan_check_names_an_unmerged_brief_whose_header_disagrees` |
| M11 | `plan-check.py` `brief_findings` 164–169 | `test_task088_plan_check_names_an_unmerged_brief_whose_none_carries_ids` |
| M12 | `brief_header_refusal` `check_satisfies` 3781 | `test_task088_the_review_guard_answers_as_on_the_checkpoint` |

## Test search

Search: `tests/` content match `brief_satisfies|read_brief_record|header_agrees|brief_header_refusal|brief_prose_fallback|plan-check`.

Step 6 files: `test_improve_satisfies_reader.py`, `test_header_plan.py`, `test_header_plan_r2.py`, `test_plan_check.py`, `test_program_merge_unit_one.py`, `test_task032_supervisor_launcher.py`.

Step 7 files: `test_bug044.py`, `test_release_b2_text.py`, `test_program_own_records.py`, `test_records_migrate.py`, `test_header_reader.py`, `test_header_plan_r3.py`, `test_header_run_parameters.py`, `test_release_s_plan_size.py`, `test_plan_demonstration.py`, `test_dump_cli.py`.

Additional step-7 batch (not in brief step 6/7 list): `test_a5_followups.py`, `test_install_check.py`, `test_task033_supervisor_r2.py`, `test_task033_supervisor.py`, `test_pace_report.py`, `test_header_status.py`, `test_release_b2_stamp.py`, `test_header_currency.py`, `test_header_tables.py`, `test_a4_review_fixes.py`, `test_bridge_run_review_ceiling.py`, `test_header_tables_r2.py`, `test_traits_existing.py`.

Scratch test files: no scratch test file.

## Known failures (caused by this change)

- `tests/test_records_migrate.py::test_r062_a_satisfies_id_named_twice_is_kept_twice_in_order` — migration read-back expects header `satisfies` `["R-062", "R-062"]` but the one reader dedupes to `["R-062"]`. Test file not edited per brief.

## Commands (final run, commit `c70da82892da8a3ae2380d1d3e739965763b2250`, working tree uncommitted changes below)

### Step 1 (before edit)

```
git status --short
```
```
(empty)
```

### Step 2 (before edit)

```
python -m pytest -p no:cacheprovider -q tests/test_improve_satisfies_reader.py
```
```
...............F....F..F..FFF.FFF.                                       [100%]
================================== FAILURES ===================================
(... 15 failures ...)
=========================== short test summary info ===========================
FAILED tests/test_improve_satisfies_reader.py::test_task088_the_reader_reads_the_line_and_the_bullets_directly_beneath
FAILED tests/test_improve_satisfies_reader.py::test_task088_the_reader_names_each_id_once_in_first_seen_order
FAILED tests/test_improve_satisfies_reader.py::test_task088_the_reader_flags_a_none_that_carries_ids[none]
FAILED tests/test_improve_satisfies_reader.py::test_task088_the_reader_flags_a_none_that_carries_ids[none-carries-an-id-on-the-line]
FAILED tests/test_improve_satisfies_reader.py::test_task088_the_reader_flags_a_none_that_carries_ids[none-carries-an-id-beneath]
FAILED tests/test_improve_satisfies_reader.py::test_task088_the_briefs_two_readers_call_the_one_reader
FAILED tests/test_improve_satisfies_reader.py::test_task088_brief_satisfies_reads_the_bullets
FAILED tests/test_improve_satisfies_reader.py::test_task088_row2_bullets_beneath_the_line_are_launched
FAILED tests/test_improve_satisfies_reader.py::test_task088_row3_a_repeated_id_is_launched
FAILED tests/test_improve_satisfies_reader.py::test_task088_row4_the_same_set_in_another_order_is_launched
FAILED tests/test_improve_satisfies_reader.py::test_task088_row6_a_none_that_carries_ids_is_refused_with_the_remedy
FAILED tests/test_improve_satisfies_reader.py::test_task088_row7_a_disagreeing_list_is_refused_with_both_lists
FAILED tests/test_improve_satisfies_reader.py::test_task088_a_none_with_a_non_ascii_line_is_refused_in_ascii
FAILED tests/test_improve_satisfies_reader.py::test_task088_plan_check_names_an_unmerged_brief_whose_header_disagrees
FAILED tests/test_improve_satisfies_reader.py::test_task088_plan_check_names_an_unmerged_brief_whose_none_carries_ids
15 failed, 6 passed in 8.53s
```

### Step 3

```
python tools/dump-cli.py
python tools/dump-cli.py --check
```
```
(both exit 0, no stdout)
```

### Step 4

```
python tools/make-manifest.py
```
```
make-manifest: version 2026.11.24a, 148 files hashed, VERSION + MANIFEST.json written
```

### Step 5

```
git status --short
```
```
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/bridge_env.py
 M bridge/cursor-bridge/plan-check.py
 M docs/CLI_REFERENCE.md
 M docs/cli-reference.json
```
(VERSION not listed; `git restore` not run.)

### Step 6

```
python -m pytest -p no:cacheprovider -q tests/test_improve_satisfies_reader.py tests/test_header_plan.py tests/test_header_plan_r2.py tests/test_plan_check.py tests/test_program_merge_unit_one.py tests/test_task032_supervisor_launcher.py
```
```
278 passed in 166.12s (0:02:46)
```

### Step 7

```
python -m pytest -p no:cacheprovider -q tests/test_bug044.py tests/test_release_b2_text.py tests/test_program_own_records.py tests/test_records_migrate.py tests/test_header_reader.py tests/test_header_plan_r3.py tests/test_header_run_parameters.py tests/test_release_s_plan_size.py tests/test_plan_demonstration.py tests/test_dump_cli.py
```
```
1 failed, 1107 passed, 1 skipped in 176.39s (0:02:56)
FAILED tests/test_records_migrate.py::test_r062_a_satisfies_id_named_twice_is_kept_twice_in_order
```

Additional grep batch:

```
python -m pytest -p no:cacheprovider -q tests/test_a5_followups.py tests/test_install_check.py tests/test_task033_supervisor_r2.py tests/test_task033_supervisor.py tests/test_pace_report.py tests/test_header_status.py tests/test_release_b2_stamp.py tests/test_header_currency.py tests/test_header_tables.py tests/test_a4_review_fixes.py tests/test_bridge_run_review_ceiling.py tests/test_header_tables_r2.py tests/test_traits_existing.py
```
```
565 passed in 116.05s (0:01:56)
```

### Step 8

```
python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet
```
```
RESULT: SOURCES MATCH bridge 2026.11.24a <Workspace>/bridge/cursor-bridge
```

### Step 9

```
python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks
```
```
windowless-check: 41 file(s) scanned, 0 FAIL, 0 NOTE
```

### Step 10

```
python -c "[open(p,'rb').read().decode('ascii') for p in ('bridge/cursor-bridge/bridge_env.py','bridge/cursor-bridge/bridge-run.py')]; print('ascii ok')"
```
```
ascii ok
```

### Step 11

```
git diff --stat HEAD
```
```
 bridge/cursor-bridge/MANIFEST.json |   6 +--
 bridge/cursor-bridge/bridge_env.py | 107 ++++++++++++++++++++++++++++++++-----
 bridge/cursor-bridge/plan-check.py |  14 +++++
 3 files changed, 112 insertions(+), 15 deletions(-)
```

### Step 12

```
git rev-parse HEAD
git status --short
```
```
c70da82892da8a3ae2380d1d3e739965763b2250
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/bridge_env.py
 M bridge/cursor-bridge/plan-check.py
 M docs/CLI_REFERENCE.md
 M docs/cli-reference.json
```

### Acceptance file (after edits, same commit context)

```
python -m pytest -p no:cacheprovider -q tests/test_improve_satisfies_reader.py
```
```
21 passed in 9.13s
```

## Assumed, not verified

- `none` as the first word on the Satisfies value is matched case-insensitively (`words[0].lower() == "none"`) · the brief names the word `none` but not casing · a fixture with `Satisfies: None` would confirm.
- A bullet line directly beneath Satisfies that contains no R-id does not end the bullet block (only a non-bullet, non-blank line does) · acceptance bullets always carry ids or the block ends at prose · a brief with `Satisfies:\n- (see above)\n- R-001` would confirm.