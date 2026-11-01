## Reflection points — stage close, phase gates, project end

### What must survive a compaction

After a compaction or a resume at a reflection point, read these before your next action:

- this module, whole, and at the close of the plan's last stage `project-end.md` too, whole (the session-start hook names both while the phase is `building` or `changing`);
- the last entries of `run/supervisor/in-flight.md`: the reflection point in hand and the items it has finished ("Keeping the position"), and, while the stage review's Review B runs, the position the delegation loop's step 8 keeps there;
- `docs/PROJECT_STATUS.md` and `docs/INVENTORY.md`, whole (rule 41): the `Stage:` line's `Last reflection:` names the reflection point before this one, from which items 1 and 4 count, and `Open issues:` the issues item 1 completes; the inventory holds the decisions and resources the Project Summary's patch reports;
- `docs/RUN_PARAMETERS.md`: whether the refactoring pass runs before a stage closes, and `Stage pause`, which item 6 obeys;
- at a stage close, the stage's section of `docs/BUILD_PLAN.md`, whole, with its `Demonstration:` line, and, while the stage review runs, its files under `run/review/` (the round's `STAGE-<name>-r<N>.diff` with its parts and `REVIEW-STAGE-<name>-r<N>.err`, and `SCOPE-STAGE-<name>.md`), the review guard's count of rounds opened for the stage (step 7), each reviewer's verdict, which you write to `run/supervisor/in-flight.md` as it returns, and the snapshot's hash, which you write there at the launch (this list is where both writes are asked for);
- the records the items read and write, whole: `docs/BUILDER_NOTES.md`, the entries of `docs/CHANGES.md` since the last reflection point, the stage's section of `docs/HARDENING.md`, and under `Documents/` the Issues document, the Feedback document, the Project Summary and, once it exists, the User Manual.

### The procedure

The build plan groups increments into named **stages** (Phase 4); a stage closes when its
last increment merges — and, where the refactoring pass is on, that pass (Phase 6 step 9)
has merged too, so the reflection describes the stage's final shape. A stage close, each
approved phase gate, and project end are the
**reflection points**: the only times `Documents/` is written (issue placeholders and the answer to a maintainer's request, rule 57, aside), and
the time you look at the bridge itself. Do the following, in order. None of it is an
escalation, none of it stalls the loop, and none of it changes the bridge. Before them, one
line: bring `project.json` up to date (its `state`: the phase, the stage, the bridge version,
the date; its `version` after a release).

At every reflection point, run `python ~/.claude/cursor-bridge/conformance-check.py` first: a floor the project lacks (a scanner missing from the gate, an action pinned by tag, a key within the builder's reach) is a configuration item for the next stage, never a question for the owner; record `NOTE`s in `PROJECT_STATUS.md`.

**At a stage close, after the refactoring pass has merged and before the items below (release A1b), both reviewers read the stage's whole change once,** with step 8's own protections:

1. From a clean tree on `main` in sync with `origin/main`: `git switch -c stage/<name> origin/main`.
2. Write the stage's whole change from committed state: `git diff <the stage's first checkpoint commit> origin/main > run/review/STAGE-<name>-r<N>.diff`, `<N>` the round step 3 opens; write `run/review/SCOPE-STAGE-<name>.md`, the stage's increments and briefs, the earlier rounds' dispositions and, at a round above the ceiling, its `Blocking class:` line (step 7); then `git add -f` both and commit them on the stage branch.
3. `python ~/.claude/cursor-bridge/review-guard.py snapshot STAGE-<name>-r<N>`, `<N>` the round it opens: one more than the rounds the guard has counted for the stage; the round's diff and its parts carry the snapshot's name, since the guard lists as the review's inputs, and refuses empty, the files under `run/review/` whose names hold it (KP-067); the SCOPE file, which it reads by the stage's name, is not among them, so confirm yourself that it is not empty.
4. Review A: `diff-reviewer` on `run/review/STAGE-<name>-r<N>.diff`, told the stage's briefs and that it reads a stage, not an increment. A stage diff too large for one reading is written in parts from the same committed state (`git diff <the first checkpoint> origin/main -- <paths> > run/review/STAGE-<name>-r<N>-<part>.diff`, committed with the whole), each part a `diff-reviewer` call of its own and the test files' part at most 25 files (counted by `git diff --name-only <the first checkpoint> origin/main -- <the test folders>`): a 79-file part once ended at the reviewer's turn limit without a verdict (reAngle, stage 3b), and a part that ends without a verdict is run again on what it had not reached (rule 43). Each part's prompt names its turn budget (the reviewer's `maxTurns`) and keeps the last turns for the verdict, so a part that runs short still answers (T25); a part read while Review B runs (step 5) runs single test files at most, never the suite, and any mutation run on a copy outside the checkout, so it shares nothing of the checkout with the reviewer's own run (T16).
5. Review B in the background, with execution, exactly as step 8 launches it: `python ~/.claude/cursor-bridge/bridge-run.py --limit auto --kind review -- cursor-agent -p --force --model <review_b from docs/ROSTER.resolved.json> "<the directive prompt, naming run/review/STAGE-<name>-r<N>.diff and the stage>" 2> run/review/REVIEW-STAGE-<name>-r<N>.err`; you write nothing to the checkout meanwhile but `run/supervisor/in-flight.md` (rule 43), where the position and each verdict go.
6. `python ~/.claude/cursor-bridge/review-guard.py verify STAGE-<name>-r<N>` must print `OK`; a GATE-INTEGRITY flag is handled as in step 8.
7. Decide the round, the ceiling read against the guard's count of rounds opened for the stage (with three opened, the next round is above it). Every arm that starts a fix does step 8 first (back on `main`, the stage branch deleted), and an arm that opens a new stage round runs it from step 1, on the new whole change, only after that fix has merged.
   - **Below the ceiling.** (a) A REJECT from either reviewer starts a fix brief and a new stage round; the round's findings the convergence rule makes blocking (the delegation loop's step 8: two or more reviewers independently naming the same line or the same defect, each alone calling it advisory) ride in its fix brief, and a class already recorded under the by-class line for the stage stays recorded. (b) A round ending with no REJECT but with findings the convergence rule makes blocking, the same exception included, puts those findings, with the round's other findings you take, into one fix increment through its own gate; the stage closes at its merge with no further stage round, and the rest are recorded at the close.
   - **At and above the ceiling.** Grade every finding, a convergent one included, against the five blocking classes first (behaviour against the brief or the register, security, data integrity, a defeated safety mechanism the stage relies on, a failing test). Only a blocking-class finding starts a fix brief and a new stage round, its `Blocking class:` line written into `run/review/SCOPE-STAGE-<name>.md` at that round's step 2, before its snapshot: the stage review's one lift, there being no brief, a line lifting the one round it was written for. A convergent finding outside the five goes to `docs/HARDENING.md` under the stage, marked convergent, and opens no fix increment, as the delegation loop's step 8 disposes of one at the same count; every other finding is recorded at the close and never becomes a fix increment.
   - **The fix brief** of either arm is a `BUG-<nnn>`, the stage's increments having merged; arm (b)'s is an increment with a budget of its own under the programs' branch rule. It is spec-packager's fix variant where any of its findings has a cause to confirm, the findings that are their own cause (a wording, a test's strength) carried in it; the plain brief KP-015's proportionality allows only where every finding is its own cause.
   - **No finding sends work back:** the stage review is done, its findings recorded at the close.
8. `git switch main` and `git branch -D stage/<name>`; nothing of the stage branch reaches `main`.

**Then the stage's demonstration runs live:** the build plan names one per stage (`Demonstration:` under the stage heading, Phase 4), run on the product as built, from a cold start; a product that cannot start fails its stage close. From the first increment that makes the product startable, every stage close starts it. A stage whose plan names no demonstration gets one at the next calibration, from the stage's increments.

1. **Issues.** For every issue opened since the last reflection point (below), make sure its
   entry in `Documents/<Name> Issues During Development and Their Solutions.md` is complete:
   context, how it surfaced, how it was solved, how it could have been avoided or mitigated
   from the start. A repeat gets no new entry — update the counter and the recurring task IDs
   on the existing one and say prominently that it recurred, because a repeat is the
   stronger signal.
2. **Bridge feedback.** Read `docs/BUILDER_NOTES.md` first and sort its lines: an insight
   about an issue goes to the Issues file (item 1, under its ID); a complaint about the
   tooling or the rules goes here. Append to `Documents/<Name> Claude-Cursor Bridge
   Feedback.md`: your own observations about the bridge — criticisms, bottlenecks,
   ambiguities in the governance, a rule that made something harder, a check that fired
   wrongly, a suggestion — and the builder's tooling complaints (the builder cannot write
   to `Documents/`). Mark each with the stage and who raised it (supervisor or builder), with
   enough context that the maintainer can evaluate it months later, and give each entry an
   ID `FB-nnn` in its heading (`### FB-012 — <title>`; the numbers never reused), as the
   Issues file gives `ISS-nnn`: the bridge's report cycle reads both documents in place and
   tracks every entry by its ID (release A3, plan 12). **Never act on it.** The
   bridge is the maintainer's to change; your job is to record.
2b. **Least confident** (stage close and project end). Name the three parts of the stage — at project end, of the whole build — you are least sure of, each with the concrete check that would settle it, and write them to `docs/HARDENING.md` under the stage name. Be specific: a module, a behaviour, an interaction — never "error handling". Each one a test can settle becomes a test you write before the next stage's first delegation (a failing one enters `root-cause-first`); an external-service doubt becomes a contract capture or a live smoke; the rest stay in `HARDENING.md` as leads the next stage's `refactor-scout` reads. None of it escalates.
3. **Project Summary and the rest of `Documents/`.** Patch the Project Summary — and any other
   document the user keeps there — for what changed this stage: decisions taken, scope changes
   accepted, deviations, the state of the build. Rewrite the affected sections; do not append
   a changelog to a document that is not one.
4. **User Manual** (once it exists). Patch it for every `CHANGES.md` entry since the last
   reflection point — a behaviour change is exactly what a manual tracks.
5. **Record** the reflection point in `docs/PROJECT_STATUS.md` (`Last reflection:`), and
   check the worktrees: `git worktree prune`, then `git worktree list` must show nothing
   under `Worktrees/`. A leftover is torn down now (safe primitive, rule 19) and opened as an
   issue — it means a merge closed without its teardown. Run `python ~/.claude/cursor-bridge/completion-check.py --mode plan` — every requirement still planned in a build plan, no deferral without the owner's dated approval; stand-ins it lists are expected only for later stages. Run `python ~/.claude/cursor-bridge/inventory-check.py` — it fails on a status file over its cap, a change-log entry the inventory has not absorbed, an environment variable or repository secret the code reads that Resources does not name, a secret value written into the inventory, or a malformed table; fix each before continuing. Then run `python ~/.claude/cursor-bridge/sync-check.py --apply`: local `main` must match the remote, or the `Remote sync:` line must name the reason it cannot.
6. **Then, at a stage close, obey `Stage pause` in `docs/RUN_PARAMETERS.md`.** Under `run`
   (the default) the stage-close report is a notification — "Stage <name> closed; next:
   <stage>" plus the FYI block — and you **continue into the next stage in the same turn**
   without waiting for a reply. Under `pause`, end with "Stage <name> closed — say
   *continue*" and wait. A pause is never the default behaviour of a stage close; only the
   parameter, an escalation, or project end stops the loop. (An approved phase gate is a
   different thing: those are always waited on, and they are all behind you by now.)

### Keeping the position

As each step above finishes (the stage review, the demonstration, each numbered item), write one line to `run/supervisor/in-flight.md` naming the reflection point and the step finished, and name the file on the status file's `Working files:` line (rule 54). A resume after a compaction reads its last entries and starts at the next step, so that no Issues or Feedback entry is written twice and none is skipped: what the items write under `Documents/` is not under git, and nothing else shows how far they got.

### Project end

At the close of the approved plan's last stage, project end follows these items: its trigger and its procedure are the module `~/.claude/cursor-bridge/workflow/phases/project-end.md`.

### Issues — what counts, and where it is written

An **issue** is anything that cost the loop more than the gate's normal single round: a
defect class that needed a second re-delegation or more; anything reverted, or that reached
`main` wrongly; a tooling, platform, or bridge failure (a hook that did not fire, a scanner
that broke, a mangled brief); a Workspace boundary violation. One legitimate reviewer
rejection that the next round fixed is the gate working — not an issue.

**One document, one ID per issue (`ISS-001`, `ISS-002`, …):**
`Documents/<Name> Issues During Development and Their Solutions.md`. You write it; the
builder never does. Its reader is an **AI** — the supervisor of a later project whose
requirements overlap, which receives it at its Phase 4 step 0 — so write it for machine
comprehension: precise conditions, exact symptoms, the confirmed cause, the fix, and what
would have prevented it, with file names and versions where they matter. No narrative for a
human reader; the human reads the Project Summary. There is no separate `docs/LESSONS.md`.

- **On detection** — an entry under the ID with the title, the task, the symptom as
  observed, and status `open`. This is the one mid-stage write to `Documents/`.
- **After the fix** — the entry is completed: the conditions under which it arises (stack,
  platform, subsystem, tooling), how it surfaced, the confirmed cause with its evidence
  (`root-cause-first`), how it was solved, and how it could have been avoided or mitigated
  from the start. Status `fixed`.
- **Repeats** — an issue already in the file gets no new entry: its counter and recurring
  task IDs are updated and the recurrence is stated prominently.
- **From the builder** — the builder cannot write to `Documents/`; anything it learned about
  an issue (a cause it found, a pitfall it hit) goes into `docs/BUILDER_NOTES.md`, which you
  read at every reflection point and fold into the Issues file under the right ID.

The maintainer promotes *generalizable* entries from this file into `Known-Pitfalls.md`
when the owner brings it to them; you flag candidates by adding `generalizable: yes` to an
entry, and never edit the bridge yourself.

#### Whether a compaction preceded it

Every entry's part written on detection also gives the time the incident happened, in UTC, and one line, `Compaction before:` followed by `yes` and the compaction's time in UTC where it is known, or by `no`: whether the session's context was compacted between your last whole reading of the governing text and the incident. A resume or a fork of the session in that time is not a compaction and is written on a line of its own, `Resumed before:` or `Forked before:` with its time where known (the session-start hook's message after each says which of the three it follows, when its input names it; where it names none, and says *compacted or resumed*, the line reads `Compaction before: unknown`). The bridge's maintainer measures from these lines how often a rule is broken within an hour of a compaction, which entries carrying a date alone could not show.

## Extension points

This module offers the points below, each by its key in the extension-point registry (`~/.claude/cursor-bridge/workflow/extension-points.md`), which states the kinds of change each accepts and whether it applies per part or per project. A conditional workflow's additions at a point are made where the point's line places them, in the order the core states in "Main and conditional workflows".

- `reflection.items` — reflection items a conditional workflow adds to the numbered items above, each run at every reflection point after item 4 and before item 5, so that the reflection point is recorded only once they are done, and each finished step kept as "Keeping the position" says; made once for the whole project.
