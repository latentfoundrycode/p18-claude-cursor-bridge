# TASK-059 round 3 report

## Files changed

- `<Workspace>/bridge/cursor-bridge/bridge-run.py`
- `<Workspace>/bridge/cursor-bridge/MANIFEST.json` (regenerated)
- `<Workspace>/tests/test_bridge_run.py`
- `<Workspace>/tests/test_release_s_launcher.py`

## Summary

Round 3 tightened npm, pnpm and yarn option parsing so only exact folder-option forms and post-subcommand bare flags (`--silent`, `-s`, `--if-present`) are allowed, refusing every `=` flag form and any flag before the subcommand; replaced the per-name environment folder checks with a prefix rule that refuses nearly all `npm_config_`, `pnpm_config_` and `yarn_` names (except the two bridge cache variables); applied the logged-head word filter to package managers and python; recognized python by head name for named suites while keeping `test_suite` path refusal; ran the cmd.exe character check for every `.cmd` runner before start; and updated two builder R-078 tests so acceptance controls and link cleanup match Requirement 13.

## Requirements (1–24)

1. **Option list:** `_package_allowed_flag` removed; `_package_scan_folder_options` allows `PACKAGE_ALLOWED_FLAGS` only after the subcommand; `_package_body_index` skips folder options only, so flags before the subcommand leave the command unnamed; `=` forms and abbreviations are refused in the scan.
2. **Known message gate:** Unchanged: `known_runner_refuse_word` folder and list scans run only when `named_suite` holds.
3. **Python intent:** `_python_suite_intent` unchanged in structure; still gates interpreter known refusals.
4. **Environment rule:** `outside_by_environment` refuses any set `npm_config_` name for npm, pnpm and yarn named suites, plus `pnpm_config_` for pnpm and `yarn_` for yarn, empty values included; `PACKAGE_CACHE_ENV` exempts `NPM_CONFIG_CACHE` and `YARN_CACHE_FOLDER`.
5. **Removed round-2 env code:** `NPM_PACKAGE_ENV`, `PNPM_PACKAGE_ENV`, `NPM_RUN_OTHER_ENV` and `_package_folder_ok`'s `relative_base` branch removed.
6. **cmd.exe characters:** `main` refuses when `cmd_inj` is set without requiring `named_suite`, so watch runs with `gh.cmd` are held too.
7. **head_text:** All heads use the filtered two-word subs from `argv[start:start+2]` after `python_interpreter_lead` or `_package_body_index`.
8. **uv scan:** Unchanged `scan_from = 1` for uv in `_escape_refuse_word`.
9. **Python by name:** `named_suite`, `runner_word`, `python_interpreter_lead`, `_python_suite_intent`, and `known_runner_refuse_word` use `head_of(argv) in ("python", "python3", "py")`; `test_suite` still refuses non-venv path-qualified interpreters.
10. **_escape_head:** Unchanged mapping of `python3` and `py` to `python`.
11. **write_log:** Unchanged guard on `run/`.
12. **Module docstring:** Not edited.
13. **Builder tests:** `test_r078_npm_prefix_and_c_count_as_one_folder_option` asserts accepted control; `test_r078_npm_prefix_through_an_inbound_link_is_refused` runs control inside `try` and strips config env names from the launch environment.
14. **Report:** This file; round 2 item 18 said `_package_body_index` skipped exact folder options only, but round 2's code also skipped the three flags at lines 374–376; round 3 removes that skip so only folder options are skipped before the subcommand.
15. **python_interpreter_lead:** Still accepts only `-B` and `-X utf8` leads.
16. **Reads after lead:** Callers unchanged in using the lead start index.
17. **Other interpreter options:** `python_interpreter_lead` still refuses duplicate or unknown flags.
18. **Leading folder form:** `_package_body_index` skips exact folder options only before the subcommand word.
19. **Folder rule:** `_package_folder_ok` and `_package_scan_folder_options` enforce roots, links, duplicates, missing values, and `-` values.
20. **Strip/log/limit:** Subfolder suites run stripped; `head_text` omits folder options, flags, and script arguments.
21. **Environment scope:** Prefix rule applies only to named npm, pnpm and yarn suites; pytest, python, uv and others unchanged.
22. **Two messages:** `KNOWN_RUNNER_REFUSE` vs unknown advice with `# wake` per gates above.
23. **No value printed:** Environment refusals name the variable only.
24. **merge_ids, glob, manifest:** Round 1 behaviour retained; `python tools/make-manifest.py` run; `VERSION` unchanged.

## Commands and output

Commit for counts below: `88cb7341a8d10a05c927e05ddcfc02679f25d950`. Working tree held uncommitted changes (`M bridge/cursor-bridge/MANIFEST.json`, `M bridge/cursor-bridge/bridge-run.py`, `M tests/test_bridge_run.py`, `M tests/test_release_s_launcher.py`).

### 1. `python tools/make-manifest.py`

```
make-manifest: version 2026.11.12a, 146 files hashed, VERSION + MANIFEST.json written
```

### 2. `python tools/dump-cli.py --check`

```
(no output; exit code 0)
```

### 3. `python -m pytest -p no:cacheprovider -q tests/test_program_launcher_forms.py`

```
............................................                             [100%]
44 passed in 74.40s (0:01:14)
```

### 4. `python -m pytest -p no:cacheprovider -q tests/test_bridge_run.py tests/test_bridge_run_driver.py tests/test_release_s_launcher.py`

```
........................................................................ [ 54%]
...........................................................              [100%]
131 passed in 44.26s
```

### 5. `python -m pytest -p no:cacheprovider -q tests/test_bug029_agent_name.py tests/test_task032_supervisor_launcher.py tests/test_header_plan.py tests/test_header_plan_r3.py tests/test_dump_cli.py`

```
........................................................................ [ 26%]
........................................................................ [ 52%]
........................................................................ [ 78%]
..........................................................               [100%]
274 passed in 196.75s (0:03:16)
```

### 6. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`

```
bridge-check: version 2026.11.12a (2026-11-14 13:26) at <Workspace>\bridge
bridge-check: 146 OK, 0 STALE, 0 MISSING, 0 EXTRA
RESULT: SOURCES MATCH bridge 2026.11.12a
```

### 7. `git rev-parse HEAD` and `git status --short`

```
88cb7341a8d10a05c927e05ddcfc02679f25d950
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/bridge-run.py
 M tests/test_bridge_run.py
 M tests/test_release_s_launcher.py
```

## Mutations

- M1: not run
- M2: not run
- M3: not run
- M4: not run
- M5: not run
- M6: not run
- M7: not run
- M8: withdrawn

## Assumed, not verified

- pnpm reads every `pnpm_config_<x>` as `--<x>` · Requirement 4 applies the prefix without re-probing pnpm · live pnpm with a stand-in that prints env names.
- yarn 1 reads every `yarn_<x>` as its option · same · live yarn or yarn source trace.
- No npm, pnpm or yarn option word outside Requirement 1's list survives the scan · brief and acceptance `NOT_LISTED` are exhaustive · formal review of each runner's nopt tables against the list.
- nopt reads folder `=` forms only as exact tokens like `--prefix=frontend` and `-C=frontend` · `_package_folder_token` matches exact names · npm probe with each `=` variant.
- cmd.exe passes a package manager's `=` flag through to the stand-in unchanged · Requirement 6 does not depend on it · Windows npm.cmd argument dump.
- Drive-relative or UNC folder values resolve the way `_package_folder_ok` expects · standard `os.path.abspath`/`realpath` · probes with `C:x` and `\\server\share` under launch roots.
- The `CMD_EXE_BAD_CHARS` set is complete for cmd.exe argument parsing · matches round 2 reality check and acceptance tests · Microsoft cmd.exe documentation for every metacharacter in forwarded arguments.