# Build plan — Claude-Cursor Bridge, Release B

The design is the Restructuring Plan's release B (§16) and the sections it rests on (§6, §15). This plan decomposes that scope into increments. Per §15 condition 3, **governance text is design: the supervisor authors it, gated by the two-critic design review; programs are implementation: the builder writes them, gated by the delegation loop.** Each increment marks its author. Status is derived from `origin/main` by `plan-check.py`, never written here. Revised 2026-10-11 after two-critic rounds 1–3 (converging: Blocking 7→6→1 and 5→1→2).

## Standing constraints (every increment)
- **Manifest:** any increment that adds, moves, removes, **or edits** a file under `bridge/` regenerates `bridge/cursor-bridge/MANIFEST.json` (`python tools/make-manifest.py`) in the same commit (a hash change fails `bridge-check --sources` in CI otherwise); `MANIFEST.json` is named in its Scope.
- **Tests name the requirement:** each increment's test contains the literal `R-nnn` of every requirement it satisfies. A governance-text increment's test is structural (the file exists at its §6.11 path, opens with its compaction-survival list where applicable, declares its extension points by the registry's names, is within the R-032 bound, and — **from TASK-006 on** — `workflow-check.py` exits 0 on it).
- **Moves, not copies:** text moved in the split (including a trait's gathered passages, §6.8) *moves* — it leaves its old home; the main workflow shrinks. A passage may move twice (baseline → phase module → trait file); `trace-check` accepts it found verbatim anywhere under `workflow/**`.
- **Trace exceptions:** `bridge/cursor-bridge/workflow/trace-exceptions.md` carries two entry kinds — `reword <TASK> <file> <heading>` and `new <TASK> <file> <heading>` — appended by the supervisor-text increment that rewords or adds; it is named in that increment's Scope so the design review sees it.
- **Open list currency:** an increment that writes a type, sub-type, or trait flips that entry's written flag in `bridge/cursor-bridge/workflow/open-list.md` (named in its Scope).
- **No hard line wraps** in any authored Markdown (rule 30).

## Prior-project lessons
The overlapping prior project is the bridge itself (`~/.claude/cursor-bridge/Known-Pitfalls.md`, the three Issues files).
**Extracted (attached to a `Done when:`).** KP-035 → TASK-010 (digest within limit), TASK-011–014 (modules read-whole), TASK-015 (one module + conditional files). Digest limit → TASK-010 keeps `test_session_start.py` green. §6.5/R11 → TASK-012 and TASK-017 (the mockup variant is an *addition*; its text lives in `interface/mockups.md`). KP-029 → TASK-006 (workflow-check fails an unwritten-type line), TASK-004 (the written column).
**Judged irrelevant.** Asset-loop/Roblox/aggregate pitfalls (E/F); code-map pitfalls (C/D).

---

## Stage B1 — Supervised-project bootstrap
Demonstration: the bridge's CI runs its full gate — tests, windowless, manifest, and the security floor — green on a PR, and a fresh session resumes release B from `docs/PROJECT_STATUS.md` and `docs/INVENTORY.md` alone.

### TASK-001 — Intake and configuration records
Author: supervisor (records; §15 condition 3).
Parent: none
Depends on: none
Parallel: no
Diagrams: none
Scope: project.json; docs/PROJECT_STATUS.md; docs/REQUIREMENTS.md; docs/INVENTORY.md; docs/RUN_PARAMETERS.md; docs/ROSTER.json; docs/ROSTER.resolved.json; docs/BUILD_PLAN.md; docs/DESIGN_CRITIQUE.md; tests/test_release_b_bootstrap.py
Satisfies: R-001
Done when: `plan-check`, `completion-check --mode plan`, `inventory-check`, `roster-check` pass; `project.json` is valid; decision 6 and R-038 are recorded as owner-answered with the date in INVENTORY Decisions and the stale Deferred row for R-038 is closed; the baseline-measurement precondition is recorded as met; `test_release_b_bootstrap.py` (names R-001) asserts the records exist, `project.json` parses, and no open Deferred row contradicts a settled Decision.

### TASK-002 — The security floor in the bridge's CI
Author: builder.
Parent: none
Depends on: TASK-001
Parallel: no
Diagrams: none
Scope: .github/workflows/tests.yml; .semgrep.yml; osv-scanner.toml; socket.yml; requirements.lock; tests/test_release_b_ci_floor.py
Satisfies: R-002
Done when: CI installs from `requirements.lock` (the dependency manifest OSV/Socket read; a change to it pairs with itself for `lock-check`); a `gate` adds Semgrep (ubuntu authoritative), OSV-Scanner, and Socket, each action pinned by commit SHA; OSV/Socket find the lockfile and do not exit 128; `test_release_b_ci_floor.py` (names R-002) asserts the three scanners run and every action is SHA-pinned; green on this PR.

## Stage B2 — The conditional-workflow framework
Demonstration: `workflow-check.py` passes on the open list and sample conditional fixtures, and exits non-zero on a renamed/undeclared extension point, a trait that replaces, a replace on a non-replaceable phase, a sub-workflow naming a missing type, two product types or two sub-types or a crossed pair on one part, and a `Workflows:` line naming an unwritten type.

### TASK-003 — The conditional-workflow model in the core
Author: supervisor.
Parent: none
Depends on: TASK-001
Parallel: no
Diagrams: none
Scope: bridge/commands/supervisor.md; bridge/cursor-bridge/MANIFEST.json; tests/test_workflow_model.py
Satisfies: R-007, R-008, R-009, R-034
Done when: the core describes the five layers, inheritance, read-when, replace/set/add ("only type/sub-workflows may replace or set; trait additions only add"), the founding-rule/merge-gate/register floor, and the stated order several traits' additions compose in (R-034); `test_workflow_model.py` (names R-007, R-008, R-009, R-034) asserts those statements and that the digest stays within its limit.

### TASK-004 — The open list
Author: supervisor.
Parent: none
Depends on: TASK-003
Parallel: no
Diagrams: none
Scope: bridge/cursor-bridge/workflow/open-list.md; bridge/cursor-bridge/MANIFEST.json; tests/test_open_list.py
Satisfies: R-011
Done when: every §6.3 product type, sub-type, and trait is listed with its definition, its default traits, its fixed workflow name / sub-workflow name, and a written/unwritten flag (all unwritten at first); the open list is the canonical source of a type's default traits (a type file's statement is checked against it by `workflow-check`; note 2026-10-17, stage B2's review: no form for that statement exists yet, so nothing checks it; the form and its check come together in the change that writes the first such statement, routed to TASK-019 in docs/HARDENING.md); the §6.10 add/change procedure is recorded; `test_open_list.py` (names R-011) asserts each entry has definition, default-traits, name, and flag, and the file parses in the shape `workflow-check.py` reads.

### TASK-005 — The extension-point registry
Author: supervisor.
Parent: none
Depends on: TASK-003
Parallel: no
Diagrams: none
Scope: bridge/cursor-bridge/workflow/extension-points.md; bridge/cursor-bridge/MANIFEST.json; tests/test_extension_points.py
Satisfies: R-006
Done when: the registry lists the §6.4 points per phase, including Definition of done and Delivery, each naming the module that declares it and whether its phase is replaceable (the interface phase is, per §6.4); `test_extension_points.py` (names R-006) asserts every §6.4 point is present, names a declaring module, and carries a replaceable flag.

### TASK-006 — The workflow check
Author: builder.
Parent: none
Depends on: TASK-002, TASK-004, TASK-005
Parallel: no
Diagrams: none
Scope: bridge/cursor-bridge/workflow-check.py; .github/workflows/tests.yml; tests/fixtures/workflows/; bridge/cursor-bridge/MANIFEST.json; tests/test_workflow_check.py
Satisfies: R-014, R-033
Done when: `workflow-check.py` exits 0 on the open list + sample fixtures and non-zero on (a) an undeclared/renamed extension point, (b) a trait that replaces or sets, (c) a replace on a non-replaceable phase (read from the registry), (d) a sub-workflow naming a missing type, (e) two product types / two sub-types / a sub-type not of its type on one part, (f) a `Workflows:` line naming an unwritten **type or sub-type** (which pauses the project); an **unwritten trait is flagged, non-fatal** (work continues, §6.7); its **CI invocation checks `workflow/**` and `tests/fixtures/workflows/` only** (never the bridge's own `docs/PROJECT_STATUS.md`); it creates `tests/fixtures/workflows/` and the sample fixtures; `test_workflow_check.py` (names R-014, R-033) covers each case, the unwritten-trait flag, and the CI step. (The tree-wide registry↔module cross-check is a Done-when of TASK-014, once every module declares its points.)

### TASK-007 — The Workflows status line: template and semantics
Author: supervisor.
Parent: none
Depends on: TASK-003
Parallel: no
Diagrams: none
Scope: bridge/commands/supervisor.md; bridge/cursor-bridge/MANIFEST.json; tests/test_workflows_line_text.py
Satisfies: R-015
Done when: the status template carries a `Workflows:` line per part (product type → sub-type; traits) beside `Phase:`, its grammar defined; `test_workflows_line_text.py` (names R-015) asserts the template and grammar are present.

### TASK-008 — The Workflows status line: enforced
Author: builder.
Parent: none
Depends on: TASK-007
Parallel: no
Diagrams: none
Scope: bridge/cursor-bridge/inventory-check.py; bridge/cursor-bridge/conformance-check.py; bridge/cursor-bridge/workflow-check.py; bridge/cursor-bridge/MANIFEST.json; tests/test_workflows_line_check.py; tests/test_conformance_check.py
Satisfies: R-015
Done when: `inventory-check.py`/`conformance-check.py` read the `Workflows:` line and report a malformed or missing one; `test_workflows_line_check.py` (names R-015) covers valid, missing, malformed.

### TASK-009 — The glossary gains the plan's terms
Author: supervisor.
Parent: none
Depends on: TASK-003
Parallel: no
Diagrams: none
Scope: bridge/cursor-bridge/Glossary.md; bridge/cursor-bridge/MANIFEST.json; tests/test_glossary_terms.py
Satisfies: R-028
Done when: the glossary defines the closed set — conditional workflow, type workflow, sub-workflow, trait, trait addition, extension point, phase module, main workflow core, product type, sub-type, replace, set, add, open list, workflow check, workflow name, sub-workflow name, compaction-survival list; and its existing "Phase" entry lists all eight template values (intake, design, mockups, planning, configuration, building, done, changing); `test_glossary_terms.py` (names R-028) asserts each has a definition.

## Stage B3 — The core and phase-module split
Demonstration: after a simulated compaction the session-start hook names the current phase's module(s) per the shared table (one for most phases; planning and building map to two) plus the current phase's conditional files and the table's further files to re-read, and the traceability comparison shows every standing rule and conditional passage mapped from the pinned pre-split baseline to its new file with nothing dropped.

### TASK-016 — The traceability comparison (built first)
Author: builder.
Parent: none
Depends on: TASK-003, TASK-005, TASK-007
Parallel: no
Diagrams: none
Scope: bridge/cursor-bridge/trace-check.py; bridge/cursor-bridge/workflow/trace-baseline.txt; bridge/cursor-bridge/workflow/trace-exceptions.md; bridge/cursor-bridge/MANIFEST.json; tests/test_trace_check.py; docs/cli-reference.json; docs/CLI_REFERENCE.md
Satisfies: R-029
Done when: `trace-baseline.txt` pins the commit before the carve (after TASK-003/005/007's core edits); `trace-check.py` maps every standing rule and conditional passage (the project-layout/Workspace-boundary section included) from that baseline to its home — a home is `supervisor.md` (for a rule that stays in the core) or any file under `workflow/**`; a passage found verbatim in **more than one** home fails as a **COPY** unless a `reword`/`new` entry explains it (so "moves, not copies" is enforced for every increment, not only where a per-increment test asserts absence); a two-hop move (baseline→module→trait, the source emptied) passes; verbatim moves are required except `reword` entries in `trace-exceptions.md`; text new to the modules is flagged unless a `new` entry declares it; every `~/.claude/...` reference and cited section still resolves; it runs incrementally; the empty `trace-exceptions.md` is scaffolded here; `test_trace_check.py` (names R-029) covers a clean move, a two-hop move, a **copy into two homes (fails)**, a silent reword (fails), an undeclared new passage (fails), a dropped boundary section (fails), a dangling reference (fails), and both exception kinds.

### TASK-010 — Carve the core and move the phase sections
Author: supervisor.
Parent: none
Depends on: TASK-003, TASK-005, TASK-006, TASK-007, TASK-016
Parallel: no
Diagrams: none
Merge unit: TASK-010 and TASK-015 are built on one stage branch and merged as one PR whose title **starts with** `TASK-010 TASK-015:` (so `plan-check` derives both as merged) — the test suite is never red on `main` between the carve and the hook, and no release ships between them.
Scope: bridge/commands/supervisor.md; bridge/cursor-bridge/workflow/phases/intake.md; .../design.md; .../interface.md; .../planning.md; .../run-parameters.md; .../configuration.md; .../delegation-loop.md; .../change-cycle.md; .../reflection.md; .../project-end.md; bridge/cursor-bridge/workflow/trace-exceptions.md; bridge/cursor-bridge/MANIFEST.json; tests/test_core_carve.py; tests/test_session_start.py; tests/instructions.py; tests/test_allowlist.py; tests/test_a5_followups.py; tests/test_text_consistency.py; tests/test_workflow_model.py (widened at the carve, 2026-10-20: the tests that read the supervisor's instructions read the core and its modules, through tests/instructions.py, so a passage that moves keeps its test; test_workflow_model.py's two assertions of the transitional reading become the carved one's)
Satisfies: R-003, R-032
Done when: every phase section moves verbatim out of `supervisor.md` into its module in one commit; project-end is carved out of the `## Reflection points` block into `project-end.md` as a declared split recorded in `trace-exceptions.md`; the core keeps only roles/division, founding rules, loop shape, escalation/reporting, project state, and the standing rules that hold in every phase, pointing at the modules; `trace-check` green for the moved sections; the digest stays within `test_session_start.py`'s limit; the core's post-carve size is recorded as a measurement; a proof test shows `workflow/**` installs from the regenerated manifest with no `bridge-install.py` change; `test_core_carve.py` (names R-003, R-032) asserts the core's section set, that no phase procedure remains, and the modules exist. (`test_session_start.py`'s heading/line-range assertions are updated for the module table in the combined TASK-010+TASK-015 change, never weakened; the carve alone does not leave the suite red on `main` because the two land as one PR.)

### TASK-011 — Enrich phase modules: intake, design
Author: supervisor.
Parent: none
Depends on: TASK-010
Parallel: no
Diagrams: none
Scope: bridge/cursor-bridge/workflow/phases/intake.md; bridge/cursor-bridge/workflow/phases/design.md; bridge/cursor-bridge/workflow/trace-exceptions.md; bridge/cursor-bridge/MANIFEST.json; tests/test_phase_modules_intake_design.py; bridge/cursor-bridge/Merge-Verification-Policy.md; bridge/agents/plan-critic.md (widened 2026-10-20 for the carve's pointer sweep, docs/HARDENING.md, Stage B3: the two files' pointers to the design phase named `supervisor.md` and now name `workflow/phases/design.md`); bridge/cursor-bridge/settings.bridge.json (widened 2026-10-20: intake now runs `workflow-check.py --status`, so the read-only checker gets the allow rule every other checker the instructions name has, tests/test_allowlist.py)
Satisfies: R-004, R-006, R-013, R-032, R-035, R-036
Done when: intake.md and design.md each open with their compaction-survival list and declare their extension points; intake.md carries the pause for an unfit/unwritten product type (R-013) and that traits are proposed at intake (R-035); design.md carries that traits and a type's default traits are settled at the design gate (R-035) and the new-trait flag with the owner's pause option (R-036, the design-gate half only — the promotion pass is TASK-014's); within the R-032 bound; `trace-check` green for the moved sections; `test_phase_modules_intake_design.py` (names R-004, R-006, R-013, R-032, R-035, R-036) asserts the structure and those passages.

### TASK-012 — Enrich phase modules: interface, planning
Author: supervisor.
Parent: none
Depends on: TASK-010
Parallel: no
Diagrams: none
Scope: bridge/cursor-bridge/workflow/phases/interface.md; .../interface/mockups.md; .../interface/command-design.md; .../interface/contract-design.md; .../interface/playable-prototype.md; .../planning.md; bridge/cursor-bridge/workflow/trace-exceptions.md; bridge/cursor-bridge/MANIFEST.json; tests/test_phase_modules_interface_planning.py
Satisfies: R-004, R-006, R-010, R-012, R-032
Done when: interface.md declares all four variants once, each variant's text in its own file; `interface/mockups.md` holds the Phase-3 mockup procedure (today's `## Phase 3 — UI mockups`), declared an *addition* activated by the trait *has screens* (R-010) — the build-phase interface passages (the frozen-rule brief constraint, the design-auditor review step, the observability tests) are NOT here; they are gathered by the has-screens trait (TASK-017) from the build modules; planning.md and interface.md each open with their compaction-survival list and declare their extension points; the playable-prototype file is a declared pointer to the Game Development workflow (release E), worded to avoid `completion-check`'s stand-in patterns (verified by `completion-check --mode plan` reporting no stand-in on `workflow/**`); within the R-032 bound; `trace-check` green; `test_phase_modules_interface_planning.py` (names R-004, R-006, R-010, R-012, R-032) asserts both files' structure, the four variants, and the mockup-as-addition.

### TASK-013 — Enrich phase modules: run parameters, configuration, the delegation loop
Author: supervisor.
Parent: none
Depends on: TASK-010
Parallel: no
Diagrams: none
Scope: bridge/cursor-bridge/workflow/phases/run-parameters.md; .../configuration.md; .../delegation-loop.md; .../delegation-loop/; bridge/cursor-bridge/workflow/trace-exceptions.md; bridge/cursor-bridge/MANIFEST.json; tests/test_phase_modules_build.py
Satisfies: R-004, R-006, R-032
Done when: each module opens with its compaction-survival list, declares its extension points, and is within the R-032 bound — the delegation-loop module split into sub-files under `workflow/phases/delegation-loop/` if it would exceed the bound, each sub-file named by the module's own pointer line; `trace-check` green; `test_phase_modules_build.py` (names R-004, R-006, R-032) asserts the structure and, if split, the sub-file pointer.

### TASK-014 — Enrich phase modules: change cycle, reflection, project end
Author: supervisor.
Parent: none
Depends on: TASK-010
Parallel: no
Diagrams: none
Scope: bridge/cursor-bridge/workflow/phases/change-cycle.md; .../reflection.md; .../project-end.md; bridge/cursor-bridge/workflow/trace-exceptions.md; bridge/cursor-bridge/MANIFEST.json; tests/test_phase_modules_close.py
Satisfies: R-004, R-006, R-032, R-036
Done when: each module opens with its compaction-survival list, declares its extension points (reflection/project-end declare Definition of done and Delivery); project-end.md carries the promotion-pass route (R-036); reflection.md's issues rule gains the line that an incident records whether a compaction preceded it (the baseline follow-up); within the R-032 bound; `trace-check` green; **the tree-wide registry↔module cross-check passes (every registry point is declared by its named module and every module declaration is in the registry)**; `test_phase_modules_close.py` (names R-004, R-006, R-032, R-036) asserts the structure, the promotion pass, and the cross-check.

### TASK-015 — The compaction hook names the phase module
Author: builder.
Parent: none
Depends on: TASK-010, TASK-006, TASK-007
Parallel: no
Diagrams: none
Merge unit: merged with TASK-010 as one PR (see TASK-010) so the suite is never red on `main` between the carve and this hook.
Scope: bridge/cursor-bridge/session-start.py; bridge/cursor-bridge/MANIFEST.json; tests/test_session_start_module.py; tests/test_session_start.py; docs/cli-reference.json; docs/CLI_REFERENCE.md
Satisfies: R-005
Done when: given a project's `Phase:` and `Workflows:` lines the hook re-injects the digest and, as a **second run** (neither near the 10,000-char cap), names the current phase's module(s), the conditional files (type/sub-type/trait) touching that phase, and the table's further files, listing a split module's sub-files and a phase's variant files from the module's own declared-variants/pointer line (no table entry names a variant file directly, so the table never points at `interface/mockups.md` before TASK-012 creates it); the shared Phase→module table maps **every template value**: intake→intake; design→design; mockups→interface (+ the mockups variant); planning→planning+run-parameters; configuration→configuration; building→delegation-loop+reflection (+project-end at the last stage close); done→change-cycle (a request on a done project is a change cycle); changing→change-cycle+delegation-loop+reflection+project-end; plus the convention re-reads (merge-policy+pitfalls while building/changing; diagram-conventions+glossary at design; project-config+pitfalls at configuration); emits trait files in the R-034 order; `test_session_start.py`'s former heading/line-range assertions are re-pointed to the module table here (never weakened; the 9,500-char digest and status-at-limits cases kept); `test_session_start_module.py` (names R-005) covers every template phase value, a phase with and without conditionals, a split module (two sub-files), the convention files, and the trait order, using the TASK-006 fixtures.

## Stage B4 — The first conditional workflows
Demonstration: the bridge, reAngle, the video factory, and the TDP are each classified per §6.3 on committed fixtures; `workflow-check.py` passes on all four; and a mock new project of an unwritten product type pauses at intake.

### TASK-017 — Trait files: has screens, installable, performance budgets, external services
Author: supervisor.
Parent: none
Depends on: TASK-011, TASK-012, TASK-013, TASK-014, TASK-006
Parallel: no
Diagrams: none
Scope: bridge/cursor-bridge/workflow/traits/has-screens.md; .../installable.md; .../performance-budgets.md; .../external-services.md; bridge/cursor-bridge/workflow/phases/interface.md; .../planning.md; .../configuration.md; .../delegation-loop.md; .../delegation-loop/; .../intake.md; .../design.md; .../reflection.md; bridge/cursor-bridge/workflow/open-list.md; bridge/cursor-bridge/workflow/trace-exceptions.md; bridge/cursor-bridge/MANIFEST.json; tests/test_traits_existing.py; tests/test_b2_least_confident.py
Satisfies: R-010, R-016, R-017, R-018, R-019
Done when: each trait file gathers its passages by **moving** them out of the named phase modules (the modules shrink; `trace-check` maps baseline→module→trait) and adds only at declared points; *has screens* activates the mockup variant (whose procedure stays in `interface/mockups.md`, TASK-012) AND gathers, by moving, the build-phase interface-project passages — the frozen-rule brief constraint, the design-auditor review step, and the observability tests — from planning/configuration/the delegation loop/reflection, each at its phase's extension point, and **points at** founding rules N7/N9 (which stay in the core, not moved); *installable* carries installers/install-scripts/command-reference/packaging-stage/installer-verification; *performance budgets* carries budgets-at-intake/mechanisms/benchmarks/the floor/the lens; *external services* carries contract capture, replay, and the deployed-layout/bounded-remote-wait checks; the four rows flip to written; `workflow-check.py` passes; `test_traits_existing.py` (names R-010, R-016–R-019) asserts each file adds-only, names its content, that the source modules no longer hold the moved passages, and that N7/N9 remain in the core. With Installable written, the pin of `tests/test_b2_least_confident.py` (the bridge's own status line, FIX-002) drops its FLAG line: the two (f) findings and `RESULT: 2 problem(s)` remain.

### TASK-018 — Trait files: spends money, long-running process, AI models
Author: supervisor.
Parent: none
Depends on: TASK-011, TASK-013, TASK-005, TASK-006
Parallel: no
Diagrams: none
Scope: bridge/cursor-bridge/workflow/traits/spends-money.md; .../long-running-process.md; .../ai-models.md; bridge/cursor-bridge/workflow/open-list.md; bridge/cursor-bridge/workflow/trace-exceptions.md; bridge/cursor-bridge/MANIFEST.json; tests/test_traits_new.py
Satisfies: R-020, R-021, R-022
Done when: *spends money* carries approval-before-paid-action, the worst-case estimate, a cap, platform+account named, the §13.1 store of paid results that is never discarded, and a dry run on a copy before any paid run; *long-running process* **points at** founding rule N1/§8.1 (which stays in the core, not moved) and adds the start/stop/health procedure, the nothing-left-running check, and the brief constraint at the configuration and delegation-loop points; *AI models* carries evaluation sets and thresholds, pinned models, recorded outputs; the three rows flip to written; `workflow-check.py` passes; `test_traits_new.py` (names R-020–R-022) asserts each adds-only, names its content, and that N1/§8.1 remains in the core.

### TASK-019 — Type workflow: web app and local web app
Author: supervisor.
Parent: none
Depends on: TASK-012, TASK-014, TASK-006, TASK-017, TASK-018
Parallel: no
Diagrams: none
Scope: bridge/cursor-bridge/workflow/types/web-app.md; bridge/cursor-bridge/workflow/types/web-app/local-web-app.md; bridge/cursor-bridge/workflow/open-list.md; tests/fixtures/workflows/reangle.status.md; tests/fixtures/workflows/video-factory.status.md; bridge/cursor-bridge/MANIFEST.json; tests/test_type_web_app.py
Satisfies: R-023
Done when: the type sets delivery (deployment) and has default traits has-screens + personal-data; local-web-app overrides delivery to an installer + a local server to start/stop and replaces personal-data with installable + long-running process (§6.3); both rows flip to written; `workflow-check.py` passes and classifies reAngle and the video factory (committed fixtures) without pausing; `test_type_web_app.py` (names R-023) asserts the set/override, the default-trait replacement, and the sub-type inheritance.

### TASK-020 — Type workflow: software on your own computer and local service
Author: supervisor.
Parent: none
Depends on: TASK-012, TASK-013, TASK-014, TASK-006, TASK-017, TASK-018
Parallel: no
Diagrams: none
Scope: bridge/cursor-bridge/workflow/types/own-computer.md; bridge/cursor-bridge/workflow/types/own-computer/local-service.md; bridge/cursor-bridge/workflow/open-list.md; tests/fixtures/workflows/tdp.status.md; bridge/cursor-bridge/MANIFEST.json; tests/test_type_own_computer.py
Satisfies: R-024
Done when: the type names its GUI/CLI/pipeline/local-service sub-types; local-service *adds* the contract-design interface variant and, where the part also has administrative commands (the TDP), the command-design variant too (variants added per interface kind, not set as one value); both rows flip to written; `workflow-check.py` passes and classifies the TDP (committed fixture, performance-budgets held per §6.3 until its code map carries one) without pausing; `test_type_own_computer.py` (names R-024) asserts the sub-types and the added variants.

### TASK-021 — Type workflow: host extension and Claude Code extension
Author: supervisor.
Parent: none
Depends on: TASK-013, TASK-014, TASK-006, TASK-017
Parallel: no
Diagrams: none
Scope: bridge/cursor-bridge/workflow/types/host-extension.md; bridge/cursor-bridge/workflow/types/host-extension/claude-code-extension.md; bridge/cursor-bridge/workflow/open-list.md; tests/fixtures/workflows/bridge.status.md; bridge/cursor-bridge/MANIFEST.json; tests/test_type_host_extension.py; tests/test_b2_least_confident.py
Satisfies: R-025
Done when: the type adds the host's behaviour as verified facts with the version checked, tests inside the real host, and *sets* delivery to installation into the host (a type/sub-workflow set, permitted — the "replace/set only here" rule bans traits from setting, not types); both rows flip to written; `workflow-check.py` passes and classifies the bridge itself (committed fixture) without pausing; `test_type_host_extension.py` (names R-025) asserts those additions and the delivery set. With both written, that pin becomes `RESULT: OK` alone, exit 0.

### TASK-022 — Interface text: contract design and command design
Author: supervisor.
Parent: none
Depends on: TASK-012
Parallel: no
Diagrams: none
Scope: bridge/cursor-bridge/workflow/phases/interface/contract-design.md; bridge/cursor-bridge/workflow/phases/interface/command-design.md; bridge/cursor-bridge/workflow/trace-exceptions.md; bridge/cursor-bridge/MANIFEST.json; tests/test_interface_text.py
Satisfies: R-026
Done when: contract design covers a protocol's operations/inputs/outputs/errors/versioning as a contract file tests enforce; command design covers commands, help text, output formats; `test_interface_text.py` (names R-026) asserts both files' required sections. (The variant files are declared in TASK-012; this fills their bodies.)

## Stage B5 — Calibration and acceptance
Demonstration: a fresh session walked intake→configuration reads only its core, its current phase module, and its own conditional workflows; the four projects each classify under §6.3 on fixtures with `workflow-check` green.

### TASK-023 — Calibration aware of conditional workflows (text)
Author: supervisor.
Parent: none
Depends on: TASK-015, TASK-017, TASK-018, TASK-019, TASK-020, TASK-021
Parallel: no
Diagrams: none
Scope: bridge/commands/calibrate-bridge.md; bridge/cursor-bridge/MANIFEST.json; tests/test_calibrate_text.py
Satisfies: R-027
Done when: calibrate-bridge.md applies a conditional workflow to a running project of that type by phase, reopens no gate, states the applied text takes effect from the next design phase or change cycle, **adds a running project's `Workflows:` line from its recorded §6.3 classification and confirms it with the owner** (the A2 precedent: calibration added `project.json`), and keeps the project's existing `Phase:` value (mapped by the hook's shared table); `test_calibrate_text.py` (names R-027) asserts those statements.

### TASK-024 — Calibration aware of conditional workflows (program)
Author: builder.
Parent: none
Depends on: TASK-023, TASK-006, TASK-008
Parallel: no
Diagrams: none
Scope: bridge/cursor-bridge/conformance-check.py; bridge/cursor-bridge/MANIFEST.json; tests/test_calibrate_program.py; docs/cli-reference.json; docs/CLI_REFERENCE.md
Satisfies: R-027, R-033
Done when: `conformance-check.py` runs `workflow-check` at calibration over a running project's status file and reports an unclassified line or one naming an unwritten workflow; `test_calibrate_program.py` (names R-027, R-033) covers a classified and an unclassified project.

### TASK-025 — Acceptance: reads-only, classification, and full trace
Author: supervisor (tests).
Parent: none
Depends on: TASK-023, TASK-024, TASK-009, TASK-015, TASK-011, TASK-016
Parallel: no
Diagrams: none
Scope: tests/test_reads_only_applicable.py; tests/test_running_projects_classify.py; tests/test_trace_full_split.py
Satisfies: R-029, R-030, R-031
Done when: `test_reads_only_applicable.py` (names R-030) walks a sample project intake→configuration and asserts only the core + current phase module + its own conditionals are named for reading; `test_running_projects_classify.py` (names R-031) asserts the bridge, reAngle, the video factory, and the TDP each classify per §6.3 on the committed fixtures (TASK-019–021) with `workflow-check` green; `test_trace_full_split.py` (names R-029) asserts `trace-check` green over the finished split (nothing dropped across all modules and traits, no passage in two homes).

## Stage B6 — Release and install
Demonstration: release B is reviewed by a fresh context, stamped, installed with the projects paused, verified against the installed tree, and reAngle (the trial) calibrates onto the new structure and resumes.

### TASK-026 — Release-level review and fixes
Author: supervisor (orchestrates the fresh-context review; findings close through the gate).
Parent: none
Depends on: TASK-022, TASK-025
Parallel: no
Diagrams: none
Scope: Reports/Reviews/ (outside Workspace/, human-facing — the review record); its working inputs stay under run/review/ (KP-016)
Satisfies: R-037
Done when: a fresh-context release-level review of the whole release (one pass, fixes, a second pass) is recorded and every finding closed — findings needing code or text become dated addendum increments through the normal gate (supervisor text / builder programs), after which the stamp (TASK-027) runs; the review confirms the carved core is still readable in one read (if not, the owner decides what else moves to a module); §15 condition 4's order (review → fix → stamp → install) holds.

### TASK-027 — Install run-sheet, stamp, install, and the trial
Author: supervisor (run-sheet text, CHANGELOG entry, VERSION/MANIFEST stamp — all records) / owner (completes the merge and runs the install run sheet).
Parent: none
Depends on: TASK-026
Parallel: no
Diagrams: none
Scope: bridge/commands/calibrate-bridge.md; bridge/cursor-bridge/CHANGELOG.md; bridge/cursor-bridge/VERSION; bridge/cursor-bridge/MANIFEST.json; docs/PROJECT_STATUS.md; docs/INVENTORY.md; tests/test_release_b_stamp.py
Satisfies: R-031, R-037, R-038
Done when: the install run sheet reflects R-038 (pause & switch this checkout to `main` at B6); the CHANGELOG entry names release B with its "if rolled back" notes; VERSION is bumped and MANIFEST regenerated; `bridge-check.py --sources` green on the stamped tree; `test_release_b_stamp.py` (names R-037, R-038) asserts VERSION/CHANGELOG/manifest agree and the run sheet says pause-and-switch; the projects are paused; `bridge-install.py` runs and `bridge-check.py` is green on `~/.claude`; reAngle calibrates (its `Workflows:` line valid, no gate reopened), resumes, and its field acceptance is met — after reAngle's first compaction under release B the hook names its current phase's module(s) read whole (visible in the transcript / `run/supervisor/`), its `Workflows:` line passes `workflow-check`, and one increment goes through the loop with no gate reopened; the video factory and the TDP each calibrate and resume per the owner's standing pause/resume policy (one calibration each, none pausing) — recorded as an owner-dated deferral at B6 if not resumed by then, so `completion-check --mode done` is not blocked by events outside release B.
