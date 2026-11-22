---
record: brief
header: 1
id: "TASK-073"
round: 2
satisfies: [R-094]
scope: ["bridge/cursor-bridge/bridge-install.py", "bridge/cursor-bridge/MANIFEST.json", "docs/cli-reference.json", "docs/CLI_REFERENCE.md", "tests/test_program_install_keep.py", "tests/test_install_check.py", "tests/test_install_check_a4.py", "tests/test_rollback.py", "docs/BUILDER_NOTES.md", "handoff/TASK-073-r2-report.md"]
merge_unit: null
blocking_class: null
---
# TASK-073 round 2: The installer refuses unknown words and keeps a named copy (R-094)

Round cause: correctness - bridge/cursor-bridge/bridge-install.py:485 save_previous with install 776-778, `--keep <version>` at the install of a new version removes the named copy (B1); security - bridge-install.py:390 read_keep_marker stops on a marker that is not text, :367 kept_release_names hides kept copies of versions with no letter, :485 the rotation leaves stale `.partial` folders, :856-869 the name checks list the folder outside the try (S1 to S4); test that does not test - tests/test_rollback.py:456 (S5); report - round 1's `Assumed, not verified` item 2 false and K2-K6 quoted from single-test runs (S6)

## Objective
This is round 2 of TASK-073. Round 1's code is committed on branch `task-073` (commit `d1bcb78`, "TASK-073: round 1, the installer's word check and --keep (R-094)"; `git log -3` shows it) and its report is `handoff/TASK-073-r1-report.md`. Round 1 made `main()` read every word through `parse_argv()` (bridge-install.py 422-471) and refuse unknown words with the usage and exit 2; added `--keep <version>|none` with a `.keep` marker file (`KEEP_MARKER`, line 89) written by `write_keep_marker()` (401-412) after a passing install check (`install()` 776-778), read by `read_keep_marker()` (390-398) and honoured by `save_previous()` (474-503); added `--rollback <version>` to `rollback()` (782-843); and filtered the kept copies by `KEPT_NAME` (line 91, `^\d{4}\.\d{2}\.\d{2}[a-z]$`) in `kept_release_names()` (367-374). Review A and the security audit rejected it. Your work is the minimum change to round 1's code that fixes B1 and S1 to S6 below, makes every case of `tests/test_program_install_keep.py` pass, and keeps every existing test green. Round 1's brief, `handoff/TASK-073.md`, stays in force for everything this brief does not change: read its Context (the design, the installer as it stood, the in-process signatures, the command reference, the existing tests, trust boundaries at ASVS level 2, development data) and its Requirements R1 to R9, which must stay met.

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
- handoff/TASK-073-r2-report.md

Limits on these paths:
- `tests/test_program_install_keep.py`: the supervisor's acceptance tests, now 64 cases: round 1's 58 and six round-2 cases added by the supervisor at the end of the file, below the line `# ---------------------------------------------------------------- round 2` (the helpers `marker_files`, `spoil_markers`, `NOT_TEXT` and the six cases whose names begin `test_r2_`). Read the round-2 part whole and run the whole file. **Do not edit it.** If a case seems wrong, stop and report it by its test id.
- `tests/test_install_check.py`, `tests/test_install_check_a4.py`, `tests/test_rollback.py`: every existing case must pass **unedited**. In `tests/test_rollback.py` only the part below your marker line `# ---- builder's cases below this line` (line 453) may change: your case `test_r094_keep_with_rollback_is_refused` gains the assertions of S5, and you may add cases there. Nothing above that line changes. The other two files are not edited at all.
- `bridge/cursor-bridge/MANIFEST.json` changes only by running `python tools/make-manifest.py` (Done), never by hand. `bridge/cursor-bridge/VERSION` is outside Scope; `make-manifest.py` rewrites its line endings, so restore it with `git restore bridge/cursor-bridge/VERSION` right after (Done).
- `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` change only by running `python tools/dump-cli.py` (Done), never by hand.

Do not modify anything else.

## Out of scope
- .env and anything under secrets/
- CI configuration
- docs/ and handoff/, except the files the Scope section names. Every other record under docs/ is the supervisor's; `handoff/TASK-073-r1-report.md` is round 1's and stays as it is.
- Every other program under `bridge/cursor-bridge/` (`bridge-check.py` included), the texts under `bridge/commands/`, `bridge/agents/`, `bridge/skills/` and `bridge/cursor-bridge/workflow/`, and `bridge/cursor-bridge/CHANGELOG.md` (no CHANGELOG entry in this increment).
- `tools/make-manifest.py` and `tools/dump-cli.py`: you run them and edit neither.
- Every test file other than the four in Scope. A failure in one is reported by its test id, never fixed there.
- `run/` (the supervisor's): read only.
- Any mutation script or mutants file. The mutants file and the mutation run are the supervisor's, after your run.
- `~/.claude`, `~/.cursor-bridge` and any real installation: you never install anything (Constraints).

## Context
**The round-2 acceptance cases** (`tests/test_program_install_keep.py`, below the round-2 line) and what each pins: `test_r2_keep_given_with_the_install_of_a_new_version_keeps_the_named_copy` (B1); `test_r2_a_marker_that_is_not_text_never_stops_an_install`, `test_r2_a_marker_that_is_not_text_never_stops_a_rollback`, `test_r2_a_marker_saved_with_a_byte_order_mark_still_keeps_its_copy` (S1); `test_r2_a_kept_copy_of_a_version_with_no_letter_is_still_rolled_back_to` (S2); `test_r2_an_interrupted_copy_is_cleared_when_the_copies_rotate` (S3). The supervisor's red run of these six cases on round 1's code is done: 6 failed, 58 deselected, each case failing on its own assertion. Round 1's 58 cases pass on round 1's code (round 1's report, step 5). After round 2 all 64 pass. S4, S5, S6, the dry-run line of B1 and K7 have no acceptance case.

**Where round 1 went wrong (read the code at these lines; they are commit `d1bcb78`'s).**
- B1: `install()` calls `save_previous(target, old_version, old_files, dry)` at line 765, and `save_previous` reads the stored marker at line 485 (`marked = read_keep_marker(base)`) and removes every other folder (486-492). This run's `--keep` value reaches `write_keep_marker` only at 777-778, after `run_check`. So `--keep A` given with the install of a new version C rotates the copies by the old marker (none) and removes A. The dry-run line at 745-751 ("would keep %s") says A would be kept, which the real run does not do.
- S1: `read_keep_marker` (390-398) opens the marker with `encoding="utf-8"` and catches only `OSError`. Bytes that are not UTF-8 raise `UnicodeDecodeError`, a `ValueError`: `main()` (874) turns it into the "stopped" exit 2, so every later install stops; in `rollback()` the read at 834 comes after the restored and newer copies were removed (831-833). A marker re-saved by a Windows editor with a UTF-8 byte order mark reads as U+FEFF followed by the name, which matches no folder.
- S2: `kept_release_names` keeps only names matching `KEPT_NAME` (letter required), and `rollback()` (788), the `--keep` check (860) and the `--rollback <version>` check (866) all use it. The bridge's own `CHANGELOG.md` has versions with no letter (2026.09.20 to 2026.09.27); before this increment `rollback()` listed every folder under `cursor-bridge-previous/` not ending `.partial` and restored such a copy. `KEPT_NAME.match` with `$` also accepts a name ending in a newline.
- S3: before this increment `save_previous` removed the whole `cursor-bridge-previous/` folder (`shutil.rmtree(base, ignore_errors=True)`) before writing the new copy, so a stale `<version>.partial` folder or a stray entry left there went with it. Round 1's loop (487-492) skips every `.partial` name and removes only folders, so these now stay forever.
- S4: in `main()` the `--keep` and `--rollback <version>` name checks (856-869) call `kept_release_names`, which calls `os.listdir`, outside the `try` at 870-877 that turns `OSError` into the "stopped, because a file could not be read or written" line and exit 2. A `cursor-bridge-previous/` that cannot be listed gives a traceback.
- S5: `tests/test_rollback.py:456-461`, `test_r094_keep_with_rollback_is_refused`, asserts the exit code and the message only, never that nothing changed. The module's helpers: `version_of(target)` (line 112), `NEW_VERSION` (22), `OLD_VERSION` (23), the fixture `installed_old_then_new` (93-101), which leaves NEW_VERSION installed and OLD_VERSION kept under `cursor-bridge-previous/`.
- S6: round 1's report, `Assumed, not verified` item 2, says non-version folders "are not removed by `save_previous()` unless they are version-shaped directories"; the code at 487-492 removes every folder not marked, version-shaped or not. Its K2 to K6 lines quote single-test runs (`1 failed in ...`), not the full-file command the brief named.

**Development data.** The inventory's decision (`docs/INVENTORY.md`, Decisions, line 135): "Development data: the dev build is the Workspace sources under `bridge/`; a session in the repo always runs the *installed* bridge (`~/.claude`), never the one being edited, and installs reach running projects only through the owner's install run sheet". For you: the installer runs only through the tests, on their scratch targets under `tmp_path`. Never run `bridge-install.py` yourself; with no `--target` it installs into the home folder's `.claude`.

**Security context.** ASVS level 2 (`docs/INVENTORY.md`, Decisions, line 140). `.cursor/rules/secure-coding.mdc` is in force for you. The marker's bytes and the names under `cursor-bridge-previous/` are input from the disk, editable by hand: neither may make the installer fail, remove more than the one-previous rule would, or escape as a traceback.

## Diagrams
None. The plan entry names no diagram for this increment.

## Requirements
1. **B1. This run's `--keep` decides the rotation.** When this run is given `--keep`, the copies rotate by its value: `--keep <version>` spares the named copy, `--keep none` spares no marked copy (the one-previous rule alone). Without `--keep` they rotate by the stored marker, as round 1 does. After a passing install check the marker reflects this run's `--keep` (names the copy, or is gone for `none`); without `--keep` it is left as it was. The report says what a failed install check (exit 1) leaves: which copies are there and what the marker names. The dry run of `--keep <version>` and of `--keep none` says truthfully what the real run would keep (the named copy, or no marked copy), and still changes nothing. In-process callers keep `install(target, dry, anyway=False, keep=None)` and the other signatures round 1's brief names.
2. **S1. A marker that cannot be read never stops anything.** Reading the marker never raises out of `read_keep_marker` (or whatever reads it): bytes that are not text, or any other read failure, count as no readable mark. No install and no rollback fails, stops or prints a traceback because of the marker, and the treatment of an unreadable mark never removes more than the one-previous rule would; which treatment you chose (for example: as no mark, or sparing the copies), state in the report. A marker saved with a UTF-8 byte order mark still names its copy (read it with `utf-8-sig`).
3. **S2. The listing is every folder not ending `.partial`.** The kept copies that `rollback()`, the `--keep` check and the `--rollback <version>` check see are every folder directly under `<target>/cursor-bridge-previous/` whose name does not end `.partial`, as `rollback()` listed them before this increment; the marker is a file, so it is not listed. No version-shape filter on that listing. If a name pattern is still used anywhere in the file, it is matched with `re.fullmatch`, never with `^...$` and `match`. The values are still compared with the listing's names exactly, as strings (round 1's R2).
4. **S3. The rotation clears what the one-previous rule cleared.** When the copies rotate, every entry under `cursor-bridge-previous/` (folders, `.partial` folders, files) is removed except the marker file and the copy kept by the mark (B1 decides which). A stale `<version>.partial` of the version being saved now is removed too: the rotation runs before this run writes its own `.partial`, so a leftover from an interrupted run never mixes its files into the new copy (as the whole-folder removal before this increment guaranteed). With no `--keep` ever given and no marker, the folder ends as it ended before this increment.
5. **S4. No traceback from the name checks.** A `cursor-bridge-previous/` that cannot be listed when `main()` checks a `--keep` or `--rollback` value gives the existing "bridge-install: stopped, because a file could not be read or written: ..." line and exit 2, never a traceback. The message text stays as it is.
6. **S5. The builder's case checks that nothing changed.** `test_r094_keep_with_rollback_is_refused` in `tests/test_rollback.py` (below the marker line) also asserts, after the refused run: `version_of(target) == NEW_VERSION`, the folder `cursor-bridge-previous/<OLD_VERSION>` still there, and no `cursor-bridge/ROLLED-BACK.md`. Its docstring still names R-094.
7. **S6. The report is true.** Every item of `Assumed, not verified` is true of the code as it stands after your change (check each against the code before writing it). The mutation self-check quotes, for each mutation, the summary line of the full-file command the Constraints name, never a run of one test (`-k`, `::` or a node id).
8. **Optional, not required:** a real (not dry) `--keep` run prints one line saying which copy is now kept (or that none is), in the program's `  keep           ...` style.
9. Round 1's R1 to R9 stay met: no new option, `bridge-install.py` ASCII-only, still recorded from its docstring (no top-level `build_parser()`, no `ArgumentParser` text), every install and rollback message and refusal of today unchanged except as B1 to S4 need.

## Acceptance criteria
- [ ] `tests/test_program_install_keep.py` passes whole, unedited (64 cases), the six `test_r2_` cases among them.
- [ ] `tests/test_install_check.py`, `tests/test_install_check_a4.py`, `tests/test_rollback.py` and `tests/test_bug034.py` pass, every existing case unedited; `test_r094_keep_with_rollback_is_refused` asserts the installed version, the kept OLD_VERSION folder and the absence of `ROLLED-BACK.md` (S5).
- [ ] `--keep <version>` given with the install of a new version keeps the named copy beside the one previous release; the marker names it after a passing check; the dry run says the same (B1).
- [ ] A marker that is not text, or with a byte order mark, never stops an install or a rollback; a byte-order-marked marker still keeps its copy; the report names the treatment chosen (S1).
- [ ] A kept copy whose version has no letter is listed, restored by `--rollback`, and accepted by `--keep` and `--rollback <version>`; no `^...$` pattern with `match` remains (S2).
- [ ] A stale `.partial` folder or stray entry under `cursor-bridge-previous/` is removed when the copies rotate; the marker and the marked copy stay, and the new copy holds only the files this run saved (S3).
- [ ] A `cursor-bridge-previous/` that cannot be listed during the name checks gives the stopped line and exit 2, no traceback (S4).
- [ ] The report's `Assumed, not verified` is true of the code, and each mutation K1 to K7 quotes the full-file summary line (S6).
- [ ] The docstring and command reference stay as round 1's R8 requires; `python tools/dump-cli.py --check` exits 0; MANIFEST regenerated; `bridge/cursor-bridge/VERSION` not listed by `git status --short`; `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` prints `RESULT: SOURCES MATCH`; `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks` passes.
- [ ] R-094 is fully met, with no stand-in, placeholder or "later" text. The tests naming R-094 are the supervisor's acceptance tests and your case in `tests/test_rollback.py`.
- [ ] No new dependency, configuration key, environment variable or option. No new Semgrep high finding. No exception escapes as a traceback (ASVS L2).

## Constraints
- Do not add dependencies (the standard library and the pytest already used only).
- Do not read or write any file outside this workspace (the folder you were started in). Everything you need is inside it, and everything you produce goes inside it.
- Do not edit `tests/test_program_install_keep.py`, any existing case of the three other test files in Scope, or anything else outside Scope. If a test case seems wrong, stop and report it by its test id instead of working around it.
- If the brief, the rules, or the tooling got in your way (an instruction that contradicted another, a check that fired wrongly, a step that cost time for no reason), append one dated line describing it to `docs/BUILDER_NOTES.md`. Do not try to fix the tooling. Do the same for anything you learned about a defect or a pitfall (a cause you found, a platform quirk that cost you a round): one dated line, so the supervisor can carry it forward.
- In any Markdown you write, never break a line inside a paragraph or a list item. One paragraph is one line. Line breaks only between blocks.
- **No owner's names, no paths.** Nothing you write (code, the notes line, the report) holds a path of this computer or a user name. In the report write `<Workspace>` for the repository folder and `<tmp>` for a temporary folder, including in quoted command output.
- This increment talks to no external service. Do not add a call to any service or the network.
- Any console process your code launches on Windows is created windowless (`creationflags=subprocess.CREATE_NO_WINDOW` in Python, `0` on other platforms; the program's `NO_WINDOW` constant). This round needs no new process; the existing `git` and `bridge-check.py` runs keep their flags.
- Never start a server, a watcher or a daemon that outlives a test. Run every command synchronously, in the foreground, and wait for it to end. Leave nothing running when you finish.
- Do not refactor code outside the scope, even if it looks wrong. Inside `bridge-install.py`, change only what B1 to S4 (and the optional item 8) need.
- Never run the product, a migration, a seed or a test against the owner's live data (Context, "Development data"). Never run `bridge-install.py` yourself; only the tests run it, on their scratch targets.
- A value the brief marks as the owner's: none in this increment.
- Follow existing conventions in the file you touch: ASCII program text, `main()` returning the exit code, messages beginning `bridge-install: `, refusals that say "nothing was changed".
- These git commands are not yours to run: `commit`, `push`, `switch`, `checkout`, `merge`, `rebase`, `reset`, `stash`, `branch -d`, `worktree`. You read with `git status`, `git diff` and `git log` only. The single exception is `git restore bridge/cursor-bridge/VERSION` in the Done section.
- Numbers: none are parsed by this increment. Versions are names, compared as strings; kept copies are ordered by their names as text, as `rollback()` and `rolled_back_note` already do.
- Every verification command the Done section asks you to run is written there in full. Run exactly those. **Do NOT run the whole `tests/` tree** (`python -m pytest`, `python -m pytest tests`, or any command that collects all of it): the whole suite is CI's run.
- **Mutation self-check (by hand, in process, no script in the diff).** The supervisor's mutants file sweeps the word check, the name match and the rotation after your run. Before you finish, apply each of these by hand, one at a time, run the full-file command `python -m pytest -p no:cacheprovider -q tests/test_program_install_keep.py` (the whole file, never one test), and revert; confirm with `git diff` that each revert is exact. List each in the report by its label and text, with that command's pytest summary line, verbatim, and the id of one test it made fail. If one is not caught, write `not caught` and one line on the case that would catch it (do not add that case):
  - K1 an unknown word beginning with `-` is ignored instead of refused.
  - K2 an option given twice is accepted.
  - K3 the name match is case-insensitive.
  - K4 the name match is made by `os.path.isdir` of the value joined to `cursor-bridge-previous/` instead of against the listing's names.
  - K5 the next install ignores the marker (the one-previous rule removes the marked copy).
  - K6 `--rollback <version>` ignores the version and restores the newest kept copy.
  - K7 `save_previous` ignores this run's `--keep` value (uses only the stored marker).
- **Known failures.** If a case fails that your change did not cause, report it by its test id with its failure lines and fix none.
- Prefer reuse over new code: the existing functions as they are, the standard library. Write the minimum that meets the acceptance criteria (the frozen `minimal-code.mdc` is in force). This never overrides a security, observability or accessibility requirement stated above.
- Rules in force for you: `.cursor/rules/secure-coding.mdc`, `.cursor/rules/workspace-boundary.mdc` and the frozen `minimal-code.mdc`.

## Done
Your report is the file `handoff/TASK-073-r2-report.md`, which you write as you go: what you did, what you changed, what you ran and what it printed, and what you could not do, so that nothing of it is lost if your run ends early. It names no computer path and no user name: write `<Workspace>` for the repository folder and `<tmp>` for a temporary folder, including in quoted command output.

When you finish, it holds:
- a list of every file you changed or created in this round;
- a one-paragraph summary of what you did;
- for B1 and S1 to S5, one line each on what meets it, naming the functions and their lines as the file stands after your change; for B1 also what a failed install check (exit 1) leaves (the copies and what the marker names); for S1 the treatment of an unreadable marker you chose;
- whether you did the optional item 8;
- the mutation self-check list, K1 to K7, each with the full-file command's pytest summary line and the test id that caught it (or `not caught` and the case that would);
- every command of the list below with its output;
- a section headed exactly `Assumed, not verified`, as the report's last section.

The `Assumed, not verified` section lists every fact this change relies on that neither this brief nor the existing code settled, and that you did not confirm, and each item is true of the code as it stands (S6). One item per line: what you assumed - why - what would confirm it. If there are none, write `Assumed, not verified: none`. Be specific: "edge cases" or "error handling" is not an item.

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
