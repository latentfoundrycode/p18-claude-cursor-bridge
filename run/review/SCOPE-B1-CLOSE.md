# SCOPE — B1-CLOSE (the records that close stage B1)

A records-only pull request (PR #46): no program, no test, no workflow change. It records stage B1's close (supervisor.md, "Reflection points": the stage review, the demonstration, the reflection items).

## Scope

- `docs/HARDENING.md`, "Stage B1": the record of the stage review's round 4 (both reviewers APPROVE; no round 5, since round 4 had no REJECT: the stage close's step 7) and "Least confident (stage close, 2026-10-19)", three items each with the check that settles it (item 2b).
- `docs/INVENTORY.md`: the run-parameter row names the owner's four answers with their dates and says Installer verification follows the product type (round 4's Review A consider C1).
- `docs/REQUIREMENTS.md`: R-001's and R-002's evidence name their commits (ba1e181; 4d0f77b).
- `docs/PROJECT_STATUS.md`: written as it reads at this pull request's merge (the convention of ISS-009, checked by test_r001_status_names_its_own_merge): stage B1 closed, stage B3 next, its configuration items first; Last reflection stage B1's close.
- `project.json`: `state.stage`.

Review A of these records: APPROVE 0/1/4, all taken in commit 880d2bd (least-confident item 1 now names a check CI's output can show; item 2 carries FB-024's caution; the twelfth mutant of round 4 recorded; R-001's evidence names ba1e181; the working-files line current).

## Claims to check against git and GitHub

- Round 4: snapshot STAGE-B1 at 4db96c3 (parent ba1e181); the six squash commits 9e181e6, fba63bc, 6743b25, 4d0f77b, 1b8c8da, ba1e181.
- The demonstration: PR #45's run 39267616332 (pull request, head e27acd2) and main's push run 39268304307 (ba1e181) green on all three required checks, with equal per-leg counts (ubuntu 1619 passed / 26 skipped, windows 1622 / 23); a fresh session given only docs/PROJECT_STATUS.md and docs/INVENTORY.md at ba1e181 stated the position, the next step, the roster, who merges and the rules for the keys.
- Reflection: conformance-check --installable 17 OK / 6 MISSING / 5 NOTE (the MISSING items are the status file's Calibration pending items and the recorded no-diagram-index decision); completion-check --mode plan OK; no worktree. The Documents folder beside the Workspace (outside git) holds ISS-009 fixed, FB-022 to FB-024, and the Project Summary's stage B1 section.

## Out of scope

Stage B3's work, which starts after this merge. Design for later stages is not this diff's defect.

## Expected files in the diff

The five records above, and `run/review/` (these review files, removed before the merge).
