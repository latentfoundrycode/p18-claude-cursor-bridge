---
record: brief
header: 1
id: "TASK-086a"
round: 3
satisfies: [R-107]
scope: ["bridge/cursor-bridge/roster-check.py", "bridge/cursor-bridge/MANIFEST.json", "tests/test_improve_roster_alt.py", "docs/cli-reference.json", "docs/CLI_REFERENCE.md", "docs/BUILDER_NOTES.md", "handoff/TASK-086a-r3-report.md"]
merge_unit: null
blocking_class: null
---
# TASK-086a round 3: The roster resolves an alternate reviewer (R-107)

Round cause: fix-induced - bridge/cursor-bridge/roster-check.py:1319 to 1324, round 2 stops probing a profile once its builder does not answer, so the second profile's `review_b` is never probed and three cases of `tests/test_program_roster_sign_in.py` fail (a failing test; Review A blocking 5); security - line 439, a builder row whose `model` is null, empty or another false value is dropped before it is counted, so the set reads known without it (Review A blocking 1, security audit blocking 3); security - lines 1213 to 1221, `--review-alt` resolves an alternate whose family is unknown (Review A blocking 3); security - line 590, a `runs.damaged.jsonl` that is a dangling symbolic link reads as absent and the repair creates its target, and the repair follows a record that is a link (Review A blocking 4, security audit blocking 1 and advisory); security - line 192, git's output is decoded with the console's code page, so a branch or file name beyond it ends in a traceback (security audit blocking 2); security - line 532, a report name is printed as it is, so a name holding a line feed prints a line of its own (security audit advisory); defect - lines 525 and 1283 to 1289, a row whose family cannot be named always gets the `checkpoint` end form, never `new branch`, so the rebuild the line names can leave the set unknown again (Review A blocking 2); records - the BUILDER_NOTES line calling the three failures unrelated, and the docstrings (Review A)

## Objective
This is round 3 of TASK-086a, at the review ceiling: only the five blocking classes send work back from here, so this round holds those alone. Round 2's code is committed ("TASK-086a: builder round 2"), and after it the supervisor's tests of round 2's blocking defects ("TASK-086a: the supervisor's tests of round 2's blocking defects"). Make the changes the corrections below name, keep every test green, and edit nothing in the acceptance file. Round 1's brief, `handoff/TASK-086a.md`, and round 2's, `handoff/TASK-086a-r2.md`, stay in force for everything this brief does not change, with the report file now `handoff/TASK-086a-r3-report.md`.

Satisfies: R-107

The requirement's full text stands in round 1's brief.

## Scope
Files and directories you may create or modify:
- bridge/cursor-bridge/roster-check.py
- bridge/cursor-bridge/MANIFEST.json
- tests/test_improve_roster_alt.py
- docs/cli-reference.json
- docs/CLI_REFERENCE.md
- docs/BUILDER_NOTES.md
- handoff/TASK-086a-r3-report.md

Limits on these paths: as round 2's brief. `tests/test_improve_roster_alt.py` is the supervisor's: read it whole and run it, **do not edit it**. `docs/BUILDER_NOTES.md`: new dated lines at its end only.

Do not modify anything else.

## Out of scope
As round 2's brief. Nothing outside the corrections below changes: round 2's reviewers named further points (the `ls-tree -r` listing of subfolders, a `merge-base` answering exit 0 with nothing, the start-commit answers not passed to the new-branch check, an unreachable branch, `roster_models` not naming `review_b_alt`, an unborn head, a launcher append racing the repair); the supervisor records them, and you change none of them.

## Corrections
1. **Every model of a profile is probed before the profile is judged (failing test; Review A blocking 5; `tests/test_program_roster_sign_in.py`'s `test_r095_r2_probe_a_reply_quoting_the_line_on_a_line_of_its_own_is_judged_as_before_round_1` and both cases of `test_r095_r3_probe_the_line_beside_another_stdout_line_is_no_answer`).** Where probing, a profile that passes the checks before the probe has its builder probed and then its `review_b` probed, both of them whatever the builder's answer, as the checkpoint did (a model excluded by a mark or its pool is not probed, as today); the alternate is probed too where the table would resolve it. Then the profile is judged: a builder that did not answer skips it; round 2's correction 2 decides the rest. A sign-in answer from any probe ends the run with SIGN-IN and exit 5 at once, as today (the sign-in tests pin that no later probe runs). Append a dated line to `docs/BUILDER_NOTES.md` saying that round 2's line about these three failures was wrong: they were caused by round 2's change to the probe order and are fixed in round 3. Do not edit the earlier line.

2. **A builder row counts whatever its `model` holds (security; Review A blocking 1, security audit blocking 3; `test_task086a_a_builder_row_whose_model_is_empty_or_missing_makes_the_set_unknown`).** Remove the model test from the filter of the branch's builder rows: a row counts where its `kind` is `builder`, its `branch` the current branch and its `slot` not `not free`, as round 2's correction 9 says. A row whose `model` is not a non-empty string (null, empty, a number, `false`, a list) makes the set unknown with the cause line correction 9 gives, its model printed with `%r`. `built_by` keeps its own filter and its answer (R13).

3. **`--review-alt` refuses an alternate of no known family (security; Review A blocking 3; `test_task086a_review_alt_refuses_an_alternate_of_no_known_family`).** An alternate whose family neither the roster's entry nor the program can name cannot be shown independent: the request ends with exit 1, the resolved file unchanged, and the line `FAIL  --review-alt refused: review_b_alt <id>: its family is unknown` (added to round 2's list of causes). The ordinary table already refuses it; keep that.

4. **The repair refuses every link (security; Review A blocking 4, security audit blocking 1 and advisory; `test_task086a_a_repair_refuses_a_damaged_file_that_is_a_dangling_link`, `test_task086a_a_repair_refuses_a_record_that_is_a_link`, `test_task086a_a_repair_refuses_a_damaged_file_linked_to_another_file`).** Before reading anything, look at the record and at `runs.damaged.jsonl` with `os.lstat` (never `os.path.exists`, which follows a link): the record is refused where it is a symbolic link or junction (`stat.S_ISLNK`, or `st_reparse_tag` where present) or not a regular file; the damaged file, where `os.lstat` finds anything at that name, is refused where it is a symbolic link or junction, not a regular file, or has more than one hard link. Open the damaged file for the append with the built-in `open(path, "ab", opener=_nofollow_opener)`, where `_nofollow_opener(path, flags)` returns `os.open(path, flags | getattr(os, "O_NOFOLLOW", 0), 0o644)`; the built-in `open` stays the call that names the path, which `test_task086a_a_repair_that_fails_part_way_leaves_the_record_whole` relies on. Then check the open handle with `os.fstat(f.fileno())` (a regular file, `st_nlink == 1`) before writing; refuse otherwise. Each refusal prints `CANNOT REPAIR: <what was refused>` and exits 2 with nothing written. Round 2's order stands (the moved lines appended and synced, then the kept lines through `mkstemp`, synced, then the replace).

5. **git's output is read as bytes and decoded as UTF-8 (security; security audit blocking 2, Review A should-fix; `test_task086a_a_report_name_beyond_the_consoles_code_page_is_read`, `test_task086a_a_branch_named_beyond_the_consoles_code_page_is_read`).** Every git call captures bytes (no `text=True`, no locale decoding) and decodes the output itself as UTF-8 with `errors="surrogateescape"`; a `ValueError` anywhere in reading git's answer is git not answering (cause `git`). A report name whose bytes are not UTF-8 (it holds a surrogate after decoding) is a report whose brief cannot be read: an unknown cause, never skipped. A branch name read so compares with a row's `branch` as text. Nothing escapes as a traceback, on the main thread or a reader thread.

6. **A report name is printed quoted (security; security audit advisory; `test_task086a_a_report_name_holding_a_line_feed_prints_no_line_of_its_own`, POSIX-only, run by CI's Linux job).** The unknown cause line for a report without its row prints the report's name with `%r` (as the model is printed), so no name can stand in the output as a line of its own. The words the tests read (the name's `-r1-report.md` ending, `unknown`) stay on that line.

7. **A row of no known family takes the end form R9 gives (defect; Review A blocking 2; `test_task086a_a_row_of_no_known_family_the_rebuild_cannot_drop_takes_a_new_branch`).** On an unknown set whose causes include a row whose family cannot be named, and no line that fails to parse and no report without its row, the REBUILD line's end form is `new branch` where the same-branch rebuild cannot drop every counted row (computed as the known set's REBUILD computes it), and `checkpoint` where it can.

8. **The docstrings (records; Review A).** The module docstring's opening usage line names `--repair-record` and `--review-alt <reason>`; its sentence that a refusal "marks the profile unusable" says how an alternate that does not answer under the reason `family` leads to the REBUILD; its claim that every builder row of the branch counts is now true. The `built_families` docstring states that TASK-086b's launcher must pass the roster and its profiles for the same set the resolve reads (without them a row whose family only the roster names reads as unknown). Regenerate the command reference.

9. **The report (records).** Each item of `Assumed, not verified` gives what you assumed, why, and what would confirm it; add that git prints names as UTF-8 bytes and that `os.lstat` fills `st_reparse_tag` on this Python. "Missing acceptance cases" names any case you found untested.

## The acceptance tests in this round
`tests/test_improve_roster_alt.py` now holds, after rounds 1 and 2's 111 cases, the supervisor's round-3 section: `test_task086a_a_builder_row_whose_model_is_empty_or_missing_makes_the_set_unknown` (5 cases), `test_task086a_a_row_of_no_known_family_the_rebuild_cannot_drop_takes_a_new_branch`, `test_task086a_review_alt_refuses_an_alternate_of_no_known_family`, `test_task086a_a_repair_refuses_a_damaged_file_that_is_a_dangling_link`, `test_task086a_a_repair_refuses_a_record_that_is_a_link`, `test_task086a_a_report_name_beyond_the_consoles_code_page_is_read`, `test_task086a_a_branch_named_beyond_the_consoles_code_page_is_read`, `test_task086a_a_report_name_holding_a_line_feed_prints_no_line_of_its_own`. On round 2's code: 9 failed and 3 skipped on Windows (the two symbolic-link cases skip where the account cannot make a symbolic link; the line-feed name is POSIX-only). After your change every case passes or skips only by its own condition, its reason quoted from `-rs`, and `tests/test_program_roster_sign_in.py` passes whole.

## Mutation code points
As round 2's brief, N1 to N22, and: N23 a row with an empty model dropped; N24 an alternate of no known family accepted on request; N25 the damaged file checked with `os.path.exists`; N26 the record's link check dropped; N27 git's output decoded with the code page; N28 a report name printed unquoted; N29 the end form for a row of no known family fixed at `checkpoint`; N30 probing a profile stopped at its builder.

## Done
As round 1's brief, steps 1 to 13, with the report at `handoff/TASK-086a-r3-report.md`. Step 2 (before your first edit) runs the acceptance file and expects 9 failed, 3 skipped among the round-3 cases; step 6 expects every case passed or skipped by its own condition; step 7's batch must show no failure at all.

Your last message is the summary and the report file's path, and nothing follows it.
