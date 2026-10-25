# BUG-020-r1 report

## Files changed

- `bridge/cursor-bridge/loop-guard.py` (only `cron_next`: signature, docstring, body)
- `handoff/BUG-020-r1-report.md` (this file)
- `docs/BUILDER_NOTES.md` (append-only, one line)

## Summary

Repaired `cron_next` in `loop-guard.py` so it walks Unix instants in 60-second steps from the first whole minute after `now`, interprets each instant as local wall time with `datetime.fromtimestamp(instant, tz)` (new keyword `tz=None` for the host local zone), matches the five cron fields, and returns the matching instant directly instead of advancing a naive datetime and converting back with `.timestamp()`.

## Named cause

The loop now advances `instant` by 60 seconds and reads wall time with `fromtimestamp(instant, tz)` on each step, returning that instant on match, which visits both occurrences of a repeated hour and never resolves an ambiguous wall time through `.timestamp()`.

## Verification

### 1. Before edit: `python -m pytest tests -q -p no:cacheprovider`

Exit code 1. Counts line: `32 failed, 2125 passed, 33 skipped, 9 errors in 357.53s`.

The fix was applied while this run was still in progress (~30% through), so the recorded run is not a clean pre-edit baseline; `tests/test_loop_guard.py` did not appear in the failure summary because the module loaded after the edit. Per the brief, the reproduction test would fail with `TypeError` on `tz` before the change; confirmed on committed code: `TypeError: cron_next() got an unexpected keyword argument 'tz'`.

Failing tests in that run (all cite `cursor-bridge/loop-guard.py (changed)` in bridge-install output except where install never reached the assertion under test):

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
- `tests/test_rollback.py::test_an_interrupted_replacement_never_leaves_a_hook_without_its_program` (8 parametrized cases)
- `tests/test_rollback.py::test_an_install_killed_at_the_nth_copied_file_can_be_repeated` (12 parametrized cases)
- `tests/test_rollback.py::test_a_rollback_killed_part_way_is_finished_with_the_release_folders_installer`
- ERROR: nine `tests/test_rollback.py` tests (install/setup blocked by stale `loop-guard.py`)

### 2. After fix: `python -m pytest "tests/test_loop_guard.py::test_bug020_a_one_shot_in_the_repeated_hour_is_found" "tests/test_loop_guard.py::test_the_hook_input_is_read_in_its_live_forms" -q -p no:cacheprovider -rs`

Exit code 0. Output: `2 passed in 1.85s`. None skipped.

### 3. `python -m pytest tests/test_loop_guard.py -q -p no:cacheprovider -rs`

Exit code 0. Output: `57 passed in 0.77s`. None skipped.

### 4. After fix: `python -m pytest tests -q -p no:cacheprovider`

Exit code 1. Counts line: `39 failed, 2118 passed, 33 skipped, 9 errors in 360.95s`.

Compared with step 1, `tests/test_loop_guard.py::test_bug020_a_one_shot_in_the_repeated_hour_is_found` now passes (not listed in failures). Seven additional failures versus the contaminated step-1 run, all from install/rollback paths that copy the Workspace `bridge/` tree and hit the unstamped `loop-guard.py` change:

- `tests/test_core_carve.py::test_r003_the_modules_install_from_the_manifest`
- `tests/test_install_check.py::test_install_into_a_fresh_target_passes_the_check`
- `tests/test_install_check.py::test_the_check_reports_a_missing_or_damaged_agent_home`
- `tests/test_install_check.py::test_install_over_owner_settings_keeps_them_and_backs_up`
- `tests/test_install_check.py::test_shim_is_installed_where_the_cli_lives_with_a_backup`
- `tests/test_install_check.py::test_check_reports_missing_bridge_entry_and_ignores_owner_keys`
- `tests/test_install_check.py::test_check_reports_a_hook_that_runs_a_bridge_program_which_is_not_installed`

Manifest-oriented failure output line (expected): `STALE    cursor-bridge/loop-guard.py` (`tests/test_install_check.py::test_the_source_tree_is_checked_against_its_manifest_only`).

Representative bridge-install refusal line (expected, repeated across many tests): `bridge-install: <the Workspace>\bridge is not release 2026.10.18a as stamped (1 file(s): cursor-bridge/loop-guard.py (changed)); nothing was changed. Tell the maintainer.`

Same rollback and install_check_a4 failure names as step 1 (32 shared names plus the seven above).

### 5. `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge`

Exit code 0. Output: `windowless-check: 31 file(s) scanned, 0 FAIL, 0 NOTE`.

### 6. `git diff --stat` and `git diff -- bridge/cursor-bridge/loop-guard.py`

```
 bridge/cursor-bridge/loop-guard.py | 15 +++++++++------
 1 file changed, 9 insertions(+), 6 deletions(-)
```

```diff
diff --git a/bridge/cursor-bridge/loop-guard.py b/bridge/cursor-bridge/loop-guard.py
index af9206f..edc1264 100644
--- a/bridge/cursor-bridge/loop-guard.py
+++ b/bridge/cursor-bridge/loop-guard.py
@@ -200,18 +200,21 @@ def cron_field(field, value):
     return False
 
 
-def cron_next(expr, now):
-    """The next fire time (local wall clock, as a unix time) of a 5-field cron expression, within
-    eight days; None when the expression does not parse. Claude Code's session crons are local time."""
+def cron_next(expr, now, tz=None):
+    """The next fire time of a 5-field cron expression within eight days, as a unix time; None when
+    the expression does not parse. Walks instants one minute apart, each read as the wall time of
+    tz, and returns the matching instant. tz is the zone (None for the computer's local zone, the
+    zone Claude Code's session crons are written in)."""
     fields = (expr or "").split()
     if len(fields) != 5:
         return None
-    t = datetime.fromtimestamp(now).replace(second=0, microsecond=0) + timedelta(minutes=1)
+    instant = int(now // 60) * 60 + 60
     for _ in range(8 * 24 * 60):
+        t = datetime.fromtimestamp(instant, tz)
         if cron_field(fields[0], t.minute) and cron_field(fields[1], t.hour) and cron_field(fields[2], t.day) \
                 and cron_field(fields[3], t.month) and cron_field(fields[4], t.weekday() + 1 if t.weekday() < 6 else 0):
-            return t.timestamp()
-        t += timedelta(minutes=1)
+            return instant
+        instant += 60
     return None
```

## Assumed, not verified

Assumed, not verified: none.
