# TASK-057 round 1 report

## Files changed

- `bridge/cursor-bridge/trace-check.py`
- `bridge/cursor-bridge/review-guard.py`
- `bridge/cursor-bridge/MANIFEST.json`
- `docs/cli-reference.json`
- `docs/CLI_REFERENCE.md`

`tests/test_trace_check.py` was not changed (pinned-mode tests stayed green without edits). `docs/BUILDER_NOTES.md` was not changed.

## Summary

The builder added `trace-check.py --moves` with `--base`, reusing `parse_units`, normal forms, `escape_field`, `git_run`, and `decode_git_bytes` to compare instruction `.md` files between the merge-base and HEAD, excuse drops via range-added `docs/TRACE_MOVES.md` entries, and report counts; registered `docs/TRACE_MOVES.md` on `review-guard.py` `FULL_GATE_RECORDS`; and regenerated the CLI reference and manifest. All supervisor acceptance and Done-section checks passed.

## Requirements

1. `run_moves` in `trace-check.py` implements merge-base resolution, changed instruction files, passage comparison, entry read/match, and FAIL/RESULT output beside the unchanged pinned path in `main`.
2. `run_moves` prints the full merge-base sha as the first line via `print(base)` after `git_merge_base`.
3. `git_merge_base` rejects `--base` values starting with `-` before git; `rev-parse --verify --end-of-options` and failed merge-base print `ERROR:` naming the revision and exit 2.
4. Every git invocation uses `git_run`; the mode writes no files.
5. Dropped passages print `FAIL <file>: <words>` plus `move_entry_line`; unmatched entries print `FAIL <hash>`.
6. `fail_count` drives `RESULT: <n> problem(s)` or `RESULT: OK` with the three count lines.
7. Missing work tree, bad HEAD, or UTF-8 read failures print `ERROR:` and `RESULT: not checked` in `run_moves`.
8. `build_parser` adds `--moves` and `--base`; `main` errors on illegal combinations before the pinned path runs.
9. `FULL_GATE_RECORDS` in `review-guard.py` includes `docs/trace_moves.md` with reason holding `the trace check`.
10. The module docstring documents move-mode usage, output, and exit codes while preserving pinned-mode text.
11. Regenerated manifest and CLI reference; `dump-cli.py --check` exit 0; `bridge-check.py --sources` reports SOURCES MATCH; `VERSION` remains `2026.11.12a`.

## Commands

### 1. `python tools/dump-cli.py`

```
(no output)
```

### 2. `python tools/make-manifest.py`

```
make-manifest: version 2026.11.12a, 146 files hashed, VERSION + MANIFEST.json written
```

### 3. `python -m pytest -q tests/test_program_trace_moves.py`

```
.................                                                        [100%]
17 passed in 21.12s
```

### 4. `python -m pytest -q tests/test_release_s_records_gate.py`

```
.....................................................................    [100%]
69 passed in 55.26s
```

### 5. `python -m pytest -q tests/test_trace_check.py tests/test_trace_full_split.py`

```
....................................s..sss.................              [100%]
55 passed, 4 skipped in 25.85s
```

### 6. `python -m pytest -q tests/test_dump_cli.py`

```
........................................................................ [ 72%]
...........................                                              [100%]
99 passed in 102.40s (0:01:42)
```

### 7. `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge`

```
windowless-check: 36 file(s) scanned, 0 FAIL, 0 NOTE
```

### 8. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`

```
bridge-check: version 2026.11.12a (2026-11-13 22:21) at <Workspace>/bridge
bridge-check: 146 OK, 0 STALE, 0 MISSING, 0 EXTRA
RESULT: SOURCES MATCH bridge 2026.11.12a
```

### 9. `python tools/dump-cli.py --check`

```
exit=0
```

### 10. `git rev-parse HEAD` and `git status --short`

```
fe22f35d6f73e1d981dccdf10c2ddc48deddb469
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/VERSION
 M bridge/cursor-bridge/review-guard.py
 M bridge/cursor-bridge/trace-check.py
 M docs/CLI_REFERENCE.md
 M docs/cli-reference.json
```

Commit for the counts above: `fe22f35d6f73e1d981dccdf10c2ddc48deddb469`. Working tree held uncommitted changes listed above (`VERSION` content unchanged at `2026.11.12a`; git shows it modified for line-ending metadata only).

## Mutations

M1–M4: not run in this session (supervisor mutation sweep remains for the supervisor run).

## Assumed, not verified

Assumed, not verified: Git on this host accepts `--end-of-options` on `rev-parse` and `merge-base` with the argument lists used · brief requires it for dashed revision text · a failed run on an older git would show in CI or local pytest.

Assumed, not verified: Two identical passage units in the same changed file at the base, both absent at HEAD, produce two FAIL lines and need two matching entries · one entry excuses one passage in the pairing loop · no test covers duplicate normals in one file.

Assumed, not verified: Duplicate entry lines with identical text in `docs/TRACE_MOVES.md` at HEAD are each treated as separate added entries if both are new to the base · set difference is on full line text · no test adds two identical new entry lines.

Assumed, not verified: A passage unit whose normal form is empty is compared like any other unit · `parse_units` can emit empty normals · no acceptance test asserts behaviour for an empty normal.
