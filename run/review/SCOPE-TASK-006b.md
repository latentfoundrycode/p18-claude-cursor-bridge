# SCOPE-TASK-006b — the workflow check (PR #23), review round 2

The diff: `run/review/REVIEW-TASK-006b.diff` (`git diff origin/main...HEAD`, main at 4d0f77b). The brief: `handoff/TASK-006.md` (in the diff, read it whole). The builder: grok-4.7-medium, one round (run 2026-10-16T18:17:36Z); its report `handoff/TASK-006-r1-report.md`.

## Round 2: what changed since round 1's reviewed head (aa0891a)
Round 1: Review A REJECT (1/1/8), Review B REJECT (2/1/1), the security auditor PASS with 5 advisories; the findings and their disposition are in docs/DESIGN_CRITIQUE.md, "TASK-006 round 1 — disposition". `run/review/DELTA-TASK-006b.diff` (`git diff aa0891a HEAD`, review files left out) shows exactly what changed:
- e9a1db9 — round 1's review files removed.
- c2faf7a — checkpoint: the corrections brief `handoff/TASK-006-r2.md` (R2-1 to R2-14; `handoff/TASK-006.md` still holds except where it says otherwise), the supervisor's tests extended (17 new; 14 failed against round 1's program, the other three are guards that held: prose headings stay prose, an empty segment is form, and the unreadable-folder test, which is POSIX-only and runs on CI's ubuntu leg), and round 2's fixtures (two of them deliberately begin with a UTF-8 byte-order mark).
- d64141b — the builder's round 2 (run 2026-10-16T19:03:23Z): workflow-check.py and the manifest; its report `handoff/TASK-006-r2-report.md`.
- eb7ec5c — records: round 1's grades and disposition.
Mutation driver (`run/supervisor/mutate_workflow_check.py`, not in the diff): 49 mutants, all killed (round 1's 30, the seven rules Review A found without a mutant, and twelve for round 2's rules). Full suite 1027 passed, 21 skipped (the unreadable-folder test on Windows, and test_allowlist.py's twenty prose lines). The workflow does not change this round; the pin is unchanged.

## Round 1's brief: Scope (the builder's)
- bridge/cursor-bridge/workflow-check.py
- .github/workflows/tests.yml — one step at the end of the `tests` (bridge programs) job, no secret, no env, no `if:`
- bridge/cursor-bridge/MANIFEST.json (regenerated; `VERSION` rewritten unchanged by the same tool)
- docs/BUILDER_NOTES.md, handoff/TASK-006-r1-report.md (bookkeeping)

## Out of scope (the brief's, quoted in short)
- The open list and the registry themselves; supervisor.md; settings.bridge.json; CHANGELOG/VERSION content.
- inventory-check.py / conformance-check.py reading the `Workflows:` line (TASK-008); the calibration run of the check (TASK-024, R-033's other half).
- The registry ↔ phase-module cross-check (TASK-014); reading `workflow/phases/`.
- A type or sub-workflow's statement of its default traits (no form exists yet).
- Reading a part's delivery kind (where it is recorded is TASK-011's question).
- The bridge's own `docs/PROJECT_STATUS.md`, never passed to the check in CI or a test.

## Written by the supervisor (tests and fixtures; each enforces docs/REQUIREMENTS.md R-014, the step test R-033)
- `tests/test_workflow_check.py` (59 tests), written from the brief's interface before the delegation (58 failed at the checkpoint 15c6a69, where no program existed; the one that passed is the guard that the check is not in the security floor). After the builder's run the supervisor changed two: `test_r014_registry_heading_missing` renamed the prose citation of the heading rather than the heading line (the builder reported it, rightly), and the `kind-missing` case now names its offending name (a driver mutant survived on it).
- `tests/fixtures/workflows/`: `pass/` (the CI root; every layer, a replaced module whose point a trait and a sub-workflow still add at, a fenced change heading, prose headings), `fail/<case>/` (one root per failing case, each checked against the bridge's real tables), `status/` (status-line cases with an open list of their own in which some entries are written).
- `tests/test_release_b_ci_floor.py`: `WORKFLOW_PIN` regenerated for the new step (the consequence recorded at BUG-001 round 5: an increment that changes the workflow regenerates the pin in the same diff). Compare the pin with the workflow yourself; nothing else in the file changed.
- Mutation driver (the supervisor's, not in the diff: `run/supervisor/mutate_workflow_check.py`): 30 mutants, each breaking one rule of the program in a temporary copy of the files the tests read; each killed by the tests named beside it.

## Records in the diff (expected)
- docs/PROJECT_STATUS.md (the position), docs/REQUIREMENTS.md (R-014 built; R-033's release half), docs/INVENTORY.md (the feature row), docs/HARDENING.md (PR #22 round 2's Consider: what each remedy for the key's reach costs), docs/DESIGN_CRITIQUE.md (PR #22 round 2; TASK-006's brief decisions).

## Results
Full suite 1011 passed, 20 skipped (the skips are tests/test_allowlist.py's prose lines, as on main); the check over the CI roots: RESULT: OK; windowless-check and bridge-check --sources: pass; secret-sentinel CLEAR.
