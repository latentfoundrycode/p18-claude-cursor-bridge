# TASK-031 round 12 builder report

## Files changed

- `bridge/cursor-bridge/mutation-run.py`
- `docs/BUILDER_NOTES.md`

`tests/test_mutation_run.py` and `tests/test_mutation_run_supervisor.py` were not modified. The builder test `test_task031_r11_extension_suffix_shadow_refused` did not need changes because `tomllib` remains on the fixed list.

## What I did

I replaced round 11's environment-wide shadow probe in `_refuse_if_copy_root_shadows_importable_module` with membership in `_PYTEST_CONFIG_SHADOW_MODULES` (`pytest`, `_pytest`, `pluggy`, `py`, `iniconfig`, `tomllib`, `tomli`), using case-insensitive name matching on Windows and exact matching elsewhere, and removed the module-level `importlib.util` import that only served the deleted `find_spec` logic. I read pytest 9.1.1's `findpaths.py` and its `load_config_dict_from_file` / `determine_setup` path read-only, ran the full verification sequence and two by-hand mutants, and corrected the TASK-031-r11 note in `docs/BUILDER_NOTES.md`.

## How this addresses the named cause

The gate now refuses a copy-root top-level module only when its derived name is one of the seven modules pytest uses to locate and parse configuration, so `test/` packages and a project's own `demo` package on `PYTHONPATH` are no longer false positives from `find_spec`, stdlib sets, or working-directory origin filtering.

## Requirement 4: top-level modules on the configuration path

In `findpaths.py` itself: `iniconfig`, and `_pytest` (via `from _pytest.outcomes`, `from _pytest.pathlib`, and `from .exceptions` under the `_pytest` package). On the TOML branch inside `load_config_dict_from_file`, which `locate_config` and `determine_setup` call: `tomllib` on Python 3.11+ or `tomli` imported as `tomllib` on older versions. I did not see `pytest`, `pluggy`, or `py` imported on this path in `findpaths.py`; those names are on the brief's fixed list.

## By-hand mutants

1. **Removed `tomllib` from `_PYTEST_CONFIG_SHADOW_MODULES`.** Caught by `test_task031_r11_a_top_level_module_shadowing_an_installed_one_is_refused[tomllib.py-tomllib-config0]`. Pytest printed: `assert ('would shadow' in ('' + 'mutation-run: resolution check failed (pytest exit 1)\n'))`.
2. **Restored round 11's `find_spec` / stdlib / origin-exclusion branch (and module-level `importlib.util`).** Caught by `test_task031_r11_a_top_level_name_shadowing_nothing_runs_its_mutant[test/__init__.py]` with `assert 2 == 0` and stderr `mutation-run: a top-level module test in the project would shadow an installed or standard-library module`, and by `test_task031_r12_the_projects_own_package_installed_elsewhere_runs_its_mutant` with `assert 2 == 0` and stderr `mutation-run: a top-level module demo in the project would shadow an installed or standard-library module`.

After both mutants I restored the fix; `git diff -- bridge/cursor-bridge/mutation-run.py` shows only the round-12 change.

## Verification command output

### 1. `python -m pytest tests/test_mutation_run_supervisor.py tests/test_mutation_run.py -q -p no:cacheprovider -rA`

```
........................................................................ [ 47%]
..........................................................s............. [ 94%]
........                                                                 [100%]
=========================== short test summary info ===========================
PASSED tests/test_mutation_run_supervisor.py::test_task031_r11_a_top_level_module_shadowing_an_installed_one_is_refused[tomllib.py-tomllib-config0]
PASSED tests/test_mutation_run_supervisor.py::test_task031_r11_a_top_level_module_shadowing_an_installed_one_is_refused[pluggy/__init__.py-pluggy-config1]
PASSED tests/test_mutation_run_supervisor.py::test_task031_r11_a_top_level_module_shadowing_an_installed_one_is_refused[_pytest/__init__.py-_pytest-config2]
PASSED tests/test_mutation_run_supervisor.py::test_task031_r11_a_top_level_module_shadowing_an_installed_one_is_refused[pytest.py-pytest-config3]
PASSED tests/test_mutation_run_supervisor.py::test_task031_r11_a_top_level_name_shadowing_nothing_runs_its_mutant[test/__init__.py]
PASSED tests/test_mutation_run_supervisor.py::test_task031_r12_the_projects_own_package_installed_elsewhere_runs_its_mutant
PASSED tests/test_mutation_run.py::test_task031_r11_extension_suffix_shadow_refused
SKIPPED [1] tests\test_mutation_run.py:968: this account cannot create a symbolic link here ([WinError 1314] A required privilege is not held by the client: '<temporary folder>' -> '<temporary folder>')
151 passed, 1 skipped in 540.50s (0:09:00)
```

Exit code 0.

### 2. `python tools/dump-cli.py --check`

Exit code 0 (no output).

### 3. `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge/mutation-run.py`

```
windowless-check: 1 file(s) scanned, 0 FAIL, 0 NOTE
```

Exit code 0.

### 4. ASCII check

```
True
```

### 5. `git status --porcelain` and `git diff --quiet -- tests/test_mutation_run_supervisor.py`

```
 M bridge/cursor-bridge/mutation-run.py
 M docs/BUILDER_NOTES.md
```

`git diff --quiet -- tests/test_mutation_run_supervisor.py` exit code: 0.

## Assumed, not verified

- That the seven listed names are every top-level module pytest 9.1.1 imports to find and read its configuration end-to-end; `findpaths.py` and `load_config_dict_from_file` directly import only `iniconfig`, `_pytest`, `tomllib`/`tomli`, while `pytest`, `pluggy`, and `py` are on the list per the brief but were not seen on that path in the source I read; confirming the full set would require tracing every import during `determine_setup` and plugin load in a live pytest 9.1.1 process.
- That a project shadowing a module outside the list (for example a top-level `json.py`) cannot change which configuration file the gate's pytest picks; I did not run an experiment with a malicious `json.py` at the project root.
