# TASK-072 round 2 report

## Files changed or created

- `bridge/cursor-bridge/conformance-check.py` (correction 3: mixed-order network `gitdir:` prefix)
- `bridge/cursor-bridge/MANIFEST.json` (regenerated)
- `handoff/TASK-072-r2-report.md` (this report)

## Summary

Round 2 hardening was already present in the working tree for corrections 1, 2, and 4 (`_own_git_dir`, `_has_github_remote`, `_workflow_triggers`). The only code delta this run added is correction 3: treat any `gitdir:` value whose first two characters are both slash or backslash (including `/\` and `\/`) as not a local git folder before `os.path` runs, so mixed-order UNC-style prefixes never reach `lstat`. All `tests/test_program_weekly_floor.py` cases pass, including the supervisor rebuild network-path guard tests. MANIFEST was regenerated; VERSION restored after `make-manifest`.

## Corrections (function and lines)

1. **_own_git_dir** (829-830): the full `gitdir:` value is taken after the prefix with surrounding whitespace stripped, so paths containing spaces are not truncated.
2. **_has_github_remote** (852-857): `git config` uses `--local` and `--no-includes`; variables whose names begin with `GIT_CONFIG` are omitted from the subprocess `env`; `GIT_DIR` is set and failures read as no remote.
3. **_own_git_dir** (836-837): any `gitdir:` whose first two characters are each `/` or `\` is rejected before path operations (covers `//`, `\\`, `/\`, `\/`).
4. **_workflow_triggers** (744): the top-level trigger key matches bare `on:`, `"on":`, or `'on':`.

## Fixture changes

none

## Mutation self-check (R2-M1 through R2-M5)

- R2-M1 (`gitdir:` cut at first `\S+` again): `1 failed, 30 passed in 12.26s` — `tests/test_program_weekly_floor.py::test_r2_a_git_dir_whose_path_holds_a_space_is_read`
- R2-M2 (`--local` dropped from the `config` call): `31 passed in 12.07s` — not caught · on this computer `GIT_CONFIG_GLOBAL` is stripped from the subprocess env and the acceptance global-file case does not exercise default global config; would catch `test_r2_a_remote_outside_this_repository_config_is_not_read[global-file]` where the user's default global git configuration names a github.com remote
- R2-M3 (`--no-includes` dropped): `31 passed in 11.84s` — not caught · on this Git for Windows build `git config --local` does not follow `include.path`, so `test_r2_an_included_config_file_is_not_read` stays green; would catch on a git version where `--local` still follows includes without `--no-includes`
- R2-M4 (`GIT_CONFIG*` passed through): `31 passed in 11.84s` — not caught · with `--local` and `--no-includes`, `GIT_CONFIG_COUNT` / `GIT_CONFIG_KEY_*` pairs are not consulted; would catch `test_r2_a_remote_outside_this_repository_config_is_not_read[environment-pairs]` if those flags were absent together with env-pair injection
- R2-M5 (bare `on:` only): `2 failed, 29 passed in 12.59s` — `tests/test_program_weekly_floor.py::test_r2_a_quoted_on_key_is_read[double-quoted]` and `[single-quoted]`

## Commands

### 1. `git status --short` (before manifest)

```
 M bridge/cursor-bridge/conformance-check.py
 M handoff/TASK-072-r2.md
 M handoff/TASK-072-r3.md
 M handoff/TASK-072.md
```

### 2. `python tools/make-manifest.py`

```
make-manifest: version 2026.11.12a, 148 files hashed, VERSION + MANIFEST.json written
```

### 3. `git restore bridge/cursor-bridge/VERSION`

(no output)

### 4. `python -m pytest -p no:cacheprovider -q -rs tests/test_program_weekly_floor.py tests/test_conformance_check.py tests/test_conformance_check_a4.py tests/test_diagram_check.py tests/test_bug042.py`

```
........................................................................ [ 94%]
....                                                                     [100%]
76 passed in 27.73s
```

### 5. `python -m pytest -p no:cacheprovider -q -rs tests/test_hotfix25a_conformance_semgrep.py tests/test_a4_followups.py tests/test_a4_review_fixes.py tests/test_b2_least_confident.py tests/test_program_branch_rule.py tests/test_calibrate_program.py tests/test_conformance_windowless.py`

```
289 passed, 2 skipped in 71.04s (0:01:11)
```

### 6. `python -m pytest -p no:cacheprovider -q -rs tests/test_workflows_line_check.py tests/test_header_status.py tests/test_header_tables.py tests/test_header_tables_r2.py tests/test_header_currency.py tests/test_program_strip_names.py tests/test_loop_text_windowless.py tests/test_running_projects_classify.py`

```
486 passed, 2 skipped in 69.60s (0:01:09)
```

### 7. `python -m pytest -p no:cacheprovider -q -rs tests/test_dump_cli.py`

```
101 passed in 121.05s (0:02:01)
```

### 8. `python tools/dump-cli.py --check`

(no output, exit 0)

### 9. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`

```
bridge-check: version 2026.11.12a (2026-11-22 14:21) at <Workspace>/bridge
bridge-check: 148 OK, 0 STALE, 0 MISSING, 0 EXTRA
RESULT: SOURCES MATCH bridge 2026.11.12a <Workspace>/bridge/cursor-bridge
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
72bbccc6ac602408742fb7264a41cd62232ebbde
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/conformance-check.py
 M handoff/TASK-072-r2.md
 M handoff/TASK-072-r3.md
 M handoff/TASK-072.md
```

`bridge/cursor-bridge/VERSION` not listed. No `.github` file modified.

Results above belong to commit `72bbccc6ac602408742fb7264a41cd62232ebbde` with uncommitted changes as shown (`handoff/` edits and this report were not part of the builder's code diff).

## Assumed, not verified

Assumed, not verified: none