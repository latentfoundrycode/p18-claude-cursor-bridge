# TASK-083 round 1 report

## Files changed

- `bridge/cursor-bridge/review-guard.py`
- `bridge/cursor-bridge/permission-guard.py`
- `bridge/cursor-bridge/MANIFEST.json` (by `python tools/make-manifest.py` only)
- `docs/cli-reference.json` (by `python tools/dump-cli.py` only)
- `docs/CLI_REFERENCE.md` (by `python tools/dump-cli.py` only)
- `docs/BUILDER_NOTES.md` (one dated line, written after step 10)
- `tests/test_permission_guard.py`
- `tests/test_review_guard.py`
- `tests/test_release_s_records_gate.py`
- `handoff/TASK-083-r1-report.md`

`bridge/cursor-bridge/VERSION` was restored with `git restore` after `make-manifest.py` and is not in the step 10 status. `docs/BUILDER_NOTES.md` and this report were written after step 10, so they are absent from that status.

## Summary

`review-guard.py ready <pr>` proves CI on the pull request's head through `bridge_env` (the base branch's required contexts, the default branch's where the base names none, or the workflow runs where neither names one), prints one READY, NOT READY or CANNOT CHECK line, and writes `<git common dir>/bridge/ready/<pr>-<head>` only on READY. `premerge-records <pr>` runs that same proof after its existing gate and writes the premerge record and the ready record together or neither. `permission-guard.py` refuses a `gh pr merge` that names no pull-request number, or that has no ready record for that number and the head it names, after the premerge check it already made.

## R1-R14

R1. `main` (line 1840) dispatches `ready` before the review-name grammar check (line 1853); any argument count other than one prints the usage and returns 2 (lines 1841-1843); an exception inside `ready` prints `review-guard: CANNOT CHECK - pull request <pr>: <reason>` and returns 2 (lines 1844-1849). The usage block is the docstring's second paragraph and gains `ready <pr>` at line 9, leaving `premerge-records [<pr>]` at line 8. The exits and the record are in the docstring at lines 82-87: `READY (exit 0)`, `NOT READY (exit 1)`, `CANNOT CHECK (exit 2)`, `bridge/ready/<pr>-<head>`. The old "CI is not checked" sentence is corrected in the module docstring (lines 66-68) and in `cmd_premerge_records`'s docstring (lines 1738-1740).

R2. `cmd_ready` (lines 1711-1713) accepts only one or more ASCII digits `0`-`9` and returns CANNOT CHECK before any `bridge_env` call otherwise. The number is kept as text in the record name (`_write_ready_record`, line 1519) and in the lines.

R3. `_premerge_stands` (lines 1488-1499) requires `<git common dir>/bridge/premerge/<head>` to be a readable JSON object for the local `git rev-parse HEAD`. Another head, a missing file, a non-object, or an unreadable folder is false, and `cmd_ready` (lines 1719-1721) answers CANNOT CHECK with the word `premerge`.

R4. `prove_ci` (lines 1643-1707) is the one proof. It calls `pull_refs`, `branch_rule`, `repo_settings` (only when the base names none), `head_state`, `latest_of_each` and `ci_class` on `bridge_env`, with the repository `"{owner}/{repo}"` and the checkout as `cwd`. It makes no `gh` call of its own. `_await_pull` (lines 1618-1640) re-reads while GitHub's head differs, sleeping `PR_HEAD_STEP` up to `PR_HEAD_WAIT`.

R5. `prove_ci` (lines 1654-1682) reads the base rule first and returns CANNOT CHECK when it cannot be read. A base that names contexts uses `the base branch's required contexts (<base>)`. A base that names none reads the default branch with `repo_settings` and returns CANNOT CHECK when that cannot be read. A different default branch's rule that cannot be read is CANNOT CHECK. A default branch that names contexts uses `the default branch's required contexts (<default>)`. Both none, or a default branch that is the base, uses `the workflow runs`. An unreadable rule never falls through to the runs.

R6. `_context_result` (lines 1563-1593) holds a context by the latest checks of that name, limited to the rule's `app_id` when the rule names one, and by the latest statuses of that context only when the rule names no app. No holder is `missing`, with `(a commit status carries no app)` when the rule names an app and a status of that name stands. A failed holder is `failed`, with `(neutral: stricter than GitHub)` when a failing check concluded `neutral`. A pending holder is `pending`. A skipped holder passes only when `_failure_beside` (lines 1552-1560) finds no failed latest check and no failed latest run; otherwise the context is `failed` with `(skipped beside a failure)`. A failed or pending status beside a passing check of a named app fails or pends the context (both must pass) and does not count as a holder that can pass it. READY only when every context passed (`prove_ci`, lines 1684-1704).

R7. `_runs_items` (lines 1596-1615) emits `run <name> (<event>): <class>` for each latest run that is pending or failed, `check <name>: failed` for each latest failed check, `status <context>: failed` for each latest failed status, and `no workflow run succeeded` when no latest run passed. A skipped run or check is not an item. READY only when the list is empty.

R8. `prove_ci` builds one line: READY (line 1706), NOT READY with the reading and the items (line 1704) or the head-moved line (lines 1651-1653), and CANNOT CHECK through `_cannot` (lines 1474-1475). A reader failure names `(<source>: <reason>)`; a rule uses `the base branch's rule cannot be read` or `the default branch's rule cannot be read` (`_rule_contexts`, lines 1524-1535).

R9. `_write_ready_record` (lines 1518-1521) writes the JSON object `pr`, `head`, `reading`, `written` at `bridge/ready/<pr>-<head>`. `cmd_ready` writes it only after exit 0 from `prove_ci` (lines 1723-1732); a write failure is CANNOT CHECK and the temporary file is removed (`_write_json`, lines 1501-1515). NOT READY and CANNOT CHECK return without writing or removing (lines 1723-1725). A record of another head or another pull request is a different file name and is left in place.

R10. `cmd_premerge_records` keeps SHORT GATE, FULL GATE, the head wait and its NOT READY line, and the earlier CANNOT CHECK answers. Only after those pass (line 1795) it calls `prove_ci`. READY prints that line and then writes the premerge record and the ready record (lines 1799-1816); if the ready write fails, the premerge file just written is removed and the answer is CANNOT CHECK. NOT READY or CANNOT CHECK from the proof prints that line and writes neither (lines 1796-1798). The OK line, the merge line and the auto-merge line stay, the auto-merge line last (lines 1817-1828). With no pull request number the command returns at line 1794, unchanged. `cmd_premerge` is untouched.

R11. `ready_recorded(pr, sha, cwd)` (lines 2451-2476) reads `<git common dir>/bridge/ready` the way `premerge_recorded` reads its folder, with `_time_left` and `git rev-parse --git-common-dir`, and is true when a name starts with `<pr>-<sha lower-cased>`. `merge_reason` (lines 2479-2515) keeps `--admin`, `--disable-auto`, `--help`/`-h` and `--match-head-commit` first, then takes the first word that is not an option and not a separate value of a flag in `GH_VALUE_FLAGS` (lines 2498-2510). No number, or a number that is not ASCII digits, is refused with a message holding `gh pr merge <n> --squash --match-head-commit <sha>`. Then `premerge_recorded` with its message unchanged (lines 2511-2512), then `ready_recorded` (lines 2513-2514), whose refusal names `review-guard.py ready <n>`. Unreadable hook input still fails open in `main`.

R12. `python tools/dump-cli.py` regenerated the command reference and `python tools/dump-cli.py --check` exited 0. `python tools/make-manifest.py` regenerated MANIFEST. `git restore bridge/cursor-bridge/VERSION` put the version file back; it reads `2026.11.12a`.

R13. The pinned cases were rewritten before the product change, and four cases were added: `test_r083_ready_recorded_fails_closed_outside_a_repository`, `test_r083_premerge_records_leaves_neither_record_when_the_ready_record_cannot_be_written`, `test_r083_ready_with_the_wrong_argument_count_prints_the_usage`, and `test_r083_an_exception_inside_ready_answers_cannot_check`. They drive the guard in process, or as the existing child-process helper, on the recorded replies through `use_standin` where GitHub is read.

R14. Each added case names `R-083` in its name or docstring. The parametrized usage case has `ids=["no argument", "two arguments"]`. The outside-a-repository case names D-003 `ready_recorded` in its docstring.

## Existing cases changed

- `recorded_repo` in `tests/test_permission_guard.py`: the fixture now also writes `.git/bridge/ready/12-<SHA>` beside `.git/bridge/premerge/<SHA>`. `test_a_merge_with_the_premerge_record_passes_and_one_without_is_refused` is otherwise unchanged, including the abbreviated-sha assertion.
- `test_premerge_and_the_permission_guard_agree_end_to_end` in `tests/test_review_guard.py`: after `premerge` prints the sha, the test writes `12-<sha>` under the repository's `.git/bridge/ready` before `allowed` is asked. Every assertion is unchanged, including the refusal outside the repository.
- `test_with_the_pull_request_the_record_is_written_and_the_permission_guard_lets_the_merge_through` in `tests/test_release_s_records_gate.py`: before `cmd_premerge_records(..., "12")`, the test installs `use_standin` and `ready_routes` from `tests/test_program_ready.py` for that head. Every assertion is unchanged.
- `test_a_lagging_head_is_read_again_and_one_that_still_differs_is_not_ready` in `tests/test_release_s_records_gate.py`: the same stand-in and routes, so the head that catches up is READY. Every assertion is unchanged.

## Mutation self-check

Each mutant was applied to the product file, the named test was run, and the file was restored before the next. All twenty-six were caught.

- M1 a missing context passed. Caught by `tests/test_program_ready.py::test_r083_not_ready_names_each_context_or_run_and_writes_nothing[S02 one required context missing]`.
- M2 a pending context passed. Caught by `tests/test_program_ready.py::test_r083_not_ready_names_each_context_or_run_and_writes_nothing[S03 one pending]`.
- M3 an earlier success taken beside a later failure. Caught by `tests/test_program_ready.py::test_r083_not_ready_names_each_context_or_run_and_writes_nothing[S16 an earlier success, a later check of the same source failed]`.
- M4 a skipped context passed beside a failure. Caught by `tests/test_program_ready.py::test_r083_not_ready_names_each_context_or_run_and_writes_nothing[S11 a required context skipped beside a failure]`.
- M5 a skipped context failed beside a superseded cancelled run. Caught by `tests/test_program_ready.py::test_r083_ready_proves_ci_writes_the_ready_record_and_names_its_reading[S27 a required context skipped beside a cancelled run its successor replaced]`.
- M6 a superseded cancelled run counted. Caught by `tests/test_program_ready.py::test_r083_ready_proves_ci_writes_the_ready_record_and_names_its_reading[S09 a cancelled run beside its successor]`.
- M7 the statuses not read. Caught by `tests/test_program_ready.py::test_r083_ready_proves_ci_writes_the_ready_record_and_names_its_reading[S17 a required context held by a commit status]`.
- M8 a neutral context passed. Caught by `tests/test_program_ready.py::test_r083_not_ready_names_each_context_or_run_and_writes_nothing[S20 a required context concluded neutral]`.
- M9 a timed-out check not counted as failed. Caught by `tests/test_program_ready.py::test_r083_not_ready_names_each_context_or_run_and_writes_nothing[S23 a check timed out beside a skipped required context]`.
- M10 a run that failed at its start not counted as failed. Caught by `tests/test_program_ready.py::test_r083_not_ready_names_each_context_or_run_and_writes_nothing[S24 a run failed at its start beside one that succeeded]`.
- M11 another app's check taken. Caught by `tests/test_program_ready.py::test_r083_not_ready_names_each_context_or_run_and_writes_nothing[S21 a rule naming an app, the check of that name from another app]`.
- M12 a status taken for a named app's check. Caught by `tests/test_program_ready.py::test_r083_not_ready_names_each_context_or_run_and_writes_nothing[S22 a rule naming an app, a commit status of that name]`.
- M13 a replaced run's check counted. Caught by `tests/test_program_ready.py::test_r083_not_ready_names_each_context_or_run_and_writes_nothing[S25 a replaced run's check still running, its successor's failed]`.
- M14 a later page unread. Caught by `tests/test_program_ready.py::test_r083_a_list_of_two_pages_whose_second_holds_a_failed_run_is_not_ready`.
- M15 the head not compared. Caught by `tests/test_program_ready.py::test_r083_the_head_moved_is_not_ready_and_writes_nothing`.
- M16 cannot read taken as ready. Caught by `tests/test_program_ready.py::test_r083_cannot_check_where_github_a_rule_or_the_pull_request_cannot_be_read[S26 the base's rule cannot be read beside a head all green]`.
- M17 an unreadable rule answered from the runs. Caught by `tests/test_program_ready.py::test_r083_cannot_check_where_github_a_rule_or_the_pull_request_cannot_be_read[S26 the base's rule cannot be read beside a head all green]`.
- M18 a queued run passed. Caught by `tests/test_program_ready.py::test_r083_not_ready_names_each_context_or_run_and_writes_nothing[S07 a queued workflow beside two green app checks]`.
- M19 a base with no run passed. Caught by `tests/test_program_ready.py::test_r083_not_ready_names_each_context_or_run_and_writes_nothing[S15 no run at all]`.
- M20 the record written on NOT READY. Caught by `tests/test_program_ready.py::test_r083_not_ready_names_each_context_or_run_and_writes_nothing[S02 one required context missing]`.
- M21 the merge allowed without the ready record. Caught by `tests/test_program_ready.py::test_r083_a_merge_without_its_ready_record_is_refused_naming_ready[no ready record-Bash]`.
- M22 the ready record of another head accepted. Caught by `tests/test_program_ready.py::test_r083_a_merge_without_its_ready_record_is_refused_naming_ready[another head's-Bash]`.
- M23 the ready record of another pull request accepted. Caught by `tests/test_program_ready.py::test_r083_a_merge_without_its_ready_record_is_refused_naming_ready[another pull request's-Bash]`.
- M24 the default branch's contexts not read. Caught by `tests/test_program_ready.py::test_r083_not_ready_names_each_context_or_run_and_writes_nothing[S13 the gate's check missing on a base with no rule while another workflow succeeded]`.
- M25 a merge with no number allowed. Caught by `tests/test_program_ready.py::test_r083_a_merge_that_names_no_number_is_refused_with_the_form[gh pr merge --squash --match-head-commit 0123456789abcdef0123456789abcdef01234567-Bash]`.
- M26 `premerge-records` writing the premerge record where CI is not proven. Caught by `tests/test_program_ready.py::test_r083_premerge_records_writes_neither_record_where_ci_is_not_proven[not ready]`.

## Commands

The counts below belong to commit `46470b8a5b48998e51250b79ea7fc2dee368db42`. At step 10 the working tree held uncommitted changes, listed in that step's status. `docs/BUILDER_NOTES.md` and this report were written after that status.

### 1. `git status --short`

```
 M bridge/cursor-bridge/permission-guard.py
 M bridge/cursor-bridge/review-guard.py
 M tests/test_permission_guard.py
 M tests/test_release_s_records_gate.py
 M tests/test_review_guard.py
```

### 2. `python tools/dump-cli.py`

The command printed no lines and the shell exit was 0.

```
```

### 3. `python tools/dump-cli.py --check`

The command printed no lines and the shell exit was 0.

```
```

### 4. `python tools/make-manifest.py`

```
make-manifest: version 2026.11.12a, 146 files hashed, VERSION + MANIFEST.json written
```

### 5. `git restore bridge/cursor-bridge/VERSION`

The command printed no lines and the shell exit was 0. The file then read:

```
2026.11.12a
```

### 6. `python -m pytest -p no:cacheprovider -q tests/test_program_ready.py tests/test_d003_review_round_states.py tests/test_permission_guard.py tests/test_allowlist.py tests/test_program_branch_rule.py tests/test_program_release_s_rows.py tests/test_review_guard.py tests/test_release_s_records_gate.py tests/test_permission_guard_a4.py`

```
........................................................................ [  6%]
........................................................................ [ 13%]
........................................................................ [ 20%]
........................................................................ [ 26%]
........................................................................ [ 33%]
......................................................s...ss.....sss.... [ 40%]
................s...............s....................................... [ 46%]
........s...........s.................s...ss.....sss.................... [ 53%]
s...............s...............................................s....... [ 60%]
....s................................................................... [ 66%]
........................................................................ [ 73%]
........................................................................ [ 80%]
........................................................................ [ 86%]
........................................................................ [ 93%]
....................................................................     [100%]
1056 passed, 20 skipped in 287.27s (0:04:47)
```

The command as specified does not print the skipped node ids. The `s` marks are the twenty skips.

### 7. `python -m pytest -p no:cacheprovider -q tests/test_program_permission_guard.py tests/test_tests_windowless.py`

```
........................................................................ [ 11%]
........................................................................ [ 23%]
........................................................................ [ 35%]
........................................................................ [ 47%]
........................................................................ [ 59%]
........................................................................ [ 71%]
........................................................................ [ 82%]
........................................................................ [ 94%]
................................                                         [100%]
608 passed in 57.07s
```

### 8. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`

```
bridge-check: version 2026.11.12a (2026-11-17 00:14) at <Workspace>\bridge
bridge-check: 146 OK, 0 STALE, 0 MISSING, 0 EXTRA
RESULT: SOURCES MATCH bridge 2026.11.12a
```

### 9. `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks`

```
windowless-check: 39 file(s) scanned, 0 FAIL, 0 NOTE
```

### 10. `git rev-parse HEAD` and `git status --short`

```
46470b8a5b48998e51250b79ea7fc2dee368db42
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/permission-guard.py
 M bridge/cursor-bridge/review-guard.py
 M docs/CLI_REFERENCE.md
 M docs/cli-reference.json
 M tests/test_permission_guard.py
 M tests/test_release_s_records_gate.py
 M tests/test_review_guard.py
```

`bridge/cursor-bridge/VERSION` is not listed.

## Assumed, not verified

- Real `gh` resolves the path `repos/{owner}/{repo}/...` from the checkout's remote the way the stand-in's placeholders do. · `prove_ci` uses the same `"{owner}/{repo}"` string `cmd_premerge` already passes to `repo_settings`, and every acceptance case answers it through the stand-in. · A capture of `gh api repos/{owner}/{repo}` run in a checkout whose remote is this repository, which this round does not run.
- A pending commit status of a context whose rule names an app, beside a passing check of that app, makes the context pending. · No recorded reply has that pair. A failed status beside a passing check is S18 and is NOT READY, and a passing status with no matching check is S22 and is missing, so a pending status was given the same "both must pass" place as the failed one. · A recorded head with a pending status and a successful check of a named-app context.
- The ready record's `written` value is local `time.strftime("%Y-%m-%dT%H:%M:%S")` with no `Z`, the same call the premerge record already uses. · The brief names the key and not the clock. · A test that reads the `written` field, which none of the acceptance cases do.
- GitHub's head sha and the local `HEAD` are compared as exact strings, so an uppercase sha from GitHub would be reported as the head having moved. · The recorded shas and `git rev-parse` are lowercase hex. · A recorded pull request whose head sha is the same commit in uppercase.
- A `branch_rule` answer of `value` with an empty `contexts` list is CANNOT CHECK, not the runs reading. · The reader returns `none` when the merged list is empty, so this branch is only a fail-closed guard for a shape the reader does not produce. · A unit of `branch_rule` that returned `value` with `contexts: []`, which the recorded replies do not.
