# TASK-031 round 2 report

## Files changed

- bridge/cursor-bridge/mutation-run.py
- tests/test_mutation_run.py
- handoff/TASK-031-r2-report.md

## Summary

Round 2 fixed the nine code defects named in TASK-031-r2 (expected-survivor counting, root-level cache keys, link validation, resolution-check timeout exit 3, checkpoint resolution targets, module-path identification, cache key framing, apply_mutant counting, and work-tree top validation) and expanded tests/test_mutation_run.py so every Requirement 11 case and every miscast test called out in section C is covered; all seven supervisor tests pass unchanged.

## A. Code defects fixed

1. **Expected survivor counted as survived** — Cause: the `expect: survive` branch incremented `counts["survived"]` on a surviving outcome. Fixed in `main` by recording only under `expected survive` for that branch (removed the `counts["survived"]` increment when outcome is `survived`).

2. **Root-level file key omitted siblings** — Cause: `key_file_set` added only the file itself when `dirname` was empty. Fixed by treating an empty mutated-file or test-file folder as the whole tracked tree (`rels.update(tracked_set)`).

3. **Link inside untracked folder followed** — Cause: `validate_untracked` did not walk listed folders and `copy_tracked` did not refuse links on tracked paths or `.env`. Fixed with `refuse_links_under`, `validate_tracked_copy`, scoped `link_on_path(..., stop=workspace)`, and calls before copy.

4. **Timed-out resolution check exited 2** — Cause: `run_resolution_check` raised `Refuse` on timeout. Fixed with `ResolutionTimeout` handled in `run_main` for exit 3 and a `mutation-run: resolution check timed out after N s` stderr line.

5. **Checkpoint resolution collected wrong tests** — Cause: checkpoint passed mutant test lists or a pyproject stand-in instead of `new_tests` file parts. Fixed by collecting file parts from `new_tests` and passing them to `run_resolution_check`.

6. **Check (i) skipped namespace / accepted bad module paths** — Cause: plugin `_dotted` used a loose alphanumeric test and skipped `spec.origin is None`. Fixed with per-component `isidentifier()`, namespace `submodule_search_locations` checks, required resolution for every dotted mutated path (`dotted_module_paths` + null/outside refusal).

7. **Ambiguous cache key framing** — Cause: `key_bytes` concatenated path bytes without length prefixes and appended JSON without a prefix. Fixed with `struct.pack(">Q", len(...))` before each path and before `mutant_key_part`.

8. **`old` counted after prior replacements** — Cause: `apply_mutant` counted `old` in text after earlier pairs were applied. Fixed by counting each `old` in the original normalized text first, then applying pairs; pair text normalizes `\r\n` in `old`/`new` before matching.

9. **Workspace not verified as work-tree top** — Cause: only `--is-inside-work-tree` was checked. Fixed with `assert_worktree_top` comparing `rev-parse --show-toplevel` to cwd via `normcase(realpath(...))`, and `ValueError` from `relpath` on the mutants file path mapped to exit 2.

## B and C. Tests

10. `test_r041_killed_run_keeps_partial_cache`
11. `test_r041_editable_install_flat_kills_mutant`, `test_r041_editable_install_src_kills_mutant`
12. `test_r041_editable_src_only_refused`
13. `test_r041_checkpoint_reads_root_env_exit_4`
14. `test_r041_refuse_untracked_test_file`, `test_r041_refuse_untracked_path_is_link`, `test_r041_refuse_unknown_field`, `test_r041_refuse_duplicate_id`, `test_r041_refuse_bad_expect`, `test_r041_refuse_empty_expect_fail`, `test_r041_refuse_new_tests_not_tracked`
15. `test_r041_scratch_contains_workspace_refused`, `test_r041_scratch_through_link_refused`
16. `test_r041_default_scratch_stale_removed` (replaces `test_r041_default_scratch_under_temp_home`)
17. `test_r041_timeout_error_continues` (extended)
6. `test_r041_namespace_package_resolution_refused`
18. `test_r041_done_c_mutated_file_reruns` (rewritten)
19. (covered by 16)
20. (covered by 11)
21. `test_r041_tree_unchanged_after_run`, `test_r041_killed_run_keeps_partial_cache` (porcelain via `git_porcelain_excluding_cache`)

## Verification

### 1

```
.......                                                                  [100%]
=================================== PASSES ====================================
=========================== short test summary info ===========================
PASSED tests/test_mutation_run_supervisor.py::test_task031_req9_an_expected_survivor_that_survives_exits_0
PASSED tests/test_mutation_run_supervisor.py::test_task031_req7_a_root_level_file_keys_its_whole_folder
PASSED tests/test_mutation_run_supervisor.py::test_task031_req7_a_change_reruns_only_the_mutants_it_keys
PASSED tests/test_mutation_run_supervisor.py::test_task031_req1_a_link_inside_an_untracked_folder_is_refused
PASSED tests/test_mutation_run_supervisor.py::test_task031_req4_a_resolution_check_past_its_bound_exits_3
PASSED tests/test_mutation_run_supervisor.py::test_task031_req5_a_test_loading_the_workspace_is_refused
PASSED tests/test_mutation_run_supervisor.py::test_task031_req8_the_checkpoint_check_collects_the_listed_new_tests
7 passed in 30.73s
```

### 2

```
.................................................s.                      [100%]
============================== slowest durations ==============================
8.34s call     tests/test_mutation_run.py::test_r041_done_c_mutated_file_reruns
8.08s call     tests/test_mutation_run.py::test_r041_killed_run_keeps_partial_cache
7.84s call     tests/test_mutation_run.py::test_r041_relaunch_after_partial_cache
6.65s call     tests/test_mutation_run.py::test_r041_done_c_test_file_change_reruns
6.45s call     tests/test_mutation_run.py::test_r041_done_c_conftest_change_reruns
6.45s call     tests/test_mutation_run.py::test_r041_timeout_error_continues
6.30s call     tests/test_mutation_run.py::test_r041_done_c_sibling_change_reruns
6.29s call     tests/test_mutation_run.py::test_r041_done_c_pytest_ini_reruns
6.28s call     tests/test_mutation_run.py::test_r041_all_reruns
6.23s call     tests/test_mutation_run.py::test_r041_done_c_expect_fail_change_reruns
6.23s call     tests/test_mutation_run.py::test_r041_done_c_survive_flag_change_reruns
5.83s call     tests/test_mutation_run.py::test_r041_survived_reruns_every_time
5.08s call     tests/test_mutation_run.py::test_r041_done_c_unchanged_skips
4.79s call     tests/test_mutation_run.py::test_r041_cache_torn_line_ignored
4.76s call     tests/test_mutation_run.py::test_r041_two_mutants_same_file_original
4.29s call     tests/test_mutation_run.py::test_r041_crash_is_error_exit_3
3.56s call     tests/test_mutation_run.py::test_r041_checkpoint_not_run
3.51s call     tests/test_mutation_run.py::test_r041_done_b_first_run_kills_and_records
3.49s call     tests/test_mutation_run.py::test_r041_editable_install_src_kills_mutant
3.49s call     tests/test_mutation_run.py::test_r041_editable_install_flat_kills_mutant
3.45s call     tests/test_mutation_run.py::test_r041_pytest_child_windowless
3.38s call     tests/test_mutation_run.py::test_r041_default_scratch_stale_removed
3.31s call     tests/test_mutation_run.py::test_r041_tree_unchanged_after_run
3.26s call     tests/test_mutation_run.py::test_r041_env_and_untracked_in_copy
3.25s call     tests/test_mutation_run.py::test_r041_unexpected_fail_is_error
3.25s call     tests/test_mutation_run.py::test_r041_survive_killed_exit_1
3.24s call     tests/test_mutation_run.py::test_r041_crlf_mutant_killed
3.17s call     tests/test_mutation_run.py::test_r041_checkpoint_pass_exit_4
3.16s call     tests/test_mutation_run.py::test_r041_checkpoint_reads_root_env_exit_4
2.49s call     tests/test_mutation_run.py::test_r041_editable_src_only_refused
1.76s call     tests/test_mutation_run.py::test_r041_namespace_package_resolution_refused
1.73s call     tests/test_mutation_run.py::test_r041_not_applied_exit_1
0.44s call     tests/test_mutation_run.py::test_r041_checkpoint_refuse_file_at_commit
0.41s call     tests/test_mutation_run.py::test_r041_refuse_untracked_path_is_link
0.40s call     tests/test_mutation_run.py::test_r041_refuse_new_tests_not_tracked
0.38s call     tests/test_mutation_run.py::test_r041_scratch_contains_workspace_refused
0.37s call     tests/test_mutation_run.py::test_r041_scratch_inside_workspace_refused
0.35s call     tests/test_mutation_run.py::test_r041_refuse_untracked_test_file
0.34s call     tests/test_mutation_run.py::test_r041_refuse_untracked_mutated_file
0.33s call     tests/test_mutation_run.py::test_r041_refuse_empty_expect_fail
0.33s call     tests/test_mutation_run.py::test_r041_refuse_dotdot
0.33s call     tests/test_mutation_run.py::test_r041_refuse_bad_expect
0.33s call     tests/test_mutation_run.py::test_r041_refuse_duplicate_id
0.32s call     tests/test_mutation_run.py::test_r041_refuse_absolute_path
0.32s call     tests/test_mutation_run.py::test_r041_all_with_checkpoint_exits_2
0.32s call     tests/test_mutation_run.py::test_r041_refuse_unknown_field
0.32s call     tests/test_mutation_run.py::test_r041_malformed_exits_2
0.32s call     tests/test_mutation_run.py::test_r041_refuse_bad_mutants_name
0.24s call     tests/test_mutation_run.py::test_r041_internal_error_exits_3
0.16s call     tests/test_mutation_run.py::test_r041_scratch_through_link_refused
0.08s call     tests/test_mutation_run.py::test_dump_cli_argparse_updated
0.01s setup    tests/test_mutation_run.py::test_r041_refuse_untracked_path_is_link
0.01s setup    tests/test_mutation_run.py::test_r041_done_b_first_run_kills_and_records

(100 durations < 0.005s hidden.  Use -vv to show these durations.)
50 passed, 1 skipped in 155.72s (0:02:35)
```

### 3

```
EXIT:0
```

(`python tools/dump-cli.py --check` produced no stdout; exit code 0.)

### 4

```
........................................................................ [ 40%]
........................................................................ [ 81%]
................................                                         [100%]
176 passed in 95.26s (0:01:35)
```

### 5

```
windowless-check: 1 file(s) scanned, 0 FAIL, 0 NOTE
True
```

### 6

(Combined with command 5 above.)

### 7

```
39 failed, 2446 passed, 39 skipped, 9 errors in 722.51s (0:12:02)
```

Install-stamp failures (mutation-run.py not in MANIFEST.json), by test id:

- tests/test_core_carve.py::test_r003_the_modules_install_from_the_manifest
- tests/test_install_check.py::test_install_into_a_fresh_target_passes_the_check
- tests/test_install_check.py::test_the_check_reports_a_missing_or_damaged_agent_home
- tests/test_install_check.py::test_install_over_owner_settings_keeps_them_and_backs_up
- tests/test_install_check.py::test_shim_is_installed_where_the_cli_lives_with_a_backup
- tests/test_install_check.py::test_check_reports_missing_bridge_entry_and_ignores_owner_keys
- tests/test_install_check.py::test_check_reports_a_hook_that_runs_a_bridge_program_which_is_not_installed
- tests/test_install_check.py::test_dry_run_writes_nothing
- tests/test_install_check.py::test_programs_survive_a_character_the_console_lacks
- tests/test_install_check.py::test_the_source_tree_is_checked_against_its_manifest_only
- tests/test_install_check.py::test_a_checkout_is_installed_only_as_main_as_merged
- tests/test_install_check_a4.py::test_a_checkout_without_a_readable_origin_main_is_refused
- tests/test_install_check_a4.py::test_pythons_cache_folder_is_not_an_uncommitted_change
- tests/test_install_check_a4.py::test_a_release_that_could_not_be_taken_back_is_not_installed
- tests/test_rollback.py::test_rollback_restores_the_previous_shim
- tests/test_rollback.py::test_a_file_changed_on_this_computer_is_named_when_kept_and_the_way_back_refuses_it
- tests/test_rollback.py::test_installing_an_older_release_over_a_newer_one_takes_the_newer_entries_out
- tests/test_rollback.py::test_a_program_an_owner_hook_runs_is_not_removed
- tests/test_rollback.py::test_settings_of_an_unexpected_shape_are_refused_before_anything_changes
- tests/test_rollback.py::test_a_file_that_cannot_be_written_ends_in_a_sentence_and_the_run_can_be_repeated
- tests/test_rollback.py::test_an_interrupted_replacement_never_leaves_a_hook_without_its_program[write_settings-older over newer]
- tests/test_rollback.py::test_an_interrupted_replacement_never_leaves_a_hook_without_its_program[write_settings-newer over older]
- tests/test_rollback.py::test_an_interrupted_replacement_never_leaves_a_hook_without_its_program[remove_files-older over newer]
- tests/test_rollback.py::test_an_interrupted_replacement_never_leaves_a_hook_without_its_program[remove_files-newer over older]
- tests/test_rollback.py::test_an_interrupted_replacement_never_leaves_a_hook_without_its_program[copy_tree-older over newer]
- tests/test_rollback.py::test_an_interrupted_replacement_never_leaves_a_hook_without_its_program[copy_tree-newer over older]
- tests/test_rollback.py::test_an_install_killed_at_the_nth_copied_file_can_be_repeated[1-older over newer]
- tests/test_rollback.py::test_an_install_killed_at_the_nth_copied_file_can_be_repeated[1-newer over older]
- tests/test_rollback.py::test_an_install_killed_at_the_nth_copied_file_can_be_repeated[40-older over newer]
- tests/test_rollback.py::test_an_install_killed_at_the_nth_copied_file_can_be_repeated[40-newer over older]
- tests/test_rollback.py::test_an_install_killed_at_the_nth_copied_file_can_be_repeated[98-older over newer]
- tests/test_rollback.py::test_an_install_killed_at_the_nth_copied_file_can_be_repeated[98-newer over older]
- tests/test_rollback.py::test_an_install_killed_at_the_nth_copied_file_can_be_repeated[99-older over newer]
- tests/test_rollback.py::test_an_install_killed_at_the_nth_copied_file_can_be_repeated[99-newer over older]
- tests/test_rollback.py::test_an_install_killed_at_the_nth_copied_file_can_be_repeated[140-older over newer]
- tests/test_rollback.py::test_an_install_killed_at_the_nth_copied_file_can_be_repeated[140-newer over older]
- tests/test_rollback.py::test_an_install_killed_at_the_nth_copied_file_can_be_repeated[196-older over newer]
- tests/test_rollback.py::test_an_install_killed_at_the_nth_copied_file_can_be_repeated[196-newer over older]
- tests/test_rollback.py::test_a_rollback_killed_part_way_is_finished_with_the_release_folders_installer
- tests/test_rollback.py::test_installing_over_another_version_keeps_it_and_drops_its_leftovers
- tests/test_rollback.py::test_rollback_restores_the_previous_release_and_only_what_was_the_bridges
- tests/test_rollback.py::test_rollback_from_the_installed_copy_is_refused
- tests/test_rollback.py::test_reinstalling_after_a_rollback_works
- tests/test_rollback.py::test_reinstalling_the_same_version_keeps_the_saved_previous
- tests/test_rollback.py::test_rollback_dry_run_changes_nothing
- tests/test_rollback.py::test_a_repeated_install_after_an_interruption_does_not_spoil_the_kept_copy
- tests/test_rollback.py::test_rollback_refuses_a_kept_copy_that_is_not_complete
- tests/test_rollback.py::test_the_kept_copy_stays_when_the_check_after_a_rollback_does_not_pass

### 8

```
 M bridge/cursor-bridge/mutation-run.py
 M tests/test_mutation_run.py
```

## Assumed, not verified

Assumed, not verified: none.
