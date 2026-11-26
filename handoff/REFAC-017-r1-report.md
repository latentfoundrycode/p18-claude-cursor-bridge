# REFAC-017 round 1 report

## Files changed

- `bridge/cursor-bridge/bridge-run.py`
- `bridge/cursor-bridge/MANIFEST.json`
- `handoff/REFAC-017-r1-report.md` (this file)

## Summary

Refactored `bridge/cursor-bridge/bridge-run.py` so `_git_launch_state` obtains HEAD via `_git_rev_parse(ws, "HEAD")` with the same 40/64-hex validation and unchanged status block, and so `roster_builder_model`, `_read_roster_json`, and `_load_deviation` each read `docs/*.json` through new private `_read_docs_json(folder, name)`; regenerated `bridge/cursor-bridge/MANIFEST.json` with `python tools/make-manifest.py`. Requirement 1 held for `bridge-run.py`; three test files already differed from `8b03c32` before this run (left untouched per Out of scope). Pytest before and after: 622 passed, 4 skipped.

## Start state

```
git status --short
```

(empty)

```
git rev-parse HEAD
```

```
25cba54f060b6217f4100d04ddb3f6fe659f22d8
```

```
git log --oneline -3
```

```
25cba54 REFAC-017: the header's satisfies list in the prose line's order
ae0e3ac REFAC-016: mutation-run.py - run paths, the checkpoint run, pytest_env's loop and the plugin's path test, each once
bc3bcd7 REFAC-015: roster-check.py - the rebuild entry, the unreadable exit and built_by's line parse, each once
```

Working tree at start: no uncommitted changes shown by `git status --short`.

## Requirement 1 (before edit)

```
git diff --stat 8b03c32 -- bridge/cursor-bridge/bridge-run.py tests
```

```
 tests/roster_rows.py                | 56 +++++++++++++++++++++++++++++++++++++
 tests/test_improve_roster_alt.py    | 51 ++-------------------------------
 tests/test_improve_roster_launch.py | 52 ++--------------------------------
 3 files changed, 61 insertions(+), 98 deletions(-)
```

`bridge/cursor-bridge/bridge-run.py` is unchanged from `8b03c32`; three test files differ (pre-existing on this branch). No edit was made to those files.

```
git grep -n -w -e _git_rev_parse -e _git_launch_state -e roster_builder_model -e _read_roster_json -e _load_deviation -e _read_docs_json -- bridge tests
```

```
bridge/cursor-bridge/bridge-run.py:1201:def roster_builder_model(folder):
bridge/cursor-bridge/bridge-run.py:1212:def _read_roster_json(ws):
bridge/cursor-bridge/bridge-run.py:1241:def _git_launch_state(ws):
bridge/cursor-bridge/bridge-run.py:1304:def _load_deviation(folder):
bridge/cursor-bridge/bridge-run.py:1329:    roster_data, profiles = _read_roster_json(ws)
bridge/cursor-bridge/bridge-run.py:1353:    deviation = _load_deviation(folder)
bridge/cursor-bridge/bridge-run.py:1432:    builder = roster_builder_model(folder)
bridge/cursor-bridge/bridge-run.py:1439:            if _load_deviation(folder) is None:
bridge/cursor-bridge/bridge-run.py:2678:        resolved_builder = roster_builder_model(ws)
bridge/cursor-bridge/bridge-run.py:3135:def _git_rev_parse(folder, *args):
bridge/cursor-bridge/bridge-run.py:3156:    raw = _git_rev_parse(folder, *args)
bridge/cursor-bridge/bridge-run.py:3609:        start_commit, clean = _git_launch_state(ws_build)
```

(Twelve lines; no `_read_docs_json`; none in `tests/`.)

```
git grep -n -F -e "json.load(" -- bridge/cursor-bridge/bridge-run.py
```

```
bridge/cursor-bridge/bridge-run.py:1204:            data = json.load(f)
bridge/cursor-bridge/bridge-run.py:1215:            data = json.load(f)
bridge/cursor-bridge/bridge-run.py:1307:            data = json.load(f)
```

```
git grep -n -F -e "except (OSError, ValueError, RecursionError):" -- bridge/cursor-bridge/bridge-run.py
```

```
bridge/cursor-bridge/bridge-run.py:1207:    except (OSError, ValueError, RecursionError):
bridge/cursor-bridge/bridge-run.py:1216:    except (OSError, ValueError, RecursionError):
bridge/cursor-bridge/bridge-run.py:1308:    except (OSError, ValueError, RecursionError):
```

```
git grep -n -F -e rev-parse -- bridge/cursor-bridge/bridge-run.py
```

```
bridge/cursor-bridge/bridge-run.py:1183:            ["git", "-C", folder or ".", "rev-parse", "--git-common-dir"],
bridge/cursor-bridge/bridge-run.py:1247:            ["git", "-C", base, "rev-parse", "HEAD"],
bridge/cursor-bridge/bridge-run.py:2584:            ["git", "-C", folder or ".", "rev-parse", "--abbrev-ref", "HEAD"],
bridge/cursor-bridge/bridge-run.py:2700:        p = subprocess.run(["git", "-C", folder, "rev-parse", "HEAD"], capture_output=True, text=True, timeout=30, creationflags=NO_WINDOW)
bridge/cursor-bridge/bridge-run.py:3138:            ["git", "-C", folder or ".", "rev-parse"] + list(args),
bridge/cursor-bridge/bridge-run.py:3155:    """Absolute path of a git rev-parse answer...
```

```
git grep -n -e "^GIT_TIMEOUT" -- bridge/cursor-bridge/bridge_env.py
```

```
bridge/cursor-bridge/bridge_env.py:416:GIT_TIMEOUT = 30
```

### Git call comparison (`_git_launch_state` rev-parse block vs `_git_rev_parse`)

For `_git_launch_state` at `8b03c32`, `base = ws or "."` and the subprocess used `["git", "-C", base, "rev-parse", "HEAD"]`. For `_git_rev_parse(ws, "HEAD")`, the command is `["git", "-C", folder or ".", "rev-parse"] + list(args)` → `["git", "-C", ws or ".", "rev-parse", "HEAD"]`. Same `-C` folder rule, same subcommand and `HEAD`, same `capture_output=True`, `text=True`, `encoding="utf-8"`, `errors="replace"`, `creationflags=NO_WINDOW`, `timeout=bridge_env.GIT_TIMEOUT` (30), neither passes `env=` or `cwd=`. Non-zero exit, empty stripped stdout, `OSError`, and `TimeoutExpired` in `_git_rev_parse` yield `None`, which maps to the same `(None, False)` paths as before; non-empty stdout is the same stripped string, then the same 40/64-hex test applies.

### JSON reader comparison

All three copies used `open(os.path.join(<folder>, "docs", <name>), encoding="utf-8", errors="replace")`, `json.load(f)`, and `except (OSError, ValueError, RecursionError):` with the same handling semantics described in the Objective. `_read_docs_json` preserves that path join (folder unchanged), encoding, `errors`, and except tuple, and returns the object only when it is a `dict`, else `None`.

## Pytest (before edit, at HEAD `25cba54`)

```
python -m pytest -p no:cacheprovider -q -rs tests/test_improve_roster_launch.py tests/test_hotfix25a_roster_launcher.py tests/test_task032_supervisor_launcher.py tests/test_bridge_run.py tests/test_bridge_run_design_ceiling.py tests/test_bridge_run_review_ceiling.py tests/test_bridge_run_driver.py tests/test_bridge_run_slot.py tests/test_hotfix24a_heavy_slots.py tests/test_header_currency.py
```

```
........................... (dots omitted) ...
=========================== short test summary info ===========================
SKIPPED [1] tests\test_bridge_run_slot.py:411: POSIX special files
SKIPPED [1] tests\test_bridge_run_slot.py:930: POSIX links and permission bits
SKIPPED [1] tests\test_bridge_run_slot.py:1125: POSIX permission bits
SKIPPED [1] tests\test_hotfix24a_heavy_slots.py:1102: POSIX file modes
622 passed, 4 skipped in 413.73s (0:06:53)
```

Working tree before this pytest: no uncommitted changes (`git status --short` empty at start).

## Post-edit verification

```
python tools/make-manifest.py
```

```
make-manifest: version 2026.11.24a, 148 files hashed, VERSION + MANIFEST.json written
```

```
python tools/dump-cli.py --check
```

(empty output, exit 0)

```
python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet
```

```
bridge-check: version 2026.11.24a (2026-11-26 04:42) at <Workspace>\bridge
bridge-check: 148 OK, 0 STALE, 0 MISSING, 0 EXTRA
RESULT: SOURCES MATCH bridge 2026.11.24a <Workspace>\bridge\cursor-bridge
```

```
git diff --numstat -- bridge/cursor-bridge/VERSION
```

(empty)

```
git diff --numstat -- bridge/cursor-bridge/bridge-run.py
```

```
18	33	bridge/cursor-bridge/bridge-run.py
```

### Acceptance `git grep` (after edit)

```
git grep -n -F -e "json.load(" -- bridge/cursor-bridge/bridge-run.py
```

```
bridge/cursor-bridge/bridge-run.py:1204:            data = json.load(f)
```

```
git grep -n -F -e "except (OSError, ValueError, RecursionError):" -- bridge/cursor-bridge/bridge-run.py
```

```
bridge/cursor-bridge/bridge-run.py:1205:    except (OSError, ValueError, RecursionError):
```

```
git grep -n -w -e _read_docs_json -- bridge
```

```
bridge/cursor-bridge/bridge-run.py:1201:def _read_docs_json(folder, name):
bridge/cursor-bridge/bridge-run.py:1211:    data = _read_docs_json(folder, "ROSTER.resolved.json")
bridge/cursor-bridge/bridge-run.py:1218:    data = _read_docs_json(ws, "ROSTER.json")
bridge/cursor-bridge/bridge-run.py:1294:    data = _read_docs_json(folder, "ROSTER.resolved.json")
```

```
git grep -n -w -e _git_rev_parse -- bridge
```

```
bridge/cursor-bridge/bridge-run.py:1246:    cand = _git_rev_parse(ws, "HEAD")
bridge/cursor-bridge/bridge-run.py:3120:def _git_rev_parse(folder, *args):
bridge/cursor-bridge/bridge-run.py:3141:    raw = _git_rev_parse(folder, *args)
```

```
git grep -n -F -e rev-parse -- bridge/cursor-bridge/bridge-run.py
```

```
bridge/cursor-bridge/bridge-run.py:1183:            ["git", "-C", folder or ".", "rev-parse", "--git-common-dir"],
bridge/cursor-bridge/bridge-run.py:2569:            ["git", "-C", folder or ".", "rev-parse", "--abbrev-ref", "HEAD"],
bridge/cursor-bridge/bridge-run.py:2685:        p = subprocess.run(["git", "-C", folder, "rev-parse", "HEAD"], ...
bridge/cursor-bridge/bridge-run.py:3123:            ["git", "-C", folder or ".", "rev-parse"] + list(args),
bridge/cursor-bridge/bridge-run.py:3140:    """Absolute path of a git rev-parse answer...
```

Five lines; none inside `_git_launch_state`.

## Pytest (after edit, at HEAD `25cba54`, uncommitted changes present)

```
python -m pytest -p no:cacheprovider -q -rs tests/test_improve_roster_launch.py tests/test_hotfix25a_roster_launcher.py tests/test_task032_supervisor_launcher.py tests/test_bridge_run.py tests/test_bridge_run_design_ceiling.py tests/test_bridge_run_review_ceiling.py tests/test_bridge_run_driver.py tests/test_bridge_run_slot.py tests/test_hotfix24a_heavy_slots.py tests/test_header_currency.py
```

```
=========================== short test summary info ===========================
SKIPPED [1] tests\test_bridge_run_slot.py:411: POSIX special files
SKIPPED [1] tests\test_bridge_run_slot.py:930: POSIX links and permission bits
SKIPPED [1] tests\test_bridge_run_slot.py:1125: POSIX permission bits
SKIPPED [1] tests\test_hotfix24a_heavy_slots.py:1102: POSIX file modes
622 passed, 4 skipped in 413.54s (0:06:53)
```

Same passed and skipped counts as before edit.

## End state

```
git status --short
```

```
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/bridge-run.py
?? handoff/REFAC-017-r1-report.md
```

```
git diff --stat
```

```
 bridge/cursor-bridge/MANIFEST.json |  4 +--
 bridge/cursor-bridge/bridge-run.py | 51 ++++++++++++++------------------------
 2 files changed, 20 insertions(+), 35 deletions(-)
```

```
git rev-parse HEAD
```

```
25cba54f060b6217f4100d04ddb3f6fe659f22d8
```

Working tree at end: uncommitted modifications to `bridge-run.py` and `MANIFEST.json`, untracked report.

## Behaviour

The launcher still runs the same git invocation for HEAD (via `_git_rev_parse`), applies the same hex gate and status porcelain logic, and still reads the same roster JSON paths with the same encoding, exception set, and per-caller field checks, so every exit, refusal, printed line, and run-record field on the exercised paths stays the same.

## Noticed, not changed

`local_head`, `branch_of`, and `git_common_dir` still carry their own git subprocess patterns; `git diff --stat 8b03c32 -- tests` shows pre-existing test extractions to `tests/roster_rows.py` on this branch.

## Assumed, not verified

Assumed, not verified: none.