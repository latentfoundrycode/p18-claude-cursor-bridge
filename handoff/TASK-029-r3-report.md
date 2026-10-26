# TASK-029 round 3 report

## Files changed

- `bridge/cursor-bridge/bridge-run.py`

## Summary

Round 3 hardens the machine-wide heavy slot in `bridge-run.py` only: holder records are read through a non-following, non-blocking open with a size cap and broad exception handling; `--kind review` refuses commands that `kind_of` names unless the head is `cursor-agent`; publication wraps folder creation and mkstemp in failure handling and writes via `os.fdopen`; POSIX lock open uses `O_NOFOLLOW` and `os.fchmod`; Windows liveness uses `WaitForSingleObject` alone; unused `run_id_epoch` is removed.

## Requirements

1. **`read_holder_record`** — Opens with `O_RDONLY`, `O_NONBLOCK`, `O_NOFOLLOW`, and `O_BINARY` (each via `getattr`); requires a regular file via `os.fstat` and `stat.S_ISREG`; reads at most 4,097 bytes; decodes strict UTF-8 and parses JSON; maps `OSError`, `ValueError`, `RecursionError`, `MemoryError`, and `OverflowError` to no record; closes the descriptor in `finally`. Tests: `test_r040_untrusted_records_in_process`, `test_r040_untrusted_records_by_launch` (all cases), `test_r040_special_file_records_posix` (skipped on Windows).

2. **`REVIEW_ONLY_REFUSE` constant and `main`** — After the limit cap refusal and before the watch refusal, refuses when `kind == "review"` and `kind_of(cmd)` is not `None` and `head_of(cmd) != "cursor-agent"`. Tests: `test_r040_review_refuses_a_heavy_command[False]`, `test_r040_review_refuses_a_heavy_command[True]`; `test_r040_review_and_watch_skip_slot` and `tests/test_bridge_run.py` unchanged.

3. **`publish_holder_record`** — `os.makedirs` and `tempfile.mkstemp` inside `try`; write through `os.fdopen` on the mkstemp fd; five `os.replace` retries; any `OSError` removes the temp file if present, prints the note once, returns `False`. Tests: `test_r040_publication_failure_is_a_note`, `test_r040_unpublishable_record_keeps_the_slot`, `test_r040_record_published_while_read`.

4. **`_open_heavy_lock`** (POSIX) — `O_NOFOLLOW` on open; `os.fchmod(fd, 0o600)` instead of `os.chmod` by path. Tests: `test_r040_lock_link_not_followed_posix` (skipped on Windows), `test_r040_posix_lock_modes`, `test_r040_lock_folder_refused`.

5. **`process_alive`** (Windows) — Alive only when `WaitForSingleObject(handle, 0) == 258`; `GetExitCodeProcess` removed. Test: `test_r040_exit_code_259_reads_as_dead`.

6. **`run_id_epoch`** — Removed (nothing called it).

## POSIX-only tests (skipped on Windows; expected on Linux)

- **`test_r040_special_file_records_posix`**: `read_holder_record` opens the holder path with `O_NOFOLLOW`, so a symlink to `/dev/zero` is not followed and fails with `OSError` → `None`. A FIFO opens non-blockingly; `os.fstat` shows it is not `S_ISREG` → `None` without blocking on read.

- **`test_r040_lock_link_not_followed_posix`**: `_open_heavy_lock` adds `O_NOFOLLOW` to `os.open` on the lock path, so a symlink at `heavy.lock` raises `OSError` (`ELOOP`), which `acquire_heavy_slot` turns into the existing refusal line and exit 125; `os.fchmod` on the descriptor never runs on a followed target, so the real file's mode stays 0o644.

## Verification

### Focused slot tests

```
$ python -m pytest tests/test_bridge_run_slot.py -q -p no:cacheprovider -k "untrusted_records or exit_code_259 or review_refuses or publication_failure or special_file or lock_link"
..s...........s.                                                         [100%]
14 passed, 2 skipped, 30 deselected in 52.10s
```

### Full suite with durations

```
$ python -m pytest tests/test_bridge_run_slot.py tests/test_a4_followups.py tests/test_bridge_run.py tests/test_loop_guard.py -q -p no:cacheprovider --durations=0
```

Summary line:

```
134 passed, 3 skipped in 120.32s (0:02:00)
```

`tests/test_bridge_run_slot.py` durations lines (pytest `--durations=0`):

```
7.55s call     tests/test_bridge_run_slot.py::test_r040_wait_before_record_published
5.65s call     tests/test_bridge_run_slot.py::test_r040_scale_not_honoured_on_a_heavy_run_without_allow_any
5.45s call     tests/test_bridge_run_slot.py::test_r040_untrusted_records_by_launch[{"kind": "test", "run_id": "2026-01-01T00:00:00Z", "start": "2026-01-01T00:00:00Z", "pid": __PID__, "created": 9999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999, "limit": 9}]
5.44s call     tests/test_bridge_run_slot.py::test_r040_untrusted_records_by_launch[{"kind": "test\\u0007", "run_id": "2026-01-01T00:00:00Z", "start": "2026-01-01T00:00:00Z", "pid": __PID__, "created": __CREATED__, "limit": 9}]
5.44s call     tests/test_bridge_run_slot.py::test_r040_waiting_line_keeps_last_live_record
5.43s call     tests/test_bridge_run_slot.py::test_r040_untrusted_records_by_launch[deep:100000]
5.42s call     tests/test_bridge_run_slot.py::test_r040_untrusted_records_by_launch[{"kind": "test", "run_id": "2026-01-01T00:00:00Z", "start": "2026-01-01T00:00:00Z", "pid": __PID32__, "created": __CREATED__, "limit": 9}]
5.42s call     tests/test_bridge_run_slot.py::test_r040_untrusted_records_by_launch[{"kind": "test", "run_id": "2026-01-01T00:00:00Z", "start": "0001-01-01T00:00:00Z", "pid": __PID__, "created": __CREATED__, "limit": 9}]
5.42s call     tests/test_bridge_run_slot.py::test_r040_untrusted_records_by_launch[not json]
5.42s call     tests/test_bridge_run_slot.py::test_r040_provisional_bound_without_record
5.41s call     tests/test_bridge_run_slot.py::test_r040_untrusted_records_by_launch[["x"]]
5.41s call     tests/test_bridge_run_slot.py::test_r040_untrusted_records_by_launch[{"kind": "test", "run_id": "2026-01-01T00:00:00Z", "start": "2026-01-01T00:00:00Z", "pid": __PID__, "created": __CREATED__, "limit": 1e400}]
5.40s call     tests/test_bridge_run_slot.py::test_r040_untrusted_records_by_launch[hex:fffe7b007d00]
4.60s call     tests/test_bridge_run_slot.py::test_r040_seconds_excludes_wait
4.24s call     tests/test_bridge_run_slot.py::test_r040_wait_timeout_exit_123_and_log
3.75s call     tests/test_bridge_run_slot.py::test_r040_two_heavy_runs_serialize_commands
2.82s call     tests/test_bridge_run_slot.py::test_r040_bound_stays_first_fixed
1.92s call     tests/test_bridge_run_slot.py::test_r040_holder_that_waited_publishes_slot_taken_start
1.57s call     tests/test_bridge_run_slot.py::test_r040_exit_code_259_reads_as_dead
1.38s call     tests/test_bridge_run_slot.py::test_r040_wait_uses_monotonic_clock
1.37s call     tests/test_bridge_run_slot.py::test_r040_killed_holder_frees_slot
1.25s call     tests/test_bridge_run_slot.py::test_r040_review_and_watch_skip_slot
1.07s call     tests/test_bridge_run_slot.py::test_r040_limit_under_one_publishes_one
1.03s call     tests/test_bridge_run_slot.py::test_r040_untrusted_records_in_process
0.79s call     tests/test_bridge_run_slot.py::test_r040_wellformed_record_named_in_wait_line
0.54s call     tests/test_bridge_run_slot.py::test_r040_record_published_while_read
0.38s call     tests/test_bridge_run_slot.py::test_r040_review_refuses_a_heavy_command[False]
0.36s call     tests/test_bridge_run_slot.py::test_r040_review_refuses_a_heavy_command[True]
0.33s call     tests/test_bridge_run_slot.py::test_r040_slot_scale_ignored_without_allow_any
0.33s call     tests/test_bridge_run_slot.py::test_r040_unpublishable_record_keeps_the_slot
0.21s call     tests/test_bridge_run_slot.py::test_r040_lock_path_from_home
0.20s call     tests/test_bridge_run_slot.py::test_r040_creation_time_unreadable_skips_record
0.13s call     tests/test_bridge_run_slot.py::test_r040_lock_folder_refused
0.10s call     tests/test_bridge_run_slot.py::test_r040_invalid_slot_scale_refused_first[-1]
0.09s call     tests/test_bridge_run_slot.py::test_r040_watch_refuses_non_gh_command
0.09s call     tests/test_bridge_run_slot.py::test_r040_invalid_slot_scale_refused_first[0]
0.09s call     tests/test_bridge_run_slot.py::test_r040_invalid_slot_scale_refused_first[2]
0.09s call     tests/test_bridge_run_slot.py::test_r040_invalid_slot_scale_refused_first[abc]
0.09s call     tests/test_bridge_run_slot.py::test_r040_invalid_slot_scale_refused_first[nan]
0.01s setup    tests/test_bridge_run_slot.py::test_r040_invalid_slot_scale_refused_first[abc]
0.01s setup    tests/test_bridge_run_slot.py::test_r040_untrusted_records_by_launch[{"kind": "test", "run_id": "2026-01-01T00:00:00Z", "start": "2026-01-01T00:00:00Z", "pid": __PID__, "created": __CREATED__, "limit": 1e400}]
0.01s call     tests/test_bridge_run_slot.py::test_r040_grace_end_lines_at_scale_one
0.01s call     tests/test_bridge_run_slot.py::test_r040_publication_failure_is_a_note
0.01s call     tests/test_bridge_run_slot.py::test_r040_ebadf_not_held
0.01s setup    tests/test_bridge_run_slot.py::test_r040_no_tasklist_in_launcher
```

All listed call durations for `tests/test_bridge_run_slot.py` are under ten seconds.

### Windowless check

```
$ python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge/bridge-run.py
windowless-check: 1 file(s) scanned, 0 FAIL, 0 NOTE
```

### `git diff -- bridge/cursor-bridge/bridge-run.py`

Reviewed in full: changes match Requirements 1–6 only (constant, `process_alive`, `read_holder_record`, removal of `run_id_epoch`, `publish_holder_record`, `_open_heavy_lock`, `main` review refusal). Module docstring lines 1–88 unchanged.

### `git status --porcelain`

```
 M bridge/cursor-bridge/bridge-run.py
```

### Leftover processes (Windows)

```
$ tasklist //FI "IMAGENAME eq python.exe"

Image Name                     PID Session Name        Session#    Mem Usage
========================= ======== ================ =========== ============
python.exe                   14400 Console                    1  2.427.796 K
python.exe                   25352 Console                    1     23.716 K
```

These processes were not started by this verification run; the pytest suite completed with exit code 0 and the slot tests use `kill_tree` in `finally` blocks. No test-spawned waiter or holder was left running after the suite.

## Assumed, not verified

- A single `os.read(fd, 4097)` on a regular file returns all bytes present when the file is smaller than 4,097 bytes · the brief caps size at 4,096 and the tests use small records · a POSIX read loop test on a padded file.
- `O_NONBLOCK` on a regular-file descriptor does not change whether one `os.read` returns the available bytes on Windows · the brief lists `O_BINARY` for the record open on Windows · read a well-formed record through the new path on Windows only.
- After five failed `os.replace` attempts, the temp path from `mkstemp` still exists and `os.remove(tmp)` is the right cleanup · prior code did the same on failure · simulate `PermissionError` on every replace and list the holder folder.
