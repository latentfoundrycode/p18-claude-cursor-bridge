## Phase 3 — Interface

### What must survive a compaction

After a compaction or a resume in this phase, read these before your next action:

- this module and the file of every variant a part runs, each whole (the session-start hook names this module and every variant file);
- the approved design: `docs/DESIGN.md`, `docs/REQUIREMENTS.md` and `docs/INVENTORY.md`, whole: each variant maps onto the agreed functionality and adds its screens, commands or operations to the register;
- what each running variant has produced so far: `docs/design/DESIGN.md` and `docs/mockups/` for the mockups, `docs/design/COMMANDS.md` for the command design, `docs/design/CONTRACT.md` and the contract file it names for the contract design;
- `run/supervisor/interface-notes.md`: every change the owner asked for on a variant's artifact and whether it is made, written there as each request arrives, because the conversation that held them does not survive a compaction (rule 54);
- `docs/PROJECT_STATUS.md`, whole: its `Workflows:` line names each part's conditional workflows, whose additions at `interface.variants` say which variants run, and its `Awaiting user on:` line says which variant waits for the owner.

### The variants

After the design is approved and before the build plan, turn the agreed design into something the owner can judge before it is built: each kind of interface a part has gets the variant made for it. The main workflow holds every variant once, its text in a file of its own beside this module:

| Variant | For the interface kind | Its file |
|---|---|---|
| Mockups | screens a person sees | `interface/mockups.md` |
| Command design | commands a person types | `interface/command-design.md` |
| Contract design | a protocol other software calls | `interface/contract-design.md` |
| Playable prototype | play | `interface/playable-prototype.md` |

Variants: interface/mockups.md; interface/command-design.md; interface/contract-design.md; interface/playable-prototype.md

Every variant is an addition, never a replacement of another: a part with screens and commands runs both the mockups and the command design. The conditional workflows add the variants that apply at `interface.variants`: the trait *has screens* adds the mockups, a sub-workflow for software met through a terminal or called through a protocol adds the command design or the contract design, and a type workflow or sub-workflow may replace the whole phase with its own (the registry marks this module replaceable), as the video game type workflow does for play.

### Which variants a part runs

Read each part's kinds of interface from the approved design: every surface a person or another program meets the part through is one of the four kinds above. A part runs the variant of every kind it has. The mockups are activated by the trait *has screens*, which a part with screens has by its definition; a part whose design shows screens without the trait on its `Workflows:` line has a trait missing, which the design gate settles (`design.md`, "Traits at the design gate") before this phase begins. The command design and the contract design are activated by the part's type workflow or sub-workflow; where the design shows commands or a protocol that none of the part's written conditional workflows activates (a sub-workflow not yet written, or administrative commands beside a service's protocol), the variant runs all the same, because its text is the main workflow's, and you name it at the gate. A conditional workflow's addition at `interface.variants` adds to the variant's text what that workflow needs, never a second copy of it. A part whose surfaces are of none of the four kinds (a pipeline whose output is files, a backend another part calls only through the contract that part's own design states) runs no variant; say so for that part at the gate. A surface the design names that fits none of the four kinds, and that the owner would judge before it is built, is raised at the gate as a decision of its own, with your proposal for how the owner sees it before the build, never left out silently.

A project with several parts runs each part's variants for that part, in the status file's order of parts; a variant two parts share (one set of screens for both) runs once, in the place of the first part that has it.

### The gate

**Gate:** present each variant's artifact to the owner and get explicit approval of each before writing the build plan; each variant's file says what its artifact is and what its own gate requires. Do not proceed while any variant a part runs is unapproved. Present them as a decision brief (`explain-for-decision` skill), each variant's approval asked as a question of its own in the app's question form, with every part that runs no variant named in one line beside them. The phase passes when every variant every part runs is approved.

## Extension points

This module offers the points below, each by its key in the extension-point registry (`~/.claude/cursor-bridge/workflow/extension-points.md`), which states the kinds of change each accepts and whether it applies per part or per project. A conditional workflow's additions at a point are made where the point's line places them, in the order the core states in "Main and conditional workflows".

- `interface.variants` — the variants a part's interface phase runs: an addition there names the variant it activates for the part, from the table under "The variants", and adds to that variant's file what its workflow needs (the trait *has screens* the mockups with their design tooling).
