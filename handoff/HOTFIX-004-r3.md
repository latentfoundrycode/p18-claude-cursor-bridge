---
record: brief
header: 1
id: "HOTFIX-004"
round: 3
satisfies: []
scope: ["bridge/cursor-bridge/bridge-run.py", "bridge/cursor-bridge/mutation-run.py", "tests/test_hotfix24a_heavy_slots.py", "docs/cli-reference.json", "docs/CLI_REFERENCE.md", "docs/BUILDER_NOTES.md", "handoff/HOTFIX-004-r3-report.md"]
merge_unit: null
blocking_class: "data integrity"
---
# HOTFIX-004 round 3: the heavy slots, round 2's review

Round cause: fix-induced

Blocking class: data integrity - a mutation run refused because its run id is already running deletes the live run's scratch folder (round 2's requirement 31); with it, security: on POSIX a hard-linked lock file is chmodded before the link check refuses it

## Objective
Round 2 (`handoff/HOTFIX-004-r2.md`, your report `handoff/HOTFIX-004-r2-report.md`) met requirements 26 to 34, and all of it stands but two points. Review A and the security audit rejected it for two defects, both listed under Requirements; the worse one is new in round 2: a mutation run refused because its run id is already running now deletes the scratch folder of the run that holds the lock. This round fixes those two defects and changes nothing else. Round 1's brief (`handoff/HOTFIX-004.md`) still governs requirements 1 to 25, its Constraints and its out-of-scope list, and round 2's brief governs 26 to 34; read both again whole, then this brief. Where they seem to disagree, this brief wins for the items it names; for anything else, stop and report rather than choose.

Satisfies: there is no build-plan increment and no requirements register row for this work (HOTFIX-004, the owner's two decisions of 2026-11-24, as in rounds 1 and 2). The trace is the acceptance file `tests/test_hotfix24a_heavy_slots.py`: round 1's 31 cases, round 2's 11 (`test_hotfix24a_r2_*`), and the cases the supervisor added after round 2's review (the section headed `round 3: round 2's review`, every test named `test_hotfix24a_r3_*`). Do not add a test.

## Scope
Files you may create or modify, each only as the paragraph after the list allows:
- bridge/cursor-bridge/bridge-run.py
- bridge/cursor-bridge/mutation-run.py
- tests/test_hotfix24a_heavy_slots.py
- docs/cli-reference.json
- docs/CLI_REFERENCE.md
- docs/BUILDER_NOTES.md
- handoff/HOTFIX-004-r3-report.md

What each entry allows, exactly: `bridge-run.py` and `mutation-run.py` are the two programs you change, only as the requirements below say. `tests/test_hotfix24a_heavy_slots.py` is the supervisor's acceptance test: read it and run it, never edit it. `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` change only by running `python tools/dump-cli.py`, and only if a program's help text changes (it should not). `docs/BUILDER_NOTES.md` takes dated lines appended at its end. `handoff/HOTFIX-004-r3-report.md` is your report, a new file. Leave `handoff/HOTFIX-004-r1-report.md` and `handoff/HOTFIX-004-r2-report.md` as they are. Do not modify anything else.

## Out of scope
- Everything rounds 1 and 2 put out of scope, unchanged.
- Every other finding of round 2's review: the window between the Windows link check and the open, the replace retry's error classes, the pid file on a timeout or an exception during the slot wait, and the wording of the mutation engine's existing link refusal. The supervisor records them; do not change them.

## Context
**Where you are.** The same checkout as rounds 1 and 2: the bridge's own source repository, on branch `hotfix-004`. Round 2's work is committed; the supervisor's checkpoint for this round is the commit that adds this brief.

**What the reviewers found** (line numbers on this branch, round 2's code):
- `mutation-run.py` `main`: requirement 31 moved the run lock under the `try` (from line 1555) whose `finally` (lines 1799 to 1807) removes `work_sub`, the folder `<scratch>/mutation-run-<run id>`. Every refusal raised in that `try` before the lock is held now reaches that `finally`: the link refusal (line 1556), the open failure (line 1561), the regular-file and one-link refusal (line 1569) and the "already running" refusal (line 1576). The last one is ordinary use: a second launch of a mutants file while the first runs is refused with exit 2, then deletes the first run's `tree/` and plugin while the first run's tests run in them, so the first run scores mutants for the wrong reason and caches those results. Round 1's rule for the second run is "ends at once with exit 2 ... writing nothing"; round 1's test 10 never put a folder there, so it did not see this.
- `bridge-run.py` `_open_heavy_lock` (lines 2063 to 2068, POSIX): `os.fchmod(fd, 0o600)` runs before the regular-file and one-link check (lines 2069 to 2075). A hard link at a lock file to another file of the owner's is refused as required, but that file has already been changed to mode 0600 (an executable script loses its execute bit). `O_NOFOLLOW` does not stop a hard link.

## Diagrams
None. The behaviour is round 1's.

## Requirements
35. **Only the run that holds the lock removes its scratch folder.** In `mutation-run.py` `main`, the scratch folder `work_sub` is removed only by a run that took the run lock (`_try_lock_byte` answered true). A refusal or exception before that point removes nothing and writes nothing; it closes the fd it opened, if any. The holder keeps round 2's order at its end: remove `work_sub`, then unlock, then close. For example: set a flag only once `_try_lock_byte` succeeds and guard the removal with it, or take the lock in an outer `try`/`finally` that only closes, with an inner `try`/`finally` after the lock that removes the folder, then unlocks. Test: `test_hotfix24a_r3_a_refused_mutation_run_leaves_the_live_runs_scratch`, with round 1's `test_hotfix24a_mutation_run_refuses_its_run_id_in_use` and round 2's `test_hotfix24a_r2_a_linked_mutation_lock_is_refused` still green.
36. **The lock file is checked before it is changed.** In `_open_heavy_lock`, on POSIX, the `os.fstat` regular-file and `st_nlink == 1` check comes directly after `os.open` and before `os.fchmod`; a file that fails it is closed and `OSError` raised as now, with no `fchmod` on it. Windows is unchanged. Test: `test_hotfix24a_r3_a_linked_lock_files_mode_is_left_as_it_was` (skipped on Windows; it runs on the POSIX CI), with round 2's `test_hotfix24a_r2_a_linked_lock_file_is_refused` still green.

## Acceptance criteria
- [ ] `python -m pytest tests/test_hotfix24a_heavy_slots.py -q -p no:cacheprovider` passes every case, round 3's included (the POSIX-only case is reported as skipped on Windows) (command 2).
- [ ] The regression batch (command 3) passes with no failure, no test file edited.
- [ ] `python tools/dump-cli.py --check` exits 0 (command 4).
- [ ] `windowless-check.py` reports no FAIL in the two programs (command 5).
- [ ] Both programs are ASCII-only (command 6 prints `ascii ok`).
- [ ] `git status --short` shows changes only to the Scope's files (command 7).
- [ ] Requirements 35 and 36 are fully met, and requirements 1 to 34 still are.

## Constraints
- Round 1's Constraints all hold, with every `HOTFIX-004-r1` in them read as `HOTFIX-004-r3` (the BUILDER_NOTES line form `YYYY-MM-DD HOTFIX-004-r3: <text>`, the report's name).
- Do not add dependencies.
- Verification commands: round 1's commands 1 to 7, exactly as written there, from the workspace root, in PowerShell, in the foreground. Run command 1 before your first edit and commands 2 to 7 once more after your last edit of any file, and quote those runs' output verbatim, never an earlier run's and never a summary of your own wording.

## Done
Your report is the file `handoff/HOTFIX-004-r3-report.md`, which you write as you go. When you finish, it holds:
- every file you changed;
- a one-paragraph summary of what you did;
- each requirement (35 and 36) with the file and line that meets it;
- the mutation code points: for each of requirements 35 and 36, the code point whose removal or change would break it, and the acceptance test (by name and parameter id) that would catch it, or `no test`;
- the output of every verification command, verbatim, in fenced blocks (both `git status --short` outputs, the last lines of both pytest runs with the summary line quoted whole and every failure's test id, the dump-cli check's exit code, the windowless-check output and exit code, the ASCII check's output, `git diff --stat`, `git rev-parse HEAD`); a command you did not run is written `not run`;
- the dated lines you appended to `docs/BUILDER_NOTES.md`, or `Builder notes: none`;
- a section headed exactly `Assumed, not verified`: every fact this change relies on that neither this brief, the earlier rounds' briefs, the design nor the existing code settled, and that you did not confirm, one per line (what you assumed; why; what would confirm it), or `Assumed, not verified: none`.

Your last message is the summary and the report file's path, and nothing follows it.
