# SCOPE - REFAC-P2 (stage P2's refactoring pass, PR #182)

## What the branch is
Stage P2's refactoring pass (bridge/cursor-bridge/workflow/phases/delegation-loop/refactoring-pass.md): removing duplication and simplifying code with the same functionality, one gate pass for the whole branch, one squash. No `docs/CHANGES.md` entry: a refactoring changes no behaviour. The question for the reviewers: **is this behaviour-preserving?**

The base is origin/main 45e4322 (TASK-082, PR #181). Stage P2's own change is its fifteen squash commits 295d4fd to 45e4322 (PRs #166 to #181, consecutive on main from 16e7e89). jscpd's launch was refused by the session's permission classifier (as at stage P1); refactor-scout read the stage's change against the 400-line budget: six candidates, all COVERED, about 225 lines; four taken (one brief each, in the production lane), two recorded as leads; the tests lane not taken (a lead). The scout's lists are kept in run/supervisor/refactor-P2-candidates.md (gitignored) and recorded in docs/HARDENING.md, "Stage P2's refactoring pass".

## The briefs
Each brief's whole text is in the diff (handoff/REFAC-008.md to handoff/REFAC-011.md), with its Scope, Out of scope, the sites with their line numbers, the semantics the supervisor's reality check found, and the builder's report (handoff/REFAC-00N-r1-report.md). Scopes:
- REFAC-008: bridge_env.py, bridge-run.py, review-guard.py, MANIFEST.json, docs/BUILDER_NOTES.md, its report.
- REFAC-009: the same six.
- REFAC-010: bridge-run.py, MANIFEST.json, docs/BUILDER_NOTES.md, its report.
- REFAC-011: the same four.

## The commits
1. deed43f, the REFAC-008 brief; ff5786e, REFAC-008 (builder grok-4.7-medium, run 2026-11-19T01:04:50Z, exit 0): bridge_env's private `_suite_id` and `_app_id_of` become the public `is_int_id`, `app_id_of` and `suite_id`; bridge-run.py's `_watch_suite`, `_run_suite`, `_watch_app`, `_watch_app_tied` and review-guard.py's `_check_app`, `_named_app` deleted, their callers calling bridge_env. One addition: `app_id_of` and `suite_id` return None for a non-dict item (every caller already skipped non-dicts). Evidence: scope-check "SCOPE CLEAN"; the builder's six test files "530 passed, 5 skipped" before and after; the full suite, stripped, "7027 passed, 48 skipped in 2750.03s".
2. 3cc411a, the REFAC-009 brief; 822212f, REFAC-009 (run 2026-11-19T02:18:09Z, exit 0): bridge_env gains `reply_bits(got, fallback)` and `rule_contexts(got)`; review-guard.py's `_reader_bits` and bridge-run.py's `_watch_contexts` deleted; review-guard's `_rule_contexts` and bridge-run's `_watch_bits` keep their names, signatures and wording and call them. Evidence: "SCOPE CLEAN"; "530 passed, 5 skipped" before and after; the full suite "7027 passed, 48 skipped in 2737.29s".
3. cadcbdf, the REFAC-010 brief; 494b630, REFAC-010 (run 2026-11-19T03:50:19Z, exit 0): bridge-run.py's `_git_rev_parse_path(folder, *args)` replaces `_git_dir`, `_git_resolved_path` (with its stale docstring) and GitConfigWatch's inline --show-toplevel resolution; `after = before` in GitConfigWatch. The one difference in code the brief states and argues: an absolute --show-toplevel answer is now passed through os.path.normpath, where it was used as git printed it; check whether you read that as a behaviour change (the file read through `_git_file_state`, the path printed through `_git_display_path`). Evidence: "SCOPE CLEAN"; the brief's three test files "165 passed, 1 skipped" before and after; the full suite "7027 passed, 48 skipped in 2685.75s".
4. 02a38ac, the REFAC-011 brief; 248cb5c, REFAC-011 (run 2026-11-19T05:00:25Z, exit 0): `_watch_decision`'s first test becomes `if failed is not None:` (`_failed_check` already filters by the same named contexts under the base's list), and the wait's fail branch drops a `head12` recompute that passed the same arguments to the same pure function. Evidence: "SCOPE CLEAN"; "191 passed, 5 skipped" before and after; the full suite "7027 passed, 48 skipped in 2729.42s".
5. The records commit: docs/HARDENING.md (the pass's section; TASK-062's lead (1), TASK-084's lead (4), TASK-065's leads (9) and (10) marked Landed), docs/INVENTORY.md (the jscpd row), docs/PROJECT_STATUS.md written as at this pull request's merge (the project's rule, ISS-009); then a one-line commit putting this pull request's number into the HARDENING heading.

## The purity reading
`refactor-check.py main --max-lines 400` on 248cb5c: "base: main | lane: production | files: 13 | changed lines: 218 (budget 400) | allowed test files: 0", PURE: no test change, no CHANGES.md entry, within the size budget.

## Evidence already taken
- Review A, refactoring mode, the whole branch: APPROVE, nothing blocking, nothing to fix. Every merged function the copies it replaced character for character (or, for REFAC-008's added non-dict guard, unreachable through every caller); no removed name left in use; CRLF kept; MANIFEST.json's hashes equal the committed files'; its own run of tests/test_program_ready.py, test_program_watch_wait.py, test_program_branch_rule.py, test_program_git_config.py and test_header_currency.py "480 passed, 6 skipped".
- Mutation (D1): stage P2's 370 mutants (fourteen mutants files) checked at the branch's tree: 7 pairs not found once. Six were anchored on code the pass moved (TASK-064 m15; TASK-065 m13, m24, m25; TASK-083 m11, m17); one, TASK-061's m27, already matched twice on main since TASK-064 (#174) added a second `except (ValueError, RecursionError):` to bridge_env. All seven re-anchored with their meaning kept, all 370 then found once, and the seven run again on the branch's tree: "counts: run=7 cached=0 killed=7 survived=0 not applied=0 error=0 expected survive=0". The mutants files are under run/supervisor/ (gitignored).
- The records tests on the records commit (tests/test_release_b_bootstrap.py, tests/test_release_s_records_gate.py): "85 passed, 1 skipped".

## Out of scope
- Not taken, recorded in docs/HARDENING.md: the scout's candidate 3 (one resolver for prove_ci and the wait's `_watch_name`; it touches the merge gate's proof), candidate 6 (push-scan's line splitting, a PYTHON_HEADS constant), the tests-lane duplication, and what the builders noticed and left (the wait's `restart = seen_watch and named["kind"] == "runs"`, also redundant; review-guard passing `reply_bits`' text into `_cannot` without `_show`; `rule_contexts` not checking its entries are dicts; `import stat` inside two functions). Each is as it was before the pass: not this diff's defect.
- Stage P2's review, its demonstration and reflection, and stage P3 are later work.

## Threat model
docs/INVENTORY.md (Decisions) records ASVS level 2. The trust boundaries these programs sit on are GitHub's replies (read through bridge_env's gh readers, clipped by `_clip_reason`) for the wait before a CI watch and `review-guard.py ready`, and git's answers in the launch folder for the git-config watch. This change moves no boundary: an unreadable rule is still never a pass (`ready` answers CANNOT CHECK, the wait falls back to the runs), an app-tied context is still held only by that app's check, every GitHub text the launcher prints still passes through `_watch_plain`, and the git-config watch reads the same files the same way (no link followed, no non-regular file opened).

## Tests the supervisor wrote, each with the paragraph it enforces
None. No test file is changed.

## Expected bookkeeping files in the diff
docs/HARDENING.md, docs/INVENTORY.md, docs/PROJECT_STATUS.md, docs/BUILDER_NOTES.md (two lines appended by the builders), handoff/REFAC-008.md to handoff/REFAC-011.md and their four r1 reports, bridge/cursor-bridge/MANIFEST.json, and run/review/ (this file, the diff, the assumptions file).
