# TASK-083 round 3 report

## Files changed

- `bridge/cursor-bridge/permission-guard.py`
- `bridge/cursor-bridge/MANIFEST.json` (by `python tools/make-manifest.py` only)
- `tests/test_permission_guard.py`
- `docs/BUILDER_NOTES.md` (one dated line, present in the step 11 status)
- `handoff/TASK-083-r3-report.md` (this report, written after step 11)

`tests/test_program_ready.py` was not edited. `bridge/cursor-bridge/VERSION` was restored with `git restore` after `make-manifest.py` and is not in the step 11 status.

## Summary

`_read_merge_words` now keeps a `--disable-auto` or help exemption only when the bare option is present and no `=` form of that option is, and `gh_words` treats an option before the gh subcommand (other than `-R`, `--repo` or `--hostname`, and other than the `gh api` walk) as unreadable when any word follows it, so `check` refuses that command before it reads a merge and `state_changing` counts it as state-changing.

## J1-J3

J1. `_read_merge_words` (lines 2489-2565) records a bare `--disable-auto`, `--help` or `-h`, records every `--disable-auto=<v>` and `--help=<v>`, and at line 2561 records a single-dash word holding `=` whose letters before `=` include `h`, then at line 2565 returns each exemption only when the bare form was seen and no `=` form was; `merge_reason` (lines 2568-2574) is unchanged and still returns no reason when that reading says an exemption stands, so a cleared exemption continues into the record checks.

J2. `gh_words` (lines 2056-2083) returns the dash word as the group when, before the group or after a group other than `api` and before the subcommand, a word other than `-R`, `--repo` or `--hostname` begins with `-` and a word follows it (lines 2074-2076); the gh branch of `_check_word_list` (lines 2315-2318) refuses that with `_cannot` before `merge_reason`, and the gh branch of `state_changing` (lines 2389-2393) returns true for it.

J3. The docstring of `_read_merge_words` (lines 2490-2491) states the J1 rule in one sentence, and the docstring added on `gh_words` (line 2057) states the J2 rule in one sentence.

One case was added in `tests/test_permission_guard.py`: `test_r083_r3_an_equals_form_before_the_bare_option_clears_it_and_the_option_is_state_changing` (lines 293-305). The supervisor's round-3 section puts every `=` form after the bare option, so a last-value reading would refuse those too, and it never asserts `state_changing`. The added case refuses `--disable-auto=false` before `--disable-auto` where no record exists, refuses `-h -sh=false` (the clustered `=` form J1 names) where a standing help exemption would allow the command, and refuses `git status && gh --subject xx pr view 12` in a workspace because the reason is `a chain of`.

## Defects

1. The one reading of the words after `merge` clears the exemption when it finds an `=` form of `--disable-auto` or of help, so a later `--disable-auto=false`, `--help=false` or `-h=false` is not left exempt by the earlier bare option while gh's last value is false.

2. `gh_words` no longer skips an unknown option before the subcommand as a single word, so the option's value is not taken as the group, and `check` refuses the command as unreadable before any merge reading.

## Commands run before the Done list

### `python -m pytest -p no:cacheprovider -q -rfE tests/test_program_ready.py -k "r083_r3 or r083_r2 or disable_auto or help" tests/test_permission_guard.py -k "r083_r3 or r083_r2 or test_allowed or test_refused"`

```
........................................................................ [ 19%]
........................................................................ [ 39%]
........................................................................ [ 59%]
........................................................................ [ 78%]
........................................................................ [ 98%]
.....                                                                    [100%]
365 passed, 79 deselected in 41.37s
```

## Done

Steps 1 through 6 were one shell, in the order below. Steps 10 and 11 were one shell. Each block is the lines that listed command printed.

### 1. `git status --short`

```
 M bridge/cursor-bridge/permission-guard.py
 M docs/BUILDER_NOTES.md
 M tests/test_permission_guard.py
```

### 2. `python tools/make-manifest.py`

```
make-manifest: version 2026.11.12a, 146 files hashed, VERSION + MANIFEST.json written
```

### 3. `git restore bridge/cursor-bridge/VERSION`

Printed no lines. Exit 0.

### 4. `git status --short`

```
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/permission-guard.py
 M docs/BUILDER_NOTES.md
 M tests/test_permission_guard.py
```

`bridge/cursor-bridge/VERSION` is not listed.

### 5. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`

```
bridge-check: version 2026.11.12a (2026-11-17 01:37) at <Workspace>\bridge
bridge-check: 146 OK, 0 STALE, 0 MISSING, 0 EXTRA
RESULT: SOURCES MATCH bridge 2026.11.12a
```

### 6. `python tools/dump-cli.py --check`

Printed no lines. Exit 0.

### 7. `python -m pytest -p no:cacheprovider -q -rfE tests/test_program_ready.py`

```
........................................................................ [ 49%]
........................................................................ [ 98%]
..                                                                       [100%]
146 passed in 52.19s
```

### 8. `python -m pytest -p no:cacheprovider -q tests/test_permission_guard.py tests/test_permission_guard_a4.py tests/test_allowlist.py tests/test_program_permission_guard.py`

```
........................................................................ [  5%]
........................................................................ [ 11%]
........................................................................ [ 16%]
........................................................................ [ 22%]
........................................................................ [ 27%]
........................................................................ [ 33%]
........................s...ss.....sss....................s............. [ 38%]
..s...............................................s...........s......... [ 44%]
........s...ss.....sss....................s...............s............. [ 49%]
..................................s...........s......................... [ 55%]
........................................................................ [ 60%]
........................................................................ [ 66%]
........................................................................ [ 71%]
........................................................................ [ 77%]
........................................................................ [ 82%]
........................................................................ [ 88%]
........................................................................ [ 93%]
........................................................................ [ 99%]
.............                                                            [100%]
1289 passed, 20 skipped in 106.85s (0:01:46)
```

### 9. `python -m pytest -p no:cacheprovider -q tests/test_d003_review_round_states.py tests/test_review_guard.py tests/test_release_s_records_gate.py tests/test_program_branch_rule.py tests/test_program_release_s_rows.py tests/test_task032_supervisor_guard.py tests/test_tests_windowless.py`

```
........................................................................ [ 15%]
........................................................................ [ 31%]
........................................................................ [ 47%]
........................................................................ [ 63%]
........................................................................ [ 78%]
........................................................................ [ 94%]
........................                                                 [100%]
456 passed in 322.96s (0:05:22)
```

### 10. `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks`

```
windowless-check: 39 file(s) scanned, 0 FAIL, 0 NOTE
```

### 11. `git rev-parse HEAD` and `git status --short`

```
ad5c1093ec02dc9f501f2b64df98db7cef1b1e4b
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/permission-guard.py
 M docs/BUILDER_NOTES.md
 M tests/test_permission_guard.py
```

`bridge/cursor-bridge/VERSION` is not listed.

## Results

The counts above belong to commit `ad5c1093ec02dc9f501f2b64df98db7cef1b1e4b`. At step 11 the working tree held uncommitted changes to `bridge/cursor-bridge/MANIFEST.json`, `bridge/cursor-bridge/permission-guard.py`, `docs/BUILDER_NOTES.md` and `tests/test_permission_guard.py`. This report was written after that status.

## Assumed, not verified

- Whether any gh command the supervisor runs places an option other than `-R`, `--repo` or `--hostname` before its subcommand, outside the `gh api` walk - the acceptance files this round ran do not require such a command to pass, and J2 refuses one whenever a word follows the option - the supervisor's gh command lines.
- Whether cobra reads `-h` or `--help` before a subcommand as the root's help and stops, rather than continuing into the subcommand - J2 treats every dash word other than the repository options as unreadable when any word follows it, and the passing cases are only help or version as the last word (`gh --help`, `gh pr --help`, `gh --version`) - `gh --help pr` and `gh -h pr merge` in cobra.
