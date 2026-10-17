# Project Status
Last updated: 2026-10-17
Phase: building
Workflows: Host Extension Development → Claude Code Extension; traits: Installable
Change cycle: none
Increment: BUG-008 — stage B2's review, round 7 (branch bug-008; the supervisor's fixtures, tests, two text sentences and the widened sweep, no program change): Review B APPROVE; Review A's tests part (the judges' output: only the first finding or cause, a registry error ignored) and fixtures part 2 (the four forms loosened by a regex literal) rejected, fixtures 4 and 5 converged on status-line rules no test fails for; the widened sweep (regex literals, widened string comparisons, slices, join separators, and the two judges) found the rest; dispositions in HARDENING, "the stage review (round 7)"; ISS-007 opened. Gate round 1: Review B APPROVE, Review A REJECT (the "yes" class and lines 203, 553, 625 separable; the sweep's comparison operator too narrow), decided for Review A; r2 widens the sweep to every comparison both ways and adds the cases (HARDENING, "BUG-008's gate round 1")
Last accepted: BUG-007, at commit e20382a (merged to main 2026-10-17, PR #33); main holds TASK-001 to TASK-009, BUG-001, the refactoring pass, BUG-002 and its records, BUG-003, BUG-004, BUG-005, BUG-006, BUG-007
Awaiting user on: deleting the logs of three PR #16 runs (38241764324, 38244794839, 38309209568) that still show 5 characters of the Socket key, and replacing the key (run sheet given 2026-10-16, run/supervisor/runsheet-socket-key-2026-10-16.md); blocks only stage B1's close, not the build
Previously: stage B1's review (2026-10-16) — Review A and Review B both REJECT: this file was stale on main (fixed here), the stage tests were too weak (fixed here), the Socket key was in the environment while npm installed the CLI (BUG-001), and three key-bearing logs survived the owner's deletion of 2026-10-13 (the owner's run sheet). Paused by the owner 2026-10-13 (weekly usage limit); resumed 2026-10-16 on the owner's word, relayed by the maintainer, with "usage reset".
Next: BUG-008 through the gate; then stage B2's review again from its step 1 (rounds 1 to 7 rejected; round 7: the class the widened sweep now covers); then the demonstration and the reflection items (item 3 also copies the per-part lead into the Restructuring Plan's §16, see HARDENING; item 1 completes ISS-007); then stage B3 (TASK-016 first); once the owner reports the logs deleted and the key replaced, stage B1's review runs again on B1's whole change (9e181e6, fba63bc, 6743b25, 4d0f77b), then its reflection items.
Deviations accepted: none
Terms fixed: conditional workflow — a type, sub-type or trait file that adds to the main workflow at extension points; a type or sub-type file may also set values where a point allows or replace a whole module the registry marks replaceable — Risky (sense revised 2026-10-17; re-anchor at the next report); extension point — a named place in a phase module where any type, sub-type or trait file may add, and a type or sub-type file may set a value where the point allows; a replacement swaps a whole module instead — Risky (sense revised 2026-10-17; re-anchor at the next report); phase module — one file holding one part of the workflow's procedure; a phase uses one or more modules — Risky (sense revised 2026-10-17; re-anchor at the next report)
Software name: Claude-Cursor Bridge
Layout: Workspace=E:\p18-claude-cursor-bridge\Workspace  Documents=E:\p18-claude-cursor-bridge\Documents
Worktrees: none
In flight: none
Working files: run/supervisor/ (local, gitignored; this file carries what a resume needs, those files hold the detail: the owner's run sheet runsheet-socket-key-2026-10-16.md, maintainer-b2.md, the mutation drivers mutate_ci_floor.py, mutate_workflow_check.py and mutate_workflows_line.py, the operator sweep sweep_workflow_check.py, drafts/, in-flight.md as a scratch log while a review runs)
Delegated gates: none
Remote sync: main at e20382a, in sync 2026-10-17; branch bug-008 started from origin/main
Stage: B1 (supervised-project bootstrap) — closing; its stage review is to be repeated. Last reflection: none yet (intake 2026-10-11)
Open issues: ISS-007 open (stage B2's review rejected seven rounds on one class, rules of the workflow check no test fails for; BUG-008 widens the sweep); ISS-002 fixed 2026-10-13; ISS-005 fixed in code, its remaining logs and key replacement are the owner's, see Awaiting; ISS-006, a roster-check test reading the Workspace's run log, fixed in 6743b25
Maintainer requests: Release B2 recorded as a post-B release (owner confirmed 2026-10-12; run/supervisor/maintainer-b2.md); FB-nnn closure at the first stage close
Bridge version: 2026.10.11d
Calibrated: n/a — the bridge runs the installed 2026.10.11d it is the source of; intake 2026-10-11
Calibration pending: none
Conformance notes (2026-10-16, stage B1 close): MISSING for the bridge as a project — the Workspace boundary rule, the secure-coding rule, the boundary-check hook, the windowless check in the hooks (all `.cursor/` builder configuration), and the diagram index (No diagram index is a recorded decision); configuration items for the next stage
Run parameters: see docs/RUN_PARAMETERS.md (stage pause=run / merge authority=supervisor / refactoring pass=on / installer verification=n/a / parallel increments=off)

## Release B — notes for a resuming session
- This is the first release the bridge's own supervisor builds, as a supervised project (§15 condition 6). The design is the Restructuring Plan (Documents/Claude-Cursor Bridge Restructuring Plan.md), release B, §16 and §6.
- Roster: full profile (builder grok-4.7-medium, Review A claude-opus-5-5, Review B gpt-5.6-sol-high) since the owner's "usage reset" of 2026-10-16; the native profile (builder composer-2.5, Review B grok-4.7-medium) ran 2026-10-12 to 2026-10-16.
- Stage B1 (TASK-001, TASK-002) merged after stage B2's TASK-003 to TASK-007, because TASK-002 waited on the owner's Socket variable; B1's change is its own squash commits (9e181e6, fba63bc, and BUG-001's), not a range of main.
- `security floor` is a required check on main since 2026-10-13 (the owner's yes).
- Merge authority = supervisor — the supervisor completes each gated merge with bare `gh pr merge --squash --match-head-commit` (piped/compound forms fall to the classifier; --admin/force stay refused).
- One writer at a time (§15 condition 2): while this supervisor builds, the maintainer session must not touch this repo.
- Governance text is authored by the supervisor and gated by the two-critic design review; programs are delegated to the builder and gated by the delegation loop (§15 condition 3).
