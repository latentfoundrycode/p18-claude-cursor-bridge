# TASK-031 round 3 report

## Files changed

- bridge/cursor-bridge/mutation-run.py
- tests/test_mutation_run.py
- handoff/TASK-031-r3-report.md

## Summary

Round 3 fixes checkpoint resolution so modules the increment adds but the checkpoint tree lacks are not refused when they resolve nowhere, and adds eight tests in tests/test_mutation_run.py that match the supervisor mutation driver's surviving mutants (M06, M07, M11, M13, M21, M22, M23, M25). All supervisor tests pass, including the new req8 checkpoint case for demo.newmod.

## Item 1 (code defect)

**Cause:** `run_resolution_check` treated every mutated module with no resolved origin as a refusal (`does not resolve inside the copy`). In `--checkpoint` mode the copy is built from the checkpoint commit, so a module the increment adds is absent there, resolves nowhere, and the run exited 2 before new tests ran.

**Fix:** Added a `checkpoint` flag to `run_resolution_check`. For mutant module paths, a missing origin is refused only in normal mode; in checkpoint mode only resolution outside the copy is refused. The checkpoint path passes `checkpoint=True`.

## Items 2–9 (mutants)

File sha256 before any mutant: `0633de53ca80eef50dd3a80882ee3290823b1e0661e5056acf78c885a8b8ac97`. After each restore the same sha256 was confirmed.

| Item | Test | Mutant (summary) | Pytest summary on mutant |
|------|------|------------------|--------------------------|
| 2 M06 | `test_r041_pytest_process_windowless` | Windows `run_process` Popen uses `creationflags=0` instead of `NO_WINDOW` | `1 failed in 4.00s` |
| 3 M07 | `test_r041_crlf_multiline_mutant_killed` | `apply_mutant`: `crlf = False` | `1 failed in 5.44s` |
| 4 M11 | `test_r041_parent_conftest_change_reruns` | `key_file_set`: no `conftest_paths` loop | `1 failed in 11.16s` |
| 5 M13 | `test_r041_refuse_tracked_data_link` | `validate_tracked_copy` returns immediately | `1 failed in 3.82s` |
| 6 M21 | `test_r041_refuse_dotdot_names_path_form` | `path_bad` does not reject `..` | `1 failed in 0.64s` |
| 7 M22 | `test_r041_duplicate_old_not_applied` | `apply_mutant` count uses `< 1` instead of `!= 1` | `1 failed in 3.53s` |
| 8 M23 | `test_r041_root_env_copied_when_extra_test_runs` | `copy_tracked` does not copy root `.env` | `1 failed in 3.71s` |
| 9 M25 | `test_r041_pytest_setup_error_is_run_error` | `classify_outcome` ignores pytest `ERROR` | `1 failed in 3.76s` |

## Verification

### 1

```
66 passed, 1 skipped in 205.26s (0:03:25)
```

(SKIPPED: `tests/test_mutation_run.py::test_r041_scratch_through_link_refused` — this account cannot create a symbolic link here.)

### 2

See the mutant table above (items 2–9); each run was a single test with the patched program, then byte-for-byte restore.

### 3

```
66 passed, 1 skipped in 205.26s (0:03:25)
```

### 4

```
(exit 0, no output)
```

### 5

```
176 passed in 97.92s (0:01:37)
```

### 6

```
windowless-check: 1 file(s) scanned, 0 FAIL, 0 NOTE
```

### 7

```
True
```

### 8

```
 M bridge/cursor-bridge/mutation-run.py
 M tests/test_mutation_run.py
```

## Assumed, not verified

- **M06 window probe on Windows only** · `test_r041_pytest_process_windowless` is skipped off Windows; the probe uses `GetConsoleWindow` and assumes a parent started with `CREATE_NEW_CONSOLE` gives pytest a distinct console when `mutation-run` passes `CREATE_NO_WINDOW` to its pytest child · Run the test on Windows CI and confirm it fails when `run_process` omits `NO_WINDOW`.
- **M13 link type on this machine** · The tracked-data link test uses a directory symlink when permitted, else a junction via `mklink /J`; skip only when neither works · Ubuntu CI with symlink support should exercise the POSIX branch; a Windows run without symlink privilege should exercise the junction branch.
- **Checkpoint absent-module behaviour on Linux** · The fix is platform-neutral; only the supervisor req8 test was re-run here on Windows · Full supervisor suite on Ubuntu confirms the same checkpoint path.
- **Round 2 report `none` for assumptions** · Checkpoint refusal of increment-only modules was not listed there · This round's item 1 and the checkpoint flag document that gap.
