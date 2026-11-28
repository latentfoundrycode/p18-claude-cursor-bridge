# SCOPE - TASK-091 (R-113): the heavy slot's line names the holder's limit, project and branch

Where the increment ends: in bridge/cursor-bridge/bridge-run.py only: the heavy slot's holder record (and the folder lock's, the same dict) gains `project` (the launch folder's parent's name where the launch folder is named `Workspace`, the launch folder's own name otherwise; a name, never a path) and `branch` (the run's log branch), each written only where it fits its rule (`HOLDER_PROJECT_RE`: 1 to 64 of A-Z a-z 0-9 . _ -; `HOLDER_BRANCH_RE`: 1 to 100 of those and /; fullmatch, ASCII); the reader returns them and treats a record whose present field breaks its rule as no live record (`held by unknown`); a record without them (as 2026.11.23a writes it) is read as before; every line naming a holder (the waiter's line, the line at the bound, the several-slot line) goes on with `, limit <n>s`, then `, project <name>` and `, branch <branch>` where the record holds them. No new option, no queue, no priority. MANIFEST is regenerated.

Rounds: one builder round (handoff/TASK-091.md). The round count at the guard is the Review B round this snapshot opens.

## Scope (the brief, quoted)

Files and directories you may create or modify:
- bridge/cursor-bridge/bridge-run.py
- bridge/cursor-bridge/MANIFEST.json
- tests/test_improve_slot_line.py
- tests/test_bridge_run_slot.py
- tests/test_hotfix24a_heavy_slots.py
- tests/test_loop_text_windowless.py
- docs/cli-reference.json
- docs/CLI_REFERENCE.md
- docs/BUILDER_NOTES.md
- handoff/TASK-091-r1-report.md

Do not modify anything else.

Limits on these paths:
- `tests/test_improve_slot_line.py` is the supervisor's acceptance file. `tests/test_bridge_run_slot.py` and `tests/test_hotfix24a_heavy_slots.py` hold the line by a whole match; the supervisor changed those matches to the new line before the checkpoint (marked `TASK-091`). `tests/test_loop_text_windowless.py` is unchanged and must stay so. All four were committed at the checkpoint and are listed in Scope only because the plan lists them. Read them and run them. **Do not edit any of the four.**
- `bridge/cursor-bridge/MANIFEST.json` changes only by running `python tools/make-manifest.py`. `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` change only by running `python tools/dump-cli.py`. Never edit any of the three by hand (Done). If `dump-cli.py` leaves the two reference files unchanged, that is the expected outcome (Requirement 7); say so in the report.
- `docs/BUILDER_NOTES.md`: add new dated lines at its end only.
- In `bridge-run.py`, change only what Requirements 1 to 7 need.

## Out of scope (the brief, quoted)

- .env and anything under secrets/
- CI configuration
- `docs/` and `handoff/`, except the files the Scope section names. `docs/REQUIREMENTS.md`, `docs/HARDENING.md` and `docs/PROJECT_STATUS.md` are the supervisor's records, written in its records-only commit.
- The loop's text under `bridge/cursor-bridge/workflow/` (including `workflow/phases/delegation-loop.md`, which quotes the waiting line's form). It is not edited here; the report names it for TASK-096 (Done).
- `bridge/cursor-bridge/CHANGELOG.md`, `bridge/cursor-bridge/VERSION` (which must come out unchanged), `bridge/cursor-bridge/bridge_env.py`, every other program under `bridge/`, and every text under `bridge/commands/` and `bridge/agents/`.
- Every test file, the four in Scope included. Also `tools/make-manifest.py` and `tools/dump-cli.py`: you run them and edit neither.
- Every option of the launcher: none is added, removed or renamed. No queue, no priority, no new environment name, and no change to the wait bound's arithmetic or to `holder_end_time`'s result.
- Every brief under `handoff/` other than your report.

## Threat model

The holder record is a JSON file under the owner's home folder that any process of the owner's can write; the reader treats it as untrusted, and what it prints goes onto lines a supervisor reads and may quote into its own records. A field that could carry a path, a newline, a control character or an unbounded length must never reach a printed line: the record is refused whole (`held by unknown`). The project must be a folder's name, never a path, so that no computer path reaches a line. The change must not alter who gets the slot, when a waiter gives up, or the exit codes.

## The supervisor's tests

tests/test_improve_slot_line.py (10 test functions, 21 tests with their parameters), each enforcing docs/BUILD_PLAN.md TASK-091's Done when (R-113; DESIGN.md C51):

- test_r113_the_record_carries_the_project_folders_name_and_the_branch
- test_r113_a_launch_folder_not_named_workspace_is_its_own_project
- test_r113_a_name_outside_the_list_is_not_written
- test_r113_the_waiters_line_names_the_limit_the_project_and_the_branch
- test_r113_the_line_at_the_bound_names_them_too
- test_r113_an_older_record_is_read_and_named_without_them
- test_r113_a_record_whose_new_field_breaks_the_rules_is_no_live_record
- test_r113_the_reader_returns_the_fields
- test_r113_each_line_form_names_them
- test_r113_no_new_option

Red on main's code: the nineteen listed in run/supervisor/TASK-091-mutants.json's new_tests, shown by the mutation engine's checkpoint run on 1e6a696. The two others are controls (a folder name outside the list is not written; no new option).

Changed expectations (the supervisor's, at the checkpoint, the new tail and nothing else): tests/test_bridge_run_slot.py (three whole matches) and tests/test_hotfix24a_heavy_slots.py (a TAIL_RE appended to six whole matches; the plan's Scope gained this file at the checkpoint). tests/test_loop_text_windowless.py is unchanged: the loop's text holds the line's form up to `ends by <end>`, still a true prefix.

The own-file run (eleven files, the guard test tests/test_program_review_rows.py included): 410 passed, 4 skipped.

## The mutants

run/supervisor/TASK-091-mutants.json: 10 mutants (the brief's M1 to M9 and M10, the one-slot waiting line's tail), each killed; the engine's full run is run/agent/TASK-091-mutation.out (killed 10, survived 0).

## Expected bookkeeping and records in the diff

- handoff/TASK-091.md (the brief) and handoff/TASK-091-r1-report.md (the builder's report)
- docs/BUILD_PLAN.md (TASK-091's Scope gains tests/test_hotfix24a_heavy_slots.py)
- docs/HARDENING.md, docs/PROJECT_STATUS.md, docs/REQUIREMENTS.md (the records commit)
- bridge/cursor-bridge/MANIFEST.json (regenerated)
- run/review/ (these review files)
