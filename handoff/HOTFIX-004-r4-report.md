# HOTFIX-004 round 4 builder report

## Files changed

- `bridge/cursor-bridge/bridge-run.py`
- `handoff/HOTFIX-004-r4-report.md` (this file)

## Summary

Round 4 fixes Review B's defects in `create_pid_file_exclusive` and its caller: `os.makedirs` for `run/launcher/pids` is no longer grouped with the exclusive pid `os.open` in one `try` that returned False for every `FileExistsError`, so a file at the pids path raises `OSError` instead of looping through run-id suffixes forever; other reservation failures also raise (with a created-but-unwritten pid file removed) instead of answering None and letting `main` keep an unreserved id; `main` now catches that `OSError`, prints `bridge-run: refused - cannot reserve run/launcher/pids/<run id> (<error class>)`, and exits 125 before the started line.

## Requirements (37–38)

| Req | Meeting location |
|-----|------------------|
| 37 | `bridge-run.py` 1560–1583 (`create_pid_file_exclusive`: None only without `run/`; False only on pid file `FileExistsError`; other failures propagate; cleanup on write failure) |
| 38 | `bridge-run.py` 3304–3309 (`main`: `OSError` from reservation → refusal line and `return 125` before `bridge-run: started`) |

## Mutation code points

| Req | Code point | Test |
|-----|------------|------|
| 37 | `os.makedirs(d, exist_ok=True)` outside the `except FileExistsError: return False` that applies only to `os.open` | `test_hotfix24a_r4_an_unusable_pids_folder_refuses_the_launch` (`tmp_path`, `env`) |
| 37 | `except OSError:` after write that calls `os.remove(path)` and `raise` | `test_hotfix24a_r4_a_pid_file_that_cannot_be_made_is_never_a_reservation` (`tmp_path`) |
| 38 | `except OSError as exc:` in the pid reservation loop with `return 125` | `test_hotfix24a_r4_an_unusable_pids_folder_refuses_the_launch` (`tmp_path`, `env`) |
| 38 | Refusal format `cannot reserve run/launcher/pids/%s` | `test_hotfix24a_r2_an_early_refusal_leaves_no_pid_file` (indirect; same early-refusal pattern) |

## Verification (after last edit)

### Command 1 (`git status --short` before changes)

```

```

### Command 2 (acceptance)

```
...........................................s..                           [100%]
45 passed, 1 skipped in 69.39s (0:01:09)
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
669 passed, 5 skipped in 1230.40s (0:20:30)
```

### Command 4 (dump-cli)

```
LASTEXITCODE=0
```

(`python tools/dump-cli.py` produced no stdout; `python tools/dump-cli.py --check` exited 0.)

### Command 5 (windowless-check)

```
windowless-check: 38 file(s) scanned, 0 FAIL, 0 NOTE
LASTEXITCODE=0
```

### Command 6 (ASCII)

```
ascii ok
```

### Command 7 (after last edit)

`git status --short`:

```
 M bridge/cursor-bridge/bridge-run.py
?? handoff/HOTFIX-004-r4-report.md
```

`git diff --stat`:

```
 bridge/cursor-bridge/bridge-run.py | 26 ++++++++++++++++++--------
 1 file changed, 18 insertions(+), 8 deletions(-)
```

`git rev-parse HEAD`:

```
fc322d7c7d5fce574dc9c01fcde3079b94eef802
```

## Builder notes

Builder notes: none

## Assumed, not verified

Assumed, not verified: none