# SCOPE - TASK-089 (R-111): plan headings take the TASK, BUG, DEP, CONFIG and FIX prefixes

Where the increment ends: one tuple `PLAN_ID_PREFIXES` in bridge_env.py and `PLAN_ID_PATTERN` composed of it; every reader of a plan id (the walker, HEAD_RX, plan_increment_ids, plan_header_inc_ids, the header's parent and depends_on reading, the plan-style and grammar-style merged readers' branch mapping) reading the tuple or the pattern; an id picked out of a longer value only where no letter or digit precedes it; plan-check reading the brief of an increment of every prefix. records-check.py keeps its own list (TASK, BUG, FIX) and permission-guard.py its own rule; neither is edited. bridge-run.py and records-migrate.py read the shared pattern and needed no edit.

Rounds: two builder rounds (briefs handoff/TASK-089.md and -r2.md). The supervisor's rulings: a subject's leading ids win over its closing parenthesis for every prefix, as for TASK on main; a grammar-style branch whose rest after the prefix begins with a letter keeps its case (`task-cleanup` gives `TASK-cleanup` where main gave `TASK-CLEANUP`), outside the five (the launcher's lapse ignores case), accepted by Review A; docs/HARDENING.md, TASK-089, records both. The round count at the guard is the Review B round this snapshot opens.

## Scope (round 1's brief, quoted; round 2 keeps it)

Files and directories you may create or modify:
- bridge/cursor-bridge/bridge_env.py
- bridge/cursor-bridge/plan-check.py
- bridge/cursor-bridge/bridge-run.py
- bridge/cursor-bridge/records-migrate.py
- bridge/cursor-bridge/MANIFEST.json
- docs/cli-reference.json
- docs/CLI_REFERENCE.md
- docs/BUILDER_NOTES.md
- handoff/TASK-089-r1-report.md

Do not modify anything else.

Limits on these paths: `tests/test_improve_plan_prefixes.py` is the supervisor's acceptance file, committed at the checkpoint and not a path of yours: read it whole and run it, **do not edit it**. `bridge/cursor-bridge/bridge-run.py` and `bridge/cursor-bridge/records-migrate.py` are edited only where each holds a TASK-only pattern of its own, which then reads the shared tuple or pattern; the supervisor's scan found none in either (both read `bridge_env.PLAN_ID_PATTERN`), so confirm that by a content search of each file (for example `TASK|task-|\\d\{3`), quote the search and its result in the report, and edit neither unless the search finds one. `bridge/cursor-bridge/MANIFEST.json` changes only by running `python tools/make-manifest.py`, and `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` only by running `python tools/dump-cli.py` (Done), never by hand. `docs/BUILDER_NOTES.md`: new dated lines at its end only. In `bridge_env.py` and `plan-check.py`, change only what the Requirements need.

## Out of scope (round 1's brief, quoted)

- .env and anything under secrets/
- CI configuration
- docs/ and handoff/, except the files the Scope section names (`docs/REQUIREMENTS.md`, `docs/HARDENING.md`, `docs/PROJECT_STATUS.md` are the supervisor's records)
- `bridge/cursor-bridge/records-check.py`: it keeps its own list, `ID = r"(?:TASK|BUG|FIX)-\d{3,}[a-z]?"`, loads no sibling, and is not edited (a merged DEP or CONFIG subject needs no `docs/CHANGES.md` line, as on the checkpoint)
- `bridge/cursor-bridge/permission-guard.py`: its `INCREMENT_RX` names REFAC for branch and commit names, another rule; not edited
- every other program under `bridge/`, every text under `bridge/commands/`, `bridge/agents/`, `bridge/cursor-bridge/workflow/`, and `bridge/cursor-bridge/VERSION` (must come out unchanged)
- every test file, `tests/test_improve_plan_prefixes.py` among them; `tools/make-manifest.py` and `tools/dump-cli.py` (you run them, you edit neither)
- every brief under `handoff/` other than your report
- every option of every program: none is added, removed or renamed

## Threat model

A plan, a brief, a branch name and a commit subject are text a builder can write (KP-078); a merge commit reaches main only through the gate. The launcher's merge-unit rule admits an id only where it fullmatches the plan pattern and is a heading of docs/BUILD_PLAN*.md; its branch rule lapses a claim on a merged id, compared ignoring case. plan-check counts as merged only ids that are increments of the plan. A wider set of plan ids must not let a crafted value, name or subject pass a check main refused.

## The supervisor's tests

tests/test_improve_plan_prefixes.py (30 test functions, 91 tests with their parameters), each enforcing docs/BUILD_PLAN.md TASK-089's Done when (R-111; DESIGN.md C30):

- test_task089_one_tuple_of_prefixes_in_bridge_env
- test_task089_the_plan_id_pattern_is_the_explicit_alternation_of_the_tuple
- test_task089_the_pattern_accepts_each_prefix
- test_task089_the_pattern_refuses_the_other_forms
- test_task089_the_pattern_composes_inside_a_larger_pattern
- test_task089_a_heading_of_each_prefix_is_read
- test_task089_the_other_headings_are_no_increment_headings
- test_task089_no_task_only_pattern_stands_in_the_program
- test_task089_the_programs_compile_no_plan_id_pattern_of_their_own
- test_task089_records_check_keeps_its_own_list
- test_task089_the_walker_reads_each_prefix_and_no_other_heading
- test_task089_plan_increment_ids_reads_each_prefix
- test_task089_plan_check_reads_each_prefix_as_an_increment
- test_task089_a_subject_counts_as_merged_only_where_the_plan_holds_its_heading
- test_task089_each_merged_form_names_a_bug_increment
- test_task089_a_headed_plan_with_a_bug_increment_agrees
- test_task089_plan_check_reads_a_bug_increments_brief
- test_task089_the_completion_check_reads_satisfies_under_each_prefix
- test_task089_satisfies_under_another_heading_plans_nothing
- test_task089_records_migrate_writes_a_bug_increment_into_the_header
- test_task089_a_merge_unit_may_name_an_increment_of_each_prefix
- test_task089_a_merge_unit_naming_another_heading_is_refused
- test_task089_a_bug_brief_naming_its_unit_runs_on_its_branch
- test_task089_a_merged_dep_or_config_subject_needs_no_changes_line
- test_task089_a_merged_bug_subject_still_needs_its_changes_line
- test_task089_r2_an_id_inside_a_longer_word_is_read_whole_by_plan_check
- test_task089_r2_the_headers_field_reading_keeps_a_longer_word_whole
- test_task089_r2_the_grammar_style_maps_a_branch_of_each_prefix_as_task
- test_task089_r2_the_plan_style_maps_a_branch_of_each_prefix
- test_task089_r2_a_leading_id_wins_over_the_closing_parenthesis

Red on main's code: the forty-four listed in run/supervisor/TASK-089-mutants.json's new_tests, shown by the mutation engine's checkpoint run on e96c50f (exit 0). Forty-seven hold what stands (the refused forms, records-check's own list, the source scans of bridge-run.py and records-migrate.py, TASK branch forms, the plan-style forms main already read).

Also, the supervisor's changed expectations (Review A judged them right under C30): tests/test_task033_supervisor.py (its plan pattern is bridge_env's; the ISS-013 subject and `BUG-018: x (#61)` merge BUG-018 under the plan pattern, never TASK-031), tests/test_plan_check.py (the ISS-013 set; the history regression compared on TASK ids), tests/test_task032_supervisor_launcher.py (the parity test passes PLAN_ID_PATTERN). Added after Review B round 1, found by the pull request's CI (1 failed of 7887 on each runner): tests/test_task033_supervisor_r4.py, the parenthesis ( R-027 , BUG-018 ) merging BUG-018 under the plan pattern, the same class of change; it is the only commit since Review B round 1 apart from the review files.

## The mutants

run/supervisor/TASK-089-mutants.json: 13 mutants, all killed (run/agent/TASK-089-mutation.out). Each expected list was set from a scratch listing (run/supervisor/mutant_failures.py).

## Expected bookkeeping and records in the diff

- handoff/TASK-089.md and -r2.md (the briefs) and handoff/TASK-089-r1-report.md and -r2-report.md (the builder's reports)
- docs/HARDENING.md, docs/PROJECT_STATUS.md, docs/REQUIREMENTS.md (the records commit)
- bridge/cursor-bridge/MANIFEST.json (regenerated)
- run/review/ (these review files)
