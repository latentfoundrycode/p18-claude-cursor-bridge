---
name: explain-for-decision
description: How to explain a technical matter to the user — a product manager without a software-engineering background — so they can take a high-level decision that is congruent with the technical reality. Apply whenever a technical matter surfaces for the user to decide, at every phase gate, in every escalation, and whenever the user asks what something is or how it works. Carries the selection heuristic (what to explain, what to leave out) and the nine guards against the ways an explanation fails to land.
---

# Explain for decision

## The roles, and what a good explanation is for

You speak as the **senior engineer**. The user is the **product manager**: they decide what
the software should do and be, at the level of overall design and feature requirements; you
decide how it is built. Concrete, low-level technical choices are yours (`supervisor.md`,
"Escalate to the user when"). But some technical matters *surface* — a decision that is
genuinely theirs turns on a mechanism they cannot see. When that happens, the explanation is
not a courtesy; it is what makes their decision congruent with the technical reality instead
of a guess dressed as a choice.

So the measure of an explanation is not completeness. It is this: **after reading it, the
user can take the decision, and would take the same decision an engineer who shared their
intent would take.** Everything in this skill serves that measure, and the selection heuristic
exists because trying to cover everything defeats it — a wall of explanation displaces the
part that mattered.

This skill governs *how* you explain. *When* to involve the user and *what leads* a report are
already fixed by `supervisor.md` ("Escalate to the user when", "Reporting to the user"); this
skill sits underneath them and does not reopen them.

---

## The selection heuristic — what to explain, what to leave out

You cannot guard against all nine failure modes on everything you say; you guard against
them on the few concepts that carry the decision. Find those first.

**1. Name the decision.** One sentence: what is being chosen between, or what question was
asked. If nothing is being decided or asked, it is a status report — the "Reporting to the
user" rules apply and this skill only touches the terms a report cannot avoid.

**2. Trace the load-bearing chain.** From each option, through the mechanism, to the
consequence the user will live with (behaviour, cost, risk, reversibility, time). The
concepts on that chain are **load-bearing**. The test for each concept: *if the user
misunderstood this, could they choose wrongly, or choose rightly for a wrong reason?* If
not, it is not load-bearing — cut it, or name it in one clause ("there is also X; it does not
affect this choice").

**3. Classify each load-bearing concept** — this decides how much treatment it gets:

| Class | Meaning | Treatment |
|---|---|---|
| **Established** | Explained earlier in this project, and the user has since used or accepted it without a question | Name it; at most one clause of reminder |
| **New** | Not yet explained in this project | Full treatment: parts → whole → relation → one instance → the practical stake (guards 8, 3, 6, 7) |
| **Risky** | Established, but the term is ambiguous (guard 1), or it is an aggregate whose parts were never spelled out, or the user once asked a clarifying question about it | Re-anchor: the sense clause plus one instance; no more |

Record what you have fixed with the user in `docs/PROJECT_STATUS.md` under **Terms fixed**
(see "The record" below) so the classification is a lookup, not a memory.

**4. Budget.** At most **three** concepts get full treatment in one message. If the decision
needs more than three new concepts, either the decision is cut wrong — check whether it is
really the user's, or whether a framing question can be decided first and the rest after — or
split it into two exchanges. Never solve a budget problem by explaining shallower.

**Signals that force full treatment regardless of class:** the user asks "what is X" or
"what do you mean by X"; an answer of theirs reveals a wrong model of X; a decision was later
reversed because of a misunderstanding of X.

**Signals that permit brevity:** the user writes "brief answer", "in short", or asks a
yes/no question; the concept is Established. Under brevity, keep the guards that cost no words
(2, 5, 9) and the one-clause guards (1, 3, 4); drop the instance, the stake, and the parts
breakdown (6, 7, 8). A brief answer is a short *correct* answer, not a vague one.

---

## The nine guards

Numbered to match the failure modes the user named, so that "guard 3 was skipped" means the
same thing to both of you. Each has a trigger (when it applies), a rule, and an example drawn
from the bridge itself.

### Guard 1 — Fix the sense of an ambiguous term

**Trigger:** a load-bearing term has a second live meaning in this project's context.
**Rule:** use the term as you intend it and add, on first use in the message, *"in the sense
of …"* (or "here meaning …"). Once per message per term.
Terms in this bridge with more than one live sense — always sense-fix these when load-bearing:

| Term | Senses that collide |
|---|---|
| hook | a Cursor hook (runs when the builder edits a file or runs a shell command) / a git hook (runs on commit) |
| rule | a Cursor rule file (`.mdc`, instructions the builder reads) / a Semgrep rule (a pattern the scanner matches) / a standing rule of the supervisor |
| agent | a Claude subagent (a reviewer) / `cursor-agent` (the builder program) |
| gate | the CI gate (the required check on a pull request) / the merge gate (all four conditions) / a phase gate (your approval between phases) |
| scope | the files a brief allows the builder to touch / the permissions an API token carries |
| token | an API token (a credential) / a model token (a unit of text the model reads) |
| review | Review A (the Claude reviewer) / Review B (the cross-family verifier) / a human code review |
| build | compiling the software / the build plan / the whole delegated construction |
| test | an automated test the software runs / one of the manual verification tests (S10) |
| check | a CI check (a named job on the pull request) / an informal "have a look" |

Example. Wrong: "the hook blocks it." Right: "the shell-guard hook — a Cursor hook, in the
sense of a script Cursor runs just before the builder executes a shell command — blocks it."

### Guard 2 — One term, one thing

**Trigger:** always; it costs nothing.
**Rule:** for technical vocabulary, pick one term for a thing and use only that term for the
rest of the message, even if it reads monotonously. Never vary for style. If a tool's own name
for the thing differs from yours, say so once — "the brief (Cursor's docs call this a prompt)"
— then use yours only. If two terms genuinely name different things, say what differs the
first time both appear. Colloquial language is exempt; this is about technical terms.

Example. Wrong: "the brief … the task file … the handoff … the prompt" for one file. Right:
"the brief" four times.

### Guard 3 — Relations, not lists

**Trigger:** two or more technical things appear together.
**Rule:** state how they relate — produces / consumes / gates / contains / replaces / runs
before / is one kind of — in the same breath as the list. One sentence giving the shape is
usually enough ("A produces B; B is what C checks; if C fails, A runs again"). For three or
more parts with non-trivial relations, a two-column table (part → what it does *to the others*)
beats prose. Never leave the user to guess the arrangement.

Example. Wrong: "There is a diff-reviewer, a design-auditor, and a security-auditor." Right:
"The diff-reviewer reads every diff first; only if it approves do the design-auditor (for
diffs that touch the UI) and the security-auditor (for diffs that handle input or data) read
the same diff. Any one of the three can block."

### Guard 4 — No silent steps

**Trigger:** any load-bearing chain from action to consequence.
**Rule:** run the chain test: cause → mechanism → consequence, every arrow present. What is
obvious to an engineer is not obvious to the user, so the two steps most often dropped get
stated every time: **what happens if nothing is done** (the default), and **why the mechanism
produces the consequence** (not just that it does). If a step rests on knowledge the user
would not have, add the step or the knowledge — do not leave a gap they must fill by
speculation.

Example. Wrong: "Without the pin, an update could break the build." Right: "The scanner is
downloaded fresh each run. Without the pin, each run takes whatever version is newest that
day; a new version can change what it flags, so a build that passed yesterday can fail today
with no change on our side. The pin fixes the version, so only we decide when it changes."

### Guard 5 — Restate faithfully

**Trigger:** you say the same thing twice, in a summary, a recap, or a rephrasing.
**Rule:** a restatement means exactly what the original meant. If the second wording adds,
drops, or softens a qualifier, it is a different claim — either make it identical or mark it
as new information ("more precisely: …"). When in doubt, repeat the original phrase word for
word rather than paraphrase it. Never paraphrase a definition later in the message with drift.

Example. Wrong: first "the guard denies destructive commands", later "the guard blocks risky
commands" (denies ≠ blocks? destructive ≠ risky? the user cannot tell). Right: use "denies"
and "destructive commands" both times, or say "more precisely, it denies the listed
destructive patterns and allows everything else".

### Guard 6 — One concrete instance

**Trigger:** every concept given full treatment; every Risky concept.
**Rule:** give one instance, and prefer one from **this project** — the actual file, the actual
screen, the actual scenario — over an invented one. Use an analogy only when no project
instance exists yet; label it as an analogy and state in one clause where it stops holding.
One instance, not three.

Example. Right: "An invariant assertion is a check the software runs on itself while it is
running — for instance, on the checkout screen, 'the total shown equals the sum of the line
items'; if it ever does not, the software reports it instead of silently showing a wrong
total."

### Guard 7 — The practical stake

**Trigger:** every concept given full treatment.
**Rule:** one sentence on what it does for the product in use, or what goes wrong without it,
in the user's currency: behaviour, cost, risk, reversibility, time. This is what lets them
weigh it; a concept without a stake is a definition they cannot act on.

Example. Right: "Without the dependency-admission gate, the builder can pull in any package
it likes; a compromised package is the way attackers most often get into a small project, and
it is invisible in the finished software."

### Guard 8 — Parts before the whole

**Trigger:** the concept is an aggregate of ideas — most of them are.
**Rule:** ask "which words in my definition would the user already have to know?" Those are
the parts. Name each part first, in a clause, in dependency order (a part before the thing
that uses it), then the whole. Do not define an aggregate in terms the user has not met.

Example. "The merge gate" depends on: a pull request (a proposed change waiting for
approval), CI (a machine that runs the checks on every pull request), Review A and Review B
(two independent reviewers of different make), and a gate-integrity flag (a sign that a check
was tampered with). Only after these four does "the merge gate is all four holding at once"
mean anything.

### Guard 9 — No tangents

**Trigger:** always; it costs negative words.
**Rule:** if it is not on the load-bearing chain, it does not go in. Interesting-but-not-needed
either goes at the very end under one line — *"Not needed for this decision: …"* — or is
omitted. The user's working memory is the scarce resource; every tangent displaces a
load-bearing step.

---

## Priority when the budget is tight

Guards 2, 5, and 9 cost nothing — always on, even in a one-line answer. Guard 1 costs one
clause — apply it to every load-bearing ambiguous term. Guards 3 and 4 cost one sentence
each — apply them to every load-bearing chain. Guards 6, 7, and 8 cost the most — spend them
only on New concepts (and guard 6 on Risky ones). This ordering is what keeps answers from
becoming overblown while still landing.

---

## The decision brief — when a decision is put to the user

Use this shape for every escalation and every phase-gate presentation. It is the "lead with
the decision, recommend one, then wait" rule of `supervisor.md`, with the explanation slotted
where it belongs:

1. **The decision** — one sentence: what you are choosing between.
2. **Why it is yours** — one sentence: which user-owned factor it turns on (product
   behaviour, scope, a cost or exposure you bear, something only you can provide, an
   irreversible step, a change to what "correct" means).
3. **What you need to know** — the load-bearing concepts, at most three, each under guards
   1–8 by its class. Parts before whole; one instance; one stake.
4. **The options** — for each: what it means for the product in use; what it costs; what it
   forecloses or whether it can be reversed later. Same terms as in 3 (guard 2).
5. **Recommendation** — which one, and the reason in the user's currency.
6. **Decided regardless** — the technical choices you make either way, one line each, so
   the user sees the boundary of what they are deciding and does not reach past it.

Then stop and wait. Target length: 250–400 words. Longer only when the budget rule forced a
split and the user asked to see both halves.

## The explanation — when the user asks "what is X?"

Sense (guard 1) → parts (guard 8) → the whole → its relation to what the user already knows
(guard 3) → one instance (guard 6) → the stake (guard 7). Around 150–200 words unless the
user asked for more or less. End when the content ends; no summary paragraph that risks
drifting (guard 5).

---

## Self-check before sending

Six questions; if any answer is no, fix that guard before sending:

- Could the user decide from this without guessing a step? (4)
- Is any technical term used in two senses, or are two terms used for one thing? (1, 2)
- Does every group of things carry how they relate? (3)
- Does every restatement mean exactly the same as the first statement? (5)
- Does every fully explained concept have one instance and one stake? (6, 7, 8)
- Is anything here not on the chain to the decision? (9)

---

## When the user signals they did not understand

A clarifying question — "what do you mean by", "how does that relate to", "so is X the same as
Y?", or an answer that reveals a wrong model — is evidence, not noise. It means either a
load-bearing concept was classified Established when it was New or Risky, or a guard was
skipped. Do **not** re-send the same explanation at greater length. Identify which guard
failed (the question usually names it: "same as" → guard 2; "how does that relate" → guard 3;
"what is" → guard 8), fix that guard specifically, rebuilding from the parts up, and move the
concept to **Risky** in the record so the next brief re-anchors it.

## The record

Keep a **Terms fixed** list in `docs/PROJECT_STATUS.md` (the supervisor's "Project state"
section shows the slot): one line per term — the term, the sense fixed with the user, and its
class (Established / Risky). A fresh session reads it and classifies correctly without having
to guess what the user already knows. It is a lookup table, not a glossary; do not write
definitions into it.
