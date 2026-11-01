## Phase 2 — Design

### What must survive a compaction

After a compaction or a resume in this phase, read these before your next action:

- this module, `~/.claude/cursor-bridge/Diagram-Planning-Conventions.md` and `~/.claude/cursor-bridge/Glossary.md`, each whole (the session-start hook names all three);
- what the design has written so far: `docs/DESIGN.md`, `docs/diagrams/INDEX.md` and every diagram it lists, and `docs/REQUIREMENTS.md` and `docs/INVENTORY.md` once written;
- `docs/DESIGN_CRITIQUE.md`, whole, while the critique runs: its rounds and its accepted list are what the stop rule and the four-round ceiling count, so that a resumed session never runs a round twice or raises an accepted finding again; with it `docs/RUN_PARAMETERS.md`, where an owner's `Design rounds above five:` line lifts the ceiling, and the round's files under `run/review/` (`DESIGN-<subject>-<round>.md` and its `REVIEW-DESIGN-` files) while a round is in flight;
- the owner's Initial Design Draft, every requirements document they supplied and `run/supervisor/intake-notes.md`, whole: the design and the requirements register answer them;
- `docs/PROJECT_STATUS.md`, whole: its `Workflows:` line holds the traits proposed at intake, which this phase's gate settles;
- `~/.claude/cursor-bridge/workflow/phases/delegation-loop.md`'s steps 3b and 8, while a critique round is in flight or a launch has failed: a round is snapshotted and verified as step 8 says, the snapshot's hash written to `run/supervisor/in-flight.md` at the launch and each critic's verdict there as it returns, both read from that file mid-round, and a failed launch is handled as step 3b says;
- once this phase's gate is approved, its reflection point: `~/.claude/cursor-bridge/workflow/phases/reflection.md`, whole, and the last entries of `run/supervisor/in-flight.md`, the items it has finished ("Keeping the position"), until the reflection point is done.

### The procedure

**The design is a Project Design Document: the text of `docs/DESIGN.md` plus the normative diagrams in `docs/diagrams/`, produced by diagram-based planning** (`~/.claude/cursor-bridge/Diagram-Planning-Conventions.md`, read whole by that absolute path; terms per `~/.claude/cursor-bridge/Glossary.md`). The text carries what diagrams cannot — purpose, non-goals, rationale, the **target environment**, the **technology selection** with the alternatives considered, constraints, budgets, failure modes, the security context. The diagrams carry what prose lets slip — every component, connection, state, entity, and interaction — in a form `diagram-check.py` verifies. The procedure (conventions §5):

1. **Select.** Write `docs/diagrams/INDEX.md`: every catalogue kind selected or omitted with a one-line reason, IDs assigned, each selected diagram tied to the requirement IDs it realizes and to what enforces it. Levels 4 and 5 only where a detail is **load-bearing** (concurrency, security, integrity — every persistent schema — performance, protocol, prior-failure), each with its reason; everything else stays the builder's free implementation space.
2. **Draft top-down, level by level, with `diagram-specialist` subagents**: kinds the catalogue marks parallel in separate runs at once, a mutually dependent pair in one run, each run given the approved upstream diagrams, its register rows, the design text, and (Levels 4-5) its load-bearing reason as fixed inputs.
3. **Integrate.** Reconcile the drafts — identifiers, boundaries, contradictions, open points; settle each specialist objection or escalate it per "Objections — bottom-up escalation". `python ~/.claude/cursor-bridge/diagram-check.py --mode design` must pass.
4. **Critique.** `plan-critic` reviews the text and the diagrams together.

Write `docs/DESIGN.md`. It covers: purpose and scope; explicit non-goals;
architecture and component breakdown; technology choices *with the reasoning for
each*; data model **and its migration policy** (pre-release: schema definitions are
edited and disposable databases rebuilt, no migrations; from the first shipped version:
migrations, additive first, destructive only with a data-preserving path — record which
regime the project is in and when it switches); key interfaces and contracts; error
handling and failure modes;
security and secret-handling approach; testing strategy; open questions.

When the design settles a technology choice or a subsystem kind that an earlier project
plausibly shared (the same framework, the same platform packager, a media pipeline, a
payments or auth layer), say so in the design presentation in one line — "an Issues file
from a project on the same stack would matter at Phase 4" — so the user has time to find
it before the build plan asks for it. This is a heads-up, not the question itself; the
question is asked once, at Phase 4 step 0.

The **security-and-secret-handling section records the chosen ASVS level and the trust
boundaries** from Phase 1, so the level in force is documented for the plan, the briefs, and
the auditor. `plan-critic` checks the security criteria alongside the rest (below).

Then the design is criticised **before the gate, by two critics of different makes, as peers**
(release A3, plan 8.6). A round is `plan-critic` and Review B's design mode on the same
committed design, each in a fresh context, each given `docs/DESIGN_CRITIQUE.md`: the list of
findings already accepted with their reasons, so that neither raises them again, and each
critic's grades per round. Review B's design mode reads only: commit the design text, the
diagrams, the requirements register, `docs/DESIGN_CRITIQUE.md` (the accepted list and the
earlier grades) and the critic's lenses (copied from `plan-critic`'s sections, so the reviewer
needs nothing outside the Workspace) to `run/review/DESIGN-<subject>-<round>.md` (`<subject>`:
`design`, `plan`, the change's name, or `<the change's name>-plan`, so that a plan's round 1
never overwrites the design's), `git add -f` it, then launch, exactly:

```bash
python ~/.claude/cursor-bridge/bridge-run.py --limit auto --kind review -- cursor-agent -p --mode=ask --trust --model <review_b from docs/ROSTER.resolved.json> "The text to criticise is already written to run/review/DESIGN-<subject>-<round>.md, with the lenses, the grades to answer in, and the record of what was accepted so far. Read that file whole; do not ask for it; the findings it lists as accepted are settled, do not raise them again; answer with your findings in its grades, each naming the diagram, section or requirement it concerns, then the counts per grade, and nothing else; where you find nothing, name instead three statements of the file you verified, each with a short quotation from it. Write no file under the checkout, point no cache there, and edit nothing." 2> run/review/REVIEW-DESIGN-<subject>-<round>.err
```

It answers in the critic's grades (Blocking, Should fix, Consider), each finding naming the
diagram, section or requirement it concerns. Snapshot before and `verify` after it, as for a
code review; a reply that names nothing from the file is a failed launch, not a verdict. A reply with no finding names three statements of the file it verified, each with a short quotation, and the check reads them against the file: fewer than three, or a quotation the file does not hold, is a failed launch too (T2). Then
fix what both found; what you accept with a reason goes on the list and is settled. The snapshot's id is the round file's name, `DESIGN-<subject>-<round>` (`review-guard.py snapshot DESIGN-<subject>-<round>`, then `verify` under the same id), and the `.err` file's name follows from it, `run/review/REVIEW-DESIGN-<subject>-<round>.err`, as the command above writes it.

**A worked scenario for money and stored data** is a lens of both critics: a rule about money or stored data is read against one worked scenario before it reaches code review (a retry after a lost reply, a dry run, a benchmark, an approved live smoke, two users on one account), each step naming the store it reads and writes; `plan-critic` carries the lens, and Review B's file copies it with the rest of its sections.

**The loop stops by what was found, and after four rounds at the most.** Another round follows
only on a Blocking finding, or a Should-fix finding you did not accept with a reason; a critic
whose round returned nothing of that kind drops out; when both have dropped out the critique
ends. A finding that reverses an earlier fix is non-convergence: it is recorded, starts no
round and waits for the resolution round; any other such finding in the same round still
starts the next. **Four rounds per subject is the owner's ceiling, whatever the critics still
find.** The subjects are the design, the plan and each change: a change cycle's design revision
(the change's name), its plan addendum (`<the change's name>-plan`), and a scoped revision
mid-build, which is a change named as `docs/DESIGN.md`'s Change section names it; a subject is
never renamed or split to start its count again. A plan addendum whose increments stood in the design's review file from round 1 is no subject of its own: it is criticised and gated with the design as one subject, under the design's token, and the subject's block heading in `docs/DESIGN_CRITIQUE.md` names both. A subject is one token of lower-case letters,
digits and hyphens: for a change, chosen from its name when the Change section is written (the
Azure monthly allowance is `azure-allowance`, its plan addendum `azure-allowance-plan`),
distinct from `design`, `plan`, every other subject and every other `<token>-plan`, and
written in its block's heading in `docs/DESIGN_CRITIQUE.md`. A launch that failed (a reply that
names nothing from the file) spends no round and follows step 3b, every failed launch recorded:
a first failure is exit 4, and the same file runs once more; a second is exit 3, which marks the
model and re-resolves, and the same file runs once more on the profile it gives, under its
number (a connection error or a hit limit keeps step 3b's exit 4 or 5 and no mark). A third
failure, an exit 5, or no usable profile makes the design wait (below), Review B's row recorded as
`not run (<the reason>)`. A round counts against the four once either critic delivered in it (the record's definitions, below); a round in which neither delivered is never run and spends none of the four. The wait ends when the roster returns
(rule 38) or on the owner's word; then the same file runs once under its number, with no
re-runs. If that launch fails too, Review B's row stays `not run (<the reason>)` and the subject goes on to its
resolution round or its gate, the report escalating it to the owner.

- **The confirming read.** When the critique ends and the text changed after either critic last
  read it, both critics read it once more, as the next round (the fifth at the most, or
  `<rounds>` at the most under an owner's line already written). Its file
  opens with *This round is the confirming read: raise a finding only on text changed since your
  last read, or a Blocking finding anywhere*, and holds the committed diff of the subject's text
  since each critic's last read, each diff labelled with its critic. **A confirming read is
  final, whatever its number: no critique round follows it**, save when the owner's line is
  written after it (below). What it finds is fixed (recorded as fixed, unverified) or accepted
  with a reason.
- **The resolution round.** Whatever is still Blocking or non-convergent (neither fixed nor
  accepted with a reason) after the confirming read, or after the critique where no confirming
  read was due, goes to the subject's **one resolution round**:
  `run/review/DESIGN-<subject>-R1.md` holds every such question and both critics' positions on
  each, and opens with *This is the resolution round: answer every open question in this file;
  raise no new finding; your reply answers each question in place of findings, with no counts*.
  Review B answers it with the same read-only command, the file's opening line taking the place
  of the command's request for findings, grades and counts. Its reply arrives on the launch's output
  (the `.err` file holds only the launcher's lines): after `verify`, write it to
  `run/review/REVIEW-DESIGN-<subject>-R<n>.md` for the resolution round just run (`R1`, or
  `R2` under the owner's line); `plan-critic` reads that file and answers it; the settlement
  goes under Resolution.
- **The gate.** Then the subject goes to its gate, whatever is still open: a Blocking finding
  still open after its last resolution round does not stop it. The critique record lists what is
  open, with both critics' grades and the settlement.

The convergence rule of step 8 (two reviewers naming the same defect make it certain, and blocking only where it is of the five blocking classes) belongs
to the code gate, not to this loop: a finding both critics name keeps the grade its content
earns and never adds a round.

**The launcher holds the ceiling.** `bridge-run.py` reads every `cursor-agent` command whose
arguments name, anywhere and with either path separator, a file `run/review/DESIGN-<name>.md`
(spelled as Windows also opens it: doubled separators, `.` segments, folder names ending in
dots or spaces);
every such name is checked, and one refused name refuses the launch. A name is read from
`DESIGN-` up to `.md` and holds only lower-case letters, digits and hyphens, but for the round's
`R`. The round is the name's last hyphen-separated part: a positive integer written without a
leading zero, or `R` and such an integer; the subject is the rest. Without the owner's line,
rounds 1 to 5 and `R1` are allowed. A name of one part is a round with an empty subject, which
is not `plan` (`DESIGN-5.md`, the plan's file before 2026.10.18a: `DESIGN-1.md` to
`DESIGN-5.md` allowed, `DESIGN-45.md` refused; no line can name that subject, so it is never
lifted). It refuses, with exit 125, before anything starts, and with a message that begins
`bridge-run: refused - design ceiling: ` and names the file, the round and the
`docs/RUN_PARAMETERS.md` it looked in, three things: a name it cannot read that way (a space or
a capital in it, `0`, `05`, `06`, `R0`, a round that is no number, a `run/review/DESIGN-` with
no `.md` after its name), a round above five, and a resolution round `R2` or later. The floor is the launcher's:
a design-mode `cursor-agent` started other than through `bridge-run.py` has no ceiling and
breaks rule 8. A refusal is neither a failed review nor a model's failure (step 3b): it is not
retried and no `--record-failure` follows it; the subject goes on to its resolution round or its
gate, as above.

**The owner's line.** The owner's words lift the ceiling for one subject: a line
`Design rounds above five: <subject> <rounds> (<their words>, <date>)` in
`docs/RUN_PARAMETERS.md`, the subject compared exactly and `<rounds>` above five, lets the
launcher allow that subject rounds 1 to `<rounds>`, `R1` and `R2`, and nothing beyond. Under it
the subject runs the same shape once more from where it stands: critique rounds under the stop
rule up to `<rounds>` minus one, then a confirming read if the text changed (round `<rounds>` at
the most), then, if anything is still open, its next resolution round (`R1` if it has had none,
else `R2`, holding what is still open after the first), then the gate. You never ask for that
line: it is written only on the owner's own words, given unprompted or at the gate, where the
record shows what is open (an owner who sends a design back at its gate to be criticised again
gives exactly those words). `<rounds>` is a round number, never a count: the number of the
last numbered round run (a resolution round not counted) plus the number the owner names, or
plus five when they name none; it is never below six; the line records their words as given,
and the report that records it says in one line how `<rounds>` is spent: critique rounds through
`<rounds>` minus one, then the confirming read at `<rounds>` if the text changed (for an owner
who named two after round four: one critique round, then the confirming read). A subject is
lifted once: the first well-formed line for it stands and a later one is ignored: the owner's words to criticise it again after that make it a scoped revision, a change
with a subject of its own. Before the run-parameters step the line is written to
`docs/RUN_PARAMETERS.md` on its own, creating the file; that step adds its lines beside it.

The record shows each critic's grades apart. Its cost: at most six subagent runs and six
verdict-bearing Cursor calls per subject, and, for a failed launch, two re-runs before the wait and one launch after it: four rounds,
the confirming read and the resolution round; under the owner's line, up to `<rounds>` and `R2`.

`docs/DESIGN_CRITIQUE.md` has three parts, one block per subject: **Accepted** (finding, critic,
round, the reason), **Rounds** (round, its kind: critique, confirming read, resolution, not run
or refused; the commit its file was built from; critic; the counts of Blocking, Should fix and
Consider; what was fixed), **Resolution** (the
question, what was settled, how). The commit its file was built from is the subject's head when the round's file was assembled; a round in which one critic delivered is a critique round, the other critic's row reading `not run (<the reason>)`. The `run/review/DESIGN-*` files are
removed with `git rm` in the commit that passes the gate, as step 8 removes the review files.
When no roster profile is usable at intake (Cursor not signed in, both pools exhausted), the
design waits and the report says so, as rule 38's failure path does; `plan-critic` alone is
never the gate's critique.

**Development data stays apart from live data (rule 55).** The design names where the
product's live data lives and how a development build is kept from it: another path or store
chosen by a build-time marker, and a build that refuses the installed product's data outright.
Record it in `docs/INVENTORY.md` → Decisions as a row that begins `Development data:`; every
brief carries it as a constraint, and the conformance check reports a project without the row.

**Who decided is recorded (rule 51).** Where the product stores decisions or approvals, it
records who or what decided each: a person, or the judge and its model. An agent's decision is
never recorded as a person's. A per-item approval step inside the product is decided by a judge
of another model family than the one that produced the item, with a person as an optional
override; the design says which judge and which family.

#### A part without screens

A part without the trait *has screens* writes no Observability & Verifiability section, and `docs/DESIGN.md` notes that it did not. The observability driver dependency is the one escalation of that trait's configuration addition (Phase 5).

### The delivery kind

When you create `docs/INVENTORY.md`, record each part's delivery kind as a Decisions row that begins `Delivery kind:`, naming each part and its kind's key from the extension-point registry: the kind a type workflow or sub-workflow sets at `intake.delivery-kind`, or else the kind confirmed with the owner at intake (the intake notes). The delivery procedure at project end applies to a part by this recorded kind, and the kind changes only with the part's classification.

### Traits at the design gate

The traits proposed at intake, the default traits of each part's product type and sub-type among them, are settled at this gate (intake's "Classifying each part"). Before presenting the design, weigh each part's traits again against the open list's definitions (`~/.claude/cursor-bridge/workflow/open-list.md`) in the light of the design: a trait the design now shows is added (the product needs accounts: *personal data*), and a proposed or default trait the design shows does not apply is dropped, each with its reason. At the gate each part's traits are a decision of their own, asked in the question form beside the separate decisions the gate below lists: each trait with its definition in one line and, in plain words, the work it adds. Once the owner has settled them, rewrite the part's `Workflows:` line if they changed, and run `python ~/.claude/cursor-bridge/workflow-check.py --status docs/PROJECT_STATUS.md` again.

A plan critique's file carries, beside `plan-critic`'s own sections, the lenses each part's conditional workflows add at `planning.critic-lenses`, each once for the project: the point applies per project, and the traits are settled at this gate, before the plan. A trait added at this gate has its additions at `intake.questions` asked, the answers written to the intake notes, its additions at `design.sections` and `design.mandatory-diagrams` written (the Select step run again for a mandatory kind), and the design and the register revised from the new answers, before the design is presented again.

**A new or unwritten trait is flagged, and the work continues.** A property that adds work and fits no trait's definition is a new trait; a trait whose open-list row reads `no` under Written (the check's `FLAG (trait)`) is defined but not yet written. Traits only add, so the main workflow and the part's product type still cover everything essential: write the extra handling into `docs/DESIGN.md`, a section of its own for each such trait saying what it adds and in which phases, and flag it at the gate as a decision of its own, saying plainly that until the bridge writes the trait's additions the design's section is the only handling it has: the work continues with the handling in the design, or the owner may still choose to pause the project. On a pause the trait goes to the bridge's maintainer as an unwritten product type does at intake: `Awaiting user on: paused at the design gate — <the trait> needs additions the bridge has not written`, the run sheet with your reasons, the release, the calibration, and the owner's word to resume. On resuming, a new trait, now in the open list, is added to each part's `Workflows:` line that has it; for a new trait and for an unwritten one already on the line alike, the check is run again, and the trait's additions, now written, take the place of the design's section. A new trait is not named on the `Workflows:` line until then, since the line names only the open list's entries; its handling lives in the design. Record each flagged trait in `docs/INVENTORY.md` → Decisions as a row that begins `Flagged trait:`, naming the trait, the parts that have it and the design section that handles it, so that the promotion pass at project end puts it forward, from which the maintainer may write it as trait additions; once the trait's additions are written and apply, the row is removed.

### The gate

**Gate:** present the design to the user. Do not proceed to the interface phase until they
approve it. Present it as a decision brief (`explain-for-decision` skill): the choices the
design makes that are theirs to approve, the concepts those rest on, and what you decide
regardless. **Present it as separate decisions, each asked as a question of its own in the
app's question form,** within the skill's budget each: the behaviour the design fixes; the
requirements register; the Level 1 diagrams; the critique's record (per round: what each
critic found, what was fixed, what was accepted with its reason; a design that converged in
one round and one that needed four are visibly different things); and, apart from these, each
item that costs money or needs an account (code signing, a paid driver, a provider) — never
one presentation of everything (plan 8.8). The **Level 1 diagrams** (use cases, operational workflows) state what the software does, so present them as part of what the owner approves; the other levels are technical, named in the brief and available to read (they render in Markdown viewers that support Mermaid), not put to the owner as questions.

Once approved, write **`Documents/<Name> Project Summary.md`** — the human-facing account
of what is being built, for whom, the architecture in plain language, the key decisions and
their reasons, and the current state. It is the first of the Documents set (see "The project
layout") and is patched at every reflection point from here on. It is a translation of
`docs/DESIGN.md` for a reader who will never open `docs/`, not a copy of it.

**Before presenting the design, write the requirements register — `docs/REQUIREMENTS.md`.** Every requirement the owner stated at intake, every one in a requirements document they supplied, and every one the design commits to becomes **one row with an ID** (`R-001`, `R-002`, … — never reused, never renumbered): one checkable sentence in the owner's terms, where it came from, and its status. A screen, a tab, a setting, a command, a behaviour — each is a row; a requirement too large to check in one sentence is split. This is the list "done" is measured against: the project is finished when every row is built and tested or the owner has deferred or dropped it, and not before (rule 44). Format, parsed by `completion-check.py`:

```markdown
# Requirements — <Name>
| ID | Requirement | Source | Status | Evidence |
|---|---|---|---|---|
| R-001 | <one checkable requirement, in the owner's terms> | <intake answer · requirements document §n · DESIGN.md §n · mockup screen "<name>" / state "<name>"> | <planned · built · deferred — owner YYYY-MM-DD · dropped — owner YYYY-MM-DD> | <test file(s) that name R-001 · —> |
```

Present the register with the design: the owner confirms the list is complete — a requirement missing here is missing from everything downstream.

At the same moment create **`docs/INVENTORY.md`** (format under "Project state"): the design's decisions, each with the reason that made it right, and every resource known so far — each key, token, account, or tool the owner has provided or will be asked for. Features fill in as increments merge. From here on, anything the owner provides is entered the moment they provide it.

## Extension points

This module offers the points below, each by its key in the extension-point registry (`~/.claude/cursor-bridge/workflow/extension-points.md`), which states the kinds of change each accepts and whether it applies per part or per project. A conditional workflow's additions at a point are made where the point's line places them, in the order the core states in "Main and conditional workflows".

- `design.sections` — additional design sections, written into `docs/DESIGN.md` with the sections this module lists.
- `design.diagram-catalogue` — additions to the diagram catalogue the Select step chooses from, made once for the whole project.
- `design.mandatory-diagrams` — diagram kinds the Select step must select for the part, never omit.
