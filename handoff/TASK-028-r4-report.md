# TASK-028 round 4 report

## Files changed

Checked against `git status` (builder changes only):

- `bridge/cursor-bridge/bridge-run.py`
- `bridge/cursor-bridge/conformance-check.py`
- `bridge/cursor-bridge/MANIFEST.json` (regenerated)
- `handoff/TASK-028-r4-report.md` (this file)

Supervisor's uncommitted changes (not modified by the builder): none listed in `git status` at finish; if present in the tree, they are `docs/HARDENING.md`, `tests/test_bridge_run_driver.py`, and `tests/test_conformance_windowless.py` per the brief.

## Summary

Round 4 restored `uv_run_pytest`'s fall-through to `return False` so `uv run` without `pytest` is refused with exit 125 instead of crashing with `NameError`, and added `_testpath_entry_has_dotdot` so `testpaths` entries containing a `..` path component are dropped before the link walk, closing the POSIX `lnk/../tests` escape without changing any other conformance or launcher behaviour.

## Fixes (review trace)

- **Review A B1 / audit 1:** `bridge/cursor-bridge/bridge-run.py` `uv_run_pytest` line 149 is `return False` again. Pinned by `test_r039_uv_run_without_pytest_still_refused` (six cases).
- **Review A S1 / audit 2:** `bridge/cursor-bridge/conformance-check.py` `_testpath_entry_has_dotdot` and the filter in `_pytest_test_roots`. Pinned by `test_r039_testpaths_dotdot_component_dropped`, `test_r039_testpaths_link_then_dotdot_posix` (where not skipped), and `test_r039_linked_testpaths_entry_falls_back_to_tests`.

## Verification

`python --version`:

```
Python 3.12.10
```

Named tests (`-k "uv_run_without_pytest or healthy_refused_for_driver_exit_3 or limit_auto_driver_empty_log or testpaths_dotdot_component_dropped or testpaths_link_then_dotdot_posix or linked_testpaths_entry_falls_back_to_tests"`):

```
10 passed, 1 skipped, 109 deselected in 1.17s
```

Skipped (named run, `-rs`):

- `tests\test_conformance_windowless.py:517`: Windows collapses `..` before it follows a link

Increment test set (`-rs` skips):

- `tests\test_conformance_windowless.py:492`: creating a file symbolic link needs a privilege here
- `tests\test_conformance_windowless.py:517`: Windows collapses `..` before it follows a link
- `tests\test_allowlist.py:65`: prose, not a runnable command (10 items)
- `tests\test_allowlist.py:103`: prose, not a runnable command (10 items)
- `tests\test_workflows_line_check.py:495`: cannot create a symbolic link here (2 items)

Windowless check last line:

```
windowless-check: 2 file(s) scanned, 0 FAIL, 0 NOTE
```

`python tools/dump-cli.py --check`: exit 0 (no output).

Manifest command last line:

```
make-manifest: version 2026.10.25a, 141 files hashed, VERSION + MANIFEST.json written
```

Full suite via `bridge-run.py`:

```
2363 passed, 35 skipped in 503.41s (0:08:23)
bridge-run: exit 0
```

## Mutation table

| Mutant | Killing test | Last failing assertion line |
|--------|--------------|---------------------------|
| `uv_run_pytest` last line `return any(":" in p for p in parts)` | `test_r039_uv_run_without_pytest_still_refused` | `assert 1 == 125` (NameError traceback, exit 1) |
| Removed `not _testpath_entry_has_dotdot(p)` from `_pytest_test_roots` kept filter | `test_r039_testpaths_dotdot_component_dropped` | `assert row_for(out + err) == [MISSING_ROW]` (got OK for `b/conftest.py`) |

**Survived:** none.

Both mutants were restored before this report; `git diff` matches the intended fix only.

## Full-suite environment observations

None. The full suite completed with `bridge-run: exit 0`.

## Assumed, not verified

Assumed, not verified: none.
