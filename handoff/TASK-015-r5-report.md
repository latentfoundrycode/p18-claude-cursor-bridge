# TASK-015 round 5 report

## Files changed

- `bridge/cursor-bridge/session-start.py` — R5-1: `load_tables_from_checker` and `table_file_shown` use `installed_open_list_path()` / `installed_registry_path()` under `workflow_root()` for reads and path mapping; R5-2: docstring states the reason and type-name character classes; R5-3: `safe_exc_type_name` requires `type(name) is str` before `fullmatch`.
- `bridge/cursor-bridge/MANIFEST.json` — regenerated via `python tools/make-manifest.py`.
- `docs/cli-reference.json` — regenerated via `python tools/dump-cli.py`.
- `docs/CLI_REFERENCE.md` — regenerated via `python tools/dump-cli.py`.

## Summary

Round 5 aligns table reads with the hook’s installed paths after the R4-3 path comparison, documents the plain-text sanitization rules in the module docstring, and hardens exception-type naming when `__name__` is not a string, so Linux CI cannot diverge from link checks and crafted checker exceptions cannot escape the hook.

## Mutation checks

- **(x) Read back to `wc.DEFAULT_OPEN` and `wc.DEFAULT_REGISTRY`:** None caught on this Windows run; `test_r005_the_tables_are_read_at_the_hooks_own_paths` still passes because `abspath` collapses `..` by text here (the test docstring notes Linux CI would catch this).
- **(y) Drop the `type(name) is str` guard in `safe_exc_type_name`:** Caught by `test_r005_a_type_name_that_is_not_a_string_is_an_exception` (hook traceback / empty pointers output).

## Verification

```
python -m pytest tests/test_session_start_module.py tests/test_session_start.py -q
```
Exit code: 0 — `67 passed, 4 skipped in 13.96s`

```
python tools/make-manifest.py
```
Exit code: 0 — `make-manifest: version 2026.10.18a, 120 files hashed, VERSION + MANIFEST.json written`

```
python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks tools
```
Exit code: 0 — `windowless-check: 37 file(s) scanned, 0 FAIL, 0 NOTE`

```
python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet
```
Exit code: 0 — `bridge-check: 120 OK, 0 STALE, 0 MISSING, 0 EXTRA` / `RESULT: SOURCES MATCH bridge 2026.10.18a`

```
python tools/dump-cli.py --check
```
Exit code: 0 (after `python tools/dump-cli.py` to refresh generated docs)

```
python -m pytest tests -q
```
Exit code: 0 — `1850 passed, 33 skipped in 410.33s (0:06:50)`

## Assumed, not verified

Assumed, not verified: none
