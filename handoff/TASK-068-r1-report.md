# TASK-068 round 1 report

## Files changed

- `bridge/cursor-bridge/in-flight.py` (new)
- `bridge/cursor-bridge/bridge_env.py`
- `bridge/cursor-bridge/bridge-run.py`
- `bridge/cursor-bridge/pace-report.py`
- `bridge/cursor-bridge/loop-guard.py`
- `bridge/cursor-bridge/settings.bridge.json`
- `bridge/cursor-bridge/MANIFEST.json` (regenerated)
- `docs/cli-reference.json` (regenerated)
- `docs/CLI_REFERENCE.md` (regenerated)
- `tests/test_dump_cli.py`
- `tests/test_allowlist.py`
- `tests/test_loop_guard.py`
- `docs/BUILDER_NOTES.md`
- `handoff/TASK-068-r1-report.md`

`tests/test_bridge_run.py` and `tests/test_pace_report.py` were not edited.

## Summary

`in-flight.py` appends one clock-stamped line to the Workspace log `run/supervisor/in-flight.md`, taking the text from one argument, from a file under `run/supervisor/`, or from a tagged review pass, and it refuses every other case before it creates a folder or writes a line. The seven round causes stand once as `bridge_env.ROUND_CAUSES`, which the launcher reads as itself and the pace report reads with `unstated` appended. The loop guard's refusal for a background agent with no timer now names that log and `python ~/.claude/cursor-bridge/in-flight.py`, the allow list admits the program, and the command reference and MANIFEST were regenerated.

## Requirements

- R1. `build_parser` (lines 350-360) and `main` (lines 363-377) expose `<text>`, `--file`, and `--pass NAME REVIEWER` with optional `--round` and `--cause`. `prepare` (lines 248-255) accepts exactly one source and refuses `--round` or `--cause` without `--pass`. `FlightParser.error` (lines 40-43) turns argparse usage errors into exit 2. The description and help name no path and no user name.
- R2. `bridge_env.workspace_of` (lines 4414-4432) walks from the start folder to the nearest parent that holds `docs/PROJECT_STATUS.md` as a file and returns that folder's absolute path, or `None`. `prepare` (line 260) calls it with the current folder. The log is `<Workspace>/run/supervisor/in-flight.md`. `append_log` (line 329) creates the folder only after `prepare` has accepted the run.
- R3. `stamp` (lines 56-57) formats `datetime.now(timezone.utc)` as `%Y-%m-%dT%H:%MZ`, 17 characters, then one space and the text.
- R4. `_strip_spaces` (lines 60-67) drops leading and trailing space separators. `_file_lines` (lines 78-98) splits a `--file` body on CR LF, LF, and CR; `_text_and_pauses` (lines 111-124) drops blank lines and joins the rest with one space. `_read_source` (lines 178-224) reads at most 65,536 bytes as UTF-8 and drops a leading byte-order mark. `_through_link` (lines 151-175) refuses a symbolic link or junction on the file or on a folder between `run/supervisor/` and the file. `_at_or_under` (lines 131-137) compares `os.path.normcase` paths, and the resolved path must sit inside the resolved `run/supervisor/` folder and must not be the log. `_forbidden` (lines 74-75) refuses an empty text and any character of category Cc, Cf, Zl, or Zp.
- R5. `prepare` (lines 263-279) builds `<stamp> <text>`, and `_paused_body` (lines 101-108) repeats each line that begins with `Paused:` in any letter case, after the stamped line, with its leading spaces removed. `_pass_text` (lines 227-243) builds `PASS <name> r<n> <reviewer> <cause>`, omitting ` r<n>` and ` <cause>` when those options are absent. The name must match `bridge_env.GRAMMAR_ID_PATTERN` whole, the reviewer is one of the seven kinds in `REVIEWERS` (lines 26-34), the round is an `int` from 1 to 999, and the cause must be a member of `bridge_env.ROUND_CAUSES`. `append_log` (line 324) ends each line with LF and writes UTF-8.
- R6. `append_log` (lines 322-347) writes every line of the run in one `os.write` after `_acquire` (lines 288-306) holds the first byte of the log. If the file is not empty and its last byte is not LF, that block starts with LF. On Windows the C runtime append is a seek to the end plus a write, so it is not one operation across processes; this program seeks to offset 0 and takes `msvcrt.locking` on that byte for the whole read-and-write, and another run waits there instead of writing into the same line. The wait stops at `LOCK_SECONDS` (line 36), 10 seconds, and then the run exits 2 with nothing appended.
- R7. `refuse` (lines 51-53) prints one stderr line, `in-flight: REFUSED - <reason>`, and returns 2. `prepare` finishes every check before `append_log` creates the folder or opens the log, and a missing Workspace creates no `run/` folder. Reasons name the fault and include no path and no traceback. `main` (lines 374-377) turns any other exception into that same line.
- R8. On success `main` (lines 371-372) calls `say` (lines 46-48), which writes each whole line to stdout as UTF-8 bytes, and returns 0.
- R9. `bridge_env.ROUND_CAUSES` (lines 4403-4411) is the seven causes in the required order, without `unstated`. `bridge-run.py` line 990 sets the module name `ROUND_CAUSES` to `bridge_env.ROUND_CAUSES`, and `round_cause` is unchanged. `pace-report.py` line 431 sets its `ROUND_CAUSES` to `bridge_env.ROUND_CAUSES + ("unstated",)`. `_pass_text` (line 235) reads `bridge_env.ROUND_CAUSES` and the program holds no copy of the list.
- R10. `loop-guard.py` line 638 keeps the opening `Loop guard (Claude-Cursor Bridge, rule 43): you are waiting on a background agent with no timer running to its ceiling:` and now tells the supervisor to append the position to `run/supervisor/in-flight.md` with `python ~/.claude/cursor-bridge/in-flight.py`. The rest of the refusal, the exit code, and the decision are unchanged, and the source no longer holds the status file's `In flight:` line. `test_r088_the_refusal_names_the_in_flight_log_and_the_program` (`tests/test_loop_guard.py` line 283) drives `lg.main()` into that refusal and checks the opening words and both names.
- R11. `settings.bridge.json` line 74 is `Bash(python ~/.claude/cursor-bridge/in-flight.py:*)`, directly after the push-scan entry. `test_r088_in_flight_rule_in_allow` (`tests/test_allowlist.py` line 266) asserts that rule is in `ALLOW` and that `decide` allows the four commands from the brief.
- R12. `tests/test_dump_cli.py` line 34 adds `"in-flight.py"` to `ARGPARSE`. `python tools/dump-cli.py` regenerated the command reference, and `python tools/dump-cli.py --check` exited 0. `python tools/make-manifest.py` regenerated MANIFEST, and `git restore bridge/cursor-bridge/VERSION` put `2026.11.12a` back. Command 12 does not list `bridge/cursor-bridge/VERSION`.
- R13. `in-flight.py` is ASCII, imports only the standard library and `bridge_env` (lines 14-24), starts no process, and makes no network call. Importing it only adjusts `sys.path` and loads `bridge_env`.

## Mutation self-check

Each mutant was applied, `python -m pytest -p no:cacheprovider -q tests/test_program_in_flight.py` was run (for M12, `tests/test_loop_guard.py`), and the file was restored. `test_r088_a_file_reached_through_a_link_is_refused` was not exercised: this account cannot create a symbolic link, and the run skipped it.

- M1 the stamp written in local time instead of UTC. Caught by `test_r088_a_text_is_appended_with_the_clock_s_time_and_printed`.
- M2 the stamp written to the second. Caught by `test_r088_a_text_is_appended_with_the_clock_s_time_and_printed`.
- M3 the log opened for writing instead of appending (`O_WRONLY | O_CREAT | O_TRUNC` in place of `O_RDWR | O_CREAT | O_APPEND`). Caught by `test_r088_a_second_run_appends_and_never_rewrites`.
- M4 the Workspace taken to be the current folder, with no walk to its parents. Caught by `test_r088_the_workspace_is_found_from_a_folder_inside_it`.
- M5 a `Paused:` line of the file joined into the stamped line only. Caught by `test_r088_a_paused_line_in_the_file_stays_a_line_the_loop_guard_reads`.
- M6 a `--file` path accepted without resolving `..` (the path was accepted when the unresolved text contained `run/supervisor`). Caught by `test_r088_a_file_outside_run_supervisor_is_refused`.
- M7 a `--file` path outside `run/supervisor/` but inside the Workspace accepted (the containment parent was the Workspace). Caught by `test_r088_a_file_outside_run_supervisor_is_refused`.
- M8 a text holding an escape character accepted. Caught by `test_r088_no_text_both_sources_or_a_control_character_is_refused[control-character]`.
- M9 a reviewer outside the list accepted. Caught by `test_r088_a_word_outside_the_lists_is_refused_and_nothing_written[unknown-reviewer]`.
- M10 `--cause` accepted outside `bridge_env.ROUND_CAUSES`. Caught by `test_r088_a_word_outside_the_lists_is_refused_and_nothing_written[unknown-cause]`.
- M11 the log's folder created before the checks run. Caught by `test_r088_outside_a_workspace_it_refuses_and_writes_nothing`.
- M12 the loop guard's refusal's first words changed (`you are waiting` to `you were waiting`). Caught by `test_r088_the_refusal_names_the_in_flight_log_and_the_program`.

## Commands

The counts below belong to commit `11469ea79c58bb3a2c43bb31680fd34501ece55c`. The working tree then held uncommitted changes. `bridge/cursor-bridge/VERSION` was not listed.

### 1. `git status --short`

```
 M bridge/cursor-bridge/bridge-run.py
 M bridge/cursor-bridge/bridge_env.py
 M bridge/cursor-bridge/loop-guard.py
 M bridge/cursor-bridge/pace-report.py
 M bridge/cursor-bridge/settings.bridge.json
 M docs/BUILDER_NOTES.md
 M tests/test_allowlist.py
 M tests/test_dump_cli.py
 M tests/test_loop_guard.py
?? bridge/cursor-bridge/in-flight.py
?? handoff/TASK-068-r1-report.md
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
.......................................................................s [ 30%]
...ss.....sss....................s...............s...................... [ 46%]
.........................s..........s.................s...ss.....sss.... [ 61%]
................s...............s....................................... [ 77%]
........s..........s.................................................... [ 92%]
...................................                                      [100%]
=========================== short test summary info ===========================
SKIPPED [1] tests\test_program_in_flight.py:230: this account cannot create a symbolic link
SKIPPED [10] tests\test_allowlist.py:65: prose, not a runnable command
SKIPPED [10] tests\test_allowlist.py:106: prose, not a runnable command
446 passed, 21 skipped in 122.60s (0:02:02)
```

`test_r088_a_file_reached_through_a_link_is_refused` was not exercised. The skip reason is the first SKIPPED line above.

### 7. `python -m pytest -p no:cacheprovider -q tests/test_bridge_run.py tests/test_pace_report.py tests/test_release_s_launcher.py`

```
........................................................................ [ 73%]
..........................                                               [100%]
98 passed in 56.11s
```

### 8. `python -m pytest -p no:cacheprovider -q tests/test_install_check.py tests/test_tests_windowless.py`

```
.........................                                                [100%]
25 passed in 22.04s
```

### 9. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`

```
bridge-check: version 2026.11.12a (2026-11-21 00:23) at <Workspace>\bridge
bridge-check: 148 OK, 0 STALE, 0 MISSING, 0 EXTRA
RESULT: SOURCES MATCH bridge 2026.11.12a
```

### 10. `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks`

```
windowless-check: 41 file(s) scanned, 0 FAIL, 0 NOTE
```

### 11. `python -c "open('bridge/cursor-bridge/in-flight.py','rb').read().decode('ascii'); print('ascii ok')"`

```
ascii ok
```

### 12. `git rev-parse HEAD` and `git status --short`

```
11469ea79c58bb3a2c43bb31680fd34501ece55c
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/bridge-run.py
 M bridge/cursor-bridge/bridge_env.py
 M bridge/cursor-bridge/loop-guard.py
 M bridge/cursor-bridge/pace-report.py
 M bridge/cursor-bridge/settings.bridge.json
 M docs/BUILDER_NOTES.md
 M docs/CLI_REFERENCE.md
 M docs/cli-reference.json
 M tests/test_allowlist.py
 M tests/test_dump_cli.py
 M tests/test_loop_guard.py
?? bridge/cursor-bridge/in-flight.py
?? handoff/TASK-068-r1-report.md
```

## Assumed, not verified

- The offset-0 byte lock plus one write keeps one run's lines whole against another in-flight process on Windows beyond the eight runs the test starts, and on Linux, which this run did not execute. · Windows append is a seek plus a write, and the lock only excludes another process that locks the same byte. · A Linux run of `tests/test_program_in_flight.py`, and a second writer that does not take the lock.
- A junction under `run/supervisor/` is refused, and so is a symbolic link whose target stays inside that folder. · `_reparse` treats `os.path.isjunction` and `os.path.islink` as a link, and `test_r088_a_file_reached_through_a_link_is_refused` was skipped on this account. · That test on an account that can create a symbolic link, and the same layout with a junction.
- When the log is not empty and its last byte is not LF, the next append starts with LF. · `append_log` reads that byte under the lock, and no acceptance test builds a log without a trailing line break. · A log ending in a letter, then one run, with the new stamp on its own line.
- A line of only Unicode space separators is blank and is dropped, and the spaces removed from either end of the text are category Zs. · The brief says blank lines are dropped and spaces are removed, and the tests use ordinary spaces only. · A `--file` body with a middle line of spaces, and one with a leading no-break space.
- If the lock is not acquired within 10 seconds, the run exits 2 and appends nothing, but a log file this run created so it could lock it can remain empty. · The file has to exist before the lock, and deleting it could remove another run's file; no test holds the lock for 10 seconds. · One process holding the lock past 10 seconds, and a second run that exits 2 with its text absent.
