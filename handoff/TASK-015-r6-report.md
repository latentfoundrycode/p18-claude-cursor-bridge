# TASK-015 round 6 report

## Files changed

- `bridge/cursor-bridge/session-start.py` — R6-1 through R6-3 corrections.
- `bridge/cursor-bridge/MANIFEST.json` — regenerated via `python tools/make-manifest.py` after the last edit to `session-start.py`.

`docs/cli-reference.json` and `docs/CLI_REFERENCE.md` were not modified by `python tools/dump-cli.py` (no CLI surface change).

## Summary

Round 6 hardens the session-start hook against hostile checker output without changing observable behavior for legitimate installs: `safe_exc_type_name` now guards the `type(err).__name__` read so a metaclass that raises on `__name__` still yields `an exception` and the pointers part prints; `safe_reason` and `conditional_candidates` accept only exact `str` keys and reasons (not subclasses whose `__str__` could smuggle paths); `workflow_table_link_error` uses `installed_open_list_path()` and `installed_registry_path()` like the table read path; the manifest was regenerated so bridge-check reports SOURCES MATCH.

## Mutation check

| Mutation | What changed | Caught by |
|----------|--------------|-----------|
| (z1) R6-1 guard removed | `safe_exc_type_name` reads `__name__` without try/except | `test_r005_an_unreadable_open_list_or_checker_names_no_conditional_file_and_says_so[checker-name-raises]` and `[checker-load-name-raises]` |
| (z2) `type(reason) is str` → `isinstance(reason, str)` | `safe_reason` | `test_r005_an_unreadable_open_list_or_checker_names_no_conditional_file_and_says_so[checker-reason-subclass]` |
| (z3) Drop `type(type_key) is str` for type key only | first branch in `conditional_candidates` | `test_r006_a_table_key_that_is_not_a_plain_string_names_no_file` |

After restoring all mutations, `git diff bridge/cursor-bridge/session-start.py` matched only the intended R6 diff (13 insertions, 10 deletions with manifest separate).

## Verification commands

1. `git status` / `git log --oneline -1` — exit 0. Head `c74e710 checkpoint before TASK-015 r6`; unstaged changes in `session-start.py` and `MANIFEST.json` only (not a clean tree after work).

2. `python -m pytest tests/test_session_start_module.py tests/test_session_start.py -q` — exit 0. `73 passed, 4 skipped in 17.84s` (skips: folder/file link cases this account cannot create).

3. `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks tools` — exit 0. `windowless-check: 37 file(s) scanned, 0 FAIL, 0 NOTE`

4. `python tools/make-manifest.py` — exit 0. `make-manifest: version 2026.10.18a, 120 files hashed, VERSION + MANIFEST.json written`

5. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` — exit 0. `120 OK, 0 STALE, 0 MISSING, 0 EXTRA` / `RESULT: SOURCES MATCH bridge 2026.10.18a`

6. `python tools/dump-cli.py` — exit 0 (no doc output changes).

7. `python tools/dump-cli.py --check` — exit 0.

8. `python bridge/cursor-bridge/workflow-check.py bridge/cursor-bridge/workflow tests/fixtures/workflows/pass` — exit 0. `RESULT: OK`

9. `python -m pytest tests -q` — exit 0. `1856 passed, 33 skipped in 402.20s`

10. `git diff --stat` — `bridge/cursor-bridge/MANIFEST.json` (4 lines), `bridge/cursor-bridge/session-start.py` (19 lines touched).

## Assumed, not verified

Assumed, not verified: none.
