## Phase 1 — Intake

### What must survive a compaction

After a compaction or a resume in this phase, read these before your next action:

- this module, whole;
- the owner's Initial Design Draft in `Documents/`, whole, if they wrote one, and every requirements document they supplied;
- `run/supervisor/intake-notes.md`: every question asked so far and the owner's answer to it, written there as each answer arrives, because the conversation that held them does not survive a compaction (rule 54);
- the open list, `~/.claude/cursor-bridge/workflow/open-list.md`, whole, until every part is classified;
- `docs/PROJECT_STATUS.md`, whole: its `Workflows:` line and its `Awaiting user on:` line say how far the classification and the questions have gone;
- once this phase's gate is approved, its reflection point: `~/.claude/cursor-bridge/workflow/phases/reflection.md`, whole, and the last entries of `run/supervisor/in-flight.md`, the items it has finished ("Keeping the position"), until the reflection point is done.

### The procedure

Every project begins here. Do not skip it, even if the user's opening description
seems complete.

The user describes what they want built — in the prompt, or in an **Initial Design Draft** they wrote beforehand and keep in `Documents/` (read it whole; it is input, and you never rewrite it). Your job is to interrogate that description
until it can survive contact with an implementer. Read what they gave you, then come
back with questions that fall into three buckets:

**Gaps.** What has not been specified that must be before anyone can build?
Persistence, authentication, error handling, concurrency, deployment target,
supported input ranges, what happens when a dependency is unavailable.

**Contradictions.** Where do two stated requirements conflict, or where does a
stated requirement conflict with a stated constraint? Name both sides explicitly
rather than silently picking one.

**Better options.** Where does a choice the user made get beaten by an alternative
*on their own stated criteria*? Say what the alternative is, what it costs, and
which of their requirements it serves better. Then defer — it is their project.
Do not relitigate a decision they have already made once.

Cover at minimum: purpose and primary user; feature list with priorities;
UI and interaction model; technology stack and any constraints on it; hardware,
platform, and runtime context; data and persistence; external services and
integrations; performance, scale, and security expectations; testing expectations;
explicit non-goals.

**The project file.** Intake ends with `project.json` at the Workspace root, the one place
that states the project's fundamentals succinctly for people and programs: `name`, `purpose`
(one sentence), `kind` (`private` or `commercial`), `version` (the product's current version,
`0.0.0` until a release), and `state` (`phase`, `stage`, `bridge`, `updated`). The one thing in
it the owner is asked is the kind, as its own question in the question form, `private` named
first as the default, with its one effect stated: it is recorded for the owner and for later
tools and changes nothing in how the bridge builds; it is never a licence question. You keep the file current
at every phase change and every stage close (the reflection points); the conformance check
reports a missing or stale one (release A2, the owner's requirement of 2026-10-10).

**The roster, at intake.** One more prerequisite is stated here: the Cursor program is
installed and signed in (`cursor-agent --list-models` answers). Then write `docs/ROSTER.json`
from the merge policy's two-profile template and resolve it (`python
~/.claude/cursor-bridge/roster-check.py docs/ROSTER.json`), so that a cross-family reviewer
exists from the first phase: the design critique needs it (release A3, plan 8.6). Phase 5 only
re-resolves it.

Alongside it, capture a light **security-context** for the feature set: the **trust
boundaries** (where untrusted input crosses into the system), the **authentication and
authorization model**, the **data sensitivity / PII** handled, and the **external inputs
and integrations**. From the data sensitivity, choose the **OWASP ASVS level** — L1
(baseline), L2 (most applications), L3 (high-assurance) — that the project will build and be
gated against. This is what lets the build plan, the brief, and the `security-auditor`
reason about IDOR/authz/data-handling later.

Ask in batches, not one at a time. Use `AskUserQuestion` where the answer is a
choice among options; use plain prose where it is open-ended. Stop asking when the
remaining unknowns are ones a competent implementer could decide without you.

Also at intake: **fix the software name** — the name the user will call the product. It
names the four `Documents/` files (see "The project layout") and never changes; if the user
has not named it, propose one and get it confirmed with the summary below. And resolve the
layout: confirm you are in `Workspace/`, that `../Documents` exists (create it if not), and
record both resolved paths and the software name in `docs/PROJECT_STATUS.md`.

### The intake notes

Write every question you ask and the owner's answer to it to `run/supervisor/intake-notes.md` as each answer arrives, and name the file on the status file's `Working files:` line (rule 54): the answers are what the design is written from, and the conversation that holds them does not survive a compaction. A key, token or password the owner gives is never written there: note only that one was given and where it now lives (rule 53 says what a key seen in the chat costs).

### Classifying each part

Each part of the project is classified at intake against the open list's definitions (`~/.claude/cursor-bridge/workflow/open-list.md`): its product type and, where one fits, its sub-type, which are fixed here because every phase that follows depends on them; and its traits, which are proposed here and settled at the design gate, because several of them only emerge from the design (whether the product needs accounts, for instance). The default traits the open list gives a product type or sub-type are proposals too, settled at the same gate. A part is classified by what the definitions turn on, never by a name that sounds close: where the owner's description leaves a definition's deciding question open (does it keep data for its users; does its user meet it in a browser), ask it.

Write each part's classification on the status file's `Workflows:` line, in the grammar "Project state" gives it, with the traits proposed, then run `python ~/.claude/cursor-bridge/workflow-check.py --status docs/PROJECT_STATUS.md`. A `FLAG (trait)` line names a trait whose additions are not yet written: the work continues, and the design handles it (see "Traits at the design gate"). The summary at the gate states each part's product type, sub-type and proposed traits, each with its definition in one line.

**The delivery kind is confirmed for every part.** Where no type workflow or sub-workflow sets a part's kind at `intake.delivery-kind`, confirm with the owner the kind of delivery the part ends in, by its key from the extension-point registry's delivery kinds (`installer`, `install-script`, `package`, `web-deployment`, `store-package`, `host-installation`), for every part and not only for installable software, and write it in the intake notes; `docs/INVENTORY.md` records each part's kind, when the design creates it, as a Decisions row that begins `Delivery kind:`, because the delivery procedure at project end applies to a part by its recorded kind.

**A part that does not fit pauses the project before design.** When a part fits no product type, fits two equally, fits one whose workflow is not yet written, fits two sub-types of its type equally, or fits a sub-type whose sub-workflow is not yet written (its open-list row reads `no` under Written, and the check prints `FAIL (f)`), the project stops before design: no design work starts for any part. A part that fits no entry, or two equally, keeps `not yet classified` on its line; a part that fits an entry not yet written is named by it, so the check shows the pause. Finish intake's questions first, then write `Awaiting user on: paused at intake — <the part> needs a workflow the bridge has not written`, and put the pause at the head of your report as a run sheet (rule 27); it is not a choice put to the owner but a step they take: the owner takes your reasons to the bridge's maintainer, in the maintainer's own session (the part, the definitions you weighed it against, and why none fits, which two fit equally, or which workflow is not yet written), and the maintainer writes the workflow with the owner as the open list's "Adding or changing a conditional workflow" sets out. The release goes out, the project calibrates (`/calibrate-bridge`), and you resume on the owner's word: classify the part again against the open list as it now stands, write its `Workflows:` line, and run the check; only when it passes does intake go on to its gate. No part goes to the gate `not yet classified`.

### The gate

**Gate:** summarise your understanding back to the user and get explicit
confirmation before moving on. Where the summary rests on a technical matter the user has
not met yet, explain it under the `explain-for-decision` skill — parts before the whole, one
instance, the practical stake — rather than assuming it is self-evident.

## Extension points

This module offers the points below, each by its key in the extension-point registry (`~/.claude/cursor-bridge/workflow/extension-points.md`), which states the kinds of change each accepts and whether it applies per part or per project. A conditional workflow's additions at a point are made where the point's line places them, in the order the core states in "Main and conditional workflows".

- `intake.questions` — additional questions, asked with the minimum this module covers.
- `intake.requirement-sources` — additional sources of requirements, read with the owner's description and entering the requirements register as it does.
- `intake.target-environment` — the product type's target environment, confirmed with the platform context; a type workflow or sub-workflow may set it.
- `intake.budget-kind` — the kind of performance budget the part is measured by (page load, frame time), settled with the budgets; a type workflow or sub-workflow may set it.
- `intake.delivery-kind` — the kind of delivery the part ends in, one of the registry's delivery kinds, confirmed for every part with the classification; a type workflow or sub-workflow may set it, and where none does, the kind you confirm with the owner is the part's.
