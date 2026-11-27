# TASK-090 round 2 report

## Files changed

- `bridge/cursor-bridge/bridge-run.py`
- `bridge/cursor-bridge/MANIFEST.json` (via `python tools/make-manifest.py`)
- `docs/cli-reference.json` (via `python tools/dump-cli.py`)
- `docs/CLI_REFERENCE.md` (via `python tools/dump-cli.py`)
- `handoff/TASK-090-r2-report.md`

## One-paragraph summary

TASK-090 round 2 corrected launcher prose and one refusal branch in `bridge-run.py` without touching round 1's pid-at-limit, encoding default, or other behaviour: the module docstring and `usage()` now describe what `stripped_env` actually does (re-pointed home folder, APPDATA and LOCALAPPDATA; owner rights unchanged; named tool caches and cursor-agent login still reach owner folders; every cursor-agent run stripped; key file refused for driver kind) and drop the false claim that a stripped run sees none of the owner's files there; the `--kind driver` hint is omitted when the launch flags before `--` include `--key-file`; CLI reference and MANIFEST were regenerated. All 35 tests in `tests/test_improve_launcher_small.py`, the listed regression files, and `test_r079_the_launcher_tests_write_no_row_into_the_checkout` passed.

## Requirements (line references in final `bridge-run.py`)

1. **Pid file at limit (round 1):** lines 3809-3811 (`remove_pid_file` before `killer()` in the non-watch `TimeoutExpired` handler); line 3819 (retained removal after the try block).
2. **Child encoding (round 1):** lines 3601-3602 (`if kind in ("driver", "test") and "PYTHONIOENCODING" not in env`).
3. **Refusal hint (round 1, extended in R2):** lines 3405-3406 (`kind == "test"`, `"--key-file" not in flags`, and `resolve_driver_program` non-None).
4. **Help text (round 1, replaced by R1 this round):** superseded by R1 below.
5. **Nothing else (round 1):** `merge_ids` untouched; no new `BRIDGE_` names; ASCII verified.
R1. **Help text accurate:** module docstring lines 101-110; `usage()` lines 166-170.
R2. **Hint exact with key file:** line 3405 (`"--key-file" not in flags` on the driver-hint condition).
R3. **Report exact:** this file; test ids taken from pytest output below.

## Mutation code points (M1-M9)

- **M1:** Function `main`, lines 3809-3811. Deleting the `remove_pid_file` at 3809 before `killer()`. Caught by `test_r112_every_limit_branch_removes_the_pid_file_before_it_ends_the_tree` and `test_r112_a_run_ended_at_its_limit_leaves_no_pid_file`.
- **M2:** Lines 3601-3602. Widening to all kinds (dropping `kind in ("driver", "test")`). Caught by `test_r112_a_builder_s_and_a_reviewer_s_environment_unchanged`.
- **M3:** Line 3601, removing `not in env` or always assigning. Caught by `test_r112_a_driver_s_child_keeps_the_caller_s_value` and `test_r112_a_test_s_child_keeps_the_caller_s_value`.
- **M4:** Applying the default only inside the `stripped_env` branch (lines 3589-3602). Caught by `test_r112_a_driver_s_child_gets_utf_8_where_the_caller_set_none[False]` and the test-kind parametrized cases with `strip=False`.
- **M5:** Removing the `kind == "test"` guard at line 3405. Caught by `test_r112_another_program_s_refusal_names_no_kind` (no hint for non-driver commands).
- **M6:** Replacing `resolve_driver_program` with a check that ignores `~/` mutation path. Caught by `test_r112_a_test_launch_of_the_installed_mutation_engine_names_the_driver_kind`.
- **M7:** Removing help words from the module docstring only (lines 101-110). Caught by `test_r112_the_docstring_names_them_too`; `test_r112_the_usage_text_names_the_owner_s_folders_a_stripped_run_does_not_see` would not catch docstring-only removal.
- **M8:** Dropping the `"--key-file" not in flags` condition at line 3405. Caught by `test_r112_a_test_launch_with_a_key_file_names_no_driver_kind`.
- **M9:** Removing help words from `usage()` only (lines 168-170). Caught by `test_r112_the_usage_text_names_the_owner_s_folders_a_stripped_run_does_not_see` and the usage side of `test_r112_the_help_claims_no_more_than_the_strip_gives`; `test_r112_the_docstring_names_them_too` would not catch usage-only removal.

## Changed expectations

no changed expectation

## Scratch test files

no scratch test file

## Commands and output (commit `18026d51d70d106a103c9b1ee8de35f2e0a75937`, uncommitted changes as below)

### Step 1

```
git status --short
```

```
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/bridge-run.py
 M docs/CLI_REFERENCE.md
 M docs/cli-reference.json
```

### Step 2 (before edit)

```
python -m pytest -p no:cacheprovider -q tests/test_improve_launcher_small.py
```

```
2 failed, 33 passed in 38.89s
```

Failing: `tests/test_improve_launcher_small.py::test_r112_a_test_launch_with_a_key_file_names_no_driver_kind`, `tests/test_improve_launcher_small.py::test_r112_the_help_claims_no_more_than_the_strip_gives`.

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
35 passed in 38.59s
```

### Step 7

```
python -m pytest -p no:cacheprovider -q tests/test_bridge_run.py tests/test_bridge_run_driver.py tests/test_program_launcher_forms.py
```

```
190 passed in 189.78s (0:03:09)
```

### Step 8

```
python -m pytest -p no:cacheprovider -q tests/test_release_s_launcher.py tests/test_bridge_run_slot.py tests/test_tests_windowless.py tests/test_bug029_agent_name.py
```

```
104 passed, 3 skipped in 137.29s (0:02:17)
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
bridge-check: version 2026.11.24a (2026-11-27 23:15) at <Workspace>/bridge
bridge-check: 148 OK, 0 STALE, 0 MISSING, 0 EXTRA
RESULT: SOURCES MATCH bridge 2026.11.24a <Workspace>/bridge/cursor-bridge
windowless-check: 41 file(s) scanned, 0 FAIL, 0 NOTE
```

### Step 11

```
python -m pytest -p no:cacheprovider -q "tests/test_program_review_rows.py::test_r079_the_launcher_tests_write_no_row_into_the_checkout"
```

```
1 passed in 2052.12s (0:34:12)
```

Checkout has a `run/` folder; test was not skipped.

### Step 12

```
git diff --stat HEAD
```

```
 bridge/cursor-bridge/MANIFEST.json |  4 ++--
 bridge/cursor-bridge/bridge-run.py | 20 ++++++++++++--------
 docs/CLI_REFERENCE.md              | 14 +++++++++-----
 docs/cli-reference.json            |  2 +-
 4 files changed, 24 insertions(+), 16 deletions(-)
```

### Step 13

```
git rev-parse HEAD
git status --short
```

```
18026d51d70d106a103c9b1ee8de35f2e0a75937
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/bridge-run.py
 M docs/CLI_REFERENCE.md
 M docs/cli-reference.json
?? handoff/TASK-090-r2-report.md
```

Neither `bridge/cursor-bridge/VERSION` nor any `tests/test_task090_scratch_*` file is listed.

## Assumed, not verified

Assumed, not verified: none