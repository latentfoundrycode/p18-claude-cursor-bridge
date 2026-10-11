# Review B — release B build plan and requirements register (round 1)

You are one of two critics of different makes reading the same committed text in fresh contexts. Read this whole file; do not ask for anything; it contains everything you need. Answer with your findings graded **Blocking** (the plan cannot go to the owner's gate with it), **Should fix** (fix or accept with a reason), or **Consider** (a judgement call), each naming the increment, stage, or requirement it concerns; then the counts per grade; and nothing else. A reply that names nothing specific from the text below is a failed launch, not a verdict.

## What is being built (the design, as context)

The Claude-Cursor Bridge is becoming a **supervised project** so its own supervisor can build **release B** (Restructuring Plan §16). Release B is the largest release in the plan. Its scope (§16, §6):

- The supervisor's single instructions file is split into a **core** (roles, founding rules, loop shape, escalation/reporting, project state, the standing rules that hold in every phase) and **per-phase modules**, each module opening with the short list of what must survive a compaction; the compaction/session-start hook names the one module to re-read (the point: after a compaction the supervisor re-reads one phase-sized file, not a 540-line section of a 170,000-character file).
- A **conditional-workflow** mechanism in three layers — **type workflow** (per product type), **sub-workflow** (per sub-type), **trait additions** (per trait) — each inheriting what it does not mention and read only when it applies. Only type/sub-workflows may *replace* or *set*; trait additions may only *add*; none may remove a founding rule, weaken the merge gate, or skip the register/inventory/reviews. Changes are allowed only at declared **extension points**.
- An **open list** of every product type, sub-type and trait with its definition and whether its workflow is written; a part that fits no type / two equally / an unwritten type **pauses** the project at intake; a new/unwritten trait is **flagged** and work continues.
- A **workflow check** (`workflow-check.py`) verifying all of the above and every project's `Workflows:` status line.
- The **first conditional workflows**: seven trait files (four gathering today's scattered conditions — has screens, installable, performance budgets, external services — and three written new — spends money, long-running process, AI models) and the three type workflows the running projects need (web app / local web app; software on your own computer / local service; host extension / Claude Code extension), plus new interface text (contract design, command design).
- **Calibration** aware of conditional workflows; the **glossary** gains the plan's terms.
- Acceptance: every standing rule and conditional passage traceable old→new by a mechanical comparison; the workflow check passes; a new project reads only its core + current phase module + its own conditionals; a new project of an unwritten type pauses; the bridge and all three running projects (reAngle, the video factory, the TDP) calibrate onto the new structure with the §6.3 classifications, none pausing, reopening no gate.

Division of labour (§15 condition 3): **governance text is the supervisor's to author** (gated by this two-critic review); **programs are the builder's** (gated by the delegation loop). Each increment marks its author.

## The lenses to apply (build plan)

- **Prior-project lessons:** does every extracted lesson land on a named increment's acceptance criteria, an ordering choice, a brief constraint, or a configuration item? A merely-mentioned lesson is Blocking.
- **Requirement trace:** does every `planned` requirement have ≥1 increment naming its ID under `Satisfies`? An untraced requirement, or a deferral without the owner's dated answer, is Blocking.
- **Ordering:** is any increment dependent on something built after it?
- **Granularity:** which increments are secretly two or more; which are noise?
- **Testability:** can each increment's acceptance criteria be checked by a specific observable outcome?
- **Scope boundaries:** does each increment name its files/dirs? Do any two overlap on the same files?
- **First runnable point; vertical slices:** is every stage a vertical slice (crossing the layers its features need, demonstrable on its own) rather than a horizontal cut? A horizontal stage is Blocking.
- **Placement:** does every increment state Depends on / Parallel / Diagrams / Scope? Are `Parallel: yes` increments truly independent? (All here are `Parallel: no`.)
- **Stages:** is every increment in exactly one named stage; is each stage coherent and demonstrable (normally 3–8 increments)?
- **Missing increments:** what must happen that no increment covers — error handling, configuration, teardown, migration, packaging, install/manifest wiring?
- **Already built / already settled:** read docs/INVENTORY.md — an increment building what Features already lists, or reversing a Decision without quoting its reason, is Blocking.
- **Testing a governance-text release:** these increments are largely markdown (phase modules, trait files, type workflows). Is each text requirement backed by a *structural* test that names its requirement ID (file exists, required sections present, the workflow check passes), so completion-check can mark it done? Prose quality is this review's job; structure must be a test.
- **The specific risks of this release:** could a standing rule be dropped in the split (is the traceability comparison, TASK-014, sufficient to catch it)? Could the compaction digest's character limit be breached by the core carve (TASK-009)? Does the interface phase keep today's conditions together (the mockup variant as an addition, not a replacement — TASK-010, TASK-015)?

## The record so far (settled; do not raise again)

Nothing accepted yet — this is round 1.

---

## THE BUILD PLAN AND REQUIREMENTS REGISTER FOLLOW



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


# Requirements — Claude-Cursor Bridge (Release B)

Drawn from the Restructuring Plan's release B (§16), its scope and "Accepted when", and the design it rests on (§6.2–6.12, §6.6, §6.7, §6.8, §15 condition 6). This register governs release B only; the rules and programs that already shipped (releases 0, A1a–A5) are the baseline, not rows here. "Done" for release B is every row below built and tested or deferred/dropped by the owner with a date.

| ID | Requirement | Source | Status | Evidence |
|---|---|---|---|---|
| R-001 | The bridge is set up as a supervised project: a status file, a requirements register drawn from this plan, a resolved model roster, run parameters, and a `project.json`. | DESIGN §15 condition 6 | planned | — |
| R-002 | The security floor (Semgrep, OSV-Scanner, Socket) runs in the bridge's own CI gate, pinned by commit, alongside the tests it already runs. | DESIGN §15 condition 6 (P2) | planned | — |
| R-003 | The supervisor's instructions are split into the main-workflow core and per-phase modules; the core holds the roles and division of labour, the founding rules, the loop's shape, escalation and reporting, project state, and the standing rules that hold in every phase. | DESIGN §6.2 | planned | — |
| R-004 | Each phase module holds its phase's whole procedure and opens with the short list of what must survive a compaction. | DESIGN §16; §6.2 | planned | — |
| R-005 | The compaction/session-start hook names the single phase module to re-read after a compaction. | DESIGN §16 (release B scope) | planned | — |
| R-006 | Extension points are declared — a canonical registry (the §6.4 initial set) and, in each phase module, the points that phase offers. | DESIGN §6.4 | planned | — |
| R-007 | The conditional-workflow layering is in force: main core, phase modules, type workflow, sub-workflow, trait additions; each layer inherits what it does not mention and is read only when it applies. | DESIGN §6.2 | planned | — |
| R-008 | Only type workflows and sub-workflows may replace or set; trait additions may only add; no conditional workflow can remove a founding rule, weaken the merge gate, or skip the register, the inventory, or the reviews. | DESIGN §6.5 | planned | — |
| R-009 | A sub-workflow inherits its type workflow and may override its replacement or setting; siblings are exclusive; two levels (type and sub-type) only. | DESIGN §6.5 | planned | — |
| R-010 | The interface phase runs one variant per kind of interface a part has, and the trait *has screens* adds the mockup variant (an addition, not a replacement), keeping the frozen interface rules, the design auditor, and the running-interface tests together. | DESIGN §6.5 | planned | — |
| R-011 | `workflow/open-list.md` lists every product type, sub-type, and trait with its definition and whether its workflow is written. | DESIGN §6.3, §6.11 | planned | — |
| R-012 | The interface-phase variants are held once in the main workflow (mockups for screens, command design, contract design, playable prototype). | DESIGN §6.4, §6.9 | planned | — |
| R-013 | A part that fits no product type, two equally, or one defined-but-unwritten pauses the project at intake and sends the owner to the maintainer; a new or defined-but-unwritten trait is flagged at the design gate and work continues. | DESIGN §6.7 | planned | — |
| R-014 | `workflow-check.py` verifies: every change targets an existing extension point; replace/set appears only in a type or sub-workflow and replace only on a replaceable phase; trait additions only add; every sub-workflow names an existing type workflow; every project's `Workflows:` line names valid, written entries. | DESIGN §6.6 | planned | — |
| R-015 | The status file records a `Workflows:` line per part (product type, sub-type, traits) beside the `Phase:` line. | DESIGN §6.2 | planned | — |
| R-016 | Trait *has screens* written: the mockup variant with its design tooling, the frozen interface rules, the design auditor, the observability tests of the running interface. | DESIGN §6.8 | planned | — |
| R-017 | Trait *installable* written: the delivery conventions — installers, install scripts, the command reference, the packaging stage, installer verification. | DESIGN §6.8 | planned | — |
| R-018 | Trait *performance budgets* written: budgets at intake, their mechanisms in the design, benchmarks, the benchmark floor, the performance lens. | DESIGN §6.8 | planned | — |
| R-019 | Trait *external services* written: contract capture before an adapter is built, replay of recorded responses, and the deployed-layout-tested-before-deployment / bounded-remote-wait checks. | DESIGN §6.8, §6.3 (P11) | planned | — |
| R-020 | Trait *spends money* written: an approval before any paid action, the estimate against the worst case, a cap, the platform and account named. | DESIGN §6.8 | planned | — |
| R-021 | Trait *long-running process* written: start, stop, and health; nothing left running; the background-process conditions of §8.1. | DESIGN §6.8 | planned | — |
| R-022 | Trait *AI models* written: evaluation sets and thresholds in place of exact tests; pinned models; recorded outputs. | DESIGN §6.8 | planned | — |
| R-023 | Type workflow *web app* and sub-type *local web app* written. | DESIGN §6.8, §6.9 | planned | — |
| R-024 | Type workflow *software on your own computer* and sub-type *local service* written. | DESIGN §6.8, §6.9 | planned | — |
| R-025 | Type workflow *host extension* and sub-type *Claude Code extension* written: the host's behaviour as verified facts with the version checked, tests inside the real host, delivery as installation into the host. | DESIGN §6.9 | planned | — |
| R-026 | The new interface text — contract design (local service) and command design (CLI) — written; it applies to a project from its next design phase or change cycle, and calibration reopens no gate. | DESIGN §6.8, §6.9 | planned | — |
| R-027 | Calibration is aware of conditional workflows: it applies a conditional workflow to running projects of that product type by phase, reopening no gate. | DESIGN §6.10 (release B scope) | planned | — |
| R-028 | The glossary gains the terms of this plan. | DESIGN release B scope; Glossary | planned | — |
| R-029 | Every standing rule and every conditional passage is traceable from its old place in the monolithic instructions to its new file, verified by a mechanical comparison. | DESIGN release B "Accepted when" | planned | — |
| R-030 | A new project walked from intake to configuration reads only its core, its current phase module, and its own conditional workflows. | DESIGN release B "Accepted when" | planned | — |
| R-031 | The bridge, reAngle, the video factory, and the TDP each calibrate onto the new structure with the §6.3 classifications, none pausing, without reopening a gate. | DESIGN §6.3; release B "Accepted when" | planned | — |


