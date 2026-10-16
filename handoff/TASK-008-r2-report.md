# TASK-008 r2 report

## Files changed

- `bridge/cursor-bridge/inventory-check.py` — `judge_workflows_line` only.
- `bridge/cursor-bridge/conformance-check.py` — `judge_workflows_line` only.
- `bridge/cursor-bridge/MANIFEST.json` — regenerated; hashes of those two programs and the `generated` stamp.
- `docs/BUILDER_NOTES.md` — one dated line for this round.
- `handoff/TASK-008-r2-report.md` — this report.

`bridge/cursor-bridge/workflow-check.py` is unchanged. `tools/make-manifest.py` rewrote `bridge/cursor-bridge/VERSION`; that file is not in the diff.

## Summary

Both `judge_workflows_line` functions now set `sys.dont_write_bytecode` to `True` only while `workflow-check.py` is loaded, and restore the previous value in a `finally`. The checker is taken from `os.path.dirname(os.path.realpath(__file__))`. `field` calls `escape_field` directly, so a loaded module without it makes a field-printing check `not-checked`. Load and post-load handlers catch `SystemExit` as well as `Exception`; the post-load reason is `<path>: <exception class>` through `ascii_text` only. `KeyboardInterrupt` is not caught. The program docstrings are unchanged.

## Commands

Run from the repository root, in the Done order.

1. `python -m pytest tests/test_workflows_line_check.py -q` — exit 0. `39 passed, 2 skipped in 5.88s`. The two skips are `test_r015_checker_is_found_beside_the_real_file_not_the_link` (inventory-check and conformance-check): `WinError 1314`, a required privilege is not held by the client, so the platform refused the symbolic link.

2. `python -m pytest tests/test_workflow_check.py tests/test_conformance_check.py tests/test_text_consistency.py -q` — exit 0. `153 passed, 1 skipped in 13.88s`.

3. `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge` — exit 0. `windowless-check: 30 file(s) scanned, 0 FAIL, 0 NOTE`.

4. `python tools/make-manifest.py` — exit 0. `make-manifest: version 2026.10.11d, 107 files hashed, VERSION + MANIFEST.json written`. Then `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` — exit 0. `RESULT: SOURCES MATCH bridge 2026.10.11d` (`107 OK, 0 STALE, 0 MISSING, 0 EXTRA`).

5. `python -m pytest tests -q` — exit 0. `1116 passed, 23 skipped in 238.77s`.

6. `git diff --stat` — exit 0.

```
 bridge/cursor-bridge/MANIFEST.json        |  6 +++---
 bridge/cursor-bridge/conformance-check.py | 15 +++++++++------
 bridge/cursor-bridge/inventory-check.py   | 15 +++++++++------
 docs/BUILDER_NOTES.md                     |  2 ++
 4 files changed, 23 insertions(+), 15 deletions(-)
```

This report is untracked, so it does not appear in `git diff --stat`. `git status --short` shows `?? handoff/TASK-008-r2-report.md`.

## Assumed, not verified

- On this host, `os.path.realpath` of a program started through a symbolic link is the target file, so `workflow-check.py` and its rule files are loaded from the directory of the real program, not from the directory of the link. · Creating that link failed with `WinError 1314`, and both parametrizations of `test_r015_checker_is_found_beside_the_real_file_not_the_link` skipped. · Re-running that test where creating a symbolic link is allowed.
