# BUG-032 round 3 report

## Initial test hash

`git hash-object tests/test_bug032.py` before edits: `ddc6415179feb4d8f940ab9650f373006a10cef0`

## Files changed

- `bridge/cursor-bridge/mutation-run.py`
- `bridge/cursor-bridge/bridge_env.py`
- `bridge/cursor-bridge/review-guard.py`

## Commands and results

1. `python -m pytest -q -p no:cacheprovider tests/test_bug032.py` — exit 0, `14 passed in 52.72s`
2. `python -m pytest -q -p no:cacheprovider tests/test_mutation_run.py tests/test_mutation_run_supervisor.py tests/test_hotfix25a_guard_scope_invisible.py tests/test_pace_report.py tests/test_task033_supervisor.py tests/test_task033_supervisor_r2.py tests/test_task033_supervisor_r3.py tests/test_task033_supervisor_r4.py tests/test_task032_supervisor_launcher.py tests/test_task032_supervisor_guard.py tests/test_review_guard_ceiling.py tests/test_bridge_run_review_ceiling.py tests/test_bug030.py` — exit 0, `665 passed, 2 skipped in 809.24s (0:13:29)`
3. `python tools/dump-cli.py --check` — exit 0
4. `git hash-object tests/test_bug032.py` — `ddc6415179feb4d8f940ab9650f373006a10cef0` (unchanged)
5. `git status --porcelain`:
```
 M bridge/cursor-bridge/bridge_env.py
 M bridge/cursor-bridge/mutation-run.py
 M bridge/cursor-bridge/review-guard.py
?? handoff/BUG-032-r3-report.md
```

## Summary

Round 3 closes four defects in the checkpoint conftest path and the refactoring-branch snapshot rule: checkpoint mode no longer trusts a multi-file pytest run to name failed conftests, instead confirming each test file alone and running a combined resolution check only on clear files; git failures no longer excuse conftests; stderr is split on newlines without `splitlines`, with colour disabled for the resolution-check pytest run; and guard snapshots on `refactor/<stage>` branches accept only `REFAC-<stage>`, not numbered REFAC IDs.

## Requirement mapping

1. **Per-file conftest confirmation:** Replaced the iterative multi-file loop with an initial probe run whose excused conftest is ignored for blocking, per-file resolution checks that populate `failed_conftests` only when the excused path lies on that file's conftest chain, plus a final combined check on clear files; removed `checkpoint_load_fail_on_run_files` and `checkpoint_test_files_clear_of_conftest`.
2. **Git failure never excuses:** `conftest_changed_by_increment` uses `git_try("ls-tree", "-z", commit, "--", rel)` where `None` means not changed by increment (not excused) and empty output means absent at the commit (excused).
3. **Plain pytest stderr line:** Added `_stderr_lines` splitting on `"\n"` with one trailing `\r` stripped per line; set `PY_COLORS=0` and drop `FORCE_COLOR` for the resolution-check pytest environment only; dropped the unused `out` argument from `copied_conftest_load_failure`.
4. **Snapshot stage name only:** `branch_allows_id(..., snapshot=False)` allows numbered REFAC IDs only when `snapshot` is false; `snapshot_review_refusal` passes `snapshot=True`; removed `_is_refac_id` and the unused `id_rx` parameter from `_declared_ids_all_refac`.

## Assumed, not verified

- `git ls-tree -z <commit> -- <rel>` returns empty stdout when `rel` is absent at the commit and non-empty when present, with exit 0 in both cases · the brief specifies this shape and the r3 git test passed · inspect `git ls-tree` on edge paths (symlinks, submodules) if needed.
- A per-file resolution check that returns no excused conftest has already satisfied every refusal that the combined run over clear files would apply · the brief treats per-file clear plus combined run as equivalent to the old loop's final full check · a case where combined clear files fail for a reason no single-file run caught would show up as the combined-run refusal path.
- Disabling colour via `PY_COLORS=0` and removing `FORCE_COLOR` is enough that pytest's conftest load line is never wrapped in ANSI codes in this environment · Review A consider item taken without running pytest under forced colour · run resolution check under inherited `FORCE_COLOR=1` and assert the line still fullmatches.
