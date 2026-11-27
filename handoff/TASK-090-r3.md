---
record: brief
header: 1
id: "TASK-090"
round: 3
satisfies: [R-112]
scope: ["bridge/cursor-bridge/bridge-run.py", "bridge/cursor-bridge/MANIFEST.json", "docs/cli-reference.json", "docs/CLI_REFERENCE.md", "docs/BUILDER_NOTES.md", "handoff/TASK-090-r3-report.md"]
merge_unit: null
blocking_class: null
---
# TASK-090 (round 3): The launcher's small repairs

Round cause: brief error and records. Round 2's work stands and meets its R2. The security audit (advisory, behaviour: the docstring says the owner's files under the home folder are not found through it, but every stripped run's home folder holds a `.cursor` link to the owner's real `~/.cursor`, and git reads the owner's `~/.gitconfig` through an include; round 2's brief left both out, `bridge-run.py` lines 105 to 110) and Review A (behaviour: the usage text leaves out that the run keeps the owner's rights and that cursor-agent's login, or the owner's APPDATA where its link cannot be made, still leads to the owner's folders, and its "otherwise" reads as if cursor-agent runs got no folders of their own, `bridge-run.py` line 169; records: the report describes M5 as the opposite mutation again and cites two parametrized tests by their bare names, `handoff/TASK-090-r2-report.md` lines 28, 29 and 32) send it back. This is the last round the ceiling gives.

Satisfies: R-112

## Objective
Round 1's and round 2's work stand in the tree. This round completes the help text and corrects the report. Read `handoff/TASK-090.md` (round 1's brief) and `handoff/TASK-090-r2.md` (round 2's) whole first: their Context, Requirements, Constraints and Done stand, except where this brief changes them. Read `handoff/TASK-090-r2-report.md`, your round-2 report.

## Scope
Files and directories you may create or modify:
- bridge/cursor-bridge/bridge-run.py
- bridge/cursor-bridge/MANIFEST.json
- docs/cli-reference.json
- docs/CLI_REFERENCE.md
- docs/BUILDER_NOTES.md
- handoff/TASK-090-r3-report.md

Do not modify anything else.

Limits on these paths: as round 1's brief. In `bridge-run.py`, change only the module docstring and the text `usage()` writes. `tests/test_improve_launcher_small.py` is the supervisor's acceptance file: read it whole and run it, **do not edit it**. Round 3 added `test_r112_the_help_names_what_the_home_folder_still_reaches` and corrected the module docstring's bullets.

## Out of scope
As round 1's and round 2's briefs. `bridge/cursor-bridge/bridge_env.py` stays unchanged: the text is corrected to match the code.

## Context (this round; the earlier rounds' Context stands)
- **What else a stripped run's home folder reaches** (`bridge/cursor-bridge/bridge_env.py`). `agent_home` (from line 129): the run's home folder holds one link, `.cursor`, to the owner's real `~/.cursor` (the Cursor CLI's account and state), and the empty folders of `SKELETON`. `write_gitconfig` (from line 258) and `stripped_env` (line 323): git reads the bridge's own global config file, which includes the owner's `~/.gitconfig` and resets the credential helper list, so the owner's git identity and settings apply and no credential helper hands out the owner's login.
- **The round-3 test.** `test_r112_the_help_names_what_the_home_folder_still_reaches` lowercases each text and collapses its whitespace. It requires `owner's rights` and `login` in both the usage text and the docstring, and in the docstring a `.cursor` not followed by `-` or a word character (so `~/.cursor-bridge` does not count) and `.gitconfig`. Round 1's and round 2's help-text tests still hold.
- **Expected on round 2's code**, by the supervisor's run: `test_r112_the_help_names_what_the_home_folder_still_reaches` red, every other test green. Done step 2 records the real split.

## Requirements (this round; the earlier rounds' Requirements stand where these do not change them)
R1. **The docstring names everything that still leads to the owner's folders.** Beside what round 2 wrote, the docstring says that the run's home folder holds a `.cursor` link to the owner's `~/.cursor`, and that git reads the owner's `~/.gitconfig` through an include (with the credential helper list reset). Its sentence that the owner's files "are not found through those variables" is corrected so that it is true with these two named (for example: the owner's other files there are not found through those variables).
R2. **The usage text says the essentials.** The usage text says, more briefly than the docstring if you like: every cursor-agent run is stripped and so is a `--strip` run; a stripped run gets its own home folder, APPDATA and LOCALAPPDATA but still runs with the owner's rights; the tools' caches and cursor-agent's login (by a link, or the owner's APPDATA where the link cannot be made) still lead to the owner's folders; a key file is refused for the driver kind, so a driver that needs the owner's key file runs unstripped, under a recorded decision. Drop the "otherwise" wording: cursor-agent runs get the same folders of their own. Round 1's added clause ("use --kind driver for programs under run/supervisor/ or the installed mutation engine") may stay. It still starts `usage: bridge-run.py`, still names `--strip`, and still returns 2.
R3. **The report is exact.** In `handoff/TASK-090-r3-report.md`, every test id you cite is a collected id, copied from pytest's output: a parametrized test is cited with its bracket, for example `test_r112_a_run_ended_at_its_limit_leaves_no_pid_file[test]`. M5 is described exactly as round 2's brief words it: the hint's condition keeps only `kind == "test"` (the `--key-file` and resolver conditions dropped), which `test_r112_another_program_s_refusal_names_no_kind` catches. Done step 1's `git status --short` runs before your first edit and is quoted as printed.

## Constraints
As round 1's brief. **Mutation: name the code points, run nothing**: M1 to M9 as round 2's brief words them, each with its function and lines as the file stands after your change and the collected test id that catches it, or a statement that no test of the files Done names would.

## Done
As round 1's brief, with the report at `handoff/TASK-090-r3-report.md` (same sections; Requirements listed as round 1's 1, 2, 3 and 5, round 2's R2 and this round's R1 to R3; mutation labels M1 to M9). Steps 1 to 13 as round 1's brief words them; in step 2, quote the summary line and the failing ids as they stand on round 2's code.

Your last message is the summary and the report file's path, and nothing follows it: the supervisor reads only the last message, and a message printed earlier and then followed by more work is lost.
