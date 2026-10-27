# TASK-031 round 11 report

## Files changed

- `bridge/cursor-bridge/mutation-run.py` (added `importlib.machinery` and `importlib.util`; new `_refuse_if_copy_root_shadows_importable_module`; call from `copy_pytest_config_file` before the configuration candidate loop)
- `tests/test_mutation_run.py` (added `test_task031_r11_extension_suffix_shadow_refused`)
- `docs/BUILDER_NOTES.md` (one dated pitfall line)
- `handoff/TASK-031-r11-report.md` (this file)

## What I did

Before any pytest configuration candidate is read, `copy_pytest_config_file` now lists top-level copy-root entry names only, derives importable module names from `importlib.machinery.all_suffixes()` and the regular-package `__init__` rule, and refuses when a derived name is a standard-library or built-in module or is resolved by `importlib.util.find_spec` in the program's own environment with a non-null `origin` that is not under the scratch copy root or the Workspace working directory (so fixture package names and editable-install paths on `PYTHONPATH` are not mistaken for external modules). The fixed Requirement 1 message names the module; `iniconfig` still uses `_INICONFIG_SHADOW_REFUSE`. A builder test covers a long extension suffix on `tomllib`. Three by-hand mutants were applied and reverted; the program was restored and `git diff` on `mutation-run.py` shows only this increment.

## How this addresses the named cause

Pytest can import project top-level modules such as `tomllib`, `pluggy`, or `_pytest` before the installed or stdlib versions and therefore choose a different configuration file than the program read with its own imports; refusing those projects before configuration lookup prevents caching mutant results against a gate configuration pytest never used.

## Project behaviour now

- A project with `demo/__init__.py`, `tests/`, and a root `tox.ini` still runs mutants as before (exit 0 when killed; `demo` is not treated as shadowing an external module).
- A `.toml`-only project with a top-level `iniconfig.py` is refused with round 10's message (`mutation-run: a top-level iniconfig in the project would shadow pytest's iniconfig`), exit 2, no cache line, even when no `.ini`/`.cfg` candidate is read first.
- A project with only a top-level `__main__.py` and no other shadowing entry still runs as before: `__main__` is not in `sys.stdlib_module_names` on this Python 3.12 build, `find_spec("__main__")` raises `ValueError` which is treated as not found, and the run does not crash with an internal error.

## By-hand mutants (Requirement 7)

1. **Removed the new check** (deleted the call in `copy_pytest_config_file`): `test_task031_r11_a_top_level_module_shadowing_an_installed_one_is_refused` all four parametrizations failed; pytest printed `FAILED tests/test_mutation_run_supervisor.py::test_task031_r11_a_top_level_module_shadowing_an_installed_one_is_refused[...]` and summary `4 failed, 3 passed, 141 deselected in 12.63s`.
2. **Only files yield module names** (dropped the regular-package branch): `pluggy/__init__.py` and `_pytest/__init__.py` cases failed; pytest printed `FAILED ...[pluggy/__init__.py-pluggy-config1]` and `FAILED ...[_pytest/__init__.py-_pytest-config2]`; summary `2 failed, 5 passed, 141 deselected in 11.91s`.
3. **Any folder is a package** (no `__init__` check): no test in `-k r11` failed; summary `7 passed, 141 deselected in 15.45s` (listed under Assumed, not verified below).

## Verification

### 1. `python -m pytest tests/test_mutation_run_supervisor.py tests/test_mutation_run.py -q -p no:cacheprovider -rA`

```
148 passed, 1 skipped in 498.92s (0:08:18)
```

Round 11 refusal cases (`-rA`):

```
PASSED tests/test_mutation_run_supervisor.py::test_task031_r11_a_top_level_module_shadowing_an_installed_one_is_refused[tomllib.py-tomllib-config0]
PASSED tests/test_mutation_run_supervisor.py::test_task031_r11_a_top_level_module_shadowing_an_installed_one_is_refused[pluggy/__init__.py-pluggy-config1]
PASSED tests/test_mutation_run_supervisor.py::test_task031_r11_a_top_level_module_shadowing_an_installed_one_is_refused[_pytest/__init__.py-_pytest-config2]
PASSED tests/test_mutation_run_supervisor.py::test_task031_r11_a_top_level_module_shadowing_an_installed_one_is_refused[json.py-json-config3]
```

Round 11 run cases (`-rA`):

```
PASSED tests/test_mutation_run_supervisor.py::test_task031_r11_a_top_level_name_shadowing_nothing_runs_its_mutant[r11_own_helper.py]
PASSED tests/test_mutation_run_supervisor.py::test_task031_r11_a_top_level_name_shadowing_nothing_runs_its_mutant[r11_notes/readme.txt]
PASSED tests/test_mutation_run_supervisor.py::test_task031_r11_a_top_level_name_shadowing_nothing_runs_its_mutant[tests_data/tomllib.json]
```

Round 10 cases (`-rA`):

```
PASSED tests/test_mutation_run_supervisor.py::test_task031_r10_a_top_level_iniconfig_in_the_project_is_refused[iniconfig.py]
PASSED tests/test_mutation_run_supervisor.py::test_task031_r10_a_top_level_iniconfig_in_the_project_is_refused[iniconfig/__init__.py]
PASSED tests/test_mutation_run.py::test_task031_r10_iniconfig_shadow_case_insensitive_refused
```

Builder extension test (`-rA`):

```
PASSED tests/test_mutation_run.py::test_task031_r11_extension_suffix_shadow_refused
```

Skip (from full run):

```
SKIPPED [1] tests\test_mutation_run.py:968: this account cannot create a symbolic link here ([WinError 1314] A required privilege is not held by the client: '<temporary folder>\\real_scratch' -> '<temporary folder>\\link_scratch')
```

### 2. `python tools/dump-cli.py --check`

Exit code 0 (no stdout).

### 3. `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge/mutation-run.py`

```
windowless-check: 1 file(s) scanned, 0 FAIL, 0 NOTE
```

### 4. ASCII check

```
True
```

### 5. `git status --porcelain` and `git diff --quiet -- tests/test_mutation_run_supervisor.py`

```
 M bridge/cursor-bridge/mutation-run.py
 M docs/BUILDER_NOTES.md
 M tests/test_mutation_run.py
?? handoff/TASK-031-r11-report.md
```

`git diff --quiet -- tests/test_mutation_run_supervisor.py` exit code: 0

## Assumed, not verified

- `importlib.util.find_spec` for a bare top-level name does not import or execute project code; the program's `sys.path` does not include the scratch copy root or the Workspace folder when `mutation-run.py` is started as a script from the fixture Workspace (only the bridge folder, caller `PYTHONPATH`, stdlib, and site-packages).
- Deriving names from `importlib.machinery.all_suffixes()` plus the `__init__` rule matches every top-level entry Python 3.12's path finder would import from the copy root on Windows and Ubuntu; only the Windows builder extension test exercises a long extension suffix here.
- `__main__` is not in `sys.stdlib_module_names` on this Python 3.12.10 build; a lone top-level `__main__.py` therefore does not trigger refusal via the stdlib set (confirmed with `python -c "import sys; print('__main__' in sys.stdlib_module_names)"` → `False`).
- A namespace `find_spec` result with `origin is None` in the program environment is never what pytest would use instead of a project regular package at the copy root for the names this check targets.
- Mutant 3 (treat every top-level folder as a package): no `-k r11` test failed on this machine; `r11_notes` is not importable here, so the brief's optional failure mode was not observed.
- Other ways a project could change what the gate's pytest imports (not fixed this round): `.pth` files on `PYTHONPATH`, root `conftest.py`, `sitecustomize`, or `-p` in configuration would still alter pytest's import graph without being caught by this name-only listing.
