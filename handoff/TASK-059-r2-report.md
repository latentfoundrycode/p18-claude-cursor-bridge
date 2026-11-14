# TASK-059 round 2 report

## Files changed

- `<Workspace>/bridge/cursor-bridge/bridge-run.py`
- `<Workspace>/bridge/cursor-bridge/MANIFEST.json` (regenerated)
- `<Workspace>/tests/test_bridge_run_driver.py`
- `<Workspace>/tests/test_release_s_launcher.py`

## Summary

Round 2 replaced npm, pnpm and yarn option parsing with an exact allow-list before a bare `--`, gated known-runner refusals on named suites while keeping interpreter-suite intent for python `-m pytest`/`unittest`, fixed environment folder checks against the launch folder with relative joins at the runner's cwd, refused `npm_config_script_shell` and `npm_config_node_options`, added a Windows cmd.exe argument character check, restored `write_log` and `head_text` behaviour per the brief, and adjusted builder R-078 tests for Requirement 13.

## Requirements (1–24)

1. **Option allow-list:** `_package_scan_folder_options` and `_package_body_index` refuse any `-` word before `--` that is not an exact folder option form or `PACKAGE_ALLOWED_FLAGS`; `_package_folder_long_match` removed.
2. **Known message gate:** `known_runner_refuse_word` returns folder/list/cmd/escape refusals only when `named_suite(argv, folder)` is true, with python interpreter refusals checked earlier via `_python_suite_intent`.
3. **Python intent:** `_python_suite_intent` scans from `argv[1]`, reaches `-m pytest` or `-m unittest` through intervening options including `-X`/`-W` values.
4. **Environment base:** `outside_by_environment` calls `_package_folder_ok(found, launch, relative_base=run_dir)` so roots and `_link_walk_ok` use the launch folder.
5. **Script-shell env names:** `outside_by_environment` refuses non-empty `npm_config_script_shell` and `npm_config_node_options` for npm and pnpm named suites (`NPM_RUN_OTHER_ENV`).
6. **cmd.exe characters:** `_cmd_exe_refuse_word` and a `main` check before `bridge-run: started` refuse dangerous characters in `argv[1:]` when `resolve` would use `cmd.exe /d /c`.
7. **head_text:** For package managers and python, `head_text` joins `argv[start:start+2]` after the proper start index.
8. **uv scan:** `_escape_refuse_word` sets `scan_from = 1` for uv.
9. **named_suite python:** Unchanged python head test via `python_interpreter_ok` and `python_interpreter_lead`.
10. **_escape_head:** Unchanged mapping of `python3` and `py` to `python`.
11. **write_log:** Restored `if not os.path.isdir(os.path.join(folder, "run")): return`.
12. **Module docstring:** Not edited; `python tools/dump-cli.py --check` reports current.
13. **Builder tests:** `test_r078_npm_prefix_through_an_inbound_link_is_refused` gained control, `CREATE_NO_WINDOW`, skip/finally for links; `test_r078_driver_with_interpreter_flags_substitutes_program_end_to_end` gained windowless `creationflags`.
14. **Report:** This file; paths as `<Workspace>` and `~` only.
15. **python_interpreter_lead:** Unchanged accepted leads `-B` and `-X utf8`.
16. **Reads after lead:** Existing callers still use `python_interpreter_lead` start index.
17. **Other interpreter options:** `python_interpreter_lead` still refuses duplicate or unknown flags.
18. **Leading folder form:** `_package_body_index` skips exact folder options only.
19. **Folder rule:** `_package_folder_ok` and `_package_scan_folder_options` enforce roots, links, duplicates, missing values, and `-` values.
20. **Strip/log/limit:** Subfolder suites unchanged; folder options excluded from `head_text`.
21. **Environment names:** `npm_config_workspace*` and `npm_config_workspace_dir` held; prefix/INIT_CWD untouched.
22. **Two messages:** `KNOWN_RUNNER_REFUSE` vs unknown advice with `# wake` per gates above.
23. **No value printed:** Environment refusals name the variable only.
24. **merge_ids, glob, manifest:** Round 1 behaviour retained; `python tools/make-manifest.py` run.

## Commands and output

Commit for counts below: `642c01398705717bece27ccfa0742d71023757fe`. Working tree had uncommitted changes (`M bridge/cursor-bridge/MANIFEST.json`, `M bridge/cursor-bridge/bridge-run.py`, `M tests/test_bridge_run_driver.py`, `M tests/test_release_s_launcher.py`).

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
39 passed in 65.27s (0:01:05)
```

### 4. `python -m pytest -p no:cacheprovider -q tests/test_bridge_run.py tests/test_bridge_run_driver.py tests/test_release_s_launcher.py`

```
131 passed in 49.56s
```

### 5. `python -m pytest -p no:cacheprovider -q tests/test_bug029_agent_name.py tests/test_task032_supervisor_launcher.py tests/test_header_plan.py tests/test_header_plan_r3.py tests/test_dump_cli.py`

```
274 passed in 196.52s (0:03:16)
```

### 6. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`

```
bridge-check: version 2026.11.12a (2026-11-14 12:54) at <Workspace>\bridge
bridge-check: 146 OK, 0 STALE, 0 MISSING, 0 EXTRA
RESULT: SOURCES MATCH bridge 2026.11.12a
```

### 7. `git rev-parse HEAD` and `git status --short`

```
642c01398705717bece27ccfa0742d71023757fe
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/bridge-run.py
 M tests/test_bridge_run_driver.py
 M tests/test_release_s_launcher.py
```

## Mutations (M1–M8)

- M1: not run
- M2: not run
- M3: not run
- M4: not run
- M5: not run
- M6: not run
- M7: not run
- M8: not run

## Assumed, not verified

- How `cmd.exe /d /c` passes a `=` form folder option such as `--prefix=frontend` through to the underlying `.cmd` runner on Windows · the launcher forwards argv unchanged and relies on npm's own parsing · a live trace of argv received by `node`/`npm` via the cmd layer.
- How a folder value in drive-relative form (`C:x`) or a UNC path resolves on every Windows edition the bridge might run on · `_package_folder_ok` uses `os.path.abspath`/`os.path.join` · probing those forms under a controlled temp launch folder.
- Whether every character in `CMD_EXE_BAD_CHARS` is the complete set cmd.exe treats as metacharacters in a single argument · aligned with the brief's list and the security audit examples · exhaustive comparison to Microsoft's cmd parsing documentation and fuzzing through a real `.cmd` stub.
- Whether npm stand-ins on PATH always resolve as `.cmd` on Windows when the acceptance subprocess tests run · tests write `npm.cmd` on PATH · confirming `shutil.which` returns the `.cmd` path in the same `LOCALAPPDATA`/`PATH` layout the tests use.