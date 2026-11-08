# TASK-049 r1 report

## Files changed

- bridge/cursor-bridge/bridge_env.py
- bridge/cursor-bridge/inventory-check.py
- bridge/cursor-bridge/conformance-check.py
- bridge/cursor-bridge/completion-check.py
- bridge/cursor-bridge/diagram-check.py
- bridge/cursor-bridge/plan-check.py
- bridge/cursor-bridge/MANIFEST.json
- tests/test_header_tables.py
- handoff/TASK-049-r1-report.md

## Summary

Moved the four tabular fallback readers into `bridge_env.py` (`inventory_parse_tables`, `inventory_fallback`, `parse_register`, `register_fallback`, diagram index and deviations helpers) and wired header-first reading with `HEADER MALFORMED` (exit 2) and owning-checker `HEADER DISAGREES` (exit 1) through `inventory-check.py`, `completion-check.py`, and `diagram-check.py`, while `conformance-check.py` and `plan-check.py` trust those owners on disagreement and retired readings (7), (8), and (9). `diagram-check.py` gained a plain `import bridge_env`; tabular rows are read from header bodies, R-ids trace the register id column only, and plan-check selects diagrams from the first index table by role.

## Existing tests pinning retired readings

none

## Manifest

Command:

```
python tools/make-manifest.py
```

Output:

```
make-manifest: version 2026.11.03a, 145 files hashed, VERSION + MANIFEST.json written
```

## Commands and output

Commit: `64a51ab2950039d6a0966ebaf6d5dd1847e809ae`. Working tree at step 8 held uncommitted changes in the seven program files, `MANIFEST.json`, `tests/test_header_tables.py`, and this report (`git status --short` below).

### 1

```
python -m pytest -q tests/test_header_tables.py
```

```
.......................................                                  [100%]
39 passed in 12.48s
```

### 2

```
python -m pytest -q tests/test_conformance_check.py tests/test_completion_check.py tests/test_diagram_check.py tests/test_plan_check.py tests/test_text_consistency.py
```

```
.........................................                                [100%]
41 passed in 28.74s
```

### 3

```
python -m pytest -q tests/test_release_t_stamp.py tests/test_diagram_check_a4.py tests/test_header_reader.py tests/test_header_status.py tests/test_header_plan.py tests/test_dump_cli.py tests/test_tests_windowless.py
```

```
1142 passed in 137.13s (0:02:17)
```

### 4

```
python tools/make-manifest.py
```

```
make-manifest: version 2026.11.03a, 145 files hashed, VERSION + MANIFEST.json written
```

### 5

```
python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet
```

```
bridge-check: version 2026.11.03a (2026-11-08 11:03) at <Workspace>\bridge
bridge-check: 145 OK, 0 STALE, 0 MISSING, 0 EXTRA
RESULT: SOURCES MATCH bridge 2026.11.03a
```

### 6

```
python tools/dump-cli.py --check
```

```
(exit 0, no output)
```

### 7

```
python bridge/cursor-bridge/diagram-check.py --mode code
```

```
note: mode code; 5 diagrams selected across 5 kinds; 13 kinds omitted
RESULT: OK
```

### 8

```
git rev-parse HEAD
```

```
64a51ab2950039d6a0966ebaf6d5dd1847e809ae
```

```
git status --short
```

```
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/bridge_env.py
 M bridge/cursor-bridge/completion-check.py
 M bridge/cursor-bridge/conformance-check.py
 M bridge/cursor-bridge/diagram-check.py
 M bridge/cursor-bridge/inventory-check.py
 M bridge/cursor-bridge/plan-check.py
 M tests/test_header_tables.py
?? handoff/TASK-049-r1-report.md
```

## Assumed, not verified

- When a tabular header's `roles` swap two column names but every name still appears in the table header row, `header_agrees` reports no disagreement (TASK-046 A1); programs then read cells by the declared role-to-column map, so swapped roles would read the wrong cells without a disagreement finding.
- `inventory-check.py` with `reflected_through: null` in a agreeing header and no `Reflected through:` line in the body skips absorption checks rather than failing on a missing line.
- A partial `bridge_env` stub that exposes only `read_header` still relies on `_bridge_env_refuse_line` rejecting the run before inventory header logic when `status_values` is absent; inventory header helpers are not individually guarded beyond that pattern.
