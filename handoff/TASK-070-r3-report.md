# TASK-070 round 3 report

## Files changed

- `bridge/cursor-bridge/mutation-run.py`
- `bridge/cursor-bridge/MANIFEST.json` (by `python tools/make-manifest.py` only: the `mutation-run.py` hash and the `generated` time)
- `docs/BUILDER_NOTES.md` (the round 2 note misread where `not applied` is checked; a foreground pytest of command 6 was killed and rerun)
- `handoff/TASK-070-r3-report.md`

## Summary

In `main`, when `base_lists` is not empty, the baselines run in a second copy at `work_sub/base`, built with `os.makedirs` and `copy_tracked` the same way as the mutants' copy, and `run_baselines` receives that folder. Round 2's rebuild of the mutants' copy is gone, so nothing a baseline test writes lands in the copy the cache keys read and the mutants run on. The baseline copy stays until the existing `finally` removes `work_sub`. When `base_lists` is empty, no `base` folder is built.

## Correction

The baseline runs in a copy of its own. In `main`, after `base_lists` is computed (line 1629), lines 1630-1634 set `base_root` to `os.path.join(work_sub, "base")` when `base_lists` is not empty, create that folder, and call `copy_tracked(workspace, base_root, tracked_list, untracked)`. Lines 1635-1636 pass `base_root` to `run_baselines`. When `base_lists` is empty, `base_root` stays `copy_root` and `run_baselines` is called with an empty list, so no `base` folder is built and no baseline pytest runs. The `elif base_lists: copy_tracked(workspace, copy_root, tracked_list, untracked)` rebuild is gone: a baseline failure still returns 5 at lines 1647-1649, and the mutant loop starts at line 1650 with `copy_root` untouched since the resolution check. The `finally` at lines 1739-1741 still removes `work_sub` with `ignore_errors=True` and is the only removal of the baseline copy.

## Commands

Results below belong to commit `f7a4a9873b25b492e49c6dacab9ab464c7833a0d`. The working tree then held uncommitted changes, listed by the last `git status --short`. `bridge/cursor-bridge/VERSION` is not in that status. `python tools/dump-cli.py` left `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` unlisted. `docs/BUILDER_NOTES.md` is listed. Temporary paths in command output are written as `<tmp>`, and the repository folder as `<Workspace>`.

Command 6 was started in the foreground and killed after a partial progress line (exit 143, the word Terminated). That partial line is not the result. The fenced output under command 6 is the same command run to completion.

### 1. `git status --short`

```
 M bridge/cursor-bridge/mutation-run.py
 M docs/BUILDER_NOTES.md
?? handoff/TASK-070-r3-report.md
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

Exit code 0.

```
.................................................................s...... [ 40%]
........................................................................ [ 80%]
...............................s....                                     [100%]
=========================== short test summary info ===========================
SKIPPED [1] tests\test_mutation_run.py:966: this account cannot create a symbolic link here ([WinError 1314] A required privilege is not held by the client: '<tmp>\\real_scratch' -> '<tmp>\\link_scratch')
SKIPPED [1] tests\test_mutation_run_supervisor.py:1218: a symbolic link cannot be made here
178 passed, 2 skipped in 773.07s (0:12:53)
```

### 7. `python -m pytest -p no:cacheprovider -q -rs tests/test_allowlist.py tests/test_bridge_run_driver.py tests/test_bug030.py tests/test_bug032.py tests/test_dump_cli.py tests/test_loop_text_pace.py tests/test_loop_text_windowless.py`

Exit code 0.

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
465 passed, 20 skipped in 211.10s (0:03:31)
```

### 8. `python -m pytest -p no:cacheprovider -q -rs tests/test_program_trace_moves.py tests/test_release_b2_stamp.py tests/test_release_t_floor.py tests/test_release_t_merge.py tests/test_release_t_stage_close.py tests/test_release_t_stamp.py`

Exit code 0.

```
........................................................................ [ 96%]
...                                                                      [100%]
75 passed in 25.97s
```

### 9. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`

Exit code 0.

```
bridge-check: version 2026.11.12a (2026-11-21 14:20) at <Workspace>\bridge
bridge-check: 148 OK, 0 STALE, 0 MISSING, 0 EXTRA
RESULT: SOURCES MATCH bridge 2026.11.12a
```

### 10. `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks`

Exit code 0.

```
windowless-check: 41 file(s) scanned, 0 FAIL, 0 NOTE
```

### 11. `python -c "open('bridge/cursor-bridge/mutation-run.py','rb').read().decode('ascii'); print('ascii ok')"`

Exit code 0.

```
ascii ok
```

### 12. `git rev-parse HEAD` and `git status --short`

Exit code 0. `bridge/cursor-bridge/VERSION` is not listed.

```
f7a4a9873b25b492e49c6dacab9ab464c7833a0d
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/mutation-run.py
 M docs/BUILDER_NOTES.md
?? handoff/TASK-070-r3-report.md
```

## Mutations

H8: the baselines run in `copy_root` again (the baseline copy built but not used). `run_baselines` was called with `copy_root` while `work_sub/base` was still built. Caught by `test_r090_r3_baseline_that_adds_a_conftest_leaves_the_mutants_copy_alone` (`m1: survived (ran)`).

```
4 failed, 13 passed in 91.92s (0:01:31)
```

H9: the baseline copy built only from the tracked files, without `.env` and the untracked entries. The `copy_tracked` call for `base_root` was replaced by a copy of `tracked_list` alone. Not caught. A case that would catch it is a baseline list that fails unless `.env` or an untracked entry is in the copy that list runs in, while the mutants' copy still holds those files. No case in `tests/test_program_mutation_baseline.py` does that.

```
17 passed in 99.34s (0:01:39)
```

## Assumed, not verified

Assumed, not verified: none
