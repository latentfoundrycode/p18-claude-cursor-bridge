# TASK-067 round 9 report

## Files changed

- `bridge/cursor-bridge/push-scan.py`
- `bridge/cursor-bridge/MANIFEST.json` (only by `python tools/make-manifest.py`)
- `docs/BUILDER_NOTES.md` (one dated line)
- `handoff/TASK-067-r9-report.md` (this file)

`bridge/cursor-bridge/VERSION` was rewritten by `make-manifest.py` and restored with `git restore`. It is not listed by `git status --short`. `docs/CHANGES.md` and this brief do not disagree.

## Summary

`has_name` now folds the text and each searched name with one helper, NFKC then `str.casefold` then NFKC, and searches that folded name as a whole word in the folded text, using the same lookbehind and lookahead as round 8. The regular-expression case flag is not on that pattern. Nothing else in the program changed.

## P1 and P2

- P1: `_caseless` (lines 133-134) returns `unicodedata.normalize("NFKC", unicodedata.normalize("NFKC", text).casefold())`. `has_name` (lines 137-145) skips an empty name, folds the text once, folds each remaining name, and searches the folded text with `(?<![^\W_])` and `(?![^\W_])`.
- P2: the signature `def has_name(text, names):` is unchanged. No reason, output line or note was added. `has_path`, `_segment_start`, `_bound`, `select_names`, `carries_identity`, `deduped_names` and the disagreement check are not in the diff.

## Diff against round 8

Step 12 is one hunk, between the end of `has_path` and `kinds_of`: the new helper, one fold of the text, a fold of the name inside the existing pattern, and the search of the folded text. The body of `has_name` no longer passes `re.IGNORECASE`. The hunk is quoted under step 12.

## Mutation self-check

Each mutant was applied to `push-scan.py`, then `python -m pytest -p no:cacheprovider -q --tb=no tests/test_program_push_scan.py` was run from `<Workspace>`, and the file was restored to the bytes from before that mutant. The Done diffs are that restored program. M7 removes the lookaround, which this round's pattern still carries, so it was re-run as the same edit as W6. N7 replaces `has_name` with the round-1 index match on `text.lower()`, and this round rewrites `has_name`, so N7 was re-run. Every other mutant of rounds 1 to 8 changes code this round did not touch (T1-T10, S1-S16, N1-N6, N8, N9, P1-P6, Q1, M1-M6, M8-M13, U1, U2, V1-V5): code unchanged, not re-run. U3 to U5 no longer apply (round 8 removed `_decode_commit`). Q2 no longer applies (round 5 removed `--text`). The round-5 size-bound mutant no longer applies (round 6 removed the bound). N4 and the expect-survive set S8, S9, S12 and S14 were not re-run.

- W1 `str.casefold` replaced by `str.lower` in `_caseless`: caught by `test_r087_a_name_is_found_under_unicode_compatibility_caseless_matching[sharp-s-upper]`.
- W2 the inner NFKC dropped (`_caseless` case-folds the raw string, then normalizes to NFKC): not caught. A case that would catch it is a searched name of at least four characters holding U+1D2C, written in the commit as the ASCII letters that form gives only when NFKC runs before `casefold`; case-folding first leaves a capital A, so the name misses.
- W3 the outer NFKC dropped (`_caseless` normalizes to NFKC, then case-folds, and returns that): not caught. A case that would catch it is a searched name that is the base letters of U+01F0, whose case fold is `j` plus U+030C, while the text holds that one character: the outer NFKC composes the mark back into the character, and without it the mark stays and is not a word character in `re`, so the base letters match as a whole word.
- W4 the name searched as read (only the text folded): caught by `test_r087_a_name_is_found_under_unicode_compatibility_caseless_matching[sharp-s-upper]`.
- W5 the text searched as read (only the name folded): caught by `test_r087_a_name_is_found_under_unicode_compatibility_caseless_matching[sharp-s-upper]`.
- W6 the whole-word lookbehind and lookahead dropped from the pattern: caught by `test_r087_a_name_is_a_whole_word_in_any_letter_case`.
- M7 the lookaround removed from the folded pattern (same edit as W6): caught by `test_r087_a_name_is_a_whole_word_in_any_letter_case`.
- N7 the lower-cased index match restored (`has_name` finds in `text.lower()` and reads the neighbours in `text` at that index): caught by `test_r087_a_name_after_a_letter_that_lowercases_to_two_characters_is_found`.

### W1 output

```
........................................................................ [ 60%]
..........................................FF....                         [100%]
=========================== short test summary info ===========================
FAILED tests/test_program_push_scan.py::test_r087_a_name_is_found_under_unicode_compatibility_caseless_matching[sharp-s-upper]
FAILED tests/test_program_push_scan.py::test_r087_a_name_is_found_under_unicode_compatibility_caseless_matching[sharp-s-lower]
2 failed, 118 passed in 109.82s (0:01:49)
```

Exit 1.

### W2 output

```
........................................................................ [ 60%]
................................................                         [100%]
120 passed in 110.63s (0:01:50)
```

Exit 0.

### W3 output

```
........................................................................ [ 60%]
................................................                         [100%]
120 passed in 109.52s (0:01:49)
```

Exit 0.

### W4 output

```
.......F..F...F.....F...FF.............................................. [ 60%]
..............F...............F.....F.....FFFFF.                         [100%]
=========================== short test summary info ===========================
FAILED tests/test_program_push_scan.py::test_r087_a_path_and_a_name_in_the_message_are_two_hits_at_message
FAILED tests/test_program_push_scan.py::test_r087_a_name_in_another_committer_is_a_hit_at_committer
FAILED tests/test_program_push_scan.py::test_r087_a_name_is_a_whole_word_in_any_letter_case
FAILED tests/test_program_push_scan.py::test_r087_owner_2026_11_18_a_searched_name_equal_to_an_identity_name_is_dropped
FAILED tests/test_program_push_scan.py::test_r087_an_added_line_that_reads_like_a_file_header_is_scanned_in_its_hunk
FAILED tests/test_program_push_scan.py::test_r087_a_changed_file_with_a_space_in_its_name_is_read_by_its_whole_name
FAILED tests/test_program_push_scan.py::test_r087_a_non_ascii_name_in_a_utf16_file_is_read
FAILED tests/test_program_push_scan.py::test_r087_a_non_ascii_name_in_an_ordinary_utf8_message_is_found
FAILED tests/test_program_push_scan.py::test_r087_an_encoding_header_never_hides_a_name_the_utf8_reading_finds
FAILED tests/test_program_push_scan.py::test_r087_a_name_is_found_under_unicode_compatibility_caseless_matching[sharp-s-upper]
FAILED tests/test_program_push_scan.py::test_r087_a_name_is_found_under_unicode_compatibility_caseless_matching[sharp-s-lower]
FAILED tests/test_program_push_scan.py::test_r087_a_name_is_found_under_unicode_compatibility_caseless_matching[fullwidth]
FAILED tests/test_program_push_scan.py::test_r087_a_name_is_found_under_unicode_compatibility_caseless_matching[decomposed-in-text]
FAILED tests/test_program_push_scan.py::test_r087_a_name_is_found_under_unicode_compatibility_caseless_matching[decomposed-in-names-file]
14 failed, 106 passed in 111.22s (0:01:51)
```

Exit 1.

### W5 output

```
.......FF.F...F.....F...FF.............................................. [ 60%]
..............F...............F.....F.....F.FFF.                         [100%]
=========================== short test summary info ===========================
FAILED tests/test_program_push_scan.py::test_r087_a_path_and_a_name_in_the_message_are_two_hits_at_message
FAILED tests/test_program_push_scan.py::test_r087_a_name_in_another_identity_s_author_name_is_a_hit_at_author
FAILED tests/test_program_push_scan.py::test_r087_a_name_in_another_committer_is_a_hit_at_committer
FAILED tests/test_program_push_scan.py::test_r087_a_name_is_a_whole_word_in_any_letter_case
FAILED tests/test_program_push_scan.py::test_r087_owner_2026_11_18_a_searched_name_equal_to_an_identity_name_is_dropped
FAILED tests/test_program_push_scan.py::test_r087_an_added_line_that_reads_like_a_file_header_is_scanned_in_its_hunk
FAILED tests/test_program_push_scan.py::test_r087_a_changed_file_with_a_space_in_its_name_is_read_by_its_whole_name
FAILED tests/test_program_push_scan.py::test_r087_a_non_ascii_name_in_a_utf16_file_is_read
FAILED tests/test_program_push_scan.py::test_r087_a_non_ascii_name_in_an_ordinary_utf8_message_is_found
FAILED tests/test_program_push_scan.py::test_r087_an_encoding_header_never_hides_a_name_the_utf8_reading_finds
FAILED tests/test_program_push_scan.py::test_r087_a_name_is_found_under_unicode_compatibility_caseless_matching[sharp-s-upper]
FAILED tests/test_program_push_scan.py::test_r087_a_name_is_found_under_unicode_compatibility_caseless_matching[fullwidth]
FAILED tests/test_program_push_scan.py::test_r087_a_name_is_found_under_unicode_compatibility_caseless_matching[decomposed-in-text]
FAILED tests/test_program_push_scan.py::test_r087_a_name_is_found_under_unicode_compatibility_caseless_matching[decomposed-in-names-file]
14 failed, 106 passed in 111.81s (0:01:51)
```

Exit 1.

### W6 output

```
..............F......................................................... [ 60%]
...............................................F                         [100%]
=========================== short test summary info ===========================
FAILED tests/test_program_push_scan.py::test_r087_a_name_is_a_whole_word_in_any_letter_case
FAILED tests/test_program_push_scan.py::test_r087_a_folded_name_inside_a_longer_word_is_still_no_hit
2 failed, 118 passed in 113.15s (0:01:53)
```

Exit 1. M7 is this same run.

### N7 output

```
...............................F........................................ [ 60%]
..........................................FFFFF.                         [100%]
=========================== short test summary info ===========================
FAILED tests/test_program_push_scan.py::test_r087_a_name_after_a_letter_that_lowercases_to_two_characters_is_found
FAILED tests/test_program_push_scan.py::test_r087_a_name_is_found_under_unicode_compatibility_caseless_matching[sharp-s-upper]
FAILED tests/test_program_push_scan.py::test_r087_a_name_is_found_under_unicode_compatibility_caseless_matching[sharp-s-lower]
FAILED tests/test_program_push_scan.py::test_r087_a_name_is_found_under_unicode_compatibility_caseless_matching[fullwidth]
FAILED tests/test_program_push_scan.py::test_r087_a_name_is_found_under_unicode_compatibility_caseless_matching[decomposed-in-text]
FAILED tests/test_program_push_scan.py::test_r087_a_name_is_found_under_unicode_compatibility_caseless_matching[decomposed-in-names-file]
6 failed, 114 passed in 111.42s (0:01:51)
```

Exit 1.

## Done commands

Counts below belong to commit `19dc493f0fca0468781d908b360864e55db551bf`. At step 13 the working tree held uncommitted changes. This report was written after that status, so its path is not in the step 13 listing.

1. `git status --short`

```
 M bridge/cursor-bridge/push-scan.py
 M docs/BUILDER_NOTES.md
```

Exit 0.

2. `python tools/dump-cli.py --check`

```
```

Exit 0. No output.

3. `python tools/make-manifest.py`

```
make-manifest: version 2026.11.12a, 147 files hashed, VERSION + MANIFEST.json written
```

Exit 0.

4. `git restore bridge/cursor-bridge/VERSION`

```
```

Exit 0. No output.

5. `python -m pytest -p no:cacheprovider -q -rs --tb=short tests/test_program_push_scan.py tests/test_dump_cli.py tests/test_allowlist.py`

```
........................................................................ [ 14%]
........................................................................ [ 29%]
........................................................................ [ 44%]
.........s...ss.....sss....................s...............s............ [ 59%]
...................................s...........s.................s...ss. [ 74%]
....sss....................s...............s............................ [ 89%]
...................s...........s.................                        [100%]
=========================== short test summary info ===========================
SKIPPED [10] tests\test_allowlist.py:65: prose, not a runnable command
SKIPPED [10] tests\test_allowlist.py:106: prose, not a runnable command
461 passed, 20 skipped in 243.83s (0:04:03)
```

Exit 0.

6. `python -m pytest -p no:cacheprovider -q tests/test_install_check.py tests/test_tests_windowless.py`

```
.........................                                                [100%]
25 passed in 24.31s
```

Exit 0.

7. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`

```
bridge-check: version 2026.11.12a (2026-11-18 16:51) at <Workspace>\bridge
bridge-check: 147 OK, 0 STALE, 0 MISSING, 0 EXTRA
RESULT: SOURCES MATCH bridge 2026.11.12a
```

Exit 0.

8. `git grep -n -I -E --no-index "[A-Za-z]:[/\\]|/Users/|/home/|AppData" -- bridge/cursor-bridge/push-scan.py`

```
```

No output. Exit 1.

9. `python -c "open('bridge/cursor-bridge/push-scan.py','rb').read().decode('ascii'); print('ascii ok')"`

```
ascii ok
```

Exit 0.

10. `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks`

```
windowless-check: 40 file(s) scanned, 0 FAIL, 0 NOTE
```

Exit 0.

11. `git diff --stat HEAD -- bridge/cursor-bridge/settings.bridge.json`

```
```

No output. Exit 0.

12. `git diff HEAD -- bridge/cursor-bridge/push-scan.py`

```
warning: in the working copy of 'bridge/cursor-bridge/push-scan.py', LF will be replaced by CRLF the next time Git touches it
diff --git a/bridge/cursor-bridge/push-scan.py b/bridge/cursor-bridge/push-scan.py
index 2c7906d..19908a7 100644
--- a/bridge/cursor-bridge/push-scan.py
+++ b/bridge/cursor-bridge/push-scan.py
@@ -130,12 +130,17 @@ def has_path(text):
     return False
 
 
+def _caseless(text):
+    return unicodedata.normalize("NFKC", unicodedata.normalize("NFKC", text).casefold())
+
+
 def has_name(text, names):
+    folded = _caseless(text)
     for name in names:
         if not name:
             continue
-        pattern = re.compile("(?<![^\\W_])" + re.escape(name) + "(?![^\\W_])", re.IGNORECASE)
-        if pattern.search(text):
+        pattern = re.compile("(?<![^\\W_])" + re.escape(_caseless(name)) + "(?![^\\W_])")
+        if pattern.search(folded):
             return True
     return False
 
```

Exit 0.

13. `git rev-parse HEAD` and `git status --short`

```
19dc493f0fca0468781d908b360864e55db551bf
```

Exit 0.

```
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/push-scan.py
 M docs/BUILDER_NOTES.md
```

Exit 0. `bridge/cursor-bridge/VERSION` is not listed.

## Assumed, not verified

- One pass of NFKC, `casefold` and NFKC is idempotent on every string the scan can see | a second pass that changed the folded form would make a name folded once miss a text folded once | apply the helper to its own result and compare, including the five round-9 strings.
- Dropping `re.IGNORECASE` after folding does not lose a match, and leaving it on would not add one, for a folded string longer than one character | the flag was removed so the search is exact on the folded strings; the engine's own fold could still pair two different characters inside an already folded string | search the same folded multi-character pairs with and without the flag. A probe of each code point against its own fold found no difference; strings longer than that one character were not compared.
- `str.casefold` and `unicodedata` use this interpreter's Unicode tables | another Unicode version can fold a character the five cases do not use, so the same source can disagree across interpreters | read `unicodedata.unidata_version` and repeat the five cases, a modifier letter such as U+1D2C, and a character whose case fold is a base letter plus a combining mark, on the other interpreter.
