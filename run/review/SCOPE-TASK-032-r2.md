# SCOPE - TASK-032-r2 (the gate's round 2 on PR #94)

TASK-032 - The code-review ceiling held by the launcher and the guard. Author: builder (composer-2.5, four runs); the supervisor wrote the acceptance tests. Satisfies R-042 in part: the launcher's and the guard's counts, lifts, branch rule and refusals, and the permission guard's refusal; the loop's text is TASK-034's and the squash reader's narrowing and `pace-report.py` TASK-033's, so R-042 stays planned.

Blocking class: failing test - two of the supervisor's guard tests fail on PR #94's Linux job: they take two snapshots of two IDs within one second, so the branch's first record ties and keeps the bridge folder's listing order (tests/test_task032_supervisor_guard.py, fixed in f897795)

## The ceiling (the owner's decision of 2026-10-24, applied by hand from 2026-10-25)
This is the increment's fourth round: builder runs of handoff/TASK-032.md, -r2.md, -r3.md and -r4.md. Round 4 is past the three-round ceiling and was lifted by the class line above (and by a second defect of a blocking class, a defeated safety mechanism: a round whose Review B reply arrived but was never verified could be re-snapshotted on any tree; the security audit of round 3). Grade every finding by the five blocking classes first: behaviour against the brief or the register, security, data integrity, a defeated safety mechanism the increment relies on, a failing test. Only a finding of those classes is a REJECT. Every other finding is a HARDENING note: name it as such, and the supervisor records it in docs/HARDENING.md with the increment. docs/HARDENING.md's "TASK-032" section already lists what the supervisor recorded from rounds 1 to 3; a finding listed there is recorded, not new.

## Scope (docs/BUILD_PLAN.md, TASK-032, quoted)
bridge/cursor-bridge/bridge_env.py; bridge/cursor-bridge/bridge-run.py; bridge/cursor-bridge/review-guard.py; bridge/cursor-bridge/permission-guard.py; bridge/cursor-bridge/MANIFEST.json; tests/test_bridge_run_review_ceiling.py; tests/test_review_guard_ceiling.py; tests/test_bridge_run_design_ceiling.py; tests/test_permission_guard.py; tests/test_review_guard.py; tests/test_review_guard_a4.py; tests/test_bridge_run.py; docs/cli-reference.json; docs/CLI_REFERENCE.md; tests/test_hotfix25a_guard_scope_invisible.py *(widened 2026-10-28 at the brief's reality check: its guard snapshots use the bare names `001` and `003`, which the grammar refuses, so they move to the grammar as tests/test_review_guard.py's do; the same check found the agent-home refusal after the launcher's `started` line, so the order clause a states is read as after the key-file and design-ceiling refusals, before the `started` line, the agent-home check left where it is)*

## Done when
docs/BUILD_PLAN.md, TASK-032, the `Done when:` paragraph (clauses (a) to (e)), read whole in the checkout. The briefs are normative in the precedence handoff/TASK-032-r4.md > -r3.md > -r2.md > handoff/TASK-032.md; -r2.md's rulings R1 to R24 settle what the plan's clauses left open, and -r3.md's L1-L10, G1-G9, C1-C4, D1 and E1-E5 fold in round 2's review.

## Out of scope (handoff/TASK-032.md, quoted)
- .env and anything under secrets/
- CI configuration
- docs/ and handoff/, except the files the Scope section names (in particular, do not write `docs/RUN_PARAMETERS.md`: the owner's line is read from it, never written by you)
- bridge/cursor-bridge/plan-check.py and bridge/cursor-bridge/pace-report.py. TASK-033 makes `plan-check.py` import the subject reader you place in `bridge_env.py`, and narrows the closing-parenthesis form there. Here, copy the four forms as they stand.
- Any text of the loop (`bridge/cursor-bridge/workflow/`, `bridge/commands/`, `bridge/agents/`, `Known-Pitfalls.md`). The loop's wording of the ceiling belongs to other increments.
- Every test file not listed in Scope, even if a new refusal makes it fail.

## Tests the supervisor wrote, and the paragraph each enforces
The builder runs these and never edits them (each brief from round 3 on says so; `git diff --quiet b1ad478` on the three files passes at the branch's head).
- tests/test_task032_supervisor_launcher.py (88 tests, 88a60a6, the flag dropped in b1ad478): every launcher case of the plan's clause (e) and clauses (a), (b) and (b2), and the rulings of handoff/TASK-032-r2.md; each docstring names R-042 and the paragraph or ruling it enforces; every case through the program's command line on a temporary launch folder.
- tests/test_task032_supervisor_guard.py (143 tests, 88a60a6, the flag dropped in b1ad478): every guard case of clause (e) and clause (c), and the -r2.md rulings; each docstring names R-042 and its paragraph; on temporary repositories.
- tests/test_task032_supervisor_r4.py (4 tests, d8d7547): handoff/TASK-032-r4.md's two defects. On round 3's code (f735a24) three fail and one passes (the open-round case, behaviour the round must keep).
- b1ad478 also drops `creationflags=NO_WINDOW` from tests/test_bridge_run_review_ceiling.py and tests/test_review_guard_ceiling.py (the builder's files): tests/test_tests_windowless.py's scan wants the literal CREATE_NO_WINDOW on a line that sets flags, and the conftest.py default gives every flagless launch that flag.
No mutation driver: the briefs' mutation lists are the builder's own in-process checks; the supervisor's probe of a revision after a later completed run (refused, as -r4.md says) ran in a scratch file outside the checkout.

## Checks run on the branch
- The full suite on 9a5d507: 2906 passed, 39 skipped, 0 failed (22 min).
- scope-check.py handoff/TASK-032.md --base cec417a: every code and test file in scope; the records the supervisor's; one drift line, docs/archive/STATUS_HISTORY.md, the supervisor's archive of the status file's older Last accepted part (bd3b862, a commit of its own), which the installed check's record list does not name.
- The new and changed test files against the checkpoint (cec417a, a read-only worktree, torn down): 257 failed, 412 passed. The passes in the new files (test_bridge_run_review_ceiling.py 7, test_review_guard_ceiling.py 2, the supervisor's launcher 5, guard 19, r4 1) are each the allowed half of a refusal pair, behaviour the increment must keep: the accepted brief names, rounds 1 to 3, a test or driver kind on `main`, a `DESIGN-` name, the probes and the launcher form the permission guard allows, a malformed launcher line skipped, and r4's open round.
- No write outside the Workspace after any of the four builder runs (the marker and `find` check).

## Expected files
docs/BUILD_PLAN.md (the Scope widening at the checkpoint); handoff/TASK-032.md, -r2.md, -r3.md, -r4.md (the briefs) and handoff/TASK-032-r1-report.md to -r4-report.md (the builder's reports); docs/cli-reference.json and docs/CLI_REFERENCE.md (regenerated); bridge/cursor-bridge/MANIFEST.json (regenerated); the records committed by the supervisor (docs/HARDENING.md, docs/INVENTORY.md, docs/PROJECT_STATUS.md, docs/REQUIREMENTS.md, docs/archive/STATUS_HISTORY.md, project.json); run/review/ (this file, the diff, the assumptions), which the diff excludes.

## Rounds
- Round 1 (2dddd9b): Review A REJECT (the seeding, about forty of clause (e)'s cases, D1-D27, D-T1-D-T9).
- Round 2 (e28721f): Review A REJECT (B1-B14, S1-S9); the builder's tests incomplete, so the supervisor wrote the 231 acceptance tests (88a60a6), 33 of them failing on round 2's code.
- Round 3 (f735a24): the 231 pass. Review A REJECT on one finding of class behaviour (N1) and eight outside the five; the security audit FAIL on one defeated safety mechanism and nine advisories. The rest recorded in docs/HARDENING.md, "TASK-032".
- Round 4 (9a5d507): the two blocking-class fixes only. Review A confirms both fixed and REJECTs on one new finding, which the security audit (PASS with findings) names too: four of `verify`'s early GATE-INTEGRITY exits write no `flagged_launch`, so a void review spends a round. The supervisor drew the by-class line there: each path follows a reviewer's tampering or a worktree left behind, the error fails closed (one round more counted, which the owner's line restores), and no ordinary run reaches it; it and the audit's four other findings (round 1's two spellings, the `.err` file deleted or overwritten, `snapshot` dropping `flagged_launch`, the revised-in-place wording) are in docs/HARDENING.md, "TASK-032". A Review B finding already listed there is recorded, not new.

## The gate's round 2 (this file)
The gate's round 1 (snapshot TASK-032 at 52b13e9): Review B REJECT on one finding, letter seeding counting past a gap (review-guard.py:471-484 against handoff/TASK-032-r3.md G9), which fails closed and needs a skipped letter in an increment in flight at the install; the supervisor drew the by-class line and recorded it (docs/HARDENING.md, TASK-032). Review A's round-4 finding, the early GATE-INTEGRITY exits, likewise. Then CI failed on Linux (2 failed, 2892 passed): the two supervisor tests above. The round's change is the supervisor's alone:
- f897795 (supervisor:): tests/test_task032_supervisor_guard.py gains next_second() and calls it before the second ID's snapshot in the two failing tests; no assertion changed. Reproduced on Windows by reversing os.listdir in the guard's process: the old test fails with CI's message, the fixed file passes 143 of 143 (153 with tests/test_task032_supervisor_r4.py and tests/test_review_guard_ceiling.py), and 143 with the listing as it is.
- 1fa9571: three lines in docs/HARDENING.md, TASK-032: the gap finding, the same-second tie in the program (bridge_env.py `_branch_events`, the sort at :746) as a lead, and the suite's rows in the real launcher log.
No program file changed since 9a5d507. The question for this round: does the fix remove the CI failure's cause without weakening either test, and does any other test depend on the order of two same-second records?
