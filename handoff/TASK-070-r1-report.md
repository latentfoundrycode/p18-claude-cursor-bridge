# TASK-070 round 1 report

## Files changed

- `bridge/cursor-bridge/mutation-run.py`
- `bridge/cursor-bridge/MANIFEST.json` (by `python tools/make-manifest.py` only)
- `docs/cli-reference.json` (by `python tools/dump-cli.py` only)
- `docs/CLI_REFERENCE.md` (by `python tools/dump-cli.py` only)
- `handoff/TASK-070-r1-report.md`

## Summary

`mutation-run.py` now replaces backslashes only in the file part of a pytest node id (the text before the first `::`), in the ordinary mode and in `--checkpoint` mode, and before the mutant loop it runs each distinct `tests` list of the mutants that will not be served from the cache once on the unmutated copy, with the same plugin, environment, pytest configuration and per-run limit as a mutant run. A failure or an error prints one stdout line per failing list and returns 5 with no mutant run and the cache untouched; a list that hits the limit reports each of its uncached mutants as `error (timed out) (not run)`, counted as an error, and the run exits 3; a baseline pytest that outlives its kill stops the run with the existing stderr line and exit 3. The module docstring and `--help` name exit 5 and that timeout rule, and the command reference and MANIFEST were regenerated. No existing test was edited. Semgrep was not run; the Done list does not name it.

## R1-R9

- R1. `_slash_file` in `OUTCOMES_PLUGIN_CODE` (lines 60-62) keeps the text from the first `::` and replaces backslashes only in the file part (an id with no `::` is all file part); the recorded test id (line 87) and the collection-error id (line 93) both call it, and that plugin is the one `--checkpoint` mode loads.
- R2. `uncached_test_lists` (lines 1363-1371) and `mutant_cached_kill` (lines 1358-1360) collect the `tests` lists of mutants that fail the loop's own cached-kill test, in first-seen order, compared as lists; `main` calls it at line 1629 after `mutant_keys` and runs nothing when the collection is empty.
- R3. `run_baselines` (lines 1409-1424) calls `run_mutant_tests` (lines 1427-1435) on the unmutated copy for each of those lists, with `timeout_sec` and the process environment, writing `pytest-outcomes-base-<n>.json` under the scratch subfolder and applying no mutant.
- R4. `baseline_failure` (lines 1387-1391) and `baseline_failing_ids` (lines 1373-1385) accept a list only when the run did not time out, pytest exited 0, and the finished record has no collection error and no `failed` or `error` test (a skip is ignored); a failed test, an error test, a collection error, an exit other than 0 or 1, a missing finished record, or any other non-zero exit is a failure.
- R5. Baseline lines go to stdout. `format_baseline_failure` (lines 1394-1402) and `print_baseline_failures` (lines 1404-1406) print one line per failing list naming every file and each failing id, and the pytest exit when it is not 0 or 1; `main` prints them at line 1643 and returns 5 at line 1644, after every list has run, with no mutant lines and no cache write. Example: `baseline failed: tests/test_a.py tests/test_bad.py: tests/test_bad.py::test_broken`
- R6. A timed-out list whose pytest did not outlive the kill is stored by `run_baselines` (lines 1418-1420) and is not a failure; in the mutant loop (lines 1660-1663) each uncached mutant of that list is recorded as `error (timed out)` with tag `None`, which the printer (lines 1710-1715) emits as `(not run)`, under `error` and not under `run`, with no cache line, and exit 3 follows from the existing error rule (line 1726). Example: `hang: error (timed out) (not run)`
- R7. When `run_baselines` returns the still-alive list (lines 1416-1417), `main` (lines 1634-1641) prints any earlier failure lines, records `<id>: error (timed out)` with the `(not run)` tag for the uncached mutants of that list only, skips the mutant loop (line 1646), prints the `counts:` line, prints the stderr line at lines 1719-1724, and returns 3 at line 1725, writing no cache line.
- R8. `--checkpoint` mode returns at its existing point, before the copy used by the ordinary mode and before `run_baselines`. The mutant loop, `classify_outcome`, the cache key and format, the result and `counts:` lines, and exits 0-4 are unchanged for every mutant that runs. No option, configuration key or environment variable was added.
- R9. The module docstring (lines 7-12) and `build_parser`'s `desc` (lines 1476-1481) name exit 5 and say that a mutant whose tests list times out on the unmutated code is an error and is not run. `python tools/dump-cli.py` regenerated the command reference and `python tools/make-manifest.py` regenerated MANIFEST.

## Edits to existing tests

no existing test edited

## Mutation self-check

Each mutant was applied to `bridge/cursor-bridge/mutation-run.py`, the command was run, and the edit was reverted. After every revert, `git diff -- bridge/cursor-bridge/mutation-run.py | git hash-object --stdin` printed `4e91b167037e754c92f277b62889ef9a38697c76`, the same hash as the implementation diff.

- H1. The recorded test id again uses `report.nodeid.replace(chr(92), "/")`. Caught by `test_r090_escaped_id_matches_expect_fail_in_the_ordinary_mode`.

```
3 failed, 10 passed in 80.65s (0:01:20)
```

- H2. A baseline failure still prints its lines, and the mutant loop then runs (the `return 5` removed). Caught by `test_r090_baseline_failing_tests_list_exits_5`.

```
5 failed, 8 passed in 84.97s (0:01:24)
```

- H3. `uncached_test_lists` keeps every mutant's `tests` list, including mutants served from the cache. Caught by `test_r090_baseline_leaves_out_the_cached_mutants_lists`.

```
2 failed, 11 passed in 77.42s (0:01:17)
```

- H4. A baseline failure whose ids all sit in that list's mutants' `expect_fail` is dropped, so the mutant runs and is classified `killed`. Caught by `test_r090_baseline_expect_fail_failing_unmutated_is_not_a_kill`.

```
1 failed, 12 passed in 76.65s (0:01:16)
```

- H5. A timed-out baseline list is appended as a failure, so the run returns 5. Caught by `test_r041_timeout_error_continues`.

```
3 failed, 1 passed, 66 deselected in 116.28s (0:01:56)
```

## Commands

Results below belong to commit `17eccf1af14173b8774ff7e07b0159826f3f8701`. The working tree then held uncommitted changes, listed by the last `git status --short`. `bridge/cursor-bridge/VERSION` reads `2026.11.12a` and is not in that status. Temporary paths in command output are written as `<tmp>`, and the repository folder as `<Workspace>`.

### 1. `git status --short`

```
 M bridge/cursor-bridge/mutation-run.py
?? handoff/TASK-070-r1-report.md
```

### 2. `python tools/dump-cli.py`

Exit code 0. The command printed no lines.

```
```

### 3. `python tools/dump-cli.py --check`

Exit code 0. The command printed no lines.

```
```

### 4. `python tools/make-manifest.py`

```
make-manifest: version 2026.11.12a, 148 files hashed, VERSION + MANIFEST.json written
```

### 5. `git restore bridge/cursor-bridge/VERSION`

Exit code 0. The command printed no lines.

```
```

### 6. `python -m pytest -p no:cacheprovider -q -rs tests/test_program_mutation_baseline.py tests/test_mutation_run.py tests/test_mutation_run_supervisor.py`

```
.............................................................s.......... [ 40%]
........................................................................ [ 81%]
...........................s....                                         [100%]
=========================== short test summary info ===========================
SKIPPED [1] tests\test_mutation_run.py:966: this account cannot create a symbolic link here ([WinError 1314] A required privilege is not held by the client: '<tmp>/real_scratch' -> '<tmp>/link_scratch')
SKIPPED [1] tests\test_mutation_run_supervisor.py:1218: a symbolic link cannot be made here
174 passed, 2 skipped in 768.50s (0:12:48)
```

### 7. `python -m pytest -p no:cacheprovider -q -rs tests/test_allowlist.py tests/test_bridge_run_driver.py tests/test_bug030.py tests/test_bug032.py tests/test_dump_cli.py tests/test_loop_text_pace.py tests/test_loop_text_windowless.py`

```
.....s...ss.....sss....................s...............s................ [ 14%]
...............................s..........s.................s...ss.....s [ 29%]
ss....................s...............s................................. [ 44%]
..............s..........s.............................................. [ 59%]
........................................................................ [ 74%]
........................................................................ [ 89%]
.....................................................                    [100%]
=========================== short test summary info ===========================
SKIPPED [10] tests\test_allowlist.py:65: prose, not a runnable command
SKIPPED [10] tests\test_allowlist.py:106: prose, not a runnable command
465 passed, 20 skipped in 220.38s (0:03:40)
```

### 8. `python -m pytest -p no:cacheprovider -q -rs tests/test_program_trace_moves.py tests/test_release_b2_stamp.py tests/test_release_t_floor.py tests/test_release_t_merge.py tests/test_release_t_stage_close.py tests/test_release_t_stamp.py`

```
........................................................................ [ 96%]
...                                                                      [100%]
75 passed in 26.50s
```

### 9. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`

```
bridge-check: version 2026.11.12a (2026-11-21 11:20) at <Workspace>/bridge
bridge-check: 148 OK, 0 STALE, 0 MISSING, 0 EXTRA
RESULT: SOURCES MATCH bridge 2026.11.12a
```

### 10. `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks`

```
windowless-check: 41 file(s) scanned, 0 FAIL, 0 NOTE
```

### 11. `python -c "open('bridge/cursor-bridge/mutation-run.py','rb').read().decode('ascii'); print('ascii ok')"`

```
ascii ok
```

### 12. `git rev-parse HEAD`

```
17eccf1af14173b8774ff7e07b0159826f3f8701
```

### 12. `git status --short`

```
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/mutation-run.py
 M docs/CLI_REFERENCE.md
 M docs/cli-reference.json
?? handoff/TASK-070-r1-report.md
```

## Assumed, not verified

- Pytest on Linux records the parametrized id of `'caf' + chr(0xE9)` as `tests/test_mod.py::test_double[caf\xe9]`, with the backslash only inside the brackets. · The acceptance tests passed on Windows and were not run on Linux. · Run `tests/test_program_mutation_baseline.py` on Linux.
- A tests list whose every test is skipped makes pytest exit 0, so the baseline accepts it. · A skip is not a failure and a pass requires exit 0, and no all-skipped list was run. · A mutant whose only unmutated test is skipped, followed by that mutant's run.
- A finished baseline session that exits 1 and records no failed test, no error test and no collection error is a failure, so those mutants do not run. · A pass requires exit 0, and the stated fail conditions name exits other than 0 or 1 while leaving exit 1 with a clean record unstated. · A pytest session that exits 1 with only passed or skipped outcomes.
