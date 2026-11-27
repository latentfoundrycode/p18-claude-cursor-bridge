---
record: brief
header: 1
id: "TASK-090"
round: 2
satisfies: [R-112]
scope: ["bridge/cursor-bridge/bridge-run.py", "bridge/cursor-bridge/MANIFEST.json", "docs/cli-reference.json", "docs/CLI_REFERENCE.md", "docs/BUILDER_NOTES.md", "handoff/TASK-090-r2-report.md"]
merge_unit: null
blocking_class: null
---
# TASK-090 (round 2): The launcher's small repairs

Round cause: round 1's work stands and meets round 1's Requirements 1, 2, 3 and 5; Review A (behaviour: the help text of Requirement 4, in `usage()` and the module docstring, says a stripped run "sees none of the owner's files under APPDATA, LOCALAPPDATA or the home folder", which `bridge_env.stripped_env` does not do: it passes the tools' caches and cursor-agent's login link through to the owner's folders, and keeps the owner's APPDATA where that link cannot be made; the wording was the brief's, corrected here) sends it back, with the security audit's advisory of the same finding (`bridge-run.py` lines 103 to 104 and 165). Also from Review A: the usage text leaves out that every cursor-agent run is stripped and that a key file is refused for the driver kind (behaviour, `bridge-run.py` line 165); the hint names `--kind driver` for a test launch that carries `--key-file`, which the driver kind refuses (behaviour, `bridge-run.py` line 3401); the report cites three test ids that do not exist, describes M5 as a different mutation, and shortens a quoted output line (records, `handoff/TASK-090-r1-report.md` lines 25 to 31 and 150).

Satisfies: R-112

## Objective
Round 1's work stands in the tree: the pid file removed before `killer()` in the limit branch that is not a watch, the encoding default for the driver and test kinds, the refusal's hint, and the help text. This round corrects the help text so that it claims no more than the code gives, makes the hint exact, and corrects the report. Read `handoff/TASK-090.md` (round 1's brief) whole first: its Context, its Requirements, its Constraints and its Done stand, except where this brief changes them. Read `handoff/TASK-090-r1-report.md`, your round-1 report.

## Scope
Files and directories you may create or modify:
- bridge/cursor-bridge/bridge-run.py
- bridge/cursor-bridge/MANIFEST.json
- docs/cli-reference.json
- docs/CLI_REFERENCE.md
- docs/BUILDER_NOTES.md
- handoff/TASK-090-r2-report.md

Do not modify anything else.

Limits on these paths: as round 1's brief. `tests/test_improve_launcher_small.py` is the supervisor's acceptance file: read it whole and run it, **do not edit it**. Round 2 added `key_file`, a `flags` parameter to `launch` and `probe_suite`, and four tests: `test_r112_a_key_file_s_value_counts_as_the_caller_s`, `test_r112_a_test_launch_with_a_key_file_names_no_driver_kind`, `test_r112_a_supervisor_program_under_another_kind_gets_no_hint` and `test_r112_the_help_claims_no_more_than_the_strip_gives`. `tests/test_program_review_rows.py` is unchanged and still not yours.

## Out of scope
As round 1's brief. `bridge/cursor-bridge/bridge_env.py`, including `stripped_env`, stays unchanged: the text is corrected to match the code, never the code to match a text.

## Context (this round; round 1's Context stands)
- **What `stripped_env` does** (`bridge/cursor-bridge/bridge_env.py`, from line 285). It points `HOME` and `USERPROFILE` at the run's own home folder, and `APPDATA` and `LOCALAPPDATA` at folders under it. It does not confine the run: the child still runs with the owner's rights. Before the re-pointing, it passes through to the owner's real folders, by each tool's own variable where that is unset and the folder exists: `CACHES` (the Hugging Face, Torch and Puppeteer caches under the owner's home folder) and `APP_CACHES` (lines 248 to 255: the uv cache and uv's Python installs, the pip cache, the Python user base, the npm cache, the Yarn cache, Playwright's browsers and the Go build cache, under the owner's `APPDATA` or `LOCALAPPDATA`). `APP_LINKS` (line 244) links `%APPDATA%\Cursor` into the run's `APPDATA`, so cursor-agent finds its login, and where that link cannot be made the run keeps the owner's `APPDATA` (lines 239 to 243 and the end of the function).
- **The help-text tests.** Round 1's test still looks, in the usage text and the docstring, for each of `appdata`, `localappdata`, `home folder`, `unstripped`, `key file`, `recorded decision` and `driver`. Round 2's `test_r112_the_help_claims_no_more_than_the_strip_gives` lowercases each text and collapses its whitespace, then requires `cache`, `a key file is refused` and `cursor-agent` in both, and neither `none of the owner's files` nor `sees none of the owner` in either.
- **The hint.** Round 1 added, at lines 3401 and 3402, `if kind == "test" and resolve_driver_program(cmd, folder) is not None:` and the line `bridge-run: refused - use --kind driver for this command`. `flags` holds the launcher's own words before `--`; the driver kind refuses `--key-file` (`DRIVER_KEYFILE_REFUSE`, line 132, checked in the driver branch at lines 3392 to 3394).
- **Expected on round 1's code**, by the supervisor's run: `test_r112_a_test_launch_with_a_key_file_names_no_driver_kind` and `test_r112_the_help_claims_no_more_than_the_strip_gives` red; the other two round-2 tests green (controls that must stay green). Done step 2 records the real split.

## Requirements (this round; round 1's Requirements 1, 2, 3 and 5 stand where these do not change them)
R1. **The help text claims no more than the code gives** (replaces round 1's Requirement 4). Both `usage()` and the module docstring say, in ASCII:
   - A stripped run (`--strip`, and every `cursor-agent` run) gets a home folder, an `APPDATA` and a `LOCALAPPDATA` of its own, so the owner's files there are not found through those variables; it still runs with the owner's rights. The tools' caches the bridge passes through (the docstring names them: uv, pip, the Python user base, npm, Yarn, Playwright, Go, Hugging Face, Torch and Puppeteer) and cursor-agent's login under `APPDATA` (by a link, or the owner's `APPDATA` itself where the link cannot be made) still lead to the owner's folders.
   - A key file is refused for the driver kind, so a driver that needs the owner's key file is launched unstripped, under a recorded decision.

   The usage text may say this more briefly than the docstring but must hold every word both help-text tests look for (Context). The usage text still starts `usage: bridge-run.py`, still names `--strip`, and still returns 2. Round 1's added usage clause ("use --kind driver for programs under run/supervisor/ or the installed mutation engine") may stay. Write no `BRIDGE_` name other than the two existing ones.
R2. **The hint is exact.** The `--kind driver` hint of round 1's Requirement 3 is given only where the launch's own words before `--` hold no `--key-file`, as well as the conditions round 1 set. A refused test launch that carries `--key-file` is refused exactly as on the checkpoint, naming no kind.
R3. **The report is exact.** In `handoff/TASK-090-r2-report.md`, every test id you cite is one that pytest collects (copy ids from pytest's output, never from memory). Each mutation label is described as this brief and round 1's brief word it. Every quoted output line is whole, never shortened with `...`.

## Constraints
As round 1's brief. **Mutation: name the code points, run nothing**: for each label below, the report gives the function and lines (as the file stands after your change) and the collected test id you expect to catch it, or says that no test of the files Done names would.
  - M1 to M7: as round 1's brief words them. M5 is "the `--kind driver` hint is given for every refused test launch", that is, the hint's condition keeps only `kind == "test"`.
  - M8: the `--key-file` condition of R2 is dropped.
  - M9: the help words are removed from the usage text only.

## Done
As round 1's brief, with the report at `handoff/TASK-090-r2-report.md` (same sections, Requirements listed as round 1's 1, 2, 3 and 5 and this round's R1 to R3, mutation labels M1 to M9). Steps 1 to 13 as round 1's brief words them; in step 2, quote the summary line and the failing ids as they stand on round 1's code.

Your last message is the summary and the report file's path, and nothing follows it: the supervisor reads only the last message, and a message printed earlier and then followed by more work is lost.
