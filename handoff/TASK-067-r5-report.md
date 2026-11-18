# TASK-067 round 5 report

## Files changed

- `bridge/cursor-bridge/push-scan.py`
- `bridge/cursor-bridge/MANIFEST.json` (only by `python tools/make-manifest.py`)
- `docs/BUILDER_NOTES.md` (one dated line)
- `handoff/TASK-067-r5-report.md` (this file)

`bridge/cursor-bridge/VERSION` was rewritten by `make-manifest.py` and restored with `git restore`. It reads `2026.11.12a` and is not listed by `git status --short`. `docs/CHANGES.md` and this brief do not disagree.

## Summary

The pre-push scan no longer uses `--text` or any attributes file to decide how a file is read: each result blob is classified from its own bytes, text that git shows as hunks is still read from those hunks, text git hides and every UTF-16 file with a byte-order mark are read by a line diff against each preimage, and a binary result is counted and never read.

## K1 to K8

- K1: `git` (line 51) takes global `options` before the subcommand and `feed` as the child's stdin; `repository_ids` (line 838) runs `hash-object -t tree --stdin` with `feed=b""` (line 850); `scan_commit` (line 1036) passes `--attr-source=<empty tree>`, `-c core.attributesFile=` and `-c core.quotePath=true` on both show calls, and the patch call (line 1057) is `--cc --full-index` without `--text`. A git that rejects `--attr-source` fails that call: `git show failed (exit %d)`.
- K2: `parse_raw_records` (line 702) reads `-z --raw --no-abbrev` (the file-list call at line 1047). Paths are decoded with `surrogateescape` (line 759) and `unquote_git` ends the same way (line 369). A malformed record, a bad mode, a status that is not allowed, a duplicate path, or an id that is not lowercase hex of the repository's hash length raises `the patch cannot be read`. `sha1` is 40 and `sha256` is 64; any other `rev-parse --show-object-format` answer is `the patch cannot be read`. A non-zero `rev-parse` is `git rev-parse failed (exit %d)`; a non-zero `hash-object` is `git hash-object failed (exit %d)`.
- K3: `added_lines` (line 559) records each section's path, index ids, hunks and `Binary files` line. The path comes from `+++`, `rename to` or `diff --cc` / `diff --combined`, otherwise from `diff --git` via `_diff_git_path` (line 492), which raises `the patch cannot be read` when the header cannot be split. `_match_index` (line 944) raises `the patch and the file list disagree` when an id is missing or not the record's. A short or ill-formed index id raises `the patch cannot be read` in `_parse_index_line` (line 525). `_type_change_addition` (line 951) matches a `T` record to a deletion section (`<pre>..<zeros>`, no added line) and an addition section (`<zeros>..<result>`). An added line in a deleted file raises `the patch cannot be read` (lines 970 and 1003). A section path that is not in the raw list raises `the patch and the file list disagree` (line 1026). The named-path check at lines 1094-1096 is unchanged.
- K4: `classify_blob` (line 866) returns `utf-16` when the bytes begin with `FF FE` or `FE FF` and the rest decodes strictly, else `binary` when a NUL is in `data[:8000]`, else `text`. `_read_blob` (line 859) is `git cat-file blob`; a non-zero exit is `git cat-file failed (exit %d)`. A deleted result and a submodule (mode `160000`) are not classified.
- K5: `_by_class` (line 979) reads hunks only for text that shows hunks; UTF-16, and text with no hunk whose result differs from every preimage, go through `line_diff_added` (line 922), which keeps a result line only where it is added against every preimage. A binary contributes no lines and adds one to the count, hunks included. `_blob_text_lines` (line 888) raises `a file too large to compare` above 1 MiB. A binary, all-zero or submodule preimage is not decoded and is not subject to that bound.
- K6: `execute` (line 1152) prints `push-scan: note - <n> binary file(s) not read` once, after the HIT lines and immediately before FOUND or OK, when the total over the range is not zero.
- K7: the runner still passes `--no-replace-objects` (line 52). The file-name condition stays `if status[:1] in ("A", "R")` (line 1084). The placement line (line 1083) and the disagreement check (lines 1094-1096) keep their wording. No other printed reason was added.
- K8: the module docstring (lines 2-19) and `build_parser` (line 1162) are unchanged, and `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` were not edited. `python tools/dump-cli.py --check` exits 0.

## Mutation self-check

Each mutant was applied to `push-scan.py`, then `python -m pytest -p no:cacheprovider -q --tb=no tests/test_program_push_scan.py` was run from `<Workspace>`, and the file was restored to the bytes from before that mutant. `RESTORED True` after the last one.

- S1 `--attr-source` dropped from the patch call: not caught. The static test only requires the substring once, and a text file a committed attribute shows as binary is still read by the line diff. A case that would catch it asserts `--attr-source` on both `git show` calls.
- S2 `-c core.attributesFile=` dropped: caught by `test_r087_no_attribute_decides_and_ids_are_full`. `1 failed, 67 passed in 62.87s (0:01:02)`
- S3 classification skipped (every result treated as text): caught by `test_r087_a_real_binary_is_counted_and_never_read_however_git_shows_it[None]`. `12 failed, 56 passed in 67.05s (0:01:07)`
- S4 the NUL window changed from `data[:8000]` to `data[:7999]`: caught by `test_r087_git_s_content_rule_decides_at_its_8000th_byte[7999-True]`. `1 failed, 67 passed in 62.73s (0:01:02)`
- S5 the UTF-16 branch removed: caught by `test_r087_a_utf16_file_with_a_byte_order_mark_is_read_as_text[\xff\xfe-utf-16-le]`. `3 failed, 65 passed in 62.34s (0:01:02)`
- S6 the line diff's intersection replaced by a union: caught by `test_r087_a_duplicate_line_a_merge_adds_against_both_parents_counts`. `1 failed, 67 passed in 62.59s (0:01:02)`
- S7 the line diff replaced by a set membership test: caught by `test_r087_a_duplicate_added_line_counts_however_git_shows_the_file[info-nodiff]`. `2 failed, 66 passed in 62.87s (0:01:02)`
- S8 the `index` id equality check removed: not caught. Every index line in the tests already matches the raw record. A case that would catch it would present a full index id that is not the record's and expect exit 2, `the patch and the file list disagree`.
- S9 the id length check removed: not caught. `--full-index` and `--no-abbrev` already emit full ids, so a missing length check still parses them. A case that would catch it would present a short id and expect exit 2, `the patch cannot be read`.
- S10 the binary count not printed: caught by `test_r087_a_real_binary_is_counted_and_never_read_however_git_shows_it[None]`. `9 failed, 59 passed in 62.56s (0:01:02)`
- S11 `--full-index` dropped: caught by `test_r087_a_clean_range_passes_naming_its_commit_count`. `58 failed, 10 passed in 56.26s`
- S12 the deleted-file added-line check removed: not caught. No test builds a deletion whose patch contains an added line. A case that would catch it would expect exit 2, `the patch cannot be read`, for that patch.
- S13 a type change's addition section not read (the deletion section kept as the record's only section): caught by `test_r087_a_type_change_reads_the_new_entry`. `1 failed, 67 passed in 63.05s (0:01:03)`
- S14 `-c core.quotePath=true` dropped from both `git show` calls: not caught. The default `core.quotePath` is already true, and no test sets it false. A case that would catch it would set `core.quotePath=false` and add a non-ASCII path, which the patch would then hand over as raw bytes.
- Q1 `--no-replace-objects` removed from the runner: caught by `test_r087_a_replaced_commit_is_read_as_the_push_sends_it`. `1 failed, 67 passed in 62.64s (0:01:02)`
- Q2 (`--text` removed) no longer applies: K1 removes `--text`, so the mutant is the program as it stands.
- N5 `log.showSignature` left on: caught by `test_r087_a_commit_s_signature_is_never_read_into_a_hit`. `1 failed, 67 passed in 62.70s (0:01:02)`
- P1 `-c log.showRoot=true` removed: caught by `test_r087_a_root_commit_in_the_range_is_read_whatever_log_show_root_says`. `1 failed, 67 passed in 62.42s (0:01:02)`
- P4 `-c diff.suppressBlankEmpty=false` removed: caught by `test_r087_a_blank_context_line_is_read_whatever_diff_suppress_blank_empty_says`. `1 failed, 67 passed in 62.76s (0:01:02)`
- N6 `--no-relative` dropped from both `git show` calls: caught by `test_r087_the_user_s_diff_settings_neither_hide_nor_misplace_a_hit`. `1 failed, 67 passed in 62.85s (0:01:02)`
- P2 `--ignore-submodules=none` removed from both `git show` calls: caught by `test_r087_a_submodule_hidden_by_the_user_s_setting_is_still_read`. `3 failed, 65 passed in 62.87s (0:01:02)`
- P3 `--submodule=short` removed from both `git show` calls: caught by `test_r087_a_submodule_s_own_diff_is_never_inlined`. `1 failed, 67 passed in 62.73s (0:01:02)`
- N3 a merge record whose status begins with `R` or `C` read as a two-path record: caught by `test_r087_a_merge_where_one_side_renamed_a_file_reads_each_file_by_its_own_position`. `1 failed, 67 passed in 62.46s (0:01:02)`
- N1 a `+++` line read inside a hunk: caught by `test_r087_an_added_line_that_reads_like_a_file_header_is_scanned_in_its_hunk`. `1 failed, 67 passed in 62.38s (0:01:02)`
- M2, M9, M10, M11, N2, N8 and P5: the statements they change were not edited (`if status[:1] in ("A", "R")`, `_parse_hunk_header`, the placement line, the dash-base check, `_path_from_rest`, `_patch_lines`). Not re-run.
- M1, M3, M4, M5, M6, M7, M8, M12, M13, N7, N9 and P6: code unchanged. Not re-run. N4 (the disagreement check removed) stays expected to survive and was not re-run.

## Commands

The counts below belong to commit `9a6e3a554d18174b2fc31d186f825079fa842468`. At step 14 the working tree held uncommitted changes, listed in that step. This report was written after that status.

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
........................................................................ [ 16%]
........................................................................ [ 33%]
.............................s...ss.....sss....................s........ [ 50%]
.......s...............................................s...........s.... [ 67%]
.............s...ss.....sss....................s...............s........ [ 83%]
.......................................s...........s.................    [100%]
=========================== short test summary info ===========================
SKIPPED [10] tests\test_allowlist.py:65: prose, not a runnable command
SKIPPED [10] tests\test_allowlist.py:106: prose, not a runnable command
409 passed, 20 skipped in 178.99s (0:02:58)
```

Exit 0.

### 6. `python -m pytest -p no:cacheprovider -q tests/test_install_check.py tests/test_tests_windowless.py`

```
.........................                                                [100%]
25 passed in 22.65s
```

Exit 0.

### 7. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`

```
bridge-check: version 2026.11.12a (2026-11-18 04:51) at <Workspace>\bridge
bridge-check: 147 OK, 0 STALE, 0 MISSING, 0 EXTRA
RESULT: SOURCES MATCH bridge 2026.11.12a
```

Exit 0. The repository folder in the first line is written `<Workspace>` here.

### 8. `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks`

```
windowless-check: 40 file(s) scanned, 0 FAIL, 0 NOTE
```

Exit 0.

### 9. `git grep -n -I -E --no-index "[A-Za-z]:[/\\]|/Users/|/home/|AppData" -- bridge/cursor-bridge/push-scan.py`

```
```

No output. Exit 1.

### 10. `python -c "open('bridge/cursor-bridge/push-scan.py','rb').read().decode('ascii'); print('ascii ok')"`

```
ascii ok
```

Exit 0.

### 11. `python -c "import difflib; print('difflib ok')"`

```
difflib ok
```

Exit 0.

### 12. `git diff --stat HEAD -- bridge/cursor-bridge/settings.bridge.json`

```
```

No output. Exit 0.

### 13. `git diff HEAD -- bridge/cursor-bridge/push-scan.py`

```
warning: in the working copy of 'bridge/cursor-bridge/push-scan.py', LF will be replaced by CRLF the next time Git touches it
diff --git a/bridge/cursor-bridge/push-scan.py b/bridge/cursor-bridge/push-scan.py
index 9c679be..4ed68bc 100644
--- a/bridge/cursor-bridge/push-scan.py
+++ b/bridge/cursor-bridge/push-scan.py
@@ -18,6 +18,7 @@ Exit 0 when the range is clean, 1 when any place holds a hit, 2 when the
 range, git or the names file cannot be read.
 """
 import argparse
+import difflib
 import os
 import re
 import subprocess
@@ -47,14 +48,19 @@ def say(line):
     sys.stdout.buffer.flush()
 
 
-def git(sub, args):
-    argv = ["git", "--no-pager", "--no-replace-objects", "-c", "color.ui=never", "-c", "log.showSignature=false", "-c", "log.showRoot=true", "-c", "diff.suppressBlankEmpty=false", sub] + list(args)
+def git(sub, args, options=None, feed=None):
+    argv = ["git", "--no-pager", "--no-replace-objects", "-c", "color.ui=never", "-c", "log.showSignature=false", "-c", "log.showRoot=true", "-c", "diff.suppressBlankEmpty=false"]
+    if options:
+        argv.extend(options)
+    argv.append(sub)
+    argv.extend(args)
     try:
         proc = subprocess.run(
             argv,
             capture_output=True,
             timeout=bridge_env.GIT_TIMEOUT,
             creationflags=bridge_env.NO_WINDOW,
+            input=feed,
         )
     except FileNotFoundError:
         raise ScanError("git cannot be started")
@@ -360,7 +366,7 @@ def unquote_git(token):
             raw.append(value)
         else:
             raw.extend(esc.encode("utf-8"))
-    return raw.decode("utf-8", errors="replace")
+    return raw.decode("utf-8", errors="surrogateescape")
 
 
 def strip_side(path, side):
@@ -455,7 +461,102 @@ def _parse_hunk_header(header):
     return len(old_counts), new_start, new_count, old_counts
 
 
-def added_lines(text):
+def _blank_section():
+    return {
+        "path": None,
+        "header": None,
+        "pre_ids": None,
+        "result_id": None,
+        "has_hunks": False,
+        "has_binary": False,
+        "added": [],
+    }
+
+
+def _take_quoted(text):
+    if not text.startswith('"'):
+        raise ScanError("the patch cannot be read")
+    index = 1
+    while index < len(text):
+        if text[index] == "\\":
+            if index + 1 >= len(text):
+                break
+            index += 2
+            continue
+        if text[index] == '"':
+            return text[:index + 1], text[index + 1:]
+        index += 1
+    raise ScanError("the patch cannot be read")
+
+
+def _diff_git_path(rest):
+    """The path of a ``diff --git`` header whose two sides name one file."""
+    if rest.startswith('"'):
+        left_tok, after = _take_quoted(rest)
+        if not after.startswith(" "):
+            raise ScanError("the patch cannot be read")
+        right_tok, tail = _take_quoted(after[1:])
+        if tail:
+            raise ScanError("the patch cannot be read")
+        left = strip_side(unquote_git(left_tok), "a")
+        right = strip_side(unquote_git(right_tok), "b")
+        if left != right:
+            raise ScanError("the patch cannot be read")
+        return left
+    found = None
+    start = 0
+    while True:
+        at = rest.find(" b/", start)
+        if at < 0:
+            break
+        left = rest[:at]
+        right = rest[at + 1:]
+        if left.startswith("a/") and right.startswith("b/") and left[2:] == right[2:]:
+            path = left[2:]
+            if found is not None and found != path:
+                raise ScanError("the patch cannot be read")
+            found = path
+        start = at + 1
+    if found is None:
+        raise ScanError("the patch cannot be read")
+    return found
+
+
+def _parse_index_line(line, hash_len):
+    rest = line[len("index "):]
+    parts = rest.split(" ")
+    if not parts or not parts[0] or len(parts) > 2:
+        raise ScanError("the patch cannot be read")
+    if len(parts) == 2 and not _is_mode(parts[1]):
+        raise ScanError("the patch cannot be read")
+    token = parts[0]
+    halves = token.split("..")
+    if len(halves) != 2 or not halves[1]:
+        raise ScanError("the patch cannot be read")
+    pre = halves[0].split(",") if halves[0] else []
+    if not pre:
+        raise ScanError("the patch cannot be read")
+    for oid in pre:
+        if not _is_oid(oid, hash_len):
+            raise ScanError("the patch cannot be read")
+    if not _is_oid(halves[1], hash_len):
+        raise ScanError("the patch cannot be read")
+    return pre, halves[1]
+
+
+def _finish_section(section):
+    if section is None:
+        return None
+    if section["path"] is None and section["header"] is not None:
+        section["path"] = _diff_git_path(section["header"])
+    if section["path"] is None and (section["has_hunks"] or section["has_binary"] or section["added"]):
+        raise ScanError("the patch cannot be read")
+    if section["path"] is None:
+        return None
+    return section
+
+
+def added_lines(text, hash_len):
     """Added lines of a patch, and every new path the patch names.
 
     Each added line is (new path, line number in the new file, text).
@@ -463,6 +564,8 @@ def added_lines(text):
     """
     found = []
     named = []
+    sections = []
+    section = None
     new_path = None
     in_hunk = False
     new_line = 1
@@ -472,13 +575,21 @@ def added_lines(text):
     for line in _patch_lines(text):
         if line.startswith("diff "):
             in_hunk = False
+            finished = _finish_section(section)
+            if finished is not None:
+                sections.append(finished)
+            section = _blank_section()
             new_path = None
             if line.startswith("diff --cc "):
                 new_path = _path_from_rest(line[len("diff --cc "):], False)
                 named.append(new_path)
+                section["path"] = new_path
             elif line.startswith("diff --combined "):
                 new_path = _path_from_rest(line[len("diff --combined "):], False)
                 named.append(new_path)
+                section["path"] = new_path
+            elif line.startswith("diff --git "):
+                section["header"] = line[len("diff --git "):]
             continue
         if in_hunk:
             if line.startswith("\\"):
@@ -505,6 +616,8 @@ def added_lines(text):
                     if new_path is None:
                         raise ScanError("the patch cannot be read")
                     found.append((new_path, new_line, line[n_cols:]))
+                    if section is not None:
+                        section["added"].append((new_line, line[n_cols:]))
                 new_line += 1
             else:
                 if "+" in prefix:
@@ -522,6 +635,8 @@ def added_lines(text):
         if line.startswith("rename to "):
             new_path = _path_from_rest(line[len("rename to "):], False)
             named.append(new_path)
+            if section is not None:
+                section["path"] = new_path
             continue
         if line.startswith("+++ "):
             path = _path_from_rest(line[len("+++ "):], True)
@@ -530,47 +645,122 @@ def added_lines(text):
             else:
                 new_path = path
                 named.append(new_path)
+                if section is not None:
+                    section["path"] = new_path
+            continue
+        if line.startswith("index ") and section is not None:
+            if section["pre_ids"] is not None:
+                raise ScanError("the patch cannot be read")
+            section["pre_ids"], section["result_id"] = _parse_index_line(line, hash_len)
+            continue
+        if line.startswith("Binary files ") and section is not None:
+            section["has_binary"] = True
             continue
         if line.startswith("@@"):
             n_cols, new_line, remain_new, remain_old = _parse_hunk_header(line)
             in_hunk = remain_new != 0 or any(count != 0 for count in remain_old)
+            if section is not None:
+                section["has_hunks"] = True
             continue
     if in_hunk:
         raise ScanError("the patch cannot be read")
-    return found, named
+    finished = _finish_section(section)
+    if finished is not None:
+        sections.append(finished)
+    return found, named, sections
 
 
-def _two_path_status(status):
-    if len(status) < 2 or status[0] not in ("R", "C"):
+def _is_oid(text, size):
+    if len(text) != size:
         return False
-    for ch in status[1:]:
-        if ch < "0" or ch > "9":
+    for ch in text:
+        if ch not in "0123456789abcdef":
+            return False
+    return True
+
+
+def _is_mode(text):
+    if len(text) != 6:
+        return False
+    for ch in text:
+        if ch < "0" or ch > "7":
             return False
+    int(text, 8)
     return True
 
 
-def parse_name_status(raw):
+def _ordinary_two_paths(status):
+    """False for one path, True for a rename or copy score, None when the status is not allowed."""
+    if status in ("A", "D", "M", "T"):
+        return False
+    if status[:1] in ("R", "C") and 2 <= len(status) <= 4 and _whole_digits(status[1:]):
+        int(status[1:], 10)
+        return True
+    return None
+
+
+def parse_raw_records(raw, n_parents, hash_len):
+    """One record per path from ``git show -z --raw --no-abbrev``."""
+    merge = n_parents > 1
+    colons_needed = n_parents if merge else 1
+    slots = colons_needed + 1
     parts = raw.split(b"\0")
     if parts and parts[-1] == b"":
         parts.pop()
     records = []
+    seen = set()
     index = 0
     while index < len(parts):
-        status = parts[index].decode("utf-8", errors="replace")
+        head = parts[index]
         index += 1
-        if not status:
-            continue
-        if _two_path_status(status) and index + 1 < len(parts):
-            index += 1  # the old path
-            new = parts[index].decode("utf-8", errors="replace")
-            index += 1
-            records.append((status, new))
-            continue
+        try:
+            text = head.decode("ascii")
+        except UnicodeDecodeError:
+            raise ScanError("the patch cannot be read")
+        colon = 0
+        while colon < len(text) and text[colon] == ":":
+            colon += 1
+        if colon != colons_needed or colon == len(text):
+            raise ScanError("the patch cannot be read")
+        fields = text[colon:].split(" ")
+        if len(fields) != slots * 2 + 1 or "" in fields:
+            raise ScanError("the patch cannot be read")
+        modes = fields[:slots]
+        oids = fields[slots:slots * 2]
+        status = fields[-1]
+        for mode in modes:
+            if not _is_mode(mode):
+                raise ScanError("the patch cannot be read")
+        for oid in oids:
+            if not _is_oid(oid, hash_len):
+                raise ScanError("the patch cannot be read")
+        if merge:
+            if len(status) != n_parents:
+                raise ScanError("the patch cannot be read")
+            for ch in status:
+                if ch not in "ADMTRC":
+                    raise ScanError("the patch cannot be read")
+            two = False
+        else:
+            two = _ordinary_two_paths(status)
+            if two is None:
+                raise ScanError("the patch cannot be read")
         if index >= len(parts):
-            break
-        path = parts[index].decode("utf-8", errors="replace")
+            raise ScanError("the patch cannot be read")
+        first = parts[index]
         index += 1
-        records.append((status, path))
+        if two:
+            if index >= len(parts):
+                raise ScanError("the patch cannot be read")
+            new_raw = parts[index]
+            index += 1
+        else:
+            new_raw = first
+        path = new_raw.decode("utf-8", "surrogateescape")
+        if path in seen:
+            raise ScanError("the patch cannot be read")
+        seen.add(path)
+        records.append({"status": status, "path": path, "modes": modes, "ids": oids})
     return records
 
 
@@ -617,33 +807,267 @@ def quote_path(path):
     return "".join(parts)
 
 
-def scan_commit(full, names, cfg_name, cfg_email):
+_LINE_DIFF_MAX = 1024 * 1024
+
+
+def _parent_count(text):
+    count = 0
+    for line in text.split("\n"):
+        if line.endswith("\r"):
+            line = line[:-1]
+        if line == "":
+            break
+        if line.startswith("parent "):
+            count += 1
+    return count
+
+
+def _one_line(out, failed):
+    text = out.decode("utf-8", "replace")
+    lines = []
+    for line in text.split("\n"):
+        if line.endswith("\r"):
+            line = line[:-1]
+        if line != "":
+            lines.append(line)
+    if len(lines) != 1:
+        raise ScanError(failed)
+    return lines[0]
+
+
+def repository_ids():
+    """The empty tree's id and the repository's hash length, once per run."""
+    code, out = git("rev-parse", ["--show-object-format"])
+    if code != 0:
+        raise ScanError("git rev-parse failed (exit %d)" % code)
+    kind = _one_line(out, "the patch cannot be read")
+    if kind == "sha1":
+        hash_len = 40
+    elif kind == "sha256":
+        hash_len = 64
+    else:
+        raise ScanError("the patch cannot be read")
+    code, out = git("hash-object", ["-t", "tree", "--stdin"], feed=b"")
+    if code != 0:
+        raise ScanError("git hash-object failed (exit %d)" % code)
+    empty = _one_line(out, "the patch cannot be read")
+    if not _is_oid(empty, hash_len):
+        raise ScanError("the patch cannot be read")
+    return empty, hash_len
+
+
+def _read_blob(oid):
+    code, out = git("cat-file", ["blob", "--end-of-options", oid])
+    if code != 0:
+        raise ScanError("git cat-file failed (exit %d)" % code)
+    return out
+
+
+def classify_blob(data):
+    """``utf-16``, ``binary`` or ``text`` from the blob's own bytes."""
+    if data.startswith(b"\xff\xfe") or data.startswith(b"\xfe\xff"):
+        codec = "utf-16-le" if data.startswith(b"\xff\xfe") else "utf-16-be"
+        try:
+            data[2:].decode(codec)
+        except UnicodeDecodeError:
+            pass
+        else:
+            return "utf-16"
+    if b"\x00" in data[:8000]:
+        return "binary"
+    return "text"
+
+
+def _zero_id(oid):
+    for ch in oid:
+        if ch != "0":
+            return False
+    return True
+
+
+def _blob_text_lines(data, kind):
+    if len(data) > _LINE_DIFF_MAX:
+        raise ScanError("a file too large to compare")
+    if kind == "utf-16":
+        codec = "utf-16-le" if data.startswith(b"\xff\xfe") else "utf-16-be"
+        try:
+            text = data[2:].decode(codec)
+        except UnicodeDecodeError:
+            raise ScanError("the patch cannot be read")
+    else:
+        text = data.decode("utf-8", "replace")
+    return _patch_lines(text)
+
+
+def _preimage_lines(oid, mode):
+    if _zero_id(oid) or mode == "160000":
+        return []
+    data = _read_blob(oid)
+    kind = classify_blob(data)
+    if kind == "binary":
+        return []
+    return _blob_text_lines(data, kind)
+
+
+def _added_positions(pre_lines, result_lines):
+    matcher = difflib.SequenceMatcher(None, pre_lines, result_lines, autojunk=False)
+    positions = set()
+    for tag, _i1, _i2, j1, j2 in matcher.get_opcodes():
+        if tag == "insert" or tag == "replace":
+            for at in range(j1, j2):
+                positions.add(at)
+    return positions
+
+
+def line_diff_added(record, result_data, result_kind):
+    """Result lines added against every preimage, as (1-based line, text)."""
+    result_lines = _blob_text_lines(result_data, result_kind)
+    common = None
+    for oid, mode in zip(record["ids"][:-1], record["modes"][:-1]):
+        positions = _added_positions(_preimage_lines(oid, mode), result_lines)
+        if common is None:
+            common = positions
+        else:
+            common = common & positions
+    if common is None:
+        common = set(range(len(result_lines)))
+    found = []
+    for at in sorted(common):
+        found.append((at + 1, result_lines[at]))
+    return found
+
+
+def _needs_index(section):
+    return section["has_hunks"] or section["has_binary"]
+
+
+def _match_index(section, pre_ids, result_id):
+    if section["pre_ids"] is None or section["result_id"] is None:
+        raise ScanError("the patch and the file list disagree")
+    if section["pre_ids"] != list(pre_ids) or section["result_id"] != result_id:
+        raise ScanError("the patch and the file list disagree")
+
+
+def _type_change_addition(record, sections):
+    if len(sections) != 2:
+        raise ScanError("the patch and the file list disagree")
+    zero = "0" * len(record["ids"][-1])
+    deletion = None
+    addition = None
+    for section in sections:
+        if section["result_id"] == zero:
+            if deletion is not None:
+                raise ScanError("the patch and the file list disagree")
+            deletion = section
+        elif section["pre_ids"] == [zero]:
+            if addition is not None:
+                raise ScanError("the patch and the file list disagree")
+            addition = section
+        else:
+            raise ScanError("the patch and the file list disagree")
+    if deletion is None or addition is None:
+        raise ScanError("the patch and the file list disagree")
+    if deletion["added"]:
+        raise ScanError("the patch cannot be read")
+    if deletion["pre_ids"] != record["ids"][:-1]:
+        raise ScanError("the patch and the file list disagree")
+    if addition["result_id"] != record["ids"][-1]:
+        raise ScanError("the patch and the file list disagree")
+    return addition
+
+
+def _by_class(record, section):
+    data = _read_blob(record["ids"][-1])
+    kind = classify_blob(data)
+    if kind == "binary":
+        return [], 1
+    if kind == "text" and section is not None and section["has_hunks"]:
+        return list(section["added"]), 0
+    for pre in record["ids"][:-1]:
+        if pre == record["ids"][-1]:
+            return [], 0
+    return line_diff_added(record, data, kind), 0
+
+
+def _lines_for_record(record, sections):
+    if record["status"] == "T":
+        addition = _type_change_addition(record, sections)
+        return _by_class(record, addition)
+    if len(sections) > 1:
+        raise ScanError("the patch cannot be read")
+    section = sections[0] if sections else None
+    result = record["ids"][-1]
+    if _zero_id(result):
+        if section is not None and _needs_index(section):
+            _match_index(section, record["ids"][:-1], result)
+        if section is not None and section["added"]:
+            raise ScanError("the patch cannot be read")
+        return [], 0
+    if record["modes"][-1] == "160000":
+        if section is not None and _needs_index(section):
+            _match_index(section, record["ids"][:-1], result)
+        if section is None:
+            return [], 0
+        return list(section["added"]), 0
+    if section is not None and _needs_index(section):
+        _match_index(section, record["ids"][:-1], result)
+    return _by_class(record, section)
+
+
+def _content_by_path(records, sections):
+    grouped = {}
+    known = set()
+    for record in records:
+        known.add(record["path"])
+        grouped.setdefault(record["path"], [])
+    for section in sections:
+        if section["path"] not in known:
+            raise ScanError("the patch and the file list disagree")
+        grouped[section["path"]].append(section)
+    lines_by_path = {}
+    binary_count = 0
+    for record in records:
+        lines, binary = _lines_for_record(record, grouped[record["path"]])
+        lines_by_path[record["path"]] = lines
+        binary_count += binary
+    return lines_by_path, binary_count
+
+
+def scan_commit(full, names, cfg_name, cfg_email, empty_tree, hash_len):
     short = _checked_short(git_need("rev-parse", ["--short", "--end-of-options", full]))
     code, commit_text = git_text("cat-file", ["-p", "--end-of-options", full])
     if code != 0:
         raise ScanError("git cat-file failed (exit %d)" % code)
     author, committer, message = parse_commit(commit_text)
+    show_options = [
+        "--attr-source=" + empty_tree,
+        "-c", "core.attributesFile=",
+        "-c", "core.quotePath=true",
+    ]
     code, status_raw = git(
         "show",
-        ["-z", "--name-status", "-M", "--format=", "--no-ext-diff", "--no-textconv",
-         "--no-color", "--no-relative", "--src-prefix=a/", "--dst-prefix=b/",
+        ["-z", "--raw", "--no-abbrev", "-M", "--format=", "--no-ext-diff", "--no-textconv",
+         "--no-color", "--no-relative",
          "--ignore-submodules=none", "--submodule=short",
          "--end-of-options", full],
+        options=show_options,
     )
     if code != 0:
         raise ScanError("git show failed (exit %d)" % code)
-    patch = git_need(
+    code, patch_raw = git(
         "show",
-        ["-M", "--format=", "--no-ext-diff", "--no-textconv", "--text", "--no-color",
-         "--no-relative", "--src-prefix=a/", "--dst-prefix=b/",
+        ["--cc", "--full-index", "-M", "--format=", "--no-ext-diff", "--no-textconv",
+         "--no-color", "--no-relative", "--src-prefix=a/", "--dst-prefix=b/",
          "--ignore-submodules=none", "--submodule=short",
          "--end-of-options", full],
+        options=show_options,
     )
-    records = parse_name_status(status_raw)
-    found, named_paths = added_lines(patch)
-    lines_by_path = {}
-    for path, number, content in found:
-        lines_by_path.setdefault(path, []).append((number, content))
+    if code != 0:
+        raise ScanError("git show failed (exit %d)" % code)
+    patch = patch_raw.decode("utf-8", "replace")
+    records = parse_raw_records(status_raw, _parent_count(commit_text), hash_len)
+    _found, named_paths, sections = added_lines(patch, hash_len)
+    lines_by_path, binary_count = _content_by_path(records, sections)
     hits = []
     for kind in kinds_of(message, names):
         hits.append(hit_line(short, "message", kind))
@@ -654,7 +1078,9 @@ def scan_commit(full, names, cfg_name, cfg_email):
         for kind in kinds_of_parts(committer, names):
             hits.append(hit_line(short, "committer", kind))
     seen = set()
-    for position, (status, path) in enumerate(records, start=1):
+    for position, record in enumerate(records, start=1):
+        status = record["status"]
+        path = record["path"]
         seen.add(path)
         hidden = bool(kinds_of(path, names) or kinds_of(quote_path(path), names))
         if status[:1] in ("A", "R"):
@@ -670,7 +1096,7 @@ def scan_commit(full, names, cfg_name, cfg_email):
     for path in named_paths:
         if path not in seen:
             raise ScanError("the patch and the file list disagree")
-    return short, hits
+    return short, hits, binary_count
 
 
 def default_base():
@@ -709,10 +1135,13 @@ def execute(args):
     names, notes = select_names(ordered, public)
     listed = git_need("rev-list", ["--reverse", "--end-of-options", base + "..HEAD"])
     commits = [line for line in listed.splitlines() if line]
+    empty_tree, hash_len = repository_ids()
     hit_lines = []
     commits_hit = 0
+    binary_total = 0
     for full in commits:
-        _short, hits = scan_commit(full, names, cfg_name, cfg_email)
+        _short, hits, binary_count = scan_commit(full, names, cfg_name, cfg_email, empty_tree, hash_len)
+        binary_total += binary_count
         if hits:
             commits_hit += 1
             hit_lines.extend(hits)
@@ -720,6 +1149,8 @@ def execute(args):
         say(line)
     for line in hit_lines:
         say(line)
+    if binary_total:
+        say("push-scan: note - %d binary file(s) not read" % binary_total)
     count = len(commits)
     if hit_lines:
         say("push-scan: FOUND - %d hit(s) in %d of %d commit(s)" % (len(hit_lines), commits_hit, count))
```

### 14. `git rev-parse HEAD` and `git status --short`

```
9a6e3a554d18174b2fc31d186f825079fa842468
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/push-scan.py
 M docs/BUILDER_NOTES.md
```

Both commands exited 0. `bridge/cursor-bridge/VERSION` is not listed.

## Assumed, not verified

- An unquoted `diff --git` header that holds a space is split at the ` b/` where the two sides are equal | with `-c core.quotePath=true` this git quotes that header, so no live patch exercised the unquoted branch | `git show -c core.quotePath=false` of a binary file whose path contains a space, which has no `+++` line.
