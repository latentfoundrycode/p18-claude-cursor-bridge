# TASK-028 round 2 report

## Files changed

- `bridge/cursor-bridge/bridge-run.py`
- `bridge/cursor-bridge/conformance-check.py`
- `tests/test_bridge_run_driver.py`
- `tests/test_conformance_windowless.py`
- `docs/cli-reference.json`
- `docs/CLI_REFERENCE.md`
- `bridge/cursor-bridge/MANIFEST.json` (regenerated)
- `bridge/cursor-bridge/VERSION` (regenerated with manifest)

## Summary

Round 2 hardened `bridge-run.py` driver acceptance: refuse `..` and post-drive `:` in program tokens, require a regular file under `run/supervisor/`, start the absolute normalised program path, re-check with `verify_driver_program_abs` immediately before `subprocess.Popen`, refuse `--key-file` for driver runs, log `head_of(cmd)` for driver, and parse `--kind` once. The conformance `Windowless test suite` floor now follows pytest config precedence, safe parsing with NOTE rows, in-workspace `testpaths`, echo and `NAME=VALUE` handling, and its own docstring bullet. Tests were expanded in `tests/test_bridge_run_driver.py` and `tests/test_conformance_windowless.py`; CLI reference and manifest were regenerated.

## Round-1 findings addressed

- Security Blocking: `..` before link collapse — `resolve_driver_program` / `_token_has_dotdot`; pinned by `test_r039_refuse_dotdot_inside_supervisor`, `test_r039_refuse_dotdot_through_supervisor_link`, `test_r039_refuse_mutation_path_dotdot`.
- Security Blocking: directory `*.py` — `os.path.isfile` in `_supervisor_file_ok`; pinned by `test_r039_refuse_directory_named_py`.
- Review A Blocking: token removal not caught — parametrized `test_r039_missing_one_token_removed`; full-row asserts throughout `test_conformance_windowless.py`.
- Review A Blocking: rows not compared whole — exact `row_for(...) == [...]` in conformance tests.
- Review A Blocking: driver log `head` carried arguments — `head_of(cmd)` for driver in `main()`; pinned by `test_r039_log_head_interpreter_only_with_args`.
- Review A Should-fix / floor crash / testpaths / precedence / echo / key-file / re-check / argv absolute — conformance helpers and driver `main()`; pinned by no-crash, precedence, outside-root, echo, and driver tests named above plus `test_r039_refuse_key_file_with_driver`, `test_r039_started_argv_absolute_*`, `test_r039_recheck_refuses_tampered_program`.
- Security advisories: ADS `:` — `_colon_in_path_after_drive`; `test_r039_refuse_alternate_data_stream`. TOCTOU re-check — `verify_driver_program_abs` before Popen; recheck test. `--key-file` env — `DRIVER_KEYFILE_REFUSE`; key-file test.
- Consider items taken in brief: `BRIDGE_RUN_ALLOW_ANY` still refused for driver violations (parametrized refusal tests); `kind_in_flags` removed; RawConfigParser/tomllib via `read()`.

## Window-handle probe (a hint, KP-010)

`0 29404 29404 28456 12656`

The console window handle is 0 (no console attached to this process). Four process ids were listed after the pid.

## Verification

- Increment pytest set (brief list): 645 passed, 22 skipped.
- `windowless-check`: `0 FAIL`.
- `dump-cli.py` / `--check`: pass after regeneration.
- `make-manifest.py --version 2026.10.25a`: pass.
- Full `pytest tests`: 2339 passed, 33 skipped.

## Mutation list (hand-checked, code restored after each)

| Mutation | Test that failed |
| --- | --- |
| Remove `_token_has_dotdot` refusal | `test_r039_refuse_dotdot_inside_supervisor` |
| Remove `_colon_in_path_after_drive` | `test_r039_refuse_alternate_data_stream` |
| Remove `os.path.isfile` in `_supervisor_file_ok` | `test_r039_refuse_directory_named_py` |
| Skip replacing `cmd[1]` with `driver_prog` | `test_r039_started_argv_absolute_supervisor` |
| Remove re-check before Popen | `test_r039_recheck_refuses_tampered_program` (stderr / log behaviour) |
| Remove `--key-file` driver refusal | `test_r039_refuse_key_file_with_driver` |
| Driver `head` uses `head_text` again | `test_r039_log_head_interpreter_only_with_args` |
| Remove supervisor containment | `test_r039_refuse_program_outside_supervisor` |
| Remove link walk | `test_r039_refuse_link_at_supervisor` |
| Remove leading-option refusal | `test_r039_refuse_interpreter_options` |
| Driver healthy exits only `(0,)` | `test_r039_healthy_accepts_driver_exit_0_and_1` |
| `BRIDGE_RUN_ALLOW_ANY` exempts driver | `test_r039_refuse_program_outside_supervisor` with `allow_any=True` |
| Remove one `WINDOWLESS_TOKENS` / `all`→`any` | `test_r039_missing_one_token_removed` |
| `setup.cfg` before `pyproject.toml` precedence | `test_r039_precedence_pyproject_over_setup` |
| Drop `testpaths` containment | `test_r039_outside_root_relative_testpaths` |
| Skip `NAME=VALUE` words | `test_r039_other_runner_skips_env_assignments` |
| Remove echo NOTE branch | `test_r039_echo_default_script_note` |
| Snapshot verbatim | `test_r039_snapshot_matches_conftest` |
| Remove `CREATE_NO_WINDOW` on Windows Popen | `test_r039_driver_grandchild_windowless` |

## Full-suite environment observations

None beyond the brief list: full suite passed in this run with no extra failures.

## Assumed, not verified

- `os.path.isfile` on Windows returns false for a directory whose name ends in `.py` and for typical alternate data stream paths passed as a single token — relied on CPython and OS behaviour; a live ADS path on NTFS would confirm the colon rule end-to-end.
- Pytest itself would treat the brief’s `testpaths` filtering the same way users expect when every entry is outside the workspace — the floor mirrors the brief’s containment rule, not a live pytest run.
- In-process `test_r039_recheck_refuses_tampered_program` relies on monkeypatched `verify_driver_program_abs` matching the production re-check call path — subprocess driver tests cover the happy path; the tamper test asserts refusal without a successful child start via stderr and an empty `runs.jsonl`.
