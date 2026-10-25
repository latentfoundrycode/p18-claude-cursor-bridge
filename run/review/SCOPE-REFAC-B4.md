# SCOPE — REFAC-B4 (stage B4's refactoring pass)

A stage-close refactoring branch, one gate pass for both lanes. "Refactoring" here means one thing: removing duplication or simplifying code while keeping the same functionality. The question for this diff: **is this behaviour-preserving?** — answered on the whole diff.

## The lanes

- **Tests lane (the supervisor's), commit ebd3ade:** a new tests/workflow_files.py (not a test file, not collected) holding the paths and helpers tests/test_type_web_app.py, test_type_own_computer.py, test_type_host_extension.py, test_traits_new.py and test_traits_existing.py each copied: the workflow folder's paths, `flat`, `trace_check`, `trace_units`, `run_check`, `rows`, `row`, `traits_of`, `file_entries`. Constraints kept: every test name, parameter id and assertion unchanged; `flat` keeps its `.strip()`; `row` returns the first match and raises AssertionError(key), `rows` keeps the last; the trace check is loaded afresh on each call; each copy check keeps its own walk (web_app: PHASES and TRAITS plus its other file; own_computer and host_extension: PHASES, TRAITS and TYPES; traits_new: PHASES recursively, TRAITS flat with its `>= 6` check). Proof: `python -m pytest tests --collect-only -q` identical before and after (2,199 tests); `refactor-check.py origin/main --lane tests` PURE, 313 changed lines.
- **Production lane, REFAC-002 (builder composer-2.5; brief handoff/REFAC-002.md; report handoff/REFAC-002-r1-report.md):** bridge/cursor-bridge/loop-guard.py:36 imports `datetime` alone; `timedelta` (unused since BUG-020) and `timezone` (unused before) removed; bridge/cursor-bridge/MANIFEST.json regenerated (138 files). `refactor-check.py ebd3ade --max-lines 87` PURE (25 changed lines with the records).

## Out of scope

Any behaviour change; any test assertion; the candidates beyond budget or held by a recorded decision (docs/HARDENING.md, the REFAC-B4 section). Design for later work is not this diff's defect.

## Tests the supervisor wrote

None new: the tests lane moves helpers and changes no test. Its proof is the identical collected set and the five files passing.

## Also in this diff, expected

- docs/HARDENING.md: a "Stage B4's refactoring pass" section (inputs, taken, beyond budget, held, not candidates).
- docs/INVENTORY.md: the jscpd row at 5.4.1, the newest release older than two weeks on 2026-10-25.
- docs/PROJECT_STATUS.md as it will read at this pull request's merge (ISS-009).
- handoff/REFAC-002.md (the checkpoint commit 689a797) and the builder's report.
- No docs/CHANGES.md entry: a refactoring changes no behaviour.
- The review files under run/review/, in their own commit, removed with `git rm` before the merge.
- Full suite on the branch before the records commit: 2166 passed, 33 skipped. The secret sentinel: CLEAR.
- Review A (refactoring mode): APPROVE on the branch at the records commit; its one should-fix (the clone count's wording) and one consider (the landed timedelta lead) answered in the next commit.
