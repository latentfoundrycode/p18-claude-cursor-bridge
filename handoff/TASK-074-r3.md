---
record: brief
header: 1
id: "TASK-074"
round: 3
satisfies: [R-093]
scope: ["bridge/cursor-bridge/bridge-check.py", "tools/make-manifest.py", "bridge/cursor-bridge/MANIFEST.json", "tests/test_install_check.py", "docs/BUILDER_NOTES.md", "handoff/TASK-074-r3-report.md"]
merge_unit: null
blocking_class: null
---
# TASK-074 round 3: the program's tree is where the program physically stands (R-093)

Round cause: brief error - both reviewers approved round 2; this round is taken for their Should fix findings, which share one cause: the program tree's formula, which round 2's brief gave as `os.path.realpath(os.path.dirname(HERE))` and which resolves the lexical parent instead of the parent of the program's resolved folder.

## Objective
Round 1 (`handoff/TASK-074.md`) made `bridge/cursor-bridge/bridge-check.py --sources` refuse, with exit 2, a check where the program does not stand in the tree it checks, and made `tools/make-manifest.py` keep `VERSION`'s line ending; round 2 (`handoff/TASK-074-r2.md`, committed at cff5974, report `handoff/TASK-074-r2-report.md`) widened the comparison to the whole `--root`, made a folder that cannot be resolved a refusal, and gave the refusal its `RESULT: REFUSED` line. Both reviewers approved round 2. Their remaining findings share one cause: the program's tree is computed as `os.path.realpath(os.path.join(HERE, os.pardir))`, which Windows resolves after collapsing the `..` (so a program reached through a link is taken for the tree it was reached from) and POSIX resolves before. This round replaces that formula with one rule, the program's tree is where the program physically stands, and carries the small findings that follow from it. **This is the last round of TASK-074 (the ceiling round): anything left after it goes to `docs/HARDENING.md` unless it is of a blocking class.** Do exactly R1-R7; nothing else.

Satisfies: R-093 - The release tooling checks the tree it stands in (C21, J5): `bridge-check.py --sources` refuses, with exit 2, where the program does not stand in the tree it checks, and prints both folders on its result line; `tools/make-manifest.py` writes `VERSION` with the file's own line ending. (Its row in `docs/REQUIREMENTS.md` is line 119.)

## Scope
Files and directories you may create or modify:
- bridge/cursor-bridge/bridge-check.py
- tools/make-manifest.py
- bridge/cursor-bridge/MANIFEST.json
- tests/test_install_check.py
- docs/BUILDER_NOTES.md
- handoff/TASK-074-r3-report.md

Limits on these paths:
- `tools/make-manifest.py`: no finding of this round touches it; leave it as round 2 left it (lines 91-100). It is in Scope only because the rounds share one Scope.
- `bridge/cursor-bridge/MANIFEST.json` changes only by running `python tools/make-manifest.py` (Done), never by hand.
- `tests/test_install_check.py`: every case above the line `# ---- builder's cases below this line` (line 296) passes **unedited**; round 2's two cases below it (`test_r093_make_manifest_keeps_a_lf_version_file_lf`, `test_r093_make_manifest_writes_a_new_version_file_with_lf`) stay as they are. No case is required this round.
- `tests/test_program_release_tooling.py` is the supervisor's acceptance file (15 cases, committed at 0d178f5). It is **read-only** for you: read it whole and run it, never edit it. If a case seems wrong, stop and report it by its test id.

Do not modify anything else.

## Out of scope
- .env and anything under secrets/
- CI configuration (`.github/`)
- docs/ and handoff/, except the files the Scope section names. `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` are the supervisor's: they are regenerated for round 2's docstring, and if this round changes the docstring again the supervisor regenerates them after your build. Do not run `python tools/dump-cli.py` without `--check`, and do not edit either file.
- `bridge/cursor-bridge/VERSION` (make-manifest rewrites it; its content must stay unchanged, Done), `bridge/cursor-bridge/CHANGELOG.md`, and every other file under `bridge/`.
- `tools/dump-cli.py` and every other file under `tools/`.
- Routed to `docs/HARDENING.md` by the supervisor; do not fix them: the extended-length spelling `\\?\<tree>` of the program's own tree given as `--root` is refused (as in rounds 1 and 2); `--root` as the last word raises `IndexError` (pre-existing, line 147); the Windows junction layout Review A noted.
- Every test file other than `tests/test_install_check.py`; `tests/test_program_release_tooling.py` included (read-only).
- Any mutation script or mutants file: the mutation run is the supervisor's, after your run.
- `~/.claude`, `~/.cursor-bridge` and any real installation: you never install anything and never run the installed `bridge-check.py`.

## Context
**The design that binds this increment.** `docs/DESIGN.md` line 363, the bullet `*C21 and J5.*`: "`bridge-check.py --sources` refuses (exit 2) where the program does not stand in the tree it checks, and prints both folders on its result line. `tools/make-manifest.py` writes `VERSION` with the file's own line ending." The plan entry is `docs/BUILD_PLAN.md`, `### TASK-074` (line 1936), its `Done when` on line 1945.

**`bridge/cursor-bridge/bridge-check.py` after round 2 (264 lines; read it whole).**
- Docstring exit list, lines 27-28, exit 2: `manifest unreadable, or under --sources the program does not stand in the tree it checks, or a folder cannot be resolved.`
- `HERE = os.path.dirname(os.path.abspath(__file__))` (line 36): the folder the program was started through, not resolved.
- `main()` (lines 141-256): `root` is `os.path.abspath(...)` of `--root` or of `HERE/..` (lines 143, 147); the manifest is read from `HERE` (lines 148-154). Round 2's comparison, lines 156-179: `here_abs = os.path.abspath(HERE)` (157, used only as a fallback), `here_tree_abs` (158), `root_abs = root` (159, an alias); `here_folder = os.path.realpath(HERE)` and `here_tree = os.path.realpath(os.path.join(HERE, os.pardir))` (162-163) and `check_tree = os.path.realpath(root)` (169), each in a `try` that catches `(OSError, ValueError)` and falls back to the unresolved spelling (164-167, 170-172); `check_cursor_bridge = os.path.join(check_tree, "cursor-bridge")` (173); `refuse = resolve_failed or os.path.normcase(here_tree) != os.path.normcase(check_tree)` (174); the refusal (176-179) prints `RESULT: REFUSED - this program stands in tree "%s" (program: "%s") but was asked to check tree "%s" (tree: "%s"); run "%s" instead.` with `here_tree, here_folder, check_tree, check_cursor_bridge, alt` and returns 2; there the label `tree:` stands before the asked-for tree's `cursor-bridge` folder.
- After an agreeing comparison: the manifest's files are hashed under the unresolved `root` (line 187), `check_settings(root)` without `--sources` (199), the EXTRA walk under `root` (229-234), the version line `bridge-check: version %s (%s) at %s` with `root` (236-237), `RESULT: SOURCES DO NOT MATCH their stamp - run tools/make-manifest.py after the last edit, then re-run. (checked: %s)` with `os.path.realpath(HERE)` (247, exit 1), `RESULT: SOURCES MATCH bridge %s %s` with the version and `os.path.realpath(HERE)` (253, exit 0).
- Keep the program free of argparse (it is recorded in the command reference from its docstring); add no option.

**The acceptance tests.** `tests/test_program_release_tooling.py`, 15 cases at 0d178f5; its module docstring (lines 1-32) states the forms it pins and what it leaves open; read it whole. On round 2's code: 4 failed, 11 passed. Helpers: `norm(text)` turns backslashes into `/` and, on Windows, lower-cases; `resolved(folder)` is `norm(os.path.realpath(folder))`; `names(text, folder)` is `resolved(folder) in norm(text)`, a substring test; `hashed_nothing(out)` is no line whose first word after leading spaces is `OK`, `STALE`, `MISSING` or `EXTRA` and no `bridge-check:` line holding `OK,`; `link_folder(target, link)` makes a junction on Windows, a symbolic link elsewhere. The round-3 cases:
- `test_r093_r3_a_program_reached_through_a_link_from_another_tree_is_refused_for_that_tree`: tree `X` holds copies of A's other folders and `X/cursor-bridge` is a link to `A/cursor-bridge`; the program is started as `X/cursor-bridge/bridge-check.py` with `--root X`. Exit 2, a `RESULT: REFUSED` line, nothing hashed. (Round 2 accepts it on Windows: the `..` is collapsed to `X` before resolving.)
- `test_r093_r3_a_program_whose_own_folder_is_a_link_into_a_tree_checks_that_tree`: `Y/cursor-bridge` is a link to `A/cursor-bridge`; the program is started as `Y/cursor-bridge/bridge-check.py` with `--root A`. Exit 0, and the last `RESULT: SOURCES MATCH` line names `A/cursor-bridge` resolved.
- `test_r093_r3_a_folder_that_raises_while_resolved_is_refused_without_a_traceback` (Windows only): `--root \\.\CON\sub` (backslash, backslash, dot, backslash, `CON`, backslash, `sub`). Exit 2, no `Traceback`, a `RESULT: REFUSED` line, nothing hashed. It passes on round 2 and is the case that now holds the `except` branch round 2's own mutant M2 showed untested.
- `test_r093_r3_a_copy_of_the_program_in_a_folder_of_another_name_is_refused`: `A/other` is a copy of `A/cursor-bridge`; the program is started as `A/other/bridge-check.py` with `--root A`. Exit 2, a `RESULT: REFUSED` line, nothing hashed.
- `test_r093_r3_a_folder_name_cannot_add_a_result_line`: `--root` is `<tmp>/no-such` followed by a newline and `RESULT: SOURCES MATCH bridge 0`. Exit 2, and exactly one line of the output begins `RESULT:`, and it begins `RESULT: REFUSED` (the test splits with `str.splitlines()`).
- The earlier 10 cases must still pass. What the earlier refusal cases look for in the output: the round-1 cases (program in `A`, `--root B`) the resolved `A/cursor-bridge` and the resolved `B/cursor-bridge`; `test_r093_r2_a_tree_whose_cursor_bridge_is_linked_into_the_program_tree_is_refused` the resolved `A/cursor-bridge` and the resolved `X`, and neither `SOURCES MATCH` nor `SOURCES DO NOT MATCH`; `test_r093_r2_the_refusal_says_it_refused_and_names_both_folders` (folders `tree A`, `tree B`, with a space) the resolved `tree A/cursor-bridge` and the resolved `tree B` on the `RESULT: REFUSED` line. The matching cases need the folder on the `RESULT: SOURCES MATCH` line (and on the `RESULT: SOURCES DO NOT MATCH` line in the EXTRA case). Since the tests compare with backslashes turned into `/`, a folder printed with doubled backslashes (as `repr` prints it) fails them on Windows.

Each case copies this repository's `bridge/` with its `MANIFEST.json`, so the cases where the program checks its own tree pass only once `MANIFEST.json` has been regenerated after your last edit of `bridge-check.py`. Run `python tools/make-manifest.py` before the pytest command (Done).

**The existing tests that hold the unchanged behaviour.** `tests/test_install_check.py` line 224 asserts `"RESULT: SOURCES MATCH bridge" in out` for the repository's own tree (nothing may come between `SOURCES MATCH` and `bridge`); line 235 asserts `"SOURCES DO NOT MATCH" in out`; the cases without `--sources` (`RESULT: INSTALLED TREE MATCHES`, lines 70 and 280) hold the installed-tree check, which does not change.

**The CI step that must still pass.** `.github/workflows/tests.yml` line 29: `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`, run from the repository root on Windows and Ubuntu, exit 0. Line 31 runs `python tools/dump-cli.py --check`: exit 0 at HEAD; if you change the docstring, it reports `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` stale until the supervisor regenerates them. Quote its output either way; do not fix it.

**External services.** None. This increment makes no external call, so there is no call time and no retry limit to record. Make no network call. The session's `claude --version` is not used by this increment.

**Trust boundaries and security context.** ASVS level 2 (`docs/INVENTORY.md`, Decisions, line 140). `.cursor/rules/secure-coding.mdc` is in force for you. Input crossing into this program: the command-line words (`--root` is any text: a device path, a path through a link, a path holding control characters), the folders and links of the tree checked, and the path the program was started through (a link may stand anywhere in it). Under `--sources` no file under a tree other than the one the program physically stands in is read or hashed, hostile input never ends in a traceback, and nothing in a folder name can forge an output line.

**Development data.** The inventory's decision (`docs/INVENTORY.md`, Decisions, line 135): "Development data: the dev build is the Workspace sources under `bridge/`; a session in the repo always runs the *installed* bridge (`~/.claude`), never the one being edited, and installs reach running projects only through the owner's install run sheet (§15 condition 1, A1a condition 1)". For you: run `bridge-check.py` only as `bridge/cursor-bridge/bridge-check.py` of this Workspace (Done) or through the tests on their copies under `tmp_path`; run `tools/make-manifest.py` of this Workspace only in the Done steps and the mutation procedure; never run the installed copy under your home folder, never run `bridge-install.py`, and never point `--root` at your home folder.

**Host.** Windows 11 with the owner's Python 3.12. CI also runs on Ubuntu.

## Diagrams
None. The plan entry names no diagram for this increment.

## Requirements
Rounds 1 and 2's requirements still hold except where a requirement below replaces them; R1 replaces round 2's comparison formula. Each finding is one requirement.

1. **R1. The program's tree is where the program physically stands** (Review A, Should fix 2, and the security audit's Should fix; `bridge/cursor-bridge/bridge-check.py:158,163`). Under `--sources`: the program's folder is `os.path.realpath(HERE)`; the program's tree is `os.path.dirname` of that resolved folder. `os.path.realpath(os.path.join(HERE, os.pardir))` and `os.path.realpath(os.path.dirname(HERE))` are not used for the tree (Windows collapses the `..` before resolving, POSIX after, so the platforms disagree; and the lexical parent of a linked folder is the wrong tree). The tree checked is `os.path.realpath(root)`; the two trees are compared under `os.path.normcase`; where they differ, refuse (exit 2, one `RESULT: REFUSED` line, R6) before any file is hashed. Cases: `test_r093_r3_a_program_reached_through_a_link_from_another_tree_is_refused_for_that_tree`, `test_r093_r3_a_program_whose_own_folder_is_a_link_into_a_tree_checks_that_tree`.
2. **R2. The program's folder is named `cursor-bridge`** (security audit, Consider, taken; `bridge/cursor-bridge/bridge-check.py:174`). Under `--sources`, where `os.path.normcase(os.path.basename(<the program's resolved folder>))` is not `os.path.normcase("cursor-bridge")`, refuse: exit 2, one `RESULT: REFUSED` line that says the program's folder is not named `cursor-bridge`, nothing hashed. Case: `test_r093_r3_a_copy_of_the_program_in_a_folder_of_another_name_is_refused`.
3. **R3. The tree checked is the resolved one** (security audit, Consider, taken; `bridge/cursor-bridge/bridge-check.py:187,229`). Under `--sources`, after the comparison agrees, the hashing of the manifest's files and the EXTRA walk run under the resolved `--root` (the tree checked), not under the spelling given. The version line (`bridge-check: version ... at <folder>`) and the RESULT lines then name the folder actually checked. The match line keeps `RESULT: SOURCES MATCH bridge <version>` first and the folder after it (`tests/test_install_check.py:224`); the do-not-match line keeps its `(checked: <folder>)` label. Without `--sources` nothing changes: `root` stays as it is read today.
4. **R4. A folder name cannot add a line** (security audit, Consider, taken; `bridge/cursor-bridge/bridge-check.py:177`). Every folder printed on a RESULT line, and on the version line under `--sources`, is printed with its control characters escaped: a newline, a carriage return and every other C0 character (U+0000 to U+001F) shown as a backslash escape (for example `\n`, `\r`, `\x1b`), and the quote character used around a folder escaped where it occurs inside the folder. Backslashes and spaces in a folder are printed as they are (doubling backslashes, as `repr` does, breaks the tests' folder match on Windows). Escaping DEL (U+007F) and the other characters `str.splitlines` breaks on (U+0085, U+2028, U+2029) as well is allowed; if you do not, name it in `Assumed, not verified`. Case: `test_r093_r3_a_folder_name_cannot_add_a_result_line`.
5. **R5. The `except` branch stays** (Review A, Should fix 1). A folder that raises `OSError` or `ValueError` while it is resolved, the program's folder or the tree asked for, is a refusal: exit 2, one `RESULT: REFUSED` line naming the unresolved spelling where resolving failed, no traceback, nothing hashed. Only those two exceptions are caught, only around the resolving; no broad `except`. Cases: `test_r093_r3_a_folder_that_raises_while_resolved_is_refused_without_a_traceback`, `test_r093_r2_a_device_name_as_root_is_refused_without_a_traceback` (both Windows only).
6. **R6. No dead aliases; each folder labelled for what it is** (Review A, Consider, taken; `bridge/cursor-bridge/bridge-check.py:157,159,177`). Drop `here_abs` and `root_abs` (aliases of values the code already holds). The refusal line labels each folder it prints for what it is: the program's folder, the program's tree, the tree asked for, and the asked-for tree's `cursor-bridge` folder labelled as that folder, not as the tree. It still begins `RESULT: REFUSED`, still says to run the asked-for tree's own `bridge-check.py` instead, keeps each folder in quotes (escaped per R4), names the folders every refusal case looks for (Context, "The acceptance tests"), and never holds `SOURCES MATCH` or `SOURCES DO NOT MATCH`. A refused run prints exactly one RESULT line.
7. **R7. The report's records** (Review A, Should fix 3 and 4). The report quotes, in fenced blocks: the exact refusal line for a folder holding spaces and for the device path, each from Done steps 5 and 6 (a run of the Workspace's program, with `<Workspace>` replacing the repository folder); each mutant's full text; and each pytest summary line, from the exact command listed for it. Its `Assumed, not verified` section names what this round relies on that no test runs (for example the POSIX behaviour of R1 on a link, which CI's Ubuntu runner exercises but your run does not).

Unchanged: no option added; no argparse; ASCII-only program text; no path of this computer hard-coded; if the docstring needs a word for R2 (a program folder not named `cursor-bridge`), one short ASCII clause in the exit-2 line is allowed and nothing else in it changes; `MANIFEST.json` regenerated after your last edit under `bridge/`, the version staying `2026.11.12a`, `git diff -- bridge/cursor-bridge/VERSION` empty.

## Acceptance criteria
- [ ] `tests/test_program_release_tooling.py` passes whole, unedited: 15 cases on Windows (on Linux the Windows-only cases are skipped).
- [ ] `tests/test_install_check.py` passes, every case unedited.
- [ ] The program's tree is `os.path.dirname(os.path.realpath(HERE))`; no `realpath` of `HERE/..` or of `dirname(HERE)` is left in the program (R1).
- [ ] A program in a folder not named `cursor-bridge` refuses under `--sources` (R2).
- [ ] Under `--sources`, hashing and the EXTRA walk run under the resolved `--root`, and the version and RESULT lines name it (R3).
- [ ] A `--root` holding a newline yields exactly one RESULT line, `RESULT: REFUSED` (R4).
- [ ] A folder that raises while resolved is refused with exit 2 and no traceback (R5).
- [ ] `here_abs` and `root_abs` are gone; the refusal labels the program's folder, the program's tree, the tree asked for and that tree's `cursor-bridge` folder each for what it is (R6).
- [ ] `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`, from the Workspace root, exits 0 and prints `RESULT: SOURCES MATCH bridge 2026.11.12a` with the folder after it.
- [ ] MANIFEST regenerated; `git status --short` does not list `bridge/cursor-bridge/VERSION`; `git diff -- bridge/cursor-bridge/VERSION` is empty.
- [ ] Both programs decode as ASCII.
- [ ] R-093 is fully met, with no stand-in, placeholder or "later" text. The tests naming R-093 are the supervisor's acceptance tests and round 2's two builder cases.
- [ ] No option added, no new dependency, configuration key or environment variable, no network call. No new Semgrep high finding. No exception escapes as a traceback (ASVS L2).

## Constraints
- Do not add dependencies (the standard library and the pytest already used only).
- Do not read or write any file outside this workspace (the folder you were started in). Everything you need is inside it, and everything you produce goes inside it.
- Do not edit `tests/test_program_release_tooling.py`, any case of `tests/test_install_check.py`, or anything else outside Scope. If a test case seems wrong, stop and report it by its test id instead of working around it.
- If the brief, the rules, or the tooling got in your way (an instruction that contradicted another, a check that fired wrongly, a step that cost time for no reason), append one dated line describing it to `docs/BUILDER_NOTES.md`. Do not try to fix the tooling. Do the same for anything you learned about a defect or a pitfall (a cause you found, a platform quirk that cost you a round): one dated line, so the supervisor can carry it forward.
- In any Markdown you write, never break a line inside a paragraph or a list item. One paragraph is one line. Line breaks only between blocks.
- **No owner's names, no paths.** Nothing you write (code, the notes line, the report) holds a path of this computer or a user name. In the report write `<Workspace>` for the repository folder and `<tmp>` for a temporary folder, including in quoted command output.
- This increment talks to no external service. Do not add a call to any service or the network.
- Any console process your code launches on Windows is created windowless (`creationflags=subprocess.CREATE_NO_WINDOW` in Python, `0` on other platforms). This increment needs no new process.
- Never start a server, a watcher or a daemon that outlives a test. Run every command synchronously, in the foreground, and wait for it to end. Leave nothing running when you finish.
- Do not fix by suppressing the symptom: no broad `except`, no `try` around `main()`; only `OSError` and `ValueError`, only around the resolving (R5).
- Do not refactor code outside the scope, even if it looks wrong. Change only what R1-R7 need; every other message, refusal and exit code stays as it is.
- Never run the product, a migration, a seed or a test against the owner's live data (Context, "Development data").
- A value the brief marks as the owner's: none in this increment.
- Follow existing conventions in the file you touch: ASCII program text, `main()` returning the exit code, messages beginning `bridge-check: `, RESULT lines beginning `RESULT: `.
- These git commands are not yours to run: `commit`, `push`, `switch`, `checkout`, `merge`, `rebase`, `reset`, `stash`, `branch -d`, `worktree`, `restore`. You read with `git status`, `git diff`, `git log` and `git rev-parse` only.
- Numbers: none are parsed by this increment.
- Every verification command the Done section asks you to run is written there in full. Run exactly those. **Do NOT run the whole `tests/` tree** (`python -m pytest`, `python -m pytest tests`, or any command that collects all of it): the whole suite is CI's run.
- **Mutation self-check (by hand, in process, no script in the diff).** The supervisor's mutation run comes after yours. Apply each mutant by hand, one at a time, to `bridge-check.py`; run `python tools/make-manifest.py` (otherwise the copied tree is STALE and every case fails for the wrong reason); run exactly `python -m pytest -p no:cacheprovider -q tests/test_program_release_tooling.py`; revert the mutant by hand; run `python tools/make-manifest.py` again; confirm with `git diff` that the revert is exact. In the report give each mutant's label and full text, the exact command, and its pytest summary line in a fenced block, with the id of one test it made fail; if it is not caught, write `not caught` and one line on why or on the case that would catch it (do not add that case):
  - M1 the program's tree computed as `os.path.realpath(os.path.join(HERE, os.pardir))` again.
  - M2 the `cursor-bridge` name check of R2 removed.
  - M3 the hashing (and the EXTRA walk) under the unresolved `root` again. If no case catches it, you may prove it by reading instead of running: write `not caught` and why (after the trees agree, the given spelling and the resolved one reach the same files, except across a change made between the comparison and the hashing).
  - M4 the escape of R4 removed.
  - M5 the `except` of R5 removed (the resolving no longer caught).
- **Known failures.** On round 2's code the acceptance file gives 4 failed, 11 passed. If a case of either test file fails that your change did not cause, report it by its test id with its failure lines and fix none.
- Prefer reuse over new code: `HERE`, the existing `root` reading, round 2's comparison block and refusal line, and the standard library (`os.path.realpath`, `os.path.dirname`, `os.path.basename`, `os.path.normcase`). Write the minimum that meets the acceptance criteria (the frozen `minimal-code.mdc` is in force). This never overrides a security, observability or accessibility requirement stated above.
- Rules in force for you: `.cursor/rules/secure-coding.mdc`, `.cursor/rules/workspace-boundary.mdc` and the frozen `minimal-code.mdc`.

## Done
Your report is the file `handoff/TASK-074-r3-report.md`, which you write as you go: what you did, what you changed, what you ran and what it printed, and what you could not do, so that nothing of it is lost if your run ends early. It names no computer path and no user name: write `<Workspace>` for the repository folder and `<tmp>` for a temporary folder, including in quoted command output.

When you finish, it holds:
- a list of every file you changed or created;
- a one-paragraph summary of what you did;
- for R1-R7, one line each on what meets it, naming the functions and their lines as the file stands after your change; for R4 which characters are escaped and how;
- the two refusal lines of R7 (Done steps 5 and 6), each in a fenced block with its command;
- the mutation self-check, M1-M5, each with its label, its full text, its command and its pytest summary line in a fenced block, and the test id that caught it (or `not caught` and why);
- every command of the list below with its output;
- a section headed exactly `Assumed, not verified`, as the report's last section.

The `Assumed, not verified` section lists every fact this change relies on that neither this brief nor the existing code settled, and that you did not confirm, and what this round relies on that no test runs. Examples: how `os.path.realpath` resolves a symbolic link to the program's folder on POSIX; whether a junction under `~/.claude` pointing into a Workspace makes the installed program check that Workspace's tree; which characters besides C0 a console or a reader splits a line on. One item per line: what you assumed - why - what would confirm it. If there are none, write `Assumed, not verified: none`. Be specific: "edge cases" or "error handling" is not an item.

Run these from the Workspace root, in this order, after your last edit, each on its own, synchronously in the foreground, with no `PYTHONPATH` or other environment change. The single quotes in steps 5 and 6 keep the words as they are in PowerShell and in bash alike; neither run reads or writes a file under the folder it names.
1. `git status --short`
2. `python tools/make-manifest.py` (expect `make-manifest: version 2026.11.12a, ...`)
3. `python -m pytest -p no:cacheprovider -q tests/test_program_release_tooling.py tests/test_install_check.py`
4. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` (expect `RESULT: SOURCES MATCH bridge 2026.11.12a` with the folder after it, exit 0)
5. `python bridge/cursor-bridge/bridge-check.py --root 'no such/tree B' --sources --quiet` (expect exit 2 and one `RESULT: REFUSED` line naming a folder that holds `tree B`)
6. `python bridge/cursor-bridge/bridge-check.py --root '\\.\CON\sub' --sources --quiet` (Windows; expect exit 2, one `RESULT: REFUSED` line, no `Traceback`)
7. `python tools/dump-cli.py --check` (exit 0 if the docstring is unchanged; if you changed it, expect `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` reported stale; quote its output and fix nothing; the supervisor regenerates both)
8. `python -c "[open(p,'rb').read().decode('ascii') for p in ('bridge/cursor-bridge/bridge-check.py','tools/make-manifest.py')]; print('ascii ok')"` (expect `ascii ok`)
9. `git diff -- bridge/cursor-bridge/VERSION` (expect no output)
10. `git rev-parse HEAD` and `git status --short` (`bridge/cursor-bridge/VERSION` must not be listed; if it is, report it and do not restore it)

Quoting rules:
- Every command you ran is quoted in the report with the lines it printed, verbatim, in a fenced block.
- Each pytest summary line is quoted verbatim in a fenced block, from the exact command listed for it. Never restate a count in prose.
- A claim that a check passed quotes the output line that shows it.
- Each mutation is listed by its label and its full text, with what caught it.
- A command you did not run is written `not run`, never described as run.
- Write the report's results after step 10, naming the commit its counts belong to (`git rev-parse HEAD`) and whether the working tree then held uncommitted changes (`git status --short`).

Your last message is the summary and the report file's path, and nothing follows it. The supervisor reads only the last message, and a message printed earlier and then followed by more work is lost.
