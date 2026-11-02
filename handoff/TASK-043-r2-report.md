# TASK-043 round 2 report

## Files changed
- bridge/cursor-bridge/review-guard.py
- bridge/cursor-bridge/MANIFEST.json (regenerated)
- docs/cli-reference.json (regenerated)
- docs/CLI_REFERENCE.md (regenerated)

## Summary
Round 2 closes five review-guard gaps left after TASK-043 round 1: rewritten snapshots no longer trust tampered `taken` for voiding, tampered rounds records fail closed at the end of verify, flags survive a mid-verify git failure, hooks path points at a process-local temp directory outside the repo, and oversized exit lines in `.err` no longer crash `launch_info`. All `tests/test_bug039.py` and listed guard suites pass; generators and windowless-check succeed with VERSION unchanged at 2026.10.30d.

## Cause 1 (site 1)
At the rewritten-snapshot return, `record_flagged_launch` is called with `snap=None` and void eligibility uses the hash-checked round entry's `time` via `_launch_time_ge_round`; authentic snapshots still compare against `taken` without `isinstance` guards, and `load_snapshot` maps invalid or non-object JSON to `{}` so verify and premerge reach the rewritten path without traceback.

## Cause 2 (site 2)
The end of `cmd_verify` always calls `load_rounds(..., seed=False)` once for parsed review names; a tamper error prints `review-guard: GATE-INTEGRITY - …` containing `rounds record`, skips reply and mark, and returns 1, while a missing record file remains a non-error and reply write stays gated on `os.path.isfile(rpath)`.

## Cause 3 (site 5)
Steps 2–4 of `cmd_verify` run inside a `try` that on `RuntimeError`, `TimeoutExpired`, or `OSError` prints collected `GATE-INTEGRITY` lines, calls `record_flagged_launch` with the authentic snapshot when any flag exists, and re-raises so `main` still exits 2 with CANNOT VERIFY.

## Cause 4 (site 6)
`no_hooks_dir` creates one empty `tempfile.mkdtemp` directory per process, caches it in `_NO_HOOKS`, registers `atexit` cleanup with ignored `OSError`, and no longer uses `.git/bridge/no-hooks`.

## Cause 5 (site 7)
`launch_info` matches exit codes with `bridge-run: exit (\d{1,9})(?!\d)` so overlong digit runs are ignored and search continues upward without `ValueError`.

## Command results (last line each)
```
python -m pytest tests/test_bug039.py -q -p no:cacheprovider
39 passed in 59.87s

python -m pytest tests/test_review_guard.py tests/test_review_guard_a4.py tests/test_review_guard_ceiling.py tests/test_bug036.py tests/test_hotfix25a_guard_scope_invisible.py tests/test_task032_supervisor_guard.py -q -p no:cacheprovider
189 passed in 200.94s (0:03:20)

python tools/dump-cli.py
(exit 0, no stdout)

python tools/make-manifest.py
make-manifest: version 2026.10.30d, 145 files hashed, VERSION + MANIFEST.json written

python tools/dump-cli.py --check
(exit 0, no stdout)

python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge
windowless-check: 35 file(s) scanned, 0 FAIL, 0 NOTE
```

## Assumed, not verified
Assumed, not verified: none
