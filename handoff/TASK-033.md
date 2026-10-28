# TASK-033: One reading of a squash subject: the plan check's title rule and `pace-report.py`

## Objective
Two programs read a squash subject on `main` to decide whether an increment has merged: `plan-check.py`, and the reader TASK-032 placed in `bridge_env.py` for the launcher and the guard. Today `plan-check.py` holds its own copy, and its closing-parenthesis form read TASK-031 as merged from BUG-018's title (ISS-013). This increment makes one copy of that reader, in `bridge_env.py`. The closing-parenthesis form is narrowed so that it merges an increment only when every item inside the parenthesis is a bare ID. `plan-check.py` imports the reader. On that reader, the increment builds `pace-report.py`, the report cycle's read-only weekly pace table: increments started and merged, rounds, days to merge, `docs/HARDENING.md` lines and, optionally, tokens. A creeping slowdown then shows the week it starts.

Satisfies: R-044 — the report cycle has a pace section for every project, computed by `pace-report.py`, read-only, from git and the launcher's and the guard's own records; the pace report and the plan check read a squash subject by one rule, one copy in `bridge_env.py`, under which a closing parenthesis merges an increment only when each of its comma-separated items is a bare ID (ISS-013). The full row is `docs/REQUIREMENTS.md` line 50; read it whole.

## Scope
Files you may create or modify:
- bridge/cursor-bridge/plan-check.py
- bridge/cursor-bridge/pace-report.py
- bridge/cursor-bridge/bridge_env.py
- bridge/cursor-bridge/MANIFEST.json
- tests/test_plan_check.py
- tests/test_pace_report.py
- tests/test_dump_cli.py
- docs/cli-reference.json
- docs/CLI_REFERENCE.md
- docs/BUILDER_NOTES.md
- handoff/TASK-033-r1-report.md

Do not modify anything else.

**Read-only, the supervisor's:** `tests/test_task033_supervisor.py`, committed with a `supervisor:` subject before your run, as commit `858da29`. Read it, run it, never edit it. It is the supervisor's acceptance test of this increment. Your own tests in `tests/test_plan_check.py` and `tests/test_pace_report.py` are written beside it, as the Done when below lists them.

## Out of scope
- .env and anything under secrets/
- CI configuration (`.github/`, `.githooks/`)
- docs/ and handoff/, except the files the Scope section names
- `bridge/cursor-bridge/bridge-run.py`, `review-guard.py`, `evaluate-reports.py` and every other program: you read them, you do not change them
- every test file not in Scope, including `tests/test_task032_supervisor_*.py` and `tests/test_evaluate_reports.py`
- these `docs/HARDENING.md` "TASK-032" leads: N3, the ID pattern written three times (`_REVIEW_NAME_RX`, `REVIEW_LIFT_RE`, `MERGE_UNIT_RE`); the lapse reading the local `main` ref; a closing parenthesis of bare IDs on a plan-revision subject still lapsing a claim (by the Done when's own rule, bare IDs merge); the malformed-record tracebacks; the test suite's rows in the real `runs.jsonl`; the Merges-trailer form reading a one-word subject under the grammar's pattern. Do not add a fourth literal copy of the ID pattern, but do not remove the three that exist.

## Context

### The build plan's acceptance text (docs/BUILD_PLAN.md:335), normative, every clause
> (a) `plan-check.py`'s closing-parenthesis form (`TRAIL_RX`) merges an increment only when every comma-separated item inside the parenthesis is a bare increment or requirement ID (`TASK-nnn[a]`, `R-nnn`, spaces around each allowed): `(TASK-100, R-027)` merges TASK-100, `(pointers, TASK-031's Scope, survival lists, records)` and `(TASK-031's Scope)` merge nothing, the other three forms unchanged, the docstring saying so, the four forms' reader, placed in `bridge_env.py` by TASK-032, narrowed there and imported by `plan-check.py` and `pace-report.py` (one copy, as the constants); `tests/test_plan_check.py` pins 9f6ace6's subject as merging nothing beside the accepted form (ISS-013), and a regression test over the bridge's own `main` (skipped where the history is shallow, CI's depth-1 checkout) asserts the set derived merged equals the set the former rule derived minus TASK-031, so no earlier squash un-merges;

> (b) `python ~/.claude/cursor-bridge/pace-report.py [<project root>...] [--weeks <n>] [--ceiling <n>] [--tokens] [--home <folder>]` prints, read-only and ASCII, one Markdown section per project root given (a folder holding `Workspace/` with its `.git`; with none given, the roots `evaluate-reports.py`'s project list names, loaded from the sibling file, and the bridge's own root found as that program finds it): a table with one row per ISO week of the last `--weeks` (default 8) and a total row — increments started (the week of the increment's first builder launch in the Workspace's `run/launcher/runs.jsonl`, by its `brief` field, or of its first round in `.git/bridge/rounds-<ID>.json`, whichever is earlier, counted only for an ID that has a brief — a stage review's or a records subject's record is no start; `unknown` where neither record exists, since a squash leaves no earlier commit on `main`), increments merged (a commit on the Workspace's `main` whose subject merges the ID under the plan check's four forms, applied to every ID that has a brief, the grammar `bridge_env`'s), rounds per merged increment as mean and maximum (an increment's rounds: the largest of three readings — the highest `<N>` of its `handoff/<ID>-r<N>[a-z]?-report.md` files, a letter sub-round reading as its `<N>`; the `run/review/REVIEW-<ID>[a-z]?.err` and `REVIEW-<ID>-r<N>.err` files, a letter as its ordinal where the longer token has no brief and the shorter has one (TASK-032's rule), which record a Review B read that followed no builder run; and the guard's `rounds-<ID>.json` count where that record exists — the source said), mean days from start to merge over the increments whose start is known, and lines added to `docs/HARDENING.md`, the header saying they are lines landing on `main` that week (a squash lands an increment's lines in its merge week); a week that merged nothing prints a blank mean, not a zero; under the table the increments over `--ceiling` (default `bridge_env.REVIEW_ROUNDS`) are listed by ID, and the stage reviews over it (`STAGE-<name>`) beneath them, with their rounds and, for each round above the ceiling, the lift it used — `class`, `owner`, `none`, or `unknown` where the records predate TASK-032 — read from `runs.jsonl` and the rounds file; a project whose `handoff/` is untracked prints `n/a (handoff/ untracked)` in the rounds and started columns; with `--tokens`, a column of the project's tokens that week (millions) from `~/.claude/projects/<key>/*.jsonl` and `<key>/**/subagents/*.jsonl` where present (the header says which were found) for the root's and the Workspace's keys as `evaluate-reports.py` derives them, each record's `message.usage` four fields (`input_tokens`, `output_tokens`, `cache_creation_input_tokens`, `cache_read_input_tokens`) summed on purpose and named in the column's header, the same four (so one week compares with the next, and a change of fields would show), one usage per message id (the copy with the greatest total), the week from the record's timestamp, and the week's tokens per merged increment beside it; a project with no session folder gets an empty tokens cell and exits 0, and the read of the session folders is bounded like a git command (120 seconds per project; on the limit an empty cell and the project named); a root that is no project exits 2 naming it; every git command is read-only with a 120-second limit, and one that reaches it fails that project naming the command (the others printed, exit 1 at the end); the program writes nothing;

> (c) `tests/test_pace_report.py` (names R-044), on repositories built in the test with dated commits and records written in the test: each column on a known history (two increments, one with three builder reports and one over the ceiling, one merged by a trailer and one by a bare-ID parenthesis, a letter sub-round report, a start from the launcher's record, a start from the guard's record, an unknown start, a stage review's record counted as no start, an increment whose `.err` files outnumber its reports read at the `.err` count, `TASK-010`'s letter files beside a real `TASK-010c`), the week boundaries, a blank mean on a week with no merge, the lift column's four values, a subject in the ISS-013 form merging nothing in both programs (one test runs both on the same subject), the guard's record outranking the reports, an untracked `handoff/`, `--tokens` on a fixture transcript folder under `--home` with a duplicated message id counted once at its greatest total and a `subagents/` record counted, an empty cell without a session folder and on a timed-out read, the bridge's own Workspace printing without error, exit 2 on a non-project root, ASCII output, and the tree unchanged after a run; `tests/test_dump_cli.py` lists the program (its `build_parser()`); the command reference regenerated; `windowless-check.py` green; no new dependency.

### What exists today: the squash-subject reader in `bridge/cursor-bridge/bridge_env.py`
- `squash_merged_ids(folder, id_rx, git_runner=None)` at :504-560 takes the pattern as a string or a compiled regex. It runs `git -C <folder> log main --format=%s%n%(trailers:key=Merges,valueonly)` with `timeout=GIT_TIMEOUT` (30 s, :302). It returns `None` on `OSError`, on `TimeoutExpired` or on a non-zero exit, else a set of IDs.
- Its forms, in this order:
  - the Merge form (`merge_rx`, :528, with `_branch_name_to_id` :475-489), tried first; a Merge line is never tried against the other forms, even when it maps no ID (`continue` at :545);
  - the subject form (`_subject_leading_ids`, :492-501), which keeps only tokens holding a hyphen and a digit;
  - the closing-parenthesis form (`trail_rx`, :525-527), which takes every ID token anywhere inside the parenthesis; this is the one to narrow;
  - the `Merges:` trailer line (:556-559).
- Its only caller is `_claim_lapsed` (:750-759), used by `branch_declared_ids` (:762) and `branch_allows_id` (:778), which `bridge-run.py` and `review-guard.py` call with `bridge_env.grammar_id_rx()` (:845; bridge-run.py:620, review-guard.py:624).
- The constants: `REVIEW_ROUNDS = 3` (:304), `BLOCKING_CLASSES` (:306-312), `GRAMMAR_ID_PATTERN = r"[A-Z][A-Za-z0-9-]*"` (:314) and `PLAN_ID_PATTERN = r"TASK-\d{3,}[a-z]?"` (:315). `NO_WINDOW` is at :30.
- The readers: `parse_review_name(name)` (:348, the name grammar: returns `(id, round)` or `None`), `read_blocking_class_line` (:369), `review_owner_lifts(folder)` (:385), `plan_increment_ids(folder)` (:414), `read_runs_jsonl(log_folder)` (:606, reads `<log_folder>/run/launcher/runs.jsonl` and drops invalid rows) and `_read_rounds_files(common)` (:651, reads `<common>/bridge/rounds-*.json`, keyed by ID).

### What exists today: `bridge/cursor-bridge/plan-check.py`
- `ID = r"TASK-\d{3,}[a-z]?"` (:58). Its own four forms:
  - `SUBJECT_RX` (:167);
  - `TRAIL_RX` (:168): `\(([^()]*%s[^()]*)\)\s*(?:[-—–]\s*v?[\w.]+\s*)?(?:\(#\d+\))?\s*$`;
  - `MERGE_RX` (:169): `^\s*Merge (?:pull request #\d+ from \S+?/|branch ')(task-\d{3,}[a-z]?)\b`, case-insensitive;
  - the trailer line (:193-194).
- These are applied in `merged_ids(base)` (:174-195) in the order subject, Merge, trailing parenthesis, trailer. It runs `git log <base>` in the current folder with no timeout and returns `None` on a non-zero exit. `main()` calls it at :402 with `--base` (default `origin/main`, :264).
- The docstring's merge rule is at :24-29. `build_parser()` is at :261-267. `tests/test_dump_cli.py` checks its shape, because plan-check is in `EXTRACTED` (:30-31).
- `tests/test_task032_supervisor_launcher.py:692-709` (read-only, not yours) calls `program("plan-check").merged_ids("main")` with the current folder set to a fixture repository. It asserts that the result equals `bridge_env.squash_merged_ids(<root>, r"TASK-\d{3,}[a-z]?")` on the subjects at :676-689.
  - So `merged_ids(base)` must stay a module-level function of `plan-check.py` with that call form.
  - The two-argument call of `squash_merged_ids` must keep working.

### Divergences the reality check found
"The other three forms unchanged" means unchanged from `plan-check.py`'s reading today. These are the places where today's `bridge_env` copy reads differently under `PLAN_ID_PATTERN`. After your change, the one reader, given the plan pattern, must give `plan-check.py`'s former answer for each of them:
- `Merge pull request #1 from x/feat/task-005`: plan-check merges TASK-005. `bridge_env` stops at the branch's first component `feat` and merges nothing.
- `Merge pull request #9 from x/feature-z (TASK-100)`: plan-check merges TASK-100 through the parenthesis. `bridge_env`'s Merge form takes the line and merges nothing.
- `Merge pull request #1 from x/task-001ab`: plan-check merges nothing (`\b`). `bridge_env` merges TASK-001a.

Every behaviour the TASK-032 tests pin under the grammar's pattern stays. Examples:
- `config-b3b` from a Merge line, case ignored and the letter kept;
- `Plan the next stage` merges nothing;
- `(TASK-001)` and `Merges: TASK-001` merge;
- the parity test above.

### HARDENING's TASK-032 leads that this increment takes
Only N4 (docs/HARDENING.md:1233) falls inside the Done when. Clause (b) counts merged "under the plan check's four forms", and the plan check's subject form reads IDs only at the subject's start. Under the grammar's pattern today, `_subject_leading_ids` reads an ID after a non-ID leading word.

After your change, under either pattern:
- `Fix TASK-001 typo`, `Revert TASK-001: x` and `Plan: TASK-033 x` merge nothing;
- `TASK-002 TASK-003: two (#2)` merges both;
- `BUG-018: x (#61)` merges BUG-018 under the grammar's pattern.

The other leads are listed under Out of scope.

### The ISS-013 subject
The squash 9f6ace6 on `main` (BUG-018, PR #61) has the subject `BUG-018: stage B3's review round 2's fixes (pointers, TASK-031's Scope, survival lists, records) (#61)`. The project's Issues document quotes it so. Confirm it with `git log -1 --format=%s 9f6ace6`, a read you may run, and use the exact text git prints.
- Under the plan pattern it must merge nothing.
- Under the grammar's pattern it merges BUG-018 by its leading ID and must not merge TASK-031.
- The clause (c) test "in both programs on the same subject" therefore uses a subject in the ISS-013 form with no leading ID, for example `docs: fixes (pointers, TASK-031's Scope, survival lists, records) (#61)`. That subject merges nothing in either program.

### What `pace-report.py` reuses from `bridge/cursor-bridge/evaluate-reports.py`
Load that file as a module from the folder `pace-report.py` sits in: its name has a hyphen, so use `importlib.util.spec_from_file_location`. It has a `__main__` guard. Do not copy these names:
- `PROJECTS` (:69-74), the project list: name to root, the bridge's own root `Bridge` included;
- `bridge_root(start=None)` (:92-102), the bridge's root, found from the current folder;
- `project_keys(project, root)` (:126-134), with `project_key(root)` at :121-123. For the bridge's own project, `project_keys` returns the Workspace's key only (the root's key is the maintainer's session). "As `evaluate-reports.py` derives them" means exactly what `project_keys` returns. For a root given on the command line, the project name is the folder's base name, as `projects_from` (:409-410) does;
- `session_files` (:549-553), which globs `<home>/.claude/projects/<key>/*.jsonl`. `pace-report.py` adds `<key>/**/subagents/*.jsonl`.

`evaluate-reports.py` captures `HOME = os.path.expanduser("~")` at import (:68), and its `--home` is "the folder holding .claude/projects" (:663). `pace-report.py`'s `--home <folder>` means the same folder; without it, `~` is resolved when the program runs.

### The records `pace-report.py` reads (as TASK-032 writes them)
**`run/launcher/runs.jsonl`**, under the Workspace (rows written at bridge-run.py:1560-1571):
- `id`: the run id, UTC, `%Y-%m-%dT%H:%M:%SZ` with an optional `-<n>` suffix (bridge-run.py:1512-1516). `_event_time_launcher` (bridge_env.py:670-675) reads the time from it;
- `kind`, `branch`, `exit`;
- for a builder launch only: `brief` (the ID), `round`, `brief_sha256`, `brief_name`, `lift` (`"class"`, `"owner"` or `null`), `lift_line` and `merge_ids`.

A row without `brief` is no builder launch of a brief. Rows from before TASK-032 have no `brief` and no `lift`.

**`.git/bridge/rounds-<ID>.json`**, under the Workspace's git common folder. It is `{"rounds": [...], ...}`. Entries are written at review-guard.py:772-779: `round`, `name`, `branch`, `tree`, `time` (the snapshot's `taken`), `lift`, `lift_line`, `reply`. Seeded entries (review-guard.py:516-523) carry `"time": ""` and `"seeded": true`; a seeded round has no start time.

**Stage reviews** are IDs `STAGE-<name>`: a rounds file `rounds-STAGE-<name>.json` and `.err` files `run/review/REVIEW-STAGE-<name>[-r<N>].err`.

**"An ID that has a brief"** means a tracked `handoff/<ID>.md` or `handoff/<ID>-r<N>.md` whose name `bridge_env.parse_review_name` reads. A `-rN-report.md` file is no brief.

**Letter rule.** A trailing letter is a sub-round only where the longer token has no brief and the shorter ID has one. This is TASK-032's rule, as in `review-guard.py`'s seeding; reuse it, do not re-invent it.

### Values and units this brief settles
These are the supervisor's choices, not the owner's. Report them in `Assumed, not verified` if you depart.
- **`--weeks`:** an integer count of ISO weeks, 1 to 520 inclusive, default 8. It means the current UTC ISO week and the weeks before it.
- **`--ceiling`:** an integer count of rounds, 1 to 100 inclusive, default `bridge_env.REVIEW_ROUNDS`. An increment is "over" when its rounds exceed it.
- A value outside its range, or one `int` cannot parse, is a usage error with exit 2.
- **Weeks are UTC ISO weeks** (`date.isocalendar()`), for every source alike.
- **A merge's week** is the squash commit's committer date.
- **Tokens** are printed in millions, to two decimal places.
- **Limits:** every git command 120 seconds; the session-folder read 120 seconds per project.

### Tests' environment (`tests/conftest.py`)
- Every `subprocess.Popen` a test starts is windowless by default on Windows (:14-41). A test therefore passes no `creationflags` argument: `tests/test_tests_windowless.py:28-45` flags one that lacks `CREATE_NO_WINDOW`.
- An autouse fixture sets `HOME` and `USERPROFILE` to a temporary folder (:62-70).
- The `program` fixture loads a program by file name (:48-59).
- Programs import `bridge_env` with `sys.path.insert(0, HERE)` (bridge-run.py:101-102, roster-check.py:74-75); follow that.

### `tests/test_dump_cli.py` and the command reference
- `ARGPARSE` (:32) is the list of argparse programs whose entries `test_cfgb3b_argparse_entry_matches_its_parser` (:170-185) compares with their `build_parser()`. Add `pace-report.py` there.
- `tools/dump-cli.py` imports each argparse program from a copy of the bridge folder, without running `main()`, and refuses any of these:
  - an absolute default outside the bridge folder;
  - any string holding the home folder, the repository folder or the current folder (:285-294, :549-555, :663-671).
- So `pace-report.py`'s parser carries no computed path, no `~` expansion and no project root in a default, help or description. The defaults of the positional roots and of `--home` are resolved in `main()`, not in the parser.
- `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` are regenerated by `python tools/dump-cli.py`. A new command must appear there, or `test_cfgb3b_committed_reference_is_current` (:407-412) fails.

### Development data (docs/INVENTORY.md, Decisions, line 86)
"the dev build is the Workspace sources under `bridge/`; a session in the repo always runs the *installed* bridge (`~/.claude`), never the one being edited, and installs reach running projects only through the owner's install run sheet."

For this increment:
- The development data is repositories and records built in pytest's temporary folders.
- Two tests the Done when names read the bridge's own checkout, read-only: the regression test over `main` and "the bridge's own Workspace printing without error".
  - They run without `--tokens`, under the temporary `HOME`.
  - They are skipped where the checkout is shallow, has no local `main`, or does not sit in a folder named `Workspace` (CI's checkout).

### Security context
- ASVS level 2 (docs/INVENTORY.md, Decisions, line 91). `.cursor/rules/secure-coding.mdc` is in force.
- **Trust boundaries:** commit subjects, the records under `run/` and `.git/bridge/`, and the session transcripts are all untrusted text.
  - A malformed line or record is skipped, never a traceback.
  - A number in them is read with `int` after a regex has matched its ASCII digits.
  - The program prints no transcript content: only counts and IDs.
  - It passes `git` an argument list, never a shell string.
  - It writes nothing anywhere.

## Diagrams
None. The build plan's `Diagrams:` field for TASK-033 is `none`.

## Requirements
1. **One reader in `bridge_env.py`.** The four forms live in `bridge_env.py` only, parametrised by the ID pattern, with the closing-parenthesis form narrowed as clause (a) says. Under either pattern:
   - every comma-separated item must fully match a bare ID, spaces around each allowed;
   - `R-nnn` counts as a bare item but merges nothing under the plan pattern.

   `plan-check.py` and `pace-report.py` import the reader; neither keeps `SUBJECT_RX`, `TRAIL_RX`, `MERGE_RX` or a trailer regex of its own. The reader can be pointed at a ref and a folder, so that:
   - `plan-check.py` keeps reading `git log <base>` in its current folder;
   - `pace-report.py` reads the Workspace's `main` with its own 120-second limit and can tell a timeout (naming the command) from a missing ref.

   `_claim_lapsed` keeps its behaviour.
2. **Same answers, except the narrowing and N4.**
   - Under `PLAN_ID_PATTERN`, the reader returns what `plan-check.py`'s former `merged_ids` returned, for every subject except a closing parenthesis holding a non-ID item. This includes the three divergences in Context.
   - Under the grammar's pattern, every case the TASK-032 tests pin is unchanged, apart from N4's subjects.
3. **`plan-check.py`.**
   - `merged_ids(base)` stays.
   - The docstring (:24-29) states the narrowed parenthesis rule, with `(TASK-100, R-027)` merging and `(TASK-031's Scope)` merging nothing.
   - `--base`, the report lines and the exit codes are unchanged.
4. **`tests/test_plan_check.py`** gains:
   - 9f6ace6's exact subject merging nothing, beside an accepted bare-ID parenthesis;
   - `(pointers, TASK-031's Scope, survival lists, records)` and `(TASK-031's Scope)` merging nothing;
   - the regression test of clause (a). It runs the former rule (a copy of today's four regexes and loop, inside the test only) and the new reader on the bridge's own `main`, and asserts new == former minus {TASK-031}. It skips where `git rev-parse --is-shallow-repository` prints `true` or `main` does not resolve.

   Name R-044 in each new test.
5. **`pace-report.py`** does what clause (b) says, as an argparse program with a module-level `build_parser()` and a `main()` that calls it.
   - **Project roots.**
     - A project root is a folder holding `Workspace/` and `Workspace/.git`.
     - With no root given, the roots are `PROJECTS`' values plus `bridge_root()`, each once (compared by normalised absolute path).
     - A given root that is no project exits 2 naming it, before any output.
     - A root from `PROJECTS` that does not exist on this computer is a named line in its section, not exit 2.
   - **Output.** It is ASCII only.
   - **Exit codes:** 0 done; 1 a project failed (a git command at its limit, named), the other projects still printed; 2 usage, or a given root that is no project.
   - **Tracked `handoff/`.** Whether `handoff/` is tracked is read with `git ls-files`.
   - **HARDENING lines.** Lines added to `docs/HARDENING.md` are the added-line counts of the commits on `main` that touch it, by commit week.
6. **`tests/test_pace_report.py`** holds every case clause (c) lists. Its docstring names R-044, and every test function's name starts with `test_r044_`.
   - Fixture repositories set `GIT_CONFIG_GLOBAL` and `GIT_CONFIG_SYSTEM` to `os.devnull` and give commits dates with `GIT_AUTHOR_DATE` and `GIT_COMMITTER_DATE`.
   - The timed-out read is produced without waiting 120 seconds, for example by a monkeypatched limit or clock in a loaded module.
   - "The tree unchanged" compares `git status --porcelain` and the fixture's file hashes before and after.
7. **`tests/test_dump_cli.py`:** `pace-report.py` joins `ARGPARSE`; nothing else in the file changes.
8. **Docstrings.** `pace-report.py`'s module docstring gives the usage, the columns, the sources and the exit codes. `pace-report.py` and `bridge_env.py` are ASCII; `plan-check.py`'s existing non-ASCII bytes (the dashes in its docstring and `HEAD_RX`) stay as they are, and you add none.
9. **Settled readings** (the supervisor's, where the plan's words leave a choice):
   - **The ID pattern for merges** in `pace-report.py` is the grammar's (`bridge_env.GRAMMAR_ID_PATTERN`, "the grammar `bridge_env`'s" in clause (b)), applied to every ID that has a brief.
   - **A timed-out session-folder read** gives an empty tokens cell and a line naming the project and the limit; it is not a failed project and does not by itself make the exit 1. Only a git command at its limit fails a project.
   - **A seeded round** (`"time": ""`) is no start; the start is the earliest of the launcher's rows and the guard's timed rounds, else `unknown`.
   - **The over-ceiling list** holds every ID with a brief whose rounds exceed the ceiling and that merged within the window's weeks or has not merged; stage reviews (`STAGE-<name>`) the same way, beneath.
   - **`none` and `unknown` in the lift column:** `none` is a round that a TASK-032 record holds (a launcher row with `brief`, or a guard round entry) with no lift; `unknown` is a round read only from report files or `.err` files, with no such record.
   - **An untracked `handoff/`:** the started and rounds cells print `n/a (handoff/ untracked)`; the merged column counts every ID the reader finds in the week's subjects.

## Acceptance criteria
- [ ] `python -m pytest tests/test_task033_supervisor.py -q -p no:cacheprovider` passes whole.
- [ ] `git diff --quiet 858da29 -- tests/test_task033_supervisor.py` exits 0.
- [ ] `python -m pytest tests/test_plan_check.py tests/test_pace_report.py -q -p no:cacheprovider` passes. Every clause (a) and (c) case is a test, and the tests name R-044.
- [ ] `python -m pytest tests/test_task032_supervisor_launcher.py tests/test_task032_supervisor_guard.py tests/test_task032_supervisor_r4.py tests/test_bridge_run_review_ceiling.py tests/test_review_guard_ceiling.py tests/test_evaluate_reports.py tests/test_dump_cli.py tests/test_tests_windowless.py -q -p no:cacheprovider` passes. The launcher's and the guard's behaviour is unchanged apart from the narrowing and N4.
- [ ] `plan-check.py` holds no copy of the four forms; `bridge_env.py` holds the one copy; `pace-report.py` imports it and `bridge_env.REVIEW_ROUNDS`.
- [ ] Run from the Workspace root, `python bridge/cursor-bridge/plan-check.py` still runs: same exit code as before your change, no traceback.
- [ ] `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge/bridge_env.py bridge/cursor-bridge/plan-check.py bridge/cursor-bridge/pace-report.py tests/test_plan_check.py tests/test_pace_report.py` reports no FAIL. Every git call in the programs passes `creationflags=NO_WINDOW`; no test passes `creationflags`.
- [ ] `python tools/dump-cli.py --check` passes after regeneration, and `python bridge/cursor-bridge/bridge-check.py --root bridge --sources` ends OK.
- [ ] R-044's program part is fully met. There is no stand-in, placeholder, "coming soon" or "arrives in a later stage" text, and at least one test names R-044.
- [ ] No new dependency.

## Constraints
- Do not add dependencies; the standard library only.
- Do not read or write any file outside this workspace (the folder you were started in). The read-only exceptions are those the Done when names: the bridge's own root folder, which is this Workspace's parent, for "the bridge's own Workspace printing without error", and `evaluate-reports.py`'s project roots, which the default run lists. Never read the real `~/.claude/projects`: every `--tokens` run in a test uses `--home` on a fixture folder.
- **No real `cursor-agent` or model.** Nothing in this increment starts one, and no test does.
- **No real home.** Tests run under conftest's temporary `HOME` and `USERPROFILE`. Do not override them with real values.
- If the brief, the rules, or the tooling got in your way (an instruction that contradicted another, a check that fired wrongly, a step that cost time for no reason), append one dated line describing it to `docs/BUILDER_NOTES.md`. Do not try to fix the tooling. Do the same for anything you learned about a defect or a pitfall (a cause you found, a platform quirk that cost you a round): one dated line, so the supervisor can carry it forward.
- In any Markdown you write, never break a line inside a paragraph or a list item; one paragraph is one line. Line breaks only between blocks.
- This increment talks to no external service. `gh` is never called.
- **Windowless launches.** Any console process your code launches on Windows is created windowless: `creationflags=NO_WINDOW` through `bridge_env.NO_WINDOW` or plan-check's own `NO_WINDOW` (:56). Capturing output does not prevent the window. In tests, launches take conftest's default, with no `creationflags` argument.
- Never start a server, a watcher or a daemon that outlives a test. Give every subprocess a `timeout`.
- Do not refactor code outside the scope, even if it looks wrong. Inside `bridge_env.py`, change only the reader and what it needs.
- **No live data.** Never run the product, a migration, a seed or a test against the owner's live data. The two read-only runs over this checkout named in Context, "Development data", are the only exception. Never run `pace-report.py --tokens` without `--home` on a temporary folder.
- **The owner's number.** The ceiling's number, 3, is the owner's (2026-10-24, "I choose three"; docs/INVENTORY.md, Decisions). `tests/test_bridge_run_review_ceiling.py` pins `bridge_env.REVIEW_ROUNDS == 3`. `--ceiling` only defaults to it. Do not change the number or that test; report it if the work seems to need a change.
- Follow existing conventions in the files you touch: ASCII-only programs, a `pace-report: ` message prefix, module-level compiled regexes, the shebang, the docstring as the usage text.
- **Git commands.** These git commands are not yours to run: `commit`, `push`, `switch`, `checkout`, `merge`, `rebase`, `reset`, `stash`, `branch -d`, `worktree`. In this Workspace you read with `git status`, `git diff` and `git log` only; `git log -1 --format=%s 9f6ace6` is one of these reads. Your tests may run any git command inside their own temporary repositories.
- **Numbers.** Numbers from text, a file, a record or an argument are parsed with `int` (or `datetime.fromisoformat` / `datetime.strptime` for times), never by slicing or splitting a string. Each value's unit and range are stated in Context, and a value outside its range is rejected.
- **Verification commands.** Run exactly these, from the Workspace root (the folder you were started in). Run only these test files, never the whole suite: the supervisor runs the suite through the launcher.
  - `python -m pytest tests/test_task033_supervisor.py -q -p no:cacheprovider`
  - `python -m pytest tests/test_plan_check.py tests/test_pace_report.py -q -p no:cacheprovider`
  - `python -m pytest tests/test_task032_supervisor_launcher.py tests/test_task032_supervisor_guard.py tests/test_task032_supervisor_r4.py tests/test_bridge_run_review_ceiling.py tests/test_review_guard_ceiling.py tests/test_evaluate_reports.py tests/test_dump_cli.py tests/test_tests_windowless.py -q -p no:cacheprovider`
  - `git diff --quiet 858da29 -- tests/test_task033_supervisor.py` (prints nothing; check that the exit code is 0)
  - `python bridge/cursor-bridge/plan-check.py`
  - `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge/bridge_env.py bridge/cursor-bridge/plan-check.py bridge/cursor-bridge/pace-report.py tests/test_plan_check.py tests/test_pace_report.py`
  - `python tools/dump-cli.py`, then `python tools/dump-cli.py --check`
  - `python tools/make-manifest.py`, last, after every program edit
  - `python bridge/cursor-bridge/bridge-check.py --root bridge --sources` (must end OK)
- **Mutation check, by hand, in your own run.** After the tests pass, apply each mutation below to the code, one at a time. Run `tests/test_plan_check.py`, `tests/test_pace_report.py` and `tests/test_task033_supervisor.py`, and restore the code before the next. List each mutation with the test that caught it, or "survived". No script of this lands in the diff. The mutations:
  1. The parenthesis form back to "any ID inside".
  2. The parenthesis form requiring a single item.
  3. The subject form reading an ID after a leading word (N4 undone).
  4. The Merge form tried before the parenthesis form on a line whose branch maps no ID.
  5. A start taken from the rounds file only, then from the launcher's log only.
  6. A stage review's record counted as a start.
  7. Rounds read from the reports alone.
  8. A duplicated message id summed twice.
  9. `subagents/` records ignored.
  10. A blank mean printed as 0.
  11. The week taken from the author date instead of the committer date.
  12. `--ceiling`'s default as 4.
- Prefer reuse over new code: `bridge_env`'s readers and constants, `evaluate-reports.py`'s `PROJECTS`, `bridge_root`, `project_keys` and `session_files`, and the standard library. Write the minimum that meets the acceptance criteria (the frozen `minimal-code.mdc` is in force). This never overrides a security, observability or accessibility requirement stated above.

## Done
Your report is the file `handoff/TASK-033-r1-report.md`, which you write as you go: what you did, what you changed, what you ran and what it printed, what you could not do. That way nothing is lost if your run ends early. When you finish, it holds:
- a list of every file you changed;
- what you changed, with file:line;
- the reader's final name and signature in `bridge_env.py`;
- how each of the three divergences and N4 now reads;
- every verification command with its pass, fail and skip counts;
- the mutation list with what caught each;
- every test file outside your Scope that fails under your change, and at which lines, without editing it;
- a one-paragraph summary of what you did;
- a section headed exactly `Assumed, not verified`. It lists every fact this change relies on that neither this brief nor the existing code settled, and that you did not confirm. Examples:
  - the exact subject of 9f6ace6, if you could not read it;
  - the transcript record fields beyond `message.id`, `message.usage` and `timestamp`;
  - whether a builder launch row with a non-zero exit counts as a start;
  - how a rounds file of an ID with no brief is treated.

  One item per line: what you assumed · why · what would confirm it. If there are none, write `Assumed, not verified: none`. Be specific: "edge cases" or "error handling" is not an item.

Your last message is the summary and the report file's path, and nothing follows it: the supervisor reads only the last message, and a message printed earlier and then followed by more work is lost.
