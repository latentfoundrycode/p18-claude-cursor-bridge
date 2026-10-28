# SCOPE - REFAC-B5 (stage B5's refactoring pass)

## What the branch is
Stage B5's refactoring pass (bridge/cursor-bridge/workflow/phases/delegation-loop/refactoring-pass.md): removing duplication with the same functionality, one gate pass for the whole branch, one squash. No `docs/CHANGES.md` entry: a refactoring changes no behaviour. The question for the reviewers: **is this behaviour-preserving?**

The base is origin/main 8a29708 (TASK-025's merge, PR #98). The candidates came from jscpd 5.4.1 over bridge, tests and tools (104 clones) and refactor-scout's ranking against the 400-line budget, kept in run/supervisor/refactor-B5-candidates.md (gitignored) and recorded in docs/HARDENING.md, "Stage B5's refactoring pass".

## The commits
1. `supervisor: REFAC-B5 tests lane` (4a25d36) - the supervisor's test-infrastructure lane (step 3b): tests/phase_modules.py gains `registry_rows`, `registry_points`, `EXT_PROSE`, `assert_survival_list` (R-004's shape), `assert_declares_registry_points` and `assert_points_placed` (R-006's) and `hook_named` (R-005's installed-hook run); tests/test_phase_modules_build.py, _intake_design.py, _interface_planning.py and _close.py call them in place of their own copies (scout candidates 1 and 5). tests/test_mutation_run.py's `run_mr` gains `python=` and `env_extra=`, and six inline copies of its body call it (candidate 4); an unused `hashlib` import is removed. Evidence: `pytest --collect-only -q tests` identical before and after (3,234 tests; run/supervisor/refactor-B5-collect-before.txt and -after.txt); `refactor-check.py origin/main --lane tests`: PURE, no production file, 343 lines; the five files: 160 passed, 1 skipped (a symbolic-link case the account cannot make).
2. `checkpoint before REFAC-003` (758ce02) - the brief handoff/REFAC-003.md.
3. `REFAC-003` (1b8afa9) - the builder's (composer-2.5) production change: bridge/cursor-bridge/pace-report.py's two loops with identical bodies (`for ident, rnd in over:` and `for ident, rnd in stage:`, in `_project_section`) made one, `for ident, rnd in over + stage:`, the same lines in the same order (candidate 6); bridge/cursor-bridge/MANIFEST.json regenerated for the file's hash; the builder's report handoff/REFAC-003-r1-report.md. `refactor-check.py 4a25d36 --max-lines 400`: PURE, 13 lines; scope-check SCOPE CLEAN; `tools/dump-cli.py --check` green.
4. `REFAC-B5: the pass's records` (15abc9d) - docs/HARDENING.md (the pass's section and Review B's noted item on TASK-025), docs/INVENTORY.md (the jscpd row), docs/PROJECT_STATUS.md written as at this pull request's merge (the project's rule, ISS-009).
5. `supervisor: REFAC-B5: Review A's fixes` (d11fd62) - Review A's should-fix: tests/conftest.py registers tests/phase_modules.py with `pytest.register_assert_rewrite`, so the assertions moved there still run under `python -O` as the test files' own did (shown with a throwaway test, removed: it raised under `-O` with the registration and did not without it); docs/HARDENING.md's wording corrected. Review A (refactoring mode) APPROVE on the branch as it stands, after a confirming read.

The full suite on d11fd62: 3,195 passed, 39 skipped (3,234; the same count as at TASK-025's merge).

`refactor-check.py origin/main --max-lines 400` over the whole branch lists the tests-lane files as test changes, by design: the two lanes share the one gate pass and are each checked on their own (step 3b and step 5); 382 changed lines in all with these review files, within the 400 budget.

## Out of scope
- Skipped (a half uncovered, a characterization test would need its own gate on main first): conformance-check.py's three loaders of workflow-check.py; mutation-run.py's copy tail.
- Beyond budget: the date and git helpers the acceptance tests share with the builder's tests.
- Held by a recorded decision: `_link_folder`, trace-check.py's `not_checked`.
- Stage B6's increments (TASK-026, TASK-027) and release B's install are later work, not this diff's defect.

## Tests and drivers the supervisor wrote
None new: the tests lane moves existing assertions into helpers; each test must make every assertion it made before, with the same values and strictness. No mutation driver: the pass changes no behaviour.

## Expected bookkeeping files in the diff
handoff/REFAC-003.md, handoff/REFAC-003-r1-report.md, bridge/cursor-bridge/MANIFEST.json, docs/HARDENING.md, docs/INVENTORY.md, docs/PROJECT_STATUS.md, and run/review/ (this file, the diff, the assumptions file).
