# SCOPE - TASK-024

TASK-024, the builder's program half of R-027 and the calibration half of R-033 (docs/BUILD_PLAN.md, "### TASK-024"). Briefs: handoff/TASK-024.md (round 1) and handoff/TASK-024-r2.md (round 2, Review A's round-1 findings), both composer-2.5; round 2's Scope is round 1's.

## The brief's Scope (quoted)

One brief carries one increment's scope; work that needs a second scope is a second brief, never a second section here.
Files and directories you may create or modify:
- bridge/cursor-bridge/conformance-check.py
- bridge/cursor-bridge/MANIFEST.json
- tests/test_calibrate_program.py (new)
- tests/test_workflows_line_check.py (only the change named in Requirement 9)
- tests/test_b2_least_confident.py (only the change named in Requirement 10)
- docs/cli-reference.json
- docs/CLI_REFERENCE.md
- docs/BUILDER_NOTES.md
- handoff/TASK-024-r1-report.md

Do not modify anything else.

## The brief's Out of scope (quoted)

- .env and anything under secrets/
- CI configuration (.github/)
- docs/ and handoff/, except the files the Scope section names
- bridge/cursor-bridge/workflow-check.py, inventory-check.py, and everything under bridge/cursor-bridge/workflow/ (the open list and the registry): read them, do not change them, not even to make a test easier
- bridge/cursor-bridge/VERSION and CHANGELOG.md, and docs/CHANGES.md
- tests/test_conformance_check.py and its `make_workspace` helper, tests/conftest.py, and every other test file not listed in Scope
- bridge/commands/ (the text half is TASK-023's, already merged)

## Tests the supervisor wrote

- None. The brief has the builder write tests/test_calibrate_program.py (enforces R-027 and R-033) and make one named change each in tests/test_workflows_line_check.py and tests/test_b2_least_confident.py. The supervisor ran every new or changed test once against the checkpoint's code (02b0efaa): the eight tests of new behaviour fail there, and the three negative controls of test_calibrate_program.py (cases a, b, j) pass, as negative controls do.
- Known deviation: the builder split test_r015_conformance_valid_line_is_ok (parametrised over the two VALID cases) into two tests; the not-yet-classified test is renamed, its assertions unchanged.

## Expected bookkeeping and record files

- handoff/TASK-024.md and handoff/TASK-024-r2.md (the briefs), handoff/TASK-024-r1-report.md and handoff/TASK-024-r2-report.md (the builder's reports).
- docs/HARDENING.md, Stage B5, "TASK-024": two leads (the twice-loaded checker, for the refactoring pass; the project.json phase NOTE's unescaped Phase value), and after Review A's round 2 (APPROVE, 0 Blocking / 0 Should fix / 2 Consider) two more for its Considers (two copy edits matching a row's `| no |` form; case (d)'s row order). No program or test changed after Review A's round-2 read.
- docs/BUILD_PLAN.md: TASK-024's Scope line widened by the two test files (the brief's reality check, spec-packager).
- docs/INVENTORY.md: the Decisions row "TASK-024's grades" and the Features row "Calibration aware of conditional workflows (program)".
- docs/REQUIREMENTS.md: R-027 and R-033 built, with their evidence.
- docs/PROJECT_STATUS.md: as at this pull request's merge, PR #86 (ISS-009).
- bridge/cursor-bridge/MANIFEST.json restamped; docs/cli-reference.json and docs/CLI_REFERENCE.md regenerated (the docstring is the usage).
- run/review/: these review files.

## Evidence

- Round 2: against 02b0efaa the 13 tests of new behaviour fail and the negative controls pass.
- Full suite 2243 passed, 33 skipped; dump-cli --check clean; bridge-check --root bridge --sources (the repository's own) 140 OK; invisible-check OK; secret-sentinel CLEAR.
