# SCOPE - TASK-014

TASK-014 enriches the last three phase modules: the change cycle, the reflection points and project end. It is governance text the supervisor writes (N4, the plan's §15 condition 3), with no builder run, so there is no builder's brief and no builder's assumption list. Its plan entry is docs/BUILD_PLAN.md, "### TASK-014 — Enrich phase modules: change cycle, reflection, project end".

## Scope (the plan's, as widened at this increment)
- bridge/cursor-bridge/workflow/phases/change-cycle.md, .../reflection.md, .../project-end.md
- bridge/cursor-bridge/workflow/trace-exceptions.md; bridge/cursor-bridge/MANIFEST.json (through tools/make-manifest.py)
- tests/test_phase_modules_close.py
- widened for docs/HARDENING.md's Stage B3 leads that name TASK-014: the four interface variant files (each declaring paragraph moved under `### What this variant is`, the mockups' procedure under `### The procedure`, their trace entries re-pointed) with tests/test_phase_modules_interface_planning.py, which pins their headings; tests/test_core_carve.py (the traceability check's pinned result: two of the change cycle's passages reworded); bridge/cursor-bridge/Glossary.md (the pointer sweep: its phase-module entry still said project end was part of the reflection points)

## Out of scope
- the bodies of the command and contract designs (TASK-022): the variant files keep their declaring paragraphs only
- the trait files (TASK-017, TASK-018) and the build-phase conditions they will gather
- any program under bridge/ or tools/
- Known-Pitfalls.md itself: the diff only adds it to TASK-030's Scope and Done when (PR #57's Review B should-fix, carried here); TASK-030 rewords KP-056
- the design for later increments is not this diff's defect

## Requirements and the tests the supervisor wrote (tests/test_phase_modules_close.py, 25 tests: 20 run in a worktree of origin/main 7552efc, 17 red there and the three bound tests passing as bound tests do; the five section pins added in round 2 fail there too, the headings they read not existing at the checkpoint)
- R-004 (each module opens with its compaction-survival list): test_r004_the_module_opens_with_its_compaction_survival_list[change-cycle|reflection|project-end]; test_r004_the_positions_the_survival_lists_name_are_kept (the change cycle's step on its `Change cycle:` line; the reflection points' and project end's finished steps in run/supervisor/in-flight.md)
- TASK-014's Done when, the compaction baseline's follow-up (Restructuring Plan §14.3): test_r004_an_issue_records_whether_a_compaction_preceded_it
- R-006 (each module declares exactly its registry points): test_r006_the_module_declares_exactly_its_registry_points_in_the_registrys_order[reflection|project-end]; test_r006_the_change_cycle_declares_no_point_and_says_so; test_r006_each_point_says_where_its_additions_are_made[*] (reads each point's Applies cell); test_r006_the_reflection_items_point_is_placed_before_the_record
- TASK-014's Done when, the tree-wide registry↔module cross-check: test_r006_the_tree_wide_registry_module_cross_check (every registry point declared by its module, every declaration in the registry in its order, every module a file and every file a module, no sub-file or variant file declaring a point)
- R-036 (the promotion pass): test_r036_the_promotion_pass_puts_the_flagged_traits_forward
- R-032: test_r032_the_module_is_read_whole[*]
- docs/HARDENING.md Stage B3 leads: test_the_change_cycle_runs_the_variant_of_every_interface_kind_it_touches; test_the_change_cycles_procedure_is_pinned (sha256, because one `new` trace entry covers the procedure); test_no_trace_entry_excuses_a_whole_phase_file; test_each_excused_variant_section_is_pinned[*] (round 2, Review A's should-fix 3: the five variant-file sections a `new` entry excuses, by sha256, and the variant files' entries exactly those five); test_the_glossary_names_the_modules_as_files
- changed: tests/test_core_carve.py (the pinned trace-check output: three NOTE lines added, 258 under workflow/, 10 excused); tests/test_phase_modules_interface_planning.py (the variant files' headings; the declaring paragraph read from its own section)
No mutation driver.

## Expected bookkeeping and record files in the diff
- docs/BUILD_PLAN.md (TASK-014's Scope widened; TASK-030's Scope and Done when gain Known-Pitfalls.md, carried from PR #57's Review B), docs/DESIGN_CRITIQUE.md (the windowless record's after-the-gate line extended for that carry), docs/REQUIREMENTS.md (R-004, R-006, R-032, R-036 built, their evidence), docs/INVENTORY.md (the closing modules Features row; a Decisions row for run/supervisor/in-flight.md as the reflection points' position), docs/HARDENING.md (Stage B3: three leads closed; "### TASK-014"), docs/PROJECT_STATUS.md (as at the merge of this pull request, ISS-009; its Working files wording carried from PR #57's Review B), docs/ROSTER.resolved.json (the roster's resolution stamp, if it changes)
- run/review/ (these review files)

## Review B round 1 (REJECT) and what this head does with it
- Blocking 1, taken: change-cycle.md's survival list names step 5's modules, `run-parameters.md` with `docs/RUN_PARAMETERS.md` and `configuration.md`.
- Blocking 2, taken: reflection.md's "Whether a compaction preceded it": `Compaction before: yes` means a compaction only; a resume or a fork is written on a line of its own; `unknown` where the hook's input names no source.
- Should-fix, taken: HARDENING's suite counts; step 7 runs project end through `project-end.md`, scaled (a third passage of the core's change cycle reworded: the carve test's pin is 258 under workflow/, 10 excused).
- The full suite on this head: 1,961 passed, 33 skipped.

## Review B round 2 (REJECT) and what this head does with it
- Blocking, taken: project-end.md's survival list names the register (`docs/REQUIREMENTS.md`) for the "Project complete" line's deferred and dropped requirements, and the status file for the deferred increments, not the inventory's Deferred rows; tests/test_phase_modules_close.py pins it. Review A's confirming read APPROVE. The full suite on this head: 1,961 passed, 33 skipped.
