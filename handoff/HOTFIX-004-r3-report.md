# HOTFIX-004 round 3 builder report

## Files changed

- `bridge/cursor-bridge/bridge-run.py`
- `bridge/cursor-bridge/mutation-run.py`
- `handoff/HOTFIX-004-r3-report.md` (this file)

## Summary

Round 3 fixes two round-2 defects without disturbing requirements 1–34: `mutation-run.py` now removes the per-run scratch folder only when this process holds the run lock (`run_lock_held`), so a refused second launch no longer deletes the live run's `mutation-run-<run id>` tree; on POSIX, `bridge-run.py` `_open_heavy_lock` runs the regular-file and one-link `fstat` check immediately after `os.open` and refuses before `os.fchmod`, so a hard-linked lock path cannot strip execute bits from the victim file.

## Requirements (35–36)

| Req | Meeting location |
|-----|------------------|
| 35 | `mutation-run.py` 1554 (`run_lock_held = False`); 1578 (`run_lock_held = True` after `_try_lock_byte`); 1802–1806 (`finally`: rmtree and unlock only when `run_lock_held`) |
| 36 | `bridge-run.py` 2065–2076 (POSIX: `fstat` / one-link check before `fchmod`, early `return fd`) |

## Mutation code points

| Req | Code point | Test |
|-----|------------|------|
| 35 | `if run_lock_held:` guard around `shutil.rmtree(work_sub, ...)` in `main`'s `finally` | `test_hotfix24a_r3_a_refused_mutation_run_leaves_the_live_runs_scratch` (`tmp_path`, `env`) |
| 36 | POSIX branch: `st = os.fstat(fd)` and `st_nlink != 1` refusal before `os.fchmod(fd, 0o600)` | `test_hotfix24a_r3_a_linked_lock_files_mode_is_left_as_it_was` (`tmp_path`, `env`; skipped on Windows) |

## Verification (after last edit)

### Command 1 (`git status --short` before changes)

```

```

### Command 2 (acceptance)

```
...........................................s                             [100%]
43 passed, 1 skipped in 69.81s (0:01:09)
```

### Command 3 (regression batch)

```
.....s............................s.............s....................... [ 10%]
........................................................................ [ 21%]
........................................................................ [ 32%]
......................................s................................. [ 42%]
........................................................................ [ 53%]
.....s.................................................................. [ 64%]
........................................................................ [ 74%]
........................................................................ [ 85%]
........................................................................ [ 96%]
..........................                                               [100%]
669 passed, 5 skipped in 1234.74s (0:20:34)
```

### Command 4 (dump-cli)

```
0
```

(`python tools/dump-cli.py` produced no stdout; `python tools/dump-cli.py --check` exited 0; `echo $?` printed `0`.)

### Command 5 (windowless-check)

```
windowless-check: 38 file(s) scanned, 0 FAIL, 0 NOTE
0
```

### Command 6 (ASCII)

```
ascii ok
```

### Command 7 (after last edit)

`git status --short`:

```
 M bridge/cursor-bridge/bridge-run.py
 M bridge/cursor-bridge/mutation-run.py
```

`git diff --stat`:

```
 bridge/cursor-bridge/bridge-run.py   |  8 ++++++++
 bridge/cursor-bridge/mutation-run.py | 10 +++++++---
 2 files changed, 15 insertions(+), 3 deletions(-)
```

`git rev-parse HEAD`:

```
ae8a098867be0ae0832e3dfcbdd592501fa5de06
```

## Builder notes

Builder notes: none

## Assumed, not verified

Assumed, not verified: none