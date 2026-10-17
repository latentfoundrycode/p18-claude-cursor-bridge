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
| **Phase** | One of the values of the status file's `Phase:` line: intake, design, mockups, planning, configuration, building, done, changing. The first six are the workflow's phases in order; done is a finished project and changing a change cycle on one. This is the only meaning of "phase" on its own; the procedure a phase follows lives in one or more **phase modules**, which are named as such. |
| **Stage** | A section of the build plan; a **vertical slice** that works end to end and can be demonstrated. The owner's DPP "phases" are stages. |
| **Increment** | One delegable task with a stable ID (`TASK-nnn`), built in one builder run and passed through the gate. The owner's DPP "tasks" are increments; a DPP parent task is a **group** increment whose children are increments. |
| **Vertical slice** | A stage that crosses the layers a feature needs (interface, logic, storage) so the parts are proven to work together and the owner sees something run. Its opposite, a **horizontal** stage (one layer across many features), is rejected. |
| **Diagram-based planning** | Designing through the diagram catalogue: top-down, level by level; implementation detail only where it is load-bearing; every normative diagram enforced. |
| **Load-bearing** | An implementation detail that must be decided at planning because getting it wrong breaks correctness under concurrency, a security mechanism, data integrity, a budgeted hot path, an external protocol, or a place where the builder has already failed. Only load-bearing detail is diagrammed at Levels 4 and 5. |
| **Free implementation space** | Everything the brief and the normative diagrams leave to the builder. Reviewers do not fail a choice made inside it. |
| **Design regression** | Code drifting from a normative diagram without an objection. A review `REJECT`. |
| **Repo ignorance** | The builder's partial view of the project. Answered by the brief and its diagram slices, never by giving the builder control of the plan. |
| **Parallel increments** | Ready increments marked `Parallel: yes` with disjoint scopes whose **builders** run at the same time (run parameter `Parallel increments: on`), each builder in its own worktree. The supervisor never works inside a worktree: it processes each finished branch in its own checkout, one at a time, through the same gate. One writer per checkout. |

## Main and conditional workflows

| Term | Meaning |
|---|---|
| **Main workflow core** | The part of the main workflow every project reads whole, at every start, resume and calibration: the roles and the division of labour, the founding rules, the loop's shape, escalation and reporting, project state, and the standing rules that hold in every phase. It is not an extension point; no conditional workflow changes it. Today it is the sections of `supervisor.md` other than the sections that are phase modules. |
| **Phase module** | A procedure file of the main workflow, listed in the extension-point registry: intake, design, the interface phase, planning, run parameters, configuration, the delegation loop, the change cycle, reflection points and project end. A phase's value selects its module or modules (several phases take more than one, as the session-start hook's table maps them), read whole on entering the phase and at every calibration. Until a module is moved into a file of its own under `workflow/phases/`, its section of `supervisor.md` is the module (project end is today part of the Reflection points section). |
| **Extension point** | A named place in a phase module where any conditional workflow may add and, where the point accepts it, a type workflow or a sub-workflow may set; declared by its module and listed with the kinds of change it accepts in the extension-point registry (`workflow/extension-points.md`). A replacement targets a whole module instead, and only one the registry marks replaceable. |
| **Product type** | How a product reaches its user: where it runs, how it is delivered, and what its main interface is (a web app, a video game, a host extension). Each part has exactly one, fixed at intake, from the open list. |
| **Sub-type** | A narrower kind within one product type (a Roblox game within video games; a Claude Code extension within host extensions), with a workflow of its own because it changes a phase, a gate, a check or the tooling. A part has at most one sub-type, of its own product type. |
| **Trait** | A property that adds work whatever the product type (has screens, installable, spends money). A part may have any number, proposed at intake and settled at the design gate, from the open list. |
| **Conditional workflow** | The collective name for a type workflow, a sub-workflow or a trait addition: a small file that changes the main workflow only by adding at extension points or, for a type workflow or a sub-workflow, also by setting at a point that accepts it or replacing a whole phase module the registry marks replaceable; everything it does not mention is inherited. It can never remove a founding rule, weaken the merge gate, or skip the requirements register, the inventory or the reviews. |
| **Type workflow** | The main workflow adapted to one product type (`workflow/types/<type>.md`): it adds at named extension points, sets where a point accepts it, and may replace a whole phase module the registry marks replaceable. |
| **Sub-workflow** | A more detailed version of a type workflow for one sub-type (`workflow/types/<type>/<sub-type>.md`): it inherits its type workflow and changes only what differs: it adds at extension points, sets where a point accepts it, and may replace a whole phase module the registry marks replaceable, overriding its type workflow's replacement or setting where both change the same thing. |
| **Trait addition** | What one trait adds to the procedure (`workflow/traits/<trait>.md`), whatever the product type. A trait addition may only add, never replace or set, so any combination of traits composes. |
| **Add** | As a kind of change a conditional workflow makes: extra content at an extension point (questions, sections, diagram kinds, checks, brief constraints, stages, completion conditions, reflection items) beside what is already there. Additions from several conditional workflows apply together, in the order the core states. |
| **Replace** | As a kind of change a conditional workflow makes: a whole phase module substituted, only where the registry marks the module replaceable; only a type workflow or a sub-workflow may replace. |
| **Set** | As a kind of change a conditional workflow makes: a value the main workflow leaves open fixed, at an extension point that accepts it (the kind of performance budget, the delivery kind); only a type workflow or a sub-workflow may set. |
| **Open list** | Every product type, sub-type and trait, against which projects are classified (`workflow/open-list.md`): each entry with its key, name, definition and Written flag; product types and sub-types also with their default traits and their workflow name or sub-workflow name. Open to new entries by its own procedure; it also fixes the order trait additions apply in. |
| **Workflow name** | A product type's workflow named as the work rather than the product (`Host Extension Development`, `Game Development`), fixed in the open list and used in the status file's `Workflows:` line. |
| **Sub-workflow name** | A sub-type's workflow named for the kind of product its sub-type makes (`Claude Code Extension`, `Roblox Game`), as the open list fixes it, and written after the workflow name and an arrow in the `Workflows:` line. |
| **Workflow check** | `workflow-check.py`: the one-shot program that checks every conditional workflow against the open list and the extension-point registry, and a status file's `Workflows:` lines against the open list; `inventory-check.py` and `conformance-check.py` use its grammar check to judge a project's `Workflows:` line. In the workflow check itself an unwritten product type or sub-type fails (the pause at intake), and an unwritten trait is flagged and the work continues. |
| **Compaction-survival list** | The short list a phase module opens with, naming what a session in that phase must re-read after a compaction or a resume before its next action. The phase modules written in release B each open with one. |

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
