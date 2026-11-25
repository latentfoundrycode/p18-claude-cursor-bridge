---
record: brief
header: 1
id: "TASK-087b"
round: 2
satisfies: [R-109]
scope: ["bridge/cursor-bridge/session-start.py", "bridge/cursor-bridge/MANIFEST.json", "tests/test_improve_digest_parts.py", "tests/test_session_start.py", "tests/test_loop_text_pace.py", "tests/test_a5_followups.py", "tests/test_release_s_budgets.py", "docs/cli-reference.json", "docs/CLI_REFERENCE.md", "docs/BUILDER_NOTES.md", "handoff/TASK-087b-r2-report.md"]
merge_unit: null
blocking_class: null
---
# TASK-087b, round 2: each part within its numbers, in the hook and in the tests (R-109)

Round cause: behaviour

## Objective
Round 1 (your run on the checkpoint, its change now committed on this branch) met most of `handoff/TASK-087b.md`, but the gate's reviewer rejected it on two points of the brief's letter, and the security audit named the first of them too: a cut second part runs two characters past `MAX_OUTPUT` (R4), and the three cap tests hold the whole digest at 10,500 but no part at 8,800 (R7). The reviewer also named smaller deviations: a false placeholder where the first part is empty, a repeated marker line printed inside the second part, a line feed written where nothing should be, the docstring's `--part all`, and the report's quoting. This round fixes them. The supervisor has added red acceptance cases to `tests/test_improve_digest_parts.py` (committed before this brief; listed under Context). **Read `handoff/TASK-087b.md` whole first: every requirement, limit, constraint and Done rule there holds for this round, except where this brief changes it.** Your report is `handoff/TASK-087b-r2-report.md`.

Satisfies: R-109

## Scope
Files and directories you may create or modify:
- bridge/cursor-bridge/session-start.py
- bridge/cursor-bridge/MANIFEST.json
- tests/test_improve_digest_parts.py
- tests/test_session_start.py
- tests/test_loop_text_pace.py
- tests/test_a5_followups.py
- tests/test_release_s_budgets.py
- docs/cli-reference.json
- docs/CLI_REFERENCE.md
- docs/BUILDER_NOTES.md
- handoff/TASK-087b-r2-report.md

Limits on these paths: those of `handoff/TASK-087b.md` (its Scope section), with these changes. In `session-start.py` you may change your round-1 helpers (`split_digest`, `digest_part_2`, `DIGEST_PART_MARK`), `digest_part`'s placeholder for an empty first part, the label passed to `cap` for the second part, the end of `main()` where nothing is written, and the module docstring; `cap` itself and `MAX_OUTPUT` stay as they are (the acceptance file pins the note's place at `MAX_OUTPUT - 90`). In the three cap tests (`tests/test_session_start.py`'s `test_digest_is_at_the_head_and_within_what_a_compaction_keeps`, `tests/test_loop_text_pace.py`'s `test_r042_the_digest_stays_within_its_cap_with_every_rule_number`, `tests/test_a5_followups.py`'s `test_the_changelog_entry_exists_and_the_digest_is_unchanged_in_size`) you may change the cap assertion you changed in round 1 and add, inside the same test function, the lines that split the measured digest at the marker line and assert each part (Requirement 2); nothing else in those files. `tests/test_release_s_budgets.py`: the same docstring sentence as round 1. `tests/test_improve_digest_parts.py` is the supervisor's: **do not edit it.** `settings.bridge.json` is done and is now outside Scope. MANIFEST and the command reference change only by their tools.

Do not modify anything else.

## Out of scope
As in `handoff/TASK-087b.md` (Out of scope), unchanged, and `bridge/cursor-bridge/settings.bridge.json`. `handoff/TASK-087b.md` and `handoff/TASK-087b-r1-report.md` are read, never edited.

## Context
**Where round 1 stands.** Your round-1 change is committed on the branch (the commit before the supervisor's round-2 cases and this brief). You work in the same worktree, `Worktrees/TASK-087b`, beside another increment's merge in the main checkout; you do not commit (as in round 1). Everything else round 1 did stays as it is unless a requirement below changes it.

**The new acceptance cases** (appended to `tests/test_improve_digest_parts.py`, each docstring naming its requirement, its finding and its mutation label):
- `test_r2_a_cut_part_never_passes_max_output[digest]`, `[digest-2]` (Requirement 1, K5)
- `test_r2_each_cap_test_holds_the_whole_and_each_part[tests/test_session_start.py]`, `[tests/test_loop_text_pace.py]`, `[tests/test_a5_followups.py]` (Requirement 2)
- `test_r2_a_marker_first_never_says_no_digest_was_found` (Requirement 3, K6)
- `test_r2_a_repeated_marker_line_is_never_printed` (Requirement 4, K7)
- `test_r2_the_second_part_without_the_marker_writes_nothing_at_all` (Requirement 5, K8)

**The supervisor's red run** (the acceptance file on round 1's code, through the launcher): `7 failed, 15 passed in 3.01s`, the seven being every case listed above but `test_r2_a_cut_part_never_passes_max_output[digest]`, which passes on round 1 (the first part's label fits) and pins that answer. Each fails for the defect it names: `assert 9802 <= 9800` for the cut second part, the words "no digest found" printed for an empty first part, a marker line printed in the second part, `b'\r\n'` written where nothing is printed, and no `8800` in each of the three cap tests.

**The arithmetic of Requirement 1.** `cap` keeps `limit - 90` characters and adds the note `"\n[%s cut at %d characters by the hook's cap; re-read it in the file]" % (what, limit)`. With `limit` 9800 the note is 68 characters plus `len(what)`, so a label of at most 22 characters keeps the cut part within `MAX_OUTPUT`: "the section pointers" (20) and "the digest" (10) fit; round 1's "the digest's second part" (24) does not. The second part's label must still name the second part as the acceptance file's pattern `SECOND` reads it (for example "the second part", "digest part 2").

## Requirements
These change or sharpen `handoff/TASK-087b.md`'s R1, R2, R4, R6 and R7; every other requirement there stands as written.

1. **R4: a cut part stays within `MAX_OUTPUT`.** The label `main()` passes to `cap` for the second part is at most 22 characters and names the second part (Context, the arithmetic). No part's output, header, text and note together, is longer than `MAX_OUTPUT` characters.
2. **R7: each cap test holds the whole and each part.** In each of the three cap tests (Scope), the assertion holds the whole slice it measured at 10,500 characters, and new lines in the same test split the digest at the line `<!-- digest:part -->` (by lines, as the acceptance file's `file_parts` does) and assert each part's text, stripped, at most 8,800 characters, with message words that say which part and which number. The maintainer's comment above the digest says these three tests hold the same two numbers; after this round it is true. The old number `9500` stands in none of them.
3. **R1: an empty first part is never called a missing digest.** Where the marker line stands first in the digest, so the first part's text is empty, `--part digest` prints its header and a placeholder that is true (that the first part is empty and the digest continues in the second part, or the like), never "(no digest found in supervisor.md; ...)", which stays for a digest that is truly missing.
4. **R2: no marker line is printed.** Where the marker line stands more than once, the digest splits at the first; every later marker line is dropped from the second part's text, the text around it kept in order. No part prints a marker line.
5. **R2: nothing is written where nothing is printed.** Where no part is to be printed (`--part digest-2` on a digest without the marker), the hook writes no byte, not a line feed, as outside a bridge project.
6. **R6: the docstring.** The module docstring names `--part all` and says what it prints (the pointers, the first part, the second part where the marker stands), names no single "both" for three things, and the sentence "It prints nothing outside a bridge project ..." reads whole (round 1 left a line break inside it). It stays ASCII; the command reference is regenerated from it.
7. **R7, the budgets docstring.** `tests/test_release_s_budgets.py`'s sentence names the files that hold the two caps as the maintainer's comment above the digest does (`tests/test_improve_digest_parts.py`, `tests/test_session_start.py`, `tests/test_loop_text_pace.py`, `tests/test_a5_followups.py`), not "the four tests named in TASK-087b".

## Acceptance criteria
- [ ] Every test in `tests/test_improve_digest_parts.py` passes, unedited, the round-2 cases above among them; every case that passed on round 1 still passes.
- [ ] Every test in the files of `handoff/TASK-087b.md`'s Done steps 6 and 7 passes; the files you edited changed only as this brief's Scope allows.
- [ ] Requirements 1 to 7 hold.
- [ ] `handoff/TASK-087b.md`'s remaining acceptance criteria (dump-cli `--check`, MANIFEST regenerated, `RESULT: SOURCES MATCH`, VERSION unchanged and unlisted, ASCII only, no dependency, no traceback, exit 0 always) hold.

## Constraints
All of `handoff/TASK-087b.md`'s Constraints hold, with these changes:
- **No scratch test this round.** Every count the report gives is read from a pytest line or an assertion message of a test in Scope (the three cap tests' new messages print each part's count where you make them print it on failure; the acceptance file's `test_r109_the_whole_digest_is_at_most_10500_and_each_part_at_most_8800` passes silently). Where a count can be read from no output, write `not read from an output` beside it; never compute it by a program of your own.
- **Mutation: name the code points, run nothing.** In the report, for each of K1 to K4 (as `handoff/TASK-087b.md` names them) and for these new labels, the function and the line(s) as the file stands after your change, and the acceptance test id you expect to catch it: K5 a cut note longer than the room the cap leaves; K6 a placeholder that says no digest was found beside a digest; K7 a later marker line printed inside a part; K8 a part with nothing to print writing a line feed.
- **Report verbatim.** Round 1's report elided Done step 9's output with "...", gave the checkpoint's failing ids in prose, did not quote the skips' `-rs` lines nor step 11's diff, and left `Assumed, not verified` empty although the brief named examples that applied. This round: every command's output is pasted as printed, whole (step 9 above all, as R8 asks); every failing id one per line; every skip with the `-rs` line that names it; an empty output written `(no output)`; and the `Assumed, not verified` section lists each fact the change relies on that neither brief settled (the brief's examples among them: what each part prints at each marker placement, whether the host counts in characters or bytes).

## Done
Your report is `handoff/TASK-087b-r2-report.md`, written as you go, holding everything `handoff/TASK-087b.md`'s Done section lists (with "R1 to R9" read as this round's Requirements 1 to 7, each in one line naming its function and lines, and for Requirements 1, 3 and 5 one output line as a test prints it), and ending with a section headed exactly `Assumed, not verified`.

Run `handoff/TASK-087b.md`'s Done commands 1 to 12, exactly as written there, from the Workspace root (this worktree's root), each on its own, synchronously, in that order (steps 1 and 2 before your first edit; 3 to 12 after your last), and quote each with its output verbatim.

Your last message is the summary and the report file's path, and nothing follows it.
