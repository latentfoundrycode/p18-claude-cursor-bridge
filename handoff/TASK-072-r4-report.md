# TASK-072 round 4 report

## Files changed

- bridge/cursor-bridge/conformance-check.py
- bridge/cursor-bridge/MANIFEST.json

## One-paragraph summary

Round 4 adds one refusal in `_own_git_dir`: a `gitdir:` value whose first four characters are a path separator, two question marks, and another separator is returned as no git folder before any `os.path` or `os.lstat` call, closing the NT object-manager prefix forms (`\??\...`, `/??/...`, and mixed slash) that round 2's two-leading-separator rule missed because the second character is `?`. MANIFEST.json was regenerated; all listed pytest batches passed; mutation R4-M1 dropped that refusal and reproduced three failures on the parametrized network-gitdir cases.

## Correction

`_own_git_dir` in `bridge/cursor-bridge/conformance-check.py`, lines 838-845 after the change:

```
    if (
        len(gitdir) >= 4
        and gitdir[0] in "/\\"
        and gitdir[1] == "?"
        and gitdir[2] == "?"
        and gitdir[3] in "/\\"
    ):
        return None
```

## Mutation self-check

R4-M1: the `\??\` refusal block above was removed by hand, `python -m pytest -p no:cacheprovider -q tests/test_program_weekly_floor.py` produced `3 failed, 31 passed in 13.10s`, failing `test_rebuild_r2_a_network_gitdir_in_either_slash_order_is_never_touched[nt-object-unc]`, `[nt-object-globalroot]`, and `[nt-object-forward-slashes]`; the block was restored by hand and confirmed with `git diff` showing only the eight added lines in `_own_git_dir`.

## Command outputs

### 1. `git status --short`

```
 M bridge/cursor-bridge/conformance-check.py
 M handoff/TASK-072-r2.md
 M handoff/TASK-072-r3.md
 M handoff/TASK-072.md
?? handoff/TASK-072-r4-report.md
```

### 2. `python tools/make-manifest.py`

```
make-manifest: version 2026.11.12a, 148 files hashed, VERSION + MANIFEST.json written
```

### 3. `git restore bridge/cursor-bridge/VERSION`

```
(no output)
```

### 4. `python -m pytest -p no:cacheprovider -q -rs tests/test_program_weekly_floor.py tests/test_conformance_check.py tests/test_conformance_check_a4.py tests/test_diagram_check.py tests/test_bug042.py`

```
........................................................................ [ 91%]
.......                                                                  [100%]
79 passed in 28.13s
```

### 5. `python -m pytest -p no:cacheprovider -q -rs tests/test_hotfix25a_conformance_semgrep.py tests/test_a4_followups.py tests/test_a4_review_fixes.py tests/test_b2_least_confident.py tests/test_program_branch_rule.py tests/test_calibrate_program.py tests/test_conformance_windowless.py`

```
........................................................................ [ 24%]
........................................................................ [ 49%]
........................................................................ [ 74%]
......................................................s.s............... [ 98%]
...                                                                      [100%]
=========================== short test summary info ===========================
SKIPPED [1] tests\test_conformance_windowless.py:526: creating a file symbolic link needs a privilege here
SKIPPED [1] tests\test_conformance_windowless.py:551: Windows collapses `..` before it follows a link
289 passed, 2 skipped in 70.36s (0:01:10)
```

### 6. `python -m pytest -p no:cacheprovider -q -rs tests/test_workflows_line_check.py tests/test_header_status.py tests/test_header_tables.py tests/test_header_tables_r2.py tests/test_header_currency.py tests/test_program_strip_names.py tests/test_loop_text_windowless.py tests/test_running_projects_classify.py`

```
.............................................ss......................... [ 14%]
........................................................................ [ 29%]
........................................................................ [ 44%]
........................................................................ [ 59%]
........................................................................ [ 73%]
........................................................................ [ 88%]
........................................................                 [100%]
=========================== short test summary info ===========================
SKIPPED [1] tests\test_workflows_line_check.py:496: cannot create a symbolic link here: [WinError 1314] A required privilege is not held by the client: '<tmp>\\test_r015_checker_is_found_bes0\\bin\\inventory-check.py' -> '<tmp>\\test_r015_checker_is_found_bes0\\elsewhere\\inventory-check.py'
SKIPPED [1] tests\test_workflows_line_check.py:496: cannot create a symbolic link here: [WinError 1314] A required privilege is not held by the client: '<tmp>\\test_r015_checker_is_found_bes1\\bin\\conformance-check.py' -> '<tmp>\\test_r015_checker_is_found_bes1\\elsewhere\\conformance-check.py'
486 passed, 2 skipped in 68.81s (0:01:08)
```

### 7. `python -m pytest -p no:cacheprovider -q -rs tests/test_dump_cli.py`

```
........................................................................ [ 71%]
.............................                                            [100%]
101 passed in 112.88s (0:01:52)
```

### 8. `python tools/dump-cli.py --check`

```
(no output; exit code 0)
```

### 9. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`

```
bridge-check: version 2026.11.12a (2026-11-22 14:35) at <Workspace>\bridge
bridge-check: 148 OK, 0 STALE, 0 MISSING, 0 EXTRA
RESULT: SOURCES MATCH bridge 2026.11.12a <Workspace>\bridge\cursor-bridge
```

### 10. `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks`

```
windowless-check: 41 file(s) scanned, 0 FAIL, 0 NOTE
```

### 11. `python -c "open('bridge/cursor-bridge/conformance-check.py','rb').read().decode('ascii'); print('ascii ok')"`

```
ascii ok
```

### 12. `git rev-parse HEAD` and `git status --short`

```
f968a7b40f7d8ac4f420b045cd96c2c71d27240d
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/conformance-check.py
 M handoff/TASK-072-r2.md
 M handoff/TASK-072-r3.md
 M handoff/TASK-072.md
?? handoff/TASK-072-r4-report.md
```

Commit `f968a7b40f7d8ac4f420b045cd96c2c71d27240d`; working tree holds uncommitted changes (`conformance-check.py`, `MANIFEST.json`, this report, and pre-existing modified handoff briefs). `bridge/cursor-bridge/VERSION` is not listed; no `.github` file is listed.

## Assumed, not verified

Assumed, not verified: none