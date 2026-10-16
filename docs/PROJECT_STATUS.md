# Project Status
Last updated: 2026-10-16
Phase: building
Workflows: Host Extension Development → Claude Code Extension; traits: Installable
Change cycle: none
Increment: none — stage B1 close in progress (branch stage-b1-close)
Last accepted: TASK-002 at commit fba63bc (merged to main 2026-10-13)
Awaiting user on: nothing (open, not blocking: replacing the Socket key SOCKET_SECURITY_API_KEY is recommended — 5 characters of its secret part were in six public CI logs, which the owner deleted 2026-10-13; a run sheet on request)
Previously: paused by the owner 2026-10-13 (weekly usage limit); resumed 2026-10-16 on the owner's word, relayed by the maintainer, with "usage reset" (roster back on the full profile). The owner set the repository variable SOCKET_ORG_SLUG = latent-foundry on 2026-10-12 (verified); PR #16 had been approved at e9299e6, and conflicted with main only on this file. Paused by the owner twice on 2026-10-12 for app restarts; resumed on the owner's word each time (relayed by the maintainer). Owner decided 2026-10-12: Semgrep runs the OSS engine with explicit rulesets and no token. B2 confirmed 2026-10-12 as a post-B release.
Next: stage B1's close (TASK-001, TASK-002 merged): refactoring pass, stage review (Review A + Review B on B1's whole change), demonstration, reflection items; then stage B2's remaining increments TASK-006, TASK-008, TASK-009, and TASK-016 (stage B3) as plan-check orders them. `security floor` is a required check on main since 2026-10-13 (owner's yes).
Deviations accepted: none
Terms fixed: conditional workflow — a type/sub-type/trait file that changes the main workflow only at extension points — New; extension point — the one named place a conditional workflow may change a phase — New; phase module — one file holding one phase's whole procedure — New
Software name: Claude-Cursor Bridge
Layout: Workspace=E:\p18-claude-cursor-bridge\Workspace  Documents=E:\p18-claude-cursor-bridge\Documents
Worktrees: none
In flight: none
Working files: run/supervisor/ — in-flight.md (the position; read first on resume), drafts/ (the supervisor's drafts), task-002-reviewA.md, maintainer-b2.md, mutate_ci_floor.py, gpt-usage-limit.err
Delegated gates: none
Remote sync: in sync at 2026-10-16 (main at fba63bc, #16 merged); branch stage-b1-close not yet pushed
Stage: Release B — Last reflection: none yet (intake 2026-10-11)
Open issues: ISS-002 (TASK-002's rounds; open until #16 merges)
Maintainer requests: Release B2 recorded as a post-B release (owner confirmed 2026-10-12; run/supervisor/maintainer-b2.md); FB-nnn closure at the first stage close
Bridge version: 2026.10.11d
Calibrated: n/a — the bridge runs the installed 2026.10.11d it is the source of; intake 2026-10-11
Calibration pending: none
Run parameters: see docs/RUN_PARAMETERS.md (stage pause=run / merge authority=supervisor / refactoring pass=on / installer verification=n/a / parallel increments=off)

## Release B — notes for a resuming session
- This is the first release the bridge's own supervisor builds, as a supervised project (§15 condition 6). The design is the Restructuring Plan (Documents/Claude-Cursor Bridge Restructuring Plan.md), release B, §16 and §6.
- Roster: full profile in use again since 2026-10-16 (builder grok-4.7-medium, Review A claude-opus-5-5, Review B gpt-5.6-sol-high), after the owner's "usage reset"; the native profile (builder composer-2.5, Review B grok-4.7-medium) ran 2026-10-12 to 2026-10-16.
- Stage B1 (TASK-001, TASK-002) merged last, after stage B2's TASK-003 to TASK-007, because TASK-002 waited on the owner's Socket variable; B1's close runs on its two squash commits (9e181e6, fba63bc).
- Merge authority = supervisor — the supervisor completes each gated merge with bare `gh pr merge --squash --match-head-commit` (piped/compound forms fall to the classifier; --admin/force stay refused).
- One writer at a time (§15 condition 2): while this supervisor builds, the maintainer session must not touch this repo.
- Governance text is authored by the supervisor and gated by the two-critic design review; programs are delegated to the builder and gated by the delegation loop (§15 condition 3).
