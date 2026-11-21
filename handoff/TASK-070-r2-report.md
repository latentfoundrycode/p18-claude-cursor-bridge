# TASK-070 round 2 report

## Files changed

- `bridge/cursor-bridge/mutation-run.py`
- `bridge/cursor-bridge/MANIFEST.json` (by `python tools/make-manifest.py` only: the `mutation-run.py` hash and the `generated` time)
- `docs/BUILDER_NOTES.md` (one pitfall line: the acceptance case below cannot pass while the counts line keeps its label)
- `handoff/TASK-070-r2-report.md`

## Summary

`main` rebuilds the scratch copy with `copy_tracked` after at least one baseline list has run and before the mutant loop, and only when the run is not returning 5 and the baseline pytest did not outlive its kill, so each mutant is applied to the bytes the cache key read. That is the same call that first built the copy: it overwrites every tracked file, `.env` and every untracked entry, then removes bytecode, and it does not remove the copy folder. `test_r090_r2_baseline_that_rewrites_a_test_file_leaves_it_pristine` passes. `test_r090_r2_baseline_that_rewrites_the_mutated_file_leaves_it_pristine` still fails: the mutant line is `m1: killed (ran)` and the exit is 0, and the case then rejects stdout because the counts line always contains `not applied`. That case was not edited. MANIFEST was regenerated and `bridge/cursor-bridge/VERSION` was restored.

## Correction

The baseline leaves the copy as it found it. In `main`, `run_baselines` returns at lines 1630-1631. The still-alive branch (lines 1634-1641) does not rebuild the copy. A baseline failure returns 5 at lines 1642-1644 and does not rebuild the copy. When `base_lists` is non-empty (lines 1645-1646), `copy_tracked(workspace, copy_root, tracked_list, untracked)` runs before the mutant loop at line 1647. `originals` are then read from that restored copy (lines 1667-1670). `copy_tracked` is the call that built the copy the keys read (line 1623), so the bytes match, including `.env` and the untracked entries, and `remove_bytecode_from_copy` runs again. It does not call `shutil.rmtree` on `copy_root`. A file a baseline test adds, that the copy did not hold, stays, except inside an untracked directory `copy_tracked` replaces. No cheaper per-file write was used: this one call is the smallest change that meets the sentence.

## Commands

Results below belong to commit `5b2c35c957bff5fb402ece29b2e63b6219c3ec30`. The working tree then held uncommitted changes, listed by the last `git status --short`. `bridge/cursor-bridge/VERSION` is not in that status. `python tools/dump-cli.py` left `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` unlisted. `docs/BUILDER_NOTES.md` is listed because the pitfall note is required there. Temporary paths in command output are written as `<tmp>`, and the repository folder as `<Workspace>`.

### 1. `git status --short`

```
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/mutation-run.py
 M docs/BUILDER_NOTES.md
?? handoff/TASK-070-r2-report.md
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

Exit code 1. `test_r090_r2_baseline_that_rewrites_the_mutated_file_leaves_it_pristine` fails at the assertion that the substring `not applied` is absent from stdout. The mutant line above that assertion is `m1: killed (ran)`.

```
.............F.................................................s........ [ 40%]
........................................................................ [ 80%]
.............................s....                                       [100%]
================================== FAILURES ===================================
___ test_r090_r2_baseline_that_rewrites_the_mutated_file_leaves_it_pristine ___

tmp_path = WindowsPath('<tmp>')

    def test_r090_r2_baseline_that_rewrites_the_mutated_file_leaves_it_pristine(tmp_path):
        """R-090, TASK-070 Done when (each distinct tests list runs once on the unmutated copy; the mutants then run as
        before), round 2 (Review B r1): a baseline test that passes and rewrites mod.py (x * 2 becomes 2 * x) must not
        change what the mutants run on. m1 replaces x * 2 and is killed, exit 0, its cache line `killed`; a second run
        serves m1 from the cache. Today the baseline's rewrite is taken as mod.py's original, m1 is `not applied`, exit 1,
        and `not applied` is cached under the key of the bytes before the baseline."""
        ws = _fixture(tmp_path, {"mod.py": MOD, "tests/test_mod.py": REWRITE_MOD_TEST})
        mf = _mutants(ws, "brw", {"mutants": [_mutant(
            "m1", "x * 2", "x * 3", ["tests/test_mod.py"], ["tests/test_mod.py::test_double"])]})
        p = _run(ws, mf)
        assert p.returncode == 0, p.stdout + p.stderr
        assert _mutant_lines(p, "m1") and "killed" in _mutant_lines(p, "m1")[0], p.stdout
>       assert "not applied" not in p.stdout, p.stdout
E       AssertionError: m1: killed (ran)
E         counts: run=1 cached=0 killed=1 survived=0 not applied=0 error=0 expected survive=0
E
E       assert 'not applied' not in 'm1: killed ... survive=0\n'
E
E         'not applied' is contained here:
E           urvived=0 not applied=0 error=0 expected survive=0
E         ?           +++++++++++

tests\test_program_mutation_baseline.py:451: AssertionError
=========================== short test summary info ===========================
SKIPPED [1] tests\test_mutation_run.py:966: this account cannot create a symbolic link here ([WinError 1314] A required privilege is not held by the client: '<tmp>/real_scratch' -> '<tmp>/link_scratch')
SKIPPED [1] tests\test_mutation_run_supervisor.py:1218: a symbolic link cannot be made here
1 failed, 175 passed, 2 skipped in 758.78s (0:12:38)
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
465 passed, 20 skipped in 210.48s (0:03:30)
```

### 8. `python -m pytest -p no:cacheprovider -q -rs tests/test_program_trace_moves.py tests/test_release_b2_stamp.py tests/test_release_t_floor.py tests/test_release_t_merge.py tests/test_release_t_stage_close.py tests/test_release_t_stamp.py`

```
........................................................................ [ 96%]
...                                                                      [100%]
75 passed in 25.68s
```

### 9. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`

```
bridge-check: version 2026.11.12a (2026-11-21 12:32) at <Workspace>/bridge
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
5b2c35c957bff5fb402ece29b2e63b6219c3ec30
```

### 12. `git status --short`

```
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/mutation-run.py
 M docs/BUILDER_NOTES.md
?? handoff/TASK-070-r2-report.md
```

## Mutation self-check

Each mutant was applied to `bridge/cursor-bridge/mutation-run.py`, the command `python -m pytest -p no:cacheprovider -q tests/test_program_mutation_baseline.py` was run, and the edit was reverted. After every revert, `git diff -- bridge/cursor-bridge/mutation-run.py | git hash-object --stdin` printed `752d14aa70677ef90d6b20c96addbd536a98c25f`, the same hash as the implementation diff.

- H6. The `copy_tracked` call after the baseline is removed, so the copy stays as the baseline wrote it. Caught by `test_r090_r2_baseline_that_rewrites_the_mutated_file_leaves_it_pristine` (`m1: not applied (ran)`, exit 1).

```
2 failed, 13 passed in 81.09s (0:01:21)
```

- H7. After the baseline, only each mutant file is copied back from the workspace, not the test files. Caught by `test_r090_r2_baseline_that_rewrites_a_test_file_leaves_it_pristine` (`m1: survived (ran)`, exit 1). On this mutant the mutated-file case still reaches `m1: killed (ran)` and then fails the same `not applied` substring assertion as the unmutated program.

```
2 failed, 13 passed in 82.25s (0:01:22)
```

## Assumed, not verified

- The second `copy_tracked` from the workspace puts back the bytes `mutant_keys` read. | `run_resolution_check` runs on the copy after the first `copy_tracked` and before the keys, and this round did not compare those file bytes with the workspace. | Compare `key_bytes` of the copy immediately after `mutant_keys` with `key_bytes` immediately after the second `copy_tracked`.
