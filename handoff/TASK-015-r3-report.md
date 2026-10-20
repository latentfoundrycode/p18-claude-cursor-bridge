# TASK-015 round 3 report

## Files changed

- `bridge/cursor-bridge/session-start.py`
- `bridge/cursor-bridge/MANIFEST.json` (via `python tools/make-manifest.py`)
- `docs/cli-reference.json` (via `python tools/dump-cli.py`)
- `docs/CLI_REFERENCE.md` (via `python tools/dump-cli.py`)
- `handoff/TASK-015-r3-report.md`

## Summary

Round 3 tightens fail-open behavior in the pointers part: the use-time handler catches `SystemExit` like other failures; table and read errors name files only by comparing checker paths to the installed open list and registry (never printing a returned absolute path), and reasons containing `/`, `\`, or `:` are replaced with `cannot be read`; before reading tables the hook refuses a linked `workflow/`, `open-list.md`, or `extension-points.md`; `KEY_PATTERN` and `POINTER_PATH` use `fullmatch`; the docstring documents these rules; and the redundant `and module_keys` guard was removed.

## Mutation check

- (o) Use-time handler back to `except Exception`: `test_r005_an_unreadable_open_list_or_checker_names_no_conditional_file_and_says_so[checker-exit]`
- (p) Unmapped table-error path printed as returned: `test_r005_an_unreadable_open_list_or_checker_names_no_conditional_file_and_says_so[checker-path]`
- (q) Reason printed as returned: `test_r005_an_unreadable_open_list_or_checker_names_no_conditional_file_and_says_so[checker-reason]`
- (r) Link test on `workflow/` before tables dropped: `test_r005_a_linked_workflow_folder_names_only_the_modules`
- (s) `KEY_PATTERN.fullmatch` back to `KEY_PATTERN.match`: none caught

## Verification commands

1. `git status` and `git log --oneline -1` — exit 0. Branch `task-010`, ahead of origin by 1; modified `session-start.py`, `MANIFEST.json`, `CLI_REFERENCE.md`, `cli-reference.json`; head `5bd31bd checkpoint before TASK-015 r3`.
2. `python -m pytest tests/test_session_start_module.py tests/test_session_start.py -q` — exit 0; `60 passed, 3 skipped in 11.02s` (after change; tree already carried supervisor r3 tests on round-2 code).
3. `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks tools` — exit 0; `windowless-check: 37 file(s) scanned, 0 FAIL, 0 NOTE`.
4. `python tools/make-manifest.py`, then `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` — exit 0; `make-manifest: version 2026.10.18a, 120 files hashed`; `bridge-check: 120 OK, 0 STALE, 0 MISSING, 0 EXTRA`; `RESULT: SOURCES MATCH bridge 2026.10.18a`.
5. `python tools/dump-cli.py`, then `python tools/dump-cli.py --check` — exit 0 (no output on `--check`).
6. `python bridge/cursor-bridge/workflow-check.py bridge/cursor-bridge/workflow tests/fixtures/workflows/pass` — exit 0; `RESULT: OK`.
7. `python -m pytest tests -q` — exit 0; `1843 passed, 32 skipped in 402.11s`.
8. `git status` and `git diff --stat` — exit 0; four files changed as listed above.

## Assumed, not verified

Assumed, not verified: none
