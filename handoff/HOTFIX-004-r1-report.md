# HOTFIX-004 round 1 builder report

## Files changed

- `bridge/cursor-bridge/bridge-run.py`
- `bridge/cursor-bridge/mutation-run.py`
- `docs/cli-reference.json` (via `python tools/dump-cli.py`)
- `docs/CLI_REFERENCE.md` (via `python tools/dump-cli.py`)
- `docs/BUILDER_NOTES.md` (dated lines appended)
- `handoff/HOTFIX-004-r1-report.md` (this file)

## Summary

Hotfix 2026.11.24a adds configurable machine-wide heavy slots (1–4 via `heavy-slots.json` and `--heavy-slots <n>`), one heavy run per checkout (`heavy-folder-<sha256>.lock`), exclusive pid reservation for unique run ids while a launch waits, integer `slot` on heavy run rows, and a per-run-id byte lock in `mutation-run.py`. With no valid setting, one-slot stderr lines and exits match 2026.11.23a except successful heavy rows now include `"slot": 1`. All 31 acceptance tests in `tests/test_hotfix24a_heavy_slots.py` pass; one pre-existing regression case disagrees with requirement 22 on the run-log `slot` field.

## Requirements (1–25)

| Req | Meeting location |
|-----|------------------|
| 1 | `bridge-run.py`: `_read_heavy_slots_file`, `read_heavy_slots_count` |
| 2 | `read_heavy_slots_count` called from `main` for `HEAVY_KINDS` only |
| 3 | `main` prints `heavy_slots_note`; causes in `_read_heavy_slots_file` |
| 4 | `run_heavy_slots_option`, `write_heavy_slots_setting` |
| 5 | `run_heavy_slots_option` range refusal |
| 6 | `run_heavy_slots_option` requires `len(argv)==2` |
| 7 | `heavy_slot_paths`; slot 1 via `heavy_state_paths` |
| 8 | `_open_slot_lock_fds` before wait loop in `acquire_heavy_for_launch` |
| 9 | `_publish_slot_taken` suffix; `_acquire_heavy_slot_one` unchanged line |
| 10 | `_waiting_line_multi` |
| 11 | `_earliest_live_record` in multi-slot and launch paths |
| 12 | `_acquire_heavy_slot_one` preserved for n=1 |
| 13 | `checkout_identity_hash`, `folder_lock_paths` |
| 14 | `acquire_heavy_for_launch` folder byte lock held until exit via `_release_heavy_locks` |
| 15 | folder lock open errors in `acquire_heavy_for_launch` |
| 16 | folder holder published when slot taken in `acquire_heavy_for_launch` |
| 17 | folder wait uses `_waiting_line` (one-slot form) in `acquire_heavy_for_launch` |
| 18 | unified `bound_wall` in `acquire_heavy_for_launch` |
| 19 | review/watch skip `acquire_heavy_for_launch` |
| 20 | `create_pid_file_exclusive` + run_id loop in `main` |
| 21 | `_abort_before_child` removes reserved pid |
| 22 | `entry["slot"]` set from `acquire_heavy_for_launch` |
| 23 | `mutation-run.py`: lock before scratch work |
| 24 | module docstrings; `dump-cli.py` regen |
| 25 | one-slot path delegated to `_acquire_heavy_slot_one` |

## Mutation code points

| Req | Code point | Test |
|-----|------------|------|
| 1 | `_read_heavy_slots_file` strict `slots` int | `test_hotfix24a_malformed_setting_is_one_note_and_one_slot[*]` |
| 2 | `read_heavy_slots_count` only from heavy `main` path | `test_hotfix24a_no_setting_file_keeps_one_slot` (no note) |
| 3 | `heavy_slots_note` cause strings | malformed parametrized tests |
| 4 | `write_heavy_slots_setting` | `test_hotfix24a_heavy_slots_option_writes_the_setting` |
| 5 | `int(argv[1])` range in `run_heavy_slots_option` | `test_hotfix24a_heavy_slots_option_refuses_out_of_range[*]` |
| 6 | `len(argv)!=2` refuse | `test_hotfix24a_heavy_slots_option_alone_only[*]` |
| 7 | `heavy_slot_paths` | `test_hotfix24a_two_slots_second_at_once_third_waits_on_both` |
| 8 | `_open_slot_lock_fds` | `test_hotfix24a_slot_lock_error_refuses` |
| 9 | `_publish_slot_taken` suffix | two-slot taken line tests |
| 10 | `_waiting_line_multi` | third launch wait line |
| 11 | `_earliest_live_record` | `test_hotfix24a_not_free_names_the_earliest_end` |
| 12 | `_acquire_heavy_slot_one` | `test_hotfix24a_no_setting_file_keeps_one_slot` |
| 13 | `checkout_identity_hash` | `test_hotfix24a_same_checkout_waits_on_the_folder_lock` |
| 14 | `acquire_heavy_for_launch` folder lock | `test_hotfix24a_same_checkout_started_together_one_at_a_time` |
| 15 | folder lock refuse | `test_hotfix24a_folder_lock_error_refuses` |
| 16 | `publish_holder_record(folder_holder` | holder record timing tests |
| 17 | folder `_waiting_line` | same-checkout wait tests |
| 18 | folder-bound exit-123 | `test_hotfix24a_same_checkout_not_free_names_the_folder_holder` |
| 19 | no folder lock for review | no test |
| 20 | `create_pid_file_exclusive` | `test_hotfix24a_same_second_launches_get_distinct_ids` |
| 21 | `_abort_before_child` | pid absent after 125/123 in same test |
| 22 | `entry["slot"]` | `test_hotfix24a_run_row_carries_its_slot` |
| 23 | `_try_lock_byte` in `mutation-run.py` | `test_hotfix24a_mutation_run_refuses_its_run_id_in_use` |
| 24 | docstrings + dump-cli | `test_cfgb3b_committed_reference_is_current` |
| 25 | `_acquire_heavy_slot_one` body | `test_hotfix24a_no_setting_file_keeps_one_slot` |

## Missing acceptance cases

- Setting path is a symlink (hardened read via `is_link`)
- Slot counts 3 or 4 exercised end-to-end
- Checkout identity with builder `--workspace` outside launch folder
- `bridge-stop.py` ending a folder-or-slot waiter
- Symlink at mutation lock path (refuse via `is_link` when present)
- Non-lock open error on mutation lock file (Refuse message not in acceptance file)

## Verification commands

### 1. git status before edits

```
```

### 2. Acceptance tests (final run)

```
...............................                                          [100%]
31 passed in 66.40s (0:01:06)
```

### 3. Regression batch (final full run; after `last_live` fix and dump-cli)

```
3 failed, 666 passed, 5 skipped in 1233.18s (0:20:33)
FAILED tests/test_bridge_run_slot.py::test_r040_waiting_line_keeps_last_live_record
FAILED tests/test_bridge_run_slot.py::test_r040_wait_timeout_exit_123_and_log
FAILED tests/test_dump_cli.py::test_cfgb3b_committed_reference_is_current
```

After doc regen and `last_live` fix, targeted re-check:

```
FAILED tests/test_bridge_run_slot.py::test_r040_wait_timeout_exit_123_and_log
1 failed, 1 passed  (with test_cfgb3b passing)
```

Remaining failure: `assert "slot" not in log2` conflicts with requirement 22 (`"slot": 1` on heavy rows).

### 4. dump-cli

```
LASTEXITCODE=0
```

### 5. windowless-check

```
windowless-check: 38 file(s) scanned, 0 FAIL, 0 NOTE
LASTEXITCODE=0
```

### 6. ASCII scan

```
[('bridge/cursor-bridge/bridge-run.py', 20), ('bridge/cursor-bridge/bridge-run.py', 21)]
```

(Unicode ellipsis in pre-existing module docstring lines, not in hotfix text.)

### 7. git after edits

```
 M bridge/cursor-bridge/bridge-run.py
 M bridge/cursor-bridge/mutation-run.py
 M docs/CLI_REFERENCE.md
 M docs/cli-reference.json
 M docs/BUILDER_NOTES.md
?? handoff/HOTFIX-004-r1-report.md

 bridge/cursor-bridge/bridge-run.py   | 668 +++++++++++++++++++++++++++++++----
 bridge/cursor-bridge/mutation-run.py |  69 +++-
 docs/CLI_REFERENCE.md                |  16 +-
 docs/cli-reference.json              |   2 +-
 docs/BUILDER_NOTES.md                |   2 +-
 5 files changed, 676 insertions(+), 81 deletions(-)

36c92a80a6803dd6f2bf9a5fadda1b38a17f850f
```

Working tree holds uncommitted changes at commit `36c92a80a6803dd6f2bf9a5fadda1b38a17f850f`.

## Builder notes

```
2026-11-25 HOTFIX-004-r1: `tests/test_bridge_run_slot.py::test_r040_wait_timeout_exit_123_and_log` still expects no `slot` key on a successful heavy run row; HOTFIX-004 requirement 22 requires `"slot": <k>` on every heavy run that took a slot, so the regression batch stays red on that assertion until the supervisor updates the suite.

2026-11-25 HOTFIX-004-r1: verification command 6 (ASCII-only scan) flags Unicode ellipsis on module docstring lines 20-21 of `bridge-run.py`, which predates this increment; the hotfix-added docstring lines are ASCII.
```

## Assumed, not verified

- Malformed-setting `<cause>` strings (`invalid JSON`, `slots out of range`, `slots not an integer`, `extra keys`, `byte order mark`, `not an object`, `empty file`, `file too large`, `not a regular file`) match supervisor expectations for each parametrized case; confirm by reading stderr in malformed tests.

- Windows `casefold()` on `realpath` checkout identity matches design; confirm with a same-checkout test on a path differing only by case (no acceptance case).

- Mutation lock open failure other than “already running” exits 2 with `could not open the run lock`; no acceptance case.

- When a waiter moves from folder wait to slot wait, waiting lines switch forms without an extra requirement line in the acceptance file; behaviour matches design N2 only indirectly.