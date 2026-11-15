# TASK-063 round 2 report

## Files changed

- `bridge/cursor-bridge/permission-guard.py`
- `bridge/cursor-bridge/MANIFEST.json` (regenerated)
- `tests/test_permission_guard_a4.py`
- `handoff/TASK-063-r2-report.md`

## Summary

Round 2 replaces the fragmented scanners with a single iterative `read_shell` reader that tracks splitting frames, quoting, substitutions, here-documents, and `case` patterns, then drives `split_commands`, `chain_parts_with_substitutions`, `chain_reason`, `commit_message`, `contains_command_substitution`, and the git/gh checks from that one parse; unquoted and shell-read here-document bodies are expanded into nested commands, Requirement 14 builder tests were added in `test_permission_guard_a4.py`, and the manifest was regenerated.

## Requirements

1. `read_shell` (from line 199) is the sole quote and separator reader; every caller uses `_parsed_snapshot` / its cache, and no parallel quote scanner remains for splits or refusal.
2. Separators are handled in `try_sep` inside `read_shell`, with heredoc-aware newline suppression and pipe keeping one chain part via `chain_segs` on the top split frame.
3. `split_commands`, `chain_parts`, `chain_parts_with_substitutions`, and `check` all consume `read_shell` output; nested spl flushes no longer pollute top-level `full_cmds`, and substitution bodies are sliced from `text[fr["start"]:i]` on close.
4. `heredoc_op_at` rejects `<<<` and the second `<<` of `<<<`; quoted delimiters stay data, unquoted bodies use `absorb_expanded_heredoc`, and shell-read bodies are re-checked through `_heredoc_shell_reads` in `split_commands`.
5. Depth bound `READ_DEPTH_BOUND = 64` (line 132): stack nesting in `read_shell` and `check` recursion share this cap, and overflow returns a “nests too deeply to read” reason.
6. `_ansi_c_decode` and `_tokenize_parsed` decode `$'...'` and `$"..."` words for `words()` and flag checks such as `force_push_reason`.
7. `leading_husky_zero`, `strip_prefix` (now including `setsid` and `winpty`), and husky recursion in `_check_one` refuse leading `HUSKY=0` through runners.
8. `hook_skipper_option` alone skips `--no-verify`/`-n` only as real git options; `commit_message` pulls checkpoint subjects from substitution heredocs via `first_heredoc_subject`.
9. `gh_api_unquoted_ampersand_reason` still scans the line; `chain_reason` uses parsed commands from the full line, not a stripped copy alone.
10. GraphQL refusal uses `parsed["hassub"]` so single-quoted `$(x)` in a query argument passes while unquoted substitutions refuse.
11. `check(command, cwd, tool)` and `_join_continuations` give PowerShell a second read without backslash escapes; bash leaves a backtick before a newline as syntax inside the command.
12. `main()` fail-open paths are unchanged from the frozen module docstring.
13. Prior refusal lists and `settings.bridge.json` are unchanged; existing tests in the four Done files still pass.
14. Requirement 14 tests at the end of `tests/test_permission_guard_a4.py` (`test_r082_req14_*`) name R-082 and cover the brief’s refused and passing builder cases.
15. `python tools/make-manifest.py` ran; `dump-cli.py --check` is clean; module docstring and `VERSION` unchanged.

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
........................................................................ [  9%]
........................................................................ [ 19%]
........................................................................ [ 29%]
........................................................................ [ 38%]
........................................................................ [ 48%]
........................................................................ [ 58%]
.......................................................s...ss.....sss... [ 67%]
.................s...............s...................................... [ 77%]
.........s...........s.................s...ss.....sss................... [ 87%]
.s...............s...............................................s...... [ 97%]
.....s................                                                   [100%]
722 passed, 20 skipped in 47.48s
```

### 4. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`

```
bridge-check: version 2026.11.12a (2026-11-15 17:25) at <Workspace>\bridge
bridge-check: 146 OK, 0 STALE, 0 MISSING, 0 EXTRA
RESULT: SOURCES MATCH bridge 2026.11.12a
```

### 5. `git diff --stat HEAD`

```
 bridge/cursor-bridge/MANIFEST.json       |    4 +-
 bridge/cursor-bridge/permission-guard.py | 1379 ++++++++++++++++++++----------
 tests/test_permission_guard_a4.py        |   54 ++
 3 files changed, 990 insertions(+), 447 deletions(-)
```

### 6. `git rev-parse HEAD` and `git status --short`

```
6fab457bf2332992cca0187c58c12447433dcf9d
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/permission-guard.py
 M tests/test_permission_guard_a4.py
```

Mutations: not run (the supervisor's)

## Assumed, not verified

Assumed, not verified: none