# BUG-032 round 2 report

## Initial test hash

`git hash-object tests/test_bug032.py` before edits: `5e998f6def2cc176ff22c091288e792b0f028fe1`

## Files changed

- `bridge/cursor-bridge/mutation-run.py`
- `bridge/cursor-bridge/bridge_env.py`
- `handoff/BUG-032-r2-report.md`

## Summary

Round 2 tightens BUG-032 cause 1 and cause 4: checkpoint mode now loops the resolution check until every excused copied conftest load failure is recorded, excuses only conftest.py files the increment actually changed (via git blob compare), parses pytest's own load-failure line from stderr with per-line full matches (last match wins, fixing CRLF and spoofed stdout lines), removes the resolution plugin on early return, and limits refactoring-branch ID admission to `REFAC-<digits>` briefs and the branch snapshot `REFAC-<stage>` only.

## Corrections

1. **Multiple failing conftests:** The `--checkpoint` branch loops `run_resolution_check` over test files not blocked by already-found failures, accumulates `failed_conftests`, refuses on duplicate or orphan reports, runs the final clear set through the full resolution refusals, and blocks items via the first failed conftest on each item's path.
2. **Unchanged conftest:** `conftest_changed_by_increment` requires the path to be absent at the checkpoint commit or to differ from that commit's blob; otherwise exit 4 is not excused and the run is refused as before BUG-032.
3. **Spoofed load line:** `_conftest_load_failure_path` scans stderr lines only, uses `fullmatch` on the exact pytest message, and keeps the last match so a conftest cannot blame another by writing the line first.
4. **Refactoring branch IDs:** `_refac_numbered_brief_id` and `_refac_branch_snapshot_id` replace the broad `_is_refac_id` gate in `branch_allows_id` and `_declared_ids_all_refac`; non-`str` IDs are rejected.

## Commands run

1. `python -m pytest -q -p no:cacheprovider tests/test_bug032.py` — exit 0 — `9 passed in 20.73s`
2. `python -m pytest -q -p no:cacheprovider tests/test_mutation_run.py tests/test_mutation_run_supervisor.py tests/test_hotfix25a_guard_scope_invisible.py tests/test_pace_report.py tests/test_task033_supervisor.py tests/test_task033_supervisor_r2.py tests/test_task033_supervisor_r3.py tests/test_task033_supervisor_r4.py tests/test_task032_supervisor_launcher.py tests/test_task032_supervisor_guard.py tests/test_review_guard_ceiling.py tests/test_bridge_run_review_ceiling.py tests/test_bug030.py` — exit 0 — `665 passed, 2 skipped in 804.54s`
3. `python tools/dump-cli.py --check` — exit 0
4. `git hash-object tests/test_bug032.py` — `5e998f6def2cc176ff22c091288e792b0f028fe1` (unchanged)
5. `git status --porcelain`:
```
 M bridge/cursor-bridge/bridge_env.py
 M bridge/cursor-bridge/mutation-run.py
?? handoff/BUG-032-r2-report.md
```

## Assumed, not verified

Assumed, not verified: none
