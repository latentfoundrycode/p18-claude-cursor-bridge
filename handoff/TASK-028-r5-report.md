# TASK-028 round 5 report

## Files changed

- `bridge/cursor-bridge/conformance-check.py` (builder)
- `bridge/cursor-bridge/MANIFEST.json` (regenerated via `make-manifest`)
- `handoff/TASK-028-r5-report.md` (this report)

Supervisor-owned uncommitted changes (not edited by builder): none visible in `git status` for this run; round-5 tests in `tests/test_conformance_windowless.py` and `tests/test_bridge_run_driver.py` were already present in the tree.

`bridge/cursor-bridge/VERSION` was rewritten by the manifest command but shows no content diff in `git diff`.

## Summary

Round 5 hardens the Windowless test suite floor in `conformance-check.py` against unusual input: NUL and similar path errors count as links during the testpaths walk, an unlistable `tests/` directory yields no discovered `test_*.py`, the OK row’s relative path is rendered through `workflow-check.py`’s `escape_field`, and the whole floor judgement is wrapped in a backstop that emits a single NOTE naming only the exception class if anything else escapes. `MANIFEST.json` was regenerated; all named tests, the increment test set, windowless-check, dump-cli, and the full suite via `bridge-run.py` completed successfully.

## Findings addressed

- **Review A 1 / audit HARDENING (NUL in testpaths):** `_ws_walk_component_ok` treats `ValueError` like non-`FileNotFoundError` `OSError`, including around `bridge_env.is_link`. Pinned by `test_r039_nul_in_testpaths_dropped`.
- **Review A 2 (unlistable tests/):** `_pytest_suite_seen` catches `OSError` from `os.listdir` on `tests/` and treats the directory as having no `test_*.py`. Pinned by `test_r039_unlistable_tests_folder_is_no_suite`.
- **Review A 3 (control character in OK path):** OK row path uses `_load_escape_field()` / `escape_field`, with printable-ASCII-only fallback when load fails. Pinned by `test_r039_ok_row_path_is_escaped`.
- **Backstop (9(c) tail):** Floor rows are collected in `floor_rows` inside `try`/`except Exception`; any failure yields exactly one NOTE with `type(e).__name__` only. Pinned by `test_r039_floor_backstop_turns_an_error_into_one_note`.

## Verification output

`python --version`:

```
Python 3.12.10
```

Named tests (`-k` filter from brief): last line:

```
16 passed, 114 deselected in 1.52s
```

Skipped tests from increment run (`-rs`); reasons with temp paths abbreviated:

- `tests/test_conformance_windowless.py:492` — creating a file symbolic link needs a privilege here
- `tests/test_conformance_windowless.py:517` — Windows collapses `..` before it follows a link
- `tests/test_allowlist.py:65` (×10) — prose, not a runnable command
- `tests/test_allowlist.py:103` (×10) — prose, not a runnable command
- `tests/test_workflows_line_check.py:495` (×2) — cannot create a symbolic link here (privilege not held)

Windowless check last line:

```
windowless-check: 2 file(s) scanned, 0 FAIL, 0 NOTE
```

`python tools/dump-cli.py --check`: exit 0 (no output).

Manifest command last line:

```
make-manifest: version 2026.10.25a, 141 files hashed, VERSION + MANIFEST.json written
```

Full suite (`run/agent/TASK-028-r5-suite.out`):

```
2373 passed, 35 skipped in 501.03s (0:08:21)
bridge-run: exit 0
```

## Mutation table

| Req | Reverted change | Test | Last failing assertion (mutant run) |
|-----|-----------------|------|-------------------------------------|
| 1 | `_ws_walk_component_ok` again catches only `OSError`; no `ValueError` / `is_link` guard | `test_r039_nul_in_testpaths_dropped` | `assert row_for(out + err) == [MISSING_ROW]` — got backstop NOTE `(ValueError)` |
| 2 | `os.listdir(tests)` no longer wrapped in `except OSError` | `test_r039_unlistable_tests_folder_is_no_suite` | `assert rows == [NEITHER_NOTE]` — got backstop NOTE `(PermissionError)` |
| 3 | OK row uses raw `rel_ok` without `escape_field` | `test_r039_ok_row_path_is_escaped` | `assert '\u202e' not in out` |
| 4 | Removed `try`/`except Exception` backstop around floor | `test_r039_floor_backstop_turns_an_error_into_one_note` | `RuntimeError: secret_zz91 ...` propagated from patched `_pytest_test_roots` |

All four mutants were restored before this report was finalized (`git diff` shows only the intended floor changes).

## Full-suite environment observations

None beyond the skipped tests listed above; no failures outside the increment test file list.

## Assumed, not verified

- Embedded NUL in a joined path makes `os.lstat` raise `ValueError` on this platform before the walk completes, and no earlier `os.path` call on that entry raises first · brief cites this as the failure mode · observed indirectly because `test_r039_nul_in_testpaths_dropped` passes with requirement 1 in place.
- `escape_field` renders U+202E as `\u202e` and leaves `/` unchanged · matches `workflow-check.py` description in brief · confirmed by passing `test_r039_ok_row_path_is_escaped`.
- `SystemExit` and `KeyboardInterrupt` cannot arise inside the floor block · not exercised · backstop intentionally catches only `Exception`.
- When requirement 1 is removed, the NUL case is caught by the backstop rather than reaching the MISSING row via dropped entry + default `tests/` · mutant run only · a stricter test would distinguish backstop from requirement 1 alone.
