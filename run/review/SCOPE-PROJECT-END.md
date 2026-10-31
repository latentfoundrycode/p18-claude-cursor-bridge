# SCOPE - PROJECT-END: project end's records (pull request #115)

Records only, written by the supervisor at project end (~/.claude/cursor-bridge/workflow/phases/project-end.md), after release B's last stage closed (PR #113) and BUG-038 (PR #114, 2026.10.30d). No program, test or shipped bridge text changes. Branch records/project-end from origin/main 50bc0cd (PR #114).

## What the records must do
- docs/REQUIREMENTS.md: R-031 and R-037 become `deferred - owner 2026-10-31`, the owner's answer in this project's chat ("The answer is yes", to recording reAngle's and the video factory's move to release B as deferred, dated, until they resume); each Evidence cell says only those two projects' calibrations and resumes are outstanding and keeps the rest of its evidence. completion-check.py reads a deferral as `deferred` plus `owner` and a date (its OWNER_DATED pattern).
- docs/diagrams/INDEX.md (new): the recorded decision "No diagram index for release B" (INVENTORY, Decisions, 2026-10-11) in diagram-check.py's form: all 18 catalogue kinds omitted, each with its reason, no diagram drawn, so `diagram-check.py --mode done` passes; the minimum set's retrofit is a lead in docs/HARDENING.md for the next design phase.
- docs/INVENTORY.md: a Decisions row for the index; a Deferred row for the two calibrations (the owner, 2026-10-31); Updated 2026-10-31.
- docs/HARDENING.md: Stage B6's least confident 3 settled (every bridge program and flag the two run sheets name is in docs/cli-reference.json; nothing added); a new section "Project end (2026-10-31)": the completion and diagram checks, and three least-confident items for the whole build with their checks.
- docs/PROJECT_STATUS.md as it will read at this pull request's merge (ISS-009; cap 12,000 characters): Phase: done; the calibration to the installed 2026.10.30d (the owner installed it on 2026-10-31; bridge-check 147 OK); the replaced lines moved to docs/archive/STATUS_HISTORY.md. project.json: phase done, state.bridge 2026.10.30d (now the installed version).

## What to check
- Each claim is true against the repository and the merged pull requests; run the checks yourself: the installed `~/.claude/cursor-bridge/completion-check.py --mode done` (RESULT: OK, 42 built, 2 deferred), `~/.claude/cursor-bridge/diagram-check.py --mode done` (RESULT: OK, 18 kinds omitted), `~/.claude/cursor-bridge/conformance-check.py` (24 OK, 0 MISSING, 6 NOTE, as the status file says), `python -B bridge/cursor-bridge/inventory-check.py`, `tests/test_release_b_bootstrap.py` with the pull-request variables for PR #115.
- A deferral is the owner's alone (supervisor.md, "Escalate to the user when", Scope): the rows must name the owner and the date, and claim no more than the owner's answer. The index must state the decision of 2026-10-11 and draw nothing.
- The records agree with each other; no computer path or user name in a tracked file (rule 54). The Documents/ folder (the User Manual, the Issues and Feedback entries, the Proposed bridge changes, the Project Summary) is outside git and not part of this diff.

## Before this round
- The full suite with the pull-request variables for PR #115 (commit 71d6a32): 3276 passed, 40 skipped, 1 failed (test_r001_no_deferred_row_reopens_a_settled_decision: the new Deferred row's last cell read `none`, not `no`); fixed in faf6f39, and tests/test_release_b_bootstrap.py with the same variables passed (14).
- Review A's round 1 rejected: the archive's project-end section held a branch-only Next line in place of main's PR #114 Next line, and lacked main's Awaiting line (both now kept word for word); the index's class and object-state reasons overstated; R-031 cited INVENTORY, Decisions for the deferral; HARDENING's project end item 2 read as still to come; the Open issues line had dropped ISS-020's pointer. All fixed in 4eb9f67; Review A's confirming read approved.
- `sync-check --strict IN SYNC` on the Stage and Remote sync lines is the post-merge step, run before the "Project complete" report (ISS-009: the file reads as at this pull request's merge).

Later releases (T, B2, the progress graph, W) are later work, not this pull request's defect. This is Review B's round 1, below the ceiling.
