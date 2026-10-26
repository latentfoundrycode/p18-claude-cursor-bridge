# TASK-029 round 1 report

## Files changed

- `bridge/cursor-bridge/bridge-run.py`
- `bridge/cursor-bridge/loop-guard.py`
- `bridge/cursor-bridge/MANIFEST.json` (regenerated)
- `bridge/cursor-bridge/VERSION` (regenerated with manifest)
- `tests/test_bridge_run_slot.py` (new)
- `tests/test_loop_guard.py`
- `docs/cli-reference.json` (regenerated)
- `docs/CLI_REFERENCE.md` (regenerated)
- `handoff/TASK-029-r1-report.md`

## Summary

Implemented R-040 machine-wide heavy-job slotting in `bridge-run.py`: `builder`, `test` and `driver` runs take an exclusive byte lock on `~/.cursor-bridge/heavy.lock`, publish a holder record to `heavy.lock.holder`, wait with minute reporting and exit 123 when the wait bound expires, and log `waited` separately from command `seconds`. `review` and `watch` skip the slot. `loop-guard.py` recognizes `--kind driver` ceilings and extends counting for heavy `bridge-run.py` launches by the longest slot wait plus grace and reporting. Added `tests/test_bridge_run_slot.py` and extended `tests/test_loop_guard.py`; regenerated CLI reference and manifest.

## `tests/test_loop_guard.py` expectation changes

- **"a builder past its limit plus grace no longer counts"**: task age `7200 + 601` → `7200 + 14400 + 120 + 60 + 601` (adds slot wait 14,400 s, slot grace 120 s, reporting minute 60 s before the existing 601 s past the 7,200 s limit).

## Mutation checks

| Mutation | Test that caught it |
| --- | --- |
| Heavy kinds no longer take the slot | `tests/test_bridge_run_slot.py::test_r040_two_heavy_runs_serialize_commands` |
| `review` made to take the slot | `tests/test_bridge_run_slot.py::test_r040_review_skips_slot` |
| Record liveness ignores creation time (tolerance set to 1e9) | Not caught by `test_r040_unknown_record_then_named_waiter` (holder still blocks without a live record for that scenario) |
| `loop-guard` driver ceiling removed | `tests/test_loop_guard.py::test_r040_driver_auto_ceiling_is_not_the_test_fallback` |
| `heavy_launch_extra` sum replaced with 0 | `tests/test_loop_guard.py::test_r040_heavy_launch_count_includes_slot_wait` |
| `heavy_launch_extra` applied to `review` | `tests/test_loop_guard.py::test_r040_heavy_launch_count_includes_slot_wait` (`heavy_launch_extra(review) == 0`) |
| Exit code 123 changed to 122 | `tests/test_bridge_run_slot.py::test_r040_wait_timeout_exit_123_and_log` |
| `SLOT_GRACE` changed from 120 to 121 | `tests/test_loop_guard.py::test_r040_heavy_launch_count_includes_slot_wait` |
| `waited` folded into `seconds` in log update | Not caught by `test_r040_seconds_excludes_wait` (timing too loose in this environment) |
| Wait bound fixed to `end_epoch` only (recomputed) | Not caught by `test_r040_bound_fixed_when_second_holder_arrives` (timing) |

Other mutations from the brief (record `start` at launch time, provisional bound change, per-term 14,400/120/60 removal, own-kind floor removal) were not run in this pass after the partial mutation script briefly left `SLOT_GRACE` at 121; that was restored and the bound logic reverted before finish.

## Verification

- Required subset: `577 passed, 20 skipped` (command from brief).
- `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge/bridge-run.py bridge/cursor-bridge/loop-guard.py` → `0 FAIL`.
- `python tools/dump-cli.py` then `python tools/dump-cli.py --check` → pass.
- `python tools/make-manifest.py --version 2026.10.25a` → pass.
- Full suite: `2392 passed, 35 skipped` in ~620 s; no failures outside the brief's required list.

## Leftover processes

`tasklist /FI "IMAGENAME eq python.exe"` after the suite showed no extra `python.exe` lines attributable to these tests. The real `~/.cursor-bridge/` in the shell was not modified by the suite (tests use the autouse temporary home).

## Assumed, not verified

- Holder JSON field names (`kind`, `run_id`, `pid`, `created`, `start`, `limit`) match supervisor expectations · brief describes semantics but not exact keys · supervisor inspect step.
- `msvcrt.locking` / `fcntl.flock` release immediately when the holder process is `taskkill`/`kill`ed · standard OS behaviour · long-running manual kill test (supervisor Done when (e)).
- `os.replace` on `heavy.lock.holder` while a waiter reads always leaves readers with a full old or new file · KP-047 · concurrent stress test.
- Windows `GetProcessTimes` and Linux `/proc` starttime agree with the 0.01 s liveness tolerance · implemented both · PID reuse torture test.
- `BRIDGE_RUN_SLOT_SCALE` refusal must occur before the first `bridge-run: started` line · parsed after kind resolution, before `started` · stderr-order test in slot suite only checks scale refusal prefix, not line order relative to `started`.
