# SCOPE - TASK-027

TASK-027 (docs/BUILD_PLAN.md, stage B6; R-031, R-037, R-038) is release B's install run sheet, its stamp, the install and the trial. Its author is the supervisor for the text and the stamp, all records, with no builder run. This pull request is the stamp half, on branch task-027 from origin/main 920447b. The install (the owner's run sheet), the calibrations, the reAngle trial and the other projects follow the merge and are not in this diff.

## Scope (the plan's, all in this diff)

- bridge/cursor-bridge/CHANGELOG.md: the new entry `## 2026.10.30a`, first, above 2026.10.25a. It has a lead naming release B, **What changed**, **Running projects must** (phase-marked; the windowless default, its floor and snapshot among them), **If rolled back** (on its own line, which bridge-install.py's rolled_back_note reads) and **Field acceptance**. Its items carry TASK-026's "For TASK-027" list (docs/HARDENING.md) and M3: what the installed review guard reads and counts for an increment whose snapshot or rounds were taken under 2026.10.25a.
- bridge/cursor-bridge/VERSION and MANIFEST.json: stamped 2026.10.30a by tools/make-manifest.py after the last edit (144 files).
- bridge/commands/calibrate-bridge.md: three additions.
  - (a) Step 1's run sheet: R-038's pause and switch, where the bridge's own repository is being built on a branch.
  - (b) Step 1's run sheet: the install checked on the real run, not a dry run, by the new VERSION and the `previous <version> kept at` line; BUG-034's same-version refusal named, with `--anyway` never passed by the owner, who tells the maintainer instead (C-1's run-sheet half).
  - (c) Step 4: a rule sending an increment in flight under the older release to the entry's items.
- tests/test_release_b_stamp.py (new, supervisor-written; names R-037 and R-038). Seven tests:
  - test_r037_version_changelog_and_manifest_agree: VERSION, the newest heading, make-manifest's pick and MANIFEST's version agree, and the manifest's hashes of VERSION and CHANGELOG are those of the files.
  - test_r037_the_new_version_sorts_after_2026_10_25a: the new heading is first, directly above 2026.10.25a, and sorts last as text.
  - test_r037_the_entry_has_its_three_parts_and_its_rolled_back_items_reach_the_installer: the four part titles are on lines of their own and in order, each holds items, the lead names release B, and bridge-install.py's rolled_back_note writes every If rolled back item for a rollback to 2026.10.25a.
  - test_r037_every_running_projects_item_is_phase_marked_and_the_windowless_default_is_named: every item of Running projects must and If rolled back opens with `all phases` or the Glossary's phases, `building` never without `changing`; the windowless default, its floor, its snapshot and the other named terms appear.
  - test_r038_the_run_sheet_says_pause_and_switch: (a)'s sentence whole, and the switch command.
  - test_r038_the_run_sheet_tells_the_maintainer_and_never_passes_anyway: (b)'s refusal sentence whole, and "never a dry run".
  - test_r037_step_4_sends_an_increment_in_flight_to_the_entry: (c)'s sentence whole.
- docs/INVENTORY.md: a Decisions row. A conditional workflow's additions bind by phase (the delegation loop's in `building` and `changing` from the next brief after the install); the install is preferred at a merge boundary with no increment in flight; this project's `Bridge version:` line is left for calibration's step 5.
- docs/PROJECT_STATUS.md: as at this pull request's merge (ISS-009). Awaiting user on: the install by the owner's run sheet. `Bridge version:` is still 2026.10.25a, on purpose: calibration writes it.

## Out of scope

- The install itself and every calibration (this project's, reAngle's, the video factory's, the TDP's). These follow the merge.
- The installer's messages: C-1's refusal wording and the dry-run tense. These are HARDENING leads for a later reviewed program change. This diff changes no program.
- REQUIREMENTS rows for R-031, R-037 and R-038 set to built. They come with the records after the install and trial.

## Supervisor's rulings (recorded here)

- calibrate's step 4 points at the entry's items rather than repeating M3's mechanics. The entry is the one place that names them, and calibration reads it in step 3.
- The entry's Field acceptance goes beyond the plan's Done when, adding the check that a reviewed increment's rounds are counted right. That is a stricter acceptance, not a scope change.

## Checks run

- bridge/cursor-bridge/bridge-check.py --sources --root bridge: 144 OK, SOURCES MATCH 2026.10.30a. (The installed 2026.10.25a check compares against its own manifest and is not the stamp's check.)
- Tests: 196 passed and 1 skipped (stamp, calibrate_text, loop_text_windowless, loop_text_pace, text_consistency, a5_followups, rollback, agent_models, leads_b3, conformance_check, install_check, release_b_bootstrap, completion_check). After the last wording change: 100 passed (stamp, rollback, text_consistency, loop_text_pace, loop_text_windowless).
- trace-check: OK (424 passages, 0 dropped, 57 excused).
- Review A, round 1: REJECT. Blocking: the delegation-loop items were marked *(building)*, now *(building, changing)*. Should fix: If rolled back item 3 after review-guard's _rounds_tamper; item 4's seeding recipe (replied rounds only, the record's shape, the common git folder); the status date. Consider: the reinstall count after launcher_effective_round; the dry-run header. All taken.
- Review A, round 2: APPROVE. Both of its Considers taken: the reseed's refusal beside a release-B snapshot, and "as replied" in Field acceptance.
- The secret sentinel; the invisible-character check; the path scan before the push.
