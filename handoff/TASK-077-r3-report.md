# TASK-077 round 3 report

## Files changed

- bridge/cursor-bridge/evaluate-reports.py
- bridge/cursor-bridge/MANIFEST.json (regenerated)

## Summary

Round 3 applies minimal fixes for Rulings 1–7 in `evaluate-reports.py`: window exit-1 findings clear on a later success and the newest exit-1 stands; failed alerts reads keep the week's remedy and add a separate alerts remedy line; standing findings keep the week's kind with a DEP- remedy beside the week's remedy; naive times and bad alert or workflow field types fail reads without tracebacks; a missing `workflow_runs` list is a failed read; and `git_origin_repo` requires `Workspace/.git` before calling git. `MANIFEST.json` was regenerated; `dump-cli` and `make-manifest` left `docs/cli-reference.json`, `docs/CLI_REFERENCE.md`, and `VERSION` unchanged.

## Rulings 1–7

- Ruling 1: `scan_project` assigns `new_standing` from `exit1_id` only when `_standing_cleared(exit1_id, ...)` is false (lines ~1013–1018).
- Ruling 2: `scan_project` failures loop keeps the exit-1 run with the greatest parsed `created_at` (lines ~993–1007).
- Ruling 3: `scan_project` sets `alerts_remedy` instead of overwriting `remedy` (lines ~1041–1042); `format_security_section` prints week and alerts remedies on separate lines (lines ~1094–1100) and adds a `finding` line when alerts fail beside a non-finding kind (lines ~1086–1087).
- Ruling 4: Removed the `no completed run`→`finding` override; `format_security_section` adds the DEP- standing remedy when `standing` is set and kind is not `finding` (lines ~1095–1097).
- Ruling 5: `parse_utc` rejects offset-naive times (lines ~480–486); `run_in_window` ignores unparseable `last_run_read` (lines ~680–684); `_validate_workflows_body` validates `path` and `state` types (lines ~738–743); `_alert_shape_ok` and `_read_alerts` validate alert shapes before formatting (lines ~855–905).
- Ruling 6: `scan_project` treats a missing or non-list `workflow_runs` as a failed runs read (lines ~970–976).
- Ruling 7: `git_origin_repo` returns none unless `Workspace/.git` exists as a file or directory (lines ~519–522).

## Recorded, not fixed this round

Confirmed unchanged: S1 (second `_run_exit_code` on the last failed run in `pending_failure` at lines ~1025–1031 remains); S3 `ascii_line`; S4/S5; Considers; security audit advisories.

## D-004

The diagram draws no flow from a project's Workspace `origin` to `p_evaluate_reports`; the code still calls git on `Workspace` when `.git` is present to resolve OWNER/REPO before GET-only GitHub reads.

## Guard test edits

none

## Commands

### 1. git status --short

```
 M bridge/cursor-bridge/evaluate-reports.py
?? handoff/TASK-077-r3-report.md
```

### 2. python tools/make-manifest.py

```
make-manifest: version 2026.11.12a, 148 files hashed, VERSION + MANIFEST.json written
```

### 3. python tools/dump-cli.py

```
(no output)
```

### 4. python -m pytest -p no:cacheprovider -q tests/test_program_security_step.py

```
........................................................................ [ 74%]
.........................                                                [100%]
97 passed in 42.35s
```

### 5. python -m pytest -p no:cacheprovider -q tests/test_evaluate_reports.py tests/test_pace_report.py

```
............                                                             [100%]
12 passed in 5.27s
```

### 6. python -m pytest -p no:cacheprovider -q tests/test_hotfix25a_loopguard_reports.py tests/test_task033_supervisor_r2.py tests/test_task033_supervisor.py

```
.........s.............................................................. [ 51%]
....................................................................     [100%]
139 passed, 1 skipped in 37.43s
```

### 7. python -m pytest -p no:cacheprovider -q tests/test_dump_cli.py

```
........................................................................ [ 71%]
.............................                                            [100%]
101 passed in 121.50s (0:02:01)
```

### 8. python tools/dump-cli.py --check

```
(no output)
```

Exit code: 0

### 9. python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet

```
bridge-check: version 2026.11.12a (2026-11-22 10:40) at <Workspace>/bridge
bridge-check: 148 OK, 0 STALE, 0 MISSING, 0 EXTRA
RESULT: SOURCES MATCH bridge 2026.11.12a <Workspace>/bridge/cursor-bridge
```

Exit code: 0

### 10. python -c ASCII check

```
ascii ok
```

### 11. python -c CRLF check

```
bridge/cursor-bridge/evaluate-reports.py bare LF 0
bridge/cursor-bridge/pace-report.py bare LF 0
```

### 12. git diff -- bridge/cursor-bridge/VERSION

```
(no output)
```

### 13. git diff --stat

```
 bridge/cursor-bridge/MANIFEST.json       |   4 +-
 bridge/cursor-bridge/evaluate-reports.py | 177 ++++++++++++++++++++-----------
 2 files changed, 116 insertions(+), 65 deletions(-)
```

### 14. git rev-parse HEAD; git status --short

```
23655ae2ef7d7c61a525f4c6a74e27fd6f490594
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/evaluate-reports.py
?? handoff/TASK-077-r3-report.md
```

## Assumed, not verified

- A supplemental `finding` line beside the week's kind when alerts read fails is the intended way to satisfy "the word finding present" without merging kinds — brief Ruling 3 names only remedy preservation, not this extra line; the acceptance tests require `\bfinding\b` when the week's kind is not already `finding`.