# BUG-046 round 2 report

## Files changed
- `bridge/cursor-bridge/permission-guard.py`
- `bridge/cursor-bridge/MANIFEST.json` (rewritten by `python tools/make-manifest.py`, not by hand)
- `tests/test_bug046.py` (below the builder's marker only)
- `handoff/BUG-046-r2-report.md` (this file, written after the Done commands, so neither `git status` below lists it)

`docs/BUILDER_NOTES.md` was not changed. `bridge/cursor-bridge/VERSION` was restored with `git restore` after `make-manifest.py` and is not in the final status. Its bytes are `2026.11.12a` followed by CRLF.

## Summary
`_percent_decoded` decodes every `%` and two hexadecimal digits, repeating until a pass changes nothing, and `_check_word_list` uses that text for both `gh api` refusals that this round may change: a merge mutation is sought in each word as written and in the decoded word, case kept, and a pull request's merge endpoint is sought in the lower-cased decoded word, in the path cut at the first `?` or `#`, and in `posixpath.normpath` of that path only. `WRITE_METHODS` is deleted. The body refusal, the alias refusal, `gh_words`, `merge_reason`, the module docstring, and the import list are unchanged.

## Causes
The merge-endpoint check no longer runs `posixpath.normpath` over a query or a fragment, so a `..` after `?` or `#`, or a trailing `merge/..`, cannot erase the merge path, while the whole decoded word is still searched so a word that holds `/pulls/<segment>/merge` before that cut stays refused.
Every `%` and two hex digits is decoded, and the decoding is repeated, so an escaped letter of the path is that letter, including a doubly escaped `%2570`.
The merge-mutation refusal searches the decoded word as well as the word as written, so a mutation name with an escaped letter in a query string is the GraphQL name.

## G1
`_percent_decoded` (lines 2200-2207) replaces each `%` and two hex digits via `re.sub` over `%([0-9A-Fa-f]{2})` and repeats until a pass changes nothing; a pass that changes the word shortens it, and a non-ASCII result is those characters. Pinned by `test_bug046_r1_a_merge_endpoint_hidden_by_a_query_a_dot_segment_or_an_escape_is_refused` (the escaped-letter ids), by `doubly-escaped-letter` in `test_bug046_a_merge_endpoint_with_a_query_fragment_or_percent_2e_is_refused` (`%2570` is `p` only on the second pass), and by `test_bug046_r1_an_escaped_merge_mutation_name_is_refused`.

## G2
In `_check_word_list` at lines 2345-2352 the decoded word is lower-cased, cut at the first `?` or `#`, and refused with the round-1 merge-endpoint reason when `/pulls/[^/]+/merge` holds in the whole decoded word, in that path, or in `posixpath.normpath` of that path. Pinned by `test_bug046_r1_a_merge_endpoint_hidden_by_a_query_a_dot_segment_or_an_escape_is_refused`, `test_bug046_the_merge_endpoint_is_refused_whatever_the_method_or_spelling`, `test_bug046_a_merge_endpoint_with_a_query_fragment_or_percent_2e_is_refused`, `test_bug046_mergeable_report_is_refused`, `test_bug046_an_issues_merge_endpoint_passes`, and `test_bug046_r1_ordinary_calls_with_escapes_or_queries_pass`.

## G3
In `_check_word_list` at line 2337 each name in `MERGE_MUTATIONS` is sought in the word as written and in `_percent_decoded` of that word, case kept, and the reason text is the round-1 sentence. Pinned by `test_bug046_r1_an_escaped_merge_mutation_name_is_refused`.

## G4
Below the marker, `test_bug046_glued_and_clustered_unreadable_bodies_are_refused_on_rest_and_graphql` asserts `body read from a file or standard input`, and the PowerShell value of `rest-glued-field` and `graphql-glued-field` is `-Fquery=@-` while the Bash value stays `-Fquery=@q.graphql`. `test_bug046_a_merge_endpoint_with_a_query_fragment_or_percent_2e_is_refused` and `test_bug046_mergeable_report_is_refused` assert `merge endpoint`. The id `percent-2e-parent` is `percent-2e-dot-before-pulls`. Nothing above the marker was edited.

## G5
`WRITE_METHODS` (round 1's line 63) is deleted. After the edit, `rg -n "WRITE_METHODS" bridge tests` printed no lines, so no file under `bridge/` or `tests/` names it.

## Mutations
None. No source line was mutated in process.

## Commands
Counts below belong to commit `2d26100b5d148b4bc90639aa670e2bffb774c425` with uncommitted changes. Steps 1-5 were one shell, joined by `&&`, with echo markers that are not part of those programs. The probe and the line-ending check ran before that, on the same program text, before `MANIFEST.json` was regenerated.

Line endings, before the Done list: `python -c "p=open('bridge/cursor-bridge/permission-guard.py','rb').read(); print('CRLF' if b'\r\n' in p else 'LF', 'mixed' if b'\n' in p.replace(b'\r\n', b'') else 'pure'); t=open('tests/test_bug046.py','rb').read(); print('test', 'CRLF' if b'\r\n' in t else 'LF')"`

```
CRLF pure
test LF
```

Diff stat, before the Done list: `git diff --stat`

```
 bridge/cursor-bridge/permission-guard.py | 20 ++++++++++++++++----
 tests/test_bug046.py                     | 31 +++++++++++++++++--------------
 2 files changed, 33 insertions(+), 18 deletions(-)
```

Probe, before the Done list: `python -m pytest -q -rs tests/test_bug046.py`

```
........................................................................ [ 63%]
..........................................                               [100%]
114 passed in 10.83s
```

Done step 1: `git status --short`

```
 M bridge/cursor-bridge/permission-guard.py
 M tests/test_bug046.py
```

Done step 2: `python tools/make-manifest.py`

```
make-manifest: version 2026.11.12a, 146 files hashed, VERSION + MANIFEST.json written
```

Done step 3: `git restore bridge/cursor-bridge/VERSION` printed no lines.

Done step 4: `python tools/dump-cli.py --check` printed no lines. The shell then ran `echo "exit:$?"`, which printed `exit:0`.

Done step 5: `git status --short`

```
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/permission-guard.py
 M tests/test_bug046.py
```

VERSION bytes, in that same shell after step 5: `python -c "import pathlib; print(repr(pathlib.Path('bridge/cursor-bridge/VERSION').read_bytes()))"`

```
b'2026.11.12a\r\n'
```

Done step 6: `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`

```
bridge-check: version 2026.11.12a (2026-11-17 07:37) at <Workspace>\bridge
bridge-check: 146 OK, 0 STALE, 0 MISSING, 0 EXTRA
RESULT: SOURCES MATCH bridge 2026.11.12a
```

Done step 7: `python -m pytest -q -rs tests/test_bug046.py`

```
........................................................................ [ 63%]
..........................................                               [100%]
114 passed in 10.73s
```

Done step 8: `python -m pytest -q tests/test_permission_guard.py tests/test_permission_guard_a4.py tests/test_program_permission_guard.py tests/test_bug045.py`

```
........................................................................ [  5%]
........................................................................ [ 11%]
........................................................................ [ 16%]
........................................................................ [ 22%]
........................................................................ [ 27%]
........................................................................ [ 33%]
........................................................................ [ 39%]
........................................................................ [ 44%]
........................................................................ [ 50%]
........................................................................ [ 55%]
........................................................................ [ 61%]
........................................................................ [ 67%]
........................................................................ [ 72%]
........................................................................ [ 78%]
........................................................................ [ 83%]
........................................................................ [ 89%]
........................................................................ [ 94%]
.................................................................        [100%]
1289 passed in 132.29s (0:02:12)
```

Done step 9: `python -m pytest -q tests/test_program_ready.py tests/test_allowlist.py tests/test_task032_supervisor_guard.py tests/test_tests_windowless.py`

```
........................................................................ [ 12%]
........................................................................ [ 25%]
.....................s...ss.....sss....................s...............s [ 37%]
...............................................s...........s............ [ 50%]
.....s...ss.....sss....................s...............s................ [ 62%]
...............................s...........s............................ [ 75%]
........................................................................ [ 87%]
.....................................................................    [100%]
553 passed, 20 skipped in 177.09s (0:02:57)
```

Done step 10: `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks`

```
windowless-check: 39 file(s) scanned, 0 FAIL, 0 NOTE
```

Done step 11: `git rev-parse HEAD` then `git status --short` (one shell, after an echo marker)

```
2d26100b5d148b4bc90639aa670e2bffb774c425
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/permission-guard.py
 M tests/test_bug046.py
```

After step 11: `rg -n "WRITE_METHODS" bridge tests` printed no lines.

`semgrep` was not run.

## Assumed, not verified
- No new Semgrep high finding · the Done list does not name Semgrep, and it was not run · the project's Semgrep invocation on this diff.
- A decoded word that is not ASCII is kept as the characters the two hex digits name, then lower-cased for the endpoint check · "read as it is" was taken as those characters, so an ASCII escape beside a non-ASCII escape is still decoded · a `gh api` word whose only merge spelling is an ASCII percent-escape next to a non-ASCII percent-escape: this reading refuses it, and the other reading (keep the original word) would let it pass.
