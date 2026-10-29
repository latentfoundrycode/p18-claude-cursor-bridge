# TASK-006 round 3 report

## Files changed

- `bridge/cursor-bridge/workflow-check.py`
- `bridge/cursor-bridge/MANIFEST.json` (regenerated; `generated` stamp and the `workflow-check.py` hash)
- `handoff/TASK-006-r3-report.md` (this report)

## Summary

Round 3 corrects `workflow-check.py` so a command-line usage error's argparse message is escaped, a table separator must have the header's cell count, a link under `types/` or `traits/` (including a dangling `types` or `traits` directory, and a link inside a type folder that is not a product type) is `FAIL (form)` and is not walked, trailing punctuation from `:;,.-` is stripped from a change heading's first word and `adding` and `setting` count as change words, a part name with surrounding whitespace is `form` and is not checked further, an unclosed fence and a heading with up to three leading spaces or a tab after `##` are `form`, and on Windows without `os.path.isjunction` a reparse point is still a link; the manifest was regenerated after the last edit under `bridge/`.

## Commands

1. `python bridge/cursor-bridge/workflow-check.py bridge/cursor-bridge/workflow tests/fixtures/workflows/pass` — exit 0

```
RESULT: OK
```

2. `python -m pytest tests/test_workflow_check.py -q` — exit 0

```
87 passed, 1 skipped in 10.22s
```

The skip is `test_r014_unreadable_folder_stops_the_check` (Windows; the test requires a non-root POSIX user).

3. `python -m pytest tests -q` — exit 0

```
1039 passed, 21 skipped in 227.45s (0:03:47)
```

This run was after a first `python tools/make-manifest.py` (exit 0: version 2026.10.11d, 107 files hashed), so the source-tree manifest test passed. Step 5 then refreshed `generated` to `2026-10-16 21:46`. The suite was not started again after that stamp.

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
bridge-check: version 2026.10.11d (2026-10-16 21:46) at <the Workspace>/bridge
bridge-check: 107 OK, 0 STALE, 0 MISSING, 0 EXTRA
RESULT: SOURCES MATCH bridge 2026.10.11d
```

6. `git diff --stat` — exit 0. The report is untracked, so it is absent here; `git status --short` also shows `?? handoff/TASK-006-r3-report.md`.

```
 bridge/cursor-bridge/MANIFEST.json     |  4 +-
 bridge/cursor-bridge/workflow-check.py | 89 ++++++++++++++++++++++++----------
 2 files changed, 65 insertions(+), 28 deletions(-)
```

## Assumed, not verified

- An `OSError` from `os.lstat`, in the Windows fallback used when `os.path.isjunction` is absent, counts the path as a link · this session's Python provides `os.path.isjunction`, and `test_r014_junction_detected_without_isjunction` removes it only for an existing junction and a real directory · a call of `is_link` on a path whose `lstat` raises.
- A part whose leading or trailing whitespace is a tab or another character `str.strip()` removes is invalid the same way a space is · the brief says whitespace and the fixtures use only U+0020 · a `Workflows` line whose part is bounded by a tab.
- A link whose own path is `types/<name>` where `<name>` is not a product-type key is `FAIL (form)` and not also `FAIL (d)` · the brief gives `(d)` to a folder of that name and `(form)` to a link, and the new test places the link inside a real directory · a root whose `types/not-a-type` entry is itself a link.
