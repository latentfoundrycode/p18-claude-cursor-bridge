# BUG-041 round 1 report

## Files changed

- `bridge/cursor-bridge/review-guard.py`
- `bridge/cursor-bridge/MANIFEST.json`

## Summary

When a reviewer deletes `.git/bridge/review-<nnn>.json` but the FB-037 hash copy outside the checkout remains, `load_snapshot` now returns an empty dict (with `snap_hash` `None`) instead of CANNOT VERIFY exit 2, and `snapshot_rewritten` detects the missing snapshot file after reading the copy and returns `"rewritten"` with a GATE-INTEGRITY line containing `deleted` and both paths. `verify` and `premerge` therefore use their existing GATE-INTEGRITY paths: exit 1, no restore, void where applicable. Cases with no snapshot and no copy, or both deleted, still CANNOT VERIFY exit 2.

## How the change addresses the named cause

The defect was early `None` from `load_snapshot` before `snapshot_rewritten` ran, so the standing hash copy was never consulted. The fix branches on `os.path.isfile` for the hash copy when the snapshot file is absent, allowing the rewritten handler to run and treat deletion like integrity failure.

## Command last lines

```
python -m pytest tests/test_bug041.py -q -p no:cacheprovider
8 passed in 8.83s

python -m pytest tests/test_bug039.py -q -p no:cacheprovider
50 passed in 72.44s (0:01:12)

python -m pytest tests/test_review_guard.py tests/test_review_guard_a4.py tests/test_review_guard_ceiling.py tests/test_bug036.py tests/test_hotfix25a_guard_scope_invisible.py tests/test_task032_supervisor_guard.py -q -p no:cacheprovider
189 passed in 177.26s (0:02:57)

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

Assumed, not verified: none
