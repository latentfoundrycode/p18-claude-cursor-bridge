# TASK-015 round 4 report

## Files changed

- `bridge/cursor-bridge/session-start.py`
- `bridge/cursor-bridge/MANIFEST.json` (via `python tools/make-manifest.py`)
- `docs/cli-reference.json` (via `python tools/dump-cli.py`)
- `docs/CLI_REFERENCE.md` (via `python tools/dump-cli.py`)
- `handoff/TASK-015-r4-report.md`

## Summary

Round 4 hardens fail-open output from the session-start pointers part: table read reasons are printed only when they fully match the plain-character pattern (R4-1), exception type names in load and use-time lines only when they are plain identifiers otherwise `an exception` (R4-2), and the hook refuses to read tables unless the checker's `DEFAULT_OPEN` and `DEFAULT_REGISTRY` match the installed `workflow/open-list.md` and `workflow/extension-points.md` paths before the link test (R4-3); the module docstring documents every cannot-read line form and the install-mismatch threat model (R4-4).

## Mutation check

- (t) Round 3's three-character `safe_reason` back in place of R4-1's pattern: `test_r005_an_unreadable_open_list_or_checker_names_no_conditional_file_and_says_so[checker-newline]`
- (u) Type name printed as given in the use-time line only: `test_r005_an_unreadable_open_list_or_checker_names_no_conditional_file_and_says_so[checker-name]`
- (v) Installed-path comparison of R4-3 dropped: `test_r005_an_unreadable_open_list_or_checker_names_no_conditional_file_and_says_so[checker-elsewhere]`
- (w) Installed-path comparison on the open list only (registry check removed): none caught

## Verification commands

1. `git status` and `git log --oneline -1` — exit 0. Branch `task-010`, ahead of origin by 1; modified `session-start.py`, `MANIFEST.json`, `CLI_REFERENCE.md`, `cli-reference.json`; head `a685568 checkpoint before TASK-015 r4`.
2. `python -m pytest tests/test_session_start_module.py tests/test_session_start.py -q` — exit 0; `63 passed, 4 skipped in 13.68s`.
3. `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks tools` — exit 0; `windowless-check: 37 file(s) scanned, 0 FAIL, 0 NOTE`.
4. `python tools/make-manifest.py`, then `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` — exit 0; `make-manifest: version 2026.10.18a, 120 files hashed`; `bridge-check: 120 OK, 0 STALE, 0 MISSING, 0 EXTRA`; `RESULT: SOURCES MATCH bridge 2026.10.18a`.
5. `python tools/dump-cli.py`, then `python tools/dump-cli.py --check` — exit 0 (no output on `--check`).
6. `python bridge/cursor-bridge/workflow-check.py bridge/cursor-bridge/workflow tests/fixtures/workflows/pass` — exit 0; `RESULT: OK`.
7. `python -m pytest tests -q` — exit 0; `1846 passed, 33 skipped in 414.81s`.
8. `git status` and `git diff --stat` — exit 0; four files changed as listed above (71 insertions, 38 deletions in `session-start.py` and regenerated docs/manifest).

## Assumed, not verified

Assumed, not verified: none
