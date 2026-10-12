### 6.2 The structure

Every project runs the main workflow. What differs by product is held in three layers of conditional workflows, and each layer inherits everything it does not mention from the layers above it:

| Layer | Holds | Read when |
|---|---|---|
| **The main workflow's core** | The roles and the division of labour; the founding rules; the loop's shape; escalation and reporting; project state; the standing rules that hold in every phase | Always, whole, at every start and calibration |
| **Phase modules** | The procedure for each phase: intake, design, the interface phase, planning, run parameters, configuration, the delegation loop, the change cycle, reflection points and project end | The module for the current phase, whole, on entering the phase and at every calibration |
| **Type workflow** | For one product type: its changes at named extension points | The part's type workflow's changes to the current phase, whole, alongside the phase module |
| **Sub-workflow** | For one sub-type: a tailored, more detailed version of its type workflow, changing only what differs for that sub-type | Alongside its type workflow, when the part has a sub-type |
| **Trait additions** | For one trait: what it adds, whatever the product type | The additions of the part's traits to the current phase |

The supervisor never reads a phase it is not in, or a conditional workflow that does not apply. A project's status file records, for each part (section 7), its product type, sub-type and traits on a `Workflows:` line, and the project's phase on the `Phase:` line; together they name exactly what a resumed session must read. A project with one part has one `Workflows:` line.

### 6.3 Product types, sub-types and traits

*Revised 2026-10-04 after the plan review (R11). Awaiting the owner (decision 6): two definitions change, two sub-types are added, and all three running projects are classified.*

**A product type answers one question: how does the product reach its user?** That covers what the user meets it through, how it is delivered, and where it runs. Each part of a project has exactly one product type, and at most one of its sub-types. **A trait is a property that adds work whatever the product type:** a settings screen, calls to paid services, a background server, speed targets. A part may have any number of traits.

**When they are decided.** The product type and sub-type are fixed at intake, because every phase that follows depends on them, and a new product type pauses the project (6.7). Traits are proposed at intake and settled at the design gate, because several of them only emerge from the design (whether the product needs accounts, for instance). A product type's default traits are proposals too, settled at the same gate.

**What the review found.** The earlier definitions folded two things into one: what the user meets the product through, and where the product runs. The video factory runs on the owner's own computer and is used in a browser; by the plan's own test (does it keep data for its users?) it was a web app, and the plan called it a pipeline. A project that fits two product types equally pauses (6.7), so release B's calibration would have paused it. reAngle was not classified at all. And the TDP's main interface is not its command line but a contract other software calls. The definitions below separate the two: the product type follows **what the user meets**, and a sub-type says where it runs when that changes the work.

**The running projects, classified:**

| Project | Product type → sub-type | Traits |
|---|---|---|
| The Short-Form Video Factory | Web app → local web app | has screens, installable, long-running process, external services, spends money, AI models |
| reAngle | Web app → local web app | has screens, installable, long-running process, external services, spends money, AI models |
| The TDP | Software on your own computer → local service | installable, long-running process, external services, spends money, AI models; performance budgets again once its code map carries one |
| The bridge itself | Host extension → Claude Code extension | installable |

reAngle also deploys code of its own to a cloud platform (its GPU jobs), and one of its recorded failures happened exactly there. No product type or sub-type carries that step, so its checks (the deployed layout tested before any deployment, every remote wait bounded) are written into the *external services* trait in release B (second pass, P11).

**The lists are open.** Nobody can foresee every product type or trait, so each entry carries a definition: a project is classified against the definitions, and a product type or trait that fits none of them is recognised as new rather than forced into the nearest entry (6.7).

**Product types.** Each product type's workflow has a **workflow name** and each sub-type's a **sub-workflow name**, fixed here, used in the status file's `Workflows:` line and in the progress graph's header (7.8); the owner chose the game's on 2026-10-01 and the others follow the same shape (the type's name, as a name for the work rather than the product).

| Product type | Definition | Sub-types | Default traits |
|---|---|---|---|
| Mobile app | Installed on a phone or tablet from an app store | Android; iOS later | has screens, installable |
| Web app | Used in a browser; keeps data for its users (accounts, saved state, runs, orders). Without a sub-type it runs on a server the owner operates and is delivered by deployment | **Local web app:** installed and run on the user's own computer and opened in their browser at a local address; it is delivered by an installer instead of a deployment and has a local server to start and stop | has screens, personal data; the local sub-type has installable and long-running process instead of personal data |
| Website | Used in a browser; presents content; keeps no data for its users | — | has screens |
| Software on your own computer | Installed and run on the user's own computer, and met through something other than a browser page | GUI (a window) · CLI (a terminal) · pipeline (nothing: it runs jobs unattended and its output is files or records) · **local service** (other software on the same computer calls it through a protocol, such as an MCP server; its interface is a contract) | installable; the GUI sub-type adds has screens; the local service adds long-running process |
| Backend service | Runs on a server, has no screen, serves other software over a network | — | long-running process |
| Library | Code that other programs include; delivered as a package | — | — |
| Video game (workflow name **Game Development**) | Built around a real-time play loop | Roblox (sub-workflow name **Roblox Game**); a game with no sub-type runs under the Game Development workflow alone | has screens, performance budgets; the Roblox sub-type adds multiplayer |
| Host extension | Runs inside another application, through that application's extension points | Claude Code extension (the bridge itself) · browser extension | installable |

To tell a website from a web app at intake, one question decides: **does it keep data for its users** (accounts, saved progress, runs, orders)? If yes, it is a web app. To tell a web app from software on your own computer: **does its user meet it in a browser?** If yes, it is a web app, wherever it runs.

**Traits:**

| Trait | Definition | Status |
|---|---|---|
| Has screens | Shows a visual interface to a person | Exists today, as the bridge's conditions for interface projects |
| Installable | Delivered as something the user installs | Exists today |
| Performance budgets | Speed, size or frame-rate targets are requirements | Exists today |
| External services | Depends on services run by others | Exists today |
| Spends money | Its actions cost real money (paid APIs, purchases) | Defined; **written in release B**, because all three running projects carry it |
| Long-running process | Keeps a process running between uses (a server, a watcher) | Defined; **written in release B**, because all three running projects carry it |
| AI models | Its results come from models, so correctness is judged by evaluation rather than by exact tests | Defined; **written in release B**, because all three running projects carry it |
| Personal data | Holds data about people: accounts, sign-in, privacy, deletion | Defined; written when a project first needs it |
| Multiplayer | Several people interact live through a server | Defined; written with the Roblox sub-workflow in release E, whose default trait it is |

### 6.4 Extension points

A conditional workflow may change the procedure only at extension points declared in the phase modules. The initial list, to be refined during implementation:

| Phase | Extension points |
|---|---|
| Intake | Additional questions; additional requirement sources; the product type's target environment |
| Design | Additional design sections; additions to the diagram catalogue; mandatory diagram kinds |
| Interface phase | The main workflow holds its variants once, one per kind of interface a part can have: mockups for screens, command design for commands, contract design for a protocol other software calls, a playable prototype for play. A part's interface phase runs the variant of every kind it has; type workflows, sub-workflows and the trait *has screens* add the variants that apply, and a type workflow or sub-workflow may replace the phase with its own |
| Planning | Mandatory stages (such as a packaging stage); additions to the plan critic's lenses |
| Run parameters | Additional run parameters |
| Configuration | Additional configuration items, tools and checks |
| The delegation loop | Additional checks at the inspect and test steps; additional brief constraints |
| Definition of done | Additional completion conditions |
| Delivery | The delivery procedure (installer, store package, web deployment, installation into a host) |
| Reflection points | Additional reflection items |

### 6.5 What each layer can do

Each change a conditional workflow makes is one of three kinds:

- **Add**: extra questions, sections, diagram kinds, checks, brief constraints, stages, completion conditions, reflection items. Additions from several conditional workflows are applied together, in a stated order.
- **Replace**: a whole phase module, only where the phase declares that it may be replaced.
- **Set**: a value the main workflow leaves open, such as the kind of performance budget (page load, frame time) or the delivery kind.

**Only type workflows and sub-workflows may replace or set; trait additions may only add** (agreed 2026-09-29). Each part follows one path down the tree of product types and sub-types, so two replacements can never collide; trait additions only add, so any combination of traits composes cleanly. A product that looks like a hybrid is therefore never improvised: it is declared, as one product type with its sub-type plus a list of traits, and the workflow check verifies it.

**A sub-workflow inherits its type workflow** and changes only what differs, at the same extension points. It may override its type workflow's replacement or setting: if the video game type workflow replaces mockups with a playable prototype, the Roblox sub-workflow may replace that prototype phase again. That is inheritance, not a collision.

**A sub-type must earn its place.** It must change a phase, a gate, a check or the tooling. A difference that changes none of these (a puzzle game against a shooter) is a design choice and belongs in the project's design document. A Roblox game earns its sub-type: a different editor, language, testing and publishing.

**Siblings are exclusive:** a part is a Roblox game or a Unity game, never both. **Two levels are enough** (a product type and its sub-types); a third needs evidence from a real project.

A conditional workflow can never remove a founding rule, weaken the merge gate, or skip the requirements register, the inventory, or the reviews. Those belong to the core and are not extension points.

**Today's interface conditions stay together** (revised 2026-10-04, R11). The earlier text split them: the mockup phase, as a replacement, was to move out of the trait *has screens* and be selected by product types, leaving the trait with the interface rules, the design auditor and the tests of the running interface. But the design auditor, and the design detector in the merge gate, both judge against the approved mockup and the design document the mockup phase writes. A project given the trait without the phase would have kept a reviewer with nothing to review against, and changes to the video factory's screens would no longer have passed the owner's visual approval. So the mockup variant is an addition, not a replacement: the interface phase runs one variant per kind of interface the part has (6.4), and the trait *has screens* adds the mockup variant, sized to the screens there are, together with the frozen interface rules, the design auditor and the tests of the running interface. The rule that trait additions only add is kept, and a settings tab gets a small mockup rather than none.
