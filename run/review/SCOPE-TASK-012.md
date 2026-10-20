# SCOPE - TASK-012

TASK-012 enriches two phase modules: the interface phase (Phase 3) and planning (Phase 4). It is governance text the supervisor writes (N4, the plan's §15 condition 3), with no builder run, so there is no builder's brief and no builder's assumption list. Its plan entry is docs/BUILD_PLAN.md, "### TASK-012 — Enrich phase modules: interface, planning".

## Scope (the plan's, as widened at this gate)
- bridge/cursor-bridge/workflow/phases/interface.md and its variant files .../interface/mockups.md, .../interface/command-design.md, .../interface/contract-design.md, .../interface/playable-prototype.md
- bridge/cursor-bridge/workflow/phases/planning.md
- bridge/cursor-bridge/workflow/trace-exceptions.md; bridge/cursor-bridge/MANIFEST.json (through tools/make-manifest.py)
- tests/test_phase_modules_interface_planning.py
- widened for the pointer sweep and Review B's should-fix carried from PR #53: bridge/commands/supervisor.md (the module table and the sentence under it, the Phase 3 sentence of "Main and conditional workflows", rule 13's pointer), bridge/cursor-bridge/workflow/phases/design.md (the gate sentence; the resume sentence), bridge/cursor-bridge/Merge-Verification-Policy.md (the approved-mockup rule's pointer), and the tests that pin what moved: tests/test_core_carve.py, tests/test_workflow_model.py, tests/test_session_start_module.py, tests/test_phase_modules_intake_design.py

## Out of scope
- the bodies of command-design.md and contract-design.md beyond their declaring paragraph: BUILD_PLAN TASK-022 writes them (R-026), its Done when bound at this gate to the artifact names this increment cites
- the build-phase conditions of screens (the frozen-rule brief constraint, the design-auditor step, the observability tests): they stay in delegation-loop.md until the trait has screens gathers them (TASK-017)
- the change cycle's interface step (change-cycle.md item 3): TASK-014's module, a lead in docs/HARDENING.md
- any program under bridge/ or tools/; the session-start hook is unchanged (FIX-003 hardened it for this increment's Variants: line)
- the design for later increments (TASK-013 onwards) is not this diff's defect

## Requirements and the tests the supervisor wrote (tests/test_phase_modules_interface_planning.py; 22 tests at the first fix round, 20 red against 9144081, the two size-bound tests passing there as bound tests do; one test added in round 2)
- R-004 (each phase module opens with its compaction-survival list): test_r004_the_module_opens_with_its_compaction_survival_list[interface|planning]; test_r004_the_interface_notes_are_written_by_the_procedure_and_no_key_among_them; test_r004_the_issues_paths_are_written_by_step_0
- R-006 (each module declares exactly its registry points): test_r006_the_module_declares_exactly_its_registry_points_in_the_registrys_order[interface|planning]
- R-010 (the mockups an addition the trait has screens activates; the build-phase conditions stay with the build modules): test_r010_the_mockups_are_an_addition_the_trait_has_screens_activates; test_r010_the_mockups_file_holds_the_phase_3_procedure_and_not_the_build_conditions; test_r010_no_text_calls_the_mockups_a_replacement
- R-012 (the four variants declared once in the interface module, each variant's text in one place): test_r012_the_four_variants_are_declared_once_in_the_interface_module; test_r012_each_variants_text_is_in_one_place; test_r012_each_variant_names_the_artifact_the_module_and_the_plan_cite; test_r012_the_gate_asks_for_every_variant_and_for_none; test_r012_the_plan_builds_against_what_the_interface_phase_approved
- R-032 (each module and variant file read whole): test_r032_the_module_and_each_variant_file_are_read_whole[*]
- R-005 with R-012 (the first real pointer line): test_r005_the_hook_names_the_interface_module_and_its_four_variants
- TASK-012's Done when (the playable prototype a declared pointer clear of completion-check's stand-in patterns; the patterns shown to match first): test_the_playable_prototype_is_a_declared_pointer_with_no_stand_in_wording
- the pointer sweep: test_the_interface_phase_is_named_by_its_variants_outside_the_module
- pins updated, each to the new text: tests/test_core_carve.py (the interface module's heading; trace-check's TRACED line and seven NOTE lines), tests/test_workflow_model.py (the Phase 3 sentence and heading), tests/test_session_start_module.py (POINTED/IFACE: the hook names the four variant files after interface.md; the split-module test writes its own module with the variants in another order), tests/test_phase_modules_intake_design.py (the resume sentence)
No mutation driver.

## Expected bookkeeping and record files in the diff
- docs/BUILD_PLAN.md (TASK-012's Scope widened and its Done when corrected; TASK-022's Done when bound), docs/REQUIREMENTS.md (R-010 in part, R-012 built; R-004, R-006 and R-032 evidence), docs/INVENTORY.md (the interface-variants Features row; the interface-notes Decisions row), docs/HARDENING.md (Stage B3, "### TASK-012"), docs/PROJECT_STATUS.md (as at the merge of PR #55, ISS-009)
- run/review/ (these review files)
