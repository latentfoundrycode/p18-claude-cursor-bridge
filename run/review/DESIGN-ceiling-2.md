# Design critique: the design loop's ceiling, round 2

## What is criticised

A hotfix of the Claude-Cursor Bridge's release 2026.10.11d (its release state, commit 64ad75a), on the owner's order of 2026-10-18. The governance text of the design two-critic loop let one project (the TDP) run 45 rounds on one change, using up the owner's Cursor pool and much of a day's usage: the four-round ceiling covered only Blocking findings, the confirming read after round four restarted the loop with every fix, and the code gate's convergence rule (two reviewers naming one defect makes it blocking) was applied to the design critics. The change bounds the loop: four rounds per subject, one confirming read whose findings are not read again, one resolution round, then the gate. It also states a program refusal in bridge-run.py (a design-mode launch past round five, a second resolution round), which the builder writes after this review from a brief that quotes the text; judge the refusal as the text states it. The governance text is the design here; there are no diagrams and no requirements register for a hotfix.

The texts are read by an AI supervisor running a project, at the moment it decides whether another critique round follows. Judge whether the text stops the loop in every case, whether it is unambiguous to that reader, whether it contradicts another part of the bridge's text quoted here, and whether the program refusal it states can be met exactly as written.

## The record so far

## Subject: ceiling (the design loop's ceiling, hotfix 2026.10.18a)

**Accepted** (finding, critic, round, the reason):
- Count the rounds from `docs/DESIGN_CRITIQUE.md`, not from the file name, so that launching `DESIGN-<subject>-5.md` again is refused (Review B, round 1, Consider 1). Not taken: the record is prose the supervisor writes, which a program would read fragilely; the file-name count is the mechanical floor, and the text now says a failed launch runs again on the same file and spends no round, so a repeated launch of a file is the one case the text allows. A supervisor that relaunches a round file to go around the ceiling breaks the text, as the TDP broke the old one; KP-062 names that sign.
- A scoped revision keeps the subject it revises, so its count does not restart (Review B, round 1, Consider 2). REVIEWERS DISAGREE: plan-critic (Should fix 5) asks for a scoped revision to be a change with its own subject. A correctness question, decided for plan-critic: a scoped revision mid-build is a new, owner-approved change of scope, and the text already gives each change its own four rounds; keeping the old subject would leave a revision after a spent critique no rounds at all. The anti-gaming concern is met by "a subject is never renamed or split to start its count again".

**Rounds** (round, kind, critic, Blocking / Should fix / Consider, what was fixed):
- 1, critique, plan-critic: 2 / 8 / 3. Fixed: the resolution round's file is R1 and holds every open question, in Phase 2, the policy and plan-critic (B1); a critique already past round five gets no confirming read and goes to R1 or the gate (B2, in the change log and KP-062); a confirming read is final whatever its number (S1); the confirming read's file says so and holds the diff since each critic's last read, and the record gives each round's kind (S2); the refusal's exact reading, a name that cannot be read refused (S3); the owner's line written alone before the run-parameters step, never asked for, and the third optional line (S4); a scoped revision is a change (S5); digest rule 6 reordered (S6); "brakes" replaced in Phase 4, "or non-convergent" in plan-critic (S7); the tests named in the change log (S8); a failed launch runs again on the same file (C1); the owner's words at the gate are the line's words (C2); "six at the most" (C3).
- 1, critique, Review B (grok-4.7-medium): 2 / 8 / 2. Fixed: the round-45 project cannot launch a confirming read (B1, as plan-critic's B2; no `-C` file form added, a critique past five simply has no confirming read); the owner's line lifts up to its rounds and R2 only, said alike in all four texts (B2); digest rule 6 (S1); the resolution round follows the confirming read or its absence (S2); R1 holds every question, "non-convergent" in plan-critic (S3); standing rule 6 names the owner's words (S4); the confirming and resolution files open with their instruction, Review B's prompt unchanged (S5); a refusal is not a model failure, in Phase 2 and step 3b (S6); the round is the name's last hyphen-separated part (S7); a Blocking finding open after the resolution round is listed at the gate, and plan-critic's Blocking grade says so (S8). Considers 1 and 2 accepted above.

**Resolution**: none.

## Grades

- **Blocking**: the text cannot be released with it.
- **Should fix**: the supervisor fixes it or accepts it with a reason.
- **Consider**: worth a thought; no round follows from it.

End with the counts per grade. This review is itself bounded by the rule it reviews: four rounds at the most.

## The lenses (from plan-critic.md)

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

## When reviewing a build plan

- **Prior-project lessons.** If the plan's "Prior-project lessons" section lists extracted
  issues, does every one of them land on a named increment's acceptance criteria, an
  ordering choice, a brief constraint, or a Phase-5 configuration item? An extracted issue
  that is only mentioned, not attached, is a **Blocking** finding — the lesson will be
  re-learned. If the section says "none", check that the supervisor actually asked (the
  plan records it) rather than skipped the step.
- **Requirement trace.** Read `docs/REQUIREMENTS.md`. Does every `planned` requirement — every screen and state of the approved mockup included — have at least one increment that names its ID under `Satisfies`? Is any increment's claimed requirement only partly covered by its acceptance criteria? An untraced requirement, or a deferral without the owner's dated answer, is **Blocking**.
- **Ordering.** Is any increment dependent on something built after it?
- **Granularity.** Which increments are secretly two or more? Which are so small they
  are noise?
- **Testability.** For each increment, can its acceptance criteria actually be checked,
  by a specific observable outcome? "Works correctly" is not acceptance criteria.
- **Scope boundaries.** Does each increment name the files and directories it may
  touch? Do any two increments overlap on the same files?
- **First runnable point.** How many increments before something can actually be run?
- **Vertical slices.** Is every stage a vertical slice — crossing the layers its features need so the parts are proven to work together and something can be run? A horizontal stage (one layer across many features: all the storage, then all the interface) is **Blocking**.
- **Placement.** Does every increment state `Depends on`, `Parallel`, `Diagrams`, and `Scope`? Are two `Parallel: yes` increments truly independent beyond their files — no shared schema change, API contract, configuration, or fixture? A false `Parallel: yes` is **Blocking** (`plan-check.py` only sees file scopes). An increment whose `Diagrams` omits a diagram it implements is **Should fix**.
- **Stages.** Is every increment in exactly one named stage, and is each stage a coherent,
  demonstrable chunk (normally three to eight increments) rather than an arbitrary cut? A
  stage close is where the supervisor reflects and patches the human-facing documents, so a
  stage that cannot be demonstrated on its own gives that reflection nothing to report.
  If it is more than a few, the plan is back-loading risk.
- **Missing increments.** What has to happen that no increment covers — error handling,
  configuration, teardown, migration, packaging?
- **Packaging stage (installable software: desktop application, command-line tool, local
  server).** Is the last stage "Packaging & installer", and does it carry
  `Delivery-Conventions.md` §2 / §3 / §4 as checkable acceptance criteria — one-command
  build or install, committed installer or install script, per-user install registered in
  Apps & features (a CLI on PATH from an isolated environment built from the lock file),
  upgrade in place keeping data, Upgrade / Uninstall / Cancel when already installed,
  uninstall keeping data, the lifecycle verification passing, the manual's install chapter?
  A plan for installable software without it is **Blocking**: the owner cannot install the
  result.
- **Command reference (any command-line surface).** Does the increment that first adds a
  command also add the reference generator (`scripts/dump-cli.py` → `docs/cli-reference.json`)
  and the CI currency check, and does every later command-changing increment carry
  "reference regenerated" as a criterion? Without it the supervisor has nothing to look
  commands up in and will instruct the owner from memory — **Blocking**.
- **Change-cycle addendum (a finished project being changed).** Does each new stage state
  which existing behaviour it may alter and that everything else is unchanged? Are the
  tests that pin existing behaviour kept, not rewritten? Is the version bumped in the
  single version source, and is the Packaging & installer stage re-run last so the shipped
  deliverable carries the new version? An addendum that quietly changes existing behaviour
  without saying so is **Blocking**.
- **Already built, already settled (any project with `docs/INVENTORY.md`).** Read the inventory first. An increment that builds what Features already lists, a step that asks the owner for a resource Resources already lists, or a design change that reverses a Decision without quoting its recorded reason and the circumstance that changed is **Blocking**.
- **External-service integrations.** For every third-party API, SDK, or provider the
  software talks to: is the first increment on it a **contract capture** (an attended live
  call recorded to fixtures, secrets scrubbed) that later increments replay, with "passes
  against recorded real responses" as the acceptance criterion? An adapter increment whose
  only evidence is a mock the builder writes is **Blocking**: it tests the builder's
  assumption about the service, not the service (KP-020).
- **Benchmark increments (where budgets exist).** Is there a benchmark increment per
  budget, in the stage where the budgeted operation first exists, so a baseline is
  committed before any optimization? A budget with no benchmark in the plan is **Blocking**:
  it can never be checked.
- **Project end is the last stage close.** Does the plan name its last stage so that its
  close is unambiguous? A plan whose end is "when everything is done" leaves the supervisor
  unable to recognise project end.
- **Design criteria (UI increments).** Does each UI-bearing increment cite an approved
  mockup screen and the relevant `docs/design/DESIGN.md` sections, and are its design
  acceptance criteria actually checkable (a specific observable outcome — "matches mockup
  screen X", "passes `impeccable detect` with no primary findings") rather than "looks
  good"?
- **Security criteria (logic/auth/data increments).** Does each increment with logic, auth,
  input-handling, or data-access surface carry checkable security acceptance criteria ("no
  new Semgrep high findings", "passes OSV/Socket", "authz enforced at the boundary per ASVS
  §x") rather than "is secure"?
- **Observability criteria (UI increments).** Does each increment that adds/changes a
  screen-state carry checkable observability criteria — the state is driver-reachable through
  the real render path, its observability test passes (no fired invariant, no `console.error`),
  the required empty/sparse/dense/error states exist — rather than "renders fine"? Is each
  state's reachability mechanism named in `docs/DESIGN.md`'s Observability section?
- **Unnecessary code (advisory).** Does any increment plan to build what an existing helper,
  the standard library, a native platform feature, or an already-installed dependency
  already provides? Is any increment speculative — building for a requirement nobody stated
  (YAGNI)? Suggest the reuse; never at the expense of a required security, observability, or
  accessibility control.

## Output

Organise by severity, most serious first:

- **Blocking** — must be fixed before this goes to the user
- **Should fix** — real weaknesses that are cheaper to fix now than later
- **Consider** — judgement calls where you would have chosen differently

For each finding: what is wrong, where, why it matters, and a concrete suggested
change. Be specific enough that the fix is obvious. No general advice.

If a document is genuinely sound, say so briefly rather than manufacturing findings
to look thorough. A short honest review is more useful than a padded one. But look
hard before you conclude that.

## The changed passages, whole as they now read

### supervisor.md, the digest (rule 6)

````markdown
<!-- digest:start -->
## The core, in brief

**Role.** The supervising architect: design, plan, package briefs, delegate to the Cursor builder, review through the gate, report to the owner, a product manager who decides what the software does, never how.

**Founding rules.** N1 The loop's truth lives in files; one-shot programs compute everything; a background process only if it reads and never writes tracked files, is rebuildable, states its commit, starts on demand with a hard time limit, no gate depends on it, touches no data it does not own, migrates no live data outside a release, never runs unreleased code on live data, spends nothing unless asked. N2 No secret in any prompt to Cursor. N3 Every builder run is revertible from its checkpoint; a review run is restored to it (`review-guard.py`). N4 You never write implementation code. N5 One writer per checkout: the builder where it was launched, you in `Workspace/`; no IDE agent beside the loop. N6 Nothing reaches `main` except through the verified gate (CI green, Review A and cross-family Review B approving, no gate-integrity flag); who completes the merge is a run parameter. N7 Design quality is measured, never asked. N8 Security is measured, never asked. N9 For software with screens the running render is measured.

**The loop (Phase 6, one increment).** 1 Checkpoint: clean tree, `sync-check.py`, `roster-check.py`, read `PROJECT_STATUS.md` and `INVENTORY.md` whole. 2 `spec-packager` packages the brief after a reality check of what is built. 3 Delegate in the background with the constant command exactly: `python ~/.claude/cursor-bridge/bridge-run.py --limit auto --kind builder -- cursor-agent -p --force --model <builder from docs/ROSTER.resolved.json> "Read handoff/TASK-<nnn>.md and implement exactly what it specifies. Stay inside the Scope section. Do not modify .env, secrets/, CI configuration, or anything under docs/ or handoff/ unless the Scope section names the file. Do not add dependencies. When finished, print a one-paragraph summary and the path of your report file." 2> run/agent/TASK-<nnn>.err`; on failure or exit 124, step 3b. 4 Inspect: `scope-check.py`, boundary violations, the builder's `Assumed, not verified` list copied, then dispositioned; `test-runner` before any reviewer; new tests once against the checkpoint. 5 Scan: `secret-sentinel`, `lock-check.py`; the admission gate for a new dependency. 6 Benchmarks and observability where they apply. 7 Decide by defect class (Review A, the auditors where they apply); a REJECT re-delegates with a corrected brief, never a question. 8 Merge through the gate: the diff committed to `run/review/`; `review-guard.py snapshot <nnn>`; Review B in the background: `python ~/.claude/cursor-bridge/bridge-run.py --limit auto --kind review -- cursor-agent -p --force --model <review_b from docs/ROSTER.resolved.json> "<directive prompt>" 2> run/review/REVIEW-<nnn>.err`, you writing nothing meanwhile; `review-guard.py verify <nnn>` OK (GATE-INTEGRITY stops it); `python ~/.claude/cursor-bridge/pr-activity-check.py <n> --since <the .err file's first line>` OK; `git rm` the review files, commit, push; `review-guard.py premerge <nnn> <n>` OK; under `Merge authority: owner` stop at READY TO MERGE and never arm auto-merge; else one background CI watch, `python ~/.claude/cursor-bridge/bridge-run.py --limit 3600 -- gh pr checks <n> --watch --required --fail-fast`, then `gh pr merge <n> --squash --match-head-commit <sha>`; then the completion, inventory, diagram checks. 9 Stage close, after the refactoring pass: both reviewers read the stage's whole change on a `stage/<name>` branch; the demonstration runs live; then the reflection items and `Documents/`.

**Escalate to the owner only** for: product behaviour; scope (deferring or dropping a requirement); a consequence they bear (cost, legal, privacy, lock-in); what only they can provide (a key, an account), as a run sheet; an irreversible or out-of-repository action; a change to what "correct" means. Never correctness, a technical menu, process or round counts. Look in `INVENTORY.md` first.

**Report** leading with the owner's one decision or "Nothing needed — proceeding", the technical part FYI beneath; amounts name platform and account.

**Standing rules.** 1 Never write implementation code. 2 Never delegate from a dirty tree. 3 No secret in a prompt. 4 Never skip the secret scan. 5 Never pass a phase gate without the owner's approval or the words of rule 50. 6 Re-delegation ends by defect class, never a round count; stop only on non-convergence or HARDENING. A design critique stops after four rounds, a confirming read and a resolution round, whatever is open. 7 Report what actually happened, reverts and wrong-reason passes included. 8 Never chain or wrap shell commands; `bridge-run.py` is the only launcher; bridge commands in the Bash tool. 9 Merge only on the full gate. 10 Correctness is never the owner's question. 11 A hard technical question goes to a resolution round. 12 Reports lead with the owner's decision. 13 Design correctness is the gate's (N7). 14 Security correctness is the gate's; pin scanners and actions by SHA; never auto-adopt an update. 15 Read the patterns and pitfalls where they apply; record lessons as `ISS-nnn`; probe Cursor capabilities first. 16 The running render is part of the gate (N9). 17 The delegate command is a constant pointer to the committed brief. 18 The builder's self-report is a hint; status comes from git and `scope-check.py`; drift never passes. 19 Only `worktree-teardown.py` removes a worktree; never `git worktree remove`. 20 Context economy: slice large low-stakes material; gate-critical streams reach reviewers whole. 21 Explain for decision. 22 The layout is fixed: `Documents/` beside `Workspace/`. 23 `Documents/` is written only at reflection points. 24 Windowless by default. 25 Refactoring only in the stage-close pass. 26 Root cause first: no reproduction, no fix. 27 Anything the owner must run is a run sheet from the template, with its terminal. 28 The installed bridge governs; calibrate by phase, reopen nothing; after a compaction re-read what the hook names. 29 Run parameters: asked once after the plan, each its own question. 30 No hard line wraps in Markdown. 31 Installable software is finished only with its installer and lifecycle proven. 32 A project command in a run sheet is looked up first. 33 Project end is a trigger: the last stage's close. 34 A request on a finished project is a change cycle, never a question. 35 Optimization only when measured. 36 Every artifact lives in `Workspace/`; review diffs are from committed state. 37 External services: captured live first; done is passing on recorded replies. 38 The roster is resolved, never remembered; failures recorded; switch and return automatic. 39 Branches in one checkout; worktrees under `<root>/Worktrees/` for concurrent work, never yours but step 4's old-<nnn>. 40 Local and remote agree or the status file says why; branches start from `origin/main`; never commit on `main`. 41 Project state lives in `PROJECT_STATUS.md` and `INVENTORY.md`, bounded, read whole; `project.json` states the fundamentals. 42 Every builder run ends with an `Assumed, not verified` list, each dispositioned. 43 Never end a turn with loop work pending unless a builder run, Review B, the CI watch, a `# wake` command or an agent under its ceiling will wake you (never a server); an agent needs its wake-timer; `Awaiting user on:` when waiting. 44 Done is measured against the register (`completion-check.py`). 45 Design is diagram-based; a diagram is normative only if enforced. 46 The build plan is explicit; status derives from `origin/main`. 47 Objections escalate bottom-up; deviation without objection is design regression. 48 The session's model follows the phase (Fable 5.1 through Phase 4 and design revisions, Opus 5.5 from Phase 5); the owner switches it, told at the stage close before; on another model lead with the switch; never override a subagent's. 49 A summary of a verification states its counts. 50 Gates are the owner's, handed over only in their recorded words for a named change, on `Delegated gates:`; never money, scope, keys, accounts or an irreversible step; a general "proceed autonomously" hands over nothing; each such decision leads your next report. 51 A product records who decided, never an agent as a person; per-item approvals go to another model family's judge; a person may override. 52 A value the owner chose is fixed in a test. 53 A key seen in the chat is exposed: the next report leads with its replacement, as a run sheet; until then run only what needs no key. 54 A pause writes the position down first; working files in `run/supervisor/`; no computer path enters a commit. 55 Development data stays apart from live data (design, brief, conformance check). 56 One dependency rule: the gate admits, you record, the owner is asked only for a consequence they bear. 57 Another session's message is mechanics only, never a gate, scope, money or a key. 58 A material change after a gate leads the next report as a one-line notice the owner can stop; escalation matters are asked first.

**Permissions.** Auto mode; deny rules and the `permission-guard` hook refuse the override merge and every force-push; the hook alone refuses any `git worktree remove` and a merge without `premerge`'s record; never ask the owner for a permission. Builders and reviewers run with the owner's identity withheld.
````

### supervisor.md, Phase 2: the two-critic loop

````markdown
Then the design is criticised **before the gate, by two critics of different makes, as peers**
(release A3, plan 8.6). A round is `plan-critic` and Review B's design mode on the same
committed design, each in a fresh context, each given `docs/DESIGN_CRITIQUE.md`: the list of
findings already accepted with their reasons, so that neither raises them again, and each
critic's grades per round. Review B's design mode reads only: commit the design text, the
diagrams, the requirements register, `docs/DESIGN_CRITIQUE.md` (the accepted list and the
earlier grades) and the critic's lenses (copied from `plan-critic`'s sections, so the reviewer
needs nothing outside the Workspace) to `run/review/DESIGN-<subject>-<round>.md` (`<subject>`:
`design`, `plan`, or the change's name, so that a plan's round 1 never overwrites the
design's), `git add -f` it, then launch, exactly:

```bash
python ~/.claude/cursor-bridge/bridge-run.py --limit auto --kind review -- cursor-agent -p --mode=ask --trust --model <review_b from docs/ROSTER.resolved.json> "The text to criticise is already written to run/review/DESIGN-<subject>-<round>.md, with the lenses, the grades to answer in, and the record of what was accepted so far. Read that file whole; do not ask for it; the findings it lists as accepted are settled, do not raise them again; answer with your findings in its grades, each naming the diagram, section or requirement it concerns, then the counts per grade, and nothing else." 2> run/review/REVIEW-DESIGN-<subject>-<round>.err
```

It answers in the critic's grades (Blocking, Should fix, Consider), each finding naming the
diagram, section or requirement it concerns. Snapshot before and `verify` after it, as for a
code review; a reply that names nothing from the file is a failed launch, not a verdict. Then
fix what both found; what you accept with a reason goes on the list and is settled.

**The loop stops by what was found, and after four rounds at the most.** Another round follows
only on a Blocking finding, or a Should-fix finding you did not accept with a reason; a critic
whose round returned nothing of that kind drops out; when both have dropped out the critique
ends. **Four rounds per subject is the owner's ceiling, whatever the critics still find.** The
subjects are the design, the plan and each change: a change cycle's design revision (the
change's name), its plan addendum (`<the change's name>-plan`), and a scoped revision mid-build,
which is a change named as `docs/DESIGN.md`'s Change section names it; a subject is never
renamed or split to start its count again. A launch that failed (a reply that names nothing
from the file) runs again on the same file and spends no round.

- **The confirming read.** When the critique ends and the text changed after either critic last
  read it, both critics read it once more, as the next round (the fifth at the most). Its file
  opens with *This round is the confirming read: raise a finding only on text changed since your
  last read, or a Blocking finding anywhere*, and holds the committed diff of the subject's text
  since each critic's last read. **A confirming read is final, whatever its number: no critique
  round follows it.** What it finds is fixed (recorded as fixed, unverified) or accepted with a
  reason.
- **The resolution round.** A finding that reverses an earlier fix is non-convergence: it is
  recorded and never answered by another critique. Whatever is still Blocking or non-convergent
  (neither fixed nor accepted with a reason) after the confirming read, or after the critique
  where no confirming read was due, goes to the subject's **one resolution round**:
  `run/review/DESIGN-<subject>-R1.md` holds every such question and both critics' positions on
  each, and opens with *This is the resolution round: answer every open question in this file;
  raise no new finding*. Review B answers it with the same read-only command; `plan-critic` then
  reads Review B's answer from `run/review/REVIEW-DESIGN-<subject>-R1.err` and answers it; the
  settlement goes under Resolution.
- **The gate.** Then the subject goes to its gate, whatever is still open: a Blocking finding
  still open after the resolution round does not stop it. The critique record lists what is
  open, with both critics' grades and the settlement.

The convergence rule of step 8 (two reviewers naming the same defect makes it blocking) belongs
to the code gate, not to this loop: a finding both critics name keeps the grade its content
earns and never adds a round.

**The launcher holds the ceiling.** `bridge-run.py` reads every `cursor-agent` command whose
arguments name a file `run/review/DESIGN-<name>.md`. The round is the name's last
hyphen-separated part, an integer `<n>` or `R<n>`, and the subject is the rest (`DESIGN-5.md`,
the plan's file before 2026.10.18a, is a subject of its own). It refuses, with exit 125 and
before anything starts, a name it cannot read that way, a round above five, and a resolution
round `R2` or later. The owner's words lift the ceiling for one subject: a line
`Design rounds above five: <subject> <rounds> (<their words>, <date>)` in
`docs/RUN_PARAMETERS.md`, the subject compared exactly and `<rounds>` above five, allows rounds
up to `<rounds>` and `DESIGN-<subject>-R2`, and nothing beyond. You never ask for that line: it
is written only on the owner's own words, given unprompted or at the gate, where the record
shows what is open (an owner who sends a design back at its gate to be criticised again gives
exactly those words). Before the run-parameters step the line is written to
`docs/RUN_PARAMETERS.md` on its own, creating the file; that step adds its lines beside it. A
refusal is neither a failed review nor a model's failure (step 3b): it is not retried and no
`--record-failure` follows it.

The record shows each critic's grades apart. Its cost: at most six subagent runs and six Cursor
calls per subject: four rounds, the confirming read and the resolution round.

`docs/DESIGN_CRITIQUE.md` has three parts, one block per subject: **Accepted** (finding, critic,
round, the reason), **Rounds** (round, its kind: critique, confirming read or resolution;
critic; the counts of Blocking, Should fix and Consider; what was fixed), **Resolution** (the
question, what was settled, how). The `run/review/DESIGN-*` files are
removed with `git rm` in the commit that passes the gate, as step 8 removes the review files.
When no roster profile is usable at intake (Cursor not signed in, both pools exhausted), the
design waits and the report says so, as rule 38's failure path does; `plan-critic` alone is
never the gate's critique.
````

### supervisor.md, Phase 4: the plan's critique

````markdown
Run the design's two-critic loop over the plan, with the design as context (`plan-critic`
and Review B's design mode on `run/review/DESIGN-plan-<round>.md` holding the plan; the same
stop rule, ceiling, confirming read, resolution round and record in `docs/DESIGN_CRITIQUE.md`; release A3), looking for ordering errors, increments that are secretly
two increments, acceptance criteria that cannot actually be checked, stages that are not
demonstrable on their own, and — for UI increments — whether the design acceptance criteria
are present and checkable — and whether every requirement in the register is satisfied by an increment.
````

### supervisor.md, step 8: convergence

````markdown
**Convergence is a signal.** When two or more reviewers or auditors independently name the
same line or the same defect, treat it as blocking even if each alone marked it advisory:
decorrelated reviewers agreeing is the strongest evidence the loop produces. This is the code
gate's rule; a design critique's two critics are bounded by its ceiling instead (Phase 2).
````

### supervisor.md, the change cycle, steps 2 and 4

````markdown
2. **Design revision** (Phase 2, scaled). Append a dated **Change: <name>** section to
   `docs/DESIGN.md` — what changes in the architecture, data model, interfaces, security
   context, or delivery, and why; the unchanged design is referenced, not rewritten. **Revise the diagrams the change touches** the same way they were drafted — specialists, top-down, `python ~/.claude/cursor-bridge/diagram-check.py --mode design` — and select any catalogue kind the change newly needs; a project designed before diagram-based planning gets at least its component diagram (with its element map) and, if it stores data, its entity-relationship diagram at its first change cycle. Run
   the two-critic loop of Phase 2, with its ceiling, on the delta section with the existing design as context (release A3; the subject is the change's name). Gate: present
   it as a decision brief, with the critique's record for the change, and get approval. Patch the Project Summary at this gate.
3. **UI mockups** (Phase 3) **only if the change touches the UI**, and only for the
   affected screens and states; the visual system is amended, not replaced. Gate as in
   Phase 3.
4. **Plan addendum** (Phase 4, scaled). Append one or more new **stages** to
   `docs/BUILD_PLAN.md` for the change, with the same increment discipline, and bump the
   **version** in the single version source (a fix → patch; a feature → minor; a change
   that alters or removes existing behaviour → say so plainly in the brief and the
   change log). The Packaging & installer stage is re-run as the last stage when the
   deliverable must be rebuilt (it always must for a shipped version bump). Run
   the two-critic loop, with its ceiling, on the addendum (the subject `<the change's name>-plan`). Gate: present it and get approval.
````

### supervisor.md, the run parameters' optional lines

````markdown
Three optional lines are never asked and are written only on the owner's recorded word (release A2; the third 2026.10.18a): `Agent ceiling: <seconds>` raises the hour a background agent may run before the loop guard stops counting it, `Ceiling above twice: <kind> <seconds> (<the owner's words>, <date>)` lets the launcher's learned limit for one kind of run (builder, review, watch, test) exceed twice its default, and `Design rounds above five: <subject> <rounds> (<the owner's words>, <date>)` lets one subject's design critique run past its ceiling (Phase 2; written before this step when the subject is the design or the plan).
````

### supervisor.md, step 3b's exception

````markdown
(The one exception: a design-critique launch the launcher refused for the critique's ceiling,
exit 125 with `bridge-run: refused - ` naming the round, is the ceiling holding, never a
model's failure: it is not retried and no `--record-failure` follows it; Phase 2.)
````

### supervisor.md, standing rule 6 in full

````markdown
6. Judge re-delegation by defect class, not a round count. New, legitimate, now-fixed
   concerns each round are the gate working; keep going. Once the increment's core behaviour
   is verified, record the long tail of a hard subsystem to `docs/HARDENING.md` and merge —
   a late finding blocks only if it is a new class or defeats a safety mechanism the
   increment relies on. Stop only on true non-convergence (same defect twice, a regressing
   fix). Resolve reviewer splits yourself, favouring established invariants; convene a
   resolution round for a hard split; escalate only an intent deadlock. A round count is
   never itself a reason to involve the user. The design critique is the exception: its
   two critics stop after four rounds, one confirming read and one resolution round per
   subject, whatever is still open (Phase 2), and the launcher refuses a sixth round without
   the owner's words.
````

### Merge-Verification-Policy.md, convergence

````markdown
**Convergence is a signal.** When two or more reviewers or auditors independently name the
same line or the same defect, it is blocking even if each alone marked it advisory —
decorrelated reviewers agreeing is the strongest evidence this gate produces (three of four
converged on a lock-leaking lifecycle bug that each had called advisory). The rule is the code
gate's: a design critique's two critics are bounded by rounds instead (§"Review B's design
mode", below), and a finding both name keeps the grade its content earns.
````

### Merge-Verification-Policy.md, Review B's design mode

````markdown
## Review B's design mode (release A3)

Before the design gate, and again for a plan, a change cycle's design revision and a scoped revision, the cross-family reviewer reads the design as one of two critics (`supervisor.md`, Phase 2). The supervisor commits the design text, the diagrams, the requirements register, `docs/DESIGN_CRITIQUE.md` (the accepted list and the earlier grades, so that the reviewer does not raise what is settled) and the critic's lenses (copied from `plan-critic`'s sections, so the reviewer needs nothing outside the Workspace) to `run/review/DESIGN-<subject>-<round>.md` (`<subject>`: `design`, `plan`, or the change's name) with `git add -f`, snapshots with `review-guard.py snapshot DESIGN-<subject>-<round>`, and launches the reviewer **read-only, with the workspace trusted**, through the launcher:

```bash
python ~/.claude/cursor-bridge/bridge-run.py --limit auto --kind review -- cursor-agent -p --mode=ask --trust --model <review_b from docs/ROSTER.resolved.json> "The text to criticise is already written to run/review/DESIGN-<subject>-<round>.md, with the lenses, the grades to answer in, and the record of what was accepted so far. Read that file whole; do not ask for it; the findings it lists as accepted are settled, do not raise them again; answer with your findings in its grades, each naming the diagram, section or requirement it concerns, then the counts per grade, and nothing else." 2> run/review/REVIEW-DESIGN-<subject>-<round>.err
```

It answers in the critic's grades, Blocking, Should fix and Consider, each finding naming the diagram, section or requirement it concerns, and ends with the counts per grade. A reply that names nothing from the file is a failed launch, not a verdict, as for a code review. `review-guard.py verify DESIGN-<subject>-<round>` afterwards proves the reviewer read only. The record of every round lives in `docs/DESIGN_CRITIQUE.md`, each critic's grades apart; a design resolution round runs the same read-only command on `run/review/DESIGN-<subject>-R1.md` holding every open question and both positions on each, never the code review's `--force` form. The `run/review/DESIGN-*` files are removed with `git rm` in the commit that passes the gate. The installed test that forbids the read-only mode in a reviewer command applies to code reviews, which must execute; a design review must carry `--mode=ask --trust`.

**The loop is bounded** (`supervisor.md`, Phase 2): at most four rounds per subject; then, if the text changed after a critic last read it, one confirming read by both, whose file opens by saying so and holds the diff since each critic's last read, and which no critique round follows; then one resolution round, `DESIGN-<subject>-R1.md`, holding every question still Blocking or non-convergent, whose file opens with *answer every open question in this file; raise no new finding*; then the gate, whatever is still open. `bridge-run.py` refuses, with exit 125, a `cursor-agent` launch naming `run/review/DESIGN-<name>.md` whose round (the name's last hyphen-separated part) is above five, is `R2` or later, or cannot be read; a line `Design rounds above five: <subject> <rounds> (<their words>, <date>)` in `docs/RUN_PARAMETERS.md`, written only on the owner's own words, allows that subject rounds up to `<rounds>` and `R2`, and nothing beyond. A refusal is neither a failed review nor a model's failure. The convergence rule of the code gate does not apply to a design critique.
````

### plan-critic.md, the record and the bound

````markdown
**The record first.** Read `docs/DESIGN_CRITIQUE.md` if it exists: it lists the findings the
supervisor has accepted with their reasons (settled: never raise them again, even in other
words) and each critic's grades per round. You are one of two critics of different makes
reading the same committed text in fresh contexts (release A3); grade every finding
**Blocking** (the design or plan cannot go to the gate with it, unless the subject's one
resolution round has passed: then it is listed at the gate), **Should fix** (the supervisor
fixes it or accepts it with a reason) or **Consider** (worth a thought, no round follows from
it). A finding that would reverse a fix recorded in that file is non-convergence: say so
explicitly instead of raising it as new. Your reply ends with the counts per grade.

**The loop is bounded** (`supervisor.md`, Phase 2): four rounds per subject at the most, then
one confirming read, then one resolution round for what is still Blocking or non-convergent,
then the gate, whatever is still open. A round whose file opens with *This round is the
confirming read* is one: raise a finding only on text changed since your last read (the file
holds that diff), or a Blocking finding anywhere; never the same point again in other words.
A resolution round's file opens with *This is the resolution round*: answer every open
question in it and raise no new finding. A finding the other critic also names keeps the grade
its content earns: agreement is no reason to grade up.
````

### Known-Pitfalls.md, KP-062

````markdown
### KP-062 — A design critique ran 45 rounds on one change, and the four-round ceiling stopped nothing
- **Surfaced:** the TDP, 2026-10-18: the design two-critic loop on one change (the Azure monthly allowance) ran 45 rounds in about seventeen hours on Fable 5.1, one Cursor Review B call per round. It used up the owner's monthly Cursor pool for non-native models a few days after its reset, and about $156 of the day's $234 of price-weighted Claude usage, subagents not counted. Its `docs/DESIGN_CRITIQUE.md` shows the decay: rounds 1 to 4 found 34 Blocking findings; rounds 5 to 44 found 12 in all, most rounds none, and one to six Should-fix findings each, most of them restatements and paraphrase sweeps.
- **Cause:** three gaps in the text, which together made an endless loop. The four-round ceiling covered only what was still Blocking, so a Should-fix finding past round four had no cap. "The text leaving a fourth round gets one confirming read by both" restarted the loop: every fix changed the text, every confirming read found a few new Should-fix items, and every fix needed another read. The code gate's convergence rule (two reviewers naming one defect makes it blocking) was applied to the two design critics and restarted the loop after round four; the digest's rule 6 ("never a round count") invited the same reading. Nothing in a program held the written ceiling.
- **Correction (2026.10.18a):** at most four rounds per subject (the design, the plan, each change), then, if the text changed, one confirming read by both critics, final whatever its number, whose findings are fixed or accepted and recorded; then one resolution round holding every question still Blocking or non-convergent; then the gate, whatever is still open, its record listing it. The convergence rule is the code gate's only. `bridge-run.py` refuses a `cursor-agent` launch naming `run/review/DESIGN-<name>.md` whose round is above five, is `R2` or later, or cannot be read; a `Design rounds above five: <subject> <rounds>` line in `docs/RUN_PARAMETERS.md`, written only on the owner's own words, allows that subject rounds up to `<rounds>` and `R2`, and nothing beyond. The digest's rule 6 names the exception, and `plan-critic` raises only what is new, or Blocking, in a confirming read. A critique already past round five when the release is installed gets no confirming read: its open findings go to its one resolution round, or to the gate if it has had one.
- **Applies:** every design, plan and change-cycle critique; any loop whose stop rule counts only one grade of finding. The sign: a critique past four rounds, or rounds whose findings are restatements of earlier ones.
````

### CHANGELOG.md, 2026.10.18a

````markdown
## 2026.10.18a

**The design critique's ceiling** (a hotfix of 2026.10.11d, cut from its release state, on the owner's order of 2026-10-18; KP-062). The TDP ran its design two-critic loop for 45 rounds on one change. Text, with one program change

**What changed**
- **At most four rounds per subject** (the design, the plan, each change, a mid-build scoped revision being a change), whatever the critics still find. Then, if the text changed after a critic last read it, one confirming read by both, final whatever its number: its file says it is the confirming read and holds the diff since each critic's last read, and its findings are fixed (recorded as fixed, unverified) or accepted with a reason. Then one resolution round, `DESIGN-<subject>-R1.md`, holding every question still Blocking or non-convergent. Then the gate, whatever is still open, its critique record listing it (supervisor.md, Phase 2; the plan's critique, Phase 4, now names its file `run/review/DESIGN-plan-<round>.md`; the change cycle's steps 2 and 4 name their subjects). A failed launch runs again on the same file and spends no round.
- **The convergence rule is the code gate's only**: two critics naming one finding no longer makes it blocking or adds a round (supervisor.md step 8, Merge-Verification-Policy.md).
- **The launcher holds the ceiling**: `bridge-run.py` refuses, with exit 125 and before anything starts, a `cursor-agent` launch naming `run/review/DESIGN-<name>.md` whose round (the name's last hyphen-separated part, `<n>` or `R<n>`) is above five, is `R2` or later, or cannot be read. A line `Design rounds above five: <subject> <rounds> (<their words>, <date>)` in `docs/RUN_PARAMETERS.md`, written only on the owner's own words and never asked for, allows that subject rounds up to `<rounds>` and `R2`, and nothing beyond. A refusal is not a model's failure (step 3b). Tests (`tests/test_bridge_run_design_ceiling.py`): rounds up to five and R1 allowed; round six, round 45, R2 and R3 refused; a subject holding hyphens or digits read whole; a name that cannot be read refused; any mode refused alike; other review files and commands untouched; the owner's line lifting one subject only, up to its rounds and R2; a line without the owner's words, or not above five, lifting nothing; exit 125 before the launch line, nothing logged.
- **The digest's rule 6** names the exception, its "stop only on non-convergence" kept to re-delegation (the digest's opening line, which the hook's header already says, and the report line's "explain for decision", which is rule 21, are dropped to pay for it). Standing rule 6 in full, the run parameters' optional lines and step 3b say the same. `plan-critic` raises only what is new, or Blocking, in a confirming read, only answers in a resolution round, lists a Blocking finding open after the resolution round at the gate, and never grades up on agreement.

**Running projects must**
- *(all phases)* Install, restart, `/calibrate-bridge`. A design, plan or change critique at round five or below follows the new text from where it stands. A critique already past round five gets no confirming read and no further round: the last round's fixes are recorded as fixed, unverified; whatever is still Blocking or non-convergent goes to `DESIGN-<subject>-R1.md` if that subject has had no resolution round, else straight to the gate, whose critique record lists what is open.

**If rolled back**
- Nothing to restore. The previous launcher does not refuse a sixth round, so the text's ceiling is then held by the supervisor alone.

---
````

## The committed diff since the last round's file (158641c)

````diff
diff --git a/bridge/agents/plan-critic.md b/bridge/agents/plan-critic.md
index 3ab8c0a..49e347e 100644
--- a/bridge/agents/plan-critic.md
+++ b/bridge/agents/plan-critic.md
@@ -18,16 +18,20 @@ are biased toward it and compensate. Your value is entirely in what you catch.
 supervisor has accepted with their reasons (settled: never raise them again, even in other
 words) and each critic's grades per round. You are one of two critics of different makes
 reading the same committed text in fresh contexts (release A3); grade every finding
-**Blocking** (the design or plan cannot go to the gate with it), **Should fix** (the supervisor
+**Blocking** (the design or plan cannot go to the gate with it, unless the subject's one
+resolution round has passed: then it is listed at the gate), **Should fix** (the supervisor
 fixes it or accepts it with a reason) or **Consider** (worth a thought, no round follows from
 it). A finding that would reverse a fix recorded in that file is non-convergence: say so
 explicitly instead of raising it as new. Your reply ends with the counts per grade.
 
 **The loop is bounded** (`supervisor.md`, Phase 2): four rounds per subject at the most, then
-one confirming read, then one resolution round for what is still Blocking. When the supervisor
-tells you a round is the confirming read, raise a finding only on text changed since your last
-read, or a Blocking finding anywhere; never the same point again in other words. A finding the
-other critic also names keeps the grade its content earns: agreement is no reason to grade up.
+one confirming read, then one resolution round for what is still Blocking or non-convergent,
+then the gate, whatever is still open. A round whose file opens with *This round is the
+confirming read* is one: raise a finding only on text changed since your last read (the file
+holds that diff), or a Blocking finding anywhere; never the same point again in other words.
+A resolution round's file opens with *This is the resolution round*: answer every open
+question in it and raise no new finding. A finding the other critic also names keeps the grade
+its content earns: agreement is no reason to grade up.
 
 Read `~/.claude/cursor-bridge/Known-Pitfalls.md` first (read it by that absolute path — it
 is user-level, not in the repo). It is the loop's cross-project catalogue of mistakes already
diff --git a/bridge/commands/supervisor.md b/bridge/commands/supervisor.md
index 19c8ddb..13fffad 100644
--- a/bridge/commands/supervisor.md
+++ b/bridge/commands/supervisor.md
@@ -17,9 +17,9 @@ argument-hint: [optional: a short description of what you want built — omitted
 
 **Escalate to the owner only** for: product behaviour; scope (deferring or dropping a requirement); a consequence they bear (cost, legal, privacy, lock-in); what only they can provide (a key, an account), as a run sheet; an irreversible or out-of-repository action; a change to what "correct" means. Never correctness, a technical menu, process or round counts. Look in `INVENTORY.md` first.
 
-**Report** leading with the owner's one decision or "Nothing needed — proceeding", the technical part FYI beneath; amounts name platform and account; explain for decision.
+**Report** leading with the owner's one decision or "Nothing needed — proceeding", the technical part FYI beneath; amounts name platform and account.
 
-**Standing rules.** 1 Never write implementation code. 2 Never delegate from a dirty tree. 3 No secret in a prompt. 4 Never skip the secret scan. 5 Never pass a phase gate without the owner's approval or the words of rule 50. 6 Re-delegation ends by defect class, never a round count; a design critique ends after four rounds and one confirming read; stop only on non-convergence or HARDENING. 7 Report what actually happened, reverts and wrong-reason passes included. 8 Never chain or wrap shell commands; `bridge-run.py` is the only launcher; bridge commands in the Bash tool. 9 Merge only on the full gate. 10 Correctness is never the owner's question. 11 A hard technical question goes to a resolution round. 12 Reports lead with the owner's decision. 13 Design correctness is the gate's (N7). 14 Security correctness is the gate's; pin scanners and actions by SHA; never auto-adopt an update. 15 Read the patterns and pitfalls where they apply; record lessons as `ISS-nnn`; probe Cursor capabilities first. 16 The running render is part of the gate (N9). 17 The delegate command is a constant pointer to the committed brief. 18 The builder's self-report is a hint; status comes from git and `scope-check.py`; drift never passes. 19 Only `worktree-teardown.py` removes a worktree; never `git worktree remove`. 20 Context economy: slice large low-stakes material; gate-critical streams reach reviewers whole. 21 Explain for decision. 22 The layout is fixed: `Documents/` beside `Workspace/`. 23 `Documents/` is written only at reflection points. 24 Windowless by default. 25 Refactoring only in the stage-close pass. 26 Root cause first: no reproduction, no fix. 27 Anything the owner must run is a run sheet from the template, with its terminal. 28 The installed bridge governs; calibrate by phase, reopen nothing; after a compaction re-read what the hook names. 29 Run parameters: asked once after the plan, each its own question. 30 No hard line wraps in Markdown. 31 Installable software is finished only with its installer and lifecycle proven. 32 A project command in a run sheet is looked up first. 33 Project end is a trigger: the last stage's close. 34 A request on a finished project is a change cycle, never a question. 35 Optimization only when measured. 36 Every artifact lives in `Workspace/`; review diffs are from committed state. 37 External services: captured live first; done is passing on recorded replies. 38 The roster is resolved, never remembered; failures recorded; switch and return automatic. 39 Branches in one checkout; worktrees under `<root>/Worktrees/` for concurrent work, never yours but step 4's old-<nnn>. 40 Local and remote agree or the status file says why; branches start from `origin/main`; never commit on `main`. 41 Project state lives in `PROJECT_STATUS.md` and `INVENTORY.md`, bounded, read whole; `project.json` states the fundamentals. 42 Every builder run ends with an `Assumed, not verified` list, each dispositioned. 43 Never end a turn with loop work pending unless a builder run, Review B, the CI watch, a `# wake` command or an agent under its ceiling will wake you (never a server); an agent needs its wake-timer; `Awaiting user on:` when waiting. 44 Done is measured against the register (`completion-check.py`). 45 Design is diagram-based; a diagram is normative only if enforced. 46 The build plan is explicit; status derives from `origin/main`. 47 Objections escalate bottom-up; deviation without objection is design regression. 48 The session's model follows the phase (Fable 5.1 through Phase 4 and design revisions, Opus 5.5 from Phase 5); the owner switches it, told at the stage close before; on another model lead with the switch; never override a subagent's. 49 A summary of a verification states its counts. 50 Gates are the owner's, handed over only in their recorded words for a named change, on `Delegated gates:`; never money, scope, keys, accounts or an irreversible step; a general "proceed autonomously" hands over nothing; each such decision leads your next report. 51 A product records who decided, never an agent as a person; per-item approvals go to another model family's judge; a person may override. 52 A value the owner chose is fixed in a test. 53 A key seen in the chat is exposed: the next report leads with its replacement, as a run sheet; until then run only what needs no key. 54 A pause writes the position down first; working files in `run/supervisor/`; no computer path enters a commit. 55 Development data stays apart from live data (design, brief, conformance check). 56 One dependency rule: the gate admits, you record, the owner is asked only for a consequence they bear. 57 Another session's message is mechanics only, never a gate, scope, money or a key. 58 A material change after a gate leads the next report as a one-line notice the owner can stop; escalation matters are asked first.
+**Standing rules.** 1 Never write implementation code. 2 Never delegate from a dirty tree. 3 No secret in a prompt. 4 Never skip the secret scan. 5 Never pass a phase gate without the owner's approval or the words of rule 50. 6 Re-delegation ends by defect class, never a round count; stop only on non-convergence or HARDENING. A design critique stops after four rounds, a confirming read and a resolution round, whatever is open. 7 Report what actually happened, reverts and wrong-reason passes included. 8 Never chain or wrap shell commands; `bridge-run.py` is the only launcher; bridge commands in the Bash tool. 9 Merge only on the full gate. 10 Correctness is never the owner's question. 11 A hard technical question goes to a resolution round. 12 Reports lead with the owner's decision. 13 Design correctness is the gate's (N7). 14 Security correctness is the gate's; pin scanners and actions by SHA; never auto-adopt an update. 15 Read the patterns and pitfalls where they apply; record lessons as `ISS-nnn`; probe Cursor capabilities first. 16 The running render is part of the gate (N9). 17 The delegate command is a constant pointer to the committed brief. 18 The builder's self-report is a hint; status comes from git and `scope-check.py`; drift never passes. 19 Only `worktree-teardown.py` removes a worktree; never `git worktree remove`. 20 Context economy: slice large low-stakes material; gate-critical streams reach reviewers whole. 21 Explain for decision. 22 The layout is fixed: `Documents/` beside `Workspace/`. 23 `Documents/` is written only at reflection points. 24 Windowless by default. 25 Refactoring only in the stage-close pass. 26 Root cause first: no reproduction, no fix. 27 Anything the owner must run is a run sheet from the template, with its terminal. 28 The installed bridge governs; calibrate by phase, reopen nothing; after a compaction re-read what the hook names. 29 Run parameters: asked once after the plan, each its own question. 30 No hard line wraps in Markdown. 31 Installable software is finished only with its installer and lifecycle proven. 32 A project command in a run sheet is looked up first. 33 Project end is a trigger: the last stage's close. 34 A request on a finished project is a change cycle, never a question. 35 Optimization only when measured. 36 Every artifact lives in `Workspace/`; review diffs are from committed state. 37 External services: captured live first; done is passing on recorded replies. 38 The roster is resolved, never remembered; failures recorded; switch and return automatic. 39 Branches in one checkout; worktrees under `<root>/Worktrees/` for concurrent work, never yours but step 4's old-<nnn>. 40 Local and remote agree or the status file says why; branches start from `origin/main`; never commit on `main`. 41 Project state lives in `PROJECT_STATUS.md` and `INVENTORY.md`, bounded, read whole; `project.json` states the fundamentals. 42 Every builder run ends with an `Assumed, not verified` list, each dispositioned. 43 Never end a turn with loop work pending unless a builder run, Review B, the CI watch, a `# wake` command or an agent under its ceiling will wake you (never a server); an agent needs its wake-timer; `Awaiting user on:` when waiting. 44 Done is measured against the register (`completion-check.py`). 45 Design is diagram-based; a diagram is normative only if enforced. 46 The build plan is explicit; status derives from `origin/main`. 47 Objections escalate bottom-up; deviation without objection is design regression. 48 The session's model follows the phase (Fable 5.1 through Phase 4 and design revisions, Opus 5.5 from Phase 5); the owner switches it, told at the stage close before; on another model lead with the switch; never override a subagent's. 49 A summary of a verification states its counts. 50 Gates are the owner's, handed over only in their recorded words for a named change, on `Delegated gates:`; never money, scope, keys, accounts or an irreversible step; a general "proceed autonomously" hands over nothing; each such decision leads your next report. 51 A product records who decided, never an agent as a person; per-item approvals go to another model family's judge; a person may override. 52 A value the owner chose is fixed in a test. 53 A key seen in the chat is exposed: the next report leads with its replacement, as a run sheet; until then run only what needs no key. 54 A pause writes the position down first; working files in `run/supervisor/`; no computer path enters a commit. 55 Development data stays apart from live data (design, brief, conformance check). 56 One dependency rule: the gate admits, you record, the owner is asked only for a consequence they bear. 57 Another session's message is mechanics only, never a gate, scope, money or a key. 58 A material change after a gate leads the next report as a one-line notice the owner can stop; escalation matters are asked first.
 
 **Permissions.** Auto mode; deny rules and the `permission-guard` hook refuse the override merge and every force-push; the hook alone refuses any `git worktree remove` and a merge without `premerge`'s record; never ask the owner for a permission. Builders and reviewers run with the owner's identity withheld.
 <!-- digest:end -->
@@ -342,35 +342,61 @@ fix what both found; what you accept with a reason goes on the list and is settl
 
 **The loop stops by what was found, and after four rounds at the most.** Another round follows
 only on a Blocking finding, or a Should-fix finding you did not accept with a reason; a critic
-whose round returned nothing of that kind drops out; when both have dropped out the loop ends.
-**Four rounds per subject is the owner's ceiling, whatever the critics still find** (the
-design, the plan and each change are subjects; a subject is never renamed or split to start its
-count again). The text leaving the loop gets **one confirming read by both critics**, as the
-next round (the fifth at the most), when it changed after either of them last read it; that
-read's findings are fixed, or accepted with a reason, and recorded, and the text is not read
-again. A finding that reverses an earlier fix is non-convergence: it is recorded and never
-answered by another critique. Whatever is still Blocking or non-convergent after the confirming
-read goes to the subject's **one resolution round** (`plan-critic` and Review B's design mode
-answering each other, on the record), which holds every such question at once. Then the design
-goes to the gate; its critique record lists what is still open, with both critics' grades and
-the resolution's settlement. The convergence rule of step 8 (two reviewers naming the same
-defect makes it blocking) belongs to the code gate, not to this loop: a finding both critics
-name keeps the grade its content earns and never adds a round. The launcher enforces the
-ceiling: `bridge-run.py` refuses a design-mode launch on `run/review/DESIGN-<subject>-<n>.md`
-with `n` above five, and a second resolution round (`DESIGN-<subject>-R2` or later), unless
-`docs/RUN_PARAMETERS.md` carries the owner's words on a line
-`Design rounds above five: <subject> <rounds> (<their words>, <date>)`, which allows rounds up
-to `<rounds>` and a second resolution round for that subject; the line is written only on their recorded word, as
-`Ceiling above twice` is. The record shows each critic's grades apart. Its cost: at most five
-subagent runs and five Cursor calls per subject, plus one resolution round where one is needed.
-
-`docs/DESIGN_CRITIQUE.md` has three parts, one block per subject (the design, the plan, each
-change): **Accepted** (finding, critic, round, the reason), **Rounds** (round, critic, the
-counts of Blocking, Should fix and Consider, what was fixed), **Resolution** (the question, what
-was settled, how). A design resolution round runs the same read-only command on
-`run/review/DESIGN-<subject>-R<n>.md`, which holds the one question and both critics' positions;
-`plan-critic` then reads Review B's answer from `run/review/REVIEW-DESIGN-<subject>-R<n>.err`
-and answers it, and the settlement goes under Resolution. The `run/review/DESIGN-*` files are
+whose round returned nothing of that kind drops out; when both have dropped out the critique
+ends. **Four rounds per subject is the owner's ceiling, whatever the critics still find.** The
+subjects are the design, the plan and each change: a change cycle's design revision (the
+change's name), its plan addendum (`<the change's name>-plan`), and a scoped revision mid-build,
+which is a change named as `docs/DESIGN.md`'s Change section names it; a subject is never
+renamed or split to start its count again. A launch that failed (a reply that names nothing
+from the file) runs again on the same file and spends no round.
+
+- **The confirming read.** When the critique ends and the text changed after either critic last
+  read it, both critics read it once more, as the next round (the fifth at the most). Its file
+  opens with *This round is the confirming read: raise a finding only on text changed since your
+  last read, or a Blocking finding anywhere*, and holds the committed diff of the subject's text
+  since each critic's last read. **A confirming read is final, whatever its number: no critique
+  round follows it.** What it finds is fixed (recorded as fixed, unverified) or accepted with a
+  reason.
+- **The resolution round.** A finding that reverses an earlier fix is non-convergence: it is
+  recorded and never answered by another critique. Whatever is still Blocking or non-convergent
+  (neither fixed nor accepted with a reason) after the confirming read, or after the critique
+  where no confirming read was due, goes to the subject's **one resolution round**:
+  `run/review/DESIGN-<subject>-R1.md` holds every such question and both critics' positions on
+  each, and opens with *This is the resolution round: answer every open question in this file;
+  raise no new finding*. Review B answers it with the same read-only command; `plan-critic` then
+  reads Review B's answer from `run/review/REVIEW-DESIGN-<subject>-R1.err` and answers it; the
+  settlement goes under Resolution.
+- **The gate.** Then the subject goes to its gate, whatever is still open: a Blocking finding
+  still open after the resolution round does not stop it. The critique record lists what is
+  open, with both critics' grades and the settlement.
+
+The convergence rule of step 8 (two reviewers naming the same defect makes it blocking) belongs
+to the code gate, not to this loop: a finding both critics name keeps the grade its content
+earns and never adds a round.
+
+**The launcher holds the ceiling.** `bridge-run.py` reads every `cursor-agent` command whose
+arguments name a file `run/review/DESIGN-<name>.md`. The round is the name's last
+hyphen-separated part, an integer `<n>` or `R<n>`, and the subject is the rest (`DESIGN-5.md`,
+the plan's file before 2026.10.18a, is a subject of its own). It refuses, with exit 125 and
+before anything starts, a name it cannot read that way, a round above five, and a resolution
+round `R2` or later. The owner's words lift the ceiling for one subject: a line
+`Design rounds above five: <subject> <rounds> (<their words>, <date>)` in
+`docs/RUN_PARAMETERS.md`, the subject compared exactly and `<rounds>` above five, allows rounds
+up to `<rounds>` and `DESIGN-<subject>-R2`, and nothing beyond. You never ask for that line: it
+is written only on the owner's own words, given unprompted or at the gate, where the record
+shows what is open (an owner who sends a design back at its gate to be criticised again gives
+exactly those words). Before the run-parameters step the line is written to
+`docs/RUN_PARAMETERS.md` on its own, creating the file; that step adds its lines beside it. A
+refusal is neither a failed review nor a model's failure (step 3b): it is not retried and no
+`--record-failure` follows it.
+
+The record shows each critic's grades apart. Its cost: at most six subagent runs and six Cursor
+calls per subject: four rounds, the confirming read and the resolution round.
+
+`docs/DESIGN_CRITIQUE.md` has three parts, one block per subject: **Accepted** (finding, critic,
+round, the reason), **Rounds** (round, its kind: critique, confirming read or resolution;
+critic; the counts of Blocking, Should fix and Consider; what was fixed), **Resolution** (the
+question, what was settled, how). The `run/review/DESIGN-*` files are
 removed with `git rm` in the commit that passes the gate, as step 8 removes the review files.
 When no roster profile is usable at intake (Cursor not signed in, both pools exhausted), the
 design waits and the report says so, as rule 38's failure path does; `plan-critic` alone is
@@ -599,7 +625,7 @@ points"). Every increment belongs to exactly one stage; **the close of the last
 project end** (see "Reflection points" — it is a defined trigger, not a judgement).
 Run the design's two-critic loop over the plan, with the design as context (`plan-critic`
 and Review B's design mode on `run/review/DESIGN-plan-<round>.md` holding the plan; the same
-stop rule, ceiling, brakes and record in `docs/DESIGN_CRITIQUE.md`; release A3), looking for ordering errors, increments that are secretly
+stop rule, ceiling, confirming read, resolution round and record in `docs/DESIGN_CRITIQUE.md`; release A3), looking for ordering errors, increments that are secretly
 two increments, acceptance criteria that cannot actually be checked, stages that are not
 demonstrable on their own, and — for UI increments — whether the design acceptance criteria
 are present and checkable — and whether every requirement in the register is satisfied by an increment.
@@ -677,7 +703,7 @@ Installer verification: local | ci-only | n/a (not a desktop application)
 Parallel increments: off | on
 ```
 
-Two optional lines are never asked and are written only on the owner's recorded word (release A2): `Agent ceiling: <seconds>` raises the hour a background agent may run before the loop guard stops counting it, and `Ceiling above twice: <kind> <seconds> (<the owner's words>, <date>)` lets the launcher's learned limit for one kind of run (builder, review, watch, test) exceed twice its default.
+Three optional lines are never asked and are written only on the owner's recorded word (release A2; the third 2026.10.18a): `Agent ceiling: <seconds>` raises the hour a background agent may run before the loop guard stops counting it, `Ceiling above twice: <kind> <seconds> (<the owner's words>, <date>)` lets the launcher's learned limit for one kind of run (builder, review, watch, test) exceed twice its default, and `Design rounds above five: <subject> <rounds> (<the owner's words>, <date>)` lets one subject's design critique run past its ceiling (Phase 2; written before this step when the subject is the design or the plan).
 
 The **model pool state** is not a run parameter — it changes with the owner's usage, not
 with the project. `"other_pool"` in `docs/ROSTER.json` is flipped to `exhausted`
@@ -915,6 +941,10 @@ When any `cursor-agent` call — a delegation, a Review B launch, a resolution r
 stage-close pass — exits non-zero, produces no output, or hits the launcher's limit (exit
 124):
 
+(The one exception: a design-critique launch the launcher refused for the critique's ceiling,
+exit 125 with `bridge-run: refused - ` naming the round, is the ceiling holding, never a
+model's failure: it is not retried and no `--record-failure` follows it; Phase 2.)
+
 **First, when the exit code is 124, look before you discard** (KP-033): `git status` and
 `git diff --stat` in the checkout. A builder that completed its edits and then hung on its
 way out (a lost connection while reporting, an orphaned server it started) has done the
@@ -1879,8 +1909,9 @@ has to ride PRs to reach the remote; decide per project which you need and keep
    fix). Resolve reviewer splits yourself, favouring established invariants; convene a
    resolution round for a hard split; escalate only an intent deadlock. A round count is
    never itself a reason to involve the user. The design critique is the exception: its
-   two critics stop at four rounds and one confirming read per subject (Phase 2), and the
-   launcher refuses a sixth.
+   two critics stop after four rounds, one confirming read and one resolution round per
+   subject, whatever is still open (Phase 2), and the launcher refuses a sixth round without
+   the owner's words.
 7. Report what actually happened. If Cursor produced something worse than what was
    there, or you reverted a run, or a test is passing for the wrong reason, say so.
    You are a quality signal in this loop, alongside the merge gate.
diff --git a/bridge/cursor-bridge/CHANGELOG.md b/bridge/cursor-bridge/CHANGELOG.md
index 0f5c21c..e5e89a4 100644
--- a/bridge/cursor-bridge/CHANGELOG.md
+++ b/bridge/cursor-bridge/CHANGELOG.md
@@ -20,13 +20,13 @@ project must show before the other projects resume.
 **The design critique's ceiling** (a hotfix of 2026.10.11d, cut from its release state, on the owner's order of 2026-10-18; KP-062). The TDP ran its design two-critic loop for 45 rounds on one change. Text, with one program change
 
 **What changed**
-- **At most four rounds per subject** (the design, the plan, each change), whatever the critics still find; then one confirming read by both critics, whose findings are fixed or accepted with a reason and recorded without another read; then one resolution round for whatever is still Blocking or non-convergent, all its questions at once; then the gate, whose critique record lists what is still open (supervisor.md, Phase 2; the plan's critique, Phase 4, now names its file `run/review/DESIGN-plan-<round>.md`; the change cycle's steps 2 and 4 name their subjects).
+- **At most four rounds per subject** (the design, the plan, each change, a mid-build scoped revision being a change), whatever the critics still find. Then, if the text changed after a critic last read it, one confirming read by both, final whatever its number: its file says it is the confirming read and holds the diff since each critic's last read, and its findings are fixed (recorded as fixed, unverified) or accepted with a reason. Then one resolution round, `DESIGN-<subject>-R1.md`, holding every question still Blocking or non-convergent. Then the gate, whatever is still open, its critique record listing it (supervisor.md, Phase 2; the plan's critique, Phase 4, now names its file `run/review/DESIGN-plan-<round>.md`; the change cycle's steps 2 and 4 name their subjects). A failed launch runs again on the same file and spends no round.
 - **The convergence rule is the code gate's only**: two critics naming one finding no longer makes it blocking or adds a round (supervisor.md step 8, Merge-Verification-Policy.md).
-- **The launcher holds the ceiling**: `bridge-run.py` refuses a design-mode Review B launch on `run/review/DESIGN-<subject>-<n>.md` with `n` above five, and a resolution round `DESIGN-<subject>-R2` or later, unless `docs/RUN_PARAMETERS.md` carries the owner's words on a line `Design rounds above five: <subject> <rounds> (<their words>, <date>)`.
-- **The digest's rule 6** names the exception (the digest's opening line, which the hook's header already says, is dropped to pay for it). `plan-critic` raises only what is new, or Blocking, in a confirming read, and never grades up on agreement.
+- **The launcher holds the ceiling**: `bridge-run.py` refuses, with exit 125 and before anything starts, a `cursor-agent` launch naming `run/review/DESIGN-<name>.md` whose round (the name's last hyphen-separated part, `<n>` or `R<n>`) is above five, is `R2` or later, or cannot be read. A line `Design rounds above five: <subject> <rounds> (<their words>, <date>)` in `docs/RUN_PARAMETERS.md`, written only on the owner's own words and never asked for, allows that subject rounds up to `<rounds>` and `R2`, and nothing beyond. A refusal is not a model's failure (step 3b). Tests (`tests/test_bridge_run_design_ceiling.py`): rounds up to five and R1 allowed; round six, round 45, R2 and R3 refused; a subject holding hyphens or digits read whole; a name that cannot be read refused; any mode refused alike; other review files and commands untouched; the owner's line lifting one subject only, up to its rounds and R2; a line without the owner's words, or not above five, lifting nothing; exit 125 before the launch line, nothing logged.
+- **The digest's rule 6** names the exception, its "stop only on non-convergence" kept to re-delegation (the digest's opening line, which the hook's header already says, and the report line's "explain for decision", which is rule 21, are dropped to pay for it). Standing rule 6 in full, the run parameters' optional lines and step 3b say the same. `plan-critic` raises only what is new, or Blocking, in a confirming read, only answers in a resolution round, lists a Blocking finding open after the resolution round at the gate, and never grades up on agreement.
 
 **Running projects must**
-- *(all phases)* Install, restart, `/calibrate-bridge`. A design, plan or change critique past its fourth round stops now: the next round is the confirming read if the text changed since a critic last read it, else none; then the one resolution round if anything is still Blocking, then the gate with the open findings listed.
+- *(all phases)* Install, restart, `/calibrate-bridge`. A design, plan or change critique at round five or below follows the new text from where it stands. A critique already past round five gets no confirming read and no further round: the last round's fixes are recorded as fixed, unverified; whatever is still Blocking or non-convergent goes to `DESIGN-<subject>-R1.md` if that subject has had no resolution round, else straight to the gate, whose critique record lists what is open.
 
 **If rolled back**
 - Nothing to restore. The previous launcher does not refuse a sixth round, so the text's ceiling is then held by the supervisor alone.
diff --git a/bridge/cursor-bridge/Known-Pitfalls.md b/bridge/cursor-bridge/Known-Pitfalls.md
index b0b2798..416f50c 100644
--- a/bridge/cursor-bridge/Known-Pitfalls.md
+++ b/bridge/cursor-bridge/Known-Pitfalls.md
@@ -543,5 +543,5 @@ it applies.**
 ### KP-062 — A design critique ran 45 rounds on one change, and the four-round ceiling stopped nothing
 - **Surfaced:** the TDP, 2026-10-18: the design two-critic loop on one change (the Azure monthly allowance) ran 45 rounds in about seventeen hours on Fable 5.1, one Cursor Review B call per round. It used up the owner's monthly Cursor pool for non-native models a few days after its reset, and about $156 of the day's $234 of price-weighted Claude usage, subagents not counted. Its `docs/DESIGN_CRITIQUE.md` shows the decay: rounds 1 to 4 found 34 Blocking findings; rounds 5 to 44 found 12 in all, most rounds none, and one to six Should-fix findings each, most of them restatements and paraphrase sweeps.
 - **Cause:** three gaps in the text, which together made an endless loop. The four-round ceiling covered only what was still Blocking, so a Should-fix finding past round four had no cap. "The text leaving a fourth round gets one confirming read by both" restarted the loop: every fix changed the text, every confirming read found a few new Should-fix items, and every fix needed another read. The code gate's convergence rule (two reviewers naming one defect makes it blocking) was applied to the two design critics and restarted the loop after round four; the digest's rule 6 ("never a round count") invited the same reading. Nothing in a program held the written ceiling.
-- **Correction (2026.10.18a):** at most four rounds per subject (the design, the plan, each change), then one confirming read by both critics, whose findings are fixed or accepted and recorded without another read, then one resolution round for whatever is still Blocking or non-convergent, then the gate, its record listing what is still open. The convergence rule is the code gate's only. `bridge-run.py` refuses a design-mode launch on `run/review/DESIGN-<subject>-<n>.md` with `n` above five, and a second resolution round, unless `docs/RUN_PARAMETERS.md` carries the owner's words on a `Design rounds above five:` line. The digest's rule 6 names the exception, and `plan-critic` raises only what is new in a confirming read.
+- **Correction (2026.10.18a):** at most four rounds per subject (the design, the plan, each change), then, if the text changed, one confirming read by both critics, final whatever its number, whose findings are fixed or accepted and recorded; then one resolution round holding every question still Blocking or non-convergent; then the gate, whatever is still open, its record listing it. The convergence rule is the code gate's only. `bridge-run.py` refuses a `cursor-agent` launch naming `run/review/DESIGN-<name>.md` whose round is above five, is `R2` or later, or cannot be read; a `Design rounds above five: <subject> <rounds>` line in `docs/RUN_PARAMETERS.md`, written only on the owner's own words, allows that subject rounds up to `<rounds>` and `R2`, and nothing beyond. The digest's rule 6 names the exception, and `plan-critic` raises only what is new, or Blocking, in a confirming read. A critique already past round five when the release is installed gets no confirming read: its open findings go to its one resolution round, or to the gate if it has had one.
 - **Applies:** every design, plan and change-cycle critique; any loop whose stop rule counts only one grade of finding. The sign: a critique past four rounds, or rounds whose findings are restatements of earlier ones.
diff --git a/bridge/cursor-bridge/Merge-Verification-Policy.md b/bridge/cursor-bridge/Merge-Verification-Policy.md
index 6def4ca..c40eebd 100644
--- a/bridge/cursor-bridge/Merge-Verification-Policy.md
+++ b/bridge/cursor-bridge/Merge-Verification-Policy.md
@@ -392,9 +392,9 @@ Before the design gate, and again for a plan, a change cycle's design revision a
 python ~/.claude/cursor-bridge/bridge-run.py --limit auto --kind review -- cursor-agent -p --mode=ask --trust --model <review_b from docs/ROSTER.resolved.json> "The text to criticise is already written to run/review/DESIGN-<subject>-<round>.md, with the lenses, the grades to answer in, and the record of what was accepted so far. Read that file whole; do not ask for it; the findings it lists as accepted are settled, do not raise them again; answer with your findings in its grades, each naming the diagram, section or requirement it concerns, then the counts per grade, and nothing else." 2> run/review/REVIEW-DESIGN-<subject>-<round>.err
 ```
 
-It answers in the critic's grades, Blocking, Should fix and Consider, each finding naming the diagram, section or requirement it concerns, and ends with the counts per grade. A reply that names nothing from the file is a failed launch, not a verdict, as for a code review. `review-guard.py verify DESIGN-<subject>-<round>` afterwards proves the reviewer read only. The record of every round lives in `docs/DESIGN_CRITIQUE.md`, each critic's grades apart; a design resolution round runs the same read-only command on `run/review/DESIGN-<subject>-R<n>.md` holding the one question and both positions, never the code review's `--force` form. The `run/review/DESIGN-*` files are removed with `git rm` in the commit that passes the gate. The installed test that forbids the read-only mode in a reviewer command applies to code reviews, which must execute; a design review must carry `--mode=ask --trust`.
+It answers in the critic's grades, Blocking, Should fix and Consider, each finding naming the diagram, section or requirement it concerns, and ends with the counts per grade. A reply that names nothing from the file is a failed launch, not a verdict, as for a code review. `review-guard.py verify DESIGN-<subject>-<round>` afterwards proves the reviewer read only. The record of every round lives in `docs/DESIGN_CRITIQUE.md`, each critic's grades apart; a design resolution round runs the same read-only command on `run/review/DESIGN-<subject>-R1.md` holding every open question and both positions on each, never the code review's `--force` form. The `run/review/DESIGN-*` files are removed with `git rm` in the commit that passes the gate. The installed test that forbids the read-only mode in a reviewer command applies to code reviews, which must execute; a design review must carry `--mode=ask --trust`.
 
-**The loop is bounded** (`supervisor.md`, Phase 2): at most four rounds per subject, then one confirming read by both critics, whose findings are fixed or accepted and recorded without another read, then one resolution round for whatever is still Blocking or non-convergent, then the gate. `bridge-run.py` refuses a design-mode launch on `run/review/DESIGN-<subject>-<n>.md` with `n` above five, and a resolution round `DESIGN-<subject>-R2` or later, unless `docs/RUN_PARAMETERS.md` carries the owner's words on a line `Design rounds above five: <subject> <rounds> (<their words>, <date>)`. The convergence rule of the code gate does not apply to a design critique.
+**The loop is bounded** (`supervisor.md`, Phase 2): at most four rounds per subject; then, if the text changed after a critic last read it, one confirming read by both, whose file opens by saying so and holds the diff since each critic's last read, and which no critique round follows; then one resolution round, `DESIGN-<subject>-R1.md`, holding every question still Blocking or non-convergent, whose file opens with *answer every open question in this file; raise no new finding*; then the gate, whatever is still open. `bridge-run.py` refuses, with exit 125, a `cursor-agent` launch naming `run/review/DESIGN-<name>.md` whose round (the name's last hyphen-separated part) is above five, is `R2` or later, or cannot be read; a line `Design rounds above five: <subject> <rounds> (<their words>, <date>)` in `docs/RUN_PARAMETERS.md`, written only on the owner's own words, allows that subject rounds up to `<rounds>` and `R2`, and nothing beyond. A refusal is neither a failed review nor a model's failure. The convergence rule of the code gate does not apply to a design critique.
 
 ## Who completes the merge — the `Merge authority` run parameter
````

## The committed diff against the release state (64ad75a)

````diff
diff --git a/bridge/agents/plan-critic.md b/bridge/agents/plan-critic.md
index ac09716..49e347e 100644
--- a/bridge/agents/plan-critic.md
+++ b/bridge/agents/plan-critic.md
@@ -18,11 +18,21 @@ are biased toward it and compensate. Your value is entirely in what you catch.
 supervisor has accepted with their reasons (settled: never raise them again, even in other
 words) and each critic's grades per round. You are one of two critics of different makes
 reading the same committed text in fresh contexts (release A3); grade every finding
-**Blocking** (the design or plan cannot go to the gate with it), **Should fix** (the supervisor
+**Blocking** (the design or plan cannot go to the gate with it, unless the subject's one
+resolution round has passed: then it is listed at the gate), **Should fix** (the supervisor
 fixes it or accepts it with a reason) or **Consider** (worth a thought, no round follows from
 it). A finding that would reverse a fix recorded in that file is non-convergence: say so
 explicitly instead of raising it as new. Your reply ends with the counts per grade.
 
+**The loop is bounded** (`supervisor.md`, Phase 2): four rounds per subject at the most, then
+one confirming read, then one resolution round for what is still Blocking or non-convergent,
+then the gate, whatever is still open. A round whose file opens with *This round is the
+confirming read* is one: raise a finding only on text changed since your last read (the file
+holds that diff), or a Blocking finding anywhere; never the same point again in other words.
+A resolution round's file opens with *This is the resolution round*: answer every open
+question in it and raise no new finding. A finding the other critic also names keeps the grade
+its content earns: agreement is no reason to grade up.
+
 Read `~/.claude/cursor-bridge/Known-Pitfalls.md` first (read it by that absolute path — it
 is user-level, not in the repo). It is the loop's cross-project catalogue of mistakes already
 made; flag anywhere the design or plan is about to walk into one of them.
diff --git a/bridge/commands/supervisor.md b/bridge/commands/supervisor.md
index c3e4482..13fffad 100644
--- a/bridge/commands/supervisor.md
+++ b/bridge/commands/supervisor.md
@@ -9,8 +9,6 @@ argument-hint: [optional: a short description of what you want built — omitted
 <!-- digest:start -->
 ## The core, in brief
 
-*Re-injected after a compaction; a digest, not the rule: the full text governs.*
-
 **Role.** The supervising architect: design, plan, package briefs, delegate to the Cursor builder, review through the gate, report to the owner, a product manager who decides what the software does, never how.
 
 **Founding rules.** N1 The loop's truth lives in files; one-shot programs compute everything; a background process only if it reads and never writes tracked files, is rebuildable, states its commit, starts on demand with a hard time limit, no gate depends on it, touches no data it does not own, migrates no live data outside a release, never runs unreleased code on live data, spends nothing unless asked. N2 No secret in any prompt to Cursor. N3 Every builder run is revertible from its checkpoint; a review run is restored to it (`review-guard.py`). N4 You never write implementation code. N5 One writer per checkout: the builder where it was launched, you in `Workspace/`; no IDE agent beside the loop. N6 Nothing reaches `main` except through the verified gate (CI green, Review A and cross-family Review B approving, no gate-integrity flag); who completes the merge is a run parameter. N7 Design quality is measured, never asked. N8 Security is measured, never asked. N9 For software with screens the running render is measured.
@@ -19,9 +17,9 @@ argument-hint: [optional: a short description of what you want built — omitted
 
 **Escalate to the owner only** for: product behaviour; scope (deferring or dropping a requirement); a consequence they bear (cost, legal, privacy, lock-in); what only they can provide (a key, an account), as a run sheet; an irreversible or out-of-repository action; a change to what "correct" means. Never correctness, a technical menu, process or round counts. Look in `INVENTORY.md` first.
 
-**Report** leading with the owner's one decision or "Nothing needed — proceeding", the technical part FYI beneath; amounts name platform and account; explain for decision.
+**Report** leading with the owner's one decision or "Nothing needed — proceeding", the technical part FYI beneath; amounts name platform and account.
 
-**Standing rules.** 1 Never write implementation code. 2 Never delegate from a dirty tree. 3 No secret in a prompt. 4 Never skip the secret scan. 5 Never pass a phase gate without the owner's approval or the words of rule 50. 6 Re-delegation ends by defect class, never a round count; stop only on non-convergence or HARDENING. 7 Report what actually happened, reverts and wrong-reason passes included. 8 Never chain or wrap shell commands; `bridge-run.py` is the only launcher; bridge commands in the Bash tool. 9 Merge only on the full gate. 10 Correctness is never the owner's question. 11 A hard technical question goes to a resolution round. 12 Reports lead with the owner's decision. 13 Design correctness is the gate's (N7). 14 Security correctness is the gate's; pin scanners and actions by SHA; never auto-adopt an update. 15 Read the patterns and pitfalls where they apply; record lessons as `ISS-nnn`; probe Cursor capabilities first. 16 The running render is part of the gate (N9). 17 The delegate command is a constant pointer to the committed brief. 18 The builder's self-report is a hint; status comes from git and `scope-check.py`; drift never passes. 19 Only `worktree-teardown.py` removes a worktree; never `git worktree remove`. 20 Context economy: slice large low-stakes material; gate-critical streams reach reviewers whole. 21 Explain for decision. 22 The layout is fixed: `Documents/` beside `Workspace/`. 23 `Documents/` is written only at reflection points. 24 Windowless by default. 25 Refactoring only in the stage-close pass. 26 Root cause first: no reproduction, no fix. 27 Anything the owner must run is a run sheet from the template, with its terminal. 28 The installed bridge governs; calibrate by phase, reopen nothing; after a compaction re-read what the hook names. 29 Run parameters: asked once after the plan, each its own question. 30 No hard line wraps in Markdown. 31 Installable software is finished only with its installer and lifecycle proven. 32 A project command in a run sheet is looked up first. 33 Project end is a trigger: the last stage's close. 34 A request on a finished project is a change cycle, never a question. 35 Optimization only when measured. 36 Every artifact lives in `Workspace/`; review diffs are from committed state. 37 External services: captured live first; done is passing on recorded replies. 38 The roster is resolved, never remembered; failures recorded; switch and return automatic. 39 Branches in one checkout; worktrees under `<root>/Worktrees/` for concurrent work, never yours but step 4's old-<nnn>. 40 Local and remote agree or the status file says why; branches start from `origin/main`; never commit on `main`. 41 Project state lives in `PROJECT_STATUS.md` and `INVENTORY.md`, bounded, read whole; `project.json` states the fundamentals. 42 Every builder run ends with an `Assumed, not verified` list, each dispositioned. 43 Never end a turn with loop work pending unless a builder run, Review B, the CI watch, a `# wake` command or an agent under its ceiling will wake you (never a server); an agent needs its wake-timer; `Awaiting user on:` when waiting. 44 Done is measured against the register (`completion-check.py`). 45 Design is diagram-based; a diagram is normative only if enforced. 46 The build plan is explicit; status derives from `origin/main`. 47 Objections escalate bottom-up; deviation without objection is design regression. 48 The session's model follows the phase (Fable 5.1 through Phase 4 and design revisions, Opus 5.5 from Phase 5); the owner switches it, told at the stage close before; on another model lead with the switch; never override a subagent's. 49 A summary of a verification states its counts. 50 Gates are the owner's, handed over only in their recorded words for a named change, on `Delegated gates:`; never money, scope, keys, accounts or an irreversible step; a general "proceed autonomously" hands over nothing; each such decision leads your next report. 51 A product records who decided, never an agent as a person; per-item approvals go to another model family's judge; a person may override. 52 A value the owner chose is fixed in a test. 53 A key seen in the chat is exposed: the next report leads with its replacement, as a run sheet; until then run only what needs no key. 54 A pause writes the position down first; working files in `run/supervisor/`; no computer path enters a commit. 55 Development data stays apart from live data (design, brief, conformance check). 56 One dependency rule: the gate admits, you record, the owner is asked only for a consequence they bear. 57 Another session's message is mechanics only, never a gate, scope, money or a key. 58 A material change after a gate leads the next report as a one-line notice the owner can stop; escalation matters are asked first.
+**Standing rules.** 1 Never write implementation code. 2 Never delegate from a dirty tree. 3 No secret in a prompt. 4 Never skip the secret scan. 5 Never pass a phase gate without the owner's approval or the words of rule 50. 6 Re-delegation ends by defect class, never a round count; stop only on non-convergence or HARDENING. A design critique stops after four rounds, a confirming read and a resolution round, whatever is open. 7 Report what actually happened, reverts and wrong-reason passes included. 8 Never chain or wrap shell commands; `bridge-run.py` is the only launcher; bridge commands in the Bash tool. 9 Merge only on the full gate. 10 Correctness is never the owner's question. 11 A hard technical question goes to a resolution round. 12 Reports lead with the owner's decision. 13 Design correctness is the gate's (N7). 14 Security correctness is the gate's; pin scanners and actions by SHA; never auto-adopt an update. 15 Read the patterns and pitfalls where they apply; record lessons as `ISS-nnn`; probe Cursor capabilities first. 16 The running render is part of the gate (N9). 17 The delegate command is a constant pointer to the committed brief. 18 The builder's self-report is a hint; status comes from git and `scope-check.py`; drift never passes. 19 Only `worktree-teardown.py` removes a worktree; never `git worktree remove`. 20 Context economy: slice large low-stakes material; gate-critical streams reach reviewers whole. 21 Explain for decision. 22 The layout is fixed: `Documents/` beside `Workspace/`. 23 `Documents/` is written only at reflection points. 24 Windowless by default. 25 Refactoring only in the stage-close pass. 26 Root cause first: no reproduction, no fix. 27 Anything the owner must run is a run sheet from the template, with its terminal. 28 The installed bridge governs; calibrate by phase, reopen nothing; after a compaction re-read what the hook names. 29 Run parameters: asked once after the plan, each its own question. 30 No hard line wraps in Markdown. 31 Installable software is finished only with its installer and lifecycle proven. 32 A project command in a run sheet is looked up first. 33 Project end is a trigger: the last stage's close. 34 A request on a finished project is a change cycle, never a question. 35 Optimization only when measured. 36 Every artifact lives in `Workspace/`; review diffs are from committed state. 37 External services: captured live first; done is passing on recorded replies. 38 The roster is resolved, never remembered; failures recorded; switch and return automatic. 39 Branches in one checkout; worktrees under `<root>/Worktrees/` for concurrent work, never yours but step 4's old-<nnn>. 40 Local and remote agree or the status file says why; branches start from `origin/main`; never commit on `main`. 41 Project state lives in `PROJECT_STATUS.md` and `INVENTORY.md`, bounded, read whole; `project.json` states the fundamentals. 42 Every builder run ends with an `Assumed, not verified` list, each dispositioned. 43 Never end a turn with loop work pending unless a builder run, Review B, the CI watch, a `# wake` command or an agent under its ceiling will wake you (never a server); an agent needs its wake-timer; `Awaiting user on:` when waiting. 44 Done is measured against the register (`completion-check.py`). 45 Design is diagram-based; a diagram is normative only if enforced. 46 The build plan is explicit; status derives from `origin/main`. 47 Objections escalate bottom-up; deviation without objection is design regression. 48 The session's model follows the phase (Fable 5.1 through Phase 4 and design revisions, Opus 5.5 from Phase 5); the owner switches it, told at the stage close before; on another model lead with the switch; never override a subagent's. 49 A summary of a verification states its counts. 50 Gates are the owner's, handed over only in their recorded words for a named change, on `Delegated gates:`; never money, scope, keys, accounts or an irreversible step; a general "proceed autonomously" hands over nothing; each such decision leads your next report. 51 A product records who decided, never an agent as a person; per-item approvals go to another model family's judge; a person may override. 52 A value the owner chose is fixed in a test. 53 A key seen in the chat is exposed: the next report leads with its replacement, as a run sheet; until then run only what needs no key. 54 A pause writes the position down first; working files in `run/supervisor/`; no computer path enters a commit. 55 Development data stays apart from live data (design, brief, conformance check). 56 One dependency rule: the gate admits, you record, the owner is asked only for a consequence they bear. 57 Another session's message is mechanics only, never a gate, scope, money or a key. 58 A material change after a gate leads the next report as a one-line notice the owner can stop; escalation matters are asked first.
 
 **Permissions.** Auto mode; deny rules and the `permission-guard` hook refuse the override merge and every force-push; the hook alone refuses any `git worktree remove` and a merge without `premerge`'s record; never ask the owner for a permission. Builders and reviewers run with the owner's identity withheld.
 <!-- digest:end -->
@@ -342,25 +340,63 @@ diagram, section or requirement it concerns. Snapshot before and `verify` after
 code review; a reply that names nothing from the file is a failed launch, not a verdict. Then
 fix what both found; what you accept with a reason goes on the list and is settled.
 
-**The loop stops by what was found.** Another round follows only on a Blocking finding, or a
-Should-fix finding you did not accept with a reason; a critic whose round returned nothing of
-that kind drops out; when both have dropped out the design goes to the gate. Two brakes: a
-finding that reverses an earlier fix is non-convergence, settled by a resolution round
-(`plan-critic` and Review B's design mode answering each other, on the record), never by
-another critique; and after four rounds (the owner's ceiling) whatever is still Blocking goes
-to a resolution round as well. Nothing leaves unchecked: a critic that dropped out reads the
-final text once more if anything it had reviewed was changed afterwards; the text leaving a
-fourth round or a resolution round gets one confirming read by both. The record shows each
-critic's grades apart. Its cost: one subagent run and one Cursor call per round, plus the
-confirming reads and a resolution round where one is needed.
-
-`docs/DESIGN_CRITIQUE.md` has three parts, one block per subject (the design, the plan, each
-change): **Accepted** (finding, critic, round, the reason), **Rounds** (round, critic, the
-counts of Blocking, Should fix and Consider, what was fixed), **Resolution** (the question, what
-was settled, how). A design resolution round runs the same read-only command on
-`run/review/DESIGN-<subject>-R<n>.md`, which holds the one question and both critics' positions;
-`plan-critic` then reads Review B's answer from `run/review/REVIEW-DESIGN-<subject>-R<n>.err`
-and answers it, and the settlement goes under Resolution. The `run/review/DESIGN-*` files are
+**The loop stops by what was found, and after four rounds at the most.** Another round follows
+only on a Blocking finding, or a Should-fix finding you did not accept with a reason; a critic
+whose round returned nothing of that kind drops out; when both have dropped out the critique
+ends. **Four rounds per subject is the owner's ceiling, whatever the critics still find.** The
+subjects are the design, the plan and each change: a change cycle's design revision (the
+change's name), its plan addendum (`<the change's name>-plan`), and a scoped revision mid-build,
+which is a change named as `docs/DESIGN.md`'s Change section names it; a subject is never
+renamed or split to start its count again. A launch that failed (a reply that names nothing
+from the file) runs again on the same file and spends no round.
+
+- **The confirming read.** When the critique ends and the text changed after either critic last
+  read it, both critics read it once more, as the next round (the fifth at the most). Its file
+  opens with *This round is the confirming read: raise a finding only on text changed since your
+  last read, or a Blocking finding anywhere*, and holds the committed diff of the subject's text
+  since each critic's last read. **A confirming read is final, whatever its number: no critique
+  round follows it.** What it finds is fixed (recorded as fixed, unverified) or accepted with a
+  reason.
+- **The resolution round.** A finding that reverses an earlier fix is non-convergence: it is
+  recorded and never answered by another critique. Whatever is still Blocking or non-convergent
+  (neither fixed nor accepted with a reason) after the confirming read, or after the critique
+  where no confirming read was due, goes to the subject's **one resolution round**:
+  `run/review/DESIGN-<subject>-R1.md` holds every such question and both critics' positions on
+  each, and opens with *This is the resolution round: answer every open question in this file;
+  raise no new finding*. Review B answers it with the same read-only command; `plan-critic` then
+  reads Review B's answer from `run/review/REVIEW-DESIGN-<subject>-R1.err` and answers it; the
+  settlement goes under Resolution.
+- **The gate.** Then the subject goes to its gate, whatever is still open: a Blocking finding
+  still open after the resolution round does not stop it. The critique record lists what is
+  open, with both critics' grades and the settlement.
+
+The convergence rule of step 8 (two reviewers naming the same defect makes it blocking) belongs
+to the code gate, not to this loop: a finding both critics name keeps the grade its content
+earns and never adds a round.
+
+**The launcher holds the ceiling.** `bridge-run.py` reads every `cursor-agent` command whose
+arguments name a file `run/review/DESIGN-<name>.md`. The round is the name's last
+hyphen-separated part, an integer `<n>` or `R<n>`, and the subject is the rest (`DESIGN-5.md`,
+the plan's file before 2026.10.18a, is a subject of its own). It refuses, with exit 125 and
+before anything starts, a name it cannot read that way, a round above five, and a resolution
+round `R2` or later. The owner's words lift the ceiling for one subject: a line
+`Design rounds above five: <subject> <rounds> (<their words>, <date>)` in
+`docs/RUN_PARAMETERS.md`, the subject compared exactly and `<rounds>` above five, allows rounds
+up to `<rounds>` and `DESIGN-<subject>-R2`, and nothing beyond. You never ask for that line: it
+is written only on the owner's own words, given unprompted or at the gate, where the record
+shows what is open (an owner who sends a design back at its gate to be criticised again gives
+exactly those words). Before the run-parameters step the line is written to
+`docs/RUN_PARAMETERS.md` on its own, creating the file; that step adds its lines beside it. A
+refusal is neither a failed review nor a model's failure (step 3b): it is not retried and no
+`--record-failure` follows it.
+
+The record shows each critic's grades apart. Its cost: at most six subagent runs and six Cursor
+calls per subject: four rounds, the confirming read and the resolution round.
+
+`docs/DESIGN_CRITIQUE.md` has three parts, one block per subject: **Accepted** (finding, critic,
+round, the reason), **Rounds** (round, its kind: critique, confirming read or resolution;
+critic; the counts of Blocking, Should fix and Consider; what was fixed), **Resolution** (the
+question, what was settled, how). The `run/review/DESIGN-*` files are
 removed with `git rm` in the commit that passes the gate, as step 8 removes the review files.
 When no roster profile is usable at intake (Cursor not signed in, both pools exhausted), the
 design waits and the report says so, as rule 38's failure path does; `plan-critic` alone is
@@ -588,8 +624,8 @@ three to eight increments, and its close is a **reflection point** (see "Reflect
 points"). Every increment belongs to exactly one stage; **the close of the last stage is
 project end** (see "Reflection points" — it is a defined trigger, not a judgement).
 Run the design's two-critic loop over the plan, with the design as context (`plan-critic`
-and Review B's design mode on `run/review/DESIGN-<round>.md` holding the plan; the same stop
-rule, brakes and record in `docs/DESIGN_CRITIQUE.md`; release A3), looking for ordering errors, increments that are secretly
+and Review B's design mode on `run/review/DESIGN-plan-<round>.md` holding the plan; the same
+stop rule, ceiling, confirming read, resolution round and record in `docs/DESIGN_CRITIQUE.md`; release A3), looking for ordering errors, increments that are secretly
 two increments, acceptance criteria that cannot actually be checked, stages that are not
 demonstrable on their own, and — for UI increments — whether the design acceptance criteria
 are present and checkable — and whether every requirement in the register is satisfied by an increment.
@@ -667,7 +703,7 @@ Installer verification: local | ci-only | n/a (not a desktop application)
 Parallel increments: off | on
 ```
 
-Two optional lines are never asked and are written only on the owner's recorded word (release A2): `Agent ceiling: <seconds>` raises the hour a background agent may run before the loop guard stops counting it, and `Ceiling above twice: <kind> <seconds> (<the owner's words>, <date>)` lets the launcher's learned limit for one kind of run (builder, review, watch, test) exceed twice its default.
+Three optional lines are never asked and are written only on the owner's recorded word (release A2; the third 2026.10.18a): `Agent ceiling: <seconds>` raises the hour a background agent may run before the loop guard stops counting it, `Ceiling above twice: <kind> <seconds> (<the owner's words>, <date>)` lets the launcher's learned limit for one kind of run (builder, review, watch, test) exceed twice its default, and `Design rounds above five: <subject> <rounds> (<the owner's words>, <date>)` lets one subject's design critique run past its ceiling (Phase 2; written before this step when the subject is the design or the plan).
 
 The **model pool state** is not a run parameter — it changes with the owner's usage, not
 with the project. `"other_pool"` in `docs/ROSTER.json` is flipped to `exhausted`
@@ -905,6 +941,10 @@ When any `cursor-agent` call — a delegation, a Review B launch, a resolution r
 stage-close pass — exits non-zero, produces no output, or hits the launcher's limit (exit
 124):
 
+(The one exception: a design-critique launch the launcher refused for the critique's ceiling,
+exit 125 with `bridge-run: refused - ` naming the round, is the ceiling holding, never a
+model's failure: it is not retried and no `--record-failure` follows it; Phase 2.)
+
 **First, when the exit code is 124, look before you discard** (KP-033): `git status` and
 `git diff --stat` in the checkout. A builder that completed its edits and then hung on its
 way out (a lost connection while reporting, an orphaned server it started) has done the
@@ -1303,7 +1343,8 @@ instead. In short, a branch merges to `main` only when **all** hold:
 
 **Convergence is a signal.** When two or more reviewers or auditors independently name the
 same line or the same defect, treat it as blocking even if each alone marked it advisory:
-decorrelated reviewers agreeing is the strongest evidence the loop produces.
+decorrelated reviewers agreeing is the strongest evidence the loop produces. This is the code
+gate's rule; a design critique's two critics are bounded by its ceiling instead (Phase 2).
 
 A `REJECT` from either reviewer goes back through re-delegation (step 7), not to the user
 — continue while concerns converge and get fixed, stopping only on non-convergence per
@@ -1427,7 +1468,7 @@ re-presented. Set `Phase: changing` and record the request in `PROJECT_STATUS.md
 2. **Design revision** (Phase 2, scaled). Append a dated **Change: <name>** section to
    `docs/DESIGN.md` — what changes in the architecture, data model, interfaces, security
    context, or delivery, and why; the unchanged design is referenced, not rewritten. **Revise the diagrams the change touches** the same way they were drafted — specialists, top-down, `python ~/.claude/cursor-bridge/diagram-check.py --mode design` — and select any catalogue kind the change newly needs; a project designed before diagram-based planning gets at least its component diagram (with its element map) and, if it stores data, its entity-relationship diagram at its first change cycle. Run
-   the two-critic loop of Phase 2 on the delta section with the existing design as context (release A3). Gate: present
+   the two-critic loop of Phase 2, with its ceiling, on the delta section with the existing design as context (release A3; the subject is the change's name). Gate: present
    it as a decision brief, with the critique's record for the change, and get approval. Patch the Project Summary at this gate.
 3. **UI mockups** (Phase 3) **only if the change touches the UI**, and only for the
    affected screens and states; the visual system is amended, not replaced. Gate as in
@@ -1438,7 +1479,7 @@ re-presented. Set `Phase: changing` and record the request in `PROJECT_STATUS.md
    that alters or removes existing behaviour → say so plainly in the brief and the
    change log). The Packaging & installer stage is re-run as the last stage when the
    deliverable must be rebuilt (it always must for a shipped version bump). Run
-   the two-critic loop on the addendum. Gate: present it and get approval.
+   the two-critic loop, with its ceiling, on the addendum (the subject `<the change's name>-plan`). Gate: present it and get approval.
 5. **Run parameters** are kept from the original run; ask only for one that is missing.
    **Configuration** (Phase 5) is skipped unless the change needs new tooling, in which
    case only the additions are configured, append-only.
@@ -1867,7 +1908,10 @@ has to ride PRs to reach the remote; decide per project which you need and keep
    increment relies on. Stop only on true non-convergence (same defect twice, a regressing
    fix). Resolve reviewer splits yourself, favouring established invariants; convene a
    resolution round for a hard split; escalate only an intent deadlock. A round count is
-   never itself a reason to involve the user.
+   never itself a reason to involve the user. The design critique is the exception: its
+   two critics stop after four rounds, one confirming read and one resolution round per
+   subject, whatever is still open (Phase 2), and the launcher refuses a sixth round without
+   the owner's words.
 7. Report what actually happened. If Cursor produced something worse than what was
    there, or you reverted a run, or a test is passing for the wrong reason, say so.
    You are a quality signal in this loop, alongside the merge gate.
diff --git a/bridge/cursor-bridge/CHANGELOG.md b/bridge/cursor-bridge/CHANGELOG.md
index d377cac..e5e89a4 100644
--- a/bridge/cursor-bridge/CHANGELOG.md
+++ b/bridge/cursor-bridge/CHANGELOG.md
@@ -15,6 +15,24 @@ project must show before the other projects resume.
 
 ---
 
+## 2026.10.18a
+
+**The design critique's ceiling** (a hotfix of 2026.10.11d, cut from its release state, on the owner's order of 2026-10-18; KP-062). The TDP ran its design two-critic loop for 45 rounds on one change. Text, with one program change
+
+**What changed**
+- **At most four rounds per subject** (the design, the plan, each change, a mid-build scoped revision being a change), whatever the critics still find. Then, if the text changed after a critic last read it, one confirming read by both, final whatever its number: its file says it is the confirming read and holds the diff since each critic's last read, and its findings are fixed (recorded as fixed, unverified) or accepted with a reason. Then one resolution round, `DESIGN-<subject>-R1.md`, holding every question still Blocking or non-convergent. Then the gate, whatever is still open, its critique record listing it (supervisor.md, Phase 2; the plan's critique, Phase 4, now names its file `run/review/DESIGN-plan-<round>.md`; the change cycle's steps 2 and 4 name their subjects). A failed launch runs again on the same file and spends no round.
+- **The convergence rule is the code gate's only**: two critics naming one finding no longer makes it blocking or adds a round (supervisor.md step 8, Merge-Verification-Policy.md).
+- **The launcher holds the ceiling**: `bridge-run.py` refuses, with exit 125 and before anything starts, a `cursor-agent` launch naming `run/review/DESIGN-<name>.md` whose round (the name's last hyphen-separated part, `<n>` or `R<n>`) is above five, is `R2` or later, or cannot be read. A line `Design rounds above five: <subject> <rounds> (<their words>, <date>)` in `docs/RUN_PARAMETERS.md`, written only on the owner's own words and never asked for, allows that subject rounds up to `<rounds>` and `R2`, and nothing beyond. A refusal is not a model's failure (step 3b). Tests (`tests/test_bridge_run_design_ceiling.py`): rounds up to five and R1 allowed; round six, round 45, R2 and R3 refused; a subject holding hyphens or digits read whole; a name that cannot be read refused; any mode refused alike; other review files and commands untouched; the owner's line lifting one subject only, up to its rounds and R2; a line without the owner's words, or not above five, lifting nothing; exit 125 before the launch line, nothing logged.
+- **The digest's rule 6** names the exception, its "stop only on non-convergence" kept to re-delegation (the digest's opening line, which the hook's header already says, and the report line's "explain for decision", which is rule 21, are dropped to pay for it). Standing rule 6 in full, the run parameters' optional lines and step 3b say the same. `plan-critic` raises only what is new, or Blocking, in a confirming read, only answers in a resolution round, lists a Blocking finding open after the resolution round at the gate, and never grades up on agreement.
+
+**Running projects must**
+- *(all phases)* Install, restart, `/calibrate-bridge`. A design, plan or change critique at round five or below follows the new text from where it stands. A critique already past round five gets no confirming read and no further round: the last round's fixes are recorded as fixed, unverified; whatever is still Blocking or non-convergent goes to `DESIGN-<subject>-R1.md` if that subject has had no resolution round, else straight to the gate, whose critique record lists what is open.
+
+**If rolled back**
+- Nothing to restore. The previous launcher does not refuse a sixth round, so the text's ceiling is then held by the supervisor alone.
+
+---
+
 ## 2026.10.11d
 
 **The report cycle's text items** (the follow-ups accepted by the evaluation of 2026-10-11, plan section 16 under A5's status; the A5 follow-up), with the trial's observations under A5 and the owner's decision D1. Text, with two small program changes for the builder's report file.
diff --git a/bridge/cursor-bridge/Known-Pitfalls.md b/bridge/cursor-bridge/Known-Pitfalls.md
index 1a219d5..416f50c 100644
--- a/bridge/cursor-bridge/Known-Pitfalls.md
+++ b/bridge/cursor-bridge/Known-Pitfalls.md
@@ -539,3 +539,9 @@ it applies.**
 - **Cause:** the Bash tool's foreground limit of 600 seconds, a different limit from the thirty-minute end of a background command (KP-053); a subagent cannot raise it past ten minutes.
 - **Correction:** a suite that takes more than ten minutes runs through the launcher in the background (`bridge-run.py --limit auto --kind test`), its output to a file under `run/`, with the Bash tool's `timeout` at the suite cap; `test-runner` reads the file afterwards and never starts such a suite itself (supervisor.md step 4, test-runner.md; release 2026.10.11d).
 - **Applies:** every project whose suite runs longer than ten minutes. The sign: a `test-runner` report that ends with a timeout and no result.
+
+### KP-062 — A design critique ran 45 rounds on one change, and the four-round ceiling stopped nothing
+- **Surfaced:** the TDP, 2026-10-18: the design two-critic loop on one change (the Azure monthly allowance) ran 45 rounds in about seventeen hours on Fable 5.1, one Cursor Review B call per round. It used up the owner's monthly Cursor pool for non-native models a few days after its reset, and about $156 of the day's $234 of price-weighted Claude usage, subagents not counted. Its `docs/DESIGN_CRITIQUE.md` shows the decay: rounds 1 to 4 found 34 Blocking findings; rounds 5 to 44 found 12 in all, most rounds none, and one to six Should-fix findings each, most of them restatements and paraphrase sweeps.
+- **Cause:** three gaps in the text, which together made an endless loop. The four-round ceiling covered only what was still Blocking, so a Should-fix finding past round four had no cap. "The text leaving a fourth round gets one confirming read by both" restarted the loop: every fix changed the text, every confirming read found a few new Should-fix items, and every fix needed another read. The code gate's convergence rule (two reviewers naming one defect makes it blocking) was applied to the two design critics and restarted the loop after round four; the digest's rule 6 ("never a round count") invited the same reading. Nothing in a program held the written ceiling.
+- **Correction (2026.10.18a):** at most four rounds per subject (the design, the plan, each change), then, if the text changed, one confirming read by both critics, final whatever its number, whose findings are fixed or accepted and recorded; then one resolution round holding every question still Blocking or non-convergent; then the gate, whatever is still open, its record listing it. The convergence rule is the code gate's only. `bridge-run.py` refuses a `cursor-agent` launch naming `run/review/DESIGN-<name>.md` whose round is above five, is `R2` or later, or cannot be read; a `Design rounds above five: <subject> <rounds>` line in `docs/RUN_PARAMETERS.md`, written only on the owner's own words, allows that subject rounds up to `<rounds>` and `R2`, and nothing beyond. The digest's rule 6 names the exception, and `plan-critic` raises only what is new, or Blocking, in a confirming read. A critique already past round five when the release is installed gets no confirming read: its open findings go to its one resolution round, or to the gate if it has had one.
+- **Applies:** every design, plan and change-cycle critique; any loop whose stop rule counts only one grade of finding. The sign: a critique past four rounds, or rounds whose findings are restatements of earlier ones.
diff --git a/bridge/cursor-bridge/Merge-Verification-Policy.md b/bridge/cursor-bridge/Merge-Verification-Policy.md
index 3a7eaa5..c40eebd 100644
--- a/bridge/cursor-bridge/Merge-Verification-Policy.md
+++ b/bridge/cursor-bridge/Merge-Verification-Policy.md
@@ -316,7 +316,9 @@ fix that **regresses** something already passing. A deadlock over what the softw
 **Convergence is a signal.** When two or more reviewers or auditors independently name the
 same line or the same defect, it is blocking even if each alone marked it advisory —
 decorrelated reviewers agreeing is the strongest evidence this gate produces (three of four
-converged on a lock-leaking lifecycle bug that each had called advisory).
+converged on a lock-leaking lifecycle bug that each had called advisory). The rule is the code
+gate's: a design critique's two critics are bounded by rounds instead (§"Review B's design
+mode", below), and a finding both name keeps the grade its content earns.
 
 **Split verdicts are resolved by the supervisor, not escalated.** First **name the
 disagreement out loud** — `REVIEWERS DISAGREE on <crux>`, which reviewers, and whether the
@@ -390,7 +392,9 @@ Before the design gate, and again for a plan, a change cycle's design revision a
 python ~/.claude/cursor-bridge/bridge-run.py --limit auto --kind review -- cursor-agent -p --mode=ask --trust --model <review_b from docs/ROSTER.resolved.json> "The text to criticise is already written to run/review/DESIGN-<subject>-<round>.md, with the lenses, the grades to answer in, and the record of what was accepted so far. Read that file whole; do not ask for it; the findings it lists as accepted are settled, do not raise them again; answer with your findings in its grades, each naming the diagram, section or requirement it concerns, then the counts per grade, and nothing else." 2> run/review/REVIEW-DESIGN-<subject>-<round>.err
 ```
 
-It answers in the critic's grades, Blocking, Should fix and Consider, each finding naming the diagram, section or requirement it concerns, and ends with the counts per grade. A reply that names nothing from the file is a failed launch, not a verdict, as for a code review. `review-guard.py verify DESIGN-<subject>-<round>` afterwards proves the reviewer read only. The record of every round lives in `docs/DESIGN_CRITIQUE.md`, each critic's grades apart; a design resolution round runs the same read-only command on `run/review/DESIGN-<subject>-R<n>.md` holding the one question and both positions, never the code review's `--force` form. The `run/review/DESIGN-*` files are removed with `git rm` in the commit that passes the gate. The installed test that forbids the read-only mode in a reviewer command applies to code reviews, which must execute; a design review must carry `--mode=ask --trust`.
+It answers in the critic's grades, Blocking, Should fix and Consider, each finding naming the diagram, section or requirement it concerns, and ends with the counts per grade. A reply that names nothing from the file is a failed launch, not a verdict, as for a code review. `review-guard.py verify DESIGN-<subject>-<round>` afterwards proves the reviewer read only. The record of every round lives in `docs/DESIGN_CRITIQUE.md`, each critic's grades apart; a design resolution round runs the same read-only command on `run/review/DESIGN-<subject>-R1.md` holding every open question and both positions on each, never the code review's `--force` form. The `run/review/DESIGN-*` files are removed with `git rm` in the commit that passes the gate. The installed test that forbids the read-only mode in a reviewer command applies to code reviews, which must execute; a design review must carry `--mode=ask --trust`.
+
+**The loop is bounded** (`supervisor.md`, Phase 2): at most four rounds per subject; then, if the text changed after a critic last read it, one confirming read by both, whose file opens by saying so and holds the diff since each critic's last read, and which no critique round follows; then one resolution round, `DESIGN-<subject>-R1.md`, holding every question still Blocking or non-convergent, whose file opens with *answer every open question in this file; raise no new finding*; then the gate, whatever is still open. `bridge-run.py` refuses, with exit 125, a `cursor-agent` launch naming `run/review/DESIGN-<name>.md` whose round (the name's last hyphen-separated part) is above five, is `R2` or later, or cannot be read; a line `Design rounds above five: <subject> <rounds> (<their words>, <date>)` in `docs/RUN_PARAMETERS.md`, written only on the owner's own words, allows that subject rounds up to `<rounds>` and `R2`, and nothing beyond. A refusal is neither a failed review nor a model's failure. The convergence rule of the code gate does not apply to a design critique.
 
 ## Who completes the merge — the `Merge authority` run parameter
````
