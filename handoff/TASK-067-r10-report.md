# TASK-067 round 10 report

## Files changed

- `bridge/cursor-bridge/push-scan.py`
- `bridge/cursor-bridge/MANIFEST.json` (only by `python tools/make-manifest.py`)
- `docs/BUILDER_NOTES.md` (one dated line)
- `handoff/TASK-067-r10-report.md` (this file)

`bridge/cursor-bridge/VERSION` was rewritten by `make-manifest.py` and restored with `git restore`. It is not listed by `git status --short`. `docs/CHANGES.md` and this brief do not disagree.

## Summary

`has_name` now returns true when either reading finds a non-empty searched name: round 8's whole-word pattern on the text as written with `re.IGNORECASE`, or round 9's whole-word pattern on the text and the name after `_caseless`. An empty name is still skipped. `_caseless` is unchanged. Nothing else in the program changed.

## E1 and E2

- E1: `has_name` (lines 137-146) skips an empty name, searches the text as written with `(?<![^\W_])`, `re.escape(name)`, `(?![^\W_])` and `re.IGNORECASE`, and searches `_caseless(text)` with the same boundaries around `re.escape(_caseless(name))` and no case flag; either match returns true.
- E2: the signature `def has_name(text, names):` is unchanged. No reason, output line or note was added. `_caseless`, `has_path`, `_segment_start`, `_bound`, `select_names`, `carries_identity`, `deduped_names`, the module docstring, `build_parser` and the disagreement check are not in the diff.

## Diff against round 9

Step 12 is one hunk inside `has_name`, between `def has_name(text, names):` and `kinds_of`: one compile of round 8's pattern on the name as read, and the search joined with `or` to round 9's search of the folded text. `_caseless` is not in the diff. The hunk is quoted under step 12.

## Mutation self-check

Each mutant was applied to `push-scan.py`, then `python -m pytest -p no:cacheprovider -q --tb=no tests/test_program_push_scan.py` was run from `<Workspace>`, and the file was restored to the bytes from before that mutant. The twelve runs were one after another in one foreground process, and the final restore compared equal to those bytes. The Done diff is that restored program. Every other mutant of rounds 1 to 9 changes code this round did not touch (T1-T10, S1-S16, N1-N6, N8, N9, P1-P6, Q1, M1-M6, M8-M13, U1, U2, V1-V5): code unchanged, not re-run. U3 to U5 no longer apply (round 8 removed `_decode_commit`). Q2 no longer applies (round 5 removed `--text`). The round-5 size-bound mutant no longer applies (round 6 removed the bound). N4 and the expect-survive set S8, S9, S12 and S14 were not re-run.

- X1 the raw reading dropped (`has_name` keeps only the folded match, as round 9 had it): caught by `test_r087_a_name_beside_a_character_folding_turns_into_letters_is_found`.
- X2 the folded reading dropped (`has_name` keeps only round 8's match): caught by `test_r087_a_name_is_found_under_unicode_compatibility_caseless_matching`.
- X3 `re.IGNORECASE` dropped from the raw reading: caught by `test_r087_a_name_whose_i_is_written_dotted_or_dotless_is_found`.
- X4 the two readings joined with `and` instead of `or`: caught by `test_r087_a_name_is_found_under_unicode_compatibility_caseless_matching`.
- W1 `str.casefold` replaced by `str.lower` in `_caseless`: caught by `test_r087_a_name_is_found_under_unicode_compatibility_caseless_matching`.
- W2 the inner NFKC dropped (`_caseless` case-folds the raw string, then normalizes to NFKC): caught by `test_r087_a_name_holding_a_compatibility_letter_is_found_written_plainly`.
- W3 the outer NFKC dropped (`_caseless` normalizes to NFKC, then case-folds, and returns that): caught by `test_r087_a_name_s_letters_before_another_letter_s_mark_are_no_hit`.
- W4 the name searched as read in the folded reading (only the text folded): caught by `test_r087_a_name_is_found_under_unicode_compatibility_caseless_matching`.
- W5 the text searched as read in the folded reading (only the name folded): caught by `test_r087_a_name_is_found_under_unicode_compatibility_caseless_matching`.
- W6 the whole-word lookbehind and lookahead dropped from the folded reading's pattern: caught by `test_r087_a_name_is_a_whole_word_in_any_letter_case`.
- M7 the lookaround removed from the raw reading's pattern: caught by `test_r087_a_name_is_a_whole_word_in_any_letter_case`.
- N7 the raw reading replaced by the lower-cased index match (find in `text.lower()` and read the neighbours in `text` at that index; the folded reading kept): caught by `test_r087_a_name_whose_i_is_written_dotted_or_dotless_is_found`.

### X1 output

```
........................................................................ [ 54%]
..................................................FFFFFFFF.              [100%]
=========================== short test summary info ===========================
FAILED tests/test_program_push_scan.py::test_r087_a_name_beside_a_character_folding_turns_into_letters_is_found[trade-mark-after]
FAILED tests/test_program_push_scan.py::test_r087_a_name_beside_a_character_folding_turns_into_letters_is_found[numero-before]
FAILED tests/test_program_push_scan.py::test_r087_a_name_beside_a_character_folding_turns_into_letters_is_found[ypogegrammeni-after]
FAILED tests/test_program_push_scan.py::test_r087_a_name_beside_a_character_folding_turns_into_letters_is_found[acute-after]
FAILED tests/test_program_push_scan.py::test_r087_a_name_beside_a_character_folding_turns_into_letters_is_found[circled-a-before]
FAILED tests/test_program_push_scan.py::test_r087_a_name_whose_i_is_written_dotted_or_dotless_is_found[dotted-capital-in-text]
FAILED tests/test_program_push_scan.py::test_r087_a_name_whose_i_is_written_dotted_or_dotless_is_found[dotless-in-text]
FAILED tests/test_program_push_scan.py::test_r087_a_name_whose_i_is_written_dotted_or_dotless_is_found[dotted-capital-in-names-file]
8 failed, 123 passed in 122.43s (0:02:02)
```

Exit 1.

### X2 output

```
........................................................................ [ 54%]
..........................................FFFFF.F.........F              [100%]
=========================== short test summary info ===========================
FAILED tests/test_program_push_scan.py::test_r087_a_name_is_found_under_unicode_compatibility_caseless_matching[sharp-s-upper]
FAILED tests/test_program_push_scan.py::test_r087_a_name_is_found_under_unicode_compatibility_caseless_matching[sharp-s-lower]
FAILED tests/test_program_push_scan.py::test_r087_a_name_is_found_under_unicode_compatibility_caseless_matching[fullwidth]
FAILED tests/test_program_push_scan.py::test_r087_a_name_is_found_under_unicode_compatibility_caseless_matching[decomposed-in-text]
FAILED tests/test_program_push_scan.py::test_r087_a_name_is_found_under_unicode_compatibility_caseless_matching[decomposed-in-names-file]
FAILED tests/test_program_push_scan.py::test_r087_a_name_holding_a_compatibility_letter_is_found_written_plainly
FAILED tests/test_program_push_scan.py::test_r087_a_punctuated_name_in_a_folding_only_spelling_is_found
7 failed, 124 passed in 124.99s (0:02:04)
```

Exit 1.

### X3 output

```
........................................................................ [ 54%]
.......................................................FFF.              [100%]
=========================== short test summary info ===========================
FAILED tests/test_program_push_scan.py::test_r087_a_name_whose_i_is_written_dotted_or_dotless_is_found[dotted-capital-in-text]
FAILED tests/test_program_push_scan.py::test_r087_a_name_whose_i_is_written_dotted_or_dotless_is_found[dotless-in-text]
FAILED tests/test_program_push_scan.py::test_r087_a_name_whose_i_is_written_dotted_or_dotless_is_found[dotted-capital-in-names-file]
3 failed, 128 passed in 123.69s (0:02:03)
```

Exit 1.

### X4 output

```
........................................................................ [ 54%]
..........................................FFFFF.F.FFFFFFFFF              [100%]
=========================== short test summary info ===========================
FAILED tests/test_program_push_scan.py::test_r087_a_name_is_found_under_unicode_compatibility_caseless_matching[sharp-s-upper]
FAILED tests/test_program_push_scan.py::test_r087_a_name_is_found_under_unicode_compatibility_caseless_matching[sharp-s-lower]
FAILED tests/test_program_push_scan.py::test_r087_a_name_is_found_under_unicode_compatibility_caseless_matching[fullwidth]
FAILED tests/test_program_push_scan.py::test_r087_a_name_is_found_under_unicode_compatibility_caseless_matching[decomposed-in-text]
FAILED tests/test_program_push_scan.py::test_r087_a_name_is_found_under_unicode_compatibility_caseless_matching[decomposed-in-names-file]
FAILED tests/test_program_push_scan.py::test_r087_a_name_holding_a_compatibility_letter_is_found_written_plainly
FAILED tests/test_program_push_scan.py::test_r087_a_name_beside_a_character_folding_turns_into_letters_is_found[trade-mark-after]
FAILED tests/test_program_push_scan.py::test_r087_a_name_beside_a_character_folding_turns_into_letters_is_found[numero-before]
FAILED tests/test_program_push_scan.py::test_r087_a_name_beside_a_character_folding_turns_into_letters_is_found[ypogegrammeni-after]
FAILED tests/test_program_push_scan.py::test_r087_a_name_beside_a_character_folding_turns_into_letters_is_found[acute-after]
FAILED tests/test_program_push_scan.py::test_r087_a_name_beside_a_character_folding_turns_into_letters_is_found[circled-a-before]
FAILED tests/test_program_push_scan.py::test_r087_a_name_whose_i_is_written_dotted_or_dotless_is_found[dotted-capital-in-text]
FAILED tests/test_program_push_scan.py::test_r087_a_name_whose_i_is_written_dotted_or_dotless_is_found[dotless-in-text]
FAILED tests/test_program_push_scan.py::test_r087_a_name_whose_i_is_written_dotted_or_dotless_is_found[dotted-capital-in-names-file]
FAILED tests/test_program_push_scan.py::test_r087_a_punctuated_name_in_a_folding_only_spelling_is_found
15 failed, 116 passed in 122.39s (0:02:02)
```

Exit 1.

### W1 output

```
........................................................................ [ 54%]
..........................................FF..............F              [100%]
=========================== short test summary info ===========================
FAILED tests/test_program_push_scan.py::test_r087_a_name_is_found_under_unicode_compatibility_caseless_matching[sharp-s-upper]
FAILED tests/test_program_push_scan.py::test_r087_a_name_is_found_under_unicode_compatibility_caseless_matching[sharp-s-lower]
FAILED tests/test_program_push_scan.py::test_r087_a_punctuated_name_in_a_folding_only_spelling_is_found
3 failed, 128 passed in 122.64s (0:02:02)
```

Exit 1.

### W2 output

```
........................................................................ [ 54%]
................................................F..........              [100%]
=========================== short test summary info ===========================
FAILED tests/test_program_push_scan.py::test_r087_a_name_holding_a_compatibility_letter_is_found_written_plainly
1 failed, 130 passed in 123.27s (0:02:03)
```

Exit 1.

### W3 output

```
........................................................................ [ 54%]
.................................................F.........              [100%]
=========================== short test summary info ===========================
FAILED tests/test_program_push_scan.py::test_r087_a_name_s_letters_before_another_letter_s_mark_are_no_hit
1 failed, 130 passed in 122.75s (0:02:02)
```

Exit 1.

### W4 output

```
........................................................................ [ 54%]
..........................................FFFFF.F.........F              [100%]
=========================== short test summary info ===========================
FAILED tests/test_program_push_scan.py::test_r087_a_name_is_found_under_unicode_compatibility_caseless_matching[sharp-s-upper]
FAILED tests/test_program_push_scan.py::test_r087_a_name_is_found_under_unicode_compatibility_caseless_matching[sharp-s-lower]
FAILED tests/test_program_push_scan.py::test_r087_a_name_is_found_under_unicode_compatibility_caseless_matching[fullwidth]
FAILED tests/test_program_push_scan.py::test_r087_a_name_is_found_under_unicode_compatibility_caseless_matching[decomposed-in-text]
FAILED tests/test_program_push_scan.py::test_r087_a_name_is_found_under_unicode_compatibility_caseless_matching[decomposed-in-names-file]
FAILED tests/test_program_push_scan.py::test_r087_a_name_holding_a_compatibility_letter_is_found_written_plainly
FAILED tests/test_program_push_scan.py::test_r087_a_punctuated_name_in_a_folding_only_spelling_is_found
7 failed, 124 passed in 122.30s (0:02:02)
```

Exit 1.

### W5 output

```
........................................................................ [ 54%]
..........................................F.FFF...........F              [100%]
=========================== short test summary info ===========================
FAILED tests/test_program_push_scan.py::test_r087_a_name_is_found_under_unicode_compatibility_caseless_matching[sharp-s-upper]
FAILED tests/test_program_push_scan.py::test_r087_a_name_is_found_under_unicode_compatibility_caseless_matching[fullwidth]
FAILED tests/test_program_push_scan.py::test_r087_a_name_is_found_under_unicode_compatibility_caseless_matching[decomposed-in-text]
FAILED tests/test_program_push_scan.py::test_r087_a_name_is_found_under_unicode_compatibility_caseless_matching[decomposed-in-names-file]
FAILED tests/test_program_push_scan.py::test_r087_a_punctuated_name_in_a_folding_only_spelling_is_found
5 failed, 126 passed in 123.86s (0:02:03)
```

Exit 1.

### W6 output

```
..............F......................................................... [ 54%]
...............................................F...........              [100%]
=========================== short test summary info ===========================
FAILED tests/test_program_push_scan.py::test_r087_a_name_is_a_whole_word_in_any_letter_case
FAILED tests/test_program_push_scan.py::test_r087_a_folded_name_inside_a_longer_word_is_still_no_hit
2 failed, 129 passed in 126.70s (0:02:06)
```

Exit 1.

### M7 output

```
..............F......................................................... [ 54%]
...........................................................              [100%]
=========================== short test summary info ===========================
FAILED tests/test_program_push_scan.py::test_r087_a_name_is_a_whole_word_in_any_letter_case
1 failed, 130 passed in 123.29s (0:02:03)
```

Exit 1.

### N7 output

```
........................................................................ [ 54%]
.......................................................FFF.              [100%]
=========================== short test summary info ===========================
FAILED tests/test_program_push_scan.py::test_r087_a_name_whose_i_is_written_dotted_or_dotless_is_found[dotted-capital-in-text]
FAILED tests/test_program_push_scan.py::test_r087_a_name_whose_i_is_written_dotted_or_dotless_is_found[dotless-in-text]
FAILED tests/test_program_push_scan.py::test_r087_a_name_whose_i_is_written_dotted_or_dotless_is_found[dotted-capital-in-names-file]
3 failed, 128 passed in 125.93s (0:02:05)
```

Exit 1.

## Done commands

Counts below belong to commit `14f3436eff2816d0906bc4a5dcc31fe4ffd997b8`. At step 13 the working tree held uncommitted changes. This report was filled in after that status, so the step 13 listing is the stub of this file, not this text.

### 1. `git status --short`

```
 M bridge/cursor-bridge/push-scan.py
 M docs/BUILDER_NOTES.md
?? handoff/TASK-067-r10-report.md
```

Exit 0.

### 2. `python tools/dump-cli.py --check`

```
```

Exit 0.

### 3. `python tools/make-manifest.py`

```
make-manifest: version 2026.11.12a, 147 files hashed, VERSION + MANIFEST.json written
```

Exit 0.

### 4. `git restore bridge/cursor-bridge/VERSION`

```
```

Exit 0. A following read of `bridge/cursor-bridge/VERSION` printed `2026.11.12a`.

### 5. `python -m pytest -p no:cacheprovider -q -rs --tb=short tests/test_program_push_scan.py tests/test_dump_cli.py tests/test_allowlist.py`

```
........................................................................ [ 14%]
........................................................................ [ 29%]
........................................................................ [ 43%]
....................s...ss.....sss....................s...............s. [ 58%]
..............................................s...........s............. [ 73%]
....s...ss.....sss....................s...............s................. [ 87%]
..............................s...........s.................             [100%]
=========================== short test summary info ===========================
SKIPPED [10] tests\test_allowlist.py:65: prose, not a runnable command
SKIPPED [10] tests\test_allowlist.py:106: prose, not a runnable command
472 passed, 20 skipped in 250.03s (0:04:10)
```

Exit 0.

### 6. `python -m pytest -p no:cacheprovider -q tests/test_install_check.py tests/test_tests_windowless.py`

```
.........................                                                [100%]
25 passed in 26.65s
```

Exit 0.

### 7. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`

```
bridge-check: version 2026.11.12a (2026-11-18 18:00) at <Workspace>\bridge
bridge-check: 147 OK, 0 STALE, 0 MISSING, 0 EXTRA
RESULT: SOURCES MATCH bridge 2026.11.12a
```

Exit 0.

### 8. `git grep -n -I -E --no-index "[A-Za-z]:[/\\]|/Users/|/home/|AppData" -- bridge/cursor-bridge/push-scan.py`

```
```

Exit 1.

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

Exit 0.

### 12. `git diff HEAD -- bridge/cursor-bridge/push-scan.py`

```
warning: in the working copy of 'bridge/cursor-bridge/push-scan.py', LF will be replaced by CRLF the next time Git touches it
diff --git a/bridge/cursor-bridge/push-scan.py b/bridge/cursor-bridge/push-scan.py
index 19908a7..a6fc4f5 100644
--- a/bridge/cursor-bridge/push-scan.py
+++ b/bridge/cursor-bridge/push-scan.py
@@ -139,8 +139,9 @@ def has_name(text, names):
     for name in names:
         if not name:
             continue
+        raw = re.compile("(?<![^\\W_])" + re.escape(name) + "(?![^\\W_])", re.IGNORECASE)
         pattern = re.compile("(?<![^\\W_])" + re.escape(_caseless(name)) + "(?![^\\W_])")
-        if pattern.search(folded):
+        if raw.search(text) or pattern.search(folded):
             return True
     return False
```

Exit 0.

### 13. `git rev-parse HEAD` and `git status --short`

```
14f3436eff2816d0906bc4a5dcc31fe4ffd997b8
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/push-scan.py
 M docs/BUILDER_NOTES.md
?? handoff/TASK-067-r10-report.md
```

Exit 0. `bridge/cursor-bridge/VERSION` is not listed.

## Assumed, not verified

- NFKC's cost on hostile text is the known lead (a hang, never a pass) and is not measured or bounded here | the union still folds the whole text on every call, before either search | time `_caseless` on runs of combining marks and on repeated U+FDFA. This round does not.
- The raw reading runs first, so the boolean changes with that order only when one reading raises and the other would return | a raise leaves `has_name` and `main` returns exit 2 | call each reading alone on the same strings, including every scalar value. A sweep of lone surrogates U+D800 to U+DFFF through `has_name` raised nothing.
