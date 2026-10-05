# Claude-Cursor Bridge — Glossary

One term per thing. The supervisor, the subagents, and every brief use these terms in these senses; a term used in another sense is a defect in the text that uses it. The owner's own planning vocabulary is mapped here too, so a document the owner brings is read correctly.

## Artifacts

| Term | Meaning | Where it lives |
|---|---|---|
| **Initial Design Draft** | The owner's own description of the software, written before intake questioning. Input to Phase 1; never rewritten by the supervisor. | `Documents/` (the owner's file) |
| **Requirements register** | Every requirement with a stable ID (`R-001` …): from intake, from any requirements document the owner supplies (their *User Requirements Document*), from the design, and every screen and state of the approved mockup. What "done" is measured against. | `docs/REQUIREMENTS.md` |
| **Project Design Document** | The whole design: the design text plus every normative diagram. | `docs/DESIGN.md` + `docs/diagrams/` |
| **Target environment** | The platform, operating system, hardware, and runtime the software runs on (the owner's *Hardware Details*). | a section of `docs/DESIGN.md` |
| **Technology selection** | The chosen technologies, each with the alternatives considered and why it won (the owner's *Suggested Technologies List*). | a section of `docs/DESIGN.md` |
| **Diagram index** | The per-project selection from the diagram catalogue: every catalogue kind selected or omitted with a reason, and for each selected diagram what it refines, realizes, and how it is enforced. | `docs/diagrams/INDEX.md` |
| **Normative diagram** | A diagram the code must conform to. A diagram is normative only if something enforces it: a deterministic check, tests derived from it, or a named review item. | `docs/diagrams/D-nnn-*.md` |
| **Build plan** | Stages of increments with explicit placement fields (the owner's *Development Phases Plan*). | `docs/BUILD_PLAN.md` |
| **Brief** | The handoff to the builder for one increment: objective, requirements satisfied, diagram slices, scope, acceptance criteria, constraints. What the owner's notes call a *contract* between planner and builder is, in the bridge, the brief. | `handoff/TASK-nnn.md` |
| **Contract tests** | Tests frozen before the build that the increment must turn green ("RED contract"). | the project's test suite |
| **Service contract** | The recorded real behaviour of an external service, captured before an adapter is built. | contract fixtures |
| **Change record** | What changed, per version: behaviour (`CHANGES.md`), design (the dated Change sections of `DESIGN.md` and the diagrams' git history), and the version number (the owner's *Software Development Record*). | `docs/` |
| **Inventory** | What the software is right now: Features, Resources, Decisions, Deferred. | `docs/INVENTORY.md` |

## Workflow

| Term | Meaning |
|---|---|
| **Phase** | One of the bridge's workflow phases: intake, design, mockups, planning, configuration, building. This is the only meaning of "phase". |
| **Stage** | A section of the build plan; a **vertical slice** that works end to end and can be demonstrated. The owner's DPP "phases" are stages. |
| **Increment** | One delegable task with a stable ID (`TASK-nnn`), built in one builder run and passed through the gate. The owner's DPP "tasks" are increments; a DPP parent task is a **group** increment whose children are increments. |
| **Vertical slice** | A stage that crosses the layers a feature needs (interface, logic, storage) so the parts are proven to work together and the owner sees something run. Its opposite, a **horizontal** stage (one layer across many features), is rejected. |
| **Diagram-based planning** | Designing through the diagram catalogue: top-down, level by level; implementation detail only where it is load-bearing; every normative diagram enforced. |
| **Load-bearing** | An implementation detail that must be decided at planning because getting it wrong breaks correctness under concurrency, a security mechanism, data integrity, a budgeted hot path, an external protocol, or a place where the builder has already failed. Only load-bearing detail is diagrammed at Levels 4 and 5. |
| **Free implementation space** | Everything the brief and the normative diagrams leave to the builder. Reviewers do not fail a choice made inside it. |
| **Design regression** | Code drifting from a normative diagram without an objection. A review `REJECT`. |
| **Repo ignorance** | The builder's partial view of the project. Answered by the brief and its diagram slices, never by giving the builder control of the plan. |
| **Parallel increments** | Ready increments marked `Parallel: yes` with disjoint scopes whose **builders** run at the same time (run parameter `Parallel increments: on`), each builder in its own worktree. The supervisor never works inside a worktree: it processes each finished branch in its own checkout, one at a time, through the same gate. One writer per checkout. |

## Roles

| Term | Meaning |
|---|---|
| **Owner** | The person the software is built for; decides what it does and is, never how it is built. |
| **Supervisor** | The single main agent that designs, plans, delegates, reviews, and merges. "Supervisor" means only this role. |
| **Specialist** | A subagent that drafts one diagram, or one mutually dependent pair, for the supervisor to integrate (`diagram-specialist`). |
| **Auditor** | A specialised reviewer: `plan-critic`, `security-auditor`, `design-auditor`, `refactor-scout`, and the performance lens. The owner's notes call these *specialized supervisors*. |
| **Builder** | The coding agent (Cursor) that implements one brief in one checkout. |
| **Reviewers** | Review A (`diff-reviewer`, Claude) and Review B (a third model family through Cursor). |

## Disputes

| Term | Meaning |
|---|---|
| **Objection** | Any dispute raised upward that halts progress on the item until it is resolved: an auditor or reviewer to the supervisor (a blocking finding), the builder to the supervisor (stop and report), a specialist to the supervisor (a conflict with an upstream diagram), the supervisor to the owner (an escalation). |
| **Autonomous resolution** | An issue settled by the agent that found it, because it has the authority to settle it. Not an objection. |
| **Bottom-up escalation** | A problem that cannot be resolved at its own level reopens the level above through that level's gate: brief and Level 4–5 detail → the supervisor; Level 2–3 architecture → the supervisor with the design critique; Level 1 and the requirements → the owner. |

## Principles

| Term | Meaning |
|---|---|
| **Berman's dual-agent principle** | The strongest model plans and reviews, where input tokens dominate; a sufficient model builds, where output tokens dominate. The model roster applies it. |
