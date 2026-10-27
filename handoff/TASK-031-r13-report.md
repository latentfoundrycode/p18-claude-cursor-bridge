# TASK-031 round 13 builder report

## Files changed

- `bridge/cursor-bridge/mutation-run.py`
- `handoff/TASK-031-r13-report.md`

## What I did

I set `PYTHONDONTWRITEBYTECODE` to `1` in `pytest_env` for every child pytest process, added `remove_bytecode_from_copy` to delete `__pycache__` trees and `.pyc` files under the copy root without following links, and call it at the end of `copy_tracked` and `archive_checkpoint` before any child runs. I ran the verification sequence and two by-hand mutants as specified.

## How this addresses the named cause

Child pytest no longer writes bytecode in the copy, and bytecode that arrived with the tracked tree, archive, or untracked entries is stripped before the resolution check or mutant runs, so Python loads source from the bytes on disk instead of a same-second stale `.pyc`.

## By-hand mutants

1. **Dropped `PYTHONDONTWRITEBYTECODE` from `pytest_env`.** Caught by `test_task031_r13_no_test_run_of_the_program_writes_bytecode`. Pytest printed: `AssertionError: m: error (unexpected failure) (ran)` and `assert 3 == 0`.
2. **Dropped the calls to `remove_bytecode_from_copy` after copy (left the helper defined).** Nothing failed; the full two-file pytest run still reported 152 passed and 1 skipped.

After both mutants I restored the fix; `git diff -- bridge/cursor-bridge/mutation-run.py` shows only the round-13 change.

## Verification command output

### 1. `python -m pytest tests/test_mutation_run_supervisor.py tests/test_mutation_run.py -q -p no:cacheprovider -rA`

```
........................................................................ [ 47%]
...........................................................s............ [ 94%]
.........                                                                [100%]
=========================== short test summary info ===========================
PASSED tests/test_mutation_run_supervisor.py::test_task031_req7_a_root_level_file_keys_its_whole_folder
PASSED tests/test_mutation_run_supervisor.py::test_task031_r4_b8_a_pytest_configuration_above_the_copy_is_not_read
PASSED tests/test_mutation_run_supervisor.py::test_task031_r6_b3_a_root_file_with_no_pytest_section_keeps_the_configuration_above_unread[setup.cfg]
PASSED tests/test_mutation_run_supervisor.py::test_task031_r6_b2_an_untracked_entry_ending_in_a_dot_or_a_space_is_refused[notes.txt ]
PASSED tests/test_mutation_run_supervisor.py::test_task031_r7_n2_a_pytest_configuration_holding_a_percent_sign_is_read_as_pytest_reads_it[tox.ini]
PASSED tests/test_mutation_run_supervisor.py::test_task031_r7_n1_a_long_plain_mutant_id_runs_its_mutant
PASSED tests/test_mutation_run_supervisor.py::test_task031_r13_no_test_run_of_the_program_writes_bytecode
SKIPPED [1] tests\test_mutation_run.py:968: this account cannot create a symbolic link here ([WinError 1314] A required privilege is not held by the client: '<temporary folder>' -> '<temporary folder>')
152 passed, 1 skipped in 517.94s (0:08:37)
```

Exit code 0.

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
?? handoff/TASK-031-r13-report.md
```

`git diff --quiet -- tests/test_mutation_run_supervisor.py` exit code: 0.

## Assumed, not verified

- That every child Python process the program starts goes through `pytest_env` (resolution check, checkpoint pytest runs, and `run_mutant_tests`); I read call sites and found no other `sys.executable` pytest launches; confirming would require a runtime audit of every code path in `main`.
- That deleting a tracked `.pyc` or `__pycache__` from the copy before `compute_key` does not change a mutant's cache key in practice: `key_bytes` only hashes tracked paths that exist as files in the copy, so a tracked bytecode file that was copied and then removed no longer contributes to the key, which could invalidate cache entries that were keyed when bytecode was present; the supervisor fixtures do not list `.pyc` paths, so this was not exercised by tests.
- Mutant 2 (no bytecode removal after copy): no test in the two allowed files failed when removal was disabled; the outcome is documented under By-hand mutants; a fixture that copies a `__pycache__` or tracked `.pyc` into the copy would be needed to catch stale bytecode carried in.
