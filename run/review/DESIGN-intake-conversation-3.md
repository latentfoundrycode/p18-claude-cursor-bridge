# Design critique: the intake hotfix (subject `intake-conversation`), round 3

## What is criticised

The Claude-Cursor Bridge is a Claude Code extension that supervises software projects built by a Cursor builder: its governance is text (a core command file and phase modules under `workflow/`) that an AI supervisor reads and follows while talking to the owner, a product manager who is not an engineer. Its installed release is 2026.11.03a. On 2026-11-08 a project supervisor, at intake, put a question about a feature's behaviour to the owner as a list of options it had guessed, in the app's question form (`AskUserQuestion`, a widget whose answer is one tick); the owner rejected the options as too rigid and ruled: the fixed questions that set a project's parameters (private or commercial, platform, product type) may keep the question form, while the software's features and their behaviour are discussed as a conversation, numbered questions in prose answered in the owner's own words, follow-ups building on the answers, never guessed options to tick. The owner ordered the fix as a hotfix of the installed text, between TASK-050's merge and TASK-051 (the inventory row below).

What is criticised is the hotfix's design and its text as written: the Change section (below; it goes into docs/DESIGN.md when the hotfix is carried onto main), the changed passages in their homes, whole (intake.md's procedure, the mockups' procedure, the change cycle's item 1, design.md's gate, the core's escalation passage and rule 12, the explain-for-decision brief, the new KP-075), the places that keep the question form (quoted below as they stand, unchanged), the pinning tests and the text mutants, and the committed diff against the installed stamp. The text is read by an AI supervisor at intake, before the design gate, in the mockup iteration, in a change cycle's intake and in an escalation mid-build, after every compaction (the session-start hook names, by phase, intake.md, design.md, interface.md with its variant files, change-cycle.md, whose intake runs intake.md's procedure, and Known-Pitfalls.md in building, changing and configuration), so each sentence must carry its rule without the conversation that produced it.

Judge: whether the sorting rule is stated so that a supervisor cannot read a feature question back into the question form (is 'what a question asks' decidable from the text; are the parameter examples a closed enough list; is the doubtful case, a question that is both, settled); whether every place the installed text sends a question to the owner about the software is covered (the design's table and its non-goals name them: are any missed, in the modules, the trait files' `intake.questions` additions, the skills, the escalation list, the explain-for-decision brief); whether any place that keeps the form should not, or any place now a conversation should keep it (the mockup iteration's discrete choices; an escalation about product behaviour mid-build); whether rule 12's bound contradicts rule 12's own sentence, rule 29, the gates or the digest's rule 12, which is not changed (the digest at 9,497 of 9,500 characters); whether the reasons given are the owner's (nothing is relitigated: the rule is the owner's as given) and whether the wording adds anything the owner did not say; whether the trace exceptions and the carve test's count are right and complete; whether the tests pin what the table says and the mutants would catch a regression; whether the CHANGELOG items under Running projects must are enough for a project mid-intake at the install; and whether anything in the hotfix's path (the release branch cut from the installed stamp, the code gate, the stamp, the owner's install, the carry onto main) departs from the two earlier hotfixes' precedent without a stated reason. Security and money: none (text only; no key, no program, no spend). Raise nothing about the two program-reading records (headers, release B2) or about stage H1's increments: they are not this change.

## The owner's rule, as recorded (docs/INVENTORY.md, Decisions)

````markdown
| The intake hotfix comes after TASK-050 merges and before TASK-051 (the owner's order, 2026-11-08, asked in this session in the question form after the maintainer session's report, rule 57): a hotfix of the bridge's text, through the two-critic design review, installed by the owner from a run sheet; its subject, as the maintainer relayed the owner's rule and this session quoted it to the owner: the fixed questions that set the project's parameters (private or commercial, platform, product type) may keep the question form, while the software's features and their behaviour are discussed as a conversation, numbered questions in prose answered in the owner's own words, follow-ups building on the answers, never guessed options to tick; places to check: `workflow/phases/intake.md` ("Ask in batches ... Use `AskUserQuestion` where the answer is a choice"), `phases/change-cycle.md` (a change request interrogated as a new project's description), the form's uses in `phases/interface/mockups.md` and `phases/design.md`, and the core's rule 12 (reports and gates, not intake) | a project supervisor offered guessed feature options at intake on 2026-11-08 and the owner rejected them as too rigid; the installed text leaves each question's sort into choice or open-ended to the supervisor | 2026-11-08 | the owner reorders it |
````

## The record so far

## Subject: intake-conversation (the intake hotfix 2026.11.09a: the software's features and behaviour asked as a conversation, never as guessed options; 2026-11-09)

**What is criticised:** the hotfix's design and its text as written on `hotfix/intake-conversation`, cut from the installed stamp 91c2efb (2026.11.03a) through `release/2026.11.03`: the Change section "the intake hotfix" (written into docs/DESIGN.md at the carry onto main), the changed passages whole in their homes (intake.md's procedure, the mockups' procedure, change-cycle.md's item 1, design.md's gate, the core's escalation passage and rule 12, the explain-for-decision brief's part 4, KP-075), the places that keep the question form, the pinning tests (tests/test_hotfix_intake.py) and the text mutants (run/supervisor/HOTFIX-003-mutants.json), and the committed diff against the stamp. The critics read `run/review/DESIGN-intake-conversation-<round>.md`, built from the committed text by run/supervisor/hotfix003_design_file.py, with plan-critic's design-document lenses. The owner's rule (INVENTORY, Decisions, 2026-11-08) is the subject's fixed input: nothing of it is relitigated.

**Accepted** (finding, critic, round, the reason):
- The digest's rule 12 says "asked in the question form" without the bound, and the changing phase re-reads change-cycle.md, not intake.md (Review B, Should fix, round 1; plan-critic S4's digest part and C1): the digest's line is R-048's D7, an owner decision of the evaluation of 2026-10-25 pinned by tests/test_release_t_records.py, so a rewording is the next revision of R-048's, not a hotfix's; the digest's header says the full text governs, and after a compaction the hook names a module that carries the rule in every phase where a question about the software arises (intake.md; design.md's gate; interface.md, whose Variants line sends the mockup phase to mockups.md; change-cycle.md's item 1, whose intake runs intake.md; Known-Pitfalls.md's KP-075 in building, changing and configuration). The design's non-goal now says so, and the digest rewording is a HARDENING lead at the carry.
- Two of the four trace-exception entries never match, since BUG-042's earlier entries on the same headings match first (plan-critic C4, round 1): the file's convention is one entry per change ("The supervisor-text increment that rewords or adds appends each entry"); kept as written, the labelling recorded in the design's table and the carve test's comment, as TASK-035's precedent did.
- "Running projects must" says nothing to a project whose intake answers already measured guessed options (plan-critic C5, round 1): nothing already answered is re-asked, and the design gate presents the behaviour the design fixes as a decision of its own, where the owner may restate any of it; the owner's rule asks for no clause, so none is added (the design's Failure modes name the case).
- The design gate's "the behaviour the design fixes" stays a question in the form (Review B, Consider, round 1): the gate approves a behaviour the design has already written down, an answer that exists before the owner speaks; a question the design must still put to the owner about behaviour is now a conversation by design.md's new paragraph.

**Rounds** (round, kind, the commit its file was built from, critic, Blocking / Should fix / Consider, what was fixed):
- 1, critique, f6f6047 (text at 171418c), plan-critic (Fable 5.1): 1 / 4 / 5. Fixed: B1 the owner's rule gets a register row (R-065) at the carry, named in the design's header, table and Delivery; S1 intake.md's third sort, the question that is both, with the tie-break and "a short answer never makes a question a parameter", pinned and mutated (i06); S2 rule 12's bound rewritten (answers that exist before the owner speaks, or a fact the bridge needs in a fixed form; the list now holds the figure, the scope question and the irreversible step; the places named), pinned and mutated (r01, r02); S3 the invariant test pins the seven kept places one assert each (configuration.md's figure and evaluate-reports.md's sign-off added), seven mutants over them (n01 to n07), KP-075's sign pinned and mutated (k02), the testing strategy rewritten to what is pinned; S4 design.md's new paragraph before the gate, pinned and mutated (d01); C1 the hook sentence corrected (change-cycle.md in a change cycle; the design's non-goal and the round file's "What is criticised"); C2 the mockups' example replaced (the smallest screen width the design must fit) and "how a screen should behave is never such a parameter" added, pinned and mutated (m03); C3 Delivery names HOTFIX-002's precedent and the expected refits of the carry. Accepted: C4, C5 (above).
- 1, critique, f6f6047 (text at 171418c), Review B (grok-4.7-medium, design mode): 2 / 3 / 2. Fixed: Blocking 1 (a parameter defined as "a fact the bridge needs in a fixed form" licenses a behaviour question with a short answer) by the closed list, the third sort and the mockups' sentence (above; i07); Blocking 2 (a product-behaviour escalation mid-build has no operative sentence: the core's "lead with the decision and the options" and the brief's part 4) by the escalation passage rewritten (options only where the answers exist before the owner speaks; a behaviour decision as a conversation, mid-build as at intake; a `reword HOTFIX-003` entry under "Escalate to the user when", the carve test at 86 excused) and the brief's part 4 (options for a decision between answers that exist; a behaviour decision is the question itself, in prose), each pinned and mutated (r03, s01), KP-075's correction naming both; Should fix 2 (the kept sentence still covers a behaviour decision) by the bound's "a decision about what the software should do or how a feature behaves is the owner's too, but its answer is theirs to describe"; Should fix 3 (the invariant test and the mutants claim more than they show; KP-075's sign unpinned) with S3 above. Accepted: Should fix 1 (the digest), Consider 2 (the gate's behaviour decision) (above). Consider 1 (the reason clause adds to the owner's words) fixed: the clause now attributes the rule and "too rigid" to the owner and the framing reason to the supervisor's reading.
- 2, critique, 821a7f6 (text at b6c5a83), plan-critic (Fable 5.1): 0 / 4 / 5. Fixed: S1 the closed list's product-type item is the confirmation of the classification made from the owner's answers (each definition in one line), since the procedure asks the deciding questions in conversation and pauses on a tie; S2 the recommendation is bounded like the options: the escalation passage ("recommend one where there are answers to choose between"; a behaviour decision with no recommendation before the owner's answer, the supervisor's view a follow-up as intake's better-options bucket), its "How you explain it" summary, the reporting rule's first bullet (a `reword HOTFIX-003` entry under "Reporting to the user"), the brief's parts 1 and 5, pinned and mutated (r03 to r06, s02); S3 rule 12's bound, the escalation passage and part 4 name a consequence they bear and a change to what "correct" means, the two parentheticals reading "among them"; S4 the CHANGELOG item gains *(design)* and a *(building, changing)* item for escalations; C1 KP-075's Applies names the design gate; C2 design.md's paragraph reads "approves something the design has already written down"; C3 insertion mutants for the two retirement asserts (i08, r04); C4 Delivery states what `git diff --stat 91c2efb origin/main` shows (MANIFEST.json alone conflicts; the text, the tests, the CHANGELOG apply clean); C5 the mockups' example reads "one of intake.md's closed list: ..., a figure" (m03 kept). Nothing accepted.
- 2, critique, 821a7f6 (text at b6c5a83), Review B (grok-4.7-medium, design mode): 1 / 4 / 1. Fixed: Blocking (part 4 made a behaviour decision a conversation while the gates approve behaviour in the form through the same brief) by part 4's "a gate's approval of what the design or the mockup already writes down" among the decisions whose answers exist, and "and the user has not yet described it" as the condition for the conversation, with design.md's paragraph (s03, d01); Should fix 1 (parts 1 and 5 and "How you explain it" presuppose options) with S2 above; Should fix 2 (KP-075's correction kept the old parameter test) by the correction's closed list and short-answer rule, pinned; Should fix 3 (the reason clause after the colon reads as the owner's) by dropping the reading from intake.md, which now carries the owner's words alone, the reading kept in KP-075's Cause; Should fix 4 (the two parentheticals' four-item gloss against rule 12's list) with S3 above; Consider (the mockups' example against the closed list) with C5 above. Nothing accepted.

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

**Subject** (the critique's token): `intake-conversation`. A hotfix of the installed release 2026.11.03a, text only (no program changes): made on `release/2026.11.03`, cut from the installed stamp (91c2efb), through the two-critic design critique and the code gate, stamped `2026.11.09a`, installed by the owner from a run sheet, then carried onto `main` with its records, as hotfixes 2026.10.18a and 2026.10.25a were (docs/HARDENING.md, their sections). It carries no `handoff/` brief: the supervisor authors governance text (INVENTORY, Decisions, "Governance text is the supervisor's to write"), and its ID in the records is HOTFIX-003; the owner's rule enters the requirements register at the carry as R-065 (round 1, B1).

### Purpose and scope

The owner's rule of 2026-11-08 (INVENTORY, Decisions, row of 2026-11-08): the fixed questions that set a project's parameters (private or commercial, platform, product type) may keep the app's question form, while the software's features and their behaviour are discussed as a conversation — numbered questions in prose, answered in the owner's own words, follow-ups building on the answers — never as guessed options to tick. The installed text leaves each intake question's sort to the supervisor ("Use `AskUserQuestion` where the answer is a choice among options; use plain prose where it is open-ended", intake.md), so a supervisor that can imagine three answers to "how should search work?" is licensed to offer them, and on 2026-11-08 one did; the owner rejected the options as too rigid. The hotfix writes the owner's sorting rule into every place the installed text sends a question to the owner about the software, and bounds the one standing rule that names the form.

**Why a hotfix, not an increment of release B2.** `main` holds stage H1's unreleased programs (TASK-046 to TASK-050), so an install from `main` is refused ("the release folder carries version 2026.11.03a but not its files", bridge-install.py); the running projects, which ask intake questions now, can only receive the text from the installed release's branch. The owner ordered it between TASK-050's merge and TASK-051 (2026-11-08).

### Non-goals

- No change to where the question form is right and already fixed: the kind `private` or `commercial` at intake (intake.md, "The project file"); the design gate's separate decisions and the traits settled there (design.md, "The gate", "Traits at the design gate"); the interface gate (interface.md, "The gate"); the five run parameters (run-parameters.md); a limit's figure (configuration.md); the report cycle's sign-off (evaluate-reports.md). Each stays as written, and the invariant test pins each of the seven with an assert of its own, each shown strong by a mutant of that place (n01 to n07). An escalation whose answers exist before the owner speaks (money, scope, an irreversible step, a reading of an approved requirement) keeps its options, as the escalation passage and the brief now say.
- The digest's rule 12 ("Reports lead with the owner's decision, asked in the question form.") is not changed: the line is R-048's D7, an owner decision of the evaluation of 2026-10-25, pinned by tests/test_release_t_records.py, and the digest stands at 9,497 of its 9,500 characters; the digest's header says the full text governs, and after a compaction the hook names, beside the digest, a module that carries the rule in every phase where a question about the software can arise: intake.md at intake; design.md ("The gate") in design; interface.md, whose `Variants:` line sends the mockup phase to interface/mockups.md; change-cycle.md (item 1) in a change cycle, whose intake runs intake.md's procedure; and Known-Pitfalls.md (KP-075) in building, changing and configuration (session-start.py, PHASE_CONVENTIONS). A rewording of the digest's line that carries the bound within the cap is a lead for the release that next revises R-048, recorded in HARDENING at the carry (round 1, Review B's first Should fix, accepted).
- No program change, no schema, no manifest entry beyond the stamp's regeneration, no change to the conditional workflows' `intake.questions` additions (installable's delivery questions, spends money's cost questions): each addition is asked "with the minimum this module covers" (intake.md, "Extension points"), so the sorting rule governs them as it governs the module's own questions.
- `Documents/` is not written by the hotfix (rule 23): the Guide on Starting Up a New Project says only that intake interrogates the description, which stays true; a sentence on the conversation's form is a reflection-point patch at stage H1's close.
- The explain-for-decision skill's decision brief keeps its six parts; only part 4, "The options", says where options belong and that a decision about the software's behaviour is asked in prose (round 1, Review B's second Blocking). The brief's other parts, the explanation and the run sheet are not changed.

### What changes — the text by home

| Home | Today | After the hotfix |
|---|---|---|
| `workflow/phases/intake.md`, "The procedure", the batches paragraph | Batches; `AskUserQuestion` where the answer is a choice among options, prose where open-ended; stop when a competent implementer could decide the rest | Batches; **the sort is by what a question asks, never by whether its answers can be guessed**: a question about the project's parameters (a fact the bridge's own procedures consume in a fixed form, one of a closed list: the kind, the platform and runtime context, the delivery kind, the confirmation of a part's product type or sub-type as classified from the owner's answers, a figure) may take the question form, the default or recommended answer first; a question about the software itself (what it does, its features and their behaviour, its users, a case the description leaves open; the gaps, contradictions and better options) is a conversation: numbered questions in prose, batched, answered in the owner's own words, the follow-ups building on the answers, never a list of guessed answers to tick (the owner's rule, who found such options too rigid; the text adds no reason of its own); **a question that is both** (a fact about the software that fixes a parameter, the open list's deciding questions among them) is a conversation, since a conversation carries a parameter's answer and the form cannot carry a description, and a short answer never makes a question a parameter; the stop rule unchanged |
| `workflow/phases/interface/mockups.md`, "The procedure", the iteration paragraph | Iterate until satisfied; `AskUserQuestion` for discrete choices, plain discussion otherwise | Iterate until satisfied; the iteration is a conversation as intake's questions about the software are (what they would change and why, in their own words, follow-ups on the answers), guessed variants of a screen never put as options to tick; the question form kept for the gate's approval (interface.md, "The gate") and for a parameter in a fixed form a screen turns on (one of intake.md's closed list: the smallest screen width the design must fit, a figure), how a screen behaves never such a parameter |
| `workflow/phases/change-cycle.md`, item 1 | The request interrogated "the same way as a new project's description — gaps, contradictions, better options — but only about the delta" | The same, "and in the same form (intake.md's sorting of questions: the change's features and behaviour as a conversation in the owner's own words, a parameter in the question form)" |
| `workflow/phases/design.md`, "The gate" | The gate's separate decisions, each in the question form | The same, and a new paragraph: a question the design must put to the owner before the gate about what the software does or how a feature behaves (a case the description left open, an open question the critique raised) is asked as intake.md's sorting of questions says, a conversation in their own words, never guessed options; the gate's decisions keep the form, since each approves something the design has already written down |
| `commands/supervisor.md`, "Escalate to the user when", the closing paragraph and the "How you explain it" paragraph | "When you do escalate, lead with the decision and the options, recommend one, then wait."; the brief's shape summarised with "the options in the user's currency; your recommendation" | Lead with the decision, recommend one where there are answers to choose between, then wait; the options are put only where the decision is between answers that exist before the owner speaks (rule 12's bound, among them scope, a consequence they bear, money, an irreversible step, a reading of an approved requirement, a change to what "correct" means); a decision about what the software should do or how a feature behaves, not yet described by the owner, is asked as a conversation in the owner's own words, never as options the supervisor guessed and with no recommendation before the answer, the supervisor's view following the answer as a follow-up (intake's better-options bucket); the summary reads "the options in the user's currency and your recommendation, where the answers exist before they speak" |
| `commands/supervisor.md`, "Reporting to the user", the first bullet | "a product-behaviour or scope call — stated as one question with your recommendation" | "stated as one question, with your recommendation where the answers exist before they speak (a behaviour they have not yet described is asked in prose, rule 12's bound)" |
| `commands/supervisor.md`, standing rule 12 | "A decision the owner owns is asked in the question form (the `AskUserQuestion` tool, the recommended option first), so that answering it is one choice." | The sentence kept (R-048's pin), followed by its bound: the form is for a decision between answers that exist before the owner speaks, or a fact the bridge needs in a fixed form (a gate, a run parameter, a project parameter, a figure the owner names, a scope question, a consequence they bear, an item that costs money, an irreversible step, a reading of an approved requirement, a change to what "correct" means); a decision about what the software should do or how a feature behaves is the owner's too, but its answer is theirs to describe, so it is asked as a conversation in their own words, never as options the supervisor guessed, wherever it arises (intake, a change's intake, the mockup iteration, a question before the design gate, an escalation mid-build) |
| `skills/explain-for-decision/SKILL.md`, "The decision brief", parts 1, 4 and 5 | "The decision — one sentence: what you are choosing between."; "The options — for each: what it means for the product in use; what it costs; what it forecloses or whether it can be reversed later."; "Recommendation — which one, and the reason in the user's currency." | Part 1 adds "or, for a behaviour the user has not yet described, the case the software must settle"; part 4 adds: options are for a decision between answers that exist before the user speaks (a gate's approval of what the design or the mockup already writes down, scope, a consequence they bear, money, an irreversible step, a reading of an approved requirement, a change to what "correct" means); when the decision is what the software should do or how a feature behaves and the user has not yet described it, part 4 is the question itself, in prose, answered in the user's own words, never guessed options to tick, and part 5 waits for the answer, the supervisor's view following as a follow-up (intake's better-options bucket); part 5 adds "withheld for a behaviour the user has not yet described" |
| `cursor-bridge/Known-Pitfalls.md` | — | KP-075, the pitfall: a question's sort left to the supervisor licenses guessed feature options; the correction is the sorting rule (the closed list, the short-answer rule, no recommendation before the owner's answer), naming its six homes; Applies names the five places; the sign is a message offering options for a feature the owner has not described, or an intake batch whose feature questions carry answer lists |
| `cursor-bridge/workflow/trace-exceptions.md`; `tests/test_core_carve.py` | 83 excused passages | The five reworded baseline passages excused by `reword HOTFIX-003` entries (the core's "Phase 1 — Intake", "Phase 3 — UI mockups", "Escalate to the user when" (two passages) and "Reporting to the user" headings) and the modules' new text by `new HOTFIX-003` entries ("The procedure" of intake.md and of mockups.md; one entry per change, the file's convention, two of them matched first by BUG-042's earlier entries and recorded as such); the trace test's count 88 and its five NOTE lines (the intake entry labelled BUG-042, whose earlier entry on the same heading matches first, as TASK-035's precedent records) |
| `docs/REQUIREMENTS.md` (at the carry, on main) | — | R-065: a question to the owner about what the software does or how a feature behaves (at intake, in a change cycle's intake, in the mockup iteration, before the design gate, in an escalation) is asked as a conversation, numbered questions in prose answered in the owner's own words, follow-ups building on the answers, never options the supervisor guessed; a project parameter in a fixed form, a gate, a run parameter and the other decisions rule 12's bound names keep the question form; source the owner's rule of 2026-11-08 (INVENTORY, Decisions) and this section; status built; evidence tests/test_hotfix_intake.py (the `test_hotfix003_` tests) and tests/test_core_carve.py (the excused passages) |
| `cursor-bridge/CHANGELOG.md`, `VERSION`, `MANIFEST.json` (at the stamp, on Opus 5.5) | 2026.11.03a | `## 2026.11.09a` with **What changed** (this table), **Running projects must** (*(intake, design, mockups, changing)*: from the install, every question still to be asked about the software is asked as the conversation the text now describes, nothing already answered re-asked, a batch already sent in the question form answered as the owner chooses; *(building, changing)*: an escalation about product behaviour not yet described by the owner is asked as a conversation, with no options and no recommendation before their answer; *(all phases)* install, restart, `/calibrate-bridge`), **If rolled back** (nothing to restore) |

### The host — Claude Code

Unchanged. The question form is the `AskUserQuestion` tool, which the hotfix uses less, not differently; no hook, setting or permission rule changes (the release's host table in "Change: release T" stands).

### Delivery (the trait's Delivery section, scoped to the kind host-installation)

The owner installs from the release branch by the setup guide's three commands, the checkout switched to `release/2026.11.03` instead of `main` (the installer accepts a `release/*` head that is GitHub's merge of a pull request, hotfix 2026.10.25a), with the run sheet's one check, the installer's exit 0 on `RESULT: INSTALLED TREE MATCHES bridge 2026.11.09a`; then the app restarted and `/calibrate-bridge` in each running project. The carry onto `main` follows the install, as HOTFIX-002's did (PR #84; HARDENING, "The carry"): the release branch's change against the stamp applied three-way onto `origin/main`, which holds stage H1's five increments, all programs: `git diff --stat 91c2efb origin/main` over the hotfix's files shows the six text homes, tests/test_core_carve.py, trace-exceptions.md, CHANGELOG and VERSION unchanged on main since the stamp, and `MANIFEST.json` alone changed (main's program hashes), so the one expected conflict is the manifest, taken from main and regenerated over main's tree by `tools/make-manifest.py` (main's version line moves to 2026.11.09a); the text, the tests and the CHANGELOG entry apply clean, each checked against this plan at the carry; and the records (this section, the critique's block, HARDENING's hotfix section with the digest lead, the inventory's feature row, the register's R-065, the status and `project.json` at the new version) in the same pull request, through the code gate.

### Security and secret handling

Nothing new: text only, no secret, no key, no program. The hotfix's public pull requests name no computer path (path_scan before every push).

### Data model and development data

None. The intake notes (`run/supervisor/intake-notes.md`) keep each question and the owner's answer as before, a conversation's answers in the owner's words.

### Testing strategy

Tests first (release T's constraint): `tests/test_hotfix_intake.py` pins every changed sentence in its home (the three sorts and the stop rule in intake.md; the iteration sentence in mockups.md; the clause in change-cycle.md; design.md's paragraph before the gate; the escalation passage, its skill summary and the reporting bullet; rule 12's bound; the brief's parts 1, 4 and 5; KP-075's heading, its correction, its six homes, its Applies and its sign) and the retirement of the two `AskUserQuestion` sorting sentences and of "the decision and the options"; each shown red on the hotfix branch's base before the text (`mutation-run.py --checkpoint`, the per-test lines read); the seven places that keep the form pinned by the invariant test, one assert each (the kind, the design gate, the traits, the interface gate, the run parameters, configuration's figure, the report cycle's sign-off), and each of the thirty-one text mutants (twenty-four over the changed sentences, two of them re-inserting a retired sentence, seven over the kept places) named with the test it must fail, all killed by the mutation run. The trace check runs green at 88 excused with its five NOTE lines (`tests/test_core_carve.py`). The full suite before the first push, with the pull request's variables (P7), since the stamp changes `VERSION`.

### Failure modes

- A supervisor on the installed text keeps offering options: the text leaves it no sort of its own to make, and the sign is named in KP-075; the owner's rejection is the detection, as on 2026-11-08.
- A project mid-intake at the install: the item under **Running projects must** says what changes (the questions still to ask) and what does not (answers given).
- A question that is both (a feature whose shape is a parameter: "which platform" is a parameter; "what the platform build does differently" is the software; the open list's deciding questions, "does it keep data for its users"): intake.md's third sort says it in the text the supervisor reads, a conversation, since a conversation can carry a parameter's answer and the form cannot carry a description, and a short answer never makes a question a parameter.
- A project past intake at the install, whose intake answers measured guessed options: nothing already answered is re-asked (Running projects must); the design gate presents the behaviour the design fixes as a decision of its own, where the owner may restate any of it (design.md, "The gate"); no clause is added for it, since the owner's rule asks for none (round 1, plan-critic C5, accepted).

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

Ask in batches, not one at a time, and sort each question by what it asks, never by whether you could guess its answers. **A question about the project's parameters** — a fact the bridge's own procedures consume in a fixed form, one of this closed list: the kind (`private` or `commercial`), the platform and runtime context, the delivery kind, the confirmation of a part's product type or sub-type as you classified it from their answers (each definition in one line), the figure of a budget or a limit — may be asked in the question form (`AskUserQuestion`, the default or the recommended answer first), so that answering it is one choice. **A question about the software itself** — what it does, which features it has and how each behaves, who uses it and how, what happens in a case the description leaves open; the gaps, contradictions and better options above — is a conversation: numbered questions in prose, batched, each answered in the owner's own words, your follow-ups building on their answers; never a list of answers you guessed for the owner to tick (the owner's rule of 2026-11-08, who found such options too rigid when a supervisor offered them at intake). **A question that is both** — a fact about the software that fixes a parameter, the open list's deciding questions among them (does it keep data for its users; does its user meet it in a browser) — is asked as a conversation: a conversation carries a parameter's answer, the form cannot carry a description. That a feature's answer could be written in a fixed form never makes it a parameter: a parameter is one the list above names, not a question whose answers are short. Stop asking when the remaining unknowns are ones a competent implementer could decide without you.

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

Iterate with the user until they are satisfied — expect change requests; this is where UI decisions are cheap to make. The iteration is a conversation, as intake's questions about the software are (`intake.md`, the sorting of questions): ask what they would change and why, numbered where several points are open, answered in their own words, your follow-ups building on the answers; variants of a screen you guessed are never put as options to tick. The question form is kept for the gate's approval (`interface.md`, "The gate") and for a parameter in a fixed form that a screen turns on (one of intake.md's closed list: the smallest screen width the design must fit, a figure); how a screen should behave is never such a parameter, however short its answer.
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

### workflow/phases/design.md, "The gate" (the new paragraph after the gate's decisions)

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

A question the design must put to the owner before the gate about what the software does or how a feature behaves — a case the description left open that the design has to settle, an open question the critique raised — is asked as intake.md's sorting of questions says: a conversation in their own words, never options you guessed. The gate's decisions above keep the question form, since each approves something the design has already written down.
````

### commands/supervisor.md, "Escalate to the user when" (the closing paragraph, "When you do escalate")

````markdown
## Escalate to the user when

**Look it up before you ask or propose.** Before asking the owner to create, set, install, or provide anything, check Resources in `docs/INVENTORY.md` — they may have provided it already, and asking twice costs them a redundant key and their trust. Before proposing a change to how the software works, check Features (it may already exist) and Decisions (it may have been settled for a reason). A proposal that reverses a settled decision quotes the decision and its reason and states what has changed since; without a changed circumstance, it is not made. A project whose app keeps secrets in its own store records each by name in Resources — the scan in `inventory-check.py` sees environment variables and CI secrets, not an app's private store.

Escalate a decision only when the deciding factor is something the user **uniquely owns
or must live with** — not when it is a technical judgment, even one with real trade-offs.
The user decides what the software should *do and be*; they do not decide *how it is
built*. "Is this code sound," "which fix is better," "which increment first," "what
implementation approach," "which library mid-build" are engineering judgments — a frontier
model decides those more reliably than the user can. So the supervisor decides them
itself, records the call in `docs/CHANGES.md`, and proceeds. It never hands the user a
menu of technical options to adjudicate.

The self-test before escalating: *if I asked the user "why did you choose that?", would
their answer come from what they want and must live with, or from knowing the software?*
If the latter, do not escalate — decide and proceed.

**A process question is never the owner's.** "Which procedure applies here?", "should I
follow the workflow for this?", "is this a stage close or project end?", "do I need a
brief for this?" — these are settled by this file and the bridge references, never by
asking. Where the governance is silent, follow the **closest defined procedure**, say in
the report which one you chose and why, and record the gap in the Bridge Feedback file at
the next reflection point so the maintainer can close it. Asking the owner a process
question hands a non-engineer a choice they cannot judge and stalls the loop on it.

Two judgments that feel like they need the user but do not: **how many re-delegation rounds
to run** (you draw a by-class line and record it — step 7) and **how to resolve a hard
reviewer split** (you convene a resolution round and decide on its record — step 8 and the
merge policy). Both are correctness work; neither is an escalation. The user learns of them
as *done*, in the report — not as a question that stalls the loop.

**Uncertainty on a technical or design question is not a reason to escalate — it is a reason
to convene a resolution round.** When the self-test says a question is the system's (it turns
on knowing the software) but you are *genuinely uncertain* — the answer isn't clear on the
merits, no established invariant settles it, and getting it wrong would be expensive — do not
fall back to asking the user. Convene the reviewer-debate step in
`~/.claude/cursor-bridge/Merge-Verification-Policy.md` (§"Resolution round") on that question,
exactly as for a hard reviewer split: write the question and the candidate options to a
committed file, have Review A and Review B each argue and return a reasoned vote, and decide
on that record. The user hears the outcome as *done*. Escalate **only** if the debate reveals
the crux is actually **intent** — what the software should *do* — and then bring up *that*
question, in plain language, not the technical one underneath it. A technical question you are
unsure about is the council's to settle, never the user's by default — being uncertain is
precisely when the decorrelated gate is worth using, not a licence to hand a non-engineer a
choice they cannot make.

Escalate only these:

- **Product behaviour** — should the software do something different, from a user's
  perspective, than what was agreed? (Not: how to implement agreed behaviour.)
- **Scope** — the work diverges from what the user signed off on in the design, the
  mockups, or the build plan. **Leaving out or postponing a specified requirement is always this:** a row in `docs/REQUIREMENTS.md` becomes `deferred` or `dropped` only with the owner's answer and the date, recorded in the row and in the inventory's Deferred table. A stand-in screen ("arrives in a later stage") is never a way to defer.
- **A user-level consequence the user would bear** — a materially larger cost, or a
  legal, privacy, or lock-in exposure. Dependencies reach the user *only* through this lens
  (rule 56), at whatever phase the dependency arises, when it carries such a consequence;
  a licence is never the owner's question. A plain "we need library X to build increment 7" mid-build is the
  supervisor's own call, recorded, not an escalation.
- **Something only the user can provide** — a secret, credential, key, token, or account.
  When providing it means the user must run or click something, hand it over as a **run
  sheet** (`explain-for-decision` skill, "Handing the user something to run"): the
  terminal named with how to open it, the folder and its `cd`, every command literal and
  numbered in order, what to expect and watch for under each, the secret typed by them
  never pasted to you, and one report-back line. A described command ("run the scanner
  with the JSON flag") is not a hand-off; it is a guess you are asking them to make.
- **An irreversible or out-of-repo action** — force-push, history rewrite, dropping data,
  deleting files outside scope, a deploy or migration, anything outside the repository.
  The revert net does not cover these, so they get a human yes/no first. This is a safety
  stop, not a taste decision.
- **A change to what "correct" means** — a test's *intent* is being changed, not code
  merely passing it: "this loosens X from A to B; was that intended?"

Do **not** escalate a code defect or implementation-soundness doubt — a reviewer REJECT
re-delegates, and CI plus two model families decide correctness. Routing those to the
user is theatre they cannot act on.

When you find something the user should *know* but not *decide* — the named increment is
already done, a planned approach turned out infeasible — surface it as a notification with
a stop-cord ("here is what I found and what I'm doing about it; say so if you'd rather I
didn't") and proceed. Inform; don't ask.

When you do escalate, lead with the decision, recommend one where there are answers to choose between, then wait. The options are put only where the decision is one between answers that exist before the owner speaks (rule 12's bound, among them scope, a consequence they bear, an item that costs money, an irreversible step, a reading of an approved requirement, a change to what "correct" means); a decision about what the software should do or how a feature behaves, which the owner has not yet described, is asked as a conversation in the owner's own words, never as options you guessed and with no recommendation before their answer, mid-build as at intake (intake.md's sorting of questions): your own view of it, where you have one, follows their answer as a follow-up, as intake's better-options bucket does.
Between escalations, do not ask for permission you already have — an approved build plan
is approval to execute it.

**How you explain it is governed by the `explain-for-decision` skill.** An escalation is the
moment a technical matter surfaces for a non-engineer to decide, and the decision is only as
good as their understanding of it. Use the skill's decision-brief shape (the decision; why it
is theirs; the at-most-three load-bearing concepts, parts before the whole, one instance, one
stake; the options in the user's currency and your recommendation, where the answers exist
before they speak; what you decide regardless) and run its self-check before sending.

---
````

### commands/supervisor.md, "Reporting to the user" (the first bullet)

````markdown
## Reporting to the user

The user is not an engineer and cannot act on a technical narrative. Since correctness is the
gate's job and hard technical questions are the resolution round's (above), most of what you
*could* report is no-action context. Every report must make the one thing that is genuinely
theirs — if anything — impossible to miss:

- **Lead with the decision they own, or its absence.** Open with either the single
  plain-language thing you need from them — a key or secret, a spend authorisation, a
  product-behaviour or scope call — stated as one question, with your recommendation where
  the answers exist before they speak (a behaviour they have not yet described is asked in
  prose, rule 12's bound); or, if nothing is needed, open with **"Nothing needed — proceeding"** (or "…stopped, awaiting only
  \<the one thing\>"). The user should be able to stop reading after the first line and know
  whether you want anything.
````

### commands/supervisor.md, standing rule 12

````markdown
12. Every report to the user leads with the one decision they own — or "Nothing needed —
    proceeding" — and marks all technical detail as FYI beneath it. Translate consequences
    into behaviour, cost, risk, and reversibility; never hand a non-engineer a technical
    narrative to parse or a technical menu to pick from. A decision the owner owns is asked in the question form (the `AskUserQuestion` tool, the recommended option first), so that answering it is one choice. The form is for a decision between answers that exist before the owner speaks, or a fact the bridge needs in a fixed form — a gate, a run parameter, a project parameter, a figure the owner names, a scope question (deferring or dropping a requirement), a consequence they bear (rule 56), an item that costs money, an irreversible step, a reading of an approved requirement, a change to what "correct" means; a decision about what the software should do or how a feature behaves is the owner's too, but its answer is theirs to describe, so it is asked as a conversation in their own words, never as options you guessed, wherever it arises — intake, a change's intake, the mockup iteration, a question before the design gate, an escalation mid-build (intake.md's sorting of questions; the owner's rule of 2026-11-08). When several rules claim the first line at once, the order is: a decision the
    owner owns; a key seen in the chat (rule 53); a gate decision you took under rule 50;
    the session model switch (rule 48). The rest follow, each on its own line.
````

### skills/explain-for-decision/SKILL.md, "The decision brief" (parts 1, 4 and 5)

````markdown
## The decision brief — when a decision is put to the user

Use this shape for every escalation and every phase-gate presentation. It is the "lead with
the decision, recommend one, then wait" rule of `supervisor.md`, with the explanation slotted
where it belongs:

1. **The decision** — one sentence: what you are choosing between, or, for a behaviour the
   user has not yet described, the case the software must settle.
2. **Why it is yours** — one sentence: which user-owned factor it turns on (product
   behaviour, scope, a cost or exposure you bear, something only you can provide, an
   irreversible step, a change to what "correct" means).
3. **What you need to know** — the load-bearing concepts, at most three, each under guards
   1–8 by its class. Parts before whole; one instance; one stake.
4. **The options** — for each: what it means for the product in use; what it costs; what it
   forecloses or whether it can be reversed later. Same terms as in 3 (guard 2). Options are
   for a decision between answers that exist before the user speaks (a gate's approval of what
   the design or the mockup already writes down, scope, a consequence they bear, money, an
   irreversible step, a reading of an approved requirement, a change to what "correct" means);
   when the decision is what the software should do or how a feature behaves and the user has
   not yet described it, this part is the question itself, in prose, answered in the user's own
   words — never options you guessed for them to tick (`intake.md`, the sorting of questions;
   the owner's rule of 2026-11-08) — and part 5 waits for their answer: your view comes as a
   follow-up building on it, as intake's better-options bucket does.
5. **Recommendation** — which one, and the reason in the user's currency; withheld for a
   behaviour the user has not yet described (part 4).
6. **Decided regardless** — the technical choices you make either way, one line each, so
   the user sees the boundary of what they are deciding and does not reach past it.

Then stop and wait. Target length: 250–400 words. Longer only when the budget rule forced a
split and the user asked to see both halves.
````

### cursor-bridge/Known-Pitfalls.md, KP-075 (new)

````markdown
### KP-075 — A question's sort left to the supervisor licensed guessed feature options at intake
- **Mistake:** at intake, a question about the software's features was put to the owner as a list of options the supervisor had guessed, for them to tick.
- **Surfaced:** a project supervisor, 2026-11-08: asked about a feature's behaviour, it offered guessed options in the app's question form; the owner rejected them as too rigid and ruled that the fixed questions setting a project's parameters (private or commercial, the platform, the product type) may keep the question form, while the software's features and their behaviour are discussed as a conversation, numbered questions in prose answered in the owner's own words, follow-ups building on the answers, never guessed options to tick (the bridge's INVENTORY, Decisions, 2026-11-08).
- **Cause:** the installed intake text sorted a question into the form or prose by whether its answer was a choice among options, which left the sort to the supervisor: any question whose answers it could imagine became a choice, and a guessed option frames the feature before the owner has described it, so the answer measures the guess, not the owner's intent.
- **Correction (2026.11.09a):** the sort is by what a question asks, never by whether its answers can be guessed: a question about the project's parameters (one of intake.md's closed list of facts the bridge's own procedures consume in a fixed form: the kind, the platform and runtime context, the delivery kind, the confirmation of a classification, a figure) may take the question form, the default or recommended answer first, and a short answer never makes a question a parameter; a question about the software itself is a conversation in the owner's own words, with no recommendation before the owner's answer, and a question that is both is a conversation too, at intake, in a change cycle's intake, in the mockup iteration, before the design gate and in an escalation mid-build alike (intake.md, change-cycle.md item 1, interface/mockups.md, design.md "The gate", the core's "Escalate to the user when", the explain-for-decision brief's part 4); the core's rule 12 bounds the form to a decision between answers that exist before the owner speaks or a fact the bridge needs in a fixed form (a gate, a run parameter, a project parameter, a figure, a scope question, a consequence the owner bears, an item that costs money, an irreversible step, a reading of an approved requirement, a change to what "correct" means).
- **Applies:** every intake, every question before the design gate, every mockup iteration, every change cycle's intake, every escalation about product behaviour. The sign: a message to the owner offering options for a feature they have not yet described, or an intake batch whose feature questions carry answer lists.
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

A question the design must put to the owner before the gate about what the software does or how a feature behaves — a case the description left open that the design has to settle, an open question the critique raised — is asked as intake.md's sorting of questions says: a conversation in their own words, never options you guessed. The gate's decisions above keep the question form, since each approves something the design has already written down.
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

### commands/evaluate-reports.md, the sign-off (item 5)

````markdown
5. **Sign-off by scope.** The owner signs off what changes what they see, pay or decide, each as a question of its own in the app's question form; nothing of that kind changes before they do. Everything else the maintainer decides under the bridge's escalation rule and reports in the evaluation. An accepted fix goes into a release, an accepted pitfall into the Known Pitfalls, an accepted gap into the plan.
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
its sentence in its home) and "Non-goals" (the places that keep the form, pinned as invariants, one assert per place).

KP-052: the one non-ASCII character these pins need, the em dash, is built with chr(), never typed."""
import os

from phase_modules import flat, read, rule, section

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRIDGE = os.path.join(ROOT, "bridge")
CORE = os.path.join(BRIDGE, "commands", "supervisor.md")
EVALUATE = os.path.join(BRIDGE, "commands", "evaluate-reports.md")
SKILL = os.path.join(BRIDGE, "skills", "explain-for-decision", "SKILL.md")
PHASES = os.path.join(BRIDGE, "cursor-bridge", "workflow", "phases")
INTAKE = os.path.join(PHASES, "intake.md")
MOCKUPS = os.path.join(PHASES, "interface", "mockups.md")
CHANGE_CYCLE = os.path.join(PHASES, "change-cycle.md")
DESIGN = os.path.join(PHASES, "design.md")
INTERFACE = os.path.join(PHASES, "interface.md")
RUN_PARAMETERS = os.path.join(PHASES, "run-parameters.md")
CONFIGURATION = os.path.join(PHASES, "configuration.md")
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
    assert ("**A question about the project's parameters** " + DASH + " a fact the bridge's own procedures consume in "
            "a fixed form, one of this closed list: the kind (`private` or `commercial`), the platform and runtime "
            "context, the delivery kind, the confirmation of a part's product type or sub-type as you classified it "
            "from their answers (each definition in one line), the figure of a budget or a limit " + DASH + " may be "
            "asked in the question form (`AskUserQuestion`, the default or the recommended answer first), so that "
            "answering it is one choice.") in procedure


def test_hotfix003_intake_a_question_about_the_software_is_a_conversation():
    procedure = flat(section(read(INTAKE), "The procedure", 3))
    assert ("**A question about the software itself** " + DASH + " what it does, which features it has and how each "
            "behaves, who uses it and how, what happens in a case the description leaves open; the gaps, contradictions "
            "and better options above " + DASH + " is a conversation: numbered questions in prose, batched, each "
            "answered in the owner's own words, your follow-ups building on their answers; never a list of answers you "
            "guessed for the owner to tick (the owner's rule of 2026-11-08, who found such options too rigid when a "
            "supervisor offered them at intake).") in procedure


def test_hotfix003_intake_a_question_that_is_both_is_a_conversation():
    """The tie-break (round 1, plan-critic S1 and Review B's first Blocking): a fact about the software that fixes a
    parameter is a conversation, and a short answer never makes a question a parameter."""
    procedure = flat(section(read(INTAKE), "The procedure", 3))
    assert ("**A question that is both** " + DASH + " a fact about the software that fixes a parameter, the open list's "
            "deciding questions among them (does it keep data for its users; does its user meet it in a browser) " + DASH
            + " is asked as a conversation: a conversation carries a parameter's answer, the form cannot carry a "
            "description. That a feature's answer could be written in a fixed form never makes it a parameter: a "
            "parameter is one the list above names, not a question whose answers are short.") in procedure


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
            "(`interface.md`, \"The gate\") and for a parameter in a fixed form that a screen turns on (one of "
            "intake.md's closed list: the smallest screen width the design must fit, a figure); how a screen should "
            "behave is never such a parameter, however short its answer.") in procedure
    assert "for discrete choices" not in procedure


# --- change-cycle.md, item 1: the change's intake in the same form

def test_hotfix003_a_change_is_interrogated_in_the_same_form():
    text = read(CHANGE_CYCLE)
    assert ("Interrogate the request the same way as a new project's description " + DASH + " gaps, contradictions, "
            "better options, and in the same form (intake.md's sorting of questions: the change's features and "
            "behaviour as a conversation in the owner's own words, a parameter in the question form) " + DASH + " but "
            "only about the delta") in item(text, 1, "Intake of the change")


# --- design.md, "The gate": a question before the gate

def test_hotfix003_a_question_before_the_design_gate_is_a_conversation():
    gate = flat(section(read(DESIGN), "The gate", 3))
    assert ("A question the design must put to the owner before the gate about what the software does or how a "
            "feature behaves " + DASH + " a case the description left open that the design has to settle, an open "
            "question the critique raised " + DASH + " is asked as intake.md's sorting of questions says: a "
            "conversation in their own words, never options you guessed. The gate's decisions above keep the question "
            "form, since each approves something the design has already written down.") in gate


# --- the core: the escalation passage, its skill summary, the reporting rule and rule 12's bound

def test_hotfix003_an_escalation_about_behaviour_is_a_conversation():
    passage = flat(section(read(CORE), "Escalate to the user when", 2))
    assert ("When you do escalate, lead with the decision, recommend one where there are answers to choose between, "
            "then wait. The options are put only where the decision is one between answers that exist before the owner "
            "speaks (rule 12's bound, among them scope, a consequence they bear, an item that costs money, an "
            "irreversible step, a reading of an approved requirement, a change to what \"correct\" means); a decision "
            "about what the software should do or how a feature behaves, which the owner has not yet described, is "
            "asked as a conversation in the owner's own words, never as options you guessed and with no recommendation "
            "before their answer, mid-build as at intake (intake.md's sorting of questions): your own view of it, where "
            "you have one, follows their answer as a follow-up, as intake's better-options bucket does.") in passage
    assert "lead with the decision and the options" not in passage


def test_hotfix003_the_recommendation_comes_only_where_answers_exist():
    """Round 2 (plan-critic S2, Review B's first Should fix): the skill summary in the escalation section and the
    reporting rule's first bullet bound the recommendation as the passage and the brief do."""
    passage = flat(section(read(CORE), "Escalate to the user when", 2))
    assert ("the options in the user's currency and your recommendation, where the answers exist before they speak; "
            "what you decide regardless") in passage
    reporting = flat(section(read(CORE), "Reporting to the user", 2))
    assert ("a product-behaviour or scope call " + DASH + " stated as one question, with your recommendation where the "
            "answers exist before they speak (a behaviour they have not yet described is asked in prose, rule 12's "
            "bound); or, if nothing is needed,") in reporting


def test_hotfix003_rule_12_bounds_the_question_form():
    text = rule(12)
    assert ("A decision the owner owns is asked in the question form (the `AskUserQuestion` tool, the recommended "
            "option first), so that answering it is one choice.") in text
    assert ("The form is for a decision between answers that exist before the owner speaks, or a fact the bridge needs "
            "in a fixed form " + DASH + " a gate, a run parameter, a project parameter, a figure the owner names, a scope "
            "question (deferring or dropping a requirement), a consequence they bear (rule 56), an item that costs "
            "money, an irreversible step, a reading of an approved requirement, a change to what \"correct\" means; a "
            "decision about what the software should do or how a feature behaves is the owner's too, but its answer is "
            "theirs to describe, so it is asked as a conversation in their own words, never as options you guessed, "
            "wherever it arises " + DASH + " intake, a change's intake, the mockup iteration, a question before the "
            "design gate, an escalation mid-build (intake.md's sorting of questions; the owner's rule of 2026-11-08).") in text


# --- the explain-for-decision brief, parts 1, 4 and 5

def test_hotfix003_the_decision_brief_puts_options_only_where_answers_exist():
    brief = flat(section(read(SKILL), "The decision brief " + DASH + " when a decision is put to the user", 2))
    assert ("1. **The decision** " + DASH + " one sentence: what you are choosing between, or, for a behaviour the user "
            "has not yet described, the case the software must settle.") in brief
    assert ("Options are for a decision between answers that exist before the user speaks (a gate's approval of what "
            "the design or the mockup already writes down, scope, a consequence they bear, money, an irreversible step, "
            "a reading of an approved requirement, a change to what \"correct\" means); when the decision is what the "
            "software should do or how a feature behaves and the user has not yet described it, this part is the "
            "question itself, in prose, answered in the user's own words " + DASH + " never options you guessed for them "
            "to tick (`intake.md`, the sorting of questions; the owner's rule of 2026-11-08) " + DASH + " and part 5 "
            "waits for their answer: your view comes as a follow-up building on it, as intake's better-options bucket "
            "does.") in brief
    assert ("5. **Recommendation** " + DASH + " which one, and the reason in the user's currency; withheld for a "
            "behaviour the user has not yet described (part 4).") in brief


# --- Known-Pitfalls: KP-075

def test_hotfix003_kp075_names_the_pitfall_its_places_and_its_sign():
    text = read(PITFALLS)
    assert "### KP-075 " + DASH + " A question's sort left to the supervisor licensed guessed feature options at intake" in text
    entry = text[text.index("### KP-075"):]
    assert "**Correction (2026.11.09a):**" in entry
    assert ("(one of intake.md's closed list of facts the bridge's own procedures consume in a fixed form: the kind, the "
            "platform and runtime context, the delivery kind, the confirmation of a classification, a figure) may take "
            "the question form, the default or recommended answer first, and a short answer never makes a question a "
            "parameter") in entry
    assert ("(intake.md, change-cycle.md item 1, interface/mockups.md, design.md \"The gate\", the core's \"Escalate to "
            "the user when\", the explain-for-decision brief's part 4)") in entry
    assert ("**Applies:** every intake, every question before the design gate, every mockup iteration, every change "
            "cycle's intake, every escalation about product behaviour.") in entry
    assert ("The sign: a message to the owner offering options for a feature they have not yet described, or an intake "
            "batch whose feature questions carry answer lists.") in entry


# --- the places that keep the form (invariants of the hotfix's non-goals, one assert per place)

def test_hotfix003_the_kind_the_gates_the_run_parameters_the_figure_and_the_sign_off_keep_the_form():
    assert ("it the owner is asked is the kind, as its own question in the question form, `private` named") in read(INTAKE)
    assert ("each asked as a question of its own in the app's question form") in flat(read(DESIGN))
    assert ("each part's traits are a decision of their own, asked in the question form") in flat(read(DESIGN))
    assert ("each variant's approval asked as a question of its own in the app's question form") in flat(section(read(INTERFACE), "The gate", 3))
    assert ("each as a question of its own in the app's question form** (`AskUserQuestion`,") in flat(read(RUN_PARAMETERS))
    assert ("A limit the owner names is theirs: ask for the figure in the question form.") in flat(read(CONFIGURATION))
    assert ("each as a question of its own in the app's question form; nothing of that kind changes before they do") in flat(read(EVALUATE))
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
   "id": "i06",
   "file": "bridge/cursor-bridge/workflow/phases/intake.md",
   "pairs": [
    {
     "old": "is asked as a conversation: a conversation carries a parameter's answer, the form cannot carry a description",
     "new": "may be asked in the question form where its answer is short"
    }
   ],
   "tests": [
    "tests/test_hotfix_intake.py"
   ],
   "expect_fail": [
    "tests/test_hotfix_intake.py::test_hotfix003_intake_a_question_that_is_both_is_a_conversation"
   ]
  },
  {
   "id": "i07",
   "file": "bridge/cursor-bridge/workflow/phases/intake.md",
   "pairs": [
    {
     "old": "a fact the bridge's own procedures consume in a fixed form, one of this closed list:",
     "new": "a fact the bridge needs in a fixed form, such as"
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
   "id": "m03",
   "file": "bridge/cursor-bridge/workflow/phases/interface/mockups.md",
   "pairs": [
    {
     "old": "how a screen should behave is never such a parameter, however short its answer",
     "new": "how a screen should behave is such a parameter where its answer is short"
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
   "id": "d01",
   "file": "bridge/cursor-bridge/workflow/phases/design.md",
   "pairs": [
    {
     "old": "is asked as intake.md's sorting of questions says: a conversation in their own words, never options you guessed",
     "new": "is asked in the question form, the likeliest behaviours as its options"
    }
   ],
   "tests": [
    "tests/test_hotfix_intake.py"
   ],
   "expect_fail": [
    "tests/test_hotfix_intake.py::test_hotfix003_a_question_before_the_design_gate_is_a_conversation"
   ]
  },
  {
   "id": "r01",
   "file": "bridge/commands/supervisor.md",
   "pairs": [
    {
     "old": "never as options you guessed, wherever it arises",
     "new": "or as options you guessed where the owner has not described it, wherever it arises"
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
   "id": "r03",
   "file": "bridge/commands/supervisor.md",
   "pairs": [
    {
     "old": "never as options you guessed and with no recommendation before their answer",
     "new": "or as options you guessed, your recommendation first"
    }
   ],
   "tests": [
    "tests/test_hotfix_intake.py"
   ],
   "expect_fail": [
    "tests/test_hotfix_intake.py::test_hotfix003_an_escalation_about_behaviour_is_a_conversation"
   ]
  },
  {
   "id": "r04",
   "file": "bridge/commands/supervisor.md",
   "pairs": [
    {
     "old": "When you do escalate, lead with the decision, recommend one",
     "new": "When you do escalate, lead with the decision and the options, recommend one"
    }
   ],
   "tests": [
    "tests/test_hotfix_intake.py"
   ],
   "expect_fail": [
    "tests/test_hotfix_intake.py::test_hotfix003_an_escalation_about_behaviour_is_a_conversation"
   ]
  },
  {
   "id": "r05",
   "file": "bridge/commands/supervisor.md",
   "pairs": [
    {
     "old": "stated as one question, with your recommendation where\n  the answers exist before they speak",
     "new": "stated as one question with your recommendation"
    }
   ],
   "tests": [
    "tests/test_hotfix_intake.py"
   ],
   "expect_fail": [
    "tests/test_hotfix_intake.py::test_hotfix003_the_recommendation_comes_only_where_answers_exist"
   ]
  },
  {
   "id": "r06",
   "file": "bridge/commands/supervisor.md",
   "pairs": [
    {
     "old": "and your recommendation, where the answers exist\nbefore they speak;",
     "new": "and your recommendation;"
    }
   ],
   "tests": [
    "tests/test_hotfix_intake.py"
   ],
   "expect_fail": [
    "tests/test_hotfix_intake.py::test_hotfix003_the_recommendation_comes_only_where_answers_exist"
   ]
  },
  {
   "id": "i08",
   "file": "bridge/cursor-bridge/workflow/phases/intake.md",
   "pairs": [
    {
     "old": "Stop asking when the remaining unknowns",
     "new": "Use `AskUserQuestion` where the answer is a choice among options. Stop asking when the remaining unknowns"
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
   "id": "s01",
   "file": "bridge/skills/explain-for-decision/SKILL.md",
   "pairs": [
    {
     "old": "this part is the question itself, in prose,",
     "new": "this part lists the behaviours you would choose between,"
    }
   ],
   "tests": [
    "tests/test_hotfix_intake.py"
   ],
   "expect_fail": [
    "tests/test_hotfix_intake.py::test_hotfix003_the_decision_brief_puts_options_only_where_answers_exist"
   ]
  },
  {
   "id": "s02",
   "file": "bridge/skills/explain-for-decision/SKILL.md",
   "pairs": [
    {
     "old": "withheld for a\n   behaviour the user has not yet described (part 4)",
     "new": "given for every decision"
    }
   ],
   "tests": [
    "tests/test_hotfix_intake.py"
   ],
   "expect_fail": [
    "tests/test_hotfix_intake.py::test_hotfix003_the_decision_brief_puts_options_only_where_answers_exist"
   ]
  },
  {
   "id": "s03",
   "file": "bridge/skills/explain-for-decision/SKILL.md",
   "pairs": [
    {
     "old": "(a gate's approval of what\n   the design or the mockup already writes down,",
     "new": "(a gate,"
    }
   ],
   "tests": [
    "tests/test_hotfix_intake.py"
   ],
   "expect_fail": [
    "tests/test_hotfix_intake.py::test_hotfix003_the_decision_brief_puts_options_only_where_answers_exist"
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
    "tests/test_hotfix_intake.py::test_hotfix003_kp075_names_the_pitfall_its_places_and_its_sign"
   ]
  },
  {
   "id": "k02",
   "file": "bridge/cursor-bridge/Known-Pitfalls.md",
   "pairs": [
    {
     "old": "The sign: a message to the owner offering options for a feature they have not yet described",
     "new": "The sign: an owner who complains of options"
    }
   ],
   "tests": [
    "tests/test_hotfix_intake.py"
   ],
   "expect_fail": [
    "tests/test_hotfix_intake.py::test_hotfix003_kp075_names_the_pitfall_its_places_and_its_sign"
   ]
  },
  {
   "id": "n01",
   "file": "bridge/cursor-bridge/workflow/phases/intake.md",
   "pairs": [
    {
     "old": "as its own question in the question form, `private` named",
     "new": "in prose, `private` named"
    }
   ],
   "tests": [
    "tests/test_hotfix_intake.py"
   ],
   "expect_fail": [
    "tests/test_hotfix_intake.py::test_hotfix003_the_kind_the_gates_the_run_parameters_the_figure_and_the_sign_off_keep_the_form"
   ]
  },
  {
   "id": "n02",
   "file": "bridge/cursor-bridge/workflow/phases/design.md",
   "pairs": [
    {
     "old": "app's question form,** within the skill's budget each",
     "new": "prose,** within the skill's budget each"
    }
   ],
   "tests": [
    "tests/test_hotfix_intake.py"
   ],
   "expect_fail": [
    "tests/test_hotfix_intake.py::test_hotfix003_the_kind_the_gates_the_run_parameters_the_figure_and_the_sign_off_keep_the_form"
   ]
  },
  {
   "id": "n03",
   "file": "bridge/cursor-bridge/workflow/phases/design.md",
   "pairs": [
    {
     "old": "each part's traits are a decision of their own, asked in the question form",
     "new": "each part's traits are a decision of their own, asked in prose"
    }
   ],
   "tests": [
    "tests/test_hotfix_intake.py"
   ],
   "expect_fail": [
    "tests/test_hotfix_intake.py::test_hotfix003_the_kind_the_gates_the_run_parameters_the_figure_and_the_sign_off_keep_the_form"
   ]
  },
  {
   "id": "n04",
   "file": "bridge/cursor-bridge/workflow/phases/interface.md",
   "pairs": [
    {
     "old": "each variant's approval asked as a question of its own in the app's question form",
     "new": "each variant's approval asked in prose"
    }
   ],
   "tests": [
    "tests/test_hotfix_intake.py"
   ],
   "expect_fail": [
    "tests/test_hotfix_intake.py::test_hotfix003_the_kind_the_gates_the_run_parameters_the_figure_and_the_sign_off_keep_the_form"
   ]
  },
  {
   "id": "n05",
   "file": "bridge/cursor-bridge/workflow/phases/run-parameters.md",
   "pairs": [
    {
     "old": "each as a question of its own in the app's question form** (`AskUserQuestion`,",
     "new": "each in prose** (`AskUserQuestion`,"
    }
   ],
   "tests": [
    "tests/test_hotfix_intake.py"
   ],
   "expect_fail": [
    "tests/test_hotfix_intake.py::test_hotfix003_the_kind_the_gates_the_run_parameters_the_figure_and_the_sign_off_keep_the_form"
   ]
  },
  {
   "id": "n06",
   "file": "bridge/cursor-bridge/workflow/phases/configuration.md",
   "pairs": [
    {
     "old": "ask for the figure in the question form",
     "new": "ask for the figure in prose"
    }
   ],
   "tests": [
    "tests/test_hotfix_intake.py"
   ],
   "expect_fail": [
    "tests/test_hotfix_intake.py::test_hotfix003_the_kind_the_gates_the_run_parameters_the_figure_and_the_sign_off_keep_the_form"
   ]
  },
  {
   "id": "n07",
   "file": "bridge/commands/evaluate-reports.md",
   "pairs": [
    {
     "old": "each as a question of its own in the app's question form; nothing",
     "new": "each in prose; nothing"
    }
   ],
   "tests": [
    "tests/test_hotfix_intake.py"
   ],
   "expect_fail": [
    "tests/test_hotfix_intake.py::test_hotfix003_the_kind_the_gates_the_run_parameters_the_figure_and_the_sign_off_keep_the_form"
   ]
  }
 ],
 "new_tests": [
  "tests/test_hotfix_intake.py::test_hotfix003_intake_sorts_a_question_by_what_it_asks",
  "tests/test_hotfix_intake.py::test_hotfix003_intake_a_parameter_question_may_take_the_question_form",
  "tests/test_hotfix_intake.py::test_hotfix003_intake_a_question_about_the_software_is_a_conversation",
  "tests/test_hotfix_intake.py::test_hotfix003_intake_a_question_that_is_both_is_a_conversation",
  "tests/test_hotfix_intake.py::test_hotfix003_intake_the_stop_rule_stays_and_the_old_sort_is_gone",
  "tests/test_hotfix_intake.py::test_hotfix003_the_mockup_iteration_is_a_conversation",
  "tests/test_hotfix_intake.py::test_hotfix003_a_change_is_interrogated_in_the_same_form",
  "tests/test_hotfix_intake.py::test_hotfix003_a_question_before_the_design_gate_is_a_conversation",
  "tests/test_hotfix_intake.py::test_hotfix003_an_escalation_about_behaviour_is_a_conversation",
  "tests/test_hotfix_intake.py::test_hotfix003_the_recommendation_comes_only_where_answers_exist",
  "tests/test_hotfix_intake.py::test_hotfix003_rule_12_bounds_the_question_form",
  "tests/test_hotfix_intake.py::test_hotfix003_the_decision_brief_puts_options_only_where_answers_exist",
  "tests/test_hotfix_intake.py::test_hotfix003_kp075_names_the_pitfall_its_places_and_its_sign"
 ],
 "untracked": []
}
````

## The committed diff since the last round's file (821a7f6)

````diff
diff --git a/bridge/commands/supervisor.md b/bridge/commands/supervisor.md
index cc2b603..63550ac 100644
--- a/bridge/commands/supervisor.md
+++ b/bridge/commands/supervisor.md
@@ -328,7 +328,7 @@ already done, a planned approach turned out infeasible — surface it as a notif
 a stop-cord ("here is what I found and what I'm doing about it; say so if you'd rather I
 didn't") and proceed. Inform; don't ask.
 
-When you do escalate, lead with the decision, recommend one, then wait. The options are put only where the decision is one between answers that exist before the owner speaks (rule 12's bound: money, scope, an irreversible step, a reading of an approved requirement); a decision about what the software should do or how a feature behaves is asked as a conversation in the owner's own words, never as options you guessed, mid-build as at intake (intake.md's sorting of questions).
+When you do escalate, lead with the decision, recommend one where there are answers to choose between, then wait. The options are put only where the decision is one between answers that exist before the owner speaks (rule 12's bound, among them scope, a consequence they bear, an item that costs money, an irreversible step, a reading of an approved requirement, a change to what "correct" means); a decision about what the software should do or how a feature behaves, which the owner has not yet described, is asked as a conversation in the owner's own words, never as options you guessed and with no recommendation before their answer, mid-build as at intake (intake.md's sorting of questions): your own view of it, where you have one, follows their answer as a follow-up, as intake's better-options bucket does.
 Between escalations, do not ask for permission you already have — an approved build plan
 is approval to execute it.
 
@@ -336,8 +336,8 @@ is approval to execute it.
 moment a technical matter surfaces for a non-engineer to decide, and the decision is only as
 good as their understanding of it. Use the skill's decision-brief shape (the decision; why it
 is theirs; the at-most-three load-bearing concepts, parts before the whole, one instance, one
-stake; the options in the user's currency; your recommendation; what you decide regardless)
-and run its self-check before sending.
+stake; the options in the user's currency and your recommendation, where the answers exist
+before they speak; what you decide regardless) and run its self-check before sending.
 
 ---
 
@@ -350,8 +350,9 @@ theirs — if anything — impossible to miss:
 
 - **Lead with the decision they own, or its absence.** Open with either the single
   plain-language thing you need from them — a key or secret, a spend authorisation, a
-  product-behaviour or scope call — stated as one question with your recommendation; or, if
-  nothing is needed, open with **"Nothing needed — proceeding"** (or "…stopped, awaiting only
+  product-behaviour or scope call — stated as one question, with your recommendation where
+  the answers exist before they speak (a behaviour they have not yet described is asked in
+  prose, rule 12's bound); or, if nothing is needed, open with **"Nothing needed — proceeding"** (or "…stopped, awaiting only
   \<the one thing\>"). The user should be able to stop reading after the first line and know
   whether you want anything.
 - **Name the model switch at the stage close before it.** Where the next stage runs on
@@ -557,7 +558,7 @@ has to ride PRs to reach the remote; decide per project which you need and keep
 12. Every report to the user leads with the one decision they own — or "Nothing needed —
     proceeding" — and marks all technical detail as FYI beneath it. Translate consequences
     into behaviour, cost, risk, and reversibility; never hand a non-engineer a technical
-    narrative to parse or a technical menu to pick from. A decision the owner owns is asked in the question form (the `AskUserQuestion` tool, the recommended option first), so that answering it is one choice. The form is for a decision between answers that exist before the owner speaks, or a fact the bridge needs in a fixed form — a gate, a run parameter, a project parameter, a figure the owner names, a scope question (deferring or dropping a requirement), an item that costs money, an irreversible step, a reading of an approved requirement; a decision about what the software should do or how a feature behaves is the owner's too, but its answer is theirs to describe, so it is asked as a conversation in their own words, never as options you guessed, wherever it arises — intake, a change's intake, the mockup iteration, a question before the design gate, an escalation mid-build (intake.md's sorting of questions; the owner's rule of 2026-11-08). When several rules claim the first line at once, the order is: a decision the
+    narrative to parse or a technical menu to pick from. A decision the owner owns is asked in the question form (the `AskUserQuestion` tool, the recommended option first), so that answering it is one choice. The form is for a decision between answers that exist before the owner speaks, or a fact the bridge needs in a fixed form — a gate, a run parameter, a project parameter, a figure the owner names, a scope question (deferring or dropping a requirement), a consequence they bear (rule 56), an item that costs money, an irreversible step, a reading of an approved requirement, a change to what "correct" means; a decision about what the software should do or how a feature behaves is the owner's too, but its answer is theirs to describe, so it is asked as a conversation in their own words, never as options you guessed, wherever it arises — intake, a change's intake, the mockup iteration, a question before the design gate, an escalation mid-build (intake.md's sorting of questions; the owner's rule of 2026-11-08). When several rules claim the first line at once, the order is: a decision the
     owner owns; a key seen in the chat (rule 53); a gate decision you took under rule 50;
     the session model switch (rule 48). The rest follow, each on its own line.
 13. Design correctness — accessibility and interface MUSTs, plus the deterministic
diff --git a/bridge/cursor-bridge/Known-Pitfalls.md b/bridge/cursor-bridge/Known-Pitfalls.md
index 5c39760..4183d18 100644
--- a/bridge/cursor-bridge/Known-Pitfalls.md
+++ b/bridge/cursor-bridge/Known-Pitfalls.md
@@ -627,5 +627,5 @@ it applies.**
 - **Mistake:** at intake, a question about the software's features was put to the owner as a list of options the supervisor had guessed, for them to tick.
 - **Surfaced:** a project supervisor, 2026-11-08: asked about a feature's behaviour, it offered guessed options in the app's question form; the owner rejected them as too rigid and ruled that the fixed questions setting a project's parameters (private or commercial, the platform, the product type) may keep the question form, while the software's features and their behaviour are discussed as a conversation, numbered questions in prose answered in the owner's own words, follow-ups building on the answers, never guessed options to tick (the bridge's INVENTORY, Decisions, 2026-11-08).
 - **Cause:** the installed intake text sorted a question into the form or prose by whether its answer was a choice among options, which left the sort to the supervisor: any question whose answers it could imagine became a choice, and a guessed option frames the feature before the owner has described it, so the answer measures the guess, not the owner's intent.
-- **Correction (2026.11.09a):** the sort is by what a question asks, never by whether its answers can be guessed: a question about the project's parameters (a fact the bridge needs in a fixed form) may take the question form, the default or recommended answer first; a question about the software itself is a conversation in the owner's own words, and a question that is both is a conversation too, at intake, in a change cycle's intake, in the mockup iteration, before the design gate and in an escalation mid-build alike (intake.md, change-cycle.md item 1, interface/mockups.md, design.md "The gate", the core's "Escalate to the user when", the explain-for-decision brief's part 4); the core's rule 12 bounds the form to a decision between answers that exist before the owner speaks or a fact the bridge needs in a fixed form (a gate, a run parameter, a project parameter, a figure, a scope question, an item that costs money, an irreversible step, a reading of an approved requirement).
-- **Applies:** every intake, every change cycle's intake, every mockup iteration, every escalation about product behaviour. The sign: a message to the owner offering options for a feature they have not yet described, or an intake batch whose feature questions carry answer lists.
+- **Correction (2026.11.09a):** the sort is by what a question asks, never by whether its answers can be guessed: a question about the project's parameters (one of intake.md's closed list of facts the bridge's own procedures consume in a fixed form: the kind, the platform and runtime context, the delivery kind, the confirmation of a classification, a figure) may take the question form, the default or recommended answer first, and a short answer never makes a question a parameter; a question about the software itself is a conversation in the owner's own words, with no recommendation before the owner's answer, and a question that is both is a conversation too, at intake, in a change cycle's intake, in the mockup iteration, before the design gate and in an escalation mid-build alike (intake.md, change-cycle.md item 1, interface/mockups.md, design.md "The gate", the core's "Escalate to the user when", the explain-for-decision brief's part 4); the core's rule 12 bounds the form to a decision between answers that exist before the owner speaks or a fact the bridge needs in a fixed form (a gate, a run parameter, a project parameter, a figure, a scope question, a consequence the owner bears, an item that costs money, an irreversible step, a reading of an approved requirement, a change to what "correct" means).
+- **Applies:** every intake, every question before the design gate, every mockup iteration, every change cycle's intake, every escalation about product behaviour. The sign: a message to the owner offering options for a feature they have not yet described, or an intake batch whose feature questions carry answer lists.
diff --git a/bridge/cursor-bridge/workflow/phases/design.md b/bridge/cursor-bridge/workflow/phases/design.md
index 8b8a549..ab46c56 100644
--- a/bridge/cursor-bridge/workflow/phases/design.md
+++ b/bridge/cursor-bridge/workflow/phases/design.md
@@ -212,7 +212,7 @@ one round and one that needed four are visibly different things); and, apart fro
 item that costs money or needs an account (code signing, a paid driver, a provider) — never
 one presentation of everything (plan 8.8). The **Level 1 diagrams** (use cases, operational workflows) state what the software does, so present them as part of what the owner approves; the other levels are technical, named in the brief and available to read (they render in Markdown viewers that support Mermaid), not put to the owner as questions.
 
-A question the design must put to the owner before the gate about what the software does or how a feature behaves — a case the description left open that the design has to settle, an open question the critique raised — is asked as intake.md's sorting of questions says: a conversation in their own words, never options you guessed. The gate's decisions above keep the question form, since each approves a behaviour the design has already written down.
+A question the design must put to the owner before the gate about what the software does or how a feature behaves — a case the description left open that the design has to settle, an open question the critique raised — is asked as intake.md's sorting of questions says: a conversation in their own words, never options you guessed. The gate's decisions above keep the question form, since each approves something the design has already written down.
 
 Once approved, write **`Documents/<Name> Project Summary.md`** — the human-facing account
 of what is being built, for whom, the architecture in plain language, the key decisions and
diff --git a/bridge/cursor-bridge/workflow/phases/intake.md b/bridge/cursor-bridge/workflow/phases/intake.md
index 3cff956..e27d3e1 100644
--- a/bridge/cursor-bridge/workflow/phases/intake.md
+++ b/bridge/cursor-bridge/workflow/phases/intake.md
@@ -64,7 +64,7 @@ and integrations**. From the data sensitivity, choose the **OWASP ASVS level** 
 gated against. This is what lets the build plan, the brief, and the `security-auditor`
 reason about IDOR/authz/data-handling later.
 
-Ask in batches, not one at a time, and sort each question by what it asks, never by whether you could guess its answers. **A question about the project's parameters** — a fact the bridge's own procedures consume in a fixed form, one of this closed list: the kind (`private` or `commercial`), the platform and runtime context, the delivery kind, a part's product type or sub-type where the owner must choose between the open list's definitions, the figure of a budget or a limit — may be asked in the question form (`AskUserQuestion`, the default or the recommended answer first), so that answering it is one choice. **A question about the software itself** — what it does, which features it has and how each behaves, who uses it and how, what happens in a case the description leaves open; the gaps, contradictions and better options above — is a conversation: numbered questions in prose, batched, each answered in the owner's own words, your follow-ups building on their answers; never a list of answers you guessed for the owner to tick — the owner's rule of 2026-11-08, who found such options too rigid when a supervisor offered them at intake: a guessed option frames the feature before the owner has described it, and their answer then measures your guess, not their intent. **A question that is both** — a fact about the software that fixes a parameter, the open list's deciding questions among them (does it keep data for its users; does its user meet it in a browser) — is asked as a conversation: a conversation carries a parameter's answer, the form cannot carry a description. That a feature's answer could be written in a fixed form never makes it a parameter: a parameter is one the list above names, not a question whose answers are short. Stop asking when the remaining unknowns are ones a competent implementer could decide without you.
+Ask in batches, not one at a time, and sort each question by what it asks, never by whether you could guess its answers. **A question about the project's parameters** — a fact the bridge's own procedures consume in a fixed form, one of this closed list: the kind (`private` or `commercial`), the platform and runtime context, the delivery kind, the confirmation of a part's product type or sub-type as you classified it from their answers (each definition in one line), the figure of a budget or a limit — may be asked in the question form (`AskUserQuestion`, the default or the recommended answer first), so that answering it is one choice. **A question about the software itself** — what it does, which features it has and how each behaves, who uses it and how, what happens in a case the description leaves open; the gaps, contradictions and better options above — is a conversation: numbered questions in prose, batched, each answered in the owner's own words, your follow-ups building on their answers; never a list of answers you guessed for the owner to tick (the owner's rule of 2026-11-08, who found such options too rigid when a supervisor offered them at intake). **A question that is both** — a fact about the software that fixes a parameter, the open list's deciding questions among them (does it keep data for its users; does its user meet it in a browser) — is asked as a conversation: a conversation carries a parameter's answer, the form cannot carry a description. That a feature's answer could be written in a fixed form never makes it a parameter: a parameter is one the list above names, not a question whose answers are short. Stop asking when the remaining unknowns are ones a competent implementer could decide without you.
 
 Also at intake: **fix the software name** — the name the user will call the product. It
 names the four `Documents/` files (see "The project layout") and never changes; if the user
diff --git a/bridge/cursor-bridge/workflow/phases/interface/mockups.md b/bridge/cursor-bridge/workflow/phases/interface/mockups.md
index 6dec91f..e4dd330 100644
--- a/bridge/cursor-bridge/workflow/phases/interface/mockups.md
+++ b/bridge/cursor-bridge/workflow/phases/interface/mockups.md
@@ -24,7 +24,7 @@ product rather than a default layout, and actively avoid the tells that make a U
 machine-generated — including this model's own persistent house style. A mockup that looks
 like the generic default is a signal to reconsider, not to present.
 
-Iterate with the user until they are satisfied — expect change requests; this is where UI decisions are cheap to make. The iteration is a conversation, as intake's questions about the software are (`intake.md`, the sorting of questions): ask what they would change and why, numbered where several points are open, answered in their own words, your follow-ups building on the answers; variants of a screen you guessed are never put as options to tick. The question form is kept for the gate's approval (`interface.md`, "The gate") and for a parameter in a fixed form that a screen turns on (the smallest screen width the design must fit, say); how a screen should behave is never such a parameter, however short its answer.
+Iterate with the user until they are satisfied — expect change requests; this is where UI decisions are cheap to make. The iteration is a conversation, as intake's questions about the software are (`intake.md`, the sorting of questions): ask what they would change and why, numbered where several points are open, answered in their own words, your follow-ups building on the answers; variants of a screen you guessed are never put as options to tick. The question form is kept for the gate's approval (`interface.md`, "The gate") and for a parameter in a fixed form that a screen turns on (one of intake.md's closed list: the smallest screen width the design must fit, a figure); how a screen should behave is never such a parameter, however short its answer.
 
 ### The design-tooling flow
 
diff --git a/bridge/cursor-bridge/workflow/trace-exceptions.md b/bridge/cursor-bridge/workflow/trace-exceptions.md
index 2b8a52b..c0404aa 100644
--- a/bridge/cursor-bridge/workflow/trace-exceptions.md
+++ b/bridge/cursor-bridge/workflow/trace-exceptions.md
@@ -199,3 +199,4 @@ Entries use the form `- <kind> <id> <file> <heading>` where `<kind>` is `reword`
 - reword HOTFIX-003 bridge/commands/supervisor.md Phase 3 — UI mockups
 - new HOTFIX-003 bridge/cursor-bridge/workflow/phases/interface/mockups.md The procedure
 - reword HOTFIX-003 bridge/commands/supervisor.md Escalate to the user when
+- reword HOTFIX-003 bridge/commands/supervisor.md Reporting to the user
diff --git a/bridge/skills/explain-for-decision/SKILL.md b/bridge/skills/explain-for-decision/SKILL.md
index f7d3380..76eac31 100644
--- a/bridge/skills/explain-for-decision/SKILL.md
+++ b/bridge/skills/explain-for-decision/SKILL.md
@@ -219,7 +219,8 @@ Use this shape for every escalation and every phase-gate presentation. It is the
 the decision, recommend one, then wait" rule of `supervisor.md`, with the explanation slotted
 where it belongs:
 
-1. **The decision** — one sentence: what you are choosing between.
+1. **The decision** — one sentence: what you are choosing between, or, for a behaviour the
+   user has not yet described, the case the software must settle.
 2. **Why it is yours** — one sentence: which user-owned factor it turns on (product
    behaviour, scope, a cost or exposure you bear, something only you can provide, an
    irreversible step, a change to what "correct" means).
@@ -227,12 +228,16 @@ where it belongs:
    1–8 by its class. Parts before whole; one instance; one stake.
 4. **The options** — for each: what it means for the product in use; what it costs; what it
    forecloses or whether it can be reversed later. Same terms as in 3 (guard 2). Options are
-   for a decision between answers that exist before the user speaks (a gate, money, scope, an
-   irreversible step, a reading of an approved requirement); when the decision is what the
-   software should do or how a feature behaves, this part is the question itself, in prose,
-   answered in the user's own words — never options you guessed for them to tick
-   (`intake.md`, the sorting of questions; the owner's rule of 2026-11-08). The other parts stand.
-5. **Recommendation** — which one, and the reason in the user's currency.
+   for a decision between answers that exist before the user speaks (a gate's approval of what
+   the design or the mockup already writes down, scope, a consequence they bear, money, an
+   irreversible step, a reading of an approved requirement, a change to what "correct" means);
+   when the decision is what the software should do or how a feature behaves and the user has
+   not yet described it, this part is the question itself, in prose, answered in the user's own
+   words — never options you guessed for them to tick (`intake.md`, the sorting of questions;
+   the owner's rule of 2026-11-08) — and part 5 waits for their answer: your view comes as a
+   follow-up building on it, as intake's better-options bucket does.
+5. **Recommendation** — which one, and the reason in the user's currency; withheld for a
+   behaviour the user has not yet described (part 4).
 6. **Decided regardless** — the technical choices you make either way, one line each, so
    the user sees the boundary of what they are deciding and does not reach past it.
 
diff --git a/tests/test_core_carve.py b/tests/test_core_carve.py
index 34ca05c..bc7241c 100644
--- a/tests/test_core_carve.py
+++ b/tests/test_core_carve.py
@@ -175,12 +175,13 @@ def test_r003_a_module_read_outside_its_own_phase_is_named_with_when():
 # (BUG-043: four more move from traced to excused, which the earlier entries excuse: step 3's parallel item 4, under
 # TASK-030's, and step 3b's exit-124 paragraph and restart item and step 7's last-resort reset, under TASK-034's: each
 # now says step 4's read of `.git/config` comes before its git command)
-# (HOTFIX-003, hotfix 2026.11.09a: three more move from traced to excused, under HOTFIX-003's own `reword` entries:
+# (HOTFIX-003, hotfix 2026.11.09a: five more move from traced to excused, under HOTFIX-003's own `reword` entries:
 # intake's batches paragraph, which now sorts a question by what it asks (labelled BUG-042, whose earlier entry on
-# "Phase 1 — Intake" matches first), the mockups' iteration paragraph, under "Phase 3 — UI mockups", and the escalation
-# passage "When you do escalate", which now puts options only where the answers exist before the owner speaks, under
-# "Escalate to the user when")
-TRACED = "TRACED: 424 passages of baseline 0a186da; 137 in supervisor.md, 201 under workflow/, 0 dropped, 86 excused"
+# "Phase 1 — Intake" matches first), the mockups' iteration paragraph, under "Phase 3 — UI mockups", the escalation
+# passage "When you do escalate" and its "How you explain it" paragraph, which now put options and a recommendation only
+# where the answers exist before the owner speaks, under "Escalate to the user when", and the reporting rule's first
+# bullet, whose recommendation is bounded the same way, under "Reporting to the user")
+TRACED = "TRACED: 424 passages of baseline 0a186da; 135 in supervisor.md, 201 under workflow/, 0 dropped, 88 excused"
 NOTES = [
     "NOTE (reword TASK-034) bridge/commands/supervisor.md: The core, in brief - **Role.** The supervising architect: design, plan, package b",
     "NOTE (reword TASK-034) bridge/commands/supervisor.md: The core, in brief - **Founding rules.** N1 The loop's truth lives in files; one-",
@@ -254,6 +255,8 @@ NOTES = [
     "NOTE (reword TASK-034) bridge/commands/supervisor.md: Reflection points \\u2014 stage close, phase gates, project end - **Then the stage's demonstration runs live:** the build plan",
     "NOTE (reword TASK-034) bridge/commands/supervisor.md: Reflection points \\u2014 stage close, phase gates, project end - 5. **Record** the reflection point in `docs/PROJECT_STATUS.m",
     "NOTE (reword HOTFIX-003) bridge/commands/supervisor.md: Escalate to the user when - When you do escalate, lead with the decision and the options",
+    "NOTE (reword HOTFIX-003) bridge/commands/supervisor.md: Escalate to the user when - **How you explain it is governed by the `explain-for-decisio",
+    "NOTE (reword HOTFIX-003) bridge/commands/supervisor.md: Reporting to the user - - **Lead with the decision they own, or its absence.** Open ",
     "NOTE (reword TASK-035) bridge/commands/supervisor.md: Project state - ```markdown\\x0a# Project Status\\x0aLast updated: <timestamp>\\x0aPhase",
     "NOTE (reword TASK-015) bridge/commands/supervisor.md: Standing rules - 6. Judge re-delegation by defect class, not a round count. N",
     "NOTE (reword TASK-015) bridge/commands/supervisor.md: Standing rules - 8. Never chain shell commands with `&&`, `|`, or `;`, and ne",
@@ -283,8 +286,8 @@ def test_r003_the_carve_traces_with_exactly_its_excuses():
     pass's step 6 and rule 39; and five passages BUG-033 reworded, which those entries excuse: the refactoring
     pass's step 4 and the run parameters' Parallel increments item and its `on` option, under TASK-035's, step 3's
     Parallel increments paragraph, under TASK-030's, and rule 46, under TASK-015's; and six passages TASK-037 reworded, which those entries excuse: three under "Phase 2 \u2014 Design" (the critique's round paragraph, its stop rule and its record), the change cycle's item 2, and rules 12 and 48, under TASK-012's, TASK-014's and TASK-015's; and three passages TASK-038 reworded, which those entries excuse: the design critique's launch block under "Phase 2 \u2014 Design", and step 8's title paragraph and its after-merge paragraph, under TASK-012's and TASK-034's; and six passages TASK-039 reworded: step 3b's restart item and step 7's Accept bullet, which TASK-034's entries excuse, step 5's paragraph, under TASK-039's own entry, and, at its Review A's round 1, the design critique's convergence paragraph under "Phase 2 — Design", step 4's reviewers paragraph and rule 36, under TASK-012's, TASK-030's and TASK-015's; and four passages TASK-040 reworded, which those entries excuse: the stage review's step 8, the demonstration's paragraph and item 5, under TASK-034's, and the refactoring pass's step 2, under TASK-035's; and one passage BUG-040 reworded, the change cycle's item 4, under TASK-014's; and four passages BUG-043 reworded, which those entries excuse: step 3's parallel item 4, under TASK-030's, and step 3b's exit-124 paragraph and restart item and step 7's last-resort reset, under TASK-034's), so an increment that excuses anything more changes this test. It
-    and three passages HOTFIX-003 reworded (hotfix 2026.11.09a): intake's batches paragraph, under BUG-042's entry, and
-    the mockups' iteration paragraph and the escalation passage, under HOTFIX-003's own.
+    and five passages HOTFIX-003 reworded (hotfix 2026.11.09a): intake's batches paragraph, under BUG-042's entry, and
+    the mockups' iteration paragraph, the two escalation paragraphs and the reporting bullet, under HOTFIX-003's own.
     needs the baseline commit, which CI's depth-1 checkout lacks (INVENTORY Decisions): skipped there, run in
     the supervisor's checkout."""
     repo = os.path.abspath(os.path.join(HERE, os.pardir))
diff --git a/tests/test_hotfix_intake.py b/tests/test_hotfix_intake.py
index 9ec4fa4..759dc12 100644
--- a/tests/test_hotfix_intake.py
+++ b/tests/test_hotfix_intake.py
@@ -46,9 +46,10 @@ def test_hotfix003_intake_a_parameter_question_may_take_the_question_form():
     procedure = flat(section(read(INTAKE), "The procedure", 3))
     assert ("**A question about the project's parameters** " + DASH + " a fact the bridge's own procedures consume in "
             "a fixed form, one of this closed list: the kind (`private` or `commercial`), the platform and runtime "
-            "context, the delivery kind, a part's product type or sub-type where the owner must choose between the "
-            "open list's definitions, the figure of a budget or a limit " + DASH + " may be asked in the question form "
-            "(`AskUserQuestion`, the default or the recommended answer first), so that answering it is one choice.") in procedure
+            "context, the delivery kind, the confirmation of a part's product type or sub-type as you classified it "
+            "from their answers (each definition in one line), the figure of a budget or a limit " + DASH + " may be "
+            "asked in the question form (`AskUserQuestion`, the default or the recommended answer first), so that "
+            "answering it is one choice.") in procedure
 
 
 def test_hotfix003_intake_a_question_about_the_software_is_a_conversation():
@@ -57,9 +58,8 @@ def test_hotfix003_intake_a_question_about_the_software_is_a_conversation():
             "behaves, who uses it and how, what happens in a case the description leaves open; the gaps, contradictions "
             "and better options above " + DASH + " is a conversation: numbered questions in prose, batched, each "
             "answered in the owner's own words, your follow-ups building on their answers; never a list of answers you "
-            "guessed for the owner to tick " + DASH + " the owner's rule of 2026-11-08, who found such options too rigid "
-            "when a supervisor offered them at intake: a guessed option frames the feature before the owner has "
-            "described it, and their answer then measures your guess, not their intent.") in procedure
+            "guessed for the owner to tick (the owner's rule of 2026-11-08, who found such options too rigid when a "
+            "supervisor offered them at intake).") in procedure
 
 
 def test_hotfix003_intake_a_question_that_is_both_is_a_conversation():
@@ -89,9 +89,9 @@ def test_hotfix003_the_mockup_iteration_is_a_conversation():
             "are (`intake.md`, the sorting of questions): ask what they would change and why, numbered where several "
             "points are open, answered in their own words, your follow-ups building on the answers; variants of a "
             "screen you guessed are never put as options to tick. The question form is kept for the gate's approval "
-            "(`interface.md`, \"The gate\") and for a parameter in a fixed form that a screen turns on (the smallest "
-            "screen width the design must fit, say); how a screen should behave is never such a parameter, however "
-            "short its answer.") in procedure
+            "(`interface.md`, \"The gate\") and for a parameter in a fixed form that a screen turns on (one of "
+            "intake.md's closed list: the smallest screen width the design must fit, a figure); how a screen should "
+            "behave is never such a parameter, however short its answer.") in procedure
     assert "for discrete choices" not in procedure
 
 
@@ -113,44 +113,66 @@ def test_hotfix003_a_question_before_the_design_gate_is_a_conversation():
             "feature behaves " + DASH + " a case the description left open that the design has to settle, an open "
             "question the critique raised " + DASH + " is asked as intake.md's sorting of questions says: a "
             "conversation in their own words, never options you guessed. The gate's decisions above keep the question "
-            "form, since each approves a behaviour the design has already written down.") in gate
+            "form, since each approves something the design has already written down.") in gate
 
 
-# --- the core: the escalation passage and rule 12's bound
+# --- the core: the escalation passage, its skill summary, the reporting rule and rule 12's bound
 
 def test_hotfix003_an_escalation_about_behaviour_is_a_conversation():
     passage = flat(section(read(CORE), "Escalate to the user when", 2))
-    assert ("When you do escalate, lead with the decision, recommend one, then wait. The options are put only where "
-            "the decision is one between answers that exist before the owner speaks (rule 12's bound: money, scope, an "
-            "irreversible step, a reading of an approved requirement); a decision about what the software should do or "
-            "how a feature behaves is asked as a conversation in the owner's own words, never as options you guessed, "
-            "mid-build as at intake (intake.md's sorting of questions).") in passage
+    assert ("When you do escalate, lead with the decision, recommend one where there are answers to choose between, "
+            "then wait. The options are put only where the decision is one between answers that exist before the owner "
+            "speaks (rule 12's bound, among them scope, a consequence they bear, an item that costs money, an "
+            "irreversible step, a reading of an approved requirement, a change to what \"correct\" means); a decision "
+            "about what the software should do or how a feature behaves, which the owner has not yet described, is "
+            "asked as a conversation in the owner's own words, never as options you guessed and with no recommendation "
+            "before their answer, mid-build as at intake (intake.md's sorting of questions): your own view of it, where "
+            "you have one, follows their answer as a follow-up, as intake's better-options bucket does.") in passage
     assert "lead with the decision and the options" not in passage
 
 
+def test_hotfix003_the_recommendation_comes_only_where_answers_exist():
+    """Round 2 (plan-critic S2, Review B's first Should fix): the skill summary in the escalation section and the
+    reporting rule's first bullet bound the recommendation as the passage and the brief do."""
+    passage = flat(section(read(CORE), "Escalate to the user when", 2))
+    assert ("the options in the user's currency and your recommendation, where the answers exist before they speak; "
+            "what you decide regardless") in passage
+    reporting = flat(section(read(CORE), "Reporting to the user", 2))
+    assert ("a product-behaviour or scope call " + DASH + " stated as one question, with your recommendation where the "
+            "answers exist before they speak (a behaviour they have not yet described is asked in prose, rule 12's "
+            "bound); or, if nothing is needed,") in reporting
+
+
 def test_hotfix003_rule_12_bounds_the_question_form():
     text = rule(12)
     assert ("A decision the owner owns is asked in the question form (the `AskUserQuestion` tool, the recommended "
             "option first), so that answering it is one choice.") in text
     assert ("The form is for a decision between answers that exist before the owner speaks, or a fact the bridge needs "
             "in a fixed form " + DASH + " a gate, a run parameter, a project parameter, a figure the owner names, a scope "
-            "question (deferring or dropping a requirement), an item that costs money, an irreversible step, a reading "
-            "of an approved requirement; a decision about what the software should do or how a feature behaves is the "
-            "owner's too, but its answer is theirs to describe, so it is asked as a conversation in their own words, "
-            "never as options you guessed, wherever it arises " + DASH + " intake, a change's intake, the mockup "
-            "iteration, a question before the design gate, an escalation mid-build (intake.md's sorting of questions; "
-            "the owner's rule of 2026-11-08).") in text
+            "question (deferring or dropping a requirement), a consequence they bear (rule 56), an item that costs "
+            "money, an irreversible step, a reading of an approved requirement, a change to what \"correct\" means; a "
+            "decision about what the software should do or how a feature behaves is the owner's too, but its answer is "
+            "theirs to describe, so it is asked as a conversation in their own words, never as options you guessed, "
+            "wherever it arises " + DASH + " intake, a change's intake, the mockup iteration, a question before the "
+            "design gate, an escalation mid-build (intake.md's sorting of questions; the owner's rule of 2026-11-08).") in text
 
 
-# --- the explain-for-decision brief, part 4
+# --- the explain-for-decision brief, parts 1, 4 and 5
 
 def test_hotfix003_the_decision_brief_puts_options_only_where_answers_exist():
     brief = flat(section(read(SKILL), "The decision brief " + DASH + " when a decision is put to the user", 2))
-    assert ("Options are for a decision between answers that exist before the user speaks (a gate, money, scope, an "
-            "irreversible step, a reading of an approved requirement); when the decision is what the software should do "
-            "or how a feature behaves, this part is the question itself, in prose, answered in the user's own words "
-            + DASH + " never options you guessed for them to tick (`intake.md`, the sorting of questions; the owner's "
-            "rule of 2026-11-08). The other parts stand.") in brief
+    assert ("1. **The decision** " + DASH + " one sentence: what you are choosing between, or, for a behaviour the user "
+            "has not yet described, the case the software must settle.") in brief
+    assert ("Options are for a decision between answers that exist before the user speaks (a gate's approval of what "
+            "the design or the mockup already writes down, scope, a consequence they bear, money, an irreversible step, "
+            "a reading of an approved requirement, a change to what \"correct\" means); when the decision is what the "
+            "software should do or how a feature behaves and the user has not yet described it, this part is the "
+            "question itself, in prose, answered in the user's own words " + DASH + " never options you guessed for them "
+            "to tick (`intake.md`, the sorting of questions; the owner's rule of 2026-11-08) " + DASH + " and part 5 "
+            "waits for their answer: your view comes as a follow-up building on it, as intake's better-options bucket "
+            "does.") in brief
+    assert ("5. **Recommendation** " + DASH + " which one, and the reason in the user's currency; withheld for a "
+            "behaviour the user has not yet described (part 4).") in brief
 
 
 # --- Known-Pitfalls: KP-075
@@ -160,8 +182,14 @@ def test_hotfix003_kp075_names_the_pitfall_its_places_and_its_sign():
     assert "### KP-075 " + DASH + " A question's sort left to the supervisor licensed guessed feature options at intake" in text
     entry = text[text.index("### KP-075"):]
     assert "**Correction (2026.11.09a):**" in entry
+    assert ("(one of intake.md's closed list of facts the bridge's own procedures consume in a fixed form: the kind, the "
+            "platform and runtime context, the delivery kind, the confirmation of a classification, a figure) may take "
+            "the question form, the default or recommended answer first, and a short answer never makes a question a "
+            "parameter") in entry
     assert ("(intake.md, change-cycle.md item 1, interface/mockups.md, design.md \"The gate\", the core's \"Escalate to "
             "the user when\", the explain-for-decision brief's part 4)") in entry
+    assert ("**Applies:** every intake, every question before the design gate, every mockup iteration, every change "
+            "cycle's intake, every escalation about product behaviour.") in entry
     assert ("The sign: a message to the owner offering options for a feature they have not yet described, or an intake "
             "batch whose feature questions carry answer lists.") in entry
````
