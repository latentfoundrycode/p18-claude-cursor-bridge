# TASK-006 round 2 report

## Files changed

- `bridge/cursor-bridge/workflow-check.py`
- `bridge/cursor-bridge/MANIFEST.json` (regenerated; `generated` stamp and the `workflow-check.py` hash)
- `handoff/TASK-006-r2-report.md` (this report)

## Summary

Round 2 corrects `workflow-check.py` so a misspelt change word is a malformed heading, every input is read as UTF-8 with a leading byte-order mark dropped, an unlistable folder exits 2, a symbolic link or Windows junction is `FAIL (form)` and is not opened or walked into, trait lists split on exactly a comma and one space, a part prefix is judged only in the head text, an empty head name is `form`, each distinct unwritten trait is flagged once, a table without a separator row cannot run, a usage error ends with `RESULT: not checked`, printed fields escape non-printable characters, and each heading section ends at the next heading's index; the manifest was regenerated after the last edit under `bridge/`.

## Commands

1. `python bridge/cursor-bridge/workflow-check.py bridge/cursor-bridge/workflow tests/fixtures/workflows/pass` — exit 0

```
RESULT: OK
```

2. `python -m pytest tests/test_workflow_check.py -q` — exit 0

```
75 passed, 1 skipped in 6.91s
```

The skip is `test_r014_unreadable_folder_stops_the_check` (Windows; the test requires a non-root POSIX user).

3. `python -m pytest tests -q` — exit 0

```
1027 passed, 21 skipped in 237.26s (0:03:57)
```

This run was after the first `make-manifest.py`, so the source-tree manifest test passed. Step 5 then refreshed `generated` to `2026-10-16 21:17`; `bridge-check.py --sources` matched that stamp. The suite was not started again after that stamp. The workflow pin is unchanged.

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
bridge-check: version 2026.10.11d (2026-10-16 21:17) at E:\p18-claude-cursor-bridge\Workspace\bridge
bridge-check: 107 OK, 0 STALE, 0 MISSING, 0 EXTRA
RESULT: SOURCES MATCH bridge 2026.10.11d
```

6. `git diff --stat` — exit 0. The report is untracked, so it is absent here; `git status --short` also shows `?? handoff/TASK-006-r2-report.md`.

```
 bridge/cursor-bridge/MANIFEST.json     |   4 +-
 bridge/cursor-bridge/workflow-check.py | 259 ++++++++++++++++++++++++---------
 2 files changed, 190 insertions(+), 73 deletions(-)
```

## Assumed, not verified

- `os.walk`'s `onerror` is called with an `OSError` whose `filename` is the unlistable folder and whose `strerror` is a usable reason, and that recording it yields exit 2 with `RESULT: not checked` and no findings · this session is Windows, so `test_r014_unreadable_folder_stops_the_check` was skipped · that test on the ubuntu CI leg.
