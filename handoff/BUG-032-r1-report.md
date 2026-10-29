# BUG-032 round 1 builder report

## test hash before edits

`git hash-object tests/test_bug032.py` → 77e47f08a512dbfbfcf499653851eb14bdc6d8d4

## Files changed

- bridge/cursor-bridge/mutation-run.py
- bridge/cursor-bridge/scope-check.py
- bridge/cursor-bridge/pace-report.py
- bridge/cursor-bridge/bridge_env.py

## Verification

1. `python -m pytest -q -p no:cacheprovider tests/test_bug032.py` — exit 0, `5 passed in 6.16s`
2. `python -m pytest -q -p no:cacheprovider tests/test_mutation_run.py tests/test_mutation_run_supervisor.py tests/test_hotfix25a_guard_scope_invisible.py tests/test_pace_report.py tests/test_task033_supervisor.py tests/test_task033_supervisor_r2.py tests/test_task033_supervisor_r3.py tests/test_task033_supervisor_r4.py tests/test_task032_supervisor_launcher.py tests/test_task032_supervisor_guard.py tests/test_review_guard_ceiling.py tests/test_bridge_run_review_ceiling.py tests/test_bug030.py` — exit 0, `665 passed, 2 skipped in 808.83s`
3. `python tools/dump-cli.py --check` — exit 0
4. `git hash-object tests/test_bug032.py` → 77e47f08a512dbfbfcf499653851eb14bdc6d8d4 (unchanged)
5. `git status --porcelain`:

```
 M bridge/cursor-bridge/bridge_env.py
 M bridge/cursor-bridge/mutation-run.py
 M bridge/cursor-bridge/pace-report.py
 M bridge/cursor-bridge/scope-check.py
?? handoff/BUG-032-r1-report.md
```

## Summary

BUG-032 fixes four confirmed defects: checkpoint mode no longer refuses the run when a working-tree conftest copied into the archive fails to import on the checkpoint code (those tests are reported `not run` with the conftest path), scope-check and pace-report ignore launcher rows with `"slot": "not free"`, and the branch rule allows any REFAC ID on a `refactor/` branch whose declared IDs are all REFAC IDs.

## Cause fixes

1. **Cause 1:** `copied_conftest_load_failure` detects pytest exit 4 with `ImportError while loading conftest` for a copied conftest; `run_resolution_check` returns instead of refusing, optionally re-runs on unaffected test files, and the checkpoint loop prints `<item>: not run (<conftest>)` and skips pytest for blocked items.
2. **Cause 2:** `builder_windows` skips rows where `slot == "not free"`.
3. **Cause 3:** `_start_times` and `_lift_map` skip runs.jsonl rows where `slot == "not free"`.
4. **Cause 4:** `branch_allows_id` admits any REFAC ID when the branch name starts with `refactor/` and every declared ID on that branch is a REFAC ID.

## Assumed, not verified

- Pytest always reports a copied conftest load failure as exit code 4 with a single `ImportError while loading conftest '<path>'` line in stderr · the brief and one manual collect-only run on Windows · run the same layout on Linux and with other pytest versions.
- The path in that line is absolute and `os.path.relpath` from the scratch copy root yields the same relative path as `normalize_rel` used when recording `copied_conftest` · observed Windows backslash path under the copy root · confirm when pytest emits a relative path or a different drive letter form.
