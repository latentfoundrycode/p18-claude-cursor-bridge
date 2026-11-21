---
record: brief
header: 1
id: "TASK-068"
round: 3
satisfies: [R-088]
scope: ["bridge/cursor-bridge/in-flight.py", "bridge/cursor-bridge/loop-guard.py", "bridge/cursor-bridge/MANIFEST.json", "tests/test_loop_guard.py", "docs/BUILDER_NOTES.md", "handoff/TASK-068-r3-report.md"]
merge_unit: null
blocking_class: null
---
# TASK-068 round 3: the in-flight program (R-088)

Round cause: defect - bridge/cursor-bridge/loop-guard.py:203, `last_field`'s pattern lets the white space after the colon run past the line break, so an empty `Paused:` line, the form that lifts a pause, takes the next line as its value and a later ordinary line reads as a pause (a defeated safety mechanism, convergent: the security review's B1 and Review A's note); security - bridge/cursor-bridge/in-flight.py:352-397, a log that is a hard link to a file outside the Workspace is appended to (convergent: Review A and the security review)

## Objective
This is round 3 of TASK-068, the review ceiling's round: only the corrections below, each a finding of the five blocking classes. Round 2's code is committed (the commit "TASK-068 r2: the builder's work (rejected) and the round-3 tests") with the supervisor's three new cases at the end of the acceptance file. Make the minimum changes the corrections name, keep every test green, and edit nothing in the acceptance file. The briefs of rounds 1 and 2, `handoff/TASK-068.md` and `handoff/TASK-068-r2.md`, stay in force for everything this brief does not change.

Satisfies: R-088 - as round 1's brief.

## Scope
Files you may create or modify:
- bridge/cursor-bridge/in-flight.py
- bridge/cursor-bridge/loop-guard.py
- bridge/cursor-bridge/MANIFEST.json
- tests/test_loop_guard.py
- docs/BUILDER_NOTES.md
- handoff/TASK-068-r3-report.md

Limits on these files: `loop-guard.py`: correction 1 alone, inside `last_field` (`field` and every other function unchanged). `in-flight.py`: corrections 2 and 3 alone. `MANIFEST.json` only as regenerated. `tests/test_loop_guard.py`: one `test_r088_` case you add for correction 1; no other case changes. `tests/test_program_in_flight.py` is the supervisor's, read only. `docs/BUILDER_NOTES.md`: correction 4, a new line at the file's end.

## Out of scope
As the earlier rounds' briefs. Nothing beyond the four corrections: no refactoring, no other finding of the reviews (the supervisor records the rest in `docs/HARDENING.md`), no option, no environment variable, no new dependency.

## Corrections
1. **An empty `Paused:` line reads as empty (a defeated safety mechanism).** In `last_field`, the white space the pattern allows after the colon, and around the value, matches spaces and tabs only (`[ \t]*` where `field`'s pattern has `\s*`), never a line break, so `Paused:` alone on its line gives the value `""` (no wait), a later line never becomes its value, and `Paused:` followed by `Paused: resumed` gives `resumed`. `field` is not changed. Add a `test_r088_` case to `tests/test_loop_guard.py` with a log `Paused: x` / `Paused:` / `<stamp> text`, read as no wait.
2. **The log is never written through a hard link, and the checks hold at the write (security).** The log is opened with `O_NOFOLLOW` where the platform has it, beside the flags it has; after the open and before any byte is written, `os.fstat` of the open log must show one link (`st_nlink == 1`), and round 2's folder checks (`_log_blocked`) are run again; either failing ends the run with exit 2, the message `in-flight: REFUSED - <reason>`, and nothing appended.
3. **The file read is the file checked, compared without following (security).** For `--file`, take `os.lstat` of the checked real path during the checks, before the open, and compare `os.fstat` of the opened file with that result (`st_dev` and `st_ino`, where both are non-zero), in place of round 2's `os.stat` after the open.
4. **The notes say where the lock is (records).** Append one line to `docs/BUILDER_NOTES.md` saying that, since round 2, the Windows lock sits on the byte at `2**31`, not byte 0 as round 1's line says.

## Context
The acceptance file gained three cases after the line `# Round 3 (TASK-068-r3)`: an empty `Paused:` line never takes the next line as its value (through the loop guard's own `paused_in_flight`); an `in-flight.md` that is a hard link to a file outside the Workspace is refused, the outside file unchanged; a `run/supervisor/` linked to another folder of the same Workspace is refused. On round 2's code: "2 failed, 1 passed" (the third already holds; keep it holding).

Threat model: as round 1's brief. The log decides, through the loop guard, whether the supervisor may end its turn.

## Acceptance criteria
- [ ] Every test in `tests/test_program_in_flight.py` passes (round 1's symbolic-link case skipped where the account cannot create a link), and every test of round 1's Done list passes.
- [ ] Corrections 1 to 4 met, each named in the report with its function and lines.
- [ ] Every line added ASCII.

## Constraints
The earlier rounds' Constraints all stand. Mutations by hand, in process, each reverted, listed by label with the pytest line that shows a test failing, else `not run`: (H1) `last_field`'s `\s*` restored; (H2) the log's `st_nlink` check dropped; (H3) the `--file` comparison made against `os.stat` after the open again. Prefer the smallest change.

## Done
Your report is `handoff/TASK-068-r3-report.md`, in round 2's form (files changed; summary; each correction with its function and lines; every command below with its output, verbatim, in fenced blocks; the mutations H1 to H3; a last section headed exactly `Assumed, not verified`). It names no computer path: `<Workspace>` for the repository folder, `<tmp>` for a temporary folder.

Run round 2's Done list, commands 1 to 12, in order, from the Workspace root, after your last edit, each in the foreground, with no environment change; quote the last run. Every pytest summary line quoted verbatim; never restate a count in prose. Your last message is the summary and the report file's path, and nothing follows it.
