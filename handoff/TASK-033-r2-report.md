# TASK-033-r2 report

## Files changed

- `bridge/cursor-bridge/bridge_env.py`
- `bridge/cursor-bridge/plan-check.py`
- `bridge/cursor-bridge/pace-report.py`
- `bridge/cursor-bridge/MANIFEST.json` (regenerated)
- `tests/test_plan_check.py`
- `tests/test_pace_report.py`
- `docs/cli-reference.json` (regenerated)
- `docs/CLI_REFERENCE.md` (regenerated)

## Changes by finding

**R1** (`bridge_env.py:520-570`) — `_parenthesis_bare_item` reuses the subject form’s hyphen-and-digit rule; `_parenthesis_merged_ids` calls it so grammar-pattern parenthesis items like `Scope` or `B3` merge nothing.

**R2** (`bridge_env.py:520-548`) — Replaced quadratic `_TRAIL_SUBJECT_RX` with `_trail_paren_inner` / `_trail_subject_search` (linear end parse, same accepted shapes).

**R3** (`plan-check.py:176-194`) — `merged_ids` uses `timeout=120`, returns `None` on `TimeoutExpired`, re-raises `OSError`.

**R4** (`pace-report.py:286-312`) — `_commits` uses `git log main --format=%x00%H %ct%n%s%n%(trailers:…)` and `squash_merged_ids_from_lines` on whole subject/trailer lines (no `\x1f` split).

**R5** (`pace-report.py:117-156, 848-868`) — `_git` distinguishes ok, timeout, fail (exit code), start failure; project sections and stderr use the three message forms; no git stderr printed.

**R6** (`pace-report.py:117-156`) — Every git invocation passes `-c core.fsmonitor=false`, `-c core.untrackedCache=false`, `-c log.showSignature=false`, `-C <Workspace>`, `GIT_OPTIONAL_LOCKS=0`, and numstat log gets `--no-textconv --no-ext-diff`.

**R7** (`pace-report.py:848-868`) — Exit 2 only for explicit CLI roots that are not projects; default/missing roots get named section lines and exit 0.

**R8** (`pace-report.py:158-176, 419-422, 518-571`) — Untracked when `git ls-files handoff/` is empty; brief IDs from that list; untracked merged counts all reader IDs; total row started/rounds use `n/a (handoff/ untracked)`.

**R9** (`pace-report.py:391-428, 448-468`) — `_parse_transcript_record` validates structure and strict int usage fields; bad lines skipped without broad except.

**R10** (`pace-report.py:81-87, 391-428`) — `_iso_week` converts to UTC; timestamps parsed with `fromisoformat` only (no slicing).

**R11** (`pace-report.py:634-639`) — With `--tokens`, prints `Token sources: N session file(s), M subagent file(s)` before the table.

**R12** (`pace-report.py:430-497`) — Session deadline set before walk; `os.scandir` without following links/junctions; deadline checks at dir/file/line; 64 MiB line cap.

**R13** (`pace-report.py:77-78, 559+)`) — `_ascii_name` on printed project and increment names.

**R14** (`pace-report.py:37`) — `sys.dont_write_bytecode = True` before importing `bridge_env`.

**R15** (`pace-report.py:286-312, 470-497`) — Merge week from earliest merging commit; days omitted when start after merge; rounds mean/max skip increments with no rounds reading.

**R16** (`tests/test_plan_check.py`, `tests/test_pace_report.py`) — Usage test asserts stderr `--weeks`; `monkeypatch.chdir`; subprocess timeouts; removed `# windowless: visible-ok`; per-commit main regression vs former rule (9f6ace6 loses TASK-031 only).

**R17** (`pace-report.py`) — Removed `_ERR_R_RX` and unreachable `_letter_err_belongs` tail; `plan-check.py` `OSError` raises again.

## Verification commands

| Command | Result |
| --- | --- |
| `pytest tests/test_task033_supervisor.py tests/test_task033_supervisor_r2.py -q -p no:cacheprovider` | pass (130) |
| `pytest tests/test_plan_check.py tests/test_pace_report.py -q -p no:cacheprovider` | pass (14) |
| `pytest tests/test_task032_supervisor_launcher.py … test_tests_windowless.py -q -p no:cacheprovider` | pass (382) |
| `git diff --quiet 858da29 -- tests/test_task033_supervisor.py` | exit 0 |
| `git diff --quiet HEAD -- tests/test_task033_supervisor_r2.py` | exit 0 |
| `python bridge/cursor-bridge/plan-check.py` | exit 0 |
| `windowless-check.py` on bridge_env, plan-check, pace-report | 0 FAIL |
| `python tools/dump-cli.py` + `--check` | exit 0 |
| `python tools/make-manifest.py` | OK |
| `python bridge/cursor-bridge/bridge-check.py --root bridge --sources` | SOURCES MATCH |

## Mutation checks

1. Parenthesis item test without hyphen-and-digit — caught by `test_task033r2_grammar_parenthesis_with_a_capitalised_word_merges_nothing`
2. Round-1 `_TRAIL_SUBJECT_RX` — caught by `test_task033r2_a_long_whitespace_run_is_read_in_linear_time`
3. Split commit records on `\x1f` — caught by `test_task033r2_a_separator_character_in_a_subject_merges_nothing`
4. Non-zero git exit as timeout — caught by `test_task033r2_a_missing_main_is_no_timeout`
5. Drop `core.fsmonitor=false` — caught by `test_task033r2_a_projects_git_configuration_runs_no_program`
6. Exit-2 on default roots — caught by `test_task033r2_a_default_root_missing_or_no_project_is_a_named_line`
7. Untracked handoff when any brief untracked — caught by `test_task033r2_one_new_brief_beside_a_tracked_handoff_is_no_untracked_handoff`
8. Accept bool/negative usage — caught by `test_task033r2_malformed_transcript_lines_are_skipped`
9. Session limit after walk — caught by `test_task033r2_the_session_walk_is_inside_the_limit`
10. Remove `sys.dont_write_bytecode` — caught by `test_task033r2_a_run_writes_no_bytecode`
11. Merge week from newest commit — caught by `test_task033r2_an_increment_merged_twice_counts_in_its_first_merge_week`

## Other test files failing under this change

None observed; full scoped regression suites passed.

## Summary

Round 2 narrows grammar-pattern parenthesis merging to true bare IDs, makes trail-subject parsing linear, hardens plan-check and pace-report git/subprocess handling, rewrites pace-report commit and session reads for security and correctness, and aligns builder tests with the supervisor’s R-044 expectations; all listed verification commands pass.

## Assumed, not verified

Assumed, not verified: none.
