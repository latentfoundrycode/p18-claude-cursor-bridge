# BUG-030 round 3 — builder report

## Files changed

- `bridge/cursor-bridge/mutation-run.py`
- `bridge/cursor-bridge/MANIFEST.json` (regenerated via `tools/make-manifest.py`)

## Verification

1. `python -m pytest tests/test_mutation_run_supervisor.py tests/test_mutation_run.py -q -rs` — exit 0 — `160 passed, 2 skipped in 544.44s (0:09:04)`
2. `python -m pytest "tests/test_mutation_run_supervisor.py::test_bug030_r3_the_internal_error_line_names_every_module_that_failed" "tests/test_mutation_run_supervisor.py::test_bug030_an_import_failure_exits_3_never_1" "tests/test_mutation_run_supervisor.py::test_bug030_r2_a_damaged_bridge_env_exits_3_never_1" "tests/test_mutation_run_supervisor.py::test_bug030_r2_the_program_loaded_as_a_module_works" -v` — exit 0 — `4 passed in 1.35s`
3. `python tools/make-manifest.py` — exit 0 — `make-manifest: version 2026.10.25a, 144 files hashed, VERSION + MANIFEST.json written`
4. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` — exit 0 — `RESULT: SOURCES MATCH bridge 2026.10.25a`
5. `python tools/dump-cli.py --check` — exit 0
6. `git diff --quiet HEAD -- tests` — exit 0; `git diff --quiet -- bridge/cursor-bridge/VERSION` — exit 0; `git status --porcelain`:

```
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/mutation-run.py
?? handoff/BUG-030-r3-report.md
```

## Summary

Round 2 stored a single `_IMPORT_ERROR` that the second failed import overwrote and printed bare, so stderr could name no module and showed only the last failure; round 3 records each failure as a `(module name, exception)` pair in import order, moves the `tomllib` guard back before the `sys.path` insert, and has `run_main` emit one ASCII line listing every failed import as `cannot import <name>: <type>: <text>` separated by `; ` before returning 3.

## Cause

The named cause was a single module-level exception variable overwritten on the second import and printed without the module name; the fix accumulates named pairs and formats them explicitly in `run_main` instead of relying on `%s` of the last exception alone.

## Assumed, not verified

Assumed, not verified: none
