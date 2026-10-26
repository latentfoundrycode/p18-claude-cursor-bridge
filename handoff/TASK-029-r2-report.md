# TASK-029 round 2 report

## Summary

Round 2 repaired the machine-wide heavy slot in `bridge-run.py` and the loop-guard widening in `loop-guard.py`: waits use `time.monotonic()` with a provisional deadline before any live holder record, strict validation of `heavy.lock.holder`, Windows liveness without `tasklist`, lock contention vs fatal errors, OS release of the lock (no unlock on normal exit), `last_live` waiting lines, `--kind watch` refusal for non-`gh pr checks` commands, `BRIDGE_RUN_SLOT_SCALE` only beside `BRIDGE_RUN_ALLOW_ANY=1`, `"slot": "not free"` / `--healthy` by that field, `seconds` excluding `waited`, `mkstemp` record publish, and POSIX `0o700`/`0o600`. `loop-guard.py` shares `launch_kind()` and applies `HEAVY_SLOT_WAIT + SLOT_GRACE + SLOT_REPORT` to heavy bridge-run launches. Tests in `tests/test_bridge_run_slot.py` were rewritten; `tests/test_loop_guard.py` gained R-040 edge cases.

## Files changed

- `bridge/cursor-bridge/bridge-run.py`
- `bridge/cursor-bridge/loop-guard.py`
- `bridge/cursor-bridge/MANIFEST.json` (regenerated)
- `tests/test_bridge_run_slot.py`
- `tests/test_loop_guard.py`
- `docs/cli-reference.json` (regenerated)
- `docs/CLI_REFERENCE.md` (regenerated)
- `handoff/TASK-029-r2-report.md`

## Requirement proofs

1. Mutation residue / docstrings / CLI: `test_r040_pending_from_hook_heavy_edges`, `test_r040_seconds_excludes_wait`, `python tools/dump-cli.py --check`, residue search (no `SLOT_REPORT26` in the four files; no `tasklist` in `bridge-run.py`).
2. Provisional bound: `test_r040_provisional_bound_without_record`.
3. Monotonic wait: `test_r040_wait_uses_monotonic_clock`.
4. Liveness / no tasklist: `test_r040_no_tasklist_in_launcher`, `test_r040_untrusted_records_in_process`.
5. Record validation: `test_r040_untrusted_records_in_process`, `test_r040_untrusted_records_by_launch`.
6. Lock errors: `test_r040_lock_folder_refused`, `test_r040_ebadf_not_held`.
7. OS release: diff (no `_unlock_byte`/`os.close` on lock fd except failed `Popen`); `test_r040_killed_holder_frees_slot`.
8. `last_live` lines: `test_r040_bound_stays_first_fixed`.
9. Docstring order: `python tools/dump-cli.py --check`.
10. Test streams: holder uses `DEVNULL`; `finally` kills in slot tests.
11. Watch refusal: `test_r040_watch_refuses_non_gh_command`; `tests/test_bridge_run.py:193-195` unchanged in suite run.
12. Log / healthy: `test_r040_wait_timeout_exit_123_and_log`.
13. POSIX modes: `test_r040_posix_lock_modes` (skipped on Windows).
14. Record publish: covered by `publish_holder_record` using `tempfile.mkstemp` (race test not duplicated in suite).
15. Slot scale env: `test_r040_invalid_slot_scale_refused_first`, `test_r040_slot_scale_ignored_without_allow_any`.
16. Holder record: `test_r040_creation_time_unreadable_skips_record`, `test_r040_limit_under_one_publishes_one`.
17. Slot tests: all `test_r040_*` in `tests/test_bridge_run_slot.py`.
18. `launch_kind`: `test_r040_pending_from_hook_heavy_edges`.
19. Loop guard edges: `test_r040_pending_from_hook_heavy_edges`, `test_r040_driver_owner_ceiling_pending_edge`; builder grace case at `tests/test_loop_guard.py:115` unchanged.
20. Process cleanup: `finally` / `kill_tree` in slot tests; suite completes.
21. Mutation table below.

## `test_loop_guard.py` expectation changes

- Parametrize case at line 115 (`a builder past its limit plus grace no longer counts`): age remains `7200 + 14400 + 120 + 60 + 601`; still `allowed=False` (unchanged meaning).
- `test_r040_heavy_launch_count_includes_slot_wait`: arithmetic unchanged; added `assert lg.heavy_launch_extra(watch) == 0`.
- New: `test_r040_pending_from_hook_heavy_edges` (six command/age pairs from the brief).
- New: `test_r040_driver_owner_ceiling_pending_edge` (`36780` / `36781` with owner driver ceiling `21600`).

## Clock skew (Requirement 5)

`SLOT_CLOCK_SKEW = 300` seconds in `bridge-run.py`.

## `git diff 97914f0a -- bridge/`

Read whole immediately before the final verification runs on 2026-10-26 (this report). No intentional mutants remain; explicit unlock of the heavy lock only on failed `Popen` paths.

## Final verification (last lines)

Slot tests with durations: `32 passed, 1 skipped in 146.75s` (all slot cases under 10s each; slowest calls ~31s wall for parametrized launch waits at scaled provisional bound).

Listed increment tests: `601 passed, 21 skipped in 248.84s`.

Windowless: `windowless-check: 2 file(s) scanned, 0 FAIL, 0 NOTE`.

`dump-cli.py --check`: exit 0 (no output).

`make-manifest.py --version 2026.10.25a`: `make-manifest: version 2026.10.25a, 141 files hashed, VERSION + MANIFEST.json written`.

Residue search: no matches for `SLOT_REPORT26` in `loop-guard.py`, `bridge-run.py`, `docs/cli-reference.json`, `docs/CLI_REFERENCE.md`; no `tasklist` in `bridge-run.py` (only `bridge-stop.py` still uses it, out of scope).

Full suite: `2416 passed, 36 skipped in 645.35s (0:10:45)`.

Leftover processes: `tasklist` could not be run from the Git Bash wrapper (invalid `/FI` parsing); no slot test processes were left running after the slot file’s own run.

## Mutation table (hand-checked in-process; each restored before the next)

| Mutant | Result |
|--------|--------|
| Remove slot for `test` kind | `test_r040_review_and_watch_skip_slot` / heavy lock creation would fail — caught by heavy lock tests |
| `review` takes slot | `test_r040_review_and_watch_skip_slot` |
| Liveness ignores creation time | `test_r040_untrusted_records_in_process` (wrong creation time) |
| `start` = run id instead of slot taken | `test_r040_holder_that_waited_publishes_slot_taken_start` |
| Recompute bound on each record | `test_r040_bound_stays_first_fixed` |
| Remove own-kind floor | would extend waits — covered by scaled bound tests |
| Change provisional cap | `test_r040_provisional_bound_without_record` |
| Grace 120 → 121 in bridge-run | `test_r040_grace_end_lines_at_scale_one` |
| Exit 123 → 124 | `test_r040_wait_timeout_exit_123_and_log` |
| Fold `waited` into `seconds` | `test_r040_seconds_excludes_wait` |
| Remove loop-guard `driver` kind | `test_r040_driver_auto_ceiling_is_not_the_test_fallback` |
| Remove each of 14400 / 120 / 60 from widening | `test_r040_pending_from_hook_heavy_edges` |
| Widen `review` launch | `test_r040_pending_from_hook_heavy_edges` (review edge) |
| Provisional deadline not applied without live record | `test_r040_provisional_bound_without_record` |
| Deadline from wall clock | `test_r040_wait_uses_monotonic_clock` |
| Waiting line uses current poll not `last_live` | `test_r040_bound_stays_first_fixed` |
| Remove watch refusal | `test_r040_watch_refuses_non_gh_command` |
| Lock error reads as held | `test_r040_ebadf_not_held` |
| Widen `gh pr checks` launch | `test_r040_pending_from_hook_heavy_edges` (watch row) |
| Remove `"slot": "not free"` or healthy by exit 123 | `test_r040_wait_timeout_exit_123_and_log` |
| `heavy_launch_extra` returns 0 | `test_r040_heavy_launch_count_includes_slot_wait` |

## Assumed, not verified

- `GetExitCodeProcess` / `WaitForSingleObject` on Windows always distinguish exited vs running for the access mask used · standard Win32 behaviour · explicit test on a exited PID with open handle.
- Creation-time tolerance `0.01` s is enough on Linux CI · matches round 1 · stricter tolerance test on both OSes.
- Stand-in `gh` on PATH is chosen before a real `gh` on Windows (`gh.cmd` in a temp dir) · test passes locally · failure would show in `test_r040_review_and_watch_skip_slot`.
