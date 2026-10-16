# TASK-006 round 4 report

## Files changed

- `bridge/cursor-bridge/workflow-check.py`
- `bridge/cursor-bridge/MANIFEST.json` (regenerated; `generated` stamp and the `workflow-check.py` hash)
- `docs/BUILDER_NOTES.md`
- `handoff/TASK-006-r4-report.md` (this report)

## Summary

Round 4 corrects `workflow-check.py` so a `types/` or `traits/` path that `os.path.lexists` says is absent is skipped, `is_link` returns false for `FileNotFoundError` and `NotADirectoryError` on both the `os.path.isjunction` branch and the Windows `lstat` fallback and true for any other `OSError`, and a fence is a line with zero to three leading spaces followed by three backticks. The manifest is regenerated after the last edit under `bridge/`.

## Commands

1. `python bridge/cursor-bridge/workflow-check.py bridge/cursor-bridge/workflow tests/fixtures/workflows/pass` — exit 0

```
RESULT: OK
```

2. `python -m pytest tests/test_workflow_check.py -q` — exit 0

```
103 passed, 1 skipped in 7.07s
```

The skip is `test_r014_unreadable_folder_stops_the_check` (Windows; the test requires a non-root POSIX user).

3. `python -m pytest tests -q` — exit 0

A first run, before the manifest was regenerated, exited 1: `38 failed, 1008 passed, 21 skipped, 9 errors`. Every failure and error was the install refusing a stale tree (`cursor-bridge/workflow-check.py (changed)`). A preliminary `python tools/make-manifest.py` (exit 0: version 2026.10.11d, 107 files hashed) brought the hash in line, and the suite was run again:

```
1055 passed, 21 skipped in 227.14s (0:03:47)
```

Step 5 then refreshed `generated` to `2026-10-16 22:16`. The suite was not started again after that stamp. The hash of `workflow-check.py` did not change between the passing run and that stamp.

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
bridge-check: version 2026.10.11d (2026-10-16 22:16) at E:\p18-claude-cursor-bridge\Workspace\bridge
bridge-check: 107 OK, 0 STALE, 0 MISSING, 0 EXTRA
RESULT: SOURCES MATCH bridge 2026.10.11d
```

6. `git diff --stat` — exit 0. The report is untracked, so it is absent here; `git status --short` also shows `?? handoff/TASK-006-r4-report.md`.

```
 bridge/cursor-bridge/MANIFEST.json     |  4 ++--
 bridge/cursor-bridge/workflow-check.py | 27 ++++++++++++++++++++-------
 docs/BUILDER_NOTES.md                  |  2 ++
 3 files changed, 24 insertions(+), 9 deletions(-)
```

## Assumed, not verified

Assumed, not verified: none
