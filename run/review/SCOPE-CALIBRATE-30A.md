# SCOPE - CALIBRATE-30A: the calibration to 2026.10.30a and TASK-027's records

Release B (2026.10.30a) was stamped by TASK-027 (PR #108) and installed by the owner on 2026-10-30, by the run sheet (this checkout on `main`, nothing running). `bridge-check.py` on the installed tree: 147 OK. The owner then ran `/calibrate-bridge`.

This pull request carries that calibration's records and TASK-027's, on branch calibrate-30a from origin/main f2828c9. It is a records pull request: no program, no test, no governance text changes. Its title does not start with a plan ID, since TASK-027 merged with PR #108 and its trial is still to come (ISS-013: no plan ID inside a closing parenthesis either).

## How the calibration ran

The status file's `Bridge version:` line already read 2026.10.30a: it moved with the stamp in PR #108 (CI's conformance test needs the stamped tree's project calibrated, as at HOTFIX-002). So calibration's step 3 found no delta, and the no-delta path runs no step 4. The entry's last Running projects must item covers this case: such a project applies the items by hand. This calibration did so. Each item, sorted by calibrate-bridge.md's step 4 (Phase: building):

1. *(all phases)* Install, restart, calibrate, bridge-check: done.
2. *(all phases)* Re-read: the core in parts, delegation-loop.md with its two sub-files, reflection.md, project-end.md, the merge policy, the pitfalls, and the conditional workflows the `Workflows:` line names (host-extension.md, host-extension/claude-code-extension.md, traits/installable.md).
3. *(all phases)* The two MISSING floors: the `Workflows:` line exists and passes workflow-check; the windowless floor is OK (tests/conftest.py holds the default since FIX-001 and TASK-028). Nothing to write.
4. *(building, changing)* An increment in flight: none (the install was at a merge boundary), so no rounds record was seeded.
5. *(building, changing)* Numbered briefs: in force from the next brief.
6. *(building, changing)* The ceiling held by the programs: the by-hand rule (INVENTORY, Decisions, the 2026-10-25 row) is marked met and retired; the status file's Next says so.
7. *(building, changing)* One heavy job at a time: in force; the status file's Next no longer says a builder waits for a suite by hand.
8. *(all phases)* The conditional workflows: host extension's `delegation-loop.test-checks` binds from the next brief; no `configuration.items` apply to host extension, Claude Code extension or installable; the intake, design and planning additions wait for the next design phase or change cycle; `project-end.delivery` for host-installation runs at project end. This project had no `Delivery kind:` row, so it is written now (a record-keeping addition, the item's last sentence).
9. *(all phases)* The `Bridge version:` line: already 2026.10.30a; the Calibrated line records the by-hand path.

## Scope (the records)

- docs/INVENTORY.md:
  - a Decisions row `Delivery kind: the bridge (its one part, Claude-Cursor Bridge) host-installation`, the format design.md asks ("a Decisions row that begins `Delivery kind:`, naming each part and its kind's key");
  - the by-hand ceiling row's "Revisit only if" cell marked met;
  - the Updated date.
- project.json: `version` and `state.bridge` 2026.10.30a, the stage text, the date. The conformance check's NOTE on project.json's bridge version clears (now 23 OK, 1 MISSING, 6 NOTE).
- docs/PROJECT_STATUS.md, as at this pull request's merge (ISS-009):
  - Increment none; Last accepted names PR #109;
  - Awaiting user on: TASK-027's trial (reAngle's calibration, run by the owner in its own session);
  - Next: the trial's field acceptance, the other projects' calibrations, then stage B6's close and project end;
  - the Calibrated and Calibration pending lines. They fix the wording Review B's round 5 of TASK-027 named: the no-delta path runs no step 4, and the items are applied by hand.
  - Open issues: ISS-015 fixed, since the programs now hold the ceiling.
  - the Conformance notes, Stage and Remote sync lines.
- docs/archive/STATUS_HISTORY.md: the status text moved out (Last accepted's older part, the old Calibrated and Open issues lines).
- docs/REQUIREMENTS.md:
  - R-038 built: the owner's settlement, the run sheet pinned by tests/test_release_b_stamp.py's test_r038_ tests, the install made by it;
  - R-037 and R-031 stay planned, their Evidence extended (the stamp, the install, this calibration). The trial, field acceptance and the other projects' calibrations are to come.
- docs/HARDENING.md: a new section, "TASK-027, the stamp and the install":
  - the five rounds and their dispositions;
  - round 5's wording label, drawn as the tail past the ceiling;
  - the lesson on the CI-only status tests;
  - the install's facts.

## Out of scope

- reAngle's, the video factory's and the TDP's calibrations: each is run in its own session. They are TASK-027's trial, to come.
- Stage B6's close and project end.
- The installer's message leads (C-1's refusal half, the dry-run tense): HARDENING leads for a later reviewed program change.

## Expected files in the diff

Only the six files above, and the review files under run/review/ (this file, the round's diff and assumptions file), which are removed before the merge.

## Checks run

- inventory-check: OK (status 11,530 of 12,000 characters).
- completion-check --mode plan: OK (42 built, 2 planned).
- workflow-check --status: OK.
- conformance-check: 23 OK, 1 MISSING (no diagram index, a recorded decision), 6 NOTE, and `Calibrated to the installed bridge (2026.10.30a)` OK.
- Tests run as CI runs them (GITHUB_REF=refs/pull/109/merge, GITHUB_BASE_REF=main, GITHUB_EVENT_NAME=pull_request; the lesson recorded in HARDENING): release_b_bootstrap, calibrate_program, release_b_stamp, completion_check, text_consistency, 50 passed.
- The invisible-character check and the secret sentinel; the path scan before the push.
- Review A, round 1: APPROVE, with two Should fix and five Consider findings, all taken in the commit "supervisor: Review A's findings on the calibration records":
  - S1: the HARDENING lesson said both CI failures escaped by being skipped locally. Only test_r001 is gated on the GitHub variables. test_r027_r033 has no gate; test_calibrate_program.py was simply in none of TASK-027's local selections. The lesson now says so, and its remedy is every test that reads the status file, project.json or VERSION, or the full suite, with the variables set.
  - S2: the Delivery kind row summarised project end's procedure short of host-extension.md:17. It now names all its obligations: the host-load check, the take-back proved once on a host kept apart, and the User Manual chapter.
  - C1: the conformance line says "the same MISSING and NOTEs as at stage B5's close", not the same counts.
  - C2: the install facts name the kept copy, which is the hotfix's tree.
  - C3: rounds 4 and 5's class lines are no longer quoted in shortened form. Round 5's result is appended to the TASK-027 scope record (gitignored).
  - C4: Next says that, until the design's host section exists, a brief records the `claude --version` it tests on.
  - C5: R-037's evidence says "this checkout paused and switched to `main`", not "the projects paused".
- After those fixes, the full suite with GITHUB_REF=refs/pull/109/merge, GITHUB_BASE_REF=main and GITHUB_EVENT_NAME=pull_request: 3,262 passed and 40 skipped (launch 2026-10-30T03:59:49Z).
