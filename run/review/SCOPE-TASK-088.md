# SCOPE - TASK-088 (R-110): one reader for a brief's Satisfies ids

Where the increment ends: one locator (`brief_satisfies_line`) and one reader (`brief_satisfies_ids`) in bridge_env.py; the brief header's `satisfies` compared as a set; the launcher's refusal (`brief_header_refusal`, through `bridge-run.py`'s existing calls) walking the keys in the agreement's order, with the `none` refusal at `satisfies` and both lists with the remedy; one escape (`ascii_brief_quote`) for brief text; plan-check's two BRIEF lines. The packager's refactoring variant's exact `Satisfies: none` is TASK-096's (instruction text); R-110 stays planned until then.

Rounds: three builder rounds (briefs handoff/TASK-088.md, -r2.md, -r3.md). Round 3, at the ceiling, approved by Review A and passed by the security audit after the supervisor's ruling that the underscore-emphasised `none` (an id beneath it, the same id in the header) is outside the five at the ceiling; docs/HARDENING.md, TASK-088, records the ruling and its reasons. The round count at the guard is the Review B round this snapshot opens.

## Scope (round 1's brief, quoted; rounds 2 and 3 keep it)

Files and directories you may create or modify:
- bridge/cursor-bridge/bridge_env.py
- bridge/cursor-bridge/bridge-run.py
- bridge/cursor-bridge/plan-check.py
- bridge/cursor-bridge/MANIFEST.json
- tests/test_improve_satisfies_reader.py
- docs/cli-reference.json
- docs/CLI_REFERENCE.md
- docs/BUILDER_NOTES.md
- handoff/TASK-088-r1-report.md

Do not modify anything else.

Limits on these paths: `tests/test_improve_satisfies_reader.py` is the supervisor's acceptance file, written before this brief: read it whole and run it, **do not edit it**. `bridge/cursor-bridge/MANIFEST.json` changes only by running `python tools/make-manifest.py`, and `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` only by running `python tools/dump-cli.py` (Done), never by hand. `docs/BUILDER_NOTES.md`: new dated lines at its end only. In `bridge_env.py`, `bridge-run.py` and `plan-check.py`, change only what the Requirements need.

## Out of scope (round 1's brief, quoted)

- .env and anything under secrets/
- CI configuration
- docs/ and handoff/, except the files the Scope section names (`docs/REQUIREMENTS.md`, `docs/HARDENING.md`, `docs/PROJECT_STATUS.md` are the supervisor's records)
- `bridge/cursor-bridge/review-guard.py` (it calls `brief_header_refusal` and is not edited; its answers must stand, Requirement 6), `bridge/cursor-bridge/records-migrate.py`, every other program under `bridge/`, every text under `bridge/commands/`, `bridge/agents/`, `bridge/cursor-bridge/workflow/`, and `bridge/cursor-bridge/VERSION` (must come out unchanged)
- every test file; `tools/make-manifest.py` and `tools/dump-cli.py` (you run them, you edit neither)
- every brief under `handoff/` other than your report, even one the new reading would read differently (report it, Constraints)
- `plan_collect_satisfies_ids`, `plan_r_ids_outside_headers`, `walk_plan_prose_body` and `FIELD_RX` in `bridge_env.py`: a plan's reading stays as it is
- every option of every program: none is added, removed or renamed

## Threat model

A brief is text a builder or a reviewer can write (KP-078). The launcher's brief check is a gate of the loop and guards the agreement of a brief's header with its prose; the review guard (review-guard.py, not edited) calls the same refusal with keys merge_unit, id and round and must answer as on main. Text from a brief printed in a refusal or a plan-check line is escaped (non-ASCII, C0, DEL). The design's table (docs/DESIGN.md, C29) gives up main's refusals of a list in another order, a repeated id and ids written as bullets beneath the line.

## The supervisor's tests

tests/test_improve_satisfies_reader.py (31 test functions, 47 tests with their parameters), each enforcing docs/BUILD_PLAN.md TASK-088's Done when (R-110; DESIGN.md C29):

- test_task088_the_reader_reads_the_line_and_the_bullets_directly_beneath
- test_task088_the_reader_names_each_id_once_in_first_seen_order
- test_task088_the_reader_flags_a_none_that_carries_ids
- test_task088_the_briefs_two_readers_call_the_one_reader
- test_task088_brief_satisfies_reads_the_bullets
- test_task088_row1_a_line_of_two_ids_beside_the_same_header_is_launched
- test_task088_row2_bullets_beneath_the_line_are_launched
- test_task088_row3_a_repeated_id_is_launched
- test_task088_row4_the_same_set_in_another_order_is_launched
- test_task088_row5_none_beside_an_empty_header_is_launched
- test_task088_row6_a_none_that_carries_ids_is_refused_with_the_remedy
- test_task088_row7_a_disagreeing_list_is_refused_with_both_lists
- test_task088_a_none_with_a_non_ascii_line_is_refused_in_ascii
- test_task088_a_brief_with_no_header_keeps_its_reading_and_no_check_at_launch
- test_task088_plan_check_names_an_unmerged_brief_whose_header_disagrees
- test_task088_plan_check_names_an_unmerged_brief_whose_none_carries_ids
- test_task088_plan_check_passes_an_agreeing_brief_with_bullets
- test_task088_the_review_guard_answers_as_on_the_checkpoint
- test_task088_a_plans_satisfies_line_is_read_as_on_the_checkpoint
- test_task088_r2_a_control_byte_in_a_none_line_is_escaped_at_the_launcher
- test_task088_r2_a_control_byte_in_a_none_line_is_escaped_by_plan_check
- test_task088_r2_plan_checks_disagreement_line_prints_the_lists_in_ascii
- test_task088_r2_a_field_written_as_a_bullet_ends_the_bullets
- test_task088_r2_none_is_matched_as_a_word
- test_task088_r2_none_inside_another_word_or_later_is_no_none
- test_task088_r2_the_ids_beside_a_none_are_returned
- test_task088_r2_one_locator_finds_the_line_for_the_reader_and_the_refusal
- test_task088_r3_a_none_that_carries_ids_is_refused_whatever_the_headers_list
- test_task088_r3_none_ends_at_a_word_boundary
- test_task088_r3_plan_checks_disagreement_line_carries_the_launchers_remedy
- test_task088_r2_a_wrong_id_is_told_before_a_none_that_carries_ids

Red on the checkpoint c70da82 (main's code): the forty listed in run/supervisor/TASK-088-mutants.json's new_tests, shown by the mutation engine's checkpoint run (exit 0). Seven hold what stands (rows 1 and 5, the header-less brief, plan-check's agreeing brief with bullets, the review guard, a plan's own line, a wrong id told before a none).

Also: tests/test_records_migrate.py, test_r062_a_satisfies_id_named_twice_is_written_once, the supervisor's changed expectation (a repeated id written once, C29).

## The mutants

run/supervisor/TASK-088-mutants.json: 18 mutants, all killed (run/agent/TASK-088-mutation.out). Each expected list was set from a scratch listing (run/supervisor/mutant_failures.py).

## Expected bookkeeping and records in the diff

- handoff/: thirty merged briefs' `satisfies` headers set to the rows their prose lists as bullets (the supervisor's checkpoint commit; no prose changed)
- handoff/TASK-088.md, -r2.md, -r3.md (the briefs) and handoff/TASK-088-r1-report.md, -r2-report.md, -r3-report.md (the builder's reports)
- docs/HARDENING.md, docs/PROJECT_STATUS.md, docs/REQUIREMENTS.md (the records commit)
- bridge/cursor-bridge/MANIFEST.json (regenerated)
- run/review/ (these review files)
