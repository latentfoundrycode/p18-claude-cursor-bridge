# TASK-061 round 4 report

## Files changed

- `bridge/cursor-bridge/bridge_env.py`
- `bridge/cursor-bridge/bridge-run.py`
- `bridge/cursor-bridge/MANIFEST.json` (regenerated)
- `handoff/TASK-061-r4-report.md`

## Summary paragraph

Round 4 adds `bridge_env.log_seconds` as the single non-raising reader for a row's `seconds`, uses it in `review_run_interval` and in `learned_limit`'s healthy filter so JSON whole numbers too large for a float no longer make `math.isfinite` raise; all supervisor acceptance tests and Done commands pass at commit `8c4a6c6b6e81562b0bbd7fcc43fec4f3dece0ced` with the diff below.

## Corrections

One length reader that never raises: `log_seconds` in `bridge_env.py` (lines 1301-1306) returns a value only for non-bool `int`/`float` strictly between `-10**9` and `10**9`, else `None`, by comparisons alone; `review_run_interval` (lines 1316-1318) and `learned_limit`'s healthy filter in `bridge-run.py` (line 1418) both read length through it.

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
.......................................                                  [100%]
39 passed in 176.89s (0:02:56)
```

### 4. `python -m pytest -p no:cacheprovider -q tests/test_bridge_run.py tests/test_bridge_run_slot.py`

```
......................................s............................s.... [ 87%]
.........s                                                               [100%]
79 passed, 3 skipped in 129.03s (0:02:09)
```

### 5. `python -m pytest -p no:cacheprovider -q tests/test_bridge_run_driver.py tests/test_release_s_launcher.py`

```
........................................................................ [ 63%]
.........................................                                [100%]
113 passed in 32.05s
```

### 6. `python -m pytest -p no:cacheprovider -q tests/test_review_guard.py tests/test_task032_supervisor_launcher.py tests/test_dump_cli.py`

```
........................................................................ [ 34%]
........................................................................ [ 68%]
...................................................................      [100%]
211 passed in 208.19s (0:03:28)
```

### 7. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`

```
bridge-check: version 2026.11.12a (2026-11-15 01:05) at <Workspace>\bridge
bridge-check: 146 OK, 0 STALE, 0 MISSING, 0 EXTRA
RESULT: SOURCES MATCH bridge 2026.11.12a
```

### 8. `git diff --stat HEAD`

```
 bridge/cursor-bridge/MANIFEST.json |  6 +++---
 bridge/cursor-bridge/bridge-run.py |  3 +--
 bridge/cursor-bridge/bridge_env.py | 16 +++++++++++-----
 3 files changed, 15 insertions(+), 10 deletions(-)
```

### 9. `git rev-parse HEAD` and `git status --short`

```
8c4a6c6b6e81562b0bbd7fcc43fec4f3dece0ced
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/bridge-run.py
 M bridge/cursor-bridge/bridge_env.py
?? handoff/TASK-061-r4-report.md
```

## Mutations

- **T1** (the upper bound dropped): `FAILED tests/test_program_review_rows.py::test_r079_a_healthy_row_whose_seconds_is_too_big_for_a_float_teaches_nothing[positive]` (OverflowError in `learned_limit` at `max`).
- **T2** (the bool test dropped): `FAILED tests/test_bridge_run.py::test_r079_learned_limit_bad_review_seconds_ignores_nothing[True]`
- **T3** (the healthy filter not reading the reader): `FAILED tests/test_program_review_rows.py::test_r079_a_healthy_row_whose_seconds_is_too_big_for_a_float_teaches_nothing[positive]`

Each mutation was reverted before the final test run.

## Assumed, not verified

- Bounds of `10**9` exclude every run duration the launcher can actually record while still covering pathological JSON integers; no row in production logs is expected near that ceiling.