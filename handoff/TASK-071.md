---
record: brief
header: 1
id: "TASK-071"
round: 1
satisfies: [R-091]
scope: ["bridge/cursor-bridge/records-migrate.py", "bridge/cursor-bridge/inventory-check.py", "bridge/cursor-bridge/bridge_env.py", "bridge/cursor-bridge/MANIFEST.json", "tests/test_program_run_parameters_empty.py", "tests/test_records_migrate.py", "tests/test_header_run_parameters.py", "tests/fixtures/headers/", "docs/BUILDER_NOTES.md", "handoff/TASK-071-r1-report.md"]
merge_unit: null
blocking_class: null
---
# TASK-071: An empty run parameter is named (R-091)

## Objective
A project's `docs/RUN_PARAMETERS.md` holds five values (Stage pause, Merge authority, Refactoring pass, Installer verification, Parallel increments). Where the file has no YAML header, `bridge_env.run_parameters_fallback` reads each value from a plain line that begins `<Label>: `. A field project wrote its file with headings instead (`## Stage pause` and the value on the next line). The fallback reads every value of that file as `""`. Today `records-migrate.py` then writes a header whose five values are all `""`, and `inventory-check.py` passes the result, because the header and the lines agree on being empty. This increment makes an empty value a named finding in both programs. `records-migrate.py` refuses such a header-less record with one `cannot read` line naming the first empty value, and writes nothing. `inventory-check.py` fails a run-parameters file, headed or not, that has any of the five empty. The fallback itself does not change: it reads no heading, bullet or bold form.

Satisfies: R-091 - An empty run parameter is named, never written (F4, J7, J13): `records-migrate.py` refuses a run-parameters record whose prose leaves any of the five values empty (`cannot read <file>: <name> has no value on a plain line`), the record left header-less; `inventory-check.py` fails a run-parameters file, headed or not, with any of the five empty; the fallback reads no new prose form; the migration's two failure exits not yet covered get their tests; calibration's exit-3 stop and its list of `cannot read` repairs name the new reason and the repair of a file already migrated with empty values. (Its row in `docs/REQUIREMENTS.md` is line 117. This brief serves the two programs and the fallback's limit. The supervisor's acceptance file already holds the tests for the two uncovered exits, and they pass today. The calibration text (J7) and the HARDENING rulings on release B2's leads belong to the supervisor, not to this brief.)

## Scope
Files and directories you may create or modify:
- bridge/cursor-bridge/records-migrate.py
- bridge/cursor-bridge/inventory-check.py
- bridge/cursor-bridge/bridge_env.py
- bridge/cursor-bridge/MANIFEST.json
- tests/test_program_run_parameters_empty.py
- tests/test_records_migrate.py
- tests/test_header_run_parameters.py
- tests/fixtures/headers/
- docs/BUILDER_NOTES.md
- handoff/TASK-071-r1-report.md

Limits on these paths:
- `bridge/cursor-bridge/bridge_env.py`: add one helper that names the empty values, and nothing else (R3). `run_parameters_fallback`, `_run_param_value_token`, `_RUN_PARAM_VALUE_PREFIXES` and every other reader stay byte for byte as they are.
- `tests/test_program_run_parameters_empty.py`: the supervisor's acceptance tests, committed at HEAD (26 cases). Read it whole and run it. **Do not edit it.** If a case seems wrong, stop and report it by its test id.
- `tests/test_records_migrate.py` and `tests/test_header_run_parameters.py`: only the edits described under Context, "Edits allowed in the two existing test files".
- `tests/fixtures/headers/`: one new fixture file (R7). Do not change or delete the nine files already there.
- `bridge/cursor-bridge/MANIFEST.json` changes only by running `python tools/make-manifest.py` (Done), never by hand. `bridge/cursor-bridge/VERSION` is outside Scope. `make-manifest.py` rewrites its line endings, so restore it with `git restore bridge/cursor-bridge/VERSION` right after (Done).

Do not modify anything else.

## Out of scope
- .env and anything under secrets/
- CI configuration
- docs/ and handoff/, except the files the Scope section names. Every record under docs/ is the supervisor's, `docs/RUN_PARAMETERS.md` included.
- `docs/cli-reference.json` and `docs/CLI_REFERENCE.md`: no `--help` text changes in this increment (R6), so they are not regenerated.
- Every other program under `bridge/cursor-bridge/`, the texts under `bridge/commands/`, `bridge/agents/` and `bridge/cursor-bridge/workflow/` (calibration's text included), and `bridge/cursor-bridge/CHANGELOG.md`.
- `tools/make-manifest.py` and `tools/dump-cli.py`: you run them and edit neither.
- Every test file other than the three in Scope. Those named in the Done list's commands must pass unedited. Report a failure there by its test id.
- `run/` (the supervisor's reproduction script and checkpoint output live there; you may read them and write nothing there).
- Any mutation script or mutants file. The mutants file and the mutation run are the supervisor's, after your run.

## Context
**The design that binds this increment.** `docs/DESIGN.md` line 356, the bullet `*F4.*`: "`records-migrate.py` refuses a run-parameters record whose prose leaves any of the five values empty (`cannot read <file>: <name> has no value on a plain line`), the record left header-less; `inventory-check.py` fails a run-parameters file, headed or not, with any of the five empty." Line 311: "The fallback readers of release B2 read no new prose form (F4)." Line 307 records that F4 does not widen the fallback's reading. The plan entry is `docs/BUILD_PLAN.md`, `### TASK-071` (line 1903). Its Scope notes say: "bridge_env.py: no new prose form is read, only the helper that names the empty values; tests/fixtures/headers/: a run-parameters fixture in the field's form, headings in place of plain lines".

**The reproduction (the supervisor's run before this brief, `run/supervisor/task071_repro.py`).** The supervisor used a header-less record in the field's form: `# Run parameters`, `Set: ...`, then for each value a `## <Label>` heading with the value on the next line. On it, `records-migrate.py --check docs/RUN_PARAMETERS.md` prints `would write docs/RUN_PARAMETERS.md` and exits 1. A run writes a header whose five values are all `""`. `inventory-check.py` then prints no finding for the file.

**The fallback as it stands (`bridge/cursor-bridge/bridge_env.py`).**
- `_RUN_PARAM_VALUE_PREFIXES` (lines 470-476) is the one list of the five keys and their plain-line labels, in this order: `("stage_pause", "Stage pause: ")`, `("merge_authority", "Merge authority: ")`, `("refactoring_pass", "Refactoring pass: ")`, `("installer_verification", "Installer verification: ")`, `("parallel_increments", "Parallel increments: ")`. A label as the new lines print it is this prefix without its trailing `: ` (for example `Stage pause`). It is also the schema's order of the five keys in `HEADER_SCHEMAS["run-parameters"]` (line 1841 on).
- `_run_param_value_token(line, prefix)` (lines 856-863) returns the text after the prefix up to the first space, `""` for a line that is the prefix alone, and `None` for a line that does not start with the prefix.
- `run_parameters_fallback(text)` (lines 3049-3133) reads the header-less body (or the body after a header) and returns the nine keys. Each of the five is the first matching plain line's token, or `""` where no line stands.
- `check_header` (line 2500) requires every schema key to be present (`_check_mapping`, "missing key"). So a header that passes `check_header` holds all five keys, and an empty one holds the string `""`.

**`records-migrate.py` as it stands.**
- `main(argv)` (lines 638-780) handles each record in turn. A record that already has a header prints `has a header <shown>` and is skipped (lines 717-723). So the refusal applies to header-less records only.
- The refusals for build plans sit at lines 727-761. `compose_header(kind, text, rel, merged)` (lines 456-481) returns `(header, None)` or `(None, reason)`. `main` prints `cannot read <shown>: <reason>` for a `(None, reason)` and continues (lines 752-754). The run-parameters branch is `return _compose_run_parameters_header(text), None` (line 480), and `_compose_run_parameters_header` (446-453) copies `run_parameters_fallback(text)` into the header.
- Exit rule (lines 776-780): under `--check`, 1 when any record was listed `would write` or `cannot write`, else 0. In a run, 1 when a `cannot write` stands, else 0. A `cannot read` changes neither, and that stays so.
- `<shown path>` is the path as given on the command line for an explicit record, or the relative path from the root when the program enumerates the records. The acceptance tests pass `docs/RUN_PARAMETERS.md`.
- The docstring (lines 2-7) and `build_parser()` (lines 26-31) hold no exit list. They do not change.

**`inventory-check.py` as it stands.**
- `main()` collects failures in the list `fails` and prints them after the notes. The final line, `RESULT: OK` or `RESULT: <n> problem(s)`, counts every entry of `fails` that does not begin with four spaces (line 454). The exit is 1 when `fails` is not empty (line 455). A line you append to `fails` is therefore counted as a problem and gives exit 1. This is where the `SHAPE` failures go too.
- The run-parameters block is lines 325-348. It reads `RUN_PARAMETERS.md` beside the inventory (`os.path.dirname(a.inventory)`). A header that `read_header` cannot read, or that `check_header` rejects, prints `HEADER MALFORMED: ...`, then `RESULT: not checked`, and exits 2. That stays. With a valid header, each key `header_agrees` names becomes `HEADER DISAGREES: <key>`. **With no header, the file is not read at all today**, and this increment adds that reading.
- `_INVENTORY_BRIDGE_NAMES` (lines 82-86) lists every `bridge_env` name the program uses. `_bridge_env_refuse_line()` refuses with `cannot be used` and exit 2 when the loaded `bridge_env` lacks one. A new `bridge_env` name the program calls belongs in that list, so an older `bridge_env` gives that refusal and not an `AttributeError` traceback (`tests/test_header_run_parameters_r2.py::test_r061_r2_inventory_check_refuses_through_its_guard_before_reading_the_run_parameters` holds the guard, with a stub module lacking the names).
- The module docstring (lines 2-30) lists the checks. Add the new failure to that list. `tools/dump-cli.py` records this program from `build_parser()` only (it has a top-level `build_parser`, so its source is `argparse`). The docstring is therefore not in the command reference. Do not change `build_parser()`'s description or any `help=`.

**The supervisor's rulings (they bind; R1-R7 restate them).**
1. `records-migrate.py` refuses a header-less run-parameters record whose `run_parameters_fallback` reading leaves any of the five values empty. It prints exactly one line, `cannot read <shown path>: <label> has no value on a plain line`, where `<label>` is the label as `_RUN_PARAM_VALUE_PREFIXES` spells it without its colon and space, the first empty one in that order. Nothing is written, and no `would write` or `wrote` line is printed for the record, in a run and under `--check`. The exit rule for a `cannot read` is unchanged. You choose where the refusal goes: in `main()`'s per-record flow beside the build-plan refusals, or in `compose_header` returning `(None, reason)` as the build-plan kind does. Name your choice in the report.
2. `inventory-check.py` fails `docs/RUN_PARAMETERS.md` (beside the inventory) with any of the five empty. With a header, it prints `RUN PARAMETERS: <key> is empty` for each empty header key, in the schema's order. With no header, it prints `RUN PARAMETERS: <label> is empty` for each value the fallback leaves empty, in the same order. Each line is a failure counted in `RESULT`, exit 1. A file with all five values passes. This repository's own `docs/RUN_PARAMETERS.md` passes.
3. The fallback reads no new form. `bridge_env.run_parameters_fallback` is unchanged. The only change to `bridge_env.py` is a helper that names the empty values, used by both programs, so the label list lives in one place.
4. `tests/fixtures/headers/` gains a run-parameters fixture in the field's form (headings in place of plain lines). `tests/test_header_run_parameters.py` and `tests/test_records_migrate.py` may be edited only where an existing case depends on migrating or passing a run-parameters record with an empty value, and to use the new fixture.
5. No option is added and no dependency. MANIFEST is regenerated through `tools/make-manifest.py`, with `bridge/cursor-bridge/VERSION` restored after. No `--help` text changes, so the command reference is not regenerated.

**The acceptance tests.** `tests/test_program_run_parameters_empty.py` (26 cases) fixes the interface. Read it whole. Each case builds a scratch Workspace under `tmp_path`. The migration cases run `records-migrate.py docs/RUN_PARAMETERS.md` (or `--check docs/RUN_PARAMETERS.md`) as a subprocess and require all of the following: no `Traceback`, stdout's non-blank lines equal to exactly `[cannot read docs/RUN_PARAMETERS.md: <label> has no value on a plain line]`, exit 0, and the file byte for byte as before. The inventory cases run `inventory-check.py` with no arguments in a scratch Workspace that holds a passing `docs/INVENTORY.md` and no git repository. They read the lines that begin `RUN PARAMETERS`, the exact line `RESULT: <n> problem(s)`, and the exit. In the headed case they also require that no line holds `HEADER`. The two exit-3 cases load the program in-process and replace `builtins.open`. They pass today and must keep passing.

On the checkpoint with the implementation stripped (`run/agent/TASK-071-checkpoint.out`), the file gives `20 failed, 6 passed`. The six that pass today hold what stands: `test_r091_a_complete_plain_line_record_still_migrates`, `test_r091_the_inventory_fixture_passes_on_its_own`, `test_r091_inventory_check_passes_this_repositorys_own_run_parameters`, `test_r091_inventory_check_passes_a_complete_headerless_file`, `test_r091_a_failed_close_of_the_temporary_file_exits_3`, `test_r091_a_failed_read_of_the_temporary_file_exits_3`. After your change all 26 pass.

**The existing tests the supervisor read against the rulings (the reality check before this brief).** Each was read, not run.
- `tests/test_records_migrate.py`: every run-parameters case uses the module's `RUN_PARAMETERS` text (lines 289-300), which holds all five values on plain lines. Those cases are `test_r062_the_runs_own_exit[writes-only]`, `test_r062_given_record_paths_take_only_those`, `test_r062_check_would_write_only_when_write_succeeds[run-parameters]`, the root-enumeration case, and the case around line 586. All should stay green unedited.
- `tests/test_header_run_parameters.py`: the inventory-check cases (lines 397-433) use `PROSE` or a header made from `VALUES`, both with all five non-empty. `changed(key)` replaces a value with another non-empty word. The supervisor found no case that goes red under the rulings. Its docstring's sentence "a file with no header is not its finding" (line 45) is superseded by R-091. It stands above the supervisor's marker and is not a case, so **do not edit it**. The supervisor will.
- `tests/test_header_run_parameters_r2.py`, `tests/test_header_tables.py`, `tests/test_header_tables_r2.py`, `tests/test_header_status.py`, `tests/test_workflows_line_check.py`, `tests/test_b2_least_confident.py`: they run `inventory-check.py`, and none puts a header-less run-parameters file with an empty value beside an inventory. They should stay green.
- `tests/test_program_own_records.py::test_r101_inventory_check_passes_over_this_repository_s_records` runs `inventory-check.py` over this repository. Its `docs/RUN_PARAMETERS.md` has a header with all five values (`run`, `supervisor`, `on`, `n/a`, `on`), and the plain lines repeat them, so it passes the new check.
- `tests/test_header_reader.py` globs `tests/fixtures/headers/*.md` (not recursive) and requires that **every** match starts with `---` and a header that PyYAML reads alike (`test_r057_every_fixture_header_equals_pyyaml`, `test_r057_the_fixtures_hold_one_valid_header_per_kind`). A header-less fixture named `tests/fixtures/headers/<name>.md` would turn these red. See R7.
- `tests/test_header_currency.py` (`test_r057_no_program_keeps_a_retired_reading`, reading 10) and `tests/test_header_run_parameters.py::test_r061_no_program_keeps_a_line_reading_of_its_own` fail a program that holds an `re.` pattern naming a run-parameters label (`Ceiling above twice`, `Agent ceiling`, `Design rounds above five`, `Review rounds above the ceiling`). Name the five labels through the helper. Write no pattern of your own for any label.
- No `RUN_PARAMETERS*` file exists under `tests/`. `tests/fixtures/headers/run-parameters.md` has a header with all five non-empty and is read only by `tests/test_header_reader.py`.

**Edits allowed in the two existing test files.** (a) An existing case that fails after your change because it migrates, or passes through `inventory-check.py`, a run-parameters record with an empty value. The supervisor found none. If you find one, edit only that case's record or assertion, and name it in the report with its test id, why it depended on the empty value, and the diff. (b) Cases of your own that read the new fixture (R7), added **below each file's builder marker**: `tests/test_header_run_parameters.py` line 449 and `tests/test_records_migrate.py` line 1458 (`# ---- builder's cases below this line`). Edit nothing above either marker. A test that fails for any other reason is reported by its test id with its failure lines, and not edited.

**External services.** None. Make no network call.

**Trust boundaries and security context.** ASVS level 2 (`docs/INVENTORY.md`, Decisions, line 140). `.cursor/rules/secure-coding.mdc` is in force for you. Outside input crossing into these programs: the record files' bytes (any text, any encoding, decoded by `bridge_env.decode_record_bytes` or `read` with `errors="replace"`). A value read from a record is never printed by the new lines. They print a fixed label or a schema key only. No exception may escape as a traceback. Both programs keep their present exits for malformed input (2) and for a failed write (3).

**Development data.** The inventory's decision (`docs/INVENTORY.md`, Decisions, line 135) reads: "the dev build is the Workspace sources under `bridge/`; a session in the repo always runs the *installed* bridge (`~/.claude`), never the one being edited, and installs reach running projects only through the owner's install run sheet". For you this means: run `records-migrate.py` only through the tests, on their scratch Workspaces under `tmp_path`. Never run it in this repository, because a run would write headers into its records. `inventory-check.py` reads only, and the one test that runs it here (`test_program_own_records.py`) is the only run over this repository. Never install anything, and never copy anything under `~/.claude` or `~/.cursor-bridge`.

**Host.** Windows 11 with the owner's Python. CI also runs on Linux.

## Diagrams
None. The plan entry names no diagram for this increment.

## Requirements
1. **R1. The migration refuses an empty value.** For a header-less record of kind `run-parameters`, when the fallback leaves any of the five values empty, `records-migrate.py` prints exactly `cannot read <shown path>: <label> has no value on a plain line`, naming the first empty one in `_RUN_PARAM_VALUE_PREFIXES`' order. It prints no other line for that record, writes nothing, and creates no temporary file. This holds in a run and under `--check`. The exit rule is unchanged: a refused record alone leaves exit 0 in both modes. A record with all five values migrates exactly as today. The `has a header` path for a headed record is unchanged.
2. **R2. The inventory check fails an empty value.** In `inventory-check.py`'s run-parameters block:
   - With a valid header: one `RUN PARAMETERS: <key> is empty` line for each of the five keys whose header value is empty, in the schema's order. This comes beside, not in place of, the existing `HEADER DISAGREES` lines.
   - With no header: one `RUN PARAMETERS: <label> is empty` line for each of the five the fallback leaves empty, in the same order.

   Each line goes into `fails`, so it is counted in `RESULT: <n> problem(s)` and the exit is 1. A malformed header keeps its `HEADER MALFORMED` and exit 2, before any of this. A file with all five passes, and so does this repository's own file. A missing `RUN_PARAMETERS.md` is still no finding.
3. **R3. One helper, one list.** `bridge_env.py` gains one helper that, given the fallback's or a header's values, names the empty ones with key and label in the prefixes' order. It derives the labels from `_RUN_PARAM_VALUE_PREFIXES`, so no second copy of the five labels exists in either program. Both programs call it. `inventory-check.py` adds its name to `_INVENTORY_BRIDGE_NAMES`. Nothing else in `bridge_env.py` changes. A value is empty when it is the empty string `""`. This is what the fallback gives for no plain line, or for a line that is the label and nothing after it, and what a header gives as `""`.
4. **R4. No new form is read.** A value under a `## <label>` heading, in a bullet (`- Stage pause: run`) or in bold (`**Stage pause:** run`) stays empty, as the fallback reads it today, so such a record is refused (R1) and fails the check (R2).
5. **R5. The two exit-3 paths stand.** `_write_record`'s failed close of the temporary file and its failed read back keep their lines, their exit 3, and their removal of the temporary file (`test_r091_a_failed_close_of_the_temporary_file_exits_3`, `test_r091_a_failed_read_of_the_temporary_file_exits_3`).
6. **R6. No interface change.** You add no option, configuration key, environment variable or dependency. `build_parser()` in both programs is unchanged, so `python tools/dump-cli.py --check` exits 0. `inventory-check.py`'s module docstring names the new failure in its list of checks.
7. **R7. The field's fixture.** Add one run-parameters fixture under `tests/fixtures/headers/` in the field's form: a header-less record whose five values each stand under a `## <Label>` heading in place of a plain line. It is read by at least one case of yours (below a builder marker, Context) that runs `records-migrate.py` on it and asserts the `Stage pause` refusal and the unchanged bytes. Because `tests/test_header_reader.py` requires every `tests/fixtures/headers/*.md` to begin with a header, the fixture's path must not match that glob (a subfolder of `tests/fixtures/headers/` or a name not ending in `.md`). Name the path you chose in the report.

## Acceptance criteria
- [ ] `tests/test_program_run_parameters_empty.py` passes whole, unedited (26 cases).
- [ ] `tests/test_records_migrate.py` and `tests/test_header_run_parameters.py` pass. Any edit is of a kind Context allows and is named in the report.
- [ ] Every other test file in the Done list's commands passes unedited, `tests/test_header_reader.py` among them.
- [ ] A header-less record with any value empty is refused with the one `cannot read ... has no value on a plain line` line, the first empty label, unchanged bytes, unchanged exit, in a run and under `--check` (R1, R4).
- [ ] `inventory-check.py` prints `RUN PARAMETERS: <key> is empty` per empty header key and `RUN PARAMETERS: <label> is empty` per empty header-less value, counted in `RESULT`, exit 1. Complete files and this repository's own file pass (R2).
- [ ] `run_parameters_fallback` is unchanged. One helper in `bridge_env.py` derives the labels from `_RUN_PARAM_VALUE_PREFIXES`, and both programs use it (R3).
- [ ] The field-form fixture exists outside the `tests/fixtures/headers/*.md` glob and a case of yours reads it (R7).
- [ ] `python tools/dump-cli.py --check` exits 0. MANIFEST is regenerated. `bridge/cursor-bridge/VERSION` is not listed by `git status --short`. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` prints `RESULT: SOURCES MATCH`.
- [ ] `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks` passes.
- [ ] The three changed programs stay ASCII, and every line you add anywhere is ASCII.
- [ ] R-091 (the parts this brief serves) is fully met, with no stand-in, placeholder or "later" text. The tests naming R-091 are the supervisor's acceptance tests. Your fixture case names R-091 in its docstring.
- [ ] No new dependency, option, configuration key or environment variable. No new Semgrep high finding. No exception escapes as a traceback (ASVS L2).

## Constraints
- Do not add dependencies (the standard library and the pytest already used only).
- Do not read or write any file outside this workspace (the folder you were started in). Everything you need is inside it, and everything you produce goes inside it.
- Do not edit `tests/test_program_run_parameters_empty.py`, anything above the builder marker of the two existing test files (beyond an edit of kind (a) in Context), or anything else outside Scope. If a test case seems wrong, stop and report it by its test id instead of working around it.
- If the brief, the rules, or the tooling got in your way (an instruction that contradicted another, a check that fired wrongly, a step that cost time for no reason), append one dated line describing it to `docs/BUILDER_NOTES.md`. Do not try to fix the tooling. Do the same for anything you learned about a defect or a pitfall (a cause you found, a platform quirk that cost you a round): one dated line, so the supervisor can carry it forward.
- In any Markdown you write, never break a line inside a paragraph or a list item. One paragraph is one line. Line breaks only between blocks.
- **No owner's names, no paths.** Nothing you write (code, the notes line, the report, the fixture) holds a path of this computer or a user name. In the report write `<Workspace>` for the repository folder and `<tmp>` for a temporary folder, including in quoted command output.
- This increment talks to no external service. Do not add a call to any service or the network.
- Any console process your code launches on Windows is created windowless (`creationflags=subprocess.CREATE_NO_WINDOW` in Python, `0` on other platforms). This increment needs no new process. Start none.
- Never start a server, a watcher or a daemon that outlives a test. Run every command synchronously, in the foreground, and wait for it to end. Leave nothing running when you finish.
- Do not refactor code outside the scope, even if it looks wrong.
- Never run the product, a migration, a seed or a test against the owner's live data (Context, "Development data"). Never run `records-migrate.py` in this repository. Only the tests run it, on their scratch Workspaces.
- A value the brief marks as the owner's: none in this increment. Do not edit `docs/RUN_PARAMETERS.md`.
- Follow existing conventions in the files you touch: ASCII program text, `main()` returning the exit code, `cannot read <shown>: <reason>` lines for a record passed over, failures appended to `fails` in `inventory-check.py`, `bridge_env` as the one home of a record's reading.
- These git commands are not yours to run: `commit`, `push`, `switch`, `checkout`, `merge`, `rebase`, `reset`, `stash`, `branch -d`, `worktree`. You read with `git status`, `git diff` and `git log` only. The single exception is `git restore bridge/cursor-bridge/VERSION` in the Done section.
- Numbers: none are parsed by this increment. The five values are strings compared with `""`. Parse nothing from a record by slicing beyond what `bridge_env`'s readers already do.
- Every verification command the Done section asks you to run is written there in full. Run exactly those. **Do NOT run the whole `tests/` tree** (`python -m pytest`, `python -m pytest tests`, or any command that collects all of it): the whole suite is CI's run.
- **Mutation self-check (by hand, in process, no script in the diff).** The supervisor's mutants file sweeps your change after your run. Before you finish, apply each of these by hand, one at a time, run the command given, and revert. Confirm with `git diff` that each revert is exact. List each in the report by its label and text, with the pytest summary line and the id of a test it made fail. If one is not caught, write `not caught` and one line on the case that would catch it (do not add that case):
  - H1 one of the five values (your choice, named) exempted from the refusal in `records-migrate.py` (an empty value of that key migrates as today). Command: `python -m pytest -p no:cacheprovider -q tests/test_program_run_parameters_empty.py`.
  - H2 the header's empty-value check skipped in `inventory-check.py` (a headed file with empty values passes). Command: as H1.
  - H3 the header-less empty-value check skipped in `inventory-check.py` (a header-less file is not read for it, as today). Command: as H1.
- **Known failures.** Context lists the acceptance cases that fail before your change. If a case fails that your change did not cause, report it by its test id with its failure lines and fix none.
- Prefer reuse over new code: `run_parameters_fallback`, `_RUN_PARAM_VALUE_PREFIXES`, `compose_header`'s `(None, reason)` path or `main`'s `cannot read` line, and `inventory-check.py`'s `fails` list. Write the minimum that meets the acceptance criteria (the frozen `minimal-code.mdc` is in force). This never overrides a security, observability or accessibility requirement stated above.
- Rules in force for you: `.cursor/rules/secure-coding.mdc`, `.cursor/rules/workspace-boundary.mdc` and the frozen `minimal-code.mdc`.

## Done
Your report is the file `handoff/TASK-071-r1-report.md`, which you write as you go: what you did, what you changed, what you ran and what it printed, and what you could not do, so that nothing of it is lost if your run ends early. It names no computer path and no user name: write `<Workspace>` for the repository folder and `<tmp>` for a temporary folder, including in quoted command output.

When you finish, it holds:
- a list of every file you changed or created;
- a one-paragraph summary of what you did;
- for R1-R7, one line each on what meets it, naming the functions and their lines as the files stand after your change. For R1, also where you placed the refusal (`main()` or `compose_header`) and why. For R3, the helper's name and signature. For R7, the fixture's path and the test id of the case that reads it;
- every edit to `tests/test_records_migrate.py` or `tests/test_header_run_parameters.py`: the test id, its kind ((a) or (b) of Context), the reason and the diff;
- the mutation self-check list, H1-H3, each with its pytest summary line and the test id that caught it (or `not caught` and the case that would);
- every command of the list below with its output;
- a section headed exactly `Assumed, not verified`, as the report's last section.

The `Assumed, not verified` section lists every fact this change relies on that neither this brief nor the existing code settled, and that you did not confirm. Examples: whether a header value of spaces only counts as empty; whether a record with a BOM or CRLF endings reads alike in the refusal; how a header-less file with an empty value and a disagreeing lift line is listed. One item per line: what you assumed · why · what would confirm it. If there are none, write `Assumed, not verified: none`. Be specific: "edge cases" or "error handling" is not an item.

Run these from the Workspace root, in this order, after your last edit, each on its own, synchronously in the foreground, with no `PYTHONPATH` or other environment change:
1. `git status --short`
2. `python tools/make-manifest.py`
3. `git restore bridge/cursor-bridge/VERSION`
4. `python -m pytest -p no:cacheprovider -q -rs tests/test_program_run_parameters_empty.py tests/test_records_migrate.py tests/test_header_run_parameters.py`
5. `python -m pytest -p no:cacheprovider -q -rs tests/test_header_run_parameters_r2.py tests/test_bug044.py tests/test_program_own_records.py tests/test_release_b2_records.py tests/test_header_reader.py tests/test_header_currency.py`
6. `python -m pytest -p no:cacheprovider -q -rs tests/test_header_tables.py tests/test_header_tables_r2.py tests/test_header_status.py tests/test_workflows_line_check.py tests/test_b2_least_confident.py tests/test_text_consistency.py tests/test_dump_cli.py`
7. `python tools/dump-cli.py --check` (expect exit 0)
8. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` (expect `RESULT: SOURCES MATCH`)
9. `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks`
10. `python -c "[open(p,'rb').read().decode('ascii') for p in ('bridge/cursor-bridge/records-migrate.py','bridge/cursor-bridge/inventory-check.py','bridge/cursor-bridge/bridge_env.py')]; print('ascii ok')"` (expect `ascii ok`)
11. `git rev-parse HEAD` and `git status --short` (`bridge/cursor-bridge/VERSION` must not be listed; if it is, report it)

Commands 5 and 6 cover every other test file that runs `records-migrate.py` or `inventory-check.py`, loads either, or reads `tests/fixtures/headers/`. Every file in them is outside Scope, and a failure in any of them is reported by test id, never fixed in that file.

Quoting rules:
- Every command you ran is quoted in the report with the lines it printed, verbatim, in a fenced block.
- Each pytest summary line is quoted verbatim in a fenced block. Never restate a count in prose.
- A claim that a check passed quotes the output line that shows it. A number of failing or skipped cases is backed by the pytest lines naming them (`-rs` prints each skip's reason).
- Each mutation is listed by its label and text, with what caught it.
- A command you did not run is written `not run`, never described as run.
- Write the report's results after step 11, naming the commit its counts belong to (`git rev-parse HEAD`) and whether the working tree then held uncommitted changes (`git status --short`).

Your last message is the summary and the report file's path, and nothing follows it. The supervisor reads only the last message, and a message printed earlier and then followed by more work is lost.
