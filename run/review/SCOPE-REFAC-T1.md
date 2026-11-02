# SCOPE - REFAC-T1 (stage T1's refactoring pass)

## What the branch is
Stage T1's refactoring pass (bridge/cursor-bridge/workflow/phases/delegation-loop/refactoring-pass.md): removing duplication with the same functionality, one gate pass for the whole branch, one squash. No `docs/CHANGES.md` entry: a refactoring changes no behaviour. The question for the reviewers: **is this behaviour-preserving?**

The base is origin/main 6306b40 (TASK-040's merge, PR #121); the stage's change is 46caed5..6306b40 (TASK-036 to TASK-040). The candidates came from jscpd 5.4.1 over bridge and tests (147 clones, 23 touching the stage's files) and refactor-scout's ranking against the 400-line budget, kept in run/supervisor/refactor-T1-candidates.md (gitignored) and recorded in docs/HARDENING.md, "Stage T1's refactoring pass". One candidate, in the tests lane; the production lane has none, so no builder ran and no REFAC-<nnn> brief exists.

## The commits
1. `supervisor: REFAC-T1 tests lane` (10dadc2) - the supervisor's test-infrastructure lane (step 3b): tests/phase_modules.py gains `CORE`, `digest()` and `rule(n)` (tests/test_loop_text_pace.py's forms, which predate the stage); tests/test_release_t_merge.py, test_release_t_records.py, test_release_t_ceiling.py and test_release_t_pitfalls.py import `read`, `flat` and `section` (and `rule`, `digest`) from it in place of their own copies; test_loop_text_pace.py imports `rule` and `digest`. Every local `section(text, title)` call takes its heading's level (3 for "The procedure" and "8. Merge (the verified gate)", 2 for the rest): phase_modules' `section` raises unless the title is exactly one heading at that level (FIX-004's rule), stricter than the copies, which took the first heading of any level. The unused `re` imports go with the copies. Evidence: `pytest --collect-only -q tests` identical before and after (3,406 tests; run/supervisor/refactor-T1-collect-before.txt and -after.txt); `refactor-check.py origin/main --lane tests`: PURE, no production file, 161 lines; the six files and phase_modules' other users: 175 passed.
2. `REFAC-T1: the pass's records` (6727acf) - docs/HARDENING.md (the pass's section), docs/INVENTORY.md (the jscpd row; the module-size row's reflection.md figure as on the merged tree, 130 lines and 21,731 characters, Review B's round-1 Should fix on PR #121), docs/PROJECT_STATUS.md written as at this pull request's merge (the project's rule, ISS-009) with the six lines it replaces moved to docs/archive/STATUS_HISTORY.md, project.json's stage.
3. `supervisor: REFAC-T1: Review A's considers 1 to 3` (71979c6). Review A in refactoring mode approved commits 1 and 2 with 0 Blocking and 0 Should fix. It compared every removed copy with the shared helper by running both: the same text at all 8 `section` call sites, and for every `rule(n)`, `digest()` and `read`. Three of its Considers are taken here:
   - `rule(n)` reads the Standing rules section through `section(read(CORE), "Standing rules", 2)`, so it stops where the removed merge and records copies stopped. Before, it read to the end of the file, which is the same text today only because that section is the core's last. Rules 1 to 57 read the same both ways.
   - `read` closes its file with a `with` block, as the copies did.
   - tests/test_release_t_ceiling.py's unused `CORE` constant is removed.
   
   Its fourth Consider needs no change: the stricter `section` is the intended tightening that HARDENING records. Evidence: the 25 test files that import phase_modules, 489 passed; the collected set unchanged, 3,406.

The full suite on 71979c6, through the launcher with the pull request's variables (run 2026-11-02T03:13:53Z), gave "3366 passed, 40 skipped in 1527.49s". That is 3,406 tests, the same count as at TASK-040's merge.

`refactor-check.py origin/main --lane tests` over the whole branch lists the records files as production changes, by design: the records ride in a commit of their own (T10) and the tests lane is checked on its own commit (step 3b).

## Out of scope
- Production lane: none (the auditor paragraph three agents repeat is R-050's placement; `Bash(git branch -D stage/*)` kept by TASK-038's Done when (c); the shared governance sentences placed by the design; merge.md is a move). Optimization: none. Beyond budget: none.
- Leads still open: stage B6's shared manifest writer, stage B5's date and git helpers.
- Stage T1's review, its demonstration and stage T2's increments (TASK-041 to TASK-045) are later work, not this diff's defect.

## Tests and drivers the supervisor wrote
None new: the tests lane replaces copies of helpers with imports of one copy; each test must make every assertion it made before, with the same values and strictness. No mutation driver: the pass changes no behaviour.

## Expected bookkeeping files in the diff
docs/HARDENING.md, docs/INVENTORY.md, docs/PROJECT_STATUS.md, docs/archive/STATUS_HISTORY.md, project.json, and run/review/ (this file, the diff, the assumptions file).
