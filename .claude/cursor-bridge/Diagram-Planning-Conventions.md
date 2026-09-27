# Diagram-Planning Conventions

How the bridge designs software through diagrams. Read by the supervisor at Phase 2 and at every calibration, by every `diagram-specialist`, by `plan-critic`, and by the reviewers when a brief names diagrams. Terms are those of `Glossary.md`.

The design of a project is its **Project Design Document**: the text of `docs/DESIGN.md` plus the **normative diagrams** in `docs/diagrams/`. The two do different jobs. The text carries what a diagram cannot: purpose, non-goals, rationale, the technology selection with its alternatives, constraints, budgets, failure modes, and the security context. The diagrams carry what prose lets slip: every component, connection, state, entity, and interaction, listed explicitly, in a form a machine can check. A requirement that was never drawn is easy to lose; a state that is not on the state machine is not built.

## 1. The three rules

1. **Top-down, level by level.** A diagram may refine only diagrams at its own level or a higher one (Level 1 is the highest). Each level's approved diagrams are fixed inputs to the next.
2. **Detail only where it is load-bearing.** Levels 1 to 3 describe what the system is and how it is put together. Levels 4 and 5 describe implementation, and a Level 4 or 5 diagram exists only where the supervisor decides a detail must be settled at planning because getting it wrong breaks one of: **concurrency** (correctness under concurrency), **security** (a security mechanism), **integrity** (data integrity, including every persistent schema), **performance** (a budgeted hot path), **protocol** (an external or inter-process protocol), or **prior-failure** (a place where a builder has already failed once). The diagram index records which, with one sentence. Everything not diagrammed is the builder's **free implementation space**; everything diagrammed constrains it deliberately.
3. **Normative only if enforced.** A diagram the code must conform to names what enforces it: a **deterministic check** (`check:components`, `check:schema <file>`), **tests** derived from it (`tests: <paths>`, each naming the diagram ID), or a named **review** item (`review: <what the reviewer checks>`). A diagram nothing enforces drifts silently, and a drifted diagram misleads every agent that trusts it. An object diagram is always enforced by tests: it specifies examples, and an example that is not a test verifies nothing.

## 2. The catalogue

Every project's diagram index lists **every** kind below, either selected (with at least one diagram) or omitted with a one-line reason, the way an interface project records an observability opt-out. Omitting is normal; forgetting is not. `Kind` is the key used in the index.

Within a level, **parallel** kinds may be drafted by separate specialists at once; a **mutually dependent** pair is drafted by one specialist in one run; otherwise kinds are drafted in the order listed.

### Level 1 — Functional and business workflows

| Kind | Diagram | Purpose | Normally selected | Mermaid | Enforced by |
|---|---|---|---|---|---|
| `use-case` | Use case diagram | Actors (people, external systems) and the goals the system must serve, from the requirements register | always | `flowchart` (convention below) | the requirement trace: every use case names its `R-` IDs, and `completion-check.py` proves them built |
| `operational-activity` | Operational activity diagram | Macro workflows and, for interface projects, navigation between screens, with parallel paths | interface projects; any multi-step workflow | `flowchart` | the requirement trace; every mockup screen is a node and every node that is a screen is in the mockup |

### Level 2 — Global infrastructure and network architecture

Order: the mutually dependent pair, then the parallel pair, then the state machine.

| Kind | Diagram | Purpose | Normally selected | Mermaid | Enforced by |
|---|---|---|---|---|---|
| `system-architecture` | System architecture diagram (pair with `deployment`) | Layers and how they interface across network or process boundaries: frontend, backend, workers, APIs, caches, stores, external services | any project with more than one process or any external service | `flowchart`, `C4Context`, `C4Container`, `architecture-beta` | review |
| `deployment` | Deployment diagram (pair with `system-architecture`) | Which artifacts run on which physical or virtual nodes; install locations; cloud boundaries | anything installed or deployed | `flowchart`, `C4Deployment`, `architecture-beta` | review; for installable software, the delivery conventions' checks |
| `context-dfd` | Context data flow diagram (parallel) | Data into, through, and out of the whole system; stores; external interfaces; **trust boundaries** | anything handling secrets, personal data, or untrusted input | `flowchart` (DFD convention below) | review; `security-auditor` checks every crossing |
| `inter-system-sequence` | Inter-system macro sequence diagram (parallel) | Time-ordered exchanges with external systems: API calls, webhooks, payloads | every external service integration | `sequenceDiagram` | tests replaying the service contract fixtures |
| `infrastructure-state` | Infrastructure state machine diagram | Lifecycle states of the whole multi-node environment: active, failover, maintenance | multi-node or cloud systems | `stateDiagram-v2` | tests; review |

### Level 3 — Application component architecture

Order: the component diagram, then the three parallel kinds.

| Kind | Diagram | Purpose | Normally selected | Mermaid | Enforced by |
|---|---|---|---|---|---|
| `component` | Component diagram | Modules and packages and which may depend on which; the backbone of design conformance | always, unless the software is one module (say so) | `flowchart`, `C4Component` | `check:components` — imports that cross a boundary the diagram does not draw fail |
| `inter-component-sequence` | Inter-component macro sequence diagram (parallel) | Time-ordered calls between components for each critical flow | every flow that crosses three or more components, or is asynchronous | `sequenceDiagram` | tests; review |
| `component-dfd` | Component-level data flow diagram (parallel) | Data movement across subsystems; where data is transformed and stored; trust boundaries inside the application | where `context-dfd` is selected and a component handles sensitive data | `flowchart` (DFD convention) | review; `security-auditor` |
| `component-state` | Component state machine diagram (parallel) | Runtime modes of a component or long-running job: idle, polling, processing, suspended, failed | anything with a lifecycle the user can see or that recovers from failure | `stateDiagram-v2` | tests naming the diagram ID and covering every state |

### Level 4 — Data structures and static code design (load-bearing only)

| Kind | Diagram | Purpose | Normally selected | Mermaid | Enforced by |
|---|---|---|---|---|---|
| `class` | Class diagram (pair with `erd`) | Classes, attributes, operations, relationships that must be built as drawn | only load-bearing parts: a domain model others depend on, an extension interface | `classDiagram` | review; tests |
| `erd` | Entity-relationship diagram (pair with `class`) | Persistent entities, attributes, keys, relationships | **every** project with a persistent structured store (load-bearing: integrity) | `erDiagram` | `check:schema <file>` against the committed schema dump |
| `domain-dfd` | Domain-level data flow diagram | How data is transformed and routed through code-level domains to its tables | where a transformation is load-bearing (money, units, redaction) | `flowchart` (DFD convention) | tests; review |

### Level 5 — Runtime execution logic (load-bearing only)

Order: the object diagram, then the three parallel kinds.

| Kind | Diagram | Purpose | Normally selected | Mermaid | Enforced by |
|---|---|---|---|---|---|
| `object` | Object diagram | Concrete instances at one moment, specifying an example that verifies the class diagram | where the class diagram is subtle enough that an example must be pinned | `classDiagram` or `flowchart` | **tests only**: the example becomes a fixture |
| `micro-sequence` | Micro sequence diagram (parallel) | Method-level call order between instances | concurrency protocols, transaction boundaries, lock ordering, retry and idempotency logic | `sequenceDiagram` | tests; review |
| `algorithmic-activity` | Algorithmic activity diagram (parallel) | Step-by-step control flow inside one function or job: loops, branches, parallel steps | algorithms whose branches are requirements (budget gates, reconciliation) | `flowchart` | tests covering each branch; review |
| `object-state` | Object state machine diagram (parallel) | Lifecycle states of one entity instance and the triggers between them (an order: pending, paid) | every entity whose status field drives behaviour | `stateDiagram-v2` | tests naming the diagram ID and covering every state |

## 3. Files

**The index** — `docs/diagrams/INDEX.md`, one table, parsed by `diagram-check.py`:

```markdown
| ID | Level | Kind | Status | File | Refines | Realizes | Enforced by | Why |
|---|---|---|---|---|---|---|---|---|
| D-001 | 1 | use-case | selected | docs/diagrams/D-001-use-cases.md | - | R-001, R-002, R-003 | review: every use case traced | - |
| D-004 | 3 | component | selected | docs/diagrams/D-004-components.md | D-002 | R-001, R-012 | check:components | - |
| D-009 | 4 | erd | selected | docs/diagrams/D-009-erd.md | D-004 | R-005 | check:schema docs/schema.sql | integrity: the run ledger is the source of truth for spend |
| - | 2 | infrastructure-state | omitted | - | - | - | - | single process on one machine; no environment states |
```

- `ID`: `D-001`, `D-002`, … — stable, never reused, never renumbered. Omitted rows use `-`.
- `Refines`: the diagram IDs it refines (same or higher level); `-` for none. Sequence diagrams must refine the structural diagram their participants come from.
- `Realizes`: the requirement IDs it serves; every selected diagram realizes at least one.
- `Enforced by`: one or more of `check:components`, `check:schema <file>`, `tests: <path>, <path>`, `review: <item>`, separated by `;`.
- `Why`: for a selected Level 4 or 5 diagram, the load-bearing category word (`concurrency`, `security`, `integrity`, `performance`, `protocol`, `prior-failure`), a colon, and one sentence; for an omitted row, the reason; otherwise `-`.

**A diagram file** — `docs/diagrams/D-nnn-<slug>.md`: a heading with the ID and kind, optional notes, and **exactly one** fenced `mermaid` block. Agents read the text; people see a picture wherever Mermaid renders: GitHub renders `mermaid` fences in Markdown files, and Typora renders them once *Diagrams* is enabled in Preferences → Markdown. Typora 1.13 bundles Mermaid 11.13, so a diagram type introduced later (such as the native `usecase-beta` of Mermaid 12) shows there as text; the catalogue therefore uses notations that render in both.

**Identifiers.** Every element that another diagram, the element map, a brief, or a test refers to has a plain identifier: letters, digits, underscores, starting with a letter (`key_store`, `SettingsView`). Labels carry the human wording: `key_store[Key store]`, or with the shape syntax `key_store@{ shape: cyl, label: "Key store" }`. Two Mermaid pitfalls are rules here: never name an element `end` (it breaks flowcharts and state machines; `diagram-check.py` fails it), and always put spaces around links (`a --> ops`, never `a-->ops`, because a node starting with `o` or `x` right after a link is read as a circle or cross edge).

## 4. Conventions per notation

**Flowchart as a use case diagram.** Mermaid 12 has a native use case type (`usecase-beta`), but it does not render in Typora's bundled Mermaid, and the owner reads Level 1 diagrams at the design gate; so use cases are drawn as a flowchart until the owner's viewers render the native type. `flowchart LR`; actors are nodes whose identifier starts with `actor_` (`actor_owner([Owner])`); use cases are nodes whose identifier starts with `uc_`, and **each use case label names its requirement IDs** (`uc_add_key(["Add an API key R-012"])`); the system boundary is a subgraph. Edges connect actors to use cases.

**Flowchart as a data flow diagram.** External entities `ext_…`, processes `p_…`, stores `ds_…` drawn as cylinders (`ds_keys[(Encrypted key store)]`) or with the data-store shape (`ds_keys@{ shape: datastore, label: "Encrypted key store" }`), flows as labelled edges naming the data. **Trust boundaries are subgraphs whose identifier starts with `tb_`**; every edge that crosses a `tb_` subgraph is a trust-boundary crossing that `security-auditor` checks for validation, authentication, and redaction.

**Flowchart as a component diagram.** Nodes are components; subgraphs group them into layers. **An edge `a --> b` means component `a` may depend on `b`** (import it, call it); `<-->` allows both directions; an undirected link grants nothing. An edge to or from a subgraph applies to every component inside it. The file carries an **element map** above the diagram:

```markdown
| Element | Paths |
|---|---|
| key_store | app/secrets/** |
| settings_ui | frontend/src/settings/** |
```

`check:components` scans the project's tracked source files (Python, JavaScript, TypeScript, Vue, Svelte; tests excluded), resolves each import to a file, maps both ends to elements, and fails every import between two different elements that the diagram does not allow. Files matching no element are reported, so the map stays complete. A dependency the diagram does not draw is either an objection (the design is wrong) or a design regression (the code is wrong); it is never silently accepted.

**Sequence diagrams.** `sequenceDiagram` with explicit `participant` declarations using the identifiers of the refined diagram (`participant key_store`). External people are declared with `actor`; they need not exist in the refined diagram. A micro sequence participant names its class in the alias: `participant l as l:RunLedger` (a colon cannot appear in a participant identifier, because it starts the message text); the class part must exist in the refined class diagram. A name listed in a `%% external: name, name` comment line is exempt from the refines check, for a participant that deliberately lives outside the refined diagram.

**State machines.** `stateDiagram-v2`, `[*]` for start and end, `s1 --> s2 : trigger` for transitions. When enforced by tests, every state identifier appears in the enforcing test files, and those files name the diagram ID: that is how "every state is exercised" is checked.

**Entity-relationship diagrams.** Entity identifiers are the **table names** (case does not matter; no aliases, since an alias would hide the table name) and attribute names are the column names, so the diagram can be compared with the real schema. Cardinalities may be symbolic (`runs ||--o{ reservations : holds`) or in words (`runs 1 to zero or more reservations : holds`). `check:schema <file>` reads the committed schema dump (a SQL file of `CREATE TABLE` statements, regenerated by a project script or test the same way the command reference is, and checked for currency in CI), and fails on an entity with no table, a table with no entity, or an attribute and column that differ.

## 5. How the design is drafted

1. **Select.** The supervisor writes the index: every catalogue kind selected or omitted with a reason, IDs assigned, `Refines` and `Realizes` filled from the requirements register, `Why` for every Level 4 and 5 selection.
2. **Draft top-down.** For each level in turn, the supervisor runs `diagram-specialist` subagents: parallel kinds at once, a mutually dependent pair in one run, each given the level's upstream approved diagrams, its register rows, the design text, and (for Levels 4 and 5) its load-bearing reason.
3. **Integrate.** The supervisor reconciles the drafts: identifiers, boundaries, contradictions, open points. A specialist's objection is resolved here or escalated per §7. Then `diagram-check.py --mode design` must pass.
4. **Critique.** `plan-critic` reviews the design text and the diagrams together: selection and omissions, load-bearing reasons (and load-bearing detail left undrawn), enforcement, contradictions between diagrams that the check cannot see, trust boundaries.
5. **Approve.** The owner approves the design with its diagrams. The Level 1 diagrams state what the software does, so the owner reads those; the rest are technical and are presented as such.

## 6. How diagrams are used during the build

- Every build-plan increment names the diagrams it touches (`Diagrams:`), and its brief carries those **slices**: the diagram files and the element identifiers the increment implements, with the constraint to conform and to raise an objection rather than deviate.
- `diagram-check.py --mode code` runs at step 4 of the loop on every increment (component and schema conformance) and at every stage close; `--mode done` at project end also requires every enforcing test file to exist.
- Reviewers check the diff against the diagrams its brief names. A deviation without an objection is **design regression** and a `FAIL`; a choice inside the free implementation space is not a finding.
- The stage-close refactoring pass treats normative diagrams as constraints. A candidate that would change one is a design change: it goes through §7, never in as a quiet edit.

## 7. Objections and bottom-up escalation

A builder, reviewer, auditor, or specialist that finds a normative diagram unworkable raises an **objection**; the item halts until it is resolved. It is resolved at the lowest level with the authority to resolve it:

| What the objection touches | Resolved by | Through |
|---|---|---|
| A choice inside the free implementation space | the builder itself | autonomous resolution; not an objection |
| A brief detail or a Level 4 or 5 diagram | the supervisor | revise the diagram, re-run `diagram-check.py`, record the revision as a Decisions row in the inventory, re-brief |
| A Level 2 or 3 diagram | the supervisor with the design critique | specialists redraw the affected diagrams, `plan-critic` re-reviews them, `diagram-check.py`, a Decisions row; an escalation to the owner only if the change carries a user-level consequence (cost, privacy, licensing, lock-in, delivery) |
| A Level 1 diagram or a requirement | the owner | the design gate: it changes what the software does |

Every revision lands in the change record: the diagram's own git history, the dated Change section of `DESIGN.md`, and the version.
