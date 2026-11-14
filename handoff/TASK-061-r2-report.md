# TASK-061 round 2 report

## Files changed

- `bridge/cursor-bridge/bridge_env.py`
- `bridge/cursor-bridge/review-guard.py`
- `bridge/cursor-bridge/MANIFEST.json` (regenerated)
- `tests/test_bridge_run.py`
- `tests/test_review_guard.py`
- `handoff/TASK-061-r2-report.md`

## Summary paragraph

Round 2 closes the Review A and security-audit gaps from round 1: non-finite review lengths no longer raise in `review_run_interval`, launcher ids require a whole ASCII `fullmatch`, `verify` keeps exit 0 when the post-OK note fails, the note lists every in-run row with `?` for non-word kinds and uses the last matching review row, and the builder tests exercise those behaviours; all supervisor acceptance tests and Done commands pass at commit `5d946d3a90b2d406360bfbe59b3b2540b9f40e22` with the diff below.

## Corrections

1. `bridge_env.review_run_interval` (line ~1311) returns no interval when `seconds` is not finite via `math.isfinite`, so NaN and infinities never reach `int(sec)`.
2. `review_guard.cmd_verify` (lines ~1164–1169) wraps the note call in `try`/`except Exception` so a note failure never changes exit 0 or prints a traceback.
3. `review_guard._launcher_rows_during_review_note` (lines ~473–477) appends every in-run row and prints `?` when kind is not a plain ASCII word.
4. The same helper (lines ~455–458) keeps the last matching review row in log order instead of stopping at the first.
5. `bridge_env._LAUNCHER_ID_RE` and `row_start_utc` (lines ~1283–1291) use `re.ASCII`, `[0-9]`, and `fullmatch` so only a whole launcher id has a start.
6. `tests/test_review_guard.py` cases at lines ~332 and ~349 and `tests/test_bridge_run.py` `test_r079_learned_limit_bad_review_seconds_ignores_nothing` were strengthened to assert named in-run rows, a log-without-`.err` path, and `at_start` plus raw `NaN`/`1e400` JSON.

## Tests changed and why

- `test_r079_verify_tolerates_malformed_log_lines` now writes a row inside the review run and expects it named while `bogus` is not.
- `test_r079_verify_missing_err_prints_no_note` seeds the launcher log like the acceptance verify case but omits `.err`, asserting nothing follows the OK line.
- `test_r079_learned_limit_bad_review_seconds_ignores_nothing` adds `2026-10-07T10:00:00Z-2` and parametrizes `NaN`/`1e400` as raw JSON so a review interval wrongly ending at start would drop that row.

## Commands and output

### 1. `python tools/make-manifest.py`

```
make-manifest: version 2026.11.12a, 146 files hashed, VERSION + MANIFEST.json written
```

### 2. `python tools/dump-cli.py --check`

```
(no output; exit 0)
```

### 3. `python -m pytest -p no:cacheprovider -q -rs tests/test_program_review_rows.py`

```
.........................                                                [100%]
25 passed in 175.06s (0:02:55)
```

### 4. `python -m pytest -p no:cacheprovider -q tests/test_bridge_run.py tests/test_bridge_run_slot.py`

```
......................................s............................s.... [ 87%]
.........s                                                               [100%]
79 passed, 3 skipped in 128.54s (0:02:08)
```

### 5. `python -m pytest -p no:cacheprovider -q tests/test_bridge_run_driver.py tests/test_release_s_launcher.py`

```
........................................................................ [ 63%]
.........................................                                [100%]
113 passed in 33.25s
```

### 6. `python -m pytest -p no:cacheprovider -q tests/test_review_guard.py`

```
...................                                                      [100%]
19 passed in 31.40s
```

### 7. Extended pytest list (Done step 7)

```
........................................................................ [ 12%]
........................................................................ [ 25%]
........................................................................ [ 38%]
........................................................................ [ 51%]
........................................................................ [ 63%]
........................................................................ [ 76%]
........................................................................ [ 89%]
...........................................................              [100%]
563 passed in 553.01s (0:09:13)
```

### 8. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`

```
bridge-check: version 2026.11.12a (2026-11-14 23:40) at <Workspace>\bridge
bridge-check: 146 OK, 0 STALE, 0 MISSING, 0 EXTRA
RESULT: SOURCES MATCH bridge 2026.11.12a
```

### 9. `git diff --stat HEAD`

```
 bridge/cursor-bridge/MANIFEST.json   |  6 +++---
 bridge/cursor-bridge/bridge_env.py   |  7 +++++--
 bridge/cursor-bridge/review-guard.py | 16 +++++++++++-----
 tests/test_bridge_run.py             | 18 +++++++++++++-----
 tests/test_review_guard.py           | 18 ++++++++++++------
 5 files changed, 44 insertions(+), 21 deletions(-)
```

### 10. `git rev-parse HEAD` and `git status --short`

```
5d946d3a90b2d406360bfbe59b3b2540b9f40e22
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/bridge_env.py
 M bridge/cursor-bridge/review-guard.py
 M tests/test_bridge_run.py
 M tests/test_review_guard.py
```

## Mutations

- **R1** (the finiteness check dropped): `FAILED tests/test_program_review_rows.py::test_r079_a_review_row_whose_seconds_is_not_finite_ignores_nothing[1e400]`
- **R2** (the note's call in `cmd_verify` not guarded, with finiteness check dropped): `FAILED tests/test_program_review_rows.py::test_r079_a_review_row_whose_seconds_is_not_finite_leaves_verify_s_exit[1e400]`
- **R3** (a row with an odd kind dropped from the note): `FAILED tests/test_program_review_rows.py::test_r079_a_row_of_any_kind_is_named_by_its_id[space]`
- **R4** (the first matching review row read instead of the last): `FAILED tests/test_program_review_rows.py::test_r079_verify_reads_the_review_s_own_row_the_last_one_with_its_id`
- **R5** (`.match` with `$` put back): `FAILED tests/test_program_review_rows.py::test_r079_only_the_whole_launcher_form_has_a_start[trailing-newline]`
- **R6** (a review row with a bad length taken as ending at its start): `FAILED tests/test_bridge_run.py::test_r079_learned_limit_bad_review_seconds_ignores_nothing[NaN]`

Each mutation was reverted before the final test run.

## Assumed, not verified

- Unguarded note alone does not fail verify when `review_run_interval` already rejects non-finite lengths, so R2 was exercised together with finiteness removed to surface a non-zero exit on the acceptance verify case.
- The builder `test_r079_learned_limit_bad_review_seconds_ignores_nothing` uses `at_start["id"] in why` rather than an exact limit because the cap may exceed the longest teaching row.