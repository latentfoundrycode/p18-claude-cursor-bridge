# TASK-063 round 4 report

## Files changed
- bridge/cursor-bridge/permission-guard.py
- bridge/cursor-bridge/MANIFEST.json
- tests/test_permission_guard.py
- tests/test_permission_guard_a4.py
- handoff/TASK-063-r4-report.md

## Summary
Round 4 repaired the R-082 reader in place: substitution close now merges inner words and text into the parent command, quote state and gh-api detection use only the innermost spl frame, bare `&` splits commands again with a head-only gh api check, heredoc lines and shell-read bodies use the reader's words, split_commands is iterative with a depth bound, backslash-newline joining lives in the reader only, and backslash_escapes is threaded as an argument instead of a global; builder R-082 cases were added and all Done pytest targets pass.

## Requirements (one sentence each)
1. `iter_commands` / substitution `)` close in `read_shell` yield each simple command's word list from the reader; `_check_one` no longer skips commands with empty re-reads.
2. The graphql refusal in `_check_one` uses `gp.get("hassub")` on the `gh api graphql` simple command only, not the whole line.
3. `bare_amp` no longer rejects glued `&`; `gh_api_cmd` at `flush_spl` / `try_sep` resets the gh-api `&` trap to the command head after `strip_prefix`.
4. `in_quote` / `in_dq` scan only frames above `_spl_ix()` so substitutions get fresh quoting.
5. `sub_chains` / `sub_chain_wds` on substitution close feed `chain_reason` per-chain substitution state.
6. The `_join_bs_newlines` pre-pass was removed; backslash-newline join runs in the top-level reader loop from the first backslash of a run.
7. `finish_heredoc` sets `hd["line"]` from `fr["buf"]` plus text after `<<`, with `words` for `_heredoc_shell_reads`.
8. `iter_commands` queues bodies with a depth bound instead of recursive `split_commands`.
9. `mark_gh` per word was removed; `gh_api_cmd` runs once in `flush_spl`; `_parsed_snapshot` caches one read per `check` at depth 0.
10. `scan_btick_body` refuses `` \` ``; `_ansi_c_decode` octal includes the first digit and NUL refuses in the ansi close path.
11. `_check_one` passes `backslash_escapes` through; the global `_READ_ESCAPES` assignment was removed.
12. R-082 named cases were added in `tests/test_permission_guard.py` and `tests/test_permission_guard_a4.py`.
13. Dead helpers (`HEREDOC_RX`, `strip_heredocs`, `_apply_heredocs`, `chain_parts_with_substitutions`, `contains_command_substitution`, `_part_state_change`) were removed; `saw_subst` in `scan_btick_body` is `nonlocal`.

## Commands

```
python tools/make-manifest.py
```
```
make-manifest: version 2026.11.12a, 146 files hashed, VERSION + MANIFEST.json written
```

```
python tools/dump-cli.py --check
```
```
(no output; exit 0)
```

```
python -m pytest -p no:cacheprovider -q tests/test_program_permission_guard.py tests/test_permission_guard.py tests/test_permission_guard_a4.py tests/test_allowlist.py tests/test_task032_supervisor_guard.py
```
```
968 passed, 20 skipped in 174.48s (0:02:54)
```

```
python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet
```
```
bridge-check: version 2026.11.12a (2026-11-15 22:01) at <Workspace>\bridge
bridge-check: 146 OK, 0 STALE, 0 MISSING, 0 EXTRA
RESULT: SOURCES MATCH bridge 2026.11.12a
```

```
git diff --stat HEAD
```
```
 bridge/cursor-bridge/MANIFEST.json       |   4 +-
 bridge/cursor-bridge/permission-guard.py | 410 ++++++++++++++-----------------
 tests/test_permission_guard.py           |  12 +
 tests/test_permission_guard_a4.py        |  12 +
 4 files changed, 216 insertions(+), 222 deletions(-)
```

```
git rev-parse HEAD
```
```
6236deacc27aef5663e589485c759250cbdb82a8
```

```
git status --short
```
```
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/permission-guard.py
 M tests/test_permission_guard.py
 M tests/test_permission_guard_a4.py
?? handoff/TASK-063-r4-report.md
```

Mutations: not run (the supervisor's)

## Assumed, not verified
- Bash octal escape edge cases beyond the acceptance tests match GNU bash byte-for-byte · only pytest-covered `$'...'` forms were checked · more exhaustive ansi-c corpora would confirm.
- Top-level subshell `(...)` state merging matches bash for every chain shape in rule 8 · subshell tests in the supervisor file passed · exotic nested subshell mixes were not hand-traced.