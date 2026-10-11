# Build plan — Claude-Cursor Bridge, Release B

The design is the Restructuring Plan's release B (§16) and the sections it rests on (§6, §15). This plan decomposes that scope into increments. Per §15 condition 3, **governance text is design: the supervisor authors it, and it is gated by the two-critic design review; programs are implementation: the builder writes them, gated by the delegation loop.** Each increment's author is marked. Status is derived from `origin/main` by `plan-check.py`, never written here.

## Prior-project lessons

The overlapping "prior project" is the bridge itself; its lessons are in `~/.claude/cursor-bridge/Known-Pitfalls.md` and the three projects' Issues files.

**Extracted.**
- **KP-035 — after a compaction, the supervisor must re-read what the hook names.** This is release B's reason for existing: the re-read today is a section of up to 540 lines inside one 170,000-character file. Becomes an acceptance criterion on TASK-010/011/012 (each phase module is sized to be read whole) and TASK-013 (the hook names exactly one module).
- **The compaction digest is at its character limit (≈9,500).** A hard constraint: TASK-009 (the core carve) must keep the digest within the limit the `test_session_start` check enforces, paying for any new line with a trim.
- **§6.5 / R11 — today's interface conditions stay together.** The mockup variant is an *addition* under the trait *has screens*, never a replacement that would leave the design auditor and the merge-gate detector with nothing to judge against. Becomes an acceptance criterion on TASK-010 (interface phase) and TASK-015 (the *has screens* trait).
- **KP-029 — a surface that exists only as a picture went unbuilt.** Becomes an acceptance criterion on TASK-007 (the workflow check fails a `Workflows:` line naming an unwritten type) and TASK-004 (the open list marks each entry written or not).

**Judged irrelevant.** The asset-loop, Roblox, and product-aggregate pitfalls (releases E/F) — those workflows are not written in release B. The code-map pitfalls (releases C/D) — out of scope.

---

## Stage B1 — Supervised-project bootstrap
Demonstration: the bridge's CI runs its full gate — tests, the windowless check, the manifest check, and the security floor — green on a pull request, and a fresh session resumes release B from `docs/PROJECT_STATUS.md` and `docs/INVENTORY.md` alone.

### TASK-001 — Intake and configuration records
Author: supervisor (records; §15 condition 3).
Parent: none
Depends on: none
Parallel: no
Diagrams: none
Scope: project.json; docs/PROJECT_STATUS.md; docs/REQUIREMENTS.md; docs/INVENTORY.md; docs/RUN_PARAMETERS.md; docs/ROSTER.json; docs/ROSTER.resolved.json; docs/BUILD_PLAN.md; tests/test_release_b_bootstrap.py
Satisfies: R-001

### TASK-002 — The security floor in the bridge's CI
Author: builder.
Parent: none
Depends on: TASK-001
Parallel: no
Diagrams: none
Scope: .github/workflows/tests.yml; .semgrep.yml; osv-scanner.toml; socket.yml; tests/test_release_b_ci_floor.py
Satisfies: R-002

## Stage B2 — The conditional-workflow framework
Demonstration: `workflow-check.py` passes on the open list and a sample set of conditional workflows, and exits non-zero when an extension point is renamed, when a trait tries to replace a phase, and when a project's `Workflows:` line names a type whose workflow is not written.

### TASK-003 — The conditional-workflow model in the core
Author: supervisor.
Parent: none
Depends on: TASK-001
Parallel: no
Diagrams: none
Scope: bridge/commands/supervisor.md; tests/test_workflow_model.py
Satisfies: R-007, R-008, R-009, R-010

### TASK-004 — The open list and the interface-phase variants
Author: supervisor.
Parent: none
Depends on: TASK-003
Parallel: no
Diagrams: none
Scope: bridge/cursor-bridge/workflow/open-list.md; bridge/cursor-bridge/MANIFEST.json; tests/test_open_list.py
Satisfies: R-011, R-012

### TASK-005 — The extension-point registry
Author: supervisor.
Parent: none
Depends on: TASK-003
Parallel: no
Diagrams: none
Scope: bridge/cursor-bridge/workflow/extension-points.md; bridge/cursor-bridge/MANIFEST.json; tests/test_extension_points.py
Satisfies: R-006

### TASK-006 — When a part does not fit: pause and flag
Author: supervisor.
Parent: none
Depends on: TASK-004
Parallel: no
Diagrams: none
Scope: bridge/commands/supervisor.md; bridge/cursor-bridge/workflow/open-list.md; tests/test_unfit_part.py
Satisfies: R-013

### TASK-007 — The workflow check
Author: builder.
Parent: none
Depends on: TASK-004, TASK-005
Parallel: no
Diagrams: none
Scope: bridge/cursor-bridge/workflow-check.py; bridge/cursor-bridge/MANIFEST.json; tests/test_workflow_check.py
Satisfies: R-014

### TASK-008 — The Workflows status line
Author: builder.
Parent: none
Depends on: TASK-005
Parallel: no
Diagrams: none
Scope: bridge/cursor-bridge/inventory-check.py; bridge/cursor-bridge/conformance-check.py; bridge/commands/supervisor.md; tests/test_workflows_line.py
Satisfies: R-015

## Stage B3 — The core and phase-module split
Demonstration: after a simulated compaction the session-start hook names exactly one phase module to re-read, and the traceability comparison shows every standing rule and every conditional passage mapped from the monolithic instructions to its new file with nothing dropped.

### TASK-009 — Carve the main-workflow core
Author: supervisor.
Parent: none
Depends on: TASK-003, TASK-005
Parallel: no
Diagrams: none
Scope: bridge/commands/supervisor.md; bridge/cursor-bridge/bridge-install.py; bridge/cursor-bridge/MANIFEST.json; tests/test_core_carve.py
Satisfies: R-003

### TASK-010 — Phase modules: intake, design, interface, planning
Author: supervisor.
Parent: none
Depends on: TASK-009
Parallel: no
Diagrams: none
Scope: bridge/cursor-bridge/workflow/phases/intake.md; bridge/cursor-bridge/workflow/phases/design.md; bridge/cursor-bridge/workflow/phases/interface.md; bridge/cursor-bridge/workflow/phases/planning.md; bridge/cursor-bridge/MANIFEST.json; tests/test_phase_modules_1.py
Satisfies: R-004, R-006

### TASK-011 — Phase modules: run parameters, configuration, the delegation loop
Author: supervisor.
Parent: none
Depends on: TASK-009
Parallel: no
Diagrams: none
Scope: bridge/cursor-bridge/workflow/phases/run-parameters.md; bridge/cursor-bridge/workflow/phases/configuration.md; bridge/cursor-bridge/workflow/phases/delegation-loop.md; bridge/cursor-bridge/MANIFEST.json; tests/test_phase_modules_2.py
Satisfies: R-004, R-006

### TASK-012 — Phase modules: change cycle, reflection points, project end
Author: supervisor.
Parent: none
Depends on: TASK-009
Parallel: no
Diagrams: none
Scope: bridge/cursor-bridge/workflow/phases/change-cycle.md; bridge/cursor-bridge/workflow/phases/reflection.md; bridge/cursor-bridge/workflow/phases/project-end.md; bridge/cursor-bridge/MANIFEST.json; tests/test_phase_modules_3.py
Satisfies: R-004, R-006

### TASK-013 — The compaction hook names the phase module
Author: builder.
Parent: none
Depends on: TASK-010, TASK-011, TASK-012
Parallel: no
Diagrams: none
Scope: bridge/cursor-bridge/session-start.py; tests/test_session_start_module.py
Satisfies: R-005

### TASK-014 — The traceability comparison
Author: builder.
Parent: none
Depends on: TASK-010, TASK-011, TASK-012
Parallel: no
Diagrams: none
Scope: bridge/cursor-bridge/trace-check.py; bridge/cursor-bridge/MANIFEST.json; tests/test_trace_check.py
Satisfies: R-029

## Stage B4 — The first conditional workflows
Demonstration: the bridge, reAngle, the video factory, and the TDP are each classified per §6.3; `workflow-check.py` passes on all four; and a mock new project of a product type whose workflow is not written pauses at intake.

### TASK-015 — Trait files: has screens, installable, performance budgets, external services
Author: supervisor.
Parent: none
Depends on: TASK-007
Parallel: no
Diagrams: none
Scope: bridge/cursor-bridge/workflow/traits/has-screens.md; bridge/cursor-bridge/workflow/traits/installable.md; bridge/cursor-bridge/workflow/traits/performance-budgets.md; bridge/cursor-bridge/workflow/traits/external-services.md; bridge/cursor-bridge/MANIFEST.json; tests/test_traits_existing.py
Satisfies: R-016, R-017, R-018, R-019

### TASK-016 — Trait files: spends money, long-running process, AI models
Author: supervisor.
Parent: none
Depends on: TASK-007
Parallel: no
Diagrams: none
Scope: bridge/cursor-bridge/workflow/traits/spends-money.md; bridge/cursor-bridge/workflow/traits/long-running-process.md; bridge/cursor-bridge/workflow/traits/ai-models.md; bridge/cursor-bridge/MANIFEST.json; tests/test_traits_new.py
Satisfies: R-020, R-021, R-022

### TASK-017 — Type workflow: web app and local web app
Author: supervisor.
Parent: none
Depends on: TASK-007
Parallel: no
Diagrams: none
Scope: bridge/cursor-bridge/workflow/types/web-app.md; bridge/cursor-bridge/workflow/types/web-app/local-web-app.md; bridge/cursor-bridge/MANIFEST.json; tests/test_type_web_app.py
Satisfies: R-023

### TASK-018 — Type workflow: software on your own computer and local service
Author: supervisor.
Parent: none
Depends on: TASK-007
Parallel: no
Diagrams: none
Scope: bridge/cursor-bridge/workflow/types/own-computer.md; bridge/cursor-bridge/workflow/types/own-computer/local-service.md; bridge/cursor-bridge/MANIFEST.json; tests/test_type_own_computer.py
Satisfies: R-024

### TASK-019 — Type workflow: host extension and Claude Code extension
Author: supervisor.
Parent: none
Depends on: TASK-007
Parallel: no
Diagrams: none
Scope: bridge/cursor-bridge/workflow/types/host-extension.md; bridge/cursor-bridge/workflow/types/host-extension/claude-code-extension.md; bridge/cursor-bridge/MANIFEST.json; tests/test_type_host_extension.py
Satisfies: R-025

### TASK-020 — Interface text: contract design and command design
Author: supervisor.
Parent: none
Depends on: TASK-018
Parallel: no
Diagrams: none
Scope: bridge/cursor-bridge/workflow/interface/contract-design.md; bridge/cursor-bridge/workflow/interface/command-design.md; bridge/cursor-bridge/MANIFEST.json; tests/test_interface_text.py
Satisfies: R-026

## Stage B5 — Calibration, glossary, and acceptance
Demonstration: a fresh session walked from intake to configuration reads only its core, its current phase module, and its own conditional workflows; and the bridge, reAngle, the video factory, and the TDP each calibrate onto the new structure without pausing and without reopening a gate (a mechanical dry-run).

### TASK-021 — Calibration aware of conditional workflows
Author: builder.
Parent: none
Depends on: TASK-015, TASK-016, TASK-017, TASK-018, TASK-019
Parallel: no
Diagrams: none
Scope: bridge/commands/calibrate-bridge.md; bridge/cursor-bridge/conformance-check.py; tests/test_calibration_workflows.py
Satisfies: R-027

### TASK-022 — The glossary gains the plan's terms
Author: supervisor.
Parent: none
Depends on: TASK-003
Parallel: no
Diagrams: none
Scope: bridge/cursor-bridge/Glossary.md; tests/test_glossary_terms.py
Satisfies: R-028

### TASK-023 — Acceptance: reads-only and running-project classification
Author: supervisor (tests).
Parent: none
Depends on: TASK-021, TASK-022
Parallel: no
Diagrams: none
Scope: tests/test_reads_only_applicable.py; tests/test_running_projects_classify.py
Satisfies: R-030, R-031
