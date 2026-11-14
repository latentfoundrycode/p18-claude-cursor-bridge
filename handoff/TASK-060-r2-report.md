# TASK-060 round 2 report

## Files changed

- `bridge/cursor-bridge/bridge_env.py`
- `bridge/cursor-bridge/bridge-run.py`
- `bridge/cursor-bridge/conformance-check.py`
- `bridge/cursor-bridge/MANIFEST.json` (regenerated)
- `tests/test_account_keys.py`
- `tests/test_bridge_run.py`
- `tests/test_conformance_check.py`
- `handoff/TASK-060-r2-report.md`

## Summary

Round 2 fixes R-080 review rejections: `CURSOR_` withholding follows `is_agent` from `resolve` (not `--kind`), home-variable refusals name every offending key-file line, `secret_like` honors `KEEP_PREFIXES`, D-004 parity tests split whole names from bare words, builder tests isolate launches under `tmp_path`, and conformance floors use a single `m.group(1)`; limit-cap and review/watch refusals move before `bridge-run: started` so stripped suites labelled review exit 125 without a start line.

## Corrections (1–8)

1. `bridge-run.py` calls `stripped_env(is_agent=is_agent)` and `stripped_env` in `bridge_env.py` sets `keep_cursor` from `is_agent` when given, else `True` only when `kind is None`, else `False`; limit/review/watch refusal block sits before the `started` line (~2270).
2. `key_file_home_refusal` in `bridge-run.py` returns `", ".join` of every home name in dict insertion (file) order.
3. `secret_like` in `bridge_env.py` iterates `KEEP_PREFIXES`, keeping non-`CURSOR_` prefixes always and `CURSOR_` only when `keep_cursor` is true.
4. `test_r055_d004_the_withheld_names_are_the_notes` in `tests/test_account_keys.py` uses `anchored_whole_names`, `pattern_bare_words`, and `note_whole_and_bare` so bounded `AUTH` and anchored names are compared separately.
5. `test_r080_a_key_file_home_variable_is_refused_before_start_for_a_test_run` in `tests/test_bridge_run.py` uses `cwd`, timeout, `CREATE_NO_WINDOW`, and a positive control key file before the home refusal case.
6. `test_r080_shim_and_stripped_env_agree_on_r080_forms` parametrizes explicit `expected` withheld/kept and asserts both recipes agree for every name including `SCREDS`.
7. `test_r080_inventory_floor_uses_bridge_env_secret_like` adds `AUTHOR_NAME` to the fixture `.env`; `test_r080_session_note_lists_bridge_env_forms_not_boundary_cases` uses a minimal session environment with timeout and `CREATE_NO_WINDOW`.
8. `conformance-check.py` keys floor (~1220) uses one `name = m.group(1)` for both checks.

## Tests changed and why

- `tests/test_account_keys.py` — corrections 4 and 6: D-004 word parity and full shim parametrization.
- `tests/test_bridge_run.py` — corrections 1 and 5: `is_agent`/`kind` in-process cases and isolated launcher refusal.
- `tests/test_conformance_check.py` — correction 7: inventory boundary and session NOTE environment.

`tests/test_program_strip_names.py` untouched (supervisor acceptance). `tests/test_release_t_strip.py` comment still partly stale.

## Verification commands

```
make-manifest: version 2026.11.12a, 146 files hashed, VERSION + MANIFEST.json written
```

```
```

```
.............................................................            [100%]
61 passed in 25.66s
```

```
........................                                                 [100%]
24 passed in 16.34s
```

```
........................                                                 [100%]
24 passed in 9.72s
```

```
...................                                                      [100%]
19 passed in 10.90s
```

```
.....................................................                    [100%]
53 passed in 10.31s
```

```
........................................................................ [ 16%]
........................................................................ [ 32%]
........................................................................ [ 48%]
.................................ss..................................... [ 64%]
........................................................................ [ 80%]
................................................................s.s..... [ 97%]
.............                                                            [100%]
441 passed, 4 skipped in 89.03s (0:01:29)
```

```
........................................................................ [ 19%]
........................................................................ [ 38%]
........................................................................ [ 57%]
........................................................................ [ 77%]
........................................................................ [ 96%]
..............                                                           [100%]
374 passed in 348.16s (0:05:48)
```

```
bridge-check: version 2026.11.12a (2026-11-14 20:37) at <Workspace>\bridge
bridge-check: 146 OK, 0 STALE, 0 MISSING, 0 EXTRA
RESULT: SOURCES MATCH bridge 2026.11.12a
```

```
 bridge/cursor-bridge/MANIFEST.json        |  8 ++---
 bridge/cursor-bridge/bridge-run.py        | 27 ++++++++-------
 bridge/cursor-bridge/bridge_env.py        | 18 ++++++----
 bridge/cursor-bridge/conformance-check.py |  5 ++-
 tests/test_account_keys.py                | 55 +++++++++++++++++--------------
 tests/test_bridge_run.py                  | 29 ++++++++++++----
 tests/test_conformance_check.py           | 10 ++++--
 7 files changed, 91 insertions(+), 61 deletions(-)
```

```
d691c9d79be22b5806f1b8c1d9b75a2e682f0d92
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/bridge-run.py
 M bridge/cursor-bridge/bridge_env.py
 M bridge/cursor-bridge/conformance-check.py
 M tests/test_account_keys.py
 M tests/test_bridge_run.py
 M tests/test_conformance_check.py
```

## Mutations (R1–R6)

| Label | Change | pytest line |
|---|---|---|
| R1 | `stripped_env` always `keep_cursor=True` | `FAILED tests/test_bridge_run.py::test_r080_stripped_cursor_agent_keeps_cursor_keys_while_stripped_test_does_not` (also `FAILED tests/test_program_strip_names.py::test_r080_a_secret_like_cursor_name_is_withheld_from_a_test_run`) |
| R2 | `stripped_env` always `keep_cursor=False` | `FAILED tests/test_bridge_run.py::test_r080_stripped_cursor_agent_keeps_cursor_keys_while_stripped_test_does_not` |
| R3 | `key_file_home_refusal` returns first name only | `FAILED tests/test_program_strip_names.py::test_r080_every_home_variable_a_key_file_names_is_named` |
| R4 | `AUTH` removed from `SECRET_LIKE` | `FAILED tests/test_account_keys.py::test_r055_d004_the_withheld_names_are_the_notes` |
| R5 | `AUTH` removed from D-004 note parenthesis | `FAILED tests/test_account_keys.py::test_r055_d004_the_withheld_names_are_the_notes` |
| R6 | `CURSOR_` removed from `KEEP_PREFIXES` | `FAILED tests/test_account_keys.py::test_r055_d004_the_withheld_names_are_the_notes` |

## Assumed, not verified

- `conformance-check.py` stand-in when `bridge_env.py` is absent still behaves as round 1 assumed.
- Moving review/watch refusal before `started` does not disturb review-guard consumers beyond what existing tests cover.