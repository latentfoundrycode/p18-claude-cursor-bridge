# TASK-072 round 1 report

## Files changed or created

- `bridge/cursor-bridge/conformance-check.py` (the weekly row, its readers, and the docstring)
- `bridge/cursor-bridge/MANIFEST.json` (rewritten by `python tools/make-manifest.py` in the Done list, not by hand)
- `handoff/TASK-072-r1-report.md` (this report)

No fixture was edited. `docs/BUILDER_NOTES.md` was not changed. No file under `.github/` was changed. `bridge/cursor-bridge/VERSION` is restored after the manifest rewrite and must not remain listed.

## Summary

`conformance-check.py` now prints one `Weekly dependency scan` row on every run that finishes `main()`: OK when some workflow with a `schedule:` trigger and an OSV-Scanner step has the same `--lockfile=` set as the workflows triggered by `push` or `pull_request`, NOTE when a Decisions cell begins `Weekly scan:` or the Workspace's own git configuration names no GitHub remote, and MISSING otherwise, saying which of the three failures it is. The module docstring lists that floor and the exits `main()` returns, including a malformed record header. This repository's weekly workflow and gate already match, so the row reads OK without any workflow edit.

## R1-R7

- R1. `weekly_dependency_scan` (lines 659-692) returns the verdict and detail, and `main` adds them once through `add` (lines 1483-1484) after the inventory sections are filled, including when `workflows` is empty. `--quiet` and a MISSING exit follow the existing print loop.
- R2. `_workflow_triggers` (lines 531-553) reads a top-level `on:` as a block of indented keys, as `on: push`, or as `on: [push, pull_request]` (names may be quoted). `_osv_lock_list` (lines 556-566) uses `workflow_steps` and the `OSV-Scanner` pattern from `SCANNERS` (`_OSV_STEP`, line 503). `_lock_token` (lines 507-511) keeps the text after `--lockfile=` up to whitespace and strips one matching quote pair. The gate list is the union of those values from workflows whose triggers include `push` or `pull_request` (lines 670-671); a weekly workflow is any scanned `.yml` or `.yaml` with an OSV-Scanner step and `schedule` (line 672). Comparison is `set(locks) == gate_set` (line 678). No file name is read.
- R3. On a matching set, lines 678-680 return OK with detail `pins, permissions and exit handling are not compared; a workflow disabled on GitHub is the evaluation's read`.
- R4. Otherwise `_weekly_decision_cell` (lines 575-582) returns the first Decisions cell that begins `Weekly scan:` (case-sensitive), and line 683 returns NOTE of that cell through `_escape_field`. Otherwise `_has_github_remote` (lines 630-650) is false and line 685 returns NOTE `the repository has no GitHub remote`. The remote is `git config --get-regexp` on this folder's own git dir only: `_own_git_dir` (lines 585-609) returns None when `Workspace/.git` is absent, so `git` is not run and a parent repository is not searched; a missing, unreadable, or failing git dir is no remote. The URL is not printed. No `gh` call was added.
- R5. Otherwise lines 686-692 return MISSING. No scheduled OSV workflow: `no workflow file runs OSV-Scanner on a schedule: trigger`. An OSV workflow that is not a `push` or `pull_request` workflow and has no `schedule`: `an OSV-Scanner workflow has no schedule: trigger`. A scheduled list that differs: `the lock files differ: the gate alone has <names>; the weekly scan alone has <names>`, each name through `_escape_field`, or `(none)` when that side is empty. OK detail: `pins, permissions and exit handling are not compared; a workflow disabled on GitHub is the evaluation's read`. Decision NOTE: the Decisions cell alone, passed through `_escape_field`. No-remote NOTE: `the repository has no GitHub remote`.
- R6. The "What it checks" list gains the weekly floor at lines 78-86 (triggers and the OSV-Scanner step, never a file name, with the OK, NOTE, and MISSING readings). The gate-workflow bullet and its file-name exclusion are unchanged. Line 87 names exit 0 (every floor present), exit 1 (at least one MISSING), and exit 2 (not a workspace, or a malformed record header, `HEADER MALFORMED`, the status file's or the inventory's). The docstring is ASCII.
- R7. No option, configuration key, environment variable, or dependency was added. Exits remain 0, 1, and 2. No `.github` file was edited. `test_this_repository_prints_the_weekly_row_ok` requires this Workspace's row to be OK.

## Fixture changes

none

## Mutation self-check

Each mutant was applied in `bridge/cursor-bridge/conformance-check.py`, then `python -m pytest -p no:cacheprovider -q tests/test_program_weekly_floor.py --tb=no` was run, then the edit was reverted. `--tb=no` was added so a failure trace would not print a temporary-folder path. After the M1 revert, `git diff --stat` showed only the feature edit. After each later revert, the file hash matched the hash taken at that point.

- M1 the surrounding quotes are not stripped from a `--lockfile=` value. `_lock_token` returned its argument unchanged. Caught by `test_ok_on_the_repository_like_pair`.

```
4 failed, 12 passed in 7.42s
```

- M2 the two lists are compared in order instead of as sets. `set(locks) == gate_set` was replaced by `locks == gate`. Caught by `test_ok_where_the_weekly_lists_two_lock_files_in_another_order`.

```
1 failed, 15 passed in 7.13s
```

- M3 the `Weekly scan:` Decisions row is not read. `_weekly_decision_cell` returned None immediately. Caught by `test_note_by_a_weekly_scan_decision_row_quoting_its_cell`.

```
1 failed, 15 passed in 6.99s
```

- M4 the `schedule:` trigger is not required of a weekly workflow (a `workflow_dispatch`-only workflow counts as weekly). The weekly test became `schedule` or `workflow_dispatch`. Caught by `test_missing_with_a_workflow_dispatch_only_scan`.

```
1 failed, 15 passed in 7.02s
```

- M5 the remote reading always answers "no GitHub remote". `_has_github_remote` returned False immediately. Caught by `test_missing_with_no_weekly_file_and_a_github_remote`.

```
3 failed, 13 passed in 7.01s
```

## Commands before the Done list

`python -m pytest -p no:cacheprovider -q tests/test_program_weekly_floor.py` (before the mutants):

```
................                                                         [100%]
16 passed in 6.94s
```

## Done commands

Run from `<Workspace>` after the last code edit, in order. Absolute paths printed by a command are written `<Workspace>` or `<tmp>` here. The counts belong to commit `72f8bd03cb0470ebe6b9d6e54129d7109cfb9d90`. At step 12 the working tree held uncommitted changes: `bridge/cursor-bridge/MANIFEST.json`, `bridge/cursor-bridge/conformance-check.py`, and `handoff/TASK-072-r1-report.md`. `bridge/cursor-bridge/VERSION` was not listed. No `.github` file was listed.

1. `git status --short`

```
 M bridge/cursor-bridge/conformance-check.py
?? handoff/TASK-072-r1-report.md
```

2. `python tools/make-manifest.py`

```
make-manifest: version 2026.11.12a, 148 files hashed, VERSION + MANIFEST.json written
```

3. `git restore bridge/cursor-bridge/VERSION` (run together with `git status --short`; restore printed no line)

```
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/conformance-check.py
?? handoff/TASK-072-r1-report.md
```

4. `python -m pytest -p no:cacheprovider -q -rs tests/test_program_weekly_floor.py tests/test_conformance_check.py tests/test_conformance_check_a4.py tests/test_diagram_check.py tests/test_bug042.py`

```
.............................................................            [100%]
61 passed in 25.85s
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
289 passed, 2 skipped in 78.76s (0:01:18)
```

6. `python -m pytest -p no:cacheprovider -q -rs tests/test_workflows_line_check.py tests/test_header_status.py tests/test_header_tables.py tests/test_header_tables_r2.py tests/test_header_currency.py tests/test_program_strip_names.py tests/test_loop_text_windowless.py tests/test_running_projects_classify.py`

```
.............................................ss......................... [ 14%]
........................................................................ [ 29%]
........................................................................ [ 44%]
........................................................................ [ 59%]
........................................................................ [ 73%]
........................................................................ [ 88%]
........................................................                 [100%]
=========================== short test summary info ===========================
SKIPPED [1] tests\test_workflows_line_check.py:496: cannot create a symbolic link here: [WinError 1314] A required privilege is not held by the client: '<tmp>' -> '<tmp>'
SKIPPED [1] tests\test_workflows_line_check.py:496: cannot create a symbolic link here: [WinError 1314] A required privilege is not held by the client: '<tmp>' -> '<tmp>'
486 passed, 2 skipped in 74.05s (0:01:14)
```

7. `python -m pytest -p no:cacheprovider -q -rs tests/test_dump_cli.py`. The expected failure is `tests/test_dump_cli.py::test_cfgb3b_committed_reference_is_current`: the docstring change makes the committed command reference stale. No other test in this file failed. The reference files were not regenerated.

```
.......................................F................................ [ 71%]
.............................                                            [100%]
================================== FAILURES ===================================
_________________ test_cfgb3b_committed_reference_is_current __________________

    def test_cfgb3b_committed_reference_is_current():
        """Criterion 10: the repository's own `--check` passes (the committed docs/cli-reference.json and
        docs/CLI_REFERENCE.md equal a fresh generation); conformance-check.py looks for this file's --check."""
        p = subprocess.run([sys.executable, str(GEN), "--check"], cwd=str(ROOT), capture_output=True, text=True,
                           encoding="utf-8", timeout=120)
>       assert p.returncode == 0, p.stdout + p.stderr
E       AssertionError: docs/cli-reference.json
E         docs/CLI_REFERENCE.md
E         
E       assert 1 == 0
E        +  where 1 = CompletedProcess(args=['<python>', '<Workspace>/tools/dump-cli.py', '--check'], returncode=1, stdout='docs/cli-reference.json\ndocs/CLI_REFERENCE.md\n', stderr='').returncode

tests\test_dump_cli.py:414: AssertionError
1 failed, 100 passed in 125.03s (0:02:05)
```

8. `python tools/dump-cli.py --check` (stale command reference, not regenerated)

```
docs/cli-reference.json
docs/CLI_REFERENCE.md
```

9. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`

```
bridge-check: version 2026.11.12a (2026-11-21 18:38) at <Workspace>\bridge
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
72f8bd03cb0470ebe6b9d6e54129d7109cfb9d90
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/conformance-check.py
?? handoff/TASK-072-r1-report.md
```

## Assumed, not verified

- When several scheduled OSV-Scanner workflows differ from the gate and none equals it, the detail names the first of those workflows in the sorted glob order, not a union of them. The brief says the weekly's lock files apart and does not say which file when there are several. A scratch project with two differing scheduled workflows would confirm which names appear.
- An OSV-Scanner workflow that has neither `push`, `pull_request`, nor `schedule` (for example `release` only, not only `workflow_dispatch`) is the "has no schedule: trigger" MISSING, and that message loses to a differing scheduled workflow when both exist. R5 names the dispatch-only case and the three messages, and does not rank a mix. A workflow triggered only by `release`, and one scheduled workflow that differs beside a dispatch-only workflow, would confirm the wording.
- A `.git` file is a worktree gitfile: the `gitdir:` token is passed to `git --git-dir`, and a missing line, a path that is not a directory, or a token that starts with `-` is no remote. The brief requires no crash and no parent search when `.git` is absent, and does not say how a gitfile is read. A worktree whose gitfile points at a GitHub remote, and a gitfile whose path contains a space, would confirm it.
- `Weekly scan:` is matched case-sensitively, and the first Decisions row in table order is the one quoted. The brief writes that exact prefix and says a row, not which row or which case. A cell `weekly scan:` and two `Weekly scan:` rows would confirm it.
- A remote URL counts as GitHub when its host is `github.com` or ends with `.github.com`, compared case-insensitively, including userinfo and the `git@host:path` form; a path that only contains the text `github.com` does not. The brief says a remote URL on github.com and does not give a host grammar. `git@github.com:owner/repo.git`, `https://user:token@github.com/owner/repo.git`, and `https://example.com/github.com/repo` would confirm it.
- A top-level `on:` written as a flow mapping (`on: {push: ...}`), a literal block (`on: |`), or a folded scalar is read as no triggers. The brief requires the block form and the inline forms `on: push` and `on: [push, pull_request]`. One workflow in each unsupported form would confirm the reading.
