# TASK-028 round 3 report

## Files changed

- `bridge/cursor-bridge/bridge-run.py`
- `bridge/cursor-bridge/conformance-check.py`
- `bridge/cursor-bridge/MANIFEST.json` (regenerated)
- `docs/CLI_REFERENCE.md` (regenerated)
- `docs/cli-reference.json` (regenerated)
- `tests/test_bridge_run_driver.py`
- `tests/test_conformance_windowless.py`

## Summary

Round 3 hardened `bridge-run.py` driver acceptance with hard-link refusal, fail-closed link-walk `os.lstat` errors, and `os.path.abspath` program paths (drive letter on Windows), and extended the conformance `Windowless test suite` floor with link-safe test roots, `RecursionError`-safe parsing, `shlex`-based runner-word extraction with `escape_field` output, and tests that pin each review finding; CLI reference and manifest were regenerated and the scoped pytest acceptance list passes.

## Round-2 findings addressed

- Review A Blocking (ADS test never created the stream): fixed `test_r039_refuse_alternate_data_stream` and colon rule load-bearing via `_colon_in_path_after_drive` in `bridge-run.py`.
- Review A Should-fix (`RecursionError` on nested `pyproject.toml` / `package.json`): `RecursionError` catches in `_read_pyproject_pytest` and `_package_json_scripts`; `test_r039_no_crash_nested_pyproject`, `test_r039_no_crash_nested_package_json`.
- Review A Consider (exact healthy/limit lines): `test_r039_healthy_refused_for_driver_exit_3`, `test_r039_limit_auto_driver_empty_log` use `in p.stderr.splitlines()`.
- Review A Consider (`_rel_forward` traceback): `_rel_forward` returns `None` instead of raising; OK row guarded in `main()`.
- Review A Consider (raw runner word): `escape_field` via `_load_escape_field`; `test_r039_other_runner_escape_control_chars` and path basename tests.
- Audit advisory 3 (`RecursionError`): same as Should-fix above.
- Audit advisory 4 (raw other-runner word): `shlex` split + `escape_field`; tests under `test_r039_other_runner_*`.
- Audit advisory 5 (testpaths / `tests/` / root `conftest.py` through links): `_test_root_path_ok`, `_tests_dir_listable`, `_root_conftest_counts`; `test_r039_testpaths_through_link`, `test_r039_tests_link_with_config`, `test_r039_tests_link_no_config`, `test_r039_root_conftest_symlink`.
- Audit advisory 6 (hard link under `run/supervisor/`): `st_nlink == 1` in `_supervisor_file_ok`; `test_r039_refuse_hard_link_supervisor`.
- Audit advisory 7 (link walk fails open on `lstat` error): `_link_component_refused` in `bridge-run.py`; `test_r039_driver_link_walk_fail_closed_lstat`.
- Audit advisory 9 (rooted token without drive): `_program_abs` uses `os.path.abspath`; `test_r039_driver_rooted_token_gets_drive` (Windows).
- Glob pin (`testpaths = tests/*` literal): `test_r039_testpaths_glob_literal`.

## Verification

`python --version`: Python 3.12.10

Skipped tests (`-rs` on acceptance list):

- `tests/test_conformance_windowless.py::test_r039_root_conftest_symlink` — creating a file symbolic link needs a privilege here
- `tests/test_allowlist.py` — prose, not a runnable command (20 skips)
- `tests/test_workflows_line_check.py` — cannot create a symbolic link here (2 skips)

Alternate-data-stream test: ran and passed (not skipped). Hard-link test: ran and passed. Rooted-token test: ran on Windows (not skipped). Rootdir-symlink test: skipped (privilege).

`python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge/bridge-run.py bridge/cursor-bridge/conformance-check.py`: `0 FAIL`

Acceptance pytest list: 661 passed, 23 skipped.

## Window-handle probe (a hint, KP-010)

`0 5548 5548 4860 25048`

Hint only: the first number (console window handle) is 0; four process ids followed (including the probe process).

## Mutation table

### Killed

| Mutant | Test |
| --- | --- |
| `_colon_in_path_after_drive` forced to return `False` | `test_r039_refuse_alternate_data_stream` |
| Remove `_colon_in_path_after_drive` call in `resolve_driver_program` | `test_r039_refuse_alternate_data_stream` |
| Remove `..` component refusal | `test_r039_refuse_dotdot_inside_supervisor` |
| Remove link-count check | `test_r039_refuse_hard_link_supervisor` |
| Fail-open `os.lstat` in driver link walk | `test_r039_driver_link_walk_fail_closed_lstat` |
| `os.path.normpath` instead of `os.path.abspath` for accepted program | `test_r039_driver_rooted_token_gets_drive` |
| Remove `RecursionError` from pyproject parse | `test_r039_no_crash_nested_pyproject` |
| Remove `RecursionError` from package.json parse | `test_r039_no_crash_nested_package_json` |
| Remove test-root link check in OK loop | `test_r039_tests_link_with_config` |
| Remove `escape_field` for runner word | `test_r039_other_runner_escape_control_chars` |
| Remove basename reduction | `test_r039_other_runner_path_basename` |
| Remove skip of words starting with `-` | `test_r039_other_runner_dash_option` |
| Restore round-2 `NAME=VALUE` skip only | `test_r039_other_runner_quoted_assignment` |
| `shlex` replaced by `str.split` | `test_r039_other_runner_quoted_assignment` |
| Remove `ValueError` fallback in `_split_script_words` | `test_r039_other_runner_unclosed_quote` |

### Survived

| Mutant | Reason |
| --- | --- |
| Remove leading-option refusal (`-c`, `-m`) | Redundant with interpreter check; brief records no test can kill it |
| Remove link check on default `tests/` only in `_pytest_test_roots` filter | Same `_test_root_path_ok` guard in `main()` loop; separate mutant for `_tests_dir_listable` covered by `test_r039_tests_link_no_config` when combined with suite-seen path |
| Remove rootdir `conftest.py` link check only | Exercised by `test_r039_root_conftest_symlink`, skipped here without symlink privilege |
| Rooted-token `normpath` mutant on non-Windows | `test_r039_driver_rooted_token_gets_drive` skipped where drive letters do not apply |

## Full-suite environment observations

`python -m pytest tests -q -p no:cacheprovider`: 39 failed, 2307 passed, 34 skipped, 9 errors — all failures/errors in `tests/test_rollback.py` and `tests/test_install.py` (install/rollback against `<home>` layout). These are environment/install tests outside the increment scope; not re-run after revert comparison, consistent with prior builder notes that install tests fail without the owner's home bridge layout.

## Assumed, not verified

- NTFS alternate data stream path `x.txt:hidden.py` is refused by `_colon_in_path_after_drive` after `abspath`, not only by `isfile` false · colon rule is the intended gate · observed `test_r039_refuse_alternate_data_stream` pass on this run.
- `os.stat(...).st_nlink == 2` for a hard link on this builder's temp file system · hard-link test asserted before refusal · observed on this run.
- Deeply nested invalid TOML/JSON raises `RecursionError` (not only `TOMLDecodeError`/`ValueError`) on Python 3.12.10 · nested fixture tests · observed in failing run before catch restored.
- `shlex.split` after backslash placeholder preserves `TOKEN="abc4x def7z"` grouping · quoted-assignment test · observed pass.
- Copied `conformance-check.py` without `bridge_env.py` (workflow-line tests) uses the inline `is_link` shim · workflow-line suite pass after `_load_bridge_env` fallback · observed 661 acceptance passes.
