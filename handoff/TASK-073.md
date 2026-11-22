---
record: brief
header: 1
id: "TASK-073"
round: 1
satisfies: [R-094]
scope: ["bridge/cursor-bridge/bridge-install.py", "bridge/cursor-bridge/MANIFEST.json", "docs/cli-reference.json", "docs/CLI_REFERENCE.md", "tests/test_program_install_keep.py", "tests/test_install_check.py", "tests/test_install_check_a4.py", "tests/test_rollback.py", "docs/BUILDER_NOTES.md", "handoff/TASK-073-r1-report.md"]
merge_unit: null
blocking_class: null
---
# TASK-073: The installer refuses unknown words and keeps a named copy (R-094)

## Objective
`bridge/cursor-bridge/bridge-install.py` installs the bridge into a `.claude` folder and takes a release back with `--rollback`. Today its `main()` reads its words by membership only: a word it does not know (`--help`, `--yes`, a typo, a positional word) is ignored and the program goes on to install, and `--target` as the last word raises an `IndexError`. This increment makes the installer read and check every word of its command line before it reads or writes anything else, and refuse anything it does not know with the usage and exit 2, the target untouched. It also adds `--keep <version>`, which marks one earlier kept copy under `<target>/cursor-bridge-previous/` so that it survives later installs beside the one previous release (until another `--keep` or `--keep none`), and lets `--rollback` name a kept copy (`--rollback <version>`), a rollback to an older copy removing the newer kept copies and writing `cursor-bridge/ROLLED-BACK.md` from every CHANGELOG entry newer than its target. The owner keeps a known-good release while trying newer ones, and a mistyped word never installs.

Satisfies: R-094 - The installer refuses what it does not know and can keep a named copy (C9, C11): `bridge-install.py` checks every word before it does anything, and an unknown option, `--help`, a positional word or a missing value prints the usage and exits 2, the target untouched; `--keep <version>` keeps the named earlier copy beside the one previous release, the value matched against the kept folders' names and never used as a path, a marker beside the copy keeping it over later installs until another `--keep` names another or `--keep none`; `--rollback [<version>]` can name a kept copy, a rollback to the older one removing the newer kept copies and writing `ROLLED-BACK.md` from every entry newer than its target. (Its row in `docs/REQUIREMENTS.md` is line 120.)

## Scope
Files and directories you may create or modify:
- bridge/cursor-bridge/bridge-install.py
- bridge/cursor-bridge/MANIFEST.json
- docs/cli-reference.json
- docs/CLI_REFERENCE.md
- tests/test_program_install_keep.py
- tests/test_install_check.py
- tests/test_install_check_a4.py
- tests/test_rollback.py
- docs/BUILDER_NOTES.md
- handoff/TASK-073-r1-report.md

Limits on these paths:
- `tests/test_program_install_keep.py`: the supervisor's acceptance tests (58 cases), committed before your run. Read it whole and run it. **Do not edit it.** If a case seems wrong, stop and report it by its test id.
- `tests/test_install_check.py`, `tests/test_install_check_a4.py`, `tests/test_rollback.py`: every existing case must pass **unedited**. The plan names these files because it expected one existing test that pins `--help` installing; the supervisor found none (Context, "The existing tests"), so no existing case is rewritten. The one edit allowed: you may append cases of your own at the very end of `tests/test_rollback.py`, below a line you add, `# ---- builder's cases below this line`, for example a case for `--keep` given with `--rollback` (R4). Nothing above that line changes. The other two files are not edited at all.
- `bridge/cursor-bridge/MANIFEST.json` changes only by running `python tools/make-manifest.py` (Done), never by hand. `bridge/cursor-bridge/VERSION` is outside Scope; `make-manifest.py` rewrites its line endings, so restore it with `git restore bridge/cursor-bridge/VERSION` right after (Done).
- `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` change only by running `python tools/dump-cli.py` (Done), never by hand.

Do not modify anything else.

## Out of scope
- .env and anything under secrets/
- CI configuration
- docs/ and handoff/, except the files the Scope section names. Every other record under docs/ is the supervisor's.
- Every other program under `bridge/cursor-bridge/` (`bridge-check.py` included), the texts under `bridge/commands/`, `bridge/agents/`, `bridge/skills/` and `bridge/cursor-bridge/workflow/`, and `bridge/cursor-bridge/CHANGELOG.md` (no CHANGELOG entry in this increment).
- `tools/make-manifest.py` and `tools/dump-cli.py`: you run them and edit neither.
- Every test file other than the four in Scope. A failure in one is reported by its test id, never fixed there.
- `run/` (the supervisor's): read only.
- Any mutation script or mutants file. The mutants file and the mutation run are the supervisor's, after your run.
- `~/.claude`, `~/.cursor-bridge` and any real installation: you never install anything (Constraints).

## Context
**The design that binds this increment.** `docs/DESIGN.md` line 362, the bullet `*C9 and C11.*`: "`bridge-install.py` checks every word before it does anything: an unknown option, `--help`, a positional word or a missing value prints the usage and exits 2, the target untouched. `--keep <version>` keeps the named earlier copy beside the one previous release, the value matched against the kept folders' names and never used as a path, a marker beside the copy keeping it over later installs until another `--keep` names another or `--keep none`; `--rollback [<version>]` can name it, a rollback to the older copy removing the newer kept ones and writing `ROLLED-BACK.md` from every entry newer than its target." The plan entry is `docs/BUILD_PLAN.md`, `### TASK-073` (line 1925), its `Done when` on line 1934.

**`bridge-install.py` as it stands (read it whole; 715 lines).**
- Module docstring, lines 2-66. Its usage lines are 5-6: `python <release>/cursor-bridge/bridge-install.py [--target <path-to-.claude>] [--dry-run] [--anyway]` and `python <release>/cursor-bridge/bridge-install.py --rollback [--target <path-to-.claude>] [--dry-run]`. Its exit list is lines 63-65 ("Exit 0 = installed (or rolled back) and verified; 1 = verification failed; 2 = refused, ..."). The docstring says "ASCII-only on purpose (cp1252 consoles)".
- `PREVIOUS = "cursor-bridge-previous"` (line 81), `ROLLED_BACK = os.path.join("cursor-bridge", "ROLLED-BACK.md")` (line 82).
- `save_previous(target, version, files, dry)` (lines 354-374): returns early when `dry` or when `<target>/cursor-bridge-previous/<version>` already exists (a repeated run after an interruption); otherwise `shutil.rmtree(base, ignore_errors=True)` (the one-previous rule: every older kept copy goes), then writes the copy under `<version>.partial` and renames it.
- `rolled_back_note(leaving_changelog, cur_version, prev_version)` (lines 377-403) returns `(text, found)`: the "If rolled back" parts of every changelog entry newer than `prev_version` (versions sort as text). It already gives the right note for a rollback to an older copy when called with that copy's version.
- `install(target, dry, anyway=False)` (lines 579-640): the release checks, then, when the installed version differs, the S4 check of the installed tree, `save_previous`, the "previous ... kept at" and "way back" lines, then `replace_release(...)`, then removal of a stale `ROLLED-BACK.md` and `run_check(target)`. An install of the version already installed, with the same fingerprints, saves nothing and rewrites the same files (no change).
- `rollback(target, dry)` (lines 643-691): refuses the release folder as target; lists the kept folders (`os.path.isdir`, not ending `.partial`), takes `saved[-1]` (the newest, names sort as versions); refuses an incomplete or changed copy; writes `ROLLED-BACK.md` before the files change (not in a dry run); `replace_release`; `run_check`; and only when the check passes removes the restored copy (`shutil.rmtree(prev_tree)`) and the `cursor-bridge-previous` folder if it is then empty. When the check fails the copy stays.
- `main()` (lines 694-707): `dry = "--dry-run" in argv`; `--target` read as `argv[argv.index("--target") + 1]` and made absolute; `--rollback` membership selects `rollback`, else `install(target, dry, "--anyway" in argv)`; `OSError`/`ValueError` become exit 2 with the "stopped, because a file could not be read or written" line.

**Signatures other tests call in-process; keep each callable with the same positional arguments (a new parameter is optional, with a default that gives today's behaviour):** `install(target, dry, anyway=False)` (`tests/test_rollback.py:405`, `tests/test_bug037.py:103`), `rollback(target, dry)` (`tests/test_rollback.py:285`, `:443`), `replace_release(target, source, existing, new_settings, dry)` (`tests/test_rollback.py:373`), `rolled_back_note(leaving_changelog, cur_version, prev_version)` (`tests/test_release_b_stamp.py:123`, `tests/test_release_b2_stamp.py:137`, `tests/test_release_t_stamp.py:145`, `tests/test_hotfix_intake.py:284`).

**The command reference.** `tools/dump-cli.py` writes `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` from each program under `bridge/cursor-bridge/`. `classify_program` (lines 182-189): a file with a top-level `build_parser()` is recorded from its argparse parser; a file whose text holds `ArgumentParser` without a top-level `build_parser()` makes dump-cli exit 1; any other file is recorded from its module docstring. `bridge-install.py` is recorded today with `"source": "docstring"` (`docs/cli-reference.json` line 24), and it stays so: the module docstring is where the reference reads the installer's usage (R8).

**The acceptance tests.** `tests/test_program_install_keep.py` (58 cases) fixes the interface; its module docstring (lines 1-30) states the forms it pins and what it leaves open. Read it whole. Each case builds a scratch computer under pytest's `tmp_path` (HOME, USERPROFILE, LOCALAPPDATA, APPDATA and the working folder all scratch), with release folders `A=2026.01.01a`, `B=2026.01.02a`, `C=2026.01.03a`, `D=2026.01.04a` made from `bridge/` (each with one file of its own, `cursor-bridge/only-<version>.md`, and one "If rolled back" item per CHANGELOG entry), and runs each release's own `bridge-install.py` as a subprocess. The starting target holds B installed and A as the one previous release. `snapshot()` hashes every folder and file under the scratch computer, names and bytes, before and after a run that must change nothing. `kept_versions()` lists only the folders under `cursor-bridge-previous/` whose names match `^\d{4}\.\d{2}\.\d{2}[a-z]$`. An install succeeds when the output holds `MATCHES bridge <version>` (bridge-check's `RESULT: INSTALLED TREE MATCHES bridge <version>`). The cases whose docstrings say "Holds today" (the four `test_r094_the_known_words_are_still_accepted_in_any_order` cases and `test_r094_one_previous_release_is_kept_without_keep`) are expected to pass before your change; the others are expected to fail before it. After your change all 58 pass.

**The existing tests (the supervisor's reality check, read, not run).** No existing test pins `--help` installing: `tests/test_install_check.py:286-294` runs `--help` against `tools/make-manifest.py`, not the installer. Every existing call of the installer passes only `--target <path>`, `--dry-run`, `--anyway` and `--rollback`, each at most once (`tests/test_install_check.py` adds `--anyway` to every run of the repository's own installer, line 33), so the strict word check leaves them green. Tests that assert what `cursor-bridge-previous/` holds without `--keep`: `tests/test_rollback.py` lines 155, 290, 331, 450 (the folder is gone after a rollback that passes its check), `tests/test_bug034.py:62` (`iterdir()` equals exactly `["2025.01.01a"]`), `tests/test_install_check_a4.py:66-67` (`iterdir()` empty after a refused install). Hence R3's rule that with no `--keep` ever given the folder holds exactly what it holds today. Out-of-scope tests that also run or load the installer and must stay green: `tests/test_bug034.py`, `tests/test_bug037.py`, `tests/test_core_carve.py:155`, `tests/test_hotfix25a_stage_records_install.py:173-196`, and the four that load `rolled_back_note` (above).

**External services.** None. Make no network call.

**Trust boundaries and security context.** ASVS level 2 (`docs/INVENTORY.md`, Decisions, line 140). `.cursor/rules/secure-coding.mdc` is in force for you. Input crossing into this program: the command-line words (any text) and the names of the folders under `<target>/cursor-bridge-previous/`. The `--keep` and `--rollback` values are never used to build a path until they have matched, exactly, a name read from that folder's listing. On Windows the file system is case-insensitive, so `os.path.isdir(os.path.join(base, value))` would accept `2026.01.01A` for `2026.01.01a`, and a value that begins with `..` and a separator would reach outside the folder; this is why the match is a string comparison against the listing (R2). No exception escapes as a traceback.

**Development data.** The inventory's decision (`docs/INVENTORY.md`, Decisions, line 135): "Development data: the dev build is the Workspace sources under `bridge/`; a session in the repo always runs the *installed* bridge (`~/.claude`), never the one being edited, and installs reach running projects only through the owner's install run sheet". For you this means: the installer runs only through the tests, on their scratch targets under `tmp_path`. Never run `bridge-install.py` yourself, and never with a target under your home folder, `~/.claude` or `~/.cursor-bridge`; with no `--target` it installs into the home folder's `.claude`.

**Host.** Windows 11 with the owner's Python. CI also runs on Linux.

## Diagrams
None. The plan entry names no diagram for this increment.

## Requirements
1. **R1. Every word is read first.** Before it reads or writes any file (the release folder, the target, settings, git), `main()` reads every word of `sys.argv[1:]`. The known words, exactly: `--target <path>`, `--dry-run`, `--anyway`, `--rollback` with an optional `<version>` (the next word, when there is one and it does not begin with `-`), and `--keep <version>` or `--keep none`. A value word for `--target` or `--keep` is the next word; when there is no next word, or it begins with `-`, the option is missing its value. Refused with the usage and exit 2, nothing read or written: any other word beginning with `-` (`--version`, `--yes`), an abbreviation (`--dry`), an `=` form (`--target=<path>`), `--help`, `-h`, a positional word anywhere (including a word after `--dry-run`, or a second word after `--rollback <version>`), any option given twice, an option missing its value, and `--keep` given together with `--rollback`. There is no help option. The usage text names all five options (`--target`, `--dry-run`, `--anyway`, `--rollback`, `--keep`) and goes to stdout or stderr, your choice. Using argparse is neither required nor forbidden, but none of its defaults may leak through (abbreviation matching, `--help` exiting 0, `--opt=value` forms), and see R8 for what the command reference needs. Combinations not named here behave as today (for example `--anyway` with `--rollback` is accepted and has no effect, as today).
2. **R2. The value is a name, never a path.** A `--keep` value other than `none`, and a `--rollback` version, is compared as a string, exactly and case-sensitively, with the names of the folders directly under `<target>/cursor-bridge-previous/` (a folder whose name ends `.partial` is no kept copy, as `rollback()` already treats it, and the marker of R3 is not a folder). It is never joined to a path before that match. A value holding `/` or a backslash, `..`, a colon (a drive letter), the empty string, or a name that matches no kept folder exits 2 with a message naming the problem, and nothing is changed (the usage may be printed with it, your choice). This check runs before anything is written, in a dry run too.
3. **R3. `--keep` keeps a named copy.** `--keep` is an install option: the run installs this release as usual (the version already installed again changes nothing, as today) and records the named copy as kept with a marker file in `<target>/cursor-bridge-previous/`, beside the copy. The marker's name is yours, but it is a file, not a folder, and its name does not match `^\d{4}\.\d{2}\.\d{2}[a-z]$`. The marked copy survives every later install beside the one previous release; another `--keep <version>` moves the mark; `--keep none` clears it; an unmarked copy is removed at the next install by the one-previous rule, as today. With no `--keep` ever given, `cursor-bridge-previous/` holds exactly what it holds today (no marker file), so the tests listed under Context, "The existing tests", stay green unedited. An install that is refused (exit 2) writes no marker. A marker that names a copy no longer present never makes an install or a rollback fail. Where in the run the marker is written (before or after the install check), and what happens to it when the install check fails (exit 1), are your choice; name both in the report.
4. **R4. `--keep` with `--rollback`** is refused with the usage, exit 2, nothing changed (R1). It is not covered by the acceptance file; a case of your own is optional and goes only below the marker line in `tests/test_rollback.py` (Scope).
5. **R5. `--rollback` alone** restores the previous release, the newest kept folder by version, as today, also when an older marked copy stands beside it. Whether that older marked copy stays after this rollback is your choice; name it in the report.
6. **R6. `--rollback <version>`** restores that kept copy (the value matched as in R2; a value naming no kept folder, or path-like, exits 2 and changes nothing). It applies the same refusals as today's rollback (the release folder as target, a copy not complete or not as shipped). It writes `cursor-bridge/ROLLED-BACK.md` from every CHANGELOG entry of the installed release newer than the target version (`rolled_back_note` already does this given that version), and removes every kept copy newer than the target version. Follow today's rule for what is removed when: today the restored copy is removed only once the install check after the rollback passes, and when the check fails every kept copy stays; the newer kept copies follow the same rule, so a failed check never leaves the owner with fewer ways back than before.
7. **R7. A dry run of each new form** (`--keep <version>`, `--keep none`, `--rollback <version>`) exits 0, prints the version it would act on (for `--keep none`: the word `none` or the copy whose mark it would clear), and changes nothing.
8. **R8. The usage and the reference.** The module docstring's usage lines gain `--keep <version>|none` on the install form and `--rollback [<version>]` on the rollback form, its prose says in a sentence or two what `--keep` and `--rollback <version>` do, and its exit list says that a word it does not know, or a value that names no kept copy, is exit 2. `bridge-install.py` stays recorded from its docstring in the command reference (`"source": "docstring"`): no top-level `build_parser()`, and the text `ArgumentParser` nowhere in the file (Context, "The command reference"). `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` are regenerated with `python tools/dump-cli.py`, and `python tools/dump-cli.py --check` exits 0.
9. **R9. ASCII.** `bridge-install.py` stays ASCII-only (its docstring says why), every line you add anywhere is ASCII, and every message is plain text with no path of this computer hard-coded.

## Acceptance criteria
- [ ] `tests/test_program_install_keep.py` passes whole, unedited (58 cases).
- [ ] `tests/test_install_check.py`, `tests/test_install_check_a4.py`, `tests/test_rollback.py` and `tests/test_bug034.py` pass, every existing case unedited; any case you added sits below the marker line at the end of `tests/test_rollback.py` and names R-094 in its docstring.
- [ ] Every refused form of R1 exits 2, prints the usage naming the five options, prints no `Traceback`, and leaves the scratch computer byte-identical (the acceptance file's `snapshot`).
- [ ] A `--keep` or `--rollback` value is matched against the listing's names as a string, never as a path; each path-like, empty, differently cased or unknown value exits 2 and changes nothing (R2).
- [ ] A marked copy survives two later installs beside the one previous release; another `--keep` moves the mark; `--keep none` clears it; without `--keep` the folder holds exactly what it holds today (R3).
- [ ] `--rollback` alone restores the newest kept copy; `--rollback <version>` restores the named copy, removes the newer kept copies, and writes `ROLLED-BACK.md` with the items of every entry newer than its target and not its own (R5, R6).
- [ ] A dry run of each new form exits 0, names the version it would act on, and changes nothing (R7).
- [ ] The docstring's usage names `--keep` and `--rollback [<version>]`; the command reference is regenerated, still `"source": "docstring"` for `bridge-install.py`; `python tools/dump-cli.py --check` exits 0 (R8).
- [ ] MANIFEST is regenerated; `bridge/cursor-bridge/VERSION` is not listed by `git status --short`; `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` prints `RESULT: SOURCES MATCH`.
- [ ] `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks` passes.
- [ ] The four in-process signatures named under Context are callable as before.
- [ ] R-094 is fully met, with no stand-in, placeholder or "later" text. The tests naming R-094 are the supervisor's acceptance tests.
- [ ] No new dependency, configuration key or environment variable; the only new option is `--keep` and the only new value is `--rollback`'s version. No new Semgrep high finding. No exception escapes as a traceback (ASVS L2).

## Constraints
- Do not add dependencies (the standard library and the pytest already used only).
- Do not read or write any file outside this workspace (the folder you were started in). Everything you need is inside it, and everything you produce goes inside it.
- Do not edit `tests/test_program_install_keep.py`, any existing case of the three other test files in Scope, or anything else outside Scope. If a test case seems wrong, stop and report it by its test id instead of working around it.
- If the brief, the rules, or the tooling got in your way (an instruction that contradicted another, a check that fired wrongly, a step that cost time for no reason), append one dated line describing it to `docs/BUILDER_NOTES.md`. Do not try to fix the tooling. Do the same for anything you learned about a defect or a pitfall (a cause you found, a platform quirk that cost you a round): one dated line, so the supervisor can carry it forward.
- In any Markdown you write, never break a line inside a paragraph or a list item. One paragraph is one line. Line breaks only between blocks.
- **No owner's names, no paths.** Nothing you write (code, the notes line, the report) holds a path of this computer or a user name. In the report write `<Workspace>` for the repository folder and `<tmp>` for a temporary folder, including in quoted command output.
- This increment talks to no external service. Do not add a call to any service or the network.
- Any console process your code launches on Windows is created windowless (`creationflags=subprocess.CREATE_NO_WINDOW` in Python, `0` on other platforms; the program's `NO_WINDOW` constant, line 84). This increment needs no new process; the existing `git` and `bridge-check.py` runs keep their flags.
- Never start a server, a watcher or a daemon that outlives a test. Run every command synchronously, in the foreground, and wait for it to end. Leave nothing running when you finish.
- Do not refactor code outside the scope, even if it looks wrong. Inside `bridge-install.py`, change only what R1-R9 need; the install and rollback paths keep every message and refusal they have today.
- Never run the product, a migration, a seed or a test against the owner's live data (Context, "Development data"). Never run `bridge-install.py` yourself; only the tests run it, on their scratch targets.
- A value the brief marks as the owner's: none in this increment.
- Follow existing conventions in the file you touch: ASCII program text, `main()` returning the exit code, messages beginning `bridge-install: `, refusals that say "nothing was changed".
- These git commands are not yours to run: `commit`, `push`, `switch`, `checkout`, `merge`, `rebase`, `reset`, `stash`, `branch -d`, `worktree`. You read with `git status`, `git diff` and `git log` only. The single exception is `git restore bridge/cursor-bridge/VERSION` in the Done section.
- Numbers: none are parsed by this increment. Versions are names, compared as strings (R2); kept copies are ordered by their names as text, as `rollback()` and `rolled_back_note` already do.
- Every verification command the Done section asks you to run is written there in full. Run exactly those. **Do NOT run the whole `tests/` tree** (`python -m pytest`, `python -m pytest tests`, or any command that collects all of it): the whole suite is CI's run.
- **Mutation self-check (by hand, in process, no script in the diff).** The supervisor's mutants file sweeps the word check and the name match after your run. Before you finish, apply each of these by hand, one at a time, run `python -m pytest -p no:cacheprovider -q tests/test_program_install_keep.py`, and revert; confirm with `git diff` that each revert is exact. List each in the report by its label and text, with the pytest summary line and the id of one test it made fail. If one is not caught, write `not caught` and one line on the case that would catch it (do not add that case):
  - K1 an unknown word beginning with `-` is ignored instead of refused.
  - K2 an option given twice is accepted.
  - K3 the name match is case-insensitive.
  - K4 the name match is made by `os.path.isdir` of the value joined to `cursor-bridge-previous/` instead of against the listing's names.
  - K5 the next install ignores the marker (the one-previous rule removes the marked copy).
  - K6 `--rollback <version>` ignores the version and restores the newest kept copy.
- **Known failures.** Context says which acceptance cases pass before your change. If a case fails that your change did not cause, report it by its test id with its failure lines and fix none.
- Prefer reuse over new code: `rolled_back_note`, `save_previous`, `rollback`'s copy checks and `replace_release` as they are, the standard library. Write the minimum that meets the acceptance criteria (the frozen `minimal-code.mdc` is in force). This never overrides a security, observability or accessibility requirement stated above.
- Rules in force for you: `.cursor/rules/secure-coding.mdc`, `.cursor/rules/workspace-boundary.mdc` and the frozen `minimal-code.mdc`.

## Done
Your report is the file `handoff/TASK-073-r1-report.md`, which you write as you go: what you did, what you changed, what you ran and what it printed, and what you could not do, so that nothing of it is lost if your run ends early. It names no computer path and no user name: write `<Workspace>` for the repository folder and `<tmp>` for a temporary folder, including in quoted command output.

When you finish, it holds:
- a list of every file you changed or created;
- a one-paragraph summary of what you did;
- for R1-R9, one line each on what meets it, naming the functions and their lines as the file stands after your change; for R3 also the marker's name, when it is written and what happens to it when the install check fails; for R5 whether an older marked copy stays after `--rollback` alone; for R6 what happens to the marker when the copy it names is removed by a rollback;
- any case you added to `tests/test_rollback.py`, by test id;
- the mutation self-check list, K1-K6, each with its pytest summary line and the test id that caught it (or `not caught` and the case that would);
- every command of the list below with its output;
- a section headed exactly `Assumed, not verified`, as the report's last section.

The `Assumed, not verified` section lists every fact this change relies on that neither this brief nor the existing code settled, and that you did not confirm. Examples: how a folder under `cursor-bridge-previous/` with a name that is not a version is treated by `--keep`; whether a marker file left by an older installer is read; what the usage prints on a cp1252 console. One item per line: what you assumed - why - what would confirm it. If there are none, write `Assumed, not verified: none`. Be specific: "edge cases" or "error handling" is not an item.

Run these from the Workspace root, in this order, after your last edit, each on its own, synchronously in the foreground, with no `PYTHONPATH` or other environment change:
1. `git status --short`
2. `python tools/dump-cli.py`
3. `python tools/make-manifest.py`
4. `git restore bridge/cursor-bridge/VERSION`
5. `python -m pytest -p no:cacheprovider -q -rs tests/test_program_install_keep.py`
6. `python -m pytest -p no:cacheprovider -q -rs tests/test_install_check.py tests/test_install_check_a4.py tests/test_rollback.py tests/test_bug034.py`
7. `python tools/dump-cli.py --check` (expect exit 0)
8. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` (expect `RESULT: SOURCES MATCH`)
9. `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks`
10. `python -c "open('bridge/cursor-bridge/bridge-install.py','rb').read().decode('ascii'); print('ascii ok')"` (expect `ascii ok`)
11. `git rev-parse HEAD` and `git status --short` (`bridge/cursor-bridge/VERSION` must not be listed; if it is, report it)

Quoting rules:
- Every command you ran is quoted in the report with the lines it printed, verbatim, in a fenced block.
- Each pytest summary line is quoted verbatim in a fenced block. Never restate a count in prose.
- A claim that a check passed quotes the output line that shows it. A number of failing or skipped cases is backed by the pytest lines naming them (`-rs` prints each skip's reason).
- Each mutation is listed by its label and text, with what caught it.
- A command you did not run is written `not run`, never described as run.
- Write the report's results after step 11, naming the commit its counts belong to (`git rev-parse HEAD`) and whether the working tree then held uncommitted changes (`git status --short`).

Your last message is the summary and the report file's path, and nothing follows it. The supervisor reads only the last message, and a message printed earlier and then followed by more work is lost.
