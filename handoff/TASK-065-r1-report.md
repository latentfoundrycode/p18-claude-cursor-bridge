# TASK-065 round 1

## Files changed

- `bridge/cursor-bridge/bridge-run.py`
- `bridge/cursor-bridge/MANIFEST.json` (by `python tools/make-manifest.py`)
- `docs/cli-reference.json` (by `python tools/dump-cli.py`)
- `docs/CLI_REFERENCE.md` (by `python tools/dump-cli.py`)
- `tests/test_bridge_run.py`
- `docs/BUILDER_NOTES.md`
- `handoff/TASK-065-r1-report.md`

`bridge/cursor-bridge/VERSION` was rewritten by `make-manifest.py` and restored with `git restore bridge/cursor-bridge/VERSION`. It reads `2026.11.12a` and is not in the step 10 status.

## Summary

The launcher's two-minute wait for any first check is replaced by `watch_loop`, which, before `gh pr checks <n> --watch`, polls GitHub through `bridge_env` until every required context of the pull request's base has a check or a commit status on the pushed head, or a check of that head has failed, then starts the watch; with no list on the base it uses the default branch's contexts, and with none anywhere or a rule that cannot be read it waits for the head's workflow runs, starts the watch without `--required`, and starts that watch again when it returns 0 while a latest run is not completed, all inside the run's own limit.

## R1-R14

- R1. `WATCH_POLL = 15` is at line 1998. `watch_loop(argv, folder, limit, start)` is at lines 2282-2376. It reads `time.monotonic` and `time.sleep` through the module name `time`, and prints with `_watch_say` (line 2012) on stderr, flushed each line.
- R2. Lines 2289-2294: without `--watch`, `watch_loop` returns `start(list(argv), limit)` and prints nothing; if the word after `checks` is not ASCII digits, it prints the no-number line and returns the same call.
- R3. `_watch_poll` (lines 2259-2275) begins with `bridge_env.pull_refs("{owner}/{repo}", number, cwd=folder)`. A pull that cannot be read fails the poll. Where GitHub's head is not `local_head` (line 2002) and the local head can be read, it returns `mismatch` and reads no list. Otherwise it reads `head_state` and `latest_of_each`, and a list that cannot be read fails the poll.
- R4. The first poll that returns a base calls `_watch_name` (lines 2083-2119) once and keeps it. The order is the base's contexts, else the default branch's when that branch is another one and names contexts, else `the workflow runs` when both name none, the default is the base, or a rule or the default branch's name cannot be read.
- R5. `_watch_decision` (lines 2239-2256) and `_missing_contexts` (lines 2163-2178): on a named list the wait ends when every context has a latest check of that name or a latest status of that context, or `_failed_check` (lines 2154-2160) finds a latest check `ci_class` calls failed.
- R6. `_runs_initial_ready` (lines 2186-2195): at least one latest run, and each is completed or has a latest check whose `check_suite.id` is the run's `check_suite_id`. A failed latest check ends this wait too. App checks of another suite do not count.
- R7. Lines 2371-2372: a base list keeps the words; every other reading drops the word `--required`. `start` is given `_watch_left` (line 2041), the seconds left of `limit` from the wait's start.
- R8. Lines 2342-2376: only the runs reading, and only after exit 0, polls at once; every latest run completed prints W6 and returns 0; otherwise it sleeps `WATCH_POLL` and starts the same words again once each incomplete run has a non-completed check of its suite or every run is completed. Any other exit returns at once. A named list returns the watch's exit with no later read.
- R9. A failed poll sets `told_fail` and prints W4 once (lines 2324-2326), then `_watch_pause` (lines 2044-2050) sleeps `min(WATCH_POLL, seconds left)`. When no time remains, `finish_limit` (lines 2304-2306) prints W3 and `watch_loop` returns 124 without calling `start`.
- R10. W1 is lines 2366-2367, W2 is lines 2315-2319, W3 is `_watch_limit_line` (lines 2278-2279), W4 is line 2325, W5 is lines 2363-2364, W6 is line 2344. The limit left for a failed poll is `poll failed (<source>: <reason>)`, without the article, because the acceptance test counts every line that contains `a poll failed` (see Builder notes).
- R11. For `kind == "watch"`, `main` (lines 2950-3037) calls `watch_loop` with the words after `--`, the folder, the limit, and `run_child` (lines 2955-3020), which starts one child as before (`resolve`, `NO_WINDOW`, `proc.wait(timeout=seconds)`). A child timeout prints the LIMIT line, `bridge-run: exit 124`, and writes the log. A 124 from the wait with no child prints `bridge-run: exit 124` and writes one log entry (lines 3032-3036). `bridge-run: started` is still the first line. `WATCH_WAIT`, `WATCH_STEP`, `wait_for_first_check`, and `gh_pr_state` are gone. The docstring sentence is lines 59-68.
- R12. `python tools/dump-cli.py` then `python tools/dump-cli.py --check` (exit 0). `python tools/make-manifest.py`, then `git restore bridge/cursor-bridge/VERSION`.
- R13. Three cases in `tests/test_bridge_run.py`: `test_r085_d004_a_watch_with_no_pull_request_number_starts_without_the_wait` (line 670), `test_r085_d004_every_completed_run_after_a_watch_prints_that_the_exit_stands` (line 683), and `test_r085_d004_the_limit_stops_the_wait_before_a_later_green_head` (line 694). They drive `watch_loop` through `test_program_watch_wait.Case`, `Clock`, and the stand-in. The run log's single entry after a second watch was not reached: that write is in `main`, and `main` is not called in process.
- R14. Each new case names R-085 and D-004 in its name and docstring. None is parametrized.

## Mutation self-check

Each mutant was applied in `bridge-run.py`, `python -m pytest -p no:cacheprovider -q --tb=no tests/test_program_watch_wait.py` was run, and the edit was reverted. The test id is the one that failed for that mutant.

- M1 the wait skipped without `--required`: `test_r085_field_b_app_checks_green_while_the_workflow_is_queued_never_start_the_watch`
- M2 a pending context taken as present on another head: `test_r085_the_checks_of_a_head_github_has_not_yet_taken_prove_nothing`
- M3 a queued run taken as started: `test_r085_field_b_app_checks_green_while_the_workflow_is_queued_never_start_the_watch`
- M4 a run with no check taken as ready to watch: `test_r085_a_run_with_no_check_at_the_limit_ends_with_124_naming_it`
- M5 a completed run with no check holding the wait: `test_r085_a_run_that_completed_without_a_check_does_not_hold_the_wait`
- M6 the second watch not started: `test_r085_a_watch_that_returned_between_two_jobs_is_started_again_once_the_next_check_is_listed`
- M7 the interval dropped before the second watch: `test_r085_a_watch_that_returned_between_two_jobs_is_started_again_once_the_next_check_is_listed`
- M8 a non-zero watch started again: `test_r085_a_watch_that_returns_another_exit_ends_the_launcher_with_it`
- M9 the limit ignored: `test_r085_contexts_still_missing_at_the_limit_end_the_run_with_124_naming_them`
- M10 a failed poll taken as an answer: `test_r085_a_failed_poll_is_retried_and_its_reason_printed_once`
- M11 `--required` kept in one of the three cases: `test_r085_a_base_with_no_rule_waits_for_the_default_branchs_contexts_without_required`
- M12 the default branch not read: `test_r085_a_base_with_no_rule_waits_for_the_default_branchs_contexts_without_required`
- M13 a failed check not starting the watch at once: `test_r085_a_failed_check_starts_the_watch_at_once_with_contexts_still_missing`
- M14 the head's mismatch ignored: `test_r085_the_checks_of_a_head_github_has_not_yet_taken_prove_nothing`
- M15 W4 printed at every failed poll: `test_r085_a_failed_poll_is_retried_and_its_reason_printed_once`
- M16 a named list read again after the watch: `test_r085_a_head_every_required_context_holds_starts_the_watch_at_once_and_is_not_watched_again`

## Commands

The counts below belong to commit `feec8512d9879107edae0400d75f8dbfcfeb1aac`. At step 10 the working tree held uncommitted changes.

### 1. `git status --short`

```
 M bridge/cursor-bridge/bridge-run.py
 M docs/BUILDER_NOTES.md
 M tests/test_bridge_run.py
```

### 2. `python tools/dump-cli.py`

```
```

The command exited 0 and printed no lines.

### 3. `python tools/dump-cli.py --check`

```
```

The command exited 0 and printed no lines.

### 4. `python tools/make-manifest.py`

```
make-manifest: version 2026.11.12a, 146 files hashed, VERSION + MANIFEST.json written
```

### 5. `git restore bridge/cursor-bridge/VERSION`

```
```

The command exited 0 and printed no lines.

### 6. `python -m pytest -p no:cacheprovider -q -rs tests/test_program_watch_wait.py tests/test_bridge_run.py tests/test_hotfix25a_roster_launcher.py tests/test_program_branch_rule.py`

```
..............................ss........................................ [ 30%]
........................................................................ [ 60%]
........................................................................ [ 90%]
.......................                                                  [100%]
=========================== short test summary info ===========================
SKIPPED [2] tests\test_program_watch_wait.py:383: a stand-in gh on PATH is a shell script; CI's ubuntu job runs it
237 passed, 2 skipped in 99.44s (0:01:39)
```

### 7. `python -m pytest -p no:cacheprovider -q tests/test_program_ready.py tests/test_program_strip_names.py tests/test_allowlist.py tests/test_tests_windowless.py`

```
........................................................................ [ 14%]
........................................................................ [ 29%]
........................................................................ [ 43%]
..........s...ss.....sss....................s...............s........... [ 58%]
....................................s...........s.................s...ss [ 73%]
.....sss....................s...............s........................... [ 87%]
....................s...........s..........................              [100%]
471 passed, 20 skipped in 82.61s (0:01:22)
```

The command as written does not name the skipped cases.

### 8. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`

```
bridge-check: version 2026.11.12a (2026-11-17 13:46) at <Workspace>\bridge
bridge-check: 146 OK, 0 STALE, 0 MISSING, 0 EXTRA
RESULT: SOURCES MATCH bridge 2026.11.12a
```

### 9. `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks`

```
windowless-check: 39 file(s) scanned, 0 FAIL, 0 NOTE
```

### 10. `git rev-parse HEAD` and `git status --short`

```
feec8512d9879107edae0400d75f8dbfcfeb1aac
```

```
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/bridge-run.py
 M docs/BUILDER_NOTES.md
 M docs/CLI_REFERENCE.md
 M docs/cli-reference.json
 M tests/test_bridge_run.py
```

`bridge/cursor-bridge/VERSION` is not listed. This report was written after that status, so it is not in the listing.

## Assumed, not verified

- A required context is held by any latest check of that name or any latest commit status of that context, with no app filter · R5 names the check's name and the status's context and does not mention the app the rule may carry · a recorded reply whose rule names an app, with only another app's check of that name on the head.
- `gh pr checks --watch` started again on the same head reports the run's present state and does not end at once on the earlier return · the tests' stand-in returns the scripted exit and does not model `gh`'s watch · a watch started again on a real run that returned between two jobs.
- A watch whose `--required` was removed still honours `--fail-fast` · the launcher drops that one word and passes the rest through, and no test starts a real `gh pr checks` · `gh` 2.97.0's own watch behaviour with `--fail-fast` and without `--required`.
- After a watch returns 0, if the immediate poll already shows a non-completed check on every incomplete run, the launcher still sleeps one `WATCH_POLL` before starting again · R8 says to wait at the interval until that condition, and the recorded gap is not yet satisfied on that poll · a head state that is already restart-ready on the poll just after the watch.
- A failed latest check during the gap before a second watch starts that watch at once · R5 and R6 say a failed check starts the watch, and R8's until-condition does not name one; no recorded second-watch state has a failed check · a fixture whose second job's check has failed while its run is not completed.
- The limit line's left for a failed poll is `poll failed (<source>: <reason>)` · `test_r085_a_poll_that_keeps_failing_ends_at_the_limit` counts every line containing `a poll failed`, which is also R10's left, so both lines cannot be printed as specified · a change to that test, or to R10, that allows W4 and the specified left together.
- An empty list of latest runs after a 0 watch is not "every run completed" · `_all_runs_completed` requires at least one run, and R8's "every" is silent on an empty list; no recorded reply goes from a started watch to zero runs · a head whose runs list becomes empty between the watch and the next poll.
- The one run-log entry for a watch counts seconds from just before `watch_loop`, so the wait is included · the previous log started at `proc.wait`, and no test reads a watch's log entry · a watch that waited, with the log row's `seconds` compared with the wait plus the child.
- On Windows `run_child` resolves `gh` the same way `main` resolves any command, including a `.cmd` wrapper · the child-launcher case is skipped on Windows · CI's ubuntu job, which runs `test_r085_the_launcher_waits_then_runs_the_watch_it_was_given`.
