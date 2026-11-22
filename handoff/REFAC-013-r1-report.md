# REFAC-013 round 1 report

## Files changed

- bridge/cursor-bridge/bridge_env.py
- bridge/cursor-bridge/bridge-run.py
- bridge/cursor-bridge/review-guard.py
- bridge/cursor-bridge/MANIFEST.json

## Summary

Moved the duplicated round-cause word matching from `bridge-run.py` and `review-guard.py` into `bridge_env.round_cause_word` and `_CAUSE_SEPS`, leaving each program its own way of finding the value after `Round cause:`; regenerated `MANIFEST.json` with `make-manifest.py`. Behaviour is unchanged by design.

## Start state

```
git status --short
(empty)

git rev-parse HEAD
f342cb39175dbe44f8a971774eae1ddbfc79d747
```

Working tree was clean at start.

## Requirements 1 (grep before edit)

```
git grep -n -e "_CAUSE_SEPS" -e "ROUND_CAUSES" -- bridge tests
```
```
bridge/cursor-bridge/bridge-run.py:990:ROUND_CAUSES = bridge_env.ROUND_CAUSES
bridge/cursor-bridge/bridge-run.py:996:    round was opened, one of ROUND_CAUSES, read into the run log for pace-report.py. A brief of
bridge/cursor-bridge/bridge-run.py:1001:        return "unstated", "the brief has no `Round cause:` line (one of: %s); logged as unstated" % ", ".join(ROUND_CAUSES)
bridge/cursor-bridge/bridge-run.py:1003:    for cause in sorted(ROUND_CAUSES, key=len, reverse=True):
bridge/cursor-bridge/bridge-run.py:1007:    return "unstated", "the brief's `Round cause:` names none of: %s; logged as unstated" % ", ".join(ROUND_CAUSES)
bridge/cursor-bridge/bridge_env.py:4417:ROUND_CAUSES = (
bridge/cursor-bridge/in-flight.py:261:    if args.cause is not None and args.cause not in bridge_env.ROUND_CAUSES:
bridge/cursor-bridge/pace-report.py:48:and the pass lines (log order); a value is stated when it is on bridge_env.ROUND_CAUSES, and
bridge/cursor-bridge/pace-report.py:52:by `; `, in the report's ROUND_CAUSES order (bridge_env.ROUND_CAUSES, then unstated), zeroes
bridge/cursor-bridge/pace-report.py:508:ROUND_CAUSES = bridge_env.ROUND_CAUSES + ("unstated",)
bridge/cursor-bridge/pace-report.py:526:        seen[(str(row["brief"]), rnd)] = (str(row.get("model") or "unknown"), cause if cause in ROUND_CAUSES else "unstated")
bridge/cursor-bridge/pace-report.py:555:    if isinstance(value, str) and value in bridge_env.ROUND_CAUSES:
bridge/cursor-bridge/pace-report.py:620:    if cause is not None and cause not in bridge_env.ROUND_CAUSES:
bridge/cursor-bridge/pace-report.py:726:    for cause in ROUND_CAUSES:
bridge/cursor-bridge/review-guard.py:127:_CAUSE_SEPS = "-:(,;" + "\u2013" + "\u2014"
bridge/cursor-bridge/review-guard.py:771:    causes = sorted(bridge_env.ROUND_CAUSES, key=len, reverse=True)
bridge/cursor-bridge/review-guard.py:781:            if value.startswith(cause) and (not rest or rest[0] in _CAUSE_SEPS):
tests/test_program_in_flight.py:11:  writes nothing. The round causes stand once, as bridge_env.ROUND_CAUSES, read by the launcher, the pace report and
tests/test_program_in_flight.py:263:    """R-088: the seven round causes of release S stand once, as bridge_env.ROUND_CAUSES, unchanged and first (R-089,
tests/test_program_in_flight.py:266:    assert tuple(env.ROUND_CAUSES)[:7] == SEVEN
tests/test_program_in_flight.py:272:    own: no tuple or list literal of the causes in their source, and each names bridge_env.ROUND_CAUSES."""
tests/test_program_in_flight.py:275:    assert "bridge_env.ROUND_CAUSES" in src, filename
tests/test_program_in_flight.py:285:    assert tuple(getattr(launcher, "ROUND_CAUSES", env.ROUND_CAUSES)) == tuple(env.ROUND_CAUSES)
tests/test_program_in_flight.py:286:    assert tuple(env.ROUND_CAUSES)[:7] == SEVEN
tests/test_program_in_flight.py:287:    report_list = tuple(getattr(report, "ROUND_CAUSES", tuple(env.ROUND_CAUSES) + ("unstated",)))
tests/test_program_in_flight.py:288:    assert report_list[:7] == SEVEN and set(report_list) - set(env.ROUND_CAUSES) <= {"unstated"}
tests/test_program_pace_rounds.py:7:  - bridge_env.ROUND_CAUSES is the one list of round causes, the seven of release S and `base update`; `unstated` is
tests/test_program_pace_rounds.py:232:    """R-089: bridge_env.ROUND_CAUSES is release S's seven causes and `base update`, in that order; `unstated` is no
tests/test_program_pace_rounds.py:235:    assert tuple(be.ROUND_CAUSES) == EIGHT, be.ROUND_CAUSES
tests/test_program_pace_rounds.py:236:    assert "unstated" not in be.ROUND_CAUSES
tests/test_release_s_launcher.py:485:    assert program("pace-report").ROUND_CAUSES == program("bridge-run").ROUND_CAUSES + ("unstated",)
```

`_CAUSE_SEPS` appeared on `review-guard.py:127` (definition) and `review-guard.py:781` (use). No line under `tests/` names `_CAUSE_SEPS`.

```
git grep -n -w -e round_cause_word -- bridge tests
```
```
(empty; exit code 1)
```

```
git grep -l -e "Round cause" -- tests
```
```
tests/test_program_pace_rounds.py
tests/test_release_s_launcher.py
```

## Comparison of the two original matchings

Both programs used the same tuple `bridge_env.ROUND_CAUSES`, sorted by length descending with a stable sort, lowercased the value string before matching, computed `rest = value[len(cause):].lstrip()`, and accepted a cause when `value.startswith(cause)` and either `rest` was empty or `rest[0]` was one of the seven separators `- : ( , ;` plus U+2013 and U+2014. Bridge-run obtained the value from the first `Round cause:` line via `ROUND_CAUSE_RE` and `m.group(1).lower()`; review-guard scanned lines, stripped one trailing carriage return per line, took the first line starting with `Round cause:`, and used `.strip(" \t").lower()` on the suffix. The shared `round_cause_word` receives exactly those prepared value strings from each caller and applies the same longest-first prefix test, so each caller still gets today's cause or `None`, which bridge-run maps to its second note and review-guard maps to `"unstated"` on the first matching line only.

## Behaviour unchanged (one sentence)

Callers still prepare the post-prefix value exactly as before and only the inner cause loop moved to `bridge_env.round_cause_word`, which uses the same list, sort, `lstrip()`, and separator set, so every input still yields the same cause or unstated path.

## What I did not change

`ROUND_CAUSE_RE` and the launcher's two unstated notes; review-guard's line scan, CRLF handling, and first-line-only semantics; `ROUND_CAUSES` in `bridge_env.py`; unrelated `rest[0] in "rR"` in `review-guard.py` line 377.

## Pytest (before edit)

```
python -m pytest -p no:cacheprovider -q -rs tests/test_release_s_launcher.py tests/test_program_pace_rounds.py tests/test_program_in_flight.py tests/test_header_currency.py
```
```
........................................................................ [ 35%]
..................s..................................................... [ 71%]
.........................................................                [100%]
=========================== short test summary info ===========================
SKIPPED [1] tests\test_program_in_flight.py:230: this account cannot create a symbolic link
200 passed, 1 skipped in 45.96s
```

Commit at before run: `f342cb39175dbe44f8a971774eae1ddbfc79d747`, working tree clean.

## Pytest (after last edit)

```
python -m pytest -p no:cacheprovider -q -rs tests/test_release_s_launcher.py tests/test_program_pace_rounds.py tests/test_program_in_flight.py tests/test_header_currency.py
```
```
........................................................................ [ 35%]
..................s..................................................... [ 71%]
.........................................................                [100%]
=========================== short test summary info ===========================
SKIPPED [1] tests\test_program_in_flight.py:230: this account cannot create a symbolic link
200 passed, 1 skipped in 73.31s (0:01:13)
```

Commit: `f342cb39175dbe44f8a971774eae1ddbfc79d747`, working tree held uncommitted changes (see end state).

## make-manifest, dump-cli, bridge-check

```
python tools/make-manifest.py
```
```
make-manifest: version 2026.11.12a, 148 files hashed, VERSION + MANIFEST.json written
```

```
python tools/dump-cli.py --check
```
```
(empty)
```

```
python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet
```
```
bridge-check: version 2026.11.12a (2026-11-22 18:23) at <Workspace>/bridge
bridge-check: 148 OK, 0 STALE, 0 MISSING, 0 EXTRA
RESULT: SOURCES MATCH bridge 2026.11.12a <Workspace>/bridge/cursor-bridge
```

## git diff --numstat

```
git diff --numstat -- bridge/cursor-bridge/VERSION
```
```
(empty)
```

```
git diff --numstat -- bridge/cursor-bridge/bridge_env.py bridge/cursor-bridge/bridge-run.py bridge/cursor-bridge/review-guard.py
```
```
3	4	bridge/cursor-bridge/bridge-run.py
10	0	bridge/cursor-bridge/bridge_env.py
3	6	bridge/cursor-bridge/review-guard.py
```

## Acceptance grep and ASCII

```
git grep -n -w -e _CAUSE_SEPS -- bridge
```
```
bridge/cursor-bridge/bridge_env.py:4428:_CAUSE_SEPS = "-:(,;" + "\u2013" + "\u2014"
bridge/cursor-bridge/bridge_env.py:4434:        if value.startswith(cause) and (not rest or rest[0] in _CAUSE_SEPS):
```

```
git grep -n -F "def round_cause_word(" -- bridge
```
```
bridge/cursor-bridge/bridge_env.py:4431:def round_cause_word(value):
```

```
git grep -n -w -e round_cause_word -- bridge/cursor-bridge/bridge-run.py bridge/cursor-bridge/review-guard.py
```
```
bridge/cursor-bridge/bridge-run.py:1003:    matched = bridge_env.round_cause_word(value)
bridge/cursor-bridge/review-guard.py:777:        matched = bridge_env.round_cause_word(value)
```

```
git grep -n -F "rest[0] in" -- bridge/cursor-bridge/bridge-run.py bridge/cursor-bridge/review-guard.py
```
```
bridge/cursor-bridge/review-guard.py:377:        if len(rest) >= 2 and rest[0] in "rR" and rest[1].isdigit():
```

Note: the brief expects no output here; one pre-existing unrelated line remains (round-number parsing, not round cause).

```
git grep -n -F "ROUND_CAUSES = bridge_env.ROUND_CAUSES" -- bridge/cursor-bridge/bridge-run.py
```
```
bridge/cursor-bridge/bridge-run.py:990:ROUND_CAUSES = bridge_env.ROUND_CAUSES
```

```
git grep -n -w -e ROUND_CAUSE_RE -- bridge
```
```
bridge/cursor-bridge/bridge-run.py:991:ROUND_CAUSE_RE = re.compile(r"^Round cause:[ \t]*(.*?)[ \t]*$", re.M)
bridge/cursor-bridge/bridge-run.py:999:    m = ROUND_CAUSE_RE.search(brief_text or "")
```

```
python -c "import sys; [print(p) for p in sys.argv[1:] if not open(p, 'rb').read().isascii()]" bridge/cursor-bridge/bridge_env.py bridge/cursor-bridge/review-guard.py
```
```
(empty)
```

## End state

```
git status --short
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/bridge-run.py
 M bridge/cursor-bridge/bridge_env.py
 M bridge/cursor-bridge/review-guard.py
 ?? handoff/REFAC-013-r1-report.md
```

```
git diff --stat
 bridge/cursor-bridge/MANIFEST.json   |  8 ++++----
 bridge/cursor-bridge/bridge-run.py   |  7 +++----
 bridge/cursor-bridge/bridge_env.py   | 10 ++++++++++
 bridge/cursor-bridge/review-guard.py |  9 +++------
 4 files changed, 20 insertions(+), 14 deletions(-)
```

```
git rev-parse HEAD
f342cb39175dbe44f8a971774eae1ddbfc79d747
```

Working tree held uncommitted changes at end.

## Assumed, not verified

Assumed, not verified: none.