# TASK-065 round 3

## Files changed

- `bridge/cursor-bridge/bridge-run.py`
- `bridge/cursor-bridge/MANIFEST.json` (by `python tools/make-manifest.py`)
- `tests/test_bridge_run.py`
- `handoff/TASK-065-r3-report.md`

`bridge/cursor-bridge/VERSION` was rewritten by `make-manifest.py` and restored with `git restore bridge/cursor-bridge/VERSION`. It reads `2026.11.12a` and is not in the step 9 status.

## Summary

The early start before a CI watch now reads every latest check and starts at once only for a check gh reports failed (`failure`, `timed_out`, or `action_required`), taking the first of those that holds a named context under the base's list and the first of those under the default branch's list and the runs, and the child's timeout path removes the pid file before the Windows job kill.

## H1-H4

- H1. `_failed_check` (lines 2172-2179) walks every latest check in order. Under the base's list it returns the first check whose conclusion is in `WATCH_FAIL_FAST` and that `_check_holds` says holds a named context; under the default branch's list and the runs it returns the first such check. `_watch_decision` (lines 2301-2303) starts the watch on that check and W1 names it `check <name> failed (<conclusion>)`.
- H2. `WATCH_FAIL_FAST` (line 2001) is `("failure", "timed_out", "action_required")`, with the comment naming gh's `aggregate.go`. `_failed_check` line 2176 counts a check only when `status` is `completed` and `conclusion` is in that constant. Any other conclusion returns nothing from this function, so the rest of `_watch_decision` waits as before, and `_check_holds` is unchanged.
- H3. In `run_child`'s timeout path, `remove_pid_file(box["pid_file"])` is line 3087, after `write_log` (line 3086) and before `killer()` (line 3089). The call after `proc.wait` remains at line 3096. The removal after `watch_loop` remains at line 3104.
- H4. `tests/test_bridge_run.py` lines 779-812 add three cases that call `watch_loop` through `test_program_watch_wait.Case` on the recorded replies and do not call `main`. The parametrized case uses `ids=["neutral", "cancelled"]`. Under the runs, with the lint run still having no check, `neutral` and `cancelled` wait one interval and `action_required` starts at once naming security floor. Under the default branch's list, lint's failed job listed before security floor's is the check W1 names.

## Commands run while editing

`python -m pytest -p no:cacheprovider -q --tb=short tests/test_program_watch_wait.py tests/test_bridge_run.py -k "r085_r3"` failed because the runs case for `action_required` let the watch return 0, so the launcher started it again until the limit. The early-start line was already `check security floor failed (action_required)`. The case was changed to `exits=(1,)`, the same shape as the existing runs failure case.

```
.........F.                                                              [100%]
================================== FAILURES ===================================
_ test_r085_r3_under_the_runs_action_required_starts_before_the_other_run_has_a_check _
tests\test_bridge_run.py:800: in test_r085_r3_under_the_runs_action_required_starts_before_the_other_run_has_a_check
    assert rc == 0 and len(case.started()) == 1 and case.clock.sleeps == [], case.err
E   AssertionError: bridge-run: the base branch release/2026.11.03 names no required context, nor does the default branch main; waiting for the workflow runs, and the watch starts without --required
E     bridge-run: waited 0s for the workflow runs on head 10c4e6041919: check security floor failed (action_required); the watch starts
E     bridge-run: the watch returned 0 while 2 latest run(s) of head 10c4e6041919 are not completed; waited 15s; the watch starts again
E     bridge-run: the watch returned 0 while 2 latest run(s) of head 10c4e6041919 are not completed; waited 15s; the watch starts again
E     bridge-run: the watch returned 0 while 2 latest run(s) of head 10c4e6041919 are not completed; waited 15s; the watch starts again
E     bridge-run: the watch returned 0 while 2 latest run(s) of head 10c4e6041919 are not completed; waited 15s; the watch starts again
E     bridge-run: the watch returned 0 while 2 latest run(s) of head 10c4e6041919 are not completed; waited 15s; the watch starts again
E     bridge-run: the watch returned 0 while 2 latest run(s) of head 10c4e6041919 are not completed; waited 15s; the watch starts again
E     bridge-run: the watch returned 0 while 2 latest run(s) of head 10c4e6041919 are not completed; waited 15s; the watch starts again
E     bridge-run: the watch returned 0 while 2 latest run(s) of head 10c4e6041919 are not completed; waited 15s; the watch starts again
E     bridge-run: the watch returned 0 while 2 latest run(s) of head 10c4e6041919 are not completed; waited 15s; the watch starts again
E     bridge-run: the watch returned 0 while 2 latest run(s) of head 10c4e6041919 are not completed; waited 15s; the watch starts again
E     bridge-run: the watch returned 0 while 2 latest run(s) of head 10c4e6041919 are not completed; waited 15s; the watch starts again
E     bridge-run: the watch returned 0 while 2 latest run(s) of head 10c4e6041919 are not completed; waited 15s; the watch starts again
E     bridge-run: the watch returned 0 while 2 latest run(s) of head 10c4e6041919 are not completed; waited 15s; the watch starts again
E     bridge-run: the watch returned 0 while 2 latest run(s) of head 10c4e6041919 are not completed; waited 15s; the watch starts again
E     bridge-run: the watch returned 0 while 2 latest run(s) of head 10c4e6041919 are not completed; waited 15s; the watch starts again
E     bridge-run: the watch returned 0 while 2 latest run(s) of head 10c4e6041919 are not completed; waited 15s; the watch starts again
E     bridge-run: the watch returned 0 while 2 latest run(s) of head 10c4e6041919 are not completed; waited 15s; the watch starts again
E     bridge-run: the watch returned 0 while 2 latest run(s) of head 10c4e6041919 are not completed; waited 15s; the watch starts again
E     bridge-run: the watch returned 0 while 2 latest run(s) of head 10c4e6041919 are not completed; waited 15s; the watch starts again
E     bridge-run: the watch returned 0 while 2 latest run(s) of head 10c4e6041919 are not completed; waited 15s; the watch starts again
E     bridge-run: the watch returned 0 while 2 latest run(s) of head 10c4e6041919 are not completed; waited 15s; the watch starts again
E     bridge-run: the watch returned 0 while 2 latest run(s) of head 10c4e6041919 are not completed; waited 15s; the watch starts again
E     bridge-run: the watch returned 0 while 2 latest run(s) of head 10c4e6041919 are not completed; waited 15s; the watch starts again
E     bridge-run: the watch returned 0 while 2 latest run(s) of head 10c4e6041919 are not completed; waited 15s; the watch starts again
E     bridge-run: the watch returned 0 while 2 latest run(s) of head 10c4e6041919 are not completed; waited 15s; the watch starts again
E     bridge-run: the watch returned 0 while 2 latest run(s) of head 10c4e6041919 are not completed; waited 15s; the watch starts again
E     bridge-run: the watch returned 0 while 2 latest run(s) of head 10c4e6041919 are not completed; waited 15s; the watch starts again
E     bridge-run: the watch returned 0 while 2 latest run(s) of head 10c4e6041919 are not completed; waited 15s; the watch starts again
E     bridge-run: the watch returned 0 while 2 latest run(s) of head 10c4e6041919 are not completed; waited 15s; the watch starts again
E     bridge-run: the watch returned 0 while 2 latest run(s) of head 10c4e6041919 are not completed; waited 15s; the watch starts again
E     bridge-run: the watch returned 0 while 2 latest run(s) of head 10c4e6041919 are not completed; waited 15s; the watch starts again
E     bridge-run: the watch returned 0 while 2 latest run(s) of head 10c4e6041919 are not completed; waited 15s; the watch starts again
E     bridge-run: the watch returned 0 while 2 latest run(s) of head 10c4e6041919 are not completed; waited 15s; the watch starts again
E     bridge-run: the watch returned 0 while 2 latest run(s) of head 10c4e6041919 are not completed; waited 15s; the watch starts again
E     bridge-run: the watch returned 0 while 2 latest run(s) of head 10c4e6041919 are not completed; waited 15s; the watch starts again
E     bridge-run: the watch returned 0 while 2 latest run(s) of head 10c4e6041919 are not completed; waited 15s; the watch starts again
E     bridge-run: the watch returned 0 while 2 latest run(s) of head 10c4e6041919 are not completed; waited 15s; the watch starts again
E     bridge-run: the watch returned 0 while 2 latest run(s) of head 10c4e6041919 are not completed; waited 15s; the watch starts again
E     bridge-run: the watch returned 0 while 2 latest run(s) of head 10c4e6041919 are not completed; waited 15s; the watch starts again
E     bridge-run: the watch returned 0 while 2 latest run(s) of head 10c4e6041919 are not completed; waited 15s; the watch starts again
E     bridge-run: the watch returned 0 while 2 latest run(s) of head 10c4e6041919 are not completed; waited 15s; the watch starts again
E     bridge-run: the watch returned 0 while 2 latest run(s) of head 10c4e6041919 are not completed; waited 15s; the watch starts again
E     bridge-run: the watch returned 0 while 2 latest run(s) of head 10c4e6041919 are not completed; waited 15s; the watch starts again
E     bridge-run: the watch returned 0 while 2 latest run(s) of head 10c4e6041919 are not completed; waited 15s; the watch starts again
E     bridge-run: the watch returned 0 while 2 latest run(s) of head 10c4e6041919 are not completed; waited 15s; the watch starts again
E     bridge-run: the watch returned 0 while 2 latest run(s) of head 10c4e6041919 are not completed; waited 15s; the watch starts again
E     bridge-run: the watch returned 0 while 2 latest run(s) of head 10c4e6041919 are not completed; waited 15s; the watch starts again
E     bridge-run: LIMIT 3600s reached while waiting for the workflow runs on head 10c4e6041919: run tests (pull_request) is not completed and has no check listed that is not completed, run lint (pull_request) is not completed and has no check listed that is not completed
E     
E   assert (124 == 0)
=========================== short test summary info ===========================
FAILED tests/test_bridge_run.py::test_r085_r3_under_the_runs_action_required_starts_before_the_other_run_has_a_check
1 failed, 10 passed, 93 deselected in 46.37s
```

`python -m pytest -p no:cacheprovider -q --tb=line tests/test_bridge_run.py -k "r085_r3"` after that change:

```
....                                                                     [100%]
4 passed, 46 deselected in 6.13s
```

## Mutation self-check

Each mutant was applied in `bridge-run.py`, `python -m pytest -p no:cacheprovider -q --tb=line --maxfail=1 tests/test_program_watch_wait.py` was run, and the edit was reverted. The run stopped at the first failure. The test id is that failure. A repository path in a traceback is written `<Workspace>`.

- M26 only the first failed check read: `test_r085_r3_under_the_base_s_list_a_named_failed_check_after_an_unnamed_one_starts_the_watch_at_once`

```
..............................ss............F
================================== FAILURES ===================================
E   AssertionError: bridge-run: LIMIT 3600s reached while waiting for the base branch's required contexts (main) on head 61e321b4b73f: missing bridge programs (windows-latest), bridge programs (ubuntu-latest)
      
    assert (124 == 0)
<Workspace>\tests\test_program_watch_wait.py:521: AssertionError: bridge-run: LIMIT 3600s reached while waiting for the base branch's required contexts (main) on head 61e321b4b73f: missing bridge programs (windows-latest), bridge programs (ubuntu-latest)
=========================== short test summary info ===========================
FAILED tests/test_program_watch_wait.py::test_r085_r3_under_the_base_s_list_a_named_failed_check_after_an_unnamed_one_starts_the_watch_at_once
!!!!!!!!!!!!!!!!!!!!!!!!!! stopping after 1 failures !!!!!!!!!!!!!!!!!!!!!!!!!!
1 failed, 42 passed, 2 skipped in 129.53s (0:02:09)
```

- M27 `neutral` counted as a failure gh reports: `test_r085_r3_only_a_conclusion_gh_counts_as_failed_starts_the_watch_at_once[neutral-base-list]`

```
..............................ss.............F
================================== FAILURES ===================================
E   AssertionError: []
    assert [] == [15]
      
      Right contains one more item: 15
      Use -v to get more diff
<Workspace>\tests\test_program_watch_wait.py:540: AssertionError: []
=========================== short test summary info ===========================
FAILED tests/test_program_watch_wait.py::test_r085_r3_only_a_conclusion_gh_counts_as_failed_starts_the_watch_at_once[neutral-base-list]
!!!!!!!!!!!!!!!!!!!!!!!!!! stopping after 1 failures !!!!!!!!!!!!!!!!!!!!!!!!!!
1 failed, 43 passed, 2 skipped in 49.72s
```

- M28 `cancelled` counted as a failure gh reports: `test_r085_r3_only_a_conclusion_gh_counts_as_failed_starts_the_watch_at_once[cancelled-base-list]`

```
..............................ss...............F
================================== FAILURES ===================================
E   AssertionError: []
    assert [] == [15]
      
      Right contains one more item: 15
      Use -v to get more diff
<Workspace>\tests\test_program_watch_wait.py:540: AssertionError: []
=========================== short test summary info ===========================
FAILED tests/test_program_watch_wait.py::test_r085_r3_only_a_conclusion_gh_counts_as_failed_starts_the_watch_at_once[cancelled-base-list]
!!!!!!!!!!!!!!!!!!!!!!!!!! stopping after 1 failures !!!!!!!!!!!!!!!!!!!!!!!!!!
1 failed, 45 passed, 2 skipped in 52.12s
```

- M29 `action_required` not counted: `test_r085_r3_only_a_conclusion_gh_counts_as_failed_starts_the_watch_at_once[action-required-base-list]`

```
..............................ss.................F
================================== FAILURES ===================================
E   AssertionError: [15]
    assert [15] == []
      
      Left contains one more item: 15
      Use -v to get more diff
<Workspace>\tests\test_program_watch_wait.py:537: AssertionError: [15]
=========================== short test summary info ===========================
FAILED tests/test_program_watch_wait.py::test_r085_r3_only_a_conclusion_gh_counts_as_failed_starts_the_watch_at_once[action-required-base-list]
!!!!!!!!!!!!!!!!!!!!!!!!!! stopping after 1 failures !!!!!!!!!!!!!!!!!!!!!!!!!!
1 failed, 47 passed, 2 skipped in 55.62s
```

## Commands

The counts below belong to commit `4e7b014e5f368756e43683586dd75a0e166f407f`. At step 9 the working tree held uncommitted changes.

### 1. `git status --short`

```
 M bridge/cursor-bridge/bridge-run.py
 M tests/test_bridge_run.py
```

### 2. `python tools/make-manifest.py`

```
make-manifest: version 2026.11.12a, 146 files hashed, VERSION + MANIFEST.json written
```

### 3. `git restore bridge/cursor-bridge/VERSION`

```
```

The command exited 0 and printed no lines.

### 4. `python tools/dump-cli.py --check`

```
```

The command exited 0 and printed no lines.

### 5. `python -m pytest -p no:cacheprovider -q -rs tests/test_program_watch_wait.py tests/test_bridge_run.py tests/test_hotfix25a_roster_launcher.py tests/test_program_branch_rule.py`

```
..............................ss...................sss.................. [ 26%]
........................................................................ [ 53%]
........................................................................ [ 79%]
.......................................................                  [100%]
=========================== short test summary info ===========================
SKIPPED [2] tests\test_program_watch_wait.py:384: a stand-in gh on PATH is a shell script; CI's ubuntu job runs it
SKIPPED [1] tests\test_program_watch_wait.py:600: a stand-in gh on PATH is a shell script; CI's ubuntu job runs it
SKIPPED [1] tests\test_program_watch_wait.py:613: a stand-in gh on PATH is a shell script; CI's ubuntu job runs it
SKIPPED [1] tests\test_program_watch_wait.py:622: a stand-in gh on PATH is a shell script; CI's ubuntu job runs it
266 passed, 5 skipped in 123.23s (0:02:03)
```

### 6. `python -m pytest -p no:cacheprovider -q tests/test_program_ready.py tests/test_program_strip_names.py tests/test_allowlist.py tests/test_tests_windowless.py`

```
........................................................................ [ 14%]
........................................................................ [ 29%]
........................................................................ [ 43%]
..........s...ss.....sss....................s...............s........... [ 58%]
....................................s...........s.................s...ss [ 73%]
.....sss....................s...............s........................... [ 87%]
....................s...........s..........................              [100%]
471 passed, 20 skipped in 81.21s (0:01:21)
```

### 7. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`

```
bridge-check: version 2026.11.12a (2026-11-17 15:40) at <Workspace>\bridge
bridge-check: 146 OK, 0 STALE, 0 MISSING, 0 EXTRA
RESULT: SOURCES MATCH bridge 2026.11.12a
```

### 8. `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks`

```
windowless-check: 39 file(s) scanned, 0 FAIL, 0 NOTE
```

### 9. `git rev-parse HEAD` and `git status --short`

```
4e7b014e5f368756e43683586dd75a0e166f407f
```

```
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/bridge-run.py
 M tests/test_bridge_run.py
```

`bridge/cursor-bridge/VERSION` is not listed. This report was written after that status, so it is not in the listing.

## Assumed, not verified

- The five child-launcher cases still pass on Linux · they are skipped on this host because a stand-in gh on PATH is a shell script, and they were not run · CI's ubuntu job.
- On Windows the pid file is gone after a watch child hits the run's limit · `killer()` ends this process, so that path cannot be driven inside pytest, and the child-launcher cases are skipped here · a Windows watch that reaches the child's timeout while `run/launcher/pids` holds a file, then a check that the file is gone.
