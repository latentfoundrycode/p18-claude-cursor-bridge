---
record: brief
header: 1
id: "TASK-073"
round: 3
satisfies: [R-094]
scope: ["bridge/cursor-bridge/bridge-install.py", "bridge/cursor-bridge/MANIFEST.json", "docs/cli-reference.json", "docs/CLI_REFERENCE.md", "tests/test_program_install_keep.py", "tests/test_install_check.py", "tests/test_install_check_a4.py", "tests/test_rollback.py", "docs/BUILDER_NOTES.md", "handoff/TASK-073-r3-report.md"]
merge_unit: null
blocking_class: null
---
# TASK-073 round 3: The installer refuses unknown words and keeps a named copy (R-094)

Round cause: security - bridge/cursor-bridge/bridge-install.py:472-508 save_previous follows a `cursor-bridge-previous` that is a link and removes the linked folder's contents (S-1), and a stray entry that cannot be removed stops the install (S-2); :366-372 kept_release_names can list the marker's name (C-5); :388-396 read_keep_marker reads without a bound (C-4); correctness - :770-788 install leaves the marker naming a removed copy after a failed install check, and :491 the rotation spares a stray file named like the version being saved (Review A); report - the quoted `git status --short` not the final tree's, line references off, `git checkout` used to revert mutations

## Objective
This is round 3 of TASK-073, the last round under the ceiling. Round 2's code is committed on branch `task-073` (commit `8dc7c44`, "TASK-073: round 2, this run's --keep decides the rotation (R-094)"; `git log -4` shows it) and its report is `handoff/TASK-073-r2-report.md`. Review A and the security audit approved round 2, each with Should-fix items; your work is the minimum change to round 2's code that fixes F1 to F7 below, makes every case of `tests/test_program_install_keep.py` pass, and keeps every existing test green. Round 1's brief `handoff/TASK-073.md` (its Context and Requirements R1 to R9) and round 2's brief `handoff/TASK-073-r2.md` (its Context and Requirements 1 to 9: B1, S1 to S6) stay in force for everything this brief does not change; read both.

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
- handoff/TASK-073-r3-report.md

Limits on these paths:
- `tests/test_program_install_keep.py`: the supervisor's acceptance tests, now 67 cases: round 1's 58, round 2's six `test_r2_` cases, and three round-3 cases added by the supervisor at the end of the file, below the line `# ---------------------------------------------------------------- round 3` (the helpers `link_dir`, `unlink_dir` and the three cases whose names begin `test_r3_`). Read the round-3 part whole and run the whole file. **Do not edit it.** If a case seems wrong, stop and report it by its test id.
- `tests/test_install_check.py`, `tests/test_install_check_a4.py`, `tests/test_rollback.py`: every existing case must pass **unedited**. In `tests/test_rollback.py` only the part below the marker line `# ---- builder's cases below this line` (line 453) may change: you add the F3 case there. Nothing above that line changes. The other two files are not edited at all.
- `bridge/cursor-bridge/MANIFEST.json` changes only by running `python tools/make-manifest.py` (Done), never by hand. `bridge/cursor-bridge/VERSION` is outside Scope; `make-manifest.py` rewrites its line endings, so restore it with `git restore bridge/cursor-bridge/VERSION` right after (Done).
- `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` change only by running `python tools/dump-cli.py` (Done), never by hand.

Do not modify anything else.

## Out of scope
- .env and anything under secrets/
- CI configuration
- docs/ and handoff/, except the files the Scope section names. `handoff/TASK-073-r1-report.md` and `handoff/TASK-073-r2-report.md` stay as they are.
- Every other program under `bridge/cursor-bridge/` (`bridge-check.py` included), the texts under `bridge/commands/`, `bridge/agents/`, `bridge/skills/` and `bridge/cursor-bridge/workflow/`, and `bridge/cursor-bridge/CHANGELOG.md` (no CHANGELOG entry in this increment).
- `tools/make-manifest.py` and `tools/dump-cli.py`: you run them and edit neither.
- Every test file other than the four in Scope. A failure in one is reported by its test id, never fixed there.
- `run/` (the supervisor's): read only.
- Any mutation script or mutants file.
- `~/.claude`, `~/.cursor-bridge` and any real installation: you never install anything.

## Context
**The code to change** (round 2's, commit `8dc7c44`, in `bridge/cursor-bridge/bridge-install.py`): `kept_release_names(target)` 366-372; `read_keep_marker(base)` 388-396; `write_keep_marker(base, version, dry)` 399-410; `save_previous(target, version, files, dry, keep=None)` 472-508, whose rotation loop is 487-497 (the `n == marked or n == version` skip at 491, `os.remove(p)` with no error handling at 497); `install()` calls it at 770 and writes the marker only after a passing `run_check` at 781-788; `rollback()` 792-853 removes the restored and newer kept copies at 841-843. `PREVIOUS = "cursor-bridge-previous"` (88), `KEEP_MARKER = ".keep"` (89). The module does not import `stat` yet; it is the standard library.

**The round-3 acceptance cases** (below the round-3 line) and what each pins: `test_r3_a_linked_previous_folder_never_has_its_other_contents_removed` (F1; on Windows it makes `cursor-bridge-previous` a junction with `_winapi.CreateJunction`, elsewhere a symbolic link, and removes the link itself in a `finally`); `test_r3_a_stray_file_that_cannot_be_removed_never_stops_an_install` (F2; a read-only stray file); `test_r3_a_stray_file_named_like_the_version_being_saved_never_stops_an_install` (F4). The three `test_r3_` cases are expected to fail on round 2's code (the supervisor's red run confirms it); after round 3 all 67 cases pass. F3, F5, F6 have no acceptance case in that file; F3 gets your case in `tests/test_rollback.py`.

**Development data.** The inventory's decision (`docs/INVENTORY.md`, Decisions, line 135): "Development data: the dev build is the Workspace sources under `bridge/`; a session in the repo always runs the *installed* bridge (`~/.claude`), never the one being edited, and installs reach running projects only through the owner's install run sheet". For you: the installer runs only through the tests, on their scratch targets under `tmp_path`. Never run `bridge-install.py` yourself; with no `--target` it installs into the home folder's `.claude`.

**Security context.** ASVS level 2 (`docs/INVENTORY.md`, Decisions, line 140). `.cursor/rules/secure-coding.mdc` is in force for you. `cursor-bridge-previous/`, every name under it and the marker's bytes are input from the disk, editable by hand: none may make the installer fail, remove anything outside the kept copies, remove more than the one-previous rule would, or escape as a traceback.

## Diagrams
None. The plan entry names no diagram for this increment.

## Requirements
1. **F1. A linked `cursor-bridge-previous` is never rotated through.** Before the rotation lists or removes anything, `save_previous` checks `os.lstat(base)`: a link is `stat.S_ISLNK(st.st_mode)`, or the `FILE_ATTRIBUTE_REPARSE_POINT` bit set in `getattr(st, "st_file_attributes", 0)` (the constant is in the standard `stat` module on every platform). When `base` is a link, nothing is removed through it. Whether the install then goes on without a rotation or stops with exit 2 and a line that says nothing was changed is your choice; state it in the report. The same check runs in `rollback()` before it removes the restored and newer kept copies: when `base` is a link, it removes nothing through it.
2. **F2. A stray entry that cannot be removed never stops an install.** In the rotation, each file removal ignores `OSError`, as the folders' `shutil.rmtree(..., ignore_errors=True)` does. An entry that is neither a file nor a folder (a broken link) is removed as a link where it can be, and its removal error is ignored. No entry is followed through a link.
3. **F3. The marker follows the rotation.** Whenever `save_previous` removes the copy the stored marker names, or this run's `--keep` spares another copy, the marker is rewritten at once: to the copy the rotation spared, or removed for `--keep none` or when no marked copy was spared. So after a failed install check (exit 1) the marker names the copy this run spared, never a copy that is gone, and the next install keeps it. After a passing check the marker still reflects this run's `--keep` (round 2's B1); without `--keep` and with nothing removed it is left as it was. A dry run still changes nothing. The report states what a failed install check leaves (the copies and what the marker names).
4. **F3 case.** Add one in-process case to `tests/test_rollback.py`, below the marker line, that patches `run_check` to return 1 (as `test_the_kept_copy_stays_when_the_check_after_a_rollback_does_not_pass` does at lines 279-290, with `load_installer(RELEASE)` and `monkeypatch`), calls `install(target, dry, anyway=..., keep=...)` so that the rotation spares a copy, and asserts that the marker then names the spared copy and that the next install keeps it. Its docstring names R-094. How the case builds the kept copies it needs is yours.
5. **F4. The version's name spares nothing.** The rotation never spares an entry only because it is named like the version being saved: the `n == version` skip is gone (a folder of that name already returns early at line 481), so a stray file of that name is removed like any stray entry and the new copy takes its place. If such an entry cannot be removed, the install never ends in a traceback; state in the report what it does then.
6. **F5. The marker's name is never a kept copy.** `kept_release_names` leaves out `KEEP_MARKER`, so a folder named like the marker is neither listed nor accepted by `--keep` or `--rollback <version>`.
7. **F6. The marker read is bounded.** `read_keep_marker` reads at most a few hundred bytes, so a huge marker never raises `MemoryError`; round 2's S1 treatment (`utf-8-sig`, any read failure counts as no readable mark) stays.
8. **F7. The report is the final tree's.** The `git status --short` the Done section quotes is run after your last edit and quoted verbatim; every line reference in the report is right for the file as it stands after your change. Mutations are reverted by editing back, or from a saved copy (see Constraints), never with `git checkout`; the report says how each was reverted.
9. Round 1's R1 to R9 and round 2's requirements 1 to 7 stay met: no new option, `bridge-install.py` ASCII-only, still recorded from its docstring, every install and rollback message and refusal unchanged except as F1 to F5 need.

## Acceptance criteria
- [ ] `tests/test_program_install_keep.py` passes whole, unedited (67 cases), the three `test_r3_` cases among them.
- [ ] `tests/test_install_check.py`, `tests/test_install_check_a4.py`, `tests/test_rollback.py` and `tests/test_bug034.py` pass, every existing case unedited; the new F3 case in `tests/test_rollback.py` passes and its docstring names R-094.
- [ ] A linked `cursor-bridge-previous` has nothing removed through it by an install or a rollback; the report names the behaviour chosen (F1).
- [ ] A read-only or otherwise unremovable stray entry, or a broken link, under `cursor-bridge-previous/` never stops an install; no link is followed (F2).
- [ ] After a failed install check the marker names the copy the rotation spared, or is absent, never a removed copy; the next install keeps it (F3).
- [ ] A stray file named like the version being saved is removed and the new copy takes its place (F4).
- [ ] `KEEP_MARKER` is never a listed kept copy (F5); the marker read is bounded (F6).
- [ ] The report's `git status --short`, line references and mutation reverts are as F7 requires; its `Assumed, not verified` is true of the code.
- [ ] `python tools/dump-cli.py --check` exits 0; MANIFEST regenerated; `bridge/cursor-bridge/VERSION` not listed by `git status --short`; `bridge-check.py --root bridge --sources --quiet` prints `RESULT: SOURCES MATCH`; `windowless-check.py` passes.
- [ ] R-094 is fully met, with no stand-in, placeholder or "later" text; the tests naming R-094 are the supervisor's acceptance tests and your cases in `tests/test_rollback.py`.
- [ ] No new dependency, configuration key, environment variable or option. No new Semgrep high finding. No exception escapes as a traceback (ASVS L2).

## Constraints
- Do not add dependencies (the standard library and the pytest already used only).
- Do not read or write any file outside this workspace (the folder you were started in). Everything you need is inside it, and everything you produce goes inside it.
- Do not edit `tests/test_program_install_keep.py`, any existing case of the three other test files in Scope, or anything else outside Scope. If a test case seems wrong, stop and report it by its test id instead of working around it.
- If the brief, the rules, or the tooling got in your way (an instruction that contradicted another, a check that fired wrongly, a step that cost time for no reason), append one dated line describing it to `docs/BUILDER_NOTES.md`. Do not try to fix the tooling. Do the same for anything you learned about a defect or a pitfall (a cause you found, a platform quirk that cost you a round): one dated line, so the supervisor can carry it forward.
- In any Markdown you write, never break a line inside a paragraph or a list item. One paragraph is one line. Line breaks only between blocks.
- **No owner's names, no paths.** Nothing you write (code, the notes line, the report) holds a path of this computer or a user name. In the report write `<Workspace>` for the repository folder and `<tmp>` for a temporary folder, including in quoted command output.
- This increment talks to no external service. Do not add a call to any service or the network.
- Any console process your code launches on Windows is created windowless (the program's `NO_WINDOW` constant). This round needs no new process.
- Never start a server, a watcher or a daemon that outlives a test. Run every command synchronously, in the foreground, and wait for it to end. Leave nothing running when you finish.
- Do not refactor code outside the scope, even if it looks wrong. Inside `bridge-install.py`, change only what F1 to F6 need.
- Never run the product, a migration, a seed or a test against the owner's live data (Context, "Development data"). Never run `bridge-install.py` yourself; only the tests run it, on their scratch targets.
- A value the brief marks as the owner's: none in this increment.
- Follow existing conventions in the file you touch: ASCII program text, `main()` returning the exit code, messages beginning `bridge-install: `, refusals that say "nothing was changed".
- These git commands are not yours to run: `commit`, `push`, `switch`, `checkout`, `merge`, `rebase`, `reset`, `stash`, `branch -d`, `worktree`. You read with `git status`, `git diff` and `git log` only. The single exception is `git restore bridge/cursor-bridge/VERSION` in the Done section.
- Numbers: none are parsed by this increment except the marker read's byte bound, a constant in the code. Versions are names, compared as strings.
- Every verification command the Done section asks you to run is written there in full. Run exactly those. **Do NOT run the whole `tests/` tree** (`python -m pytest`, `python -m pytest tests`, or any command that collects all of it): the whole suite is CI's run.
- **Mutation self-check (by hand, in process, no script in the diff).** Before you finish, apply each of these by hand, one at a time, run the full-file command `python -m pytest -p no:cacheprovider -q tests/test_program_install_keep.py` (the whole file, never one test), and revert. Revert by editing back, or from a saved copy of `bridge-install.py` kept in a folder you create at the Workspace root that no tracked file's path is under (for example `mutation-save.tmp/`), never under `bridge/`, and deleted before step 1 of Done; never with `git checkout` or `git restore`. Confirm with `git diff` that each revert is exact. List each in the report by its label and text, with that command's pytest summary line, verbatim, the id of one test it made fail, and how it was reverted. If one is not caught, write `not caught` and one line on the case that would catch it (do not add that case):
  - K1 an unknown word beginning with `-` is ignored instead of refused.
  - K2 an option given twice is accepted.
  - K3 the name match is case-insensitive.
  - K4 the name match is made by `os.path.isdir` of the value joined to `cursor-bridge-previous/` instead of against the listing's names.
  - K5 the next install ignores the marker (the one-previous rule removes the marked copy).
  - K6 `--rollback <version>` ignores the version and restores the newest kept copy.
  - K7 `save_previous` ignores this run's `--keep` value (uses only the stored marker).
  - K8 the link check removed (the rotation lists a linked base).
- **Known failures.** If a case fails that your change did not cause, report it by its test id with its failure lines and fix none.
- Prefer reuse over new code: the existing functions as they are, the standard library. Write the minimum that meets the acceptance criteria (the frozen `minimal-code.mdc` is in force). This never overrides a security, observability or accessibility requirement stated above.
- Rules in force for you: `.cursor/rules/secure-coding.mdc`, `.cursor/rules/workspace-boundary.mdc` and the frozen `minimal-code.mdc`.

## Done
Your report is the file `handoff/TASK-073-r3-report.md`, which you write as you go: what you did, what you changed, what you ran and what it printed, and what you could not do, so that nothing of it is lost if your run ends early. It names no computer path and no user name: write `<Workspace>` for the repository folder and `<tmp>` for a temporary folder, including in quoted command output.

When you finish, it holds:
- a list of every file you changed or created in this round;
- a one-paragraph summary of what you did;
- for F1 to F6, one line each on what meets it, naming the functions and their lines as the file stands after your change; for F1 the behaviour chosen for a linked folder; for F3 what a failed install check (exit 1) leaves (the copies and what the marker names); for F4 what happens when the entry named like the version cannot be removed;
- the mutation self-check list, K1 to K8, each with the full-file command's pytest summary line, the test id that caught it (or `not caught` and the case that would) and how it was reverted;
- every command of the list below with its output;
- a section headed exactly `Assumed, not verified`, as the report's last section.

The `Assumed, not verified` section lists every fact this change relies on that neither this brief nor the existing code settled, and that you did not confirm, and each item is true of the code as it stands. One item per line: what you assumed - why - what would confirm it. If there are none, write `Assumed, not verified: none`. Be specific: "edge cases" or "error handling" is not an item.

Run these from the Workspace root, in this order, after your last edit (and after the mutation save folder is deleted), each on its own, synchronously in the foreground, with no `PYTHONPATH` or other environment change:
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
- Each mutation is listed by its label and text, with what caught it and how it was reverted.
- A command you did not run is written `not run`, never described as run.
- Write the report's results after step 11, naming the commit its counts belong to (`git rev-parse HEAD`) and whether the working tree then held uncommitted changes (`git status --short`, step 11's output quoted verbatim).

Your last message is the summary and the report file's path, and nothing follows it. The supervisor reads only the last message, and a message printed earlier and then followed by more work is lost.
