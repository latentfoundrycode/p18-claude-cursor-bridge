# TASK-061 round 1 report

## Files changed

- `bridge/cursor-bridge/bridge_env.py`
- `bridge/cursor-bridge/bridge-run.py`
- `bridge/cursor-bridge/review-guard.py`
- `bridge/cursor-bridge/MANIFEST.json` (regenerated)
- `tests/test_bridge_run.py`
- `tests/test_review_guard.py`
- `handoff/TASK-061-r1-report.md`

## Summary paragraph

R-079 is met by shared interval helpers in `bridge_env.py`, `learned_limit` excluding rows whose starts fall inside a review run (while the review row itself still teaches for the review kind), `verify` printing one post-OK note listing in-log-order id and kind pairs for rows inside that run, and launcher subprocess tests in `test_bridge_run.py` running under `tmp_path` so the checkout `run/launcher/runs.jsonl` is untouched; all supervisor acceptance tests and the Done-section commands pass at commit `1ac4dace0da86d466943b42ecb92e9e81bf6166c` with uncommitted changes listed below.

## Requirements

1. `bridge_env.row_start_utc` parses launcher ids with `datetime` after a regex match, stripping an optional `-digits` suffix before parsing the stamp.
2. `bridge_run.learned_limit` filters through `bridge_env.review_run_intervals` and `bridge_env.row_inside_review_run` before the existing healthy/cap logic.
3. The same four `bridge_env` functions implement start, interval, and inside-run for both programs.
4. `review_guard._launcher_rows_during_review_note` and `cmd_verify` print `launcher rows during the review: <id> <kind>, ...` only after the OK line on exit 0; the first matching review row in log order defines the run; kinds that are not plain ASCII letters are omitted from the note; GATE-INTEGRITY and CANNOT VERIFY paths do not print this note.
5. Launcher tests already ran in temp folders in the slot, driver, and release S files; `test_bridge_run.py` subprocess launches now pass `cwd` under `tmp_path`.
6. R-079-named cases were added at the end of `test_bridge_run.py` and `test_review_guard.py` as specified.
7. `python tools/make-manifest.py` was run; `VERSION` unchanged; `python tools/dump-cli.py --check` exited 0.

## Launches moved to a temporary folder (`test_bridge_run.py`)

| Test | Line |
|------|------|
| `test_limit_kills_parent_and_child` | 43 |
| `test_an_orphan_left_at_a_normal_end_is_killed` | 63 |
| `test_exit_code_and_output_pass_through` | 74 |
| `test_only_the_loops_commands_are_accepted` | 85, 88 |
| `test_usage_errors` | 259, 262 |
| `test_stripped_environment_reaches_the_child` | 268, 275, 281 |
| `test_r055_d004_a_stripped_run_gets_the_notes_names` | 307, 315 |

## Commands and output

### 1. `python tools/make-manifest.py`

```
make-manifest: version 2026.11.12a, 146 files hashed, VERSION + MANIFEST.json written
```

### 2. `python tools/dump-cli.py --check`

```
(no output; exit 0)
```

### 3. `python -m pytest -p no:cacheprovider -q -rs tests/test_program_review_rows.py`

```
.........                                                                [100%]
9 passed in 166.66s (0:02:46)
```

### 4. `python -m pytest -p no:cacheprovider -q tests/test_bridge_run.py tests/test_bridge_run_slot.py`

```
....................................s............................s...... [ 90%]
.......s                                                                 [100%]
77 passed, 3 skipped in 129.29s (0:02:09)
```

### 5. `python -m pytest -p no:cacheprovider -q tests/test_bridge_run_driver.py tests/test_release_s_launcher.py`

```
........................................................................ [ 63%]
.........................................                                [100%]
113 passed in 31.93s
```

### 6. `python -m pytest -p no:cacheprovider -q tests/test_review_guard.py`

```
...................                                                      [100%]
19 passed in 29.11s
```

### 7. Extended pytest list (Done step 7)

```
........................................................................ [ 12%]
........................................................................ [ 25%]
........................................................................ [ 38%]
........................................................................ [ 51%]
........................................................................ [ 63%]
........................................................................ [ 76%]
........................................................................ [ 89%]
...........................................................              [100%]
563 passed in 550.11s (0:09:10)
```

### 8. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`

```
bridge-check: version 2026.11.12a (2026-11-14 23:07) at <Workspace>\bridge
bridge-check: 146 OK, 0 STALE, 0 MISSING, 0 EXTRA
RESULT: SOURCES MATCH bridge 2026.11.12a
```

### 9. `git diff --stat b9a8dd0`

```
 bridge/cursor-bridge/MANIFEST.json   |   8 +-
 bridge/cursor-bridge/bridge-run.py   |   7 +-
 bridge/cursor-bridge/bridge_env.py   |  55 ++++++++++++
 bridge/cursor-bridge/review-guard.py |  45 ++++++++++
 handoff/TASK-061.md                  | 164 +++++++++++++++++++++++++++++++++++
 tests/test_bridge_run.py             |  99 ++++++++++++++++++---
 tests/test_review_guard.py           |  35 ++++++++
 7 files changed, 395 insertions(+), 18 deletions(-)
```

### 10. `git rev-parse HEAD` and `git status --short`

```
1ac4dace0da86d466943b42ecb92e9e81bf6166c
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/bridge-run.py
 M bridge/cursor-bridge/bridge_env.py
 M bridge/cursor-bridge/review-guard.py
 M tests/test_bridge_run.py
 M tests/test_review_guard.py
```

Counts above belong to commit `1ac4dace0da86d466943b42ecb92e9e81bf6166c`; the working tree held uncommitted changes to the six modified paths (not `handoff/TASK-061.md`, which was already present in the diff from the checkpoint).

## Mutations

- **M1** (exclusion for `test` kind only): `FAILED tests/test_program_review_rows.py::test_r079_every_kind_inside_a_review_is_ignored`
- **M2** (`-<digits>` suffix not accepted): `FAILED tests/test_program_review_rows.py::test_r079_a_suffixed_id_inside_a_review_is_ignored_too`
- **M3** (end dropped; all rows after review start ignored): `FAILED tests/test_program_review_rows.py::test_r079_a_row_after_the_review_s_end_still_teaches`
- **M4** (inclusive end shortened by one second): `FAILED tests/test_bridge_run.py::test_r079_learned_limit_row_at_review_end_is_inside`
- **M5**: not run
- **M6**: not run
- **M7** (note names row outside review run): `FAILED tests/test_program_review_rows.py::test_r079_verify_names_the_rows_written_during_the_review`
- **M8** (note before OK line): `FAILED tests/test_program_review_rows.py::test_r079_verify_names_the_rows_written_during_the_review`
- **M9**: not run

Each mutation was reverted before the final test run.

## Assumed, not verified

- The review row id in `runs.jsonl` matches `launch_info` from the `.err` file to the second when the slot waiter delays the first stderr line · acceptance tests write them equal · compare launcher id assignment vs err first line under slot contention in a live Review B run.
- `verify` always runs in the checkout whose `run/launcher/runs.jsonl` holds the review rows · design and acceptance tests use the same repo fixture · no check against a detached worktree review.
- Every launcher subprocess in the four test files now uses a temp cwd · only `test_bridge_run.py` needed edits; slot/driver/release S already used `launch_dir` or `folder` · a grep-only audit, not a mutation replay.