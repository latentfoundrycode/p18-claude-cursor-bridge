# Build plan — Claude-Cursor Bridge, Release B

The design is the Restructuring Plan's release B (§16) and the sections it rests on (§6, §15). This plan decomposes that scope into increments. Per §15 condition 3, **governance text is design: the supervisor authors it, gated by the two-critic design review; programs are implementation: the builder writes them, gated by the delegation loop.** Each increment marks its author. Status is derived from `origin/main` by `plan-check.py`, never written here. Revised 2026-10-11 after the two-critic review (round 1).

## Standing constraints (every increment)
- **Manifest:** any increment that adds, moves, or removes a file under `bridge/` regenerates `bridge/cursor-bridge/MANIFEST.json` (`python tools/make-manifest.py`) in the same commit; `MANIFEST.json` is named in its Scope. CI (`bridge-check --sources`) fails a mismatch.
- **Tests name the requirement:** each increment's test contains the literal `R-nnn` of every requirement it satisfies, so `completion-check --mode done` can see it. For a governance-text increment the test is structural (the file exists at its §6.11 path, opens with the compaction-survival list where applicable, declares its extension points by the registry's names, is within the size bound, and `workflow-check.py` exits 0 on it).
- **Verbatim moves:** text moved in the split is moved verbatim; any reword is a listed exception in the trace-check's exceptions file, seen by the design review.
- **No hard line wraps** in any authored Markdown (rule 30).

## Prior-project lessons
The overlapping "prior project" is the bridge itself; its lessons are in `~/.claude/cursor-bridge/Known-Pitfalls.md` and the three projects' Issues files.

**Extracted (each attached to an increment's `Done when:`).**
- **KP-035 — after a compaction the supervisor re-reads what the hook names.** → TASK-010 (digest within its limit), TASK-011/012/013/014 (each module read-whole), TASK-015 (the hook names one module + the conditional files).
- **The compaction digest is at its character limit (≈9,500).** → TASK-010 `Done when:` keeps `test_session_start.py`'s digest-length assertion green.
- **§6.5 / R11 — today's interface conditions stay together.** → TASK-012 and TASK-017 (the mockup variant is an *addition* under *has screens*, and `interface.md` still holds the variant).
- **KP-029 — a surface that exists only as a picture went unbuilt.** → TASK-006 (workflow-check fails a `Workflows:` line naming an unwritten type) and TASK-004 (the open list's written/unwritten column).

**Judged irrelevant.** The asset-loop, Roblox, and product-aggregate pitfalls (releases E/F); the code-map pitfalls (releases C/D) — out of release B's scope.

---

## Stage B1 — Supervised-project bootstrap
Demonstration: the bridge's CI runs its full gate — tests, the windowless check, the manifest check, and the security floor — green on a pull request, and a fresh session resumes release B from `docs/PROJECT_STATUS.md` and `docs/INVENTORY.md` alone.

### TASK-001 — Intake and configuration records
Author: supervisor (records; §15 condition 3).
Parent: none
Depends on: none
Parallel: no
Diagrams: none
Scope: project.json; docs/PROJECT_STATUS.md; docs/REQUIREMENTS.md; docs/INVENTORY.md; docs/RUN_PARAMETERS.md; docs/ROSTER.json; docs/ROSTER.resolved.json; docs/BUILD_PLAN.md; docs/DESIGN_CRITIQUE.md; tests/test_release_b_bootstrap.py
Satisfies: R-001
Done when: `plan-check.py`, `completion-check.py --mode plan`, `inventory-check.py`, and `roster-check.py` all pass; `project.json` is valid JSON with name/purpose/kind/version/state; `test_release_b_bootstrap.py` (names R-001) asserts the records exist and `project.json` parses; the baseline-measurement precondition is recorded as met in INVENTORY.

### TASK-002 — The security floor in the bridge's CI
Author: builder.
Parent: none
Depends on: TASK-001
Parallel: no
Diagrams: none
Scope: .github/workflows/tests.yml; .semgrep.yml; osv-scanner.toml; socket.yml; requirements.lock; tests/test_release_b_ci_floor.py
Satisfies: R-002
Done when: CI installs from `requirements.lock`; a `gate` adds Semgrep (ubuntu authoritative), OSV-Scanner, and Socket, every action pinned by commit SHA; OSV/Socket find the lockfile and do not exit 128 "no packages"; `test_release_b_ci_floor.py` (names R-002) asserts the three scanners run and every action is SHA-pinned; the workflow is green on this PR.

## Stage B2 — The conditional-workflow framework
Demonstration: `workflow-check.py` passes on the open list and a sample set of conditional workflows, and exits non-zero when an extension point is renamed, when a trait tries to replace a phase, and when a project's `Workflows:` line names a type whose workflow is not written.

### TASK-003 — The conditional-workflow model in the core
Author: supervisor.
Parent: none
Depends on: TASK-001
Parallel: no
Diagrams: none
Scope: bridge/commands/supervisor.md; bridge/cursor-bridge/MANIFEST.json; tests/test_workflow_model.py
Satisfies: R-007, R-008, R-009, R-034
Done when: the core describes the five layers, inheritance, read-when, replace/set/add with "only type/sub-workflows may replace or set; trait additions only add", the founding-rule/merge-gate/register floor, and the stated order in which several traits' additions compose; `test_workflow_model.py` (names R-007, R-008, R-009, R-034) asserts those statements are present and the digest stays within its limit.

### TASK-004 — The open list
Author: supervisor.
Parent: none
Depends on: TASK-003
Parallel: no
Diagrams: none
Scope: bridge/cursor-bridge/workflow/open-list.md; bridge/cursor-bridge/MANIFEST.json; tests/test_open_list.py
Satisfies: R-011
Done when: every product type, sub-type, and trait of §6.3 is listed with its definition and a written/unwritten column; the §6.10 add/change procedure is recorded; `test_open_list.py` (names R-011) asserts each §6.3 entry is present with a written-flag and the file parses in the shape `workflow-check.py` reads.

### TASK-005 — The extension-point registry
Author: supervisor.
Parent: none
Depends on: TASK-003
Parallel: no
Diagrams: none
Scope: bridge/cursor-bridge/workflow/extension-points.md; bridge/cursor-bridge/MANIFEST.json; tests/test_extension_points.py
Satisfies: R-006
Done when: the registry lists the §6.4 initial points per phase, including Definition of done and Delivery, each naming the module that declares it; `test_extension_points.py` (names R-006) asserts every §6.4 point is present and each names a declaring module.

### TASK-006 — The workflow check
Author: builder.
Parent: none
Depends on: TASK-004, TASK-005
Parallel: no
Diagrams: none
Scope: bridge/cursor-bridge/workflow-check.py; .github/workflows/tests.yml; bridge/cursor-bridge/MANIFEST.json; tests/test_workflow_check.py
Satisfies: R-014, R-033
Done when: `workflow-check.py` passes on the open list + a sample conditional set and exits non-zero on (a) a change to a non-existent extension point, (b) a trait that replaces or sets, (c) a replace on a non-replaceable phase, (d) a sub-workflow naming a missing type, (e) a `Workflows:` line naming an unwritten type; it runs in CI; `test_workflow_check.py` (names R-014, R-033) covers each case and asserts the CI step exists.

### TASK-007 — The Workflows status line: template and semantics
Author: supervisor.
Parent: none
Depends on: TASK-003
Parallel: no
Diagrams: none
Scope: bridge/commands/supervisor.md; bridge/cursor-bridge/MANIFEST.json; tests/test_workflows_line_text.py
Satisfies: R-015
Done when: the status template carries a `Workflows:` line per part (product type → sub-type; traits) beside `Phase:`, with its grammar defined; `test_workflows_line_text.py` (names R-015) asserts the template and its description are present.

### TASK-008 — The Workflows status line: enforced
Author: builder.
Parent: none
Depends on: TASK-007
Parallel: no
Diagrams: none
Scope: bridge/cursor-bridge/inventory-check.py; bridge/cursor-bridge/conformance-check.py; tests/test_workflows_line_check.py
Satisfies: R-015
Done when: `inventory-check.py`/`conformance-check.py` read the `Workflows:` line and report a malformed or missing one; `test_workflows_line_check.py` (names R-015) covers a valid line, a missing one, and a malformed one.

### TASK-009 — The glossary gains the plan's terms
Author: supervisor.
Parent: none
Depends on: TASK-003
Parallel: no
Diagrams: none
Scope: bridge/cursor-bridge/Glossary.md; bridge/cursor-bridge/MANIFEST.json; tests/test_glossary_terms.py
Satisfies: R-028
Done when: the glossary defines conditional workflow, type workflow, sub-workflow, trait, extension point, phase module, product type, sub-type, and the other terms this plan introduces; `test_glossary_terms.py` (names R-028) asserts each term has a definition.

## Stage B3 — The core and phase-module split
Demonstration: after a simulated compaction the session-start hook names exactly one phase module (plus the current phase's conditional files) to re-read, and the traceability comparison shows every standing rule and every conditional passage mapped from the pinned pre-split baseline to its new file with nothing dropped.

### TASK-010 — Carve the main-workflow core
Author: supervisor.
Parent: none
Depends on: TASK-003, TASK-005
Parallel: no
Diagrams: none
Scope: bridge/commands/supervisor.md; bridge/cursor-bridge/MANIFEST.json; tests/test_core_carve.py; tests/test_session_start.py; tests/test_text_consistency.py
Satisfies: R-003, R-032
Done when: the core holds only the roles/division of labour, founding rules, loop shape, escalation/reporting, project state, and the standing rules that hold in every phase, and points at the phase modules; the compaction digest stays within the limit `test_session_start.py` enforces; a proof test shows `workflow/**` installs from the regenerated manifest with no `bridge-install.py` change (if it cannot, a builder increment is added); the structure-pinning tests are re-pointed to the carved core, never deleted; `test_core_carve.py` (names R-003, R-032) asserts the core's section set and that no phase procedure remains in it.

### TASK-011 — Phase modules: intake, design
Author: supervisor.
Parent: none
Depends on: TASK-010
Parallel: no
Diagrams: none
Scope: bridge/cursor-bridge/workflow/phases/intake.md; bridge/cursor-bridge/workflow/phases/design.md; bridge/cursor-bridge/MANIFEST.json; tests/test_phase_modules_intake_design.py
Satisfies: R-004, R-006, R-013, R-036
Done when: each module opens with its compaction-survival list and declares its extension points by the registry's names; intake.md carries the pause for an unfit/unwritten product type (R-013); design.md carries the new-trait flag, the owner's pause option, and the promotion-pass route (R-036); each module is within the size bound; `trace-check` passes for the sections moved so far; `test_phase_modules_intake_design.py` (names R-004, R-006, R-013, R-036) asserts the structure and the pause/flag text.

### TASK-012 — Phase modules: interface, planning
Author: supervisor.
Parent: none
Depends on: TASK-010
Parallel: no
Diagrams: none
Scope: bridge/cursor-bridge/workflow/phases/interface.md; bridge/cursor-bridge/workflow/phases/interface/mockups.md; bridge/cursor-bridge/workflow/phases/interface/command-design.md; bridge/cursor-bridge/workflow/phases/interface/contract-design.md; bridge/cursor-bridge/workflow/phases/interface/playable-prototype.md; bridge/cursor-bridge/workflow/phases/planning.md; bridge/cursor-bridge/MANIFEST.json; tests/test_phase_modules_interface_planning.py
Satisfies: R-004, R-006, R-010, R-012, R-032, R-035
Done when: interface.md declares all four variants once, each variant's text in its own file; the mockup variant is an addition that keeps the frozen interface rules, the design auditor, and the running-interface tests together (R-010); design/intake carries that traits are proposed at intake and settled at the design gate (R-035); each module within the size bound; `test_phase_modules_interface_planning.py` (names R-004, R-006, R-010, R-012, R-032, R-035) asserts the four variants exist and the mockup variant is declared as an addition.

### TASK-013 — Phase modules: run parameters, configuration, the delegation loop
Author: supervisor.
Parent: none
Depends on: TASK-010
Parallel: no
Diagrams: none
Scope: bridge/cursor-bridge/workflow/phases/run-parameters.md; bridge/cursor-bridge/workflow/phases/configuration.md; bridge/cursor-bridge/workflow/phases/delegation-loop.md; bridge/cursor-bridge/MANIFEST.json; tests/test_phase_modules_build.py
Satisfies: R-004, R-006, R-032
Done when: each module opens with its compaction-survival list, declares its extension points, is within the size bound, and `trace-check` passes for its moved sections; `test_phase_modules_build.py` (names R-004, R-006, R-032) asserts the structure.

### TASK-014 — Phase modules: change cycle, reflection points, project end
Author: supervisor.
Parent: none
Depends on: TASK-010
Parallel: no
Diagrams: none
Scope: bridge/cursor-bridge/workflow/phases/change-cycle.md; bridge/cursor-bridge/workflow/phases/reflection.md; bridge/cursor-bridge/workflow/phases/project-end.md; bridge/cursor-bridge/MANIFEST.json; tests/test_phase_modules_close.py
Satisfies: R-004, R-006, R-032
Done when: each module opens with its compaction-survival list, declares its extension points (reflection/project-end declare Definition of done and Delivery), is within the size bound, and `trace-check` passes for its moved sections; `test_phase_modules_close.py` (names R-004, R-006, R-032) asserts the structure.

### TASK-015 — The compaction hook names the phase module
Author: builder.
Parent: none
Depends on: TASK-011, TASK-012, TASK-013, TASK-014, TASK-007
Parallel: no
Diagrams: none
Scope: bridge/cursor-bridge/session-start.py; tests/test_session_start_module.py
Satisfies: R-005
Done when: given a project's `Phase:` and `Workflows:` lines the hook re-injects the digest and names exactly one phase module plus the conditional files (type/sub-type/trait) touching that phase, within the 10,000-char cap; it carries the full Phase→module table (including reflection/project-end and the renamed phases) and the further files a phase re-reads; `test_session_start_module.py` (names R-005) covers a phase with and without conditionals and the reflection/stage-close case.

### TASK-016 — The traceability comparison
Author: builder.
Parent: none
Depends on: TASK-010
Parallel: no
Diagrams: none
Scope: bridge/cursor-bridge/trace-check.py; bridge/cursor-bridge/workflow/trace-exceptions.md; bridge/cursor-bridge/MANIFEST.json; tests/test_trace_check.py
Satisfies: R-029
Done when: `trace-check.py` reads a pinned pre-split baseline commit, maps every standing rule and conditional passage (the project-layout/Workspace-boundary section included) to its new file, requires verbatim moves except entries listed in `trace-exceptions.md`, flags text new to the modules unless its increment declared it, and checks every `~/.claude/...` reference and cited section still resolves; it runs incrementally (passes for the sections moved so far); `test_trace_check.py` (names R-029) covers a clean move, a silently reworded rule (fails), a dropped boundary section (fails), and a dangling reference (fails).

## Stage B4 — The first conditional workflows
Demonstration: the bridge, reAngle, the video factory, and the TDP are each classified per §6.3 on committed fixtures; `workflow-check.py` passes on all four; and a mock new project of a product type whose workflow is not written pauses at intake.

### TASK-017 — Trait files: has screens, installable, performance budgets, external services
Author: supervisor.
Parent: none
Depends on: TASK-012, TASK-006
Parallel: no
Diagrams: none
Scope: bridge/cursor-bridge/workflow/traits/has-screens.md; bridge/cursor-bridge/workflow/traits/installable.md; bridge/cursor-bridge/workflow/traits/performance-budgets.md; bridge/cursor-bridge/workflow/traits/external-services.md; bridge/cursor-bridge/MANIFEST.json; tests/test_traits_existing.py
Satisfies: R-010, R-016, R-017, R-018, R-019
Done when: each trait adds (never replaces) at declared extension points; *has screens* activates the mockup variant and adds the frozen interface rules, the design auditor, and the running-interface tests; *external services* carries contract capture, replay, and the deployed-layout/bounded-remote-wait checks; `workflow-check.py` passes on all four; `test_traits_existing.py` (names R-010, R-016–R-019) asserts each file adds-only and names its gathered conditions.

### TASK-018 — Trait files: spends money, long-running process, AI models
Author: supervisor.
Parent: none
Depends on: TASK-005, TASK-006
Parallel: no
Diagrams: none
Scope: bridge/cursor-bridge/workflow/traits/spends-money.md; bridge/cursor-bridge/workflow/traits/long-running-process.md; bridge/cursor-bridge/workflow/traits/ai-models.md; bridge/cursor-bridge/MANIFEST.json; tests/test_traits_new.py
Satisfies: R-020, R-021, R-022
Done when: *spends money* carries approval-before-paid-action, the worst-case estimate, a cap, and platform+account named; *long-running process* carries start/stop/health, nothing-left-running, and §8.1's conditions; *AI models* carries evaluation sets and thresholds, pinned models, recorded outputs; `workflow-check.py` passes; `test_traits_new.py` (names R-020–R-022) asserts each file adds-only and names its content.

### TASK-019 — Type workflow: web app and local web app
Author: supervisor.
Parent: none
Depends on: TASK-012, TASK-014, TASK-006
Parallel: no
Diagrams: none
Scope: bridge/cursor-bridge/workflow/types/web-app.md; bridge/cursor-bridge/workflow/types/web-app/local-web-app.md; bridge/cursor-bridge/MANIFEST.json; tests/test_type_web_app.py
Satisfies: R-023
Done when: the type sets delivery (deployment) and the sub-type sets it to an installer + a local server to start/stop; replace/set appear only here; `workflow-check.py` passes and classifies reAngle and the video factory without pausing; `test_type_web_app.py` (names R-023) asserts the set/replace points and the sub-type inheritance.

### TASK-020 — Type workflow: software on your own computer and local service
Author: supervisor.
Parent: none
Depends on: TASK-012, TASK-013, TASK-014, TASK-006
Parallel: no
Diagrams: none
Scope: bridge/cursor-bridge/workflow/types/own-computer.md; bridge/cursor-bridge/workflow/types/own-computer/local-service.md; bridge/cursor-bridge/MANIFEST.json; tests/test_type_own_computer.py
Satisfies: R-024
Done when: the type names its GUI/CLI/pipeline/local-service sub-types; local-service sets the interface variant to contract design; `workflow-check.py` passes and classifies the TDP without pausing; `test_type_own_computer.py` (names R-024) asserts the sub-types and the contract-design setting.

### TASK-021 — Type workflow: host extension and Claude Code extension
Author: supervisor.
Parent: none
Depends on: TASK-013, TASK-014, TASK-006
Parallel: no
Diagrams: none
Scope: bridge/cursor-bridge/workflow/types/host-extension.md; bridge/cursor-bridge/workflow/types/host-extension/claude-code-extension.md; bridge/cursor-bridge/MANIFEST.json; tests/test_type_host_extension.py
Satisfies: R-025
Done when: the type adds the host's behaviour as verified facts with the version checked, tests inside the real host, and delivery as installation into the host; `workflow-check.py` passes and classifies the bridge itself without pausing; `test_type_host_extension.py` (names R-025) asserts those additions.

### TASK-022 — Interface text: contract design and command design
Author: supervisor.
Parent: none
Depends on: TASK-012, TASK-020
Parallel: no
Diagrams: none
Scope: bridge/cursor-bridge/workflow/phases/interface/contract-design.md; bridge/cursor-bridge/workflow/phases/interface/command-design.md; bridge/cursor-bridge/MANIFEST.json; tests/test_interface_text.py
Satisfies: R-026
Done when: contract design covers a protocol's operations/inputs/outputs/errors/versioning as a contract file tests enforce; command design covers commands, help text, and output formats; `test_interface_text.py` (names R-026) asserts both files' required sections. (The variant files are created empty-of-body in TASK-012; this increment fills them.)

## Stage B5 — Calibration and acceptance
Demonstration: a fresh session walked from intake to configuration reads only its core, its current phase module, and its own conditional workflows; and the four projects each classify under §6.3 on fixtures with `workflow-check` green.

### TASK-023 — Calibration aware of conditional workflows (text)
Author: supervisor.
Parent: none
Depends on: TASK-017, TASK-018, TASK-019, TASK-020, TASK-021
Parallel: no
Diagrams: none
Scope: bridge/commands/calibrate-bridge.md; bridge/cursor-bridge/MANIFEST.json; tests/test_calibrate_text.py
Satisfies: R-027
Done when: calibrate-bridge.md applies a conditional workflow to a running project of that type by phase, reopens no gate, and states that new text takes effect from the next design phase or change cycle; `test_calibrate_text.py` (names R-027) asserts those statements.

### TASK-024 — Calibration aware of conditional workflows (program)
Author: builder.
Parent: none
Depends on: TASK-023, TASK-006
Parallel: no
Diagrams: none
Scope: bridge/cursor-bridge/conformance-check.py; tests/test_calibrate_program.py
Satisfies: R-027, R-033
Done when: `conformance-check.py` runs `workflow-check` at calibration and reports a running project whose `Workflows:` line is unclassified or names an unwritten workflow; `test_calibrate_program.py` (names R-027, R-033) covers a classified project and an unclassified one.

### TASK-025 — Acceptance: reads-only and classification fixtures
Author: supervisor (tests).
Parent: none
Depends on: TASK-023, TASK-024, TASK-009
Parallel: no
Diagrams: none
Scope: tests/test_reads_only_applicable.py; tests/test_running_projects_classify.py; tests/fixtures/workflows/
Satisfies: R-030, R-031
Done when: `test_reads_only_applicable.py` (names R-030) walks a sample project intake→configuration and asserts only the core + current phase module + its own conditionals are named for reading; `test_running_projects_classify.py` (names R-031) asserts the bridge, reAngle, the video factory, and the TDP each classify per §6.3 on committed `Workflows:` fixtures with `workflow-check` green.

## Stage B6 — Release and install
Demonstration: release B is reviewed by a fresh context, stamped, installed on this computer with the projects paused, verified against the installed tree, and the trial project (reAngle) calibrates onto the new structure and resumes — then the other projects resume on the owner's word.

### TASK-026 — The release stamp
Author: builder.
Parent: none
Depends on: TASK-025
Parallel: no
Diagrams: none
Scope: bridge/cursor-bridge/VERSION; bridge/cursor-bridge/MANIFEST.json; bridge/cursor-bridge/CHANGELOG.md; tests/test_release_b_stamp.py
Satisfies: R-037
Done when: VERSION is bumped to the release B stamp; MANIFEST regenerated; a CHANGELOG entry names release B with its "if rolled back" notes; `bridge-check.py --sources` is green on the stamped tree; `test_release_b_stamp.py` (names R-037) asserts VERSION/CHANGELOG/manifest agree.

### TASK-027 — Release review, install, and the trial
Author: supervisor / owner (the owner completes the merge and runs the install run sheet).
Parent: none
Depends on: TASK-026
Parallel: no
Diagrams: none
Scope: Reports/Reviews/ (the release-level review record); docs/PROJECT_STATUS.md; docs/INVENTORY.md
Satisfies: R-031, R-037, R-038
Done when: a fresh-context release-level review (one pass, fixes, a second pass) is recorded and its findings closed; the install-while-building mechanics (R-038) are settled by the owner and recorded; the projects are paused; `bridge-install.py` runs and `bridge-check.py` is green on `~/.claude`; reAngle calibrates onto the new structure (its `Workflows:` line valid, no gate reopened) and resumes; field acceptance is met; the video factory and the TDP resume on the owner's word.
