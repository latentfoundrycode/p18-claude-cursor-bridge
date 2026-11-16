# SCOPE: TASK-063 (R-082), the permission guard reads a command as the shell does

Round cause: defect

Blocking class: behaviour - CI red on PR #171 at 3964f80: tests/test_tests_windowless.py::test_fix001_no_test_starts_a_program_around_the_default fails on tests/test_program_permission_guard.py line 397, the acceptance case husky-before-python-c, whose string literal holds the text os.system( and so matches the windowless scan's launch pattern (1 failed, 6064 passed, 66 skipped on ubuntu-latest)

The head the line is confirmed against: 3964f80 (the pull request's head when CI failed; the reviews of round 3 approved its tree apart from run/review/). Confirm or deny the line by running that test at 3964f80, never against the head under review.

## This re-review

The only change since 3964f80 outside run/review/ is one line of the supervisor's acceptance file, tests/test_program_permission_guard.py line 397: the literal is split into two concatenated parts, so the line no longer holds os.system( as one piece and the string the test hands the guard is unchanged. No builder ran and no guard code changed. merge.md: a new head is read again by the reviews; this one is above the ceiling, so this class line lifts it. Round 10's code and the rest of the increment are as round 3's reviews read them; Review B's round-3 finding (git worktree remove -- --help, the guard's --help exemption) was resolved for Review A's approval as a contrived layout, recorded and not blocking, its record going to docs/CHANGES.md and docs/HARDENING.md after the merge.

## Where the increment ends

The increment is ten builder rounds of one brief series, handoff/TASK-063.md and handoff/TASK-063-r2.md to handoff/TASK-063-r10.md, each later brief governing where they differ, and two resolution rounds (handoff/RESOLUTION-TASK-063.md and handoff/RESOLUTION-TASK-063-2.md; their decisions in docs/CHANGES.md, 2026-11-15). The design it builds is the flat grammar the second resolution round chose: one list of complete words per command, read by bash, PowerShell 5.1 or cmd rules, every nested construct refused as unreadable (docs/DESIGN.md, Change: the program release, "The permission guard, permission-guard.py (C5)", rewritten in this branch's records commit). The last round's Scope, quoted from handoff/TASK-063-r10.md:

- bridge/cursor-bridge/permission-guard.py
- bridge/cursor-bridge/MANIFEST.json
- docs/cli-reference.json
- docs/CLI_REFERENCE.md
- tests/test_permission_guard.py
- tests/test_permission_guard_a4.py
- docs/BUILDER_NOTES.md
- handoff/TASK-063-r10-report.md

Its Out of scope, quoted: everything the Out of scope sections of rounds 5 to 9 list, unchanged; `tests/test_program_permission_guard.py`, `tests/test_allowlist.py` and `tests/test_task032_supervisor_guard.py` are the supervisor's; env's and sudo's strict reading (round 9's requirement 3) is unchanged; everything round 9's readers found besides B1 and B2 (ssh's `-o` by a cluster, a quoted key or a leading blank; a locale value with a modifier; a `/bin/../` path to Git's launcher; ssh-agent's second parse; tar's checkpoint action; a command in an option, a configuration value or the environment), which the supervisor records.

Design for later increments is not this diff's defect: TASK-083 adds the ready record the guard will read, TASK-064 the branch rule's reader; neither is here.

## The threat model (docs/INVENTORY.md, Decisions)

The permission guard's row (2026-11-16, in this diff): inside it, a command the agent's Bash or PowerShell tool is about to run that names a refused action in its own words (a force-push, an override merge, a merge without the pre-merge record, `git worktree remove`, `cursor-agent` started around the launcher, a commit with the hook runner off) under any quoting, chain, wrapper shell, prefix, assignment or launcher the guard reads or sees through, and the guard's own deadline; outside it, recorded in docs/HARDENING.md and never blocking by itself: a deliberate reach that hides the action from that reading, as code given to an interpreter (`python -c`, a script file), a command a program takes from an option value, its configuration or the environment, a word a child program parses again under a runtime or locale crafted for it, or a path written to reach a launcher the guard excludes. The refusals already built against some of these stand as defence in depth, their completeness not claimed. The bridge's whole model (the row after it) names outside input: what the builder and the reviewers write, what a program reads from GitHub, a record an agent left; a deliberate reach past a program's check by a process running as the owner's account is outside it.

## The tests the supervisor wrote

- `tests/test_program_permission_guard.py` (the acceptance file, written before round 1 and extended each round, never edited by a builder): each test runs the guard as the hook runs it and reads the exit and the reason. Its sections, in order: the design's two reproductions (DESIGN.md, the guard paragraph's "two holes"); the refusals moved onto the command's own words (the `gh api graphql` substitution, `HUSKY=0`, `--no-verify` per subcommand) and the three false refusals passing (the paragraph's first bullet); the `gh api` ampersand's remedy (third bullet); the first resolution round's forms; the flat grammar's forms after the second resolution round (unreadable forms with their reasons, the instructed commands passing, timing within the hook's 15 seconds); and one section per round's findings, "round 5's findings" to "round 9's findings", each form a finding of that round's readers that the round before let through (the flat grammar's bullet and the threat-model row). The last section ends with four cases the supervisor added after round 10's reviews, holding the builder's assumptions (`GIT_CONFIG+=`, `BASH_FUNC_x+=`, `sudo X+=1`, `husky+=0`).
- `tests/test_allowlist.py` (the supervisor's change of the first resolution round): every runnable instructed command, its `<...>` placeholders replaced by a sample word, passes the guard.
- `tests/test_task032_supervisor_guard.py` (two cases respelt with the round-7 brief): the launcher-bypass refusals of `cursor-agent` behind `bash -c` and `cmd //c`.

## The mutants

`run/supervisor/TASK-063-mutants.json`, written by `run/supervisor/make_063_mutants.py` (both gitignored, in the supervisor's checkout): 11 mutants over round 10's guard, each listing every test it fails in the acceptance file and `tests/test_permission_guard_a4.py` (a substitution inside double quotes read as text; the append assignment not read; `HUSKY+=0` not the hook runner; the shell-code names read as plain; any locale value accepted; no word an MSYS program parses again; the re-parse scan at every prefix; a blank powershell.exe argument kept; a find clause running the found file allowed; ssh-agent running a command allowed; the cd wrapper not refused). Its result is in docs/HARDENING.md under TASK-063.

## Expected bookkeeping and record files in the diff

`docs/BUILDER_NOTES.md`; `docs/cli-reference.json` and `docs/CLI_REFERENCE.md`, regenerated by `tools/dump-cli.py` from the guard's docstring; `docs/ROSTER.resolved.json`, the roster check's resolution after the full profile returned on 2026-11-16 (dcaf5a3); the builders' reports `handoff/TASK-063-r<N>-report.md`; the briefs `handoff/TASK-063*.md` and the resolution files `handoff/RESOLUTION-TASK-063*.md`; the records committed by the supervisor (`docs/CHANGES.md`, `docs/DESIGN.md`, `docs/HARDENING.md`, `docs/INVENTORY.md`, `docs/PROJECT_STATUS.md`, `docs/REQUIREMENTS.md`); `run/review/` (this file, the round's diff and assumptions file).
