# TASK-067 round 8 report

## Files changed

- `bridge/cursor-bridge/push-scan.py`
- `bridge/cursor-bridge/MANIFEST.json` (only by `python tools/make-manifest.py`)
- `docs/BUILDER_NOTES.md` (one dated line)
- `handoff/TASK-067-r8-report.md` (this file)

`bridge/cursor-bridge/VERSION` was rewritten by `make-manifest.py` and restored with `git restore`. It reads `2026.11.12a` and is not listed by `git status --short`. `docs/CHANGES.md` and this brief do not disagree.

## Summary

Round 7's decoding of a commit object from its `encoding` header is withdrawn, so the object is read as UTF-8 with replacement through `git_text` as in round 6, and `_segment_start` also treats ESC (U+001B) and SO (U+000E) as the start of a path segment, written as Python escapes so the source stays ASCII.

## N1 to N3

- N1: `_decode_commit` is gone. `split_ident` ends at line 311 and `parse_commit` begins at line 314. `scan_commit` (lines 1107-1112) reads the object with `git_text("cat-file", ["-p", "--end-of-options", full])` at line 1109, raises `ScanError("git cat-file failed (exit %d)" % code)` at lines 1110-1111, and calls `parse_commit(commit_text)` at line 1112. No `encoding` header is read.
- N2: `_segment_start` (lines 91-92) returns true for a letter, a digit, `_`, `.`, `-`, ESC (`\x1b`), SO (`\x0e`), or a non-ASCII character that is not whitespace. `_bound` and `has_path` are unchanged.
- N3: no new reason, output line, or note. The module docstring (lines 2-19) and `build_parser` (line 1234) are not in the diff. The disagreement check (lines 1167-1169) is the same text.

## Diff against round 6 (`f4f4e11`)

Against `f4f4e11` the diff is one hunk, in `_segment_start`: the return adds `\x1b` and `\x0e` beside `_.-` and keeps the non-ASCII clause. Nothing else differs from round 6. The hunk is quoted under step 12.

## Mutation self-check

Each mutant was applied to `push-scan.py`, then `python -m pytest -p no:cacheprovider -q --tb=no tests/test_program_push_scan.py` was run from `<Workspace>`, and the file was restored to the bytes from before that mutant. The Done diffs are that restored program. Round 7's U3 to U5 changed `_decode_commit`, which this round removes, so they no longer apply. U1 and M6 change `_segment_start`, which this round edits, so they were re-run; U2's text is V4's (`return not ch.isspace()`) and that run is V4. Every other mutant of rounds 1 to 7 changes code this round did not touch (T1-T10, S1-S16, N1-N9, P1-P6, Q1, M1-M5, M7-M13): code unchanged, not re-run. Q2 no longer applies (round 5 removed `--text`). The round-5 size-bound mutant no longer applies (round 6 removed the bound). N4 and the expect-survive set S8, S9, S12 and S14 were not re-run.

- V1 the non-ASCII clause dropped from `_segment_start` (`return ch.isalpha() or ch.isdigit() or ch in "_.-\x1b\x0e"`): caught by `test_r087_a_path_in_a_message_git_records_in_another_encoding_is_found[drive-back]`.
- V2 ESC dropped from `_segment_start` (SO kept, `ch in "_.-\x0e"`): caught by `test_r087_a_path_whose_segment_an_iso2022_shift_begins_is_found[jp-message-with-header]`.
- V3 SO dropped from `_segment_start` (ESC kept, `ch in "_.-\x1b"`): caught by `test_r087_a_path_whose_segment_an_iso2022_shift_begins_is_found[kr-file-line]`.
- V4 ASCII punctuation added (any non-space character begins a segment, `return not ch.isspace()`): caught by `test_r087_a_placeholder_segment_in_angle_brackets_passes`.
- V5 a header read again as round 7 did (round 7's `_decode_commit` and its call put back): caught by `test_r087_an_encoding_header_never_hides_a_path_the_utf8_reading_finds[iso2022jp-users]`.
- U1 M1's non-ASCII clause dropped and the return set back to round 6 (`return ch.isalpha() or ch.isdigit() or ch in "_.-"`): caught by `test_r087_a_path_in_a_message_git_records_in_another_encoding_is_found[drive-back]`.
- M6 a placeholder segment flagged (`ch in "_.-\x1b\x0e<"` on this round's `_segment_start`): caught by `test_r087_a_placeholder_segment_in_angle_brackets_passes`.

### V1 output

```
........................................................................ [ 63%]
.................FFFF.FFFF................                               [100%]
=========================== short test summary info ===========================
FAILED tests/test_program_push_scan.py::test_r087_a_path_in_a_message_git_records_in_another_encoding_is_found[drive-back]
FAILED tests/test_program_push_scan.py::test_r087_a_path_in_a_message_git_records_in_another_encoding_is_found[drive-forward]
FAILED tests/test_program_push_scan.py::test_r087_a_path_in_a_message_git_records_in_another_encoding_is_found[home]
FAILED tests/test_program_push_scan.py::test_r087_a_path_in_a_message_git_records_in_another_encoding_is_found[users]
FAILED tests/test_program_push_scan.py::test_r087_a_path_in_a_file_written_in_another_encoding_is_found[drive-back]
FAILED tests/test_program_push_scan.py::test_r087_a_path_in_a_file_written_in_another_encoding_is_found[drive-forward]
FAILED tests/test_program_push_scan.py::test_r087_a_path_in_a_file_written_in_another_encoding_is_found[home]
FAILED tests/test_program_push_scan.py::test_r087_a_path_in_a_file_written_in_another_encoding_is_found[users]
8 failed, 106 passed in 104.94s (0:01:44)
```

Exit 1.

### V2 output

```
........................................................................ [ 63%]
......................................FFF.                               [100%]
=========================== short test summary info ===========================
FAILED tests/test_program_push_scan.py::test_r087_a_path_whose_segment_an_iso2022_shift_begins_is_found[jp-message-with-header]
FAILED tests/test_program_push_scan.py::test_r087_a_path_whose_segment_an_iso2022_shift_begins_is_found[jp-message-without-header]
FAILED tests/test_program_push_scan.py::test_r087_a_path_whose_segment_an_iso2022_shift_begins_is_found[jp-file-line]
3 failed, 111 passed in 105.60s (0:01:45)
```

Exit 1.

### V3 output

```
........................................................................ [ 63%]
.........................................F                               [100%]
=========================== short test summary info ===========================
FAILED tests/test_program_push_scan.py::test_r087_a_path_whose_segment_an_iso2022_shift_begins_is_found[kr-file-line]
1 failed, 113 passed in 104.84s (0:01:44)
```

Exit 1.

### V4 output

```
.............F.......................................................... [ 63%]
..........................FF..............                               [100%]
=========================== short test summary info ===========================
FAILED tests/test_program_push_scan.py::test_r087_a_placeholder_segment_in_angle_brackets_passes
FAILED tests/test_program_push_scan.py::test_r087_ascii_punctuation_after_a_drive_still_begins_no_segment[backslash-quote]
FAILED tests/test_program_push_scan.py::test_r087_ascii_punctuation_after_a_drive_still_begins_no_segment[slash-quote]
3 failed, 111 passed in 106.30s (0:01:46)
```

Exit 1.

### V5 output

```
........................................................................ [ 63%]
...............................FFFFFFF....                               [100%]
=========================== short test summary info ===========================
FAILED tests/test_program_push_scan.py::test_r087_an_encoding_header_never_hides_a_path_the_utf8_reading_finds[iso2022jp-users]
FAILED tests/test_program_push_scan.py::test_r087_an_encoding_header_never_hides_a_path_the_utf8_reading_finds[iso2022jp-home]
FAILED tests/test_program_push_scan.py::test_r087_an_encoding_header_never_hides_a_path_the_utf8_reading_finds[shiftjis-drive]
FAILED tests/test_program_push_scan.py::test_r087_an_encoding_header_never_hides_a_path_the_utf8_reading_finds[big5-drive]
FAILED tests/test_program_push_scan.py::test_r087_an_encoding_header_never_hides_a_path_the_utf8_reading_finds[unicode-escape-drive]
FAILED tests/test_program_push_scan.py::test_r087_an_encoding_header_never_hides_a_name_the_utf8_reading_finds
FAILED tests/test_program_push_scan.py::test_r087_a_non_ascii_identity_stays_exempt_under_another_encoding_header
7 failed, 107 passed in 113.10s (0:01:53)
```

Exit 1.

### M6 output

```
.............F.......................................................... [ 63%]
..........................................                               [100%]
=========================== short test summary info ===========================
FAILED tests/test_program_push_scan.py::test_r087_a_placeholder_segment_in_angle_brackets_passes
1 failed, 113 passed in 106.53s (0:01:46)
```

Exit 1.

### U1 output

```
........................................................................ [ 63%]
.................FFFF.FFFF............FFFF                               [100%]
=========================== short test summary info ===========================
FAILED tests/test_program_push_scan.py::test_r087_a_path_in_a_message_git_records_in_another_encoding_is_found[drive-back]
FAILED tests/test_program_push_scan.py::test_r087_a_path_in_a_message_git_records_in_another_encoding_is_found[drive-forward]
FAILED tests/test_program_push_scan.py::test_r087_a_path_in_a_message_git_records_in_another_encoding_is_found[home]
FAILED tests/test_program_push_scan.py::test_r087_a_path_in_a_message_git_records_in_another_encoding_is_found[users]
FAILED tests/test_program_push_scan.py::test_r087_a_path_in_a_file_written_in_another_encoding_is_found[drive-back]
FAILED tests/test_program_push_scan.py::test_r087_a_path_in_a_file_written_in_another_encoding_is_found[drive-forward]
FAILED tests/test_program_push_scan.py::test_r087_a_path_in_a_file_written_in_another_encoding_is_found[home]
FAILED tests/test_program_push_scan.py::test_r087_a_path_in_a_file_written_in_another_encoding_is_found[users]
FAILED tests/test_program_push_scan.py::test_r087_a_path_whose_segment_an_iso2022_shift_begins_is_found[jp-message-with-header]
FAILED tests/test_program_push_scan.py::test_r087_a_path_whose_segment_an_iso2022_shift_begins_is_found[jp-message-without-header]
FAILED tests/test_program_push_scan.py::test_r087_a_path_whose_segment_an_iso2022_shift_begins_is_found[jp-file-line]
FAILED tests/test_program_push_scan.py::test_r087_a_path_whose_segment_an_iso2022_shift_begins_is_found[kr-file-line]
12 failed, 102 passed in 106.41s (0:01:46)
```

Exit 1.

## Commands

These counts belong to commit `4b029240b8917c22300be0ae368e4ca90c662c26`. After step 14 the working tree held uncommitted changes; `bridge/cursor-bridge/VERSION` was not listed.

### 1. `git status --short`

```
 M bridge/cursor-bridge/push-scan.py
 M docs/BUILDER_NOTES.md
?? handoff/TASK-067-r8-report.md
```

Exit 0.

### 2. `python tools/dump-cli.py --check`

```
```

Exit 0. The command printed no lines.

### 3. `python tools/make-manifest.py`

```
make-manifest: version 2026.11.12a, 147 files hashed, VERSION + MANIFEST.json written
```

Exit 0.

### 4. `git restore bridge/cursor-bridge/VERSION`

```
```

Exit 0. The command printed no lines.

### 5. `python -m pytest -p no:cacheprovider -q -rs --tb=short tests/test_program_push_scan.py tests/test_dump_cli.py tests/test_allowlist.py`

```
........................................................................ [ 15%]
........................................................................ [ 30%]
........................................................................ [ 45%]
...s...ss.....sss....................s...............s.................. [ 60%]
.............................s...........s.................s...ss.....ss [ 75%]
s....................s...............s.................................. [ 90%]
.............s...........s.................                              [100%]
=========================== short test summary info ===========================
SKIPPED [10] tests\test_allowlist.py:65: prose, not a runnable command
SKIPPED [10] tests\test_allowlist.py:106: prose, not a runnable command
455 passed, 20 skipped in 213.62s (0:03:33)
```

Exit 0.

### 6. `python -m pytest -p no:cacheprovider -q tests/test_install_check.py tests/test_tests_windowless.py`

```
.........................                                                [100%]
25 passed in 22.86s
```

Exit 0.

### 7. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`

```
bridge-check: version 2026.11.12a (2026-11-18 13:03) at <Workspace>\bridge
bridge-check: 147 OK, 0 STALE, 0 MISSING, 0 EXTRA
RESULT: SOURCES MATCH bridge 2026.11.12a
```

Exit 0.

### 8. `git grep -n -I -E --no-index "[A-Za-z]:[/\\]|/Users/|/home/|AppData" -- bridge/cursor-bridge/push-scan.py`

```
```

The command printed no lines. Exit 1.

### 9. `python -c "open('bridge/cursor-bridge/push-scan.py','rb').read().decode('ascii'); print('ascii ok')"`

```
ascii ok
```

Exit 0.

### 10. `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks`

```
windowless-check: 40 file(s) scanned, 0 FAIL, 0 NOTE
```

Exit 0.

### 11. `git diff --stat HEAD -- bridge/cursor-bridge/settings.bridge.json`

```
```

The command printed no lines. Exit 0.

### 12. `git diff f4f4e11 -- bridge/cursor-bridge/push-scan.py`

```
warning: in the working copy of 'bridge/cursor-bridge/push-scan.py', LF will be replaced by CRLF the next time Git touches it
diff --git a/bridge/cursor-bridge/push-scan.py b/bridge/cursor-bridge/push-scan.py
index 09213a4..2c7906d 100644
--- a/bridge/cursor-bridge/push-scan.py
+++ b/bridge/cursor-bridge/push-scan.py
@@ -89,7 +89,7 @@ def _bound(ch):
 
 
 def _segment_start(ch):
-    return ch.isalpha() or ch.isdigit() or ch in "_.-"
+    return ch.isalpha() or ch.isdigit() or ch in "_.-\x1b\x0e" or (not ch.isascii() and not ch.isspace())
 
 
 def has_path(text):
```

Exit 0.

### 13. `git diff HEAD -- bridge/cursor-bridge/push-scan.py`

```
warning: in the working copy of 'bridge/cursor-bridge/push-scan.py', LF will be replaced by CRLF the next time Git touches it
diff --git a/bridge/cursor-bridge/push-scan.py b/bridge/cursor-bridge/push-scan.py
index 292da64..2c7906d 100644
--- a/bridge/cursor-bridge/push-scan.py
+++ b/bridge/cursor-bridge/push-scan.py
@@ -89,7 +89,7 @@ def _bound(ch):
 
 
 def _segment_start(ch):
-    return ch.isalpha() or ch.isdigit() or ch in "_.-" or (not ch.isascii() and not ch.isspace())
+    return ch.isalpha() or ch.isdigit() or ch in "_.-\x1b\x0e" or (not ch.isascii() and not ch.isspace())
 
 
 def has_path(text):
@@ -311,31 +311,6 @@ def split_ident(rest):
     return rest[:start], rest[start + 2:end]
 
 
-def _decode_commit(raw):
-    """The commit object in the encoding its header records, else UTF-8."""
-    chosen = None
-    sample = bytes(range(32, 127)) + b"\n"
-    plain = sample.decode("ascii")
-    for line in raw.split(b"\n"):
-        if line.endswith(b"\r"):
-            line = line[:-1]
-        if line == b"":
-            break
-        if not line.startswith(b"encoding "):
-            continue
-        token = line[len(b"encoding "):]
-        if any(byte < 32 or byte > 126 for byte in token):
-            continue
-        name = token.decode("ascii")
-        try:
-            same = sample.decode(name) == plain
-        except (LookupError, UnicodeError):
-            continue
-        if same:
-            chosen = name
-    return raw.decode(chosen or "utf-8", errors="replace")
-
-
 def parse_commit(text):
     lines = [line[:-1] if line.endswith("\r") else line for line in text.split("\n")]
     author = ("", "")
@@ -1131,10 +1106,9 @@ def _content_by_path(records, sections, work):
 
 def scan_commit(full, names, cfg_name, cfg_email, empty_tree, hash_len, work):
     short = _checked_short(git_need("rev-parse", ["--short", "--end-of-options", full]))
-    code, commit_raw = git("cat-file", ["-p", "--end-of-options", full])
+    code, commit_text = git_text("cat-file", ["-p", "--end-of-options", full])
     if code != 0:
         raise ScanError("git cat-file failed (exit %d)" % code)
-    commit_text = _decode_commit(commit_raw)
     author, committer, message = parse_commit(commit_text)
     show_options = [
         "--attr-source=" + empty_tree,
```

Exit 0.

### 14. `git rev-parse HEAD` and `git status --short`

```
4b029240b8917c22300be0ae368e4ca90c662c26
```

Exit 0.

```
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/push-scan.py
 M docs/BUILDER_NOTES.md
?? handoff/TASK-067-r8-report.md
```

Exit 0. `bridge/cursor-bridge/VERSION` is not listed.

## Assumed, not verified

Assumed, not verified: none
