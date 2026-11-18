# TASK-067 round 3 report

## Files changed

- `bridge/cursor-bridge/push-scan.py` (G1-G7 only: the `git` argv, both `git show` calls in `scan_commit`, the placement line, `quote_path`'s category set, and the removal of `take_token`)
- `bridge/cursor-bridge/MANIFEST.json` (rewritten by `python tools/make-manifest.py` in Done step 4; the diff changes `generated` and the `push-scan.py` hash)
- `handoff/TASK-067-r3-report.md` (this file, written after Done step 13)

`docs/cli-reference.json` and `docs/CLI_REFERENCE.md` were not edited: the parser text did not change, and `python tools/dump-cli.py` printed nothing. `docs/BUILDER_NOTES.md` was not edited. `bridge/cursor-bridge/VERSION` was restored with `git restore` and is not in the step 13 status. `bridge/cursor-bridge/settings.bridge.json` was not edited.

## Summary

The pre-push scan now forces `log.showRoot=true` and `diff.suppressBlankEmpty=false` on every git call, and both `git show` reads pass `--ignore-submodules=none` and `--submodule=short`, so a root commit, a submodule entry, and a blank context line are read whatever the user's settings or the commit's `.gitmodules` say. A file's lines are placed by position when either the real path or the text `quote_path` would print holds a hit, format characters are quoted as octal UTF-8 bytes, and the unused `take_token` function is gone.

## G1-G7

- G1: `git` (line 51) passes `-c log.showRoot=true` beside `-c log.showSignature=false`, so every git call carries it and a root commit's file list and patch are read.
- G2: both `git show` calls in `scan_commit` (lines 630 and 639) pass `--ignore-submodules=none`, written out in each argument list.
- G3: those same two lines pass `--submodule=short`, written out in each argument list.
- G4: `git` (line 51) passes `-c diff.suppressBlankEmpty=false` beside the other `-c` pairs. `added_lines` is unchanged.
- G5: `scan_commit` (line 659) sets `hidden` from `kinds_of` on the real path or on `quote_path` of that path. The file-name hit (lines 660-662) still uses `kinds_of` on the real path only.
- G6: `quote_path` (lines 598 and 611) uses the category set `Cc`, `Cf`, `Zl`, `Zp` in both the quoting test and the escaping branch, and lines 612-613 escape any other such character as three-digit octal of each UTF-8 byte.
- G7: `take_token` is removed. `unquote_git` ends at line 363 and `strip_side` begins at line 366. The disagreement check (lines 670-672) is unchanged.

## Mutation self-check

Each of P1-P6, N5, N6, N9, and M10 was applied to `push-scan.py`, then `python -m pytest -p no:cacheprovider -q --tb=no tests/test_program_push_scan.py` was run from `<Workspace>`, and the file was restored to the bytes from before that mutant. A first attempt to remove `--submodule=short` looked for a space after the comma; the source has a newline there, so that attempt did not write the file, and P3 below is the run that did.

- P1 `-c log.showRoot=true` removed from the runner (G1): caught by `test_r087_a_root_commit_in_the_range_is_read_whatever_log_show_root_says`.
- P2 `--ignore-submodules=none` removed from both `git show` calls (G2): caught by `test_r087_a_submodule_hidden_by_the_user_s_setting_is_still_read`. The other FAILED ids were `test_r087_a_submodule_hidden_by_the_commit_s_own_gitmodules_is_still_read` and `test_r087_a_submodule_s_own_diff_is_never_inlined`.
- P3 `--submodule=short` removed from both `git show` calls (G3): caught by `test_r087_a_submodule_s_own_diff_is_never_inlined`.
- P4 `-c diff.suppressBlankEmpty=false` removed from the runner (G4): caught by `test_r087_a_blank_context_line_is_read_whatever_diff_suppress_blank_empty_says`.
- P5 the escaped-text check of G5 removed (placement decided on the real path only): caught by `test_r087_a_path_whose_escaped_form_holds_a_name_is_placed_by_its_position`.
- P6 `Cf` removed from `quote_path`'s set (G6): caught by `test_r087_a_format_character_in_a_printed_path_is_escaped`.
- N5 `log.showSignature` left on (the `-c log.showSignature=false` pair removed from `git`): caught by `test_r087_a_commit_s_signature_is_never_read_into_a_hit`.
- N6 `--no-relative` dropped from both `git show` calls: caught by `test_r087_the_user_s_diff_settings_neither_hide_nor_misplace_a_hit`.
- N9 a printed path not escaped (`quote_path` returns the path unchanged): caught by `test_r087_a_control_character_in_a_printed_path_is_escaped`. The other FAILED ids were `test_r087_a_path_whose_escaped_form_holds_a_name_is_placed_by_its_position` and `test_r087_a_format_character_in_a_printed_path_is_escaped`.
- M10 a file whose own path holds a hit placed by its path (`if False and hidden`): caught by `test_r087_a_line_of_a_file_whose_own_name_holds_a_hit_is_placed_by_the_file_s_position`. The other FAILED ids were `test_r087_a_changed_file_with_a_space_in_its_name_is_read_by_its_whole_name`, `test_r087_a_merge_where_one_side_renamed_a_file_reads_each_file_by_its_own_position`, and `test_r087_a_path_whose_escaped_form_holds_a_name_is_placed_by_its_position`.
- N1 a `+++` line read inside a hunk: code unchanged (`added_lines` is untouched). Not re-run.
- N2 a path cut at its first space: code unchanged (`_path_from_rest` is untouched). Not re-run.
- N3 a combined status read with two paths: code unchanged (`_two_path_status` is untouched). Not re-run.
- N4 the disagreement check removed: code unchanged (`scan_commit` lines 670-672). Expected to survive. Not re-run.
- N7 the lower-cased index match restored: code unchanged (`has_name` is untouched). Not re-run.
- N8 `str.splitlines` restored for the patch: code unchanged (`_patch_lines` is untouched). Not re-run.
- M1 the committer line not read: code unchanged. Not re-run.
- M2 a renamed file's new name not read: code unchanged (`if status[:1] in ("A", "R")` is still that line). Not re-run.
- M3 the committer line exempted for any identity: code unchanged (`carries_identity` is untouched). Not re-run.
- M4 the owner segment of the remote kept as a name: code unchanged (`owner_of` and `public_names` are untouched). Not re-run.
- M5 the matched text printed in the hit line: code unchanged (`hit_line` is untouched). Not re-run.
- M6 a placeholder segment flagged: code unchanged (`has_path` and `_segment_start` are untouched). Not re-run.
- M7 a name matched inside a longer word: code unchanged (`has_name` is untouched). Not re-run.
- M8 a name shorter than four characters searched: code unchanged (`select_names` is untouched). Not re-run.
- M9 the line number counted in the old file: code unchanged (`added_lines` is untouched). Not re-run.
- M11 a base beginning with `-` accepted: code unchanged (`execute` is untouched). Not re-run.
- M12 the configured identity's names not dropped: code unchanged (`public_names` is untouched). Not re-run.
- M13 the configured identity's author and committer lines not exempted: code unchanged (both `if not carries_identity` lines are still those lines). Not re-run.

```
P1: 1 failed, 38 passed in 27.53s
P2: 3 failed, 36 passed in 27.47s
P3: 1 failed, 38 passed in 26.78s
P4: 1 failed, 38 passed in 27.05s
P5: 1 failed, 38 passed in 27.24s
P6: 1 failed, 38 passed in 26.86s
N5: 1 failed, 38 passed in 27.24s
N6: 1 failed, 38 passed in 27.11s
N9: 3 failed, 36 passed in 27.01s
M10: 4 failed, 35 passed in 27.12s
```

Before those mutants, the same pytest command on the edited file printed:

```
.......................................                                  [100%]
39 passed in 27.23s
```

Exit code 0.

## Done commands

Counts below belong to commit `89436e950ad3c18c96a0bb2bff627576f4e93a61`. At step 13 the working tree held uncommitted changes. This report was written after that status, so its path is not in the step 13 status. In the bridge-check line the repository folder is written as `<Workspace>`.

1. `git status --short`

```
 M bridge/cursor-bridge/push-scan.py
```

Exit code 0.

2. `python tools/dump-cli.py`

```
```

No lines printed. Exit code 0.

3. `python tools/dump-cli.py --check`

```
```

No lines printed. Exit code 0.

4. `python tools/make-manifest.py`

```
make-manifest: version 2026.11.12a, 147 files hashed, VERSION + MANIFEST.json written
```

Exit code 0.

5. `git restore bridge/cursor-bridge/VERSION`

```
```

No lines printed. Exit code 0. `bridge/cursor-bridge/VERSION` reads `2026.11.12a`.

6. `python -m pytest -p no:cacheprovider -q -rs --tb=short tests/test_program_push_scan.py tests/test_dump_cli.py tests/test_allowlist.py`

```
........................................................................ [ 18%]
........................................................................ [ 36%]
s...ss.....sss....................s...............s..................... [ 54%]
..........................s...........s.................s...ss.....sss.. [ 72%]
..................s...............s..................................... [ 90%]
..........s...........s.................                                 [100%]
=========================== short test summary info ===========================
SKIPPED [10] tests\test_allowlist.py:65: prose, not a runnable command
SKIPPED [10] tests\test_allowlist.py:106: prose, not a runnable command
380 passed, 20 skipped in 142.93s (0:02:22)
```

Exit code 0.

7. `python -m pytest -p no:cacheprovider -q tests/test_install_check.py tests/test_tests_windowless.py`

```
.........................                                                [100%]
25 passed in 22.01s
```

Exit code 0.

8. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`

```
bridge-check: version 2026.11.12a (2026-11-18 02:39) at <Workspace>/bridge
bridge-check: 147 OK, 0 STALE, 0 MISSING, 0 EXTRA
RESULT: SOURCES MATCH bridge 2026.11.12a
```

Exit code 0.

9. `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks`

```
windowless-check: 40 file(s) scanned, 0 FAIL, 0 NOTE
```

Exit code 0.

10. `git diff --stat HEAD -- bridge/cursor-bridge/settings.bridge.json`

```
```

No lines printed. Exit code 0.

11. `git grep -n -I -E --no-index "[A-Za-z]:[/\\]|/Users/|/home/|AppData" -- bridge/cursor-bridge/push-scan.py`

```
```

No lines printed. Exit code 1.

12. `python -c "open('bridge/cursor-bridge/push-scan.py','rb').read().decode('ascii'); print('ascii ok')"`

```
ascii ok
```

Exit code 0.

13. `git rev-parse HEAD` and `git status --short`

```
89436e950ad3c18c96a0bb2bff627576f4e93a61
```

Exit code 0.

```
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/push-scan.py
```

Exit code 0. `bridge/cursor-bridge/VERSION` is not listed.

## Assumed, not verified

- that `--submodule=short` on the command line overrides a user's `diff.submodule` of `diff` or `log` for both the name-status list and the patch, so a submodule's own files are not inlined under paths outside the commit's file list | the round-3 case only counts the option text in the source, and no case sets `diff.submodule`; the gitlink cases that did run used the default | A commit that changes a gitlink while `diff.submodule` is `diff` or `log`, expecting the gitlink's own name at its file position, no path from inside the submodule, and exit 1 rather than `the patch and the file list disagree`.
