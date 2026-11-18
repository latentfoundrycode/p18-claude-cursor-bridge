# TASK-067 round 4 report

## Files changed

- `bridge/cursor-bridge/push-scan.py` (H1 and H2 only: `--no-replace-objects` on the `git` argv, and `--text` on the patch `git show` in `scan_commit`)
- `bridge/cursor-bridge/MANIFEST.json` (rewritten by `python tools/make-manifest.py` in Done step 3; the diff changes `generated` from `2026-11-18 02:39` to `2026-11-18 03:08` and the `cursor-bridge/push-scan.py` hash)
- `handoff/TASK-067-r4-report.md` (this file, written after Done step 13)

`docs/BUILDER_NOTES.md` was not edited. `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` were not edited: the parser text did not change, and `python tools/dump-cli.py` was not run without `--check`. `bridge/cursor-bridge/VERSION` was restored with `git restore` and is not in the step 13 status. `bridge/cursor-bridge/settings.bridge.json` was not edited.

## Summary

The pre-push scan now passes `--no-replace-objects` on every git call and `--text` on the patch `git show`, so a replace ref cannot hide the commit a push sends and a text file marked `-diff` or `binary` by that commit's `.gitattributes` is still read line by line.

## H1-H3

- H1: `git` (line 51) puts `--no-replace-objects` immediately after `--no-pager` and before the subcommand, so every git call of the program ignores `refs/replace/`. The `-c` pairs, `subprocess.run` arguments and exception handling are unchanged.
- H2: the patch call in `scan_commit` (the argument list at lines 637-640) passes `--text` immediately after `--no-textconv` on line 637. The name-status call (lines 628-631) is unchanged. Both calls still pass `--ignore-submodules=none` and `--submodule=short`.
- H3: `git diff HEAD -- bridge/cursor-bridge/push-scan.py` (Done step 12) has two hunks, the argv in `git` and the patch argument list in `scan_commit`. Every other line of the program is the round-3 text.

## Mutation self-check

Each of Q1, Q2, N5, N6, P1, P2, P3 and P4 was applied to `push-scan.py`, then `python -m pytest -p no:cacheprovider -q --tb=no tests/test_program_push_scan.py` was run from `<Workspace>`, and the file was restored to the bytes from before that mutant. A first look for `"--submodule=short", ` with a space after the comma found no match because the source breaks the line after the comma; that attempt did not write the file, and P3 below is the run that removed the flag.

- Q1 `--no-replace-objects` removed from the runner (H1): caught by `test_r087_a_replaced_commit_is_read_as_the_push_sends_it`.
- Q2 `--text` removed from the patch call (H2): caught by `test_r087_a_text_file_the_commit_marks_binary_is_still_read[-diff]`. The other FAILED id was `test_r087_a_text_file_the_commit_marks_binary_is_still_read[binary]`.
- N5 `log.showSignature` left on (the `-c log.showSignature=false` pair removed from `git`): caught by `test_r087_a_commit_s_signature_is_never_read_into_a_hit`.
- N6 `--no-relative` dropped from both `git show` calls: caught by `test_r087_the_user_s_diff_settings_neither_hide_nor_misplace_a_hit`.
- P1 `-c log.showRoot=true` removed from the runner: caught by `test_r087_a_root_commit_in_the_range_is_read_whatever_log_show_root_says`.
- P2 `--ignore-submodules=none` removed from both `git show` calls: caught by `test_r087_a_submodule_hidden_by_the_user_s_setting_is_still_read`. The other FAILED ids were `test_r087_a_submodule_hidden_by_the_commit_s_own_gitmodules_is_still_read` and `test_r087_a_submodule_s_own_diff_is_never_inlined`.
- P3 `--submodule=short` removed from both `git show` calls: caught by `test_r087_a_submodule_s_own_diff_is_never_inlined`.
- P4 `-c diff.suppressBlankEmpty=false` removed from the runner: caught by `test_r087_a_blank_context_line_is_read_whatever_diff_suppress_blank_empty_says`.
- N1 a `+++` line read inside a hunk: code unchanged (`added_lines` is untouched). Not re-run.
- N2 a path cut at its first space: code unchanged (`_path_from_rest` is untouched). Not re-run.
- N3 a combined status read with two paths: code unchanged (`_two_path_status` is untouched). Not re-run.
- N4 the disagreement check removed: code unchanged (`scan_commit` lines 670-672). Expected to survive. Not re-run.
- N7 the lower-cased index match restored: code unchanged (`has_name` is untouched). Not re-run.
- N8 `str.splitlines` restored for the patch: code unchanged (`_patch_lines` is untouched). Not re-run.
- N9 a printed path not escaped (`quote_path` returns the path unchanged): code unchanged (`quote_path` is untouched). Not re-run.
- P5 the escaped-text check of G5 removed (placement decided on the real path only): code unchanged (the placement line, `scan_commit` line 659, is untouched). Not re-run.
- P6 `Cf` removed from `quote_path`'s set: code unchanged (`quote_path` is untouched). Not re-run.
- M1 the committer line not read: code unchanged. Not re-run.
- M2 a renamed file's new name not read: code unchanged (`if status[:1] in ("A", "R")` is still that line). Not re-run.
- M3 the committer line exempted for any identity: code unchanged (`carries_identity` is untouched). Not re-run.
- M4 the owner segment of the remote kept as a name: code unchanged (`owner_of` and `public_names` are untouched). Not re-run.
- M5 the matched text printed in the hit line: code unchanged (`hit_line` is untouched). Not re-run.
- M6 a placeholder segment flagged: code unchanged (`has_path` and `_segment_start` are untouched). Not re-run.
- M7 a name matched inside a longer word: code unchanged (`has_name` is untouched). Not re-run.
- M8 a name shorter than four characters searched: code unchanged (`select_names` is untouched). Not re-run.
- M9 the line number counted in the old file: code unchanged (`added_lines` is untouched). Not re-run.
- M10 a file whose own path holds a hit placed by its path: code unchanged (the placement line is untouched). Not re-run.
- M11 a base beginning with `-` accepted: code unchanged (`execute` is untouched). Not re-run.
- M12 the configured identity's names not dropped: code unchanged (`public_names` is untouched). Not re-run.
- M13 the configured identity's author and committer lines not exempted: code unchanged (both `if not carries_identity` lines are still those lines). Not re-run.

```
Q1: 1 failed, 41 passed in 29.47s
Q2: 2 failed, 40 passed in 29.73s
N5: 1 failed, 41 passed in 29.96s
N6: 1 failed, 41 passed in 29.91s
P1: 1 failed, 41 passed in 29.85s
P2: 3 failed, 39 passed in 29.85s
P3: 1 failed, 41 passed in 29.78s
P4: 1 failed, 41 passed in 29.88s
```

Before those mutants, the same pytest command on the edited file printed:

```
..........................................                               [100%]
42 passed in 29.97s
```

Exit code 0.

## Done commands

Counts below belong to commit `776168e300e9f763801e58aea8a2124036e78408`. At step 13 the working tree held uncommitted changes. This report was written after that status, so its path is not in the step 13 status. In the bridge-check line the repository folder is written as `<Workspace>`.

1. `git status --short`

```
 M bridge/cursor-bridge/push-scan.py
```

Exit code 0.

2. `python tools/dump-cli.py --check`

```
```

No lines printed. Exit code 0.

3. `python tools/make-manifest.py`

```
make-manifest: version 2026.11.12a, 147 files hashed, VERSION + MANIFEST.json written
```

Exit code 0.

4. `git restore bridge/cursor-bridge/VERSION`

```
```

No lines printed. Exit code 0. `bridge/cursor-bridge/VERSION` reads `2026.11.12a`.

5. `python -m pytest -p no:cacheprovider -q -rs --tb=short tests/test_program_push_scan.py tests/test_dump_cli.py tests/test_allowlist.py`

```
........................................................................ [ 17%]
........................................................................ [ 35%]
...s...ss.....sss....................s...............s.................. [ 53%]
.............................s...........s.................s...ss.....ss [ 71%]
s....................s...............s.................................. [ 89%]
.............s...........s.................                              [100%]
=========================== short test summary info ===========================
SKIPPED [10] tests\test_allowlist.py:65: prose, not a runnable command
SKIPPED [10] tests\test_allowlist.py:106: prose, not a runnable command
383 passed, 20 skipped in 146.97s (0:02:26)
```

Exit code 0.

6. `python -m pytest -p no:cacheprovider -q tests/test_install_check.py tests/test_tests_windowless.py`

```
.........................                                                [100%]
25 passed in 22.75s
```

Exit code 0.

7. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`

```
bridge-check: version 2026.11.12a (2026-11-18 03:08) at <Workspace>/bridge
bridge-check: 147 OK, 0 STALE, 0 MISSING, 0 EXTRA
RESULT: SOURCES MATCH bridge 2026.11.12a
```

Exit code 0.

8. `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks`

```
windowless-check: 40 file(s) scanned, 0 FAIL, 0 NOTE
```

Exit code 0.

9. `git grep -n -I -E --no-index "[A-Za-z]:[/\\]|/Users/|/home/|AppData" -- bridge/cursor-bridge/push-scan.py`

```
```

No lines printed. Exit code 1.

10. `python -c "open('bridge/cursor-bridge/push-scan.py','rb').read().decode('ascii'); print('ascii ok')"`

```
ascii ok
```

Exit code 0.

11. `git diff --stat HEAD -- bridge/cursor-bridge/settings.bridge.json`

```
```

No lines printed. Exit code 0.

12. `git diff HEAD -- bridge/cursor-bridge/push-scan.py`

```
warning: in the working copy of 'bridge/cursor-bridge/push-scan.py', LF will be replaced by CRLF the next time Git touches it
diff --git a/bridge/cursor-bridge/push-scan.py b/bridge/cursor-bridge/push-scan.py
index a75a75d..9c679be 100644
--- a/bridge/cursor-bridge/push-scan.py
+++ b/bridge/cursor-bridge/push-scan.py
@@ -48,7 +48,7 @@ def say(line):
 
 
 def git(sub, args):
-    argv = ["git", "--no-pager", "-c", "color.ui=never", "-c", "log.showSignature=false", "-c", "log.showRoot=true", "-c", "diff.suppressBlankEmpty=false", sub] + list(args)
+    argv = ["git", "--no-pager", "--no-replace-objects", "-c", "color.ui=never", "-c", "log.showSignature=false", "-c", "log.showRoot=true", "-c", "diff.suppressBlankEmpty=false", sub] + list(args)
     try:
         proc = subprocess.run(
             argv,
@@ -634,7 +634,7 @@ def scan_commit(full, names, cfg_name, cfg_email):
         raise ScanError("git show failed (exit %d)" % code)
     patch = git_need(
         "show",
-        ["-M", "--format=", "--no-ext-diff", "--no-textconv", "--no-color",
+        ["-M", "--format=", "--no-ext-diff", "--no-textconv", "--text", "--no-color",
          "--no-relative", "--src-prefix=a/", "--dst-prefix=b/",
          "--ignore-submodules=none", "--submodule=short",
          "--end-of-options", full],
```

Exit code 0.

13. `git rev-parse HEAD` and `git status --short`

```
776168e300e9f763801e58aea8a2124036e78408
```

Exit code 0.

```
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/push-scan.py
```

Exit code 0. `bridge/cursor-bridge/VERSION` is not listed.

## Assumed, not verified

- that `--no-replace-objects` before the subcommand makes `rev-list`, `cat-file -p`, `rev-parse --short` and `git show` read the original objects when `core.useReplaceRefs` is set or `GIT_REPLACE_REF_BASE` names another ref namespace | the passing round-4 case uses a default `git replace` under `refs/replace/` and sets neither | The same hidden commit with `core.useReplaceRefs` set, and again with `GIT_REPLACE_REF_BASE` pointing at a namespace that holds the replace ref, each expecting `HIT` for the original and exit 1.
- that `--text` on `git show` overrides a `binary` or `-diff` attribute from `.git/info/attributes` and from `core.attributesFile`, a diff driver's `binary` setting, and `core.bigFileThreshold`, with `--no-textconv` and `--no-ext-diff` still in force | the passing cases only commit `.gitattributes` with `*.md -diff` and `*.md binary` | Each of those four sources marking the added text file binary or `-diff`, with a path on an added line, expecting `HIT` and exit 1.
- that a file shown by `--text` whose bytes hold a CR or a NUL inside a line, or no final newline, is read by `added_lines` without a `the patch cannot be read` refusal | no case in this round builds those bytes; a UTF-16 file is a recorded lead left out of this round | An added text line that contains a CR or a NUL and still holds a path, and an added file with no final newline, each expecting a hit or exit 2, and a clean range still exiting 0.
