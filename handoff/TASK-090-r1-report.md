# TASK-090 round 1 report

## Files changed

- `bridge/cursor-bridge/bridge-run.py`
- `bridge/cursor-bridge/MANIFEST.json` (via `python tools/make-manifest.py`)
- `docs/cli-reference.json` (via `python tools/dump-cli.py`)
- `docs/CLI_REFERENCE.md` (via `python tools/dump-cli.py`)
- `handoff/TASK-090-r1-report.md`

## One-paragraph summary

TASK-090 applied four small repairs to `bridge-run.py`: the non-watch limit branch now removes the pid file after `write_log` and before `killer()` (matching the watch branch) while keeping the post-try removal; driver and test child processes receive `PYTHONIOENCODING=utf-8` only when the merged environment lacks that name; refused `--kind test` launches whose command `resolve_driver_program` would accept emit an extra stderr line naming `--kind driver`; and the module docstring plus `usage()` document stripped runs' isolated APPDATA, LOCALAPPDATA and home folder and how an unstripped driver run is chosen under a recorded decision. CLI reference and MANIFEST were regenerated from the program. All 27 tests in `tests/test_improve_launcher_small.py`, the listed regression files, and `test_r079_the_launcher_tests_write_no_row_into_the_checkout` passed; no other files were edited.

## Requirements (line references in final `bridge-run.py`)

1. **Pid file at limit:** lines 3804-3805 (`remove_pid_file` before `killer()` in the non-watch `TimeoutExpired` handler); line 3815 (retained removal after the try block). Watch branch unchanged at lines 3734-3734 area.
2. **Child encoding:** lines 3597-3598 (`if kind in ("driver", "test") and "PYTHONIOENCODING" not in env`).
3. **Refusal hint:** lines 3401-3402 (`kind == "test"` and `resolve_driver_program` non-None).
4. **Help text:** module docstring lines 103-106; `usage()` lines 162-166.
5. **Nothing else:** `merge_ids` untouched; no new `BRIDGE_` names; ASCII verified.

## Mutation code points (M1-M7)

- **M1:** Function `main`, lines 3804-3807. Deleting the `remove_pid_file` at 3805 before `killer()`. Caught by `test_r112_every_limit_branch_removes_the_pid_file_before_it_ends_the_tree` and `test_r112_a_run_ended_at_its_limit_leaves_no_pid_file`.
- **M2:** Lines 3597-3598. Widening to all kinds (dropping `kind in ("driver", "test")`). Caught by `test_r112_a_builder_s_and_a_reviewer_s_environment_unchanged`.
- **M3:** Line 3597, removing `not in env` or always assigning. Caught by `test_r112_a_driver_s_child_keeps_a_caller_value_where_set` and `test_r112_a_test_s_child_keeps_a_caller_value_where_set`.
- **M4:** Applying the default only inside the `stripped_env` branch (lines 3585-3598). Caught by `test_r112_a_driver_s_child_gets_utf_8_where_the_caller_set_none[False]` and the test-kind parametrized cases with `strip=False`.
- **M5:** Removing the `kind == "test"` guard at line 3401. Caught by `test_r112_a_refused_test_launch_of_tools_y_names_no_kind` (no hint for non-driver commands).
- **M6:** Replacing `resolve_driver_program` with a check that ignores `~/` mutation path. Caught by `test_r112_a_test_launch_of_the_installed_mutation_engine_names_the_driver_kind` (second words tuple).
- **M7:** Removing help words from the module docstring only (lines 103-106). Caught by `test_r112_the_docstring_names_them_too`; `test_r112_the_usage_text_names_the_owner_s_folders_a_stripped_run_does_not_see` would not catch docstring-only removal.

## Changed expectations

no changed expectation

## Scratch test files

no scratch test file

## Commands and output (commit `0380a9bea4d102398d7b4dc5cef01e113130ba8f`, uncommitted changes as below)

### Step 1

```
git status --short
```

```
(empty)
```

### Step 2 (before edit)

```
python -m pytest -p no:cacheprovider -q tests/test_improve_launcher_small.py
```

```
12 failed, 15 passed in 65.59s (0:01:05)
```

Failing: `test_r112_a_run_ended_at_its_limit_leaves_no_pid_file[test]`, `[driver]`, `[builder]`, `test_r112_every_limit_branch_removes_the_pid_file_before_it_ends_the_tree`, `test_r112_a_driver_s_child_gets_utf_8_where_the_caller_set_none[False]`, `[True]`, `test_r112_a_test_s_child_gets_utf_8_where_the_caller_set_none[False]`, `[True]`, `test_r112_a_test_launch_of_a_supervisor_program_names_the_driver_kind`, `test_r112_a_test_launch_of_the_installed_mutation_engine_names_the_driver_kind`, `test_r112_the_usage_text_names_the_owner_s_folders_a_stripped_run_does_not_see`, `test_r112_the_docstring_names_them_too`.

### Step 3

```
python tools/dump-cli.py
python tools/dump-cli.py --check
```

```
(no stdout; exit 0)
```

### Step 4

```
python tools/make-manifest.py
```

```
make-manifest: version 2026.11.24a, 148 files hashed, VERSION + MANIFEST.json written
```

### Step 5

```
git status --short
```

```
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/bridge-run.py
 M docs/CLI_REFERENCE.md
 M docs/cli-reference.json
?? handoff/TASK-090-r1-report.md
```

(`bridge/cursor-bridge/VERSION` not listed; `git restore` not run.)

### Step 6 (after edit)

```
python -m pytest -p no:cacheprovider -q tests/test_improve_launcher_small.py
```

```
27 passed in 35.27s
```

### Step 7

```
python -m pytest -p no:cacheprovider -q tests/test_bridge_run.py tests/test_bridge_run_driver.py tests/test_program_launcher_forms.py
```

```
190 passed in 195.10s (0:03:15)
```

### Step 8

```
python -m pytest -p no:cacheprovider -q tests/test_release_s_launcher.py tests/test_bridge_run_slot.py tests/test_tests_windowless.py tests/test_bug029_agent_name.py
```

```
104 passed, 3 skipped in 135.59s (0:02:15)
```

### Step 9

```
python -c "open('bridge/cursor-bridge/bridge-run.py','rb').read().decode('ascii'); print('ascii ok')"
```

```
ascii ok
```

### Step 10

```
python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet
python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks
```

```
RESULT: SOURCES MATCH bridge 2026.11.24a ...
windowless-check: 41 file(s) scanned, 0 FAIL, 0 NOTE
```

### Step 11

```
python -m pytest -p no:cacheprovider -q "tests/test_program_review_rows.py::test_r079_the_launcher_tests_write_no_row_into_the_checkout"
```

```
1 passed in 2003.99s (0:33:23)
```

Checkout has a `run/` folder; test was not skipped.

### Step 12

```
git diff --stat HEAD
```

```
 bridge/cursor-bridge/MANIFEST.json |  4 ++--
 bridge/cursor-bridge/bridge-run.py | 14 ++++++++++++--
 docs/CLI_REFERENCE.md              |  5 ++++-
 docs/cli-reference.json            |  2 +-
 4 files changed, 19 insertions(+), 6 deletions(-)
```

### Step 13

```
git rev-parse HEAD
git status --short
```

```
0380a9bea4d102398d7b4dc5cef01e113130ba8f
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/bridge-run.py
 M docs/CLI_REFERENCE.md
 M docs/cli-reference.json
?? handoff/TASK-090-r1-report.md
```

Neither `bridge/cursor-bridge/VERSION` nor any `tests/test_task090_scratch_*` file is listed.

## Assumed, not verified

Assumed, not verified: none