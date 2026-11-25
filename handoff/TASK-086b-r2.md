---
record: brief
header: 1
id: "TASK-086b"
round: 2
satisfies: [R-107]
scope: ["bridge/cursor-bridge/bridge-run.py", "bridge/cursor-bridge/MANIFEST.json", "tests/test_improve_roster_launch.py", "tests/test_hotfix25a_roster_launcher.py", "docs/cli-reference.json", "docs/CLI_REFERENCE.md", "docs/BUILDER_NOTES.md", "handoff/TASK-086b-r2-report.md"]
merge_unit: null
blocking_class: null
---
# TASK-086b, round 2: the launcher's review refusals fail closed in every path (R-107)

Round cause: security

## Objective
Round 1 (your run on the checkpoint, its diff now committed on this branch) met most of `handoff/TASK-086b.md`, but both of the gate's reviewers rejected it on the same three defects, each a path where the launcher lets a review run that the brief says it must refuse, and named five smaller deviations from the brief's letter. This round fixes all eight in `bridge/cursor-bridge/bridge-run.py` and nothing else. The supervisor has added red acceptance cases for them to `tests/test_improve_roster_launch.py` (committed before this brief; listed under Context). **Read `handoff/TASK-086b.md` whole first: every requirement, limit, constraint and Done rule there holds for this round, except where this brief changes it.** Your report is `handoff/TASK-086b-r2-report.md`.

Satisfies: R-107

## Scope
Files and directories you may create or modify:
- bridge/cursor-bridge/bridge-run.py
- bridge/cursor-bridge/MANIFEST.json
- tests/test_improve_roster_launch.py
- tests/test_hotfix25a_roster_launcher.py
- docs/cli-reference.json
- docs/CLI_REFERENCE.md
- docs/BUILDER_NOTES.md
- handoff/TASK-086b-r2-report.md

Limits on these paths: those of `handoff/TASK-086b.md` (its Scope section), with one widening: in `bridge-run.py` you may change your own round-1 helpers (`_read_roster_json`, `_roster_for_review`, `_git_launch_state`, `_load_deviation`, `_built_set_at_launch`, `_unknown_cause_text`, `_deviation_allows_builder_review`, `_resolved_builder_model`) as well as `review_launch_refusal`, `review_family_refusal`, `write_log` and the row's two keys. The two test files are the supervisor's: **do not edit them.** MANIFEST and the command reference change only by their tools.

Do not modify anything else.

## Out of scope
As in `handoff/TASK-086b.md` (Out of scope), unchanged. `handoff/TASK-086b.md` and `handoff/TASK-086b-r1-report.md` are read, never edited.

## Context
**Where round 1 stands.** Your round-1 change is committed on the branch (the commit before this brief's, with the supervisor's new tests between). The supervisor's run of the acceptance file on that code, through the launcher, is quoted at the end of this section. Everything else round 1 did stays as it is unless a requirement below changes it, in particular the call-site `_ascii_refusal(reason)` at the family refusal's print: the supervisor accepts it (R5 needs the escaping; recorded as a ruling).

**The new acceptance cases** (all in `tests/test_improve_roster_launch.py`, each docstring naming its requirement, its round-2 finding and its mutation label):
- `test_r2_parsing_rows_count_where_the_roster_file_cannot_be_read[absent]`, `[malformed]` (B1, M14)
- `test_r2_the_refusal_names_each_unknown_cause` (S3, M17)
- `test_r2_a_roster_file_naming_no_builder_family_lets_the_resolved_builder_stand_in` (the supervisor's ruling in B1, M19)
- `test_r4_a_roster_program_whose_built_set_raises_refuses_every_review` (B3, M16)
- `test_r4_a_roster_file_of_the_wrong_shape_never_opens_a_review_of_the_building_family[a-number-and-null]`, `[a-model-not-a-string]` (B3)
- `test_r6_a_brief_named_in_a_review_launch_stays_refused[composer-2.5]` (B2, M15; its `[gpt-5.6-sol-high]` case is the round-1 test, renamed by parametrization)
- `test_r7_a_last_byte_of_a_carriage_return_is_a_torn_line` (S4, M18)
- `test_r8_a_staged_rename_into_the_resolved_roster_is_not_clean` (S2, M20)

The helper `broken_copy` gained one breakage, `built-families-raises`, used by the R4 case above.

**The supervisor's red run** (the acceptance file on round 1's code, through the launcher): `9 failed, 91 passed in 60.89s (0:01:00)`, the nine being every case listed above but `test_r4_a_roster_file_of_the_wrong_shape_never_opens_a_review_of_the_building_family[a-model-not-a-string]`, which passes on round 1 and pins that answer. Each fails for the defect it names: a review that ran where it must be refused (exit 0 where 125 is asserted), the report file's cause missing from the refusal, `bridge-check.py` missing from the refusal, the row glued on after the carriage return, and `clean` true after the rename.

## Requirements
These change or sharpen `handoff/TASK-086b.md`'s R2, R4, R6, R7, R8 and R1; every other requirement there stands as written.

1. **B1 (R2): a parsing builder row always counts on an unknown set.** Where the status is `unknown`, the families a review is refused for are the union of (a) the roster file's builders' families (`roster._roster_builder_families`), or, where the roster file cannot be read **or reads but names no builder of a known family** (the supervisor's ruling: an unknown set is never read as nobody having built), the resolved file's builder's family standing in for them; and (b) the families of the branch's parsing builder rows (`roster._parsing_row_families(bset["parsing_rows"], <the roster data or {}>, <the profiles or []>)`), computed in every case, whether or not the roster file can be read. Where (a) yields no family (neither the roster file's builders nor the resolved builder can be read), every review is refused, as today, whatever (b) holds. An exception from `_parsing_row_families` or `_roster_builder_families` never widens what runs: where one raises, refuse every review, naming the cause and saying to resolve the roster again.
2. **B2 (R6): the brief-named refusal is never skipped.** Where `_deviation_allows_builder_review` lets the builder model through, `review_launch_refusal` does not return there: it goes on to the brief-token check below it, which refuses a review launch naming a brief exactly as for any other model. Keep the builder-model refusal's place and words where it refuses (existing tests read them).
3. **B3 (R4 and R2): a roster program that cannot answer refuses every review.** An exception raised by `roster.built_families(...)` is not turned into an `unknown` set: the review is refused, with exit 125, naming the exception (its type and message, through `_ascii_refusal`) and `bridge-check.py`, as R4's loader failure is. And `_read_roster_json` reads a roster file whose `profiles` list holds anything but objects (a number, `null`, a string) as a roster file that cannot be read (`None`), before the roster program is called with it.
4. **S1 (R8, R10): git not answering is null.** In `_git_launch_state`, an unexpected exit of `git status` after `git rev-parse HEAD` succeeded is git not answering: `start_commit` is `None` and `clean` is `False`, as for a timeout or a failure to start.
5. **S2 (R8): the tree is read whole, renames included.** Read the status with `git status --porcelain -z --untracked-files=normal --ignore-submodules=none` (a list of arguments, windowless, bounded, decoded without raising, as R10). Entries are separated by NUL; an entry whose first or second status letter is `R` or `C` is followed by one more NUL-separated field, its source path. `clean` is true only where every path named (each entry's path, and a rename's or copy's source path) is `docs/ROSTER.resolved.json`; any other path, a rename of another file onto the resolved roster among them, makes it false. Paths are compared as git prints them under `-z` (unquoted, `/`-separated, relative to the repository root).
6. **S3 (R2, R5): every unknown cause is named.** The unknown-set refusal names each unknown cause's label (every entry of `bset["unknown_causes"]`, in the order given, joined with `, `), not the first alone; the words R5 requires stay.
7. **S4 (R7): the line feed is the test.** `write_log` begins a new line exactly where the record's last byte is not a line feed (`b"\n"`); a last byte of a carriage return is a torn line. An `OSError` while reading the record's last byte does not drop the row: the row is appended as the checkpoint appended it (no new line begun), and the existing `bridge-run: run log not written` path is kept for a failure to open or write.
8. **S5 (R1, R6): one read of the set per launch.** `built_families` is called at most once per launch: the set read for the builder-model exception (R6) is the set the family refusal (R1 to R3) judges, passed or kept for the launch's process (a module-level value for the one launch is acceptable), never read a second time.
9. **Tidy.** Remove `_resolved_builder_model` (a pass-through of `roster_builder_model`; call that directly).

## Acceptance criteria
- [ ] Every test in `tests/test_improve_roster_launch.py` passes, unedited, the round-2 cases above among them; every case that passed on round 1 still passes.
- [ ] Every test in `tests/test_hotfix25a_roster_launcher.py` and in the files of `handoff/TASK-086b.md`'s Done steps 7 and 8 passes, unedited.
- [ ] B1, B2, B3 and S1 to S5 behave as Requirements 1 to 8 say; Requirement 9 done.
- [ ] `handoff/TASK-086b.md`'s remaining acceptance criteria (dump-cli `--check`, MANIFEST regenerated, `RESULT: SOURCES MATCH`, VERSION unchanged and unlisted, windowless-check, ASCII only, no dependency, no traceback) hold.

## Constraints
All of `handoff/TASK-086b.md`'s Constraints hold, with these changes:
- **Mutation: name the code points, run nothing.** In the report, for each of M1 to M12 (as `handoff/TASK-086b.md` names them) and for these new labels, the function and the line(s) as the file stands after your change, and the acceptance test id you expect to catch it: M14 a parsing row's family dropped where the roster file cannot be read; M15 the brief-named refusal skipped for the alternate; M16 an exception of `built_families` read as an unknown set; M17 only the first unknown cause named; M18 a carriage return taken for a line end; M19 an empty refused set read as nobody having built; M20 a rename's source path ignored for `clean`.
- **Report verbatim.** Round 1's report quoted `git status --short` lines that its own `git diff --stat` contradicted, described failing ids as groups, and quoted empty output with a prose exit code. This round, every command's output is pasted as printed, every failing id is listed one per line, and an empty output is written `(no output)` with the exit code shown by the command itself where it prints one.

## Done
Your report is `handoff/TASK-086b-r2-report.md`, written as you go, holding everything `handoff/TASK-086b.md`'s Done section lists (with "R1 to R11" read as the round's Requirements 1 to 9 here, each in one line naming its function and lines, and one refusal line as a test prints it for Requirements 1, 2, 3 and 6), and ending with a section headed exactly `Assumed, not verified`.

Run `handoff/TASK-086b.md`'s Done commands 1 to 14, exactly as written there, from the Workspace root, each on its own, synchronously, in that order (steps 1 and 2 before your first edit; 3 to 14 after your last), and quote each with its output verbatim.

Your last message is the summary and the report file's path, and nothing follows it.
