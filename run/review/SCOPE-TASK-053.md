# SCOPE for TASK-053 (Review B, round 1)

TASK-053 is release B2's stamp, supervisor-authored, no builder run. Branch task-053 from main 54c849f (PR #148's merge, BUG-044). This is the review guard's first round for TASK-053, below the code gate's ceiling: there is no Blocking class line.

Where the increment ends: the stamp (VERSION 2026.11.11a, the CHANGELOG entry, the regenerated manifest, project.json, R-064 built in the accept commit as the plan's one exception) and its records. The owner's install from a run sheet comes after the merge; TASK-054 migrates this repository's records with the installed program at this project's calibration; stage H2's close and project end follow. Those are not this diff's defect. records-migrate.py must never be run over this repository's records or with the checkout as its folder: a copy in the system temporary folder only.

The type's rule (host-extension.md, planning.stages): the stage review of the release's text runs before the stamp. Stage H2's review, round 2 (STAGE-H2-r2, tag stage-review/H2-2), both reviewers APPROVE, read f32f54f^..54c849f; this diff changes no text under bridge/ but the CHANGELOG, VERSION and the manifest.

## The plan entry's Scope, quoted (docs/BUILD_PLAN.md, TASK-053; read its Done when whole there)
Scope: bridge/cursor-bridge/VERSION; bridge/cursor-bridge/CHANGELOG.md; bridge/cursor-bridge/MANIFEST.json; bridge/cursor-bridge/workflow/trace-exceptions.md; tests/test_release_b2_stamp.py; docs/REQUIREMENTS.md; project.json
Scope notes: bridge/cursor-bridge/workflow/trace-exceptions.md: the release's entries complete; docs/REQUIREMENTS.md: R-064's flip and Evidence, in the accept commit; project.json: the version, in the accept commit; the records the increment writes in its records-only commit, outside Scope by the RECORDS rule: docs/PROJECT_STATUS.md, docs/INVENTORY.md, docs/HARDENING.md
Satisfies: R-064

## The supervisor's tests, each with the paragraph it enforces
- tests/test_release_b2_stamp.py (10 tests; its module docstring gives each test's paragraph): enforces TASK-053's Done when (VERSION, the entry, the manifest, project.json and the status file agreeing; the version sorting after 2026.11.09a; the entry's parts with every running-projects item phase-marked and the plan's items named; the If rolled back lines quoted; the field acceptance's stand-in; the maintainer's three items; R-057 to R-062 and R-064 built with Evidence in the constraints' grammar and R-063 planned or built), R-064, and host-extension.md's planning.stages sentence on the field acceptance. Before the stamp "8 failed, 3 passed"; after Review A's round-1 fix, with the two earlier stamp tests, "39 passed in 0.73s". The new tests against the checkpoint 54c849f (mutation-run.py --checkpoint, 2026-11-11T12:07:13Z, after the fix, exit 0): all 9 listed "failing"; the tenth, completion-check --mode plan OK, is the Done when's check pinned and passes on the old tree by design, so it is not listed.

## The If rolled back observation
run/supervisor/task053_rollback_observe.py (gitignored; read it) cloned HEAD into the system temporary folder, shaped the copy as TASK-054 will shape the live records, ran the installed 2026.11.09a checkers (the programs a rollback puts back) before and after the copy's own records-migrate.py, printed both runs and their differences, and removed the copy. Its output is run/agent/task053-observe.out (gitignored; read it). Every quoted line and claim of the entry's If rolled back part must match that output and the installed programs at ~/.claude/cursor-bridge/ (conformance-check.py's status_field and its project.json-state NOTE).

## The mutants
run/supervisor/TASK-053-mutants.json (15 mutants: the version's day, project.json's bridge, a quoted line changed, building without changing, the lift sentence dropped, R-063 after the stamp dropped, R-064 planned, the allow rule dropped, a maintainer item reworded, the stand-in dropped, the lead's new file dropped, the heading another day; and, for Review A's round-1 fix, the older hooks reading the header dropped, write-both while rolled back dropped, a malformed header repaired at the line for a schema break). Mutation run 2026-11-11T12:10:41Z, exit 0: counts: run=15 cached=0 killed=15 survived=0 not applied=0 error=0 expected survive=0

## Review A's round 1 (before any snapshot, so no round)
Review A REJECTed the first text: B1, the If rolled back part said the older programs read past the header, where four read header lines as prose lines (loop-guard.py and session-start.py field() the status header's phase:, conformance-check.py status_field its phase: and stage:, completion-check.py the plan header's satisfies:); B2, the HEADER MALFORMED sentence named the line for a schema break, where calibrate-bridge.md step 4 names the keys. Fixed in commit 7f2b108 (the entry, the manifest, the test's pins) with HARDENING in 065f335; Review A's confirming read approved it.

## The threat model
None is recorded in docs/INVENTORY.md (Decisions) for release text; no program changes in this diff.

## Evidence
- trace-check: "RESULT: OK" (424 passages, 0 dropped, 93 excused); bridge-check --sources "RESULT: SOURCES MATCH bridge 2026.11.11a" (146 OK); completion-check --mode plan "RESULT: OK" (62 built, 2 deferred, 1 planned); plan-check "RESULT: OK"; inventory-check "RESULT: OK" ("note: status: 39 lines / 11821 chars (cap 120 / 12000)").
- Review A: round 1 REJECT (B1, B2), fixed before any snapshot; confirming read APPROVE, nothing of the five, no should-fix (bridge-check --sources 146 OK, SOURCES MATCH bridge 2026.11.11a; 39 passed in 0.72s)
- the full suite with the pull request's variables (GITHUB_REF=refs/pull/149/merge): 5091 passed, 41 skipped in 1919.40s (0:31:59), exit 0 (launcher, stripped, key file with GITHUB_REF=refs/pull/149/merge)

## Expected bookkeeping and records in the diff
bridge/cursor-bridge/MANIFEST.json (regenerated); docs/REQUIREMENTS.md (R-064 built; R-062's Evidence gains tests/test_bug044.py, stage H2's round 2 records part); project.json; the records commit: docs/PROJECT_STATUS.md (as at PR #149's merge, Bridge version moved with the stamp), docs/INVENTORY.md, docs/HARDENING.md; and run/review/ (these files).
