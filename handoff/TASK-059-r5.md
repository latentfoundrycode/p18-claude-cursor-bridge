---
record: brief
header: 1
id: "TASK-059"
round: 5
satisfies: [R-078]
scope: ["bridge/cursor-bridge/bridge-run.py", "bridge/cursor-bridge/bridge_env.py", "bridge/cursor-bridge/MANIFEST.json", "tests/test_program_launcher_forms.py", "tests/test_bridge_run.py", "tests/test_bridge_run_driver.py", "tests/test_release_s_launcher.py", "docs/BUILDER_NOTES.md", "handoff/TASK-059-r5-report.md"]
merge_unit: null
blocking_class: security
---
# TASK-059 round 5: The launcher's command forms: a folder value held to a list of characters (R-078)

Round cause: security - round 4's security audit ran npm in a folder the rule never checked, by a folder value npm trims (a leading U+00A0 before `~/`) or expands (`${NAME}`) that round 4 accepted (both reproduced through the launcher with npm 11.16.0)

Blocking class: security - security audit, round 4, B1 and B2 (a folder value npm trims or expands to a folder the rule never checked)

## Objective
This is round 5 of TASK-059, a one-correction round. Round 4's code is committed (commit 25414fa, "TASK-059: round 4 of the builder (R-078)"): Review A approved it, and the security audit failed it on two findings, B1 and B2, of the security class. Round 4's code is the base of this round and stays as it is; you make exactly one correction, the one Requirement 19 (amended again below) states, add one case of your own to `tests/test_bridge_run.py`, and write the report. Requirements 1 to 24 (round 3's brief `handoff/TASK-059-r3.md` numbers them, round 4's brief `handoff/TASK-059-r4.md` amended Requirement 19) stand as round 4's code met them and must stay met; they are not work in this round, and earlier rounds' corrections are already built. The findings: npm's parser trims a folder value (JavaScript `trim()`: U+00A0, U+2000 to U+200A, U+3000, U+FEFF and the ASCII whitespace) before its home rule, so a value of U+00A0 followed by `~/x` passed round 4's `startswith("~")` and ran npm in `<home>/x` (B1); npm's configuration expands `${NAME}` and `${NAME?}` in a path value after the folder rule checked the literal text, so `a${OS}/x` passed the rule while npm ran in `aWindows_NT/x` (B2). The supervisor's acceptance file `tests/test_program_launcher_forms.py` gained two tests that pin the correction, `test_r078_a_folder_value_outside_the_character_list_is_refused` and `test_r078_a_trimmed_or_expanded_folder_value_is_refused_before_anything_starts`, committed after 25414fa and before this brief; you edit nothing in that file. The increment as a whole (round 1's brief `handoff/TASK-059.md` and rounds 2 to 4's `handoff/TASK-059-r2.md`, `handoff/TASK-059-r3.md` and `handoff/TASK-059-r4.md`, which you may read for history) makes the launcher accept the interpreter's two flags `-B` and `-X utf8`, serve a suite in a subfolder through npm's, pnpm's and yarn's folder options held to the target rule, hold the runners' option names in the environment to the same list, give a refused option of a known runner its own exit-125 message, write `merge_ids` sorted and escape the root of both plan globs.

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
- handoff/TASK-059-r5-report.md

Limits on these files:
- `bridge/cursor-bridge/bridge-run.py`: the one correction of Requirement 19 goes here, in `_package_scan_folder_options` (and, if you compile the expression at module level, beside the constants there). Its module docstring (the triple-quoted string at the top of the file) does not change at all (round 3's Requirement 12). Every line stays ASCII.
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
- Every change to round 4's code other than the one correction of Requirement 19: no rework of Requirements 1 to 24 as round 4 met them, no refactoring. The value's other checks (missing, twice, the roots, the link walk) stay as they are.
- No new launcher option and no change to an existing one (`--limit`, `--kind`, `--strip`, `--key-file`, `--healthy`). No new dependency.
- Every other test file.
- The leads the supervisor recorded in `docs/HARDENING.md`'s TASK-059 section, which you do not work on.

## Context
**Development data.** `docs/INVENTORY.md`: "Development data: the dev build is the Workspace sources under `bridge/`; a session in the repo always runs the *installed* bridge (`~/.claude`), never the one being edited, and installs reach running projects only through the owner's install run sheet (§15 condition 1, A1a condition 1)". For you: the code under `bridge/cursor-bridge/` is exercised only by the tests, which load it from the Workspace (the `program` fixture of `tests/conftest.py`) or start it as `bridge/cursor-bridge/bridge-run.py` in temporary folders under `tmp_path`. Never read, edit or copy anything under the home folder.

**The findings.** `docs/HARDENING.md`, its TASK-059 section, records round 4's security audit, B1 and B2 (read it; do not repeat the probes). B1: npm trims a folder value's leading Unicode or ASCII whitespace (JavaScript `trim()`: U+00A0, U+2000 to U+200A, U+3000, U+FEFF and the ASCII whitespace) before its home rule reads `~/`, while the launcher's rule read the untrimmed text, which does not start with `~`, as a folder inside the launch folder. B2: npm's configuration expands `${NAME}` and `${NAME?}` in a path value after the folder rule checked the literal text, so the rule checked a folder named `a${OS}/x` inside the launch folder and npm ran in `aWindows_NT/x`. Whether pnpm and yarn trim or expand the same way was not probed; the list covers them either way.

**Round 4's code as committed** (`bridge/cursor-bridge/bridge-run.py` at 25414fa; the lines this round touches):
- `import re` (line 98); the module's compiled patterns are module-level constants, for example `RUN_ID_RE = re.compile(r"^\d{4}-...$", re.ASCII)` (line 128).
- Constants (lines 216-228): `KNOWN_RUNNER_REFUSE` (the known-runner message, `"bridge-run: refused - the launcher knows this runner and refuses %r; it is a defect to report, never a run to start by hand\n"`), `PACKAGE_FOLDER_LONG`, `PACKAGE_FOLDER_CANON`, `PACKAGE_ALLOWED_FLAGS`.
- `def _package_folder_value(word, argv, i):` (line 278) the value of a folder option, from its `=` form or the next word.
- `def _package_folder_ok(value, launch_folder):` (line 286) the folder rule: a relative value joined to the launch folder (line 290), then `os.path.isdir`, the launch roots by `_real_path`, and `_link_walk_ok`. This is the first filesystem call a value meets.
- `def _package_scan_folder_options(argv, head, folder):` (line 304) returns `(run_dir, refused word)`; for a folder option it reads the value (line 324), sets `label` to the option's word without any `=` part (line 325), refuses a repeat (lines 326-328) and a missing or blank value (lines 329-330), then refuses by its text a value that starts with `-` (lines 331-332) and, since round 4, one that starts with `~` (lines 333-334), and only then calls `_package_folder_ok` (lines 335-336):

```python
            if value.startswith("-"):
                return run_dir, label
            if value.startswith("~"):
                return run_dir, label
            if not _package_folder_ok(value, base):
                return run_dir, label
```

  The returned `label` is what `known_runner_refuse_word` passes on to the known-runner message, so a refusal here names the folder option (`--prefix`, `-C`, `--dir`, `--cwd`) with no `# wake`, exit 125, before anything starts.

**The acceptance tests** (`tests/test_program_launcher_forms.py`, the supervisor's; read its module docstring and the tests).
- `test_r078_a_folder_value_outside_the_character_list_is_refused(br, tmp_path)` (in process, not parametrised): for every folder option of `OPTIONS = [("npm", "--prefix"), ("npm", "-C"), ("pnpm", "--dir"), ("pnpm", "-C"), ("yarn", "--cwd")]`, each value of `FOLDER_SHAPED` (`frontend`, `./frontend`, `sub-dir_1.x`, `frontend` joined to `pkg` by `os.path.join`, `frontend/pkg`) is accepted by `br.test_suite`, and each value of `NOT_A_FOLDER` (U+00A0, U+3000, U+FEFF or U+2002 before `~/x`; a space before `~/x`; `frontend` with a trailing space, a leading space or a leading tab; `a${OS}/x`, `${HOME}`, `a${Z?}b`, `a{b}`; `front` U+00EB `nd`; `a$b`, `a b`, `a;b`, `a'b`, `a,b`) is refused in the two-word and the `=` form, before and after the subcommand, with `br.known_runner_refuse_word` naming the option. Each refused value names a folder created inside the launch folder where the system allows the name, so the refusal is the list's, not the folder rule's.
- `test_r078_a_trimmed_or_expanded_folder_value_is_refused_before_anything_starts(ws, value)` (through the launcher, two parametrised cases: U+00A0 followed by `~/x`, and `a${OS}/x`): with the folder planted, `npm --prefix <value> test` gets the known-runner message naming `--prefix`, exit 125, before `bridge-run: started`; the control `npm --prefix frontend test` starts.
- Round 4's `test_r078_a_folder_value_beginning_with_a_tilde_is_refused` (five parametrised cases) stays in the file and must stay green.

**Security context.** ASVS level 2 (`docs/INVENTORY.md`: "The builder's secure-coding rule is ASVS level 2"; the bridge launches subprocesses, confines paths, reads keys and gates merges). Trust boundaries: the launcher's command line is untrusted input (the allow rule lets an agent start an accepted command without the owner's word, so every form the launcher accepts must be held to the target rule); the filesystem under the launch folder is untrusted (an agent may have planted a folder of any name the system allows, a symbolic link or a junction). The security auditor reads this round's diff. `.cursor/rules/secure-coding.mdc` and `.cursor/rules/workspace-boundary.mdc` are in force for you, and the frozen `minimal-code.mdc`.

**External services.** None. The increment calls no service and adds no remote wait.

**Values.** No value in this increment is the owner's (rule 52). The folder options and the character list are the design's, the reality check's and the reviews', pinned by the acceptance tests.

## Diagrams
None. The build plan names no diagram for this increment (`Diagrams: none`).

## Requirements
Requirements 1 to 24 are round 3's brief's (`handoff/TASK-059-r3.md`), numbered as there, Requirement 19 as round 4's brief amended it; every one stands as round 4's code (25414fa) meets it and must stay met. Round 5 amends Requirement 19 again only, and adds this round's report (Requirement 14 as round 3 wrote it, for the new report file).

19. **The folder rule (amended in round 5; security, the security audit's round-4 B1 and B2; replaces round 4's single `~` check).** As round 4 met it: the folder is accepted only where it exists as a folder, lies under the launch roots (`launch_roots`) by its resolved path, and every component from the launch folder to it is reached through no link (`bridge_env.is_link`), a link that leads back inside included. A relative value is read against the launch folder. Each of these is refused with exit 125 and the known-runner message naming the option before anything starts: a folder outside the roots; a link on the way; a folder that does not exist; the option given twice (an option and its other name count as one option, so `-C x --prefix x` is twice); a missing value (the option as the last word, or `--prefix=` with nothing after it); a value that starts with `-`; a value that starts with `~`. New in round 5: in `_package_scan_folder_options`, where the value is read (today the checks `value.startswith("-")` and `value.startswith("~")`, lines 331 to 334, before the `_package_folder_ok` call at line 335), a folder value is accepted only when its whole text matches one list: an optional leading drive (one ASCII letter and `:`), then one or more of the ASCII letters `A-Z` and `a-z`, the digits `0-9`, and `.`, `_`, `-`, `/` and the backslash; and its first character is neither `-` nor `~` (a leading `-` keeps today's refusal; `~` is outside the list anyway). Every other value is refused by its text before any filesystem call, with the known-runner message naming the folder option, for every folder option of npm, pnpm and yarn (npm `--prefix` and `-C`; pnpm `--dir` and `-C`; yarn `--cwd`), in the two-word and the `=` form, before or after the subcommand. Use a compiled regular expression matched against the whole value with `re.fullmatch` (ASCII classes written out, not `\w`, which matches letters outside ASCII), not `str.strip()`, which leaves U+FEFF. The `~` refusal of round 4 may stay or be folded into the list; the behaviour pinned is the same. The value's other checks (missing, twice, the roots, the link walk) stay as they are. Pinned by `test_r078_a_folder_value_outside_the_character_list_is_refused` (in process, every folder option; plain names, `./frontend`, `sub-dir_1.x`, `frontend/pkg` accepted; leading Unicode and ASCII spaces, a trailing space, a tab, `${...}`, `{`, `}`, `$`, a space inside, `;`, `'`, `,`, a letter outside ASCII refused) and `test_r078_a_trimmed_or_expanded_folder_value_is_refused_before_anything_starts` (through the launcher). Add one builder case to `tests/test_bridge_run.py`, naming R-078 in its name or docstring: the control `test_suite(["npm", "--prefix", "frontend", "test"], base)` True, and `test_suite` False for the value `chr(0xA0) + "~/frontend"` and for the value `"a${OS}"`, each with its folder created where the system allows the name (the existing `test_r078_npm_prefix_value_beginning_with_tilde_is_refused`, line 355, shows the `program` fixture and the `base` folder under `tmp_path`). Write any non-ASCII example in a test as `chr(0x....)`.

14. **The report (as round 3's Requirement 14, for this round).** The report `handoff/TASK-059-r5-report.md` lists the files you changed, the requirement this round amends and how the change meets it, every command of the Done list with its output lines, and the section `Assumed, not verified`. Mutations are listed only where applied, with the output line that shows the test failing; a mutation not applied is written `not run`. No computer path in the report: `<Workspace>` and `~`.

## Acceptance criteria
- [ ] Every test in `tests/test_program_launcher_forms.py` passes (it names R-078), `test_r078_a_folder_value_outside_the_character_list_is_refused`, the two cases of `test_r078_a_trimmed_or_expanded_folder_value_is_refused_before_anything_starts` and the five cases of `test_r078_a_folder_value_beginning_with_a_tilde_is_refused` among them; the npm test and the two cmd.exe tests pass or are skipped only for their own stated reason, quoted from the pytest output.
- [ ] A folder value whose whole text is not an optional leading drive (one ASCII letter and `:`) followed by one or more of `A-Z`, `a-z`, `0-9`, `.`, `_`, `-`, `/` and the backslash, or whose first character is `-` or `~`, is refused in `_package_scan_folder_options` by its text with `re.fullmatch` on a compiled expression, before `_package_folder_ok` or any other filesystem call, with the known-runner message naming the folder option, exit 125, before the `bridge-run: started` line (Requirement 19).
- [ ] The new case in `tests/test_bridge_run.py` names R-078, asserts its control `test_suite(["npm", "--prefix", "frontend", "test"], base)` True and `test_suite` False for `chr(0xA0) + "~/frontend"` and for `"a${OS}"`, each with its folder created where the system allows the name.
- [ ] Every existing test in `tests/test_bridge_run.py`, `tests/test_bridge_run_driver.py`, `tests/test_release_s_launcher.py`, `tests/test_bug029_agent_name.py`, `tests/test_task032_supervisor_launcher.py`, `tests/test_header_plan.py`, `tests/test_header_plan_r3.py` and `tests/test_dump_cli.py` passes.
- [ ] Requirements 1 to 24 stay met as round 4's code met them; nothing in `bridge-run.py` changes but the one correction.
- [ ] `python tools/dump-cli.py --check` reports the reference current, and `git diff 73869de -- bridge/cursor-bridge/bridge-run.py` shows no change inside the module docstring.
- [ ] `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` reports the sources match; `bridge/cursor-bridge/VERSION` unchanged.
- [ ] R-078's launcher clauses are fully met, with no stand-in, placeholder or "later" text.
- [ ] No new Semgrep high findings; every refusal is exit 125 before anything starts; every path compared by its resolved form with links refused on the way (ASVS L2).
- [ ] No launcher option added or changed; no new dependency; `bridge-run.py` stays ASCII.

## Constraints
- Do not add dependencies.
- Do not read or write any file outside this workspace (the folder you were started in). Everything you need is inside it; everything you produce goes inside it.
- No secret is needed or used. Refer to `.env` and configuration keys by name only; never reproduce a value.
- If the brief, the rules, or the tooling got in your way (an instruction that contradicted another, a check that fired wrongly, a step that cost time for no reason), append one dated line describing it to `docs/BUILDER_NOTES.md`. Do not try to fix the tooling. Do the same for anything you learned about a defect or a pitfall (a cause you found, a platform quirk that cost you a round): one dated line, so the supervisor can carry it forward.
- In any Markdown you write, never break a line inside a paragraph or a list item; one paragraph is one line. Line breaks only between blocks.
- This increment talks to no external service and adds no remote wait.
- Any console process your code launches on Windows is created windowless (`creationflags=subprocess.CREATE_NO_WINDOW` in Python, `0` on other platforms); this round starts no new process in the launcher (the refusal reads the command's text only). Every subprocess call in a test passes `creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)` and a timeout.
- **Run every command in the foreground and wait for it to end.** Start nothing in the background, and leave no process running when you finish. Never start a server, a watcher or a daemon.
- **Run named test files only**, with exactly the commands the Done section lists (`python -m pytest -p no:cacheprovider -q <files>`; your own run is already stripped by the launcher that started you). Do NOT run the full `tests/` tree (`python -m pytest`, `python -m pytest tests`, or any command that collects all of it); the supervisor and CI run the full suite. No `PYTHONPATH` or other environment change.
- Run no Python other than the Done section's commands: no `python -c`, no here-document, no script of your own, and never import the project's tests outside pytest.
- Do not refactor code outside the scope, even if it looks wrong. Do not change round 4's code beyond the one correction.
- Never run the product, a migration, a seed or a test against the owner's live data (Context, "Development data").
- No value in this increment is the owner's (rule 52).
- Follow existing conventions in the files you touch: the `bridge-run: refused - ...` lines, exit 125, ASCII-only code and docstrings. Every line of `bridge-run.py` stays ASCII; write any non-ASCII example in a test as `chr(0x....)`.
- These git commands are not yours to run: `commit`, `push`, `switch`, `checkout`, `merge`, `rebase`, `reset`, `stash`, `branch -d`, `worktree`. You read with `git status`, `git diff` and `git log` only. (Tests run git inside their own scratch repositories under `tmp_path`; that is not this repository.)
- Numbers from text are parsed with the language's own parser, never by slicing a string. This increment reads no number from text.
- Every verification command is written in the Done section in full; run exactly those, from the Workspace root. The supervisor checks this increment's tests by mutation after your run, with its own mutants file. You may apply these mutations by hand in-process in your own run, reverting each, to check the tests catch them; list each by its label, only where applied with the pytest output line that shows the test failing, else `not run`: (M1) the helper accepts a flag given twice; (M2) the helper accepts an `-X` value other than `utf8`; (M3) the folder rule skips the link walk; (M4) the option list admits a word outside it (an abbreviation such as `--pre`, or a cluster such as `-sC`); (M5) a folder option after a bare `--` is read; (M6) `merge_ids` written unsorted; (M7) the cmd.exe character check skipped. (M8) is withdrawn: write it `withdrawn` in the report. No mutation script lands in the diff.
- **Known failures.** `test_r078_a_folder_value_outside_the_character_list_is_refused` and the two cases of `test_r078_a_trimmed_or_expanded_folder_value_is_refused_before_anything_starts` are red on round 4's code (the acceptance file's docstring); this round turns them green. No other failure is known in the files the Done section runs; if another fails and this change did not cause it, report it by its test id and fix none.
- If an acceptance test and this brief seem to disagree, or a test seems to pin something this brief does not say, stop and report it; do not edit the test.
- Prefer reuse over new code: the existing refusals at lines 331 to 334 are the model, and write the minimum that meets the acceptance criteria (the frozen `minimal-code.mdc` is in force). This never overrides a security, observability or accessibility requirement stated above.
- Rules in force for you: `.cursor/rules/secure-coding.mdc`, `.cursor/rules/workspace-boundary.mdc` and the frozen `minimal-code.mdc`.

## Done
Your report is the file `handoff/TASK-059-r5-report.md`, which you write as you go: what you did, what you changed, what you ran and what it printed, what you could not do, so that nothing of it is lost when your run ends early. It names no computer path: write `<Workspace>` for the repository folder and `~` for the home folder, including in quoted command output.

When you finish, it holds:
- a list of every file you changed;
- a one-paragraph summary of what you did;
- for Requirement 19 as amended, one sentence on how the change meets it, naming the function and line;
- every command of the list below with its output;
- the mutations (M1 to M7), each applied one with the pytest output line that shows the test failing, each other one written `not run`, and (M8) written `withdrawn`;
- a section headed exactly `Assumed, not verified`, as the report's last section.

The `Assumed, not verified` section lists every fact this change relies on that neither this brief nor the existing code settled, and that you did not confirm, among them, where they apply: that pnpm and yarn trim or expand a folder value as npm does (the list covers them either way); that an absolute folder value of the test fixtures holds only listed characters on every computer the suite runs on. One item per line: what you assumed · why · what would confirm it. If there are none, write `Assumed, not verified: none`. Be specific: "edge cases" or "error handling" is not an item.

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
