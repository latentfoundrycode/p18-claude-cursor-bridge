# TASK-033-r3 report

## Files changed

- `bridge/cursor-bridge/bridge_env.py`
- `bridge/cursor-bridge/plan-check.py`
- `bridge/cursor-bridge/pace-report.py`
- `bridge/cursor-bridge/MANIFEST.json` (via `make-manifest.py`)
- `tests/test_plan_check.py`
- `handoff/TASK-033-r3-report.md`

## Changes by finding

### F1 — trailing parenthesis (`bridge_env.py`)

- `:492-498` — added `_id_token_hyphen_and_digit`, shared bare-ID test.
- `:525-546` — `_trail_paren_inner` uses argument-less `rstrip()` and version suffix `[-\u2014\u2013]\s*v?[\w.]+\s*$` only (no extra `[\w.]` words after a version); removed `_TrailMatch`.
- `:618-637` — parenthesis call sites use inner `str` from `_trail_subject_search`.

### F10 — one copy of bare-ID test (`bridge_env.py`)

- `:509-510` / `:563-571` — `_subject_leading_ids` and `_parenthesis_bare_item` both call `_id_token_hyphen_and_digit` (no duplicated hyphen/digit logic).

### F4 — newline-only splits (`bridge_env.py`, `plan-check.py`)

- `:665-682` — default `squash_merged_ids` git runner captures bytes; decode UTF-8 `replace`; `split("\n")` not `splitlines()`.
- `plan-check.py:179-198` — same bytes decode and `\n` split in `merged_ids`.

### F2 — timestamp OverflowError (`pace-report.py`)

- `:467-468` — `_parse_transcript_record` catches `OverflowError` with `ValueError` and `TypeError` around `fromisoformat` / UTC conversion.

### F3 — line cap and dot names (`pace-report.py`)

- `:56-57` — module-level `LINE_CAP = 64 * 1024 * 1024`.
- `:472-487` — `_read_line_capped` uses `readline(cap + 1)`, drains with `readline(65536)` and deadline checks.
- `:505-506` — `_walk_key_dir` skips entries whose name starts with `.`.

### F5 — git environment (`pace-report.py`)

- `:119-133` — `_git_env` sets `GIT_NO_LAZY_FETCH=1`, `GIT_OPTIONAL_LOCKS=0`, strips inherited `GIT_DIR`, `GIT_WORK_TREE`, `GIT_INDEX_FILE`, `GIT_OBJECT_DIRECTORY`, `GIT_ALTERNATE_OBJECT_DIRECTORIES`, `GIT_COMMON_DIR`, `GIT_NAMESPACE`.

### F6 — unambiguous ref (`pace-report.py`)

- `:61-63` — `_COMMIT_LOG_CMD` documents the exact printed command.
- `:311-320` — `_commits` runs `git log --format=... refs/heads/main --`; failure tuple uses `_COMMIT_LOG_CMD` (`:624-625`).

### F7 — far-future commit times (`pace-report.py`)

- `:331-341` — `_commits` wraps `fromtimestamp` in `(OverflowError, OSError, ValueError)`.
- `:377-382` — `_hardening_by_week` same for numstat commit times.

### F8 — stage IDs (`pace-report.py`)

- `:176-183` — `_rounds_file_ids` drops stage keys `parse_review_name` rejects; used at `:655-656`, `:807-816`.

### F9 — briefs and merge weeks (`pace-report.py`)

- `:193-196` — `_ids_with_brief` ignores tracked paths with `/` after `handoff/`.
- `:635-644` — merge week from minimum committer `dt`, not first log visit.

### F11 — regression test (`tests/test_plan_check.py`)

- `:173-175` — removed `sys.path.insert`; test uses `monkeypatch.syspath_prepend(CB)` (`:259`).
- `:264-272` — `9f6ace6` uses `== {"TASK-031"}`; `assert seen_9f6`.

### F12 — leftovers (`pace-report.py`)

- `:215-217` — removed unreachable `-r` branch in `_letter_err_belongs`.
- `:11-27` — module docstring: exit 1 is git failure; untracked handoff merged column counts every ID found.
- `:264-271` — `_has_rounds_reading` delegates to `_report_rounds`, `_err_rounds`, `_guard_rounds`.
- `:619-633` — removed unreachable `status != "ok"` branches after handoff ls-files and hardening git calls.

## Verification commands

| Command | Result |
| --- | --- |
| `python -m pytest tests/test_task033_supervisor.py tests/test_task033_supervisor_r2.py tests/test_task033_supervisor_r3.py -q -p no:cacheprovider` | pass 198 / fail 0 / skip 0 |
| `python -m pytest tests/test_plan_check.py tests/test_pace_report.py -q -p no:cacheprovider` | pass 14 / fail 0 / skip 0 |
| `python -m pytest tests/test_task032_supervisor_launcher.py … test_tests_windowless.py -q -p no:cacheprovider` | pass 382 / fail 0 / skip 0 |
| `git diff --quiet 858da29 -- tests/test_task033_supervisor.py` | exit 0 |
| `git diff --quiet a44c878 -- tests/test_task033_supervisor_r2.py` | exit 0 |
| `git diff --quiet HEAD -- tests/test_task033_supervisor_r3.py` | exit 0 |
| `python bridge/cursor-bridge/plan-check.py` | exit 0 |
| `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge/bridge_env.py bridge/cursor-bridge/plan-check.py bridge/cursor-bridge/pace-report.py` | 0 FAIL |
| `python tools/dump-cli.py --check` | pass |
| `python tools/make-manifest.py` | OK |
| `python bridge/cursor-bridge/bridge-check.py --root bridge --sources` | OK |

## Mutation checks

1. Version suffix accepts extra word after `[\w.]+` — **fail** — `test_task033r3_the_trailing_parenthesis_accepts_exactly_round_1s_shapes` (e.g. `- not done`).
2. Trailing strip `rstrip(" \t")` only — **fail** — same test (no-break space shapes).
3. Drop `OverflowError` from transcript parse — **fail** — `test_task033r3_a_timestamp_at_the_edge_of_the_calendar_is_skipped`.
4. `f.readline()` without size — **fail** — `test_task033r3_a_line_over_the_cap_is_skipped`.
5. `splitlines()` in `squash_merged_ids` — **fail** — `test_task033r3_the_reader_splits_git_output_on_newlines_only`.
6. Unset `GIT_NO_LAZY_FETCH` — **fail** — `test_task033r3_every_git_command_runs_without_lazy_fetch`.
7. Drop `--` after ref — **fail** — `test_task033r3_a_tracked_folder_named_main_is_no_failure`.
8. Merge week first log row only — **fail** — `test_task033r3_the_first_merge_is_the_earliest_commit_time`.
9. Regression `<=` plus parenthesis “any ID inside” — **fail** — `test_r044_main_regression_minus_task031` (brief’s paired mutation).

## Tests outside Scope failing under this change

None (after restore from mutation experiments).

## Summary

Round 3 aligned the shared squash-subject reader and pace report with the supervisor’s round-2 findings: round-1 trailing-parenthesis shapes and Unicode whitespace, safe transcript and commit timestamps, bounded session line reads, sanitized git environment and ref syntax, earliest merge week by committer time, top-level brief paths only, filtered stage round files, tightened main regression test, and docstring/dead-code cleanup in `pace-report.py`.

## Assumed, not verified

- `datetime.fromtimestamp(33000000000)` raises `OSError` on Windows · exercised by `test_task033r3_a_commit_dated_past_the_calendar_is_skipped` in the supervisor file, not in `tests/test_pace_report.py` · a builder test calling the same date would confirm on non-Windows platforms too.
