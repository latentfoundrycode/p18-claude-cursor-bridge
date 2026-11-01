# Merge Verification Policy — Bridge

The rule that replaces a human reading the diff before merge. The owner is not a
software engineer and cannot judge code correctness, so **no code-correctness decision
is ever routed to the human.** Correctness is decided by an automated, decorrelated gate;
the human is asked only *intent* questions they are actually competent to answer.

Read this alongside the delegation loop (`~/.claude/cursor-bridge/workflow/phases/delegation-loop.md`) — this file defines the gate; the
supervisor applies it.

---

## The gate: all four must hold to merge

A branch merges to `main` only when every one of these is true. Any failure means
**do not merge** — route per §"What each outcome does" below.

1. **Executable floor — CI is green.** The required GitHub status check ran the real
   test suite and passed. This is the one part of the gate no model can talk its way
   past: tests either run and pass or they don't. On a paid plan (GitHub Pro for a personal account, Team for an organization) this check is
   *required* via branch protection, so a red or missing check blocks the merge at the
   repo level, not just by convention.

2. **Review A — the Claude reviewer approves.** The `diff-reviewer` subagent, pinned to
   a strong model and read-only, reviews the cumulative diff against the brief and the
   design. Anthropic-family judgment.

3. **Review B — a cross-family verifier approves.** A **non-Anthropic** frontier model
   reviews the same diff independently. This is the decorrelation that matters:
   duplicating the same model would only reduce variance, not blind spots — different
   model families fail on different things. Review B and Review A must both approve.

4. **Gate integrity holds.** The diff does not weaken the gate itself (see §Anti-gaming),
   and the **builder's model is a different family from both reviewers'**. If Cursor
   built with family X, neither reviewer may be family X — set `--model` explicitly on
   the build and on Review B so this is guaranteed, not incidental.

Three independent families (builder, Review A, Review B) plus an executable test floor.
That is the substitute for the human glance — stronger than it, because the human could
not actually evaluate the code and these three can, in decorrelated ways, on top of tests
that really run.

---

## Design in the gate (UI-bearing projects)

Design quality sits in the gate the same way code quality does — a deterministic floor plus
a judgement layer — not as a new human gate.

- **Executable floor.** Where the project has CI, the required `gate` check includes the
  deterministic `npx impeccable@<pinned> detect --json <ui paths>` step; **primary findings
  block**, tuned only via recorded `impeccable ignores`. This is a floor item exactly like
  the project's lint/type/test commands — a model cannot talk past it. Where the project has
  **no** CI, the supervisor runs that same command locally before merge.
- **Judgement layer.** The `design-auditor` subagent is a review input (read-only, returns
  only violations). A **blocking** design finding re-delegates and an **advisory** one is
  logged to `docs/CHANGES.md` — governed by the same two rules below, the re-delegation-by-class
  rule and the convergence rule, not a separate mechanism. Its blocking class (accessibility / keyboard / label MUSTs, missing
  required states) is a correctness class and behaves like any other REJECT.
- **No new human gate.** Design correctness never reaches the owner. Only a genuine *intent*
  question — how the UI should look or behave — does, and that routes through the
  approved-mockup rule in `~/.claude/cursor-bridge/workflow/phases/interface/mockups.md` (Phase 3), not through this policy.

---

## Security in the gate

Security is decorrelated the same way the merge gate is — a deterministic floor plus two
model families — and, like design, adds **no new human gate**.

- **Deterministic floor — model-independent.** Semgrep (SAST), OSV-Scanner (known-vuln +
  known-malicious dependencies), and Socket (behavioural malicious-package analysis) run as
  **steps inside the required `gate` job** (Semgrep on Linux; OSV-Scanner on the PR diff with
  explicit exit-code handling; `socket ci`). A high-severity/primary finding turns the single
  `gate` check red — one required check, so branch protection and the merge-watch are
  unchanged. In CI, Semgrep runs the **Pro engine** (`semgrep ci` + `SEMGREP_APP_TOKEN`, taint —
  the real SQL-injection catch) when the token is set, else the OSS packs + the bundled
  token-free bridge rules (a heuristic supplement, not taint). Where there is no CI, the
  supervisor runs the three locally before merge (token-free mode).
- **Review A judgement — Anthropic family.** The `security-auditor` subagent (read-only,
  strong model) catches the classes SAST misses — IDOR/BOLA, broken authN, business-logic
  and authz gaps. A **blocking** finding re-delegates like any REJECT; an **advisory** one is
  logged to `docs/HARDENING.md` / `docs/CHANGES.md`. The same two rules below, the
  re-delegation-by-class rule and the convergence rule.
- **Review B judgement — cross-family.** Review B already reads the whole cumulative diff;
  its mandate is **extended** to cover the same vuln classes and the security anti-gaming
  checks (below). No new model, no new invocation — a prompt extension (see Review B's
  invocation section).
- **Runtime pre-execution control (defense-in-depth).** The fail-closed shell-guard hook
  (`beforeShellExecution`) blocks the builder's destructive/irreversible/exfil shell commands
  *before they run*, under `--force`, where nothing else would. It is not part of the merge
  verdict — it is a live guardrail during the build — but weakening it is a gate-integrity
  flag (see §Anti-gaming).
- **No new human gate.** Security correctness never reaches the owner. Only *intent* — should
  the software do something different, is a slower/costlier-but-safer path wanted — and the
  pre-existing dependency/irreversibility questions do. A malicious dependency is rejected at
  the admission gate, not escalated.

---

## Observability in the gate (UI-bearing projects)

Extends the floor with the *running render* — a class the static detector and the
Vercel-rules-on-diff cannot see (see `Observability-Conventions.md`).

- **Deterministic floor — NEW coverage.** The supervisor-authored observability tests drive
  every Phase-1 inventory state through the **real render path** and assert no runtime invariant
  fired (no `undefined`/`NaN`/`[object Object]`/untranslated-key rendered), no `console.error`,
  and the required states exist. They run as a step **inside the required `gate` job** (on
  demand, no daemon; locally at the merge gate where there is no CI). A fired invariant, a
  `console.error`, or an unreachable inventory state **blocks** and re-delegates like any REJECT.
- **Judgement — existing, richer evidence.** Tier-B screenshots feed `design-auditor`'s existing
  mockup-fidelity pass — same verdict classes, better input. Not a pixel diff, not a new pass.
- **No new human gate.** Running-render correctness never reaches the owner.

---

## Model roster (this project)

Two **profiles**, tried in order; the first usable one fills the roles. Review A is
always Claude through Claude Code (it never touches Cursor usage).

| Profile | Builder | Review B | When |
|---|---|---|---|
| **full** (preferred) | `grok-4.7-high` (xAI; Cursor Models pool) | `gpt-5.6-sol-high` (OpenAI; Other Models pool) | while the owner's Cursor "Other Models" usage is available |
| **native** | `composer-2.5` (Cursor's own model; Cursor Models pool) | `grok-4.7-high` (xAI; Cursor Models pool) | when the Other Models pool is exhausted — the roles swap so the stronger native reasoner reviews and the plentiful native coder builds |

**Pool membership is taken from Cursor's Models & Pricing page, never from an id's shape.**
Read on 2026-09-25: *"The Cursor Models pool includes Grok 4.7, Grok 4.6, Grok 4.5, and
Composer 2.5"*; every third-party model (GPT, Gemini, Claude, GLM, Kimi, …) draws from
*"Other Models"* at its API rate; at the limit requests *stop* unless pay-as-you-go is
enabled — never a degraded mode; usage resets with the billing cycle. **At configuration,
check the ids against `cursor-agent --list-models` and the pools against that page**, and
pick the strongest model each pool offers at that time — this table records the picks of
2026-09-25, and a newer Grok or Composer supersedes them.

`docs/ROSTER.json`:

```json
{
  "other_pool": "available",
  "reset_day": 16,
  "review_a": "claude-opus-5-5",
  "profiles": [
    { "name": "full",   "builder": "grok-4.7-high", "review_b": "gpt-5.6-sol-high" },
    { "name": "native", "builder": "composer-2.5",  "review_b": "grok-4.7-high" }
  ]
}
```

`other_pool` flips to `exhausted` in two ways: **automatically**, when a call to a model
in that pool returns a usage-limit message or fails twice in a row
(`roster-check.py --record-failure`, the delegation loop's step 3b, `~/.claude/cursor-bridge/workflow/phases/delegation-loop.md` — the loop then re-resolves
and restarts the interrupted step without waiting for anyone), or **pre-emptively by the
owner** saying "usage exhausted" when the dashboard shows the pool nearly gone (a one-word
probe succeeds at 1% remaining exactly as at 90%, so a nearly-empty pool cannot be
detected, only a refused call). It returns to `available` **automatically**: `reset_day` is the
day of month (UTC) on which the owner's subscription has reset (the owner's resets on the
15th, so `16`); at the first checkpoint on or after 00:00 UTC of the first reset day after
the exhaustion stamp, `roster-check.py` restores the pool and clears the marks. The owner's
"usage reset" brings it earlier; a probe is never used for the return. `roster-check.py` then skips profiles that need the exhausted pool, probes the
candidates for hard failures (refusal, empty reply, timeout), verifies three distinct
families, and writes `docs/ROSTER.resolved.json`, which the delegate and Review B commands
read. Running on the native profile is a weaker cross-family verdict than GPT-5.6 Sol and
is reported as such; the decorrelation the gate depends on is intact under both profiles.

**The roster is a resolved file, not a table to remember.**
`python ~/.claude/cursor-bridge/roster-check.py docs/ROSTER.json --command "<delegate
command>"` resolves the profile as above and fails on a shared family, an unknown family
(add a `family` override), no usable profile, or a delegate command that does not set
`--model` to the resolved builder. It runs at
configuration, at every calibration, and at every checkpoint before a delegation — because
a project once ran its builder on Review B's family for several increments before anyone
noticed (KP-022).

**The invariant, not just the current picks:** Review B must be a family that is *neither
the builder's nor Review A's*. Under the full profile the builder is Grok (xAI), so Review B must **never**
be a Grok model (4.5, 4.6 and 4.7 are one family — a different version is not
decorrelation) and never a Claude model; GPT-5.6 Sol satisfies this. Under the native profile the builder is Composer (Cursor) and Review B is Grok 4.7 (xAI), which satisfies it the other way round. If the builder's
model is ever changed, re-check this invariant before the next run — a verifier that
shares the builder's family is no verifier at all.

---

## Anti-gaming: protect the gate from being passed dishonestly

The failure mode of "make CI green, then auto-merge" is an agent turning the check green
by **weakening what the check checks.** Both reviewers must explicitly look for, and
must never silently approve, any of:

- deleting, skipping, or commenting out tests or assertions;
- loosening an assertion (widening a tolerance, changing `==` to a range, asserting a
  weaker property) without a stated, intended reason;
- adding blanket retries, `sleep`s, or `try/except pass` that mask a failure;
- narrowing test scope or excluding files so a failure stops being exercised;
- editing the CI workflow to skip, `continue-on-error`, or drop the failing job;
- using `git commit --no-verify` on an increment/accept commit to bypass the pre-commit lint
  gate (only the supervisor's pre-delegation checkpoint snapshots, and a parallel builder's hand-off snapshot in its worktree, may use `--no-verify`; the accept commit on top of either runs the hook);
- **treating the builder's `Assumed, not verified` list as the review's scope.** The list is where the builder knows it guessed; reviewers check each item *and* review everything else. A list reading `none` on a diff that relies on an unverified external fact, or one that omits an assumption the code plainly depends on, is a finding (`REJECT` for an external-service fact, KP-020). "I listed it" never excuses a defect;
- **compressing, truncating, slicing, or summarizing a gate-critical stream before a
  reviewer reads it** — the diff, scanner output, test results, or the file Review B reads.
  These reach the reviewer **whole**: a reviewer that saw a trimmed diff can emit an
  APPROVE-shaped reply on something it never examined (this has happened with a missing
  diff). Context economy (see `supervisor.md`) applies only to high-volume, low-stakes
  material that no verdict rests on.

**Security-control tampering** is a gate-integrity flag on the same footing — both reviewers
must treat any of these as such:

- adding a `nosemgrep` / inline suppression, an `osv-scanner.toml` `[[IgnoredVulns]]`, or a
  `@SocketSecurity ignore` to silence a **real** finding rather than a justified, expiring
  false positive;
- removing or weakening input validation, an authz check, output encoding, or a crypto choice;
- editing the CI `gate` job to skip, `continue-on-error`, or drop a security step;
- downgrading the ASVS level or narrowing the rule globs to dodge coverage;
- unpinning a security tool or CI action from its SHA to a mutable tag;
- weakening the shell guard — removing its `beforeShellExecution` entry, dropping
  `failClosed: true`, or deleting/loosening entries in `shell-guard.py`'s deny-list to get a
  blocked command through (extending the deny-list is fine; gutting it is not);
- weakening observability — disabling a runtime invariant assertion or the
  `console.error`-fails rule, or narrowing the reachability set so a state stops being
  exercised, to get a UI increment through (adding invariants/states is fine; removing them to
  dodge a failure is not).

**Refactoring-diff tampering** is a gate-integrity flag on the same footing. A stage's
refactoring branch claims "same functionality", and the deterministic `refactor-check.py`
already fails it on any test-file change, any `docs/CHANGES.md` change, or a diff beyond the
size budget. Both reviewers must additionally treat as a flag:

- a behaviour change carried inside a refactoring diff — a changed error message, default,
  edge case, or public signature — however small, and however much of an improvement (it
  belongs in a feature increment with its own `CHANGES.md` entry);
- a test file edited beyond the mechanical rename the brief explicitly listed;
- a "simplification" that removes a required security, observability, or accessibility
  control because it looked repetitive.

Review B's mandate on a refactoring diff is the explicit question **"is this
behaviour-preserving?"**, answered on the whole diff.

**Performance-floor tampering** is a gate-integrity flag on the same footing
(`Performance-Conventions.md` §4). Both reviewers must treat as a flag: raising a `max`,
lowering a `min`, or widening a `tolerance_pct` in `bench/budgets.json` without an owner
decision recorded in `CHANGES.md`; a `bench/baseline.json` change in a commit that is not
an optimization with its before/after numbers in the message; a benchmark deleted, skipped,
or its fixed dataset or seed changed so a number passes; a warm-cache measurement where the
budget stated a cold one. A budget passes by the software getting faster, never by the
budget getting looser; relaxing one is a product decision that goes through the change
cycle's intake.

**Fix-diff tampering** is a gate-integrity flag on the same footing. A fix brief — spec-packager's
fix variant, known by its Objective, which opens "Fix the following confirmed defect" and
states the confirmed cause with its evidence, whatever its name: `handoff/<ID>-r<N>.md`
inside an increment's gate, `handoff/BUG-<nnn>.md` for a defect found after a merge — names a
confirmed root cause and its evidence (the `root-cause-first` procedure).
Both reviewers must treat as a flag:

- **symptom suppression** where the brief named a cause elsewhere — a retry, a broad
  `try/except`, a widened tolerance, an added `sleep`, a null-check that hides a wrong value;
- the reproduction test edited so it passes, rather than the cause repaired;
- instrumentation residue — any `DEBUG-BUG-` tag, stray print, or changed log level
  (`secret-sentinel` blocks these deterministically);
- a fix made anyway after the builder reported it believes the cause is different.

Review B's question on a fix diff is **"does this repair the named cause at the named
mechanism, or does it make the symptom disappear?"**

Any of these is a **gate-integrity flag**. It is never an auto-approve. It is either a
`REJECT` (if the change is plainly a workaround) or an `ESCALATE-INTENT` (if it might be
a legitimate change to what "correct" or "secure enough" means — see below), never a quiet
pass.

---

## Verdict contract

Each reviewer returns exactly one of:

- **APPROVE** — implements the brief, sound, no gate-integrity flags.
- **REJECT** — with specific reasons. Sends the increment back into the delegation loop
  for a corrected re-delegation; it does **not** go to the human. A code defect is the
  loop's problem to fix, not the owner's to adjudicate.
- **ESCALATE-INTENT** — with a single, plain-language *intent* question. Only for the
  categories in §"What the human decides." Never for "is this code correct."

Merge is authorised iff: **CI green AND Review A = APPROVE AND Review B = APPROVE AND no
open gate-integrity flag.** Anything else does not merge. A reply from either reviewer that
carries none of the three verdicts is a failed launch, never a verdict of any kind: the
supervisor re-runs it once and then takes the roster's failure path (release A5).

**CI green means the run of the pushed head.** A watch started right after a push can
report the previous commit's finished run; before the merge the supervisor confirms that
the green run's head equals the pushed head (`gh pr view <n> --json statusCheckRollup,headRefOid`),
which `premerge` checks for the pull request's head as well (the TDP's TASK-117-r2, KP-051).

**A vulnerability newly published in a pinned library nobody touched** fails every pull
request of the project at once, since the scanner reads the lock. The procedure (the TDP's
DEP-001 and DEP-002, release A5): a separate supervisor increment `DEP-<nnn>` off `main`
bumps the lock's pin (and the manifest's floor where the fix needs it), writes the
`CHANGES.md` entry, runs the sentinel, Review A and Review B and CI like any increment, and
merges first; then `main` is merged into each blocked branch, whose checks go green without
a change of their own. Nothing in a blocked branch is edited to pass; no finding is ignored
or suppressed (§Anti-gaming).

**Re-delegation runs while the code converges, and converges by defect class rather than a
round count.** Several REJECTs are not a stop. If each round surfaces *new, legitimate*
concerns that then get fixed — a thorough cross-family Review B catching real edges Review A
approved past is the system working, not failing — keep re-delegating. **A round count is
never itself a reason to stop or to involve the human.** Once the increment's core behaviour
is implemented and verified, and the findings that keep arriving are all the long tail of one
genuinely hard subsystem (subprocess teardown, retry/timeout races, kill paths, concurrency
edges), the supervisor draws a **by-class line**: it records each such finding to
`docs/HARDENING.md` and merges, rather than re-delegating the tail indefinitely. A late
finding blocks the merge only if it is of one of the five **blocking classes** — behaviour
against the brief or the register, security, data integrity, a defeated safety mechanism the
increment relies on (a bug in the very timeout or kill path built to protect the run is core,
not tail), a failing test. What a defect of the five is for the project is bounded by its threat model, recorded in `docs/INVENTORY.md` (Decisions) with its reason and what would reopen it and given to the reviewers with the diff: a finding outside it is recorded, not blocking, whatever its label and however many reviewers name it. Within it, a finding is a member of a blocking class when it reproduces as a regression or a false result on an ordinary, realistic project layout, a reviewer's label alone never deciding: one that needs a contrived setup goes to `docs/HARDENING.md` with the increment, and a security finding is judged instead by whether untrusted input can reach it (files a builder or reviewer writes, a cloned or third-party repository), never by the layout's ordinariness. Two reviewers naming the same late finding make it certain, never blocking of itself: it blocks only where its content is of the five ("Convergence is a signal", below). The class is the defect, not the operator that exposed it: a
further mutant, input or operator family that shows a class already recorded in
`docs/HARDENING.md` under the by-class line for the increment or the stage is that class and
never a new one, while a defect of one of the five blocks whatever was recorded before.
**The ceiling** (R-042): three rounds per increment and per stage review, the owner's number,
held by `bridge-run.py`, which counts the builder rounds, and `review-guard.py`, which counts
the Review B rounds; the count is the guard's (`~/.claude/cursor-bridge/workflow/phases/delegation-loop/decide.md`,
step 7, "The review ceiling"). Below it the by-class line is the supervisor's judgment; at and above it
the line is the rule: only a finding of the five sends the work back, every other finding goes
to `docs/HARDENING.md` with the increment, and a round above the ceiling runs only under a
`Blocking class:` line or the owner's `Review rounds above the ceiling:` line. Every reviewer
and auditor grades each finding of a round at or above the ceiling by the five first and confirms
or denies the round's `Blocking class:` line where it has one, against the code of the round it lifted, never against the fixed code under review; a denial is a breach, which voids the round's result and
withholds the merge as GATE-INTEGRITY does, recorded in `docs/HARDENING.md` and as an issue. Stop entirely only on genuine non-convergence: the **same** defect unfixed twice, or a
fix that **regresses** something already passing. A deadlock over what the software should
**do** is the one thing that reaches the human, as an intent question.

**Convergence is a signal.** When two or more reviewers or auditors independently name the same defect, it is certain even if each alone marked it advisory — decorrelated reviewers agreeing is the strongest evidence this gate produces (three of four converged on a lock-leaking lifecycle bug that each had called advisory); two findings on one line are one defect only where they name the same fault in it. The rule is the code gate's: a design critique's two critics are bounded by rounds instead (§"Review B's design mode", below), and a finding both name keeps the grade its content earns. The rule grades a finding's certainty, never its class. Two reviewers independently naming the same defect make it blocking where its content is of one of the five blocking classes, at any round; a convergent finding of another class is fixed by the next increment that edits its file, or recorded in `docs/HARDENING.md`, marked convergent, with no gate pass of its own. A class already recorded under the by-class line for that increment or that stage stays that class: two reviewers naming a further mutant, input or operator family of it name that class, which stays recorded and starts no round, and no class of the five is ever on that line. A finding outside the project's threat model (`docs/INVENTORY.md`, Decisions) is recorded, not blocking, however many reviewers name it.

**Split verdicts are resolved by the supervisor, not escalated.** First **name the
disagreement out loud** — `REVIEWERS DISAGREE on <crux>`, which reviewers, and whether the
crux is correctness or intent — so the split is on the record rather than dissolving into
"mostly approved"; that flag is where the supervisor's judgement adds the most. When one reviewer blocks
and the other approves, decide on the merits, biasing toward the project's **established
invariants** — a rule the codebase already enforces elsewhere. A blocking concern that
aligns with an existing project standard (e.g. a path-confinement check another increment
already added) gets fixed and the loop continues; the call is recorded in `docs/CHANGES.md`.
A split escalates to the human **only** when it turns on intent — what the software should
do — never on which reviewer is technically "more right." When the merits are *not*
clear-cut — the two disagree on a substantive correctness question, neither side plainly
aligns with an established invariant, or the call is entrenchable enough that getting it
wrong is expensive to undo — the supervisor does not adjudicate alone and does not hand it
up. It convenes a resolution round.

### Resolution round

The resolution round fires on **either** trigger:

- a **contested split** — Review A and Review B disagree on a diff and the merits aren't
  clear-cut (per the paragraph above); or
- a **hard technical or design question** the supervisor faces during planning or building
  that the escalation self-test assigns to the system (it turns on knowing the software) but
  which the supervisor is *genuinely uncertain* about — the answer isn't clear on the merits,
  no established invariant settles it, and getting it wrong would be expensive. This is the
  case that would otherwise leak to the human as a technical question. It must not; convene
  the round instead. Uncertainty on a system-owned question is the trigger to convene the
  council you already have — never a default reason to reach for the user.

The purpose is the same for both: keep a hard call *inside* the decorrelated gate — decided
on a fuller, adversarial record — rather than resting it on one adjudicator's line of
reasoning or pushing it to a human who cannot judge it. It reuses the two reviewers already in
the loop; it is not a new set of models, and it is not a per-question "council" spun up fresh
(the property you want is already latent in the two-family gate — you are only adding a step
that makes the reviewers argue rather than vote blind).

1. **State the question on disk.** The supervisor writes a short file to a committed path
   (e.g. `handoff/RESOLUTION-<id>.md`): the specific question, the candidate answers, each
   reviewer's position if they already hold one (a split) or the competing options and their
   trade-offs (a standalone question), and the material the question turns on — the diff, or
   the design/spec section and code paths at issue. As with Review B, the reviewers **read
   from this file** — nothing load-bearing is passed inline through the shell.
2. **Each reviewer answers the other.** Invoke Review A and Review B once more, each told to
   read the file, engage the *other's* argument directly (not merely restate its own), and
   return a **reasoned vote** for one candidate answer with its decisive reason. Review A is the
   `diff-reviewer` subagent, given the file's path; Review B is launched exactly as in the
   merge step (`review-guard.py snapshot`, the launcher with `--force` in the background,
   `review-guard.py verify` printing `OK` afterwards) with a directive prompt ("the material
   is at `<path>`; read it; do not ask for it"). Both get a **receipt check** — a reply that
   does not name something specific from the file is a failed launch, not a vote; re-run it.
3. **The supervisor decides on the record.** With both reasoned votes in hand it makes the
   call, still biasing to established invariants, and records the decision *and the reasoning
   that settled it* in `docs/CHANGES.md`.
4. **Escalate only if the crux is intent.** If the debate reveals the disagreement is really
   about what the software should *do* — not which implementation is correct — that, and only
   that, goes to the human as a plain intent question. Correctness never does. A genuine tie
   that no invariant breaks is itself a hint the choice may be intent rather than correctness.

Keep it bounded: one resolution round per question. Its output is a decision, not a new
negotiation to reopen. If it surfaces a genuinely *new* substantive defect, that re-enters the
ordinary re-delegation loop as a fresh finding.

---

## Review B's design mode (release A3)

Before the design gate, and again for a plan, a change cycle's design revision and a scoped revision, the cross-family reviewer reads the design as one of two critics (`~/.claude/cursor-bridge/workflow/phases/design.md`, Phase 2). The supervisor commits the design text, the diagrams, the requirements register, `docs/DESIGN_CRITIQUE.md` (the accepted list and the earlier grades, so that the reviewer does not raise what is settled) and the critic's lenses (copied from `plan-critic`'s sections, so the reviewer needs nothing outside the Workspace) to `run/review/DESIGN-<subject>-<round>.md` (`<subject>`: `design`, `plan`, the change's name, or `<the change's name>-plan`) with `git add -f`, snapshots with `review-guard.py snapshot DESIGN-<subject>-<round>`, and launches the reviewer **read-only, with the workspace trusted**, through the launcher:

```bash
python ~/.claude/cursor-bridge/bridge-run.py --limit auto --kind review -- cursor-agent -p --mode=ask --trust --model <review_b from docs/ROSTER.resolved.json> "The text to criticise is already written to run/review/DESIGN-<subject>-<round>.md, with the lenses, the grades to answer in, and the record of what was accepted so far. Read that file whole; do not ask for it; the findings it lists as accepted are settled, do not raise them again; answer with your findings in its grades, each naming the diagram, section or requirement it concerns, then the counts per grade, and nothing else; where you find nothing, name instead three statements of the file you verified, each with a short quotation from it. Write no file under the checkout, point no cache there, and edit nothing." 2> run/review/REVIEW-DESIGN-<subject>-<round>.err
```

It answers in the critic's grades, Blocking, Should fix and Consider, each finding naming the diagram, section or requirement it concerns, and ends with the counts per grade. A reply that names nothing from the file is a failed launch, not a verdict, as for a code review. `review-guard.py verify DESIGN-<subject>-<round>` afterwards proves the reviewer read only. The record of every round lives in `docs/DESIGN_CRITIQUE.md`, each critic's grades apart; a design resolution round runs the same read-only command on `run/review/DESIGN-<subject>-R1.md` (`R2` under the owner's line) holding every open question and both positions on each, never the code review's `--force` form. The `run/review/DESIGN-*` files are removed with `git rm` in the commit that passes the gate. The installed test that forbids the read-only mode in a reviewer command applies to code reviews, which must execute; a design review must carry `--mode=ask --trust`.

**The loop is bounded** (`~/.claude/cursor-bridge/workflow/phases/design.md`, Phase 2): at most four rounds per subject, a non-convergent finding starting none; then, if the text changed after a critic last read it, one confirming read by both, whose file opens by saying so and holds the diff since each critic's last read, labelled by critic, and which no critique round follows; then one resolution round, `DESIGN-<subject>-R1.md`, holding every question still Blocking or non-convergent, whose file opens with *answer every open question in this file; raise no new finding; your reply answers each question in place of findings, with no counts*, which takes the place of the launch command's request for findings, grades and counts, and whose Review B reply the supervisor writes to `run/review/REVIEW-DESIGN-<subject>-R<n>.md` for `plan-critic`; then the gate, whatever is still open. A subject is one token of lower-case letters, digits and hyphens, distinct from every other subject. A failed launch follows the delegation loop's step 3b (`~/.claude/cursor-bridge/workflow/phases/delegation-loop.md`), every one recorded: the first (exit 4) runs once more on the same file, the second (exit 3) marks the model and runs once on the re-resolved profile; then the design waits for the roster or the owner's word, and the file runs once more under its number with no re-runs; if that fails too, Review B's row stays `not run (<the reason>)` and the subject goes on to its resolution round or its gate. `bridge-run.py` refuses, with exit 125 and a message beginning `bridge-run: refused - design ceiling: `, a `cursor-agent` launch naming, anywhere and with either separator, a `run/review/DESIGN-<name>.md` whose round (the name's last hyphen-separated part: a positive integer without a leading zero, or `R` and one; 1 to 5 and `R1` allowed) is above five, is `R2` or later, or cannot be read, a name holding anything but lower-case letters, digits, hyphens and the round's `R` being one that cannot. A line `Design rounds above five: <subject> <rounds> (<their words>, <date>)` in `docs/RUN_PARAMETERS.md`, written only on the owner's own words, allows that subject rounds up to `<rounds>` and `R2`, and nothing beyond: the same shape once more, critique rounds up to `<rounds>` minus one, a confirming read at `<rounds>` at the most, then the next resolution round if anything is open. `<rounds>` is a round number: the last numbered round run, a resolution round not counted, plus the more rounds the owner names, or five more when they name none, never below six; a subject is lifted once, its first well-formed line standing and a later one ignored. A refusal is neither a failed review nor a model's failure. The convergence rule of the code gate does not apply to a design critique.

## Who completes the merge — the `Merge authority` run parameter

The gate decides *whether* a branch may merge; the owner's `Merge authority` run parameter
(`docs/RUN_PARAMETERS.md`, set once after the plan is approved) decides *who* completes it.
Under `supervisor` (the default) the supervisor arms and completes the merge as described
below. Under `owner` the supervisor does everything up to the merge and then stops with
**READY TO MERGE** — the PR link, the four conditions with their evidence, and a one-line
run sheet — and never arms auto-merge. The parameter changes the last step only: the four
conditions, the anti-gaming checks, and the resolution round are identical under both.

## Enforcement at merge — how GitHub auto-merge composes with this gate

GitHub's auto-merge only knows about **GitHub checks** — i.e. CI. It cannot see Review A
or Review B, which are model verdicts the supervisor computes locally. So GitHub
auto-merge, left to itself, would merge the moment CI is green — *before and regardless of*
the model reviews. Using it raw would silently defeat this policy.

The composition that keeps the gate intact:

1. The supervisor opens the PR and runs Review A and Review B on the PR's diff.
2. **Only if both APPROVE and no gate-integrity flag is open** does the supervisor arm the
   merge — `gh pr merge <n> --squash --auto --match-head-commit <sha>`, the sha that `review-guard.py premerge` printed — and then watch the required `gate` check with **one background command** (`gh pr checks <n> --watch --required --fail-fast`, run in the background). Its completion is what wakes the supervisor; the desktop app's CI monitor reports failures and review comments only, never a green gate, so it cannot be the wake-up (KP-028).
3. The merge lands only when the required CI check is green — which, thanks to branch
   protection on the Team plan, is a *required* check, so a red or missing CI run blocks
   the merge at the repo level as a hard backstop.

**Completing the merge — do not depend on GitHub's auto-merge queue.** GitHub's auto-merge
queue frequently lags by minutes after the check goes green; that is a known GitHub-side
delay with no reliable fix. Do not sit polling it. Once the merge is **authorised** — both
reviews APPROVE, no gate-integrity flag, the required `gate` check green, and the PR
mergeable/`CLEAN` — the supervisor may **complete the squash directly** (`gh pr merge <n>
--squash --match-head-commit <sha>`). This is safe and equivalent to the queue landing it: branch protection enforces
the required check regardless of *who* triggers the merge, so a direct `gh pr merge` cannot
bypass CI any more than auto-merge can. The armed `--auto` form (with the same `--match-head-commit`) is still set first,
as a **safety net** in case the session ends before the check is green; it is not the
mechanism to wait on. Never complete a merge before the required check is green or before
both reviews have APPROVED — the direct path is a convenience over the queue, never a
shortcut around the gate.

So the model reviews gate the *authorisation*; the required CI check gates the *merge*; and
branch protection guarantees CI can't be skipped whether the queue or the supervisor lands
it. All four conditions are enforced, and the merge still lands hands-off.

**Do not use the CI status bar's blanket Auto-merge toggle.** That toggle enables
auto-merge on PRs up front, on CI alone, which bypasses Reviews A and B. Let the
supervisor enable auto-merge per-PR *after* the reviews instead. (The same caveat applies
to Auto-fix: it can push CI-passing changes on its own, so keep the gate-integrity checks
in force so it can't go green by weakening a test.)

---

## What the human decides (intent only)

Escalate to the owner only for questions answerable without reading code:

- **Product behaviour** — should the software do something different from what was agreed?
- **Scope** — this diverges from `DESIGN.md`/`BUILD_PLAN.md`; is the new direction wanted?
- **Dependencies** — only a consequence the owner bears (money, privacy, lock-in), under the one dependency rule (supervisor rule 56); never the technical merit, never a licence.
- **Cost / effort** — a materially more expensive or slower path; is it worth it?
- **Irreversibility** — anything the revert net does *not* cover: a deploy, a data
  migration, a secret, a history rewrite, an action outside the repo. These get a human
  yes/no *before* they happen.
- **Changed meaning of "correct"** — a test's *semantics* are being changed (not just
  code passing them): "this loosens the timing assertion from 5s to 30s — did we intend
  to accept a slower stop?" That is an intent question, and answerable, even by a
  non-coder, because it is about desired behaviour.

Never escalate: "is this implementation sound / safe / idiomatic / correct." That is the
gate's job. Routing it to the owner is theatre — it looks like oversight and catches
nothing, because the owner cannot evaluate it.

---

## Why merges are not a catastrophe (and where that stops)

A bad merge is reversible: `git revert`/`reset` steps back to a known-good commit, so the
gate optimises for catching the *un-revertible* hard (that is why irreversibility is a
human gate above) and treats an ordinary behavioural miss as a retrospective fix. The one
residual risk is **detection** — a bad merge nobody notices never gets reverted — which is
why the supervisor keeps a plain-language change log the owner can skim after the fact and
say "that behaviour is wrong, roll it back." Revert covers in-repo damage that is noticed;
it does not un-leak a secret or un-run a deploy, hence those stay pre-merge human gates.

---

## Invocation

**Review A (Claude, Anthropic family).** Its verdict is the `diff-reviewer`'s own, in this policy's words: `APPROVE`, `REJECT` or `ESCALATE-INTENT`. The auditors that read the same diff (`security-auditor`, `design-auditor`) report PASS or FAIL as inputs to it, and an auditor's FAIL on a blocking class is a `REJECT`. The `diff-reviewer` subagent with a strong model
pinned in its frontmatter (`model: opus` or a full strong model ID) and read-only tools.
Already part of the loop; this policy only pins its model and adds the anti-gaming checks
to its mandate.

**Review B (cross-family).** Reach a non-Anthropic frontier model with execution, on a committed checkpoint restored afterwards. Its mandate
covers code correctness/soundness, the gate-integrity checks, **and security** — the same
exploitable-vulnerability and authz/authn/data-integrity classes the `security-auditor`
hunts, plus the security anti-gaming checks in §Anti-gaming. This is a **prompt extension**,
not a new model or invocation: the directive prompt tells it to check those classes too.
Two options for reaching it:

- *Default — via Cursor's CLI (no new secret, no script):* write the verification brief and
  the diff to a committed file **inside the workspace** (`run/review/REVIEW-<ID>-r<N>.diff`, named as the round's snapshot,
  committed on the increment's branch, `git rm`-ed before the merge — never a temp path
  outside `Workspace/`, which the boundary blocks), **generated only from committed state**
  (`git status --porcelain` empty, then `git diff <merge-base>...HEAD`; a working-tree diff
  omits every untracked new file, and a reviewer that receives an incomplete diff has
  correctly refused it twice), then invoke Review B **through the launcher, with execution**:
  `python ~/.claude/cursor-bridge/bridge-run.py --limit auto --kind review -- cursor-agent -p --force --model <Review B from docs/ROSTER.resolved.json> "<prompt>" 2> run/review/REVIEW-<ID>-r<N>.err`
  (`--force` lets it run the project's tests, write throwaway reproductions, and try a
  temporary mutation to see whether the tests catch it — the reviewer's strongest findings
  in the record came from exactly that, and the owner decided on 2026-10-04 to keep it
  after a read-only mode was tried and found weaker; the launcher withholds the owner's
  GitHub identity from the process, so a post, push or merge from inside the review fails,
  and ends the run at the limit, KP-032 and KP-033) with
  a prompt that tells it to **read the diff from that file** — do **not** pass the diff
  inline through the shell — and that names `run/review/SCOPE-<ID>.md`, committed beside
  the diff before the snapshot, where the supervisor wrote the brief's Scope and Out of scope, the project's threat model from `docs/INVENTORY.md`'s Decisions, the tests it wrote
  first with the paragraph each enforces, and the bookkeeping files in the diff that are
  expected (`docs/BUILDER_NOTES.md`, the builder's report file under `handoff/`); the prompt itself says only that design for later increments is not this diff's
  defect, that a claim about a build is verified by building it, that the reviewer writes no file under the checkout and points no cache there, its scratch files and test caches going to the system temporary folder, and edits nothing, that at a round at or above the
  ceiling every finding is graded by the five blocking classes first and the SCOPE file's
  `Blocking class:` line, where it has one, confirmed or denied against the code of the round it lifted, never against the fixed code under review, and that the reply is one of
  the three verdicts (release A5; `~/.claude/cursor-bridge/workflow/phases/delegation-loop/merge.md`, step 8, has the clauses). (Inline heredocs mangle or drop the diff; a reviewer that got no
  diff can still reply with something APPROVE-shaped, silently bypassing the gate. This is a
  real failure that has happened — the file path avoids it.) Confirm from its reply that it
  actually saw the diff before trusting the verdict. It also reads `run/review/ASSUMPTIONS-<ID>-r<N>.md` — the branch's builder assumption lists with their dispositions (`~/.claude/cursor-bridge/workflow/phases/delegation-loop/merge.md`, step 8) — as extra places to look, never as its scope. Per the roster above, Review B is
  **GPT-5.6 Sol** while the builder is Grok 4.7 (full profile), or **Grok 4.7** while the builder is Composer 2.5 (native profile) — a genuine third family either way; the ids in use are always the ones in `docs/ROSTER.resolved.json`.
  (`cursor-agent --list-models` shows what your plan offers; the invariant is Review B ≠
  builder family and ≠ Anthropic.) Instruct it to output only a verdict and to modify
  nothing that reaches the branch: run it on a clean committed checkpoint, **commit your
  own work first and write nothing to the checkout while it runs** (no builder, no
  `test-runner`, no commit; the launch is in the background and its completion wakes you).
  The checkpoint is guarded by `review-guard.py`: `snapshot <ID>-r<N>` before the launch, `<N>`
  the round it opens by the guard's count, the SCOPE file committed first since the guard reads
  its `Blocking class:` line (it refuses a dirty tree, a round off its count and a round above
  the ceiling with no lift, and records HEAD, the branch, the refs, the stashes, `.git/config`,
  the hooks folder and the ignored entries), `verify <ID>-r<N>` after the run, and
  `premerge <ID>-r<N>` before `gh pr merge`; since release A1b `verify` writes a verified mark when it prints OK (the snapshot's hash, the launch time and the exit code of the Review B run from `run/review/REVIEW-<ID>-r<N>.err`; `snapshot` and `verify` remove an older mark first), `premerge` refuses a snapshot without that mark, with a mark of another snapshot, with a launch before the snapshot or with an exit other than 0, and then writes a record of the head it approved (`<git common dir>/bridge/premerge/<sha>`), and the `permission-guard` hook refuses a `gh pr merge` whose `--match-head-commit <sha>` has no such record, so a merge that skipped the cross-family review or the pre-merge check is refused by the computer, not only by the rule (the sha alone proves nothing; the mark and the record do). A pull request that changes only records takes the same round. **What the restore covers and what it does not:**
  `verify` puts tracked and untracked files back with `git reset --hard` and `git clean -fd`
  (keeping the launcher's own `run/review/REVIEW-<ID>-r<N>.err`, whose first line it prints) and
  lists what it removed — a temporary file or mutation the reviewer made for a check is
  expected. A commit, a moved HEAD or branch, a new or moved local ref or stash, a changed
  `.git/config` or hook file, a changed record under `docs/`, `handoff/` or `run/review/`
  even where the project gitignores it, or a changed `.env` is **reported as
  `GATE-INTEGRITY`**: the tree and the refs are put back, the flag opens, the merge waits.
  The configuration, the active hooks folder (`core.hooksPath`) and `.git/hooks` are read as
  files before any git command runs, because a `core.fsmonitor` line or a planted hook
  would run the reviewer's program with the owner's identity on the supervisor's next git
  command — and every git command the guard runs has the repository's hooks and file
  monitor switched off, so the guard itself never runs one. A moved remote-tracking ref (a
  fetch) is only a note. The guard prints the snapshot file's hash at both ends, because a
  reviewer could rewrite the snapshot. It does not see the contents of cache folders,
  anything outside the checkout (the owner's profile, the installed bridge, other projects),
  or a reviewer that reaches for the credential store on purpose: it is a guard against
  what a reviewer does in passing, not a sandbox (KP-032). `premerge <ID>-r<N> <pr>`, run after
  the review files are removed, committed and pushed, then proves the head about to merge
  descends from the reviewed head, differs from it only by that removal, and is the pull
  request's head on GitHub; the merge uses `--match-head-commit` with that head. **Then check it wrote nowhere else:**
  `python ~/.claude/cursor-bridge/pr-activity-check.py <n> --since <the launch time>`, where
  the launch time is the launcher's first stderr line (`bridge-run: started <time>Z`, the
  first line of the `.err` file; a time without a zone is refused). It lists every comment
  and review on the pull request since the launch and flags any written as the owner (the
  reviewer once posted its verdict on a pull request under the owner's name, twice:
  KP-032), and it flags what the owner's account did elsewhere in the repository meanwhile
  that an agent would cause: a comment or review on another pull request, a merge, a push
  to `main`. `GATE-INTEGRITY` means do not merge; record the flag and an issue (a merge of
  *another* pull request by the supervisor itself while the review ran is legitimate and is
  simply recorded). `CANNOT VERIFY` is not clean: fix the cause and re-run before the
  merge. The check sees the likely cases, not every edit; the identity withheld from the
  agents is what stops the rest.

  **Two launch failures that have actually happened — prevent both, don't just catch them:**

  1. **Workspace-trust gate.** In a folder Cursor has not trusted yet (a fresh clone or
     worktree) `cursor-agent` refuses to run
     non-interactively until the folder is trusted, so Review B silently doesn't launch.
     Invoke Review B with `--force` (which also clears that gate), through the launcher.
     What keeps a reviewer with execution from doing harm: its identity is withheld (it
     cannot post, push or merge as the owner), it runs on a committed checkpoint that is
     restored afterwards (nothing it writes reaches the branch), the launcher's limit ends
     a hung reproduction, and the pull-request activity check runs before the merge.
  2. **Prompt-as-preamble.** Review B has replied "please provide the diff" instead of
     reading the file, treating the instructions as chatter. Use a **directive** prompt that
     removes all ambiguity: state that the diff is *already written to `<path>`*, that it must
     read that file, and that it must not ask for the diff — then a bare verdict.

  **A reply that does not demonstrably reference the diff's actual contents is a failed
  launch, not a verdict.** Require Review B to name something specific from the diff (a
  changed symbol, file, or line) in its reply; if it doesn't — or it asks for the diff, or it
  errors on trust — treat it as no-review and re-run. Never let an APPROVE-shaped reply from a
  reviewer that never saw the diff pass the gate.
- *Maximum independence — a direct provider API or MCP server:* a separate vendor entirely,
  truly read-only (send diff, get a JSON verdict). Cleanest decorrelation, but needs that
  provider's API key — a **secret**, so setting it up is a one-time human escalation, and
  the key lives in a key file outside the Workspace or in the MCP config, never in a prompt, the repo, or an environment variable the owner sets.

Prefer the default unless the builder is already using the only non-Anthropic family your
Cursor plan offers (in which case use the API option to get a genuinely different family
for Review B).

**The merge's own commands.** Pushes and the merge run bare (`git push`, `gh pr merge <n> --squash --match-head-commit <sha>`), never piped, chained or wrapped: the allow rules and the permission guard read a command as written (rule 8, T8). A pull request's title starts with every increment ID it merges; one that merges none starts with its kind and ends with its bare requirement or issue IDs in parentheses, never a plan increment's ID there (ISS-013), and the `Merges:` trailer form holds only where the repository's squash message is the pull request's description (T4; the delegation loop's step 8, `~/.claude/cursor-bridge/workflow/phases/delegation-loop/merge.md`).

---

## One-line summary

Merge when tests really pass **and** two different model families both approve **and** no
one weakened the tests to get there — with the human asked only what the software should
do, never whether the code is right.
