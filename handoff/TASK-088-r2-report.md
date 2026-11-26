# TASK-088 round 2 report

## Summary paragraph

Round 2 corrects TASK-088 round 1 per security and review findings: `ascii_brief_quote` (and `ascii_brief_list`) now escape C0 controls and non-ASCII for every brief-sourced fragment in launcher refusals and plan-check `BRIEF` lines; `brief_satisfies_line` is the sole locator for the `Satisfies` field; `brief_satisfies_ids` matches `none` as a first word (punctuation and markdown emphasis allowed), returns ids beside `none`, and stops bullet collection at the next `FIELD_RX` line; `brief_header_refusal` walks disagreements in key order so `id` precedes a `none`-carries-ids refusal; plan-check calls `brief_none_carries_message` and `brief_satisfies_disagree_message` from `bridge_env.py`. All 37 tests in `tests/test_improve_satisfies_reader.py` pass unedited; Done steps 3–12 complete with uncommitted changes on commit `356d8482014a7b5017819bbdc2786fa0de29193b`.

## Files changed

- `bridge/cursor-bridge/bridge_env.py`
- `bridge/cursor-bridge/plan-check.py`
- `bridge/cursor-bridge/MANIFEST.json` (via `python tools/make-manifest.py`)

## Requirements R1–R7 (functions and lines)

1. **R1 One escape.** `ascii_brief_quote` at lines 3746–3757; `ascii_brief_list` at 3760–3761. Callers: `brief_none_carries_message` line 3766 (`ascii_brief_quote` on the Satisfies line from `brief_satisfies_line`); `brief_satisfies_disagree_lists` lines 3773–3776 via `ascii_brief_list` on header and prose id lists; launcher still wraps refusal strings with `bridge-run.py` `_ascii_refusal` (unchanged).
2. **R2 `none` as a word.** `_SAT_NONE_FIRST_RX` line 575; `_satisfies_value_reads_none` lines 587–588; used in `brief_satisfies_ids` line 598.
3. **R3 Ids beside `none`.** `brief_satisfies_ids` lines 614–627 collects ids for both normal and `none` lines; `none_carries_ids` is `reads_none and bool(ids)`.
4. **R4 Refusal order.** `brief_header_refusal` lines 3810–3818 iterates `disagrees` in order and handles `satisfies` (none or set disagree) only when that key is reached.
5. **R5 One locator.** `brief_satisfies_line` lines 578–584; callers `brief_satisfies_ids` line 593, `brief_none_carries_message` line 3765; `_brief_satisfies_prose_line` removed.
6. **R6 Field bullet ends bullets.** `brief_satisfies_ids` lines 606–607 break the bullet scan on `FIELD_RX.match(ln)`.
7. **R7 One wording of each remedy.** `plan-check.py` `brief_findings` lines 164–168 call `bridge_env.brief_none_carries_message` and `bridge_env.brief_satisfies_disagree_message`; launcher uses `_brief_none_carries_refusal` / `_brief_satisfies_disagree_refusal` built from the same message helpers.

## Sole reader and locator (acceptance audit)

- **`brief_satisfies_line`** lines 578–584: only code that finds a brief's `Satisfies` line.
- **`brief_satisfies_ids`** lines 591–627: only code that reads its ids; callers `_brief_fallback_from_body` (~639), `brief_satisfies` (~3611).

## Mutation code points (N1–N6; run nothing)

| Label | Function / lines | Test id |
|-------|------------------|---------|
| N1 | `ascii_brief_quote` control-byte branch 3751–3752 removed | `test_task088_r2_a_control_byte_in_a_none_line_is_escaped_at_the_launcher` |
| N2 | `_SAT_NONE_FIRST_RX` / `_satisfies_value_reads_none` reverted to whitespace-first-word | `test_task088_r2_none_is_matched_as_a_word[comma]` |
| N3 | `brief_satisfies_ids` returns `[], True` for `none` with ids instead of collecting ids | `test_task088_r2_the_ids_beside_a_none_are_returned` |
| N4 | `brief_header_refusal` checks `none_carries_ids` before the disagrees loop | `test_task088_r2_a_wrong_id_is_told_before_a_none_that_carries_ids` |
| N5 | `brief_satisfies_ids` omits `FIELD_RX` break at 606–607 | `test_task088_r2_a_field_written_as_a_bullet_ends_the_bullets[ids-then-a-field-bullet]` |
| N6 | `brief_none_carries_message` reads the line without `brief_satisfies_line` | `test_task088_r2_one_locator_finds_the_line_for_the_reader_and_the_refusal` |

Round 1 labels M1–M12 remain as in `handoff/TASK-088-r1-report.md` with line numbers shifted slightly after this diff.

## Commands

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
.....................F....F..F..FFF.FFF.                                 [100%]
=========================== short test summary info ===========================
FAILED tests/test_improve_satisfies_reader.py::test_task088_r2_a_control_byte_in_a_none_line_is_escaped_at_the_launcher
FAILED tests/test_improve_satisfies_reader.py::test_task088_r2_a_control_byte_in_a_none_line_is_escaped_by_plan_check
FAILED tests/test_improve_satisfies_reader.py::test_task088_r2_plan_checks_disagreement_line_prints_the_lists_in_ascii
FAILED tests/test_improve_satisfies_reader.py::test_task088_r2_a_field_written_as_a_bullet_ends_the_bullets[ids-then-a-field-bullet]
FAILED tests/test_improve_satisfies_reader.py::test_task088_r2_a_field_written_as_a_bullet_ends_the_bullets[none-then-a-field-bullet]
FAILED tests/test_improve_satisfies_reader.py::test_task088_r2_none_is_matched_as_a_word[full-stop-then-a-bullet]
FAILED tests/test_improve_satisfies_reader.py::test_task088_r2_none_is_matched_as_a_word[comma]
FAILED tests/test_improve_satisfies_reader.py::test_task088_r2_none_is_matched_as_a_word[semicolon]
FAILED tests/test_improve_satisfies_reader.py::test_task088_r2_none_is_matched_as_a_word[parenthesis]
FAILED tests/test_improve_satisfies_reader.py::test_task088_r2_none_is_matched_as_a_word[bold]
FAILED tests/test_improve_satisfies_reader.py::test_task088_r2_the_ids_beside_a_none_are_returned
FAILED tests/test_improve_satisfies_reader.py::test_task088_r2_one_locator_finds_the_line_for_the_reader_and_the_refusal
FAILED tests/test_improve_satisfies_reader.py::test_task088_r2_a_wrong_id_is_told_before_a_none_that_carries_ids
13 failed, 24 passed in 12.79s
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
```

(VERSION not listed; `git restore` not run.)

### Step 6

```
python -m pytest -p no:cacheprovider -q tests/test_improve_satisfies_reader.py tests/test_header_plan.py tests/test_header_plan_r2.py tests/test_plan_check.py tests/test_program_merge_unit_one.py tests/test_task032_supervisor_launcher.py
```

```
294 passed in 172.54s (0:02:52)
```

### Step 7

```
python -m pytest -p no:cacheprovider -q tests/test_bug044.py tests/test_release_b2_text.py tests/test_program_own_records.py tests/test_records_migrate.py tests/test_header_reader.py tests/test_header_plan_r3.py tests/test_header_run_parameters.py tests/test_release_s_plan_size.py tests/test_plan_demonstration.py tests/test_dump_cli.py
```

```
1108 passed, 1 skipped in 170.70s (0:02:50)
```

Additional grep batch:

```
python -m pytest -p no:cacheprovider -q tests/test_a5_followups.py tests/test_install_check.py tests/test_task033_supervisor_r2.py tests/test_task033_supervisor.py tests/test_pace_report.py tests/test_header_status.py tests/test_release_b2_stamp.py tests/test_header_currency.py tests/test_header_tables.py tests/test_a4_review_fixes.py tests/test_bridge_run_review_ceiling.py tests/test_header_tables_r2.py tests/test_traits_existing.py
```

```
565 passed in 117.03s (0:01:57)
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
 bridge/cursor-bridge/MANIFEST.json |  6 +--
 bridge/cursor-bridge/bridge_env.py | 97 ++++++++++++++++++++++++--------------
 bridge/cursor-bridge/plan-check.py | 13 +----
 3 files changed, 67 insertions(+), 49 deletions(-)
```

### Step 12

```
git rev-parse HEAD
git status --short
```

```
356d8482014a7b5017819bbdc2786fa0de29193b
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/bridge_env.py
 M bridge/cursor-bridge/plan-check.py
```

### Acceptance file (after edits, final run)

```
python -m pytest -p no:cacheprovider -q tests/test_improve_satisfies_reader.py
```

```
37 passed in 15.42s
```

Commit for counts: `356d8482014a7b5017819bbdc2786fa0de29193b`. Working tree held uncommitted changes as in step 12.

Scratch test files: no scratch test file.

## Assumed, not verified

Assumed, not verified: none.