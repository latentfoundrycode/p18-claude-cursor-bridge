# BUG-046 report

## Summary
`_check_word_list`'s `gh api` branch no longer takes a method from the command's words. A `gh api` call is refused when any word is a body the guard cannot read (`--input`, a word beginning `--input=`, a word beginning `@`, or a word holding `=@`), whatever the endpoint, and when any word, lower-cased, with `%2f` read as `/` and `%2e` read as `.` and then passed through `posixpath.normpath`, holds `/pulls/<segment>/merge`. The pinned read `gh api repos/o/r/pulls/12/merge` is on the refused list, the module docstring matches those two refusals, and the manifest and the CLI reference were regenerated from the program.

## Files changed
- `bridge/cursor-bridge/permission-guard.py`
- `bridge/cursor-bridge/MANIFEST.json` (rewritten by `python tools/make-manifest.py`, not by hand)
- `docs/cli-reference.json` (rewritten by `python tools/dump-cli.py`, not by hand)
- `docs/CLI_REFERENCE.md` (rewritten by `python tools/dump-cli.py`, not by hand)
- `tests/test_bug046.py` (cases below the marker only)
- `tests/test_permission_guard.py` (the one moved line)
- `docs/BUILDER_NOTES.md` (one dated line)
- `handoff/BUG-046-report.md` (this file)

`bridge/cursor-bridge/VERSION` was restored with `git restore` after `make-manifest.py` and is not in the final status. Its text is `2026.11.12a`.

## Causes
The merge refusal no longer reads a method from any word, so a method-shaped value of `-p`, `-H`, `-q`, or `-t` cannot replace the method gh would send.
The body refusal no longer depends on the endpoint word being exactly `graphql`, so `--input` or a field read from a file is refused for a URL or a path as well as for the bare word.

## F1
In `_check_word_list` at lines 2330-2331, a `group == "api"` command is refused when any word equals `--input`, begins with `--input=`, begins with `@`, or holds `=@`, and the reason names a body read from a file or standard input that the guard cannot read and tells the caller to write the query or fields on the command line. Pinned by `test_bug046_a_body_the_guard_cannot_read_is_refused_whatever_the_endpoint`, by `test_bug046_glued_and_clustered_unreadable_bodies_are_refused_on_rest_and_graphql`, and by the existing `test_refused` rows `gh api graphql -F query=@merge.graphql` and `gh api graphql --input merge.json`.

## F2
In `_check_word_list` at lines 2336-2340 the method loop is gone: each word is lower-cased, `%2f` and `%2e` are read as `/` and `.`, `posixpath.normpath` resolves `.` and `..` and collapsed slashes, and a word that then holds `/pulls/[^/]+/merge` is refused with a reason that names a pull request's merge endpoint and merging outside the gate. Pinned by `test_bug046_a_method_word_that_is_another_options_value_never_lets_a_merge_through`, `test_bug046_the_merge_endpoint_is_refused_whatever_the_method_or_spelling`, `test_bug046_a_merge_endpoint_with_a_query_fragment_or_percent_2e_is_refused`, `test_bug046_mergeable_report_is_refused`, and `test_bug046_an_issues_merge_endpoint_passes`. `WRITE_METHODS` at line 63 is the same tuple as before and is not read. The merge-mutation refusal at lines 2328-2329, the alias refusal at lines 2332-2335, `gh_words`, and `merge_reason` are unchanged.

## F3
`"gh api repos/o/r/pulls/12/merge"` moved from `test_allowed` to the refused list in `tests/test_permission_guard.py`, on the line after `gh api --method PUT /repos/o/r/pulls/12/merge`. No other line of that file changed.

## F4
The module docstring lines 5-6 say the REST route `gh api … /pulls/<n>/merge` is refused whatever its method, and lines 25-27 drop "`-XPUT` is a method" and say a `gh api` body read from a file or standard input is refused unread, whatever the endpoint. The colon after `` `find -exec` runs its command `` is the colon that clause used to carry. `python tools/dump-cli.py` rewrote `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` from that docstring. No other docstring sentence changed.

## F5
Each case runs `guard` from `plain` under Bash and PowerShell (`ids=["Bash", "PowerShell"]`).
- `rest-input-equals` pins `--input=body.json` on a REST path.
- `graphql-input-equals` pins `--input=body.json` on `graphql`.
- `rest-glued-field` pins `-Fquery=@q.graphql` on a REST path.
- `graphql-glued-field` pins `-Fquery=@q.graphql` on `graphql`.
- `rest-long-field` pins `--field=query=@q.graphql` on a REST path.
- `graphql-long-field` pins `--field=query=@q.graphql` on `graphql`.
- `raw-field-at` pins the accepted over-refusal of `-f key=@x` (a raw field, refused because the word holds `=@`).
- `trailing-query` pins `repos/o/r/pulls/5/merge?x=1` (single-quoted, because an unquoted `?` is a glob to the Bash reader).
- `trailing-fragment` pins `repos/o/r/pulls/5/merge#frag`.
- `percent-2e-dot` pins `repos/o/r/pulls/5/%2E/merge`.
- `percent-2e-parent` pins `repos/o/r/%2E/pulls/5/merge`.
- `test_bug046_an_issues_merge_endpoint_passes` pins that `repos/o/r/issues/5/merge` is allowed.
- `test_bug046_mergeable_report_is_refused` pins the accepted over-refusal of `repos/o/r/pulls/5/mergeable-report`, which holds `/pulls/5/merge`. The comment on that test says so.

## Mutations
None. No source line was mutated in process.

## Commands
`semgrep` was not run. The Done list does not name it.

A probe before the Done list, `python -m pytest -q -rs tests/test_bug046.py`:

```
........................................................................ [ 94%]
....                                                                     [100%]
76 passed in 7.29s
```

Done step 1, then 2, then 3, then a read of VERSION, in one shell: `git status --short && echo "---STEP2---" && python tools/make-manifest.py && echo "---STEP3---" && git restore bridge/cursor-bridge/VERSION && echo "---VERSION---" && python -c "import pathlib; print(repr(pathlib.Path('bridge/cursor-bridge/VERSION').read_bytes()))"`

```
 M bridge/cursor-bridge/permission-guard.py
 M docs/BUILDER_NOTES.md
 M tests/test_bug046.py
 M tests/test_permission_guard.py
---STEP2---
make-manifest: version 2026.11.12a, 146 files hashed, VERSION + MANIFEST.json written
---STEP3---
---VERSION---
b'2026.11.12a\r\n'
```

`git restore` printed no lines. The VERSION bytes are the text `2026.11.12a` and a CRLF.

Done step 4, first check: `python tools/dump-cli.py --check; echo "exit:$?"`

```
docs/cli-reference.json
docs/CLI_REFERENCE.md
exit:1
```

Done step 4, regenerate and check again: `python tools/dump-cli.py; echo "dump_exit:$?"; python tools/dump-cli.py --check; echo "check_exit:$?"`

```
dump_exit:0
check_exit:0
```

`python tools/dump-cli.py` printed no lines.

Done steps 5 and 6: `git status --short; echo "status_exit:$?"; python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet; echo "check_exit:$?"`

```
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/permission-guard.py
 M docs/BUILDER_NOTES.md
 M docs/CLI_REFERENCE.md
 M docs/cli-reference.json
 M tests/test_bug046.py
 M tests/test_permission_guard.py
status_exit:0
bridge-check: version 2026.11.12a (2026-11-17 06:57) at <Workspace>\bridge
bridge-check: 146 OK, 0 STALE, 0 MISSING, 0 EXTRA
RESULT: SOURCES MATCH bridge 2026.11.12a
check_exit:0
```

`bridge/cursor-bridge/VERSION` is not in that status. The bridge-check line that names a folder is quoted with `<Workspace>` in place of the repository folder.

Done step 7, then 8, then 9, in one shell.

`python -m pytest -q -rs tests/test_bug046.py`

```
........................................................................ [ 94%]
....                                                                     [100%]
76 passed in 7.16s
pytest7_exit:0
```

`python -m pytest -q tests/test_permission_guard.py tests/test_permission_guard_a4.py tests/test_program_permission_guard.py tests/test_bug045.py`

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
1289 passed in 130.24s (0:02:10)
pytest8_exit:0
```

`python -m pytest -q tests/test_program_ready.py tests/test_allowlist.py tests/test_task032_supervisor_guard.py tests/test_tests_windowless.py`

```
........................................................................ [ 12%]
........................................................................ [ 25%]
.....................s...ss.....sss....................s...............s [ 37%]
...............................................s...........s............ [ 50%]
.....s...ss.....sss....................s...............s................ [ 62%]
...............................s...........s............................ [ 75%]
........................................................................ [ 87%]
.....................................................................    [100%]
553 passed, 20 skipped in 175.86s (0:02:55)
pytest9_exit:0
```

Done steps 10 and 11: `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks; echo "win_exit:$?"; git rev-parse HEAD; echo "rev_exit:$?"; git status --short; echo "status_exit:$?"`

```
windowless-check: 39 file(s) scanned, 0 FAIL, 0 NOTE
win_exit:0
3d6e4eb3b3a640842d3be13ea1c2cce36b243eb7
rev_exit:0
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/permission-guard.py
 M docs/BUILDER_NOTES.md
 M docs/CLI_REFERENCE.md
 M docs/cli-reference.json
 M tests/test_bug046.py
 M tests/test_permission_guard.py
status_exit:0
```

Results after step 11 belong to commit `3d6e4eb3b3a640842d3be13ea1c2cce36b243eb7`. The working tree held uncommitted changes, the seven paths in the status above. This report file was written after that status, so it is not in that fence. A later `git status --short`, after this file existed, printed:

```
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/permission-guard.py
 M docs/BUILDER_NOTES.md
 M docs/CLI_REFERENCE.md
 M docs/cli-reference.json
 M tests/test_bug046.py
 M tests/test_permission_guard.py
?? handoff/BUG-046-report.md
```

The step 9 skips are named by a later run, `python -m pytest -q -rs --tb=no tests/test_program_ready.py tests/test_allowlist.py tests/test_task032_supervisor_guard.py tests/test_tests_windowless.py`:

```
........................................................................ [ 12%]
........................................................................ [ 25%]
.....................s...ss.....sss....................s...............s [ 37%]
...............................................s...........s............ [ 50%]
.....s...ss.....sss....................s...............s................ [ 62%]
...............................s...........s............................ [ 75%]
........................................................................ [ 87%]
.....................................................................    [100%]
=========================== short test summary info ===========================
SKIPPED [10] tests\test_allowlist.py:65: prose, not a runnable command
SKIPPED [10] tests\test_allowlist.py:106: prose, not a runnable command
553 passed, 20 skipped in 176.50s (0:02:56)
```

Those two rows are the allowlist file's prose cases. This change does not edit that file.

A reason probe after the tests, run as one `python -c` that launches the guard the way `guard()` does. Its cwd was a folder from `tempfile.mkdtemp`, which is outside `<Workspace>` and is not a pytest `tmp_path`. The guard was not installed, and `gh` was not run. The printed reasons are the merge-endpoint sentence, the unread-body sentence, or exit 0 for `repos/o/r/issues/5/merge`.

```
Bash 2 permission-guard (Claude-Cursor Bridge): refused - gh api on a pull request's merge endpoint (merging outside the gate). The loop merges only through the verified gate and never fo
CMD gh api 'repos/o/r/pulls/5/merge?x=1'
Bash 2 permission-guard (Claude-Cursor Bridge): refused - gh api on a pull request's merge endpoint (merging outside the gate). The loop merges only through the verified gate and never fo
CMD gh api repos/o/r/pulls/5/merge#frag
Bash 2 permission-guard (Claude-Cursor Bridge): refused - gh api on a pull request's merge endpoint (merging outside the gate). The loop merges only through the verified gate and never fo
CMD gh api repos/o/r/pulls/5/%2E/merge
Bash 2 permission-guard (Claude-Cursor Bridge): refused - gh api with a body read from a file or standard input, which the guard cannot read (write the query or fields on the command line
CMD gh api repos/o/r/issues/5/comments --input=body.json
Bash 2 permission-guard (Claude-Cursor Bridge): refused - gh api with a body read from a file or standard input, which the guard cannot read (write the query or fields on the command line
CMD gh api repos/o/r/issues/5/comments -f key=@x
Bash 2 permission-guard (Claude-Cursor Bridge): refused - gh api on a pull request's merge endpoint (merging outside the gate). The loop merges only through the verified gate and never fo
CMD gh api repos/o/r/pulls/5/mergeable-report
Bash 0 
CMD gh api repos/o/r/issues/5/merge
Bash 2 permission-guard (Claude-Cursor Bridge): refused - gh api on a pull request's merge endpoint (merging outside the gate). The loop merges only through the verified gate and never fo
CMD gh api -X PUT repos/o/r/pulls/5/merge -p -XGET
PowerShell 2 permission-guard (Claude-Cursor Bridge): refused - gh api on a pull request's merge endpoint (merging outside the gate). The loop merges only through the verified gate and never fo
CMD gh api 'repos/o/r/pulls/5/merge?x=1'
PowerShell 2 permission-guard (Claude-Cursor Bridge): refused - gh api on a pull request's merge endpoint (merging outside the gate). The loop merges only through the verified gate and never fo
CMD gh api repos/o/r/pulls/5/merge#frag
PowerShell 2 permission-guard (Claude-Cursor Bridge): refused - gh api on a pull request's merge endpoint (merging outside the gate). The loop merges only through the verified gate and never fo
CMD gh api repos/o/r/pulls/5/%2E/merge
PowerShell 2 permission-guard (Claude-Cursor Bridge): refused - gh api with a body read from a file or standard input, which the guard cannot read (write the query or fields on the command line
CMD gh api repos/o/r/issues/5/comments --input=body.json
PowerShell 2 permission-guard (Claude-Cursor Bridge): refused - gh api with a body read from a file or standard input, which the guard cannot read (write the query or fields on the command line
CMD gh api repos/o/r/issues/5/comments -f key=@x
PowerShell 2 permission-guard (Claude-Cursor Bridge): refused - gh api on a pull request's merge endpoint (merging outside the gate). The loop merges only through the verified gate and never fo
CMD gh api repos/o/r/pulls/5/mergeable-report
PowerShell 0 
CMD gh api repos/o/r/issues/5/merge
PowerShell 2 permission-guard (Claude-Cursor Bridge): refused - gh api on a pull request's merge endpoint (merging outside the gate). The loop merges only through the verified gate and never fo
CMD gh api -X PUT repos/o/r/pulls/5/merge -p -XGET
```

`git diff --stat && git diff -U3 -- bridge/cursor-bridge/permission-guard.py | head -n 220` showed line-ending warnings for `MANIFEST.json`, `docs/CLI_REFERENCE.md`, `docs/cli-reference.json`, and `tests/test_bug046.py`, then this stat:

```
 bridge/cursor-bridge/MANIFEST.json       |  4 +--
 bridge/cursor-bridge/permission-guard.py | 28 +++++++----------
 docs/BUILDER_NOTES.md                    |  2 ++
 docs/CLI_REFERENCE.md                    |  8 ++---
 docs/cli-reference.json                  |  2 +-
 tests/test_bug046.py                     | 53 ++++++++++++++++++++++++++++++++
 tests/test_permission_guard.py           |  2 +-
 7 files changed, 74 insertions(+), 25 deletions(-)
```

The permission-guard hunks are the two docstring edits, `import posixpath`, and the two `gh api` refusals. The alias block and the merge-mutation line are absent from the diff.

## Assumed, not verified
- `posixpath.normpath` resolves a leading `..` the way GitHub's server would · the brief names `posixpath.normpath` as the reader and the tests only check the guard's result · send GitHub a path that climbs with `..` and compare the path it routes
- a `..` or `%2e` inside a query or fragment is collapsed with the path, because `normpath` sees the whole word · the added query case is `?x=1` and holds no `..`, and the brief applies `normpath` to the whole word · run the guard on `repos/o/r/pulls/5/merge?x=../y` and compare it with the path gh actually requests
