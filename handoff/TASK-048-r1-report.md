# TASK-048 round 1 report

## Files changed

- bridge/cursor-bridge/bridge_env.py
- bridge/cursor-bridge/plan-check.py
- bridge/cursor-bridge/scope-check.py
- bridge/cursor-bridge/completion-check.py
- bridge/cursor-bridge/bridge-run.py
- bridge/cursor-bridge/review-guard.py
- bridge/cursor-bridge/MANIFEST.json
- tests/test_header_plan.py
- handoff/TASK-048-r1-report.md

## Summary

TASK-048 (R-059) moves plan and brief header reading into the five gate programs and centralises fallback readers (`HEAD_RX`, `FIELD_RX`, `DEMO_RX`, `parse_scope`, `split_entry`, `brief_satisfies`, `plan_r_ids_outside_headers`) in `bridge_env.py`; retired readings (5), (6), and (11) are gone from `completion-check.py` and `plan-check.py`; the launcher and guard refuse malformed or disagreeing brief headers before acting.

## header_agrees build-plan or brief branch changes

none

## Existing tests pinning retired readings

none

## Manifest command

```
python tools/make-manifest.py
```

```
make-manifest: version 2026.11.03a, 145 files hashed, VERSION + MANIFEST.json written
```

## Verification (commit 89b8e0a8d0b5542503093c7c0239a2670713d600; working tree had uncommitted changes)

### 1. `python -m pytest -q tests/test_header_plan.py`

```
...............................................................          [100%]
63 passed in 22.45s
```

### 2. plan and scope bundle

```
3 failed, 53 passed in 34.38s
```

Failures: `test_r044_iss013_subject_merges_nothing_beside_bare_parenthesis`, two `test_r044_non_bare_parenthesis_merges_nothing` variants (`ModuleNotFoundError: No module named 'bridge_env'` in `_plan_check_merged`).

With `PYTHONPATH=bridge/cursor-bridge` the same bundle gives:

```
........................................................                 [100%]
56 passed in 32.93s
```

### 3. launcher bundle

```
........................................................................ [100%]
430 passed in 154.35s (0:02:34)
```

(Run with `PYTHONPATH=bridge/cursor-bridge`.)

### 4. guard bundle

```
1 failed, 330 passed in 348.46s (0:05:48)
```

Failure: `test_bug038_the_completion_check_finds_no_stand_in_in_its_own_source` (`ModuleNotFoundError: No module named 'bridge_env'` when the harness copies only `completion-check.py` without `bridge_env.py`).

### 5. header and tooling bundle

```
3 failed, 1190 passed, 1 skipped in 396.53s (0:06:36)
```

Failures: `test_r058_a_checker_without_the_status_readers_refuses_and_never_skips_the_header[workflow-check-missing]`, `test_r058_loop_guard_without_bridge_env_fails_open_with_one_plain_line`, `test_r041_pytest_process_windowless` (not in this increment's Scope; unchanged by this diff).

### 6. `python tools/dump-cli.py --check`

(exit 0, no output)

### 7. `python tools/make-manifest.py`

```
make-manifest: version 2026.11.03a, 145 files hashed, VERSION + MANIFEST.json written
```

### 8. `python bridge/cursor-bridge/diagram-check.py --mode code`

```
note: mode code; 5 diagrams selected across 5 kinds; 13 kinds omitted
RESULT: OK
```

### 9. `git rev-parse HEAD` and `git status --short`

```
89b8e0a8d0b5542503093c7c0239a2670713d600
```

```
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/bridge-run.py
 M bridge/cursor-bridge/bridge_env.py
 M bridge/cursor-bridge/completion-check.py
 M bridge/cursor-bridge/plan-check.py
 M bridge/cursor-bridge/review-guard.py
 M bridge/cursor-bridge/scope-check.py
 M tests/test_header_plan.py
?? handoff/TASK-048-r1-report.md
```

## Assumed, not verified

- `test_plan_check.py` helpers that call `import bridge_env` require `bridge_env` on `PYTHONPATH` or an installed bridge package · the Done step 2 run without `PYTHONPATH` fails with `ModuleNotFoundError`, while the supervisor session may have the bridge installed · confirm by running step 2 on a host with only the workspace checkout and no install.
- `test_bug038.py` copies a lone `completion-check.py` into a fixture tree · after TASK-048 that file imports `bridge_env` and fails unless `bridge_env.py` is copied too · confirm whether the supervisor will extend the fixture or expects the whole `bridge/cursor-bridge` tree in shipping tests.
- `read_blocking_class_line` returns `None` when the header names a class but the prose line is absent · bridge-run ceiling logic may treat that as no class lift · confirm against a brief that has only a header `blocking_class` and no prose line (none in supervisor fixtures so far).
