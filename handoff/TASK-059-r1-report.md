# TASK-059 round 1 report

## Files changed

- `bridge/cursor-bridge/bridge-run.py`
- `bridge/cursor-bridge/bridge_env.py`
- `bridge/cursor-bridge/MANIFEST.json` (regenerated)
- `tests/test_bridge_run.py`
- `tests/test_bridge_run_driver.py`
- `tests/test_release_s_launcher.py`
- `handoff/TASK-059-r1-report.md`

## Summary

The launcher now accepts exactly the interpreter leading flags `-B` and `-X utf8`, reads npm, pnpm and yarn folder options before a bare `--` with link-safe folder and environment rules, distinguishes known-runner defect refusals from unknown-runner `# wake` advice, writes sorted `merge_ids`, and escapes both plan globs; supervisor acceptance tests and added R-078 builder tests pass with manifest sources matching.

## Requirements

1. Requirement 1: `python_interpreter_lead` in `bridge-run.py` accepts only `-B` and `-X utf8` once each in either order and returns the command start or a refused word.
2. Requirement 2: `named_suite`, `test_suite`, `runner_word`, `outside_target`, `outside_by_environment`, `head_text`, `resolve_driver_program`, and driver substitution in `main` all read from `python_interpreter_lead` or package folder skips so logs show heads without leading flags.
3. Requirement 3: Any other interpreter flag before `-m` or the driver program is refused via `python_interpreter_lead` and `known_runner_refusal` without setting `PYTHONUTF8`.
4. Requirement 4: `_package_folder_token`, `_package_scan_folder_options`, and `_package_body_index` read npm `--prefix`/`-C`, pnpm `--dir`/`-C`, yarn `--cwd`, abbreviations, `=` forms, and refuse attached `-C<folder>`.
5. Requirement 5: `named_suite` skips folder options before the `test` or `run test*` subcommand so leading folder forms are named suites.
6. Requirement 6: `_package_folder_ok` and `_package_scan_folder_options` enforce launch roots, existence, no links on the path, no duplicate canonical folder options, and missing values with known-runner refusal words.
7. Requirement 7: Accepted package suites run through existing strip, limit and `head_text` paths so logged heads omit folder options.
8. Requirement 8: `outside_by_environment` applies `NPM_PACKAGE_ENV` and `PNPM_PACKAGE_ENV` against `package_runner_cwd` with the same folder rule as `_package_folder_ok`.
9. Requirement 9: `KNOWN_RUNNER_REFUSE` and `known_runner_refusal` in `main` precede the generic refusal for known escape, interpreter and folder cases; unknown runners keep the `# wake` message.
10. Requirement 10: Environment refusals continue to name only the variable; no value is printed on stderr or stdout.
11. Requirement 11: `builder_review_refusal` stores `merge_ids` as `tuple(sorted(declared))` and the run log writes that sorted list.
12. Requirement 12: `builder_review_refusal` escapes the workspace path with `glob.escape` before the `BUILD_PLAN*.md` glob.
13. Requirement 13: `bridge_env.plan_increment_ids` escapes the `docs` folder with `glob.escape` before its glob (only change in that file).
14. Requirement 14: `python tools/make-manifest.py` regenerated `MANIFEST.json`; `bridge/cursor-bridge/VERSION` remained `2026.11.12a`.

## Verification commands

### 1. `python tools/make-manifest.py`

```
make-manifest: version 2026.11.12a, 146 files hashed, VERSION + MANIFEST.json written
```

### 2. `python -m pytest -p no:cacheprovider -q tests/test_program_launcher_forms.py`

```
.................................                                        [100%]
33 passed in 50.32s
```

### 3. `python -m pytest -p no:cacheprovider -q tests/test_bridge_run.py tests/test_bridge_run_driver.py tests/test_release_s_launcher.py`

```
........................................................................ [ 54%]
...........................................................              [100%]
131 passed in 47.32s
```

### 4. `python -m pytest -p no:cacheprovider -q tests/test_bug029_agent_name.py tests/test_task032_supervisor_launcher.py tests/test_header_plan.py tests/test_header_plan_r3.py`

```
........................................................................ [ 41%]
........................................................................ [ 82%]
...............................                                          [100%]
175 passed in 97.33s (0:01:37)
```

### 5. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`

```
bridge-check: version 2026.11.12a (2026-11-14 12:14) at <Workspace>\bridge
bridge-check: 146 OK, 0 STALE, 0 MISSING, 0 EXTRA
RESULT: SOURCES MATCH bridge 2026.11.12a
```

### 6. `git rev-parse HEAD` and `git status --short`

```
3a37bde53c33a4e009b499c3802e88401148917e
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/bridge-run.py
 M bridge/cursor-bridge/bridge_env.py
 M tests/test_bridge_run.py
 M tests/test_bridge_run_driver.py
 M tests/test_release_s_launcher.py
```

Counts above belong to commit `3a37bde53c33a4e009b499c3802e88401148917e` with uncommitted changes as listed.

## Builder tests added (R-078)

- `tests/test_bridge_run_driver.py::test_r078_driver_with_interpreter_flags_substitutes_program_end_to_end`
- `tests/test_release_s_launcher.py::test_r078_npm_prefix_through_an_inbound_link_is_refused`
- `tests/test_bridge_run.py::test_r078_npm_prefix_and_c_count_as_one_folder_option`

## Mutations (manual spot-check)

- (M1) Accepting `-B` twice: refused by `tests/test_program_launcher_forms.py::test_r078_every_other_interpreter_option_is_refused` and `test_r078_a_refused_option_of_a_known_runner_is_a_defect_to_report`.
- (M2) Accepting `-X dev`: refused by the same interpreter refusal tests.
- (M3) Skipping link walk: would let `tests/test_program_launcher_forms.py::test_r078_a_folder_outside_missing_or_through_a_link_is_refused_naming_the_option` and `test_r078_npm_prefix_through_an_inbound_link_is_refused` pass wrongly.
- (M4) Dropping the three-character abbreviation bound: would break abbreviated folder forms in `test_r078_a_folder_inside_the_launch_folder_is_accepted_in_every_form`.
- (M5) Reading a folder option after `--`: would accept `npm test -- <outside>` in that acceptance test instead of treating it as a script argument only.
- (M6) Writing unsorted `merge_ids`: would fail `test_r078_merge_ids_is_written_sorted_whatever_the_briefs_order`.

## Assumed, not verified

Assumed, not verified: none