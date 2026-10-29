# SCOPE - TASK-026's records

TASK-026 (docs/BUILD_PLAN.md, stage B6; R-037) is the release-level review of release B: one pass, the fixes, a second pass. It is supervisor-orchestrated, its Scope being Reports/Reviews/ outside the Workspace, with working inputs under run/review/. Both passes are done:

- **Pass 1:** on main 1f5ef8e, by a fresh-context Claude reviewer and Review B; both APPROVE.
- **The fixes:** BUG-034 (PR #105) and BUG-035 (PR #106).
- **Pass 2:** on main a60fe91, by both reviewers; both APPROVE (install after the stamp).

This pull request carries the records, on branch task-026-records from origin/main a60fe91. Its title starts with "TASK-026:" so that plan-check counts TASK-026 merged.

## Scope (the records)

- docs/HARDENING.md, the new section "TASK-026, the release-level review of release B":
  - the review and the plan's Done-when figures;
  - the dispositions of M1, M2, M3, L1 to L3, C-1 and pass 2 Review B's Consider;
  - the "For TASK-027" list;
  - Review A of these records.
- docs/INVENTORY.md: a Decisions row for BUG-034's accepted round-1 assumption (few()'s sorted order), which the "accepted" disposition requires.
- docs/REQUIREMENTS.md: R-037's Evidence becomes partial. Its status stays planned, since TASK-027 completes it.
- docs/PROJECT_STATUS.md: as at PR #107's merge (ISS-009). Next is TASK-027.
- docs/archive/STATUS_HISTORY.md: the parts of Last accepted moved out at BUG-035 and here.

## The evidence (outside the Workspace or gitignored)

- The record the plan asks for: Reports/Reviews/Claude-Cursor Bridge Release B Review.md, beside the Workspace, human-facing.
- The four reports: run/supervisor/task026-pass1-claude.md, task026-pass1-reviewB.txt, task026-pass2-claude.md and task026-pass2-reviewB.txt. They are gitignored because they quote this computer's folders.
- This file quotes their verdicts and figures. Review B may read the gitignored files in place but must write nothing.

## Out of scope

- TASK-027: the stamp, the CHANGELOG entry, calibrate-bridge.md's note and run sheet, and the install. This is later work, not this diff's defect.
- The installer's messages: C-1's refusal half and the dry-run tense. These are leads for a later reviewed change.

## Checks run

- inventory-check OK; completion-check --mode plan OK; plan-check RESULT OK with TASK-026 READY.
- test_release_b_bootstrap, test_text_consistency, test_completion_check: 27 passed, 1 skipped.
- The secret sentinel; the path scan before the push.
- Review A: APPROVE, with three Should fix taken (pass 2 Review B's Consider added; C-1's refusal half moved from TASK-027 to a lead; the two floors' calibration steps corrected) and its Considers taken.
- Review B's round 1 (snapshot TASK-026) rejected one omission: the list for TASK-027 lacked pass 2 Review B's constraint that the "previous ... kept at" line appears only on a version change. Fixed in commit "TASK-026 records: Review B's round 1" (HARDENING and the Reports record), the only change since round 1 apart from the review files. This is Review B's round 2, below the ceiling.
