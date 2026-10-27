# TASK-031 round 10 report

## Files changed

- `bridge/cursor-bridge/mutation-run.py`
- `tests/test_mutation_run.py` (one new test)
- `handoff/TASK-031-r10-report.md`

## What I did

Added `_refuse_if_copy_root_shadows_iniconfig`, which lists the copy-root directory with `os.listdir` and raises the brief's fixed `Refuse` when any entry name is `iniconfig` or starts with `iniconfig.`, using case-insensitive name comparison on Windows. The helper runs at the start of the `.ini` and `.cfg` branches of `_pytest_config_dict_from_file`, before `import iniconfig`. I added `test_task031_r10_iniconfig_shadow_case_insensitive_refused` for a root `IniConfig.py` on Windows (skipped elsewhere). I ran the full supervisor and builder mutation-run test modules, the other verification commands, and the two by-hand mutants from Requirement 5.

## How this addresses the named cause

The program no longer imports the installed `iniconfig` while the gate's pytest would import a project top-level shadow module; it refuses first with exit 2 and no cache line.

## Behaviour unchanged for other cases

A project with a root `tox.ini` and no top-level `iniconfig` entry still goes through configuration resolution and mutants as before. A `.toml`-only project with a top-level `iniconfig.py` still never hits this check (the `.toml` branch is unchanged), so behaviour is as before.

## By-hand mutants (Requirement 5)

1. **Removed the shadow check entirely.** Both parametrized cases of `test_task031_r10_a_top_level_iniconfig_in_the_project_is_refused` failed at `tests/test_mutation_run_supervisor.py:1004` with `assert "would shadow pytest's iniconfig" in ...` because the run ended with `mutation-run: resolution check failed (pytest exit 1)` instead of the refusal.
2. **Matched only the file name `iniconfig.py`.** `test_task031_r10_a_top_level_iniconfig_in_the_project_is_refused[iniconfig/__init__.py]` failed at `tests/test_mutation_run_supervisor.py:1004` with the same assertion message pattern as mutant 1.

After both mutants, `bridge/cursor-bridge/mutation-run.py` was restored to the fix; `git diff -- bridge/cursor-bridge/mutation-run.py` shows only the helper and the two call sites.

## Verification output

### `python -m pytest tests/test_mutation_run_supervisor.py tests/test_mutation_run.py -q -p no:cacheprovider -rA`

Summary line:

```
140 passed, 1 skipped in 490.36s (0:08:10)
```

Round 10 supervisor cases (`-rA`):

```
PASSED tests/test_mutation_run_supervisor.py::test_task031_r10_a_top_level_iniconfig_in_the_project_is_refused[iniconfig.py]
PASSED tests/test_mutation_run_supervisor.py::test_task031_r10_a_top_level_iniconfig_in_the_project_is_refused[iniconfig/__init__.py]
```

Not-importable tests (`-rA`):

```
PASSED tests/test_mutation_run_supervisor.py::test_task031_r9_iniconfig_not_importable_while_reading_setup_cfg_is_refused
PASSED tests/test_mutation_run.py::test_task031_r9_iniconfig_not_importable_refused
```

Builder Round 10 test (`-rA`):

```
PASSED tests/test_mutation_run.py::test_task031_r10_iniconfig_shadow_case_insensitive_refused
```

Skip:

```
SKIPPED [1] tests\test_mutation_run.py:968: this account cannot create a symbolic link here ([WinError 1314] A required privilege is not held by the client: '<temporary folder>\\real_scratch' -> '<temporary folder>\\link_scratch')
```

Exit code: 0.

### `python tools/dump-cli.py --check`

Exit code: 0 (no stdout).

### `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge/mutation-run.py`

```
windowless-check: 1 file(s) scanned, 0 FAIL, 0 NOTE
```

Exit code: 0.

### `python -c "d=open('bridge/cursor-bridge/mutation-run.py','rb').read(); print(all(b < 128 for b in d))"`

```
True
```

### `git status --porcelain`

```
 M bridge/cursor-bridge/mutation-run.py
 M tests/test_mutation_run.py
?? handoff/TASK-031-r10-report.md
```

### `git diff --quiet -- tests/test_mutation_run_supervisor.py`

Exit code: 0.

## Assumed, not verified

- The folder passed as `os.path.dirname(filepath)` is always the copy root for every call to `_pytest_config_dict_from_file`; this follows from `copy_pytest_config_file` being the only caller and joining each candidate name under `copy_root`.
- Matching entry names `iniconfig` and `iniconfig.*` covers every top-level name Python 3.12 would import as `iniconfig` on Ubuntu and Windows for normal layouts (module file, package directory, bytecode, extension modules); the brief accepts over-refusal such as `iniconfig.txt`.
- On Windows without `PYTHONCASEOK`, a file named `IniConfig.py` may or may not be importable as `iniconfig` depending on import machinery and filesystem case sensitivity; the brief requires refusing it on `nt` anyway, and the builder test covers that path.
- Extension-module shadow names such as `iniconfig.pyd` or `iniconfig.cpython-312-x86_64-linux-gnu.so` are refused by the `iniconfig.*` rule but were not given a dedicated builder test on this machine (the optional test chose the Windows case variant).
- A project could still change what the gate's pytest imports via `.pth` files, `conftest.py`, `sitecustomize`, or `-p` options in configuration; those remain out of scope and were not fixed.
- A `iniconfig/` package directory is refused because the directory entry name is exactly `iniconfig`, not because `__init__.py` alone is matched.
