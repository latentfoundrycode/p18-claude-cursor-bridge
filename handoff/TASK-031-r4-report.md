# TASK-031 round 4 report

## Files changed

- `bridge/cursor-bridge/mutation-run.py`
- `tests/test_mutation_run.py`

## Summary

Round 4 replaced terminal parsing with a pytest outcomes plugin, hardened paths, archive extraction, cache and scratch checks, copy-based cache keys, checkpoint handling, and bounded process teardown; added unit tests for archive refusal and pipe hangs plus cache assertions on rerun tests.

## Items

### B1 — kill from plugin JSON, not terminal summary

**Cause:** `SUMMARY_RX` missed quiet, coloured, and long-duration pytest summaries, so kills became uncached `error (no pytest summary)`.

**Where:** `_mutation_outcomes` plugin, `run_mutant_tests`, `classify_outcome`, `read_pytest_results`; plugins live under `mutation-run-<id>/` with `MUTATION_PYTEST_RESULTS`.

**Tests:** `test_task031_r4_b1_a_kill_is_read_from_the_outcomes_not_the_terminal_text`; rerun cache assertions in `test_r041_done_c_*` (except expect_fail change) and `test_r041_all_reruns`, `test_r041_parent_conftest_change_reruns`.

### B2 — checkpoint allows new test ids in existing files

**Cause:** `validate_checkpoint` refused any `new_tests` file present at the commit, including `path::name` ids.

**Where:** `validate_checkpoint` applies the file-at-commit rule only when `::` is absent.

**Tests:** `test_task031_r4_b2_a_new_test_in_an_existing_file_is_checked_at_the_checkpoint`.

### B3 — checkpoint judges each test in a listed file

**Cause:** A whole-file listing was summarised as one outcome instead of per node id.

**Where:** Checkpoint loop prints each plugin-reported node id with `passing on old code`, `failing`, or `not run`.

**Tests:** `test_task031_r4_b3_each_listed_test_is_judged_alone_at_the_checkpoint`.

### B4 — cache key from copy bytes before mutants

**Cause:** Keys were computed from the Workspace during the mutant loop; `tox.ini` was omitted.

**Where:** `mutant_keys` from `compute_key(copy_root, ...)` after `copy_tracked`; `key_file_set` includes `tox.ini`.

**Tests:** `test_task031_r4_b4_a_kill_is_keyed_by_the_bytes_that_ran`.

### B5 — archive member path validation

**Cause:** `archive_checkpoint` joined tar names without traversal or type checks.

**Where:** `extract_archive_tar`; used from `archive_checkpoint`.

**Tests:** `test_r041_extract_archive_tar_well_formed`, `test_r041_extract_archive_tar_refuses_bad_member`, `test_r041_extract_archive_tar_refuses_non_file`.

### B6 — expected survive kill not in killed count

**Cause:** Killed `expect: survive` mutants incremented `counts["killed"]`.

**Where:** Main loop and cached-kill branch skip `killed` for survive mutants.

**Tests:** `test_task031_r4_b6_an_expected_survivor_killed_is_not_counted_killed`.

### B7 — malformed fields exit 2 before copy

**Cause:** Wrong types and invalid `expect_fail` ids raised internal errors or ran.

**Where:** `load_mutants` type checks and `expect_fail` validation.

**Tests:** `test_task031_r4_b7_a_malformed_mutant_is_refused_with_2`.

### B8 — ignore pytest config above the copy

**Cause:** Pytest searched parent directories from the scratch copy under the home directory.

**Where:** `pytest_config_argv` passes empty `-c` and `--rootdir` when the copy has no config file.

**Tests:** `test_task031_r4_b8_a_pytest_configuration_above_the_copy_is_not_read`.

### S1 — case-insensitive scratch containment

**Cause:** Scratch vs Workspace used case-sensitive string prefixes.

**Where:** `paths_overlap_workspace`, `validate_scratch`, `path_under_or_equal` for untracked.

**Tests:** `test_task031_r4_s1_a_scratch_folder_inside_the_workspace_in_another_case_is_refused`.

### S2 — cache file link refusal

**Cause:** The cache file was not checked for links or extra hard links before read/append.

**Where:** `validate_cache_file`.

**Tests:** `test_task031_r4_s2_a_cache_file_that_is_a_link_is_refused`.

### S3 — refuse `.`, `.git`, and `.` path components

**Cause:** `path_bad` and untracked validation allowed `.` and `.git`.

**Where:** `path_bad`.

**Tests:** `test_task031_r4_s3_an_untracked_entry_naming_the_workspace_or_git_is_refused`.

### Bound kill / pipe hang (item 12)

**Cause:** `taskkill` and post-kill `communicate()` could block without timeout when a grandchild held pipes.

**Where:** `kill_tree` timeout; `run_process` closes pipes after second `TimeoutExpired`.

**Tests:** `test_r041_grandchild_holding_pipes_times_out`.

### Checkpoint collect refusal (supports existing tests)

**Cause:** Src-layout checkpoint runs that cannot import a module present at the commit should exit 2; imports of modules absent at the commit should list `not run`.

**Where:** `checkpoint_collect_refused`, `module_file_at_commit` in resolution check.

**Tests:** `test_r041_editable_src_only_refused`, `test_task031_req8_a_module_the_increment_adds_does_not_refuse_the_checkpoint_run`, `test_r041_checkpoint_not_run`.

## Verification output

```
$ python -m pytest tests/test_mutation_run_supervisor.py tests/test_mutation_run.py -q -p no:cacheprovider -rA --durations=0
87 passed, 1 skipped in 259.82s (0:04:19)
```

```
$ python tools/dump-cli.py --check
(exit 0, no output)
```

```
$ python -m pytest tests/test_dump_cli.py tests/test_tests_windowless.py tests/test_bridge_run_driver.py -q -p no:cacheprovider
176 passed in 97.41s (0:01:37)
```

```
$ python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge/mutation-run.py
windowless-check: 1 file(s) scanned, 0 FAIL, 0 NOTE
```

```
$ python -c "d=open('bridge/cursor-bridge/mutation-run.py','rb').read(); print(all(b < 128 for b in d))"
True
```

```
$ git status --porcelain
 M bridge/cursor-bridge/mutation-run.py
 M tests/test_mutation_run.py
```

```
$ git diff --quiet -- tests/test_mutation_run_supervisor.py
(exit 0)
```

## Assumed, not verified

- The outcomes plugin records every test outcome via `pytest_runtest_logreport` and `pytest_sessionfinish` under pytest-xdist, with `-p no:` disables, and with arbitrary project plugins loaded · hooks may not run in the same order or on the same workers · run a matrix with xdist and representative third-party plugins.
- Passing `-c` with an empty `pytest.ini` outside the copy stops upward config search but still allows `pyproject.toml` discovery unless pytest treats `-c` as the sole config source · read pytest 8 config-init behaviour and add a fixture that places only a parent `pyproject.toml` · confirm mutant runs ignore it.
