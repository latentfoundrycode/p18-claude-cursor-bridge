# TASK-072 round 1 report

## Files changed or created

- `bridge/cursor-bridge/conformance-check.py` (weekly row helpers, docstring, MANIFEST-driving logic in `main()`)
- `bridge/cursor-bridge/MANIFEST.json` (regenerated)

## Summary

Added the `Weekly dependency scan` conformance row: workflows are classified by triggers and OSV-Scanner steps (not file names), lock files are compared as sets with quote stripping, and verdicts follow OK / NOTE (Decisions `Weekly scan:` or no GitHub remote from local git config only, with link and include hardening) / MISSING (no scheduled scan, dispatch-only scan, or differing lists). The module docstring now documents the floor and all three exit codes. Acceptance and related tests pass; `docs/cli-reference.json` is stale as expected from the docstring change.

## R1-R7

- R1: `_add_weekly_dependency_scan` (879-910) adds exactly one row named `Weekly dependency scan` via `add` before the summary; called from `main()` at 1598-1599.
- R2: `_workflow_triggers` (736-781) reads bare, quoted, block and inline-list `on:` forms (direct children of block `on:` only); `_osv_lockfiles` (790-796) unions `--lockfile=` from OSV steps; gate locks in `main()` (1031-1044) from workflows with `push` or `pull_request`; scheduled lists from workflows with `schedule`.
- R3: `_add_weekly_dependency_scan` (880-884) sets OK when a scheduled lock set equals `gate_locks`, with `not compared` and `disabled` in the detail.
- R4: NOTE for Decisions via `_weekly_scan_decision` (872-876) quoting through `_escape_field`; else `_has_github_remote` (847-869) with `_own_git_dir` (813-844), `--local --no-includes`, stripped `GIT_CONFIG*`, no URL printed, NOTE detail `the repository has no GitHub remote`.
- R5: MISSING details — (1) `no workflow file runs OSV-Scanner on a \`schedule:\` trigger` (909-910); (2) `a workflow runs OSV-Scanner but has no \`schedule:\` trigger` (905-907); (3) gate-only and weekly-only lock names in 893-903; NOTE OK detail as in R3; NOTE decision and no-remote as in R4.
- R6: Docstring lines 15-20 (weekly floor) and 84-85 (exits 0/1/2 including malformed header).
- R7: No new options or dependencies; `python tools/make-manifest.py` run; this repository's weekly row OK under `test_this_repository_prints_the_weekly_row_ok`.

## Fixture changes

none

## Mutation self-check

- M1 (quotes not stripped): `1 failed in 1.76s` — `tests/test_program_weekly_floor.py::test_ok_on_the_repository_like_pair`
- M2 (lists compared in order instead of sets): applied mutant `len(locks) == len(gate_locks)` only; `1 failed in 11.15s` — `tests/test_program_weekly_floor.py::test_missing_with_a_scheduled_scan_whose_list_differs` (earlier mutants `list(locks)==list(gate_locks)` and `",".join` did not fail on this host because equal sets iterated identically)
- M3 (`Weekly scan:` not read): `1 failed in 0.92s` — `tests/test_program_weekly_floor.py::test_note_by_a_weekly_scan_decision_row_quoting_its_cell`
- M4 (`schedule:` not required): `1 failed in 0.90s` — `tests/test_program_weekly_floor.py::test_missing_with_a_workflow_dispatch_only_scan`
- M5 (remote always no GitHub): `1 failed in 0.89s` — `tests/test_program_weekly_floor.py::test_missing_with_no_weekly_file_and_a_github_remote`

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
........................................................................ [100%]
72 passed in 27.08s
```

### 5. `python -m pytest -p no:cacheprovider -q -rs tests/test_hotfix25a_conformance_semgrep.py tests/test_a4_followups.py tests/test_a4_review_fixes.py tests/test_b2_least_confident.py tests/test_program_branch_rule.py tests/test_calibrate_program.py tests/test_conformance_windowless.py`

```
289 passed, 2 skipped in 71.89s (0:01:11)
```

### 6. `python -m pytest -p no:cacheprovider -q -rs tests/test_workflows_line_check.py tests/test_header_status.py tests/test_header_tables.py tests/test_header_tables_r2.py tests/test_header_currency.py tests/test_program_strip_names.py tests/test_loop_text_windowless.py tests/test_running_projects_classify.py`

```
486 passed, 2 skipped in 69.38s (0:01:09)
```

### 7. `python -m pytest -p no:cacheprovider -q -rs tests/test_dump_cli.py`

```
1 failed, 100 passed in 123.20s (0:02:03)
```

Expected failure only:

```
FAILED tests/test_dump_cli.py::test_cfgb3b_committed_reference_is_current
```

### 8. `python tools/dump-cli.py --check`

```
docs/cli-reference.json
docs/CLI_REFERENCE.md
```

### 9. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`

```
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
b21984cbe7c19fb25169ec49d1c9fc5538f5df05
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/conformance-check.py
 M handoff/TASK-072-r2.md
 M handoff/TASK-072-r3.md
 M handoff/TASK-072.md
```

`bridge/cursor-bridge/VERSION` not listed. No `.github` file modified.

Results above belong to commit `b21984cbe7c19fb25169ec49d1c9fc5538f5df05` with uncommitted changes as shown.

## Expected stale command reference

`tests/test_dump_cli.py::test_cfgb3b_committed_reference_is_current` fails because the module docstring changed and `docs/cli-reference.json` / `docs/CLI_REFERENCE.md` are out of scope for this increment.

## Assumed, not verified

- A workflow triggered by both `push` and `schedule:` on one file counts toward both gate and scheduled weekly sets · the brief does not define dual-trigger files · a dedicated fixture with one file carrying both triggers
- Empty gate lock set and empty weekly lock set are equal for OK · both sides absent of `--lockfile=` could mean match · fixture with no OSV lock args on either side
- When several scheduled workflows differ from the gate, MISSING list detail uses the first scheduled entry in sorted workflow path order · only `scheduled_locks[0]` is read · multi-file fixture with two mismatched scheduled workflows
- `--lockfile` with a space instead of `=` is ignored · regex requires `=` · workflow using space form only
- `Weekly scan:` Decisions match is case-sensitive · code uses `startswith("Weekly scan:")` · inventory row with different casing