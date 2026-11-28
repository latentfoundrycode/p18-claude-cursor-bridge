# TASK-090 round 3 report

## Files changed

- `bridge/cursor-bridge/bridge-run.py`
- `bridge/cursor-bridge/MANIFEST.json` (via `python tools/make-manifest.py`)
- `docs/cli-reference.json` (via `python tools/dump-cli.py`)
- `docs/CLI_REFERENCE.md` (via `python tools/dump-cli.py`)
- `handoff/TASK-090-r3-report.md`

## One-paragraph summary

TASK-090 round 3 updated only the module docstring and `usage()` in `bridge-run.py` so the help text matches what a stripped run's home folder and git config still reach: both texts now say the run keeps the owner's rights and that cursor-agent's login still leads to the owner's folders; the docstring names the `.cursor` link to `~/.cursor` and git reading the owner's `.gitconfig` through an include with the credential helper list reset; the wording about files under the re-pointed variables is corrected to "the owner's other files"; the usage line drops the misleading "otherwise" and states that every cursor-agent run and every `--strip` run get folders of their own. CLI reference and MANIFEST were regenerated. All 36 tests in `tests/test_improve_launcher_small.py`, the listed regression files, and `test_r079_the_launcher_tests_write_no_row_into_the_checkout` passed.

## Requirements (line references in final `bridge-run.py`)

1. **Pid file at limit (round 1):** lines 3813-3814 (`remove_pid_file` before `killer()` in the non-watch `TimeoutExpired` handler); line 3823 (retained removal after the try block).
2. **Child encoding (round 1):** lines 3605-3606 (`if kind in ("driver", "test") and "PYTHONIOENCODING" not in env`).
3. **Refusal hint (round 1, extended in round 2):** lines 3409-3410 (`kind == "test"`, `"--key-file" not in flags`, and `resolve_driver_program` non-None).
4. **Help text (round 1, replaced by rounds 2-3):** superseded by R1 rounds 2-3 below.
5. **Nothing else (round 1):** `merge_ids` untouched; no new `BRIDGE_` names; ASCII verified.
R1. **Docstring names remaining owner reach:** module docstring lines 103-114 (`.cursor` link, `.gitconfig` include, "owner's other files").
R2. **Usage essentials:** `usage()` lines 173-174 (owner's rights, login, stripped cursor-agent and `--strip` runs, no "otherwise").
R3. **Report exact:** this file; test ids from pytest output below; M5 as round 2 brief words it.

## Mutation code points (M1-M9)

- **M1:** Function `main`, lines 3813-3814. Deleting the `remove_pid_file` at 3813 before `killer()`. Caught by `test_r112_every_limit_branch_removes_the_pid_file_before_it_ends_the_tree` and `test_r112_a_run_ended_at_its_limit_leaves_no_pid_file[test]`, `test_r112_a_run_ended_at_its_limit_leaves_no_pid_file[driver]`, `test_r112_a_run_ended_at_its_limit_leaves_no_pid_file[builder]`.
- **M2:** Lines 3605-3606. Widening to all kinds (dropping `kind in ("driver", "test")`). Caught by `test_r112_a_builder_s_and_a_reviewer_s_environment_unchanged[None-builder]`, `test_r112_a_builder_s_and_a_reviewer_s_environment_unchanged[cp1252-builder]`, `test_r112_a_builder_s_and_a_reviewer_s_environment_unchanged[None-review]`, `test_r112_a_builder_s_and_a_reviewer_s_environment_unchanged[cp1252-review]`.
- **M3:** Line 3605, removing `not in env` or always assigning. Caught by `test_r112_a_driver_s_child_keeps_the_caller_s_value[False]`, `test_r112_a_driver_s_child_keeps_the_caller_s_value[True]`, `test_r112_a_test_s_child_keeps_the_caller_s_value[False]`, `test_r112_a_test_s_child_keeps_the_caller_s_value[True]`.
- **M4:** Applying the default only inside the `stripped_env` branch (lines 3593-3606). Caught by `test_r112_a_driver_s_child_gets_utf_8_where_the_caller_set_none[False]`, `test_r112_a_driver_s_child_gets_utf_8_where_the_caller_set_none[True]`, `test_r112_a_test_s_child_gets_utf_8_where_the_caller_set_none[False]`, `test_r112_a_test_s_child_gets_utf_8_where_the_caller_set_none[True]`.
- **M5:** The `--kind driver` hint is given for every refused test launch: the hint's condition keeps only `kind == "test"` (the `--key-file` and resolver conditions dropped), at line 3409. Caught by `test_r112_another_program_s_refusal_names_no_kind`.
- **M6:** Replacing `resolve_driver_program` with a check that ignores `~/` mutation path. Caught by `test_r112_a_test_launch_of_the_installed_mutation_engine_names_the_driver_kind`.
- **M7:** Removing help words from the module docstring only (lines 103-114). Caught by `test_r112_the_docstring_names_them_too`, `test_r112_the_help_claims_no_more_than_the_strip_gives`, and `test_r112_the_help_names_what_the_home_folder_still_reaches`; `test_r112_the_usage_text_names_the_owner_s_folders_a_stripped_run_does_not_see` would not catch docstring-only removal.
- **M8:** Dropping the `"--key-file" not in flags` condition at line 3409. Caught by `test_r112_a_test_launch_with_a_key_file_names_no_driver_kind`.
- **M9:** Removing help words from `usage()` only (lines 173-174). Caught by `test_r112_the_usage_text_names_the_owner_s_folders_a_stripped_run_does_not_see`, `test_r112_the_help_claims_no_more_than_the_strip_gives`, and `test_r112_the_help_names_what_the_home_folder_still_reaches`; `test_r112_the_docstring_names_them_too` would not catch usage-only removal.

## Changed expectations

no changed expectation

## Scratch test files

no scratch test file

## Commands and output (commit `3dcfff403b1c9440939746d649ddb5f7793b8684`, uncommitted changes as below)

### Step 1

```
git status --short
```

```
```

### Step 2 (before edit)

```
python -m pytest -p no:cacheprovider -q tests/test_improve_launcher_small.py
```

```
================================== FAILURES ===================================
_________ test_r112_the_help_names_what_the_home_folder_still_reaches _________
...
1 failed, 35 passed in 38.79s
```

Failing: `tests/test_improve_launcher_small.py::test_r112_the_help_names_what_the_home_folder_still_reaches`.

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
```

(`bridge/cursor-bridge/VERSION` not listed; `git restore` not run.)

### Step 6 (after edit)

```
python -m pytest -p no:cacheprovider -q tests/test_improve_launcher_small.py
```

```
36 passed in 38.59s
```

### Step 7

```
python -m pytest -p no:cacheprovider -q tests/test_bridge_run.py tests/test_bridge_run_driver.py tests/test_program_launcher_forms.py
```

```
190 passed in 187.74s (0:03:07)
```

### Step 8

```
python -m pytest -p no:cacheprovider -q tests/test_release_s_launcher.py tests/test_bridge_run_slot.py tests/test_tests_windowless.py tests/test_bug029_agent_name.py
```

```
104 passed, 3 skipped in 135.41s (0:02:15)
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
bridge-check: version 2026.11.24a (2026-11-28 00:37) at <Workspace>/bridge
bridge-check: 148 OK, 0 STALE, 0 MISSING, 0 EXTRA
RESULT: SOURCES MATCH bridge 2026.11.24a <Workspace>/bridge/cursor-bridge
windowless-check: 41 file(s) scanned, 0 FAIL, 0 NOTE
```

### Step 11

```
python -m pytest -p no:cacheprovider -q "tests/test_program_review_rows.py::test_r079_the_launcher_tests_write_no_row_into_the_checkout"
```

```
1 passed in 1981.34s (0:33:01)
```

Checkout has a `run/` folder; test was not skipped.

### Step 12

```
git diff --stat HEAD
```

```
 bridge/cursor-bridge/MANIFEST.json |  4 ++--
 bridge/cursor-bridge/bridge-run.py | 18 +++++++++++-------
 docs/CLI_REFERENCE.md              | 16 ++++++++++------
 docs/cli-reference.json            |  2 +-
 4 files changed, 24 insertions(+), 16 deletions(-)
```

### Step 13

```
git rev-parse HEAD
git status --short
```

```
3dcfff403b1c9440939746d649ddb5f7793b8684
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/bridge-run.py
 M docs/CLI_REFERENCE.md
 M docs/cli-reference.json
?? handoff/TASK-090-r3-report.md
```

Neither `bridge/cursor-bridge/VERSION` nor any `tests/test_task090_scratch_*` file is listed.

## Assumed, not verified

Assumed, not verified: none