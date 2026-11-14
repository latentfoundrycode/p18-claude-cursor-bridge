---
record: brief
header: 1
id: "TASK-059"
round: 6
satisfies: [R-078]
scope: ["bridge/cursor-bridge/bridge-run.py", "bridge/cursor-bridge/bridge_env.py", "bridge/cursor-bridge/MANIFEST.json", "tests/test_program_launcher_forms.py", "tests/test_bridge_run.py", "tests/test_bridge_run_driver.py", "tests/test_release_s_launcher.py", "docs/BUILDER_NOTES.md", "handoff/TASK-059-r6-report.md"]
merge_unit: null
blocking_class: security
---
# TASK-059 round 6: The launcher's command forms: the runner is given the folder the rule checked (R-078)

Round cause: security - round 5's security audit ran npm in a folder outside the launch roots by a folder value whose trailing dots Windows drops (`...`, `a..`), which the rule checked as the launch folder (or `a`) while npm read the word as written through a junction planted under that name (reproduced through the launcher with npm 11.16.0)

Blocking class: security - security audit, round 5, B1 (a folder value whose trailing dots Windows drops runs npm through a planted junction)

## Objective
This is round 6 of TASK-059, a one-correction round. Round 5's code is committed (commit f62855a, "TASK-059: round 5 of the builder (R-078)"): Review A approved it, and the security audit failed it on one finding, B1, of the security class. Round 5's code is the base of this round and stays as it is; you make exactly one correction, the one Requirements 19 and 20 (amended below) state, add one case of your own to `tests/test_bridge_run.py`, and write the report. Requirements 1 to 24 (round 3's brief `handoff/TASK-059-r3.md` numbers them, round 4's brief `handoff/TASK-059-r4.md` and round 5's brief `handoff/TASK-059-r5.md` amended Requirement 19) stand as round 5's code met them and must stay met; they are not work in this round, and earlier rounds' corrections are already built. The finding: Python's `os.path.abspath` on Windows drops a last path component's trailing dots, so for `--prefix ...` (or `a..`, `....`, `.../`) the folder rule checked the launch folder (or `a`) while npm resolved the word as written and read through a junction planted under that name, running a folder outside the launch roots. Rounds 3 to 5 each met one more spelling the rule and npm read differently; the cause is that the rule checks one string while the runner is handed another. The correction: for an accepted named npm, pnpm or yarn suite, the launcher hands the runner, in place of each folder option's value, the absolute folder the rule checked, so the folder that runs is the folder checked. The supervisor's acceptance file `tests/test_program_launcher_forms.py` gained two tests that pin the correction, `test_r078_the_runner_is_given_the_folder_the_rule_checked` and `test_r078_a_trailing_dot_name_never_reaches_the_runner_as_written`, committed after f62855a and before this brief; you edit nothing in that file. The increment as a whole (round 1's brief `handoff/TASK-059.md` and rounds 2 to 5's `handoff/TASK-059-r2.md` to `handoff/TASK-059-r5.md`, which you may read for history) makes the launcher accept the interpreter's two flags `-B` and `-X utf8`, serve a suite in a subfolder through npm's, pnpm's and yarn's folder options held to the target rule, hold the runners' option names in the environment to the same list, give a refused option of a known runner its own exit-125 message, write `merge_ids` sorted and escape the root of both plan globs.

Satisfies: R-078 - The launcher accepts the forms a project's suites need and holds each to the target rule (C6, F5, J4, J9, J12): the test and the driver kind accept the interpreter's own leading flags, exactly `-B` and the two words `-X utf8`, every reading of the command starting after them, and no other interpreter option; npm's `--prefix`, pnpm's `--dir` and `-C` and yarn's `--cwd` are read wherever they stand before a bare `--` and refused (exit 125) unless the folder lies under the launch roots by its resolved path, through no link, given once, the `=` form alike, and an environment name that moves the folder one of the three runners executes in, each found by the increment's reality check from the tool's documentation and a probe and listed in the inventory's row for the target rule, is held to the same rule in the run's environment, a value that does not resolve refused, the variable named and its value never printed, a configuration file a runner finds staying outside the rule as that row says; the exit-125 message tells a refused option of a known runner (a defect to report, never a run to start by hand) from an unknown runner; `merge_ids` is written sorted; the plan glob escapes its root; `reflection.md`'s demonstration sentence names the `-B` form. (The last clause, the `reflection.md` sentence, is written by a later text increment, TASK-082, not by you; the inventory row is the supervisor's.)

## Scope
Files and directories you may create or modify:
- bridge/cursor-bridge/bridge-run.py
- bridge/cursor-bridge/bridge_env.py
- bridge/cursor-bridge/MANIFEST.json
- tests/test_program_launcher_forms.py
- tests/test_bridge_run.py
- tests/test_bridge_run_driver.py
- tests/test_release_s_launcher.py
- docs/BUILDER_NOTES.md
- handoff/TASK-059-r6-report.md

Limits on these files:
- `bridge/cursor-bridge/bridge-run.py`: the one correction of Requirements 19 and 20 goes here: one new helper beside `_package_scan_folder_options`, and its call in `main` between the accepted check (lines 2104 to 2110) and the cmd.exe character check (line 2111). Its module docstring (the triple-quoted string at the top of the file) does not change at all (round 3's Requirement 12). Every line stays ASCII.
- `bridge/cursor-bridge/bridge_env.py`: nothing in it changes in this round. It is listed because the increment's Scope names it (round 1's one change, the escaped glob in `plan_increment_ids`, stands).
- `bridge/cursor-bridge/MANIFEST.json` changes only as regenerated by `python tools/make-manifest.py`. Never edit it by hand. `bridge/cursor-bridge/VERSION` must come out unchanged.
- `tests/test_program_launcher_forms.py` is the supervisor's acceptance file. It is listed so the scope check reads it as part of the increment; you read it and edit nothing in it.
- `tests/test_bridge_run.py`: you add the one case Requirement 19 names. Every existing test stays green.
- `tests/test_bridge_run_driver.py`, `tests/test_release_s_launcher.py`: listed as the increment's Scope; you should not need to change them in this round. Every existing test stays green.

Do not modify anything else.

## Out of scope
- .env and anything under secrets/
- CI configuration: nothing under `.github/`.
- docs/ and handoff/, except the files the Scope section names. In particular `docs/INVENTORY.md`, `docs/HARDENING.md`, `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` are the supervisor's; read them, never edit them. The two reference files stay current only because bridge-run.py's module docstring does not change.
- The mutants file for this increment is the supervisor's; write no mutants file and no mutation script.
- `reflection.md` and every other instruction text: not this increment.
- `bridge/cursor-bridge/CHANGELOG.md`, `bridge/cursor-bridge/VERSION`, every other program under `bridge/`, and `tools/`. Run `tools/make-manifest.py` and `tools/dump-cli.py --check`; change neither.
- Every change to round 5's code other than the one correction of Requirements 19 and 20: no rework of Requirements 1 to 24 as round 5 met them, no refactoring. The character list (round 5), the dash refusal, the twice and missing refusals, the roots and the link walk stay in front of the rewrite, unchanged.
- No new launcher option and no change to an existing one (`--limit`, `--kind`, `--strip`, `--key-file`, `--healthy`). No new dependency.
- Every other test file.
- The leads the supervisor recorded in `docs/HARDENING.md`'s TASK-059 section (leads 1 to 9, the UNC value among them) and Review A's note on an absolute folder value under a project path with a space: the supervisor's, not yours to work on.

## Context
**Development data.** `docs/INVENTORY.md`: "Development data: the dev build is the Workspace sources under `bridge/`; a session in the repo always runs the *installed* bridge (`~/.claude`), never the one being edited, and installs reach running projects only through the owner's install run sheet (§15 condition 1, A1a condition 1)". For you: the code under `bridge/cursor-bridge/` is exercised only by the tests, which load it from the Workspace (the `program` fixture of `tests/conftest.py`) or start it as `bridge/cursor-bridge/bridge-run.py` in temporary folders under `tmp_path`. Never read, edit or copy anything under the home folder.

**The finding.** `docs/HARDENING.md`, its TASK-059 section, records round 5's security audit, B1 (read it; do not repeat the probes). `_package_folder_ok` joins a relative value to the launch folder and calls `os.path.abspath` (line 296), which on Windows drops the last component's trailing dots, so `...` was checked as the launch folder and `a..` as `a`; npm was then handed the word as written and resolved it through a junction planted under the dotted name (created through the `\\?\` prefix, which keeps the dots), running a folder outside the launch roots.

**Round 5's code as committed** (`bridge/cursor-bridge/bridge-run.py` at f62855a; the lines this round reads or touches):
- Constants (lines 216-232): `KNOWN_RUNNER_REFUSE`, `PACKAGE_FOLDER_LONG`, `PACKAGE_FOLDER_CANON`, `PACKAGE_ALLOWED_FLAGS`, `PACKAGE_FOLDER_VALUE_RE` (lines 227-230, round 5's character list), `CMD_EXE_BAD_CHARS` (line 232).
- `def _package_folder_token(head, word):` (line 266) the folder option named by a word in an exact listed form, `"attached"` for `-C<path>`, or None.
- `def _package_folder_value(word, argv, i):` (line 282) returns `(value, next index, word)`, the value from the `=` form or the next word.
- `def _package_folder_ok(value, launch_folder):` (line 290) the folder rule; the `os.path.abspath` call is line 296.
- `def _package_scan_folder_options(argv, head, folder):` (line 308) returns `(run_dir, refused word)`. It stops at a bare `--` (line 315), reads each folder option through `_package_folder_token` and `_package_folder_value`, runs the twice, missing, dash, character-list and `_package_folder_ok` checks (lines 330 to 340), and then computes the folder the rule checked (line 341):

```python
            run_dir = os.path.abspath(value if os.path.isabs(value) else os.path.join(base, value))
```

  where `base = folder or os.getcwd()` (line 312). That path is the one `_package_folder_ok` checked, and the one the runner is to be given.
- `def _cmd_exe_refuse_word(argv, folder=None):` (line 451) the cmd.exe character check over `argv[1:]`.
- `def resolve(argv):` (line 2007) wraps a `.cmd` or `.bat` runner as `["cmd.exe", "/d", "/c", found] + argv[1:]` on Windows (line 2019).
- `def main():` (line 2080). The accepted check is `elif not accepted(cmd, folder):` (line 2104), whose refusal returns 125 at line 2110; it sits in the `if kind == "driver": ... elif ...` chain (line 2095), so a driver command never reaches it. The cmd.exe check follows at lines 2111 to 2114 (`cmd_inj = _cmd_exe_refuse_word(cmd, folder)`). The logged head is computed at line 2186 (`head = head_of(cmd) if kind == "driver" else head_text(cmd)`), `bridge-run: started` is written at line 2193, and `cmd, is_agent = resolve(cmd)` is line 2220. Every check after line 2110 reads `cmd`, so after the rewrite they read the words the runner gets.

**The acceptance tests** (`tests/test_program_launcher_forms.py`, the supervisor's; read its module docstring and the tests).
- `test_r078_the_runner_is_given_the_folder_the_rule_checked(ws, runner, option)` (through the launcher, parametrised over `OPTIONS`: npm `--prefix` and `-C`, pnpm `--dir` and `-C`, yarn `--cwd`): stand-ins on PATH (`write_arg_runners`) print the words they were given. For `[runner, option, "frontend", "test"]`, `[runner, "test", option, "frontend"]` and `[runner, option, "./frontend", "test"]` the word after the option is an absolute path naming `ws/frontend`; for the `=` form before and after the subcommand exactly one word starts with `option + "="` and its value is an absolute path naming `ws/frontend`; for `[runner, "test", "--", option, "frontend"]` the last two words are `option` and `frontend`, untouched.
- `test_r078_a_trailing_dot_name_never_reaches_the_runner_as_written(ws)` (Windows only): junctions named `...`, `a..` and `....` are planted under the launch folder, leading outside; for each value of `...`, `a..`, `a...`, `....` and `.../`, `npm --prefix <value> test` is either refused with the known-runner message naming `--prefix`, exit 125, or started with the runner given an absolute folder inside the launch folder, never the value as written and never the outside folder.
- Round 5's and earlier rounds' tests stay in the file and must stay green, `test_r078_a_folder_inside_the_launch_folder_is_accepted_in_every_form`, `test_r078_a_suite_in_a_subfolder_is_stripped_logged_and_limited` (the row's head is `npm test`), the two logged-head tests and the two cmd.exe tests among them.

**Security context.** ASVS level 2 (`docs/INVENTORY.md`: "The builder's secure-coding rule is ASVS level 2"; the bridge launches subprocesses, confines paths, reads keys and gates merges). Trust boundaries: the launcher's command line is untrusted input (the allow rule lets an agent start an accepted command without the owner's word, so every form the launcher accepts must be held to the target rule, and the runner must get the words the rule checked); the filesystem under the launch folder is untrusted (an agent may have planted a folder of any name the system allows, a symbolic link or a junction). The security auditor reads this round's diff. `.cursor/rules/secure-coding.mdc` and `.cursor/rules/workspace-boundary.mdc` are in force for you, and the frozen `minimal-code.mdc`.

**External services.** None. The increment calls no service and adds no remote wait.

**Values.** No value in this increment is the owner's (rule 52). The folder options and the character list are the design's, the reality check's and the reviews', pinned by the acceptance tests.

## Diagrams
None. The build plan names no diagram for this increment (`Diagrams: none`).

## Requirements
Requirements 1 to 24 are round 3's brief's (`handoff/TASK-059-r3.md`), numbered as there, Requirement 19 as round 4's and round 5's briefs amended it; every one stands as round 5's code (f62855a) meets it and must stay met. Round 6 amends Requirements 19 and 20 only, and adds this round's report (Requirement 14 as round 3 wrote it, for the new report file).

19. **The folder rule (amended in round 6; security, the security audit's round-5 B1).** As round 5 met it: the folder is accepted only where its value holds only the listed characters (round 5), exists as a folder, lies under the launch roots by its resolved path, and is reached through no link; it is refused, exit 125, with the known-runner message naming the option, before anything starts, where it is outside, through a link, missing, given twice, without its value, or starting with `-` or `~`. All of that stays in front of the rewrite, unchanged. New in round 6: for an accepted named npm, pnpm or yarn suite, the launcher rewrites each folder option's value in the command it starts to the absolute folder the rule checked: the same path `_package_folder_ok` checked, the `os.path.abspath` of the value joined to the launch folder, which `_package_scan_folder_options` already computes as `run_dir` (line 341). The two-word form keeps the option word and replaces the next word (`--prefix <abs>`); the `=` form becomes one word `<option>=<abs>` with the option as given (`--prefix=`, `-C=`, `--dir=`, `--cwd=`); the position before or after the subcommand is kept; the words after a bare `--` are never touched; nothing else in the command changes. The rewrite is done in `main` after the command is accepted (after line 2110) and before the cmd.exe character check (line 2111) and `resolve` (line 2220), so the cmd.exe check reads the words the runner gets, all before the `bridge-run: started` line. A driver command and a command that is no named npm, pnpm or yarn suite are not rewritten. Write it as one helper (for example `package_folder_rewrite(argv, folder)` returning the new list) that reads the folder options exactly as `_package_scan_folder_options` does (the same `_package_folder_token` and `_package_folder_value`, the same stop at a bare `--`, the same path as `run_dir`), so the two cannot disagree about which words are folder options. Pinned by `test_r078_the_runner_is_given_the_folder_the_rule_checked` and, on Windows, `test_r078_a_trailing_dot_name_never_reaches_the_runner_as_written`. Add one builder case to `tests/test_bridge_run.py` for the helper in process, naming R-078 in its name or docstring, with `base` a folder under `tmp_path` holding `frontend` and `abs` meaning `os.path.abspath(os.path.join(base, "frontend"))`: `["npm", "test", "--prefix", "frontend"]` becomes `["npm", "test", "--prefix", abs]`, and `["npm", "--prefix=frontend", "test", "--", "--prefix", "x"]` becomes `["npm", "--prefix=" + abs, "test", "--", "--prefix", "x"]` (the existing `test_r078_npm_prefix_folder_value_held_to_character_list`, line 365, shows the `program` fixture and the `base` folder).

20. **A suite so launched (amended in round 6).** As round 5 met it: a suite so launched is stripped, logged and limited as any named suite; its run log row has kind `test`, the limit given, and the logged head is `npm test` (or `npm run test:unit`, `pnpm test`, `yarn test`), never a folder option or its value, a flag, a bare `--` or a script's argument. New in round 6: the command started is the rewritten one of Requirement 19, and the logged head (`head_text`, line 2186, which reads `cmd` after the rewrite) is unchanged by it, the folder never in it.

14. **The report (as round 3's Requirement 14, for this round).** The report `handoff/TASK-059-r6-report.md` lists the files you changed, the requirements this round amends and how the change meets them, every command of the Done list with its output lines, and the section `Assumed, not verified`. Mutations are listed only where applied, with the output line that shows the test failing; a mutation not applied is written `not run`. No computer path in the report: `<Workspace>` and `~`.

## Acceptance criteria
- [ ] Every test in `tests/test_program_launcher_forms.py` passes (it names R-078), the five cases of `test_r078_the_runner_is_given_the_folder_the_rule_checked` and `test_r078_a_trailing_dot_name_never_reaches_the_runner_as_written` among them; the npm test, the trailing-dot test and the two cmd.exe tests pass or are skipped only for their own stated reason, quoted from the pytest output.
- [ ] For an accepted named npm, pnpm or yarn suite, the command started carries, for each folder option before a bare `--`, the absolute folder the rule checked (the `run_dir` path of `_package_scan_folder_options`) in place of the value given, in the two-word and the `=` form, before or after the subcommand; the words after a bare `--` and every other word are unchanged (Requirement 19).
- [ ] The rewrite is made by one helper that reads the folder options through `_package_folder_token` and `_package_folder_value` with the same stop at a bare `--` as `_package_scan_folder_options`, called in `main` after the accepted check and before the cmd.exe character check, `resolve` and the `bridge-run: started` line; the character list, the dash, twice and missing refusals, the roots and the link walk still run before it, unchanged.
- [ ] The logged head of a suite so launched is unchanged (`npm test` for `npm --prefix frontend test`), the folder never in it (Requirement 20).
- [ ] The new case in `tests/test_bridge_run.py` names R-078 and asserts both rewrites Requirement 19 names, in process.
- [ ] Every existing test in `tests/test_bridge_run.py`, `tests/test_bridge_run_driver.py`, `tests/test_release_s_launcher.py`, `tests/test_bug029_agent_name.py`, `tests/test_task032_supervisor_launcher.py`, `tests/test_header_plan.py`, `tests/test_header_plan_r3.py` and `tests/test_dump_cli.py` passes.
- [ ] Requirements 1 to 24 stay met as round 5's code met them; nothing in `bridge-run.py` changes but the one correction.
- [ ] `python tools/dump-cli.py --check` reports the reference current, and `git diff 73869de -- bridge/cursor-bridge/bridge-run.py` shows no change inside the module docstring.
- [ ] `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` reports the sources match; `bridge/cursor-bridge/VERSION` unchanged.
- [ ] R-078's launcher clauses are fully met, with no stand-in, placeholder or "later" text.
- [ ] No new Semgrep high findings; every refusal is exit 125 before anything starts; every path compared by its resolved form with links refused on the way, and the runner given the path compared (ASVS L2).
- [ ] No launcher option added or changed; no new dependency; `bridge-run.py` stays ASCII.

## Constraints
- Do not add dependencies.
- Do not read or write any file outside this workspace (the folder you were started in). Everything you need is inside it; everything you produce goes inside it.
- No secret is needed or used. Refer to `.env` and configuration keys by name only; never reproduce a value.
- If the brief, the rules, or the tooling got in your way (an instruction that contradicted another, a check that fired wrongly, a step that cost time for no reason), append one dated line describing it to `docs/BUILDER_NOTES.md`. Do not try to fix the tooling. Do the same for anything you learned about a defect or a pitfall (a cause you found, a platform quirk that cost you a round): one dated line, so the supervisor can carry it forward.
- In any Markdown you write, never break a line inside a paragraph or a list item; one paragraph is one line. Line breaks only between blocks.
- This increment talks to no external service and adds no remote wait.
- Any console process your code launches on Windows is created windowless (`creationflags=subprocess.CREATE_NO_WINDOW` in Python, `0` on other platforms); this round starts no new process in the launcher (the rewrite changes the command's words only). Every subprocess call in a test passes `creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)` and a timeout.
- **Run every command in the foreground and wait for it to end.** Start nothing in the background, and leave no process running when you finish. Never start a server, a watcher or a daemon.
- **Run named test files only**, with exactly the commands the Done section lists (`python -m pytest -p no:cacheprovider -q <files>`; your own run is already stripped by the launcher that started you). Do NOT run the full `tests/` tree (`python -m pytest`, `python -m pytest tests`, or any command that collects all of it); the supervisor and CI run the full suite. No `PYTHONPATH` or other environment change.
- Run no Python other than the Done section's commands: no `python -c`, no here-document, no script of your own, and never import the project's tests outside pytest.
- Do not refactor code outside the scope, even if it looks wrong. Do not change round 5's code beyond the one correction.
- Never run the product, a migration, a seed or a test against the owner's live data (Context, "Development data").
- No value in this increment is the owner's (rule 52).
- Follow existing conventions in the files you touch: the `bridge-run: refused - ...` lines, exit 125, ASCII-only code and docstrings. Every line of `bridge-run.py` stays ASCII; write any non-ASCII example in a test as `chr(0x....)`.
- These git commands are not yours to run: `commit`, `push`, `switch`, `checkout`, `merge`, `rebase`, `reset`, `stash`, `branch -d`, `worktree`. You read with `git status`, `git diff` and `git log` only. (Tests run git inside their own scratch repositories under `tmp_path`; that is not this repository.)
- Numbers from text are parsed with the language's own parser, never by slicing a string. This increment reads no number from text.
- Every verification command is written in the Done section in full; run exactly those, from the Workspace root. The supervisor checks this increment's tests by mutation after your run, with its own mutants file. You may apply these mutations by hand in-process in your own run, reverting each, to check the tests catch them; list each by its label, only where applied with the pytest output line that shows the test failing, else `not run`: (M1) the helper accepts a flag given twice; (M2) the helper accepts an `-X` value other than `utf8`; (M3) the folder rule skips the link walk; (M4) the option list admits a word outside it (an abbreviation such as `--pre`, or a cluster such as `-sC`); (M5) a folder option after a bare `--` is read; (M6) `merge_ids` written unsorted; (M7) the cmd.exe character check skipped. (M8) is withdrawn: write it `withdrawn` in the report. No mutation script lands in the diff.
- **Known failures.** `test_r078_the_runner_is_given_the_folder_the_rule_checked` and `test_r078_a_trailing_dot_name_never_reaches_the_runner_as_written` are red on round 5's code (the acceptance file's docstring); this round turns them green. No other failure is known in the files the Done section runs; if another fails and this change did not cause it, report it by its test id and fix none.
- If an acceptance test and this brief seem to disagree, or a test seems to pin something this brief does not say, stop and report it; do not edit the test.
- Prefer reuse over new code: `_package_folder_token`, `_package_folder_value` and the `run_dir` computation of `_package_scan_folder_options` are the model, and write the minimum that meets the acceptance criteria (the frozen `minimal-code.mdc` is in force). This never overrides a security, observability or accessibility requirement stated above.
- Rules in force for you: `.cursor/rules/secure-coding.mdc`, `.cursor/rules/workspace-boundary.mdc` and the frozen `minimal-code.mdc`.

## Done
Your report is the file `handoff/TASK-059-r6-report.md`, which you write as you go: what you did, what you changed, what you ran and what it printed, what you could not do, so that nothing of it is lost when your run ends early. It names no computer path: write `<Workspace>` for the repository folder and `~` for the home folder, including in quoted command output.

When you finish, it holds:
- a list of every file you changed;
- a one-paragraph summary of what you did;
- for Requirements 19 and 20 as amended, one sentence each on how the change meets them, naming the function and line;
- every command of the list below with its output;
- the mutations (M1 to M7), each applied one with the pytest output line that shows the test failing, each other one written `not run`, and (M8) written `withdrawn`;
- a section headed exactly `Assumed, not verified`, as the report's last section.

The `Assumed, not verified` section lists every fact this change relies on that neither this brief nor the existing code settled, and that you did not confirm, among them, where they apply: that pnpm and yarn take an absolute folder value as npm does; that cmd.exe passes an absolute path without a space through npm.cmd unchanged. One item per line: what you assumed · why · what would confirm it. If there are none, write `Assumed, not verified: none`. Be specific: "edge cases" or "error handling" is not an item.

Run these from the Workspace root, in this order, after your last edit, each in the foreground, with no `PYTHONPATH` or other environment change.
1. `python tools/make-manifest.py`
2. `python tools/dump-cli.py --check` (expect the reference current)
3. `python -m pytest -p no:cacheprovider -q tests/test_program_launcher_forms.py`
4. `python -m pytest -p no:cacheprovider -q tests/test_bridge_run.py tests/test_bridge_run_driver.py tests/test_release_s_launcher.py`
5. `python -m pytest -p no:cacheprovider -q tests/test_bug029_agent_name.py tests/test_task032_supervisor_launcher.py tests/test_header_plan.py tests/test_header_plan_r3.py tests/test_dump_cli.py`
6. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` (expect the sources to match)
7. `git rev-parse HEAD` and `git status --short`

Every command you ran is quoted in the report with the lines it printed, verbatim, in a fenced block; the launcher's own lines (`bridge-run: started ...`, `bridge-run: exit ...`) included. Each pytest summary line is quoted verbatim; never restate a count in prose. A claim that a check passed quotes the output line that shows it, and a number of failing or skipped cases is backed by the pytest lines naming them. A command you did not run is written `not run`, never described as run. Run this brief's test commands once more after your last edit, and write the report's results after step 7, naming the commit its counts belong to (`git rev-parse HEAD`) and whether the working tree then held uncommitted changes (`git status --short`).

Your last message is the summary and the report file's path, and nothing follows it. The supervisor reads only the last message, and a message printed earlier and then followed by more work is lost.
