# HOTFIX-004 round 2 builder report

## Files changed

- `bridge/cursor-bridge/bridge-run.py`
- `bridge/cursor-bridge/mutation-run.py`
- `docs/cli-reference.json` (via `python tools/dump-cli.py`)
- `docs/CLI_REFERENCE.md` (via `python tools/dump-cli.py`)
- `handoff/HOTFIX-004-r2-report.md` (this file)

## Summary

Round 2 fixes review and security findings on hotfix 2026.11.24a without changing behaviour outside the defects: checkout identity now follows `workspace_of` on the pre-resolve command and `git rev-parse` on that workspace; pid files are reserved only after early refusals and are removed when pid rewrite fails; `--heavy-slots` is read only from launcher words before `--`; lock opens reject links and hard links via `fstat`; setting writes use `0o700`, retried replace, and temp cleanup; `mutation-run.py` deletes scratch before unlock and holds the run lock inside one `try`/`finally`; duplicate multi-slot logic in `acquire_heavy_slot` is removed; exception paths unlock before close; module docstring ellipses are ASCII; CLI reference regenerated.

## Requirements (26–34)

| Req | Meeting location |
|-----|------------------|
| 26 | `bridge-run.py` 1694–1704 (`checkout_identity_hash`); 3338, 3396 (`cmd_before_resolve` into `acquire_heavy_for_launch`) |
| 27 | `bridge-run.py` 3284–3297 (pid reserve after refusals); 3563 (`remove_pid_file(pid_file or reserved_pid_file)`) |
| 28 | `bridge-run.py` 1714–1718 (`run_heavy_slots_option` launcher prefix) |
| 29 | `bridge-run.py` 2055–2076 (`_open_heavy_lock`); `mutation-run.py` 1562–1569 (post-open `fstat`) |
| 30 | `bridge-run.py` 1658–1691 (`write_heavy_slots_setting`) |
| 31 | `mutation-run.py` 1553–1798 (`try` around lock through body); 1799–1807 (`finally`: rmtree then unlock) |
| 32 | `bridge-run.py` 2362–2371 (`acquire_heavy_for_launch` `except Exception`) |
| 33 | `bridge-run.py` 2183–2185 (`acquire_heavy_slot` → `_acquire_heavy_slot_one` only); `_acquire_heavy_slot_many` removed |
| 34 | `bridge-run.py` 20–21 (ASCII `...`); `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` via dump-cli |

## Mutation code points

| Req | Code point | Test |
|-----|------------|------|
| 26 | `_git_rev_parse_path(ws, ...)` and `cmd_before_resolve` passed to `acquire_heavy_for_launch` | `test_hotfix24a_r2_identity_follows_the_builders_workspace`; `test_hotfix24a_r2_the_identity_reads_the_command_never_the_launchers_options` |
| 27 | pid reservation loop after cap/review/watch refusals; `remove_pid_file(pid_file or reserved_pid_file)` | `test_hotfix24a_r2_an_early_refusal_leaves_no_pid_file` (cap, watch-only, key-file) |
| 28 | `launcher = argv[:argv.index("--")] if "--" in argv else argv` | `test_hotfix24a_r2_heavy_slots_after_the_separator_belongs_to_the_command`; `test_hotfix24a_heavy_slots_option_alone_only` |
| 29 | `stat.S_ISREG` and `st.st_nlink == 1` in `_open_heavy_lock` / mutation run lock | `test_hotfix24a_r2_a_linked_lock_file_is_refused` (heavy.lock, heavy-2.lock, folder); `test_hotfix24a_r2_a_linked_mutation_lock_is_refused` |
| 30 | retry loop and `os.remove(tmp)` before raise in `write_heavy_slots_setting` | `test_hotfix24a_r2_a_failed_setting_write_leaves_no_temporary_file` |
| 31 | `finally` at `mutation-run.py` 1799–1807: `shutil.rmtree(work_sub)` before `_unlock_byte` | no test |
| 32 | `_unlock_byte(fd)` in `acquire_heavy_for_launch` `except Exception` | no test |
| 33 | `return _acquire_heavy_slot_one(...)` only; removal of `_acquire_heavy_slot_many` | `tests/test_bridge_run_slot.py`; `tests/test_bug029_agent_name.py` (regression batch) |
| 34 | U+2026 → `...` in module docstring | command 6 ASCII check |

## Verification (after last edit)

### Command 1 (`git status --short` before changes)

not run

### Command 2 (acceptance)

```
..........................................                               [100%]
42 passed in 72.67s (0:01:12)
```

### Command 3 (regression batch)

```
..........................                                               [100%]
669 passed, 5 skipped in 1226.36s (0:20:26)
```

### Command 4 (dump-cli)

```
EXIT:0
```

(`python tools/dump-cli.py` produced no stdout; `python tools/dump-cli.py --check` exited 0.)

### Command 5 (windowless-check)

```
windowless-check: 38 file(s) scanned, 0 FAIL, 0 NOTE

EXIT:0
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
 M docs/CLI_REFERENCE.md
 M docs/cli-reference.json
?? handoff/HOTFIX-004-r2-report.md
```

`git diff --stat`:

```
 bridge/cursor-bridge/bridge-run.py   | 181 +++++++++++++----------------------
 bridge/cursor-bridge/mutation-run.py |  57 +++++------
 docs/CLI_REFERENCE.md                |   4 +-
 docs/cli-reference.json              |   2 +-
 4 files changed, 101 insertions(+), 143 deletions(-)
```

`git rev-parse HEAD`:

```
3eb8984a33aec5c7d919165892b7f50a9a3fe6bf
```

## Builder notes

Builder notes: none

## Assumed, not verified

Assumed, not verified: none