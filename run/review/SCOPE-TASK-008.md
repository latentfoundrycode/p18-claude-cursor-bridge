# SCOPE-TASK-008 — the Workflows status line enforced (PR #24), review round 1

The diff is `run/review/REVIEW-TASK-008.diff` (`git diff e2a7f9f...HEAD`, e2a7f9f being origin/main, TASK-006's merge). The brief is `handoff/TASK-008.md`; read it whole. Its Scope and Out of scope, quoted:

## Scope (quoted from the brief)
Files you may create or modify:
- bridge/cursor-bridge/inventory-check.py
- bridge/cursor-bridge/conformance-check.py
- bridge/cursor-bridge/workflow-check.py (only to add the one function of Requirement 1; nothing else in it changes)
- bridge/cursor-bridge/MANIFEST.json (regenerated with `python tools/make-manifest.py` after your last edit under `bridge/`)
- docs/BUILDER_NOTES.md
- handoff/TASK-008-r1-report.md

## Out of scope (quoted from the brief)
- .env and anything under secrets/
- CI configuration (`.github/workflows/`)
- docs/ and handoff/, except the files the Scope section names
- Everything under `bridge/` except the four files in Scope. In particular these stay unedited: `bridge/commands/supervisor.md`, `workflow/open-list.md`, `workflow/extension-points.md`, `CHANGELOG.md`, `VERSION`.
- In `workflow-check.py`, everything except adding `check_placement`: its module docstring (which is its `--help` text), `main`, `check_status`, every other function, its finding codes, its output and its exit codes.
- The other checks of `inventory-check.py` and `conformance-check.py`. That includes `inventory-check.py`'s status-length cap, which counts lines with `str.splitlines()` and stays as it is: it does not read the `Workflows:` line.
- Checking that several parts' lines come "in the order of the project's parts". Nothing records that order elsewhere, so it is not checkable.

## The supervisor's tests (written before the delegation, then tightened after the driver run)
- `tests/test_workflows_line_check.py` — enforces docs/REQUIREMENTS.md R-015 and the brief's Requirements 1 to 8: `check_placement` called directly; through both programs, a valid line (the bridge's own, and `not yet classified`), a missing line (none; one joined to `Phase:` by a form feed; one joined by U+2028 — TASK-006's line-feed-only split), malformed lines (no `; traits: `, an unknown name, a line between, above `Phase:`, no Phase line), unwritten types not counted, the problem count, ASCII output, no status file, and `workflow-check.py` or its rule files not loadable (a failure naming the cause, no traceback). Checkpoint 390370d; tightened in 1f59cf8 after three driver mutants survived (the rules case must name `open-list.md`; the count test must see a WORKFLOWS LINE line).
- `tests/test_conformance_check.py` — `make_workspace`'s status file now carries `Workflows: not yet classified` right after `Phase: building`, so the conformant workspace stays conformant (enforces R-015 by keeping the existing conformance tests valid).
- Mutation driver `run/supervisor/mutate_workflows_line.py` (the supervisor's, not in the diff): 21 mutants over the glue in both programs, the program-specific outputs and `check_placement`'s rules; all killed.

Test results: the increment's three test files 172 passed, 1 skipped (the POSIX-only test in test_workflow_check.py, run on CI's ubuntu leg); full suite 1107 passed, 21 skipped; windowless-check and bridge-check --sources pass; secret-sentinel CLEAR.

## Expected bookkeeping and record files in the diff
- `docs/BUILDER_NOTES.md` (one builder line: Done's order runs the suite before make-manifest, so the install tests fail until the manifest is regenerated)
- `handoff/TASK-008.md` (the brief) and `handoff/TASK-008-r1-report.md` (the builder's report, with its `Assumed, not verified` list)
- `docs/BUILD_PLAN.md` (TASK-008's Scope widened to workflow-check.py and tests/test_conformance_check.py, before the delegation)
- `docs/REQUIREMENTS.md` (R-015 built), `docs/INVENTORY.md` (the feature row), `docs/HARDENING.md` (TASK-008's two notes), `docs/PROJECT_STATUS.md`
- the first commits of the branch carry TASK-006 round 6's records (d25e38b: DESIGN_CRITIQUE, HARDENING, status), made after PR #23 merged
- `run/review/` (these review files)
