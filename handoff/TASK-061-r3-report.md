# TASK-061 round 3 report

## Files changed

- `bridge/cursor-bridge/bridge-run.py`
- `bridge/cursor-bridge/bridge_env.py`
- `bridge/cursor-bridge/MANIFEST.json` (regenerated)
- `handoff/TASK-061-r3-report.md`

## Summary paragraph

Round 3 closes the round-2 security audit holes in run-log handling: `learned_limit` no longer treats a healthy row whose `seconds` is NaN, infinity, or otherwise non-finite as teachable, and `read_runs_jsonl` skips lines whose JSON nesting triggers `RecursionError`; all supervisor acceptance tests and Done commands pass at commit `732ab6759e1c3e75892c0312f7eefb7eab90412c` with the diff below.

## Corrections

1. `learned_limit` healthy filter (lines ~1417–1419): a row teaches only when `seconds` is an `int` or `float` that is not a `bool` and `math.isfinite(seconds)` holds.
2. `read_runs_jsonl` (line ~1364): `except (ValueError, RecursionError)` skips a line Python's json cannot read for depth, like any other unreadable line.

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
..................................                                       [100%]
34 passed in 181.59s (0:03:01)
```

### 4. `python -m pytest -p no:cacheprovider -q tests/test_bridge_run.py tests/test_bridge_run_slot.py`

```
......................................s............................s.... [ 87%]
.........s                                                               [100%]
79 passed, 3 skipped in 130.15s (0:02:10)
```

### 5. `python -m pytest -p no:cacheprovider -q tests/test_bridge_run_driver.py tests/test_release_s_launcher.py`

```
........................................................................ [ 63%]
.........................................                                [100%]
113 passed in 33.59s
```

### 6. `python -m pytest -p no:cacheprovider -q tests/test_review_guard.py tests/test_task032_supervisor_launcher.py tests/test_dump_cli.py`

```
........................................................................ [ 34%]
........................................................................ [ 68%]
...................................................................      [100%]
211 passed in 215.39s (0:03:35)
```

### 7. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`

```
bridge-check: version 2026.11.12a (2026-11-15 00:37) at <Workspace>\bridge
bridge-check: 146 OK, 0 STALE, 0 MISSING, 0 EXTRA
RESULT: SOURCES MATCH bridge 2026.11.12a
```

### 8. `git diff --stat HEAD`

```
 bridge/cursor-bridge/MANIFEST.json | 6 +++---
 bridge/cursor-bridge/bridge-run.py | 3 ++-
 bridge/cursor-bridge/bridge_env.py | 2 +-
 3 files changed, 6 insertions(+), 5 deletions(-)
```

### 9. `git rev-parse HEAD` and `git status --short`

```
732ab6759e1c3e75892c0312f7eefb7eab90412c
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/bridge-run.py
 M bridge/cursor-bridge/bridge_env.py
?? handoff/TASK-061-r3-report.md
```

## Mutations

- **S1** (the finiteness check dropped from the healthy filter): `FAILED tests/test_program_review_rows.py::test_r079_a_healthy_row_whose_seconds_is_not_finite_teaches_nothing[x-NaN]` (six parametrized cases failed; this line is representative).
- **S2** (`RecursionError` not caught): `FAILED tests/test_program_review_rows.py::test_r079_a_line_nested_too_deep_to_read_is_skipped`

Each mutation was reverted before the final test run.

## Assumed, not verified

- The acceptance parametrized finite-seconds case fully covers bool `seconds` values; the healthy filter excludes `bool` for symmetry with other row validators, though JSON would not normally decode `seconds` as a bool.