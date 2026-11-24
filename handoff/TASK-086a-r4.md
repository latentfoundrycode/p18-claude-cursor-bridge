---
record: brief
header: 1
id: "TASK-086a"
round: 4
satisfies: [R-107]
scope: ["bridge/cursor-bridge/roster-check.py", "bridge/cursor-bridge/MANIFEST.json", "tests/test_improve_roster_alt.py", "docs/cli-reference.json", "docs/CLI_REFERENCE.md", "docs/BUILDER_NOTES.md", "handoff/TASK-086a-r4-report.md"]
merge_unit: null
blocking_class: "behaviour"
---
# TASK-086a round 4: The roster resolves an alternate reviewer (R-107)

Round cause: fix-induced - bridge/cursor-bridge/roster-check.py:1389 to 1422, round 3 probes `review_b` and the alternate together and judges them on one answer, so under the reason `family` a `review_b` that does not answer discards an alternate that answered, prints a REBUILD, probes `review_b` a second time and ends with no usable profile (Review A, round 3, B1; reproduced by the supervisor's tests below)

Blocking class: behaviour - Review A, round 3, B1: under the family deviation (C39 table row 2, "the alternate, with deviation (reason family)") a `review_b` that does not answer its probe turns an alternate that answered into a REBUILD and then "FAIL  no usable profile", exit 1; round 2 resolved the alternate there (a regression of round 3, against the design's table and round 2's correction 2)

## Objective
This is round 4 of TASK-086a, above the review ceiling under the class line above alone: nothing else of the round-3 review is in it. Round 3's code is committed ("TASK-086a: builder round 3"), and after it the supervisor's tests of this defect ("TASK-086a: the supervisor's tests of round 3's blocking defect"). Make the one change the correction below names, keep every test green, and edit nothing in the acceptance file. Round 1's brief, `handoff/TASK-086a.md`, round 2's, `handoff/TASK-086a-r2.md`, and round 3's, `handoff/TASK-086a-r3.md`, stay in force for everything this brief does not change, with the report file now `handoff/TASK-086a-r4-report.md`. Every line number below is as of round 3's committed tree.

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
- handoff/TASK-086a-r4-report.md

Limits on these paths: as round 3's brief. `tests/test_improve_roster_alt.py` is the supervisor's: read it whole and run it, **do not edit it**. `docs/BUILDER_NOTES.md`: new dated lines at its end only.

Do not modify anything else.

## Out of scope
Everything outside the correction below. Round 3's reviewers named further points (record values such as a row's `id`, `built_by` and the last builder run's model printed as they are; the end form chosen by matching the words of a cause label; a check-then-open race on the damaged file on Windows; every reparse point refused, cloud placeholders included; the round-3 report's counts); the supervisor records them, and you change none of them.

## Correction
1. **Each model's probe answer is judged apart (behaviour; Review A, round 3, B1; `test_task086a_review_b_silent_under_the_family_deviation_leaves_the_alternate_resolved`, `test_task086a_an_alternate_silent_under_the_family_deviation_judges_review_b_on_its_first_answer`, `test_task086a_both_reviewers_silent_under_the_family_deviation_skip_the_profile`).** In the probe block (lines 1384 to 1422) keep round 3's order and its sign-in rule exactly: the builder probed first, then `review_b` where no mark or pool excludes it, then the alternate where a deviation would resolve it, each model probed **once**, and a sign-in answer from any probe ending the run with SIGN-IN and exit 5 at once. Keep each model's answer separately (one answer for the builder, one for `review_b`, one for the alternate), not one flag for `review_b` and the alternate together. Then judge the profile in this order:
   - the builder did not answer: the profile is skipped, as now;
   - a deviation of the reason `unavailable`: the alternate did not answer, the profile is skipped, as now (`review_b` is excluded and not probed, as now);
   - a deviation of the reason `family`: the alternate answered, the deviation stands and the alternate resolves, **whatever `review_b` answered**; the alternate did not answer, the REBUILD with `review_b` is taken as lines 1405 to 1415 take it now (the end form, `deviation` dropped, `review_b` the reviewer), and `review_b` is judged on the answer it gave in the first probe: answered, the profile resolves with the REBUILD; did not answer, the profile is skipped. **`review_b` is never probed a second time** (remove the probe at line 1416);
   - no deviation (the plain path and every REBUILD path): `review_b` did not answer, the profile is skipped, as now.
   Correct the module docstring's account of the probe judgement (lines 47 to 50) to say the same, and regenerate the command reference if its text changes. Append a dated line to `docs/BUILDER_NOTES.md` saying round 3 judged `review_b` and the alternate on one answer and round 4 judges each apart. `tests/test_program_roster_sign_in.py` must stay green whole.

## The acceptance tests in this round
`tests/test_improve_roster_alt.py` now holds, after rounds 1 to 3's 123 cases, the supervisor's round-4 section: the three cases named in the correction. On round 3's code all three fail: the first ends with "FAIL  no usable profile" and exit 1, the other two show `review_b` probed twice (`['composer-2.5', 'grok-4.7-medium', 'gpt-5.6-sol-high', 'grok-4.7-medium']`). After your change every case of the file passes or skips only by its own condition (the two symbolic-link cases where the account cannot make a symbolic link, the line-feed name off POSIX), its reason quoted from `-rs`.

## Mutation code points
As round 3's brief, N1 to N30, and: N31 `review_b`'s answer read for the alternate under the family deviation; N32 `review_b` probed a second time after the alternate's silence.

## Done
As round 1's brief, steps 1 to 13, with the report at `handoff/TASK-086a-r4-report.md`. Step 2 (before your first edit) runs the acceptance file and expects exactly the three round-4 cases failed and 3 skipped; step 6 expects every case passed or skipped by its own condition; step 7's batch, with `tests/test_program_roster_sign_in.py` in it, must show no failure at all. **Run steps 6 to 9 and quote their output only after your last edit of any file in scope**, so the counts, the diff's stat and the manifest's time are those of the tree you hand back (round 3's report quoted runs made before its last edits). In `Assumed, not verified`, give each item's assumption, why, and what would confirm it, and claim no case as exercised that skipped on this host.

Your last message is the summary and the report file's path, and nothing follows it.
