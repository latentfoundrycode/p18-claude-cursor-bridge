# SCOPE-BUG-001g — the follow-up of PR #21 (BUG-001), PR #22

The diff: `run/review/REVIEW-BUG-001g.diff` (`git diff origin/main...HEAD`, main at 6743b25, BUG-001's squash).

## What this pull request is
No builder run. PR #21 (BUG-001, stage B1's review fixes) merged as 6743b25 after six rounds; in round 6 Review A approved with one Should fix that Review B did not raise: the whole-workflow pin (`WORKFLOW_PIN`, `test_r002_workflow_is_the_pinned_one`) and the one-secret rule (`test_r002_one_step_holds_a_secret`) read `.github/workflows/tests.yml` only, so a second file under `.github/workflows/` could hand `secrets.SOCKET_SECURITY_API_KEY` to a step that installs a package (or run on `pull_request_target`) with every test passing. The supervisor drew the by-class line (not converged, not weaker than main, a new file every reviewer and scope-check sees), merged, and fixes it here, before stage B1's review runs again on B1's whole change.

## The supervisor's test (enforces R-002 and the BUG-001 fix brief's cause: no secret where code it does not need runs)
- `tests/test_release_b_ci_floor.py`, `test_r002_workflow_is_the_only_one`: the entries of the workflow folder are exactly `[tests.yml]`. A change that adds a workflow must widen these tests in the same diff.
- Mutation driver (the supervisor's, not in the diff: run/supervisor/mutate_ci_floor.py): new mutant "second workflow beside the pinned one" (a copy of the workflow in a temporary folder with an `extra.yml` running on `pull_request_target`), killed only when this test's message fires; 57 mutants, all killed. The driver writes only temporary copies.
- Stage tests 31 passed; full suite 952 passed, 20 skipped (the skips are tests/test_allowlist.py's prose lines, as on main).

## Records (expected in the diff)
- docs/DESIGN_CRITIQUE.md: round 6's grades and disposition.
- docs/HARDENING.md: two leads from Review A's round-6 Considers — PyYAML (YAML 1.1) against GitHub's parser; the scanners' configuration files outside the pin.
- docs/REQUIREMENTS.md: R-002's evidence names BUG-001's squash and this follow-up.
- docs/PROJECT_STATUS.md: the position (Last accepted BUG-001 at 6743b25; this follow-up; the owner's open run sheet).

## Out of scope
- The workflow itself, unchanged (the pin still equals it).
- The HARDENING leads are recorded, not settled, here.
- Stage B2's increments (TASK-006 regenerates `WORKFLOW_PIN` when it changes the workflow).
