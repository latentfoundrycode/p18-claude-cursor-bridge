# TASK-028 round-1 report

## Files changed

- `bridge/cursor-bridge/bridge-run.py`
- `bridge/cursor-bridge/conformance-check.py`
- `bridge/cursor-bridge/windowless-default.snapshot.md` (new)
- `bridge/cursor-bridge/settings.bridge.json`
- `bridge/cursor-bridge/MANIFEST.json` (regenerated)
- `tests/conftest.py`
- `tests/test_bridge_run_driver.py` (new)
- `tests/test_conformance_windowless.py` (new)
- `tests/test_allowlist.py`
- `docs/cli-reference.json`
- `docs/CLI_REFERENCE.md`

## Summary

This increment adds the `driver` kind to `bridge-run.py` with fail-closed validation for `python <program>` (programs under `run/supervisor/` or `~/.claude/cursor-bridge/mutation-run.py`), a 7200 s default ceiling with health and learning at exits 0 and 1, windowless starts unchanged, a frozen FIX-001 block in `windowless-default.snapshot.md` mirrored in `tests/conftest.py`, a `Windowless test suite` conformance floor, and the matching allow rule plus tests for R-039.

## Window-handle probe (a hint, KP-010)

Hint only (owner screen is the observation): `0 30208 30208 28688 5128`

The console window handle is 0 (no visible window). Four process ids followed the handle and launcher pid on the list.

## Verification

- Focused pytest list from the brief: 609 passed, 22 skipped.
- `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge/bridge-run.py bridge/cursor-bridge/conformance-check.py`: `windowless-check: 2 file(s) scanned, 0 FAIL, 0 NOTE`
- `python tools/dump-cli.py` and `python tools/dump-cli.py --check`: pass after regeneration.
- `python tools/make-manifest.py --version 2026.10.25a`: manifest includes `windowless-default.snapshot.md`.
- Full suite: `python -m pytest tests -q -p no:cacheprovider` — 2303 passed, 33 skipped; no extra failures outside the brief list.

## Mutation list

| Mutation | Test that caught it |
|---|---|
| `KINDS["driver"]` 7200 → 3600 | `test_r039_driver_ceiling_defaults` |
| Driver learning exits `(0, 1)` → `(0,)` only | `test_r039_driver_learning_from_exit_1` |
| `tests/conftest.py` token `windowless_kwargs` → `windowless_kwarg` | `test_r039_snapshot_matches_conftest` |
| `_supervisor_program_ok` forced false (manual) | `test_r039_accept_supervisor_relative` |
| `argv[1].startswith("-")` check removed (manual) | `test_r039_refuse_interpreter_options` |
| `bridge_env.is_link` always false (manual) | `test_r039_refuse_link_at_supervisor` |
| Skip driver kind branch when `BRIDGE_RUN_ALLOW_ANY=1` (manual) | `test_r039_refuse_program_outside_supervisor` with allow_any True |
| Driver health `rc in (0, 1)` → `rc == 0` only (manual) | `test_r039_driver_health_logged` parametrized code 1 |
| Remove `CREATE_NO_WINDOW` from Windows Popen flags (manual) | `test_r039_driver_grandchild_windowless` |
| Conftest missing `CREATE_NO_WINDOW` token (manual) | `test_r039_missing_bad_conftest` |
| Root `conftest.py` OK path disabled (manual) | `test_r039_ok_root_conftest` |
| Snapshot block altered by one character (manual) | `test_r039_snapshot_matches_conftest` |

## Full-suite environment observations

None beyond the brief’s expected skips; full suite green in this run.

## Assumed, not verified

Assumed, not verified: none.
