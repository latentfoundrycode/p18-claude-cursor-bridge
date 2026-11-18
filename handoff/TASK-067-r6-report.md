# TASK-067 round 6 report

## Files changed

- `bridge/cursor-bridge/push-scan.py`
- `bridge/cursor-bridge/MANIFEST.json` (only by `python tools/make-manifest.py`)
- `docs/BUILDER_NOTES.md` (one dated line)
- `handoff/TASK-067-r6-report.md` (this file)

`bridge/cursor-bridge/VERSION` was rewritten by `make-manifest.py` and restored with `git restore`. It reads `2026.11.12a` and is not listed by `git status --short`. `docs/CHANGES.md` and this brief do not disagree.

## Summary

A marked blob is never counted as binary and is read by the line diff in two views, its bytes with every NUL removed and UTF-16 in the mark's byte order, with one hit per line number; a merge record git lists with no section is not read, a single-parent record with no section is refused, a mode `160000` result is handled before any blob read, and the line diff trims common ends and over-reads past a line-pair bound instead of refusing on size.

## L1 to L5 and L7

- L1: `classify_blob` (line 863) returns `marked` when the bytes begin with `FF FE` or `FE FF`, before the NUL test, so a marked blob is never `binary`. `_blob_views` (line 888) builds the NUL-removed view (`_blob_text_lines` of the bytes with every `0x00` removed, UTF-8 with replacement) and the UTF-16 view (from offset 2, the mark's byte order, `errors="replace"`). `line_diff_added` (line 961) diffs each result view against the same view of each preimage; `_lines_of` (line 900) uses an unmarked text preimage's bytes for a view it does not have, and `_preimage_lines` (line 909) contributes no line for a binary, an all-zero id or mode `160000`. `_by_class` (line 1040) still reads hunks only when the kind is `text`. The same result line number is one entry (lines 984-992), the views' texts joined by `\n` where they differ.
- L2: `_lines_for_record` (lines 1079-1082) returns nothing for a merge record (`len(record["ids"]) > 2`) with no section, and raises `the patch and the file list disagree` for a single-parent record with no section, after the mode `160000` check (line 1064) and the deleted-result check (line 1073). A section with no hunk whose result id differs from every preimage still takes the line diff in `_by_class`. The `Binary files` wording is not read.
- L3: `_lines_for_record` (line 1064) handles a result of mode `160000` first, through `_gitlink_lines` (line 1048), before any blob read. For status `T` the two-section check in `_type_change_addition` stays and the addition's lines are returned unclassified. Any other status reads the one section's added lines, or nothing when git printed no section. A gitlink preimage contributes no line (`_preimage_lines`, line 909). Mode `120000` is still classified and read.
- L4: the run's total is a per-run one-element list, `work = [0]` in `execute` (line 1213), passed through `scan_commit` (signature line 1107, call line 1215), `_content_by_path` (call line 1141), `_lines_for_record`, `_by_class` and `line_diff_added` into `_added_positions` (line 945) and `_over_read` (line 936). `_trim_ends` (line 916) drops the common leading lines and the common trailing lines one to one. A trimmed middle whose product exceeds `1000000`, or whose product would take the run's total past `10000000`, counts every line of the result middle as added and adds nothing to the total. `_LINE_DIFF_MAX` and `a file too large to compare` are gone.
- L5: the closed list of reasons is again round 2's: `not inside a git repository`, `the base must not begin with "-"`, `origin/HEAD is not set; name the base, e.g. origin/main`, `the base is not a commit here`, `the names file cannot be read`, `git cannot be started`, `git <subcommand> failed (exit <code>)`, `git <subcommand> took longer than <GIT_TIMEOUT>s`, `the patch and the file list disagree`, `internal error`, `the patch cannot be read`. No reason was added. The disagreement check (lines 1166-1169), the note, `quote_path`, the short hash, the hit format and the exits are unchanged. K5's same-id rule still returns nothing before the line diff (`_by_class`, lines 1042-1044).
- L7: the module docstring and `build_parser` are not in the diff. `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` were not edited. `python tools/dump-cli.py --check` exits 0.

## Mutation self-check

Each mutant was applied to `push-scan.py`, then `python -m pytest -p no:cacheprovider -q --tb=no tests/test_program_push_scan.py` was run from `<Workspace>`, and the file was restored to the bytes from before that mutant. `RESTORED True` after the last one.

- T1 the NUL-removed view dropped (the UTF-16 view only): caught by `test_r087_a_byte_order_mark_before_plain_text_never_hides_its_lines[]`. `5 failed, 82 passed in 82.44s (0:01:22)`
- T2 the UTF-16 view dropped (the NUL-removed view only): caught by `test_r087_a_non_ascii_name_in_a_utf16_file_is_read`. `1 failed, 86 passed in 82.63s (0:01:22)`
- T3 a marked blob classified binary when it holds a `0x00` byte (round 5's rule back): caught by `test_r087_a_utf16_file_with_a_byte_order_mark_is_read_as_text[\xff\xfe-utf-16-le]`. `11 failed, 76 passed in 82.82s (0:01:22)`
- T4 the hits of both views not deduped: caught by `test_r087_a_utf16_file_with_a_byte_order_mark_is_read_as_text[\xff\xfe-utf-16-le]`. `5 failed, 82 passed in 83.67s (0:01:23)`
- T5 a merge record with no section takes the line diff (round 5's rule): not caught. A clean merge's intersection is empty and its trimmed middles stay under the pair bound, so the line diff and reading nothing print the same OK. A case that would catch it is a merge git lists with no section whose trimmed middles are large enough to over-read and whose result still holds a path one parent already has inside that middle.
- T6 the single-parent no-section check removed: not caught. No case builds a single-parent record with no patch section. A case that would catch it expects exit 2 and `the patch and the file list disagree` for that record.
- T7 the `160000` check moved after the `T` branch (round 5's order): caught by `test_r087_type_changes_to_and_from_a_submodule_are_read`. `3 failed, 84 passed in 82.42s (0:01:22)`
- T8 the trimming removed: caught by `test_r087_a_far_edit_of_a_large_repetitive_file_does_not_read_an_old_line`. `1 failed, 86 passed in 84.34s (0:01:24)`
- T9 the over-read replaced by running the matcher anyway: caught by `test_r087_a_middle_too_costly_to_diff_is_read_whole` (the run waited out that test's timeout). `1 failed, 86 passed in 383.51s (0:06:23)`
- T10 the intersection over preimages replaced by a union: caught by `test_r087_a_duplicate_line_a_merge_adds_against_both_parents_counts`. `1 failed, 86 passed in 83.42s (0:01:23)`
- S3 the classification skipped (every result treated as text): caught by `test_r087_a_real_binary_is_counted_and_never_read_however_git_shows_it[None]`. `16 failed, 71 passed in 83.51s (0:01:23)`
- S5 the UTF-16 branch removed (a marked blob falls to the NUL rule): caught by `test_r087_a_utf16_file_with_a_byte_order_mark_is_read_as_text[\xff\xfe-utf-16-le]`. `11 failed, 76 passed in 83.17s (0:01:23)`
- S6 the line diff's intersection replaced by a union: caught by `test_r087_a_duplicate_line_a_merge_adds_against_both_parents_counts`. `1 failed, 86 passed in 83.37s (0:01:23)`
- S7 the line diff replaced by a set membership test: caught by `test_r087_a_duplicate_added_line_counts_however_git_shows_the_file[info-nodiff]`. `2 failed, 85 passed in 83.22s (0:01:23)`
- S13 a type change's addition section not read (its deletion section kept): caught by `test_r087_a_type_change_reads_the_new_entry`. `2 failed, 85 passed in 83.43s (0:01:23)`
- S16 the binary branch of `_by_class` made never taken: caught by `test_r087_a_real_binary_is_counted_and_never_read_however_git_shows_it[None]`. `9 failed, 78 passed in 82.32s (0:01:22)`
- N1 a `+++` line read inside a hunk: code unchanged. Not re-run.
- N3 a combined status read with two paths: code unchanged. Not re-run.
- N5 `log.showSignature` left on: code unchanged. Not re-run.
- N6 `--no-relative` dropped from both `git show` calls: code unchanged. Not re-run.
- P1 `-c log.showRoot=true` removed from the runner: code unchanged. Not re-run.
- P2 `--ignore-submodules=none` removed from both `git show` calls: code unchanged. Not re-run.
- P3 `--submodule=short` removed from both `git show` calls: code unchanged. Not re-run.
- P4 `-c diff.suppressBlankEmpty=false` removed from the runner: code unchanged. Not re-run.
- Q1 `--no-replace-objects` removed from the runner: code unchanged. Not re-run.
- M1-M13, N2, N7-N9, P5, P6, S1, S2, S4, S10 and S11: code unchanged. Not re-run.
- Q2 (`--text` removed) no longer applies: round 5 removed `--text`.
- r15 (the 1 MiB size bound dropped) no longer applies: L4 removes the bound, so the program as it stands is that change.
- N4 (the disagreement check removed) and the expect-survive set S8, S9, S12 and S14 stay expected to survive and were not re-run.

## Commands

The counts below belong to commit `5ae7abb397844cf3b601cd04b82caac04ac4b1a4`. At step 15 the working tree held uncommitted changes, listed in that step. This report was written after that status, so it is not in that listing.

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

### 5. `python -m pytest -p no:cacheprovider -q -rs --tb=short --durations=5 tests/test_program_push_scan.py tests/test_dump_cli.py tests/test_allowlist.py`

```
........................................................................ [ 16%]
........................................................................ [ 32%]
................................................s...ss.....sss.......... [ 48%]
..........s...............s............................................. [ 64%]
..s...........s.................s...ss.....sss....................s..... [ 80%]
..........s...............................................s...........s. [ 96%]
................                                                         [100%]
============================= slowest 5 durations =============================
3.44s call     tests/test_program_push_scan.py::test_r087_entries_without_content_to_read_never_end_the_scan
2.86s call     tests/test_dump_cli.py::test_cfgb3b_r4_an_option_string_or_dest_holding_a_path_is_refused
2.86s call     tests/test_dump_cli.py::test_cfgb3b_r4_a_default_or_choice_that_is_the_program_folder_itself_is_refused
2.83s call     tests/test_dump_cli.py::test_cfgb3b_r3_the_home_folder_in_another_case_is_refused
2.82s call     tests/test_dump_cli.py::test_cfgb3b_r4_a_folder_written_with_doubled_backslashes_is_refused
=========================== short test summary info ===========================
SKIPPED [10] tests\test_allowlist.py:65: prose, not a runnable command
SKIPPED [10] tests\test_allowlist.py:106: prose, not a runnable command
428 passed, 20 skipped in 200.33s (0:03:20)
```

Exit 0. `test_r087_a_middle_too_costly_to_diff_is_read_whole` is not among the five slowest calls; the slowest call is 3.44s.

```
428 passed, 20 skipped in 200.33s (0:03:20)
```

### 6. `python -m pytest -p no:cacheprovider -q tests/test_install_check.py tests/test_tests_windowless.py`

```
.........................                                                [100%]
25 passed in 22.79s
```

Exit 0.

```
25 passed in 22.79s
```

### 7. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`

```
bridge-check: version 2026.11.12a (2026-11-18 06:52) at <Workspace>\bridge
bridge-check: 147 OK, 0 STALE, 0 MISSING, 0 EXTRA
RESULT: SOURCES MATCH bridge 2026.11.12a
```

Exit 0.

### 8. `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks`

```
windowless-check: 40 file(s) scanned, 0 FAIL, 0 NOTE
```

Exit 0.

### 9. `git grep -n -I -E --no-index "[A-Za-z]:[/\\]|/Users/|/home/|AppData" -- bridge/cursor-bridge/push-scan.py`

```
```

Exit 1. The command printed no lines.

### 10. `python -c "open('bridge/cursor-bridge/push-scan.py','rb').read().decode('ascii'); print('ascii ok')"`

```
ascii ok
```

Exit 0.

### 11. `git grep -n -I -E --no-index "_LINE_DIFF_MAX|a file too large to compare" -- bridge/cursor-bridge/push-scan.py`

```
```

Exit 1. The command printed no lines.

### 12. `python -c "import difflib; print('difflib ok')"`

```
difflib ok
```

Exit 0.

### 13. `git diff --stat HEAD -- bridge/cursor-bridge/settings.bridge.json`

```
```

Exit 0. The command printed no lines.

### 14. `git diff HEAD -- bridge/cursor-bridge/push-scan.py`

```
warning: in the working copy of 'bridge/cursor-bridge/push-scan.py', LF will be replaced by CRLF the next time Git touches it
diff --git a/bridge/cursor-bridge/push-scan.py b/bridge/cursor-bridge/push-scan.py
index 4ed68bc..09213a4 100644
--- a/bridge/cursor-bridge/push-scan.py
+++ b/bridge/cursor-bridge/push-scan.py
@@ -807,9 +807,6 @@ def quote_path(path):
     return "".join(parts)
 
 
-_LINE_DIFF_MAX = 1024 * 1024
-
-
 def _parent_count(text):
     count = 0
     for line in text.split("\n"):
@@ -864,15 +861,9 @@ def _read_blob(oid):
 
 
 def classify_blob(data):
-    """``utf-16``, ``binary`` or ``text`` from the blob's own bytes."""
+    """``marked``, ``binary`` or ``text`` from the blob's own bytes."""
     if data.startswith(b"\xff\xfe") or data.startswith(b"\xfe\xff"):
-        codec = "utf-16-le" if data.startswith(b"\xff\xfe") else "utf-16-be"
-        try:
-            data[2:].decode(codec)
-        except UnicodeDecodeError:
-            pass
-        else:
-            return "utf-16"
+        return "marked"
     if b"\x00" in data[:8000]:
         return "binary"
     return "text"
@@ -886,54 +877,119 @@ def _zero_id(oid):
 
 
 def _blob_text_lines(data, kind):
-    if len(data) > _LINE_DIFF_MAX:
-        raise ScanError("a file too large to compare")
     if kind == "utf-16":
         codec = "utf-16-le" if data.startswith(b"\xff\xfe") else "utf-16-be"
-        try:
-            text = data[2:].decode(codec)
-        except UnicodeDecodeError:
-            raise ScanError("the patch cannot be read")
+        text = data[2:].decode(codec, "replace")
     else:
         text = data.decode("utf-8", "replace")
     return _patch_lines(text)
 
 
+def _blob_views(data, kind):
+    """Lines of each view, or ``None`` when the blob contributes no line."""
+    if kind == "binary":
+        return None
+    if kind == "marked":
+        return {
+            "nul": _blob_text_lines(data.replace(b"\x00", b""), "text"),
+            "utf16": _blob_text_lines(data, "utf-16"),
+        }
+    return {"nul": _blob_text_lines(data, "text")}
+
+
+def _lines_of(views, name):
+    if views is None:
+        return []
+    found = views.get(name)
+    if found is None:
+        return views["nul"]
+    return found
+
+
 def _preimage_lines(oid, mode):
     if _zero_id(oid) or mode == "160000":
-        return []
+        return None
     data = _read_blob(oid)
-    kind = classify_blob(data)
-    if kind == "binary":
-        return []
-    return _blob_text_lines(data, kind)
+    return _blob_views(data, classify_blob(data))
+
+
+def _trim_ends(pre_lines, result_lines):
+    """Common leading and trailing lines, one to one, never overlapping."""
+    lead = 0
+    shorter = len(pre_lines)
+    if len(result_lines) < shorter:
+        shorter = len(result_lines)
+    while lead < shorter and pre_lines[lead] == result_lines[lead]:
+        lead += 1
+    trail = 0
+    pre_left = len(pre_lines) - lead
+    result_left = len(result_lines) - lead
+    while (
+        trail < pre_left
+        and trail < result_left
+        and pre_lines[-1 - trail] == result_lines[-1 - trail]
+    ):
+        trail += 1
+    return lead, pre_lines[lead:len(pre_lines) - trail], result_lines[lead:len(result_lines) - trail]
+
+
+def _over_read(pre_count, result_count, work):
+    """True when this pair is past the line-pair bounds. An over-read adds nothing."""
+    product = pre_count * result_count
+    if product > 1000000 or work[0] + product > 10000000:
+        return True
+    work[0] = work[0] + product
+    return False
 
 
-def _added_positions(pre_lines, result_lines):
-    matcher = difflib.SequenceMatcher(None, pre_lines, result_lines, autojunk=False)
+def _added_positions(pre_lines, result_lines, work):
+    lead, pre_middle, result_middle = _trim_ends(pre_lines, result_lines)
+    if _over_read(len(pre_middle), len(result_middle), work):
+        positions = set()
+        for at in range(len(result_middle)):
+            positions.add(lead + at)
+        return positions
+    matcher = difflib.SequenceMatcher(None, pre_middle, result_middle, autojunk=False)
     positions = set()
     for tag, _i1, _i2, j1, j2 in matcher.get_opcodes():
         if tag == "insert" or tag == "replace":
             for at in range(j1, j2):
-                positions.add(at)
+                positions.add(lead + at)
     return positions
 
 
-def line_diff_added(record, result_data, result_kind):
+def line_diff_added(record, result_data, result_kind, work):
     """Result lines added against every preimage, as (1-based line, text)."""
-    result_lines = _blob_text_lines(result_data, result_kind)
-    common = None
+    result_views = _blob_views(result_data, result_kind)
+    if result_kind == "marked":
+        names = ("nul", "utf16")
+    else:
+        names = ("nul",)
+    preimages = []
     for oid, mode in zip(record["ids"][:-1], record["modes"][:-1]):
-        positions = _added_positions(_preimage_lines(oid, mode), result_lines)
+        preimages.append(_preimage_lines(oid, mode))
+    by_number = {}
+    for name in names:
+        result_lines = result_views[name]
+        common = None
+        for views in preimages:
+            positions = _added_positions(_lines_of(views, name), result_lines, work)
+            if common is None:
+                common = positions
+            else:
+                common = common & positions
         if common is None:
-            common = positions
-        else:
-            common = common & positions
-    if common is None:
-        common = set(range(len(result_lines)))
+            common = set(range(len(result_lines)))
+        for at in common:
+            text = result_lines[at]
+            held = by_number.get(at)
+            if held is None:
+                by_number[at] = [text]
+            elif text not in held:
+                held.append(text)
     found = []
-    for at in sorted(common):
-        found.append((at + 1, result_lines[at]))
+    for at in sorted(by_number):
+        found.append((at + 1, "\n".join(by_number[at])))
     return found
 
 
@@ -976,7 +1032,7 @@ def _type_change_addition(record, sections):
     return addition
 
 
-def _by_class(record, section):
+def _by_class(record, section, work):
     data = _read_blob(record["ids"][-1])
     kind = classify_blob(data)
     if kind == "binary":
@@ -986,13 +1042,30 @@ def _by_class(record, section):
     for pre in record["ids"][:-1]:
         if pre == record["ids"][-1]:
             return [], 0
-    return line_diff_added(record, data, kind), 0
+    return line_diff_added(record, data, kind, work), 0
 
 
-def _lines_for_record(record, sections):
+def _gitlink_lines(record, sections):
+    """A mode ``160000`` result, before any blob read, for every status."""
     if record["status"] == "T":
         addition = _type_change_addition(record, sections)
-        return _by_class(record, addition)
+        return list(addition["added"]), 0
+    if len(sections) > 1:
+        raise ScanError("the patch cannot be read")
+    section = sections[0] if sections else None
+    if section is not None and _needs_index(section):
+        _match_index(section, record["ids"][:-1], record["ids"][-1])
+    if section is None:
+        return [], 0
+    return list(section["added"]), 0
+
+
+def _lines_for_record(record, sections, work):
+    if record["modes"][-1] == "160000":
+        return _gitlink_lines(record, sections)
+    if record["status"] == "T":
+        addition = _type_change_addition(record, sections)
+        return _by_class(record, addition, work)
     if len(sections) > 1:
         raise ScanError("the patch cannot be read")
     section = sections[0] if sections else None
@@ -1003,18 +1076,16 @@ def _lines_for_record(record, sections):
         if section is not None and section["added"]:
             raise ScanError("the patch cannot be read")
         return [], 0
-    if record["modes"][-1] == "160000":
-        if section is not None and _needs_index(section):
-            _match_index(section, record["ids"][:-1], result)
-        if section is None:
+    if section is None:
+        if len(record["ids"]) > 2:
             return [], 0
-        return list(section["added"]), 0
-    if section is not None and _needs_index(section):
+        raise ScanError("the patch and the file list disagree")
+    if _needs_index(section):
         _match_index(section, record["ids"][:-1], result)
-    return _by_class(record, section)
+    return _by_class(record, section, work)
 
 
-def _content_by_path(records, sections):
+def _content_by_path(records, sections, work):
     grouped = {}
     known = set()
     for record in records:
@@ -1027,13 +1098,13 @@ def _content_by_path(records, sections):
     lines_by_path = {}
     binary_count = 0
     for record in records:
-        lines, binary = _lines_for_record(record, grouped[record["path"]])
+        lines, binary = _lines_for_record(record, grouped[record["path"]], work)
         lines_by_path[record["path"]] = lines
         binary_count += binary
     return lines_by_path, binary_count
 
 
-def scan_commit(full, names, cfg_name, cfg_email, empty_tree, hash_len):
+def scan_commit(full, names, cfg_name, cfg_email, empty_tree, hash_len, work):
     short = _checked_short(git_need("rev-parse", ["--short", "--end-of-options", full]))
     code, commit_text = git_text("cat-file", ["-p", "--end-of-options", full])
     if code != 0:
@@ -1067,7 +1138,7 @@ def scan_commit(full, names, cfg_name, cfg_email, empty_tree, hash_len):
     patch = patch_raw.decode("utf-8", "replace")
     records = parse_raw_records(status_raw, _parent_count(commit_text), hash_len)
     _found, named_paths, sections = added_lines(patch, hash_len)
-    lines_by_path, binary_count = _content_by_path(records, sections)
+    lines_by_path, binary_count = _content_by_path(records, sections, work)
     hits = []
     for kind in kinds_of(message, names):
         hits.append(hit_line(short, "message", kind))
@@ -1139,8 +1210,9 @@ def execute(args):
     hit_lines = []
     commits_hit = 0
     binary_total = 0
+    work = [0]
     for full in commits:
-        _short, hits, binary_count = scan_commit(full, names, cfg_name, cfg_email, empty_tree, hash_len)
+        _short, hits, binary_count = scan_commit(full, names, cfg_name, cfg_email, empty_tree, hash_len, work)
         binary_total += binary_count
         if hits:
             commits_hit += 1
```

Exit 0. The hunks are the removal of `_LINE_DIFF_MAX`, `classify_blob`, `_blob_text_lines`, the new view, trim and bound helpers, `_preimage_lines`, `_added_positions`, `line_diff_added`, `_by_class`, `_gitlink_lines`, `_lines_for_record`, `_content_by_path`, and the lines of `scan_commit` and `execute` that carry `work`.

### 15. `git rev-parse HEAD` and `git status --short`

```
5ae7abb397844cf3b601cd04b82caac04ac4b1a4
```

Exit 0.

```
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/push-scan.py
 M docs/BUILDER_NOTES.md
```

Exit 0. `bridge/cursor-bridge/VERSION` is not listed.

## Assumed, not verified

- that git prints a patch section for every single-parent record of a changed file | the refusal for a missing section is a false exit 2 if git omits a section for an ordinary edit, and no test builds a single-parent record with no section | a commit whose raw list names a path and whose `--cc` patch has no section for it, and whether an ordinary edit ever looks like that
- that removing every NUL from a marked blob keeps the NUL-removed view's line numbers equal to the UTF-16 view's except where a non-ASCII code unit holds a `0x0A` or `0x0D` byte, such as U+010A | the tests that passed use ASCII text, so they do not show a line split | a marked file whose UTF-16 text contains U+010A before a path, and the hit line numbers it prints
- that `SequenceMatcher` indexes on a trimmed middle map back onto the result by adding the leading trim's length | a one-line edit landing on line 3501 matches that mapping, and the library's opcode indexes were not read apart from that result | a middle whose first opcode is an equal run inside the middle, and the line number the hit prints
