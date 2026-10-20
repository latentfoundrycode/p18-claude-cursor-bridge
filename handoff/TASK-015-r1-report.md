# TASK-015 round 1 report

## Files changed

- `bridge/cursor-bridge/session-start.py`
- `bridge/cursor-bridge/MANIFEST.json` (via `python tools/make-manifest.py`)
- `docs/cli-reference.json` (via `python tools/dump-cli.py`)
- `docs/CLI_REFERENCE.md` (via `python tools/dump-cli.py`)
- `handoff/TASK-015-r1-report.md`

## Summary

Replaced `PHASE_SECTIONS` with `PHASE_MODULES` and rewrote the pointers part of `session-start.py` so that after compaction, resume, or fork the hook names each current-phase module under `~/.claude/cursor-bridge/workflow/phases/` (read whole), optional `Sub-files:` / `Variants:` paths from those modules, conditional workflow files that exist and touch the phase (type, then sub-type, then traits in open-list order), and unchanged convention lines; unknown phases get a map pointer to `## The phase modules` in the core; `building` and `changing` annotate `project-end` with the last-stage note; digest behaviour is unchanged via `read_digest`; the installed `workflow-check.py` is loaded by path only when pointer lines or classified `Workflows:` lines need it, with a single fail-open line when load or table parse fails.

## Mutation checks

| Mutation | Caught by |
|---|---|
| (a) Drop the project-end note | `test_r005_project_end_is_named_for_the_last_stage_close` (2 cases) |
| (b) Stop validating pointer-line paths | `test_r005_a_pointer_line_names_no_file_outside_its_module_folder` |
| (c) Order conditional files alphabetically by trait key | `test_r034_the_conditional_files_follow_the_order_additions_apply_in`, `test_r005_a_file_two_parts_share_is_named_once_in_the_first_parts_place`, `test_r005_the_conditional_files_that_touch_the_phase_are_named_after_its_modules` |
| (d) Count change headings inside fenced blocks | `test_r005_the_conditional_files_that_touch_the_phase_are_named_after_its_modules` (building case), `test_r005_a_named_workflow_that_is_not_written_is_not_named` |
| (e) Name a file two parts share twice | `test_r005_a_file_two_parts_share_is_named_once_in_the_first_parts_place` |
| (f) Name a type file when it does not exist | **No test caught** (38 passed) |
| (g) Print each module with a line range | Fifteen failures across `test_r005_each_phase_names_its_modules_in_order_and_its_conventions` (8), `test_both_parts_fit_under_the_cap_for_every_phase_on_a_realistic_status_file` (7), and related `lines ` assertions |

## Verification

1. `git status` / `git log --oneline -1`: exit 0; clean tree; `5146889 checkpoint before TASK-015`.
2. `python -m pytest tests/test_session_start_module.py tests/test_session_start.py -q` before change: exit 1; `29 failed, 9 passed in 5.45s`. After change: exit 0; `38 passed in 6.25s`.
3. `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks tools`: exit 0; `windowless-check: 37 file(s) scanned, 0 FAIL, 0 NOTE`.
4. `python tools/make-manifest.py`: exit 0; `make-manifest: version 2026.10.18a, 120 files hashed, VERSION + MANIFEST.json written`. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`: exit 0; `RESULT: SOURCES MATCH bridge 2026.10.18a` / `RESULT: OK`.
5. `python tools/dump-cli.py`: exit 0. `python tools/dump-cli.py --check`: exit 0.
6. `python bridge/cursor-bridge/workflow-check.py bridge/cursor-bridge/workflow tests/fixtures/workflows/pass`: exit 0 (no FAIL output).
7. `python -m pytest tests -q`: exit 0; `1821 passed, 29 skipped in 395.13s (0:06:35)`.
8. `git status` / `git diff --stat`: modified `session-start.py`, `MANIFEST.json`, `CLI_REFERENCE.md`, `cli-reference.json`, plus this report; tests unchanged.

## Assumed, not verified

- Fail-open wording uses `cannot be loaded (<ExceptionName>)` or `read_utf8` / `load_tables` path-and-reason strings from the installed checker, matching inventory-check style; no dedicated test asserts the exact line when the open list is unreadable.
- A `Sub-files:` / `Variants:` line with a trailing `;` and no path after it is ignored via empty split segments; no test covers that trailing semicolon.
- `sys.dont_write_bytecode = True` around `exec_module` for the installed checker is assumed sufficient to avoid `__pycache__` under the test home; not probed on this Python build beyond tests passing.
- When `workflow-check.py` loads but `load_tables` fails, pointer-line files are still suppressed even though fence parsing could work without tables; the brief groups both under Requirement 7.
