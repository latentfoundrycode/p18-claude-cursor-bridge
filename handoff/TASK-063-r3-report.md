---
record: report
header: 1
id: "TASK-063"
round: 3
---

# TASK-063 round 3 report

## Files changed

- bridge/cursor-bridge/permission-guard.py
- bridge/cursor-bridge/MANIFEST.json
- docs/BUILDER_NOTES.md
- handoff/TASK-063-r3-report.md

## Summary

Round 3 replaces the fragmented scanners with an extended positive-grammar `read_shell` (`_join_bs_newlines`, `wmerge` word building, `try_redirect`, `finish_heredoc`, `scan_btick_body`, `gh_amp`, `unreadable`), single PowerShell read in `check`, per-list `chain_reason`, early `HUSKY` on simple-command text, and removal of `gh_api_unquoted_ampersand_reason`, `_tokenize_parsed`, `_shell_words`, `_join_continuations`, and the `shlex` import. Acceptance improved substantially but the Done pytest run is not yet green (39 failures remain in `tests/test_program_permission_guard.py`, plus regressions in `tests/test_permission_guard.py` and supervisor cases).

## Requirements

1. `read_shell` at line 218 is the sole reader; helpers `split_commands`, `chain_parts`, `words`, and `_check_one` consume `_parsed_snapshot`.
2. Subset grammar in `read_shell` with refuse hooks for `<<<`, `<<-`, `case`, `$((`, `((`, brace expansion, named `{fd}>`, partial `$'`/`$"`, PowerShell here-strings and lone CR.
3. Unreadable returns via `refuse()` and end-of-read unclosed-context check.
4. `check()` single read per tool; `pwsh`/`powershell` inner uses PowerShell.
5. `chain_reason` uses top `chain` and `sub_chains` only (no flattening).
6. `HUSKY=0` before `split_commands` word strip via regex on simple command text.
7. `commit_message(args, simple)` limits heredoc subject to commit-owned substitutions.
8. GraphQL uses `contains_command_substitution(" ".join(w))` on the `gh api graphql` command only.
9. `gh_amp` set in `try_sep` / `finish_heredoc` when `gh` is active and `&` splits a glued argument.
10. Prior refusals partly restored; not fully verified green.
11. R-082 a4 cases not fully updated this pass.
12. `python tools/make-manifest.py` run; `dump-cli.py --check` clean.

## Reader states and bound

`spl`, `sq`, `dq`, `ansi`, `loc`, `br`, `sub`, `btf`; bound `READ_DEPTH_BOUND = 64` in `push_split` and heredoc count.

## Commands and output

### python tools/make-manifest.py

```
make-manifest: version 2026.11.12a, 146 files hashed, VERSION + MANIFEST.json written
```

### python tools/dump-cli.py --check

```
```

### pytest tests/test_program_permission_guard.py tests/test_permission_guard.py tests/test_permission_guard_a4.py tests/test_allowlist.py tests/test_task032_supervisor_guard.py

```
77 failed, 884 passed, 20 skipped in 271.93s (0:04:31)
```

### tests/test_program_permission_guard.py alone

```
37 failed, 161 passed in 119s (approx.)
```

### tests/test_allowlist.py

```
240 passed, 20 skipped
```

### python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet

```
RESULT: SOURCES MATCH bridge 2026.11.12a
```

## Mutations

not run (the supervisor's)

## Assumed, not verified

- Heredoc inside `$(…)` inside double quotes for the continued `gh pr create` form matches bash closing rules without further operator-line work · several failures still name this form · that single test passing with a workspace cwd
- `scan_btick_body` comment and nested-quote behavior matches bash for all ROUND2 backtick cases · remaining backtick-related failures · those tests green
- Thirty-thousand-word substitution timeout case refuses within hook time via depth or rule 8 rather than a dedicated word-count cap · TIMED test still failing · that test under HOOK_SECONDS