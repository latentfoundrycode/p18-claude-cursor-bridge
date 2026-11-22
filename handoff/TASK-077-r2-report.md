# TASK-077 round 2 report

## Files changed

- `bridge/cursor-bridge/evaluate-reports.py`
- `bridge/cursor-bridge/pace-report.py`
- `bridge/cursor-bridge/MANIFEST.json` (regenerated)

## Summary

Round 2 rewrote the security scan path in `evaluate-reports.py` so every failed window run is logged, standing findings classify beside the week's kind and clear on a later success, alerts always run for remotes, and failed reads name the read and failure in printable ASCII. The projects file is always `~/.cursor-bridge/projects.json` (UTF-8 with BOM), git origin reads match pace-report hardening, and `pace-report.py` default roots use file order and folder basenames. All supervisor security tests and guard suites pass; CLI reference was already current after `dump-cli.py`.

## Rulings 1-16

- Ruling 1: `_run_exit_code` (794-856) reads jobs and logs for every window failure; `scan_project` (875-1024) sets standing from the newest exit-1 run beside the week's kind from `classify_window_runs` (823-838).
- Ruling 2: `classify_window_runs` (823-838) classifies the week first; `scan_project` (938-983) advances `last_run_read` and writes standing after classification.
- Ruling 3: `_standing_cleared` (774-791) clears standing when any later window run succeeded, comparing `last_run_read` when the standing run's time is unknown.
- Ruling 4: `_read_alerts` (859-872) runs after every branch with a remote; `scan_project` always calls it before return.
- Ruling 5: `_api_failure_phrase` (567-584), `_gh_api_include` (597-612), `_gh_paginate_json` (615-647), `_raw_failure_phrase` (557-564), and `format_security_section` (1037-1064) write `read failed: the <read>, <failure>` lines and keep scan kind beside alerts failures.
- Ruling 6: `printable_ascii` / `ascii_line` (453-471) and pace-report `_ascii_name` (153-165) escape all bytes outside 0x20-0x7E.
- Ruling 7: `projects_file_path` (413-414), `load_projects` (417-443), and `resolve_projects` (446-450) read only `~` with `utf-8-sig`; `pace-report` `_default_roots` (1337-1353) calls `load_projects()` without `--home`.
- Ruling 8: `_digit_id` (705-711), `_normalize_standing` (714-722), and run/job validation in `_validate_runs_list` (737-748) and `_validate_jobs_body` (751-762).
- Ruling 9: Validators and `_gh_paginate_json` (615-647) refuse unexpected JSON shapes without traceback.
- Ruling 10: `_validate_runs_list` (737-748) fails the runs read on bad `created_at` or missing conclusion.
- Ruling 11: `_completed_runs` (765-769) and `classify_window_runs` (823-838) sort and choose by parsed UTC time.
- Ruling 12: `dependency_workflow` (690-701) matches only paths ending in `/dependency-scan.yml`.
- Ruling 13: `github_repo_from_url` (488-496) with `_repo_segment_ok` (485-486) refuses dot-only owner/repo segments.
- Ruling 14: `git_origin_repo` (516-535) uses `_git_env` (499-513) and `-c core.fsmonitor=false`.
- Ruling 15: `_default_roots` (1337-1353) preserves projects-file order and basenames; `main` (1391-1394) prints projects refusal on stderr.
- Ruling 16: `scan_project` (917) keeps a single runs GET with `per_page=100`; disabled branch no longer carries an unused `update` key.

## R1-R16

- R1: `cmd_security` (1346-1416) and `build_parser` security subparser write `Reports/Evaluations/<date>/security.md` with GET-only reads named in the module docstring.
- R2: `load_projects` (417-443) is the sole reader; absent or malformed file exits 2 with a named line via `resolve_projects` callers.
- R3: `WORKSPACE_KEY_ONLY` and `project_keys` unchanged; no `PROJECTS` dict in scope files.
- R4: `git_origin_repo` (516-535) and `github_repo_from_url` (488-496) resolve GitHub origin or `no remote` without gh.
- R5: `scan_project` and helpers issue GET `gh api` reads in order (a)-(e); logs and alerts use `_gh_api_raw` where include/paginate/plain text require it.
- R6: Kinds and remedies come from `classify_window_runs`, `_run_exit_code`, and `format_security_section`; `green` only when kind is green without alerts failure.
- R7: Failed reads append `read_failures`; ledger skipped on (a)-(c) failure via `ledger_skip` in `scan_project` (1014-1017).
- R8: `log_exit_code` (653-659) and `EXIT_LINE_RX` (88) gate exit-line digits only.
- R9: `_read_alerts` and `_format_alerts` (846-856) name open alerts, off, or failures.
- R10: `format_security_section` (1037-1064) builds one non-empty section per project in printable ASCII.
- R11: `cmd_security` (1384-1415) updates `_meta.security` only after `security.md` is written; `scan_project` returns `None` update when `ledger_skip`.
- R12: Ledger replace after write in `cmd_security` (1411-1415); failed write path unchanged.
- R13: `parse_seed_security` (1067-1089) seeds by repository match.
- R14: Exit codes in `cmd_security` and `load_projects` refusal paths.
- R15: `_default_roots` and pace-report `main` refusal on stderr.
- R16: `tools/dump-cli.py` / `make-manifest.py` regeneration; `VERSION` unchanged.

## GitHub reads: `_gh_get` vs own call

- `bridge_env._gh_get`: workflows list (a), runs list (b), jobs list for each failed run (c). JSON bodies with standard success/failure mapping.
- `_gh_api_raw` (program): job logs (plain text, not JSON); `vulnerability-alerts` with `-i` (HTTP status 204/404/4xx); `dependabot/alerts` with `--paginate` (concatenated JSON arrays, empty-body guard). Used because `_gh_get` treats non-JSON success as failure and does not surface HTTP status lines for (d).

## D-004

The diagram at lines 198-202 shows projects roots from `ds_projects_file` and GitHub reads only. The built code also reads each project's `origin` URL via git in `git_origin_repo` (516-535) before any GitHub call; that local git flow is not drawn on the diagram.

## Test guard edits

none

## Commands and output

### 1. `git status --short`

```
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/evaluate-reports.py
 M bridge/cursor-bridge/pace-report.py
```

### 2. `python tools/make-manifest.py`

```
make-manifest: version 2026.11.12a, 148 files hashed, VERSION + MANIFEST.json written
```

### 3. `python tools/dump-cli.py`

```
(no stdout; exit 0)
```

### 4. `python -m pytest -p no:cacheprovider -q tests/test_program_security_step.py`

```
73 passed in 29.31s
```

### 5. `python -m pytest -p no:cacheprovider -q tests/test_evaluate_reports.py tests/test_pace_report.py`

```
12 passed in 6.00s
```

### 6. `python -m pytest -p no:cacheprovider -q tests/test_hotfix25a_loopguard_reports.py tests/test_task033_supervisor_r2.py tests/test_task033_supervisor.py`

```
139 passed, 1 skipped in 41.63s
```

### 7. `python -m pytest -p no:cacheprovider -q tests/test_dump_cli.py`

```
101 passed in 122.14s (0:02:02)
```

### 8. `python tools/dump-cli.py --check`

```
(exit 0, no stdout)
```

### 9. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`

```
bridge-check: version 2026.11.12a (2026-11-22 10:14) at <Workspace>\bridge
bridge-check: 148 OK, 0 STALE, 0 MISSING, 0 EXTRA
RESULT: SOURCES MATCH bridge 2026.11.12a <Workspace>\bridge\cursor-bridge
```

### 10. ASCII check

```
ascii ok
```

### 11. CRLF check

```
bridge/cursor-bridge/evaluate-reports.py bare LF 0
bridge/cursor-bridge/pace-report.py bare LF 0
```

### 12. `git diff -- bridge/cursor-bridge/VERSION`

```
(no output)
```

### 13. `git diff --stat`

```
 bridge/cursor-bridge/MANIFEST.json       |   6 +-
 bridge/cursor-bridge/evaluate-reports.py | 566 +++++++++++++++++++++++--------
 bridge/cursor-bridge/pace-report.py      |  21 +-
 3 files changed, 442 insertions(+), 151 deletions(-)
```

### 14. `git rev-parse HEAD` and `git status --short`

```
d8d6e4d34f6732a602645e0026c82220cf5ab9aa
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/evaluate-reports.py
 M bridge/cursor-bridge/pace-report.py
```

Results above are for commit `d8d6e4d34f6732a602645e0026c82220cf5ab9aa`; the working tree then held uncommitted changes in the three Scope files listed.

## Assumed, not verified

- How the installed `gh api -i` maps live 204/404 on `vulnerability-alerts` — fixtures drive tests — a capture against a real repo would confirm.
- That `gh api --paginate` on the real CLI concatenates pages as adjacent JSON arrays — paginate loop matches supervisor fixtures — side-by-side with real gh on an repo with multiple alert pages would confirm.
- That the logs endpoint redirect yields plain text to stdout on the real gh — success path uses fixture text — one live failed-job log read would confirm.
- Exact OAuth scope strings in `gh auth refresh -s` remedy lines — brief names repo scope — gh documentation for minimal Dependabot/actions scopes would confirm.
- How multiple failed jobs in one run combine when more than one carries an exit line — code takes the first failed job with a parsed exit line — a fixture with two failing jobs would confirm.
- Window when `_meta.last_extract` is absent for a project with no ledger entry — existing `run_in_window` / `security_runs_day` logic from round 1 — an integration run with empty `_meta` would confirm.
- Whether a disabled workflow's runs list is still returned if GitHub lists historical runs — code does not read (b) when state is not active — enabling the workflow on a test repo would confirm.
- One runs GET with `per_page=100` holds every run of a week (Ruling 16) — query uses `per_page=100` — a busier repo exceeding 100 weekly runs would confirm.