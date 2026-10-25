# Status history

Lines moved out of docs/PROJECT_STATUS.md to keep it under its cap (inventory-check.py), newest first, each word for word as it stood.

## Moved 2026-10-25 (HOTFIX-002, the calibration to 2026.10.25a)

Calibrated: 2026-10-19 from 2026.10.11d to 2026.10.18a — applied: the design critique's ceiling (no design, plan or change critique is running here: release B's plan critique and the hotfix's both closed at their gates, so no subject takes a token and no round file is renamed; it does not reach a code-gate stage review, which stays under standing rule 6's by-class brake), project.json's state; pending: none (the conformance MISSING items were applied at stage B3's start by CFG-B3 and CONFIG-B3b, below); not applied (gate passed): none

Calibration pending: none (the conformance check after CONFIG-B3b, 2026-10-19: 22 OK / 1 MISSING, the recorded no-diagram-index decision / 5 NOTE). Applied 2026-10-19 by CONFIG-B3b (PR #49): the generated command reference docs/cli-reference.json and its CI check (rule 32). Applied 2026-10-19 by CFG-B3: the Workspace boundary rule, the secure-coding rule (ASVS 5.0.0, L2), the boundary-check hook (configured; it does not run in builder runs, ISS-010) and the windowless pre-commit gate (conformance then 21 OK / 2 MISSING: the command reference and the recorded no-diagram-index decision; one of the OK floors, the boundary-check hook, is a floor configured but not engaging, ISS-010 and FB-025, and the supervisor's outside-write check stands in for it, INVENTORY Decisions)

Conformance notes (2026-10-19, calibration): the diagram index is MISSING (No diagram index is a recorded decision); NOTE the repository is public; NOTE the design exists under other names (DESIGN_CRITIQUE.md), for the diagram retrofit; NOTE a messaging token of the desktop app is in the session's environment (the launcher withholds it from builder and reviewer runs); NOTE two private memory folders, reviewed at calibration step 2b
