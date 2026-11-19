# REFAC-011 round 1 report

## Files changed

- `bridge/cursor-bridge/bridge-run.py`
- `bridge/cursor-bridge/MANIFEST.json`
- `handoff/REFAC-011-r1-report.md` (this file)

`docs/BUILDER_NOTES.md` was not changed. No test file was edited.

## Summary

`_watch_decision` now starts the watch on `if failed is not None:` alone, and the fail branch of `watch_loop` keeps a single `head12 = _watch_head12(...)` line. The second evaluation of `_check_holds` on a check `_failed_check` had already accepted, and the second `_watch_head12` call that repeated the same arguments when the poll had no base, are deleted. `MANIFEST.json` was regenerated at version `2026.11.12a`. Behaviour is unchanged: the same `bridge-run:` lines, the same exit codes, the same head in every LIMIT line and after every failed poll, and the same early start or wait under the base's list, the default branch's list and the runs.

## Start state

Working tree before edits: clean (no uncommitted changes). HEAD is `02a38aceb1687daa3f4b263364e742d304ced9ae`, the commit that adds this brief. `494b630` (REFAC-010) is its parent, and the two sites were at the line numbers the Objective names.

```text
git status --short && echo "---HEAD---" && git rev-parse HEAD
---HEAD---
02a38aceb1687daa3f4b263364e742d304ced9ae
```

`git status --short` printed no lines.

```text
git log -5 --oneline && echo "---" && git merge-base --is-ancestor 494b630 HEAD; echo "ancestor-exit:$?" && git rev-parse --short=7 HEAD && git status --short | wc -l
02a38ac REFAC-011: the brief (stage P2's refactoring pass, candidate 5)
494b630 REFAC-010: one resolver of a git rev-parse path, and one snapshot read, in the git-config watch
cadcbdf REFAC-010: the brief (stage P2's refactoring pass, candidate 4)
822212f REFAC-009: one reading of a reader's reply bits and a rule's contexts, in bridge_env
3cc411a REFAC-009: the brief (stage P2's refactoring pass, candidate 2)
---
ancestor-exit:0
02a38ac
0
```

## Requirements 1

Both checks held, so the edit proceeded. The first command printed exactly the two expected lines. The second printed nothing (exit 1).

```text
git grep -n -F -e "_check_holds(failed" -e "if not polled.get(" -- bridge; echo "---GREP2-EXIT:$?---"; git grep -n -w -e _watch_decision -e _failed_check -e _check_holds -e _watch_head12 -- tests; echo "---GREP3-EXIT:$?"
bridge/cursor-bridge/bridge-run.py:2249:    if failed is not None and (named["kind"] != "base" or any(_check_holds(failed, entry) for entry in named["contexts"] or [])):
bridge/cursor-bridge/bridge-run.py:2340:            if not polled.get("base"):
---GREP2-EXIT:0---
---GREP3-EXIT:1---
```

## Why each deleted evaluation already had its value

Site 1. `_failed_check` (bridge-run.py, the function that begins at the line the brief names 2134) sets `contexts = (named["contexts"] or []) if named["kind"] == "base" else None`, then returns the first dict in `latest.get("checks")` whose `status` is `completed` and whose `conclusion` is in `WATCH_FAIL_FAST`, and only when `contexts is None` or `any(_check_holds(item, entry) for entry in contexts)`. Under `named["kind"] == "base"` that `contexts` value is the same list the deleted clause walks, `named["contexts"] or []`, so a returned item has already satisfied `any(_check_holds(item, entry) for entry in (named["contexts"] or []))`. `_watch_name` stores contexts only in its `if contexts:` branch, and `bridge_env.rule_contexts` (bridge_env.py lines 4301-4311) returns `None`, `[]`, or the reply's `contexts` list, so a base name's `named["contexts"]` is that non-empty list and both walks see the same elements. Under every other kind (`"default"`, `"runs"`) `contexts` is `None` and the clause's first operand, `named["kind"] != "base"`, is true, so the `or` is true without the second walk. `_failed_check` has already read `named["kind"]` and `named["contexts"]`, and it does not write to `named`, so the deleted operands cannot raise where that call did not. `_check_holds` (lines 2144-2153) only reads its two arguments: it returns false unless both are dicts, then requires `entry.get("context")` to be a str equal to `item.get("name")`, and when `bridge_env.is_int_id(entry.get("app_id"))` it compares `bridge_env.app_id_of(item)` with that id, otherwise it returns true. `is_int_id` (bridge_env.py lines 4260-4261) returns whether its argument is an `int` and not a `bool`. `app_id_of` (lines 4264-4273) returns `None` unless its argument is a dict whose `app` is a dict whose `id` passes `is_int_id`, and otherwise returns that id. Neither writes. The deleted clause was therefore true whenever `failed is not None`.

Site 2. The kept line is `head12 = _watch_head12(polled.get("local"), polled.get("github") if polled.get("base") else None)`. When `polled.get("base")` is falsy, the second argument is already `None`, so the deleted line `_watch_head12(polled.get("local"), None)` called the same function with the same arguments. When `polled.get("base")` is truthy, that line was not reached. `_watch_head12` (lines 2074-2076) returns `_watch_plain(local or github or "?")[:12]`. `_watch_plain` (lines 2019-2027) builds a new string from its argument (none becomes empty; a tab or newline becomes a space; characters from 32 through 126 are kept; the result is split and joined). `polled` is the dict `_watch_poll` returned, and `.get` only reads it. The deleted assignment stored the string already in `head12`.

## Why the behaviour is identical

The condition that starts the watch on a failed check is true in exactly the same cases, the head shown after a failed poll is the same string with and without a base, and no other line of `watch_loop` or `_watch_decision` changed, so the wait's `bridge-run:` lines, exit codes, LIMIT heads, words passed to the watch, and early start or wait under each of the three lists stay as they were.

## Pytest before the edit

Counts belong to commit `02a38aceb1687daa3f4b263364e742d304ced9ae` with a clean working tree. `191 passed, 5 skipped`.

```text
python -m pytest -p no:cacheprovider -q -rs tests/test_program_watch_wait.py tests/test_bridge_run.py tests/test_header_currency.py
..............................ss...................sss.................. [ 36%]
........................................................................ [ 73%]
....................................................                     [100%]
=========================== short test summary info ===========================
SKIPPED [2] tests\test_program_watch_wait.py:384: a stand-in gh on PATH is a shell script; CI's ubuntu job runs it
SKIPPED [1] tests\test_program_watch_wait.py:600: a stand-in gh on PATH is a shell script; CI's ubuntu job runs it
SKIPPED [1] tests\test_program_watch_wait.py:613: a stand-in gh on PATH is a shell script; CI's ubuntu job runs it
SKIPPED [1] tests\test_program_watch_wait.py:622: a stand-in gh on PATH is a shell script; CI's ubuntu job runs it
191 passed, 5 skipped in 91.67s (0:01:31)
```

## Edit

Line 2249 is `    if failed is not None:`. The fail branch's only `head12 =` line is the former line 2339, unchanged. The `if not polled.get("base"):` re-assignment and its body are gone. No comment was added. The file was rewritten as bytes so every line stays CRLF and no line gained trailing whitespace. The script refused to write if any LF-only newline was already present or if either site occurred more or less than once.

```text
python -c '
from pathlib import Path
p = Path("bridge/cursor-bridge/bridge-run.py")
data = p.read_bytes()
lf_only = data.replace(b"\r\n", b"").count(b"\n")
if lf_only:
    raise SystemExit("lf-only newlines present: %s" % lf_only)
old1 = b"    if failed is not None and (named[\"kind\"] != \"base\" or any(_check_holds(failed, entry) for entry in named[\"contexts\"] or [])):\r\n"
new1 = b"    if failed is not None:\r\n"
if data.count(old1) != 1:
    raise SystemExit("site1 count %s" % data.count(old1))
data = data.replace(old1, new1, 1)
old2 = (
    b"            head12 = _watch_head12(polled.get(\"local\"), polled.get(\"github\") if polled.get(\"base\") else None)\r\n"
    b"            if not polled.get(\"base\"):\r\n"
    b"                head12 = _watch_head12(polled.get(\"local\"), None)\r\n"
)
new2 = b"            head12 = _watch_head12(polled.get(\"local\"), polled.get(\"github\") if polled.get(\"base\") else None)\r\n"
if data.count(old2) != 1:
    raise SystemExit("site2 count %s" % data.count(old2))
data = data.replace(old2, new2, 1)
for i, line in enumerate(data.split(b"\r\n"), 1):
    if line.endswith(b" ") or line.endswith(b"\t"):
        raise SystemExit("trailing whitespace on line %s" % i)
p.write_bytes(data)
print("written", len(data), "crlf", data.count(b"\r\n"))
'
written 141297 crlf 3127
```

## After the last source edit

`python tools/dump-cli.py --check` printed nothing and exited 0. `git diff --numstat -- bridge/cursor-bridge/VERSION` printed no numstat line (a line-ending warning only). `bridge/cursor-bridge/VERSION` reads `2026.11.12a` followed by a single LF (`b'2026.11.12a\n'`). `git diff --numstat -- bridge/cursor-bridge/bridge-run.py` printed `1`, `3` and the path. The repository folder in the bridge-check line below is written `<Workspace>`.

```text
python tools/make-manifest.py && echo "---DUMP---" && python tools/dump-cli.py --check; echo "DUMP_EXIT:$?" && echo "---CHECK---" && python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet && echo "---NUMSTAT-VERSION---" && git diff --numstat -- bridge/cursor-bridge/VERSION && echo "---NUMSTAT-RUN---" && git diff --numstat -- bridge/cursor-bridge/bridge-run.py && echo "---GREP-A---" && git grep -n -F "_check_holds(failed" -- bridge; echo "GREP_A_EXIT:$?" && echo "---GREP-B---" && git grep -n -F "if not polled.get(" -- bridge; echo "GREP_B_EXIT:$?" && echo "---GREP-C---" && git grep -n -F "if failed is not None:" -- bridge; echo "GREP_C_EXIT:$?" && echo "---GREP-D---" && git grep -n -F "head12 = " -- bridge; echo "GREP_D_EXIT:$?"
make-manifest: version 2026.11.12a, 147 files hashed, VERSION + MANIFEST.json written
---DUMP---
DUMP_EXIT:0
---CHECK---
bridge-check: version 2026.11.12a (2026-11-19 06:03) at <Workspace>\bridge
bridge-check: 147 OK, 0 STALE, 0 MISSING, 0 EXTRA
RESULT: SOURCES MATCH bridge 2026.11.12a
---NUMSTAT-VERSION---
warning: in the working copy of 'bridge/cursor-bridge/VERSION', LF will be replaced by CRLF the next time Git touches it
---NUMSTAT-RUN---
1	3	bridge/cursor-bridge/bridge-run.py
---GREP-A---
GREP_A_EXIT:1
---GREP-B---
GREP_B_EXIT:1
---GREP-C---
bridge/cursor-bridge/bridge-run.py:2249:    if failed is not None:
GREP_C_EXIT:0
---GREP-D---
bridge/cursor-bridge/bridge-run.py:2314:    head12 = "?"
bridge/cursor-bridge/bridge-run.py:2339:            head12 = _watch_head12(polled.get("local"), polled.get("github") if polled.get("base") else None)
bridge/cursor-bridge/bridge-run.py:2349:            head12 = _watch_head12(polled.get("local"), None)
bridge/cursor-bridge/bridge-run.py:2357:        head12 = _watch_head12(polled.get("local"), polled.get("github"))
GREP_D_EXIT:0
```

`git grep -n -F "_check_holds(failed" -- bridge` printed nothing. `git grep -n -F "if not polled.get(" -- bridge` printed nothing. `git grep -n -F "if failed is not None:" -- bridge` printed one line, in `bridge/cursor-bridge/bridge-run.py`, inside `_watch_decision`. `git grep -n -F "head12 = " -- bridge` printed four lines, all in `bridge-run.py`: the initial `head12 = "?"`, the fail branch's one, the mismatch branch's and the lists' line.

## Pytest after the last edit

Counts belong to commit `02a38aceb1687daa3f4b263364e742d304ced9ae`. The working tree then held uncommitted changes in `bridge/cursor-bridge/bridge-run.py` and `bridge/cursor-bridge/MANIFEST.json` (this report file was not yet written). `191 passed, 5 skipped`. None failed. The skip count matches the before-edit run (the same five skips in `tests/test_program_watch_wait.py`).

```text
python -m pytest -p no:cacheprovider -q -rs tests/test_program_watch_wait.py tests/test_bridge_run.py tests/test_header_currency.py
..............................ss...................sss.................. [ 36%]
........................................................................ [ 73%]
....................................................                     [100%]
=========================== short test summary info ===========================
SKIPPED [2] tests\test_program_watch_wait.py:384: a stand-in gh on PATH is a shell script; CI's ubuntu job runs it
SKIPPED [1] tests\test_program_watch_wait.py:600: a stand-in gh on PATH is a shell script; CI's ubuntu job runs it
SKIPPED [1] tests\test_program_watch_wait.py:613: a stand-in gh on PATH is a shell script; CI's ubuntu job runs it
SKIPPED [1] tests\test_program_watch_wait.py:622: a stand-in gh on PATH is a shell script; CI's ubuntu job runs it
191 passed, 5 skipped in 92.98s (0:01:32)
```

## End state

Taken after the after-edit pytest and before this report file existed. HEAD is unchanged. The working tree held uncommitted changes. `git diff --stat` lists only `bridge/cursor-bridge/MANIFEST.json` and `bridge/cursor-bridge/bridge-run.py`. `docs/CHANGES.md`, `bridge/cursor-bridge/CHANGELOG.md` and every file under `tests/` are absent from that stat. No mutation script is in the diff.

```text
echo "---STATUS---" && git status --short && echo "---STAT---" && git diff --stat && echo "---HEAD---" && git rev-parse HEAD && echo "---VERSION-BYTES---" && python -c "d=open(r'bridge/cursor-bridge/VERSION','rb').read(); print(repr(d))"
---STATUS---
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/bridge-run.py
---STAT---
warning: in the working copy of 'bridge/cursor-bridge/MANIFEST.json', LF will be replaced by CRLF the next time Git touches it
 bridge/cursor-bridge/MANIFEST.json | 4 ++--
 bridge/cursor-bridge/bridge-run.py | 4 +---
 2 files changed, 3 insertions(+), 5 deletions(-)
---HEAD---
02a38aceb1687daa3f4b263364e742d304ced9ae
---VERSION-BYTES---
b'2026.11.12a\n'
```

After this report file was written, the same HEAD and the same diff stat still hold, and status also lists the new report file.

```text
git status --short && echo "---STAT---" && git diff --stat && echo "---HEAD---" && git rev-parse HEAD
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/bridge-run.py
?? handoff/REFAC-011-r1-report.md
---STAT---
warning: in the working copy of 'bridge/cursor-bridge/MANIFEST.json', LF will be replaced by CRLF the next time Git touches it
 bridge/cursor-bridge/MANIFEST.json | 4 ++--
 bridge/cursor-bridge/bridge-run.py | 4 +---
 2 files changed, 3 insertions(+), 5 deletions(-)
---HEAD---
02a38aceb1687daa3f4b263364e742d304ced9ae
```

## Noticed but not changed

The assignment the brief names at line 2376, now line 2374, is still `restart = seen_watch and named["kind"] == "runs"`. `seen_watch` is set only after a watch returns, and the function returns immediately for every kind but `"runs"`, and `named` is not reassigned once set, so the kind test repeats a fact already fixed by `seen_watch`. It is not this candidate. `finish_limit` still computes its own twelve characters from a fresh `local_head` when `problem` is absent. The mismatch branch and the lists path still call `_watch_head12` themselves (now lines 2349 and 2357). `_watch_decision`'s docstring is unchanged. No name was added, renamed or removed, and `bridge-run.py` imports nothing new.

## Assumed, not verified

Assumed, not verified: none
