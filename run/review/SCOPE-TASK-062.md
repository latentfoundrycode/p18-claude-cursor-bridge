# SCOPE for TASK-062 (Review B, round 1)

TASK-062 is the launcher's detection of a change of git's configuration (R-081). Around a run of kind test or driver, the launcher fixes the paths to read from git before the child starts: the common git folder's `config` and `info/attributes`; the worktree's `config.worktree`, `commondir` and `.git`; and the hooks folders (the folder git uses, from `git rev-parse --git-path hooks` joined against the launch folder, and the common folder's `hooks`). It reads them by content before and after, with no git call after, and prints one line `bridge-run: GIT-CONFIG <path> <new|removed|changed|unreadable>` per difference, after the run's output and before the exit line. The exit code, the log row and the limit are unchanged, and nothing is restored.

The branch is task-062, from main db96c46 (PR #168's merge, TASK-061). There were two builder rounds. This is the review guard's first round for TASK-062, below the code gate's ceiling, so there is no Blocking class line.

Where the increment ends:
- `bridge/cursor-bridge/bridge-run.py`: the helpers `_git_rev_parse` to `git_config_changes`, `GitConfigWatch`, and their use in `main()`.
- `MANIFEST.json`, regenerated.
- `tests/test_program_git_config.py` (the supervisor's) and the builder's R-081 cases in `tests/test_bridge_run.py`.
- The records.

Three cases beyond the plan's file list were taken from the security audit of round 1 (docs/CHANGES.md, 2026-11-15):
- a hooks entry that is not a regular file reads `unreadable` and is never opened;
- a hooks folder that is a link or junction is never listed through it;
- a linked worktree's `.git` file and `commondir` are read.

The reviews' leads (HARDENING, TASK-062, leads 1 to 20) are recorded, not this diff's defects. Among them:
- the gap between lstat and open, and between the folder check and the listing;
- the limit path's after-read running before the kill;
- a link at both reads giving no line;
- no cap on entries or bytes;
- an absolute path printed for an outside path;
- `_git_resolved_path`'s stale docstring, fixed by TASK-084, the next increment that edits the file.

The INVENTORY order row's change (release E moved last) is the owner's decision of 2026-11-15 and unrelated to the code.

Read the commit messages (git log, the full bodies) for the quoted lines.

## The plan entry, quoted (docs/BUILD_PLAN.md, TASK-062)
Scope: bridge/cursor-bridge/bridge-run.py; bridge/cursor-bridge/MANIFEST.json; tests/test_program_git_config.py; tests/test_bridge_run.py; docs/BUILDER_NOTES.md; handoff/TASK-062-r<N>-report.md
Satisfies: R-081
Done when: around a run of kind test or driver the launcher reads, before and after, the bytes of `config` and `info/attributes` in the common git folder of the repository the launch folder belongs to, of `config.worktree` in the worktree's own git folder, and of every entry in the hooks folders, the folder `core.hooksPath` named before the run and the common folder's `hooks`, each entry compared by its name and a hash of its content, and prints on standard error one line `bridge-run: GIT-CONFIG <path relative to the repository> <new|removed|changed>` per difference, after the run's own output; the run's exit code, its log row and its limit are unchanged, nothing is restored, and a launch folder in no repository prints nothing; a read that fails prints `bridge-run: GIT-CONFIG <path> unreadable` and changes nothing else; builder and review runs are untouched (the guard and BOUNDARY hold those); `tests/test_program_git_config.py` (names R-081, D-004) holds the reproduction of release T's stage T2, a stripped test that writes `core.fsmonitor`, red on the checkpoint, a hook file added, a hook replaced by a file of the same size, a hooks path set, an attributes file added, a `config.worktree` written in a worktree, a file removed, and a run that changes nothing printing no line; the mutants file sweeps the comparison (a file dropped from the list, the after-read skipped, the exit changed), every mutant killed; MANIFEST regenerated; no option added; no new dependency.

## The supervisor's tests, each with the clause it enforces
- tests/test_program_git_config.py names R-081 and D-004. It was committed at the checkpoint 3014cbe (red there: 12 failed, 3 passed). It covers:
  - the T2 reproduction: a stripped test writing core.fsmonitor, exit 3 passing through, the line after the run's output, the exit line last, nothing restored;
  - a run that changes nothing, with the log row's keys unchanged;
  - a hook new, changed with the same size, and removed;
  - core.hooksPath set during the run (`.git/config changed` only);
  - the folder core.hooksPath named before the run, read;
  - attributes new and removed;
  - config.worktree in a linked worktree;
  - a driver run;
  - builder and review runs untouched;
  - no repository;
  - a read that fails.
- Cases added for round 2 (c3027d2), 4 red on round 1:
  - make_repo creates run/;
  - a launch from a sub-folder, with and without a relative core.hooksPath;
  - a hook replaced by a folder (unreadable);
  - a persistent sub-folder of a hooks folder (no line);
  - a FIFO on POSIX;
  - the hooks folder swapped for a junction or link;
  - a linked worktree's .git file and commondir.
- Cases added after round 2's builder, both failing on round 1's code by mutation-run.py --checkpoint c3027d2:
  - a launch folder without run/ gains none;
  - one entry whose read fails in any way (MemoryError, in process) silences no other line.
- The supervisor's test-only fix in 4db20db: 11 creationflags lines in this file and in the builder's cases spell CREATE_NO_WINDOW (tests/test_tests_windowless.py's scan).

## The builder's departure, round 1
Round 1 made main() create a missing run/ folder before write_log, to satisfy the acceptance file's defect. Round 2 removed it on both reviewers' findings.

## The mutants
run/supervisor/TASK-062-mutants.json: 19 mutants over the two test files. counts: run=19 cached=0 killed=19 survived=0 not applied=0 error=0 expected survive=0

## Evidence
- Review A: round 1 REJECT, round 2 APPROVE; its re-read of the records REJECT on records only (a case count, two missing leads), fixed in the commit after the records and confirmed.
- Security audit: round 1 FAIL, round 2 PASS.
- Targeted run on round 2: 469 passed, 4 skipped (POSIX-only skips).
- Whole suite with the records: 1 failed, 5340 passed, 43 skipped. The failure was the windowless scan, fixed in 4db20db; its re-run: 70 passed, 1 skipped.

## Expected bookkeeping and records in the diff
- handoff/TASK-062.md and handoff/TASK-062-r2.md, with their reports
- docs/BUILDER_NOTES.md
- docs/HARDENING.md
- docs/CHANGES.md
- docs/INVENTORY.md
- docs/PROJECT_STATUS.md (as at PR #169's merge)
- run/review/ (these files)

docs/REQUIREMENTS.md is unchanged: R-081 stays planned until TASK-082 writes its step-4 sentence.
