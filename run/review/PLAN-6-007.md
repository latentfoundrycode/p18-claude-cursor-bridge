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

### 6.6 Where it keeps its promises: the workflow check

A deterministic check, run at every bridge release and every calibration:

- every change in every conditional workflow targets an extension point that exists;
- a replacement or a setting appears only in a type workflow or a sub-workflow, and a replacement targets a phase declared replaceable;
- trait additions only add;
- every sub-workflow names a type workflow that exists;
- every project's `Workflows:` lines name, for each part, exactly one product type, at most one of its sub-types, and traits, all present in the open list; a product type or sub-type whose workflow is not yet written fails the check (6.7).

A bridge release that renames an extension point therefore fails loudly, instead of silently breaking a conditional workflow nobody is looking at.

### 6.7 When something does not fit

At intake, the supervisor classifies each part against the definitions in 6.3 (decided 2026-09-29):

- **A new product type or sub-type pauses the project.** When a part fits no product type, fits two equally, or fits one whose workflow is defined but not yet written, the supervisor stops before design and sends the owner to the bridge's maintainer with its reasons. The maintainer writes the workflow with the owner (6.10), the release goes out, the project calibrates, and the supervisor resumes.
- **A new trait is flagged, and the work continues.** Traits only add, so the main workflow and the part's product type still cover everything essential. The supervisor writes the extra handling into the project's design, flags it at the design gate, where the owner may still choose to pause, and puts it forward at the promotion pass at project end, from which the maintainer may write it as trait additions. The same holds for a trait that is defined but not yet written.

### 6.8 The first conditional workflows

The first trait additions come from the bridge itself, from the conditions already scattered in the supervisor's instructions. They are not new rules, only moved into their own files:

| Trait | What it gathers |
|---|---|
| **Has screens** (today's conditions for interface projects) | The mockup variant of the interface phase with its design tooling; the frozen interface rules; the design auditor; the observability tests of the running interface (6.5) |
| **Installable** | The delivery conventions: installers, install scripts, the command reference, the packaging stage, installer verification |
| **Performance budgets** | Budgets at intake, their mechanisms in the design, benchmarks, the benchmark floor, the performance lens |
| **External services** | Contract capture before an adapter is built; replay of recorded responses |

Three more are written new in release B, because every running project carries them (revised 2026-10-04, R11): **spends money** (an approval before any paid action, the estimate against the worst case, a cap, the platform and account named), **long-running process** (start, stop and health; nothing left running; the conditions of 8.1) and **AI models** (evaluation sets and thresholds in place of exact tests; pinned models; recorded outputs).

Beside them, release B writes the type workflows the running projects need, so that none of them pauses at its calibration: web app with its local web app sub-type (the video factory, reAngle), software on your own computer with its local service sub-type (the TDP), and host extension with its Claude Code extension sub-type (the bridge itself, section 15). The local service's contract design and the CLI's command design (6.9) are new text; they apply to a project from its next design phase or change cycle, and calibration reopens no gate. Every other product type is written when the first project of that type arrives (6.7).

After this move the main workflow's text shrinks for every project, and each project reads only the conditional workflows that apply to it.

### 6.9 Notes on particular product types

These are not specifications; the owner specifies each type workflow when it is written.

- **Video game, and Roblox.** Specified in 6.12: the playable prototype and playtesting from the first playable on, the game diagram kinds, concept sheets and the style guide, the asset loop with its roster and admission gate, environments built blockout-first, the scoped design revision, and the Roblox sub-workflow (Rojo, Open Cloud tests, the Studio MCP server, publishing). Written by release E.
- **Mobile app.** Android first. iOS apps can only be built on a Mac; the iOS sub-type is written when the owner builds on one.
- **Software on your own computer → CLI.** Its interface phase runs **command design**: the commands, their help text, and their output formats.
- **Software on your own computer → local service.** Its interface phase runs **contract design**: the protocol's operations, their inputs, outputs and errors, and how the contract is versioned, written as a contract file that tests enforce. Where the service also has administrative commands, as the TDP does, those get command design.
- **Web app → local web app.** Mockups as for any web app; delivery is an installer or install script and a local server the user starts and stops, in place of a deployment.
- **Host extension.** The host's rules are not the project's: the host decides how its extension points behave and changes them with its updates. For the bridge, Claude Code decides how hooks, commands and permissions behave, and most of the bridge's worst pitfalls came from exactly that: the Stop hook's semantics, the permission allowlist not recognising `git -C`, Typora's older Mermaid. Its type workflow adds the host's behaviour recorded as verified facts with the version that was checked; tests that run inside the real host, not only in isolation; and delivery as installation into the host. Browser extensions, and later editor plugins, are its siblings.

### 6.10 Adding or changing a conditional workflow

The procedure, once the framework exists:

1. The owner describes the product type, sub-type or trait and what should differ, in plain words, in the maintainer's session; a project paused for a new product type (6.7) brings its supervisor's reasons.
2. The maintainer writes the conditional workflow: which extension points it uses, and what it adds, replaces or sets at each (trait additions only add). Its definition joins the open list.
3. The workflow check passes.
4. The release's changelog names the conditional workflow, and calibration applies it to running projects of that product type by phase, reopening no gate.

Changing an existing one is the same, editing only its file. A project's supervisor never writes a conditional workflow; it may propose one through the promotion pass at project end.

### 6.11 Where the files live

The command stays `/supervisor`; with it the owner starts the head supervisor (section 7). Proposed layout under the installed bridge:

| File | Holds |
|---|---|
| `~/.claude/commands/supervisor.md` | The main workflow's core |
| `~/.claude/cursor-bridge/workflow/phases/<phase>.md` | One phase module per phase, with its extension points declared |
| `~/.claude/cursor-bridge/workflow/types/<product-type>.md` | One type workflow per product type |
| `~/.claude/cursor-bridge/workflow/types/<product-type>/<sub-type>.md` | One sub-workflow per sub-type |
| `~/.claude/cursor-bridge/workflow/traits/<trait>.md` | The trait additions of one trait |
| `~/.claude/cursor-bridge/workflow/open-list.md` | Every product type, sub-type and trait with its definition, and whether its workflow is written |
| `~/.claude/cursor-bridge/workflow/aggregate.md` | The aggregate workflow, read only by the head supervisor of a project with several parts (7.5) |
| `~/.claude/cursor-bridge/workflow-check.py` | The workflow check |

