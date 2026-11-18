# TASK-067 round 2 report

## Files changed

- `bridge/cursor-bridge/push-scan.py` (F1-F10 in the functions the brief names, plus the helpers those functions call)
- `bridge/cursor-bridge/MANIFEST.json` (rewritten by `python tools/make-manifest.py` in Done step 4)
- `docs/BUILDER_NOTES.md` (one line for the uncaught N4 gap)
- `handoff/TASK-067-r2-report.md` (this file, written after Done step 13)

`docs/cli-reference.json` and `docs/CLI_REFERENCE.md` were not edited: the parser text did not change, and `python tools/dump-cli.py` printed nothing. `bridge/cursor-bridge/VERSION` was restored with `git restore` and is not in the step 13 status. `bridge/cursor-bridge/settings.bridge.json` was not edited.

## Summary

The pre-push scan now reads each hunk until its new-side count and each old-side count are used, so a body line is never a header, takes every new path as the whole rest of its header line, reads two name-status paths only for a single-parent rename or copy, exits 2 when a patch path is missing from the file list, forces `log.showSignature=false` and checks the short hash from `rev-parse`, pins `--no-relative` and the `a/` and `b/` prefixes, matches a name with one case-insensitive expression, splits the patch on newline only, and quotes a printed path that contains a control, line, or paragraph separator, a double quote, or a backslash.

## F1-F10

- F1: `_parse_hunk_header` (lines 424-475) reads each start and count with `int` (an omitted count is 1, a start may be 0) and raises `the patch cannot be read` when the numbers cannot be read; `added_lines` (lines 478-560) keeps the following lines as body until those counts are used, a line that begins with a backslash uses no count (lines 504-505), and a line that begins with `diff ` (line 493) ends the hunk and does not carry the previous path forward.
- F2: `_path_from_rest` (lines 411-421) drops one trailing tab, undoes git quoting when the rest begins and ends with a double quote, and never cuts at a space; `added_lines` removes the `b/` prefix only on a `+++ ` line (lines 537-544), gives no new path for the null device (lines 539-540), and does not take a path from `diff --git` (lines 493-501).
- F3: `_two_path_status` (lines 563-569) is true only for `R` or `C` followed by one or more digits; `parse_name_status` (line 583) reads a second path only then, so a combined status such as `RM` keeps one path.
- F4: `scan_commit` (lines 688-690) raises `the patch and the file list disagree` when any new path the patch names is absent from the name-status list, and the old loop that skipped those lines is gone.
- F5: `git` (line 51) passes `-c log.showSignature=false` beside `-c color.ui=never` on every call; `scan_commit` (line 641) takes the short hash with `git rev-parse --short` and `_checked_short` (lines 601-612) requires one or more of `0-9a-f` or raises `internal error`.
- F6: both `git show` calls in `scan_commit` (lines 644-658) pass `--no-relative --src-prefix=a/ --dst-prefix=b/` in addition to the round-1 options.
- F7: `has_name` (lines 127-134) compiles `(?<![^\W_])` plus the escaped name plus `(?![^\W_])` with `re.IGNORECASE`, and does not index a lower-cased copy.
- F8: `_patch_lines` (lines 393-399) splits the patch on `\n` only and strips one trailing `\r` from each line; `added_lines` (line 492) uses it and does not call `str.splitlines`.
- F9: `quote_path` (lines 614-637) leaves a path as it is when it holds none of the named characters, and otherwise quotes it with the named single-character escapes and three-digit octal for each UTF-8 byte of any other such character; `scan_commit` (line 677) tests the real path, and the printed `line <path>:<n>` place (line 686) uses the escaped path.
- F10: `main` (lines 765-766) reports `internal error` for an unexpected exception, while `git cannot be started` stays in `git`; `unquote_git` (lines 357-359) raises `the patch cannot be read` for an octal value above 255; the only new reasons are `the patch cannot be read`, `the patch and the file list disagree`, and `internal error`.

## Mutation self-check

Each N and the re-run M mutants was applied to `push-scan.py`, then `python -m pytest -p no:cacheprovider -q --tb=no tests/test_program_push_scan.py` was run from `<Workspace>`, and the edit was reverted. The summary line is the pytest line.

- N1 a `+++` line read inside a hunk (`if in_hunk and not line.startswith("+++ ")`, so that line is parsed as a header): caught by `test_r087_an_added_line_that_reads_like_a_file_header_is_scanned_in_its_hunk`.
- N2 a path cut at its first space (an unquoted rest in `_path_from_rest` kept only up to the first space): caught by `test_r087_a_changed_file_with_a_space_in_its_name_is_read_by_its_whole_name`.
- N3 a combined status read with two paths (`_two_path_status` true for any status beginning with `R` or `C`): caught by `test_r087_a_merge_where_one_side_renamed_a_file_reads_each_file_by_its_own_position`.
- N4 an unlisted patch path skipped (the disagreement loop removed, so a patch path missing from the file list is not a failure): not caught. The case that would catch it is a commit whose patch names a path the name-status list does not contain, expecting exit 2, the reason `the patch and the file list disagree`, and no OK line.
- N5 `log.showSignature` left on (the `-c log.showSignature=false` pair removed from `git`): caught by `test_r087_a_commit_s_signature_is_never_read_into_a_hit`.
- N6 `diff.relative` honoured (`--no-relative` dropped from both `git show` calls): caught by `test_r087_the_user_s_diff_settings_neither_hide_nor_misplace_a_hit`.
- N7 the lower-cased index match restored (`has_name` finds in `text.lower()` and reads neighbours in `text` at that index): caught by `test_r087_a_name_after_a_letter_that_lowercases_to_two_characters_is_found`.
- N8 `str.splitlines` restored for the patch (`_patch_lines` returns `text.splitlines()`): caught by `test_r087_a_form_feed_inside_an_added_line_moves_no_line_number`.
- N9 a printed path not escaped (`quote_path` returns the path unchanged): caught by `test_r087_a_control_character_in_a_printed_path_is_escaped`.
- M7 a name matched inside a longer word (the lookaround removed, leaving `re.compile(re.escape(name), re.IGNORECASE)`): caught by `test_r087_a_name_is_a_whole_word_in_any_letter_case`. This code was rewritten for F7, so M7 was re-run.
- M9 the line number counted in the old file (the new-side start passed to `added_lines` is the first `-` start): caught by `test_r087_each_path_form_in_an_added_line_is_a_hit_at_its_line`. This code was rewritten for F1, so M9 was re-run. The other FAILED ids were `test_r087_a_name_is_a_whole_word_in_any_letter_case`, `test_r087_a_line_of_a_file_whose_own_name_holds_a_hit_is_placed_by_the_file_s_position`, `test_r087_owner_2026_11_18_a_searched_name_equal_to_an_identity_name_is_dropped`, `test_r087_an_added_line_that_reads_like_a_file_header_is_scanned_in_its_hunk`, `test_r087_a_control_character_in_a_printed_path_is_escaped`, `test_r087_the_user_s_diff_settings_neither_hide_nor_misplace_a_hit`, `test_r087_a_name_after_a_letter_that_lowercases_to_two_characters_is_found`, and `test_r087_a_form_feed_inside_an_added_line_moves_no_line_number`.
- M10 a file whose own path holds a hit placed by its path in its line hits (`if False and hidden`): caught by `test_r087_a_line_of_a_file_whose_own_name_holds_a_hit_is_placed_by_the_file_s_position`. The place line was edited for F9, so M10 was re-run. The other FAILED ids were `test_r087_a_changed_file_with_a_space_in_its_name_is_read_by_its_whole_name` and `test_r087_a_merge_where_one_side_renamed_a_file_reads_each_file_by_its_own_position`.
- M1 the committer line not read: code unchanged (`if not carries_identity` on the committer line is still the round-1 line). Not re-run.
- M2 a renamed file's new name not read: code unchanged (`if status[:1] in ("A", "R")` is still that line). Not re-run.
- M3 the committer line exempted for any identity: code unchanged (`carries_identity` is untouched). Not re-run.
- M4 the owner segment of the remote kept as a name: code unchanged (`owner_of` and `public_names` are untouched). Not re-run.
- M5 the matched text printed in the hit line: code unchanged (`hit_line` is untouched). Not re-run.
- M6 a placeholder segment flagged: code unchanged (`has_path` and `_segment_start` are untouched). Not re-run.
- M8 a name shorter than four characters searched: code unchanged (`select_names` is untouched). Not re-run.
- M11 a base beginning with `-` accepted: code unchanged (`execute` is untouched). Not re-run.
- M12 the configured identity's names not dropped: code unchanged (`public_names` is untouched). Not re-run.
- M13 the configured identity's author and committer lines not exempted: code unchanged (both `if not carries_identity` lines are still the round-1 lines). Not re-run.

```
N1: 1 failed, 31 passed in 22.04s
N2: 1 failed, 31 passed in 21.58s
N3: 1 failed, 31 passed in 22.10s
N4: 32 passed in 22.11s
N5: 1 failed, 31 passed in 22.20s
N6: 1 failed, 31 passed in 22.08s
N7: 1 failed, 31 passed in 22.29s
N8: 1 failed, 31 passed in 22.12s
N9: 1 failed, 31 passed in 22.14s
M7: 1 failed, 31 passed in 22.25s
M9: 9 failed, 23 passed in 22.10s
M10: 3 failed, 29 passed in 22.05s
```

## Done commands

Counts below belong to commit `c64758a8dbd3b3218d04fba36bf10dab848eb5a9`. At step 13 the working tree held uncommitted changes. This report was written after that status, so its path is not in the step 13 status. In the bridge-check line the repository folder is written as `<Workspace>`.

1. `git status --short`

```
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/push-scan.py
 M docs/BUILDER_NOTES.md
```

Exit code 0.

2. `python tools/dump-cli.py`

```
```

Exit code 0. No lines printed.

3. `python tools/dump-cli.py --check`

```
```

Exit code 0. No lines printed.

4. `python tools/make-manifest.py`

```
make-manifest: version 2026.11.12a, 147 files hashed, VERSION + MANIFEST.json written
```

Exit code 0.

5. `git restore bridge/cursor-bridge/VERSION`

```
```

Exit code 0. No lines printed.

6. `python -m pytest -p no:cacheprovider -q -rs --tb=short tests/test_program_push_scan.py tests/test_dump_cli.py tests/test_allowlist.py`

```
........................................................................ [ 18%]
.................................................................s...ss. [ 36%]
....sss....................s...............s............................ [ 54%]
...................s...........s.................s...ss.....sss......... [ 73%]
...........s...............s............................................ [ 91%]
...s...........s.................                                        [100%]
=========================== short test summary info ===========================
SKIPPED [10] tests\test_allowlist.py:65: prose, not a runnable command
SKIPPED [10] tests\test_allowlist.py:106: prose, not a runnable command
373 passed, 20 skipped in 139.45s (0:02:19)
```

Exit code 0.

7. `python -m pytest -p no:cacheprovider -q tests/test_install_check.py tests/test_tests_windowless.py`

```
.........................                                                [100%]
25 passed in 21.80s
```

Exit code 0.

8. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`

```
bridge-check: version 2026.11.12a (2026-11-18 02:02) at <Workspace>/bridge
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

Exit code 0. No lines printed.

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
c64758a8dbd3b3218d04fba36bf10dab848eb5a9
```

Exit code 0.

```
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/push-scan.py
 M docs/BUILDER_NOTES.md
```

Exit code 0. `bridge/cursor-bridge/VERSION` is not listed.

## Assumed, not verified

- A combined-diff body line is in the new file when no column is `-`; a space in a parent's column consumes that parent's count, a minus consumes that parent's count and keeps the line out of the new file, and a plus consumes only the new side | F1 gives each old side a count and the new side a start and a count, and does not say which prefix character consumes which count; the merge test only requires the added path to be line 3 of its file | Print that merge's combined hunk and match each column to the counts in its header.
- The same column rule holds for a combined hunk with three or more parents | the round-2 merge has two parents | An octopus merge that adds one line, with the hit expected on that line's number in the new file.
- An unquoted path that contains a space is ended by one trailing tab and by nothing after that tab | F2 says git writes one trailing tab after such a path; the space-name test shows the whole path was kept and does not show whether a tab was present | Show the raw `+++` line of a change to a file whose name contains a space.
- Skipping every hunk line whose first character is a backslash drops only the no-newline marker | F1 names `\ No newline at end of file` and says it uses no count; no case omits the final newline | A file whose last added line has no newline, with the next added line keeping its number.
- `--src-prefix` and `--dst-prefix` on the command line override `diff.srcPrefix` and `diff.dstPrefix` | the diff-settings test sets `diff.noprefix` and `diff.relative`, not those two keys, and that test passed | A scratch repository with `diff.srcPrefix` and `diff.dstPrefix` set to other text, expecting the hit still placed at `notes.md`.
