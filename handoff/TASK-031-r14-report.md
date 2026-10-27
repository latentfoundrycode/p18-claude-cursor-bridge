# TASK-031 round 14 report

## Files changed

- `bridge/cursor-bridge/mutation-run.py` (body of `remove_bytecode_from_copy` only)

## What I did

In `remove_bytecode_from_copy` I removed the loop that walked every file in the copy and deleted paths ending in `.pyc`, and left the existing top-down walk that deletes only directories named `__pycache__` when they are not links. I ran the by-hand mutant (that loop restored), then put the fix back and ran the verification commands from the brief.

## How the change addresses the named cause

The copy step no longer strips loose `.pyc` test fixtures, so mutant runs fail or survive only because of the mutated source under test, not because bytecode test data vanished before pytest ran.

## By-hand mutant

Re-applied round 13's `filenames` loop that calls `os.remove` on every non-link path ending in `.pyc` anywhere under the copy root. `test_task031_r14_a_tracked_pyc_the_tests_read_stays_in_the_copy` failed with pytest printing:

```
E       AssertionError: equiv: killed (ran)
E         counts: run=1 cached=0 killed=1 survived=0 not applied=0 error=0 expected survive=0
```

Summary line from that run: `1 failed, 152 passed, 1 skipped in 523.34s (0:08:43)` (exit code 1). After restoring the fix, `git diff -- bridge/cursor-bridge/mutation-run.py` showed only the removal of that loop.

## Verification

### 1. `python -m pytest tests/test_mutation_run_supervisor.py tests/test_mutation_run.py -q -p no:cacheprovider -rA`

Exit code 0.

```
........................................................................ [ 46%]
............................................................s........... [ 93%]
..........                                                               [100%]
=========================== short test summary info ===========================
PASSED tests/test_mutation_run_supervisor.py::test_task031_r13_no_test_run_of_the_program_writes_bytecode
PASSED tests/test_mutation_run_supervisor.py::test_task031_r14_a_tracked_pyc_the_tests_read_stays_in_the_copy
SKIPPED [1] tests\test_mutation_run.py:968: this account cannot create a symbolic link here ([WinError 1314] A required privilege is not held by the client: '<temporary folder>\\real_scratch' -> '<temporary folder>\\link_scratch')
153 passed, 1 skipped in 544.07s (0:09:04)
```

### 2. `python tools/dump-cli.py --check`

Exit code 0 (no output).

### 3. `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge/mutation-run.py`

```
windowless-check: 1 file(s) scanned, 0 FAIL, 0 NOTE
```

Exit code 0.

### 4. ASCII check

```
True
```

### 5. `git status --porcelain` and `git diff --quiet -- tests/test_mutation_run_supervisor.py`

```
 M bridge/cursor-bridge/mutation-run.py
?? handoff/TASK-031-r14-report.md
```

`git diff --quiet -- tests/test_mutation_run_supervisor.py` exit code: 0.

## Notes for the supervisor

none

## Assumed, not verified

- The import system on the Python versions in the CI matrix never loads a loose `.pyc` as the module implementation when a `.py` with the same basename sits beside it, and uses stale bytecode for a normal source module only from `__pycache__`; confirmation would be a targeted import experiment on each matrix version.
- A sourceless `.pyc` committed outside `__pycache__` and imported with no adjacent `.py` would remain in the copy after this change; the brief treats that as acceptable because such bytecode is not how the import system resolves modules beside source, and round 13's loose-file deletion was not required for the stated fix.
