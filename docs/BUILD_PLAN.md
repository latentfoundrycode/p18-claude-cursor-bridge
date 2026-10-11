# Build plan — Claude-Cursor Bridge, Release B

The design is the Restructuring Plan's release B (§16) and the sections it rests on (§6, §15). This plan decomposes that scope into increments. Per §15 condition 3, **governance text is design: the supervisor authors it, gated by the two-critic design review; programs are implementation: the builder writes them, gated by the delegation loop.** Each increment marks its author. Status is derived from `origin/main` by `plan-check.py`, never written here. Revised 2026-10-11 after two-critic rounds 1 and 2.

## Standing constraints (every increment)
- **Manifest:** any increment that adds, moves, or removes a file under `bridge/` regenerates `bridge/cursor-bridge/MANIFEST.json` (`python tools/make-manifest.py`) in the same commit; `MANIFEST.json` is named in its Scope.
- **Tests name the requirement:** each increment's test contains the literal `R-nnn` of every requirement it satisfies, so `completion-check --mode done` sees it. A governance-text increment's test is structural (the file exists at its §6.11 path, opens with the compaction-survival list where applicable, declares its extension points by the registry's names, is within the R-032 size bound, and — **from TASK-006 on** — `workflow-check.py` exits 0 on it).
- **Verbatim moves + exceptions:** text moved in the split is moved verbatim; any reword is appended by the moving (supervisor-text) increment to `bridge/cursor-bridge/workflow/trace-exceptions.md` (named in that increment's Scope) so the design review sees it.
- **Open list currency:** an increment that writes a type, sub-type, or trait workflow flips that entry's written/unwritten flag in `bridge/cursor-bridge/workflow/open-list.md` (named in its Scope).
- **No hard line wraps** in any authored Markdown (rule 30).

## Prior-project lessons
The overlapping "prior project" is the bridge itself; lessons in `~/.claude/cursor-bridge/Known-Pitfalls.md` and the three projects' Issues files.
**Extracted (attached to a `Done when:`).** KP-035 → TASK-010 (digest within limit), TASK-011–014 (modules read-whole), TASK-015 (one module + the conditional files). Digest limit → TASK-010 keeps `test_session_start.py` green. §6.5/R11 → TASK-012 and TASK-017 (the mockup variant is an *addition*; `interface.md` holds the variant). KP-029 → TASK-006 (workflow-check fails an unwritten-type line) and TASK-004 (the written column).
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
Done when: `plan-check`, `completion-check --mode plan`, `inventory-check`, `roster-check` pass; `project.json` is valid with name/purpose/kind/version/state; decision 6 and R-038 are recorded as answered by the owner with the date in INVENTORY; the baseline-measurement precondition is recorded as met; `test_release_b_bootstrap.py` (names R-001) asserts the records exist and `project.json` parses.

### TASK-002 — The security floor in the bridge's CI
Author: builder.
Parent: none
Depends on: TASK-001
Parallel: no
Diagrams: none
Scope: .github/workflows/tests.yml; .semgrep.yml; osv-scanner.toml; socket.yml; requirements.lock; tests/test_release_b_ci_floor.py
Satisfies: R-002
Done when: CI installs from `requirements.lock` (which serves as the dependency manifest OSV/Socket read; a change to it pairs with itself for `lock-check`); a `gate` adds Semgrep (ubuntu authoritative), OSV-Scanner, and Socket, each action pinned by commit SHA; OSV/Socket find the lockfile and do not exit 128 "no packages"; `test_release_b_ci_floor.py` (names R-002) asserts the three scanners run and every action is SHA-pinned; the workflow is green on this PR.

## Stage B2 — The conditional-workflow framework
Demonstration: `workflow-check.py` passes on the open list and sample conditional fixtures, and exits non-zero on a renamed extension point, a trait that replaces, and a `Workflows:` line naming an unwritten type.

### TASK-003 — The conditional-workflow model in the core
Author: supervisor.
Parent: none
Depends on: TASK-001
Parallel: no
Diagrams: none
Scope: bridge/commands/supervisor.md; bridge/cursor-bridge/MANIFEST.json; tests/test_workflow_model.py
Satisfies: R-007, R-008, R-009, R-034
Done when: the core describes the five layers, inheritance, read-when, replace/set/add ("only type/sub-workflows may replace or set; trait additions only add"), the founding-rule/merge-gate/register floor, and the stated order several traits' additions compose in; `test_workflow_model.py` (names R-007, R-008, R-009, R-034) asserts those statements and that the digest stays within its limit.

### TASK-004 — The open list
Author: supervisor.
Parent: none
Depends on: TASK-003
Parallel: no
Diagrams: none
Scope: bridge/cursor-bridge/workflow/open-list.md; bridge/cursor-bridge/MANIFEST.json; tests/test_open_list.py
Satisfies: R-011
Done when: every §6.3 product type, sub-type, and trait is listed with its definition and a written/unwritten flag (all unwritten at first); the §6.10 add/change procedure is recorded; `test_open_list.py` (names R-011) asserts each entry is present with a flag and the file parses in the shape `workflow-check.py` reads.

### TASK-005 — The extension-point registry
Author: supervisor.
Parent: none
Depends on: TASK-003
Parallel: no
Diagrams: none
Scope: bridge/cursor-bridge/workflow/extension-points.md; bridge/cursor-bridge/MANIFEST.json; tests/test_extension_points.py
Satisfies: R-006
Done when: the registry lists the §6.4 points per phase, including Definition of done and Delivery, each naming the module that declares it; `test_extension_points.py` (names R-006) asserts every §6.4 point is present and names a declaring module.

### TASK-006 — The workflow check
Author: builder.
Parent: none
Depends on: TASK-002, TASK-004, TASK-005
Parallel: no
Diagrams: none
Scope: bridge/cursor-bridge/workflow-check.py; .github/workflows/tests.yml; tests/fixtures/workflows/; bridge/cursor-bridge/MANIFEST.json; tests/test_workflow_check.py
Satisfies: R-014, R-033
Done when: `workflow-check.py` passes on the open list + the sample fixtures and exits non-zero on (a) a change to a non-existent extension point, (b) a trait that replaces or sets, (c) a replace on a non-replaceable phase, (d) a sub-workflow naming a missing type, (e) a `Workflows:` line naming an unwritten type, and (f) a registry point no module declares or a module declaration absent from the registry; it runs in CI (added after TASK-002's floor); it owns `tests/fixtures/workflows/`; `test_workflow_check.py` (names R-014, R-033) covers each case and the CI step.

### TASK-007 — The Workflows status line: template and semantics
Author: supervisor.
Parent: none
Depends on: TASK-003
Parallel: no
Diagrams: none
Scope: bridge/commands/supervisor.md; bridge/cursor-bridge/MANIFEST.json; tests/test_workflows_line_text.py
Satisfies: R-015
Done when: the status template carries a `Workflows:` line per part (product type → sub-type; traits) beside `Phase:`, its grammar defined; `test_workflows_line_text.py` (names R-015) asserts the template and its grammar are present.

### TASK-008 — The Workflows status line: enforced
Author: builder.
Parent: none
Depends on: TASK-007
Parallel: no
Diagrams: none
Scope: bridge/cursor-bridge/inventory-check.py; bridge/cursor-bridge/conformance-check.py; tests/test_workflows_line_check.py
Satisfies: R-015
Done when: `inventory-check.py`/`conformance-check.py` read the `Workflows:` line and report a malformed or missing one; `test_workflows_line_check.py` (names R-015) covers valid, missing, and malformed.

### TASK-009 — The glossary gains the plan's terms
Author: supervisor.
Parent: none
Depends on: TASK-003
Parallel: no
Diagrams: none
Scope: bridge/cursor-bridge/Glossary.md; bridge/cursor-bridge/MANIFEST.json; tests/test_glossary_terms.py
Satisfies: R-028
Done when: the glossary defines the closed set — conditional workflow, type workflow, sub-workflow, trait, trait addition, extension point, phase module, main workflow core, product type, sub-type, replace, set, add, open list, workflow check; `test_glossary_terms.py` (names R-028) asserts each of those terms has a definition.

## Stage B3 — The core and phase-module split
Demonstration: after a simulated compaction the session-start hook names exactly one phase module (plus the current phase's conditional files) to re-read, and the traceability comparison shows every standing rule and conditional passage mapped from the pinned pre-split baseline to its new file with nothing dropped.

### TASK-016 — The traceability comparison (built first)
Author: builder.
Parent: none
Depends on: TASK-003, TASK-005
Parallel: no
Diagrams: none
Scope: bridge/cursor-bridge/trace-check.py; bridge/cursor-bridge/workflow/trace-baseline.txt; bridge/cursor-bridge/workflow/trace-exceptions.md; bridge/cursor-bridge/MANIFEST.json; tests/test_trace_check.py
Satisfies: R-029
Done when: `trace-baseline.txt` pins the commit before the carve (the current `main` pre-split); `trace-check.py` maps every standing rule and conditional passage (the project-layout/Workspace-boundary section included) from that baseline to its new file, requires verbatim moves except entries listed in `trace-exceptions.md`, flags text new to the modules unless its increment declared it, checks every `~/.claude/...` reference and cited section still resolves, and runs incrementally (passes for the sections moved so far); the empty `trace-exceptions.md` is created here for later increments to append to; `test_trace_check.py` (names R-029) covers a clean move, a silently reworded rule (fails), a dropped boundary section (fails), and a dangling reference (fails).

### TASK-010 — Carve the core and move the phase sections
Author: supervisor.
Parent: none
Depends on: TASK-003, TASK-005, TASK-007, TASK-016
Parallel: no
Diagrams: none
Scope: bridge/commands/supervisor.md; bridge/cursor-bridge/workflow/phases/intake.md; bridge/cursor-bridge/workflow/phases/design.md; bridge/cursor-bridge/workflow/phases/interface.md; bridge/cursor-bridge/workflow/phases/planning.md; bridge/cursor-bridge/workflow/phases/run-parameters.md; bridge/cursor-bridge/workflow/phases/configuration.md; bridge/cursor-bridge/workflow/phases/delegation-loop.md; bridge/cursor-bridge/workflow/phases/change-cycle.md; bridge/cursor-bridge/workflow/phases/reflection.md; bridge/cursor-bridge/workflow/phases/project-end.md; bridge/cursor-bridge/workflow/trace-exceptions.md; bridge/cursor-bridge/MANIFEST.json; tests/test_core_carve.py
Satisfies: R-003, R-032
Done when: every phase section moves verbatim out of `supervisor.md` into its `workflow/phases/<phase>.md` in this one commit; the core keeps only the roles/division of labour, founding rules, loop shape, escalation/reporting, project state, and the standing rules that hold in every phase, and points at the modules; `trace-check` is green for the moved sections; the compaction digest stays within `test_session_start.py`'s limit; a proof test shows `workflow/**` installs from the regenerated manifest with no `bridge-install.py` change (if not, a builder increment is added); the structure-pinning tests (`test_session_start.py`, `test_text_consistency.py`, and any other asserting `supervisor.md` headings) are re-pointed, never deleted; the hook increment (TASK-015) lands immediately after and no release is stamped between them; `test_core_carve.py` (names R-003, R-032) asserts the core's section set, that no phase procedure remains in it, and the module files exist.

### TASK-011 — Enrich phase modules: intake, design
Author: supervisor.
Parent: none
Depends on: TASK-010
Parallel: no
Diagrams: none
Scope: bridge/cursor-bridge/workflow/phases/intake.md; bridge/cursor-bridge/workflow/phases/design.md; bridge/cursor-bridge/workflow/phases/project-end.md; bridge/cursor-bridge/workflow/trace-exceptions.md; bridge/cursor-bridge/MANIFEST.json; tests/test_phase_modules_intake_design.py
Satisfies: R-004, R-006, R-013, R-032, R-035, R-036
Done when: intake.md and design.md each open with their compaction-survival list and declare their extension points; intake.md carries the pause for an unfit/unwritten product type (R-013) and that traits are proposed at intake (R-035); design.md carries that traits (and a type's default traits) are settled at the design gate (R-035), the new-trait flag with the owner's pause option (R-036), and project-end.md carries the promotion-pass route (R-036); each module within the R-032 bound; `trace-check` green for the moved sections; `test_phase_modules_intake_design.py` (names R-004, R-006, R-013, R-032, R-035, R-036) asserts the structure and those passages.

### TASK-012 — Enrich phase modules: interface, planning
Author: supervisor.
Parent: none
Depends on: TASK-010
Parallel: no
Diagrams: none
Scope: bridge/cursor-bridge/workflow/phases/interface.md; bridge/cursor-bridge/workflow/phases/interface/mockups.md; bridge/cursor-bridge/workflow/phases/interface/command-design.md; bridge/cursor-bridge/workflow/phases/interface/contract-design.md; bridge/cursor-bridge/workflow/phases/interface/playable-prototype.md; bridge/cursor-bridge/workflow/phases/planning.md; bridge/cursor-bridge/workflow/trace-exceptions.md; bridge/cursor-bridge/MANIFEST.json; tests/test_phase_modules_interface_planning.py
Satisfies: R-004, R-006, R-010, R-012, R-032
Done when: interface.md declares all four variants once, each variant's text in its own file; the mockup variant is declared an *addition* that keeps the frozen interface rules, the design auditor, and the running-interface tests together (R-010); the playable-prototype file is a declared stub pointing at the Game Development workflow (release E), not stand-in text the completion check rejects; each module within the R-032 bound; `trace-check` green for the moved sections; `test_phase_modules_interface_planning.py` (names R-004, R-006, R-010, R-012, R-032) asserts the four variants and the mockup-as-addition.

### TASK-013 — Enrich phase modules: run parameters, configuration, the delegation loop
Author: supervisor.
Parent: none
Depends on: TASK-010
Parallel: no
Diagrams: none
Scope: bridge/cursor-bridge/workflow/phases/run-parameters.md; bridge/cursor-bridge/workflow/phases/configuration.md; bridge/cursor-bridge/workflow/phases/delegation-loop.md; bridge/cursor-bridge/workflow/trace-exceptions.md; bridge/cursor-bridge/MANIFEST.json; tests/test_phase_modules_build.py
Satisfies: R-004, R-006, R-032
Done when: each module opens with its compaction-survival list, declares its extension points, is within the R-032 bound (the delegation-loop module split into sub-files under `workflow/phases/delegation-loop/` named by the module's own pointer if it would exceed the bound), and `trace-check` is green for its moved sections; `test_phase_modules_build.py` (names R-004, R-006, R-032) asserts the structure.

### TASK-014 — Enrich phase modules: change cycle, reflection, project end
Author: supervisor.
Parent: none
Depends on: TASK-010
Parallel: no
Diagrams: none
Scope: bridge/cursor-bridge/workflow/phases/change-cycle.md; bridge/cursor-bridge/workflow/phases/reflection.md; bridge/cursor-bridge/workflow/phases/project-end.md; bridge/cursor-bridge/workflow/trace-exceptions.md; bridge/cursor-bridge/MANIFEST.json; tests/test_phase_modules_close.py
Satisfies: R-004, R-006, R-032, R-036
Done when: each module opens with its compaction-survival list, declares its extension points (reflection/project-end declare Definition of done and Delivery), is within the R-032 bound; reflection.md's issues rule gains the line that an incident records whether a compaction preceded it (the baseline follow-up); project-end.md carries the promotion-pass route (R-036); `trace-check` green for its moved sections; `test_phase_modules_close.py` (names R-004, R-006, R-032, R-036) asserts the structure and those passages.

### TASK-015 — The compaction hook names the phase module
Author: builder.
Parent: none
Depends on: TASK-010, TASK-007
Parallel: no
Diagrams: none
Scope: bridge/cursor-bridge/session-start.py; tests/test_session_start_module.py
Satisfies: R-005
Done when: given a project's `Phase:` and `Workflows:` lines the hook re-injects the digest and, as a **second run** (so neither run nears the 10,000-char cap), names exactly one phase module plus the conditional files (type/sub-type/trait) touching that phase and any further files that phase re-reads; it carries the full Phase→module table, mapping each live `Phase:` value (planning → planning + run-parameters; building → delegation-loop + reflection; changing → change-cycle; etc.); `test_session_start_module.py` (names R-005) covers a phase with and without conditionals and the stage-close (reflection) case, using the TASK-006 fixtures.

## Stage B4 — The first conditional workflows
Demonstration: the bridge, reAngle, the video factory, and the TDP are each classified per §6.3 on committed fixtures; `workflow-check.py` passes on all four; and a mock new project of a product type whose workflow is not written pauses at intake.

### TASK-017 — Trait files: has screens, installable, performance budgets, external services
Author: supervisor.
Parent: none
Depends on: TASK-011, TASK-012, TASK-013, TASK-014, TASK-006
Parallel: no
Diagrams: none
Scope: bridge/cursor-bridge/workflow/traits/has-screens.md; bridge/cursor-bridge/workflow/traits/installable.md; bridge/cursor-bridge/workflow/traits/performance-budgets.md; bridge/cursor-bridge/workflow/traits/external-services.md; bridge/cursor-bridge/workflow/open-list.md; bridge/cursor-bridge/workflow/trace-exceptions.md; bridge/cursor-bridge/MANIFEST.json; tests/test_traits_existing.py
Satisfies: R-010, R-016, R-017, R-018, R-019
Done when: each trait adds (never replaces) at declared points; *has screens* activates the mockup variant and adds the frozen interface rules, the design auditor, the running-interface tests; *installable* carries installers, install scripts, the command reference, the packaging stage, installer verification; *performance budgets* carries budgets at intake, mechanisms in the design, benchmarks, the benchmark floor, the performance lens; *external services* carries contract capture, replay, and the deployed-layout/bounded-remote-wait checks; the four rows flip to written in the open list; `workflow-check.py` passes; `test_traits_existing.py` (names R-010, R-016–R-019) asserts each file adds-only and names its content.

### TASK-018 — Trait files: spends money, long-running process, AI models
Author: supervisor.
Parent: none
Depends on: TASK-011, TASK-013, TASK-005, TASK-006
Parallel: no
Diagrams: none
Scope: bridge/cursor-bridge/workflow/traits/spends-money.md; bridge/cursor-bridge/workflow/traits/long-running-process.md; bridge/cursor-bridge/workflow/traits/ai-models.md; bridge/cursor-bridge/workflow/open-list.md; bridge/cursor-bridge/MANIFEST.json; tests/test_traits_new.py
Satisfies: R-020, R-021, R-022
Done when: *spends money* carries approval-before-paid-action, the worst-case estimate, a cap, platform+account named; *long-running process* carries start/stop/health, nothing-left-running, §8.1's conditions; *AI models* carries evaluation sets and thresholds, pinned models, recorded outputs; the three rows flip to written; `workflow-check.py` passes; `test_traits_new.py` (names R-020–R-022) asserts each adds-only and names its content.

### TASK-019 — Type workflow: web app and local web app
Author: supervisor.
Parent: none
Depends on: TASK-012, TASK-014, TASK-006, TASK-017, TASK-018
Parallel: no
Diagrams: none
Scope: bridge/cursor-bridge/workflow/types/web-app.md; bridge/cursor-bridge/workflow/types/web-app/local-web-app.md; bridge/cursor-bridge/workflow/open-list.md; bridge/cursor-bridge/MANIFEST.json; tests/test_type_web_app.py
Satisfies: R-023
Done when: the type sets delivery (deployment); local-web-app overrides it to an installer + a local server to start/stop and adds the installable and long-running-process traits per §6.3; replace/set appear only here; both rows flip to written; `workflow-check.py` passes and classifies reAngle and the video factory without pausing; `test_type_web_app.py` (names R-023) asserts the set/override and sub-type inheritance.

### TASK-020 — Type workflow: software on your own computer and local service
Author: supervisor.
Parent: none
Depends on: TASK-012, TASK-013, TASK-014, TASK-006, TASK-017, TASK-018
Parallel: no
Diagrams: none
Scope: bridge/cursor-bridge/workflow/types/own-computer.md; bridge/cursor-bridge/workflow/types/own-computer/local-service.md; bridge/cursor-bridge/workflow/open-list.md; bridge/cursor-bridge/MANIFEST.json; tests/test_type_own_computer.py
Satisfies: R-024
Done when: the type names its GUI/CLI/pipeline/local-service sub-types; local-service *adds* the contract-design interface variant and, where the part also has administrative commands (the TDP), the command-design variant too — variants are added per interface kind, not set as one value; both rows flip to written; `workflow-check.py` passes and classifies the TDP without pausing; `test_type_own_computer.py` (names R-024) asserts the sub-types and the added variants.

### TASK-021 — Type workflow: host extension and Claude Code extension
Author: supervisor.
Parent: none
Depends on: TASK-013, TASK-014, TASK-006, TASK-017
Parallel: no
Diagrams: none
Scope: bridge/cursor-bridge/workflow/types/host-extension.md; bridge/cursor-bridge/workflow/types/host-extension/claude-code-extension.md; bridge/cursor-bridge/workflow/open-list.md; bridge/cursor-bridge/MANIFEST.json; tests/test_type_host_extension.py
Satisfies: R-025
Done when: the type adds the host's behaviour as verified facts with the version checked, tests inside the real host, and *sets* delivery to installation into the host; both rows flip to written; `workflow-check.py` passes and classifies the bridge itself without pausing; `test_type_host_extension.py` (names R-025) asserts those additions and the delivery set.

### TASK-022 — Interface text: contract design and command design
Author: supervisor.
Parent: none
Depends on: TASK-012
Parallel: no
Diagrams: none
Scope: bridge/cursor-bridge/workflow/phases/interface/contract-design.md; bridge/cursor-bridge/workflow/phases/interface/command-design.md; bridge/cursor-bridge/workflow/trace-exceptions.md; bridge/cursor-bridge/MANIFEST.json; tests/test_interface_text.py
Satisfies: R-026
Done when: contract design covers a protocol's operations/inputs/outputs/errors/versioning as a contract file tests enforce; command design covers commands, help text, output formats; `test_interface_text.py` (names R-026) asserts both files' required sections. (The variant files are declared in TASK-012; this increment fills their bodies.)

## Stage B5 — Calibration and acceptance
Demonstration: a fresh session walked intake→configuration reads only its core, its current phase module, and its own conditional workflows; the four projects each classify under §6.3 on fixtures with `workflow-check` green.

### TASK-023 — Calibration aware of conditional workflows (text)
Author: supervisor.
Parent: none
Depends on: TASK-017, TASK-018, TASK-019, TASK-020, TASK-021
Parallel: no
Diagrams: none
Scope: bridge/commands/calibrate-bridge.md; bridge/cursor-bridge/MANIFEST.json; tests/test_calibrate_text.py
Satisfies: R-027
Done when: calibrate-bridge.md applies a conditional workflow to a running project of that type by phase, reopens no gate, states the applied text takes effect from the next design phase or change cycle, and says whether it rewrites a running project's `Phase:` line (it keeps the existing value, mapped by the hook's table); `test_calibrate_text.py` (names R-027) asserts those statements.

### TASK-024 — Calibration aware of conditional workflows (program)
Author: builder.
Parent: none
Depends on: TASK-023, TASK-006, TASK-008
Parallel: no
Diagrams: none
Scope: bridge/cursor-bridge/conformance-check.py; tests/test_calibrate_program.py
Satisfies: R-027, R-033
Done when: `conformance-check.py` runs `workflow-check` at calibration and reports a running project whose `Workflows:` line is unclassified or names an unwritten workflow; `test_calibrate_program.py` (names R-027, R-033) covers a classified and an unclassified project.

### TASK-025 — Acceptance: reads-only, classification, and full trace
Author: supervisor (tests).
Parent: none
Depends on: TASK-023, TASK-024, TASK-009, TASK-015, TASK-011, TASK-016
Parallel: no
Diagrams: none
Scope: tests/test_reads_only_applicable.py; tests/test_running_projects_classify.py; tests/test_trace_full_split.py; tests/fixtures/workflows/
Satisfies: R-030, R-031
Done when: `test_reads_only_applicable.py` (names R-030) walks a sample project intake→configuration and asserts only the core + current phase module + its own conditionals are named for reading; `test_running_projects_classify.py` (names R-031) asserts the bridge, reAngle, the video factory, and the TDP each classify per §6.3 on committed `Workflows:` fixtures with `workflow-check` green; `test_trace_full_split.py` asserts `trace-check` is green over the finished split (nothing dropped across all modules).

## Stage B6 — Release and install
Demonstration: release B is reviewed by a fresh context, stamped, installed on this computer with the projects paused, verified against the installed tree, and reAngle (the trial) calibrates onto the new structure and resumes — the other projects resuming per the owner's pause/resume policy.

### TASK-026 — The install run-sheet text and the release stamp
Author: supervisor (the run-sheet text and the CHANGELOG entry) + builder (VERSION/MANIFEST, a mechanical bump).
Parent: none
Depends on: TASK-025
Parallel: no
Diagrams: none
Scope: bridge/commands/calibrate-bridge.md; bridge/cursor-bridge/CHANGELOG.md; bridge/cursor-bridge/VERSION; bridge/cursor-bridge/MANIFEST.json; tests/test_release_b_stamp.py
Satisfies: R-037, R-038
Done when: the install run sheet reflects R-038 (pause & switch this checkout to `main` at B6); the supervisor writes the CHANGELOG entry naming release B with its "if rolled back" notes; VERSION is bumped to the release-B stamp and MANIFEST regenerated (the mechanical half); `bridge-check.py --sources` is green on the stamped tree; `test_release_b_stamp.py` (names R-037) asserts VERSION/CHANGELOG/manifest agree.

### TASK-027 — Release review, install, and the trial
Author: supervisor / owner (the owner completes the merge and runs the install run sheet).
Parent: none
Depends on: TASK-026
Parallel: no
Diagrams: none
Scope: Reports/Reviews/ (outside Workspace/, human-facing — the release-level review record); docs/PROJECT_STATUS.md; docs/INVENTORY.md
Satisfies: R-031, R-037
Done when: a fresh-context release-level review (one pass, fixes, a second pass) is recorded and its findings closed; the projects are paused; `bridge-install.py` runs and `bridge-check.py` is green on `~/.claude`; reAngle calibrates onto the new structure (its `Workflows:` line valid, no gate reopened) and resumes, and its field acceptance is met — after reAngle's first compaction under release B the hook names exactly one module read whole (visible in the transcript / `run/supervisor/`), its `Workflows:` line passes `workflow-check`, and one increment goes through the loop with no gate reopened; the video factory and the TDP calibrate and resume per the owner's standing pause/resume policy (one calibration each, none pausing).
