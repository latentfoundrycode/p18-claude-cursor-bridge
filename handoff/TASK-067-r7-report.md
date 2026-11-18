# TASK-067 round 7 report

## Files changed

- `bridge/cursor-bridge/push-scan.py`
- `bridge/cursor-bridge/MANIFEST.json` (only by `python tools/make-manifest.py`)
- `docs/BUILDER_NOTES.md` (two dated lines)
- `handoff/TASK-067-r7-report.md` (this file)

`bridge/cursor-bridge/VERSION` was rewritten by `make-manifest.py` and restored with `git restore`. It reads `2026.11.12a` and is not listed by `git status --short`. `docs/CHANGES.md` and this brief do not disagree.

## Summary

A path's segment now begins with a letter, a digit, `_`, `.`, `-`, or any non-ASCII character that is not whitespace, so a byte no decoding reads still starts a segment, and a commit object is decoded in the encoding its header records when Python knows that encoding and it reads ASCII as ASCII, otherwise as UTF-8 with replacement.

## M1 to M3

- M1: `_segment_start` (lines 91-92) returns true for a letter, a digit, `_`, `.`, `-`, or `not ch.isascii() and not ch.isspace()`. `has_path` and `_bound` are unchanged.
- M2: `_decode_commit` (lines 314-336) reads header lines up to the first empty line, strips one trailing CR, and decodes the whole object with `errors="replace"` in the last `encoding` name that is printable ASCII, that Python knows, and that decodes every printable ASCII byte plus LF to that same text; otherwise it decodes UTF-8. `scan_commit` (lines 1134-1137) reads the object with `git("cat-file", ["-p", "--end-of-options", full])` and raises the same `ScanError` on a non-zero exit before calling `_decode_commit`. `parse_commit` and `_parent_count` are unchanged.
- M3: no new reason, output line, or note. The module docstring and `build_parser` (line 1260) are not in the diff. The disagreement check (lines 1193-1195) is the same text.

## Mutation self-check

Each mutant was applied to `push-scan.py`, then `python -m pytest -p no:cacheprovider -q --tb=no tests/test_program_push_scan.py` was run from `<Workspace>`, and the file was restored to the bytes from before that mutant. Step 12's diff is that restored program. Round 1's M6 was re-run because this round edits `_segment_start`. Every other mutant of rounds 1 to 6 changes code this round did not touch (T1-T10, S1-S16, N1-N9, P1-P6, Q1, M1-M5, M7-M13): code unchanged, not re-run. Q2 no longer applies (round 5 removed `--text`). The round-5 size-bound mutant no longer applies (round 6 removed the bound). N4 and the expect-survive set S8, S9, S12 and S14 were not re-run.

- U1 M1's non-ASCII clause dropped (`_segment_start` as in round 6, `return ch.isalpha() or ch.isdigit() or ch in "_.-"`): caught by `test_r087_a_path_in_a_file_written_in_another_encoding_is_found[drive-back]` (and the other three forms of that test). `4 failed, 98 passed in 95.94s (0:01:35)`
- U2 M1 widened to any non-space character (`return not ch.isspace()`): caught by `test_r087_ascii_punctuation_after_a_drive_still_begins_no_segment[backslash-quote]` (also `[slash-quote]` and `test_r087_a_placeholder_segment_in_angle_brackets_passes`). `3 failed, 99 passed in 95.92s (0:01:35)`
- U3 M2's header ignored (`_decode_commit` returns `raw.decode("utf-8", errors="replace")` at once): caught by `test_r087_a_non_ascii_name_in_a_message_git_records_in_another_encoding_is_found`. `1 failed, 101 passed in 96.57s (0:01:36)`
- U4 M2's ASCII check dropped (any encoding Python knows is used: `sample.decode(name)` selects the name unless it raises `LookupError`): not caught. `102 passed in 98.48s (0:01:38)`. A case that would catch it is a commit whose `encoding` header names an encoding Python knows that does not read ASCII as ASCII, whose bytes are UTF-8 and hold an ASCII path: a UTF-8 reading finds the path and that encoding hides it.
- U5 M2's fallback to UTF-8 dropped (`LookupError` from an encoding Python does not know is not caught and leaves `_decode_commit`): caught by `test_r087_a_message_whose_encoding_python_does_not_know_is_read_as_utf8`. `1 failed, 101 passed in 100.30s (0:01:40)`
- M6 a placeholder segment flagged (`ch in "_.-<"` on this round's `_segment_start`): caught by `test_r087_a_placeholder_segment_in_angle_brackets_passes`. `1 failed, 101 passed in 98.89s (0:01:38)`

An earlier probe of U4 used `b"".decode(name)`. That call returns an empty string for an unknown name and does not raise `LookupError`, so the probe was not the mutant above. Its run failed `test_r087_a_message_whose_encoding_python_does_not_know_is_read_as_utf8` (`1 failed, 101 passed in 98.03s (0:01:38)`).

### U1 output

```
........................................................................ [ 70%]
.......................FFFF...                                           [100%]
=========================== short test summary info ===========================
FAILED tests/test_program_push_scan.py::test_r087_a_path_in_a_file_written_in_another_encoding_is_found[drive-back]
FAILED tests/test_program_push_scan.py::test_r087_a_path_in_a_file_written_in_another_encoding_is_found[drive-forward]
FAILED tests/test_program_push_scan.py::test_r087_a_path_in_a_file_written_in_another_encoding_is_found[home]
FAILED tests/test_program_push_scan.py::test_r087_a_path_in_a_file_written_in_another_encoding_is_found[users]
4 failed, 98 passed in 95.94s (0:01:35)
```

Exit 1.

### U2 output

```
.............F.......................................................... [ 70%]
...........................FF.                                           [100%]
=========================== short test summary info ===========================
FAILED tests/test_program_push_scan.py::test_r087_a_placeholder_segment_in_angle_brackets_passes
FAILED tests/test_program_push_scan.py::test_r087_ascii_punctuation_after_a_drive_still_begins_no_segment[backslash-quote]
FAILED tests/test_program_push_scan.py::test_r087_ascii_punctuation_after_a_drive_still_begins_no_segment[slash-quote]
3 failed, 99 passed in 95.92s (0:01:35)
```

Exit 1.

### U3 output

```
........................................................................ [ 70%]
.....................F........                                           [100%]
=========================== short test summary info ===========================
FAILED tests/test_program_push_scan.py::test_r087_a_non_ascii_name_in_a_message_git_records_in_another_encoding_is_found
1 failed, 101 passed in 96.57s (0:01:36)
```

Exit 1.

### U4 output

```
........................................................................ [ 70%]
..............................                                           [100%]
102 passed in 98.48s (0:01:38)
```

Exit 0.

### U5 output

```
........................................................................ [ 70%]
......................F.......                                           [100%]
=========================== short test summary info ===========================
FAILED tests/test_program_push_scan.py::test_r087_a_message_whose_encoding_python_does_not_know_is_read_as_utf8
1 failed, 101 passed in 100.30s (0:01:40)
```

Exit 1.

### M6 output

```
.............F.......................................................... [ 70%]
..............................                                           [100%]
=========================== short test summary info ===========================
FAILED tests/test_program_push_scan.py::test_r087_a_placeholder_segment_in_angle_brackets_passes
1 failed, 101 passed in 98.89s (0:01:38)
```

Exit 1.

## Commands

The counts below belong to commit `f4f4e1168e711efe2b6f8d713d7811d772a912ee`. At step 13 the working tree held uncommitted changes, listed in that step. This report was written after that status, so it is not in that listing.

Before the Done list, the round-7 cases were run on their own: `python -m pytest -p no:cacheprovider -q --tb=line tests/test_program_push_scan.py -k "another_encoding or does_not_know or ascii_punctuation"`.

```
...............                                                          [100%]
15 passed, 87 deselected in 17.07s
```

Exit 0.

### 1. `git status --short`

```
 M bridge/cursor-bridge/push-scan.py
 M docs/BUILDER_NOTES.md
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
........................................................................ [ 31%]
...............................................................s...ss... [ 46%]
..sss....................s...............s.............................. [ 62%]
.................s...........s.................s...ss.....sss........... [ 77%]
.........s...............s.............................................. [ 93%]
.s...........s.................                                          [100%]
=========================== short test summary info ===========================
SKIPPED [10] tests\test_allowlist.py:65: prose, not a runnable command
SKIPPED [10] tests\test_allowlist.py:106: prose, not a runnable command
443 passed, 20 skipped in 213.74s (0:03:33)
```

Exit 0.

### 6. `python -m pytest -p no:cacheprovider -q tests/test_install_check.py tests/test_tests_windowless.py`

```
.........................                                                [100%]
25 passed in 23.98s
```

Exit 0.

### 7. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`

```
bridge-check: version 2026.11.12a (2026-11-18 12:01) at <Workspace>/bridge
bridge-check: 147 OK, 0 STALE, 0 MISSING, 0 EXTRA
RESULT: SOURCES MATCH bridge 2026.11.12a
```

Exit 0. The repository folder in the first line is written `<Workspace>` here.

### 8. `git grep -n -I -E --no-index "[A-Za-z]:[/\\]|/Users/|/home/|AppData" -- bridge/cursor-bridge/push-scan.py`

```
```

Exit 1. The command printed no lines.

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

Exit 0. The command printed no lines.

### 12. `git diff HEAD -- bridge/cursor-bridge/push-scan.py`

```
warning: in the working copy of 'bridge/cursor-bridge/push-scan.py', LF will be replaced by CRLF the next time Git touches it
diff --git a/bridge/cursor-bridge/push-scan.py b/bridge/cursor-bridge/push-scan.py
index 09213a4..292da64 100644
--- a/bridge/cursor-bridge/push-scan.py
+++ b/bridge/cursor-bridge/push-scan.py
@@ -89,7 +89,7 @@ def _bound(ch):
 
 
 def _segment_start(ch):
-    return ch.isalpha() or ch.isdigit() or ch in "_.-"
+    return ch.isalpha() or ch.isdigit() or ch in "_.-" or (not ch.isascii() and not ch.isspace())
 
 
 def has_path(text):
@@ -311,6 +311,31 @@ def split_ident(rest):
     return rest[:start], rest[start + 2:end]
 
 
+def _decode_commit(raw):
+    """The commit object in the encoding its header records, else UTF-8."""
+    chosen = None
+    sample = bytes(range(32, 127)) + b"\n"
+    plain = sample.decode("ascii")
+    for line in raw.split(b"\n"):
+        if line.endswith(b"\r"):
+            line = line[:-1]
+        if line == b"":
+            break
+        if not line.startswith(b"encoding "):
+            continue
+        token = line[len(b"encoding "):]
+        if any(byte < 32 or byte > 126 for byte in token):
+            continue
+        name = token.decode("ascii")
+        try:
+            same = sample.decode(name) == plain
+        except (LookupError, UnicodeError):
+            continue
+        if same:
+            chosen = name
+    return raw.decode(chosen or "utf-8", errors="replace")
+
+
 def parse_commit(text):
     lines = [line[:-1] if line.endswith("\r") else line for line in text.split("\n")]
     author = ("", "")
@@ -1106,9 +1131,10 @@ def _content_by_path(records, sections, work):
 
 def scan_commit(full, names, cfg_name, cfg_email, empty_tree, hash_len, work):
     short = _checked_short(git_need("rev-parse", ["--short", "--end-of-options", full]))
-    code, commit_text = git_text("cat-file", ["-p", "--end-of-options", full])
+    code, commit_raw = git("cat-file", ["-p", "--end-of-options", full])
     if code != 0:
         raise ScanError("git cat-file failed (exit %d)" % code)
+    commit_text = _decode_commit(commit_raw)
     author, committer, message = parse_commit(commit_text)
     show_options = [
         "--attr-source=" + empty_tree,
```

Exit 0.

### 13. `git rev-parse HEAD`

```
f4f4e1168e711efe2b6f8d713d7811d772a912ee
```

Exit 0.

### 13. `git status --short`

```
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/push-scan.py
 M docs/BUILDER_NOTES.md
```

Exit 0. `bridge/cursor-bridge/VERSION` is not listed.

## Assumed, not verified

- The last `encoding` line whose name passes the ASCII check is the one used, and a line that fails the check does not clear an earlier passing line | two headers can name different encodings, and only one of them may show a non-ASCII name | a commit with two `encoding` lines and a searched name that only one decoding shows.
- A header token that is not printable ASCII is ignored and the object is read as UTF-8 | the ISO-8859-1 tests used an ASCII name, so a non-ASCII name was not seen | a commit whose `encoding` token is not ASCII and whose message holds a non-ASCII searched name.
- One trailing CR is removed from a header line before the name is read | the commits these tests made were LF, so a CR on that line was not seen | a commit whose `encoding` line ends in CR and whose message holds a non-ASCII searched name.
- A codec that returns the printable-ASCII sample unchanged still shows an ASCII path when non-ASCII bytes sit beside it | the check compares one sample, and a separate probe of 356 standard-library codec names hid none of one ASCII-only path | decode, in each codec that passes the sample, an ASCII path placed after a non-ASCII byte.
