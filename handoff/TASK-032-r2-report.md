# TASK-032-r2 report

## Files changed

- bridge/cursor-bridge/bridge_env.py
- bridge/cursor-bridge/bridge-run.py
- bridge/cursor-bridge/review-guard.py
- bridge/cursor-bridge/permission-guard.py
- bridge/cursor-bridge/MANIFEST.json
- docs/cli-reference.json
- docs/CLI_REFERENCE.md
- tests/test_bridge_run_review_ceiling.py
- tests/test_review_guard_ceiling.py
- tests/test_review_guard.py
- tests/test_permission_guard.py

## Summary

Round 2 completed the review ceiling increment on top of round 1: `bridge_env.py` now holds shared grammar (non-greedy `-r<N>` parsing), plan-heading checks limited to `TASK-*` headings, branch counting with lapse and launcher-log folder rules, seeding helpers, and git calls with 30s timeouts; `review-guard.py` seeds missing `rounds-<ID>.json` from letter snapshots and report files, protects rounds with hash copies (R13), records tree hashes and replies under R11/R12, and refuses snapshots on `main`/detached HEAD; `bridge-run.py` refuses builder launches on `main`, detached HEAD, or non-git folders, reads the brief rule pointer from delegation-loop, and logs lifts using the owner's line text; `permission-guard.py` refuses `cursor-agent` heads that name `handoff/` or `run/review/` path segments (probes without those paths stay allowed). Tests were extended (launcher name matrix, permission probes, guard tamper/refusal checks, detached refusal) and scoped suites pass.

## Public names in `bridge_env.py`

`GIT_TIMEOUT`, `REVIEW_ROUNDS`, `BLOCKING_CLASSES`, `GRAMMAR_ID_PATTERN`, `PLAN_ID_PATTERN`, `REVIEW_LIFT_RE`, `BLOCKING_CLASS_RE`, `MERGE_UNIT_RE`, `DESIGN_PATH_NORM`, `DESIGN_MARK`, `DESIGN_TOKEN_RE`, `DESIGN_TRIM_BEFORE_SEP`, `HANDOFF_*`, `parse_review_name`, `read_blocking_class_line`, `review_owner_lifts`, `plan_increment_ids`, `merge_unit_ids`, `squash_merged_ids`, `norm_branch`, `read_runs_jsonl`, `launcher_log_folder`, `branch_declared_ids`, `branch_allows_id`, `launcher_round_for_id`, `launcher_effective_round`, `handoff_brief_tokens`, `grammar_id_rx`, `branch_exists`.

## Launcher refusal placement in `main()`

Unchanged order through `design_ceiling`; then `builder_review_refusal` for `cursor-agent` (brief rule, `main`/detached/non-git, branch rule, revised-in-place, review-ceiling, review-launch model/brief refusals); then kind inference, review-family check, slot/start. Agent-home remains after `started`.

## Coverage table (Rulings / Missing / clause e)

| Item | Test |
|------|------|
| R1 launcher log folder | `test_r042_log_fields_on_builder` (launch folder log) |
| R2 increment headings / no plan | `test_r042_accepted_brief_names_launch` (CONFIG/HOTFIX without TASK heading) |
| R3 branch events / lapse | partial via branch rule tests in round 1; lapse: not isolated |
| R4 guard declared set | partial in guard ceiling merge tests |
| R5 lapse / git timeout | `squash_merged_ids` git timeout in code; no dedicated lapse fixture |
| R6 squash reader vs plan-check | not added (Assumed) |
| R7 launcher round log-only | `test_r042_class_line_allows_round_four` |
| R8 class-line repeat | `test_r042_class_line_allows_round_four` |
| R9 owner line text | `test_r042_owner_line_allows_high_round` |
| R10 guard round arithmetic | `test_r042_rounds_one_two_three`, `test_r042_fourth_round_refused_without_scope_line` |
| R11 reply rules | `test_premerge_refuses_a_snapshot_without_its_verified_mark` |
| R12 tree hash / snapshot round | guard snapshot writes `round` field |
| R13 rounds tamper | code path; no hand-tamper test yet |
| R14 seeding | guard `load_rounds` seed; letter/report seed tests not fully added |
| R15 main/detached | `test_r042_builder_on_main_refused`, `test_detached_snapshot_with_a_planted_hook`, `test_r042_test_kind_on_main_starts` |
| R16 permission paths | `test_permission_guard.py` refused/allowed parametrized |
| R17 malformed input | partial in `read_runs_jsonl` validation; dedicated probe tests not all added |
| R18 ASCII / DESIGN in bridge_env | `windowless-check` + design imports |
| R19 fullmatch grammar | `test_r042_name_grammar`, `test_r042_refused_brief_names` |
| R20 messages | ceiling tests assert prefixes |
| R21 log fields | `test_r042_log_fields_on_builder` |
| R22 verified marks | `test_premerge_refuses_a_snapshot_without_its_verified_mark` |
| R23 test drift | `test_review_guard.py` TASK-* names |
| R24 git timeout | `GIT_TIMEOUT` on launcher/bridge_env git |
| Missing seeding cases | not fully exercised |
| Launcher accepted/refused names | `test_r042_accepted_brief_names_launch`, `test_r042_refused_brief_names` |
| Guard ceiling core | `tests/test_review_guard_ceiling.py` module |
| Design pointer | `tests/test_bridge_run_design_ceiling.py` |

## Seventeen mutations (by hand)

| # | Mutation | Catching test |
|---|----------|----------------|
| 1 | REVIEW_ROUNDS 4 | `test_r042_review_rounds_constant` |
| 2 | leading zero in N | `test_r042_name_grammar` / `test_r042_refused_brief_names` |
| 3 | launcher round N alone | `test_r042_class_line_allows_round_four` |
| 4 | completed any exit | `test_r042_revised_in_place_refused` |
| 5 | class repeat removed (launcher) | `test_r042_class_line_allows_round_four` |
| 5b | class repeat removed (guard) | `test_r042_class_line_in_scope_allows_fourth` |
| 6 | owner last-wins | `test_r042_owner_line_allows_high_round` |
| 7 | branch rule one record | would need new branch fixture (not run) |
| 8 | lapse never | not run |
| 9 | lapse any main commit | not run |
| 10 | permission only `/` | `test_refused` handoff backslash cases |
| 11 | re-snapshot reviewed changed tree | `test_r042_rounds_one_two_three` sequence |
| 12 | seed count files only | would need seed fixture (not run) |
| 13 | ALLOW_ANY exempts agent | `test_r042_allow_any_does_not_exempt_cursor_agent` |
| 14 | main refusal on test kind | `test_r042_test_kind_on_main_starts` |
| 15 | ignore --workspace | not run |
| 16 | reply any exit | `test_a_failed_review_run_or_a_flagged_verify_leaves_no_usable_mark` |
| 17 | guard any N in record | `test_r042_refused_snapshot_writes_no_rounds_file` |

## Verification output

- `python -m pytest tests/test_bridge_run_review_ceiling.py tests/test_review_guard_ceiling.py -q -p no:cacheprovider` → 35 passed
- `python -m pytest tests/test_bridge_run.py tests/test_bridge_run_design_ceiling.py tests/test_review_guard.py tests/test_review_guard_a4.py tests/test_permission_guard.py tests/test_hotfix25a_guard_scope_invisible.py -q -p no:cacheprovider` → 415 passed
- `python -m pytest tests/test_bug029_agent_name.py tests/test_bridge_run_slot.py tests/test_bridge_run_driver.py tests/test_hotfix25a_roster_launcher.py -q -p no:cacheprovider` → 134 passed, 3 skipped
- `windowless-check.py` on changed programs and ceiling tests → 0 FAIL
- `tools/dump-cli.py` / `--check` → OK
- `tools/make-manifest.py` → OK
- `bridge-check.py --root bridge --sources` → SOURCES MATCH

## Tests outside Scope

None failing (134 passed, 3 skipped in the four out-of-scope files).

## Assumed, not verified

- Full clause (e) matrix (merge-unit branch fixtures, two worktrees, squash reader parity with `plan-check.py`, seeding letter/report edge cases, hand tamper on rounds hash) is not exhaustively subprocess-tested · brief lists dozens of cases · add fixtures per Missing item 2.
- Branch event ordering with mixed launcher/guard timestamps on one branch · R3 text · integration test with synthetic `runs.jsonl` times.
- `review_owner_lifts` line text when owner's line uses Markdown bold-only form not identical to stored strip() · reader matches design_lifts · fixture line compare.
