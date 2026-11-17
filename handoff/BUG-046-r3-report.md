# BUG-046 round 3 report

## Files changed
- `bridge/cursor-bridge/permission-guard.py`
- `bridge/cursor-bridge/MANIFEST.json` (rewritten by `python tools/make-manifest.py`, not by hand)
- `tests/test_bug046.py` (below the builder's marker only)
- `handoff/BUG-046-r3-report.md` (this file, written after the Done commands, so neither `git status` below lists it)

`docs/BUILDER_NOTES.md` was not changed. `bridge/cursor-bridge/VERSION` was restored with `git restore` after `make-manifest.py` and is not in the final status. Its bytes are `2026.11.12a` followed by CRLF.

## Summary
`_check_word_list` now percent-decodes each word of a `gh api` command once, and that one decoding serves both refusals: a merge mutation is still sought, case kept, in the raw word or the decoding, and a pull request's merge endpoint is refused when the lower-cased decoding of any one word holds both `pulls` and `merge`, in either order, with no cut, no `posixpath.normpath`, and no path pattern. `import posixpath` is deleted. Below the marker, three cases cover a word that holds the two names only after decoding, the accepted reverse-order field, and a comments path that passes. No source line was mutated in process.

## Cause
The merge-endpoint refusal no longer parses the path, so an escaped `%3F`, `%23`, or `%2F` cannot split the word away from `pulls` and `merge`: both names are sought in the decoded, lower-cased text of that one word.

## K1
In `_check_word_list` at lines 2345-2349 a `gh api` command is refused with `gh api on a pull request's merge endpoint (merging outside the gate)` when any word of `decoded_w`, lower-cased, contains both `pulls` and `merge`, pinned by `test_bug046_r2_an_escaped_delimiter_never_hides_the_merge_endpoint`, `test_bug046_r1_a_merge_endpoint_hidden_by_a_query_a_dot_segment_or_an_escape_is_refused`, `test_bug046_the_merge_endpoint_is_refused_whatever_the_method_or_spelling`, `test_bug046_a_merge_endpoint_with_a_query_fragment_or_percent_2e_is_refused`, `test_bug046_mergeable_report_is_refused`, `test_bug046_an_issues_merge_endpoint_passes`, `test_bug046_r1_ordinary_calls_with_escapes_or_queries_pass`, `test_bug046_r2_pulls_and_merge_in_separate_words_pass`, `test_bug046_r3_pulls_and_merge_only_after_decoding_are_refused`, `test_bug046_r3_merge_then_pulls_in_one_field_is_refused`, and `test_bug046_r3_pull_request_comments_pass`.

## K2
In `_check_word_list` at lines 2336-2338 each word of `w` is passed through `_percent_decoded` once when `group == "api"`, and that list is what line 2337 searches for `MERGE_MUTATIONS` (case kept, in the raw word or the decoding) and what lines 2346-2348 lower-case for K1, with the mutation refusal still first, pinned by `test_bug046_r1_an_escaped_merge_mutation_name_is_refused` and by the endpoint tests named under K1.

## K3
`import posixpath` is deleted, and the import block is lines 55-60; after the edit a count of the name `posixpath` in `permission-guard.py` is 0, so the guard names it nowhere else.

## K4
Below the marker, `test_bug046_r3_pulls_and_merge_only_after_decoding_are_refused` (lines 277-281) refuses `repos/o/r/pul%6cs/5/m%65rge`, `test_bug046_r3_merge_then_pulls_in_one_field_is_refused` (lines 284-288) refuses `-f 'body=merge the pulls'` and its comment calls that an accepted over-refusal, and `test_bug046_r3_pull_request_comments_pass` (lines 291-295) lets `repos/o/r/pulls/5/comments` through, each under both tools with `ids=["Bash", "PowerShell"]`; every earlier case and its assertion is unchanged.

## Commands
Counts below belong to commit `2c653de54940e8fc041823231096e01dcb777229` with uncommitted changes. The Done steps were one shell, in order, with echo markers that are not part of those programs. The probes ran before that, on the same program text, before `MANIFEST.json` was regenerated.

Probe, before the Done list: `git diff --stat` joined with a line-ending print and `python -m pytest -q -rs tests/test_bug046.py`. The line-ending print labels any file that still contains `\n` after removing `\r\n` as mixed, so an LF-only file is labelled mixed by that print.

```
warning: in the working copy of 'tests/test_bug046.py', LF will be replaced by CRLF the next time Git touches it
 bridge/cursor-bridge/permission-guard.py | 13 +++++--------
 tests/test_bug046.py                     | 22 ++++++++++++++++++++++
 2 files changed, 27 insertions(+), 8 deletions(-)
guard CRLF pure
test LF mixed
........................................................................ [ 50%]
........................................................................ [100%]
144 passed in 13.90s
```

Probe, before the Done list: a count of `\r` in `tests/test_bug046.py`

```
cr count 0
```

Probe, before the Done list: `git diff -- bridge/cursor-bridge/permission-guard.py`

```
diff --git a/bridge/cursor-bridge/permission-guard.py b/bridge/cursor-bridge/permission-guard.py
index 46488b6..633f142 100644
--- a/bridge/cursor-bridge/permission-guard.py
+++ b/bridge/cursor-bridge/permission-guard.py
@@ -54,7 +54,6 @@ passes. ASCII-only on purpose. Never writes.
 """
 import json
 import os
-import posixpath
 import re
 import subprocess
 import sys
@@ -2334,7 +2333,8 @@ def _check_word_list(cmd_wds, command, cwd, tool, mode, depth, slash_ok, fed=Fal
             r = merge_reason(args, cwd)
             if r:
                 return r
-        if group == "api" and any(m in tok or m in _percent_decoded(tok) for tok in w for m in MERGE_MUTATIONS):
+        decoded_w = [_percent_decoded(tok) for tok in w] if group == "api" else []
+        if group == "api" and any(m in tok or m in dec for tok, dec in zip(w, decoded_w) for m in MERGE_MUTATIONS):
             return "gh api with a merge mutation (merging outside the gate)"
         if group == "api" and any(t == "--input" or t.startswith("--input=") or t.startswith("@") or "=@" in t for t in w):
             return "gh api with a body read from a file or standard input, which the guard cannot read (write the query or fields on the command line)"
@@ -2343,12 +2343,9 @@ def _check_word_list(cmd_wds, command, cwd, tool, mode, depth, slash_ok, fed=Fal
             if sub == "import" or re.match(r"^(pr\s+merge|api)\b", expansion) or "worktree" in expansion:
                 return "a gh alias for a merge or an api call (%s)" % " ".join(args)[:60]
         if group == "api":
-            for a in w:
-                decoded = _percent_decoded(a).lower()
-                q, h = decoded.find("?"), decoded.find("#")
-                cuts = [i for i in (q, h) if i >= 0]
-                path = decoded if not cuts else decoded[:min(cuts)]
-                if any(re.search(r"/pulls/[^/]+/merge", part) for part in (decoded, path, posixpath.normpath(path))):
+            for dec in decoded_w:
+                low = dec.lower()
+                if "pulls" in low and "merge" in low:
                     return "gh api on a pull request's merge endpoint (merging outside the gate)"
     return None
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

Done step 4: `python tools/dump-cli.py --check` printed no lines and exited 0.

Done step 5: `git status --short`

```
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/permission-guard.py
 M tests/test_bug046.py
```

Done step 6: `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`

```
bridge-check: version 2026.11.12a (2026-11-17 10:59) at <Workspace>\bridge
bridge-check: 146 OK, 0 STALE, 0 MISSING, 0 EXTRA
RESULT: SOURCES MATCH bridge 2026.11.12a
```

Done step 7: `python -m pytest -q -rs tests/test_bug046.py`

```
........................................................................ [ 50%]
........................................................................ [100%]
144 passed in 14.70s
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
1289 passed in 135.90s (0:02:15)
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
553 passed, 20 skipped in 185.60s (0:03:05)
```

Done step 10: `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks`

```
windowless-check: 39 file(s) scanned, 0 FAIL, 0 NOTE
```

Done step 11: `git rev-parse HEAD` then `git status --short`

```
2c653de54940e8fc041823231096e01dcb777229
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/permission-guard.py
 M tests/test_bug046.py
```

After step 11, in that same shell: `python -c "print(repr(open('bridge/cursor-bridge/VERSION','rb').read()))"`

```
b'2026.11.12a\r\n'
```

After step 11, in that same shell: a count of `posixpath` in `bridge/cursor-bridge/permission-guard.py`

```
posixpath count 0
```

`semgrep` was not run.

## Assumed, not verified
- No new Semgrep high finding · the Done list does not name Semgrep, and it was not run · the project's Semgrep invocation on this diff.
