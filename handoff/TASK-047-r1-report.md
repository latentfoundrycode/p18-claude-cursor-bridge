# TASK-047 r1 report

## Files changed

- bridge/cursor-bridge/bridge_env.py
- bridge/cursor-bridge/loop-guard.py
- bridge/cursor-bridge/session-start.py
- bridge/cursor-bridge/conformance-check.py
- bridge/cursor-bridge/workflow-check.py
- bridge/cursor-bridge/inventory-check.py
- bridge/cursor-bridge/evaluate-reports.py
- bridge/cursor-bridge/MANIFEST.json
- docs/cli-reference.json
- docs/CLI_REFERENCE.md
- tests/test_header_status.py
- tests/test_session_start.py

## Summary

Added `status_fallback`, `status_workflows`, and `status_values` to `bridge_env.py` (without changing the TASK-046 header reader) and wired all six status readers to use them: hooks print malformed/disagree/workflow-refusal lines, checkers exit 2 on malformed headers, `inventory-check.py` disagrees on every key and counts caps on the body after the header, and retired prose readings (1)–(4) were removed from session-start and conformance-check. Regenerated CLI reference and MANIFEST.

## Tests corrected in existing scope files

none (only new cases added in `tests/test_header_status.py` and `tests/test_session_start.py`)

## Manifest command

```
python tools/make-manifest.py
```

```
make-manifest: version 2026.11.03a, 145 files hashed, VERSION + MANIFEST.json written
```

## Verification (commit f68a8830ae1a93bd8d98e01588bbdb82baa74346; uncommitted changes listed below)

### 1. tests/test_header_status.py

```
103 passed in 15.92s
```

### 2. scope test bundle

```
1606 passed, 8 skipped in 99.60s (0:01:39)
```

### 3. tools/dump-cli.py

```
(no output)
```

### 3b. tools/dump-cli.py --check

```
(no output, exit 0)
```

### 4. python tools/make-manifest.py

```
make-manifest: version 2026.11.03a, 145 files hashed, VERSION + MANIFEST.json written
```

### 5. python ~/.claude/cursor-bridge/diagram-check.py --mode code

not run: `<the agent home>/.claude/cursor-bridge/diagram-check.py` not present on this host (path redacted by the supervisor, rule 54)

### 5b. workspace diagram-check (informational)

```
note: mode code; 5 diagrams selected across 5 kinds; 13 kinds omitted
RESULT: OK
```

### 6. python -m pytest -q (full suite from repo root)

```
INTERNALERROR> Traceback (most recent call last):
INTERNALERROR>   File "<the Workspace>/run/supervisor/t2close_test.py (path redacted by the supervisor, rule 54)", line 35, in <module>
INTERNALERROR>     sys.exit("already appended")
INTERNALERROR> SystemExit: already appended
no tests ran in 0.35s
```

### 6b. python -m pytest -q tests (full tests/ tree; collection succeeds)

```
8 failed, 4516 passed, 41 skipped in 1822.59s (0:30:22)
```

Failures (outside Scope files): `tests/test_running_projects_classify.py` (7 cases), `tests/test_tests_windowless.py::test_fix001_no_test_starts_a_program_around_the_default`

### 7. git

```
f68a8830ae1a93bd8d98e01588bbdb82baa74346
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/bridge_env.py
 M bridge/cursor-bridge/conformance-check.py
 M bridge/cursor-bridge/evaluate-reports.py
 M bridge/cursor-bridge/inventory-check.py
 M bridge/cursor-bridge/loop-guard.py
 M bridge/cursor-bridge/session-start.py
 M bridge/cursor-bridge/workflow-check.py
 M docs/CLI_REFERENCE.md
 M docs/cli-reference.json
 M tests/test_header_status.py
 M tests/test_session_start.py
 ?? handoff/TASK-047-r1-report.md
```

## Assumed, not verified

- Isolated copies of `workflow-check.py` / `inventory-check.py` / `conformance-check.py` without a sibling `bridge_env.py` (R-015 harness) skip header enforcement when `status_values` is absent, so those tests keep passing without bundling `bridge_env.py`.
- Installed `~/.claude/cursor-bridge/diagram-check.py` is not available on this builder host; D-002 `check:components` was checked with the workspace `diagram-check.py --mode code` only.
