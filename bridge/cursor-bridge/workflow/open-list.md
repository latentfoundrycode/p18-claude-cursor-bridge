# The open list — product types, sub-types and traits

This file is the canonical list of every product type, sub-type and trait the bridge knows, each with its definition and whether its conditional workflow is written (Restructuring Plan §6.3, §6.11). It is the one source of the default traits of a product type and of a sub-type: a type workflow or sub-workflow that states its default traits states the ones given here. No form for that statement exists yet, so `workflow-check.py` does not check it; the form and its check come together, in the change that writes the first such statement, and the reviewers of that change compare the statement with this file. Each part of a project is classified against the definitions here at intake, and a part that fits none of them is handled as "When something does not fit" below says (§6.7).

**The lists are open.** Nobody can foresee every product type or trait, so each entry carries a definition: a part is classified against the definitions, and a part that fits none of them is recognised as new rather than forced into the nearest entry (see "When something does not fit" below).

## How this file is read

`workflow-check.py` reads the three tables below and nothing else in this file; the prose is for the reader. Each table is the first table after its heading (`## Product types`, `## Sub-types`, `## Traits`), its rows running to the first line that is not a table line; its columns are found by their header names; no cell contains a `|`.

- **Key** — the entry's identifier and the base name of its workflow file: a type workflow at `workflow/types/<key>.md`, a sub-workflow at `workflow/types/<type key>/<key>.md`, a trait's additions at `workflow/traits/<key>.md`. Lowercase letters, digits and hyphens; unique within its table.
- **Name** — the entry's name in plain words, used in prose and at intake. A trait, which has no workflow name, is named by it on a `Workflows:` line.
- **Definition** — what a part must be, or have, for the entry to apply.
- **Workflow name** / **Sub-workflow name** — the fixed name of the entry's workflow, used in the status file's `Workflows:` line and in the progress graph's header (§6.3, §7.8). A `Workflows:` line is read by name, so the Workflow names, the Sub-workflow names and the traits' Names are unique across the three tables.
- **Default traits** — trait keys, separated by commas, or `—` for none. A sub-type's cell is the complete default set for a part with that sub-type, in place of its type's. The order inside a cell carries no meaning; the order traits apply in is the Traits table's. Default traits are proposals, settled at the design gate.
- **Of type** — a sub-type's product type, by key.
- **Written** — `yes` once the entry's workflow file exists at its key's path and passes the workflow check, else `no`. The increment that writes an entry's file sets its flag in the same change. A part whose product type or sub-type is not written pauses its project; a trait that is not written is flagged and the work continues (§6.7).
- **Planned** — when the entry's workflow is to be written (§6.8, §6.9).

## Product types

A product type answers one question: **how does the product reach its user?** That covers what the user meets it through, how it is delivered, and where it runs. Each part of a project has exactly one product type.

| Key | Name | Definition | Workflow name | Default traits | Written | Planned |
|---|---|---|---|---|---|---|
| mobile-app | Mobile app | Installed on a phone or tablet from an app store | Mobile App Development | has-screens, installable | no | when the first project of this type arrives |
| web-app | Web app | Used in a browser; keeps data for its users (accounts, saved state, runs, orders). Without a sub-type it runs on a server the owner operates and is delivered by deployment | Web App Development | has-screens, personal-data | no | release B |
| website | Website | Used in a browser; presents content; keeps no data for its users | Website Development | has-screens | no | when the first project of this type arrives |
| own-computer | Software on your own computer | Installed and run on the user's own computer, and met through something other than a browser page | Own-Computer Software Development | installable | no | release B |
| backend-service | Backend service | Runs on a server, has no screen, serves other software over a network | Backend Service Development | long-running-process | no | when the first project of this type arrives |
| library | Library | Code that other programs include; delivered as a package | Library Development | — | no | when the first project of this type arrives |
| video-game | Video game | Built around a real-time play loop | Game Development | has-screens, performance-budgets | no | release E |
| host-extension | Host extension | Runs inside another application, through that application's extension points | Host Extension Development | installable | no | release B |

To tell a website from a web app at intake, one question decides: **does it keep data for its users** (accounts, saved progress, runs, orders)? If yes, it is a web app. To tell a web app from software on your own computer: **does its user meet it in a browser?** If yes, it is a web app, wherever it runs.

## Sub-types

A sub-type says more precisely what a part of its product type is, where that changes the work. A part has at most one sub-type, of its own product type; a part with no sub-type runs under its type workflow alone. A part that fits a sub-type's definition takes that sub-type, so a sub-type whose workflow is not yet written pauses the project as an unwritten product type does ("When something does not fit").

| Key | Name | Of type | Definition | Sub-workflow name | Default traits | Written | Planned |
|---|---|---|---|---|---|---|---|
| android | Android | mobile-app | A mobile app for Android | Android App | has-screens, installable | no | when the first project of this type arrives |
| ios | iOS | mobile-app | A mobile app for iOS; it can only be built on a Mac | iOS App | has-screens, installable | no | when the owner builds on a Mac |
| local-web-app | Local web app | web-app | Installed and run on the user's own computer and opened in their browser at a local address; it is delivered by an installer instead of a deployment and has a local server to start and stop | Local Web App | has-screens, installable, long-running-process | no | release B |
| gui | GUI | own-computer | Met through a window | GUI Software | has-screens, installable | no | when the first project of this type arrives |
| cli | CLI | own-computer | Met through a terminal | CLI Software | installable | no | when the first project of this type arrives |
| pipeline | Pipeline | own-computer | Met through nothing: it runs jobs unattended and its output is files or records | Pipeline Software | installable | no | when the first project of this type arrives |
| local-service | Local service | own-computer | Other software on the same computer calls it through a protocol, such as an MCP server; its interface is a contract | Local Service Software | installable, long-running-process | no | release B |
| roblox | Roblox | video-game | A game built for and published on Roblox | Roblox Game | has-screens, performance-budgets, multiplayer | no | release E |
| claude-code-extension | Claude Code extension | host-extension | Runs inside Claude Code, through its commands, agents, hooks and settings (the bridge itself) | Claude Code Extension | installable | no | release B |
| browser-extension | Browser extension | host-extension | Runs inside a web browser, through the browser's extension interfaces | Browser Extension | installable | no | when the first project of this type arrives |

**A sub-type must earn its place.** It must change a phase, a gate, a check or the tooling. A difference that changes none of these (a puzzle game against a shooter) is a design choice and belongs in the project's design document. A Roblox game earns its sub-type: a different editor, language, testing and publishing.

**Siblings are exclusive:** a part has at most one sub-type of its product type. **Two levels are enough** (a product type and its sub-types); a third needs evidence from a real project.

## Traits

A trait is a property that adds work whatever the product type. A part may have any number of traits. Traits are proposed at intake and settled at the design gate. This table's order is the order in which several traits' additions apply (`supervisor.md`, "The order additions apply in"); a trait added later goes at the end of the table.

| Key | Name | Definition | Written | Planned |
|---|---|---|---|---|
| has-screens | Has screens | Shows a visual interface to a person | no | release B |
| installable | Installable | Delivered as something the user installs | no | release B |
| performance-budgets | Performance budgets | Speed, size or frame-rate targets are requirements | no | release B |
| external-services | External services | Depends on services run by others | no | release B |
| spends-money | Spends money | Its actions cost real money (paid APIs, purchases) | no | release B |
| long-running-process | Long-running process | Keeps a process running between uses (a server, a watcher) | no | release B |
| ai-models | AI models | Its results come from models, so correctness is judged by evaluation rather than by exact tests | no | release B |
| personal-data | Personal data | Holds data about people: accounts, sign-in, privacy, deletion | no | when a project first needs it |
| multiplayer | Multiplayer | Several people interact live through a server | no | release E, with the Roblox sub-workflow |

## When something does not fit

At intake, the supervisor classifies each part against the definitions above (§6.7):

- **A new product type or sub-type pauses the project.** When a part fits no product type, fits two equally, or fits one whose workflow is not yet written, the supervisor stops before design and sends the owner to the bridge's maintainer with its reasons. The maintainer writes the workflow with the owner (below), the release goes out, the project calibrates, and the supervisor resumes.
- **A new trait is flagged, and the work continues.** Traits only add, so the main workflow and the part's product type still cover everything essential. The supervisor writes the extra handling into the project's design, flags it at the design gate, where the owner may still choose to pause, and puts it forward at the promotion pass at project end, from which the maintainer may write it as trait additions. The same holds for a trait that is defined but not yet written.

## Adding or changing a conditional workflow

The procedure (§6.10):

1. The owner describes the product type, sub-type or trait and what should differ, in plain words, in the maintainer's session; a project paused for a new product type brings its supervisor's reasons.
2. The maintainer writes the conditional workflow: which extension points it uses, and what it adds, replaces or sets at each (trait additions only add). Its entry joins this list with every column of its table filled, including, for a product type or sub-type its definition, default traits and workflow or sub-workflow name (and a sub-type's Of type); for a trait its definition.
3. The workflow check passes, and the entry's Written flag is set to `yes` in the same change.
4. The release's changelog names the conditional workflow, and calibration applies it to running projects of that product type by phase, reopening no gate.

Changing an existing one is the same, editing only its file and, where its definition, default traits or name change, its entry here. A project's supervisor never writes a conditional workflow and never changes this file; it may propose either through the promotion pass at project end.

## Names

The workflow names of the video game (Game Development) and of its Roblox sub-type (Roblox Game) are the owner's (2026-10-01). The others follow the same shape, as §6.3 fixes it: a type workflow is named for the work on its product type, and a sub-workflow for the kind of product its sub-type makes.
