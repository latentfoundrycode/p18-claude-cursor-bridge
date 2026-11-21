# SCOPE for TASK-069 (Review B, round 3)

## What changed since Review B's round 2 (your approval)
CI on PR 186 (ubuntu) failed 11 cases, all in TASK-033's older tests (tests/test_task033_supervisor.py, _r2.py, _r3.py), which asserted that a squash naming no ID merges nothing and that a records subject's guard record starts nothing; R-089 counts the first as PR-<n> and the second as a name. No program changed. The supervisor's test fix: seven fixture commits whose (#n) ending was incidental to the ID reader they test now close no pull request; the stage-and-records case and the total row expect B3-RECORDS's start; the ISS-013 form case expects PR-61 merged and started, TASK-031 still not merged; a fixture docstring follows. Read the commit TASK-069: TASK-033's pace-report tests brought to R-089 with git show, and the records commit after it. Review A approved the fix. This is the guard's third round, at the ceiling: only the five blocking classes send it back.

## What changed between Review B's rounds 1 and 2
Review B's round 1 rejected on two behaviour findings: a PR-<n> the subject reader returns was read as a name the subject names (PR-2: follow-up (#1) folded PR-1 into PR-2 and merged PR-2), and a pass line with a cause outside the list was dropped instead of read as unstated. Builder round 3 (handoff/TASK-069-r3.md, the review ceiling's round) fixed both in pace-report.py; it also changed the rule for several commits closing the same (#n), forced by the supervisor's case reusing the fixture's (#1): a close naming no counted name now makes PR-<n> its own name, merged at that close. The supervisor ruled that plan-consistent (the plan counts PR-<n> where a commit closes with (#n) and names no counted name) and added a case with an unused number. Read the commits since round 1 with git log, from the commit TASK-069 r3: Review B's two findings as tests to HEAD. Review A approved round 3; the security review passed. This is round 2 of the guard, at three builder rounds: the code gate's ceiling. Only findings of the five blocking classes send it back.

TASK-069 is review passes and round causes in the pace report (R-089): the pace report counts a name, an increment's ID or `PR-<n>`, from a tracked brief, a guard rounds record, a tagged pass line of the in-flight log or a squash on main; each round's cause comes from the builder's launcher row, the guard's round or a pass line; `review-guard.py snapshot` writes the round's `cause` from its SCOPE file; `base update` is the eighth round cause in `bridge_env.ROUND_CAUSES`. Branch task-069 from main 1a27fa0 (PR #185's merge, TASK-068). Three builder rounds; this is the review guard's third round for TASK-069, at the code gate's ceiling of three: there is no Blocking class line.

Round cause: defect

Where the increment ends: the programs pace-report.py, review-guard.py and bridge_env.py, MANIFEST.json, the command reference (two files), docs/BUILDER_NOTES.md, two builder reports, tests/test_program_pace_rounds.py (the supervisor's), tests/test_pace_report.py, two test files edited by the supervisor outside the plan's Scope (tests/test_program_in_flight.py and tests/test_release_s_launcher.py, both needing the eighth cause; HARDENING, TASK-069, the deviation) and the records. The reviews' leads (HARDENING, TASK-069, leads 1 to 17) are recorded, not this diff's defects: among them a folded PR-<n>'s own rows outside its target's start, an unparsable guard time suppressing a pass line, the log's byte cap keeping the oldest part, bridge-run.py's cause pattern, scope_blocking_line's unbounded read and _parse_run_time's digit class.

Read the commit messages (git log, the full bodies) for the quoted lines.

## The plan entry, quoted (docs/BUILD_PLAN.md, TASK-069)
Scope: bridge/cursor-bridge/review-guard.py; bridge/cursor-bridge/pace-report.py; bridge/cursor-bridge/bridge_env.py; bridge/cursor-bridge/MANIFEST.json; docs/cli-reference.json; docs/CLI_REFERENCE.md; tests/test_program_pace_rounds.py; tests/test_pace_report.py; tests/test_review_guard.py; tests/test_review_guard_ceiling.py; tests/test_d003_review_round_states.py; docs/BUILDER_NOTES.md; handoff/TASK-069-r<N>-report.md
Satisfies: R-089
Done when: read it whole in docs/BUILD_PLAN.md under the heading TASK-069 (one long paragraph): the eighth cause in the one list the launcher, the guard, in-flight.py and the report read; the snapshot's `cause` from the SCOPE file's `Round cause:` line, unstated where missing or outside the list, deciding no count, lift or verdict; the counting of names by the design's one set of rules (brief, guard record, pass line, and PR-<n> from a squash naming no counted name), started and merged as stated, the folding of PR-<n> pass lines, the cause line, the passes line per week ending `recorded passes only`, the week crossing, the field's week as the reproduction red on the checkpoint, the HARDENING column, the docstring, the command reference and MANIFEST regenerated, no option, no new dependency.

## The supervisor's rulings on the plan's text (round 2's brief, handoff/TASK-069-r2.md)
- A PR-<n>'s start at its commit's time counts for Started only, never as a known start for Mean days.
- STAGE- and DESIGN- names are never counted names from any source; their passes still count (a stage review's guard round a review-b pass). A squash naming only such a name counts as its PR-<n>.
- The PR-<n> rule holds with handoff/ untracked too.
- The in-flight log is read in binary within 8,388,608 bytes; pass-line stamps take ASCII digits only.
- The guard reads the SCOPE file in binary, at most 1,048,576 bytes, a longer file unstated, with no backtracking pattern.

## The supervisor's tests, each with the clause it enforces
- tests/test_program_pace_rounds.py (names R-089 and D-003; ten cases committed before the checkpoint in 85ad45b, red there "9 failed, 90 passed, 1 skipped" over the targeted files; six cases added after round 1's reviews in 85350b8, on round 1's work "4 failed, 2 passed"): the three sources of a cause and their order; a name with no brief; a name that never merged; the passes line counting a round once; the week crossing; the field's week; PR-<n> folding; then the days read only from a recorded start, stage and design names, untracked mode, the ISS-013 subject as PR-61, a stamp of other digits no pass line, a long SCOPE line under 20 seconds.
- tests/test_program_in_flight.py and tests/test_release_s_launcher.py (85ad45b): the seven causes as the first seven of the list, the launcher's list equal to bridge_env's, and the cause heading's count with eight causes.

## Evidence
- Review A: round 1 REJECT (two behaviour findings), round 2 REJECT on one records item only (four em dashes in the builder's report), fixed by the supervisor in 7f85982 with two line numbers, no builder round; round 3 APPROVE
- security audit: round 1 PASS with three advisories, round 2 PASS, the advisories closed; round 3 PASS with two advisories (HARDENING leads 10 and 11)
- Review B: round 1 REJECT (two behaviour findings, fixed by round 3); round 2 APPROVE
- CI's first run on PR 186: ubuntu 11 failed, 7074 passed, 66 skipped (TASK-033's tests); after the supervisor's test fix, the eight pace-report test files stripped: 253 passed; Review A APPROVE on the fix
- targeted run on round 3, stripped, nine files: 345 passed, 1 skipped; record tests stripped, five files: 224 passed
- completion-check.py --mode plan OK (89 built, 2 deferred, 14 planned); inventory-check.py OK

## Expected bookkeeping and records in the diff
handoff/TASK-069.md, handoff/TASK-069-r2.md, handoff/TASK-069-r3.md and their reports, docs/BUILDER_NOTES.md, docs/HARDENING.md, docs/INVENTORY.md, docs/PROJECT_STATUS.md (as at this pull request's merge), docs/diagrams/D-003-review-round-states.md (the field's wording), and run/review/ (these files).
