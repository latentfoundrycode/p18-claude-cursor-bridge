# TASK-008 r1 report

## Files changed

- `bridge/cursor-bridge/workflow-check.py` — added `check_placement` only.
- `bridge/cursor-bridge/inventory-check.py` — check 6, `WORKFLOWS LINE`, after the status-length cap.
- `bridge/cursor-bridge/conformance-check.py` — one `Workflows line` row after the records-file loop.
- `bridge/cursor-bridge/MANIFEST.json` — regenerated; the three program hashes and the `generated` stamp.
- `docs/BUILDER_NOTES.md` — one dated line on the Done order and the stamp check.
- `handoff/TASK-008-r1-report.md` — this report.

`bridge/cursor-bridge/VERSION` was rewritten by `tools/make-manifest.py` and is not in the diff.

## Summary

`check_placement` in `workflow-check.py` reports one `place` finding when Workflows lines are not one unbroken run directly after the first `Phase: ` line, and reports nothing when the line is missing. `inventory-check.py` and `conformance-check.py` each load `workflow-check.py` from their own folder, build its tables, and call `check_status` and `check_placement`. Findings whose code is `f` or `FLAG` are dropped, so an unwritten type or trait is valid. A missing line, a malformed line, a misplaced line, and a checker or rule file that cannot be loaded are failures; printed names and reasons go through `escape_field` and then ASCII backslashreplace.

## Commands

Run from the repository root, in the Done order. Step 4 exited 1 because the manifest still described the previous program bytes. Step 6 regenerated it. The suite was then run again and exited 0. That second run is recorded after the ordered commands.

1. `python bridge/cursor-bridge/inventory-check.py` — exit 0. No `WORKFLOWS LINE:` line.

```
note: status: 36 lines / 5147 chars (cap 120 / 12000)
note: changes: docs/CHANGES.md not found (absorption not checked)
note: resources listed but read by no tracked code (fine for accounts/tools): CLI, OSV, SEMGREP_APP_TOKEN, SOCKET_CLI_ORG_SLUG, SOCKET_ORG_SLUG
RESULT: OK
```

2. `python -m pytest tests/test_workflows_line_check.py -q` — exit 0. `30 passed in 5.39s`.

3. `python -m pytest tests/test_workflow_check.py tests/test_conformance_check.py -q` — exit 0. `142 passed, 1 skipped in 15.36s`.

4. `python -m pytest tests -q` — exit 1. `38 failed, 1060 passed, 21 skipped, 9 errors in 168.64s`. Every failure and error was an install or rollback test refusing the tree as not release `2026.10.11d` as stamped, naming `conformance-check.py`, `inventory-check.py`, and `workflow-check.py` changed, or `bridge-check` reporting those three files `STALE`.

5. `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge` — exit 0. `windowless-check: 30 file(s) scanned, 0 FAIL, 0 NOTE`.

6. `python tools/make-manifest.py` — exit 0. `make-manifest: version 2026.10.11d, 107 files hashed, VERSION + MANIFEST.json written`. Then `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` — exit 0. `RESULT: SOURCES MATCH bridge 2026.10.11d` (`107 OK, 0 STALE, 0 MISSING, 0 EXTRA`).

7. `git diff --stat` — exit 0. Taken before this report and `docs/BUILDER_NOTES.md` existed:

```
 bridge/cursor-bridge/MANIFEST.json        |  8 ++--
 bridge/cursor-bridge/conformance-check.py | 66 +++++++++++++++++++++++++++++++
 bridge/cursor-bridge/inventory-check.py   | 66 +++++++++++++++++++++++++++++++
 bridge/cursor-bridge/workflow-check.py    | 31 +++++++++++++++
 4 files changed, 167 insertions(+), 4 deletions(-)
```

After `docs/BUILDER_NOTES.md` was written, `git diff --stat` was exit 0 and listed those four files plus `docs/BUILDER_NOTES.md` (`5 files changed, 169 insertions(+), 4 deletions(-)`). This report is untracked, so it does not appear in `git diff --stat`; `git status --short` shows `?? handoff/TASK-008-r1-report.md`.

After step 6, `python -m pytest tests -q` — exit 0. `1107 passed, 21 skipped in 233.79s`.

## Assumed, not verified

- The `Workflows line` row is the first row after the records-file loop and before the `project.json` content checks. · The brief says "among the records rows (after the loop over the record files)" and does not name the `project.json` block that follows. · A test that asserts that row's position in the printed list, not only the floor name.
- Any exception while loading `workflow-check.py` is reported as `cannot be loaded (<type(err).__name__>)`, including `FileNotFoundError` from `exec_module` on a missing file and `ImportError` when the spec or its loader is missing. · The brief says "absent or raises while loading" and to print the exception class name, without listing the classes. · The not-checked line for a missing `workflow-check.py`, reading the class name in parentheses; the supervisor test only requires the words `cannot be loaded`.
- When `workflow-check.py` cannot be loaded, that reason is not passed through `escape_field`, only through ASCII `backslashreplace`. · `escape_field` belongs to the module that failed to load. · A load-failure path or exception class that contains a non-ASCII character, compared with `escape_field` then `backslashreplace`.
- An exception after a successful load is a not-checked reason `<path to workflow-check.py>: <exception class name>`, without the words `cannot be loaded`. · The brief reserves `cannot be loaded` for the load itself, and says no exception may escape. · A `workflow-check.py` that loads and whose `check_status` raises.
- If `conformance-check.py`'s `read` of an existing `docs/PROJECT_STATUS.md` returns `None`, the text judged is empty, so the outcome is missing. · `read` returns `None` on `OSError` and no reason, and the brief's not-checked causes are the checker and the rule files. · A `PROJECT_STATUS.md` that `os.path.isfile` accepts and that `open` raises `OSError` for.
- The inventory missing line encodes the slash-normalized `--status` argument with ASCII `backslashreplace`. · Acceptance requires ASCII output, and the brief's missing line is that argument with `\` turned into `/`. · A `--status` path containing a non-ASCII character; an ASCII path is unchanged, which is what the supervisor test compares.
