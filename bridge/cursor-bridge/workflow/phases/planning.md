## Phase 4 — Build plan

### What must survive a compaction

After a compaction or a resume in this phase, read these before your next action:

- this module, whole;
- the approved design and what the interface phase approved: `docs/DESIGN.md`, `docs/REQUIREMENTS.md`, `docs/INVENTORY.md`, `docs/diagrams/INDEX.md` and every diagram it lists, and the approved artifacts under `docs/design/` and `docs/mockups/`, whole: every increment satisfies requirements of the register and cites what it implements;
- `docs/BUILD_PLAN.md` as drafted so far, whole, and each Issues file the owner named at Step 0, whole (its path stands in the plan's Prior-project lessons section, written there as soon as the owner names it);
- `docs/DESIGN_CRITIQUE.md`, whole, while the plan critique runs, with `docs/RUN_PARAMETERS.md` and the round's files under `run/review/` (`DESIGN-plan-<round>.md` and its `REVIEW-DESIGN-` files) while a round is in flight: the plan critique counts its rounds as the design critique does;
- `docs/PROJECT_STATUS.md`, whole: its `Awaiting user on:` line says whether Step 0's question or the plan's gate waits for the owner.

### Step 0 — Prior-project lessons (ask before drafting)

Before you draft the plan, ask the user — once, explicitly — whether an earlier project
overlaps with this one and, if so, for the path to its
`<Name> Issues During Development and Their Solutions.md`. Frame the question so they can
answer it: state in one paragraph what this project is *technically* (the stack, the
platform, the kinds of subsystems — a video pipeline, an auth layer, a desktop packager) so
they can judge overlap against projects they remember. Point them at the bridge's
`Claude-Cursor Bridge Issues Index.md` in the bridge's own `Documents/` if they keep one.
If they name none, record "Prior-project lessons: none" in the plan and move on.

For each file they give you, read it whole (it is the size of a report, not a codebase),
then produce a short **Prior-project lessons** section at the top of `docs/BUILD_PLAN.md`:

- **Extracted** — every issue whose *conditions* this project shares (same stack, same
  platform quirk, same kind of subsystem, same tooling), each with the issue's ID and
  source file, and **what it becomes here**: a specific acceptance criterion on a named
  increment, an ordering choice (build X before Y because the old project learned Y needs
  X), a constraint the brief will carry, or a configuration item for Phase 5. An issue that
  cannot be attached to something concrete in the plan has not been extracted — it has been
  noted, and noting is not the point.
- **Judged irrelevant** — the rest, one line each with the reason (different stack, the
  condition does not arise here, already covered by an existing bridge rule). This list
  exists so the user can overrule a judgement; keep it terse.

`plan-critic` verifies that every extracted issue landed on a named increment or
configuration item. Do not paste the old file's prose into the plan; the plan carries the
consequence, not the story. If a lesson is generalizable beyond both projects, say so in
your report — it is a candidate for `Known-Pitfalls.md`, which is the maintainer's call.

### The plan

Write `docs/BUILD_PLAN.md` as an ordered list of increments. Each increment must be:

- **Small** — one focused change, reviewable in a single sitting
- **Independently testable** — with acceptance criteria written before it is built
- **Ordered** — dependencies before dependents; something runnable as early as possible
- **Scoped** — the files and directories it may touch are named
- **Demonstrated** — every stage heading (`## <stage>`) is followed by a line `Demonstration: <what is shown live, on the product as built, when the stage closes>` (release A1b; `plan-check.py` notes a stage without one)
- **Placed** — its heading is `### TASK-nnn — <title>` and its field lines state `Parent:` (a group increment it helps fulfil, or none), `Depends on:` (the increments that must be merged first, or none), `Parallel:` (yes if it may be built alongside other ready increments), `Diagrams:` (the normative diagrams its brief carries), and `Scope:`. A large task is a `Kind: group` heading whose children are increments; the group is done when all its children are. Status is never written in the plan: `python ~/.claude/cursor-bridge/plan-check.py` derives it from the commits on `origin/main`, validates the fields (missing dependencies, cycles, parallel increments whose scopes overlap, diagrams not in the index), and lists what is ready.
- **Traced** — it names the requirement IDs it satisfies (`Satisfies: R-004, R-011`). Every `planned` requirement in `docs/REQUIREMENTS.md` is satisfied by at least one increment; `python ~/.claude/cursor-bridge/completion-check.py --mode plan` must pass before the plan gate; it counts an increment's `Satisfies:` field, never a mention in prose, and fails a `built` requirement whose Evidence names no test file (release A4). On an older project brought under the register part by part, `--only R-001,R-002` limits a run to those rows. A requirement no increment satisfies is either planned now or put to the owner as a deferral — never left out silently.

Each **UI-bearing** increment additionally **cites the approved mockup screen(s) and the
relevant `docs/design/DESIGN.md` sections** it implements, and carries **design acceptance
criteria** beside its functional ones ("matches mockup screen X", "passes
`impeccable detect` with no primary findings", "satisfies the relevant Vercel
interaction/forms items"). Where the increment adds or changes a screen-state, it also carries
**observability acceptance criteria** (Tier A): "state X is driver-reachable through the real
render path", "the observability test for X passes — no fired invariant, no `console.error`",
"required empty/sparse/dense/error states present" — checkable, not "renders fine".

Each increment with **logic, auth, input-handling, or data-access surface** carries
**security acceptance criteria** too ("no new Semgrep high findings", "passes OSV-Scanner
and Socket", "authorization enforced at the boundary per ASVS §x") — checkable, not
"is secure".

For **installable software** the plan's **last stage is "Packaging & installer"**: the
build script or install script, the committed installer script (desktop), the CI artifact,
the lifecycle verification (`installer-check.ps1`, or the project's `install-check.ps1` for
a CLI: your own run is a rehearsal, the proof is the owner's run from their terminal by a
run sheet, since a session of the packaged desktop app installs into a hidden copy of the
local application folder, KP-055), the command reference's currency check, and the User Manual's install and command
chapters — with `Delivery-Conventions.md` §2/§3/§4's rows as its acceptance criteria,
verbatim. The increment that first adds a command-line surface carries the
command-reference generator (§4). A plan for installable software without this stage, or a
CLI plan without the generator, is incomplete.

For every **external service** the software talks to (a third-party API, SDK, or
provider), the plan's first increment on that integration is a **contract capture**: an
attended live call that records the service's real responses as fixtures (secrets
scrubbed), which the adapter's tests then replay. A mock the builder invents encodes the
builder's *assumption* about the service, and a wrong assumption produces a
self-consistent green test — six adapters once merged green that way and every one failed
on its first real call (KP-020). "Done" for an external-integration increment means passing
against recorded real responses or an attended live smoke, never against an invented mock.
The live call needs the owner's key and possibly money: that is the existing
secret/cost escalation, asked once per service.

For every **budget** the plan carries a **benchmark increment** — a benchmark in `bench/`
that drives the budgeted operation with a fixed dataset and seed and reports the metric —
scheduled in the stage where the operation first exists, so a baseline is committed before
anything is optimized (`Performance-Conventions.md` §3). From that stage on the checker
runs in the gate.

Give each one an ID (`TASK-001`, `TASK-002`, …). Group the increments into named
**stages** — a stage is a coherent, demonstrable chunk of the plan (a milestone) and a **vertical slice**: it crosses the layers its features need (interface, logic, storage) so the parts are proven to work together and the owner can see something run. A **horizontal** stage — one layer across many features, all the storage and then all the interface — is rejected by `plan-critic`. Normally
three to eight increments, and its close is a **reflection point** (see "Reflection
points"). Every increment belongs to exactly one stage; **the close of the last stage is
project end** (see "Reflection points" — it is a defined trigger, not a judgement).
Run the design's two-critic loop over the plan, with the design as context (`plan-critic`
and Review B's design mode on `run/review/DESIGN-plan-<round>.md` holding the plan; the same
stop rule, ceiling, confirming read, resolution round and record in `docs/DESIGN_CRITIQUE.md`; release A3), looking for ordering errors, increments that are secretly
two increments, acceptance criteria that cannot actually be checked, stages that are not
demonstrable on their own, and — for UI increments — whether the design acceptance criteria
are present and checkable — and whether every requirement in the register is satisfied by an increment.

The settings that govern *how the run proceeds* — whether the loop pauses at stage closes,
who merges, whether the refactoring pass runs — are **not** part of the plan and are not
asked at this gate. They are asked once, each as its own question, at the **Run parameters**
step right after the plan is approved (below).

**Gate:** present the plan to the user. Do not delegate anything until they approve it.
Present it as a decision brief (`explain-for-decision` skill), not as the plan file itself,
with the critique's record for the plan (per round: what each critic found, what was fixed,
what was accepted with its reason) as one of its separate decisions.
Its second line, right after the approval question, is the model switch that follows
approval: *on approval, set this session to Opus 5.5 in the model menu* (rule 48) — the run
parameters and everything after them run on it.

## Extension points

This module offers the points below, each by its key in the extension-point registry (`~/.claude/cursor-bridge/workflow/extension-points.md`), which states the kinds of change each accepts and whether it applies per part or per project. A conditional workflow's additions at a point are made where the point's line places them, in the order the core states in "Main and conditional workflows".

- `planning.stages` — stages every plan for the part must hold, such as a packaging stage, written into the plan beside the stages "The plan" asks for, each with its increments and its `Demonstration:` line.
- `planning.critic-lenses` — lenses the plan critique adds to those "The plan" lists, made once for the whole project and given to both critics with the plan.
