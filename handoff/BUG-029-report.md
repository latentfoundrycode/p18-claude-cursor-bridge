# BUG-029 report

## Files changed

- `bridge/cursor-bridge/bridge-run.py`
- `handoff/BUG-029-report.md`

## Summary

BUG-029 is fixed in `bridge-run.py` by adding `is_agent_argv` so only bare `AGENT_NAMES` tokens count as the agent, teaching `head_of` to strip a single trailing `.exe` or `.cmd`, reordering `acquire_heavy_slot` so the holder record is published before the `slot taken` line, and routing every agent check through `is_agent_argv` including `resolve`.

Cause 1: acceptance and `resolve` now share `is_agent_argv`, so a command is only treated as the agent when `argv[0]` is an exact bare name that `resolve` replaces with the real launcher. Cause 2: `publish_holder_record` runs before stderr prints `bridge-run: slot taken`, so waiters that react to that line see the current holder.

## `is_agent_argv` call sites

- `kind_of`
- `design_ceiling`
- `head_text`
- `workspace_of`
- `review_family_refusal`
- `resolve`
- `main` (key-file refusal and review-only refusal)

## Verification

### 1. Before change: `python -m pytest tests/test_bug029_agent_name.py -q -p no:cacheprovider`

```text
=========================== short test summary info ===========================
FAILED tests/test_bug029_agent_name.py::test_bug029_head_of_strips_one_trailing_suffix
FAILED tests/test_bug029_agent_name.py::test_bug029_only_the_exact_agent_names_are_the_agent
FAILED tests/test_bug029_agent_name.py::test_bug029_resolve_swaps_in_the_agent_for_an_exact_name_only
FAILED tests/test_bug029_agent_name.py::test_bug029_a_doubled_suffix_never_runs_as_the_agent[review]
FAILED tests/test_bug029_agent_name.py::test_bug029_a_doubled_suffix_never_runs_as_the_agent[None]
FAILED tests/test_bug029_agent_name.py::test_bug029_record_published_before_the_slot_taken_line
6 failed in 0.70s
```

### 2. After change: `python -m pytest tests/test_bug029_agent_name.py -q -p no:cacheprovider`

```text
6 passed in 0.33s
```

### 3. `python -m pytest tests/test_bridge_run.py tests/test_bridge_run_slot.py tests/test_bridge_run_driver.py -q`

```text
132 passed, 3 skipped in 133.69s (0:02:13)
```

### 4. `python -m pytest tests -q`

```text
39 failed, 2388 passed, 38 skipped, 9 errors in 539.87s (0:08:59)
```

Install-stamp failures (MANIFEST.json not regenerated (expected)):

- `tests/test_core_carve.py::test_r003_the_modules_install_from_the_manifest`
- `tests/test_install_check.py::test_install_into_a_fresh_target_passes_the_check`
- `tests/test_install_check.py::test_the_check_reports_a_missing_or_damaged_agent_home`
- `tests/test_install_check.py::test_install_over_owner_settings_keeps_them_and_backs_up`
- `tests/test_install_check.py::test_shim_is_installed_where_the_cli_lives_with_a_backup`
- `tests/test_install_check.py::test_check_reports_missing_bridge_entry_and_ignores_owner_keys`
- `tests/test_install_check.py::test_check_reports_a_hook_that_runs_a_bridge_program_which_is_not_installed`
- `tests/test_install_check.py::test_dry_run_writes_nothing`
- `tests/test_install_check.py::test_programs_survive_a_character_the_console_lacks`
- `tests/test_install_check.py::test_the_source_tree_is_checked_against_its_manifest_only`
- `tests/test_install_check.py::test_a_checkout_is_installed_only_as_main_as_merged`
- `tests/test_install_check_a4.py::test_a_checkout_without_a_readable_origin_main_is_refused`
- `tests/test_install_check_a4.py::test_pythons_cache_folder_is_not_an_uncommitted_change`
- `tests/test_install_check_a4.py::test_a_release_that_could_not_be_taken_back_is_not_installed`
- `tests/test_rollback.py::test_rollback_restores_the_previous_shim`
- `tests/test_rollback.py::test_a_file_changed_on_this_computer_is_named_when_kept_and_the_way_back_refuses_it`
- `tests/test_rollback.py::test_installing_an_older_release_over_a_newer_one_takes_the_newer_entries_out`
- `tests/test_rollback.py::test_a_program_an_owner_hook_runs_is_not_removed`
- `tests/test_rollback.py::test_settings_of_an_unexpected_shape_are_refused_before_anything_changes`
- `tests/test_rollback.py::test_a_file_that_cannot_be_written_ends_in_a_sentence_and_the_run_can_be_repeated`
- `tests/test_rollback.py::test_an_interrupted_replacement_never_leaves_a_hook_without_its_program[write_settings-older over newer]`
- `tests/test_rollback.py::test_an_interrupted_replacement_never_leaves_a_hook_without_its_program[write_settings-newer over older]`
- `tests/test_rollback.py::test_an_interrupted_replacement_never_leaves_a_hook_without_its_program[remove_files-older over newer]`
- `tests/test_rollback.py::test_an_interrupted_replacement_never_leaves_a_hook_without_its_program[remove_files-newer over older]`
- `tests/test_rollback.py::test_an_interrupted_replacement_never_leaves_a_hook_without_its_program[copy_tree-older over newer]`
- `tests/test_rollback.py::test_an_interrupted_replacement_never_leaves_a_hook_without_its_program[copy_tree-newer over older]`
- `tests/test_rollback.py::test_an_install_killed_at_the_nth_copied_file_can_be_repeated[1-older over newer]`
- `tests/test_rollback.py::test_an_install_killed_at_the_nth_copied_file_can_be_repeated[1-newer over older]`
- `tests/test_rollback.py::test_an_install_killed_at_the_nth_copied_file_can_be_repeated[40-older over newer]`
- `tests/test_rollback.py::test_an_install_killed_at_the_nth_copied_file_can_be_repeated[40-newer over older]`
- `tests/test_rollback.py::test_an_install_killed_at_the_nth_copied_file_can_be_repeated[98-older over newer]`
- `tests/test_rollback.py::test_an_install_killed_at_the_nth_copied_file_can_be_repeated[98-newer over older]`
- `tests/test_rollback.py::test_an_install_killed_at_the_nth_copied_file_can_be_repeated[99-older over newer]`
- `tests/test_rollback.py::test_an_install_killed_at_the_nth_copied_file_can_be_repeated[99-newer over older]`
- `tests/test_rollback.py::test_an_install_killed_at_the_nth_copied_file_can_be_repeated[140-older over newer]`
- `tests/test_rollback.py::test_an_install_killed_at_the_nth_copied_file_can_be_repeated[140-newer over older]`
- `tests/test_rollback.py::test_an_install_killed_at_the_nth_copied_file_can_be_repeated[196-older over newer]`
- `tests/test_rollback.py::test_an_install_killed_at_the_nth_copied_file_can_be_repeated[196-newer over older]`
- `tests/test_rollback.py::test_a_rollback_killed_part_way_is_finished_with_the_release_folders_installer`

The nine errors in the full run are the same manifest/install-stamp class (no separate defect reported).

### 5. Mutation check (code restored after each; `git diff` empty of mutation residue)

1. `head_of` strips `.exe` and `.cmd` everywhere again. Caught by `test_bug029_head_of_strips_one_trailing_suffix`. Summary: `1 failed, 21 passed in 14.68s`.
2. `is_agent_argv` uses basename only (no path refusal). Caught by `test_bug029_only_the_exact_agent_names_are_the_agent` and `test_bug029_resolve_swaps_in_the_agent_for_an_exact_name_only`. Summary: `2 failed, 20 passed in 14.78s`.
3. Holder record published after the `slot taken` line again. Caught by `test_bug029_record_published_before_the_slot_taken_line`. Summary: `1 failed, 21 passed in 28.37s`.
4. `resolve` uses `head_of(argv) == "cursor-agent"` instead of `is_agent_argv`. Caught by `test_bug029_resolve_swaps_in_the_agent_for_an_exact_name_only`. Summary: `1 failed, 21 passed in 14.43s`.

Post-restore re-runs: `6 passed in 0.33s` (BUG-029 file); `132 passed, 3 skipped in 133.69s` (launcher suites).

### 6. `python tools/dump-cli.py --check`

(no output; exit 0)

### 7. `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge/bridge-run.py`

```text
windowless-check: 1 file(s) scanned, 0 FAIL, 0 NOTE
```

### 8. `git diff -- bridge/cursor-bridge/bridge-run.py`

Diff adds `is_agent_argv`, fixes `head_of` to one trailing suffix, switches listed call sites to `is_agent_argv`, and moves `slot taken` after `publish_holder_record`. Lines 1–88 unchanged.

### 9. `git status --porcelain`

```text
 M bridge/cursor-bridge/bridge-run.py
?? handoff/BUG-029-report.md
```

### 10. Leftover processes: `tasklist //FI "IMAGENAME eq python.exe"`

One `python.exe` (PID 29704, ~24 MB) was listed at check time; it was not tied to a specific test subprocess from this run.

## Assumed, not verified

- `os.path.dirname(argv[0])` is empty on every platform for the three bare agent names the tests use · the brief names directory separators and drive prefixes but does not define every edge token · a POSIX-only argv such as a lone drive-relative name was not exercised here.
- After `publish_holder_record`'s `os.replace`, another process reading the holder file on the `slot taken` line sees the new record · the reproduction test reads the file in the same process at stderr write time · cross-process visibility on all OS file systems was not measured separately.
- The nine errors in the full pytest run are manifest/install-stamp only · only failed test ids were classified from the summary list · error tracebacks were not re-opened one by one.
