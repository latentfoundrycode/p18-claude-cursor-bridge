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
- Review B, round 1 (snapshot TASK-027): REJECT on four statements, all fixed in commit "TASK-027: Review B's round 1". That commit and the review files are the only changes since round 1. This is Review B's round 2, below the ceiling.
  - The "38 files new" count and the rollback item named no base. Two trees carry the version 2026.10.25a: the hotfix's, installed on this computer (106 files, its core whole, 2,300 lines), and `main`'s from HOTFIX-002's merge (a0bca8e, 140 files, release B's earlier stages in it, its core already split). Review B's rehearsal rolled back onto a0bca8e. The count holds against the installed manifest: 38 files and the two allow entries, which the installed settings.bridge.json lacks. The lead now names that base. The rollback item now says the rollback restores the kept copy, removing what it lacks, and says what follows where the kept copy is `main`'s tree.
  - The launcher accepts three bare names (`cursor-agent`, `.cmd`, `.exe`) and refuses a path (bridge-run.py AGENT_NAMES, is_agent_argv). The entry now says so.
  - The reinstall count: launcher_effective_round counts distinct completed brief names. The entry now says so.
  - calibrate (b): a dry run prints the `previous ... kept at` line while keeping nothing, and ends before the check. The sentence now says so; the test pins "never a dry run" only.
  - Tests after the fix: 117 passed, 1 skipped (stamp, calibrate_text, rollback, text_consistency, loop_text_pace, loop_text_windowless, release_b_bootstrap). bridge-check --sources: 144 OK, SOURCES MATCH.
- Review B, round 2 (snapshot TASK-027, launch 2026-10-30T00:28:49Z): REJECT on two statements, both fixed in commit "TASK-027: Review B's round 2". That commit and the review files are the only changes since round 2. This is Review B's round 3, at the ceiling: only the five classes block (behaviour against the brief or register, security, data integrity, a defeated safety mechanism, a failing test); anything else is recorded in HARDENING.
  - If rolled back item 2 said the previous release reads none of the `Workflows:` line. That holds for the hotfix's tree. `main`'s tree a0bca8e, which round 1's fix brought into the entry, reads it: its session-start.py hook names the files the line names, and its conformance-check floor, inventory-check and workflow-check check it. The item now says both, and that what the checks report is recorded with the line left as written.
  - Running projects item 4's report-file pattern: `_report_file_rounds` (review-guard.py:518) also matches a letter after `<N>` (`-r<N>b-report.md`). The entry now says so.
  - Checked against a0bca8e beyond the two findings: its programs have no heavy slot, driver kind, scratch folder, `rounds-` record or runs.jsonl round fields. The rest of the If rolled back items hold there too.
  - Tests after the fix: 104 passed (stamp, rollback, text_consistency, loop_text_pace, loop_text_windowless, calibrate_text). bridge-check --sources: 144 OK, SOURCES MATCH.
- Review B, round 3 (snapshot TASK-027, launch 2026-10-30T00:52:39Z): REJECT with one line in a blocking class:

Blocking class: behaviour against the brief or register - CHANGELOG If rolled back item 1 named an install from `main` between HOTFIX-002's merge and the stamp as a kept copy the items describe, yet such a tree (920447b) holds release B's guard, launcher and mutation runs, so items 3 to 5 are false for it (R-037's if-rolled-back notes)

  - Fixed in commit "TASK-027: Review B's round 3", the only change since round 3 apart from the review files. The fix narrows the text and adds no claim. Item 1 now says the items are written for the hotfix's tree, which every project installed. A kept copy from `main` of that version holds part or all of release B and was installed by no project (a maintainer's rehearsal): the rollback restores it as it is, and each item applies only to what it lacks. Item 2 drops round 2's sentences on a0bca8e and keeps the hotfix's statement, which Review B confirmed in round 3. Round 3 confirmed every other statement on the trees it names.
  - This is round 4, above the ceiling. It is opened by the Blocking class line above (the ceiling held by hand until release B installs, INVENTORY, Decisions). Its scope is that one fix: a finding outside the five classes is a note the supervisor records in HARDENING.
  - Tests after the fix: 104 passed (stamp, rollback, text_consistency, loop_text_pace, loop_text_windowless, calibrate_text). bridge-check --sources: 144 OK, SOURCES MATCH.
- Round 4 (launch 2026-10-30T01:23:12Z): APPROVE.
- CI on the reviewed head (a86f855) failed two tests on ubuntu-latest, both reading docs/PROJECT_STATUS.md:

Blocking class: a failing test - test_release_b_bootstrap.py::test_r001_status_names_its_own_merge (Increment must read none at the merge, ISS-009) and test_calibrate_program.py::test_r027_r033_bridge_own_status_file (the stamped tree's conformance check: MISSING `Calibrated to the installed bridge`, the status file saying 2026.10.25a against the stamped 2026.10.30a)

  - Fixed in commit "TASK-027: CI's two failing tests", records only, no test changed:
    - PROJECT_STATUS `Increment: none`, with the install, the calibrations and the trial under Next.
    - `Bridge version: 2026.10.30a`, moved with the stamp as HOTFIX-002 did. The entry's own last item already covers this: a project whose line reads the new version before its calibration takes the no-delta path and applies the items by hand. The status file's Next and Calibration pending lines, and INVENTORY's Decisions row, now say so; they had said the line was left for calibration's step 5.
    - Run as CI runs them (GITHUB_REF=refs/pull/108/merge): both tests pass, with release_b_bootstrap, calibrate_program, release_b_stamp, completion_check and text_consistency, 50 passed. inventory-check OK (11,747 characters of 12,000).
  - This is round 5, opened by the Blocking class line above. Its question is that fix alone.
