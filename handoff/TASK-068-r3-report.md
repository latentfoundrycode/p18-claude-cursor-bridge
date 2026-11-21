# TASK-068 round 3 report

## Files changed

- `bridge/cursor-bridge/in-flight.py`
- `bridge/cursor-bridge/loop-guard.py`
- `bridge/cursor-bridge/MANIFEST.json` (regenerated)
- `tests/test_loop_guard.py`
- `docs/BUILDER_NOTES.md`
- `handoff/TASK-068-r3-report.md`

`tests/test_program_in_flight.py` was not edited. `field` in `loop-guard.py` was not edited.

## Summary

An empty `Paused:` line is read as empty, because `last_field` no longer lets the white space after the colon cross a line break, so a later ordinary line is not a pause and `Paused: resumed` after an empty pause is no wait. The log is opened with `O_NOFOLLOW` where the platform has it, and before any byte is written the open file must have one link and the folder checks run again, so a hard link to a file outside the Workspace is refused and left unchanged. A `--file` is compared with `os.lstat` taken before the open, not with `os.stat` after it. The notes record that the Windows lock sits on the byte at `2**31`.

## Corrections

1. `last_field` (lines 201-209) keeps `field`'s pattern except the white space after the colon and around the value, which is `[ \t]*` (line 203), so `Paused:` alone yields `""` and the next line is a separate line. `field` (lines 191-198) is unchanged. `test_r088_an_empty_paused_line_reads_as_no_wait` (`tests/test_loop_guard.py` lines 491-499) reads a log `Paused: x` / `Paused:` / `2026-11-21T02:43Z text` as no wait.
2. `append_log` (lines 388-427) adds `O_NOFOLLOW` where the platform has it (lines 400-401) beside `O_RDWR | O_CREAT | O_APPEND` and `O_BINARY`. After the open and before `_write_all` (line 417), `os.fstat` of the open log must show `st_nlink == 1` (lines 411-413) and `_log_blocked` runs again (lines 414-416). Either failure returns a reason, and `main` ends the run with exit 2, `in-flight: REFUSED - <reason>`, and nothing appended.
3. `_read_source` (lines 193-249) takes `os.lstat` of the checked real path during the checks, before the open (lines 213-216), and compares `os.fstat` of the opened file with that result on `st_dev` and `st_ino` where both are non-zero (lines 227-231), in place of round 2's `os.stat` after the open.
4. `docs/BUILDER_NOTES.md` line 104 says that, since round 2, the Windows lock sits on the byte at `2**31`, not byte 0 as round 1's line says.

## Commands

The outputs below are the last run, after the source edits above. A repository path printed by a command is written `<Workspace>`. `bridge/cursor-bridge/VERSION` is not listed.

### 1. `git status --short`

```
 M bridge/cursor-bridge/in-flight.py
 M bridge/cursor-bridge/loop-guard.py
 M docs/BUILDER_NOTES.md
 M tests/test_loop_guard.py
?? handoff/TASK-068-r3-report.md
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
..........s...ss.....sss....................s...............s........... [ 45%]
....................................s..........s.................s...ss. [ 60%]
....sss....................s...............s............................ [ 75%]
...................s..........s......................................... [ 90%]
................................................                         [100%]
=========================== short test summary info ===========================
SKIPPED [1] tests\test_program_in_flight.py:230: this account cannot create a symbolic link
SKIPPED [10] tests\test_allowlist.py:65: prose, not a runnable command
SKIPPED [10] tests\test_allowlist.py:106: prose, not a runnable command
459 passed, 21 skipped in 127.65s (0:02:07)
```

`test_r088_a_file_reached_through_a_link_is_refused` was not exercised. The skip reason is the first SKIPPED line above.

### 7. `python -m pytest -p no:cacheprovider -q tests/test_bridge_run.py tests/test_pace_report.py tests/test_release_s_launcher.py`

```
........................................................................ [ 73%]
..........................                                               [100%]
98 passed in 56.18s
```

### 8. `python -m pytest -p no:cacheprovider -q tests/test_install_check.py tests/test_tests_windowless.py`

```
.........................                                                [100%]
25 passed in 21.18s
```

### 9. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`

```
bridge-check: version 2026.11.12a (2026-11-21 02:51) at <Workspace>\bridge
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
32db4290f39736d074bb4ec8f0e845e1e2043ecc
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/in-flight.py
 M bridge/cursor-bridge/loop-guard.py
 M docs/BUILDER_NOTES.md
 M tests/test_loop_guard.py
?? handoff/TASK-068-r3-report.md
```

## Mutation self-check

Each mutant was applied to the finished source, the pytest command below was run, and the file was restored.

- H1 `last_field`'s `\s*` restored (the white space after the colon and around the value). Caught by `test_r088_r3_an_empty_paused_line_never_takes_the_next_line_as_its_value` and `test_r088_an_empty_paused_line_reads_as_no_wait`.

```
FAILED tests/test_program_in_flight.py::test_r088_r3_an_empty_paused_line_never_takes_the_next_line_as_its_value
FAILED tests/test_loop_guard.py::test_r088_an_empty_paused_line_reads_as_no_wait
2 failed, 1 passed in 0.54s
```

- H2 the log's `st_nlink` check dropped. Caught by `test_r088_r3_a_log_that_is_a_hard_link_is_refused`. The supervisor-folder link case still passed.

```
FAILED tests/test_program_in_flight.py::test_r088_r3_a_log_that_is_a_hard_link_is_refused
1 failed, 1 passed in 0.77s
```

- H3 the `--file` comparison made against `os.stat` after the open again (`os.lstat` before the open removed). No test failed. The symbolic-link case was skipped, so this mutant was not distinguished from the finished source. Failing pytest line: `not run`.

```
47 passed, 1 skipped in 6.12s
```

## Assumed, not verified

- On Linux the log open adds `O_NOFOLLOW` and a symlink at the log path fails the open. · This run was Windows, where `os.O_NOFOLLOW` is present and a normal create still succeeded. · A Linux run of `tests/test_program_in_flight.py` with the log path a symbolic link.
- `os.lstat` before the open disagrees with `os.fstat` when the path is replaced by a link between the check and the open. · H3 left the acceptance file green, and `test_r088_a_file_reached_through_a_link_is_refused` was skipped on this account. · That case on an account that can create a symbolic link, and a file swapped for a link after `os.lstat`.
- The second `_log_blocked` after the open refuses a `run/supervisor/` link that appears during the lock wait. · The acceptance case plants the link before the run, so the first `_log_blocked` already refuses it. · A link created after the first check and before the write.
