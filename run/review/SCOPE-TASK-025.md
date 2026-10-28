# SCOPE - TASK-025 (PR #98)

TASK-025 - Acceptance: reads-only, classification, and full trace. Author: supervisor (tests); no builder run, no program or governance text changed. Satisfies R-029 (Evidence extended), R-030 (built) and R-031's first half (the classification on the committed fixtures; its calibrations are TASK-027's, which also satisfies R-031, so the row stays planned).

## Scope (docs/BUILD_PLAN.md, TASK-025, quoted)
tests/test_reads_only_applicable.py; tests/test_running_projects_classify.py; tests/test_trace_full_split.py

## Done when (docs/BUILD_PLAN.md, TASK-025, quoted)
`test_reads_only_applicable.py` (names R-030) walks a sample project intake→configuration and asserts only the core + current phase module + its own conditionals are named for reading; `test_running_projects_classify.py` (names R-031) asserts the bridge, reAngle, the video factory, and the TDP each classify per §6.3 on the committed fixtures (TASK-019–021) with `workflow-check` green; `test_trace_full_split.py` (names R-029) asserts `trace-check` green over the finished split (nothing dropped across all modules and traits, no passage in two homes).

## Out of scope
- Every program and every governance text: session-start.py, trace-check.py, workflow-check.py, conformance-check.py, the open list, the registry, the modules and the core are unchanged; the tests read them.
- TASK-026 and TASK-027 (stage B6: the release-level review, the stamp, the install and the calibrations of the running projects). Design for those increments is not this diff's defect.

## The readings taken (docs/INVENTORY.md, Decisions, "TASK-025's settled points")
- §6.3's classifications are read from INVENTORY's "Decision 6 confirmed" row; the Restructuring Plan lies outside the Workspace.
- "Reads only" (R-030) is what the session-start hook names for reading after a compaction (rule 28): the core is its digest part; R-030's layers are the workflow files (phase modules, their sub-files and variants, type, sub-type and trait files); every other file it lists must be a reference text at the bridge's top folder (`and <file>, whole`), the same as for an unclassified project at that phase.
- The expected files are computed from the texts, never from the hook: WALK transcribed from the core's "The phase modules" table (each module checked to stand in it), the modules' `Sub-files:` and `Variants:` lines, the registry's declaring modules, the open list, each conditional file's change headings outside fences.
- The samples: one per written type and sub-type with the open list's default traits (the type-only web app names Personal data, unwritten, with no file), and a local web app with every written trait; the walk ends at configuration, as R-030 says.
- `none` in a `Workflows:` line's traits is the grammar's word for no traits.
- The trace test skips where the baseline commit 0a186da is absent (CI's depth-1 checkout), as tests/test_core_carve.py's trace test does.

## Tests the supervisor wrote, and the paragraph each enforces
Each file's docstring names its requirement and quotes TASK-025's Done when.

tests/test_trace_full_split.py (R-029):
  - test_r029_the_check_is_green_with_nothing_dropped: trace-check exits 0 with RESULT: OK and no FAIL line of any kind (dropped, copy, new, ref, cite), over the baseline the repository pins, and reports 0 dropped.
  - test_r029_every_passage_has_one_home_or_its_reword: Each of the baseline's passages is mapped once, to exactly one current home or to `-`; the core's count, the workflow's count and the excused count add up to all passages, and each excused passage is a `reword` NOTE.
  - test_r029_the_excused_passages_are_exactly_the_recorded_rewords: A `reword` entry excuses every passage under its section, so a passage dropped there is reported excused, not dropped (the trace check's section-wide entries, docs/INVENTORY.md, Decisions); "nothing dropped" holds only because the excused passages are exactly the ones each increment recorded with its reword, the list tests/test_core_carve.py pins. A passage dropped under a reworded section adds a NOTE line and fails here.
  - test_r029_the_homes_are_the_core_the_modules_and_the_moved_traits: Every home is the core, a phase module (its file, a sub-file or a variant), or one of the four trait files TASK-017 moved passages into; every module of the registry holds moved passages, and so does each of those four; no type workflow, no other trait and no table (the open list, the registry) is a home.

tests/test_reads_only_applicable.py (R-030):
  - test_r030_walk_modules_stand_in_the_cores_table: WALK's modules are the core's table's (a transcription, checked here so a change to the table is seen).
  - test_r030_the_samples_cover_every_written_type_and_sub_type: The walk's projects are one per written type and sub-type, and every written trait file belongs to one of them, so each conditional workflow the bridge ships is walked.
  - test_r030_before_classification_intake_names_its_module_alone: A new project at intake, its parts not yet classified, is told to read the intake module and no conditional workflow.
  - test_r030_each_phase_from_intake_to_configuration_names_only_its_modules_and_own_conditionals: For each phase of the walk the hook names exactly the phase's module files and, after them, the project's own conditional workflows that change that phase, in the order additions apply in: no other phase's module and no other type's, sub-type's or trait's file; every other file it names is a reference text, the same as for an unclassified project at that phase. Over the walk each of the project's own files that changes one of these phases is named at its phase.
  - test_r030_the_other_part_is_the_core_and_names_no_workflow_file: The hook's other part re-injects the core's digest, the core a session reads in every phase, and names no module or conditional workflow file.

tests/test_running_projects_classify.py (R-031):
  - test_r031_the_decision_names_all_four_projects: The record of §6.3's classifications covers the four projects R-031 names, two of them in one entry.
  - test_r031_each_project_is_classified_as_section_6_3_decided: The fixture's `Workflows:` line names, by the open list's workflow names, the type and sub-type §6.3 gave the project; both are written, the sub-type is of that type, every trait named is written and in the open list's order, and the sub-type's default traits are among them (proposed at intake, settled at the design gate).
  - test_r031_the_workflow_check_passes_each_fixture: workflow-check.py --status on the fixture prints RESULT: OK alone: no FAIL (a part whose type or sub-type is not written pauses the project) and no FLAG (an unwritten trait).
  - test_r031_calibration_grades_each_fixture_with_nothing_to_pause_or_note: The conformance check's calibration grades of the fixture's `Workflows:` line, which calibration step 1b reads: OK, with no NOTE (no unwritten trait, no part left unclassified past intake), so the project calibrates onto the new structure and resumes without pausing (calibrate-bridge.md step 4b).
  - test_r031_the_bridges_own_status_file_carries_its_fixtures_line: The bridge is classified by running the release: its own status file's `Workflows:` line is the fixture's.

## The checkpoint run, and the mutation driver that stands in for it
The increment adds tests only, over behaviour TASK-009 to TASK-034 built: its checkpoint, origin/main e3978d2, is the code under test, so every test passes there by design and a checkpoint run proves nothing either way. A hand mutation driver stands in (run/supervisor/task025_mutants.py, gitignored; each mutant in a `git clone --shared` of the Workspace in the system temporary folder with the working tree copied over it, never the Workspace; one named test per mutant, which passes unmutated): 28 of 28 mutants killed. Each plants one error in what the tests read, never in the tests: the fixtures (another sub-type, traits out of order, a default trait dropped), the Decision 6 row (an entry dropped, another sub-type), the open list (a sub-type of another type, a sub-type or a trait unwritten), the calibration grades (a NOTE added), the bridge's own status line, the hook (every own file named whatever it touches, the traits reversed, the variants dropped, the sub-type dropped, the mockups phase's module, intake naming design, the digest naming a module, every open-list trait named, a reference text added by trait, a core line range listed), a shipped trait file no sample walks, and the trace (a moved passage dropped, a passage in two homes, a moved passage in a type file, a module's text moved whole into another, the map's excused passages shown as the core's, a sentence cut under a heading no reword names). The first run killed 26 of 27: the moved passage dropped from installable.md survived the green test, the core's TASK-034 `reword` under its baseline heading excusing it (51 excused, RESULT: OK; the trace check's section-wide entries, INVENTORY, Decisions); the trace test now also asserts that the excused passages are exactly the ones tests/test_core_carve.py records, which kills it.

## Review A
- Round 1: APPROVE, 0 Blocking, 2 Should fix (the `none` traits read as a trait name, so one mutant was killed for the wrong reason; the other listed lines left unasserted, against the settled point), 4 Consider (the digest checked whole; WALK checked against the core's table; five mutants for clauses with none; the reason given for the trace's module clause). All taken.
- Confirming read: APPROVE, 0 Blocking, 0 Should fix, 2 Consider: a mutant moving a module whole into another taken (module-moved-into-another, killed); WALK's phase-to-row pairing recorded in docs/HARDENING.md, "TASK-025".
- Read of the driver's finding and its fix (the excused-list test, the retargeted and the new mutant): APPROVE, 0 Blocking, 0 Should fix, 0 new Consider.
- secret-sentinel: see the commit message.

## Checks run on the branch
- trace-check --map: TRACED: 424 passages of baseline 0a186da; 143 in supervisor.md, 231 under workflow/, 0 dropped, 50 excused; RESULT: OK.
- The full suite on the branch's final text: 3195 passed, 39 skipped, none failed (23 min); a first run, on the first text of the tests and records, 3193 passed, 39 skipped, none failed.
- inventory-check, completion-check --mode plan, plan-check: OK.

## Expected files
- The three test files.
- The records: docs/REQUIREMENTS.md (R-029's Evidence, R-030 built, R-031's Evidence), docs/INVENTORY.md (the Features row "Release B's acceptance tests"; the Decisions row "TASK-025's settled points"), docs/HARDENING.md ("TASK-025"), docs/PROJECT_STATUS.md (as at this pull request's merge, ISS-009), docs/archive/STATUS_HISTORY.md (Last accepted's older part, in a commit of its own), project.json.
- docs/ROSTER.resolved.json, the roster stamp before Review B (bookkeeping), if it changed.
- run/review/, the review files.
