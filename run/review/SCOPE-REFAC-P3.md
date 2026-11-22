# SCOPE - REFAC-P3 (stage P3's refactoring pass, PR #197)

## What the branch is
Stage P3's refactoring pass (bridge/cursor-bridge/workflow/phases/delegation-loop/refactoring-pass.md): removing duplication and simplifying code with the same functionality, one gate pass for the whole branch, one squash. No `docs/CHANGES.md` entry: a refactoring changes no behaviour. The question for the reviewers: **is this behaviour-preserving?**

The base is origin/main c530abd (TASK-078, PR #196). Stage P3's own change is its eleven squash commits after 618292e (PRs #185 to #196). jscpd was not launched (an npx download needs the owner's yes); refactor-scout read the stage's change against the 400-line budget: eight candidates, all COVERED, about 190 lines; four taken in three briefs (production lane), four recorded as leads; the tests lane not taken (a lead).

## The briefs
Each brief's whole text is in the diff (handoff/REFAC-012.md to handoff/REFAC-014.md) with its Scope, the sites and the semantics the packager confirmed by reading, and the builder's report (handoff/REFAC-01N-r1-report.md). Scopes:
- REFAC-012: bridge/cursor-bridge/evaluate-reports.py, MANIFEST.json, docs/BUILDER_NOTES.md, its report.
- REFAC-013: bridge_env.py, bridge-run.py, review-guard.py, MANIFEST.json, docs/BUILDER_NOTES.md, its report.
- REFAC-014: bridge_env.py, in-flight.py, pace-report.py, evaluate-reports.py, MANIFEST.json, docs/BUILDER_NOTES.md, its report.

## The commits
1. The REFAC-012 brief; REFAC-012 (builder composer-2.5, run 2026-11-22T17:09:00Z, exit 0): scan_project's eight failed-read blocks become one `failure` tuple per failing read and one block after the reads, before `_read_alerts`; `ledger_skip` deleted (always set with `scan_unreadable`); the always-true `if not scan_unreadable:` in the runs loop's for-else deleted; the non-dict body and non-list runs branches folded into `_validate_runs_list` (which already answers "reply could not be parsed" for a non-list); `DEP_SCAN_RERUN`. Evidence: the brief's tests "192 passed" before and after; the 25 test files that read evaluate-reports.py or the manifest "1110 passed, 21 skipped".
2. The REFAC-013 and REFAC-014 briefs (one commit, f03f1de); REFAC-013 (run 2026-11-22T17:22:38Z, exit 0): `bridge_env.round_cause_word(value)` and `_CAUSE_SEPS` (moved from review-guard.py), called by bridge-run.py's `round_cause` and review-guard.py's `_cause_on_first_line`, each keeping its own line-finding. Evidence: "200 passed, 1 skipped" before and after; 20 files "494 passed, 1 skipped".
3. REFAC-014 (run 2026-11-22T17:34:33Z, exit 0): `bridge_env.REVIEWERS` replaces in-flight.py's `REVIEWERS` and pace-report.py's `_REVIEWERS`; `bridge_env.git_read_env()` replaces the byte-identical `_git_env` in evaluate-reports.py and pace-report.py. Evidence: "341 passed, 1 skipped" before and after; 30 files "1259 passed, 22 skipped".
4. The records commit: docs/HARDENING.md (the pass's section), docs/INVENTORY.md (the jscpd row), docs/PROJECT_STATUS.md as at this pull request's merge (the project's rule, ISS-009).

## Scope check, read
scope-check reads a brief's range from the commit that first added it. The REFAC-013 and REFAC-014 briefs were committed before REFAC-012 ran, so REFAC-013's drift line (evaluate-reports.py) and REFAC-014's (bridge-run.py, review-guard.py) are the earlier briefs' own commits; each builder's uncommitted changes were within its Scope.

## The purity reading
`refactor-check.py main --max-lines 400`: "base: main | lane: production | files: 13 | changed lines: 281 (budget 400) | allowed test files: 0", PURE.

## Evidence already taken
- Review A, refactoring mode, the whole branch: APPROVE, nothing blocking, nothing to fix (read_failures' order kept, GitHub reads in the same number and order, new_last and new_standing as before; round_cause_word the old loop with the same separators; git_read_env line for line; no removed name in use; MANIFEST hashes equal the committed files').
- Mutation (D1): 90 mutants of stage P3's eight mutants files checked at the branch's tree; TASK-077's m06, m07, m11 and m13 moved by REFAC-012, re-anchored with their meaning kept (m11 now inserts its empty-list default before the `_validate_runs_list(all_runs)` call), all 90 found once, the four run again on the branch's tree: "counts: run=4 cached=0 killed=4 survived=0 not applied=0 error=0 expected survive=0".

## Out of scope
- Not taken, recorded in docs/HARDENING.md: the scout's candidates 5 to 8 (small dead weight in evaluate-reports.py and pace-report.py, bridge-install.py's tidy, bridge-check.py's two REFUSED prints, conformance-check.py's double walk), its behaviour notes (the pending-failure path's second read of `_run_exit_code`; `load_projects` ignoring pace-report's `--home`; `classify_window_runs`' unused `marker_at`), stage P2's candidates 3 and 6, and the tests-lane duplication. Each is as it was before the pass: not this diff's defect.
- Stage P3's review, its demonstration and reflection, and stage P4 are later work.

## Threat model
docs/INVENTORY.md (Decisions) records ASVS level 2. The trust boundaries these programs sit on: GitHub's replies (read through bridge_env's gh readers) for the security step; git's answers in a project's checkout for the origin read and the pace report, run in the read-only environment `git_read_env` builds (no optional locks, no lazy fetch, the seven `GIT_*` redirections dropped); the in-flight log's PASS lines and the SCOPE file's `Round cause:` line, matched against fixed lists. This change moves no boundary: the same environment, the same lists, every failed read still a finding with the ledger update skipped.

## Tests the supervisor wrote
None. No test file is changed.

## Expected bookkeeping files in the diff
docs/HARDENING.md, docs/INVENTORY.md, docs/PROJECT_STATUS.md, handoff/REFAC-012.md to handoff/REFAC-014.md and their three r1 reports, bridge/cursor-bridge/MANIFEST.json, and run/review/ (this file and the diff).
