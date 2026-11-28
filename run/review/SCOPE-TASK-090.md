# SCOPE - TASK-090 (R-112): the launcher's small repairs

Where the increment ends: in bridge/cursor-bridge/bridge-run.py only: (1) the limit branch that is not a watch removes the run's pid file after writing its record row and before `killer()`, as the watch's branch already did, keeping the removal after the try block; (2) for the driver and test kinds only, the child's environment gets PYTHONIOENCODING=utf-8 where it has none after the stripped or unstripped environment and a key file's names are merged, and keeps any value it has; no kind sets PYTHONUTF8; (3) a refused `--kind test` launch whose command the driver kind would accept (the existing resolver), and whose launcher words carry no `--key-file`, gets one more refused line naming `--kind driver`, still exit 125; (4) the module docstring and the usage text say what a stripped run gets of its own and what still leads to the owner's folders. merge_ids, the options, the acceptance rules and bridge_env.py are unchanged. The command reference and MANIFEST are regenerated. R-112 stays planned until TASK-096.

Rounds: three builder rounds (briefs handoff/TASK-090.md, -r2.md, -r3.md). Round 1's help text was the brief's and claimed isolation the code does not give (a brief error); rounds 2 and 3 corrected it against bridge_env (CACHES, APP_CACHES, APP_LINKS, agent_home, write_gitconfig). The round count at the guard is the Review B round this snapshot opens.

## Scope (round 1's brief, quoted; rounds 2 and 3 narrow it to the program, the generated files and their reports)

Files and directories you may create or modify:
- bridge/cursor-bridge/bridge-run.py
- bridge/cursor-bridge/MANIFEST.json
- tests/test_improve_launcher_small.py
- tests/test_program_review_rows.py
- docs/cli-reference.json
- docs/CLI_REFERENCE.md
- docs/BUILDER_NOTES.md
- handoff/TASK-090-r1-report.md

Do not modify anything else.

Limits on these paths:
- `tests/test_improve_launcher_small.py` is the supervisor's acceptance file. `tests/test_program_review_rows.py` holds the supervisor's widened guard test, `test_r079_the_launcher_tests_write_no_row_into_the_checkout`. Both files were committed at the checkpoint and are listed in Scope only because the plan lists them. Read both and run both. **Do not edit either one.**
- `bridge/cursor-bridge/MANIFEST.json` changes only by running `python tools/make-manifest.py`. `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` change only by running `python tools/dump-cli.py`. Never edit any of the three by hand (Done).
- `docs/BUILDER_NOTES.md`: add new dated lines at its end only.
- In `bridge-run.py`, change only what Requirements 1 to 4 need.

## Out of scope (round 1's brief, quoted)

- .env and anything under secrets/
- CI configuration
- `docs/` and `handoff/`, except the files the Scope section names. `docs/REQUIREMENTS.md`, `docs/HARDENING.md` and `docs/PROJECT_STATUS.md` are the supervisor's records, written in its records-only commit.
- `bridge/cursor-bridge/bridge_env.py`, including `stripped_env`. The encoding default is set in `bridge-run.py`.
- Every other program under `bridge/`, every text under `bridge/commands/`, `bridge/agents/` and `bridge/cursor-bridge/workflow/`, and `bridge/cursor-bridge/VERSION`, which must come out unchanged.
- Every test file. That includes the two in Scope, `tests/test_program_launcher_forms.py` (its test that the launcher sets no `PYTHONUTF8`) and the existing test that holds `merge_ids` sorted. It also includes `tools/make-manifest.py` and `tools/dump-cli.py`: you run them and edit neither.
- The rest of C54: the `interpreters` list in `project.json` and the `jscpd` driver word are later work. Add neither.
- Every option of the launcher: none is added, removed or renamed. No acceptance rule is added or widened.
- Every brief under `handoff/` other than your report.

## Threat model

The launcher's acceptance rules are a security boundary: a command line is text a builder or a reviewer can write, and whatever the launcher starts runs with the caller's rights or the stripped environment. The hint is text on a launch already refused with exit 125; nothing new starts. The encoding default must reach no builder, reviewer or watch run and must not replace a value the caller set. The pid file removed earlier must be this run's own (named by its run id under run/launcher/pids/ of the launch folder). The help text must not tell a reader that `--strip` is a sandbox.

## The supervisor's tests

tests/test_improve_launcher_small.py (23 test functions, 36 tests with their parameters), each enforcing docs/BUILD_PLAN.md TASK-090's Done when (R-112; DESIGN.md C36, C37, C54's first part, T74):

- test_r112_a_run_ended_at_its_limit_leaves_no_pid_file
- test_r112_a_run_that_ends_normally_leaves_no_pid_file_either
- test_r112_every_limit_branch_removes_the_pid_file_before_it_ends_the_tree
- test_r112_a_driver_s_child_gets_utf_8_where_the_caller_set_none
- test_r112_a_driver_s_child_keeps_the_caller_s_value
- test_r112_a_key_file_s_value_counts_as_the_caller_s
- test_r112_a_test_s_child_gets_utf_8_where_the_caller_set_none
- test_r112_a_test_s_child_keeps_the_caller_s_value
- test_r112_a_builder_s_and_a_reviewer_s_environment_unchanged
- test_r112_the_launcher_sets_no_pythonutf8
- test_r112_a_test_launch_of_a_supervisor_program_names_the_driver_kind
- test_r112_a_test_launch_of_the_installed_mutation_engine_names_the_driver_kind
- test_r112_another_program_s_refusal_names_no_kind
- test_r112_a_test_launch_with_a_key_file_names_no_driver_kind
- test_r112_a_supervisor_program_under_another_kind_gets_no_hint
- test_r112_the_driver_kind_still_runs_the_supervisor_program
- test_r112_the_usage_text_names_the_owner_s_folders_a_stripped_run_does_not_see
- test_r112_the_docstring_names_them_too
- test_r112_the_help_claims_no_more_than_the_strip_gives
- test_r112_the_help_names_what_the_home_folder_still_reaches
- test_r112_no_environment_name_moves_the_record
- test_r112_the_launcher_reads_no_environment_name_but_its_two_test_names
- test_r112_merge_ids_is_written_sorted

Red on main's code: the fourteen listed in run/supervisor/TASK-090-mutants.json's new_tests, shown by the mutation engine's checkpoint run on 3973eb7. The rest hold what stands (a run that ends normally, the caller's value kept, builder and review unchanged, no PYTHONUTF8, another program's refusal naming no kind, the driver kind still running the program, the record not moved, merge_ids sorted).

Also tests/test_program_review_rows.py: the guard test of R-079 widened to every test file that names the launcher (about 52) and to the checkout's pid folder; skipped where the checkout has no run/ (as in CI). It passed in each own-file run (round 3: 369 passed, 3 skipped over nine files).

## The mutants

run/supervisor/TASK-090-mutants.json: 9 mutants (the briefs' M1 to M9), each killed in the scratch listing (run/supervisor/mutant_failures.py); the engine's full run is run/agent/TASK-090-mutation.out.

## Expected bookkeeping and records in the diff

- handoff/TASK-090.md, -r2.md and -r3.md (the briefs) and handoff/TASK-090-r1-report.md, -r2-report.md and -r3-report.md (the builder's reports)
- docs/HARDENING.md, docs/PROJECT_STATUS.md (the records commit)
- docs/CLI_REFERENCE.md, docs/cli-reference.json and bridge/cursor-bridge/MANIFEST.json (regenerated)
- run/review/ (these review files)
