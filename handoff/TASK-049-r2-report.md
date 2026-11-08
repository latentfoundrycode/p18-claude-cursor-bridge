# TASK-049-r2 report

## Files changed

- `bridge/cursor-bridge/bridge_env.py`
- `bridge/cursor-bridge/inventory-check.py`
- `bridge/cursor-bridge/completion-check.py`
- `bridge/cursor-bridge/diagram-check.py`
- `bridge/cursor-bridge/conformance-check.py`
- `bridge/cursor-bridge/plan-check.py`
- `bridge/cursor-bridge/MANIFEST.json` (regenerated)
- `tests/test_header_tables.py`
- `tests/test_header_tables_r2.py`

## Summary

Round 2 repairs the eight reviewer findings on TASK-049 by making headed tabular records obey the same row rules as header-less reads from the single `bridge_env` copies: inventory reflected-through and template column SHAPE, register malformed rows and requirement text, diagram index without the prose first-word check on a header, `known_deviations` raising on malformed headers, refusal when `bridge_env` is unusable, and conformance inventory floors that say not checked instead of false verdicts.

## Findings

- **B1:** Headed inventory with YAML-null `reflected_through` now derives the marker from the body when null and applies the same `SHAPE: no 'Reflected through:' line` rule; the duplicate regex and silent `elif pass` are removed.
- **B2:** Headed register malformed-row checks require every declared column non-empty except the evidence role column.
- **B3:** Requirement text in findings is the first declared column that is not any role column (no fictional `requirement` role).
- **B4:** Headed diagram-check index rows come from `diagram_index_body_table` without the header-less first-word gate; header-less path uses `diagram_index_table`.
- **SF-1:** Removed `SECTIONS`, local `parse_tables` body, and `Reflected through` regex from `inventory-check.py`; removed index `want` list from `diagram-check.py`; dropped unused `header_orig` in `parse_register` and the no-op in `register_fallback`.
- **SF-1b:** Conformance development-data floor uses `inventory_development_data`; `diagram_index_selected_ids` applies `diagram_index_table` on the header-less path (plan-check simplified to call it).
- **SF-2:** `known_deviations` runs `check_header` and raises `HeaderError` on schema findings instead of returning an empty set.
- **SF-3:** `_bridge_env_refuse_line` guards all inventory-related `bridge_env` names; inventory reading refuses before `read_header` when `bridge_env` is missing.
- **SF-4:** When inventory parsing cannot use `bridge_env`, both A1b floors print `MISSING` with `not checked` like the status floor.
- **A5:** Headed inventory tables are parsed from `inv_body` only (empty body yields no sections).
- **N2:** Column-count SHAPE always uses `bridge_env.INVENTORY_SECTIONS`, not the header's declared column lists.

## `bridge_env.py` TASK-046/047/048 edits

- ~2784–2794: removed unused `header_orig` from `parse_register` (SF-1).
- ~2800–2812: removed no-op assignment in `register_fallback` (SF-1).
- ~2838–2841: added `diagram_index_body_table` for headed index reads without the normative check (B4).
- ~2927–2949: `diagram_index_selected_ids` header-less path gated by `diagram_index_table` (SF-1b).

## Existing tests pinning a retired reading

none

## Commands

### 1

```
python -m pytest -q tests/test_header_tables.py tests/test_header_tables_r2.py
```

```
......................................................                   [100%]
54 passed in 8.83s
```

### 2

```
python -m pytest -q tests/test_conformance_check.py tests/test_completion_check.py tests/test_diagram_check.py tests/test_plan_check.py tests/test_text_consistency.py
```

```
.........................................                                [100%]
41 passed in 28.72s
```

### 3

```
python -m pytest -q tests/test_release_t_stamp.py tests/test_diagram_check_a4.py tests/test_header_reader.py tests/test_header_status.py tests/test_header_plan.py tests/test_dump_cli.py tests/test_tests_windowless.py
```

```
........................................................................ [  6%]
........................................................................ [ 12%]
........................................................................ [ 18%]
........................................................................ [ 25%]
........................................................................ [ 31%]
........................................................................ [ 37%]
........................................................................ [ 44%]
........................................................................ [ 50%]
........................................................................ [ 56%]
........................................................................ [ 63%]
........................................................................ [ 69%]
........................................................................ [ 75%]
........................................................................ [ 81%]
........................................................................ [ 88%]
........................................................................ [ 94%]
..............................................................           [100%]
1142 passed in 138.41s (0:02:18)
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
bridge-check: version 2026.11.03a (2026-11-08 11:48) at <Workspace>\bridge
bridge-check: 145 OK, 0 STALE, 0 MISSING, 0 EXTRA
RESULT: SOURCES MATCH bridge 2026.11.03a
```

### 6

```
python tools/dump-cli.py --check
```

(exit 0, no stdout)

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
9e0d5c91c3bfbbed29054bd22af86f4e75dc6337
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
 M tests/test_header_tables_r2.py
```

(Report file and any `docs/BUILDER_NOTES.md` entry are additional uncommitted changes after step 8.)

## Assumed, not verified

Assumed, not verified: none
