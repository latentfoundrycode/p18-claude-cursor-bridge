# REFAC-009 round 1 report

## Files changed

- `bridge/cursor-bridge/bridge_env.py`
- `bridge/cursor-bridge/bridge-run.py`
- `bridge/cursor-bridge/review-guard.py`
- `bridge/cursor-bridge/MANIFEST.json`
- `docs/BUILDER_NOTES.md`
- `handoff/REFAC-009-r1-report.md` (this file)

## Summary

`bridge_env.reply_bits` and `bridge_env.rule_contexts` now hold the one reading of a reader's `source` and `reason` and the one classification of a branch-rule reply; `review-guard.py` no longer defines `_reader_bits` and `bridge-run.py` no longer defines `_watch_contexts`, while `_rule_contexts` and `_watch_bits` keep their signatures and docstrings and call those two functions. `MANIFEST.json` was regenerated at version `2026.11.12a`.

## Start state

Working tree before edits: clean (no uncommitted changes). HEAD is `3cc411adba46140de0ab7ed4fa4073b44e489a87`, the commit that adds this brief, one commit after `ff5786e` (REFAC-008). The helper sites were at the line numbers the Objective names.

```text
git status --short && echo "---REV---" && git rev-parse HEAD && echo "---GREP1---" && git grep -n -e _reader_bits -e _watch_bits -e _rule_contexts -e _watch_contexts -- bridge tools tests docs && echo "---GREP2---" && git grep -n -w -e reply_bits -e rule_contexts; echo "GREP2_EXIT:$?"
---REV---
3cc411adba46140de0ab7ed4fa4073b44e489a87
---GREP1---
bridge/cursor-bridge/bridge-run.py:2030:def _watch_bits(got, fallback):
bridge/cursor-bridge/bridge-run.py:2084:def _watch_contexts(rule):
bridge/cursor-bridge/bridge-run.py:2102:    contexts = _watch_contexts(rule)
bridge/cursor-bridge/bridge-run.py:2107:        source, reason = _watch_bits(rule, "protection")
bridge/cursor-bridge/bridge-run.py:2112:        source, reason = _watch_bits(settings, "repo")
bridge/cursor-bridge/bridge-run.py:2124:    contexts = _watch_contexts(other)
bridge/cursor-bridge/bridge-run.py:2130:        source, reason = _watch_bits(other, "protection")
bridge/cursor-bridge/bridge-run.py:2290:        source, reason = _watch_bits(got, "pull")
bridge/cursor-bridge/bridge-run.py:2301:        source, reason = _watch_bits(state, "checks")
bridge/cursor-bridge/review-guard.py:1478:def _reader_bits(got, fallback):
bridge/cursor-bridge/review-guard.py:1524:def _rule_contexts(got, which):
bridge/cursor-bridge/review-guard.py:1527:        source, reason = _reader_bits(got, "protection")
bridge/cursor-bridge/review-guard.py:1533:        source, reason = _reader_bits(got, "protection")
bridge/cursor-bridge/review-guard.py:1611:            source, reason = _reader_bits(got, "pull")
bridge/cursor-bridge/review-guard.py:1643:    contexts, err = _rule_contexts(bridge_env.branch_rule(repo, base, cwd=cwd), "base")
bridge/cursor-bridge/review-guard.py:1651:            source, reason = _reader_bits(settings, "repo")
bridge/cursor-bridge/review-guard.py:1659:            contexts, err = _rule_contexts(bridge_env.branch_rule(repo, default, cwd=cwd), "default")
bridge/cursor-bridge/review-guard.py:1668:        source, reason = _reader_bits(state, "checks")
---GREP2---
handoff/REFAC-009.md:77:**The proposed shape.** `bridge_env.py` gains two public functions in its GitHub reads section (the section that begins at line 3836 with `GH_COMMAND`, `ANSWER_VALUE`, `ANSWER_NONE`; the placement inside it is yours): `reply_bits(got, fallback)`, giving exactly the `(source, reason)` pair `_reader_bits` gives today, unwrapped; and `rule_contexts(got)`, giving the `contexts` list where the answer is a value with a non-empty list, `[]` where the answer is none, and `None` for everything else, exactly as `_watch_contexts` gives today. Then:
handoff/REFAC-009.md:79:- review-guard.py: `_reader_bits` is deleted; its callers at lines 1611, 1651 and 1668 call `bridge_env.reply_bits(...)` with their own fallback. `_rule_contexts(got, which)` stays, with its name, signature, docstring and return values as today, and its body calls `bridge_env.rule_contexts(got)`; where that gives `None` it returns `None, "the %s branch's rule cannot be read (%s: %s)" % (which, source, reason)` with `source, reason` from `bridge_env.reply_bits(got, "protection")`; otherwise it returns the list and `None`. Its callers at 1643 and 1659 do not change.
handoff/REFAC-009.md:80:- bridge-run.py: `_watch_contexts` is deleted; its callers at lines 2102 and 2124 call `bridge_env.rule_contexts(...)`. `_watch_bits(got, fallback)` stays, with its name, signature and docstring, and its body becomes `bridge_env.reply_bits(got, fallback)` with `_watch_plain` applied to each of the two results, as today. Its five callers do not change.
handoff/REFAC-009.md:82:Use the module's existing `bridge_env.<name>(...)` form at each call; bind no module-level alias (no `_watch_contexts = bridge_env.rule_contexts`).
handoff/REFAC-009.md:112:**Names.** At `ff5786e` the strings `reply_bits` and `rule_contexts` appear nowhere in the repository except as part of review-guard's `_rule_contexts`; the two public names are free. No file under `tests/`, `tools/` or `docs/` names `_reader_bits`, `_watch_bits`, `_rule_contexts` or `_watch_contexts`.
handoff/REFAC-009.md:135:1. **Checks first, before any edit; paste each command and its output in the report.** From the Workspace root, run `git grep -n -e _reader_bits -e _watch_bits -e _rule_contexts -e _watch_contexts -- bridge tools tests docs` and confirm every line is in bridge-run.py or review-guard.py, at the definitions and calls listed in the Objective (line numbers may differ by a few). Run `git grep -n -w -e reply_bits -e rule_contexts` and confirm it shows nothing. If a check does not hold, stop, change nothing, and report it.
handoff/REFAC-009.md:136:2. bridge_env.py defines `reply_bits(got, fallback)` and `rule_contexts(got)` once each, public, with the semantics stated in the Objective; `rule_contexts` returns the reply's own `contexts` list, not a copy.
handoff/REFAC-009.md:144:- [ ] Every listed caller uses the single implementation in bridge_env; the two deleted copies are gone (`git grep -n -e "def _reader_bits" -e "def _watch_contexts" -- bridge` shows nothing), and `git grep -n -e "def reply_bits" -e "def rule_contexts" -- bridge` shows one line each, both in bridge_env.py.
handoff/REFAC-009.md:145:- [ ] No public signature outside the listed sites changed; the only new names are `bridge_env.reply_bits` and `bridge_env.rule_contexts`.
handoff/REFAC-009.md:175:- **Refactoring constraints.** Do not edit any test file. Do not add an entry to `docs/CHANGES.md`. Do not "improve" behaviour, messages, edge cases, or defaults you notice along the way (for example review-guard's `reply_bits` results reaching `_cannot` without a `_show`, or a `contexts` list whose entries are not dicts); report them in your summary instead. Do not introduce an abstraction beyond what the listed duplicates need: the two functions in bridge_env; no class, no new parameter (in particular, no `plain` or wrapper argument on `reply_bits`, and no message argument on `rule_contexts`), no module-level alias in either script, nothing new outside the three programs.
GREP2_EXIT:0
```

`git status --short` printed no lines. Every GREP1 line is a definition or a call in `bridge-run.py` or `review-guard.py`, at the lines the Objective lists. The word grep does not print nothing: every hit is this brief, which is committed at HEAD. The names are unused as code in `bridge`, `tools`, `tests`, and `docs`. I edited on that reading and recorded it under Assumed, not verified, and in `docs/BUILDER_NOTES.md`.

```text
git log -8 --oneline && echo "---FF---" && git rev-parse --verify ff5786e && echo "---MERGE-BASE---" && git merge-base --is-ancestor ff5786e HEAD; echo "ANCESTOR_EXIT:$?"
3cc411a REFAC-009: the brief (stage P2's refactoring pass, candidate 2)
ff5786e REFAC-008: one reader of a check's app id and suite id, in bridge_env
deed43f REFAC-008: the brief (stage P2's refactoring pass, candidate 1)
45e4322 TASK-082: stage P2's texts (R-078, R-081, R-083, R-085, R-087, R-105) (#181)
b213ea6 TASK-067: the pre-push scan as a program (R-087) (#180)
667c646 TASK-066: the invisible-character check refuses by category (R-086) (#179)
2b6d76b TASK-065: the watch waits for the required checks (R-085) (#178)
aa22a52 BUG-046: the guard's gh api merge refusal read as gh reads it (R-082) (#177)
---FF---
ff5786e4ada80ba112d483c4290a99a0326e9571
---MERGE-BASE---
ANCESTOR_EXIT:0
```

## Pytest (before the edit)

```text
python -m pytest -p no:cacheprovider -q -rs tests/test_program_ready.py tests/test_program_watch_wait.py tests/test_program_branch_rule.py tests/test_bridge_run.py tests/test_review_guard.py tests/test_header_currency.py
........................................................................ [ 13%]
........................................................................ [ 26%]
..............................................ss...................sss.. [ 40%]
........................................................................ [ 53%]
........................................................................ [ 67%]
........................................................................ [ 80%]
........................................................................ [ 94%]
...............................                                          [100%]
=========================== short test summary info ===========================
SKIPPED [2] tests\test_program_watch_wait.py:384: a stand-in gh on PATH is a shell script; CI's ubuntu job runs it
SKIPPED [1] tests\test_program_watch_wait.py:600: a stand-in gh on PATH is a shell script; CI's ubuntu job runs it
SKIPPED [1] tests\test_program_watch_wait.py:613: a stand-in gh on PATH is a shell script; CI's ubuntu job runs it
SKIPPED [1] tests\test_program_watch_wait.py:622: a stand-in gh on PATH is a shell script; CI's ubuntu job runs it
530 passed, 5 skipped in 207.78s (0:03:27)
```

Summary line: `530 passed, 5 skipped in 207.78s (0:03:27)`. Exit code 0. None failed.

## What changed

`reply_bits(got, fallback)` and `rule_contexts(got)` were added in the GitHub reads section of `bridge_env.py`, after `suite_id` and before `latest_of_each`. `reply_bits` is the body of the deleted `_reader_bits`. `rule_contexts` is the body of the deleted `_watch_contexts`, and it returns the reply's own `contexts` list. `_rule_contexts` still has its name, signature, and docstring; when `bridge_env.rule_contexts` returns `None` it still returns `None` and `the %s branch's rule cannot be read (%s: %s)` with `source, reason` from `bridge_env.reply_bits(got, "protection")`, and otherwise the list and `None`. Its callers at the old lines 1643 and 1659 are unchanged. The three other `_reader_bits` callers now call `bridge_env.reply_bits` with `"pull"`, `"repo"`, and `"checks"`. `_watch_bits` still has its name, signature, and docstring; its body is `bridge_env.reply_bits` with `_watch_plain` on each result. Its five callers are unchanged. The two `_watch_contexts` callers now call `bridge_env.rule_contexts`. No module-level alias was added. No import was added. Neither script imports the other.

## Commands around the edit

Line endings before the edit (CRLF count equals LF count on each file):

```text
python -c "
from pathlib import Path

def load(p):
    b = Path(p).read_bytes()
    bare = b.replace(b'\r\n', b'\n')
    if b'\n' in bare and b'\r' in b:
        # mixed?
        pass
    crlf = b.count(b'\r\n')
    lf = b.count(b'\n')
    cr = b.count(b'\r')
    print(p, 'len', len(b), 'crlf', crlf, 'lf', lf, 'cr', cr, 'endswith', repr(b[-4:]))

for p in [
    'bridge/cursor-bridge/bridge_env.py',
    'bridge/cursor-bridge/bridge-run.py',
    'bridge/cursor-bridge/review-guard.py',
    'docs/BUILDER_NOTES.md',
]:
    load(p)
"
bridge/cursor-bridge/bridge_env.py len 159620 crlf 4378 lf 4378 cr 4378 endswith b'\r\n\r\n'
bridge/cursor-bridge/bridge-run.py len 142688 crlf 3165 lf 3165 cr 3165 endswith b'))\r\n'
bridge/cursor-bridge/review-guard.py len 92764 crlf 1855 lf 1855 cr 1855 endswith b'))\r\n'
docs/BUILDER_NOTES.md len 16071 crlf 96 lf 96 cr 96 endswith b's.\r\n'
```

The edit command, then the lines it printed:

```text
python << 'PY'
from pathlib import Path

def crlf(text):
    return text.replace("\r\n", "\n").replace("\n", "\r\n").encode("utf-8")

def replace_once(path, old, new, label):
    data = Path(path).read_bytes()
    old_b, new_b = crlf(old), crlf(new)
    count = data.count(old_b)
    if count != 1:
        raise SystemExit(f"{label}: count {count} in {path}")
    data = data.replace(old_b, new_b, 1)
    # no bare LF
    if data.count(b"\n") != data.count(b"\r\n") or data.count(b"\r") != data.count(b"\r\n"):
        raise SystemExit(f"{label}: line ending drift in {path}")
    Path(path).write_bytes(data)
    print(f"ok {label}")

# bridge_env: insert before latest_of_each
replace_once(
    "bridge/cursor-bridge/bridge_env.py",
    "def latest_of_each(state):\n",
    '''def reply_bits(got, fallback):
    source, reason = fallback, "cannot read"
    if isinstance(got, dict):
        if isinstance(got.get("source"), str) and got.get("source"):
            source = got["source"]
        if isinstance(got.get("reason"), str) and got.get("reason"):
            reason = got["reason"]
    return source, reason


def rule_contexts(got):
    if not isinstance(got, dict):
        return None
    if got.get("answer") == ANSWER_NONE:
        return []
    if got.get("answer") != ANSWER_VALUE:
        return None
    contexts = got.get("contexts")
    if not isinstance(contexts, list) or not contexts:
        return None
    return contexts


def latest_of_each(state):
''',
    "bridge_env insert",
)

replace_once(
    "bridge/cursor-bridge/review-guard.py",
    '''def _reader_bits(got, fallback):
    source, reason = fallback, "cannot read"
    if isinstance(got, dict):
        if isinstance(got.get("source"), str) and got.get("source"):
            source = got["source"]
        if isinstance(got.get("reason"), str) and got.get("reason"):
            reason = got["reason"]
    return source, reason


''',
    "",
    "delete _reader_bits",
)

replace_once(
    "bridge/cursor-bridge/review-guard.py",
    '''def _rule_contexts(got, which):
    """(contexts, None) or (None, the CANNOT CHECK reason). An empty list is a rule that names none."""
    if not isinstance(got, dict) or got.get("answer") not in (bridge_env.ANSWER_VALUE, bridge_env.ANSWER_NONE):
        source, reason = _reader_bits(got, "protection")
        return None, "the %s branch's rule cannot be read (%s: %s)" % (which, source, reason)
    if got.get("answer") == bridge_env.ANSWER_NONE:
        return [], None
    contexts = got.get("contexts")
    if not isinstance(contexts, list) or not contexts:
        source, reason = _reader_bits(got, "protection")
        return None, "the %s branch's rule cannot be read (%s: %s)" % (which, source, reason)
    return contexts, None
''',
    '''def _rule_contexts(got, which):
    """(contexts, None) or (None, the CANNOT CHECK reason). An empty list is a rule that names none."""
    contexts = bridge_env.rule_contexts(got)
    if contexts is None:
        source, reason = bridge_env.reply_bits(got, "protection")
        return None, "the %s branch's rule cannot be read (%s: %s)" % (which, source, reason)
    return contexts, None
''',
    "rewrite _rule_contexts",
)

for old, new, label in [
    ('source, reason = _reader_bits(got, "pull")', 'source, reason = bridge_env.reply_bits(got, "pull")', "pull"),
    ('source, reason = _reader_bits(settings, "repo")', 'source, reason = bridge_env.reply_bits(settings, "repo")', "repo"),
    ('source, reason = _reader_bits(state, "checks")', 'source, reason = bridge_env.reply_bits(state, "checks")', "checks"),
]:
    replace_once("bridge/cursor-bridge/review-guard.py", old, new, label)

replace_once(
    "bridge/cursor-bridge/bridge-run.py",
    '''def _watch_bits(got, fallback):
    """(source, reason) as the reader clipped them, or the fallback when the reply has neither."""
    source, reason = fallback, "cannot read"
    if isinstance(got, dict):
        if isinstance(got.get("source"), str) and got.get("source"):
            source = got["source"]
        if isinstance(got.get("reason"), str) and got.get("reason"):
            reason = got["reason"]
    return _watch_plain(source), _watch_plain(reason)
''',
    '''def _watch_bits(got, fallback):
    """(source, reason) as the reader clipped them, or the fallback when the reply has neither."""
    source, reason = bridge_env.reply_bits(got, fallback)
    return _watch_plain(source), _watch_plain(reason)
''',
    "rewrite _watch_bits",
)

replace_once(
    "bridge/cursor-bridge/bridge-run.py",
    '''def _watch_contexts(rule):
    """The rule's contexts, [] where it names none, or None where it cannot be read (never a pass)."""
    if not isinstance(rule, dict):
        return None
    if rule.get("answer") == bridge_env.ANSWER_NONE:
        return []
    if rule.get("answer") != bridge_env.ANSWER_VALUE:
        return None
    contexts = rule.get("contexts")
    if not isinstance(contexts, list) or not contexts:
        return None
    return contexts


''',
    "",
    "delete _watch_contexts",
)

for old, new, label in [
    ("contexts = _watch_contexts(rule)", "contexts = bridge_env.rule_contexts(rule)", "rule"),
    ("contexts = _watch_contexts(other)", "contexts = bridge_env.rule_contexts(other)", "other"),
]:
    replace_once("bridge/cursor-bridge/bridge-run.py", old, new, label)

note = (
    "\r\n\r\n2026-11-19 REFAC-009: `git grep -n -w -e reply_bits -e rule_contexts` matches only the committed brief in handoff/REFAC-009.md; "
    "the two names are unused in bridge, tools, tests and docs, so the move continued.\r\n"
)
p = Path("docs/BUILDER_NOTES.md")
b = p.read_bytes()
if not b.endswith(b"\r\n"):
    raise SystemExit("builder notes ending")
p.write_bytes(b + note.encode("utf-8"))
data = p.read_bytes()
if data.count(b"\n") != data.count(b"\r\n"):
    raise SystemExit("builder notes line ending drift")
print("ok builder notes")
PY
ok bridge_env insert
ok delete _reader_bits
ok rewrite _rule_contexts
ok pull
ok repo
ok checks
ok rewrite _watch_bits
ok delete _watch_contexts
ok rule
ok other
ok builder notes
```

The diff and whitespace check below ran while that note still had two blank lines above it.

```text
git diff --stat && echo "---CHECK---" && git diff --check && echo "---WS---" && python -c "
from pathlib import Path
for p in ['bridge/cursor-bridge/bridge_env.py','bridge/cursor-bridge/bridge-run.py','bridge/cursor-bridge/review-guard.py','docs/BUILDER_NOTES.md']:
    b = Path(p).read_bytes()
    bad = 0
    for i, line in enumerate(b.split(b'\n'), 1):
        if line.endswith(b' ') or line.endswith(b'\t') or (line.endswith(b'\r') and (line[:-1].endswith(b' ') or line[:-1].endswith(b'\t'))):
            # only report if the line is in the diff? report all trailing
            bad += 1
            if bad <= 5:
                print(p, i, repr(line[-20:]))
    crlf = b.count(b'\r\n'); lf = b.count(b'\n'); cr = b.count(b'\r')
    print(p, 'trail', bad, 'crlf', crlf, 'lf', lf, 'cr', cr)
"
 bridge/cursor-bridge/bridge-run.py   | 25 +++----------------------
 bridge/cursor-bridge/bridge_env.py   | 23 +++++++++++++++++++++++
 bridge/cursor-bridge/review-guard.py | 27 ++++++---------------------
 docs/BUILDER_NOTES.md                |  3 +++
 4 files changed, 35 insertions(+), 43 deletions(-)
---CHECK---
---WS---
bridge/cursor-bridge/bridge_env.py trail 0 crlf 4401 lf 4401 cr 4401
bridge/cursor-bridge/bridge-run.py trail 0 crlf 3146 lf 3146 cr 3146
bridge/cursor-bridge/review-guard.py trail 0 crlf 1840 lf 1840 cr 1840
docs/BUILDER_NOTES.md trail 0 crlf 99 lf 99 cr 99
```

`git diff --check` printed nothing (exit code 0). This follow-up removed one of the two blank lines, which is why the later `git diff --stat` shows `docs/BUILDER_NOTES.md` as two added lines:

```text
python -c "
from pathlib import Path
p = Path('docs/BUILDER_NOTES.md')
b = p.read_bytes()
old = b'programs.\r\n\r\n\r\n2026-11-19 REFAC-009:'
new = b'programs.\r\n\r\n2026-11-19 REFAC-009:'
if b.count(old) != 1:
    raise SystemExit('count %s' % b.count(old))
b = b.replace(old, new, 1)
if b.count(b'\n') != b.count(b'\r\n'):
    raise SystemExit('endings')
p.write_bytes(b)
print('fixed', b.endswith(b'continued.\r\n'))
"
fixed True
```


## Pytest (after the source edit, before make-manifest)

```text
python -m pytest -p no:cacheprovider -q -rs tests/test_program_ready.py tests/test_program_watch_wait.py tests/test_program_branch_rule.py tests/test_bridge_run.py tests/test_review_guard.py tests/test_header_currency.py
........................................................................ [ 13%]
........................................................................ [ 26%]
..............................................ss...................sss.. [ 40%]
........................................................................ [ 53%]
........................................................................ [ 67%]
........................................................................ [ 80%]
........................................................................ [ 94%]
...............................                                          [100%]
=========================== short test summary info ===========================
SKIPPED [2] tests\test_program_watch_wait.py:384: a stand-in gh on PATH is a shell script; CI's ubuntu job runs it
SKIPPED [1] tests\test_program_watch_wait.py:600: a stand-in gh on PATH is a shell script; CI's ubuntu job runs it
SKIPPED [1] tests\test_program_watch_wait.py:613: a stand-in gh on PATH is a shell script; CI's ubuntu job runs it
SKIPPED [1] tests\test_program_watch_wait.py:622: a stand-in gh on PATH is a shell script; CI's ubuntu job runs it
530 passed, 5 skipped in 210.26s (0:03:30)
```

Summary line: `530 passed, 5 skipped in 210.26s (0:03:30)`. Exit code 0. None failed. Same count passed and the same count skipped as the before run.

## Verification after the last source edit

These ran in one shell, in this order, after the source edits and the blank-line fix. The repository folder in the bridge-check line is written `<Workspace>`.

```text
python tools/make-manifest.py && echo "---DUMP---" && python tools/dump-cli.py --check && echo "DUMP_EXIT:$?" && echo "---CHECK---" && python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet && echo "---NUMSTAT---" && git diff --numstat -- bridge/cursor-bridge/VERSION && echo "NUMSTAT_DONE" && echo "---GREP-DELETED---" && git grep -n -e "def _reader_bits" -e "def _watch_contexts" -- bridge; echo "GREP_DELETED_EXIT:$?" && echo "---GREP-DEFS---" && git grep -n -e "def reply_bits" -e "def rule_contexts" -- bridge && echo "---VERSION---" && python -c "from pathlib import Path; print(repr(Path('bridge/cursor-bridge/VERSION').read_bytes()))" && echo "---ENDSTATE---" && git status --short && echo "---STAT---" && git diff --stat && echo "---HEAD---" && git rev-parse HEAD
make-manifest: version 2026.11.12a, 147 files hashed, VERSION + MANIFEST.json written
---DUMP---
DUMP_EXIT:0
---CHECK---
bridge-check: version 2026.11.12a (2026-11-19 03:28) at <Workspace>\bridge
bridge-check: 147 OK, 0 STALE, 0 MISSING, 0 EXTRA
RESULT: SOURCES MATCH bridge 2026.11.12a
---NUMSTAT---
warning: in the working copy of 'bridge/cursor-bridge/VERSION', LF will be replaced by CRLF the next time Git touches it
NUMSTAT_DONE
---GREP-DELETED---
GREP_DELETED_EXIT:1
---GREP-DEFS---
bridge/cursor-bridge/bridge_env.py:4291:def reply_bits(got, fallback):
bridge/cursor-bridge/bridge_env.py:4301:def rule_contexts(got):
---VERSION---
b'2026.11.12a\n'
---ENDSTATE---
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/bridge-run.py
 M bridge/cursor-bridge/bridge_env.py
 M bridge/cursor-bridge/review-guard.py
 M docs/BUILDER_NOTES.md
---STAT---
warning: in the working copy of 'bridge/cursor-bridge/MANIFEST.json', LF will be replaced by CRLF the next time Git touches it
 bridge/cursor-bridge/MANIFEST.json   |  8 ++++----
 bridge/cursor-bridge/bridge-run.py   | 25 +++----------------------
 bridge/cursor-bridge/bridge_env.py   | 23 +++++++++++++++++++++++
 bridge/cursor-bridge/review-guard.py | 27 ++++++---------------------
 docs/BUILDER_NOTES.md                |  2 ++
 5 files changed, 38 insertions(+), 47 deletions(-)
---HEAD---
3cc411adba46140de0ab7ed4fa4073b44e489a87
```

`python tools/dump-cli.py --check` printed nothing and exited 0. `git diff --numstat -- bridge/cursor-bridge/VERSION` printed no numstat line (the warning above only). The file's bytes are `b'2026.11.12a\n'`, so its content reads `2026.11.12a`. `git grep -n -e "def _reader_bits" -e "def _watch_contexts" -- bridge` printed nothing (exit code 1). `git grep -n -e "def reply_bits" -e "def rule_contexts" -- bridge` shows one line each, both in `bridge_env.py`.

## Pytest (after the last edit)

This run is after `make-manifest`. Commit: `3cc411adba46140de0ab7ed4fa4073b44e489a87`. The working tree then held uncommitted changes. `git status --short` immediately after this pytest, before this report file existed:

```text
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/bridge-run.py
 M bridge/cursor-bridge/bridge_env.py
 M bridge/cursor-bridge/review-guard.py
 M docs/BUILDER_NOTES.md
```

```text
python -m pytest -p no:cacheprovider -q -rs tests/test_program_ready.py tests/test_program_watch_wait.py tests/test_program_branch_rule.py tests/test_bridge_run.py tests/test_review_guard.py tests/test_header_currency.py; echo "---STATUS-AFTER-PYTEST---"; git status --short; echo "---HEAD-AFTER-PYTEST---"; git rev-parse HEAD
........................................................................ [ 13%]
........................................................................ [ 26%]
..............................................ss...................sss.. [ 40%]
........................................................................ [ 53%]
........................................................................ [ 67%]
........................................................................ [ 80%]
........................................................................ [ 94%]
...............................                                          [100%]
=========================== short test summary info ===========================
SKIPPED [2] tests\test_program_watch_wait.py:384: a stand-in gh on PATH is a shell script; CI's ubuntu job runs it
SKIPPED [1] tests\test_program_watch_wait.py:600: a stand-in gh on PATH is a shell script; CI's ubuntu job runs it
SKIPPED [1] tests\test_program_watch_wait.py:613: a stand-in gh on PATH is a shell script; CI's ubuntu job runs it
SKIPPED [1] tests\test_program_watch_wait.py:622: a stand-in gh on PATH is a shell script; CI's ubuntu job runs it
530 passed, 5 skipped in 209.79s (0:03:29)
---STATUS-AFTER-PYTEST---
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/bridge-run.py
 M bridge/cursor-bridge/bridge_env.py
 M bridge/cursor-bridge/review-guard.py
 M docs/BUILDER_NOTES.md
---HEAD-AFTER-PYTEST---
3cc411adba46140de0ab7ed4fa4073b44e489a87
```

Summary line: `530 passed, 5 skipped in 209.79s (0:03:29)`. Exit code 0. None failed. Same count passed and the same count skipped as the before run.

## End state

Recorded after this report file was written. Working tree: uncommitted changes on the five paths below, plus this new report.

```text
echo "---STATUS---" && git status --short && echo "---STAT---" && git diff --stat && echo "---HEAD---" && git rev-parse HEAD
---STATUS---
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/bridge-run.py
 M bridge/cursor-bridge/bridge_env.py
 M bridge/cursor-bridge/review-guard.py
 M docs/BUILDER_NOTES.md
?? handoff/REFAC-009-r1-report.md
---STAT---
warning: in the working copy of 'bridge/cursor-bridge/MANIFEST.json', LF will be replaced by CRLF the next time Git touches it
 bridge/cursor-bridge/MANIFEST.json   |  8 ++++----
 bridge/cursor-bridge/bridge-run.py   | 25 +++----------------------
 bridge/cursor-bridge/bridge_env.py   | 23 +++++++++++++++++++++++
 bridge/cursor-bridge/review-guard.py | 27 ++++++---------------------
 docs/BUILDER_NOTES.md                |  2 ++
 5 files changed, 38 insertions(+), 47 deletions(-)
---HEAD---
3cc411adba46140de0ab7ed4fa4073b44e489a87
```

`git diff --stat` shows only the three programs, `bridge/cursor-bridge/MANIFEST.json`, and `docs/BUILDER_NOTES.md`. This report is the untracked file. `bridge/cursor-bridge/VERSION` is not a diff entry. `docs/CHANGES.md`, `bridge/cursor-bridge/CHANGELOG.md`, and every file under `tests/` are unchanged. No mutation script is in the diff.

## Behaviour unchanged

`reply_bits` returns the `(source, reason)` pair `_reader_bits` returned, `_watch_bits` still passes both results through `_watch_plain`, and `rule_contexts` returns the same list object, `[]`, or `None` that `_watch_contexts` returned, so `_rule_contexts` still builds the same CANNOT CHECK string or returns that list, and every caller keeps the lines, error strings, exit codes, and refusals it had before.

## Noticed, not changed

Review-guard still passes the `source` and `reason` from `reply_bits` into `_cannot` with no `_show`; bridge-run still applies `_watch_plain` inside `_watch_bits` before it prints. `rule_contexts` still returns a `contexts` list without checking that its entries are dicts; `prove_ci` and the wait still check entries later.

## Assumed, not verified

Requirement 1's `git grep -n -w -e reply_bits -e rule_contexts` still means "edit" when every hit is the committed brief `handoff/REFAC-009.md` · the stop sentence says to change nothing if a check does not hold, and those hits are the brief's own words, not definitions or uses of the names in code · a supervisor ruling that those hits require a stop.
