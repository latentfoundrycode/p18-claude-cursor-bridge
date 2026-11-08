# TASK-050 builder report (r1)

## Files changed

- bridge/cursor-bridge/bridge_env.py
- bridge/cursor-bridge/bridge-run.py
- bridge/cursor-bridge/loop-guard.py
- bridge/cursor-bridge/review-guard.py
- bridge/cursor-bridge/inventory-check.py
- bridge/cursor-bridge/MANIFEST.json (regenerated)
- tests/test_header_run_parameters.py
- tests/test_header_currency.py
- tests/test_loop_guard.py
- tests/test_bridge_run_design_ceiling.py
- tests/test_bridge_run_review_ceiling.py
- tests/test_review_guard_ceiling.py
- tests/test_release_b_bootstrap.py
- handoff/TASK-050-r1-report.md

## Summary

TASK-050 moved the run-parameters line readers into `bridge_env.py` (`run_parameters_fallback`, `run_parameters_values`, `run_parameters_refusal`, shared regexes), switched `bridge-run.py`, `loop-guard.py`, and `review-guard.py` to header-first reads with gate refusals on the keys each program owns, added `inventory-check.py` agreement checking for all nine keys, updated `review_owner_lifts` for header-first review lifts, and added builder tests naming R-061 or R-057 below the supervisor markers.

## Requirements

- **R1.** `run_parameters_fallback` in `bridge_env.py` returns the nine schema keys with the line-reading rules from Requirements 1 (value tokens, `AGENT_CEILING_RE`, `CEILING_LIFT_RE`, `DESIGN_LIFT_RE`, `REVIEW_LIFT_RE`, date suffix parsing).
- **R2.** `DESIGN_LIFT_RE`, `CEILING_LIFT_RE`, and `AGENT_CEILING_RE` live beside `REVIEW_LIFT_RE`; program copies are removed; `review_owner_lifts` reads a well-formed header's `review_rounds_above_ceiling` with line text from prose.
- **R3.** `run_parameters_values` mirrors `status_values`: header values when well-formed, else fallback; malformed tuple; disagrees via `header_agrees("run-parameters", ...)`.
- **R4.** `run_parameters_refusal` returns malformed or first disagreeing key from the caller's key tuple, else `None`.
- **R5.** `bridge-run.py` `main()` calls `run_parameters_refusal` before `design_ceiling`; `owner_cap` and `design_lifts` use `run_parameters_values`.
- **R6.** `snapshot_review_refusal` in `review-guard.py` calls `run_parameters_refusal(root, ("review_rounds_above_ceiling",))` before `review_owner_lifts`.
- **R7.** `loop-guard.py` `agent_ceiling` and `owner_ceiling` use `run_parameters_values`; `main()` exits 2 on `agent_ceiling` or `ceiling_above_twice` disagrees; import check requires `run_parameters_values`.
- **R8.** `inventory-check.py` checks `RUN_PARAMETERS.md` beside the inventory path; `_INVENTORY_BRIDGE_NAMES` includes the new readers.
- **R9.** Header-first paths use `errors="replace"` reads; existing ceiling tests unchanged except new additive cases.
- **R10.** `test_r001_run_parameters_owner_values` reads owner tokens through `run_parameters_values`; `test_r061_bootstrap_owner_values_from_header_match_lines` covers the header path in `tmp_path`.
- **R11.** Currency tests pass including retired reading (10) for `loop-guard.py`.
- **R12.** No CLI, dependency, or `HEADER_SCHEMAS` edits; `dump-cli --check` exits 0.
- **R13.** Builder cases below markers in acceptance, currency, ceiling, loop-guard, and bootstrap files, including header-only lift refusal and non-UTF-8 loop-guard cases.

## Earlier increment code in bridge_env (TASK-046 to TASK-049)

- `review_owner_lifts` (header first when well-formed, line text from prose). Reason: Requirement 2.

## Existing tests pinning a retired reading

none

## Commands and output

Commit for counts below: `f96c9c0cf36d6755b0b02e66dd6329a007af887a`. Working tree: uncommitted changes (see `git status --short` in step 7).

### 1

```
python -m pytest -q tests/test_header_run_parameters.py tests/test_header_currency.py
```

```
........................................................................ [ 48%]
........................................................................ [ 96%]
.....                                                                    [100%]
149 passed in 11.22s
```

### 2

```
python -m pytest -q tests/test_loop_guard.py tests/test_bridge_run_design_ceiling.py tests/test_bridge_run_review_ceiling.py tests/test_review_guard_ceiling.py tests/test_release_b_bootstrap.py
```

```
........................................................................ [ 36%]
........................................................................ [ 73%]
..................................................s..                    [100%]
196 passed, 1 skipped in 22.45s
```

### 3

```
python -m pytest -q tests/test_task032_supervisor_launcher.py tests/test_task032_supervisor_guard.py tests/test_loop_text_pace.py tests/test_bridge_run.py tests/test_bridge_run_driver.py tests/test_bridge_run_slot.py tests/test_d003_review_round_states.py tests/test_task033_supervisor.py tests/test_a4_followups.py tests/test_header_reader.py tests/test_header_schemas.py tests/test_header_status.py tests/test_header_plan.py tests/test_header_tables.py tests/test_dump_cli.py tests/test_tests_windowless.py
```

```
1774 passed, 3 skipped in 593.04s (0:09:53)
```

### 4

```
python tools/make-manifest.py
```

```
make-manifest: version 2026.11.03a, 145 files hashed, VERSION + MANIFEST.json written
```

### 5

```
python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet
```

```
bridge-check: version 2026.11.03a (2026-11-08 14:52) at <Workspace>\bridge
bridge-check: 145 OK, 0 STALE, 0 MISSING, 0 EXTRA
RESULT: SOURCES MATCH bridge 2026.11.03a
```

### 6

```
python tools/dump-cli.py --check
```

```
(exit 0, no stdout)
```

### 7

```
git rev-parse HEAD
```

```
f96c9c0cf36d6755b0b02e66dd6329a007af887a
```

```
git status --short
```

```
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/bridge-run.py
 M bridge/cursor-bridge/bridge_env.py
 M bridge/cursor-bridge/inventory-check.py
 M bridge/cursor-bridge/loop-guard.py
 M bridge/cursor-bridge/review-guard.py
 M tests/test_bridge_run_design_ceiling.py
 M tests/test_bridge_run_review_ceiling.py
 M tests/test_header_currency.py
 M tests/test_header_run_parameters.py
 M tests/test_loop_guard.py
 M tests/test_release_b_bootstrap.py
 M tests/test_review_guard_ceiling.py
?? handoff/TASK-050-r1-report.md
```

## Assumed, not verified

Assumed, not verified: none
