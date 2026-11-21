# TASK-072 round 3 report

## Files changed or created

- `bridge/cursor-bridge/conformance-check.py` (the one correction, inside `_own_git_dir`)
- `bridge/cursor-bridge/MANIFEST.json` (rewritten by `python tools/make-manifest.py` in the Done list, not by hand)
- `docs/BUILDER_NOTES.md` (one dated line on `stat.FILE_ATTRIBUTE_REPARSE_POINT` being absent off Windows)
- `handoff/TASK-072-r3-report.md` (this report)

No test file was edited. No file under `.github/` was changed. The module docstring is unchanged. `bridge/cursor-bridge/VERSION` was restored after the manifest rewrite and is not listed by `git status --short`.

## Summary

`_own_git_dir` now looks at the Workspace's `.git` entry and at the folder a `.git` file's `gitdir:` line names with `os.lstat`, before `os.path.isdir` or `os.path.isfile`, and returns None when that last component is a symbolic link or any reparse point. A missing or unreadable entry is still no git folder. The weekly row therefore reads NOTE when `.git` or the `gitdir:` target is a junction or a symbolic link, and a plain `.git` folder, a `.git` file, and a missing `.git` read as before.

## Correction

- Correction 1. `_own_git_dir` (lines 587-623) imports `stat` and reads `FILE_ATTRIBUTE_REPARSE_POINT` with `getattr` so a missing constant is 0. At the Workspace `.git` path (lines 592-594) and at the joined `gitdir:` folder (lines 616-618), after the network-path refusal, `os.lstat` runs before any follow; `stat.S_ISLNK` or `st_file_attributes & reparse` returns None. `OSError` from `os.lstat` returns None. `os.path.abspath` is unchanged.

## Mutation self-check

Each mutant was applied in `bridge/cursor-bridge/conformance-check.py`, then `python -m pytest -p no:cacheprovider -q tests/test_program_weekly_floor.py` was run, then the edit was reverted. After each revert, `git diff` on that file was the one correction only: 9 insertions, both `os.lstat` checks present.

- R3-M1 the link check at the `.git` entry is removed. The `os.lstat` and the link test before `os.path.isdir` on the Workspace `.git` path were deleted. Caught by `test_r3_a_git_entry_that_is_a_link_is_not_followed`.

```
1 failed, 26 passed in 11.98s
```

- R3-M2 the link check at the `gitdir:` target is removed. The `os.lstat` and the link test before `os.path.isdir` on the joined `gitdir:` folder were deleted. Caught by `test_r3_a_gitdir_target_that_is_a_link_is_not_followed`.

```
1 failed, 26 passed in 12.09s
```

- R3-M3 only `S_ISLNK` is tested (the reparse-point attribute dropped). Both conditions kept `stat.S_ISLNK` and dropped `st_file_attributes & reparse`. Caught by `test_r3_a_git_entry_that_is_a_link_is_not_followed` (and `test_r3_a_gitdir_target_that_is_a_link_is_not_followed`).

```
2 failed, 25 passed in 12.30s
```

## Commands before the Done list

`python -m pytest -p no:cacheprovider -q tests/test_program_weekly_floor.py` (after the correction, before the mutants):

```
...........................                                              [100%]
27 passed in 15.85s
```

## Done commands

Run from `<Workspace>` after the last code edit, in order. Absolute paths printed by a command are written `<Workspace>` or `<tmp>` here. Commands 8 to 12 ran in one foreground shell, in that order, each after the previous had exited. The counts belong to commit `00f09d7601521acbf2e6732e539cedfe9e39a927`. At step 12 the working tree held uncommitted changes: `bridge/cursor-bridge/MANIFEST.json`, `bridge/cursor-bridge/conformance-check.py`, `docs/BUILDER_NOTES.md`, and this report (untracked). `bridge/cursor-bridge/VERSION` was not listed. No `.github` file was listed.

1. `git status --short`

```
 M bridge/cursor-bridge/conformance-check.py
 M docs/BUILDER_NOTES.md
?? handoff/TASK-072-r3-report.md
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
........................................................................ [100%]
72 passed in 29.93s
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
289 passed, 2 skipped in 74.22s (0:01:14)
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
486 passed, 2 skipped in 72.71s (0:01:12)
```

7. `python -m pytest -p no:cacheprovider -q -rs tests/test_dump_cli.py`

```
........................................................................ [ 71%]
.............................                                            [100%]
101 passed in 121.48s (0:02:01)
```

8. `python tools/dump-cli.py --check`

The command printed no lines and exited 0.

9. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`

```
bridge-check: version 2026.11.12a (2026-11-21 20:31) at <Workspace>\bridge
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
00f09d7601521acbf2e6732e539cedfe9e39a927
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/conformance-check.py
 M docs/BUILDER_NOTES.md
?? handoff/TASK-072-r3-report.md
```

## Assumed, not verified

- `stat.FILE_ATTRIBUTE_REPARSE_POINT` is missing on non-Windows CPython, so the reparse mask is `getattr(..., 0)`. This computer's Python is Windows and has the constant (1024); a bare name was not executed on Linux. On CI's Linux Python, `hasattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT")` is false and a Workspace whose `.git` is an ordinary directory still returns that directory.
- A relative `gitdir:` value is joined to the Workspace and then the last component is tested. The round-3 gitdir case uses the absolute path `git init --separate-git-dir` writes. A `.git` file whose `gitdir:` line is a relative path whose last component is a junction would confirm that joined path is refused.
