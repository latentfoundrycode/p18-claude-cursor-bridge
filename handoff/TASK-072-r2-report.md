# TASK-072 round 2 report

## Files changed or created

- `bridge/cursor-bridge/conformance-check.py` (the four corrections, inside `_workflow_triggers`, `_own_git_dir`, and `_has_github_remote`)
- `bridge/cursor-bridge/MANIFEST.json` (rewritten by `python tools/make-manifest.py` in the Done list, not by hand)
- `docs/BUILDER_NOTES.md` (one dated line on Git for Windows 2.53 and `git config --local`)
- `handoff/TASK-072-r2-report.md` (this report)

No test file was edited. No file under `.github/` was changed. The module docstring is unchanged. `bridge/cursor-bridge/VERSION` was restored after the manifest rewrite and is not listed by `git status --short`.

## Summary

The weekly row still reads a GitHub remote only from this Workspace's own git configuration, and it now keeps a `gitdir:` path that contains spaces, ignores a remote that arrives from the global file, from `GIT_CONFIG*` environment pairs, or from an included file, and treats a `gitdir:` value that names another host as no git folder. A top-level trigger key written `"on":` or `'on':` is read the same way as a bare `on:`.

## Corrections

- Correction 1. `_own_git_dir` (lines 596-602) takes the first `gitdir:` line, keeps the rest of that line, and strips surrounding spaces and tabs; `splitlines` drops the line ending, so a path may hold spaces.
- Correction 2. `_has_github_remote` (lines 643-648) deletes every copied environment name that begins `GIT_CONFIG`, and the `config` call passes `--local` and `--no-includes`. The call still sets `GIT_DIR`, drops `GIT_WORK_TREE`, passes `-c core.fsmonitor=false`, is windowless, uses `timeout=GH_TIMEOUT`, and reads a failure as no remote.
- Correction 3. `_own_git_dir` (lines 604-606) returns None, before any `os.path` call, when the `gitdir:` value begins with two slashes of either direction (`/`, `\`, or one of each).
- Correction 4. `_workflow_triggers` (line 535) matches a top-level key that is `on:`, `"on":`, or `'on':`, with the quotes matching.

## Mutation self-check

Each mutant was applied in `bridge/cursor-bridge/conformance-check.py`, then the weekly-floor file was run, then the edit was reverted. R2-M1 used `python -m pytest -p no:cacheprovider -q tests/test_program_weekly_floor.py`. R2-M2 added `--tb=no`, and R2-M3, R2-M4, and R2-M5 added `--tb=line`, so a failure trace would not be copied here. After R2-M1, `git diff` on that file was only the four corrections. After R2-M2, R2-M3, and R2-M4 the restored `--local --no-includes` call and the `GIT_CONFIG` loop were back. After R2-M5, `git diff --stat` was `1 file changed, 14 insertions(+), 6 deletions(-)` and the diff was the four corrections only.

- R2-M1 the `gitdir:` value is cut at its first space again. The value was split on the first space after the surrounding spaces and tabs were stripped. Caught by `test_r2_a_git_dir_whose_path_holds_a_space_is_read`.

```
1 failed, 24 passed in 11.36s
```

- R2-M2 `--local` is dropped from the `config` call. not caught. `test_r2_a_remote_outside_this_repository_config_is_not_read[global-file]` would catch it if `GIT_CONFIG_GLOBAL` were still passed to git; with those variables removed, the system and global files git then reads on this computer name no github.com remote, and the case stays NOTE.

```
25 passed in 10.94s
```

- R2-M3 `--no-includes` is dropped from the `config` call. not caught. `test_r2_an_included_config_file_is_not_read` would catch it if the call had no file scope; Git for Windows 2.53 leaves includes off when `--local` is set, so the case stays NOTE.

```
25 passed in 11.10s
```

- R2-M4 the `GIT_CONFIG*` variables are passed on. not caught. `test_r2_a_remote_outside_this_repository_config_is_not_read[environment-pairs]` would catch it if `git config --local` applied `GIT_CONFIG_COUNT` pairs; on Git for Windows 2.53 those pairs are applied only when no file scope is given, so the case stays NOTE while `--local` remains.

```
25 passed in 11.09s
```

- R2-M5 only a bare `on:` is matched. The trigger pattern was restored to `^on:`. Caught by `test_r2_a_quoted_on_key_is_read[double-quoted]` (and `[single-quoted]`).

```
2 failed, 23 passed in 11.05s
```

## Commands before the Done list

`python -m pytest -p no:cacheprovider -q tests/test_program_weekly_floor.py` (after the four corrections, before the mutants):

```
.........................                                                [100%]
25 passed in 11.11s
```

## Done commands

Run from `<Workspace>` after the last code edit, in order. Absolute paths printed by a command are written `<Workspace>` or `<tmp>` here. Commands 8 to 12 ran in one foreground shell, in that order, each after the previous had exited. The counts belong to commit `506640688a7a517f3b5766db1ad43eb65f97f353`. At step 12 the working tree held uncommitted changes: `bridge/cursor-bridge/MANIFEST.json`, `bridge/cursor-bridge/conformance-check.py`, and `docs/BUILDER_NOTES.md`. `bridge/cursor-bridge/VERSION` was not listed. No `.github` file was listed. This report was written after step 12, so that listing does not name it.

1. `git status --short`

```
 M bridge/cursor-bridge/conformance-check.py
 M docs/BUILDER_NOTES.md
```

2. `python tools/make-manifest.py`

```
make-manifest: version 2026.11.12a, 148 files hashed, VERSION + MANIFEST.json written
```

3. `git restore bridge/cursor-bridge/VERSION`

The command printed nothing and exited 0. A following `git status --short` limited to `VERSION` and `MANIFEST.json` printed:

```
 M bridge/cursor-bridge/MANIFEST.json
```

4. `python -m pytest -p no:cacheprovider -q -rs tests/test_program_weekly_floor.py tests/test_conformance_check.py tests/test_conformance_check_a4.py tests/test_diagram_check.py tests/test_bug042.py`

```
......................................................................   [100%]
70 passed in 29.45s
```

5. `python -m pytest -p no:cacheprovider -q -rs tests/test_hotfix25a_conformance_semgrep.py tests/test_a4_followups.py tests/test_a4_review_fixes.py tests/test_b2_least_confident.py tests/test_program_branch_rule.py tests/test_calibrate_program.py tests/test_conformance_windowless.py`

```
........................................................................ [ 24%]
........................................................................ [ 49%]
........................................................................ [ 74%]
......................................................s.s............... [ 98%]
...                                                                      [100%]
=========================== short test summary info ===========================
SKIPPED [1] tests\test_conformance_windowless.py:526: creating a file symbolic link needs a privilege here
SKIPPED [1] tests\test_conformance_windowless.py:551: Windows collapses `..` before it follows a link
289 passed, 2 skipped in 75.28s (0:01:15)
```

6. `python -m pytest -p no:cacheprovider -q -rs tests/test_workflows_line_check.py tests/test_header_status.py tests/test_header_tables.py tests/test_header_tables_r2.py tests/test_header_currency.py tests/test_program_strip_names.py tests/test_loop_text_windowless.py tests/test_running_projects_classify.py`

The two skip lines below replace the temporary-folder prefix with `<tmp>`.

```
.............................................ss......................... [ 14%]
........................................................................ [ 29%]
........................................................................ [ 44%]
........................................................................ [ 59%]
........................................................................ [ 73%]
........................................................................ [ 88%]
........................................................                 [100%]
=========================== short test summary info ===========================
SKIPPED [1] tests\test_workflows_line_check.py:496: cannot create a symbolic link here: [WinError 1314] A required privilege is not held by the client: '<tmp>\bin\inventory-check.py' -> '<tmp>\elsewhere\inventory-check.py'
SKIPPED [1] tests\test_workflows_line_check.py:496: cannot create a symbolic link here: [WinError 1314] A required privilege is not held by the client: '<tmp>\bin\conformance-check.py' -> '<tmp>\elsewhere\conformance-check.py'
486 passed, 2 skipped in 72.82s (0:01:12)
```

7. `python -m pytest -p no:cacheprovider -q -rs tests/test_dump_cli.py`

```
........................................................................ [ 71%]
.............................                                            [100%]
101 passed in 120.83s (0:02:00)
```

8. `python tools/dump-cli.py --check`

The command printed no lines and exited 0.

9. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`

```
bridge-check: version 2026.11.12a (2026-11-21 19:38) at <Workspace>\bridge
bridge-check: 148 OK, 0 STALE, 0 MISSING, 0 EXTRA
RESULT: SOURCES MATCH bridge 2026.11.12a
```

10. `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks`

```
windowless-check: 41 file(s) scanned, 0 FAIL, 0 NOTE
```

11. `python -c "open('bridge/cursor-bridge/conformance-check.py','rb').read().decode('ascii'); print('ascii ok')"`

```
ascii ok
```

12. `git rev-parse HEAD` and `git status --short`

```
506640688a7a517f3b5766db1ad43eb65f97f353
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/conformance-check.py
 M docs/BUILDER_NOTES.md
```

## Assumed, not verified

- A quoted `on` key with a space before the colon (`"on" :` or `'on' :`) is not matched. The brief and the cases use the colon immediately after the key, as the bare `on:` form does. A workflow line `"on" :` would confirm it.
- The first `gitdir:` line in a `.git` file is the value used. Git writes one such line, and the space case uses that file. A second `gitdir:` line later in the file would confirm which line is used.
- A network path includes the mixed prefixes `/\` and `\/` as well as `//` and `\\`. The brief says two slashes or two backslashes, in either order of slash, and there is no test. A reviewer reading those four prefixes in `_own_git_dir` confirms the reading.
