## Phase 1 — Intake

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

For **installable software** — a desktop application, a command-line tool, a local server
— the platform context includes the **delivery**: the project ends with one file the owner
double-clicks on Windows 11 x64 that installs it, upgrades it in place, and uninstalls it
cleanly, per `~/.claude/cursor-bridge/Delivery-Conventions.md` §1 (which kind ships what).
Confirm the kind and the target (Windows 11 x64 unless the user says otherwise), whether it
must be per-machine (a service, a driver, a machine-wide file association) or can be
per-user (the default, no administrator prompt), where its data should live, and — for
anything with a command-line surface — that a generated **command reference** will exist
(§4). This is not optional and not a late addition: it is a stage of the build plan.

**Performance and cost budgets** (`~/.claude/cursor-bridge/Performance-Conventions.md` §1).
Turn the stated performance, scale, and cost expectations into numbered budgets — one
operation, one condition, one number, one measurement: "a search over 10,000 documents
answers within 2 s at p95", "startup under 1 s", "syncing 1,000 files costs at most $0.50".
Propose the numbers from the platform and the expected data; the owner sets them (a
decision brief: what each number means for the user and what meeting it costs). "No
budgets" is a legitimate answer for software with no operation the owner cares about the
speed or cost of — it must be an answer, not a default. The budgets are recorded as prose
in `docs/DESIGN.md` and as `bench/budgets.json` at configuration.

For every **UI-bearing** feature, capture a **screen-and-state inventory** — the screens
it needs and, for each, the states that must exist: empty, sparse, dense, and error. This
is what makes the mockup (Phase 3) complete rather than a happy-path shell, and it is what
each screen's mockup is later mapped back onto.

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

**Gate:** summarise your understanding back to the user and get explicit
confirmation before moving on. Where the summary rests on a technical matter the user has
not met yet, explain it under the `explain-for-decision` skill — parts before the whole, one
instance, the practical stake — rather than assuming it is self-evident.
