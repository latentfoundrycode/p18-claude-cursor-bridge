# SCOPE - CALIBRATE-30B: the calibration to 2026.10.30b and the trial's results

The fix release 2026.10.30b (BUG-036, PR #110: the review guard seeds no Review B round from a builder round release B's launcher logged) was installed by the owner on 2026-10-30, by the run sheet (this checkout on `main`, nothing running in any project). `bridge-check.py` on the installed tree: 147 OK, with 2026.10.30a kept as the way back. The owner then ran `/calibrate-bridge`.

This pull request carries that calibration's records and the trial's results so far, on branch calibrate-30b from origin/main cce651b. It is a records pull request: no program, no test, no governance text changes. Its title starts with no plan ID (ISS-013).

## How the calibration ran

The status file's `Bridge version:` line already read 2026.10.30b (it moved with the stamp in PR #110), so the no-delta path applied, and the 2026.10.30b entry's Running projects must items were applied by hand (Phase: building):

1. *(all phases)* Install paused, restart, calibrate, bridge-check: done (147 OK; `~/.claude/cursor-bridge-previous/2026.10.30a` exists).
2. *(building, changing)* Nothing to rewrite: no increment is in flight here, and no `rounds-<ID>.json` of this project holds a `seeded` round written by the 2026.10.30a guard. Nothing was set right.

Also run: the re-read of the governing files (the core in parts to its end, the building modules and sub-files, the three conditional workflows, the merge policy, configuration, pitfalls, delivery, the diagram conventions, the glossary, the skills); conformance (23 OK, 1 MISSING by recorded decision, 7 NOTE, the seventh being project.json's bridge version, set right here); the memory notes (3 read, 1 reduced). The roster check first printed FAIL: every probe answered `Authentication required` because Cursor's command-line tool had been signed out (ISS-020); no model failure was recorded, the owner signed in again, and the native profile resolved.

## Scope (the records)

- docs/PROJECT_STATUS.md, as at this pull request's merge (ISS-009): Increment none; Last accepted names PR #111; Awaiting user on: the TDP's report of 2026.10.30b's field check (the owner's word of 2026-10-30); Next; the Stage, Open issues (ISS-020), Remote sync, Calibrated, Calibration pending and Conformance notes lines; the Working files line compressed to fit the cap.
- docs/archive/STATUS_HISTORY.md: the replaced Last accepted, Awaiting user on, Next, Calibrated, Calibration pending and Conformance notes lines, word for word.
- project.json: `version` and `state.bridge` 2026.10.30b, the stage text.
- docs/REQUIREMENTS.md: R-031 and R-037 stay planned; their Evidence cells add the trial's four points met on 2026-10-30 (points 1 and 3 under the hand seed), the install of 2026.10.30b and this calibration. 2026.10.30b's own field acceptance (the TDP's next increment) and the resumes are still to come.
- docs/HARDENING.md: under BUG-036's section, the TDP's two further notes (the hook's bare no-wait values; the step 8 / decide.md reading of which count opens Review B's fifth clause, for release T); a new section, "The calibration to 2026.10.30b", with the roster check's usage advice for a signed-out tool (ISS-020).

## Out of scope

- The TDP's field check of 2026.10.30b (its next increment, TASK-158) and the resumes of reAngle and the video factory.
- Stage B6's close and project end.
- Any change to roster-check.py or to the governance text: HARDENING leads for later releases.

## Expected files in the diff

Only the five files above, and the review files under run/review/ (this file, the round's diff and assumptions file), which are removed before the merge.

## Tests and checks

No test was written: the change is records only.

- inventory-check: OK (status 11,995 of 12,000 characters); completion-check --mode plan: OK (42 built, 2 planned); workflow-check --status: OK.
- The full suite with GITHUB_REF=refs/pull/111/merge, GITHUB_BASE_REF=main and GITHUB_EVENT_NAME=pull_request, before Review A's fixes: 3,268 passed, 40 skipped; after them, again 3,268 passed, 40 skipped.
- Review A, round 1: APPROVE, three Should fix (R-037's "points 1 and 3 under the hand seed"; decide.md's two readings in the text-conflict bullet; the archive keeping every replaced line) and four Consider items, all taken. Confirming read: APPROVE, nothing new.
- The invisible-character check, the secret sentinel and the path scan before the push.
