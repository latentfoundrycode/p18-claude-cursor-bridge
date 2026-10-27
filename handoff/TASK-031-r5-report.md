# TASK-031 round 5 report

## Files changed

- `bridge/cursor-bridge/mutation-run.py`
- `tests/test_mutation_run.py`
- `docs/BUILDER_NOTES.md`
- `handoff/TASK-031-r5-report.md`

## What I did

After the per-mutant bound kills the pytest tree, `run_process` no longer calls `proc.stdout.close()` or `proc.stderr.close()` when the second `communicate` times out; it returns empty output and waits only on `proc.wait` (bounded), so a pipe holder outside the killed tree cannot block the bound on Windows reader threads. I added `test_r041_pipe_holder_outside_tree_cwd_in_copy_times_out`, which runs mutation-run end-to-end with an orphaned holder whose working directory is the scratch copy root, and asserts exit code 3, `error (timed out)` in the summary, no `internal error` on stderr, and (on Windows) that `mutation-run-phc/tree/` remains until the test ends the holder.

## Named cause

Closing stdout/stderr after the second timeout waited on `communicate`'s reader threads, which stayed blocked while an outside holder kept the pipes open; skipping pipe close/drain and returning after a bounded `proc.wait` removes that wait.

## Requirement 2 (copy removal with holder cwd in copy)

On Windows, while the orphaned holder keeps its current working directory at the scratch copy root (`mutation-run-<id>/tree/`), the `finally` `shutil.rmtree(work_sub, ignore_errors=True)` cannot remove that directory; the run still finishes with exit 3 and the normal timed-out summary (no `internal error`). In the new test, `mutation-run-phc/` is left with an empty `tree/` directory (files under `tree/` are removed first; the directory node stays pinned). The copied `.env` is not left on disk in that state because file entries under `tree/` are deleted before the directory removal fails. The next run with the same id begins with `shutil.rmtree(work_sub, ignore_errors=True)` at startup (same as any stale scratch folder); once the holder is gone, that removes the leftover. Test: `tests/test_mutation_run.py::test_r041_pipe_holder_outside_tree_cwd_in_copy_times_out`.

## Verification

### 1

```
91 passed, 1 skipped in 288.85s (0:04:48)
```

Reproduction (`-rA`):

```
PASSED tests/test_mutation_run_supervisor.py::test_task031_r4_item12_a_pipe_holder_outside_the_killed_tree_cannot_hold_the_run
1 passed in 32.45s
```

### 2

```
```

(exit 0, no output)

### 3

```
FAILED tests/test_tests_windowless.py::test_fix001_no_test_starts_a_program_around_the_default
1 failed, 175 passed in 96.72s (0:01:36)
```

Pre-existing: embedded `PIPE_*` strings in `tests/test_mutation_run_supervisor.py` use `creationflags=NO_WINDOW` without the `CREATE_NO_WINDOW` substring the scan requires; that file is out of scope for this round.

### 4

```
windowless-check: 1 file(s) scanned, 0 FAIL, 0 NOTE
```

### 5

```
True
```

### 6

```
 M bridge/cursor-bridge/mutation-run.py
 M tests/test_mutation_run.py
```

(plus uncommitted `docs/BUILDER_NOTES.md` and this report)

## Assumed, not verified

- Abandoned `communicate` reader threads and open pipe handles after `run_process` returns while the holder is still alive are reclaimed when the holder process exits and the test driver drops its `Popen` reference · CPython normally ends daemon reader threads when the process object is collected and the holder closes the inherited handles on exit · explicit post-run handle audit on Windows was not done.
- The POSIX path after the second timeout matches the Windows requirement without closing pipes · same code path (no close, bounded `wait`) · Ubuntu CI was not run in this session.
