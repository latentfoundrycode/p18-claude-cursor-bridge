# ASSUMPTIONS - TASK-032-r2

From the `Assumptions:` sections of the branch's commit messages (extra places to look, never the review's scope).

- r1: the seeding from letter snapshots and report files partial -> test (tests/test_task032_supervisor_guard.py, the seeding cases; pass on 9a5d507)
- r1: the squash reader's branch-name rule simplified -> test (the supervisor's squash-reader cases); the reading after a leading word recorded in docs/HARDENING.md (TASK-032, N4)
- r1: verify records a reply even on GATE-INTEGRITY -> test (a flagged review spends no round: tests/test_task032_supervisor_guard.py and tests/test_task032_supervisor_r4.py); the four early exits that set no flag recorded in docs/HARDENING.md (TASK-032)
- r1: a missing docs/ROSTER.resolved.json skips the builder-model check -> accepted (docs/INVENTORY.md, Decisions, TASK-032's settled points)
- r1: a detached HEAD or a folder outside git -> test (refused in both programs: the launcher's and the guard's R15 cases)
- r2: clause (e)'s matrix not exhaustively tested -> test (the supervisor's 231 acceptance tests, 88a60a6)
- r2: branch event ordering across the two records -> test (the supervisor's lapse and branch-rule cases)
- r2: the owner's line in a bold-only Markdown form -> accepted (bridge_env.REVIEW_LIFT_RE reads the plain form and the two bold forms, with or without a list mark; a line in any other form lifts nothing, failing closed)
- r3 and r4: "none" -> noted (round 3's report claimed D1 and C1 done, which the diff does not show; round 4's omitted the GATE-INTEGRITY exits; the reviewers hunt unaided)
