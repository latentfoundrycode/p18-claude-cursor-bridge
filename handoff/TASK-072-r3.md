---
record: brief
header: 1
id: "TASK-072"
round: 3
satisfies: [R-092]
scope: ["bridge/cursor-bridge/conformance-check.py", "bridge/cursor-bridge/MANIFEST.json", "docs/BUILDER_NOTES.md", "handoff/TASK-072-r3-report.md"]
merge_unit: null
blocking_class: null
---
# TASK-072 round 3: no link is followed to the git folder (R-092)

Round cause: defect - bridge/cursor-bridge/conformance-check.py:589 and the gitdir target's check below it, os.path.isdir follows a link or reparse point at the Workspace's .git (and at the folder a .git file's gitdir: line names) before the network-path refusal, so a .git link naming a folder on another host opens a network connection outside any timeout, against the round-2 brief's rule that reading the row never opens one (Review B round 1, finding 1; defeated safety mechanism)

## Objective
This is round 3 of TASK-072. Round 2's code is accepted and committed; Review B's round 1 found the defect above. The supervisor's two new cases are at the end of `tests/test_program_weekly_floor.py`, after the comment `# ---------------------------------------------------------------- round 3: no link is followed to the git folder`, each named `test_r3_...`. Make the one correction below, keep every test green, and edit nothing in the acceptance file. Round 1's brief, `handoff/TASK-072.md`, and round 2's, `handoff/TASK-072-r2.md`, stay in force for everything this brief does not change: their rulings, Context, Constraints and Done list.

Satisfies: R-092 - as round 1's brief.

## Scope
Files you may create or modify:
- bridge/cursor-bridge/conformance-check.py
- bridge/cursor-bridge/MANIFEST.json
- docs/BUILDER_NOTES.md
- handoff/TASK-072-r3-report.md

Limits on these files: `conformance-check.py`, the one correction alone, inside `_own_git_dir`; `MANIFEST.json` only through its generator, as round 1 (`python tools/make-manifest.py`, then `git restore bridge/cursor-bridge/VERSION`). Every other file is read only, every test file among them (`tests/test_program_weekly_floor.py` is the supervisor's). The module docstring does not change, so the command reference is not regenerated and `python tools/dump-cli.py --check` stays green.

## Out of scope
As round 1's and round 2's briefs. Nothing beyond the correction: no refactoring, no other finding (the supervisor records the rest in `docs/HARDENING.md` under TASK-072: a link in a parent folder of the path, git's own `commondir`, the `\??\` form, the environment's `GIT_COMMON_DIR`), no option, no environment variable, no new dependency. The program's other git calls (`git_ignored`, `git_tracked`, `tracked_files`) are not changed.

## Correction
1. **No link is followed to the git folder (Review B round 1, finding 1).** In `_own_git_dir`, before any call that follows a link (`os.path.isdir`, `os.path.isfile`, `os.path.abspath` is string work and may stay), look at the entry itself without following it (`os.lstat`) and read it as no git folder (return None) where it is a link or a reparse point of any kind: `stat.S_ISLNK(st.st_mode)`, or on Windows `st.st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT` (a junction, which `os.path.islink` does not report, among them; read the attribute with `getattr(st, "st_file_attributes", 0)` so the code runs on Linux). Do this at the two places a path is followed: the Workspace's `.git` entry, and the folder a `.git` file's `gitdir:` line names (after the network-path refusal and the join to the Workspace, before `os.path.isdir`). An `OSError` from `os.lstat` (the entry missing or unreadable) is read as no git folder, as today. Only the last component of each path is looked at; a link in a parent folder is out of scope. Cases: `test_r3_a_git_entry_that_is_a_link_is_not_followed` (round 2: MISSING where NOTE is right) and `test_r3_a_gitdir_target_that_is_a_link_is_not_followed` (round 2: MISSING where NOTE is right). The cases make a junction on Windows (no privilege needed) and a symbolic link elsewhere.

## Context
The two cases are red on round 2's code; the supervisor's stripped run of the acceptance file is quoted in the commit that added them ("TASK-072 r3: Review B's finding as tests"). Read `_own_git_dir` as it stands (from line 585): the `.git` entry is tested with `os.path.isdir` then `os.path.isfile`, the `gitdir:` value read, refused when empty, starting with `-`, holding a NUL or beginning with two slashes, joined to the Workspace when relative, then tested with `os.path.isdir`. The other cases of the acceptance file (a plain `.git` folder, a `.git` file from `git init --separate-git-dir` with a space in its path, no `.git`) must read as today.

## Acceptance criteria
- [ ] Every test in `tests/test_program_weekly_floor.py` passes, unedited.
- [ ] Every test of round 1's Done list passes, unedited, `tests/test_dump_cli.py` whole among them.
- [ ] The one correction and nothing else; no new option, environment variable or dependency; no `.github` file changed; the docstring unchanged.
- [ ] MANIFEST regenerated; `bridge/cursor-bridge/VERSION` not listed by `git status --short`; `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` prints `RESULT: SOURCES MATCH`.
- [ ] `conformance-check.py` stays ASCII.

## Constraints
As round 1's brief, every one of them; among them: do not run the whole `tests/` tree; no path of this computer or user name in anything you write (`<Workspace>`, `<tmp>`); the git commands that are not yours to run; the mutation self-check by hand, in process, no script in the diff, this round's labels being:
- R3-M1 the link check at the `.git` entry is removed.
- R3-M2 the link check at the `gitdir:` target is removed.
- R3-M3 only `S_ISLNK` is tested (the reparse-point attribute dropped).
Apply each by hand, one at a time, run `python -m pytest -p no:cacheprovider -q tests/test_program_weekly_floor.py`, revert, confirm the revert with `git diff`, and list each in the report with its pytest summary line and the id of a case it made fail, or `not caught` with one line on the case that would catch it (add none).

## Done
Your report is the file `handoff/TASK-072-r3-report.md`, written as you go, holding what round 1's Done section asks of its report (the files changed, a summary, one line on the correction naming the function and its lines, the mutation self-check list, every command with its output, and the `Assumed, not verified` section as the last section). Run round 1's Done list (commands 1 to 12) after your last edit, in its order, with round 2's change: commands 7 and 8 are expected to pass whole. Your last message is the summary and the report file's path, and nothing follows it.
