# SCOPE for TASK-054 (Review B, round 1)

TASK-054 is this repository's records migrated by the installed 2026.11.11a records-migrate.py at this project's calibration (R-063), supervisor-authored, no builder run. Branch task-054 from main 0f8fe4c (PR #149's merge, the stamp). This is the review guard's first round for TASK-054, below the code gate's ceiling: there is no Blocking class line.

Where the increment ends: the calibration record, the trim, the repairs the program's --check asked for, the migration (one commit, the installed program's write and nothing else), the test, R-063 built, and the records. Stage H2's close (its refactoring pass, stage review, demonstration and reflection) and project end follow; they are not this diff's defect. The program itself (records-migrate.py, bridge_env.py) is not in this diff: it was reviewed at TASK-051, TASK-052 and BUG-044 and stage H2's review, and is installed.

The commits, in order: 0d61b47 the calibration record; 9a798d9 the trim (the Working files line one sentence); 5473fc6 the repairs (three status lines shortened, 15 plan Scope lines' semicolons inside a parenthesis made commas); 9199d04 the migration (121 records, 1940 insertions, 0 deletions); 372332c the accept commit (the test, R-063 built); c796d6e the records; fa4b7c9 and 3163c53 Review A round 1's should-fix taken before any snapshot. Read the commit messages (git log, the full bodies) for the quoted lines.

## The plan entry's Scope, quoted (docs/BUILD_PLAN.md, TASK-054; read its Done when whole there)
Scope: docs/PROJECT_STATUS.md; docs/BUILD_PLAN.md; handoff/; docs/INVENTORY.md; docs/REQUIREMENTS.md; docs/diagrams/INDEX.md; docs/diagrams/DEVIATIONS.md; docs/RUN_PARAMETERS.md; docs/HARDENING.md; run/supervisor/working-files.md; tests/test_release_b2_records.py; tests/test_release_b_bootstrap.py; tests/test_text_consistency.py; tests/test_b2_least_confident.py
Scope notes: handoff/: every brief the fallback reads, no report or resolution file touched; run/supervisor/working-files.md: gitignored, named by the status file's one sentence; tests/test_b2_least_confident.py: every test that parses this repository's status file or its records, re-read on the migrated shape before the first push, re-taken only where it pins a byte the header changes, named in the accept commit
Satisfies: R-063

## The supervisor's tests, each with the paragraph it enforces
- tests/test_release_b2_records.py (5 tests; its module docstring names R-063 and TASK-054's Done when): every record of the eight kinds, enumerated as the migration enumerates them, opens with its header but the three refused merged briefs; every header reads the same through yaml.safe_load and read_header and passes check_header; handoff/TASK-046.md's prose unchanged (length and sha256 at 5473fc6); the status file's growth over 5473fc6 and 9199d04 by git show, skipped where either commit is absent. After the migration "5 passed". Against the checkpoint 0f8fe4c (mutation-run.py --checkpoint, after the round-1 fix, exit 0): the three listed tests "failing"; the kinds test passes on the old tree (every kind exists) and the growth test skips in the engine's copy (no repository), so neither is listed.

## The mutants
run/supervisor/TASK-054-mutants.json (7 mutants: a brief's header of another kind, the status phase outside the schema, the run parameters' header unreadable, a brief's prose changed, a status header key dropped, the index's record key renamed, a same-length prose change). Mutation run 2026-11-11, exit 0: counts: run=1 cached=6 killed=7 survived=0 not applied=0 error=0 expected survive=0 (the first run erred on m01 only, its expect_fail missing the prose test its longer header also fails; corrected in the mutants file, no round)

## The old programs over the migrated records
run/supervisor/task054_previous_checkers.py (gitignored; read it) ran the kept 2026.11.09a checkers over the migrated records; output run/agent/task054-previous.out (gitignored; read it). HARDENING's TASK-054 section quotes them beside the stamp's scratch-copy lines.

## The threat model
None is recorded in docs/INVENTORY.md (Decisions) for records; no program changes in this diff.

## Evidence
- Review A: round 1 APPROVE, nothing of the five; its two should-fix (the TDP's pause at the owner's word restored in Next; the brief prose pinned by sha256) taken before any snapshot; confirming read APPROVE (5 passed; inventory-check 39 lines / 9459 chars)
- the full suite with the pull request's variables (GITHUB_REF=refs/pull/150/merge): 5096 passed, 41 skipped in 1965.91s (0:32:45), exit 0 (launcher, stripped, key file with GITHUB_REF=refs/pull/150/merge)
- installed checkers after the migration: inventory-check, plan-check, completion-check plan and done, diagram-check design and code all RESULT: OK; records-migrate.py --check lists has a header for every record and the three refused briefs only.

## Expected bookkeeping and records in the diff
docs/PROJECT_STATUS.md (the calibration line, the trim, the repairs, the header, as at PR #150's merge); docs/BUILD_PLAN.md (the Scope repairs, the header); handoff/*.md (headers only, 114 briefs); docs/INVENTORY.md, docs/REQUIREMENTS.md, docs/diagrams/INDEX.md, docs/diagrams/DEVIATIONS.md, docs/RUN_PARAMETERS.md (headers; R-063 built; the growth row); docs/HARDENING.md; and run/review/ (these files).
