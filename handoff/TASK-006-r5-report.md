# TASK-006 round 5 report

## Files changed

- `bridge/cursor-bridge/workflow-check.py`
- `bridge/cursor-bridge/MANIFEST.json` (regenerated; `generated` stamp and the `workflow-check.py` hash)
- `docs/BUILDER_NOTES.md`
- `handoff/TASK-006-r5-report.md` (this report)

## Summary

Round 5 corrects `workflow-check.py` so `collect` examines `types/` and `traits/` with `os.lstat` (a missing path is skipped; any other `OSError` is an `ERROR` line and exit 2), `is_link` classifies a path from one `os.lstat` on every Python (`S_ISLNK`, or on Windows `FILE_ATTRIBUTE_REPARSE_POINT`, failing closed on any `OSError` other than a missing path), and fences follow CommonMark: an opening run of at least three backticks or tildes, closed only by an equal or longer run of the same character with nothing after it but spaces or tabs. The manifest is regenerated after the last edit under `bridge/`.

## What changed

- R5-1. In `collect`, `os.lstat` on `ROOT/types` and `ROOT/traits` replaces `os.path.lexists`. `FileNotFoundError` and `NotADirectoryError` skip the layer. Any other `OSError` is recorded as `(path, strerror or "cannot be examined")` and the run ends `RESULT: not checked` with exit 2. A path `lstat` can see still goes to the link test.
- R5-2. `is_link` no longer calls `os.path.isjunction` or `os.path.islink`. It calls `os.lstat` once: missing path → `False`; other `OSError` → `True`; else `stat.S_ISLNK`, or on Windows a non-zero `st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT`.
- R5-3. `opening_fence` / `closing_fence` replace the three-backtick toggle. A backtick opening whose info string contains a backtick is not a fence. Inside a fence, a shorter run, the other character, or a run with text after it is content. An unclosed fence is still one `form` finding (R3-6).

## Commands

A preliminary `python tools/make-manifest.py` (exit 0: version 2026.10.11d, 107 files hashed) was run after the last edit under `bridge/` and before command 3, so the suite would see the new `workflow-check.py` hash. Command 5 ran it again and set `generated` to `2026-10-16 22:41`. The hash of `workflow-check.py` (`fd3313dc95ecaf8fd6bda61496c6dd70bcca737b6dcd882dcccddeac480c9172`) did not change between the passing run and that stamp. The suite was not started again after that stamp.

1. `python bridge/cursor-bridge/workflow-check.py bridge/cursor-bridge/workflow tests/fixtures/workflows/pass` — exit 0

```
RESULT: OK
```

2. `python -m pytest tests/test_workflow_check.py -q` — exit 0

```
112 passed, 1 skipped in 12.86s
```

The skip is `test_r014_unreadable_folder_stops_the_check` (Windows; the test requires a non-root POSIX user).

3. `python -m pytest tests -q` — exit 0

```
1064 passed, 21 skipped in 238.67s (0:03:58)
```

4. `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge` — exit 0

```
windowless-check: 30 file(s) scanned, 0 FAIL, 0 NOTE
```

5. `python tools/make-manifest.py` — exit 0

```
make-manifest: version 2026.10.11d, 107 files hashed, VERSION + MANIFEST.json written
```

`python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` — exit 0

```
bridge-check: version 2026.10.11d (2026-10-16 22:41) at <the Workspace>/bridge
bridge-check: 107 OK, 0 STALE, 0 MISSING, 0 EXTRA
RESULT: SOURCES MATCH bridge 2026.10.11d
```

6. `git diff --stat` — exit 0. The report is untracked, so it is absent here; `git status --short` also shows `?? handoff/TASK-006-r5-report.md`.

```
 bridge/cursor-bridge/MANIFEST.json     |   4 +-
 bridge/cursor-bridge/workflow-check.py | 106 ++++++++++++++++++++++-----------
 docs/BUILDER_NOTES.md                  |   2 +
 3 files changed, 75 insertions(+), 37 deletions(-)
```

## Assumed, not verified

Assumed, not verified: none
