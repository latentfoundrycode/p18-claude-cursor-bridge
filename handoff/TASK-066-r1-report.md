# TASK-066 round 1

## Summary
`findings()` in `bridge/cursor-bridge/invisible-check.py` flags a character when `unicodedata.category` is Cc, Cf, Zl or Zp, or Zs other than U+0020, allowing U+0009, U+000A and U+000D anywhere and U+FEFF only at line 1 column 1. A finding that has a Unicode name prints that name in lower case, and a finding that has none prints the code point with nothing after it. The options, the exits, the files read, the binary skip, the `--non-ascii` listing and both `RESULT:` lines are unchanged, and one added case covers U+180E.

## Files changed
- `bridge/cursor-bridge/invisible-check.py`
- `bridge/cursor-bridge/MANIFEST.json`
- `tests/test_hotfix25a_guard_scope_invisible.py`
- `docs/BUILDER_NOTES.md`
- `handoff/TASK-066-r1-report.md`

## Requirements
1. `findings()` lines 68-71: `unicodedata.category` is Cc, Cf, Zl or Zp, or Zs with the code point other than U+0020, and the character is kept out when it is U+0009, U+000A or U+000D, or U+FEFF at line 1 column 1 (`n == 1 and i == 0`).
2. The `INVISIBLE` dict and the `range(0x2000, 0x200B)` loop are removed. The finding decision is the category comparisons in `findings()` lines 68-70, which read `unicodedata.category` and do not consult a list or set of code points.
3. `findings()` line 71 stores `unicodedata.name(ch, "").lower()`, empty when the character has no name. `main()` line 82 prints `INVISIBLE: <path>:<line>:<column> U+XXXX <name>` when that name is non-empty and `INVISIBLE: <path>:<line>:<column> U+XXXX` when it is empty.
4. `changed_files()` lines 39-44, the binary and unreadable tests and the UTF-8 decode in `findings()` lines 50-59, the `--non-ascii` branch lines 64-66, and `main()` lines 75-96 keep the previous options, exits, files, listing and `RESULT:` lines. Line 82 is the unnamed-character exception in Requirement 3.
5. The module docstring lines 7-10 state the categories Cc, Cf, Zl and Zp, Zs other than U+0020, the allow-list U+0009, U+000A and U+000D anywhere and U+FEFF as the file's first character, and that a character with no Unicode name is named by its code point alone. The usage line and the other docstring sentences are unchanged.
6. `test_r086_mongolian_vowel_separator_stays_a_named_finding` in `tests/test_hotfix25a_guard_scope_invisible.py` lines 427-432 names R-086, builds U+180E with `chr()`, and uses `changed_repo` and `run`. No existing line in that file or in `tests/test_invisible_check.py` was edited. `tests/test_program_invisible.py` was not edited.
7. `python tools/make-manifest.py` rewrote `bridge/cursor-bridge/MANIFEST.json` (the `generated` stamp and the `invisible-check.py` hash). `git restore bridge/cursor-bridge/VERSION` left that file as `2026.11.12a`, and step 9 does not list it.

## Mutation self-check
Each mutant was applied to `bridge/cursor-bridge/invisible-check.py`, then `python -m pytest -p no:cacheprovider -q tests/test_program_invisible.py` was run from `<Workspace>`, then the file was restored. The last restore compared equal to the bytes from before M1. Exit code 1 for every mutant.
- M1 the category Cc dropped from the rule (`cat == "Cc" or ` removed). Caught by `test_r086_each_category_is_a_finding_named_by_its_unicode_name_or_its_code_point[Cc-U+0001]`. Summary: `11 failed, 12 passed in 8.29s`.
- M2 the category Cf dropped (`cat == "Cf" or ` removed). Caught by `test_r086_each_category_is_a_finding_named_by_its_unicode_name_or_its_code_point[Cf-U+200E]`. Summary: `5 failed, 18 passed in 8.27s`.
- M3 the category Zl dropped (`cat == "Zl" or ` removed). Caught by `test_r086_each_category_is_a_finding_named_by_its_unicode_name_or_its_code_point[Zl-U+2028]`. Summary: `3 failed, 20 passed in 8.75s`.
- M4 the category Zp dropped (`cat == "Zp" or ` removed). Caught by `test_r086_each_category_is_a_finding_named_by_its_unicode_name_or_its_code_point[Zp-U+2029]`. Summary: `2 failed, 21 passed in 8.40s`.
- M5 the category Zs dropped (` or (cat == "Zs" and cp != 0x0020)` removed). Caught by `test_r086_each_category_is_a_finding_named_by_its_unicode_name_or_its_code_point[Zs-U+1680]`. Summary: `2 failed, 21 passed in 8.49s`.
- M6 the allow-list widened by U+000B (`or cp == 0x000B` added). Caught by `test_r086_each_category_is_a_finding_named_by_its_unicode_name_or_its_code_point[Cc-U+000B]`. Summary: `2 failed, 21 passed in 8.38s`.
- M7 the allow-list widened by U+0085 (`or cp == 0x0085` added). Caught by `test_r086_each_category_is_a_finding_named_by_its_unicode_name_or_its_code_point[Cc-U+0085]`. Summary: `2 failed, 21 passed in 8.43s`.
- M8 the first-character rule applied anywhere (`n == 1 and ` removed, so U+FEFF is allowed at column 1 of any line). Caught by `test_r086_the_allow_list_passes_and_only_the_other_characters_are_findings`. Summary: `1 failed, 22 passed in 8.52s`.
- M9 the name dropped for a named character (the stored name replaced with `""`). Caught by `test_r086_each_category_is_a_finding_named_by_its_unicode_name_or_its_code_point[Cf-U+200E]`. Summary: `11 failed, 12 passed in 8.82s`.
- M10 a placeholder printed for an unnamed character (`unicodedata.name(ch, "(no name)").lower()`). Caught by `test_r086_each_category_is_a_finding_named_by_its_unicode_name_or_its_code_point[Cc-U+0001]`. Summary: `11 failed, 12 passed in 9.08s`.

## Commands

Checkpoint, before the edit. `python -m pytest -p no:cacheprovider -q -rs tests/test_program_invisible.py`. Exit code 1. The failure listing was truncated by the runner and named a temporary folder, so those bodies are not copied. The progress line and the summary line:

```
FFFFFFFFFFFFFFFFFFFFFF.                                                  [100%]
22 failed, 1 passed in 7.88s
```

`python -c` printing category and `unicodedata.name` for the old list's code points. Exit code 0.

```
0x180e Cf MONGOLIAN VOWEL SEPARATOR
0x200b Cf ZERO WIDTH SPACE
0x200c Cf ZERO WIDTH NON-JOINER
0x200d Cf ZERO WIDTH JOINER
0x2060 Cf WORD JOINER
0xfeff Cf ZERO WIDTH NO-BREAK SPACE
0xad Cf SOFT HYPHEN
0x202a Cf LEFT-TO-RIGHT EMBEDDING
0x202e Cf RIGHT-TO-LEFT OVERRIDE
0x2066 Cf LEFT-TO-RIGHT ISOLATE
0x2069 Cf POP DIRECTIONAL ISOLATE
0x61c Cf ARABIC LETTER MARK
0xa0 Zs NO-BREAK SPACE
0x202f Zs NARROW NO-BREAK SPACE
0x3000 Zs IDEOGRAPHIC SPACE
0x2007 Zs FIGURE SPACE
0x2000 Zs EN QUAD
```

`python -c` scanning every code point in Cc, Cf, Zl, Zp and Zs for a Unicode name. Exit code 0.

```
named Cc 0 []
unnamed non-Cc in set 0 []
```

`python -c` scanning those same categories for a non-ASCII name. Exit code 0.

```
non-ascii names 0
```

After the edit, before the Done list. ASCII check of the program plus `python -m pytest -p no:cacheprovider -q -rs tests/test_program_invisible.py tests/test_invisible_check.py tests/test_hotfix25a_guard_scope_invisible.py`. Exit code 0.

```
nonascii []
INVISIBLE False
.........................................                                [100%]
41 passed in 27.47s
```

`git diff --stat` then the start of `git diff -- bridge/cursor-bridge/invisible-check.py`. Exit code 0. The diff is the docstring, the removal of `INVISIBLE` and its loop, the category branch in `findings()`, and the unnamed-character print in `main()`.

```
 bridge/cursor-bridge/invisible-check.py       | 25 +++++++++----------------
 docs/BUILDER_NOTES.md                         |  2 ++
 tests/test_hotfix25a_guard_scope_invisible.py |  8 ++++++++
 3 files changed, 19 insertions(+), 16 deletions(-)
```

The mutation driver printed the headers and the summary line of each pytest run above, then `RESTORED True`. Exit code 0.

Done step 1. `git status --short`. Exit code 0.

```
 M bridge/cursor-bridge/invisible-check.py
 M docs/BUILDER_NOTES.md
 M tests/test_hotfix25a_guard_scope_invisible.py
```

Done step 2. `python -c "import sys, unicodedata; print(sys.version); print(unicodedata.unidata_version)"`. Exit code 0.

```
3.12.10 (tags/v3.12.10:0cc8128, Apr  8 2025, 12:21:36) [MSC v.1943 64 bit (AMD64)]
15.0.0
```

Done step 3. `python tools/make-manifest.py`. Exit code 0.

```
make-manifest: version 2026.11.12a, 146 files hashed, VERSION + MANIFEST.json written
```

Done step 4. `git restore bridge/cursor-bridge/VERSION`. Exit code 0. A following read of the file bytes printed `b'2026.11.12a\r\n'`.

Done step 5. `python -m pytest -p no:cacheprovider -q -rs tests/test_program_invisible.py tests/test_invisible_check.py tests/test_hotfix25a_guard_scope_invisible.py`. Exit code 0.

```
.........................................                                [100%]
41 passed in 27.39s
```

Done step 6. `python -m pytest -p no:cacheprovider -q tests/test_workflow_check.py tests/test_release_t_ceiling.py tests/test_tests_windowless.py`. Exit code 0. That command does not name the skips. A later run of the same files with `-rs` does; it is quoted after step 9.

```
........................................................................ [ 14%]
........................................................................ [ 28%]
........................................................................ [ 42%]
..............s......................................................... [ 56%]
........................................................................ [ 71%]
........................................................................ [ 85%]
......................................s................................. [ 99%]
..                                                                       [100%]
504 passed, 2 skipped in 46.89s
```

Done step 7. `python bridge/cursor-bridge/invisible-check.py --all`. Exit code 0.

```
RESULT: OK - no invisible character in 946 file(s)
```

Done step 8. `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks`. Exit code 0.

```
windowless-check: 39 file(s) scanned, 0 FAIL, 0 NOTE
```

Done step 9. `git rev-parse HEAD` then `git status --short`. Exit code 0 for both. `bridge/cursor-bridge/VERSION`, `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` are not listed.

```
436b43b56e98cf80e581ae57b7f571220aef77b7
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/invisible-check.py
 M docs/BUILDER_NOTES.md
 M tests/test_hotfix25a_guard_scope_invisible.py
```

After step 9. `git diff --stat -- bridge/cursor-bridge/MANIFEST.json bridge/cursor-bridge/VERSION` and `git diff -U1 -- bridge/cursor-bridge/MANIFEST.json`. Exit code 0. Git printed `warning: in the working copy of 'bridge/cursor-bridge/MANIFEST.json', LF will be replaced by CRLF the next time Git touches it`. The content diff is the stamp and the program hash.

```
 bridge/cursor-bridge/MANIFEST.json | 4 ++--
 1 file changed, 2 insertions(+), 2 deletions(-)
```

```
-  "generated": "2026-11-17 15:40",
+  "generated": "2026-11-17 20:10",
-    "cursor-bridge/invisible-check.py": "aa6f6b129546ae10c0e22b70a6bc4ed78982ac184d3b4a117a9ff04050d881e5",
+    "cursor-bridge/invisible-check.py": "5584c8f1e4099603d965c86dbdaad8f226fe373dba736c10264a88894fbb7a91",
```

After step 9, to name the two skips. `python -m pytest -p no:cacheprovider -q -rs tests/test_workflow_check.py tests/test_release_t_ceiling.py tests/test_tests_windowless.py`. Exit code 0.

```
=========================== short test summary info ===========================
SKIPPED [1] tests\test_workflow_check.py:1093: a folder made unreadable by mode bits needs a non-root POSIX user (CI's ubuntu leg)
SKIPPED [1] tests\test_workflow_check.py:3369: this file system trims a trailing space from a name: ['host-extension', 'web-app.md', 'has-screens.md']
504 passed, 2 skipped in 49.77s
```

`python tools/dump-cli.py`: not run. Semgrep: not run.

## Results
The counts above belong to commit `436b43b56e98cf80e581ae57b7f571220aef77b7`. At step 9 the working tree held uncommitted changes:

```
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/invisible-check.py
 M docs/BUILDER_NOTES.md
 M tests/test_hotfix25a_guard_scope_invisible.py
```

## Assumed, not verified
Assumed, not verified: none
