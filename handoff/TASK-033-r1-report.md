# TASK-033-r1 report

## Files changed

- `bridge/cursor-bridge/bridge_env.py` — unified squash reader helpers and `squash_merged_ids_from_lines` / updated `squash_merged_ids`
- `bridge/cursor-bridge/plan-check.py` — imports `bridge_env`, narrowed parenthesis docstring, `merged_ids` delegates to reader
- `bridge/cursor-bridge/pace-report.py` — new R-044 pace table program
- `bridge/cursor-bridge/MANIFEST.json` — regenerated via make-manifest
- `tests/test_plan_check.py` — R-044 ISS-013 and main regression tests
- `tests/test_pace_report.py` — new R-044 pace-report tests
- `tests/test_dump_cli.py` — `pace-report.py` in ARGPARSE
- `docs/cli-reference.json`, `docs/CLI_REFERENCE.md` — regenerated via dump-cli

## Reader (`bridge_env.py`)

Name: `squash_merged_ids_from_lines(lines, id_rx, plan_style=None)` and `squash_merged_ids(folder, id_rx, git_runner=None, ref="main")`.

Plan pattern (`PLAN_ID_PATTERN`): subject, plan Merge (`_PLAN_MERGE_RX`), narrowed parenthesis (`_parenthesis_merged_ids`), trailer. Grammar pattern: grammar Merge first, subject (leading ID tokens only; N4), narrowed parenthesis, trailer. Parenthesis merges only when every comma-separated item is a bare ID or `R-nnn`; `R-nnn` adds nothing under the plan pattern.

## Divergences and N4

- `Merge pull request #1 from x/feat/task-005`: plan Merge branch scan merges TASK-005.
- `Merge pull request #9 from x/feature-z (TASK-100)`: plan tries Merge then parenthesis; TASK-100 merges.
- `Merge pull request #1 from x/task-001ab`: plan `\b` on branch token merges nothing.
- N4: `_subject_leading_ids` stops at the first token that is not a hyphen+digit ID, so mid-subject IDs merge nothing under either pattern.

## Verification

- `python -m pytest tests/test_task033_supervisor.py -q -p no:cacheprovider` — pass (103)
- `python -m pytest tests/test_plan_check.py tests/test_pace_report.py -q -p no:cacheprovider` — pass (14)
- `python -m pytest tests/test_task032_supervisor_launcher.py tests/test_task032_supervisor_guard.py tests/test_task032_supervisor_r4.py tests/test_bridge_run_review_ceiling.py tests/test_review_guard_ceiling.py tests/test_evaluate_reports.py tests/test_dump_cli.py tests/test_tests_windowless.py -q -p no:cacheprovider` — pass (494)
- `git diff --quiet 858da29 -- tests/test_task033_supervisor.py` — exit 0
- `python bridge/cursor-bridge/plan-check.py` — exit 0
- `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge/bridge_env.py bridge/cursor-bridge/plan-check.py bridge/cursor-bridge/pace-report.py tests/test_plan_check.py tests/test_pace_report.py` — 0 FAIL
- `python tools/dump-cli.py` and `python tools/dump-cli.py --check` — pass
- `python tools/make-manifest.py` — OK
- `python bridge/cursor-bridge/bridge-check.py --root bridge --sources` — OK

## Mutations (manual, restored after each)

1. Parenthesis any-ID inside — caught by `test_task033_parenthesis_with_a_non_id_item_merges_nothing`
2. Parenthesis single-item only — caught by `test_task033_parenthesis_items_may_have_spaces_around_them`
3. Subject ID after leading word — caught by `test_task033_n4_an_id_after_a_leading_word_merges_nothing`
4. Merge before parenthesis on failed branch map — caught by `test_task033_the_three_divergences_read_as_plan_check_did`
5. Start from rounds only / launcher only — caught by `test_task033_started_whichever_is_earlier`
6. Stage record as start — caught by `test_task033_stage_and_records_subject_records_are_no_start`
7. Rounds from reports alone — caught by `test_task033_rounds_guard_record_outranks_reports_and_err_files_outnumber`
8. Duplicate message id summed twice — caught by `test_task033_tokens_dedupe_a_message_id_at_its_greatest_total`
9. subagents ignored — caught by `test_task033_tokens_subagents_record_counted`
10. Blank mean as 0 — caught by `test_task033_a_week_without_a_merge_prints_a_blank_mean`
11. Author date for merge week — caught by `test_task033_a_merge_week_is_the_committer_date`
12. `--ceiling` default 4 — caught by `test_task033_over_the_default_ceiling_listed_by_id`

## Tests outside Scope

None failing after final run.

## Summary

TASK-033 centralizes squash-subject reading in `bridge_env.py` with a narrowed closing-parenthesis rule (ISS-013), wires `plan-check.py` to that reader, and adds read-only `pace-report.py` for weekly pace tables (starts, merges, rounds, days, HARDENING lines, optional tokens) plus builder and supervisor tests and CLI reference updates for R-044.

## Assumed, not verified

- Builder regression on `main` uses `new - former == set()` and `former - new <= {TASK-031}` so a legitimate `TASK-031:` subject merge on `main` does not fail the test · the brief’s literal `former minus {TASK-031}` would drop that merge too · a commit inventory would show whether only 9f6ace6 added the spurious TASK-031 under the former parenthesis rule.
- Launcher rows with non-zero `exit` still count as increment starts · brief says builder launch with `brief` · no fixture uses a failed launch as the first start.
- Seeded guard rounds with empty `time` never contribute to start · matches brief and code path skipping empty times.
