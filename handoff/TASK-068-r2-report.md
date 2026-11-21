# TASK-068 round 2 report

## Files changed

- `bridge/cursor-bridge/in-flight.py`
- `bridge/cursor-bridge/loop-guard.py`
- `bridge/cursor-bridge/bridge_env.py`
- `bridge/cursor-bridge/MANIFEST.json` (regenerated)
- `tests/test_loop_guard.py`
- `docs/BUILDER_NOTES.md`
- `handoff/TASK-068-r2-report.md`

`python tools/dump-cli.py` printed nothing and `python tools/dump-cli.py --check` exited 0, so `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` are unchanged. `tests/test_program_in_flight.py` was not edited.

## Summary

The in-flight log is appended in binary mode, and the run writes every byte of that payload or exits 1 with `in-flight: INCOMPLETE` and prints no line. The loop guard takes the last `Paused:` line, so a later `Paused: resumed` lifts a pause and a later pause sets it again. An empty `--file` counts as a source, a text whose first word is `PASS` is refused unless it comes from `--pass`, and the program refuses before it creates or opens the log when `run/`, `run/supervisor/` or the log is a link or the real supervisor folder leaves the Workspace. A `--file` is opened at the real path already checked, the Windows lock is the byte at `2 ** 31`, and `bridge_env.py` ends with one line break.

## Corrections

1. `append_log` (line 396) opens the log with `O_RDWR | O_CREAT | O_APPEND` and `getattr(os, "O_BINARY", 0)`, so the bytes written are the payload and every line ends with LF.
2. `last_field` (lines 201-209) returns the last match of `field`'s pattern, and `paused_in_flight` (lines 283-300) uses it for `Paused`; `test_r088_the_last_paused_line_decides` (`tests/test_loop_guard.py` lines 478-488) reads a pause followed by `Paused: resumed` as no wait, and a resume followed by a pause as that pause.
3. `prepare` (line 274) counts a source with `args.file is not None`, so `--file ""` beside a text is two sources, and line 279 refuses `--file ""` alone as no text.
4. `_first_word_is_pass` (lines 107-109) is true only when the first word is `pass` in any letter case, and `prepare` (lines 298-304) refuses that word on the first line of a `--file` text and on the text that would be written, exit 2, the reason naming `--pass`.
5. `_log_blocked` (lines 352-367) runs in `append_log` (lines 387-389) before the folder is created or the log opened, and it refuses when `_reparse` (lines 151-163) finds a link at `run/`, `run/supervisor/` or the log, or when the real path of `run/supervisor/` is not under the real Workspace.
6. `_read_source` opens `file_real` (line 219) with `O_BINARY` where the platform has it (lines 214-215) and `O_NOFOLLOW` where it has it (lines 216-217), then requires `os.fstat` and `os.stat` of that path to agree on `st_dev` and `st_ino` where both are non-zero and requires `st_nlink == 1` (lines 223-230).
7. `_acquire` (lines 324-325) and `_release` (lines 343-344) seek to `2 ** 31` before `msvcrt.locking` on Windows, and on POSIX they keep `fcntl.flock`; the wait is still `LOCK_SECONDS`, 10 seconds.
8. `_write_all` (lines 370-383) repeats `os.write` until every byte is written, and a write of zero bytes or an `OSError` returns the counts; `main` (lines 438-439) then calls `incomplete` (lines 57-59), which exits 1 with `in-flight: INCOMPLETE - <n> of <m> bytes written` and does not print the line. `_reparse` calls `os.path.isjunction` when that function exists, and otherwise uses `st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT` (lines 156-161).
9. `bridge_env.py` ends at `workspace_of`'s `return None` (line 4432) with one line break.

## Mutation self-check

Each mutant was applied to the finished source, the pytest command below was run, and the file was restored. H1, H3, H4 and H5 ran `python -m pytest -p no:cacheprovider -q --tb=no tests/test_program_in_flight.py`. H2 ran that file and `tests/test_loop_guard.py`. `test_r088_a_file_reached_through_a_link_is_refused` was skipped on this account, as in the acceptance run.

- H1 `O_BINARY` dropped from `append_log`'s flags. Caught by `test_r088_r2_every_line_the_program_writes_ends_with_lf_alone`.

```
FAILED tests/test_program_in_flight.py::test_r088_r2_every_line_the_program_writes_ends_with_lf_alone
1 failed, 43 passed, 1 skipped in 6.04s
```

- H2 `paused_in_flight` read the first `Paused:` line again (`field` in place of `last_field`). Caught by `test_r088_r2_a_later_paused_line_lifts_or_replaces_an_earlier_one` and `test_r088_the_last_paused_line_decides`.

```
FAILED tests/test_program_in_flight.py::test_r088_r2_a_later_paused_line_lifts_or_replaces_an_earlier_one
FAILED tests/test_loop_guard.py::test_r088_the_last_paused_line_decides - ass...
2 failed, 112 passed, 1 skipped in 6.65s
```

- H3 `bool(args.file)` restored in the source count. Caught by `test_r088_r2_an_empty_file_option_beside_a_text_is_two_sources`.

```
FAILED tests/test_program_in_flight.py::test_r088_r2_an_empty_file_option_beside_a_text_is_two_sources
1 failed, 43 passed, 1 skipped in 5.70s
```

- H4 the `PASS` refusal dropped (`_first_word_is_pass` returned false). Caught by `test_r088_r2_a_free_text_cannot_forge_a_pass_line`.

```
FAILED tests/test_program_in_flight.py::test_r088_r2_a_free_text_cannot_forge_a_pass_line[PASS TASK-1 r9 review-a defect]
FAILED tests/test_program_in_flight.py::test_r088_r2_a_free_text_cannot_forge_a_pass_line[pass PR-3 r1 review-b records]
FAILED tests/test_program_in_flight.py::test_r088_r2_a_free_text_cannot_forge_a_pass_line[Pass X]
3 failed, 41 passed, 1 skipped in 5.51s
```

- H5 the link test of `run/supervisor/` dropped. Removing `supervisor` from the reparse loop alone left the acceptance file green (`44 passed, 1 skipped in 5.72s`), because the real-path confinement still refuses a junction that leaves the Workspace. Dropping that confinement as well, so nothing tests `run/supervisor/`, was caught by `test_r088_r2_a_log_folder_that_is_a_link_is_refused[supervisor]`.

```
FAILED tests/test_program_in_flight.py::test_r088_r2_a_log_folder_that_is_a_link_is_refused[supervisor]
1 failed, 43 passed, 1 skipped in 5.69s
```

## Commands

The outputs below are the last run, after the source edits above. A repository path printed by a command is written `<Workspace>`. `bridge/cursor-bridge/VERSION` is not listed.

### 1. `git status --short`

```
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/bridge_env.py
 M bridge/cursor-bridge/in-flight.py
 M bridge/cursor-bridge/loop-guard.py
 M docs/BUILDER_NOTES.md
 M tests/test_loop_guard.py
?? handoff/TASK-068-r2-report.md
```

### 2. `python tools/dump-cli.py`

The command printed no lines and exited 0.

### 3. `python tools/dump-cli.py --check`

The command printed no lines and exited 0.

### 4. `python tools/make-manifest.py`

```
make-manifest: version 2026.11.12a, 148 files hashed, VERSION + MANIFEST.json written
```

### 5. `git restore bridge/cursor-bridge/VERSION`

The command printed no lines and exited 0.

### 6. `python -m pytest -p no:cacheprovider -q -rs tests/test_program_in_flight.py tests/test_dump_cli.py tests/test_allowlist.py tests/test_loop_guard.py`

```
.............................s.......................................... [ 15%]
........................................................................ [ 30%]
.......s...ss.....sss....................s...............s.............. [ 45%]
.................................s..........s.................s...ss.... [ 60%]
.sss....................s...............s............................... [ 75%]
................s..........s............................................ [ 90%]
............................................                             [100%]
=========================== short test summary info ===========================
SKIPPED [1] tests\test_program_in_flight.py:230: this account cannot create a symbolic link
SKIPPED [10] tests\test_allowlist.py:65: prose, not a runnable command
SKIPPED [10] tests\test_allowlist.py:106: prose, not a runnable command
455 passed, 21 skipped in 129.10s (0:02:09)
```

`test_r088_a_file_reached_through_a_link_is_refused` was not exercised. The skip reason is the first SKIPPED line above.

### 7. `python -m pytest -p no:cacheprovider -q tests/test_bridge_run.py tests/test_pace_report.py tests/test_release_s_launcher.py`

```
........................................................................ [ 73%]
..........................                                               [100%]
98 passed in 56.93s
```

### 8. `python -m pytest -p no:cacheprovider -q tests/test_install_check.py tests/test_tests_windowless.py`

```
.........................                                                [100%]
25 passed in 21.46s
```

### 9. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`

```
bridge-check: version 2026.11.12a (2026-11-21 01:51) at <Workspace>\bridge
bridge-check: 148 OK, 0 STALE, 0 MISSING, 0 EXTRA
RESULT: SOURCES MATCH bridge 2026.11.12a
```

### 10. `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks`

```
windowless-check: 41 file(s) scanned, 0 FAIL, 0 NOTE
```

### 11. `python -c "open('bridge/cursor-bridge/in-flight.py','rb').read().decode('ascii'); open('bridge/cursor-bridge/loop-guard.py','rb').read().decode('ascii'); print('ascii ok')"`

```
ascii ok
```

### 12. `git rev-parse HEAD` and `git status --short`

```
5df881c38ae0d02e2324783bc874071eca40c575
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/bridge_env.py
 M bridge/cursor-bridge/in-flight.py
 M bridge/cursor-bridge/loop-guard.py
 M docs/BUILDER_NOTES.md
 M tests/test_loop_guard.py
?? handoff/TASK-068-r2-report.md
```

## Assumed, not verified

- On Linux the append flag `O_BINARY` is absent, the `--file` open adds `O_NOFOLLOW`, and the lock is `fcntl.flock` on the whole file. · The branches are the POSIX arms of `_acquire`, `_release` and `_read_source`, and this run was Windows. · A Linux run of `tests/test_program_in_flight.py`.
- A short or failed `os.write` exits 1 with `in-flight: INCOMPLETE - <n> of <m> bytes written` and prints no line. · `_write_all` returns the counts and `main` calls `incomplete` before `say`, and no acceptance test makes `os.write` return 0 or raise. · A run whose write returns 0 after some bytes, with the log holding only that prefix and stdout empty.
- Python before 3.12 takes `_reparse`'s `lstat` branch. · `getattr(os.path, "isjunction", None)` is how the missing attribute is avoided, and this interpreter is 3.12.10, which has `os.path.isjunction`. · The junction case of `test_r088_r2_a_log_folder_that_is_a_link_is_refused` on Python 3.11.
- A reader can read the log while a run holds the byte at `2 ** 31`, and a second run that cannot take that byte exits 2 after 10 seconds with nothing appended. · The lock range is one byte at that position and `LOCK_SECONDS` is unchanged, and no test holds the lock or reads during it. · One process locking that byte, a concurrent read of the log, and a second `in-flight.py` that waits out the 10 seconds.
