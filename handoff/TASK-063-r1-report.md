# TASK-063 round 1 report

## Files changed

- `bridge/cursor-bridge/permission-guard.py`
- `bridge/cursor-bridge/MANIFEST.json` (regenerated)
- `tests/test_permission_guard_a4.py`
- `handoff/TASK-063-r1-report.md`

## Summary

Replaced the permission guard's quote-aware splitting with bash-style scanning: double-quote closes only on an even run of backslashes before `"`, `$'...'` ANSI-C strings, command/process substitutions, and `${}` bodies yield nested command text for `split_commands` and selective chain expansion. Moved the graphql, HUSKY=0, and `--no-verify` checks off the raw line onto parsed words and git options; added refusal for an unquoted `&` glued inside a `gh api` endpoint. Added four R-082 builder tests in `test_permission_guard_a4.py`. Regenerated the manifest.

## Requirements

1. `_substitution_inners`, `_matching_paren`, and `_split_on_separators` feed `split_commands` (absorb recursion) and `chain_parts_with_substitutions` for rule 8; backtick and `$(` are not split as separators, only extracted.
2. `_substitution_opens` treats `<(` and `>(` like `$(` in `_matching_paren` and `_substitution_inners`.
3. `_double_quote_ends`, single-quote, and `ansi` (`$'`) branches in `_split_on_separators` and `_substitution_inners` implement bash quote closing.
4. `_slashes_before` and `_substitution_opens` ignore `$(`, backticks, and process opens behind an odd backslash run; single-quoted spans never open substitutions.
5. Removed the raw-line graphql regex in `check`; refusal is in the `gh` branch via `contains_command_substitution` on that simple command's args and body.
6. `leading_husky_zero` (including `env` argv) and `hook_skipper_option` replace raw-line HUSKY and per-word `--no-verify` scanning in `check`.
7. `gh_api_unquoted_ampersand_reason` runs first in `check`; a `&` with non-whitespace on both sides is treated as inside one argv fragment, not `_amp_is_command_separator`.
8. No new refusal for `${!name}` or `$CMD`; they remain ordinary words.
9. Existing denials and snapshot logic unchanged; `chain_parts_with_substitutions` adds inner parts only when `chain_parts(strip_heredocs(inner))` already has two or more segments, so the app's commit heredoc is not a false chain.
10. Single-pass index scans with recursive depth bounded by nesting; no whole-line regex backtracking in the new helpers.
11. Four tests at the end of `tests/test_permission_guard_a4.py` name R-082 and use `_run_r082` with timeout and `CREATE_NO_WINDOW`.
12. Ran `python tools/make-manifest.py`; `VERSION` unchanged; `dump-cli.py --check` clean; module docstring unchanged.

## tests/test_allowlist.py

tests/test_allowlist.py: unchanged

## Commands and output

### 1. `python tools/make-manifest.py`

```
make-manifest: version 2026.11.12a, 146 files hashed, VERSION + MANIFEST.json written
```

### 2. `python tools/dump-cli.py --check`

```
```

### 3. `python -m pytest -p no:cacheprovider -q tests/test_program_permission_guard.py tests/test_permission_guard.py tests/test_permission_guard_a4.py tests/test_allowlist.py`

```
........................................................................ [ 10%]
........................................................................ [ 21%]
........................................................................ [ 31%]
........................................................................ [ 42%]
........................................................................ [ 53%]
..............................................................s...ss.... [ 63%]
.sss....................s...............s............................... [ 74%]
................s...........s.................s...ss.....sss............ [ 85%]
........s...............s............................................... [ 95%]
s...........s................                                            [100%]
657 passed, 20 skipped in 39.15s
```

Commit for counts: `d5c4f3d5e51c9909c96d1e7689417958059dd42c`; working tree after step 6 held uncommitted changes (`M bridge/cursor-bridge/MANIFEST.json`, `M bridge/cursor-bridge/permission-guard.py`, `M tests/test_permission_guard_a4.py`).

### 4. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`

```
bridge-check: version 2026.11.12a (2026-11-15 15:58) at <Workspace>\bridge
bridge-check: 146 OK, 0 STALE, 0 MISSING, 0 EXTRA
RESULT: SOURCES MATCH bridge 2026.11.12a
```

### 5. `git diff --stat HEAD`

```
 bridge/cursor-bridge/MANIFEST.json       |   4 +-
 bridge/cursor-bridge/permission-guard.py | 525 ++++++++++++++++++++++++++++---
 tests/test_permission_guard_a4.py        |  45 +++
 3 files changed, 528 insertions(+), 46 deletions(-)
```

### 6. `git rev-parse HEAD` and `git status --short`

```
d5c4f3d5e51c9909c96d1e7689417958059dd42c
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/permission-guard.py
 M tests/test_permission_guard_a4.py
```

Mutations: not run (the supervisor's).

## Assumed, not verified

PowerShell reads the same quoting and substitution forms as bash for every acceptance case, because tests run both tools only where the existing suite parametrizes them and no PowerShell-only form was probed separately · the brief requires one reading for both tools · a failing PowerShell-only parametrized case would disprove it.

A single-quoted `$(` inside a `gh api graphql` argument is literal data and not refused, because single-quoted spans never call `_substitution_opens` · brief harmlessness table and req 4 · the supervisor graphql suite uses double-quoted or unquoted substitutions only.

Unclosed `"`, `$(`, or `${` at end of input are treated as literal text with no extra refusal, because scanners run to end-of-string without a syntax error path · no brief requirement · an explicit acceptance test for truncation would confirm.