# TASK-031 round 6 report

## Files changed

- `bridge/cursor-bridge/mutation-run.py`
- `tests/test_mutation_run.py`

## Summary

Round 6 closes the gate’s blocking findings by hardening scratch and untracked path validation, aligning pytest configuration with pytest 9.1.1 at the copy root, fixing checkpoint id matching and collection-error classification, giving each pytest run its own outcomes file, stopping the mutant loop when pytest survives a kill, and strengthening the pipe-holder builder tests.

## Items

**B-1.** Cause: `paths_overlap_workspace` missed Windows extended, device, and UNC `--scratch` spellings and could miss same-inode overlap. Fix: `_scratch_arg_forbidden` refuses `\\?\`, `\\.\`, and any `\\` UNC prefix before creating folders; `_scratch_overlaps_workspace_identity` walks existing ancestors with `samefile`/device+inode plus the existing realpath check in `validate_scratch`. Tests: `test_task031_r6_b1_a_scratch_folder_inside_the_workspace_in_another_path_form_is_refused`.

**B-2.** Cause: `path_bad` and `validate_untracked` did not catch alternate `.git` names or risky path components. Fix: `path_bad` rejects trailing dots/spaces and colons in components; `_untracked_reaches_git` refuses by identity to the workspace `.git` (with `OSError` turned into `Refuse`, not internal error) in `validate_untracked`. Tests: `test_task031_r6_b2_an_untracked_entry_reaching_git_by_another_name_is_refused`.

**B-3.** Cause: `copy_has_pytest_config` treated any root ini/toml/cfg as “has config” and skipped `-c`, and ignored `.pytest.ini`/`pytest.toml`. Fix: `copy_pytest_config_file` and `_pytest_config_dict_from_file` mirror pytest’s root discovery; `pytest_config_argv` always passes `-c` (found file or `pytest-empty.ini`) and `--rootdir`; `key_file_set` lists the same root config names. Tests: `test_task031_r6_b3_a_root_file_with_no_pytest_section_keeps_the_configuration_above_unread`, `test_task031_r6_b3_the_copys_own_pytest_configuration_is_read`.

**A-1.** Cause: checkpoint id items matched only an exact node id. Fix: `checkpoint_records_for_item` matches the item or ids starting with `item[` or `item::`, printing each match separately in the checkpoint loop. Tests: `test_task031_r6_a1_a_parametrized_or_class_id_is_judged_by_its_tests_at_the_checkpoint`.

**A-3.** Cause: `classify_outcome` ignored `collect_errors`. Fix: non-empty `collect_errors` yields `error` / `collection error` before kill logic. Test: `test_task031_r6_a3_a_collection_error_beside_a_kill_is_an_error`.

**Item 6.** Cause: one shared `pytest-outcomes.json` and no fatal exit when pytest outlived `kill_tree`. Fix: per-run paths `pytest-outcomes-<mutant id>.json` and `pytest-outcomes-chk-<n>.json`; `run_process_still_alive_after_timeout` after timeout; mutant loop breaks and stderr prints the bound when pytest remains alive. Shown in code: distinct `MUTATION_PYTEST_RESULTS` per run. Test: `test_r041_pytest_survives_kill_stops_run`.

**Item 7.** Cause: fixtures used pytest capture fds, not `run_process` pipes. Fix: `addopts = -s` in fixture `pytest.ini`, real `stdout`/`stderr` in holders, `harness_slack=120`; outside-tree test asserts elapsed ≥ 30 s and no `tree/.env` after the run while the holder still lives (files under `tree/` removed in `finally` before the pinned directory); grandchild holder is inside the killed tree so taskkill ends it in ~7 s—the test asserts elapsed ≥ 5 s (mutant bound) with `-s` real pipes. Tests: `test_r041_pipe_holder_outside_tree_cwd_in_copy_times_out`, `test_r041_grandchild_holding_pipes_times_out`.

## Pytest 9.1.1 configuration discovery (from `_pytest/config/findpaths.py`)

At a directory, `locate_config` tries basenames in order: `pytest.toml`, `.pytest.toml`, `pytest.ini`, `.pytest.ini`, `pyproject.toml`, `tox.ini`, `setup.cfg`. For each existing file, `load_config_dict_from_file` applies: `.ini` with `[pytest]` (or empty dict for `pytest.ini`/`.pytest.ini` even without a section); `.cfg` only with `[tool:pytest]`; `.toml` with `[pytest]` for `pytest.toml`/`.pytest.toml` (empty dict if the table is missing), or `pyproject.toml` with `[tool.pytest]` or `[tool.pytest.ini_options]`; `tox.ini` only with `[pytest]`. The first file that yields a config dict wins; a `pyproject.toml` with no pytest tables is not selected during the walk (only remembered if nothing else matches). This round selects a file only when that function would return non-`None`, except the always-config toml/ini names above, matching the brief’s “no pytest section” vs “owns configuration” split.

## Verification

```
$ python -m pytest tests/test_mutation_run_supervisor.py tests/test_mutation_run.py -q -p no:cacheprovider -rA --durations=0
...
PASSED tests/test_mutation_run_supervisor.py::test_task031_r6_b1_a_scratch_folder_inside_the_workspace_in_another_path_form_is_refused[extended]
PASSED tests/test_mutation_run_supervisor.py::test_task031_r6_b1_a_scratch_folder_inside_the_workspace_in_another_path_form_is_refused[admin share]
PASSED tests/test_mutation_run_supervisor.py::test_task031_r6_b2_an_untracked_entry_reaching_git_by_another_name_is_refused[.git.]
PASSED tests/test_mutation_run_supervisor.py::test_task031_r6_b2_an_untracked_entry_reaching_git_by_another_name_is_refused[.git ]
PASSED tests/test_mutation_run_supervisor.py::test_task031_r6_b2_an_untracked_entry_reaching_git_by_another_name_is_refused[.git::$INDEX_ALLOCATION]
PASSED tests/test_mutation_run_supervisor.py::test_task031_r6_b2_an_untracked_entry_reaching_git_by_another_name_is_refused[short name]
PASSED tests/test_mutation_run_supervisor.py::test_task031_r6_b3_a_root_file_with_no_pytest_section_keeps_the_configuration_above_unread[pyproject.toml]
PASSED tests/test_mutation_run_supervisor.py::test_task031_r6_b3_a_root_file_with_no_pytest_section_keeps_the_configuration_above_unread[setup.cfg]
PASSED tests/test_mutation_run_supervisor.py::test_task031_r6_b3_a_root_file_with_no_pytest_section_keeps_the_configuration_above_unread[tox.ini]
PASSED tests/test_mutation_run_supervisor.py::test_task031_r6_b3_the_copys_own_pytest_configuration_is_read[.pytest.ini]
PASSED tests/test_mutation_run_supervisor.py::test_task031_r6_b3_the_copys_own_pytest_configuration_is_read[pytest.toml]
PASSED tests/test_mutation_run_supervisor.py::test_task031_r6_b3_the_copys_own_pytest_configuration_is_read[pyproject.toml]
PASSED tests/test_mutation_run_supervisor.py::test_task031_r6_a1_a_parametrized_or_class_id_is_judged_by_its_tests_at_the_checkpoint[tests/test_calc.py::test_p]
PASSED tests/test_mutation_run_supervisor.py::test_task031_r6_a1_a_parametrized_or_class_id_is_judged_by_its_tests_at_the_checkpoint[tests/test_calc.py::TestNew]
PASSED tests/test_mutation_run_supervisor.py::test_task031_r6_a3_a_collection_error_beside_a_kill_is_an_error
SKIPPED [1] tests/test_mutation_run.py:968: this account cannot create a symbolic link here ...
107 passed, 1 skipped in 416.49s (0:06:56)
```

Item 6 and 7 test durations (from the same full run): `test_r041_pytest_survives_kill_stops_run` 64.81s call; `test_r041_pipe_holder_outside_tree_cwd_in_copy_times_out` 37.32s call; `test_r041_grandchild_holding_pipes_times_out` 7.01s call.

```
$ python tools/dump-cli.py --check
(exit 0, no output)

$ python -m pytest tests/test_dump_cli.py tests/test_tests_windowless.py tests/test_bridge_run_driver.py -q -p no:cacheprovider
176 passed in 100.24s (0:01:40)

$ python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge/mutation-run.py
windowless-check: 1 file(s) scanned, 0 FAIL, 0 NOTE

$ python -c "d=open('bridge/cursor-bridge/mutation-run.py','rb').read(); print(all(b < 128 for b in d))"
True

$ git status --porcelain
 M bridge/cursor-bridge/mutation-run.py
 M tests/test_mutation_run.py

$ git diff --quiet -- tests/test_mutation_run_supervisor.py; echo $?
0
```

## Assumed, not verified

- Pytest 9.1.1 `findpaths.py` order and section rules as read from the installed package on this machine; passing `-c` to `pytest.toml` or `pyproject.toml` is treated like pytest’s own loader would—confirmed by passing supervisor B-3 tests, not by a separate pytest source audit on Linux CI.
- POSIX: no `\\?\`, administrative-share, or UNC `--scratch` forms; inode-based scratch overlap and `.git` alternate names on non-Windows volumes—only Windows supervisor cases were run here.
- POSIX: process-group kill leaving pytest alive after timeout (item 6)—exercised via no-op `kill_tree` in-process on Windows only; Linux `start_new_session` behaviour not re-run in this session.
- Grandchild pipe-holder on POSIX: whether the holder survives taskkill-equivalent long enough to require a 30 s hold—on this Windows run taskkill ended the in-tree grandchild in about 7 s.
