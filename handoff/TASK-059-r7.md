---
record: brief
header: 1
id: "TASK-059"
round: 7
satisfies: [R-078]
scope: ["bridge/cursor-bridge/bridge-run.py", "bridge/cursor-bridge/MANIFEST.json", "tests/test_bridge_run.py", "docs/BUILDER_NOTES.md", "handoff/TASK-059-r7-report.md"]
merge_unit: null
blocking_class: null
---
# TASK-059 round 7: The launcher's command forms: the runner is given the checked folder relative to the launch folder (R-078)

Round cause: fix-induced - round 6's fix (the runner handed the absolute folder the rule checked) caused R1, a behaviour regression both round-6 readers reproduced: on Windows a `.cmd` runner is started through cmd.exe, so with npm under a folder holding a space a launch folder with a space never ran its suite, and a launch folder holding `(`, `)`, `&`, `%`, `!` or `^` was refused by the cmd.exe check

## Objective
This is round 7 of TASK-059, a one-correction round after a regression the previous round's fix caused. Round 6's code is committed (commit 009e42f, "TASK-059: round 6 of the builder (R-078)"): it added `_package_folder_rewrite` in `bridge/cursor-bridge/bridge-run.py`, called in `main` after the command is accepted and before the cmd.exe character check, which hands an accepted npm, pnpm or yarn suite's runner the absolute folder the rule checked in place of each folder option's value. Both readers (Review A and the security audit) confirmed that this closed round 5's trailing-dot hole, and both blocked on R1, which round 6 caused: the absolute folder brought the project's own location onto cmd.exe's command line, so (a) with npm under a folder holding a space (Node's default install folder, under `Program Files`) a launch folder with a space never ran its suite (`'C:\Program' is not recognized`, exit 1: four quotes on the line, of which `cmd.exe /c` strips the first and the last), and (b) a launch folder holding `(`, `)`, `&`, `%`, `!` or `^` was refused, exit 125, because `_cmd_exe_refuse_word` read the rewritten absolute path. A resolution round settled the fix (material `handoff/RESOLUTION-TASK-059.md`, decision and reasoning in `docs/CHANGES.md`, recorded at the end of `docs/HARDENING.md`'s TASK-059 section; read all three): the runner is handed the checked folder **relative to the launch folder**, beginning with `.`, and a value whose relative path cannot be computed is refused, never handed absolute. The runner's working folder is the launch folder, so it reads the relative word back as the folder checked (round 6's property kept), while the launch folder's own characters never reach cmd.exe. Round 6's code is the base of this round and stays as it is apart from the one correction Requirement 19 (amended below) states, inside the one helper and its call in `main`; you update your own case in `tests/test_bridge_run.py` and write the report. Requirements 1 to 24 (round 3's brief `handoff/TASK-059-r3.md` numbers them; rounds 4, 5 and 6 amended Requirement 19, round 6 Requirement 20) stand as round 6's code meets them, except the absolute word Requirement 19 now replaces, and must stay met; they are not work in this round. The increment as a whole (round 1's brief `handoff/TASK-059.md` and rounds 2 to 6's `handoff/TASK-059-r2.md` to `handoff/TASK-059-r6.md`, which you may read for history) makes the launcher accept the interpreter's two flags `-B` and `-X utf8`, serve a suite in a subfolder through npm's, pnpm's and yarn's folder options held to the target rule, hold the runners' option names in the environment to the same list, give a refused option of a known runner its own exit-125 message, write `merge_ids` sorted and escape the root of both plan globs.

Satisfies: R-078 - The launcher accepts the forms a project's suites need and holds each to the target rule (C6, F5, J4, J9, J12): the test and the driver kind accept the interpreter's own leading flags, exactly `-B` and the two words `-X utf8`, every reading of the command starting after them, and no other interpreter option; npm's `--prefix`, pnpm's `--dir` and `-C` and yarn's `--cwd` are read wherever they stand before a bare `--` and refused (exit 125) unless the folder lies under the launch roots by its resolved path, through no link, given once, the `=` form alike, and an environment name that moves the folder one of the three runners executes in, each found by the increment's reality check from the tool's documentation and a probe and listed in the inventory's row for the target rule, is held to the same rule in the run's environment, a value that does not resolve refused, the variable named and its value never printed, a configuration file a runner finds staying outside the rule as that row says; the exit-125 message tells a refused option of a known runner (a defect to report, never a run to start by hand) from an unknown runner; `merge_ids` is written sorted; the plan glob escapes its root; `reflection.md`'s demonstration sentence names the `-B` form. (The last clause, the `reflection.md` sentence, is written by a later text increment, TASK-082, not by you; the inventory row is the supervisor's.)

## Scope
Files and directories you may create or modify:
- bridge/cursor-bridge/bridge-run.py
- bridge/cursor-bridge/MANIFEST.json
- tests/test_bridge_run.py
- docs/BUILDER_NOTES.md
- handoff/TASK-059-r7-report.md

Limits on these files:
- `bridge/cursor-bridge/bridge-run.py`: the one correction of Requirement 19 goes here, in `_package_folder_rewrite` (lines 351 to 389, its own docstring updated to say what it now hands) and its call in `main` (lines 2152 and 2153), where the refusal of Requirement 19 (c) is written and returned. Nothing else in the file changes. Its module docstring (the triple-quoted string at the top of the file) does not change at all (round 3's Requirement 12). Every line stays ASCII.
- `bridge/cursor-bridge/MANIFEST.json` changes only as regenerated by `python tools/make-manifest.py`. Never edit it by hand. `bridge/cursor-bridge/VERSION` must come out unchanged.
- `tests/test_bridge_run.py`: you update your own round-6 case `test_r078_folder_option_value_rewritten_to_rule_checked_path` (lines 381 to 392) as Requirement 19 states, and you add one case for the refusal of Requirement 19 (c). Every other test in it stays as it is and green.

Do not modify anything else.

## Out of scope
- .env and anything under secrets/
- CI configuration: nothing under `.github/`.
- docs/ and handoff/, except the files the Scope section names. In particular `docs/INVENTORY.md`, `docs/HARDENING.md`, `docs/CHANGES.md`, `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` are the supervisor's; read them, never edit them. The two reference files stay current only because bridge-run.py's module docstring does not change.
- `tests/test_program_launcher_forms.py`: the supervisor's acceptance file. Read it; edit nothing in it.
- `tests/test_bridge_run_driver.py`, `tests/test_release_s_launcher.py`, `tests/test_bug029_agent_name.py` and every other test file: you run the ones the Done section names; you change none.
- `bridge/cursor-bridge/bridge_env.py`, `bridge/cursor-bridge/CHANGELOG.md`, `bridge/cursor-bridge/VERSION`, every other program under `bridge/`, and `tools/`. Run `tools/make-manifest.py` and `tools/dump-cli.py --check`; change neither.
- The mutants file for this increment is the supervisor's; write no mutants file and no mutation script.
- `reflection.md` and every other instruction text: not this increment.
- Every change to round 6's code other than the one correction: the character list `PACKAGE_FOLDER_VALUE_RE`, the dash, tilde, twice and missing refusals, `_package_folder_ok`, the roots, the link walk `_link_walk_ok`, `_package_scan_folder_options`, `_cmd_exe_refuse_word` and its place after the rewrite, `CMD_EXE_BAD_CHARS`, and `resolve` stay exactly as round 6 left them. No refactoring.
- `resolve`'s cmd.exe quoting (HARDENING's lead 1, a spaced argument the agent writes) and the scan's traceback where `os.path.relpath` raises inside `_link_walk_ok` (HARDENING's lead 3): recorded leads, not this round's work. Likewise the other leads in `docs/HARDENING.md`'s TASK-059 section (leads 1 to 12), the UNC launch folder (lead 10) and the recomputed folder (lead 12) among them.
- No new launcher option and no change to an existing one (`--limit`, `--kind`, `--strip`, `--key-file`, `--healthy`). No new dependency.

## Context
**Development data.** `docs/INVENTORY.md`: "Development data: the dev build is the Workspace sources under `bridge/`; a session in the repo always runs the *installed* bridge (`~/.claude`), never the one being edited, and installs reach running projects only through the owner's install run sheet (§15 condition 1, A1a condition 1)". For you: the code under `bridge/cursor-bridge/` is exercised only by the tests, which load it from the Workspace (the `program` fixture of `tests/conftest.py`) or start it as `bridge/cursor-bridge/bridge-run.py` in temporary folders under `tmp_path`. Never read, edit or copy anything under the home folder.

**The regression and the decision.** `docs/HARDENING.md`, TASK-059 section, last entry "Round 6's reviews and the resolution round", and `docs/CHANGES.md`'s entry "TASK-059: resolution round on round 6's regression (R1)" (read both; do not repeat the probes). Under the decision the handed word is made only of components of a value already held to the character list and normalised by `os.path.abspath` (`...` becomes `.`, `a..` becomes `a`), and is the same relative path `_link_walk_ok` computes on the same absolute path and base, so the folder that runs is still the folder checked.

**Round 6's code as committed** (`bridge/cursor-bridge/bridge-run.py` at 009e42f; the lines this round reads or touches):
- Constants: `KNOWN_RUNNER_REFUSE` (lines 216-219, the known-runner message, `%r` the refused word), `PACKAGE_FOLDER_LONG` (line 220), `PACKAGE_FOLDER_VALUE_RE` (lines 227-230), `CMD_EXE_BAD_CHARS = '&|<>^%!"\r\n()'` (line 232).
- `def _package_folder_token(head, word):` (line 266) and `def _package_folder_value(word, argv, i):` (line 282), which return `(value, next index, word)`.
- `def _package_folder_ok(value, launch_folder):` (lines 290-305): the value joined to the launch folder, `os.path.abspath`, a folder, under `launch_roots`, then `_link_walk_ok(path, walk_base)`.
- `def _package_scan_folder_options(argv, head, folder):` (lines 308-348): `base = folder or os.getcwd()` (line 312); the label of a refused option is `shown.split("=", 1)[0] if "=" in shown else shown` (line 329); the folder checked is (line 341):

```python
            run_dir = os.path.abspath(value if os.path.isabs(value) else os.path.join(base, value))
```

- `def _package_folder_rewrite(argv, folder):` (lines 351-389), round 6's helper: returns `list(argv)` unchanged unless the head is npm, pnpm or yarn and `named_suite(argv, folder)`; `base = folder or os.getcwd()` (line 356); stops at a bare `--` and copies the rest (lines 360-362); for a folder option computes (line 373)

```python
                abs_path = os.path.abspath(value if os.path.isabs(value) else os.path.join(base, value))
```

  and hands `abs_path` as the next word (two-word form) or as `<option>=<abs_path>` (`=` form, lines 374-378). This `abs_path` is the path this round turns into the relative word.
- `def _link_walk_ok(prog, base):` (lines 563-572) computes `rel = os.path.relpath(prog, base)` and returns False where `rel.startswith("..")`; it is called by `_package_folder_ok` for every folder value before acceptance.
- `def resolve(argv):` (lines 2048-2062) starts a `.cmd` or `.bat` runner on Windows as `["cmd.exe", "/d", "/c", found] + argv[1:]` (line 2060).
- `def main():` (line 2121): `folder = os.getcwd()` (line 2123); the accepted check `elif not accepted(cmd, folder):` (lines 2145-2151, refusal exit 125); the rewrite (lines 2152-2153):

```python
    if head_of(cmd) in PACKAGE_FOLDER_LONG and named_suite(cmd, folder):
        cmd = _package_folder_rewrite(cmd, folder)
```

  then the cmd.exe check (lines 2154-2157: `cmd_inj = _cmd_exe_refuse_word(cmd, folder)`, `sys.stderr.write(KNOWN_RUNNER_REFUSE % cmd_inj)`, `return 125`), which is the pattern for this round's refusal. The logged head is computed at line 2229 (`head_text(cmd)`), `bridge-run: started` is written at line 2236, `cmd, is_agent = resolve(cmd)` is line 2263. `subprocess.Popen` (lines 2374 and 2389) is given no `cwd`, so the runner's working folder is the launch folder, `folder`.

**Why the refusal of Requirement 19 (c) is a guard, not an expected path.** Every value that reaches the helper has passed `_package_folder_ok`: a value outside the launch folder fails the roots check or `_link_walk_ok` (which refuses any relative path starting with `..`), and a value for which `os.path.relpath` raises (another drive, a subst drive, the `\\.\GLOBALROOT\...` form; HARDENING's lead 3) raises inside `_link_walk_ok` already, before acceptance (lead 3's traceback, unchanged in this round). So for an accepted value `os.path.relpath` does not raise in the helper. The guard is still required, so that the helper never hands an absolute path whatever changes in front of it; do not build any fallback to the absolute form, and do not leave the guard out because it is unreachable today.

**The acceptance tests** (`tests/test_program_launcher_forms.py`, the supervisor's; read its module docstring and these tests). Changed and added by the supervisor before this brief; you edit nothing in that file. The helper `assert_handed(word, ws, folder, context)` (line 424) asserts the handed word is not absolute, has no drive, begins with `.`, and that `os.path.join(ws, word)` is the folder (by `realpath`).
- `test_r078_the_runner_is_given_the_folder_the_rule_checked(ws, runner, option)` (line 440, parametrised over npm `--prefix` and `-C`, pnpm `--dir` and `-C`, yarn `--cwd`): stand-ins on PATH print the words they were given; for `[runner, option, "frontend", "test"]`, `[runner, "test", option, "frontend"]`, `[runner, option, "./frontend", "test"]` and the two `=` forms the handed word passes `assert_handed` for `ws/frontend`; after a bare `--` the last two words are `option` and `frontend`, untouched.
- `test_r078_a_trailing_dot_name_never_reaches_the_runner_as_written(ws)` (line 465, Windows only): junctions `...`, `a..`, `....` planted to a folder outside; for `...`, `a..`, `a...`, `....`, `.../` the run is refused with the known-runner message naming `--prefix`, or started with a handed word that differs from the value, is not absolute, begins with `.`, and read from the launch folder lies inside it and is not the outside folder.
- `test_r078_a_launch_folder_with_a_space_runs_under_a_runner_in_a_spaced_folder(tmp_path)` (line 510, Windows only): the launch folder under `proj space`, the stand-ins under `Program Files x/nodejs`; every runner and option in `FORMS_OF` (line 505: the two-word form before and after the subcommand, the `=` form after) starts, exit 0, and the handed word passes `assert_handed`.
- `test_r078_a_launch_folder_holding_a_cmd_character_runs(tmp_path, name)` (line 527, Windows only, `name` in `P (old)`, `R&D`, `x^y`, `100%`, `wow!`): the launch folder under that name; every form starts and the handed word passes `assert_handed`.
- `test_r078_a_handed_folder_never_begins_with_a_dash(ws, runner, option)` (line 542): a folder `-r` under the launch folder, given as `./-r` (two-word before the subcommand, `=` form after); the run starts and the handed word passes `assert_handed` for `ws/-r` (so it begins with `.`, never `-`).
- Every other test in the file stays green, the logged-head tests, the subfolder test (`test_r078_a_suite_in_a_subfolder_is_stripped_logged_and_limited`, head `npm test`) and the two cmd.exe tests among them.

**Security context.** ASVS level 2 (`docs/INVENTORY.md`: the builder's secure-coding rule is ASVS level 2; the bridge launches subprocesses, confines paths, reads keys and gates merges). Trust boundaries: the launcher's command line is untrusted input (the allow rule lets an agent start an accepted command without the owner's word, so every form the launcher accepts must be held to the target rule, and the runner must read back the folder the rule checked); the filesystem under the launch folder is untrusted (an agent may have planted a folder of any name the system allows, a symbolic link or a junction); the launch folder's own path is the owner's and may hold a space or any character cmd.exe reads. The security auditor reads this round's diff. `.cursor/rules/secure-coding.mdc` and `.cursor/rules/workspace-boundary.mdc` are in force for you, and the frozen `minimal-code.mdc`.

**External services.** None. The increment calls no service and adds no remote wait.

**Values.** No value in this increment is the owner's (rule 52). The folder options and the character list are the design's, the reality check's and the reviews', pinned by the acceptance tests.

## Diagrams
None. The build plan names no diagram for this increment (`Diagrams: none`).

## Requirements
Requirements 1 to 24 are round 3's brief's (`handoff/TASK-059-r3.md`), numbered as there, Requirement 19 as rounds 4, 5 and 6 amended it and Requirement 20 as round 6 amended it; every one stands as round 6's code (009e42f) meets it and must stay met, but for the word Requirement 19 now hands. Round 7 amends Requirement 19 only, and adds this round's report (Requirement 14 as round 3 wrote it, for the new report file).

19. **The folder rule (amended in round 7; the resolution round on round 6's regression R1).** As round 6 met it, unchanged: the folder is accepted only where its value holds only the listed characters, exists as a folder, lies under the launch roots by its resolved path and is reached through no link; it is refused, exit 125, with the known-runner message naming the option, before anything starts, where it is outside, through a link, missing, given twice, without its value, or starting with `-` or `~`. For an accepted named npm, pnpm or yarn suite, `main` rewrites each folder option's value in the command it starts, after the accepted check and before the cmd.exe character check, `resolve` and the `bridge-run: started` line, through the one helper `_package_folder_rewrite`, which reads the folder options exactly as `_package_scan_folder_options` does (the same `_package_folder_token` and `_package_folder_value`, the same stop at a bare `--`); the two-word form keeps the option word and replaces the next word; the `=` form becomes one word `<option>=<word>` with the option as given (`--prefix=`, `-C=`, `--dir=`, `--cwd=`); the position before or after the subcommand is kept; the words after a bare `--` are never touched; nothing else in the command changes; a driver command and a command that is no named npm, pnpm or yarn suite are not rewritten. Changed in round 7, the word handed in place of the value:
    - (a) It is the checked folder relative to the launch folder: `os.path.relpath` of the same absolute path the helper computes today as `abs_path` (line 373, the scan's `run_dir`, line 341), from the same base (`folder or os.getcwd()`, line 356). It never holds the launch folder's own path, so no character of that path reaches cmd.exe or the cmd.exe check.
    - (b) It begins with `.`: exactly `.` where the checked folder is the launch folder itself (the relative path is `.`), otherwise `.`, the platform's separator `os.sep`, then the relative path, as `os.path.join(".", <relative path>)` gives it: `.\frontend` on Windows and `./frontend` elsewhere; a folder named `-r` given as `./-r` is handed `.\-r` on Windows and `./-r` elsewhere, never `-r`. The launch folder is never handed as `.` followed by a separator and `.`.
    - (c) Where the relative path cannot be computed (`os.path.relpath` raises `ValueError`), the run is refused: `main` writes `KNOWN_RUNNER_REFUSE` naming the option word as the scan names it (line 329: `--prefix` for both `--prefix x` and `--prefix=x`; `-C`, `--dir`, `--cwd` likewise) and returns 125, before the cmd.exe check, before the `bridge-run: started` line, with nothing started. The value is never handed absolute: there is no fallback to round 6's absolute word. This branch is a guard (Context, "Why the refusal ... is a guard"); the helper's return shape for it is yours to choose, and `main`'s call is the only caller besides your test.
    - Pinned by `test_r078_the_runner_is_given_the_folder_the_rule_checked`, `test_r078_a_handed_folder_never_begins_with_a_dash` and, on Windows, `test_r078_a_trailing_dot_name_never_reaches_the_runner_as_written`, `test_r078_a_launch_folder_with_a_space_runs_under_a_runner_in_a_spaced_folder` and `test_r078_a_launch_folder_holding_a_cmd_character_runs`.
    - Update your case `test_r078_folder_option_value_rewritten_to_rule_checked_path` in `tests/test_bridge_run.py` (lines 381-392), naming R-078 in its docstring, with `base` a folder under `tmp_path` holding `frontend` and `rel` meaning `os.path.join(".", "frontend")`: `["npm", "test", "--prefix", "frontend"]` becomes `["npm", "test", "--prefix", rel]`; `["npm", "--prefix=frontend", "test", "--", "--prefix", "x"]` becomes `["npm", "--prefix=" + rel, "test", "--", "--prefix", "x"]`; and `["npm", "--prefix", "frontend/..", "test"]` becomes `["npm", "--prefix", ".", "test"]` (the launch folder handed as the dot alone). Add one case, naming R-078, for the refusal of (c) (required: it is the only test that holds the decision's no-fallback condition), calling the helper or `main`'s path directly with `os.path.relpath` made to raise `ValueError` for the call (monkeypatch); it asserts the refusal, the option word it names (`--prefix` for both forms), and that no word of the result, where the helper returns one, is an absolute path.

20. **A suite so launched (as round 6 amended it, unchanged).** A suite so launched is stripped, logged and limited as any named suite; its run log row has kind `test`, the limit given, and the logged head is `npm test` (or `npm run test:unit`, `pnpm test`, `yarn test`), never a folder option or its value, a flag, a bare `--` or a script's argument. The command started is the rewritten one of Requirement 19, and the logged head (`head_text`, line 2229, which reads `cmd` after the rewrite) is unchanged by it.

14. **The report (as round 3's Requirement 14, for this round).** The report `handoff/TASK-059-r7-report.md` lists the files you changed, the requirement this round amends and how the change meets it, every command of the Done list with its output lines, and the section `Assumed, not verified`. Mutations are listed only where applied, with the output line that shows the test failing; a mutation not applied is written `not run`. No computer path in the report: `<Workspace>` and `~`.

## Acceptance criteria
- [ ] Every test in `tests/test_program_launcher_forms.py` passes (it names R-078), among them the five cases of `test_r078_the_runner_is_given_the_folder_the_rule_checked`, the five of `test_r078_a_handed_folder_never_begins_with_a_dash`, `test_r078_a_trailing_dot_name_never_reaches_the_runner_as_written`, `test_r078_a_launch_folder_with_a_space_runs_under_a_runner_in_a_spaced_folder` and the five cases of `test_r078_a_launch_folder_holding_a_cmd_character_runs`; a Windows-only test, the npm test and the two cmd.exe tests pass or are skipped only for their own stated reason, quoted from the pytest output.
- [ ] For an accepted named npm, pnpm or yarn suite, the command started carries, for each folder option before a bare `--`, the checked folder relative to the launch folder in place of the value given, beginning with `.` (the dot alone for the launch folder, else `.`, `os.sep` and the relative path), in the two-word and the `=` form, before or after the subcommand; the words after a bare `--` and every other word are unchanged (Requirement 19 (a), (b)).
- [ ] Where `os.path.relpath` raises for a folder value in the helper, the launcher writes the known-runner message naming the option word and exits 125 before the cmd.exe check and the `bridge-run: started` line; no code path hands the runner an absolute folder (Requirement 19 (c)).
- [ ] The rewrite stays in the one helper `_package_folder_rewrite`, called in `main` after the accepted check and before the cmd.exe character check, `resolve` and the `bridge-run: started` line; the character list, the dash, tilde, twice and missing refusals, the roots, the link walk, the cmd.exe check and `resolve` are unchanged from 009e42f (`git diff 009e42f -- bridge/cursor-bridge/bridge-run.py` shows changes only inside `_package_folder_rewrite` and at its call in `main`).
- [ ] The logged head of a suite so launched is unchanged (`npm test` for `npm --prefix frontend test`), the folder never in it (Requirement 20).
- [ ] The updated case in `tests/test_bridge_run.py` names R-078 and asserts the three rewrites Requirement 19 names, in process; any refusal case you add names R-078.
- [ ] Every test in each of these files passes, each file's pytest summary line quoted from its own run: `tests/test_bridge_run.py`, `tests/test_bridge_run_driver.py`, `tests/test_release_s_launcher.py`, `tests/test_bug029_agent_name.py`, `tests/test_task032_supervisor_launcher.py`, `tests/test_header_plan.py`, `tests/test_header_plan_r3.py`, `tests/test_dump_cli.py`. These hold the subsystem this round touches (the launcher's folder options, `named_suite`, the cmd.exe check and `resolve`); after a fix that regressed, they are run in your own run.
- [ ] Requirements 1 to 24 stay met as round 6's code met them, but for the word Requirement 19 now hands.
- [ ] `python tools/dump-cli.py --check` reports the reference current, and `git diff 73869de -- bridge/cursor-bridge/bridge-run.py` shows no change inside the module docstring.
- [ ] `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` reports the sources match; `bridge/cursor-bridge/VERSION` unchanged.
- [ ] R-078's launcher clauses are fully met, with no stand-in, placeholder or "later" text.
- [ ] No new Semgrep high findings; every refusal is exit 125 before anything starts; every path compared by its resolved form with links refused on the way, and the runner given a word that, read from its working folder, is the path compared (ASVS L2).
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
- **Run named test files only**, with exactly the commands the Done section lists (`python -m pytest -p no:cacheprovider -q <file>`; your own run is already stripped by the launcher that started you). Do NOT run the full `tests/` tree (`python -m pytest`, `python -m pytest tests`, or any command that collects all of it); the supervisor and CI run the full suite. No `PYTHONPATH` or other environment change.
- Run no Python other than the Done section's commands: no `python -c`, no here-document, no script of your own, and never import the project's tests outside pytest.
- Do not refactor code outside the scope, even if it looks wrong. Do not change round 6's code beyond the one correction.
- Never run the product, a migration, a seed or a test against the owner's live data (Context, "Development data").
- No value in this increment is the owner's (rule 52).
- Follow existing conventions in the files you touch: the `bridge-run: refused - ...` lines through `KNOWN_RUNNER_REFUSE`, exit 125, ASCII-only code and docstrings. Every line of `bridge-run.py` stays ASCII; write any non-ASCII example in a test as `chr(0x....)`.
- These git commands are not yours to run: `commit`, `push`, `switch`, `checkout`, `merge`, `rebase`, `reset`, `stash`, `branch -d`, `worktree`. You read with `git status`, `git diff` and `git log` only. (Tests run git inside their own scratch repositories under `tmp_path`; that is not this repository.)
- Numbers from text are parsed with the language's own parser, never by slicing a string. This increment reads no number from text.
- Every verification command is written in the Done section in full; run exactly those, from the Workspace root. The supervisor checks this increment's tests by mutation after your run, with its own mutants file. You may apply these mutations by hand in-process in your own run, reverting each, to check the tests catch them; list each by its label, only where applied with the pytest output line that shows the test failing, else `not run`: (M1) the helper accepts a flag given twice; (M2) the helper accepts an `-X` value other than `utf8`; (M3) the folder rule skips the link walk; (M4) the option list admits a word outside it (an abbreviation such as `--pre`, or a cluster such as `-sC`); (M5) a folder option after a bare `--` is read; (M6) `merge_ids` written unsorted; (M7) the cmd.exe character check skipped. (M8) is withdrawn: write it `withdrawn` in the report. No mutation script lands in the diff.
- **Known failures.** On round 6's code (009e42f) the supervisor's acceptance file gives 17 failed, 5 passed in the tests this round pins: the five cases of `test_r078_the_runner_is_given_the_folder_the_rule_checked`, `test_r078_a_trailing_dot_name_never_reaches_the_runner_as_written`, `test_r078_a_launch_folder_with_a_space_runs_under_a_runner_in_a_spaced_folder`, the five cases of `test_r078_a_launch_folder_holding_a_cmd_character_runs` and the five cases of `test_r078_a_handed_folder_never_begins_with_a_dash`. Your own case `test_r078_folder_option_value_rewritten_to_rule_checked_path` asserts round 6's absolute word until you update it. This round turns all of them green. No other failure is known in the files the Done section runs; if another fails and this change did not cause it, report it by its test id and fix none.
- If an acceptance test and this brief seem to disagree, or a test seems to pin something this brief does not say, stop and report it; do not edit the test.
- Prefer reuse over new code: round 6's helper, its `abs_path`, and the scan's label (line 329) are the model, and write the minimum that meets the acceptance criteria (the frozen `minimal-code.mdc` is in force). This never overrides a security, observability or accessibility requirement stated above.
- Rules in force for you: `.cursor/rules/secure-coding.mdc`, `.cursor/rules/workspace-boundary.mdc` and the frozen `minimal-code.mdc`.

## Done
Your report is the file `handoff/TASK-059-r7-report.md`, which you write as you go: what you did, what you changed, what you ran and what it printed, what you could not do, so that nothing of it is lost when your run ends early. It names no computer path: write `<Workspace>` for the repository folder and `~` for the home folder, including in quoted command output.

When you finish, it holds:
- a list of every file you changed;
- a one-paragraph summary of what you did;
- for Requirement 19 as amended, one sentence each for (a), (b) and (c) on how the change meets it, naming the function and line, and one sentence on how the change removes R1 (both its parts) while the runner still reads back the folder checked;
- every command of the list below with its output, each test file's pytest summary line quoted from its own command;
- the mutations (M1 to M7), each applied one with the pytest output line that shows the test failing, each other one written `not run`, and (M8) written `withdrawn`;
- a section headed exactly `Assumed, not verified`, as the report's last section.

The `Assumed, not verified` section lists every fact this change relies on that neither this brief nor the existing code settled, and that you did not confirm, among them, where they apply: that npm, pnpm and yarn resolve a relative folder value beginning with `.` against their working folder; that a real npm.cmd passes `.\frontend` through cmd.exe unchanged (the acceptance tests use stand-ins); that no runner reads `.\x` differently from `./x`. One item per line: what you assumed · why · what would confirm it. If there are none, write `Assumed, not verified: none`. Be specific: "edge cases" or "error handling" is not an item.

Run these from the Workspace root, in this order, after your last edit, each in the foreground, with no `PYTHONPATH` or other environment change.
1. `python tools/make-manifest.py`
2. `python tools/dump-cli.py --check` (expect the reference current)
3. `python -m pytest -p no:cacheprovider -q tests/test_program_launcher_forms.py`
4. `python -m pytest -p no:cacheprovider -q tests/test_bridge_run.py`
5. `python -m pytest -p no:cacheprovider -q tests/test_bridge_run_driver.py`
6. `python -m pytest -p no:cacheprovider -q tests/test_release_s_launcher.py`
7. `python -m pytest -p no:cacheprovider -q tests/test_bug029_agent_name.py`
8. `python -m pytest -p no:cacheprovider -q tests/test_task032_supervisor_launcher.py`
9. `python -m pytest -p no:cacheprovider -q tests/test_header_plan.py`
10. `python -m pytest -p no:cacheprovider -q tests/test_header_plan_r3.py`
11. `python -m pytest -p no:cacheprovider -q tests/test_dump_cli.py`
12. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` (expect the sources to match)
13. `git diff --stat 009e42f -- bridge/cursor-bridge/bridge-run.py tests/test_bridge_run.py`
14. `git rev-parse HEAD` and `git status --short`

Every command you ran is quoted in the report with the lines it printed, verbatim, in a fenced block; the launcher's own lines (`bridge-run: started ...`, `bridge-run: exit ...`) included. Each pytest summary line is quoted verbatim; never restate a count in prose. A claim that a check passed quotes the output line that shows it, and a number of failing or skipped cases is backed by the pytest lines naming them. A command you did not run is written `not run`, never described as run. Run this brief's test commands once more after your last edit, and write the report's results after step 14, naming the commit its counts belong to (`git rev-parse HEAD`) and whether the working tree then held uncommitted changes (`git status --short`).

Your last message is the summary and the report file's path, and nothing follows it. The supervisor reads only the last message, and a message printed earlier and then followed by more work is lost.
