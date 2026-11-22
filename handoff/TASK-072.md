---
record: brief
header: 1
id: "TASK-072"
round: 1
satisfies: [R-092]
scope: ["bridge/cursor-bridge/conformance-check.py", "bridge/cursor-bridge/MANIFEST.json", "tests/test_program_weekly_floor.py", "tests/test_conformance_check.py", "tests/test_conformance_check_a4.py", "tests/test_diagram_check.py", "tests/fixtures/", "docs/BUILDER_NOTES.md", "handoff/TASK-072-r1-report.md"]
merge_unit: null
blocking_class: null
---
# TASK-072: The conformance check knows the weekly scan (R-092)

Round cause: first round (no earlier round)

## Objective
`bridge/cursor-bridge/conformance-check.py` reports, per floor, OK, MISSING or NOTE for a project's configuration. Every project receives a second workflow beside its gate, the weekly dependency scan (`.github/workflows/dependency-scan.yml` in this repository): an OSV-Scanner run on a `schedule:` trigger over the same lock files the gate scans. Today the check prints no row for it, so a project that lacks the weekly scan, or whose weekly scan reads other lock files than the gate, passes unseen. This increment adds one row, `Weekly dependency scan`, which finds the weekly workflow by its triggers and its steps (never by a file name), compares its `--lockfile=` values with the gate's as sets, and reads OK, NOTE or MISSING by the rulings below. It also makes the module docstring true: the new floor in its "What it checks" list, and its exit line naming every exit `main()` returns (J14). This repository's own run must print the new row OK.

Satisfies: R-092 - The conformance check knows the weekly dependency scan (C12, C10): rows for the weekly workflow, the file present, a `schedule:` trigger, its `--lockfile=` list equal to the gate's OSV-Scanner step's; a NOTE without a GitHub remote or with an inventory Decisions row that begins `Weekly scan:`, otherwise MISSING for a missing file or a differing list; the configurator's text names that row's opening words; a diagram index with every kind omitted passes `diagram-check.py`'s three modes and the conformance check, held by tests; the check's docstring lists its exits as the code has them (J14). (Its row in `docs/REQUIREMENTS.md` is line 118. This brief serves the row, the docstring and this repository's run. The configurator's text belongs to the supervisor, not to this brief. The diagram half is held by four tests in the acceptance file that already pass.)

## Scope
Files and directories you may create or modify:
- bridge/cursor-bridge/conformance-check.py
- bridge/cursor-bridge/MANIFEST.json
- tests/test_program_weekly_floor.py
- tests/test_conformance_check.py
- tests/test_conformance_check_a4.py
- tests/test_diagram_check.py
- tests/fixtures/
- docs/BUILDER_NOTES.md
- handoff/TASK-072-r1-report.md

Limits on these paths:
- `tests/test_program_weekly_floor.py`: the supervisor's acceptance tests, committed at HEAD (16 cases). Read it whole and run it. **Do not edit it.** If a case seems wrong, stop and report it by its test id.
- `tests/test_conformance_check.py`, `tests/test_conformance_check_a4.py`, `tests/fixtures/` (the plan's Scope notes): "the conformant fixtures gain the weekly file or have no remote, so that every existing conformance test stays green, each changed fixture named in the report". The supervisor's reality check (Context) found no existing case that the new row turns red, so no edit is expected. Edit a fixture only if a case in them goes red because of the new row, and only that fixture: give it the weekly file or leave it without a remote. Name each such change in the report with the test id, why, and the diff.
- `tests/test_diagram_check.py`: the plan lists it for the diagram half. This brief asks no change to it. Run it (Done, command 6).
- `bridge/cursor-bridge/MANIFEST.json` changes only by running `python tools/make-manifest.py` (Done), never by hand. `bridge/cursor-bridge/VERSION` is outside Scope. `make-manifest.py` rewrites its line endings, so restore it with `git restore bridge/cursor-bridge/VERSION` right after (Done).

Do not modify anything else.

## Out of scope
- .env and anything under secrets/
- CI configuration: **every file under `.github/`**, `dependency-scan.yml` and `tests.yml` included. This repository's run must turn OK by your code, never by editing a workflow.
- docs/ and handoff/, except the files the Scope section names. Every record under docs/ is the supervisor's.
- `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` (see Context, "The command reference"). Do not regenerate them.
- Every other program under `bridge/cursor-bridge/` (`bridge_env.py` and `diagram-check.py` included), the texts under `bridge/commands/`, `bridge/agents/` (the configurator's text, which R-092 also names, is the supervisor's) and `bridge/cursor-bridge/workflow/`, and `bridge/cursor-bridge/CHANGELOG.md`.
- `tools/make-manifest.py` and `tools/dump-cli.py`: you run them and edit neither.
- Every test file not named in Scope. Those named in the Done list's commands must pass unedited (one known exception, Context, "The command reference"). Report a failure there by its test id.
- `run/` (the supervisor's working files; you may read them and write nothing there).
- Any mutation script or mutants file. The mutants file and the mutation run are the supervisor's, after your run.
- Recorded as leads, not built in this increment: (1) the existing gate reader still excludes `dependency-scan.yml` / `.yaml` by file name, so a weekly workflow named otherwise is still read by the gate reader as gate steps; do not change that (ruling 4). (2) Precedence where a `Weekly scan:` Decisions row and a matching weekly workflow both exist (OK wins by ruling 3) is not tested by the acceptance file; implement the order, add no test for it.

## Context
**The design that binds this increment.** `docs/DESIGN.md` line 358, the bullet `*C12 and C10.*`: "`conformance-check.py` gains rows for the weekly dependency scan: the file present, a `schedule:` trigger, its `--lockfile=` list equal to the gate's OSV-Scanner step's. Without a GitHub remote, or with an inventory Decisions row that begins `Weekly scan:` (the recorded reason the configurator's stop asks for), the row is a NOTE; otherwise a missing file or a differing list is MISSING. Pins and permissions are not compared, the text leaving a block change to the project's next configuration touch. A diagram index with every kind omitted already passes both programs; C10 adds the regression tests that hold it." The plan entry is `docs/BUILD_PLAN.md`, `### TASK-072` (line 1914). Its Done when: "`conformance-check.py` prints one row for the weekly dependency scan: `OK` where a workflow file under `.github/workflows/` carries a `schedule:` trigger and an OSV-Scanner step whose `--lockfile=` list equals, as a set, the gate workflow's OSV-Scanner step's; `NOTE` where the repository has no GitHub remote, read from the local configuration alone, or where the inventory's Decisions holds a row whose first cell begins `Weekly scan:`, the note quoting that cell; `MISSING` where the file is absent, has no `schedule:` trigger, or its list differs, the row saying which and naming the lock files apart; pins, permissions and exit handling are not compared, and a workflow disabled on GitHub is the evaluation's read, both said in the row's text; the row is found by the steps' own commands, never by a file name, so a project that names its workflow otherwise passes; a diagram index with every kind omitted, each with its reason, passes `diagram-check.py --mode design`, `--mode code` and `--mode done` and the conformance check's diagram floor, held by four tests that are green on the checkpoint (the design found main right; the tests hold it); `tests/test_program_weekly_floor.py` names R-092; the check's docstring lists its exits as the code has them (J14); this repository's own conformance run prints the new row `OK`; MANIFEST regenerated; no option added; no new dependency."

**The supervisor's rulings (they bind; R1-R7 restate them).**
1. The new row is named exactly `Weekly dependency scan`, printed once per run, in the program's usual row form (`  <STATUS>  Weekly dependency scan  - <detail>`).
2. Workflows are told apart by their triggers and steps, never by a file name. The gate set is the union of the OSV-Scanner `--lockfile=` values in workflows triggered by `pull_request` or `push`. A weekly workflow is any file under `.github/workflows/` (`.yml` or `.yaml`) with an OSV-Scanner step and a `schedule:` trigger. One pair of surrounding quotes (single or double, matching) is stripped from each value, and the lists are compared as sets.
3. Order: OK if some weekly workflow's set equals the gate set; its detail says that pins, permissions and exit handling are not compared and that a workflow disabled on GitHub is the evaluation's read (the tests look for the words `not compared` and `disabled`). Otherwise NOTE where the inventory's Decisions (`docs/INVENTORY.md`) holds a row whose first cell begins `Weekly scan:`, the note quoting that cell. Otherwise NOTE where the repository has no GitHub remote, read from the local git configuration alone (no remote, or a non-GitHub remote; a workspace with no `.git` at all counts as no remote and must not crash). Otherwise MISSING, the row saying which: no workflow file with an OSV step and a `schedule:` trigger (the text must contain `no workflow file` and `schedule:`); an OSV workflow with `workflow_dispatch` only (`has no schedule: trigger`); or a scheduled one whose list differs, naming the lock files apart (on each side). MISSING sets exit 1 like every MISSING; OK and NOTE leave the exit as it is.
4. The existing gate reader's exclusion of `dependency-scan.yml` / `.yaml` by file name (docstring lines 14-17 and the code behind them, lines 847-853) is NOT changed in this increment; the new row's own reading uses no file name. The docstring must still be made true: add the new floor to the "What it checks" list, describing the row as found by triggers and steps.
5. J14: the docstring's exit line (line 78, `Exit 0 = every floor present; 1 = at least one MISSING; 2 = not a workspace.`) must list the exits `main()` actually returns: 2 is also returned for a malformed record header (`HEADER MALFORMED`, the returns at lines 841, 1270 and 1276).
6. This repository's own run must print the row OK: its `.github/workflows/dependency-scan.yml` has `schedule:` (cron) and `--lockfile=requirements.txt:requirements.lock` unquoted; the gate `.github/workflows/tests.yml` (`on:` with `push:` and `pull_request:`) has `--lockfile='requirements.txt:requirements.lock'` quoted. You must not edit any `.github` file.
7. No option added, no new dependency, MANIFEST regenerated by `python tools/make-manifest.py`.

**`conformance-check.py` as it stands.**
- `main()` (line 814) parses `sys.argv` by hand (`--quiet`, `--screens`, `--installable`, `--offline`, one positional), resolves the Workspace with `resolve_workspace` (line 439: the path or its `Workspace/` child holding `docs/` or `.git/`), and collects rows through `add(verdict, floor, detail="")` into `results`. At the end (lines 1398-1410) it prints `conformance-check: <ws>`, one line per row as `"  %-8s %s%s" % (verdict, floor, ("  - " + detail) if detail else "")` (OK rows are skipped under `--quiet`), the count line `conformance-check: <n> OK, <n> MISSING, <n> NOTE`, then `RESULT: CONFORMANT` and returns 0, or `RESULT: <n> floor(s) missing - ...` and returns 1 when any row is MISSING. A MISSING row added through `add` therefore gives exit 1 by itself.
- The workflow section (lines 844-903): `workflows` is the sorted glob of `.github/workflows/*.yml` and `*.yaml`; `gate_workflows` leaves out `dependency-scan.yml` / `.yaml` by name (ruling 4: unchanged); `workflow_steps(text)` (lines 449-491) returns each step as `(body, guarded, commands)`, where `commands` is the step's `run:` / `uses:` lines and its block-scalar continuation lines. `SCANNERS` (line 130) holds the OSV-Scanner pattern `r"osv-scanner"`, matched with `re.I` against `commands` (line 864). An OSV-Scanner step for this row is a step whose commands match that pattern. When there is no workflow at all, the section adds `CI gate` MISSING and nothing else; the weekly row is still printed once (ruling 1).
- The inventory section (lines 1250-1281) reads `docs/INVENTORY.md` (`read_header` / `check_header` first, `HEADER MALFORMED` and return 2 for a bad header), then fills `sections` from `bridge_env.inventory_parse_tables(...)`: `sections["Decisions"]` is the list of the Decisions table's rows, each a list of stripped cells, so `row[0]` is the first cell. Where the loaded `bridge_env` lacks the readers (`inv_can_read` false), `sections` stays empty. `bridge_env.inventory_development_data` (bridge_env.py line 3281) is the existing reading of a Decisions row by its first cell, for comparison.
- `_escape_field(value)` (line 707) turns any non-printable or non-ASCII character into a backslash escape and leaves printable ASCII as it is. A value read from a project file (a Decisions cell, a lock-file name) is printed through it.
- The subprocess helpers `git_ignored` / `git_tracked` (lines 504-517) show the program's convention for a local `git` call: `cwd=ws`, `capture_output=True`, `timeout=GH_TIMEOUT` (25 s), `creationflags=NO_WINDOW`, `OSError` and `TimeoutExpired` caught, no retry. `gh(...)` (line 494) is the only GitHub call and runs only without `--offline`; the new row never calls `gh` and never reaches the network, with or without `--offline`.
- The module docstring (lines 2-80) is the program's usage text. Line 78 is the exit line (ruling 5).

**The acceptance tests.** `tests/test_program_weekly_floor.py` (16 cases) fixes the interface. Read it whole. `make_project` builds a scratch Workspace under `tmp_path` that the check finds conformant but for the weekly row, runs `git init` in it, and adds `origin` = `https://github.com/example-owner/thing.git` unless told otherwise (`remote=None`: no remote; `OTHER_REMOTE` = a gitlab URL). Every run is `conformance-check.py <ws> --offline`. `rows(out, name)` reads `^  (OK|MISSING|NOTE) +(.*)$` and requires the detail after `<name>  - `; `weekly_row` requires exactly one row named `Weekly dependency scan`. `plain(detail)` removes backticks before some checks. `assert_ok` requires the row OK, its detail holding `not compared` and `disabled`, exit 0 and `RESULT: CONFORMANT`. `test_ok_with_a_weekly_workflow_named_otherwise` uses `nightly-deps.yaml` (schedule + workflow_dispatch). `test_the_docstring_lists_the_exits_the_code_has` parses the program with `ast`: the integer constants returned in `main()` plus every `<x>.exit(<int constant>)` call anywhere must equal `{0, 1, 2}` (so add no other exit), and in the module docstring every single digit not preceded by a word character, `.` or `-`, and not followed by a word character or `.`, then optional spaces and `=`, `:` or `-`, is read as an exit mark; the text up to the next mark (at most 250 characters) is that exit's meaning. Exit 0's meaning must hold `every floor` or `conformant`; exit 1's `missing`; exit 2's `workspace` and also `header` or `malformed`. A digit followed by `=`, `:` or `-` in the text you add elsewhere in the docstring becomes a mark too, and can cut a meaning short. `test_this_repository_prints_the_weekly_row_ok` runs the check over this Workspace (`cwd` the Workspace, `--offline`) and requires the row OK; it does not require exit 0.

On the checkpoint, 11 of the 16 fail and 5 pass. The five that pass today hold what stands and must keep passing: `test_a_scheduled_scan_is_never_read_as_the_gate`, `test_an_all_omitted_index_passes_diagram_check[design]`, `[code]`, `[done]`, and `test_an_all_omitted_index_passes_the_conformance_diagram_floor`. After your change all 16 pass.

**The existing tests the supervisor read against the rulings (the reality check before this brief).** Each was read, not run.
- No existing conformance test sets a git remote, and no fixture under `tests/fixtures/` holds a workflow or an OSV-Scanner step. The shared fixture `make_workspace` (`tests/test_conformance_check.py` line 63) writes no `.git` at all; `tests/test_hotfix25a_conformance_semgrep.py` (lines 101, 198) and `test_second_pass_residue` (line 289) run `git init` without a remote. All of them land on the no-remote NOTE, which leaves the exit as it is. They stay green **only if** a Workspace with no `.git` of its own is read as no remote: never let `git` search the parent folders of a scratch Workspace (`tmp_path` can sit inside some other repository), and never ask `gh`.
- `tests/test_conformance_check.py::test_a_conformant_workspace_passes_from_workspace_and_from_root` requires exit 0, `RESULT: CONFORMANT`, `0 MISSING` and no `  MISSING` line; its gate is `on: [pull_request]` (the inline list form) with `--lockfile package-lock.json` (a space, no `=`). No `.git`, so the NOTE.
- `test_r083_the_required_check_row_follows_the_branch_rule`, `test_r083_a_bridge_env_without_branch_rule_does_not_invent_a_row` (`tests/test_conformance_check.py`) and `tests/test_program_branch_rule.py::test_r083_r2_the_none_row_is_true_for_both_causes_of_none` load the program in-process, run it **without** `--offline`, replace `gh` with a stub that answers `OWNER/REPO` to any call, and require exit 0 for the value and cannot-read cases. A remote read through `gh` would make those MISSING; read the remote from the local git configuration only.
- `tests/test_b2_least_confident.py::test_fix002_conformance_check_judges_a_shaped_status_file_by_its_line_alone` and `test_fix002_a_broken_line_in_a_shaped_file_is_the_one_finding` require the NOTE lines of two runs on two different scratch folders to be equal, and the MISSING lines to be the `Workflows line` rows only. The row's detail therefore names no path and nothing that differs between two scratch folders.
- `tests/test_conformance_windowless.py::run_check` fails any output line other than the first that holds the fixture's folder name; its fixtures hold `docs/` alone (no workflow, no `.git`). Same consequence: the detail names no path.
- `tests/test_bug042.py` pins the gate reader's file-name exclusion (`test_bug042_the_weekly_file_is_known_by_its_name_in_either_form`, `test_bug042_the_same_steps_under_another_name_are_a_gate`: the weekly text in `security-scan.yml` answers `OSV-Scanner in the gate` OK). It checks the scanner rows only, never the exit. It stays green as long as ruling 4 holds.
- `tests/test_calibrate_program.py` and `tests/test_workflows_line_check.py` run a copy of the program (with `bridge_env.py` beside it) on `make_workspace` fixtures and require exit 0 in several cases: no `.git`, so the NOTE.
- `tests/test_header_currency.py` (reading 4, the `Phase: ` reading in `conformance-check.py`), `tests/test_header_status.py` (`test_r058_retired_3_...`, `test_r058_retired_4_...`) and `tests/test_program_strip_names.py::test_r080_conformance_check_holds_no_copy_of_the_name_test` read the program's source: add no reading of `Phase:`, `Bridge version:` or `Stage:`, and no copy of the secret-name test.
- No test counts the conformance check's rows or its OK/NOTE totals over a scratch project. `tests/test_release_b2_stamp.py` quotes `conformance-check: 24 OK, 0 MISSING, 2 NOTE` from a record's text, not from a run; it is unaffected.

**The command reference (a known consequence, the supervisor's to settle).** `tools/dump-cli.py` records `conformance-check.py` from its module docstring (`docs/cli-reference.json`, `"source": "docstring"`), and `docs/CLI_REFERENCE.md` is rendered from it. Rulings 4 and 5 change that docstring, so after your change `python tools/dump-cli.py --check` reports the reference stale and `tests/test_dump_cli.py::test_cfgb3b_committed_reference_is_current` fails. Both reference files are outside your Scope: do not regenerate them. Run the two commands of the Done list that show it, quote their output, and name it in the report as the expected consequence. Any other failure in `tests/test_dump_cli.py` is reported by test id.

**External services.** None in this increment. The row makes no network call, with or without `--offline`; the GitHub read the program already makes stays behind `--offline` as today. A local `git` call, if you make one, follows the program's convention (above): windowless, `timeout=GH_TIMEOUT`, no retry, its failure read as no remote.

**Trust boundaries and security context.** ASVS level 2 (`docs/INVENTORY.md`, Decisions, line 140). `.cursor/rules/secure-coding.mdc` is in force for you. Outside input crossing into the program: the project's workflow files, its inventory and its git configuration (any bytes). A value read from them (a lock-file name, a Decisions cell, a remote URL) is printed only through `_escape_field`; a remote URL is never printed at all (it can hold a credential). No exception may escape as a traceback; the program keeps its exits 0, 1 and 2 and adds none. The program never writes (docstring: "Never writes.").

**Development data.** The inventory's decision (`docs/INVENTORY.md`, Decisions, line 135) reads: "the dev build is the Workspace sources under `bridge/`; a session in the repo always runs the *installed* bridge (`~/.claude`), never the one being edited, and installs reach running projects only through the owner's install run sheet". For you: run `conformance-check.py` only through the tests (scratch Workspaces under `tmp_path`, and the one read-only `--offline` run over this Workspace in `test_this_repository_prints_the_weekly_row_ok`). Never install anything, and never read or copy anything under `~/.claude` or `~/.cursor-bridge`.

**Host.** Windows 11 with the owner's Python. CI also runs on Linux.

## Diagrams
None. The plan entry names no diagram for this increment.

## Requirements
1. **R1. One row.** Every run that reaches the end of `main()` prints exactly one row named `Weekly dependency scan`, OK, NOTE or MISSING, also when the project has no workflow at all. It is added through `add`, so `--quiet` hides it when OK and a MISSING counts in the totals and gives exit 1.
2. **R2. Found by triggers and steps.** A workflow's triggers are read from its top-level `on:`: at least the block form (`on:` followed by indented keys such as `push:`, `pull_request:`, `schedule:`, `workflow_dispatch:`) and the inline forms `on: push` and `on: [push, pull_request]`. The gate set is the union of the `--lockfile=` values of the OSV-Scanner steps in every workflow triggered by `push` or `pull_request`. A weekly workflow is any `.github/workflows/*.yml` or `*.yaml` with an OSV-Scanner step and a `schedule:` trigger; its set is the union of its OSV-Scanner steps' `--lockfile=` values. No file name decides either reading. Each value is the text after `--lockfile=` up to the next whitespace, with one pair of matching surrounding quotes (`'...'` or `"..."`) removed. Sets are compared, never ordered lists.
3. **R3. OK.** Where some weekly workflow's set equals the gate set, the row is OK and its detail says that pins, permissions and exit handling are not compared and that a workflow disabled on GitHub is the evaluation's read (the words `not compared` and `disabled` appear in it).
4. **R4. NOTE.** Otherwise, where `docs/INVENTORY.md`'s Decisions table holds a row whose first cell begins `Weekly scan:`, the row is NOTE and its detail quotes that cell (through `_escape_field`). Otherwise, where the Workspace's own git configuration names no GitHub remote (no `.git` in the Workspace, no remote, or no remote URL on `github.com`), the row is NOTE, its detail saying the repository has no GitHub remote. The remote is read from the local configuration alone: no `gh`, no network, no parent folder's repository, no crash on a missing or unreadable `.git`.
5. **R5. MISSING, saying which.** Otherwise the row is MISSING and its detail says which of the three it is: no workflow file runs OSV-Scanner on a `schedule:` trigger (the detail holds `no workflow file` and `schedule:`); a workflow with an OSV-Scanner step has no `schedule:` trigger (the detail holds `has no schedule: trigger`, backticks around `schedule:` allowed); or a scheduled OSV-Scanner workflow's list differs from the gate's, the detail naming the lock files on each side apart (the gate's alone and the weekly's alone), each through `_escape_field`.
6. **R6. The docstring.** The "What it checks" list gains the weekly floor, described as found by its triggers and its OSV-Scanner step (no file name), with its OK, NOTE and MISSING readings. The bullet on the gate workflows (lines 15-17) and its file-name exclusion stay as they are. The exit line names exit 0 (every floor present), 1 (at least one MISSING) and 2 (not a workspace, or a malformed record header, `HEADER MALFORMED`, the status file's or the inventory's), so that `test_the_docstring_lists_the_exits_the_code_has` passes. The docstring stays ASCII.
7. **R7. No interface change.** No option, configuration key, environment variable or dependency is added; the program's arguments and its exits 0, 1, 2 are unchanged; no `.github` file changes; this repository's run prints the row OK.

## Acceptance criteria
- [ ] `tests/test_program_weekly_floor.py` passes whole, unedited (16 cases).
- [ ] `tests/test_conformance_check.py`, `tests/test_conformance_check_a4.py` and `tests/test_diagram_check.py` pass. Any edit to a fixture is of the kind Scope allows and is named in the report.
- [ ] Every other test file in the Done list's commands passes unedited, except `tests/test_dump_cli.py::test_cfgb3b_committed_reference_is_current`, reported as the expected stale reference (Context).
- [ ] One `Weekly dependency scan` row per run; OK, NOTE and MISSING as R2-R5 say; the reading uses no file name (R1-R5).
- [ ] The no-remote NOTE holds for a Workspace with no `.git`, no remote, or a non-GitHub remote, read locally, with no `gh` call and no crash (R4).
- [ ] The docstring lists the weekly floor and every exit `main()` returns (R6, J14).
- [ ] `python bridge/cursor-bridge/conformance-check.py . --offline` over this Workspace (through its test) prints the row OK; no `.github` file changed (R7).
- [ ] MANIFEST is regenerated. `bridge/cursor-bridge/VERSION` is not listed by `git status --short`. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` prints `RESULT: SOURCES MATCH`.
- [ ] `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks` passes.
- [ ] `conformance-check.py` stays ASCII, and every line you add anywhere is ASCII.
- [ ] R-092 (the parts this brief serves) is fully met, with no stand-in, placeholder or "later" text. The tests naming R-092 are the supervisor's acceptance tests.
- [ ] No new dependency, option, configuration key or environment variable. No new Semgrep high finding. No exception escapes as a traceback (ASVS L2).

## Constraints
- Do not add dependencies (the standard library and the pytest already used only).
- Do not read or write any file outside this workspace (the folder you were started in). Everything you need is inside it, and everything you produce goes inside it.
- Do not edit `tests/test_program_weekly_floor.py`, any `.github` file, or anything else outside Scope. If a test case seems wrong, stop and report it by its test id instead of working around it.
- If the brief, the rules, or the tooling got in your way (an instruction that contradicted another, a check that fired wrongly, a step that cost time for no reason), append one dated line describing it to `docs/BUILDER_NOTES.md`. Do not try to fix the tooling. Do the same for anything you learned about a defect or a pitfall (a cause you found, a platform quirk that cost you a round): one dated line, so the supervisor can carry it forward.
- In any Markdown you write, never break a line inside a paragraph or a list item. One paragraph is one line. Line breaks only between blocks.
- **No owner's names, no paths.** Nothing you write (code, the notes line, the report) holds a path of this computer or a user name. In the report write `<Workspace>` for the repository folder and `<tmp>` for a temporary folder, including in quoted command output.
- This increment talks to no external service. Add no call to any service or the network; the existing `gh` read stays behind `--offline` as it is.
- Any console process your code launches on Windows is created windowless (`creationflags=NO_WINDOW`, the program's constant: `subprocess.CREATE_NO_WINDOW` on Windows, `0` elsewhere). A `git` call, if you make one, carries `timeout=GH_TIMEOUT`, catches `OSError` and `subprocess.TimeoutExpired`, and is not retried.
- Never start a server, a watcher or a daemon that outlives a test. Run every command synchronously, in the foreground, and wait for it to end. Leave nothing running when you finish.
- Do not refactor code outside the scope, even if it looks wrong. The gate reader's file-name exclusion stays (ruling 4).
- Never run the product, a migration, a seed or a test against the owner's live data (Context, "Development data").
- A value the brief marks as the owner's: none in this increment.
- Follow existing conventions in the file you touch: ASCII program text, rows through `add`, details through `_escape_field` for read values, `main()` returning the exit code, `glob` for the workflow files, `workflow_steps` for the steps.
- These git commands are not yours to run: `commit`, `push`, `switch`, `checkout`, `merge`, `rebase`, `reset`, `stash`, `branch -d`, `worktree`. You read with `git status`, `git diff` and `git log` only. The single exception is `git restore bridge/cursor-bridge/VERSION` in the Done section.
- Numbers: none are parsed by this increment. Lock-file values are strings compared as sets.
- Every verification command the Done section asks you to run is written there in full. Run exactly those. **Do NOT run the whole `tests/` tree** (`python -m pytest`, `python -m pytest tests`, or any command that collects all of it): the whole suite is CI's run.
- **Mutation self-check (by hand, in process, no script in the diff).** The supervisor's mutants file sweeps your change after your run. Before you finish, apply each of these by hand, one at a time, run `python -m pytest -p no:cacheprovider -q tests/test_program_weekly_floor.py`, and revert. Confirm with `git diff` that each revert is exact. List each in the report by its label and text, with the pytest summary line and the id of a test it made fail. If one is not caught, write `not caught` and one line on the case that would catch it (do not add that case):
  - M1 the surrounding quotes are not stripped from a `--lockfile=` value.
  - M2 the two lists are compared in order instead of as sets.
  - M3 the `Weekly scan:` Decisions row is not read.
  - M4 the `schedule:` trigger is not required of a weekly workflow (a `workflow_dispatch`-only workflow counts as weekly).
  - M5 the remote reading always answers "no GitHub remote".
- **Known failures.** Context lists the acceptance cases that fail before your change, and the one expected failure after it (the stale command reference). If a case fails that your change did not cause, report it by its test id with its failure lines and fix none.
- Prefer reuse over new code: `workflow_steps`, `SCANNERS`' OSV-Scanner pattern, the `sections` dict the inventory section already fills, `_escape_field`, `add`, and the existing `git` call convention. Write the minimum that meets the acceptance criteria (the frozen `minimal-code.mdc` is in force). This never overrides a security, observability or accessibility requirement stated above.
- Rules in force for you: `.cursor/rules/secure-coding.mdc`, `.cursor/rules/workspace-boundary.mdc` and the frozen `minimal-code.mdc`.

## Done
Your report is the file `handoff/TASK-072-r1-report.md`, which you write as you go: what you did, what you changed, what you ran and what it printed, and what you could not do, so that nothing of it is lost if your run ends early. It names no computer path and no user name: write `<Workspace>` for the repository folder and `<tmp>` for a temporary folder, including in quoted command output.

When you finish, it holds:
- a list of every file you changed or created;
- a one-paragraph summary of what you did;
- for R1-R7, one line each on what meets it, naming the functions and their lines as the file stands after your change. For R2, the trigger forms you read; for R4, how the remote is read and how a Workspace without `.git` is handled; for R5, the exact detail texts of the three MISSING cases, the NOTE cases and the OK row;
- every fixture change in `tests/test_conformance_check.py`, `tests/test_conformance_check_a4.py` or `tests/fixtures/`: the test id, why, and the diff (or `none`);
- the mutation self-check list, M1-M5, each with its pytest summary line and the test id that caught it (or `not caught` and the case that would);
- every command of the list below with its output;
- a section headed exactly `Assumed, not verified`, as the report's last section.

The `Assumed, not verified` section lists every fact this change relies on that neither this brief nor the existing code settled, and that you did not confirm. Examples: how a workflow triggered by both `push` and `schedule:` is read; whether an empty gate set and an empty weekly set count as equal; which weekly workflow a differing-list detail names when there are several; whether a `--lockfile` value given with a space instead of `=` should count; how a `.git` file (a worktree) is read; whether `Weekly scan:` is matched case-sensitively. One item per line: what you assumed · why · what would confirm it. If there are none, write `Assumed, not verified: none`. Be specific: "edge cases" or "error handling" is not an item.

Run these from the Workspace root, in this order, after your last edit, each on its own, synchronously in the foreground, with no `PYTHONPATH` or other environment change:
1. `git status --short`
2. `python tools/make-manifest.py`
3. `git restore bridge/cursor-bridge/VERSION`
4. `python -m pytest -p no:cacheprovider -q -rs tests/test_program_weekly_floor.py tests/test_conformance_check.py tests/test_conformance_check_a4.py tests/test_diagram_check.py tests/test_bug042.py`
5. `python -m pytest -p no:cacheprovider -q -rs tests/test_hotfix25a_conformance_semgrep.py tests/test_a4_followups.py tests/test_a4_review_fixes.py tests/test_b2_least_confident.py tests/test_program_branch_rule.py tests/test_calibrate_program.py tests/test_conformance_windowless.py`
6. `python -m pytest -p no:cacheprovider -q -rs tests/test_workflows_line_check.py tests/test_header_status.py tests/test_header_tables.py tests/test_header_tables_r2.py tests/test_header_currency.py tests/test_program_strip_names.py tests/test_loop_text_windowless.py tests/test_running_projects_classify.py`
7. `python -m pytest -p no:cacheprovider -q -rs tests/test_dump_cli.py` (expect `test_cfgb3b_committed_reference_is_current` to fail on the stale reference, and nothing else)
8. `python tools/dump-cli.py --check` (expect it to name the command reference stale; do not regenerate)
9. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` (expect `RESULT: SOURCES MATCH`)
10. `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks`
11. `python -c "open('bridge/cursor-bridge/conformance-check.py','rb').read().decode('ascii'); print('ascii ok')"` (expect `ascii ok`)
12. `git rev-parse HEAD` and `git status --short` (`bridge/cursor-bridge/VERSION` must not be listed, and no `.github` file; if either is, report it)

Commands 4 to 7 cover every test file that runs `conformance-check.py`, loads it, or reads its source. Every file in them outside Scope is reported by test id on failure, never fixed in that file.

Quoting rules:
- Every command you ran is quoted in the report with the lines it printed, verbatim, in a fenced block.
- Each pytest summary line is quoted verbatim in a fenced block. Never restate a count in prose.
- A claim that a check passed quotes the output line that shows it. A number of failing or skipped cases is backed by the pytest lines naming them (`-rs` prints each skip's reason).
- Each mutation is listed by its label and text, with what caught it.
- A command you did not run is written `not run`, never described as run.
- Write the report's results after step 12, naming the commit its counts belong to (`git rev-parse HEAD`) and whether the working tree then held uncommitted changes (`git status --short`).

Your last message is the summary and the report file's path, and nothing follows it. The supervisor reads only the last message, and a message printed earlier and then followed by more work is lost.
