# SCOPE-REFAC-B2 — stage B2's refactoring pass (PR #26)

The diff is `run/review/REVIEW-REFAC-B2.diff` (`git diff origin/main...HEAD`, 2509383 the base). No brief and no builder: the one candidate taken is in the test-infrastructure lane, which supervisor.md Phase 6 step 9 item 3b gives the supervisor (the supervisor owns the tests), and the records are the supervisor's.

## What the branch carries
1. **Records** (commit 90f5bec), expected bookkeeping, not refactoring:
   - docs/DESIGN_CRITIQUE.md: TASK-009 round 6 grades and disposition; the round 3 correction note says the round that added it; round 4's disposition sentence restored as first written (Review A's round 6 consider C3).
   - docs/HARDENING.md: the TASK-009 lead routed by file (C1: TASK-010 and TASK-014's scopes hold neither open-list.md, extension-points.md nor Glossary.md); the TASK-008 lead on `judge_workflows_line` closed as kept on purpose, with the dropped `load_rules` candidate.
   - docs/PROJECT_STATUS.md: the position after TASK-009's merge; the Terms fixed sense of conditional workflow qualifies setting and replacing (C2).
   - docs/INVENTORY.md: jscpd 5.3.3 as a tool resource (the newest release older than two weeks on 2026-10-17).
2. **Test lane** (commit 3cdd6a7): `table()` was copied word for word in tests/test_open_list.py and tests/test_extension_points.py (jscpd 5.3.3's 23-line clone; refactor-scout's candidate 1). `test_open_list.table` takes the text to read (default: the open list); test_extension_points.py keeps its `table(heading)` name as a one-line call of it on the registry's text, so its call sites (`modules()`, `points()`, the column test) are unchanged.

## The question for this diff
Is it behaviour-preserving? The purity check is deterministic and passed: `refactor-check.py 90f5bec --lane tests` PURE (2 files, 34 changed lines, no production file). The lane's rule is that the collected test set is identical: `pytest --collect-only -q` printed the same 1163 test ids before and after (only the timing line differs). Probe (supervisor, on a copy): with the shared parser changed to ignore the text it is given, 8 of test_extension_points.py's 21 tests fail, so the registry's tests do parse the registry through it. Full suite on the branch: 1140 passed, 0 failed, 23 skipped (the known skips: allowlist prose 20, a non-root POSIX test 1, Windows symlink tests 2); bridge-check SOURCES MATCH.

## Considered and not taken (refactor-scout, recorded in HARDENING)
- `judge_workflows_line`, identical in inventory-check.py and conformance-check.py: most of its lines are the guarded load of workflow-check.py (no bytecode, fail closed), which a shared file would itself need in each program; kept on purpose.
- `load_rules` in workflow-check.py for the rule-reading block written four times: about ten net lines, its payoff a third rule file that no planned increment adds; dropped (the pass never adds an abstraction for hypothetical reuse).
- `table()` in tests/test_workflows_line_text.py: a looser variant (no separator or width assertions); routing it through the strict parser would add assertions, so left alone.

## Out of scope
Design for later increments; the texts the HARDENING lead names (they are rewritten by TASK-010 and TASK-017).
