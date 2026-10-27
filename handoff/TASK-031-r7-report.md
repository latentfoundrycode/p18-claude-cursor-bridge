# TASK-031 round 7 report

## Files changed

- `bridge/cursor-bridge/mutation-run.py`
- `tests/test_mutation_run.py` (`test_r041_grandchild_holding_pipes_times_out` only)
- `handoff/TASK-031-r7-report.md`

## Summary

Round 7 closed three blocking findings from the round-6 security audit and Review A: mutant ids are validated as plain names and no longer influence results file paths, pytest `.ini`/`.cfg` roots are read without percent interpolation and decode/parse failures refuse instead of exiting 3, and the grandchild pipe-holder builder test now records pids, asserts both processes end after the timed run, and cleans up in its own `finally`.

## Item 1 (N-1)

**Cause:** Untrusted mutant `id` values were accepted without `MUTANT_ID_RX` and were embedded in `pytest-outcomes-<id>.json`, so a path-like id could delete or overwrite files outside `mutation-run-<id>/`.

**Fix:** In `load_mutants`, each id is checked with `MUTANT_ID_RX.fullmatch(mid)` before copy or cache; the mutant loop names results `pytest-outcomes-<mut_idx>.json` using `enumerate`, parallel to checkpoint files `pytest-outcomes-chk-<chk_idx>.json`.

**Tests:** `test_task031_r7_n1_a_mutant_id_that_is_not_a_plain_name_is_refused`.

Mutant results use the numeric index prefix `pytest-outcomes-` (no `-chk-`), so they cannot collide with checkpoint files named `pytest-outcomes-chk-<n>.json`.

## Item 2 (N-2)

**Cause:** Default `ConfigParser` interpolated `%` in pytest config values when building section dicts, raising before mutants ran.

**Fix:** `.ini` and `.cfg` branches use `ConfigParser(interpolation=None)`; read and section access sit in one `try` that maps `configparser.Error` and `UnicodeDecodeError` to `Refuse` with `mutation-run: invalid ini file <base>` or `invalid cfg file <base>` (exit 2).

**Tests:** `test_task031_r7_n2_a_pytest_configuration_holding_a_percent_sign_is_read_as_pytest_reads_it` for `pytest.ini`, `tox.ini`, and `setup.cfg`.

A `pytest.ini` with no `[pytest]` section still returns `{}` and counts as configuration, unchanged from before.

## Item 3 (grandchild pipe-holder test)

**Cause:** The test did not prove processes ended after the bound and relied on `teardown_module` inside the killed pytest.

**Fix:** The fixture writes holder and inner-pytest pids to files under the outer `tmp_path` before looping; after `run_mr` the test asserts the holder pid file exists, polls `pid_dead` for up to 10 s for both pids, and `finally` runs `taskkill /T` (or `killpg`) for any pid still alive. `elapsed >= 5` now only states the mutant bound was waited out. Docstring cites `handoff/TASK-031-r7.md` item 3.

**By-hand `kill_tree` check:** A temporary early `return` in `kill_tree` (removed before finish; not in diff) made the test fail with `AssertionError: holder still alive after run` / `assert False` / `pid_dead(28372)` after ~77 s call time; `finally` left no stray holders. Restored `kill_tree`; `git diff -- bridge/cursor-bridge/mutation-run.py` shows only item 1 and item 2 edits.

On a successful run the grandchild test call duration was about 7.0 s (bound 5 s plus overhead); holder and inner pytest were dead within the 10 s poll window immediately after the run ended.

## Verification commands

### 1

```
python -m pytest tests/test_mutation_run_supervisor.py tests/test_mutation_run.py -q -p no:cacheprovider -rA --durations=0
```

```
120 passed, 1 skipped in 451.79s (0:07:31)
```

Round 7 `-rA` lines:

```
PASSED tests/test_mutation_run_supervisor.py::test_task031_r7_n1_a_mutant_id_that_is_not_a_plain_name_is_refused
PASSED tests/test_mutation_run_supervisor.py::test_task031_r7_n2_a_pytest_configuration_holding_a_percent_sign_is_read_as_pytest_reads_it[pytest.ini]
PASSED tests/test_mutation_run_supervisor.py::test_task031_r7_n2_a_pytest_configuration_holding_a_percent_sign_is_read_as_pytest_reads_it[tox.ini]
PASSED tests/test_mutation_run_supervisor.py::test_task031_r7_n2_a_pytest_configuration_holding_a_percent_sign_is_read_as_pytest_reads_it[setup.cfg]
```

Skip:

```
SKIPPED [1] tests\test_mutation_run.py:968: this account cannot create a symbolic link here ([WinError 1314] A required privilege is not held by the client: ...
```

Selected durations from the same run:

```
64.87s call     tests/test_mutation_run.py::test_r041_pytest_survives_kill_stops_run
37.30s call     tests/test_mutation_run.py::test_r041_pipe_holder_outside_tree_cwd_in_copy_times_out
7.03s call     tests/test_mutation_run.py::test_r041_grandchild_holding_pipes_times_out
```

### 2

```
python -m pytest "tests/test_mutation_run.py::test_r041_grandchild_holding_pipes_times_out" -q -p no:cacheprovider -rA --durations=0
```

```
PASSED tests/test_mutation_run.py::test_r041_grandchild_holding_pipes_times_out
1 passed in 8.76s
```

```
7.01s call     tests/test_mutation_run.py::test_r041_grandchild_holding_pipes_times_out
```

### 3

```
python tools/dump-cli.py --check
```

Exit code 0 (no output).

### 4

```
python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge/mutation-run.py
```

```
windowless-check: 1 file(s) scanned, 0 FAIL, 0 NOTE
```

### 5

```
python -c "d=open('bridge/cursor-bridge/mutation-run.py','rb').read(); print(all(b < 128 for b in d))"
```

```
True
```

### 6

```
git status --porcelain
```

```
 M bridge/cursor-bridge/mutation-run.py
 M tests/test_mutation_run.py
?? handoff/TASK-031-r7-report.md
```

```
git diff --quiet -- tests/test_mutation_run_supervisor.py
```

Exit code 0.

### 7

`tasklist /FI "IMAGENAME eq python.exe" /V` failed under Git Bash (path mangling). PowerShell `Get-Process python` after commands 1 and 2 showed one `python.exe` with an empty window title (the invoking shell), not pytest or mutation-run titles from the finished tests. No test-started process appeared still running by title or timing.

## Assumed, not verified

- `ConfigParser(interpolation=None)` agrees with pytest 9.1.1's `iniconfig` on whether a file parses and whether the pytest section exists for the cases this round uses; known divergences not exercised here include duplicate section names (ConfigParser can merge or error depending on version; iniconfig may differ), keys without `=` (iniconfig often tolerates; strict ConfigParser may not), line continuations and comment placement (rules differ), and `setup.cfg` where a plain `[pytest]` section is ignored by our `[tool:pytest]` rule but might be read by pytest in some layouts.
- With `addopts = -s`, the grandchild holder's `stdout=sys.stdout` is the same stream pytest inherited from `run_process`'s pipe, not a capture buffer; we did not attach a tracer to the kernel handles.
- Item 3 process-group teardown via `os.killpg` on POSIX was not run on this Windows machine; behaviour there is assumed to match the pattern used in `test_r041_pipe_holder_outside_tree_cwd_in_copy_times_out`.
