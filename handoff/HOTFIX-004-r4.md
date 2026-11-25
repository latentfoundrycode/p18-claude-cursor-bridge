---
record: brief
header: 1
id: "HOTFIX-004"
round: 4
satisfies: []
scope: ["bridge/cursor-bridge/bridge-run.py", "tests/test_hotfix24a_heavy_slots.py", "docs/BUILDER_NOTES.md", "handoff/HOTFIX-004-r4-report.md"]
merge_unit: null
blocking_class: "behaviour"
---
# HOTFIX-004 round 4: the heavy slots, Review B's first round

Round cause: defect

Blocking class: behaviour - a file at run/launcher/pids makes the launch try run ids forever; with it, safety mechanism: any other failure to make the pid file keeps a run id that was never reserved

## Objective
Rounds 1 to 3 (`handoff/HOTFIX-004.md`, `handoff/HOTFIX-004-r2.md`, `handoff/HOTFIX-004-r3.md`) built hotfix 2026.11.24a, and Review A and the security audit approved round 3. The cross-family Review B then rejected the branch for two defects in one function, `create_pid_file_exclusive`, listed under Requirements: the launch can loop forever, or keep a run id it never reserved. This round fixes that function and its one caller, and changes nothing else. The earlier briefs still govern requirements 1 to 36, their Constraints and their out-of-scope lists; read them again whole, then this brief. Where they seem to disagree, this brief wins for the items it names; for anything else, stop and report rather than choose.

Satisfies: there is no build-plan increment and no requirements register row for this work (HOTFIX-004, the owner's two decisions of 2026-11-24). The trace is the acceptance file `tests/test_hotfix24a_heavy_slots.py`: rounds 1 to 3's cases, and the cases the supervisor added after Review B (the section headed `round 4: Review B round 1`, every test named `test_hotfix24a_r4_*`). Do not add a test.

## Scope
Files you may create or modify, each only as the paragraph after the list allows:
- bridge/cursor-bridge/bridge-run.py
- tests/test_hotfix24a_heavy_slots.py
- docs/BUILDER_NOTES.md
- handoff/HOTFIX-004-r4-report.md

What each entry allows, exactly: `bridge-run.py` is the one program you change, only as the requirements below say. `tests/test_hotfix24a_heavy_slots.py` is the supervisor's acceptance test: read it and run it, never edit it. `docs/BUILDER_NOTES.md` takes dated lines appended at its end. `handoff/HOTFIX-004-r4-report.md` is your report, a new file. Leave the earlier rounds' reports as they are. Do not modify anything else: `mutation-run.py`, `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` included (no help text changes this round).

## Out of scope
- Everything the earlier rounds put out of scope, unchanged, and the release stamp: `VERSION`, `MANIFEST.json`, `CHANGELOG.md` and `docs/HARDENING.md` are the supervisor's, restamped after your run.
- `write_pid_file` (the rewrite at the child's start) stays as it is.
- Never run `bridge-run.py`, `mutation-run.py` or `bridge-install.py` against the real home folder, this repository's real `run/` record or the real `cursor-agent`.

## Context
**Where you are.** The same checkout as the earlier rounds: the bridge's own source repository, on branch `hotfix-004`. Round 3's work and the release stamp are committed; the supervisor's checkpoint for this round is the commit that adds this brief.

**What Review B found** (line numbers on this branch, round 3's code):
- `create_pid_file_exclusive` (lines 1560 to 1578) wraps `os.makedirs(run/launcher/pids)` and the exclusive `os.open` of the pid file in one `try`, and answers False for any `FileExistsError`. `os.makedirs` raises `FileExistsError` when `run/launcher/pids` is a file, so every run id reads as taken; `main`'s loop (lines 3295 to 3305) then tries the next suffix with no end, never printing its started line. Review B planted the file and saw 1294 tries in 0.3 seconds.
- Every other `OSError` answers None, the same answer as a folder with no `run/`, and `main` keeps that run id with no pid file. A folder at `run/launcher/pids/<run id>` makes the open fail with a permission error on Windows, so two launches in one second can both keep one id, and `bridge-stop.py` has no pid file for either.

## Diagrams
None.

## Requirements
37. **What the reservation answers.** `create_pid_file_exclusive(folder, run_id)` keeps its name and parameters and answers: None only when `folder` has no `run/` folder (as now); the pid file's path when it created the file exclusively (as now); False only when the exclusive `os.open` of the pid file itself raises `FileExistsError` (the name is taken); and for every other failure, `os.makedirs` of `run/launcher/pids` included, it raises the `OSError` to its caller, leaving nothing behind (a pid file it created and could not write is removed). Test: `test_hotfix24a_r4_a_pid_file_that_cannot_be_made_is_never_a_reservation`.
38. **A reservation that fails refuses the launch.** In `main`, an `OSError` from `create_pid_file_exclusive` ends the launch at once with exit 125 and the one line `bridge-run: refused - cannot reserve run/launcher/pids/<run id> (<error class>)` (`<run id>` the id being tried, as written in the started line; `<error class>` the exception's class name), before the started line, like the early refusals that precede it: the command never starts, no pid file is left, and nothing else is written. The suffix loop is otherwise unchanged. Test: `test_hotfix24a_r4_an_unusable_pids_folder_refuses_the_launch`, with round 1's `test_hotfix24a_same_second_launches_get_distinct_ids` and round 2's `test_hotfix24a_r2_an_early_refusal_leaves_no_pid_file` still green.

## Acceptance criteria
- [ ] `python -m pytest tests/test_hotfix24a_heavy_slots.py -q -p no:cacheprovider` passes every case, round 4's included (the POSIX-only case is reported as skipped on Windows) (command 2).
- [ ] The regression batch (command 3) passes with no failure, no test file edited.
- [ ] `python tools/dump-cli.py --check` exits 0 (command 4).
- [ ] `windowless-check.py` reports no FAIL (command 5).
- [ ] `bridge-run.py` is ASCII-only (command 6 prints `ascii ok`).
- [ ] `git status --short` shows changes only to the Scope's files (command 7).
- [ ] Requirements 37 and 38 are fully met, and requirements 1 to 36 still are.

## Constraints
- Round 1's Constraints all hold, with every `HOTFIX-004-r1` in them read as `HOTFIX-004-r4` (the BUILDER_NOTES line form `YYYY-MM-DD HOTFIX-004-r4: <text>`, the report's name).
- Do not add dependencies.
- Verification commands: round 1's commands 1 to 7, exactly as written there, from the workspace root, in PowerShell, in the foreground. Run command 1 before your first edit, and commands 2 to 7 once more after your last edit of any file, the report included: write the report, then run command 7 and paste its output last. Quote those runs' output verbatim, never an earlier run's and never a summary in your own words.

## Done
Your report is the file `handoff/HOTFIX-004-r4-report.md`, which you write as you go. When you finish, it holds:
- every file you changed;
- a one-paragraph summary of what you did;
- each requirement (37 and 38) with the file and line that meets it;
- the mutation code points: for each of requirements 37 and 38, the code point whose removal or change would break it, and the acceptance test that would catch it, or `no test`;
- the output of every verification command, verbatim, in fenced blocks (both `git status --short` outputs, the last lines of both pytest runs with the summary line quoted whole and every failure's test id, the dump-cli check's exit code, the windowless-check output and exit code, the ASCII check's output, `git diff --stat`, `git rev-parse HEAD`); a command you did not run is written `not run`;
- the dated lines you appended to `docs/BUILDER_NOTES.md`, or `Builder notes: none`;
- a section headed exactly `Assumed, not verified`: every fact this change relies on that neither this brief, the earlier rounds' briefs, the design nor the existing code settled, and that you did not confirm, one per line (what you assumed; why; what would confirm it), or `Assumed, not verified: none`.

Your last message is the summary and the report file's path, and nothing follows it.
