# TASK-065 round 2

## Files changed

- `bridge/cursor-bridge/bridge-run.py`
- `bridge/cursor-bridge/MANIFEST.json` (by `python tools/make-manifest.py`)
- `docs/cli-reference.json` (by `python tools/dump-cli.py`)
- `docs/CLI_REFERENCE.md` (by `python tools/dump-cli.py`)
- `tests/test_bridge_run.py`
- `docs/BUILDER_NOTES.md`
- `handoff/TASK-065-r2-report.md`

`bridge/cursor-bridge/VERSION` was rewritten by `make-manifest.py` and restored with `git restore bridge/cursor-bridge/VERSION`. It reads `2026.11.12a` and is not in the step 10 status.

## Summary

The launcher's wait before a CI watch now ends on `bridge-run: exit <rc>` whenever the child timeout has not already printed that line, keeps a pid file naming the launcher while it waits and the child while a watch runs, treats a local head that cannot be read as a failed poll instead of GitHub's head, starts a `--required` watch on a failed check only when that check holds a named context, exits 1 when a watch returns 0 and a completed latest run has failed, skips the wait when the watch names another repository, and prints a limit line that names only what the last poll found.

## G1-G9

- G1. In `main`, the watch block is lines 3022-3107. After `watch_loop` returns, lines 3098-3106 remove the pid file and, where the child timeout has not already logged the run, call `report_git_config` and `report_boundary`, print `bridge-run: exit <rc>`, and write one log entry with the seconds since `mark` and `rc`. The child's LIMIT line (lines 3074-3075) names `limit` and the seconds since `mark`; `proc.wait` still uses `seconds` (line 3072).
- G2. `write_pid_file(folder, run_id, os.getpid(), os.getpid())` runs at line 3025 before `watch_loop`, with the child's pid second at line 3068 when the child starts, and with the launcher's pid in both places at line 3092 when the child ends without the timeout. `remove_pid_file` at line 3098 runs after `watch_loop` returns and before the exit line. The timeout path also removes the file at line 3090.
- G3. `_watch_poll` (lines 2314-2332) reads the pull request first. Lines 2324-2325: where `local_head` returns nothing, the poll fails with source `local` and reason `the pushed head cannot be read`, and `head_state` is not called.
- G4. `_watch_decision` line 2297 starts the watch on a failed latest check at once only when the reading is not the base's list, or when `_check_holds` (lines 2193-2202) says that check holds a named context. The line still says `check <name> failed (<conclusion>)`.
- G5. `watch_loop` lines 2409-2416: on the runs reading, after a watch returned 0, if every latest run is completed, `_failed_run_notes` (lines 2228-2234) names each run `ci_class` calls failed and the launcher prints W6b and returns 1; otherwise it prints W6 and returns 0.
- G6. `_watch_other_repo` (lines 2053-2062) matches `--repo`, `-R`, a word beginning `--repo=`, and `-R` followed by more characters. `watch_loop` lines 2348-2350, after the `--watch` check and before the number check, print the repository line and return `start` with the words unchanged. The docstring's clauses for G5 and G6 are lines 67-68.
- G7. `finish_limit` (lines 2364-2372) uses the last poll's left, and where no poll has failed it names the local head (or `?`) and `no time left before the first poll`. The loop returns at lines 2375-2377 before `_watch_poll` when no time is left. A ready poll with no time left prints `ready (<what>), but no time left to start the watch` at lines 2432-2435 and does not print W1 or W5.
- G8. `_missing_contexts` (lines 2205-2220): a context whose `app_id` is an int and not a bool is held only by `_check_holds`, which requires that app's check of the context's name. A commit status is consulted only when the context is not app-tied. A context with `app_id` None is still held by a latest check of that name or a latest status of that context.
- G9. Five cases in `tests/test_bridge_run.py`, lines 705-776, drive `watch_loop` through `test_program_watch_wait.Case` and name R-085 and D-004. They cover `--repo` and a joined `-R` before the pull-request number (`ids=["repo-before-number", "R-joined-before-number"]`), `--repo` without `--watch`, limit 0 naming the local head, limit 0 naming `?` when the head cannot be read, and the exact ready-but-no-time left. A case that names two failed runs was not added: no recorded reply has two failed latest runs. The one recorded failure stays the supervisor's case. `main` is not called.

## Could not run

The five child-launcher cases in `tests/test_program_watch_wait.py` (round 1's two and round 2's three, G1 and G2) are skipped on Windows. They were not run. `gh` was not run.

## Mutation self-check

Each mutant was applied in `bridge-run.py`, `python -m pytest -p no:cacheprovider -q --tb=line --maxfail=1 tests/test_program_watch_wait.py` was run, and the edit was reverted. The run stopped at the first failure. The test id is that failure. Assertion traces named `<Workspace>` and are omitted; the FAILED line is quoted.

- M17 a local head that cannot be read taken as GitHub's: `test_r085_r2_a_local_head_that_cannot_be_read_is_a_failed_poll`

```
FAILED tests/test_program_watch_wait.py::test_r085_r2_a_local_head_that_cannot_be_read_is_a_failed_poll
1 failed, 30 passed, 2 skipped in 40.53s
```

- M18 any failed check starting the watch under the base's list: `test_r085_r2_under_the_base_s_list_a_failed_check_holding_no_named_context_does_not_start_the_watch`

```
FAILED tests/test_program_watch_wait.py::test_r085_r2_under_the_base_s_list_a_failed_check_holding_no_named_context_does_not_start_the_watch
1 failed, 31 passed, 2 skipped in 41.13s
```

- M19 a failed run after the watch keeping exit 0: `test_r085_r2_a_watch_that_returned_0_where_every_run_completed_and_one_failed_ends_with_1`

```
FAILED tests/test_program_watch_wait.py::test_r085_r2_a_watch_that_returned_0_where_every_run_completed_and_one_failed_ends_with_1
1 failed, 33 passed, 2 skipped in 44.02s
```

- M20 `--repo` not looked for: `test_r085_r2_a_watch_naming_a_repository_starts_without_the_wait[repo]`

```
FAILED tests/test_program_watch_wait.py::test_r085_r2_a_watch_naming_a_repository_starts_without_the_wait[repo]
1 failed, 34 passed, 2 skipped in 44.15s
```

- M21 `-R` joined to its value not looked for: `test_r085_r2_a_watch_naming_a_repository_starts_without_the_wait[R-joined]`

```
FAILED tests/test_program_watch_wait.py::test_r085_r2_a_watch_naming_a_repository_starts_without_the_wait[R-joined]
1 failed, 37 passed, 2 skipped in 45.29s
```

- M22 limit 0 reading the pull request: `test_r085_r2_a_run_with_no_time_left_reads_nothing_and_names_no_failed_poll`

```
FAILED tests/test_program_watch_wait.py::test_r085_r2_a_run_with_no_time_left_reads_nothing_and_names_no_failed_poll
1 failed, 38 passed, 2 skipped in 47.31s
```

- M23 W1 printed with no time left: `test_r085_r2_a_ready_poll_that_ends_past_the_limit_names_what_it_found`

```
FAILED tests/test_program_watch_wait.py::test_r085_r2_a_ready_poll_that_ends_past_the_limit_names_what_it_found
1 failed, 39 passed, 2 skipped in 46.06s
```

- M24 a check of another app holding an app's context: `test_r085_r2_a_context_the_rule_ties_to_an_app_is_held_only_by_that_app_s_check`

```
FAILED tests/test_program_watch_wait.py::test_r085_r2_a_context_the_rule_ties_to_an_app_is_held_only_by_that_app_s_check
1 failed, 40 passed, 2 skipped in 46.96s
```

- M25 a commit status holding an app's context: `test_r085_r2_a_commit_status_never_holds_a_context_the_rule_ties_to_an_app`

```
FAILED tests/test_program_watch_wait.py::test_r085_r2_a_commit_status_never_holds_a_context_the_rule_ties_to_an_app
1 failed, 41 passed, 2 skipped in 48.25s
```

## Commands

The counts below belong to commit `316fd4e5bda4eb3a1944369ae664c39c452b02a4`. At step 10 the working tree held uncommitted changes.

### 1. `git status --short`

```
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/bridge-run.py
 M docs/BUILDER_NOTES.md
 M docs/CLI_REFERENCE.md
 M docs/cli-reference.json
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
..............................ss............sss......................... [ 27%]
........................................................................ [ 55%]
........................................................................ [ 83%]
............................................                             [100%]
=========================== short test summary info ===========================
SKIPPED [2] tests\test_program_watch_wait.py:384: a stand-in gh on PATH is a shell script; CI's ubuntu job runs it
SKIPPED [1] tests\test_program_watch_wait.py:570: a stand-in gh on PATH is a shell script; CI's ubuntu job runs it
SKIPPED [1] tests\test_program_watch_wait.py:583: a stand-in gh on PATH is a shell script; CI's ubuntu job runs it
SKIPPED [1] tests\test_program_watch_wait.py:592: a stand-in gh on PATH is a shell script; CI's ubuntu job runs it
255 passed, 5 skipped in 108.63s (0:01:48)
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
471 passed, 20 skipped in 81.34s (0:01:21)
```

### 8. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`

```
bridge-check: version 2026.11.12a (2026-11-17 14:32) at <Workspace>\bridge
bridge-check: 146 OK, 0 STALE, 0 MISSING, 0 EXTRA
RESULT: SOURCES MATCH bridge 2026.11.12a
```

### 9. `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks`

```
windowless-check: 39 file(s) scanned, 0 FAIL, 0 NOTE
```

### 10. `git rev-parse HEAD` and `git status --short`

```
316fd4e5bda4eb3a1944369ae664c39c452b02a4
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

- Ending the launcher's process tree twice is harmless when both pid-file fields are the launcher's pid · `bridge-stop.py` ends the second pid's tree and then the first, and during the wait those are the same pid · a stop during the wait, on a host where the second kill of an already-ending tree is observed.
- A failed run's `conclusion` is a plain word · the one recorded failed run concludes `startup_failure`, and no reply here has an empty or non-text conclusion on a completed failed run · a completed run `ci_class` calls failed whose conclusion is null or not text.
- Two failed latest runs are printed in `latest_of_each` order, joined by `, ` · no recorded reply has two failed latest runs, so that join was not run · a head state with two failed latest runs.
