# Project Status
Last updated: 2026-10-19
Phase: building
Workflows: Host Extension Development → Claude Code Extension; traits: Installable
Change cycle: none
Increment: none — this file states the position at stage B1's close records' merge (PR #46); stage B3 is next
Last accepted: stage B1's close records (PR #46, at its merge); before them BUG-016 at ba1e181 (PR #45) and BUG-015 at 1b8c8da (PR #44); main holds TASK-001 to TASK-009, BUG-001, the refactoring pass, BUG-002 to BUG-016, HOTFIX-001
Awaiting user on: none
Previously: stage B1 closed 2026-10-19 after four stage-review rounds — round 1 (2026-10-16) both REJECT (BUG-001); round 2 Review A REJECT (the bootstrap tests checked a word, not a record: BUG-015); round 3 Review B REJECT, Review A the same item, convergent (this file on main described its own pull request before the gate: BUG-016, ISS-009); round 4 both APPROVE.
Next: stage B3 (docs/BUILD_PLAN.md), its configuration items first (Calibration pending, through cursor-configurator as the bridge's own configuration checkpoint), then the least-confident tests of stage B2 (docs/HARDENING.md, "Stage B2 — least confident", items 2 and 3) before B3's first delegation, then TASK-016.
Deviations accepted: none
Terms fixed: conditional workflow — a type, sub-type or trait file that adds to the main workflow at extension points; a type or sub-type file may also set values where a point allows or replace a whole module the registry marks replaceable — Risky (sense revised 2026-10-17; re-anchor at the next report); extension point — a named place in a phase module where any type, sub-type or trait file may add, and a type or sub-type file may set a value where the point allows; a replacement swaps a whole module instead — Risky (sense revised 2026-10-17; re-anchor at the next report); phase module — one file holding one part of the workflow's procedure; a phase uses one or more modules — Risky (sense revised 2026-10-17; re-anchor at the next report)
Software name: Claude-Cursor Bridge
Layout: Workspace=E:\p18-claude-cursor-bridge\Workspace  Documents=E:\p18-claude-cursor-bridge\Documents
Worktrees: none
In flight: none
Working files: run/supervisor/ (local, gitignored; this file carries what a resume needs, those files hold the detail): write_stage_b1.py with SCOPE-STAGE-B1.md (round 3's; SCOPE-STAGE-B1-r2.md and -r1.md earlier rounds) for the stage review; the mutation drivers bug016_mutants.py, bug015_mutants.py, mutate_ci_floor.py, mutate_workflow_check.py, mutate_workflows_line.py and the sweeps of stage B2; demo_b2.py; drafts/; in-flight.md as the scratch log while a review runs; the hotfix's record in hotfix-position.md and hotfix/; the owner's run sheet runsheet-socket-key-2026-10-16.md; maintainer-b2.md
Delegated gates: none
Remote sync: main at the merge of PR #46, in sync with origin/main at that merge; local main is fast-forwarded after every merge (sync-check.py --apply)
Stage: B1 (supervised-project bootstrap) — closed 2026-10-19; B2 (conditional-workflow framework) — closed 2026-10-19; B3 next. Last reflection: stage B1's close, 2026-10-19 (demonstration passed: CI's full gate green on PR #45 and main's push of ba1e181, a fresh session resumed from this file and the inventory alone; conformance 17 OK / 6 MISSING, the Calibration pending items and the recorded no-diagram-index decision / 5 NOTE; completion-check --mode plan OK; no worktree; Issues ISS-009 completed; Feedback FB-022 to FB-024; least confident in HARDENING; Project Summary patched)
Open issues: none open. ISS-009 fixed 2026-10-19 (BUG-016; recurred twice); ISS-007 and ISS-008 fixed 2026-10-19; ISS-005 closed 2026-10-19; ISS-002 fixed 2026-10-13; ISS-006 fixed in 6743b25
Maintainer requests: none open (Release B2's request answered as FB-021 at stage B2's close, 2026-10-19; recorded as a post-B release in INVENTORY.md, Decisions)
Bridge version: 2026.10.18a
Calibrated: 2026-10-19 from 2026.10.11d to 2026.10.18a — applied: the design critique's ceiling (no design, plan or change critique is running here: release B's plan critique and the hotfix's both closed at their gates, so no subject takes a token and no round file is renamed; it does not reach a code-gate stage review, which stays under standing rule 6's by-class brake), project.json's state; pending: the conformance MISSING items @ stage B3's start (below); not applied (gate passed): none
Calibration pending: at stage B3's start, as configuration work — the Workspace boundary rule, the secure-coding rule, the boundary-check hook and the windowless check in the hooks (`.cursor/` builder configuration, recorded 2026-10-16), and the generated command reference docs/cli-reference.json (rule 32, newly reported 2026-10-19 under --installable)
Conformance notes (2026-10-19, calibration): the diagram index is MISSING (No diagram index is a recorded decision); NOTE the repository is public; NOTE the design exists under other names (DESIGN_CRITIQUE.md), for the diagram retrofit; NOTE a messaging token of the desktop app is in the session's environment (the launcher withholds it from builder and reviewer runs); NOTE two private memory folders, reviewed at calibration step 2b
Run parameters: see docs/RUN_PARAMETERS.md (the one record; the owner's four answers fixed by test_r001_run_parameters_owner_values)

## How this file is written (ISS-009)
Every pull request carries this file as it will read at that pull request's merge: Last accepted names the pull request first (by number; a squash cannot know its own hash), In flight is none, and Next is the step after the merge. tests/test_release_b_bootstrap.py, test_r001_status_names_its_own_merge, checks it in CI for pull requests into main and for squashes on main. Between merges the position lives in run/supervisor/in-flight.md, which a resume after a compaction reads first (this file's In flight reads none during a gate). Its costs: the post-merge steps (the healthy marks, sync-check.py --apply) are the loop's, not this file's Next; a revert pull request restores an older file and fails its own CI until the file is rewritten for it; a maintainer's pull request into main rewrites this file too.

## Stage B1, closed 2026-10-19
- Stage review: four rounds; round 4 (snapshot STAGE-B1, 4db96c3, hash 36eee2821606eec6, verify OK; stage/B1 deleted) Review B APPROVE with no findings, Review A APPROVE 0/0/3 (two taken in these records, one recorded as FB-024 and least-confident item 3). The record: docs/HARDENING.md, "Stage B1", rounds 2 to 4 and "Least confident (stage close, 2026-10-19)".
- B1's change is its own squash commits (9e181e6, fba63bc, 6743b25, 4d0f77b, 1b8c8da, ba1e181), not a range of main: stage B1 merged after stage B2's TASK-003 to TASK-007, because TASK-002 waited on the owner's Socket variable.

## Release B — notes for a resuming session
- This is the first release the bridge's own supervisor builds, as a supervised project (§15 condition 6). The design is the Restructuring Plan (Documents/Claude-Cursor Bridge Restructuring Plan.md), release B, §16 and §6.
- Roster: the native profile (builder composer-2.5, Review A claude-opus-5-5, Review B grok-4.7-medium) since 2026-10-18, on the owner's word ("use the alternative roster") after Cursor's Other Models pool was used up (ISS-008); the full profile (builder grok-4.7-medium, Review B gpt-5.6-sol-high) returns on 2026-11-16 UTC, or earlier if the owner says *usage reset*.
- The owner's re-plan of 2026-10-18 (the design critique's ceiling as hotfix 2026.10.18a first, then release B) is complete: the hotfix on main as e1a97de (PR #40), stage B2 closed 2026-10-19.
- `security floor` is a required check on main since 2026-10-13 (the owner's yes).
- Merge authority = supervisor — the supervisor completes each gated merge with bare `gh pr merge --squash --match-head-commit` (piped/compound forms fall to the classifier; --admin/force stay refused).
- One writer at a time (§15 condition 2): while this supervisor builds, the maintainer session must not touch this repo.
- Governance text is authored by the supervisor and gated by the two-critic design review; programs are delegated to the builder and gated by the delegation loop (§15 condition 3).
