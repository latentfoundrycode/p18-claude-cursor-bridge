# TASK-077 round 1 report

## Files changed

- bridge/cursor-bridge/evaluate-reports.py
- bridge/cursor-bridge/pace-report.py
- bridge/cursor-bridge/MANIFEST.json (regenerated)
- docs/cli-reference.json (regenerated)
- docs/CLI_REFERENCE.md (regenerated)
- handoff/TASK-077-r1-report.md

## Summary

The bridge evaluation program gained a `security` subcommand that performs GET-only `gh api` reads per project (workflow, runs, failed job logs, vulnerability-alerts, open Dependabot alerts), writes `Reports/Evaluations/<date>/security.md`, and updates `_meta.security` in the ledger only after a successful write. Hard-coded project roots were removed; `collect`, `record`, `seed`, `extract`, `security`, and `pace-report.py` with no roots now read `~/.cursor-bridge/projects.json` via `load_projects`. All 36 supervisor security acceptance tests and the listed guard and fixed tests pass; CLI reference and manifest were regenerated.

## Requirements R1–R16

- R1: `build_parser` adds fifth subparser `security` with `--date` and `--seed-from`; `cmd_security` writes `Reports/Evaluations/<date>/security.md` under `bridge_root()`.
- R2: `load_projects`, `resolve_projects`, `projects_file_path`; refusal lines name `PROJECTS_FILE_LABEL`; exit 2 when absent or malformed; all affected commands call `resolve_projects`.
- R3: `PROJECTS` dict removed; `project_keys` compares roots to `bridge_root()` with `normcase`/`abspath`; `WORKSPACE_KEY_ONLY` unchanged.
- R4: `git_origin_repo` reads `origin` windowlessly; `github_repo_from_url` validates owner/repo; `no remote` sections skip `gh`.
- R5: `scan_project` uses `bridge_env._gh_get` for workflows, runs, jobs; `_gh_api_raw`, `_gh_api_include`, `_gh_paginate_json` for logs, alerts enablement, and paginated alerts.
- R6: `classify_window_runs`, log `EXIT_LINE_RX` / `log_exit_code`, and `format_security_section` emit the defined kinds and remedies.
- R7: Failed reads become `finding` sections with `read_failure_remedy`; ledger entry left unchanged when `update` is `None`.
- R8: `log_exit_code` keeps only the timestamped `dependency-scan: OSV-Scanner exit <digits>` line; log text does not enter `security.md`.
- R9: Open alerts listed by number, package, GHSA; `No open Dependabot alert.` when none; `alerts off` on 404 for vulnerability-alerts.
- R10: `format_security_section` and `cmd_security` build one ASCII section per project with required fields.
- R11: `_meta.security` entries hold `last_run_read` and `finding_standing`; `run_in_window` and `security_runs_day` implement the window.
- R12: `save_ledger` runs only after `security.md` is written; write failure returns 1 with ledger unchanged.
- R13: `parse_seed_security` and seeding in `cmd_security` before the scan loop.
- R14: `cmd_security` exit 0 on write, 2 for usage/projects/`--seed-from` read failure, 1 on write error; docstring exit list updated.
- R15: `pace-report.py` `_default_roots` calls `er.load_projects`; exit 2 on refusal; docstring and `roots` help updated.
- R16: Regenerated `docs/cli-reference.json`, `docs/CLI_REFERENCE.md`, and `MANIFEST.json` via the required tools.

## D-004

- The code reads each project's GitHub `OWNER/REPO` from `git remote get-url origin` on `<root>/Workspace` before any `gh api` call. D-004 lines 198–202 draw no such flow from the Workspace git configuration to `p_evaluate_reports`.
- Otherwise: projects come from `ds_projects_file`, GET-only GitHub reads, output to `security.md` and ledger `_meta.security` only.

## Edits to run-only guards

none

## Verification commands

```
git status --short
```
```
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/evaluate-reports.py
 M bridge/cursor-bridge/pace-report.py
 M docs/CLI_REFERENCE.md
 M docs/cli-reference.json
```

```
python tools/make-manifest.py
```
```
make-manifest: version 2026.11.12a, 148 files hashed, VERSION + MANIFEST.json written
```

```
python tools/dump-cli.py
```
```
(no output)
```

```
python -m pytest -p no:cacheprovider -q tests/test_program_security_step.py
```
```
....................................
36 passed in 12.42s
```

```
python -m pytest -p no:cacheprovider -q tests/test_evaluate_reports.py tests/test_pace_report.py
```
```
............
12 passed in 5.16s
```

```
python -m pytest -p no:cacheprovider -q tests/test_hotfix25a_loopguard_reports.py tests/test_task033_supervisor_r2.py tests/test_task033_supervisor.py
```
```
.........s.............................................................. [ 51%]
....................................................................
139 passed, 1 skipped in 42.39s
```

```
python -m pytest -p no:cacheprovider -q tests/test_dump_cli.py
```
```
........................................................................ [ 71%]
.............................
101 passed in 120.40s (0:02:00)
```

```
python tools/dump-cli.py --check
```
```
(exit code 0, no output)
```

```
python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet
```
```
bridge-check: version 2026.11.12a (2026-11-22 09:51) at <Workspace>/bridge
bridge-check: 148 OK, 0 STALE, 0 MISSING, 0 EXTRA
RESULT: SOURCES MATCH bridge 2026.11.12a <Workspace>/bridge/cursor-bridge
(exit code 0)
```

```
python -c "[open(p,'rb').read().decode('ascii') for p in ('bridge/cursor-bridge/evaluate-reports.py','bridge/cursor-bridge/pace-report.py')]; print('ascii ok')"
```
```
ascii ok
```

```
python -c "import sys; [print(p, 'bare LF', d.count(b'\n')-d.count(b'\r\n')) for p in ('bridge/cursor-bridge/evaluate-reports.py','bridge/cursor-bridge/pace-report.py') for d in [open(p,'rb').read()]]"
```
```
bridge/cursor-bridge/evaluate-reports.py bare LF 0
bridge/cursor-bridge/pace-report.py bare LF 0
```

```
git diff -- bridge/cursor-bridge/VERSION
```
```
(no output)
```

```
git diff --stat
```
```
 bridge/cursor-bridge/MANIFEST.json       |   6 +-
 bridge/cursor-bridge/evaluate-reports.py | 548 +++++++++++++++++++++++++++++--
 bridge/cursor-bridge/pace-report.py      |  23 +-
 docs/CLI_REFERENCE.md                    |  10 +-
 docs/cli-reference.json                  |  46 ++-
 5 files changed, 597 insertions(+), 36 deletions(-)
```

```
git rev-parse HEAD
```
```
66e34c9ba1117d03d0b4b94d4370017457512279
```

```
git status --short
```
```
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/evaluate-reports.py
 M bridge/cursor-bridge/pace-report.py
 M docs/CLI_REFERENCE.md
 M docs/cli-reference.json
```

Results are for commit `66e34c9ba1117d03d0b4b94d4370017457512279` with uncommitted changes in the files above (report file unlisted until saved).

## Assumed, not verified

- `_gh_api_include` with `-i` is how production `gh api` exposes HTTP 204 vs 404 for `vulnerability-alerts` — tests use the stand-in's `HTTP/2.0` status line — a live GET with and without `-i` on a repo with alerts on and off.
- Non-zero `gh` exit on 403/connection errors combined with JSON body is what production returns — fixtures use `gh_exit` and stderr — comparing stand-in to one refused live read.
- `gh api --paginate` prints concatenated JSON arrays without `--slurp` — `_gh_paginate_json` parses with `JSONDecoder.raw_decode` — capture stdout from a repo with more than one page of open alerts.
- `gh auth refresh -s repo` is the scope named for actions reads and for alerts reads in remedies — GitHub docs for the scopes `gh api` needs for each path.
- Several failed jobs in one run: only the first failed job's log is read for an exit line — minimal code — behavior when multiple failed jobs each have exit lines.
- When `_meta.last_extract` is absent and a project has no security entry, `run_in_window` treats all listed runs as in the window — brief allows choice — ledger with no `last_extract` and empty `_meta.security`.
- A disabled `dependency-scan` workflow: runs list (b) is not fetched; kind is `no completed run` from workflow state alone — brief allows choice — enable workflow and compare API run list to an active repo.