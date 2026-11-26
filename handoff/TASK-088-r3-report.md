# TASK-088 round 3 report

## Summary paragraph

Round 3 fixes the three blocking round-2 reproductions: `brief_header_refusal` now walks `_BRIEF_HEADER_REFUSAL_ORDER` and at `satisfies` returns the `none` refusal whenever `fallback["none_carries_ids"]` is true even when header and prose lists agree as sets; `_SAT_NONE_FIRST_RX` matches the first word `none` with `\b` so colon, hyphen, em dash, slash, parenthesis and exclamation after `none` still read as `none`; `brief_satisfies_disagree_message` holds the shared remedy sentence and both `_brief_satisfies_disagree_refusal` and plan-check's `brief_findings` compose from it. All 47 tests in `tests/test_improve_satisfies_reader.py` pass unedited; Done steps 3–12 complete with uncommitted changes on commit `30caeb91944867713d9805deac6a8223fd40ed88`.

## Files changed

- `bridge/cursor-bridge/bridge_env.py`
- `bridge/cursor-bridge/plan-check.py`
- `bridge/cursor-bridge/MANIFEST.json` (via `python tools/make-manifest.py`)

## Requirements S1–S3 (functions and lines)

1. **S1 `none` refusal whatever the header's list.** `_BRIEF_HEADER_REFUSAL_ORDER` line 3796; `brief_header_refusal` lines 3799–3826: fixed-order walk, at `satisfies` when `check_satisfies` returns `_brief_none_carries_refusal` when `none_carries_ids` before set-disagreement only when `satisfies` is in `disagrees`.
2. **S2 `none` ends at a word boundary.** `_SAT_NONE_FIRST_RX` line 575 `^[\*_`]*none\b`; `_satisfies_value_reads_none` lines 587–588.
3. **S3 One wording of the disagreement's remedy.** `brief_satisfies_disagree_message` lines 3779–3785 (lists plus `the header and the prose name the same rows`); `_brief_satisfies_disagree_refusal` line 3793 prefixes `header: `; plan-check `brief_findings` lines 167–169 prefixes `header ` for the same message through `ascii_brief_list`.

## Mutation code points (P1–P3; run nothing)

| Label | Function / lines | Test id |
|-------|------------------|---------|
| P1 | `brief_header_refusal` lines 3817–3823: only return `_brief_none_carries_refusal` when `satisfies` is in `disagrees` | `test_task088_r3_a_none_that_carries_ids_is_refused_whatever_the_headers_list` |
| P2 | `_SAT_NONE_FIRST_RX` reverted to a trailing-character list instead of `\b` | `test_task088_r3_none_ends_at_a_word_boundary` |
| P3 | `brief_satisfies_disagree_message` lines 3782–3783 omit the remedy clause | `test_task088_r3_plan_checks_disagreement_line_carries_the_launchers_remedy` |

Round 2 labels N1–N6 remain with these line updates: N2 now `_SAT_NONE_FIRST_RX` line 575 (was a character-class suffix); N4 `brief_header_refusal` satisfy-branch lines 3818–3820 (order walk, not `disagrees` list order alone). Round 1 M1–M12 line shifts are minor; see `handoff/TASK-088-r1-report.md` for labels.

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
FAILED tests/test_improve_satisfies_reader.py::test_task088_r3_a_none_that_carries_ids_is_refused_whatever_the_headers_list[on-the-line]
FAILED tests/test_improve_satisfies_reader.py::test_task088_r3_a_none_that_carries_ids_is_refused_whatever_the_headers_list[beneath-refused-on-main]
FAILED tests/test_improve_satisfies_reader.py::test_task088_r3_a_none_that_carries_ids_is_refused_whatever_the_headers_list[bold-beneath-refused-on-main]
FAILED tests/test_improve_satisfies_reader.py::test_task088_r3_none_ends_at_a_word_boundary[colon]
FAILED tests/test_improve_satisfies_reader.py::test_task088_r3_none_ends_at_a_word_boundary[em-dash]
FAILED tests/test_improve_satisfies_reader.py::test_task088_r3_none_ends_at_a_word_boundary[hyphen]
FAILED tests/test_improve_satisfies_reader.py::test_task088_r3_none_ends_at_a_word_boundary[slash]
FAILED tests/test_improve_satisfies_reader.py::test_task088_r3_none_ends_at_a_word_boundary[closing-parenthesis]
FAILED tests/test_improve_satisfies_reader.py::test_task088_r3_none_ends_at_a_word_boundary[exclamation]
FAILED tests/test_improve_satisfies_reader.py::test_task088_r3_plan_checks_disagreement_line_carries_the_launchers_remedy
10 failed, 37 passed in 14.82s
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
304 passed in 170.72s (0:02:50)
```

### Step 7

```
python -m pytest -p no:cacheprovider -q tests/test_bug044.py tests/test_release_b2_text.py tests/test_program_own_records.py tests/test_records_migrate.py tests/test_header_reader.py tests/test_header_plan_r3.py tests/test_header_run_parameters.py tests/test_release_s_plan_size.py tests/test_plan_demonstration.py tests/test_dump_cli.py
```

```
1108 passed, 1 skipped in 173.22s (0:02:53)
```

Additional grep batch:

```
python -m pytest -p no:cacheprovider -q tests/test_a5_followups.py tests/test_install_check.py tests/test_task033_supervisor_r2.py tests/test_task033_supervisor.py tests/test_pace_report.py tests/test_header_status.py tests/test_release_b2_stamp.py tests/test_header_currency.py tests/test_header_tables.py tests/test_a4_review_fixes.py tests/test_bridge_run_review_ceiling.py tests/test_header_tables_r2.py tests/test_traits_existing.py
```

```
565 passed in 116.20s (0:01:56)
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
 bridge/cursor-bridge/MANIFEST.json |  6 +++---
 bridge/cursor-bridge/bridge_env.py | 35 +++++++++++++++++++++--------------
 bridge/cursor-bridge/plan-check.py |  4 +++-
 3 files changed, 27 insertions(+), 18 deletions(-)
```

### Step 12

```
git rev-parse HEAD
git status --short
```

```
30caeb91944867713d9805deac6a8223fd40ed88
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/bridge_env.py
 M bridge/cursor-bridge/plan-check.py
```

### Acceptance file (after edits, final run)

```
python -m pytest -p no:cacheprovider -q tests/test_improve_satisfies_reader.py
```

```
47 passed in 17.50s
```

Commit for counts: `30caeb91944867713d9805deac6a8223fd40ed88`. Working tree held uncommitted changes as in step 12.

Scratch test files: no scratch test file.

## Assumed, not verified

Assumed, not verified: none.