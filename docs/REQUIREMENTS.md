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
