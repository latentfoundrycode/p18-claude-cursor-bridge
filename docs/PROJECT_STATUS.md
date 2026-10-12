# Project Status
Last updated: 2026-10-12
Phase: building
Workflows: Host Extension Development → Claude Code Extension; traits: Installable
Change cycle: none
Increment: TASK-007 — The `Workflows:` status line (branch task-007, started 2026-10-12 while PR #16 waits)
Last accepted: TASK-005 at commit 82f0e44 (merged to main 2026-10-12)
Awaiting user on: the repository variable SOCKET_ORG_SLUG (their Socket organization slug; run sheet given 2026-10-12; still unset at the resume check 2026-10-12; the owner asked what the slug is and was told 2026-10-12: the name after /org/ in the Socket dashboard's address, likely `latent-foundry`, theirs to confirm). PR #16 (TASK-002, branch task-002) has passed every other gate condition — Review A and Review B (second round) APPROVE, secret-sentinel CLEAR, spec test 12/12, premerge OK at head e9299e6. On "variable set": re-run the PR's failed CI job, confirm all checks green on e9299e6 (read the Socket step log), merge bare (`gh pr merge 16 --squash --match-head-commit e9299e62773f86d3a8c3494951dd670a359b807d`), mark runs healthy, sync main, then make the `security floor` job a required check.
Previously: paused by the owner twice on 2026-10-12 for app restarts; resumed on the owner's word each time (relayed by the maintainer). Owner decided 2026-10-12: Semgrep runs the OSS engine with explicit rulesets and no token. B2 confirmed 2026-10-12 as a post-B release.
Next: TASK-007 round 2 (snapshot 007b: Review A + Review B on round 1's Should fix and Consider items), CI, premerge and the merge; then TASK-008 (the builder's check of the `Workflows:` line) and TASK-009 (the glossary); merge #16 when the variable is set (it then needs origin/main merged in and a re-review, since TASK-003 and later increments changed this file); TASK-006 follows #16.
Deviations accepted: none
Terms fixed: conditional workflow — a type/sub-type/trait file that changes the main workflow only at extension points — New; extension point — the one named place a conditional workflow may change a phase — New; phase module — one file holding one phase's whole procedure — New
Software name: Claude-Cursor Bridge
Layout: Workspace=E:\p18-claude-cursor-bridge\Workspace  Documents=E:\p18-claude-cursor-bridge\Documents
Worktrees: none
In flight: none
Working files: run/supervisor/ — in-flight.md (the position; read first on resume), drafts/ (the supervisor's drafts), status-task002-wip.md (task-002's status copy), task-002-reviewA.md, maintainer-b2.md, mutate_ci_floor.py, gpt-usage-limit.err
Delegated gates: none
Remote sync: in sync at 2026-10-12 (main at 82f0e44); task-002 pushed at e9299e6; task-007 pushed as PR #20 (round 2 under review)
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
- Two branches live: task-002 (PR #16, reviewed, waiting on the owner's variable) and task-007 (in progress). TASK-003 merged first, so #16 now takes `main` in before it merges, and its new head is re-reviewed (policy: an updated branch is a new head).
- Merge authority = supervisor — the supervisor completes each gated merge with bare `gh pr merge --squash --match-head-commit` (piped/compound forms fall to the classifier; --admin/force stay refused).
- One writer at a time (§15 condition 2): while this supervisor builds, the maintainer session must not touch this repo.
- Governance text is authored by the supervisor and gated by the two-critic design review; programs are delegated to the builder and gated by the delegation loop (§15 condition 3).
