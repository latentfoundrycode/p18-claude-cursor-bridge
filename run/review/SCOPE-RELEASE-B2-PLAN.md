# SCOPE - RELEASE-B2-PLAN: release B2's design revision and plan addendum (pull request #136)

Records and one test, written by the supervisor in release B2's change cycle (~/.claude/cursor-bridge/workflow/phases/change-cycle.md, items 2 to 5) on the finished release T: the design revision and its plan addendum as one subject, through the two-critic design critique and the owner's gate (2026-11-04). No program, workflow or shipped bridge text changes; no builder ran. Branch change/release-b2 from origin/main at the merge of PR #135.

## What the records must do
- docs/DESIGN.md, the section "Change: release B2": headers on eight record kinds, the three kinds of record and their one rule each, header first, fallback, malformed, the eleven retired readings, the subset reader in bridge_env.py with pyyaml in the tests only, the migration program and the calibration's step, the status file's cap on the body, Failure modes, Security, Testing strategy, Delivery, Who decided.
- docs/REQUIREMENTS.md: R-057 to R-064 added, each `planned`.
- docs/INVENTORY.md: release B2's eight Decisions rows.
- docs/diagrams/: D-005 new (the header schemas, Level 4), D-001 and D-002 revised, INDEX.md.
- docs/BUILD_PLAN.md, "Release B2 — the plan addendum": the constraints, stage H1 (TASK-046 to TASK-050), stage H2 (TASK-051 to TASK-054), a Demonstration line per stage.
- docs/DESIGN_CRITIQUE.md: subject release-b2, five rounds (four critique rounds, round 4 the ceiling, then the confirming read), every finding fixed, none accepted, no resolution round due, the gate with the owner's six approvals, and the paragraph after the gate.
- docs/HARDENING.md: a stale sentence of release T's project end corrected, and the new section "Release B2's design records".
- docs/PROJECT_STATUS.md as it will read at this pull request's merge (ISS-009; cap 12,000 characters): Phase changing, the change cycle at item 6, Increment none with TASK-046 next, Last accepted naming PR #136 first, In flight none, Awaiting user on nothing, Remote sync naming PR #136; the replaced lines moved word for word to docs/archive/STATUS_HISTORY.md. project.json: phase changing, the stage, updated 2026-11-04.

## The one test changed, with the paragraph it enforces
tests/test_release_t_stamp.py, written by the supervisor: test_r056_the_completion_check_passes_in_done_mode required `completion-check.py --mode done` to read RESULT OK at all times, and this pull request's eight planned rows fail it. It enforces TASK-045's Done when (docs/BUILD_PLAN.md), which asks for that check green at the accept commit, and R-056. It now excuses only a run at `Phase: changing`, exit 1, whose every counted problem is a `NOT BUILT` line for a row after R-056 still planned, the RESULT line's count equal to those lines. At `Phase: done` the check must read RESULT OK as before. test_r056_only_a_change_cycle_s_later_planned_rows_are_excused pins those limits. Apply the anti-gaming checks: this touches a test.

## What to check
- Each claim is true against the repository: run `~/.claude/cursor-bridge/plan-check.py` (RESULT: OK, 54 increments, 45 merged, READY TASK-046), `~/.claude/cursor-bridge/completion-check.py --mode plan` (RESULT: OK; 54 built, 2 deferred, 8 planned), `~/.claude/cursor-bridge/inventory-check.py` (RESULT: OK) and `~/.claude/cursor-bridge/diagram-check.py --mode design` (RESULT: OK, 5 selected, 13 omitted); `--mode code` is expected to carry one `TESTS` note for D-005 until TASK-046, which is not this pull request's defect.
- The records agree with each other and with the programs they name under bridge/cursor-bridge/: every R-057 to R-064 row is planned and in some increment's Satisfies line; D-005's attributes equal the design's table; the status file's position lines read as at this merge and its Phase equals project.json's; the archive holds main's replaced lines word for word (`git show origin/main:docs/PROJECT_STATUS.md`).
- The merged-brief rule: three of the 97 briefs, handoff/TASK-002-r2.md, -r3.md and -r4.md, are ones `parse_scope` refuses, and they stay header-less by rule.
- No computer path, user name or e-mail address in a tracked file (rule 54). The Documents/ folder (the Project Summary) is outside git and not part of this diff.

## The threat model
docs/INVENTORY.md's Decisions record none for what this diff changes (records and one test). The five blocking classes stand.

## Before this round
- The full suite with the pull-request variables for PR #136 (GITHUB_REF=refs/pull/136/merge, GITHUB_BASE_REF=main, GITHUB_EVENT_NAME=pull_request): `3562 passed, 40 skipped` on this head. An earlier run, on eda2024, read `1 failed, 3560 passed, 40 skipped`, the failure the stamp test above. A first run was stopped by hand before it ended, since Review A's fixes changed the records it read; it has no result.
- Review A (diff-reviewer): round 1 REJECT, one Blocking (TASK-054 said no brief is refused; three are), three Should fix, seven Consider, all taken in eda2024 but the archive's lack of the Phase and Working files lines, since the new Working files line only inserts text. Round 2 APPROVE, one Should fix and three Consider, taken. Round 3, on the stamp test, APPROVE, a narrowing with a stated reason and no gate-integrity flag, its Should fix and its Considers on the test taken in e40cc28 and 7705bf1.
- The critique's substance passed two critics of different families and the owner's gate; Review B checks the merge gate's points, not the design's or the plan's choices again.

Release B2's increments (TASK-046 to TASK-054) are later work, not this pull request's defect. This is Review B's round 1, below the ceiling.
