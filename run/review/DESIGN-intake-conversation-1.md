# Design critique: the intake hotfix (subject `intake-conversation`), round 1

## What is criticised

The Claude-Cursor Bridge is a Claude Code extension that supervises software projects built by a Cursor builder: its governance is text (a core command file and phase modules under `workflow/`) that an AI supervisor reads and follows while talking to the owner, a product manager who is not an engineer. Its installed release is 2026.11.03a. On 2026-11-08 a project supervisor, at intake, put a question about a feature's behaviour to the owner as a list of options it had guessed, in the app's question form (`AskUserQuestion`, a widget whose answer is one tick); the owner rejected the options as too rigid and ruled: the fixed questions that set a project's parameters (private or commercial, platform, product type) may keep the question form, while the software's features and their behaviour are discussed as a conversation, numbered questions in prose answered in the owner's own words, follow-ups building on the answers, never guessed options to tick. The owner ordered the fix as a hotfix of the installed text, between TASK-050's merge and TASK-051 (the inventory row below).

What is criticised is the hotfix's design and its text as written: the Change section (below; it goes into docs/DESIGN.md when the hotfix is carried onto main), the changed passages in their homes, whole (intake.md's procedure, the mockups' procedure, the change cycle's item 1, the core's rule 12, the new KP-075), the places that keep the question form (quoted below as they stand, unchanged), the pinning tests and the text mutants, and the committed diff against the installed stamp. The text is read by an AI supervisor at intake, in a change cycle's intake and in the mockup iteration, after every compaction (the session-start hook names intake.md for re-reading in those phases), so each sentence must carry its rule without the conversation that produced it.

Judge: whether the sorting rule is stated so that a supervisor cannot read a feature question back into the question form (is 'what a question asks' decidable from the text; are the parameter examples a closed enough list; is the doubtful case, a question that is both, settled); whether every place the installed text sends a question to the owner about the software is covered (the design's table and its non-goals name them: are any missed, in the modules, the trait files' `intake.questions` additions, the skills, the escalation list, the explain-for-decision brief); whether any place that keeps the form should not, or any place now a conversation should keep it (the mockup iteration's discrete choices; an escalation about product behaviour mid-build); whether rule 12's bound contradicts rule 12's own sentence, rule 29, the gates or the digest's rule 12, which is not changed (the digest at 9,497 of 9,500 characters); whether the reasons given are the owner's (nothing is relitigated: the rule is the owner's as given) and whether the wording adds anything the owner did not say; whether the trace exceptions and the carve test's count are right and complete; whether the tests pin what the table says and the mutants would catch a regression; whether the CHANGELOG items under Running projects must are enough for a project mid-intake at the install; and whether anything in the hotfix's path (the release branch cut from the installed stamp, the code gate, the stamp, the owner's install, the carry onto main) departs from the two earlier hotfixes' precedent without a stated reason. Security and money: none (text only; no key, no program, no spend). Raise nothing about the two program-reading records (headers, release B2) or about stage H1's increments: they are not this change.

## The owner's rule, as recorded (docs/INVENTORY.md, Decisions)

````markdown
| The intake hotfix comes after TASK-050 merges and before TASK-051 (the owner's order, 2026-11-08, asked in this session in the question form after the maintainer session's report, rule 57): a hotfix of the bridge's text, through the two-critic design review, installed by the owner from a run sheet; its subject, as the maintainer relayed the owner's rule and this session quoted it to the owner: the fixed questions that set the project's parameters (private or commercial, platform, product type) may keep the question form, while the software's features and their behaviour are discussed as a conversation, numbered questions in prose answered in the owner's own words, follow-ups building on the answers, never guessed options to tick; places to check: `workflow/phases/intake.md` ("Ask in batches ... Use `AskUserQuestion` where the answer is a choice"), `phases/change-cycle.md` (a change request interrogated as a new project's description), the form's uses in `phases/interface/mockups.md` and `phases/design.md`, and the core's rule 12 (reports and gates, not intake) | a project supervisor offered guessed feature options at intake on 2026-11-08 and the owner rejected them as too rigid; the installed text leaves each question's sort into choice or open-ended to the supervisor | 2026-11-08 | the owner reorders it |
````

## The record so far

## Subject: intake-conversation (the intake hotfix 2026.11.09a: the software's features and behaviour asked as a conversation, never as guessed options; 2026-11-09)

**What is criticised:** the hotfix's design and its text as written on `hotfix/intake-conversation`, cut from the installed stamp 91c2efb (2026.11.03a) through `release/2026.11.03`: the Change section "the intake hotfix" (written into docs/DESIGN.md at the carry onto main), the changed passages whole in their homes (intake.md's procedure, the mockups' procedure, change-cycle.md's item 1, the core's rule 12, KP-075), the places that keep the question form, the pinning tests (tests/test_hotfix_intake.py) and the text mutants (run/supervisor/HOTFIX-003-mutants.json), and the committed diff against the stamp. The critics read `run/review/DESIGN-intake-conversation-<round>.md`, built from the committed text by run/supervisor/hotfix003_design_file.py, with plan-critic's design-document lenses. The owner's rule (INVENTORY, Decisions, 2026-11-08) is the subject's fixed input: nothing of it is relitigated.

**Accepted** (finding, critic, round, the reason):
- (none yet)

**Rounds** (round, kind, the commit its file was built from, critic, Blocking / Should fix / Consider, what was fixed):

## Grades

- **Blocking**: the design cannot go to its gate with it.
- **Should fix**: the supervisor fixes it or accepts it with a reason.
- **Consider**: worth a thought; no round follows from it.

End with the counts per grade. Four rounds at the most, then a confirming read if the text changed, then one resolution round for what is still open.

## The lenses (from plan-critic.md, the design-document section)

## When reviewing a design document

Attack it along these lines:

- **Unstated assumptions.** What must be true for this design to work that nobody has
  written down?
- **Failure modes.** What happens when the network is down, the disk is full, the
  input is hostile, the dependency is a version behind, two things happen at once?
- **Contradictions.** Does any part of the design conflict with another part, or with
  a stated requirement or constraint?
- **Unjustified choices.** Which technology choices have no reasoning attached, or
  reasoning that does not survive a follow-up question?
- **Scope creep.** What is in this design that no requirement asked for?
- **Scope gaps.** Which stated requirement has nothing in the design serving it? Is every requirement from intake, the owner's requirements document, and the design a row in `docs/REQUIREMENTS.md` with an ID? A requirement that appears in a source but not in the register is **Blocking**.
- **The thing that will hurt in six weeks.** Where is the decision that is cheap now
  and expensive to reverse later?
- **Security criteria.** Does the design address authorization, input validation, and
  secret-handling at each trust boundary? Is the chosen ASVS level recorded, and does it fit
  the data sensitivity? Are the security acceptance criteria it implies actually checkable?
- **Migration policy.** Does the data model state which regime the project is in —
  pre-release (edit the schema definitions, rebuild disposable databases, no migrations) or
  shipped (additive migrations first, destructive only with a data-preserving path) — and
  when it switches? A design that plans destructive migrations on a pre-release, disposable
  database is spending risk for nothing; one that plans schema edits after data exists in
  the field is destroying it. Missing regime: **Should fix**.
- **A worked scenario for money and stored data.** Is every rule about money or stored data read against one worked scenario before it reaches code review: a retry after a lost reply, a dry run, a benchmark, an approved live smoke, two users on one account, each step naming the store it reads and writes? A rule no scenario was walked through is **Should fix**; a step that can charge twice or lose a result is **Blocking**.
- **Performance lens (where budgets exist).** Read `~/.claude/cursor-bridge/Performance-Patterns.md`
  (by that absolute path). For each budget in the design: is a mechanism named that
  plausibly meets it at the stated data size — or does the design walk into a catalogued
  pattern (name the `PP-nnn`): a per-item query or model call in a loop, a full scan where
  an index is implied, recomputation of unchanged values, synchronous IO on a hot path, an
  unbounded collection or cache, work on the interface thread, eager startup, per-item model
  calls where batching or a cheaper model would do? Is the budgeted operation measurable in
  isolation with fixed inputs? A budget with no mechanism behind it is **Blocking**; a
  mechanism that cannot scale to the stated size is **Blocking**.
- **Diagram selection (any project with `docs/diagrams/INDEX.md`).** Read `~/.claude/cursor-bridge/Diagram-Planning-Conventions.md`. Does every omitted catalogue kind have a reason that holds for this design? A kind omitted that the design needs — a lifecycle with no state machine, an external service with no inter-system sequence, stored data with no entity-relationship diagram, secrets or personal data with no data flow diagram and its trust boundaries, more than one module with no component diagram — is **Blocking**.
- **Load-bearing detail.** Does every Level 4-5 diagram's stated reason hold, or is it implementation detail that should stay the builder's (**Should fix**)? Conversely, is a load-bearing mechanism — a concurrency protocol, a reservation scheme, a security flow — described only in prose where a diagram would pin it (**Blocking** when getting it wrong corrupts data or money)?
- **Enforcement.** Would what enforces each normative diagram actually catch drift? `review:` where a deterministic check or tests would work is **Should fix**; a diagram nothing enforces is **Blocking**.
- **Meaning across diagrams.** Contradictions the deterministic check cannot see: a sequence that calls in a direction the component diagram does not allow, a state no transition reaches, an entity no component owns, a data flow that crosses a trust boundary with no validation stated, an operational workflow that reaches a screen the mockup does not have. Each is **Blocking**.

## The design: the Change section (to go into docs/DESIGN.md at the carry), whole

````markdown
## Change: the intake hotfix (2026-11-09) — the software's features and behaviour asked as a conversation, never as guessed options

**Subject** (the critique's token): `intake-conversation`. A hotfix of the installed release 2026.11.03a, text only (no program changes): made on `release/2026.11.03`, cut from the installed stamp (91c2efb), through the two-critic design critique and the code gate, stamped `2026.11.09a`, installed by the owner from a run sheet, then carried onto `main` with its records, as hotfixes 2026.10.18a and 2026.10.25a were (docs/HARDENING.md, their sections). It carries no `handoff/` brief: the supervisor authors governance text (INVENTORY, Decisions, "Governance text is the supervisor's to write"), and its ID in the records is HOTFIX-003.

### Purpose and scope

The owner's rule of 2026-11-08 (INVENTORY, Decisions, row of 2026-11-08): the fixed questions that set a project's parameters (private or commercial, platform, product type) may keep the app's question form, while the software's features and their behaviour are discussed as a conversation — numbered questions in prose, answered in the owner's own words, follow-ups building on the answers — never as guessed options to tick. The installed text leaves each intake question's sort to the supervisor ("Use `AskUserQuestion` where the answer is a choice among options; use plain prose where it is open-ended", intake.md), so a supervisor that can imagine three answers to "how should search work?" is licensed to offer them, and on 2026-11-08 one did; the owner rejected the options as too rigid. The hotfix writes the owner's sorting rule into every place the installed text sends a question to the owner about the software, and bounds the one standing rule that names the form.

**Why a hotfix, not an increment of release B2.** `main` holds stage H1's unreleased programs (TASK-046 to TASK-050), so an install from `main` is refused ("the release folder carries version 2026.11.03a but not its files", bridge-install.py); the running projects, which ask intake questions now, can only receive the text from the installed release's branch. The owner ordered it between TASK-050's merge and TASK-051 (2026-11-08).

### Non-goals

- No change to where the question form is right and already fixed: the kind `private` or `commercial` at intake (intake.md, "The project file"); the design gate's separate decisions and the traits settled there (design.md, "The gate", "Traits at the design gate"); the interface gate (interface.md, "The gate"); the five run parameters (run-parameters.md); a limit's figure (configuration.md); the report cycle's sign-off (evaluate-reports.md); every escalation whose answers exist before the owner speaks (an item that costs money, an irreversible step, a reading of an approved requirement). Each stays as written, and the hotfix's tests pin that they do.
- The digest's rule 12 ("Reports lead with the owner's decision, asked in the question form.") is not changed: the digest stands at 9,497 of its 9,500 characters (tests/test_session_start.py), and the core's rule 12, which the digest summarises, carries the bound; the sorting rule's home is intake.md, which the session-start hook names for re-reading in the intake phase and in a change cycle's intake.
- No program change, no schema, no manifest entry beyond the stamp's regeneration, no change to the conditional workflows' `intake.questions` additions (installable's delivery questions, spends money's cost questions): each addition is asked "with the minimum this module covers" (intake.md, "Extension points"), so the sorting rule governs them as it governs the module's own questions.
- `Documents/` is not written by the hotfix (rule 23): the Guide on Starting Up a New Project says only that intake interrogates the description, which stays true; a sentence on the conversation's form is a reflection-point patch at stage H1's close.
- The explain-for-decision skill's decision brief (a gate's shape) is not changed: it governs how a decision is explained once it exists, and the hotfix changes what is a decision and what is a conversation.

### What changes — the text by home

| Home | Today | After the hotfix |
|---|---|---|
| `workflow/phases/intake.md`, "The procedure", the batches paragraph | Batches; `AskUserQuestion` where the answer is a choice among options, prose where open-ended; stop when a competent implementer could decide the rest | Batches; **the sort is by what a question asks, never by whether its answers can be guessed**: a question about the project's parameters (the kind, the platform and runtime context, the delivery kind, a product type or sub-type between the open list's definitions, a figure) may take the question form, the default or recommended answer first; a question about the software itself (what it does, its features and their behaviour, its users, a case the description leaves open; the gaps, contradictions and better options) is a conversation: numbered questions in prose, batched, answered in the owner's own words, the follow-ups building on the answers, never a list of guessed answers to tick, with the reason (a guessed option frames the feature before the owner has described it, and the answer then measures the guess); the stop rule unchanged |
| `workflow/phases/interface/mockups.md`, "The procedure", the iteration paragraph | Iterate until satisfied; `AskUserQuestion` for discrete choices, plain discussion otherwise | Iterate until satisfied; the iteration is a conversation as intake's questions about the software are (what they would change and why, in their own words, follow-ups on the answers), guessed variants of a screen never put as options to tick; the question form kept for the gate's approval (interface.md, "The gate") and for a parameter in a fixed form a screen turns on |
| `workflow/phases/change-cycle.md`, item 1 | The request interrogated "the same way as a new project's description — gaps, contradictions, better options — but only about the delta" | The same, "and in the same form (intake.md's sorting of questions: the change's features and behaviour as a conversation in the owner's own words, a parameter in the question form)" |
| `commands/supervisor.md`, standing rule 12 | "A decision the owner owns is asked in the question form (the `AskUserQuestion` tool, the recommended option first), so that answering it is one choice." | The sentence kept (R-048's pin), followed by its bound: the form is for a decision between answers that exist before the owner speaks (a gate, a run parameter, a project parameter at intake, an item that costs money, a reading of an approved requirement); what the software should do and how its features behave is asked as a conversation in the owner's own words, never as options the supervisor guessed (intake.md's sorting of questions; the owner's rule of 2026-11-08) |
| `cursor-bridge/Known-Pitfalls.md` | — | KP-075, the pitfall: a question's sort left to the supervisor licenses guessed feature options; the correction is the sorting rule; the sign is an intake or mockup message offering options for a feature the owner has not described |
| `cursor-bridge/workflow/trace-exceptions.md`; `tests/test_core_carve.py` | 83 excused passages | The two reworded baseline passages excused by `reword HOTFIX-003` entries (the core's "Phase 1 — Intake" and "Phase 3 — UI mockups" headings) and the modules' new text by `new HOTFIX-003` entries ("The procedure" of intake.md and of mockups.md); the trace test's count 85 and its two NOTE lines (the intake entry labelled BUG-042, whose earlier entry on the same heading matches first, as TASK-035's precedent records) |
| `cursor-bridge/CHANGELOG.md`, `VERSION`, `MANIFEST.json` (at the stamp, on Opus 5.5) | 2026.11.03a | `## 2026.11.09a` with **What changed** (this table), **Running projects must** (*(intake, mockups, changing)*: from the install, every question still to be asked about the software is asked as the conversation the text now describes, nothing already answered re-asked, a batch already sent in the question form answered as the owner chooses; *(all phases)* install, restart, `/calibrate-bridge`), **If rolled back** (nothing to restore) |

### The host — Claude Code

Unchanged. The question form is the `AskUserQuestion` tool, which the hotfix uses less, not differently; no hook, setting or permission rule changes (the release's host table in "Change: release T" stands).

### Delivery (the trait's Delivery section, scoped to the kind host-installation)

The owner installs from the release branch by the setup guide's three commands, the checkout switched to `release/2026.11.03` instead of `main` (the installer accepts a `release/*` head that is GitHub's merge of a pull request, hotfix 2026.10.25a), with the run sheet's one check, the installer's exit 0 on `RESULT: INSTALLED TREE MATCHES bridge 2026.11.09a`; then the app restarted and `/calibrate-bridge` in each running project. The carry onto `main` follows the install, as HOTFIX-001's did (PR #40): the hotfix's commits applied onto `origin/main`, the records (this section, the critique's block, HARDENING, the inventory's feature row, the status and `project.json` at the new version) in the same pull request, through the code gate.

### Security and secret handling

Nothing new: text only, no secret, no key, no program. The hotfix's public pull requests name no computer path (path_scan before every push).

### Data model and development data

None. The intake notes (`run/supervisor/intake-notes.md`) keep each question and the owner's answer as before, a conversation's answers in the owner's words.

### Testing strategy

Tests first (release T's constraint): `tests/test_hotfix_intake.py` pins every changed sentence in its home (the two sorts and the stop rule in intake.md; the iteration sentence in mockups.md; the clause in change-cycle.md; rule 12's bound; KP-075's heading) and the retirement of the two `AskUserQuestion` sorting sentences; each shown red on the hotfix branch's head before the text (`mutation-run.py --checkpoint`, the per-test lines read), the places that keep the form pinned as invariants (shown strong by the mutants file's text mutants). The trace check runs green at 85 excused with its two NOTE lines (`tests/test_core_carve.py`). The full suite before the first push, with the pull request's variables (P7), since the stamp changes `VERSION`.

### Failure modes

- A supervisor on the installed text keeps offering options: the text leaves it no sort of its own to make, and the sign is named in KP-075; the owner's rejection is the detection, as on 2026-11-08.
- A project mid-intake at the install: the item under **Running projects must** says what changes (the questions still to ask) and what does not (answers given).
- A question that is both (a feature whose shape is a parameter: "which platform" is a parameter; "what the platform build does differently" is the software): the rule sorts by what the question asks, and a doubtful one is asked as a conversation, since a conversation can carry a parameter's answer and the form cannot carry a description.

### Impact on existing behaviour

Intake's questions about the software, the mockup iteration and a change cycle's intake change their form; every gate, run parameter and parameter question keeps the form; no program, record or check changes; no gate reopens, nothing already answered is re-asked.

### Open questions

None for the owner: the rule is theirs as given; the places and the wording are the supervisor's, under the critique.

### Who decided (rule 51)

The rule and the hotfix's order: the owner (2026-11-08, relayed by the maintainer session and confirmed in this session's chat in the question form, rule 57; the order asked in the question form). The places, the wording, the base and the carry: the supervisor, under the two-critic critique.

### Version

The bridge's `2026.11.09a` (a hotfix of 2026.11.03a), stamped on the release branch; `main`'s version line moves with the carry.
````

## The changed passages in their homes, whole

### workflow/phases/intake.md, "The procedure"

````markdown
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

Ask in batches, not one at a time, and sort each question by what it asks, never by whether you could guess its answers. **A question about the project's parameters** — a fact the bridge needs in a fixed form: the kind (`private` or `commercial`), the platform and runtime context, the delivery kind, a part's product type or sub-type where the owner must choose between the open list's definitions, the figure of a budget or a limit — may be asked in the question form (`AskUserQuestion`, the default or the recommended answer first), so that answering it is one choice. **A question about the software itself** — what it does, which features it has and how each behaves, who uses it and how, what happens in a case the description leaves open; the gaps, contradictions and better options above — is a conversation: numbered questions in prose, batched, each answered in the owner's own words, your follow-ups building on their answers; never a list of answers you guessed for the owner to tick, since a guessed option frames the feature before the owner has described it, and their answer then measures your guess, not their intent (the owner's rule of 2026-11-08, after a supervisor offered guessed feature options at intake). Stop asking when the remaining unknowns are ones a competent implementer could decide without you.

Also at intake: **fix the software name** — the name the user will call the product. It
names the four `Documents/` files (see "The project layout") and never changes; if the user
has not named it, propose one and get it confirmed with the summary below. And resolve the
layout: confirm you are in `Workspace/`, that `../Documents` exists (create it if not), and
record them and the software name in `docs/PROJECT_STATUS.md`, the two on its `Layout:` line, relative to the project root and never as a computer path (rule 54).
````

### workflow/phases/interface/mockups.md, "The procedure"

````markdown
### The procedure

After the design is approved and before the build plan, turn the agreed design into
something the user can *see*. Build an HTML/CSS mockup of the interface — a static,
disposable design artifact for the user to judge and change, not the product's real
frontend. Cursor implements the real frontend later, in the delegation loop; this mockup
is upstream of the author/reviewer split, so writing it yourself does not compromise
reviewer independence. It is design documentation, not implementation.

The mockup must map onto the agreed functionality **with no gaps, in both directions**:
every capability in `DESIGN.md` has a visible surface in the mockup, and every element in
the mockup traces back to an agreed capability — no orphan screens implying unspecified
features, no agreed feature with nowhere to live. Walk the design's feature list against
the mockup and account for each item before presenting.

Apply the `design-sense` skill (if installed) when building the mockup: design from the
product rather than a default layout, and actively avoid the tells that make a UI look
machine-generated — including this model's own persistent house style. A mockup that looks
like the generic default is a signal to reconsider, not to present.

Iterate with the user until they are satisfied — expect change requests; this is where UI decisions are cheap to make. The iteration is a conversation, as intake's questions about the software are (`intake.md`, the sorting of questions): ask what they would change and why, numbered where several points are open, answered in their own words, your follow-ups building on the answers; variants of a screen you guessed are never put as options to tick. The question form is kept for the gate's approval (`interface.md`, "The gate") and for a parameter in a fixed form that a screen turns on (the target platform, say).
````

### workflow/phases/change-cycle.md, item 1

````markdown
1. **Intake of the change** (Phase 1, scaled). The session is on Opus 5.5 from the build:
   your first report leads with *set this session to Fable 5.1 before the design work* (rule
   48), and the design gate's report says *back to Opus 5.5*. Interrogate the request the
   same way as a new project's description — gaps, contradictions, better options, and in the same form (intake.md's sorting of questions: the change's features and behaviour as a conversation in the owner's own words, a parameter in the question form) — but only about the
   delta: what changes, what explicitly stays, and the **impact on existing behaviour**
   (which current features, screens, data, or commands the change touches, and whether any
   existing behaviour is altered or removed). Read this project's own Issues file in place
   of the prior-project lessons step: the issues already recorded are the ones this change
   must not repeat. **Verify the inherited "done" before anything else:** run `python ~/.claude/cursor-bridge/completion-check.py --mode done` on the product as it stands. Every failure is a gap in the previous delivery — a requirement never built, a stand-in shipped as a feature — and it is reported to the owner first, plainly, as such ("the previous release was marked complete but R-012 Settings tab was never built"), then planned into this cycle ahead of the new request unless the owner defers it. A project with no register gets one built from its requirements document, design, and mockup before the check runs. A project that became supervised after it was built (its code written before the bridge supervised it) also runs `python ~/.claude/cursor-bridge/conformance-check.py` here, before the first delegation: every `MISSING` floor becomes a configuration increment of the plan addendum, planned ahead of the request's increments, and every `NOTE` is recorded in `PROJECT_STATUS.md` (T12). Read `docs/INVENTORY.md` whole next: a request that
   Features already satisfies is answered by pointing at the feature, not by proposing it;
   a request that reverses a Decision is named as such, with the recorded reason, and goes
   through the gates as a change to that decision. A report of **several defects** is triaged before any of them is diagnosed — the `root-cause-first` skill's step 0: shared cause binned only on evidence, otherwise one at a time. The item ends with a confirmation inside intake, not a gate: `intake.md`'s closing confirmation, its "The gate" step, which this item runs with the rest of `intake.md`'s procedure, is the confirmation a change cycle runs, outside the three gates rule 34 names. Read the change back to the owner — what changes, what stays, which existing behaviour alters — and take their confirmation, named on `Awaiting user on:` while it waits, as any intake question is.
````

### commands/supervisor.md, standing rule 12

````markdown
12. Every report to the user leads with the one decision they own — or "Nothing needed —
    proceeding" — and marks all technical detail as FYI beneath it. Translate consequences
    into behaviour, cost, risk, and reversibility; never hand a non-engineer a technical
    narrative to parse or a technical menu to pick from. A decision the owner owns is asked in the question form (the `AskUserQuestion` tool, the recommended option first), so that answering it is one choice. The form is for a decision between answers that exist before the owner speaks — a gate, a run parameter, a project parameter at intake, an item that costs money, a reading of an approved requirement; what the software should do and how its features behave is asked as a conversation in the owner's own words, never as options you guessed (intake.md's sorting of questions; the owner's rule of 2026-11-08). When several rules claim the first line at once, the order is: a decision the
    owner owns; a key seen in the chat (rule 53); a gate decision you took under rule 50;
    the session model switch (rule 48). The rest follow, each on its own line.
````

### cursor-bridge/Known-Pitfalls.md, KP-075 (new)

````markdown
### KP-075 — A question's sort left to the supervisor licensed guessed feature options at intake
- **Mistake:** at intake, a question about the software's features was put to the owner as a list of options the supervisor had guessed, for them to tick.
- **Surfaced:** a project supervisor, 2026-11-08: asked about a feature's behaviour, it offered guessed options in the app's question form; the owner rejected them as too rigid and ruled that the fixed questions setting a project's parameters (private or commercial, the platform, the product type) may keep the question form, while the software's features and their behaviour are discussed as a conversation, numbered questions in prose answered in the owner's own words, follow-ups building on the answers, never guessed options to tick (the bridge's INVENTORY, Decisions, 2026-11-08).
- **Cause:** the installed intake text sorted a question into the form or prose by whether its answer was a choice among options, which left the sort to the supervisor: any question whose answers it could imagine became a choice, and a guessed option frames the feature before the owner has described it, so the answer measures the guess, not the owner's intent.
- **Correction (2026.11.09a):** the sort is by what a question asks, never by whether its answers can be guessed: a question about the project's parameters (a fact the bridge needs in a fixed form) may take the question form, the default or recommended answer first; a question about the software itself is a conversation in the owner's own words, at intake, in a change cycle's intake and in the mockup iteration alike (intake.md, change-cycle.md item 1, interface/mockups.md); the core's rule 12 bounds the form to a decision between answers that exist before the owner speaks (a gate, a run parameter, a project parameter, an item that costs money, a reading of an approved requirement).
- **Applies:** every intake, every change cycle's intake, every mockup iteration, every escalation about product behaviour. The sign: a message to the owner offering options for a feature they have not yet described, or an intake batch whose feature questions carry answer lists.
````

## The places that keep the question form, as they stand (unchanged)

### intake.md, the project file (the kind)

````markdown
**The project file.** Intake ends with `project.json` at the Workspace root, the one place
that states the project's fundamentals succinctly for people and programs: `name`, `purpose`
(one sentence), `kind` (`private` or `commercial`), `version` (the product's current version,
`0.0.0` until a release), and `state` (`phase`, `stage`, `bridge`, `updated`). The one thing in
it the owner is asked is the kind, as its own question in the question form, `private` named
first as the default, with its one effect stated: it is recorded for the owner and for later
tools and changes nothing in how the bridge builds; it is never a licence question. You keep the file current
at every phase change and every stage close (the reflection points); the conformance check
reports a missing or stale one (release A2, the owner's requirement of 2026-10-10).
````

### design.md, the gate

````markdown
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
````

### design.md, traits at the design gate (its first paragraph)

````markdown
The traits proposed at intake, the default traits of each part's product type and sub-type among them, are settled at this gate (intake's "Classifying each part"). Before presenting the design, weigh each part's traits again against the open list's definitions (`~/.claude/cursor-bridge/workflow/open-list.md`) in the light of the design: a trait the design now shows is added (the product needs accounts: *personal data*), and a proposed or default trait the design shows does not apply is dropped, each with its reason. At the gate each part's traits are a decision of their own, asked in the question form beside the separate decisions the gate below lists: each trait with its definition in one line and, in plain words, the work it adds. Once the owner has settled them, rewrite the part's `Workflows:` line if they changed, and run `python ~/.claude/cursor-bridge/workflow-check.py --status docs/PROJECT_STATUS.md` again.
````

### interface.md, the gate

````markdown
### The gate

**Gate:** present each variant's artifact to the owner and get explicit approval of each before writing the build plan; each variant's file says what its artifact is and what its own gate requires. Do not proceed while any variant a part runs is unapproved. Present them as a decision brief (`explain-for-decision` skill), each variant's approval asked as a question of its own in the app's question form, with every part that runs no variant named in one line beside them. When no part runs any variant, the gate still asks the owner's word, that no part has an interface to judge before the build (rule 5). The phase passes when every variant every part runs is approved.
````

### run-parameters.md, the procedure's opening

````markdown
### The procedure

The plan says *what* will be built; the run parameters say *how the loop proceeds* while
building it. They are the owner's settings, asked **once, right after the plan gate and
before Phase 5, each as a question of its own in the app's question form** (`AskUserQuestion`,
the default named first, each explained under the `explain-for-decision` skill), never as
one combined brief (rule 29). The parameters:
````

### configuration.md, the limit's figure

````markdown
row without one. A limit the owner names is theirs: ask for the figure in the question form.
````

### supervisor.md, rule 29

````markdown
29. The five run parameters — `Stage pause`, `Merge authority`, `Refactoring pass`, `Installer verification`, `Parallel increments` — are asked
    once, right after the plan is approved, each as a question of its own in the app's
    question form (`AskUserQuestion`, the default named first), and recorded in
    `docs/RUN_PARAMETERS.md`, read at every resume, stage close, and merge. A stage close
    never waits by itself: under `run` (the default) you report and continue in the same
    turn; only `pause`, the escalation list, or project end stops the loop. Under
    `Merge authority: owner` you stop at READY TO MERGE with the evidence and never arm
    auto-merge. No parameter loosens the gate, and the escalation list holds under every
    setting. The owner may change a parameter at any time by saying so.
````

### the digest's rule 12 (supervisor.md, the digest; 9,497 of 9,500 characters)

````markdown
**Standing rules.** 1 Never write implementation code. 2 Never delegate from a dirty tree. 3 No secret in a prompt. 4 Never skip the secret scan. 5 Never pass a phase gate without the owner's approval or the words of rule 50. 6 Re-delegation ends by defect class, whatever operator showed it; from round three (program-held) only the five blocking classes send work back, the rest to HARDENING; stop only on non-convergence. A design critique stops after four rounds, a due confirming read and resolution round, whatever is open. 7 Report what actually happened, reverts and wrong-reason passes included. 8 Never chain or wrap shell commands; `bridge-run.py` is the only launcher; bridge commands in the Bash tool. 9 Merge only on the full gate. 10 Correctness is never the owner's question. 11 A hard technical question goes to a resolution round. 12 Reports lead with the owner's decision, asked in the question form. 13 Design correctness is the gate's (N7). 14 Security correctness is the gate's; pin scanners and actions by SHA; never auto-adopt an update. 15 Read the patterns and pitfalls where they apply; record lessons as `ISS-nnn`; probe Cursor capabilities first. 16 The running render is part of the gate (N9). 17 The delegate command is a constant pointer to the committed brief. 18 The builder's self-report is a hint; status comes from git and `scope-check.py`; drift never passes. 19 Only `worktree-teardown.py` removes a worktree; never `git worktree remove`. 20 Context economy: slice large low-stakes material; gate-critical streams reach reviewers whole. 21 Explain for decision. 22 The layout is fixed: `Documents/` beside `Workspace/`. 23 `Documents/` is written only at reflection points. 24 Windowless by default. 25 Refactoring only in the stage-close pass. 26 Root cause first: no reproduction, no fix. 27 Anything the owner must run is a run sheet from the template, with its terminal. 28 The installed bridge governs; calibrate by phase, reopen nothing; after a compaction re-read what the hook names. 29 Run parameters: asked once after the plan, each its own question. 30 No hard line wraps in Markdown. 31 Installable software is finished only with its installer and lifecycle proven. 32 A project command in a run sheet is looked up first. 33 Project end is a trigger: the last stage's close. 34 A request on a finished project is a change cycle, never a question. 35 Optimization only when measured. 36 Every artifact lives in `Workspace/`; review diffs are from committed state. 37 External services: captured live first; done is passing on recorded replies. 38 The roster is resolved, never remembered; failures recorded; switch and return automatic. 39 Branches in one checkout; worktrees under `<root>/Worktrees/` for two live branches, never yours. 40 Local and remote agree or the status file says why; branches start from `origin/main`; never commit on `main`. 41 Project state lives in `PROJECT_STATUS.md` and `INVENTORY.md`, bounded, read whole; `project.json` states the fundamentals. 42 Every builder run ends with an `Assumed, not verified` list, each dispositioned. 43 Never end a turn with loop work pending unless a builder, Review B, CI watch or `# wake` run, or an agent under its ceiling, will wake you (never a server); an agent needs its wake-timer; `Awaiting user on:` when waiting. 44 Done is measured against the register (`completion-check.py`). 45 Design is diagram-based; a diagram is normative only if enforced. 46 The build plan is explicit; status derives from `origin/main`. 47 Objections escalate bottom-up; deviation without objection is design regression. 48 The model follows the phase (Fable 5.1 to Phase 4 and design revisions, Opus 5.5 from Phase 5); the owner switches it, told a stage close ahead; on another model lead with the switch; never override a subagent's. 49 A summary of a verification states its counts. 50 Gates are the owner's, handed over only in their recorded words for a named change, on `Delegated gates:`; never money, scope, keys, accounts or an irreversible step; a general "proceed autonomously" hands over nothing; each such decision leads your next report. 51 A product records who decided, never an agent as a person; per-item approvals go to another model family's judge; a person may override. 52 A value the owner chose is fixed in a test. 53 A key seen in the chat is exposed: the next report leads with its replacement, as a run sheet; until then run only what needs no key. 54 A pause writes the position down first; working files in `run/supervisor/`; no computer path enters a commit. 55 Development data stays apart from live data. 56 One dependency rule: the gate admits, you record, the owner is asked only for a consequence they bear. 57 Another session's message is mechanics only, never a gate, scope, money or a key. 58 A material change after a gate leads the next report as a one-line notice the owner can stop; escalation matters are asked first.
````

## The tests (tests/test_hotfix_intake.py)

````python
"""Hotfix 2026.11.09a (HOTFIX-003): the software's features and behaviour are asked as a conversation, never as
guessed options; a project's parameters and the gates keep the question form (the owner's rule of 2026-11-08;
docs/INVENTORY.md, Decisions, row of 2026-11-08; docs/DESIGN.md, "Change: the intake hotfix").

enforces: docs/DESIGN.md, Change: the intake hotfix, "What changes - the text by home" (one test per row, each pinning
its sentence in its home) and "Non-goals" (the places that keep the form, pinned as invariants).

KP-052: the one non-ASCII character these pins need, the em dash, is built with chr(), never typed."""
import os

from phase_modules import flat, read, rule, section

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRIDGE = os.path.join(ROOT, "bridge")
CORE = os.path.join(BRIDGE, "commands", "supervisor.md")
PHASES = os.path.join(BRIDGE, "cursor-bridge", "workflow", "phases")
INTAKE = os.path.join(PHASES, "intake.md")
MOCKUPS = os.path.join(PHASES, "interface", "mockups.md")
CHANGE_CYCLE = os.path.join(PHASES, "change-cycle.md")
DESIGN = os.path.join(PHASES, "design.md")
INTERFACE = os.path.join(PHASES, "interface.md")
RUN_PARAMETERS = os.path.join(PHASES, "run-parameters.md")
PITFALLS = os.path.join(BRIDGE, "cursor-bridge", "Known-Pitfalls.md")
DASH = chr(0x2014)


def item(text, number, label):
    """A numbered item of a procedure list, from `<number>. **<label>**` to the next item."""
    start = text.index("\n%d. **%s**" % (number, label))
    end = text.index("\n%d. **" % (number + 1), start)
    return flat(text[start:end])


# --- intake.md, "The procedure": the sorting of questions

def test_hotfix003_intake_sorts_a_question_by_what_it_asks():
    procedure = flat(section(read(INTAKE), "The procedure", 3))
    assert ("Ask in batches, not one at a time, and sort each question by what it asks, never by whether you could "
            "guess its answers.") in procedure


def test_hotfix003_intake_a_parameter_question_may_take_the_question_form():
    procedure = flat(section(read(INTAKE), "The procedure", 3))
    assert ("**A question about the project's parameters** " + DASH + " a fact the bridge needs in a fixed form: the "
            "kind (`private` or `commercial`), the platform and runtime context, the delivery kind, a part's product "
            "type or sub-type where the owner must choose between the open list's definitions, the figure of a budget "
            "or a limit " + DASH + " may be asked in the question form (`AskUserQuestion`, the default or the "
            "recommended answer first), so that answering it is one choice.") in procedure


def test_hotfix003_intake_a_question_about_the_software_is_a_conversation():
    procedure = flat(section(read(INTAKE), "The procedure", 3))
    assert ("**A question about the software itself** " + DASH + " what it does, which features it has and how each "
            "behaves, who uses it and how, what happens in a case the description leaves open; the gaps, contradictions "
            "and better options above " + DASH + " is a conversation: numbered questions in prose, batched, each "
            "answered in the owner's own words, your follow-ups building on their answers; never a list of answers you "
            "guessed for the owner to tick, since a guessed option frames the feature before the owner has described "
            "it, and their answer then measures your guess, not their intent (the owner's rule of 2026-11-08, after a "
            "supervisor offered guessed feature options at intake).") in procedure


def test_hotfix003_intake_the_stop_rule_stays_and_the_old_sort_is_gone():
    procedure = flat(section(read(INTAKE), "The procedure", 3))
    assert ("Stop asking when the remaining unknowns are ones a competent implementer could decide without you.") in procedure
    assert "where the answer is a choice among options" not in procedure
    assert "use plain prose where it is open-ended" not in procedure


# --- mockups.md, "The procedure": the iteration

def test_hotfix003_the_mockup_iteration_is_a_conversation():
    procedure = flat(section(read(MOCKUPS), "The procedure", 3))
    assert ("Iterate with the user until they are satisfied " + DASH + " expect change requests; this is where UI "
            "decisions are cheap to make. The iteration is a conversation, as intake's questions about the software "
            "are (`intake.md`, the sorting of questions): ask what they would change and why, numbered where several "
            "points are open, answered in their own words, your follow-ups building on the answers; variants of a "
            "screen you guessed are never put as options to tick. The question form is kept for the gate's approval "
            "(`interface.md`, \"The gate\") and for a parameter in a fixed form that a screen turns on (the target "
            "platform, say).") in procedure
    assert "for discrete choices" not in procedure


# --- change-cycle.md, item 1: the change's intake in the same form

def test_hotfix003_a_change_is_interrogated_in_the_same_form():
    text = read(CHANGE_CYCLE)
    assert ("Interrogate the request the same way as a new project's description " + DASH + " gaps, contradictions, "
            "better options, and in the same form (intake.md's sorting of questions: the change's features and "
            "behaviour as a conversation in the owner's own words, a parameter in the question form) " + DASH + " but "
            "only about the delta") in item(text, 1, "Intake of the change")


# --- the core's rule 12: the form's bound

def test_hotfix003_rule_12_bounds_the_question_form():
    text = rule(12)
    assert ("A decision the owner owns is asked in the question form (the `AskUserQuestion` tool, the recommended "
            "option first), so that answering it is one choice.") in text
    assert ("The form is for a decision between answers that exist before the owner speaks " + DASH + " a gate, a run "
            "parameter, a project parameter at intake, an item that costs money, a reading of an approved requirement; "
            "what the software should do and how its features behave is asked as a conversation in the owner's own "
            "words, never as options you guessed (intake.md's sorting of questions; the owner's rule of 2026-11-08).") in text


# --- Known-Pitfalls: KP-075

def test_hotfix003_kp075_names_the_pitfall_and_its_sign():
    text = read(PITFALLS)
    assert "### KP-075 " + DASH + " A question's sort left to the supervisor licensed guessed feature options at intake" in text
    entry = text[text.index("### KP-075"):]
    assert "**Correction (2026.11.09a):**" in entry
    assert "The sign:" in entry


# --- the places that keep the form (invariants of the hotfix's non-goals)

def test_hotfix003_the_kind_the_gates_and_the_run_parameters_keep_the_form():
    assert ("it the owner is asked is the kind, as its own question in the question form, `private` named") in read(INTAKE)
    assert ("each asked as a question of its own in the app's question form") in flat(read(DESIGN))
    assert ("each part's traits are a decision of their own, asked in the question form") in flat(read(DESIGN))
    assert "question form" in flat(section(read(INTERFACE), "The gate", 3))
    assert ("each as a question of its own in the app's question form** (`AskUserQuestion`,") in flat(read(RUN_PARAMETERS))
````

## The text mutants (run/supervisor/HOTFIX-003-mutants.json)

````json
{
 "mutants": [
  {
   "id": "i01",
   "file": "bridge/cursor-bridge/workflow/phases/intake.md",
   "pairs": [
    {
     "old": "sort each question by what it asks, never by whether you could guess its answers",
     "new": "sort each question by whether its answer is a choice among options"
    }
   ],
   "tests": [
    "tests/test_hotfix_intake.py"
   ],
   "expect_fail": [
    "tests/test_hotfix_intake.py::test_hotfix003_intake_sorts_a_question_by_what_it_asks"
   ]
  },
  {
   "id": "i02",
   "file": "bridge/cursor-bridge/workflow/phases/intake.md",
   "pairs": [
    {
     "old": "may be asked in the question form (`AskUserQuestion`, the default or the recommended answer first)",
     "new": "is asked in the question form (`AskUserQuestion`, the default or the recommended answer first)"
    }
   ],
   "tests": [
    "tests/test_hotfix_intake.py"
   ],
   "expect_fail": [
    "tests/test_hotfix_intake.py::test_hotfix003_intake_a_parameter_question_may_take_the_question_form"
   ]
  },
  {
   "id": "i03",
   "file": "bridge/cursor-bridge/workflow/phases/intake.md",
   "pairs": [
    {
     "old": "never a list of answers you guessed for the owner to tick",
     "new": "or a list of answers you guessed for the owner to tick where that is quicker"
    }
   ],
   "tests": [
    "tests/test_hotfix_intake.py"
   ],
   "expect_fail": [
    "tests/test_hotfix_intake.py::test_hotfix003_intake_a_question_about_the_software_is_a_conversation"
   ]
  },
  {
   "id": "i04",
   "file": "bridge/cursor-bridge/workflow/phases/intake.md",
   "pairs": [
    {
     "old": "each answered in the owner's own words, your follow-ups building on their answers",
     "new": "each answered as the owner likes"
    }
   ],
   "tests": [
    "tests/test_hotfix_intake.py"
   ],
   "expect_fail": [
    "tests/test_hotfix_intake.py::test_hotfix003_intake_a_question_about_the_software_is_a_conversation"
   ]
  },
  {
   "id": "i05",
   "file": "bridge/cursor-bridge/workflow/phases/intake.md",
   "pairs": [
    {
     "old": "Stop asking when the remaining unknowns are ones a competent implementer could decide without you.",
     "new": "Stop asking when every unknown is settled."
    }
   ],
   "tests": [
    "tests/test_hotfix_intake.py"
   ],
   "expect_fail": [
    "tests/test_hotfix_intake.py::test_hotfix003_intake_the_stop_rule_stays_and_the_old_sort_is_gone"
   ]
  },
  {
   "id": "m01",
   "file": "bridge/cursor-bridge/workflow/phases/interface/mockups.md",
   "pairs": [
    {
     "old": "variants of a screen you guessed are never put as options to tick",
     "new": "variants of a screen you guessed may be put as options to tick"
    }
   ],
   "tests": [
    "tests/test_hotfix_intake.py"
   ],
   "expect_fail": [
    "tests/test_hotfix_intake.py::test_hotfix003_the_mockup_iteration_is_a_conversation"
   ]
  },
  {
   "id": "m02",
   "file": "bridge/cursor-bridge/workflow/phases/interface/mockups.md",
   "pairs": [
    {
     "old": "The question form is kept for the gate's approval (`interface.md`, \"The gate\")",
     "new": "The question form is kept for every discrete choice"
    }
   ],
   "tests": [
    "tests/test_hotfix_intake.py"
   ],
   "expect_fail": [
    "tests/test_hotfix_intake.py::test_hotfix003_the_mockup_iteration_is_a_conversation"
   ]
  },
  {
   "id": "c01",
   "file": "bridge/cursor-bridge/workflow/phases/change-cycle.md",
   "pairs": [
    {
     "old": "and in the same form (intake.md's sorting of questions: the change's features and behaviour as a conversation in the owner's own words, a parameter in the question form) \u2014 but only about the",
     "new": "\u2014 but only about the"
    }
   ],
   "tests": [
    "tests/test_hotfix_intake.py"
   ],
   "expect_fail": [
    "tests/test_hotfix_intake.py::test_hotfix003_a_change_is_interrogated_in_the_same_form"
   ]
  },
  {
   "id": "r01",
   "file": "bridge/commands/supervisor.md",
   "pairs": [
    {
     "old": "never as options you guessed (intake.md's sorting of questions; the owner's rule of 2026-11-08)",
     "new": "or as options you guessed where the owner has not described it"
    }
   ],
   "tests": [
    "tests/test_hotfix_intake.py"
   ],
   "expect_fail": [
    "tests/test_hotfix_intake.py::test_hotfix003_rule_12_bounds_the_question_form"
   ]
  },
  {
   "id": "r02",
   "file": "bridge/commands/supervisor.md",
   "pairs": [
    {
     "old": "The form is for a decision between answers that exist before the owner speaks",
     "new": "The form is for every decision the owner owns"
    }
   ],
   "tests": [
    "tests/test_hotfix_intake.py"
   ],
   "expect_fail": [
    "tests/test_hotfix_intake.py::test_hotfix003_rule_12_bounds_the_question_form"
   ]
  },
  {
   "id": "k01",
   "file": "bridge/cursor-bridge/Known-Pitfalls.md",
   "pairs": [
    {
     "old": "### KP-075 \u2014 A question's sort left to the supervisor licensed guessed feature options at intake",
     "new": "### KP-075 \u2014 Guessed feature options at intake"
    }
   ],
   "tests": [
    "tests/test_hotfix_intake.py"
   ],
   "expect_fail": [
    "tests/test_hotfix_intake.py::test_hotfix003_kp075_names_the_pitfall_and_its_sign"
   ]
  }
 ],
 "new_tests": [
  "tests/test_hotfix_intake.py::test_hotfix003_intake_sorts_a_question_by_what_it_asks",
  "tests/test_hotfix_intake.py::test_hotfix003_intake_a_parameter_question_may_take_the_question_form",
  "tests/test_hotfix_intake.py::test_hotfix003_intake_a_question_about_the_software_is_a_conversation",
  "tests/test_hotfix_intake.py::test_hotfix003_intake_the_stop_rule_stays_and_the_old_sort_is_gone",
  "tests/test_hotfix_intake.py::test_hotfix003_the_mockup_iteration_is_a_conversation",
  "tests/test_hotfix_intake.py::test_hotfix003_a_change_is_interrogated_in_the_same_form",
  "tests/test_hotfix_intake.py::test_hotfix003_rule_12_bounds_the_question_form",
  "tests/test_hotfix_intake.py::test_hotfix003_kp075_names_the_pitfall_and_its_sign"
 ],
 "untracked": []
}
````

## The committed diff of the text against the installed stamp (91c2efb)

````diff
diff --git a/bridge/commands/supervisor.md b/bridge/commands/supervisor.md
index 09f140a..b9090fb 100644
--- a/bridge/commands/supervisor.md
+++ b/bridge/commands/supervisor.md
@@ -557,7 +557,7 @@ has to ride PRs to reach the remote; decide per project which you need and keep
 12. Every report to the user leads with the one decision they own — or "Nothing needed —
     proceeding" — and marks all technical detail as FYI beneath it. Translate consequences
     into behaviour, cost, risk, and reversibility; never hand a non-engineer a technical
-    narrative to parse or a technical menu to pick from. A decision the owner owns is asked in the question form (the `AskUserQuestion` tool, the recommended option first), so that answering it is one choice. When several rules claim the first line at once, the order is: a decision the
+    narrative to parse or a technical menu to pick from. A decision the owner owns is asked in the question form (the `AskUserQuestion` tool, the recommended option first), so that answering it is one choice. The form is for a decision between answers that exist before the owner speaks — a gate, a run parameter, a project parameter at intake, an item that costs money, a reading of an approved requirement; what the software should do and how its features behave is asked as a conversation in the owner's own words, never as options you guessed (intake.md's sorting of questions; the owner's rule of 2026-11-08). When several rules claim the first line at once, the order is: a decision the
     owner owns; a key seen in the chat (rule 53); a gate decision you took under rule 50;
     the session model switch (rule 48). The rest follow, each on its own line.
 13. Design correctness — accessibility and interface MUSTs, plus the deterministic
diff --git a/bridge/cursor-bridge/Known-Pitfalls.md b/bridge/cursor-bridge/Known-Pitfalls.md
index 0d4b1be..ee2c03d 100644
--- a/bridge/cursor-bridge/Known-Pitfalls.md
+++ b/bridge/cursor-bridge/Known-Pitfalls.md
@@ -622,3 +622,10 @@ it applies.**
 - **Surfaced:** the bridge, 2026-10-30 (ISS-022, TASK-027's stamp): two tests every local run passed failed on CI, one gated on the GitHub pull-request variables and so skipped locally, one in a file no local selection included.
 - **Correction:** before the first push of a pull request that changes `docs/PROJECT_STATUS.md`, `project.json` or a `VERSION`, the full suite runs once with `GITHUB_REF=refs/pull/<n>/merge`, `GITHUB_BASE_REF=main` and `GITHUB_EVENT_NAME=pull_request` set for the launcher's run, through a key file outside the Workspace (`--key-file`); a test gated on those variables names the gate in its skip reason.
 - **Applies:** every pull request that changes the status file, `project.json` or a `VERSION`. The sign: a test skipped locally that CI runs.
+
+### KP-075 — A question's sort left to the supervisor licensed guessed feature options at intake
+- **Mistake:** at intake, a question about the software's features was put to the owner as a list of options the supervisor had guessed, for them to tick.
+- **Surfaced:** a project supervisor, 2026-11-08: asked about a feature's behaviour, it offered guessed options in the app's question form; the owner rejected them as too rigid and ruled that the fixed questions setting a project's parameters (private or commercial, the platform, the product type) may keep the question form, while the software's features and their behaviour are discussed as a conversation, numbered questions in prose answered in the owner's own words, follow-ups building on the answers, never guessed options to tick (the bridge's INVENTORY, Decisions, 2026-11-08).
+- **Cause:** the installed intake text sorted a question into the form or prose by whether its answer was a choice among options, which left the sort to the supervisor: any question whose answers it could imagine became a choice, and a guessed option frames the feature before the owner has described it, so the answer measures the guess, not the owner's intent.
+- **Correction (2026.11.09a):** the sort is by what a question asks, never by whether its answers can be guessed: a question about the project's parameters (a fact the bridge needs in a fixed form) may take the question form, the default or recommended answer first; a question about the software itself is a conversation in the owner's own words, at intake, in a change cycle's intake and in the mockup iteration alike (intake.md, change-cycle.md item 1, interface/mockups.md); the core's rule 12 bounds the form to a decision between answers that exist before the owner speaks (a gate, a run parameter, a project parameter, an item that costs money, a reading of an approved requirement).
+- **Applies:** every intake, every change cycle's intake, every mockup iteration, every escalation about product behaviour. The sign: a message to the owner offering options for a feature they have not yet described, or an intake batch whose feature questions carry answer lists.
diff --git a/bridge/cursor-bridge/workflow/phases/change-cycle.md b/bridge/cursor-bridge/workflow/phases/change-cycle.md
index aadee63..03f49b3 100644
--- a/bridge/cursor-bridge/workflow/phases/change-cycle.md
+++ b/bridge/cursor-bridge/workflow/phases/change-cycle.md
@@ -23,7 +23,7 @@ Keep the step the change has reached on the `Change cycle:` line, rewritten as e
 1. **Intake of the change** (Phase 1, scaled). The session is on Opus 5.5 from the build:
    your first report leads with *set this session to Fable 5.1 before the design work* (rule
    48), and the design gate's report says *back to Opus 5.5*. Interrogate the request the
-   same way as a new project's description — gaps, contradictions, better options — but only about the
+   same way as a new project's description — gaps, contradictions, better options, and in the same form (intake.md's sorting of questions: the change's features and behaviour as a conversation in the owner's own words, a parameter in the question form) — but only about the
    delta: what changes, what explicitly stays, and the **impact on existing behaviour**
    (which current features, screens, data, or commands the change touches, and whether any
    existing behaviour is altered or removed). Read this project's own Issues file in place
diff --git a/bridge/cursor-bridge/workflow/phases/intake.md b/bridge/cursor-bridge/workflow/phases/intake.md
index cbef5a4..0f5aee6 100644
--- a/bridge/cursor-bridge/workflow/phases/intake.md
+++ b/bridge/cursor-bridge/workflow/phases/intake.md
@@ -64,9 +64,7 @@ and integrations**. From the data sensitivity, choose the **OWASP ASVS level** 
 gated against. This is what lets the build plan, the brief, and the `security-auditor`
 reason about IDOR/authz/data-handling later.
 
-Ask in batches, not one at a time. Use `AskUserQuestion` where the answer is a
-choice among options; use plain prose where it is open-ended. Stop asking when the
-remaining unknowns are ones a competent implementer could decide without you.
+Ask in batches, not one at a time, and sort each question by what it asks, never by whether you could guess its answers. **A question about the project's parameters** — a fact the bridge needs in a fixed form: the kind (`private` or `commercial`), the platform and runtime context, the delivery kind, a part's product type or sub-type where the owner must choose between the open list's definitions, the figure of a budget or a limit — may be asked in the question form (`AskUserQuestion`, the default or the recommended answer first), so that answering it is one choice. **A question about the software itself** — what it does, which features it has and how each behaves, who uses it and how, what happens in a case the description leaves open; the gaps, contradictions and better options above — is a conversation: numbered questions in prose, batched, each answered in the owner's own words, your follow-ups building on their answers; never a list of answers you guessed for the owner to tick, since a guessed option frames the feature before the owner has described it, and their answer then measures your guess, not their intent (the owner's rule of 2026-11-08, after a supervisor offered guessed feature options at intake). Stop asking when the remaining unknowns are ones a competent implementer could decide without you.
 
 Also at intake: **fix the software name** — the name the user will call the product. It
 names the four `Documents/` files (see "The project layout") and never changes; if the user
diff --git a/bridge/cursor-bridge/workflow/phases/interface/mockups.md b/bridge/cursor-bridge/workflow/phases/interface/mockups.md
index 4f8f266..62aab7d 100644
--- a/bridge/cursor-bridge/workflow/phases/interface/mockups.md
+++ b/bridge/cursor-bridge/workflow/phases/interface/mockups.md
@@ -24,9 +24,7 @@ product rather than a default layout, and actively avoid the tells that make a U
 machine-generated — including this model's own persistent house style. A mockup that looks
 like the generic default is a signal to reconsider, not to present.
 
-Iterate with the user until they are satisfied — expect change requests; this is where UI
-decisions are cheap to make. Use `AskUserQuestion` for discrete choices, plain discussion
-otherwise.
+Iterate with the user until they are satisfied — expect change requests; this is where UI decisions are cheap to make. The iteration is a conversation, as intake's questions about the software are (`intake.md`, the sorting of questions): ask what they would change and why, numbered where several points are open, answered in their own words, your follow-ups building on the answers; variants of a screen you guessed are never put as options to tick. The question form is kept for the gate's approval (`interface.md`, "The gate") and for a parameter in a fixed form that a screen turns on (the target platform, say).
 
 ### The design-tooling flow
 
diff --git a/bridge/cursor-bridge/workflow/trace-exceptions.md b/bridge/cursor-bridge/workflow/trace-exceptions.md
index b2774dd..4a48d0f 100644
--- a/bridge/cursor-bridge/workflow/trace-exceptions.md
+++ b/bridge/cursor-bridge/workflow/trace-exceptions.md
@@ -194,3 +194,7 @@ Entries use the form `- <kind> <id> <file> <heading>` where `<kind>` is `reword`
 - new BUG-042 bridge/cursor-bridge/workflow/phases/intake.md The procedure
 - new BUG-042 bridge/cursor-bridge/workflow/phases/configuration.md The procedure
 - new BUG-043 bridge/cursor-bridge/workflow/phases/delegation-loop.md 4. Inspect
+- reword HOTFIX-003 bridge/commands/supervisor.md Phase 1 — Intake
+- new HOTFIX-003 bridge/cursor-bridge/workflow/phases/intake.md The procedure
+- reword HOTFIX-003 bridge/commands/supervisor.md Phase 3 — UI mockups
+- new HOTFIX-003 bridge/cursor-bridge/workflow/phases/interface/mockups.md The procedure
diff --git a/tests/test_core_carve.py b/tests/test_core_carve.py
index c14037e..c69d294 100644
--- a/tests/test_core_carve.py
+++ b/tests/test_core_carve.py
@@ -175,7 +175,10 @@ def test_r003_a_module_read_outside_its_own_phase_is_named_with_when():
 # (BUG-043: four more move from traced to excused, which the earlier entries excuse: step 3's parallel item 4, under
 # TASK-030's, and step 3b's exit-124 paragraph and restart item and step 7's last-resort reset, under TASK-034's: each
 # now says step 4's read of `.git/config` comes before its git command)
-TRACED = "TRACED: 424 passages of baseline 0a186da; 138 in supervisor.md, 203 under workflow/, 0 dropped, 83 excused"
+# (HOTFIX-003, hotfix 2026.11.09a: two more move from traced to excused, under HOTFIX-003's own `reword` entries:
+# intake's batches paragraph, which now sorts a question by what it asks (labelled BUG-042, whose earlier entry on
+# "Phase 1 — Intake" matches first), and the mockups' iteration paragraph, under "Phase 3 — UI mockups")
+TRACED = "TRACED: 424 passages of baseline 0a186da; 138 in supervisor.md, 201 under workflow/, 0 dropped, 85 excused"
 NOTES = [
     "NOTE (reword TASK-034) bridge/commands/supervisor.md: The core, in brief - **Role.** The supervising architect: design, plan, package b",
     "NOTE (reword TASK-034) bridge/commands/supervisor.md: The core, in brief - **Founding rules.** N1 The loop's truth lives in files; one-",
@@ -186,6 +189,7 @@ NOTES = [
     "NOTE (reword TASK-010) bridge/commands/supervisor.md: Main and conditional workflows - Until the phases are moved into files of their own, each pha",
     "NOTE (reword TASK-010) bridge/commands/supervisor.md: Main and conditional workflows - **The order additions apply in.** Additions from several con",
     "NOTE (reword TASK-035) bridge/commands/supervisor.md: The project layout - You work in `Workspace/`; `Documents/` is its sibling (`../D",
+    "NOTE (reword BUG-042) bridge/commands/supervisor.md: Phase 1 \\u2014 Intake - Ask in batches, not one at a time. Use `AskUserQuestion` whe",
     "NOTE (reword BUG-042) bridge/commands/supervisor.md: Phase 1 \\u2014 Intake - Also at intake: **fix the software name** \\u2014 the name the use",
     "NOTE (reword TASK-012) bridge/commands/supervisor.md: Phase 2 \\u2014 Design - For every **performance or cost budget** the design names th",
     "NOTE (reword TASK-012) bridge/commands/supervisor.md: Phase 2 \\u2014 Design - ```bash\\x0apython ~/.claude/cursor-bridge/bridge-run.py --limit",
@@ -195,6 +199,7 @@ NOTES = [
     "NOTE (reword TASK-012) bridge/commands/supervisor.md: Phase 2 \\u2014 Design - `docs/DESIGN_CRITIQUE.md` has three parts, one block per sub",
     "NOTE (reword TASK-012) bridge/commands/supervisor.md: Phase 2 \\u2014 Design - Also for a UI-bearing project, add an **\"Observability & Ver",
     "NOTE (reword TASK-012) bridge/commands/supervisor.md: Phase 2 \\u2014 Design - **Gate:** present the design to the user. Do not proceed to ",
+    "NOTE (reword HOTFIX-003) bridge/commands/supervisor.md: Phase 3 \\u2014 UI mockups - Iterate with the user until they are satisfied \\u2014 expect chan",
     "NOTE (reword TASK-012) bridge/commands/supervisor.md: The design-tooling flow - Save the mockup files under `docs/mockups/` (one file per sc",
     "NOTE (reword TASK-035) bridge/commands/supervisor.md: The plan - Give each one an ID (`TASK-001`, `TASK-002`, \\u2026). Group the i",
     "NOTE (reword TASK-035) bridge/commands/supervisor.md: Run parameters \\u2014 asked once, after the plan is approved, before configuration - - `run` *(default)* \\u2014 report the stage close as a notificati",
@@ -275,6 +280,8 @@ def test_r003_the_carve_traces_with_exactly_its_excuses():
     pass's step 6 and rule 39; and five passages BUG-033 reworded, which those entries excuse: the refactoring
     pass's step 4 and the run parameters' Parallel increments item and its `on` option, under TASK-035's, step 3's
     Parallel increments paragraph, under TASK-030's, and rule 46, under TASK-015's; and six passages TASK-037 reworded, which those entries excuse: three under "Phase 2 \u2014 Design" (the critique's round paragraph, its stop rule and its record), the change cycle's item 2, and rules 12 and 48, under TASK-012's, TASK-014's and TASK-015's; and three passages TASK-038 reworded, which those entries excuse: the design critique's launch block under "Phase 2 \u2014 Design", and step 8's title paragraph and its after-merge paragraph, under TASK-012's and TASK-034's; and six passages TASK-039 reworded: step 3b's restart item and step 7's Accept bullet, which TASK-034's entries excuse, step 5's paragraph, under TASK-039's own entry, and, at its Review A's round 1, the design critique's convergence paragraph under "Phase 2 — Design", step 4's reviewers paragraph and rule 36, under TASK-012's, TASK-030's and TASK-015's; and four passages TASK-040 reworded, which those entries excuse: the stage review's step 8, the demonstration's paragraph and item 5, under TASK-034's, and the refactoring pass's step 2, under TASK-035's; and one passage BUG-040 reworded, the change cycle's item 4, under TASK-014's; and four passages BUG-043 reworded, which those entries excuse: step 3's parallel item 4, under TASK-030's, and step 3b's exit-124 paragraph and restart item and step 7's last-resort reset, under TASK-034's), so an increment that excuses anything more changes this test. It
+    and two passages HOTFIX-003 reworded (hotfix 2026.11.09a): intake's batches paragraph, under BUG-042's entry, and the
+    mockups' iteration paragraph, under HOTFIX-003's own.
     needs the baseline commit, which CI's depth-1 checkout lacks (INVENTORY Decisions): skipped there, run in
     the supervisor's checkout."""
     repo = os.path.abspath(os.path.join(HERE, os.pardir))
diff --git a/tests/test_hotfix_intake.py b/tests/test_hotfix_intake.py
new file mode 100644
index 0000000..312528d
--- /dev/null
+++ b/tests/test_hotfix_intake.py
@@ -0,0 +1,122 @@
+"""Hotfix 2026.11.09a (HOTFIX-003): the software's features and behaviour are asked as a conversation, never as
+guessed options; a project's parameters and the gates keep the question form (the owner's rule of 2026-11-08;
+docs/INVENTORY.md, Decisions, row of 2026-11-08; docs/DESIGN.md, "Change: the intake hotfix").
+
+enforces: docs/DESIGN.md, Change: the intake hotfix, "What changes - the text by home" (one test per row, each pinning
+its sentence in its home) and "Non-goals" (the places that keep the form, pinned as invariants).
+
+KP-052: the one non-ASCII character these pins need, the em dash, is built with chr(), never typed."""
+import os
+
+from phase_modules import flat, read, rule, section
+
+ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
+BRIDGE = os.path.join(ROOT, "bridge")
+CORE = os.path.join(BRIDGE, "commands", "supervisor.md")
+PHASES = os.path.join(BRIDGE, "cursor-bridge", "workflow", "phases")
+INTAKE = os.path.join(PHASES, "intake.md")
+MOCKUPS = os.path.join(PHASES, "interface", "mockups.md")
+CHANGE_CYCLE = os.path.join(PHASES, "change-cycle.md")
+DESIGN = os.path.join(PHASES, "design.md")
+INTERFACE = os.path.join(PHASES, "interface.md")
+RUN_PARAMETERS = os.path.join(PHASES, "run-parameters.md")
+PITFALLS = os.path.join(BRIDGE, "cursor-bridge", "Known-Pitfalls.md")
+DASH = chr(0x2014)
+
+
+def item(text, number, label):
+    """A numbered item of a procedure list, from `<number>. **<label>**` to the next item."""
+    start = text.index("\n%d. **%s**" % (number, label))
+    end = text.index("\n%d. **" % (number + 1), start)
+    return flat(text[start:end])
+
+
+# --- intake.md, "The procedure": the sorting of questions
+
+def test_hotfix003_intake_sorts_a_question_by_what_it_asks():
+    procedure = flat(section(read(INTAKE), "The procedure", 3))
+    assert ("Ask in batches, not one at a time, and sort each question by what it asks, never by whether you could "
+            "guess its answers.") in procedure
+
+
+def test_hotfix003_intake_a_parameter_question_may_take_the_question_form():
+    procedure = flat(section(read(INTAKE), "The procedure", 3))
+    assert ("**A question about the project's parameters** " + DASH + " a fact the bridge needs in a fixed form: the "
+            "kind (`private` or `commercial`), the platform and runtime context, the delivery kind, a part's product "
+            "type or sub-type where the owner must choose between the open list's definitions, the figure of a budget "
+            "or a limit " + DASH + " may be asked in the question form (`AskUserQuestion`, the default or the "
+            "recommended answer first), so that answering it is one choice.") in procedure
+
+
+def test_hotfix003_intake_a_question_about_the_software_is_a_conversation():
+    procedure = flat(section(read(INTAKE), "The procedure", 3))
+    assert ("**A question about the software itself** " + DASH + " what it does, which features it has and how each "
+            "behaves, who uses it and how, what happens in a case the description leaves open; the gaps, contradictions "
+            "and better options above " + DASH + " is a conversation: numbered questions in prose, batched, each "
+            "answered in the owner's own words, your follow-ups building on their answers; never a list of answers you "
+            "guessed for the owner to tick, since a guessed option frames the feature before the owner has described "
+            "it, and their answer then measures your guess, not their intent (the owner's rule of 2026-11-08, after a "
+            "supervisor offered guessed feature options at intake).") in procedure
+
+
+def test_hotfix003_intake_the_stop_rule_stays_and_the_old_sort_is_gone():
+    procedure = flat(section(read(INTAKE), "The procedure", 3))
+    assert ("Stop asking when the remaining unknowns are ones a competent implementer could decide without you.") in procedure
+    assert "where the answer is a choice among options" not in procedure
+    assert "use plain prose where it is open-ended" not in procedure
+
+
+# --- mockups.md, "The procedure": the iteration
+
+def test_hotfix003_the_mockup_iteration_is_a_conversation():
+    procedure = flat(section(read(MOCKUPS), "The procedure", 3))
+    assert ("Iterate with the user until they are satisfied " + DASH + " expect change requests; this is where UI "
+            "decisions are cheap to make. The iteration is a conversation, as intake's questions about the software "
+            "are (`intake.md`, the sorting of questions): ask what they would change and why, numbered where several "
+            "points are open, answered in their own words, your follow-ups building on the answers; variants of a "
+            "screen you guessed are never put as options to tick. The question form is kept for the gate's approval "
+            "(`interface.md`, \"The gate\") and for a parameter in a fixed form that a screen turns on (the target "
+            "platform, say).") in procedure
+    assert "for discrete choices" not in procedure
+
+
+# --- change-cycle.md, item 1: the change's intake in the same form
+
+def test_hotfix003_a_change_is_interrogated_in_the_same_form():
+    text = read(CHANGE_CYCLE)
+    assert ("Interrogate the request the same way as a new project's description " + DASH + " gaps, contradictions, "
+            "better options, and in the same form (intake.md's sorting of questions: the change's features and "
+            "behaviour as a conversation in the owner's own words, a parameter in the question form) " + DASH + " but "
+            "only about the delta") in item(text, 1, "Intake of the change")
+
+
+# --- the core's rule 12: the form's bound
+
+def test_hotfix003_rule_12_bounds_the_question_form():
+    text = rule(12)
+    assert ("A decision the owner owns is asked in the question form (the `AskUserQuestion` tool, the recommended "
+            "option first), so that answering it is one choice.") in text
+    assert ("The form is for a decision between answers that exist before the owner speaks " + DASH + " a gate, a run "
+            "parameter, a project parameter at intake, an item that costs money, a reading of an approved requirement; "
+            "what the software should do and how its features behave is asked as a conversation in the owner's own "
+            "words, never as options you guessed (intake.md's sorting of questions; the owner's rule of 2026-11-08).") in text
+
+
+# --- Known-Pitfalls: KP-075
+
+def test_hotfix003_kp075_names_the_pitfall_and_its_sign():
+    text = read(PITFALLS)
+    assert "### KP-075 " + DASH + " A question's sort left to the supervisor licensed guessed feature options at intake" in text
+    entry = text[text.index("### KP-075"):]
+    assert "**Correction (2026.11.09a):**" in entry
+    assert "The sign:" in entry
+
+
+# --- the places that keep the form (invariants of the hotfix's non-goals)
+
+def test_hotfix003_the_kind_the_gates_and_the_run_parameters_keep_the_form():
+    assert ("it the owner is asked is the kind, as its own question in the question form, `private` named") in read(INTAKE)
+    assert ("each asked as a question of its own in the app's question form") in flat(read(DESIGN))
+    assert ("each part's traits are a decision of their own, asked in the question form") in flat(read(DESIGN))
+    assert "question form" in flat(section(read(INTERFACE), "The gate", 3))
+    assert ("each as a question of its own in the app's question form** (`AskUserQuestion`,") in flat(read(RUN_PARAMETERS))
````
