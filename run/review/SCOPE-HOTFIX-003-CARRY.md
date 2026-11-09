# SCOPE: HOTFIX-003-CARRY, the intake hotfix 2026.11.09a carried onto main (round 1)

## Where the increment ends

The intake hotfix 2026.11.09a (HOTFIX-003) was made on `hotfix/intake-conversation`, reviewed at its own code gate (rounds HOTFIX-003-r1 and HOTFIX-003-r2, both reviewers approving at round 2) and merged into `release/2026.11.03` as PR #142 (squash 2c211ef). The owner installed it on 2026-11-09 and the project calibrated to it (commit 9958c3a). This pull request carries that hotfix onto `main` with its records, the precedent of HOTFIX-001's carry (its own review name, HOTFIX-001-main) and HOTFIX-002's (PR #84). The review name is HOTFIX-003-CARRY because this is a different diff, against a different base, carrying files the hotfix's gate never read (the records, the regenerated manifest on main's tree, the loosened stamp test); the hotfix's own text is carried unchanged.

What this diff holds, by commit:

- `e352792`, the carry: `git diff 91c2efb 2c211ef` applied onto `main`, minus the three files `main` owns (`docs/PROJECT_STATUS.md`, `project.json`, `bridge/cursor-bridge/MANIFEST.json`). The manifest is regenerated on `main`'s tree by `tools/make-manifest.py --version 2026.11.09a` (145 files) and checked by `bridge-check.py --sources` (SOURCES MATCH). `project.json`'s `version` and `state.bridge` move to 2026.11.09a. One change beyond the release branch's text: `tests/test_hotfix_intake.py::test_hotfix003_the_stamp_agrees_everywhere` is loosened as Review A's round-2 should-fix asked (ruled to the carry): the hotfix's heading stands directly above 2026.11.03a, and VERSION, the manifest, project.json and the status file's Bridge version are this hotfix's stamp or a later one's, so release B2's own stamp (TASK-053) never breaks it.
- `6685ddb`, the records (R-065): docs/DESIGN.md's Change section, docs/DESIGN_CRITIQUE.md's block for the subject intake-conversation, docs/HARDENING.md's "Hotfix 2026.11.09a" section, docs/INVENTORY.md's feature row, trace count and the 2026-11-08 Decisions row settled, docs/REQUIREMENTS.md's R-065 built, docs/BUILD_PLAN.md's TASK-053 note (its version sorts after 2026.11.09a), docs/PROJECT_STATUS.md as at this pull request's merge (#143).
- `9958c3a`, `88c6a46`, `bfe7895`, `8fdeb30`: the supervisor's status records since TASK-050's merge (the pauses for the owner's model switch and install, the calibration to 2026.11.09a). Records only.

## In scope (the files this diff may change)

- The hotfix's text, as merged into the release branch: `bridge/commands/supervisor.md`, `bridge/skills/explain-for-decision/SKILL.md`, `bridge/cursor-bridge/Known-Pitfalls.md` (KP-075), `bridge/cursor-bridge/workflow/phases/intake.md`, `change-cycle.md`, `design.md`, `interface/mockups.md`, `bridge/cursor-bridge/workflow/trace-exceptions.md`, `bridge/cursor-bridge/CHANGELOG.md` (the 2026.11.09a entry), `bridge/cursor-bridge/VERSION`.
- `bridge/cursor-bridge/MANIFEST.json`, regenerated on main's tree (version and hashes only).
- The tests: `tests/test_hotfix_intake.py` (new on main; the stamp test loosened), `tests/test_core_carve.py`, `tests/test_b3_least_confident.py`, `tests/test_phase_modules_close.py` (the pins the hotfix re-took, as on the release branch).
- The records: `docs/DESIGN.md`, `docs/DESIGN_CRITIQUE.md`, `docs/HARDENING.md`, `docs/INVENTORY.md`, `docs/REQUIREMENTS.md`, `docs/BUILD_PLAN.md`, `docs/PROJECT_STATUS.md`, `project.json`.

## Out of scope

- Every program, `settings.bridge.json`, the hooks, the agents' definitions: the hotfix is text only.
- Re-deciding the hotfix's text: it passed its design critique (four rounds), the owner's design gate (2026-11-09) and its own code gate (two rounds, both approving). A defect in it found now is still a finding; a preference about its wording is not this diff's.
- The digest's rule 12 (R-048's D7, pinned by tests/test_release_t_records.py; the digest at 9,497 of its 9,500 characters): accepted at the critique, a lead in docs/HARDENING.md.
- Release B2's remaining increments (TASK-051 to TASK-054) and stage H1's close: later work.

## The threat model

None is recorded in docs/INVENTORY.md's Decisions for governance text or for the records: the diff is text read by a supervisor and the project's own records, with no program, no input handling, no key and no spend. The review guard's own threat model (KP-032; the inventory's row of 2026-11-02 for R-050) bounds the gate itself, not this diff. Where none is recorded, the five blocking classes stand unbounded.

## The tests, each with what it enforces

- `tests/test_hotfix_intake.py`: seventeen tests, each enforcing one row of the design's table "What changes - the text by home" (the Change section in docs/DESIGN.md, this diff), as on the release branch, where sixteen were shown red before the text and one invariant test green by design. On main: `test_hotfix003_the_stamp_agrees_everywhere` now enforces that the hotfix's CHANGELOG heading stands directly above 2026.11.03a and that VERSION, MANIFEST.json, project.json (`version`, `state.bridge`) and the status file's Bridge version are 2026.11.09a or later; which entry is newest stays tests/test_release_t_stamp.py's.
- `tests/test_core_carve.py`: the trace check's TRACED line at 89 excused, its six NOTE lines.
- `tests/test_b3_least_confident.py`, `tests/test_phase_modules_close.py`: the excused sections' pins, re-taken for the hotfix's reworded sections.
- `tests/test_release_b_bootstrap.py::test_r001_status_names_its_own_merge` (unchanged) checks the status file reads as at PR #143's merge; `tests/test_release_t_stamp.py` (unchanged) checks the stamp agrees everywhere.

## The mutants

The hotfix's mutants file, `run/supervisor/HOTFIX-003-mutants.json` (42 mutants over the changed sentences, the stamp and the places that keep the question form), ran at the hotfix's own gate, every mutant killed. The carry changes no sentence of the text, so it is not run again; the one test changed on main (the stamp test) is loosened, not new, and its asserts read files the carry's other tests also pin.

## The full suite

Run once with the pull request's variables (GITHUB_REF refs/pull/143/merge, GITHUB_BASE_REF main, GITHUB_EVENT_NAME pull_request) before the first push, into run/agent/HOTFIX-003-carry-suite.out; its counts line is quoted in the pull request's description.

## Bookkeeping and record files expected in the diff

- `docs/PROJECT_STATUS.md` and `project.json`, as above (ISS-009: the status file reads as at PR #143's merge).
- `run/review/` (this file, the round's diff and assumptions file), removed with `git rm` before the merge.
