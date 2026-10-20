# TASK-015 round 7 report

## Files changed

- `bridge/cursor-bridge/session-start.py` — R7-1 through R7-4 corrections.
- `bridge/cursor-bridge/MANIFEST.json` — regenerated via `python tools/make-manifest.py` after the last edit to `session-start.py`.
- `docs/cli-reference.json` — regenerated via `python tools/dump-cli.py` (docstring failing-open paragraph).
- `docs/CLI_REFERENCE.md` — regenerated via `python tools/dump-cli.py`.

## Summary

Round 7 tightens the session-start hook against a hand-edited checker inside the stated threat model: `pointer_paths_from_module` ignores non-exact-`str` lines and path segments so a str subclass cannot steer printed paths via `__radd__`; checker load and use run under discarded stdout/stderr redirection; handlers and `safe_exc_type_name` catch `BaseException` so `KeyboardInterrupt` and similar failures still yield the existing cannot-be-loaded or cannot-be-used lines; the module docstring documents that exceptions are caught and checker prints are discarded.

## Mutation check

| Mutation | What changed | Caught by |
|----------|--------------|-----------|
| (v1) Drop `type(line) is str` (R7-1) | Removed the line-type guard in `pointer_paths_from_module` | None — `type(p) is str` still blocks the supervisor's `_Sly` path segments, so `test_r007_a_pointer_line_that_is_not_a_plain_string_names_nothing` still passes on this platform |
| (v2) Use-time handler back to `(Exception, SystemExit)` | Only the `except` in `pointers_part` (load and `safe_exc_type_name` left as `BaseException`) | `test_r005_an_unreadable_open_list_or_checker_names_no_conditional_file_and_says_so[checker-interrupt]` |
| (v3) Drop stdout/stderr redirection during use (load kept) | Unwrapped `contextlib.redirect_stdout` / `redirect_stderr` around the checker-use block | `test_r007_what_the_checker_writes_is_not_the_hooks_output` |

After restoring all mutations, `git diff bridge/cursor-bridge/session-start.py` matched only the intended R7 diff (manifest and CLI reference separate).

## Verification commands

1. `git status` / `git log --oneline -1` — exit 0. Head `7e9a60a checkpoint before TASK-015 r7`; unstaged changes in `session-start.py`, `MANIFEST.json`, `docs/cli-reference.json`, and `docs/CLI_REFERENCE.md`.

2. `python -m pytest tests/test_session_start_module.py tests/test_session_start.py -q` — exit 0. `82 passed, 4 skipped in 19.11s` (skips: link cases this account cannot create).

3. `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks tools` — exit 0. `windowless-check: 37 file(s) scanned, 0 FAIL, 0 NOTE`

4. `python tools/make-manifest.py` — exit 0. `make-manifest: version 2026.10.18a, 120 files hashed, VERSION + MANIFEST.json written`

5. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` — exit 0. `120 OK, 0 STALE, 0 MISSING, 0 EXTRA` / `RESULT: SOURCES MATCH bridge 2026.10.18a`

6. `python tools/dump-cli.py` — exit 0 (docstring failing-open paragraph updated in generated reference).

7. `python tools/dump-cli.py --check` — exit 0.

8. `python bridge/cursor-bridge/workflow-check.py bridge/cursor-bridge/workflow tests/fixtures/workflows/pass` — exit 0. `RESULT: OK`

9. `python -m pytest tests -q` — exit 0. `1865 passed, 33 skipped in 408.00s (0:06:48)`

10. `git diff --stat` — `bridge/cursor-bridge/MANIFEST.json` (4 lines), `bridge/cursor-bridge/session-start.py`, `docs/CLI_REFERENCE.md` (7 lines), `docs/cli-reference.json` (2 lines).

## Assumed, not verified

Dropping only the `type(line) is str` guard does not fail the supervisor's R7-1 test on this run · the test's `_Sly` line still yields non-`str` path segments filtered by `type(p) is str` · a mutation that also removes the path-segment guard would be needed to observe a failure on this platform.
