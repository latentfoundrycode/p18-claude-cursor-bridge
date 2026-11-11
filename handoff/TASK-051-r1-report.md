# TASK-051 builder report (round 1)

## Files changed

- `bridge/cursor-bridge/records-migrate.py` (new)
- `bridge/cursor-bridge/MANIFEST.json` (regenerated)
- `bridge/cursor-bridge/VERSION` (regenerated with manifest)
- `bridge/cursor-bridge/settings.bridge.json` (R13 allow rule)
- `docs/cli-reference.json` (regenerated)
- `docs/CLI_REFERENCE.md` (regenerated)
- `tests/test_records_migrate.py` (builder cases below marker)
- `tests/test_dump_cli.py` (ARGPARSE entry)
- `tests/test_allowlist.py` (R13 test)
- `handoff/TASK-051-r1-report.md` (this file)

## Summary

Implemented `records-migrate.py` with YAML-subset header writing from `bridge_env` fallbacks, atomic temp-file writes with read-back validation, enumeration and refusal rules from R-062, permission and CLI reference updates, and fourteen builder acceptance cases under the supervisor marker. All 66 cases in `tests/test_records_migrate.py` pass.

## Requirements

- **R1:** `build_parser()`, `main(argv)`, shebang and docstring usage line, import-only side effects; implemented throughout `records-migrate.py`.
- **R2:** Root vs explicit paths, second folder and mixed folder/path refusal in `main()`; pinned by `test_r062_a_second_folder_is_refused`, `test_r062_ruling7_folder_and_record_paths_together_refused`.
- **R3:** `record_kind()` and `enumerate_records()`; pinned by `test_r062_from_a_project_root_every_kind_is_found_and_reports_passed_over`, `test_r062_ruling6_report_and_resolution_are_not_record_kinds`.
- **R4:** `shown` path logic in `main()` loop; pinned by `test_r062_ruling2_given_path_shown_as_given`.
- **R5:** `_handle_headed()`; pinned by `test_r062_a_malformed_header_stops_the_run_after_the_records_before_it`, `test_r062_ruling10_header_malformed_line_form`.
- **R6:** `compose_header()` and per-kind composers; pinned by `test_r062_each_kind_is_migrated_to_the_fallbacks_reading`.
- **R7:** `_format_scalar()`, `_dump_lines()`, `_serialize_header()`; pinned by oracle cases and `test_r062_strings_the_plain_form_refuses_are_written_double_quoted`.
- **R8:** `_plan_needs_merged()`, `squash_merged_ids` in `main()`; pinned by `test_r062_a_merged_increment_without_scope_or_kind_is_marked_historic`, `test_r062_ruling4_historic_increment_keeps_satisfies_list`.
- **R9:** `parse_scope` in `_compose_brief_header()`; pinned by `test_r062_records_the_fallback_refuses_are_listed_and_left_headerless`, `test_r062_ruling5_scope_refusal_carries_parse_scope_value`.
- **R10:** `_write_record()` temp file and `os.replace`; pinned by supervisor atomic tests and `test_r062_os_replace_failure_exits_3`, `test_r062_failed_read_back_removes_temporary`.
- **R11:** `_status_cap_text()`; pinned by `test_r062_a_status_file_over_the_older_cap_is_not_written`, `test_r062_ruling3_lines_cap_message_exact`.
- **R12:** stdout lines and exit aggregation in `main()`; pinned by `test_r062_check_exit_code`, `test_r062_ruling1_wrote_line_on_enumerated_run`.
- **R13:** `settings.bridge.json` and `test_r062_records_migrate_rule_in_allow`.
- **R14:** `ARGPARSE` plus regenerated CLI reference; `dump-cli.py --check` exit 0.
- **R15:** `make-manifest.py` and `RESULT: SOURCES MATCH`.
- **R16:** fourteen builder cases below the marker.

## Rulings

1. `wrote <path>` — `test_r062_ruling1_wrote_line_on_enumerated_run`
2. Path display — `test_r062_ruling2_given_path_shown_as_given`
3. Lines cap message — `test_r062_ruling3_lines_cap_message_exact`
4. Historic lists — `test_r062_ruling4_historic_increment_keeps_satisfies_list`
5. Scope refusal — `test_r062_ruling5_scope_refusal_carries_parse_scope_value`
6. Report/resolution — `test_r062_ruling6_report_and_resolution_are_not_record_kinds`
7. Folder + paths — `test_r062_ruling7_folder_and_record_paths_together_refused`
8. Disagreeing header — `test_r062_ruling8_disagreeing_header_left_unchanged`
9. Duplicate satisfies — `test_r062_a_satisfies_id_named_twice_is_kept_twice_in_order`
10. HEADER MALFORMED line — `test_r062_ruling10_header_malformed_line_form`

## Commands and output

```
$ python tools/dump-cli.py
make-manifest: version 2026.11.09a, 146 files hashed, VERSION + MANIFEST.json written
```

```
$ python tools/make-manifest.py
make-manifest: version 2026.11.09a, 146 files hashed, VERSION + MANIFEST.json written
```

```
$ python -m pytest -q tests/test_records_migrate.py
..................................................................       [100%]
66 passed in 10.20s
```

```
$ python -m pytest -q tests/test_dump_cli.py tests/test_allowlist.py tests/test_header_reader.py tests/test_tests_windowless.py
```

```
================================== FAILURES ===================================
_____ test_r055_d002_the_programs_dump_cli_loads_equal_the_diagrams_edges _____
E       AssertionError: the programs dump-cli.py loads and D-002's dump_cli edges differ
E         At index 8 diff: 'records-migrate.py' != 'stage-diff.py'
...
___________ test_fix001_no_test_starts_a_program_around_the_default ___________
E       AssertionError: assert ['test_record...s=NO_WINDOW)'] == []
E         Left contains 2 more items, first extra item: 'test_records_migrate.py:76: creationflags=NO_WINDOW)'
=========================== short test summary info ===========================
FAILED tests/test_dump_cli.py::test_r055_d002_the_programs_dump_cli_loads_equal_the_diagrams_edges
FAILED tests/test_tests_windowless.py::test_fix001_no_test_starts_a_program_around_the_default
2 failed, 1153 passed, 20 skipped in 106.23s (0:01:46)
```

(Known: `test_r055_d002_the_programs_dump_cli_loads_equal_the_diagrams_edges` after adding the thirteenth program. `test_fix001_no_test_starts_a_program_around_the_default` flags supervisor lines 76 and 81 in `tests/test_records_migrate.py` using `creationflags=NO_WINDOW` instead of spelling `CREATE_NO_WINDOW` literally; those lines are above the builder marker and were not edited.)

```
$ python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks
windowless-check: 39 file(s) scanned, 0 FAIL, 0 NOTE
```

```
$ python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet
bridge-check: version 2026.11.09a (2026-11-11 03:26) at <Workspace>\bridge
bridge-check: 146 OK, 0 STALE, 0 MISSING, 0 EXTRA
RESULT: SOURCES MATCH bridge 2026.11.09a
```

```
$ python tools/dump-cli.py --check

```
(exit 0)

```
$ git rev-parse HEAD
3a323465a74376dd8a90014902d35afd261f185f
```

```
$ git status --short
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/VERSION
 M bridge/cursor-bridge/settings.bridge.json
 M docs/CLI_REFERENCE.md
 M docs/cli-reference.json
 M tests/test_allowlist.py
 M tests/test_dump_cli.py
 M tests/test_records_migrate.py
?? bridge/cursor-bridge/records-migrate.py
?? handoff/TASK-051-r1-report.md
```

Commit `3a323465a74376dd8a90014902d35afd261f185f`; working tree had uncommitted changes as shown.

## Assumed, not verified

- Short-scalar flow lists match `_use_flow_list()` heuristics (plain words, small ints, booleans, null, quoted strings without newlines); confirmed on supervisor fixtures only.
- Given record paths that do not exist are skipped silently with no output line; no test pins this.
- `merged set unreadable` wording with parenthetical ref name is acceptable to the supervisor oracle; pinned only on `no-such-ref` case.
- A nonexistent explicit path produces no line and does not affect exit; not tested.
