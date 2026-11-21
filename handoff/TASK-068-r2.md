---
record: brief
header: 1
id: "TASK-068"
round: 2
satisfies: [R-088]
scope: ["bridge/cursor-bridge/in-flight.py", "bridge/cursor-bridge/loop-guard.py", "bridge/cursor-bridge/bridge_env.py", "bridge/cursor-bridge/MANIFEST.json", "docs/cli-reference.json", "docs/CLI_REFERENCE.md", "tests/test_loop_guard.py", "docs/BUILDER_NOTES.md", "handoff/TASK-068-r2-report.md"]
merge_unit: null
blocking_class: null
---
# TASK-068 round 2: the in-flight program (R-088)

Round cause: defect - bridge/cursor-bridge/loop-guard.py:191-196 with bridge/cursor-bridge/in-flight.py:101-124, the loop guard reads the first `Paused:` line of the log, so a log the program only appends to can never lift a pause and the guard then lets every stop through (a defeated safety mechanism, convergent: Review A B2 and the security review's blocking finding); behaviour - bridge/cursor-bridge/in-flight.py:330, the log is opened without `O_BINARY`, so every line is written with CR LF on Windows where Requirement 5 says LF (Review A B1)

## Objective
This is round 2 of TASK-068. Round 1's code is committed (the commit "TASK-068 r1: the builder's work (rejected) and the round-2 tests", `git log` shows it) with the supervisor's eight new cases at the end of the acceptance file. Round 1 met most of the brief; this round makes the minimum changes the corrections below name, keeps every test green, and edits nothing in the acceptance file. Round 1's brief, `handoff/TASK-068.md`, stays in force for everything this brief does not change, except one sentence of it: round 1's brief kept the loop guard's decision unchanged; correction 2 changes which `Paused:` line the guard reads (the supervisor's decision for this round).

Satisfies: R-088 - The live position is written by a program (C15, J3): `in-flight.py` appends one line, `<UTC time from the clock> <text>`, to the Workspace's `run/supervisor/in-flight.md`, the text from a file under `run/supervisor/` (`--file`) or from one argument, and with `--pass <name> <reviewer>` and the optional `--round <n>` and `--cause <cause>` a tagged line for a review pass; it refuses outside a Workspace or with no text and prints what it wrote; the loop guard's refusal and the three texts that sent the live position to the status file's `In flight:` line (rule 54, calibration's step 0, the parallel builders' paragraph) name the in-flight log and this program, and KP-041 is retired. (The three texts and KP-041 are TASK-078's, as in round 1.)

## Scope
Files you may create or modify:
- bridge/cursor-bridge/in-flight.py
- bridge/cursor-bridge/loop-guard.py
- bridge/cursor-bridge/bridge_env.py
- bridge/cursor-bridge/MANIFEST.json
- docs/cli-reference.json
- docs/CLI_REFERENCE.md
- tests/test_loop_guard.py
- docs/BUILDER_NOTES.md
- handoff/TASK-068-r2-report.md

Limits on these files: `in-flight.py`: corrections 1 and 3 to 8. `loop-guard.py`: correction 2 alone (the function `paused_in_flight` and, where you need one, one new helper beside `field`; `field` itself and every other reader of the status file unchanged). `bridge_env.py`: correction 9 alone. `MANIFEST.json`, `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` only as regenerated. `tests/test_loop_guard.py`: one or two `test_r088_` cases you add for correction 2; no other case changes. `tests/test_program_in_flight.py` is the supervisor's, read only. `docs/BUILDER_NOTES.md`: a new line at the file's end.

## Out of scope
As round 1's brief. In particular: `bridge-run.py`, `pace-report.py`, `settings.bridge.json` and every test file but `tests/test_loop_guard.py` untouched; the loop guard's other decisions, its other messages and the status file's readers unchanged; no option, no environment variable, no new dependency, no import of a module outside the standard library; the supervisor's mutants file is not yours.

## Corrections
1. **LF on every platform (behaviour; Review A B1).** The log is opened for the append with `O_BINARY` where the platform has it (`getattr(os, "O_BINARY", 0)` added to the flags), so the bytes written are the bytes of the payload: every line ends with LF alone, on Windows as on Linux. The acceptance case `test_r088_r2_every_line_the_program_writes_ends_with_lf_alone` reads the raw bytes.
2. **The last `Paused:` line decides (a defeated safety mechanism; convergent: Review A B2, the security review).** `paused_in_flight` in `loop-guard.py` reads the **last** line of `run/supervisor/in-flight.md` that begins `Paused:` (the same pattern `field` uses, its last match), never the first, and applies to it the tests it applies today (`names_a_wait`, and the words `no`, `not`, `false`, `off`, `resumed`, `ended`, `cleared` read as no wait). So `Paused: resumed` written after a pause lifts it, and a later `Paused: <reason>` sets it again. A stamped line (`<stamp> Paused: ...`) is no `Paused:` line, as today. Add a `test_r088_` case to `tests/test_loop_guard.py` with a log holding a pause and then `Paused: resumed`, read as no wait, and one holding a resume and then a pause, read as that pause.
3. **Two sources are two sources (behaviour; Review A SF1).** `--file` given at all, even as an empty string, counts as a source: `args.file is not None`. `--file ""` alone is refused as no text; beside a text it is refused as two sources.
4. **Only `--pass` writes a pass line (data integrity; convergent: Review A, the security review).** A text, or the first line of a `--file` text, whose first word is `PASS` in any letter case (the word alone or followed by white space) is refused with exit 2 and nothing written, the reason naming `--pass`. A word that only begins with those letters (`PASSED`, `passing`) is not refused.
5. **The log is written only inside the Workspace (security; convergent: Review A, the security review).** Before it creates or opens anything, the program refuses, exit 2 and nothing written, where `run/`, `run/supervisor/` or `run/supervisor/in-flight.md` exists and is a symbolic link or a junction (round 1's link test, made to work on every Python 3 this project runs, correction 8), or where the real path of `run/supervisor/` does not lie under the real path of the Workspace. A folder it creates is created with no link in its way.
6. **The file read is the file checked (security; Review A SF2, the security review).** `--file` opens the real path its checks resolved (round 1's `file_real`), never `os.path.abspath(given)`, with `O_NOFOLLOW` where the platform has it and `O_BINARY` where it has it; after the open, `os.fstat` of the open file must name the same file as `os.stat` of that real path (`st_dev` and `st_ino`, compared where both are non-zero) and the file must have one link (`st_nlink == 1`), else exit 2 and nothing written.
7. **The lock never blocks a reader (other; convergent: Review A, the security review).** On Windows the lock is taken on one byte far past any log's end (the file position set to `2**31` before `msvcrt.locking`, and set there again before the unlock), never byte 0, so a reader such as the loop guard is never refused while a run appends. The lock stays bounded at 10 seconds as in round 1. On POSIX keep round 1's lock.
8. **Every byte is written or none is claimed (data integrity; security review).** The append writes the whole payload: `os.write` repeated until every byte is written, a write of zero bytes or an error ending the run with exit 1 and the message `in-flight: INCOMPLETE - <n> of <m> bytes written`, never `REFUSED` and never the printed line. The test of a link: `os.path.isjunction` where it exists, else the reparse-point attribute of `os.lstat` (`st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT` on Windows), so the program never ends in an `AttributeError` on a Python before 3.12.
9. **One stray line (other; Review A note).** Remove the extra blank line round 1 left at the end of `bridge_env.py`; the file ends with one line break.

## Context
The acceptance file `tests/test_program_in_flight.py` gained eight cases after the line `# Round 2 (TASK-068-r2)`: the raw bytes hold no CR; a later `Paused:` line lifts or replaces an earlier one, read through the loop guard's own `paused_in_flight`; `--file ""` beside a text refused; a free text and a `--file` text whose first word is `PASS` (three spellings) refused; `run/` and `run/supervisor/` each made a junction (or a link where a junction cannot be made) to a folder outside the Workspace, refused with no `.md` written there. On round 1's code: "8 failed, 37 deselected".

Threat model: as round 1's brief (`docs/INVENTORY.md` Decisions, "The bridge's threat model as a whole"). The log decides, through the loop guard, whether the supervisor may end its turn: what the log holds is a safety input, and a link or junction under the Workspace's `run/` is outside input, which needs no privilege on Windows.

## Acceptance criteria
- [ ] Every test in `tests/test_program_in_flight.py` passes, the link case of round 1 skipped where the account cannot create a link, and every test of round 1's Done list passes.
- [ ] Corrections 1 to 9 met, each named in the report with its function and lines.
- [ ] Round 1's requirements and choices stand where this brief does not change them.
- [ ] Every line added ASCII; no option, environment variable or dependency.

## Constraints
Round 1's brief's Constraints all stand. Mutations by hand, in process, each reverted, listed by label with the pytest line that shows a test failing, else `not run`: (H1) `O_BINARY` dropped from the append's flags; (H2) `paused_in_flight` reading the first `Paused:` line again; (H3) `bool(args.file)` restored; (H4) the `PASS` refusal dropped; (H5) the link test of `run/supervisor/` dropped. Prefer the smallest change; refactor nothing else.

## Done
Your report is `handoff/TASK-068-r2-report.md`, written as you go, in round 1's form (files changed, the report itself among them; summary; each correction in one sentence with the function and lines; every command below with its output, verbatim, in fenced blocks, each pytest summary line quoted; the mutations H1 to H5, each with the FAILED line and the summary line; a last section headed exactly `Assumed, not verified`). It names no computer path: `<Workspace>` for the repository folder, `<tmp>` for a temporary folder.

Run these from the Workspace root, in this order, after your last edit, each in the foreground, with no `PYTHONPATH` or other environment change; run them again in order if you edit anything after them, and quote the last run:
1. `git status --short`
2. `python tools/dump-cli.py`
3. `python tools/dump-cli.py --check` (expect exit 0)
4. `python tools/make-manifest.py`
5. `git restore bridge/cursor-bridge/VERSION`
6. `python -m pytest -p no:cacheprovider -q -rs tests/test_program_in_flight.py tests/test_dump_cli.py tests/test_allowlist.py tests/test_loop_guard.py`
7. `python -m pytest -p no:cacheprovider -q tests/test_bridge_run.py tests/test_pace_report.py tests/test_release_s_launcher.py`
8. `python -m pytest -p no:cacheprovider -q tests/test_install_check.py tests/test_tests_windowless.py`
9. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` (expect `RESULT: SOURCES MATCH`)
10. `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks`
11. `python -c "open('bridge/cursor-bridge/in-flight.py','rb').read().decode('ascii'); open('bridge/cursor-bridge/loop-guard.py','rb').read().decode('ascii'); print('ascii ok')"` (expect `ascii ok`)
12. `git rev-parse HEAD` and `git status --short` (`bridge/cursor-bridge/VERSION` must not be listed; if it is, report it)

Every pytest summary line quoted verbatim; never restate a count in prose. Your last message is the summary and the report file's path, and nothing follows it.
