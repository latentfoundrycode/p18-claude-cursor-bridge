# REFAC-008 round 1 report

## Files changed

- `bridge/cursor-bridge/bridge_env.py`
- `bridge/cursor-bridge/bridge-run.py`
- `bridge/cursor-bridge/review-guard.py`
- `bridge/cursor-bridge/MANIFEST.json`
- `docs/BUILDER_NOTES.md`
- `handoff/REFAC-008-r1-report.md` (this file)

## Summary

`bridge_env` now defines `is_int_id`, `app_id_of`, and `suite_id` once, in place of its private `_suite_id` and `_app_id_of`, and `latest_of_each`, the CI watch in `bridge-run.py`, and `prove_ci` / `_context_result` in `review-guard.py` call those three functions; the six script copies are gone. A non-dict item yields `None`, a bool is not an id, and every other key path is the one the copies read. `MANIFEST.json` was regenerated at version `2026.11.12a`.

## Start state

Working tree before edits: clean (no uncommitted changes).

```text
git status --short && echo "---REV---" && git rev-parse HEAD
---REV---
deed43f65edfc92367e22a0875db2ff98bdd92c7
```

`git status --short` printed no lines.

## Requirements 1 (grep before edit)

The helper definitions and calls sit in the three programs at the line numbers the Objective names. Two extra classes of hit are not those helpers: every `check_suite_id` line is the JSON key the brief allows, and `tests/test_loop_guard.py:225` is the substring `_check_app` inside `test_the_run_sheet_check_applies_in_every_phase_and_blocks_the_stop`. The word grep of the three public names matches only this brief, which is committed, so that command does not print nothing. The names are unused as code. I edited on that reading and recorded it under Assumed, not verified, and in `docs/BUILDER_NOTES.md`.

```text
git grep -n -e _suite_id -e _app_id_of -e _watch_suite -e _run_suite -e _watch_app -e _check_app -e _named_app -- bridge tools tests
bridge/cursor-bridge/bridge-run.py:2137:def _watch_suite(item):
bridge/cursor-bridge/bridge-run.py:2147:def _run_suite(run):
bridge/cursor-bridge/bridge-run.py:2150:    value = run.get("check_suite_id")
bridge/cursor-bridge/bridge-run.py:2158:    suite = _run_suite(run)
bridge/cursor-bridge/bridge-run.py:2161:    return [item for item in checks if isinstance(item, dict) and _watch_suite(item) == suite]
bridge/cursor-bridge/bridge-run.py:2182:def _watch_app(item):
bridge/cursor-bridge/bridge-run.py:2193:def _watch_app_tied(app_id):
bridge/cursor-bridge/bridge-run.py:2204:    if _watch_app_tied(entry.get("app_id")):
bridge/cursor-bridge/bridge-run.py:2205:        return _watch_app(item) == entry.get("app_id")
bridge/cursor-bridge/bridge-run.py:2220:        if not held and isinstance(entry, dict) and not _watch_app_tied(entry.get("app_id")):
bridge/cursor-bridge/bridge_env.py:4210:            for field in ("run_number", "run_attempt", "id", "workflow_id", "check_suite_id"):
bridge/cursor-bridge/bridge_env.py:4260:def _suite_id(item, key):
bridge/cursor-bridge/bridge_env.py:4273:def _app_id_of(item):
bridge/cursor-bridge/bridge_env.py:4296:        sid = _suite_id(run, "check_suite_id")
bridge/cursor-bridge/bridge_env.py:4309:        sid = _suite_id(run, "check_suite_id")
bridge/cursor-bridge/bridge_env.py:4319:        sid = _suite_id(item, "check_suite")
bridge/cursor-bridge/bridge_env.py:4326:            key = (_freeze(item.get("name")), _app_id_of(item))
bridge/cursor-bridge/review-guard.py:1538:def _check_app(item):
bridge/cursor-bridge/review-guard.py:1548:def _named_app(app_id):
bridge/cursor-bridge/review-guard.py:1565:    named = _named_app(app_id)
bridge/cursor-bridge/review-guard.py:1568:        if isinstance(item, dict) and item.get("name") == name and (not named or _check_app(item) == app_id):
bridge/cursor-bridge/review-guard.py:1691:            if app_id is not None and not _named_app(app_id):
tests/fixtures/github/ready-runs-S03-pending.json:20:    "check_suite_id": 118713714642,
tests/fixtures/github/ready-runs-S04-failed.json:20:    "check_suite_id": 118713714642,
tests/fixtures/github/ready-runs-S07-queued.json:20:    "check_suite_id": 118713714642,
tests/fixtures/github/ready-runs-S08-failed.json:20:    "check_suite_id": 118713714642,
tests/fixtures/github/ready-runs-S09-cancelled.json:20:    "check_suite_id": 900001,
tests/fixtures/github/ready-runs-S09-cancelled.json:32:    "check_suite_id": 118713714642,
tests/fixtures/github/ready-runs-S12-page1.json:20:    "check_suite_id": 118713714642,
tests/fixtures/github/ready-runs-S12-page2.json:20:    "check_suite_id": 900005,
tests/fixtures/github/ready-runs-S13-other.json:20:    "check_suite_id": 900002,
tests/fixtures/github/ready-runs-S16-failed.json:20:    "check_suite_id": 118713714642,
tests/fixtures/github/ready-runs-S16-pending.json:20:    "check_suite_id": 118713714642,
tests/fixtures/github/ready-runs-S19-push.json:20:    "check_suite_id": 900003,
tests/fixtures/github/ready-runs-S19-push.json:32:    "check_suite_id": 118713714642,
tests/fixtures/github/ready-runs-S24-startup.json:20:    "check_suite_id": 900006,
tests/fixtures/github/ready-runs-S24-startup.json:32:    "check_suite_id": 118713714642,
tests/fixtures/github/ready-runs-S25-replaced.json:20:    "check_suite_id": 900004,
tests/fixtures/github/ready-runs-S25-replaced.json:32:    "check_suite_id": 118713714642,
tests/fixtures/github/runs.json:20:    "check_suite_id": 118713714642,
tests/fixtures/github/wait-runs-completed.json:20:    "check_suite_id": 118713714642,
tests/fixtures/github/wait-runs-failed-at-start.json:20:    "check_suite_id": 118713714642,
tests/fixtures/github/wait-runs-in-progress.json:20:    "check_suite_id": 118713714642,
tests/fixtures/github/wait-runs-two-done.json:20:    "check_suite_id": 118713714642,
tests/fixtures/github/wait-runs-two-done.json:32:    "check_suite_id": 118713714999,
tests/fixtures/github/wait-runs-two-one-done.json:20:    "check_suite_id": 118713714642,
tests/fixtures/github/wait-runs-two-one-done.json:32:    "check_suite_id": 118713714999,
tests/fixtures/github/wait-runs-two-running.json:20:    "check_suite_id": 118713714642,
tests/fixtures/github/wait-runs-two-running.json:32:    "check_suite_id": 118713714999,
tests/test_loop_guard.py:225:def test_the_run_sheet_check_applies_in_every_phase_and_blocks_the_stop(lg, tmp_path, monkeypatch, capsys):
tests/test_program_branch_rule.py:300:            "status": status, "conclusion": conclusion, "check_suite_id": suite, "head_sha": SHA}
tests/test_program_branch_rule.py:782:    ("runs", "workflow_id"), ("runs", "event"), ("runs", "check_suite_id"),
```

Exit code 0.

```text
git grep -n -w -e app_id_of -e suite_id -e is_int_id
handoff/REFAC-008.md:52:**The proposed shape.** `bridge_env.py` gains three public functions, in place of its two private ones, beside `latest_of_each`: `app_id_of(item)`, `suite_id(item, key)` and `is_int_id(value)`, each giving exactly what the copies give today, with the outer dict guard (a non-dict `item` gives `None`). `suite_id(item, "check_suite")` reads `item["check_suite"]["id"]`; any other key is read flat, as `_suite_id` does today (`suite_id(run, "check_suite_id")`). `is_int_id(value)` is true exactly where `isinstance(value, int) and not isinstance(value, bool)`. bridge_env's private `_suite_id` and `_app_id_of` are removed and `latest_of_each`'s four calls use the public names (no test, tool or other program names the private ones; Requirements 1 checks it). In the two scripts the six copies are deleted and their callers call `bridge_env.app_id_of`, `bridge_env.suite_id` and `bridge_env.is_int_id` at the call site, in the module's existing `bridge_env.<name>(...)` form; bind no module-level alias (no `_watch_app = bridge_env.app_id_of`). Whether `app_id_of` and the `int` test share code inside bridge_env is yours to decide.
handoff/REFAC-008.md:54:**Callers to update**, each in the named line only, every other token of the line and every line around it as it is: bridge-run.py 2158 (`_run_suite(run)` to `bridge_env.suite_id(run, "check_suite_id")`), 2161 (`_watch_suite(item)` to `bridge_env.suite_id(item, "check_suite")`; the `isinstance(item, dict) and` before it stays), 2204 and 2220 (`_watch_app_tied(...)` to `bridge_env.is_int_id(...)`), 2205 (`_watch_app(item)` to `bridge_env.app_id_of(item)`); review-guard.py 1565 and 1691 (`_named_app(...)` to `bridge_env.is_int_id(...)`), 1568 (`_check_app(item)` to `bridge_env.app_id_of(item)`); bridge_env.py 4296, 4309, 4319 and 4326.
handoff/REFAC-008.md:84:**Names.** `git grep -n -e app_id_of -e suite_id -e is_int_id` at `45e4322` finds only bridge_env's private `_suite_id` and `_app_id_of` and the string `check_suite_id` (bridge_env line 4210 and the callers above; fixtures and tests use it only as a JSON key); the three public names are free. No file under `tests/` or `tools/` names any of the eight helpers (`_suite_id`, `_app_id_of`, `_watch_suite`, `_run_suite`, `_watch_app`, `_watch_app_tied`, `_check_app`, `_named_app`).
handoff/REFAC-008.md:107:1. **Checks first, before any edit; paste each command and its output in the report.** From the Workspace root, run `git grep -n -e _suite_id -e _app_id_of -e _watch_suite -e _run_suite -e _watch_app -e _check_app -e _named_app -- bridge tools tests` and confirm that apart from the string `check_suite_id` every line is in one of the three programs, at the definitions and calls listed in the Objective (line numbers may differ by a few). Run `git grep -n -w -e app_id_of -e suite_id -e is_int_id` and confirm it shows nothing. If a check does not hold, stop, change nothing, and report it.
handoff/REFAC-008.md:108:2. bridge_env.py defines `app_id_of(item)`, `suite_id(item, key)` and `is_int_id(value)` once each, public, with the semantics stated in the Objective, and no longer defines `_suite_id` or `_app_id_of`; `latest_of_each` calls the public names and is otherwise unchanged.
handoff/REFAC-008.md:117:- [ ] No public signature outside the listed sites changed; the only new names are `bridge_env.app_id_of`, `bridge_env.suite_id` and `bridge_env.is_int_id`.
```

Exit code 0. No line is under `bridge/`, `tools/`, or `tests/`.

## Pytest (before edit)

Commit: `deed43f65edfc92367e22a0875db2ff98bdd92c7`. Working tree: clean (`git status --short` printed no lines).

```text
python -m pytest -p no:cacheprovider -q -rs tests/test_program_watch_wait.py tests/test_program_ready.py tests/test_program_branch_rule.py tests/test_bridge_run.py tests/test_review_guard.py tests/test_header_currency.py
..............................ss...................sss.................. [ 13%]
........................................................................ [ 26%]
........................................................................ [ 40%]
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
530 passed, 5 skipped in 205.22s (0:03:25)
```

Summary line: `530 passed, 5 skipped in 205.22s (0:03:25)`.

## What changed

`is_int_id(value)` is `isinstance(value, int) and not isinstance(value, bool)`. `app_id_of` and `suite_id` return `None` when `item` is not a dict, then read `item["app"]["id"]` and either `item["check_suite"]["id"]` (key `"check_suite"`) or `item[key]` (any other key), and return the value only when `is_int_id` is true. `latest_of_each` calls `suite_id` and `app_id_of` at its four former private-call sites. `bridge-run.py` no longer defines `_watch_suite`, `_run_suite`, `_watch_app`, or `_watch_app_tied`; `review-guard.py` no longer defines `_check_app` or `_named_app`. Call sites use `bridge_env.suite_id`, `bridge_env.app_id_of`, and `bridge_env.is_int_id`. Neither script gained an import or a module-level alias.

## Post-edit verification

```text
python tools/make-manifest.py
make-manifest: version 2026.11.12a, 147 files hashed, VERSION + MANIFEST.json written
```

Exit code 0.

```text
python tools/dump-cli.py --check
```

Empty output. Exit code 0.

```text
python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet
bridge-check: version 2026.11.12a (2026-11-19 02:12) at <Workspace>\bridge
bridge-check: 147 OK, 0 STALE, 0 MISSING, 0 EXTRA
RESULT: SOURCES MATCH bridge 2026.11.12a
```

Exit code 0.

```text
git diff --numstat -- bridge/cursor-bridge/VERSION
warning: in the working copy of 'bridge/cursor-bridge/VERSION', LF will be replaced by CRLF the next time Git touches it
```

Exit code 0. No numstat line. The file's bytes are `b'2026.11.12a\n'`, so its content reads `2026.11.12a`.

```text
git grep -n -e "def _suite_id" -e "def _app_id_of" -e "def _watch_suite" -e "def _run_suite" -e "def _watch_app" -e "def _check_app" -e "def _named_app" -- bridge
```

Empty output. Exit code 1 (no matches).

## Pytest (after last edit)

Commit: `deed43f65edfc92367e22a0875db2ff98bdd92c7`. Working tree then held uncommitted changes. `git status --short` at that point, before this report file existed:

```text
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/bridge-run.py
 M bridge/cursor-bridge/bridge_env.py
 M bridge/cursor-bridge/review-guard.py
 M docs/BUILDER_NOTES.md
```

```text
python -m pytest -p no:cacheprovider -q -rs tests/test_program_watch_wait.py tests/test_program_ready.py tests/test_program_branch_rule.py tests/test_bridge_run.py tests/test_review_guard.py tests/test_header_currency.py
..............................ss...................sss.................. [ 13%]
........................................................................ [ 26%]
........................................................................ [ 40%]
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
530 passed, 5 skipped in 207.31s (0:03:27)
```

Summary line: `530 passed, 5 skipped in 207.31s (0:03:27)`. Same count passed, none failed, same count skipped, as the before run.

## End state

```text
git status --short
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/bridge-run.py
 M bridge/cursor-bridge/bridge_env.py
 M bridge/cursor-bridge/review-guard.py
 M docs/BUILDER_NOTES.md
?? handoff/REFAC-008-r1-report.md
```

Working tree after the report file was written: uncommitted changes on the five paths above, plus this new report.

```text
git diff --stat
warning: in the working copy of 'bridge/cursor-bridge/MANIFEST.json', LF will be replaced by CRLF the next time Git touches it
 bridge/cursor-bridge/MANIFEST.json   |  8 +++----
 bridge/cursor-bridge/bridge-run.py   | 44 ++++--------------------------------
 bridge/cursor-bridge/bridge_env.py   | 40 +++++++++++++++++++-------------
 bridge/cursor-bridge/review-guard.py | 20 +++-------------
 docs/BUILDER_NOTES.md                |  2 ++
 5 files changed, 38 insertions(+), 76 deletions(-)
```

```text
git rev-parse HEAD
deed43f65edfc92367e22a0875db2ff98bdd92c7
```

`bridge/cursor-bridge/VERSION` is not a diff entry. `docs/CHANGES.md`, `bridge/cursor-bridge/CHANGELOG.md`, and every file under `tests/` are unchanged. No mutation script is in the diff.

## Behaviour unchanged

The shared functions return the value each deleted copy returned: the same nested or flat key, `None` for a non-dict, a missing key, a non-dict inner object, a bool, or any non-int, and the int itself otherwise, so the wait, `ready`, and `latest_of_each` keep the same results, lines, and exit codes.

## Noticed, not changed

`_checks_of_run` still requires `isinstance(item, dict)` before `bridge_env.suite_id(item, "check_suite")`. The new outer guard makes that test redundant for a non-dict item. The brief says to leave that token, so it stays.

## Assumed, not verified

Requirement 1's greps still mean "edit" when they also hit the committed brief and the substring `_check_app` inside `test_the_run_sheet_check_applies_in_every_phase_and_blocks_the_stop` · the stop sentence says to change nothing if a check does not hold, and those two hits are not helper definitions or uses of the new names in code · a supervisor ruling that those hits require a stop, or a grep of definitions and call sites only.
