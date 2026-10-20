# FIX-003 r1 report

## Files changed

- `bridge/cursor-bridge/session-start.py` — R1–R4 code and module docstring
- `bridge/cursor-bridge/MANIFEST.json` — regenerated via `python tools/make-manifest.py`
- `docs/cli-reference.json` — regenerated via `python tools/dump-cli.py`
- `docs/CLI_REFERENCE.md` — regenerated via `python tools/dump-cli.py`
- `handoff/FIX-003-r1-report.md` — this report

`bridge/cursor-bridge/VERSION` was rewritten by make-manifest; content remains `2026.10.18a`.

## Summary

Hardened `session-start.py` for FIX-003: `safe_exc_type_name` now reads `type(err).__name__` under stdout/stderr redirection so load/use error lines cannot leak checker prints; non-`str` lines from `wc.file_lines` raise `TypeError` so `pointers_part` reports `cannot be used (TypeError)`; pointer path segments are matched without per-segment `rstrip()`; the module docstring documents the grammar, streams, and non-str line behaviour. Regenerated CLI reference and bridge manifest; all targeted and full session-start tests pass.

## Mutation check

| Mutation | Tests that failed |
|----------|-------------------|
| Undo R1 (remove redirection inside `safe_exc_type_name`) | `test_r005_the_type_name_is_read_where_the_checker_cannot_print[load]`, `[use]` |
| Undo R2 (`continue` instead of `raise TypeError` for non-str lines) | `test_r005_a_line_that_is_not_a_str_makes_the_checker_unusable[uniform]`, `[fence]`, `test_r005_a_pointer_line_that_is_not_a_plain_string_names_nothing[sly]`, `[plain]` |
| Undo R3 (restore `p = part.rstrip()`) | `test_r005_a_pointer_path_is_taken_as_written_between_separators` |

Each mutation was reverted before the next; final code matches the fix.

## R1 / R2 / R3

- **R1:** Exception type names are resolved inside `safe_exc_type_name` with `redirect_stdout`/`redirect_stderr` to a `StringIO`, so both `load_checker_module` and `pointers_part` handlers get a safe name even after their outer redirection context has ended.
- **R2:** `pointer_paths_from_module` raises `TypeError` when `type(line) is not str`, which the existing `pointers_part` handler turns into the single `cannot be used (TypeError)` line with no pointer or conditional files named.
- **R3:** Removed per-part `rstrip()`; only `rest = line[len(prefix):].rstrip()` trims the line end, so interior spaces or tabs before `; ` fail `POINTER_PATH` and are not named.

## Assumed, not verified

Assumed, not verified: none.

## Commands run

```
python -m pytest tests/test_session_start_module.py tests/test_session_start.py -q
→ 90 passed, 4 skipped in ~21–31s

python -m pytest tests/test_session_start_module.py -q -k "not_a_plain_string or not_a_str or cannot_print or as_written_between or states_the_grammar"
→ 13 passed, 63 deselected

python tools/dump-cli.py
python tools/dump-cli.py --check
→ exit 0

python tools/make-manifest.py
→ make-manifest: version 2026.10.18a, 120 files hashed, VERSION + MANIFEST.json written

python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet
→ RESULT: SOURCES MATCH bridge 2026.10.18a
```

Mutation checks used the same `-k` filters as above for R1 (`cannot_print`), R2 (`not_a_str or not_a_plain_string`), and R3 (`as_written_between`).
