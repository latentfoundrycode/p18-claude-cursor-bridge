# The extension-point registry

This file is the canonical list of the extension points: the named places where a conditional workflow (a type workflow, a sub-workflow or a trait's additions) may change the main workflow (Restructuring Plan §6.4, §6.5). It names, for each point, the phase module that declares it, and for each phase module whether a type workflow or sub-workflow may replace it. A conditional workflow that changes anything at a point not listed here, sets a value at a point whose Changes do not include `set`, or replaces a phase not marked replaceable here, fails `workflow-check.py`. A point is added, renamed or removed only by the bridge's maintainer, in a bridge release, in the same change as the phase module that declares it; the workflow check then fails every conditional workflow still naming an old point (§6.6), loudly rather than silently. A project's supervisor never changes this file.

What no point offers stays with the core: a conditional workflow can never remove a founding rule, weaken the merge gate, or skip the requirements register, the inventory or the reviews (`supervisor.md`, "Main and conditional workflows").

## How this file is read

`workflow-check.py` reads the two tables below and nothing else in this file; the prose is for the reader. Each table is the first table after its heading (`## Phase modules`, `## Extension points`), its rows running to the first line that is not a table line; its columns are found by their header names; no cell contains a `|`.

- **Module** — the phase module's key and the base name of its file, `workflow/phases/<module>.md` (§6.11). Until the phases move into files of their own, each module is its phase's section of `supervisor.md`.
- **Phase** — the phase in plain words; for a point, the row of §6.4's table it comes from (Definition of done and Delivery are rows of their own there, declared by the project-end module).
- **Replaceable** — `yes` where a type workflow or sub-workflow may replace the whole module with its own, else `no`. A trait never replaces (§6.5).
- **Key** — the point's identifier: its module's key, a dot, then the point's own name in lowercase letters, digits and hyphens. Unique; a conditional workflow names a point by it.
- **Point** — what may be changed there, in plain words.
- **Declared by** — the key of the phase module that declares the point; always a module of the first table. A point's phase is replaceable exactly when the module that declares it is, so the flag is read from that module's row and stated once.
- **Changes** — the kinds of change the point accepts: `add`, or `add, set` where the main workflow leaves a value open there for a type workflow or sub-workflow to set (§6.5). Every point accepts additions, from type workflows, sub-workflows and traits alike; at a point that holds a value, an addition adds to what is asked or recorded about that value (a further question about the target environment), never a second value.
- **Applies** — `part` where an addition is made for each part that has the conditional workflow; `project` where the thing it adds exists once for the whole project, so an addition two parts share is made once, in the place of the first part, in the status file's order, that has the conditional workflow. The core's order ("The order additions apply in") governs every point; its rule that a shared conditional workflow's additions apply to every part that has it, each in that part's own place, is the rule for `part` points, and a `project` point is the one exception, as stated here (`supervisor.md` is to cite it when the core is carved, BUILD_PLAN TASK-010).

## Phase modules

| Module | Phase | Replaceable |
|---|---|---|
| intake | Intake | no |
| design | Design | no |
| interface | Interface phase | yes |
| planning | Planning | no |
| run-parameters | Run parameters | no |
| configuration | Configuration | no |
| delegation-loop | The delegation loop | no |
| change-cycle | The change cycle | no |
| reflection | Reflection points | no |
| project-end | Project end | no |

The interface phase is the one replaceable module (§6.4): the main workflow holds its variants once, one per kind of interface a part can have, and a type workflow or sub-workflow may replace the phase with its own; a sub-workflow may replace its type workflow's replacement again (§6.5). A replacement keeps the points of the module it replaces, without declaring them again under its `## Replace` heading, so every conditional workflow's additions at those points still apply to it, in the core's order: the type workflow's, the sub-workflow's and each trait's, such as the trait *has screens* adding the mockup variant at `interface.variants` (§6.5, "Today's interface conditions stay together"). The change cycle declares no points of its own: it runs the other phases' modules again for the change, and their points apply there; its module has no `## Extension points` section.

## Extension points

| Key | Phase | Point | Declared by | Changes | Applies |
|---|---|---|---|---|---|
| intake.questions | Intake | Additional questions | intake | add | part |
| intake.requirement-sources | Intake | Additional requirement sources | intake | add | part |
| intake.target-environment | Intake | The product type's target environment | intake | add, set | part |
| intake.budget-kind | Intake | The kind of performance budget the part is measured by (page load, frame time); the kind is the value set | intake | add, set | part |
| intake.delivery-kind | Intake | The kind of delivery the part ends in, one of the delivery kinds below; the kind is the value set | intake | add, set | part |
| design.sections | Design | Additional design sections | design | add | part |
| design.diagram-catalogue | Design | Additions to the diagram catalogue | design | add | project |
| design.mandatory-diagrams | Design | Mandatory diagram kinds | design | add | part |
| interface.variants | Interface phase | The variants: mockups for screens, command design for commands, contract design for a protocol other software calls, a playable prototype for play | interface | add | part |
| planning.stages | Planning | Mandatory stages, such as a packaging stage | planning | add | part |
| planning.critic-lenses | Planning | Additions to the plan critic's lenses | planning | add | project |
| run-parameters.parameters | Run parameters | Additional run parameters | run-parameters | add | project |
| configuration.items | Configuration | Additional configuration items, tools and checks | configuration | add | project |
| delegation-loop.inspect-checks | The delegation loop | Additional checks at the inspect step | delegation-loop | add | part |
| delegation-loop.test-checks | The delegation loop | Additional checks at the test step | delegation-loop | add | part |
| delegation-loop.brief-constraints | The delegation loop | Additional brief constraints | delegation-loop | add | part |
| project-end.completion-conditions | Definition of done | Additional completion conditions | project-end | add | part |
| project-end.delivery | Delivery | The delivery procedure for the part's delivery kind | project-end | add | part |
| reflection.items | Reflection points | Additional reflection items | reflection | add | project |

§6.4 calls its list initial, to be refined during implementation; a refinement is a change to this file as above, never an unlisted point in a conditional workflow. §6.4's "additional checks at the inspect and test steps" is two points here, one per step, so that a check names the step it runs at. The two points divide between them every check and review the delegation loop makes of a change, wherever the module's text places it and whatever the change is: an increment, a fix, a refactoring candidate, or the gate pass of a stage's refactoring branch. The test step is the running of the tests (the increment's tests and the suite, the new tests against the checkpoint) and the checks that run with them, such as the observability tests and the benchmark floor; step 6 runs no tests of its own, the tests having run in step 4, and the trait *performance budgets* carries the floor (§6.8). The inspect step is every other check or review, before the tests or after them: the scope check, the diagram check, the boundary log, the triage of the builder's assumptions, the reviewer passes (such as the design auditor the trait *has screens* carries), the secret scan and the dependency admission. The merge gate's conditions (step 8) belong to the core and offer no point; a CI check a conditional workflow needs is added at `configuration.items`. An addition at either point is placed in the delegation loop's text at the step that runs it. Two points are added to §6.4's list, both at intake, because §6.5 names their kinds as values a type workflow or sub-workflow sets and the core settles both at intake, before design and planning act on them: `intake.budget-kind`, the kind of performance budget, and `intake.delivery-kind`, the delivery kind; `project-end.delivery` holds the procedure for the kind set there. The delivery kinds are one list, the kinds `Delivery-Conventions.md` §1 ships plus §6.4's own: `installer` (a desktop application, §2), `install-script` (a command-line tool or a local server, §3), `package` (a library, its registry's artifact), `web-deployment` (a hosted web application), `store-package` (an app delivered through a store) and `host-installation` (an extension installed into its host); the value set at `intake.delivery-kind` and the kind an addition at `project-end.delivery` names are both drawn from it, and it grows only as a point does. Where no type workflow or sub-workflow sets a part's kind, the kind the supervisor confirms with the owner at intake (Phase 1) is the part's kind, recorded by its key from this list. Each addition at `project-end.delivery` names the delivery kind it is for and applies only to a part of that kind; so a sub-workflow that sets another kind leaves its type workflow's procedure behind, and a trait's procedure for one kind never reaches a part of another. A completion condition added at `project-end.completion-conditions` is checked at project end; a condition the plan must build toward is also added at intake (`intake.requirement-sources`), naming that completion condition as its source, so that it enters the requirements register before planning.

## How a conditional workflow names a point

A conditional workflow file states each change it makes under a heading of its own, naming the kind of change and its target, and nothing else in the file changes the main workflow:

- `## Add at <point key>` — its additions there. Any conditional workflow may add.
- `## Add at project-end.delivery for <delivery kind>` — an addition at `project-end.delivery`, naming the delivery kind it is for by its key from the list above (`## Add at project-end.delivery for installer`). At that point this form is required and the plain `## Add at project-end.delivery` fails; at every other point a heading ending `for <kind>` fails.
- `## Set at <point key>` — the value it sets there, at a point whose Changes cell includes `set`. Only a type workflow or a sub-workflow may set. The value is the section's first non-blank line; at `intake.delivery-kind` it is one delivery kind's key from the list above, bare or in backticks.
- `## Replace <module key>` — its own version of the whole phase, for a module marked replaceable. Only a type workflow or a sub-workflow may replace.

Any other `##` heading is prose, except one that reads like a change: a heading whose first word, in any case and with any trailing `:`, `;`, `,`, `.` or `-` ignored, is add, adds, added, adding, set, sets, setting, replace, replaces, replaced or replacing, or whose second word is `at` in any case, fails as a malformed change heading unless it is one of the four forms above, so a prose heading such as "Setting up the host" or "Look at the target" is renamed. A file sets each point, and replaces each module, at most once.

A trait attaches to the main workflow only through its `Add at` headings, so each of its additions names the point it belongs to. Within one file, additions at one point keep the order the file writes them in; across files they apply in the order `supervisor.md` states ("The order additions apply in").

## How a phase module declares its points

Each phase module that declares points does so in a section headed `## Extension points`, one line per point, giving the point's key from the table above, in the table's order. A module declares exactly the points this registry names it as declaring, and every point it declares is in this registry; the two directions are checked once every module declares its points (BUILD_PLAN TASK-014).
