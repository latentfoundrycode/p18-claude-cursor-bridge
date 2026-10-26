# Status history

Lines moved out of docs/PROJECT_STATUS.md to keep it under its cap (inventory-check.py), newest first, each word for word as it stood.

## Moved 2026-10-25 (HOTFIX-002, the calibration to 2026.10.25a)

Calibrated: 2026-10-19 from 2026.10.11d to 2026.10.18a — applied: the design critique's ceiling (no design, plan or change critique is running here: release B's plan critique and the hotfix's both closed at their gates, so no subject takes a token and no round file is renamed; it does not reach a code-gate stage review, which stays under standing rule 6's by-class brake), project.json's state; pending: none (the conformance MISSING items were applied at stage B3's start by CFG-B3 and CONFIG-B3b, below); not applied (gate passed): none

Calibration pending: none (the conformance check after CONFIG-B3b, 2026-10-19: 22 OK / 1 MISSING, the recorded no-diagram-index decision / 5 NOTE). Applied 2026-10-19 by CONFIG-B3b (PR #49): the generated command reference docs/cli-reference.json and its CI check (rule 32). Applied 2026-10-19 by CFG-B3: the Workspace boundary rule, the secure-coding rule (ASVS 5.0.0, L2), the boundary-check hook (configured; it does not run in builder runs, ISS-010) and the windowless pre-commit gate (conformance then 21 OK / 2 MISSING: the command reference and the recorded no-diagram-index decision; one of the OK floors, the boundary-check hook, is a floor configured but not engaging, ISS-010 and FB-025, and the supervisor's outside-write check stands in for it, INVENTORY Decisions)

Conformance notes (2026-10-19, calibration): the diagram index is MISSING (No diagram index is a recorded decision); NOTE the repository is public; NOTE the design exists under other names (DESIGN_CRITIQUE.md), for the diagram retrofit; NOTE a messaging token of the desktop app is in the session's environment (the launcher withholds it from builder and reviewer runs); NOTE two private memory folders, reviewed at calibration step 2b

Last accepted, the part moved out at BUG-028 (2026-10-26): stage B4's close records (PR #82); BUG-027 (PR #81) to BUG-021 (PR #75): the stage review's rounds 7 to 1; REFAC-B4 (PR #74); BUG-020 (PR #73, ISS-014); TASK-021 (PR #72) to TASK-017 (PR #68) and TASK-022 (PR #66): the stage's increments; the stage B4 plan revision (PR #67, approved 2026-10-24), FIX-004 (PR #65) and the pace plan revision (PR #64)

Maintainer requests, the part moved out at BUG-028 (2026-10-26): Earlier: the pace update (2026-10-20; run/supervisor/maintainer-pace.md): a code-review round ceiling, one mutation run per increment, a pace report; placed by the owner on 2026-10-22 ("a": stage B5 beside TASK-028 to TASK-031; INVENTORY, Decisions), the maintainer told; designed as R-042 to R-044 and TASK-032 to TASK-035 and approved 2026-10-24 with the ceiling at three ("I choose three"). Earlier: the windowless fix (TASK-028 to TASK-031, PR #57); Release B2 (FB-021; INVENTORY, Decisions)

Last accepted, the part moved out at TASK-028 (2026-10-26): before it TASK-024 (PR #86): calibration aware of conditional workflows, the program half of R-027 and the calibration half of R-033 (the conformance check reports a line naming an unwritten workflow, an unwritten trait, and an unclassified project past intake); before it TASK-023 (PR #85), the text half; before it HOTFIX-002 (PR #84): hotfix 2026.10.25a (release/2026.10.11's c0822c0, PR #83) carried onto main and the project calibrated to it

Last accepted, the part moved out at TASK-029 (2026-10-26): before it BUG-028 (PR #87): the review-guard test fixture records the guard's own sleeps only, so Linux CI no longer fails at random on the lagging-head test (ISS-016)
