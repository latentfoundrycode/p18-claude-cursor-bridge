# TASK-043 round 3 report

## Files changed

- `bridge/cursor-bridge/review-guard.py`
- `bridge/cursor-bridge/MANIFEST.json` (regenerated via `make-manifest.py`)

## Summary

Round 3 narrows and completes four round-2 regressions in `review-guard.py`: snapshot parse errors are caught as `ValueError` and `RecursionError` only so read failures still exit 2 via CANNOT VERIFY; a void write failure during git-error handling prints a GATE-INTEGRITY line containing `not recorded` before re-raising the git error; the launcher exit regex accepts up to ten digits for Windows crash codes; and tampered or unreadable rounds records at the end of `verify` print one fixed GATE-INTEGRITY sentence with the increment ID instead of forwarding `load_rounds`' message.

## Cause fixes (one sentence each)

1. **Cause 1:** `load_snapshot` now catches only `ValueError` and `RecursionError` around `json.load`, so `OSError` from an unreadable file reaches `main` as CANNOT VERIFY exit 2 while invalid JSON and deeply nested JSON still become an empty dict for the rewritten-snapshot path.
2. **Cause 2:** The `cmd_verify` handler that runs after flags are collected wraps `record_flagged_launch` in `try`/`except OSError`, prints that the flagged launch could not be voided (`not recorded`), then bare-raises so the original git failure is named.
3. **Cause 3:** `launch_info` matches `bridge-run: exit` with `(\d{1,10})(?!\d)` so a ten-digit Windows crash code is the last exit line.
4. **Cause 4:** When `load_rounds` returns an error at the end of `verify`, the guard prints the fixed sentence `the rounds record of <ID> was changed outside the guard or cannot be read: no reply and no verified mark` and no longer strips or forwards `load_rounds`' text.

## Done commands (last line each)

```
python -m pytest tests/test_bug039.py -q -p no:cacheprovider
49 passed in 70.40s (0:01:10)

python -m pytest tests/test_review_guard.py tests/test_review_guard_a4.py tests/test_review_guard_ceiling.py tests/test_bug036.py tests/test_hotfix25a_guard_scope_invisible.py tests/test_task032_supervisor_guard.py -q -p no:cacheprovider
189 passed in 175.51s (0:02:55)

python tools/dump-cli.py
(no output; exit 0)

python tools/make-manifest.py
make-manifest: version 2026.10.30d, 145 files hashed, VERSION + MANIFEST.json written

python tools/dump-cli.py --check
(no output; exit 0)

python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge
windowless-check: 35 file(s) scanned, 0 FAIL, 0 NOTE
```

## Assumed, not verified

Assumed, not verified: none.
