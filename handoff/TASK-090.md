---
record: brief
header: 1
id: "TASK-090"
round: 1
satisfies: [R-112]
scope: ["bridge/cursor-bridge/bridge-run.py", "bridge/cursor-bridge/MANIFEST.json", "tests/test_improve_launcher_small.py", "tests/test_program_review_rows.py", "docs/cli-reference.json", "docs/CLI_REFERENCE.md", "docs/BUILDER_NOTES.md", "handoff/TASK-090-r1-report.md"]
merge_unit: null
blocking_class: null
---
# TASK-090: The launcher's small repairs

## Objective
The launcher, `bridge/cursor-bridge/bridge-run.py`, gets four small repairs. First, a run that is not a watch and ends at its limit must leave no pid file under `run/launcher/pids/`. Today the branch that is not a watch calls `killer()` before it removes the pid file, and on Windows `killer()` ends the launcher too (the job object), so the file is left behind. The watch's branch already removes the file first. Second, the child of a driver run or a test run gets `PYTHONIOENCODING=utf-8` where the environment it would get has none, and keeps any value the caller set. Builder, review and watch runs are unchanged, and no kind ever sets `PYTHONUTF8`. Third, when a `--kind test` launch is refused and the command is one the driver kind would accept (a python program under `<launch folder>/run/supervisor/`, or the installed mutation engine), the refusal names `--kind driver`. Fourth, the usage text and the module docstring say what a stripped run no longer sees, and how a driver that needs the owner's key file is launched. Everything else stays as it is on the checkpoint: `merge_ids` is already written sorted, and no environment name moves the run record or the pid folder.

Satisfies: R-112

That row of `docs/REQUIREMENTS.md` reads: "The launcher's small repairs (C36, C37, C54's first part, T74): it removes its pid file before it ends a run at its limit, and a test holds the real run record and pid folder untouched by every test file that names the launcher; a driver's or a test's child gets `PYTHONIOENCODING=utf-8` where the caller set none, and `merge_ids` stays written sorted; the refusal of a test launch names the driver kind where the command is a program under `run/supervisor/` or the installed mutation engine; the help text names the owner's folders a stripped run no longer sees." You change no record of the row. R-112 stays `planned` until TASK-096, and the supervisor's records commit writes it.

## Scope
Files and directories you may create or modify:
- bridge/cursor-bridge/bridge-run.py
- bridge/cursor-bridge/MANIFEST.json
- tests/test_improve_launcher_small.py
- tests/test_program_review_rows.py
- docs/cli-reference.json
- docs/CLI_REFERENCE.md
- docs/BUILDER_NOTES.md
- handoff/TASK-090-r1-report.md

Do not modify anything else.

Limits on these paths:
- `tests/test_improve_launcher_small.py` is the supervisor's acceptance file. `tests/test_program_review_rows.py` holds the supervisor's widened guard test, `test_r079_the_launcher_tests_write_no_row_into_the_checkout`. Both files were committed at the checkpoint and are listed in Scope only because the plan lists them. Read both and run both. **Do not edit either one.**
- `bridge/cursor-bridge/MANIFEST.json` changes only by running `python tools/make-manifest.py`. `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` change only by running `python tools/dump-cli.py`. Never edit any of the three by hand (Done).
- `docs/BUILDER_NOTES.md`: add new dated lines at its end only.
- In `bridge-run.py`, change only what Requirements 1 to 4 need.

## Out of scope
- .env and anything under secrets/
- CI configuration
- `docs/` and `handoff/`, except the files the Scope section names. `docs/REQUIREMENTS.md`, `docs/HARDENING.md` and `docs/PROJECT_STATUS.md` are the supervisor's records, written in its records-only commit.
- `bridge/cursor-bridge/bridge_env.py`, including `stripped_env`. The encoding default is set in `bridge-run.py`.
- Every other program under `bridge/`, every text under `bridge/commands/`, `bridge/agents/` and `bridge/cursor-bridge/workflow/`, and `bridge/cursor-bridge/VERSION`, which must come out unchanged.
- Every test file. That includes the two in Scope, `tests/test_program_launcher_forms.py` (its test that the launcher sets no `PYTHONUTF8`) and the existing test that holds `merge_ids` sorted. It also includes `tools/make-manifest.py` and `tools/dump-cli.py`: you run them and edit neither.
- The rest of C54: the `interpreters` list in `project.json` and the `jscpd` driver word are later work. Add neither.
- Every option of the launcher: none is added, removed or renamed. No acceptance rule is added or widened.
- Every brief under `handoff/` other than your report.

## Context
Line numbers are those of `3973eb7`. The supervisor's checkpoint commit adds only the two test files and this brief, so they still hold.

- **The limit branch that is not a watch** (`bridge-run.py`). Line 3782: `pid_file = write_pid_file(folder, run_id, os.getpid(), proc.pid)`. The handler `except subprocess.TimeoutExpired:` runs from line 3786 to line 3804: it sets `timed_out`, writes the `LIMIT` line, calls `report_git_config()` and `report_boundary()`, writes `bridge-run: exit 124`, flushes, updates `entry`, calls `write_log(folder, entry)` (commented "before the job ends this process too"), then reaches `try: killer()` at line 3797 (commented "on Windows this ends this process too, with exit code 124"), then `proc.wait(timeout=30)` / `proc.kill()`, then `rc = 124`. The pid file is removed only at line 3805, after the try block: `remove_pid_file(pid_file or reserved_pid_file)`. `reserved_pid_file` is set at lines 3518 to 3534 through `create_pid_file_exclusive(folder, run_id)`.
- **The watch's limit branch** (lines 3716 to 3735) already has the right order. Line 3725 is `remove_pid_file(box["pid_file"])  # before killer(); on Windows the job ends this process`, line 3727 is `killer()`, and line 3734 removes the file again.
- **The pid helpers.** `write_pid_file` (line 1713), `remove_pid_file(path)` (line 1728) and `create_pid_file_exclusive` (line 1736) read no environment. `remove_pid_file` ignores a missing file, so a second removal is harmless. `write_log` is at line 1044.
- **The child's environment.** Line 3578: `env = bridge_env.stripped_env(is_agent=is_agent) if (is_agent or strip) else dict(os.environ)`, with `strip = "--strip" in flags` at line 3571. Lines 3582 to 3589 add a key file's names where `--key-file` is given. A key file is refused for the driver kind at lines 3387 to 3389, and for `cursor-agent`. `stripped_env` (`bridge_env.py` line 285) copies the caller's environment and passes `PYTHONIOENCODING` through. Of `PYTHONUTF8`, `bridge-run.py` holds no string today. `tests/test_program_launcher_forms.py` (`test_r078_a_suite_launched_with_both_flags_runs_with_them_and_no_pythonutf8`, `test_r078_a_driver_launched_with_both_flags_runs_its_program_with_them`) holds that the launcher sets no `PYTHONUTF8`.
- **`merge_ids`.** Line 1604, `"merge_ids": tuple(sorted(declared)),`, is already sorted. Make no change.
- **The test kind's refusal.** Lines 3379 to 3396: for `kind == "driver"`, `driver_prog = resolve_driver_program(cmd, folder)`, and `DRIVER_REFUSE` (line 127) where it is None. Otherwise, `elif not accepted(cmd, folder):` writes either `known_runner_refusal(cmd, folder)` (line 541) or the generic line at 3395, which starts `bridge-run: refused - the launcher runs only cursor-agent, gh pr checks and the test suites it knows by name ...` and ends `... marked # wake`. In both cases it returns 125. `resolve_driver_program(argv, folder=None)` is at line 618 and `driver_accepted(argv, folder=None)` at line 640. They accept `python <program>.py` under the launch folder's `run/supervisor/` (no link on the path), or the installed `~/.claude/cursor-bridge/mutation-run.py`, given absolute or in the `~/` form (`_program_abs`, line 554; `_mutation_run_path`, line 550). Several existing tests check that the generic line *starts* with `bridge-run: refused - the launcher runs only cursor-agent`: `tests/test_bridge_run_driver.py` lines 447 and 550, `tests/test_bug029_agent_name.py` line 102, and `tests/test_program_launcher_forms.py` line 683 (`line.startswith(UNKNOWN) and "# wake" in line`).
- **The help texts.** `usage()` is at lines 159 to 162 and returns 2. `main` calls it where `--limit` or `--` is missing (lines 3372 to 3377). The module docstring runs from line 2 to line 106, and lines 101 to 103 describe `--strip`. `tools/dump-cli.py` builds the command reference from the program, so a docstring change shows up in `docs/cli-reference.json` and `docs/CLI_REFERENCE.md`. The docstring is ASCII by design (line 105, "ASCII-only on purpose (cp1252 consoles)"). `stripped_env` gives the run its own home folder and its own `APPDATA` and `LOCALAPPDATA` (its docstring, `bridge_env.py` lines 286 to 291).
- **Environment names.** Of its own names, the launcher reads only `BRIDGE_RUN_ALLOW_ANY` (lines 1037, 3458, 3465, 3540) and `BRIDGE_RUN_SLOT_SCALE` (lines 1922, 3464). `test_r112_the_launcher_reads_no_environment_name_but_its_two_test_names` checks that every `BRIDGE_\w+` in the *whole source, docstring included* is one of these two.
- **The acceptance tests**, `tests/test_improve_launcher_small.py`. By the brief writer's reading there are 27 tests; pytest's collection gives the real count. Their fixture `lab` builds a launch folder with `run/supervisor/`, plus a home folder of its own (`HOME`/`USERPROFILE`), so the heavy slot and the mutation engine are the test's own. By reading, not by a run, these are expected red on the checkpoint on Windows:
  - `test_r112_a_run_ended_at_its_limit_leaves_no_pid_file[test]`, `[driver]`, `[builder]`
  - `test_r112_every_limit_branch_removes_the_pid_file_before_it_ends_the_tree`
  - `test_r112_a_driver_s_child_gets_utf_8_where_the_caller_set_none[False]`, `[True]`
  - `test_r112_a_test_s_child_gets_utf_8_where_the_caller_set_none[False]`, `[True]`
  - `test_r112_a_test_launch_of_a_supervisor_program_names_the_driver_kind`
  - `test_r112_a_test_launch_of_the_installed_mutation_engine_names_the_driver_kind`
  - `test_r112_the_usage_text_names_the_owner_s_folders_a_stripped_run_does_not_see`
  - `test_r112_the_docstring_names_them_too`

  The rest are controls that must keep passing. Done step 2 records the real split.
- **The source checks.** `_limit_handlers` finds every `except ... .TimeoutExpired:` handler whose body calls `killer()`. In each one, a top-level statement that calls `remove_pid_file(...)` must come before the first top-level statement that calls `killer()`. `test_r112_the_launcher_sets_no_pythonutf8` checks that no string constant outside a docstring holds `PYTHONUTF8`. A comment may name it.
- **The help-text test.** It lowercases the text and collapses whitespace, then looks for each of `appdata`, `localappdata`, `home folder`, `unstripped`, `key file`, `recorded decision` and `driver`. It runs on the usage text, which must also still hold `usage: bridge-run.py` and `--strip` and exit 2, and on the module docstring, which it loads through the `program` fixture of `tests/conftest.py`.
- **The widened guard test**, `tests/test_program_review_rows.py::test_r079_the_launcher_tests_write_no_row_into_the_checkout`. `launcher_tests()` (line 35) lists every `tests/test_*.py` whose text matches `bridge[-_]run`, apart from that file itself (about 52 files). `pid_folder_state()` (line 47) reads every file's name and bytes under the checkout's `run/launcher/pids/`. The test runs all the listed files in one `python -m pytest -p no:cacheprovider -q` subprocess, with `BRIDGE_RUN_ALLOW_ANY` and `BRIDGE_RUN_SLOT_SCALE` removed and a timeout of 10800 seconds. It requires ` passed` in the output, the checkout's `run/launcher/runs.jsonl` byte-identical, and the pid folder's state unchanged. It is skipped where the checkout has no `run/` folder, as in CI; this checkout has one, so it runs. It takes long, so run it once, at the end (Done step 11). Your own run's pid file sits in that folder throughout and is unchanged by it.
- **Trust boundary and security level.** The launcher's acceptance rules are a security boundary: whatever it starts runs with the caller's rights, or the stripped environment. A command line is text a builder or a reviewer can write. The hint of Requirement 3 is text only: the run is still refused with exit 125 and nothing starts. The project's ASVS level is 2 (`docs/INVENTORY.md`). Rules in force for you: `.cursor/rules/secure-coding.mdc`, `.cursor/rules/workspace-boundary.mdc` and the frozen `minimal-code.mdc`.
- **Development data** (`docs/INVENTORY.md`): "Development data: the dev build is the Workspace sources under `bridge/`; a session in the repo always runs the *installed* bridge (`~/.claude`), never the one being edited, and installs reach running projects only through the owner's install run sheet". What this means for you: never run `bridge/cursor-bridge/bridge-run.py` yourself against this repository. Every launcher run is a test's, inside its own temporary launch folder.
- This increment talks to no external service and changes no Claude Code host behaviour.

## Diagrams
None: the plan names no diagram for this increment.

## Requirements
1. **The pid file at a limit (C36).** In the limit branch that is not a watch (the handler at lines 3786 to 3804), remove the run's pid file (`pid_file or reserved_pid_file`) after `write_log(folder, entry)` and before the statement that calls `killer()`, as the watch's branch does at line 3725. Keep the removal after the try block (line 3805). With the change, a test, driver or builder run that ends at its limit leaves `run/launcher/pids/` empty, still exits 124, still writes the `LIMIT` line and `bridge-run: exit 124` as its last line, and still writes its record row with `"exit": 124`. The watch's branch keeps its order.
2. **The child's encoding (C37).** For `--kind driver` and `--kind test` only, the environment handed to the child holds `PYTHONIOENCODING=utf-8` where it has no `PYTHONIOENCODING`. Where it has one, that value is kept unchanged. This holds whether the caller set it in its own environment (with or without `--strip`) or, for the test kind, in a key file. Builder, review and watch runs get exactly the environment they get on the checkpoint. No string constant of the launcher names `PYTHONUTF8`, and no kind sets it. The default is set in `bridge-run.py`, not in `bridge_env.py`.
3. **The refusal's hint (C54, first part).** Where a `--kind test` launch is refused (either the `known_runner_refusal` line or the generic line at 3395), and `resolve_driver_program(cmd, folder)` (or `driver_accepted`) says the driver kind would accept the command, the refused text names `--kind driver`. Put it either on the refusal line itself or on one more line right after it that also starts with `bridge-run: refused`. The run still exits 125 and nothing starts. The existing line keeps its start (`bridge-run: refused - the launcher runs only cursor-agent` for the generic line) and its `# wake` ending. A refused program the driver kind would not accept, such as `python tools/y.py`, gets a refusal that names no kind, exactly as on the checkpoint. Use the existing resolver. Add no acceptance rule and no new path check. Refusals of other kinds, and of a launch without `--kind`, are unchanged.
4. **The help text (T74).** Both `usage()` and the module docstring must say, in ASCII, the following:
   - A stripped run (`--strip`, and every `cursor-agent` run) sees none of the owner's files under `APPDATA`, `LOCALAPPDATA` or the home folder, because it gets a home folder and app folders of its own.
   - A driver that needs the owner's key file (a key file is refused for the driver kind) is launched unstripped, under a recorded decision.

   Both texts must hold the words the help-text test checks (Context). The usage text still starts `usage: bridge-run.py`, still names `--strip`, and still returns 2. Write no `BRIDGE_` name other than the two existing ones anywhere in the file.
5. **Nothing else changes.** `merge_ids` stays `tuple(sorted(declared))`. No environment name moves the run record or the pid folder: add no read of the environment to `write_log`, `write_pid_file`, `remove_pid_file` or `create_pid_file_exclusive`, and no new `BRIDGE_` name. No option is added or removed, and no dependency or new import. `bridge-run.py` stays ASCII. Every existing output line form is kept.

## Acceptance criteria
- [ ] Every test of `tests/test_improve_launcher_small.py` passes, the file unedited. Its module docstring names R-112.
- [ ] `tests/test_program_review_rows.py::test_r079_the_launcher_tests_write_no_row_into_the_checkout` passes, the file unedited. The checkout's real `run/launcher/runs.jsonl` and `run/launcher/pids/` are untouched by every test file that names the launcher.
- [ ] Every test of `tests/test_bridge_run.py`, `tests/test_bridge_run_driver.py`, `tests/test_program_launcher_forms.py`, `tests/test_release_s_launcher.py`, `tests/test_bridge_run_slot.py`, `tests/test_tests_windowless.py` and `tests/test_bug029_agent_name.py` passes, or is skipped by its own condition, each file unedited. A test whose expectation the change alters is not edited. Name it in the report by id, with its failure lines, as a changed expectation for the supervisor to review. A failure you did not cause is reported by test id, not fixed.
- [ ] `python tools/dump-cli.py --check` passes after `python tools/dump-cli.py`. MANIFEST is regenerated after the last edit under `bridge/`. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` prints `RESULT: SOURCES MATCH`. `bridge/cursor-bridge/VERSION` is unchanged and not listed by `git status --short`.
- [ ] Every requirement under "Satisfies" is fully met, with no stand-in, placeholder or "arrives in a later stage" text.

## Constraints
- Do not add dependencies.
- Do not read or write any file outside this workspace (the folder you were started in). Everything you need is inside it; everything you produce goes inside it.
- Write the report as you go, so that nothing is lost if the run ends early.
- No secret is needed or used. Nothing you write (code, the notes line, the report) may hold a path of this computer or a user name. Write `<Workspace>`, `<tmp>` and `~` instead, also in quoted output.
- Do not edit any test file. If an acceptance test and this brief seem to disagree, stop and report it by its test id. Do not work around it.
- If the brief, the rules, or the tooling got in your way - an instruction that contradicted another, a check that fired wrongly, a step that cost time for no reason - append one dated line describing it to `docs/BUILDER_NOTES.md`. Do not try to fix the tooling. Do the same for anything you learned about a defect or a pitfall (a cause you found, a platform quirk that cost you a round): one dated line, so the supervisor can carry it forward.
- In any Markdown you write, never break a line inside a paragraph or a list item; one paragraph is one line. Line breaks only between blocks.
- This increment talks to no external service. Add no call to any service or to the network.
- Any console process your code launches on Windows is created windowless (`creationflags=subprocess.CREATE_NO_WINDOW` in Python, `0` on other platforms). You are not expected to add any process launch.
- Never start a server, a watcher or a daemon that outlives a test. Run every command synchronously, in the foreground, and wait for it to end. Leave nothing running.
- Do not refactor code outside the scope, even if it looks wrong.
- Never run the product, a migration, a seed or a test against the owner's live data (Context, "Development data").
- No value in this increment is the owner's (rule 52). `utf-8` is the design's value (C37).
- Follow existing conventions in the file you touch: ASCII program text, refusal lines written to stderr starting `bridge-run: refused`, and the existing output line forms kept.
- These git commands are not yours to run: `commit`, `push`, `switch`, `checkout`, `merge`, `rebase`, `reset`, `stash`, `branch -d`, `worktree`. You read with `git status`, `git diff` and `git log` only. The one exception is `git restore bridge/cursor-bridge/VERSION` in Done step 5.
- Numbers: no number is read from text in this increment.
- **A probe runs only as a test.** Run no Python other than the Done section's commands: no script of your own, no here-document, and no `python -c` other than step 9's. Where you need a scratch check, write it as a test file under `tests/` named `test_task090_scratch_*.py`, run it with `python -m pytest -p no:cacheprovider -q <that file>`, and delete it. Note that such a file must not name the launcher's file name, or the guard test would pick it up. None may stay in the diff. The report names each one, what it showed, and that it was deleted.
- Run the tests directly, with `python -m pytest -p no:cacheprovider -q` as Done lists, not through `bridge-run.py`. Run only the files Done names. **Do NOT run the whole `tests/` tree**: the whole suite is CI's run.
- **Mutation: name the code points, run nothing.** For each label below, the report gives the function and lines (as the file stands after your change) that the mutation would touch, and the test id you expect to catch it. Where no test of the files Done names would catch a mutation, say so for that label.
  - M1: the new `remove_pid_file` call before `killer()` in the branch that is not a watch is deleted.
  - M2: the encoding default is applied to every kind.
  - M3: the default overwrites a value that was already set.
  - M4: the default is set only on the stripped path.
  - M5: the `--kind driver` hint is given for every refused test launch.
  - M6: the hint is computed without the `~/` form of the mutation engine.
  - M7: the help words are removed from the docstring only.
- **Known failures.** The acceptance file is red on the checkpoint (Context). If any other test fails that your change did not cause, report it by test id with its failure lines, and fix none.
- Prefer reuse over new code - the existing helpers, the standard library - and write the minimum that meets the acceptance criteria (the frozen `minimal-code.mdc` is in force). This never overrides a security, observability, or accessibility requirement stated above.

## Done
Your report is the file `handoff/TASK-090-r1-report.md`, which you write as you go: what you did, what you changed, what you ran and what it printed, and what you could not do, so that nothing of it is lost when your run ends early. When you finish, it holds:
- a list of every file you changed;
- a one-paragraph summary of what you did;
- for Requirements 1 to 5, one line each naming the lines that meet it;
- the code points of M1 to M7;
- every changed expectation, or `no changed expectation`;
- every scratch test file, or `no scratch test file`;
- a section headed exactly `Assumed, not verified`, which is the report's last section.

That last section lists every fact this change relies on that neither this brief nor the existing code settled, and that you did not confirm. Examples: whether a key file's `PYTHONIOENCODING` counts as the caller's, whether the hint should also reach a refusal from `known_runner_refusal`, or how the help text's wording fits the command reference. One item per line: what you assumed · why · what would confirm it. If there are none, write `Assumed, not verified: none`. Be specific: "edge cases" or "error handling" is not an item.

Run these from the Workspace root, each on its own, synchronously in the foreground, with no `PYTHONPATH` or other environment change. Steps 1 and 2 come before your first edit. Steps 3 to 13 come after your last edit, in this order:
1. `git status --short`
2. `python -m pytest -p no:cacheprovider -q tests/test_improve_launcher_small.py` (quote the summary line and the failing ids)
3. `python tools/dump-cli.py`, then `python tools/dump-cli.py --check` (it must pass)
4. `python tools/make-manifest.py`
5. `git status --short`. If `bridge/cursor-bridge/VERSION` is listed, run `git restore bridge/cursor-bridge/VERSION` and then `git status --short` again.
6. `python -m pytest -p no:cacheprovider -q tests/test_improve_launcher_small.py`
7. `python -m pytest -p no:cacheprovider -q tests/test_bridge_run.py tests/test_bridge_run_driver.py tests/test_program_launcher_forms.py`
8. `python -m pytest -p no:cacheprovider -q tests/test_release_s_launcher.py tests/test_bridge_run_slot.py tests/test_tests_windowless.py tests/test_bug029_agent_name.py`
9. `python -c "open('bridge/cursor-bridge/bridge-run.py','rb').read().decode('ascii'); print('ascii ok')"` (expect `ascii ok`)
10. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` (expect `RESULT: SOURCES MATCH`), then `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks`
11. Write the report's results for steps 1 to 10 first. Then run the guard test once: `python -m pytest -p no:cacheprovider -q "tests/test_program_review_rows.py::test_r079_the_launcher_tests_write_no_row_into_the_checkout"`. It runs about 52 test files in one subprocess and takes long; wait for it in the foreground. Quote its summary line. It reports `skipped` only where the checkout has no `run/` folder; say so if it does.
12. `git diff --stat HEAD`
13. `git rev-parse HEAD` and `git status --short`. Neither `bridge/cursor-bridge/VERSION` nor any `tests/test_task090_scratch_` file may be listed.

A failure in a file outside Scope is reported by test id, never fixed there.

Quote every command you ran in the report, verbatim in a fenced block, with the lines it printed. A count, or a claim that a check passed, quotes the output line that shows it. List each mutation code point by this brief's own label. Write a command you did not run as `not run`; never describe it as run. Run this brief's test commands (steps 6 to 8, and step 11) once more after your last edit if you edited after running them. Write the report's results after that run, naming the commit its counts belong to (`git rev-parse HEAD`) and whether the working tree then held uncommitted changes (`git status --short`).

Your last message is the summary and the report file's path, and nothing follows it: the supervisor reads only the last message, and a message printed earlier and then followed by more work is lost.
