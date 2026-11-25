---
record: brief
header: 1
id: "TASK-086b"
round: 3
satisfies: [R-107]
scope: ["bridge/cursor-bridge/bridge-run.py", "bridge/cursor-bridge/MANIFEST.json", "tests/test_improve_roster_launch.py", "docs/cli-reference.json", "docs/CLI_REFERENCE.md", "docs/BUILDER_NOTES.md", "handoff/TASK-086b-r3-report.md"]
merge_unit: null
blocking_class: null
---
# TASK-086b, round 3: the branch is read as git prints it, never a traceback (R-107)

Round cause: behaviour

## Objective
Round 2 (committed on this branch) passed the gate's Review A and security audit, and the cross-family Review B rejected it on one finding: `branch_of` reads `git rev-parse --abbrev-ref HEAD` as text in the system's code page, so on a branch whose name holds characters outside that code page the read raises, and the two review refusals, which call `branch_of` outside any `try`, end the launch with a traceback (exit 1) instead of judging it. On the checkpoint the family refusal called `branch_of` inside its `try`, so this is the increment's own regression. This round reads the branch as git prints it and keeps every launch free of a traceback. The supervisor has added red acceptance cases to `tests/test_improve_roster_launch.py` (committed before this brief; listed under Context). **Read `handoff/TASK-086b.md` and `handoff/TASK-086b-r2.md` whole first: every requirement, limit, constraint and Done rule there holds for this round, except where this brief changes it.** Your report is `handoff/TASK-086b-r3-report.md`.

Satisfies: R-107

## Scope
Files and directories you may create or modify:
- bridge/cursor-bridge/bridge-run.py
- bridge/cursor-bridge/MANIFEST.json
- tests/test_improve_roster_launch.py
- docs/cli-reference.json
- docs/CLI_REFERENCE.md
- docs/BUILDER_NOTES.md
- handoff/TASK-086b-r3-report.md

Limits on these paths: in `bridge-run.py`, the function `branch_of` (a widening: it was outside round 1's and round 2's Scope) and, where Requirement 2 needs it, the two lines in `_deviation_allows_builder_review` and `review_family_refusal` that read the branch; nothing else in the file. `tests/test_improve_roster_launch.py` is the supervisor's: **do not edit it.** MANIFEST and the command reference change only by their tools (the help text does not change, so the reference should come out unchanged).

Do not modify anything else.

## Out of scope
As in `handoff/TASK-086b.md` (Out of scope), unchanged, and `tests/test_hotfix25a_roster_launcher.py`, which round 3 does not touch. `handoff/TASK-086b.md`, `handoff/TASK-086b-r2.md` and both earlier reports are read, never edited.

## Context
**Where round 2 stands.** Your round-2 change is committed on the branch, accepted by the supervisor, and is the base of this round; the supervisor's commits since are the review files under `run/review/` (Review B's input, removed before the merge) and the round-3 cases. Everything round 2 did stays as it is.

**The finding** (Review B, round 1, in its words reduced): `branch_of` runs `git -C <folder> rev-parse --abbrev-ref HEAD` with `text=True` and no encoding, so Python decodes git's output in the system's ANSI code page; git prints a ref name as the bytes it stores, UTF-8 on this platform. Where those bytes do not decode (code page 1252 leaves 0x81, 0x8D, 0x8F, 0x90 and 0x9D undefined), the decode raises; `branch_of` catches only `OSError` and `subprocess.TimeoutExpired`, and `_deviation_allows_builder_review` and `review_family_refusal` call it outside any `try`. The launch prints a traceback and exits 1: the stand-in never runs and no row is written, so nothing unreviewed runs, but `handoff/TASK-086b.md` asks for a refusal or a judgement, never a traceback, on git's output (its R10).

**The new acceptance cases** (appended to `tests/test_improve_roster_launch.py`; each docstring names its requirement, the finding and the mutation label M21, the branch read in the code page or not at all):
- `test_r3_a_branch_name_outside_the_code_page_is_read_and_judged` (a grok row on the branch refuses a grok review by name; a GPT review runs and its row names the branch)
- `test_r3_a_deviation_on_such_a_branch_opens_the_builder_models_review` (the builder-model exception reads the same branch)
- `test_r3_a_builder_launch_on_such_a_branch_writes_its_name_and_both_keys` (a builder row on that branch: its name, `start_commit`, `clean`)

The branch name they use is `task-` followed by the five characters U+0101, U+010D, U+010F, U+0110 and U+011D, whose UTF-8 bytes include each byte code page 1252 leaves undefined.

**The supervisor's red run** (the round-3 cases on round 2's code, through the launcher, `-k test_r3_`, which also selects round 1's six R3 cases): `3 failed, 6 passed, 95 deselected in 14.57s`, the three being the new cases, each launch ending in the traceback Review B named (`UnicodeDecodeError: 'charmap' codec can't decode byte 0x81 in position 6` in the reader thread, then `AttributeError: 'NoneType' object has no attribute 'strip'` in `branch_of`).

## Requirements
1. **The branch is read as git prints it.** `branch_of` runs the same git command (a list of arguments, windowless, bounded by `bridge_env.GIT_TIMEOUT`), reads its output as bytes and decodes it as UTF-8 with replacement (`errors="replace"`), so no output of git can make it raise; it returns the stripped name where git exits 0 and `None` otherwise, as now. Any exception while it runs (a decode, an `OSError`, a timeout, anything else) returns `None`; `branch_of` never raises.
2. **No traceback from the two refusals' branch read.** Where `branch_of` returns `None` inside a repository, the two refusals judge as they already do for a branch that cannot be read (the set cannot be read: every review refused, exit 125, the refusal naming the cause). Add nothing where that already holds; if a path remains on which reading the branch can raise in either refusal, catch it there and refuse the review (exit 125, the refusal naming the cause and `git`), never letting it through.
3. **Every other caller unchanged in behaviour.** The brief-rule check and the run log's branch (the other two callers of `branch_of`) get the same name for an ASCII branch as before, and for a branch outside the code page the name as git prints it (the third new case reads the row).

## Acceptance criteria
- [ ] Every test in `tests/test_improve_roster_launch.py` passes, unedited, the round-3 cases among them; every case that passed on round 2 still passes.
- [ ] Every test in `tests/test_hotfix25a_roster_launcher.py` and in the files of `handoff/TASK-086b.md`'s Done steps 7 and 8 passes, unedited.
- [ ] Requirements 1 to 3 hold.
- [ ] `handoff/TASK-086b.md`'s remaining acceptance criteria (dump-cli `--check`, MANIFEST regenerated, `RESULT: SOURCES MATCH`, VERSION unchanged and unlisted, windowless-check, ASCII only, no dependency, no traceback) hold.

## Constraints
All of `handoff/TASK-086b.md`'s and `handoff/TASK-086b-r2.md`'s Constraints hold, with these changes:
- **Mutation: name the code points, run nothing.** In the report, for M21 (the branch read in the code page or not at all), the function and the line(s) as the file stands after your change, and the acceptance test ids you expect to catch it.
- **Report verbatim**, as round 2's brief asks: every command's output pasted as printed, every failing id one per line, an empty output written `(no output)`.

## Done
Your report is `handoff/TASK-086b-r3-report.md`, written as you go, holding everything `handoff/TASK-086b.md`'s Done section lists (with "R1 to R11" read as this round's Requirements 1 to 3, each in one line naming its function and lines), and ending with a section headed exactly `Assumed, not verified`.

Run `handoff/TASK-086b.md`'s Done commands 1 to 14, exactly as written there, from the Workspace root, each on its own, synchronously, in that order (steps 1 and 2 before your first edit; 3 to 14 after your last), and quote each with its output verbatim.

Your last message is the summary and the report file's path, and nothing follows it.
