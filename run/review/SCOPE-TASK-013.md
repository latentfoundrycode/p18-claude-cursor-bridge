# SCOPE - TASK-013

TASK-013 enriches three phase modules: run parameters, configuration (Phase 5) and the delegation loop (Phase 6), and splits the delegation loop. It is governance text the supervisor writes (N4, the plan's §15 condition 3), with no builder run, so there is no builder's brief and no builder's assumption list. Its plan entry is docs/BUILD_PLAN.md, "### TASK-013 — Enrich phase modules: run parameters, configuration, the delegation loop".

## Scope (the plan's, as widened at this increment)
- bridge/cursor-bridge/workflow/phases/run-parameters.md, .../configuration.md, .../delegation-loop.md and the new .../delegation-loop/refactoring-pass.md
- bridge/cursor-bridge/workflow/trace-exceptions.md; bridge/cursor-bridge/MANIFEST.json (through tools/make-manifest.py)
- tests/test_phase_modules_build.py
- widened for the split: bridge/commands/supervisor.md (the module table's delegation-loop row and the sentence under the table) and tests/test_session_start_module.py (the hook's expected names for Phase: building and Phase: changing; the pointer-grammar tests write a delegation-loop module of their own)

## Out of scope
- the build-phase conditions of screens and of the other traits (the frozen-rule brief constraint, the design-auditor step, the observability tests): they stay in delegation-loop.md until the trait files gather them (TASK-017, TASK-018)
- the change cycle, reflection and project-end modules (TASK-014), including the change cycle's interface step (docs/HARDENING.md, TASK-012's lead)
- any program under bridge/ or tools/; the session-start hook is unchanged (it already reads Sub-files: lines, TASK-015, FIX-003)
- the design for later increments (TASK-014 onwards) is not this diff's defect

## Requirements and the tests the supervisor wrote (tests/test_phase_modules_build.py, 22 tests: 19 committed at the checkpoint 2770735, three added in round 2 for Review A's B2, S3 and C1; all 22 run in a worktree of origin/main 5bed396: 19 red, the three bound tests of the unsplit modules passing there as bound tests do)
- R-004 (each phase module opens with its compaction-survival list): test_r004_the_module_opens_with_its_compaction_survival_list[run-parameters|configuration|delegation-loop]; test_the_run_parameters_are_written_as_each_answer_is_given; test_the_configurations_position_is_kept_on_in_flight (the procedure writes what the lists name)
- R-004, the refactoring pass: test_the_refactoring_passs_position_is_written_down
- R-006 (each module declares exactly its registry points): test_r006_the_module_declares_exactly_its_registry_points_in_the_registrys_order[*]; test_r006_each_point_says_where_its_additions_are_made[*] (reads each point's Applies cell); test_r006_the_inspect_point_spans_every_step_the_registry_gives_it (the registry's words checked first)
- R-032 (each module read whole; a module past the bound split into sub-files its pointer line names): test_r032_the_delegation_loop_names_its_sub_file_on_its_pointer_line; test_r032_step_9_is_in_the_sub_file_whole_and_nowhere_else; test_r032_step_9_is_verbatim (sha256 of the step as at origin/main); test_r032_the_module_and_its_sub_file_are_read_whole[*]
- R-005 with R-032 (the first real Sub-files: line): test_r005_the_hook_names_the_delegation_loop_and_its_sub_file
- the pointer sweep: test_the_core_names_the_delegation_loops_sub_file
- pins updated in tests/test_session_start_module.py: POINTED/LOOP (the hook names delegation-loop/refactoring-pass.md after delegation-loop.md; four tests red against the checkpoint's text), and own_loop (the five pointer-grammar tests write a delegation-loop module of their own, so they see only their own lines; each passed before and after)
No mutation driver.

## Expected bookkeeping and record files in the diff
- docs/BUILD_PLAN.md (TASK-013's Scope widened), docs/REQUIREMENTS.md (R-004, R-006 and R-032 evidence), docs/INVENTORY.md (the build-phase modules Features row; the module-size Decisions row), docs/HARDENING.md (Stage B3, "### TASK-013"; and the TASK-012 section's trace lead corrected, Review B's should-fix at PR #55), docs/PROJECT_STATUS.md (as at the merge of this pull request, ISS-009), docs/ROSTER.resolved.json (the roster's resolution stamp, if it changes)
- run/review/ (these review files)
