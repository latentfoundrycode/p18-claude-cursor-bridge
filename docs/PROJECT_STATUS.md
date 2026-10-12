# Project Status
Last updated: 2026-10-12
Phase: building
Workflows: Host Extension Development → Claude Code Extension; traits: Installable
Change cycle: none
Increment: TASK-002 — The security floor in the bridge's CI (PR #16, branch task-002, origin/main merged in 2026-10-12; re-review of the new head)
Last accepted: TASK-007 at commit d4023f6 (merged to main 2026-10-12)
Awaiting user on: nothing
Previously: the owner set the repository variable SOCKET_ORG_SLUG = latent-foundry on 2026-10-12 (verified); PR #16 had been approved at e9299e6, and conflicted with main only on this file. Paused by the owner twice on 2026-10-12 for app restarts; resumed on the owner's word each time (relayed by the maintainer). Owner decided 2026-10-12: Semgrep runs the OSS engine with explicit rulesets and no token. B2 confirmed 2026-10-12 as a post-B release.
Next: PR #16's re-review (snapshot 002c: Review A + Review B on the merged head), CI, premerge and the merge; then the `security floor` job made a required check on main; then TASK-006 (now unblocked), TASK-008 and TASK-009 as plan-check orders them.
Deviations accepted: none
Terms fixed: conditional workflow — a type/sub-type/trait file that changes the main workflow only at extension points — New; extension point — the one named place a conditional workflow may change a phase — New; phase module — one file holding one phase's whole procedure — New
Software name: Claude-Cursor Bridge
Layout: Workspace=E:\p18-claude-cursor-bridge\Workspace  Documents=E:\p18-claude-cursor-bridge\Documents
Worktrees: none
In flight: none
Working files: run/supervisor/ — in-flight.md (the position; read first on resume), drafts/ (the supervisor's drafts), status-task002-wip.md (task-002's status copy), task-002-reviewA.md, maintainer-b2.md, mutate_ci_floor.py, gpt-usage-limit.err
Delegated gates: none
Remote sync: in sync at 2026-10-12 (main at d4023f6, #20 merged); task-002 to be pushed with main merged in (PR #16)
Stage: Release B — Last reflection: none yet (intake 2026-10-11)
Open issues: ISS-002 (TASK-002's rounds; open until #16 merges)
Maintainer requests: Release B2 recorded as a post-B release (owner confirmed 2026-10-12; run/supervisor/maintainer-b2.md); FB-nnn closure at the first stage close
Bridge version: 2026.10.11d
Calibrated: n/a — the bridge runs the installed 2026.10.11d it is the source of; intake 2026-10-11
Calibration pending: none
Run parameters: see docs/RUN_PARAMETERS.md (stage pause=run / merge authority=supervisor / refactoring pass=on / installer verification=n/a / parallel increments=off)

## Release B — notes for a resuming session
- This is the first release the bridge's own supervisor builds, as a supervised project (§15 condition 6). The design is the Restructuring Plan (Documents/Claude-Cursor Bridge Restructuring Plan.md), release B, §16 and §6.
- Roster: native profile in use (builder composer-2.5, Review A claude-opus-5-5, Review B grok-4.7-medium). The Other Models pool is marked exhausted (gpt-5.6-sol-high returned a usage limit; recorded 2026-10-12); automatic reset due 2026-10-16 00:00 UTC (reset day 16), or earlier when the owner says "usage reset".
- One branch live: task-002 (PR #16). TASK-003 to TASK-007 merged first, so #16 took `main` in and its new head is re-reviewed (policy: an updated branch is a new head).
- Merge authority = supervisor — the supervisor completes each gated merge with bare `gh pr merge --squash --match-head-commit` (piped/compound forms fall to the classifier; --admin/force stay refused).
- One writer at a time (§15 condition 2): while this supervisor builds, the maintainer session must not touch this repo.
- Governance text is authored by the supervisor and gated by the two-critic design review; programs are delegated to the builder and gated by the delegation loop (§15 condition 3).
