# TASK-006 round 6 report

## Files changed

- `bridge/cursor-bridge/workflow-check.py`
- `bridge/cursor-bridge/MANIFEST.json` (regenerated; `generated` stamp and the `workflow-check.py` hash)
- `docs/BUILDER_NOTES.md`
- `handoff/TASK-006-r6-report.md` (this report)

## Summary

Round 6 corrects `workflow-check.py` so `cells_of` removes exactly one leading `|` and one trailing `|` before splitting, and so file text is split into lines only at a line feed. A table row that starts or ends with `||` keeps its empty cell and fails the header width check (exit 2). A form feed, vertical tab, file/group/record separator, NEL, U+2028, or U+2029 stays inside the line, so it cannot hide a heading between two fence markers. The manifest is regenerated after the last edit under `bridge/`.

## What changed

- R6-1. `cells_of` strips surrounding whitespace, drops one leading `|` when present and one trailing `|` when present, then splits on `|` and strips each cell. The header and the separator use the same function, so a separator ending `||` fails the width check.
- R6-2. `file_lines` replaces every `str.splitlines()` of file text (`parse_table`, `heading_spans`, `check_status`). It splits only on `\n`. `read_utf8` already opens with universal newlines, so a carriage return is already a line feed. A final line feed does not add an empty line.

## Commands

A preliminary `python tools/make-manifest.py` (exit 0: version 2026.10.11d, 107 files hashed) was run after the last edit under `bridge/` and before command 3, so the suite would see the new `workflow-check.py` hash. Command 5 ran it again and set `generated` to `2026-10-16 23:12`. The hash of `workflow-check.py` (`d36e929a2a1bb29becd88543ca66d8ef8c2aae371246470a409b7f1bfc6432dc`) did not change between the passing run and that stamp. The suite was not started again after that stamp.

1. `python bridge/cursor-bridge/workflow-check.py bridge/cursor-bridge/workflow tests/fixtures/workflows/pass` — exit 0

```
RESULT: OK
```

2. `python -m pytest tests/test_workflow_check.py -q` — exit 0

```
123 passed, 1 skipped in 8.52s
```

The skip is `test_r014_unreadable_folder_stops_the_check` (Windows; the test requires a non-root POSIX user).

3. `python -m pytest tests -q` — exit 0

```
1075 passed, 21 skipped in 236.72s (0:03:56)
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
bridge-check: version 2026.10.11d (2026-10-16 23:12) at E:\p18-claude-cursor-bridge\Workspace\bridge
bridge-check: 107 OK, 0 STALE, 0 MISSING, 0 EXTRA
RESULT: SOURCES MATCH bridge 2026.10.11d
```

6. `git diff --stat` — exit 0. The report is untracked, so it is absent here; `git status --short` also shows `?? handoff/TASK-006-r6-report.md`.

```
 bridge/cursor-bridge/MANIFEST.json     |  4 ++--
 bridge/cursor-bridge/workflow-check.py | 31 +++++++++++++++++++++++++++----
 docs/BUILDER_NOTES.md                  |  2 ++
 3 files changed, 31 insertions(+), 6 deletions(-)
```

## Assumed, not verified

A file that ends in a line feed does not gain a final empty line · `file_lines` drops a trailing empty segment after `split("\n")`, which is what `str.splitlines()` did for `\n` and what the brief does not state · a fixture or sentence that says whether the last line feed is its own empty line.
