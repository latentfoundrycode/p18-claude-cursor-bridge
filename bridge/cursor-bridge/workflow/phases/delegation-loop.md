## Phase 6 — The delegation loop

### What must survive a compaction

After a compaction or a resume in this phase, read these before your next action:

- this module and its sub-file, each whole (the session-start hook names both), with `~/.claude/cursor-bridge/Merge-Verification-Policy.md` and `~/.claude/cursor-bridge/Known-Pitfalls.md`, each whole, and the other files the hook names;
- `docs/PROJECT_STATUS.md` and `docs/INVENTORY.md`, whole (rule 41), and the last entries of `run/supervisor/in-flight.md` where it exists: the increment in hand, its branch and its checkpoint, the background runs that will wake you and what waits for the owner; while Review B runs the status file is not written and the position is kept in `in-flight.md` (step 8), with the snapshot's hash `review-guard.py snapshot` printed, written there at the launch, since the hash `verify` prints must equal it;
- the increment's entry in `docs/BUILD_PLAN.md`, its brief `handoff/TASK-<nnn>.md` with every revision of it, and each builder report `handoff/TASK-<nnn>-r<N>-report.md`, whole: the brief bounds the increment, and the report holds the `Assumed, not verified` list whose every item takes a disposition (rule 42);
- for a fix (step 7, the `root-cause-first` procedure), `docs/debug/BUG-<nnn>.md`, whole: its hypotheses and the diagnostic rounds counted toward a resolution round; the fix brief `handoff/BUG-<nnn>.md` with every revision and report, as for a task; and `git grep DEBUG-BUG-<nnn>` for instrumentation not yet removed;
- `docs/RUN_PARAMETERS.md` and `docs/ROSTER.resolved.json`: who completes a merge, whether the refactoring pass runs and whether increments run in parallel, and the models the delegate command and Review B name;
- the runs' files: `run/agent/TASK-<nnn>.err`, which step 3b reads after a failed call, `run/agent/TASK-<nnn>.assumptions.md`, the only copy of a list the builder printed only in its last message (step 4), and `run/agent/TASK-<nnn>-suite.out`, which `test-runner` reads after a suite run in the background; and, while a gate is open, its files under `run/review/` (`REVIEW-<nnn>.diff`, `SCOPE-<nnn>.md`, `ASSUMPTIONS-<nnn>.md`, and `REVIEW-<nnn>.err`, whose first line is the launch time `pr-activity-check.py` needs), whole;
- while step 9 runs, its position: `run/supervisor/refactor-<stage>-candidates.md` (the sub-file's "Keeping the pass's position"), the detector's report under `docs/refactor/<stage>`, each `handoff/REFAC-<nnn>.md` brief with its report, the commits on `refactor/<stage>`, and `docs/HARDENING.md`'s section for the stage.

### The procedure

Steps 1 to 8 below run for every increment; step 9, the refactoring and optimization pass at a stage's close, is in a sub-file of this module, read whole with it wherever the module is read:

Sub-files: delegation-loop/refactoring-pass.md

For each increment, in order:

### 1. Checkpoint

Confirm the working tree is clean and commit if it is not. Every delegation must
start from a known-good commit so it can be reverted wholesale. Also **resolve the model roster** — which profile fills the builder and Review B roles
today, three distinct families, each model proven to answer (KP-022, KP-024):

```bash
python ~/.claude/cursor-bridge/roster-check.py docs/ROSTER.json --command "<the delegate command you are about to run>"
```

It skips every profile that needs Cursor's Other Models pool while `docs/ROSTER.json` says `"other_pool": "exhausted"` — set **automatically** when a call returns a usage-limit error or a model fails twice in a row (step 3b), or when the owner says *usage exhausted*, because a probe cannot see a nearly-empty quota, only a refusal — and it restores the pool by itself on the roster's `reset_day` (UTC). It probes the remaining profiles with a one-word request and writes the chosen one to `docs/ROSTER.resolved.json`. Read the builder id from that file into the delegate command (`--model <builder>`) and the Review B id into the Review B invocation. `FAIL` stops the delegation. If the profile in use is not the preferred one, say so in the report's first line, with the ids taken from the resolved file, never from this example: "running on the native profile: builder composer-2.5, Review B grok-4.7-high — the full profile returns on <the next reset day> UTC, or earlier if you say *usage reset*".

**Start every new branch from the remote's base.** When this checkpoint opens a new branch (the first increment of a merge unit, a refactoring pass, a fix), first run `python ~/.claude/cursor-bridge/sync-check.py --apply`, then create the branch from the remote-tracking base — `git switch -c <branch> origin/main` — never from local `main`. A stale local copy then can never become the starting point of new work (KP-026). Then:

```bash
git status --short
git add -A
git commit --no-verify -m "checkpoint before TASK-<nnn>"
```

The checkpoint commit uses `--no-verify` deliberately: it is the recovery anchor and must
succeed even when the tree does not pass lint (a partial or inherited state). This and a parallel builder's hand-off commit in its worktree (step 3, a snapshot of its work made where no environment exists to lint it) are the
**only** commits that bypass the pre-commit lint gate — your accept/increment commits (step 7)
run a plain `git commit` and must pass it. Using `--no-verify` on an increment commit is a
gate-integrity flag, not a shortcut.

Issue each git command on its own line — never join them with `&&`, `|`, or `;`.
The permission allowlist matches a command against a single rule, so a chained
command like `git add -A && git commit` matches none of them and forces an approval
prompt on every checkpoint, defeating the point of the allowlist.

Never delegate from a dirty tree. You will not be able to tell Cursor's changes from
whatever was already there.

### 2. Package the brief

Delegate to **spec-packager** to write `handoff/TASK-<nnn>.md`. The brief must be
self-contained — Cursor gets no conversation history, only this file. For a UI-bearing
increment, the brief must name the exact approved mockup file(s) and the relevant
`docs/design/DESIGN.md` sections, and list the frozen `vercel-interface.mdc` as an
applicable rule. Every brief carries the Workspace boundary and the standing invitation to
note tooling friction in `docs/BUILDER_NOTES.md` (spec-packager's constraints template).
spec-packager's **reality check** runs first: the schema, configuration, data, and
interfaces the increment assumes must exist in the codebase *as built*; "approved in the
plan" is not "fits the data" (KP-019). A mismatch comes back to you as a scope question,
not as a brief. Once the brief is written, `python ~/.claude/cursor-bridge/plan-check.py`
compares it with its increment: a Scope path outside the increment's Scope or a requirement
the increment satisfies that the brief does not name is a `BRIEF` failure, fixed in the brief
before the checkpoint commit (release A4: a brief once silently dropped planned work).

### 3. Delegate to Cursor

```bash
python ~/.claude/cursor-bridge/bridge-run.py --limit auto --kind builder -- cursor-agent -p --force --model <builder from docs/ROSTER.resolved.json> "Read handoff/TASK-<nnn>.md and implement exactly what it specifies. Stay inside the Scope section. Do not modify .env, secrets/, CI configuration, or anything under docs/ or handoff/ unless the Scope section names the file. Do not add dependencies. When finished, print a one-paragraph summary and the path of your report file." 2> run/agent/TASK-<nnn>.err
```

The `--model` value is copied from `docs/ROSTER.resolved.json` (step 1), never typed from
memory; the stderr redirect keeps the CLI's own messages in a file, which is what the
automatic model switch below reads. The call runs in the background with the Bash tool's
own `timeout` set to the kind's cap in milliseconds, twice the launcher's default
(`14400000` for a builder, `7200000` for a review or a watch, `3600000` for a test suite;
a learned `--limit auto` never exceeds the cap): without it the tool may end a background
command after thirty minutes, before the launcher's limit, mid-work and with no report (the
TDP's TASK-157 r13d, KP-053, observed once; the same `timeout` goes on every background
launch, Review B's, the CI watch's, a launched suite's and a wake-timer's). (`run/agent/` is gitignored.) **The launcher** gives
the run its ceiling (`--limit auto`: two hours until a healthy run of this project has taught it more, never above four without the owner's words; release A2) and kills the whole process tree at it (exit code 124),
and withholds the owner's GitHub identity from the builder (KP-032, KP-033). Exit 124 is
handled in step 3b: inspect the tree first, because a builder that hung on its way out may
have finished its work.

Rules for this call, all of which matter:

- **`cursor-agent`, never `agent`.** On Windows the bare `agent` command may belong
  to a different vendor's CLI.
- **`--force` is required.** Without it the headless run hangs on an approval prompt
  that nothing will ever answer.
- **No secrets in the prompt, ever.** The prompt leaves the machine. Refer to
  `.env` by name; never quote its contents.
- **The brief carries the constraints — the command line carries *nothing* but this
  constant pointer.** Never put task content in the CLI argument: no code, no paths with
  special characters, no multi-line instructions, no corrections. The shell (Git Bash) eats
  backticks and `${…}` before Cursor ever sees them, and a builder handed a mangled prompt
  "improvises" — in practice it has skipped the exact fix it was asked for. **This applies
  to re-delegations too:** corrections go into the committed brief (revise
  `handoff/TASK-<nnn>.md` in place, or write `TASK-<nnn>-r2.md`), then re-issue the *same*
  constant pointer command. If you catch yourself typing instructions inside the quotes,
  stop and put them in the file.
- If a run needs a specific model, add `--model <name>`; `cursor-agent --list-models`
  shows what is available.

**Parallel increments** (only when `docs/RUN_PARAMETERS.md` says `Parallel increments: on`). When `python ~/.claude/cursor-bridge/plan-check.py` lists ready increments under `TOGETHER` (all `Parallel: yes`, scopes disjoint, no dependency between them), you may run their **builders** at the same time. Only the builders run concurrently — that is where the time goes; everything you do stays sequential and happens in your own checkout. Claude Code asks before running git in another folder (that folder's hooks could run) and before touching files outside your working directory, so **you never work inside a worktree**: it exists only so a second builder has a checkout of its own.

1. **Prepare each branch in your own checkout**, after `sync-check.py --apply`: `git switch -c task-<nnn> origin/main`, write and commit the brief (spec-packager's parallel variant: the builder commits its own work at the end and knows its checkout has no project environment), note the branch's starting commit (`git rev-parse HEAD`) on the status file's `In flight:` line, and switch back.
2. **Create each worktree from your checkout**: `git worktree add ../Worktrees/TASK-<nnn> task-<nnn>`.
3. **Delegate each in the background**, pointing the builder at its checkout with `--workspace` and otherwise exactly as in step 3 (the launcher first, then `cursor-agent`):

```bash
python ~/.claude/cursor-bridge/bridge-run.py --limit auto --kind builder -- cursor-agent -p --force --workspace ../Worktrees/TASK-<nnn> --model <builder> "Read handoff/TASK-<nnn>.md and implement exactly what it specifies. Stay inside the Scope section. Do not modify .env, secrets/, CI configuration, or anything under docs/ or handoff/ unless the Scope section names the file. Do not add dependencies. When finished, print a one-paragraph summary and the path of your report file." 2> run/agent/TASK-<nnn>.err
```

4. **When a builder finishes**, remove its worktree from your checkout (`python ~/.claude/cursor-bridge/worktree-teardown.py ../Worktrees/TASK-<nnn>`, which refuses while anything is linked inside and never forces), switch your checkout to its branch, and run steps 4 to 8 there like any increment: the scope check with `--base <the recorded starting commit>`, the diagram check, the reviews, the tests, the accept commit, the pull request, the gate, the merge. Process finished branches **one at a time**. Before the accept commit of every branch after the first, run `git merge --no-edit origin/main` to bring in what merged meanwhile — the other increment's code, disjoint by construction, and its record updates, so the change log, the inventory, and the register do not conflict. CI runs on the pull request's merge with `main`, so the combined state is tested either way.
5. **A re-delegation** after a review runs in your own checkout like any sequential increment.

Never use Cursor's own `--worktree` option: it places the checkout under your home folder, outside the project and outside the Workspace boundary. **One writer per checkout** holds throughout: no two builders share a checkout, and you never touch a checkout a builder is running in. The price is known: a builder in a worktree has no project environment (no virtual environment, no installed packages), so it cannot run the test suite and its first delivery may need one more iteration. Record each running builder on `In flight:`; each is a background task, so the loop guard knows something will wake you.

### 3b. A model fails mid-step — switch automatically, restart the step, never wait

The owner may be asleep while the loop runs. A usage limit reached at 03:00 must not stall
the build until morning, so a model failure is handled by the loop, never by a question.
When any `cursor-agent` call — a delegation, a Review B launch, a resolution round, the
stage-close pass — exits non-zero, produces no output, or hits the launcher's limit (exit
124):

(The one exception: every exit 125 whose message begins `bridge-run: refused - design
ceiling: ` is the design critique's ceiling holding, never a model's failure: it is not retried
and no `--record-failure` follows it; Phase 2. A design-critique reply that names nothing from
its file is recorded like any failed call and follows the exits below, which Phase 2 counts: the
exit-4 retry, the exit-3 re-resolve and one run on the profile it gives, then the wait Phase 2
describes.)

**First, when the exit code is 124, look before you discard** (KP-033): `git status` and
`git diff --stat` in the checkout. A builder that completed its edits and then hung on its
way out (a lost connection while reporting, an orphaned server it started) has done the
work; take the tree through the normal inspect, scan and test steps as if the run had
returned. Only a tree with no finished work goes through the restart below. Every run that
ended at its limit gets an Issues entry (`ISS-nnn`): what the inspection found, what was kept,
the kind's ceiling and the longest healthy run on record (`run/launcher/runs.jsonl`), so a kind
that keeps reaching its ceiling is diagnosed rather than retried forever (release A2). The
entry leads somewhere: when the kept work merged, mark that run healthy too
(`bridge-run.py --healthy <run id>`), so the kind's ceiling grows from it; when a kind reaches
its ceiling twice with nothing kept, the brief is too large for one run and is split.

```bash
python ~/.claude/cursor-bridge/roster-check.py docs/ROSTER.json --record-failure <model id> --stderr-file <the .err file of that call>
```

The argument after `--record-failure` is the **model id** of the failed call, copied from
`docs/ROSTER.resolved.json` — never a file path or a task name; the script refuses anything
that is not a model of the roster (exit 2) and changes nothing (KP-034).

- **Exit 4 — transient.** A connection error (lost, reset, reconnecting, a 5xx, a rate
  limit) or a hit limit, each retried at most twice in eight hours, or a first other
  failure. Retry the same step once, unchanged. A second other failure within eight hours
  is exit 3; a third connection failure is exit 5.
- **Exit 5 — a dead line, not a dead model.** A third connection failure or hit limit of
  the same model within eight hours. No switch helps; stop the step, write it on the
  `Awaiting user on:` line and tell the owner what failed and how often.
- **Exit 3 — exhausted or unavailable.** A usage-limit message (a usage, quota, plan or
  spending limit reached or exceeded; insufficient credits; upgrade your plan; payment
  required), or a second other failure of the same model within eight hours. The script
  has already marked the pool exhausted (or the model unavailable, for six hours) in the
  roster's state file (`.git/bridge/roster-state.json`, which no reset touches). Now, **in
  this order**:
  1. **Restart point first.** A delegation: the working tree goes back to the
     pre-delegation checkpoint (`git reset --hard <checkpoint sha>` then `git clean -fd`
     inside the workspace — the checkpoint exists exactly for this). The reset cannot
     erase the switch: the roster's state lives under `.git/bridge/`, and the re-resolve
     that follows rewrites `docs/ROSTER.resolved.json` after the reset (KP-034).
  2. **Re-resolve:** `python ~/.claude/cursor-bridge/roster-check.py docs/ROSTER.json` —
     the next profile that answers is written to `docs/ROSTER.resolved.json`. `FAIL` here
     (no profile answers at all) is the one case that stops the loop: report it as the
     single decision — buy usage, or add a candidate — and wait.
  3. **Restart the interrupted step** with the newly resolved models. A delegation: the
     same brief is re-issued with the new `--model`. A Review B launch: re-run on the same
     committed diff file with the new reviewer. A resolution round or a stage-close pass:
     re-run the failed call with the new model; earlier completed calls stand. Nothing
     partial survives, nothing completed is redone.
  4. **Record and report.** Open an issue (`ISS-nnn`) whose entry carries the stderr
     excerpt — that text is how the maintainer sharpens the classifier — and put the switch
     in the **first line of the next report**: "auto-switched to the native profile at
     <time> (<model> returned: <excerpt>); TASK-<nnn> restarted with builder <id>, Review B
     <id>; say *usage reset* when the other-models pool is back." Then continue.

A wrong switch costs a weaker reviewer until the pool resets; a stall costs a night. The
rule therefore errs toward switching. **Returning** to the preferred profile is a calendar
fact, not a probe: the roster's `reset_day` (day of month, UTC — the owner's subscription
resets on the 15th, so `16`) and the UTC exhaustion stamp let `roster-check.py` restore the
pool by itself at the first checkpoint on or after 00:00 UTC of the first reset day after
the exhaustion (`AUTO-RESET` in its output; put it in the report's first line). The owner
can also say "usage reset" (`--mark-reset`) or "usage exhausted" (`--mark-exhausted`) at
any time. A probe is never used for the return: it cannot tell a reset from 1% remaining.

### 4. Inspect

**The builder's report — the file `handoff/TASK-<nnn>-r<N>-report.md` it writes as it runs,
its last message the summary with the file's path (release 2026.10.11d; twice a last message
arrived as one line and the report with it would have been lost) — and its "files I changed"
list are a hint, never evidence.**
It has claimed fixes it did not make and described unrequested edits as the requested ones.
Never surface "done / N passed" from the builder as status. The working tree is the only
trustworthy manifest — derive everything from git:

```bash
git status --short
git diff --name-only
git diff --stat
git diff
```

Then run the **deterministic scope check** — the file-level floor, before any reviewer:

```bash
python ~/.claude/cursor-bridge/scope-check.py handoff/TASK-<nnn>.md
```

Where the project has a diagram index, run the **design-conformance check** too — before any reviewer, like the scope check:

```bash
python ~/.claude/cursor-bridge/diagram-check.py --mode code
```

An `IMPORT` or `SCHEMA` failure is **design regression**: the code crossed a boundary the component diagram does not draw, or the schema drifted from the entity-relationship diagram. It is handled like `SCOPE DRIFT` — re-delegate with the diagram restated — unless the builder raised an objection in its summary, which goes to "Objections — bottom-up escalation" instead.

And read `docs/BOUNDARY_VIOLATIONS.md` if it exists. Git cannot see a write outside the
repository, so this log — written by the `boundary-check` hook — is the only trace of the
builder reaching outside `Workspace/`. Any new entry is handled like `SCOPE DRIFT`: undo the
outside edit by hand (`Documents/` is not under git), re-delegate, open an issue.

**Then triage the builder's `Assumed, not verified` list** (rule 42). It is the one thing the builder knows that no reviewer can see — where it guessed. It stands in the builder's report file, `handoff/TASK-<nnn>-r<N>-report.md`, which the accept commit keeps (`git add -f` where the project ignores `handoff/`); where a builder printed it only in its last message, copy it verbatim into `run/agent/TASK-<nnn>.assumptions.md` before anything else, since the message is lost with the run. A missing section means *unknown*, never *none*: note it, and the reviewers hunt unaided. Give every item exactly one disposition:

- **test** — a test settles it; you write it (N4 permits tests), and a failing one re-delegates like any defect;
- **contract** — a fact about an external service; the increment is not done until recorded real responses or a live smoke confirm it (rule 37);
- **council** — a design or requirement ambiguity; the resolution round settles it, or an intent escalation if it turns on what the software should do;
- **accepted** — a risk you knowingly carry; a row in `docs/INVENTORY.md` → Decisions with the reason and what would reopen it.

Record the dispositions in the accept commit's message body under `Assumptions:` (one line per item: assumption → disposition). Hand the list to `diff-reviewer` and `security-auditor` — and at merge to Review B — as **extra places to look, never as the places to look**: a review that checks only the listed items is not a review, and an empty list proves nothing.

It compares the git-derived changeset (tracked diffs vs the checkpoint plus untracked new
files) against the brief's `## Scope` and prints `SCOPE CLEAN` or `SCOPE DRIFT` with the
out-of-scope files — surfaced, not discovered. **Exit 1 (drift):** the increment does not
proceed as-is — re-delegate with the scope restated, or, if the out-of-scope edit is a
genuine improvement you choose to keep, widen the brief's Scope explicitly and record the
call in `docs/CHANGES.md`; never let drift pass silently. **Exit 2 (cannot verify):** the
brief has no `## Scope` — a `spec-packager` defect; fix the brief, do not proceed blind.

**The tests run before the first reviewer** (release A5, plan 13.1). Once the scope and
diagram checks pass: if the increment's acceptance criteria are not yet covered by tests,
write those tests yourself first — you are allowed to write tests, and tests written by
the reviewer rather than the implementer are worth more; each carries the paragraph it
enforces (`enforces: <document> §<section>` in its docstring or a comment). A mutation
driver — the script that applies each mutant, runs the tests and restores the code — is
written here too, on your side, after the builder's run and never by the builder (the
brief's mutation list is the builder's own in-process check, by hand, no script of it in
the diff): a builder's driver is judged by
nobody, and five mutants that did not model their names once cost three rounds (reAngle
TASK-010c); `diff-reviewer` reads a driver's mutants against their names as it reads a test
against its paragraph, and a fix brief after a driver run asks for the code fix only. A
driver run you must end is ended whole with `bridge-stop.py` (KP-056). Then delegate to
`test-runner` for the increment's tests and the suite, naming the increment's test files
(the brief's test paths plus `git diff --name-only <checkpoint> -- <the test folders>`), so
it knows which skips are the increment's: a test of the increment that was skipped fails the
step, like a failed one (a builder has reported passing tests that had been skipped). A suite that takes more
than ten minutes is not run inside `test-runner`'s call: the Bash tool ends a foreground
command at ten minutes (600 seconds, KP-061), so such a suite runs through the launcher in
the background (`python ~/.claude/cursor-bridge/bridge-run.py --limit auto --kind test -- <the
recorded suite command> > run/agent/TASK-<nnn>-suite.out 2>&1`, the tool's `timeout` at
`3600000`; a runner the launcher does not know answers 125 and runs directly with `# wake`,
rule 43), its completion wakes you, and `test-runner` then reads that file. Then
run every new or changed test file once against the checkpoint's code: `git worktree add
../Worktrees/old-<nnn> <the checkpoint commit>` (the one worktree of your own that rule 39
allows: read-only, torn down in this step), copy in the test files and the fixtures they
import (`conftest.py`, the fixture folders), and first check where the package resolves from
there (`python -c "import <package>; print(<package>.__file__)"` run in the worktree): where
it resolves to the Workspace, as an editable install does (KP-054), the checkpoint run cannot
run the old code, and the step records "not run against the checkpoint: editable install",
the reviewer's check of each test against its paragraph standing in; where it resolves to the
worktree, run the new files there: a test that passes against the old code proves nothing (a
test written from a misread specification once made wrong code pass every gate) and goes
back to be rewritten before any reviewer reads the diff; a collection error is "not run",
neither pass nor fail, and is said. Tear the worktree down with `worktree-teardown.py`. The
cost where it works is the worktree's seconds and one run of the new files, a minute or two
per increment; a reviewer then judges a tested diff.

Delegate the diff to **diff-reviewer**, naming the tests you wrote and the paragraph each
enforces, so it judges them against the paragraph and does not take them for the builder's.
You are asking two questions: does this implement the brief, and is it sound? A diff that does something better than the
brief asked for is still a deviation — flag it rather than silently accepting it.
File-level drift is already settled by the scope check before it reads; `diff-reviewer`'s
scope job is **region-level** — an in-scope file edited beyond what the brief asked.

For a **UI-bearing** diff, also delegate to **design-auditor** after `diff-reviewer` — it
reviews design conformance (mockup fidelity, visual system, the frozen interface rules)
that `diff-reviewer` deliberately leaves alone. A **blocking** design finding re-delegates
like any correctness `REJECT` (a corrected brief, step 7) — it does **not** escalate.
**Advisory** findings go to `docs/CHANGES.md`, not a re-delegation.

For a diff with **logic, auth, input-handling, or data-access** surface (almost all, not just
UI), also delegate to **security-auditor** after `diff-reviewer` — it reviews the
exploitable-vulnerability and authz/authn/data-integrity classes the deterministic floor
misses, and does **not** re-run Semgrep/OSV/Socket. A **blocking** security finding
re-delegates like any correctness `REJECT` — it does **not** escalate. **Advisory** hardening
findings go to `docs/HARDENING.md` / `docs/CHANGES.md`.

**Reviewer routing — codified by diff shape, not hand-picked.** Every increment gets the
first row; add the others by what the diff touches:

| Diff shape | Required reviewers / checks |
|---|---|
| **Every increment** | deterministic `scope-check.py` → `diff-reviewer` → `secret-sentinel`; at merge, Review A + cross-family Review B |
| **UI-bearing** (screens, styles, components) | + `design-auditor`; the observability tests run under `test-runner` (Tier B: hand it the screenshots) |
| **Logic / auth / input-handling / data-access / deletions** (almost all) | + `security-auditor` |
| **New dependency** | + the dependency-admission gate (`socket package score` + OSV) *before* acceptance |
| **Touches tests, CI, hooks, scanner config, or a frozen rule** | reviewers apply the anti-gaming checks explicitly (`Merge-Verification-Policy.md`) |
| **Stage refactoring branch** (`REFAC-*`, pure by `refactor-check.py`) | `diff-reviewer` in refactoring mode → `secret-sentinel`; `design-auditor` / `security-auditor` only if it touches their surface; Review B asked "is this behaviour-preserving?"; **one** gate pass for the whole branch |

**When reviewers disagree, say so loudly.** Before adjudicating (step 7) or convening a
resolution round, write it out explicitly — `REVIEWERS DISAGREE on <crux>` — naming which
reviewers, what they disagree about, and whether the crux is correctness or intent. That flag
is where your judgement adds the most; never let a split dissolve silently into "mostly
approved."

### 5. Scan

Delegate to **secret-sentinel** before anything is committed. This runs on every
increment without exception, including ones that look trivial. It runs
`python ~/.claude/cursor-bridge/invisible-check.py` first (release A4): a zero-width or
bidirectional character in a changed file hides a token from every reader and reorders
what a reviewer sees, and the diff reviewers cannot see it either. `secret-sentinel` still flags
unpinned or oddly-shaped dependency names and protected-path/`.gitignore` issues, but
dependency **reputation** now belongs to the admission gate below, not its heuristic.

### 5b. Dependency-admission gate

Whenever an increment needs a **new dependency** — flagged in the plan, the brief, or by a
reviewer — run the admission gate on the candidate *before* accepting it: **`socket package
score <ecosystem> <pkg>`** (the ecosystem argument is required, e.g. `socket package score
npm lodash`) and an **OSV-Scanner** lookup.

- **The lockfile is part of the dependency.** After admitting one, the increment must
  change the manifest *and* the lockfile CI installs from. Reviewers read what is in a diff,
  not what is missing from it, so this is checked deterministically before any reviewer:
  ```bash
  python ~/.claude/cursor-bridge/lock-check.py <checkpoint-sha>
  ```
  `LOCKFILE MISSING FROM DIFF` re-delegates with "regenerate the lockfile with the project's
  lock command and commit it in the same increment" (KP-018). Name the project's lock command
  and lockfile in `PROJECT_STATUS.md` at configuration.
- **Malicious or known-bad** → reject the dependency and find an alternative. This is a
  correctness call you make and record in `docs/CHANGES.md` — **not** an escalation.
- **Clean but carrying a consequence the owner bears (money, privacy, lock-in)** → the one
  dependency rule (rule 56): admitted and recorded by you, put to the owner for that
  consequence only, with the security signal attached; never for its licence or its merit.

This stops a poisoned package at the moment of admission rather than catching it downstream.
`socket package score` works on the free tier.

### 6. Benchmarks and observability

The tests already ran in step 4, before the first reviewer, the ones you wrote first.

Where budgets exist and their benchmarks are built, the **benchmark floor** runs with the
tests: `scripts/bench.ps1` then
`python ~/.claude/cursor-bridge/bench-check.py bench/budgets.json bench/baseline.json bench/results/latest.json`.
`OVER BUDGET`, `REGRESSION`, or `NOT MEASURED` is a correctness-class block: re-delegate
with the numbers in the brief, never route it to the user, and never fix it by loosening a
budget or moving the baseline (`Merge-Verification-Policy.md` §Anti-gaming). Write the
corrected brief from a **named cause**: profile the failing benchmark, match the hot spot
against `~/.claude/cursor-bridge/Performance-Patterns.md`, and put the entry's fix and
measure in the brief — never "make it faster". A hot spot that matches no entry goes through
`root-cause-first` like any other defect.

For a UI-bearing increment, the tests you write include the **observability tests** (Tier A):
drive the app to each affected inventory state *through the real render path* and assert no
runtime invariant fired, no `console.error`, and the required states exist (see
`~/.claude/cursor-bridge/Observability-Conventions.md`). These run under `test-runner`/CI like
any test — no daemon. A fired invariant / `console.error` / unreachable state is a
**correctness-class block** (re-delegate, step 7), never a user question. If Tier B is on, the
tests capture per-state screenshots; hand those to **design-auditor** as evidence for its
existing mockup-fidelity judgement (they do not add a new pass).

### 7. Decide (accept the increment)

- **Accept** — local review, scan, and tests pass. Run `scope-check.py` once more just
  before this commit (its base is the commit that committed the brief, so a builder's own
  commits are inside the diff; release A4). Commit to the increment branch with a
  message referencing the task ID. Update `docs/PROJECT_STATUS.md` (rewrite the fields; never append history) and, when the increment changes behaviour or needs a new resource, `docs/INVENTORY.md` — in the same commit as the increment's `CHANGES.md` entry, moving `Reflected through:` to that entry (rule 41). When the increment completes a requirement, set its row in `docs/REQUIREMENTS.md` to `built` and name the tests — which carry the requirement's ID — in its Evidence cell, in the same commit. Move to the next
  increment. Increments accumulate on the branch; merging to `main` is a separate,
  verified step (below), not something you do per increment.
- **Iterate** — something is wrong and you understand why. Revise the brief *file* (in
  place, or as `TASK-<nnn>-r2.md`) with specific corrections, commit it, and re-issue the
  same constant delegate command. Never inline the corrections into the CLI prompt (step 3).
- **Re-delegate on a review REJECT** — if a reviewer rejects the work (see step 8), that
  is a code defect, which is the loop's problem, not the user's. Feed the reasons into a
  corrected brief file and re-delegate — again via the file, never the prompt. This does
  not count against the user's attention.

**Diagnose before you re-delegate a defect — the `root-cause-first` skill.** A corrected
brief written from a *symptom* makes the builder guess, and a guessed fix passes the
failing test by suppressing what it saw. So before any Iterate or Re-delegate for a
behaviour defect, ask: *is the cause already proven by the failure itself?* If the
traceback names it, or the brief listed a requirement the diff simply omitted, fix
directly. Otherwise — an assertion on an output, a fired invariant, an unreachable state,
a timing or intermittent failure, a regression, a user-reported bug, a `test-runner`
diagnosis labelled **INFERRED**, or **any second re-delegation for the same defect** — run
the procedure: reproduce deterministically (a failing test, or an observability test that
drives the exact state), write two or more hypotheses each with its discriminating
observation in `docs/debug/BUG-<nnn>.md`, instrument only to tell them apart (tagged
`DEBUG-BUG-<nnn>`, in the working tree, never committed), capture the run to the
gitignored artifacts dir, keep the hypothesis the evidence supports, clean up and prove it
(`git status` clean, `git grep DEBUG-BUG-` empty), then package the **fix brief**
(`handoff/BUG-<nnn>.md`, spec-packager's fix variant) carrying the confirmed cause, the
evidence, and the reproduction test that must go red to green. Three diagnostic rounds
without a confirmed cause go to a resolution round, never to a guessed fix and never to the
user. The fix goes through the normal gate once — no extra gate pass; `diff-reviewer`'s fix
mode rejects symptom suppression and a cause left untouched.

**When to stop re-delegating — judge convergence by defect class, not a raw count.** The
brake exists to stop *grinding on a broken brief or design*, not to interrupt a gate that is
successfully hardening the code — and **reaching some number of rounds is never itself a
reason to involve the user.** Whether to continue, draw a line, or stop is your judgment to
make and record. Judge it like this:

- **Keep going** when each round surfaces *new, legitimate concerns that then get fixed* —
  that is the gate working (especially a thorough cross-family Review B finding real edges
  Review A missed). Convergence looks like: fixes land and the concerns get more esoteric
  round over round.
- **Draw a by-class line once the core is correct.** When the increment's actual behaviour —
  what the software *does and produces* — is implemented and verified, and the findings that
  keep coming are all the long tail of one genuinely hard subsystem (subprocess teardown,
  retry/timeout races, kill paths, concurrency edges), do **not** re-delegate that tail
  round after round. Record each such finding to `docs/HARDENING.md` (one line each, on the
  increment's PR branch) and merge. A late finding blocks the merge only if it is a **new
  class** — render/output correctness, data integrity, security, or what the software
  actually does — **or** if it *defeats a safety mechanism this increment relies on* (a bug
  in the very timeout or kill path built to protect the run is core, not tail). Drawing this
  line is a decision you make and record, not one you bring to the user.
- **Stop** on genuine *non-convergence*: the **same** defect rejected twice unfixed, or a
  fix that **regresses** something already passing. That is a broken brief or design — say so
  plainly in your report. Raw "several REJECTs" is *not* a stop if each round found a
  different, legitimate, now-fixed issue. The one kind of deadlock that goes to the user is
  an **intent** deadlock — reviewers at odds over what the software should *do* — and it goes
  as an intent question, never a correctness one.

**Split verdicts you resolve yourself, not by escalating.** When one reviewer blocks and
the other approves, decide it on the merits — and bias toward the project's own
**established invariants** (a rule the codebase already enforces elsewhere). If the
blocking concern aligns with an existing project standard (e.g. a path-confinement check
another increment already added), apply the fix and continue; record the call in
`docs/CHANGES.md`. Escalate a split **only** when it turns on intent — what the software
should do — not on code correctness or which reviewer is "right" technically.

**When a split is genuinely hard, convene a resolution round before deciding.** Most splits
you settle at once on the merits. But when the merits are not clear-cut — the reviewers
disagree on a substantive correctness question and neither side obviously aligns with an
established invariant, or the call is entrenchable enough that getting it wrong is expensive
to undo — do not adjudicate it alone, and do not hand it to the user. Run the bounded
reviewer-debate step in `~/.claude/cursor-bridge/Merge-Verification-Policy.md`
(§"Resolution round"): each reviewer reads the other's position from a
committed file and returns a reasoned vote, and you decide on that fuller record, biasing to
established invariants and recording the call in `docs/CHANGES.md`. This keeps a hard
correctness call inside the decorrelated gate instead of on your desk or the user's.
Escalate to the user only if the crux turns out to be intent — what the software should do —
never correctness.

If a run has left the tree in a state you cannot make sense of:
`git reset --hard HEAD` returns you to the checkpoint. Say so plainly when you do it.

### 8. Merge (the verified gate)

Do not decide merge-worthiness by reading the diff for the user, and never ask the user
whether the code is correct — they cannot judge it, and a check they cannot perform is
not a check. Apply the gate in `~/.claude/cursor-bridge/Merge-Verification-Policy.md`
instead. In short, a branch merges to `main` only when **all** hold:

1. the required CI check is green (the real test suite ran and passed);
2. **Review A** — the `diff-reviewer` subagent (pinned to a strong model) returns
   APPROVE on the cumulative diff;
3. **Review B** — a **cross-family**, non-Anthropic verifier returns APPROVE on the same
   diff, invoked with execution per the policy, on a committed checkpoint that
   `review-guard.py` snapshots before the launch and verifies and restores after it. **Write the diff to a committed file inside the
   workspace and have Review B read it from that file — never pass it inline through the
   shell** (inline heredocs mangle or drop the diff, and a reviewer that received no diff can
   still emit an APPROVE-shaped reply). Two rules make that file whole and reachable:
   (a) **generate it only from committed state** — `git status --porcelain` must print
   nothing first, then `git diff <merge-base>...HEAD > run/review/REVIEW-<nnn>.diff`; a diff
   taken from the working tree silently omits every untracked new file (KP-017);
   (b) **the file lives inside `Workspace/`** at `run/review/`, committed on the increment's
   branch and removed with `git rm` before the merge — never in a temp folder outside the
   project, which the Workspace boundary rightly blocks (KP-016); (c) **the branch's assumption lists travel with it** — write `run/review/ASSUMPTIONS-<nnn>.md` from the `Assumptions:` sections of the branch's commit messages (`git log <merge-base>..HEAD --format=%B`), commit it beside the diff, remove it with the diff before the merge, and name both files in the prompt: the list as extra places to look, never as the review's scope. Launch it exactly as the policy shows. **First** `python ~/.claude/cursor-bridge/review-guard.py snapshot <nnn>` — it refuses a tree that is not clean (commit everything of yours first) and records HEAD, the branch, every ref, the stash list, the repository's configuration and the ignored entries. **Then** the launcher, **in the background** (`run_in_background`; its completion is what wakes you, rule 43):
   `python ~/.claude/cursor-bridge/bridge-run.py --limit auto --kind review -- cursor-agent -p --force --model <review_b from docs/ROSTER.resolved.json> "<directive prompt>" 2> run/review/REVIEW-<nnn>.err`
   (`--force` lets the reviewer **run the tests and build its own reproductions**, which is
   where its strongest findings have come from — the owner's decision of 2026-10-04 after
   a read-only mode was tried and found weaker; the launcher withholds the owner's
   identity and ends the run at the limit; a review that runs a large suite can take most
   of the hour). **While it runs, nothing of yours writes to the checkout**: no builder, no
   `test-runner` (it would share the checkout, the databases, the ports and the caches with
   the reviewer's own run), no commit, and no writing subagent either — no `spec-packager`
   (the next brief waits for `verify`; one once wrote `handoff/` during a Review B run and
   the guard flagged GATE-INTEGRITY, reAngle ISS-014), no `diagram-specialist`, no
   `cursor-configurator`, nothing that writes under the checkout, your own status-file edits
   included (`run/supervisor/in-flight.md` exists for those, rule 43); besides that file, the launcher's own `run/review/REVIEW-<nnn>.err` is
   the one file written meanwhile, and the guard keeps it; read-only subagents
   (`security-auditor`, a Review A on another branch's committed diff) may run.
   **Afterwards** `python ~/.claude/cursor-bridge/review-guard.py verify <nnn>` must print `OK`: it reads `.git/config`, the active hooks folder (`core.hooksPath`, `.githooks` on every project today) and `.git/hooks` first, as files, without git — a `core.fsmonitor` line or a hook left there would run the reviewer's program with your identity on your next git command, and a change there stops the guard before it runs any git command of its own; every git command it then runs has the repository's hooks and file monitor switched off. It checks HEAD, the branch, the local refs and the stashes, puts the branch and every moved or added local ref back, restores the tree with `git reset --hard` and `git clean -fd` (keeping the `.err` file, whose first line — the launch time — it prints), lists what it removed, and compares every ignored file (cache folders apart): a change under `docs/`, `handoff/` or `run/review/`, or to `.env*`, is a flag even where the project gitignores those files; any other is listed as left behind. `GATE-INTEGRITY` — a commit, a moved HEAD, a new or moved ref or stash, a changed configuration, hook, record or `.env` — opens the flag (condition 4) and an issue; the tree is back at the checkpoint, the merge is not. It prints the snapshot file's hash, which must equal the one `snapshot` printed (a reviewer could rewrite the snapshot). What the guard cannot see is said in its header and KP-032: the contents of cache folders, anything outside the checkout, a reviewer that reaches for the credential store on purpose. **Note the
   launch time in UTC** — the
   launcher prints `bridge-run: started <time>Z` as its first stderr line, so it is the
   first line of the `.err` file. The launch carries the Bash tool's `timeout` at the review
   cap (`7200000`, step 3). Before the launch, write `run/review/SCOPE-<nnn>.md` and commit
   it beside the diff (removed with `git rm` with it): the brief's Scope and Out of scope
   sections quoted, the tests and mutation drivers you wrote with the paragraph each enforces, and the
   bookkeeping and record files in the diff that are expected (`docs/BUILDER_NOTES.md`, the
   builder's report `handoff/TASK-<nnn>-r<N>-report.md`, the records you committed,
   `run/review/`). Nothing of this goes inline through the shell,
   which mangles quoted text (KP-009). Give a **directive** prompt ("the diff is already at
   `<path>`; read it; do not ask for it") with four short clauses (release A5): where the
   increment ends and which tests the supervisor wrote are in `run/review/SCOPE-<nnn>.md`,
   read it; design for later increments is not this diff's defect (a reviewer once reviewed
   design for later increments for nine rounds on one of them); verify a claim about a build
   by building it, never by reasoning; reply with APPROVE, REJECT or ESCALATE-INTENT and the
   reasons. A reply that does not name something specific from the diff — or that asks for
   the diff, errors on trust, or carries none of the three verdicts — is a failed launch,
   not a verdict: re-run once, then the roster's failure path (step 3b). Confirm receipt before trusting the verdict; with the guard's `OK`
   in hand, **`python ~/.claude/cursor-bridge/pr-activity-check.py <n> --since <that launch time>` printing `OK`**: it lists what was written to the pull request since the launch and flags anything written as the owner (KP-032). `GATE-INTEGRITY` opens a gate-integrity flag (condition 4) and an issue; `CANNOT VERIFY` is not `OK`;
4. no gate-integrity flag is open — the diff does not weaken tests, assertions, or CI, and
   the builder's model family differs from both reviewers'.

**Convergence is a signal.** When two or more reviewers or auditors independently name the
same line or the same defect, treat it as blocking even if each alone marked it advisory:
decorrelated reviewers agreeing is the strongest evidence the loop produces. This is the code
gate's rule; a design critique's two critics are bounded by its ceiling instead (Phase 2).

A `REJECT` from either reviewer goes back through re-delegation (step 7), not to the user
— continue while concerns converge and get fixed, stopping only on non-convergence per
step 7's brake. A **split** verdict (one reviewer blocks, the other approves) you resolve
yourself, favouring the project's established invariants; escalate it only if it turns on
intent. An `ESCALATE-INTENT` verdict, and only that, surfaces to the user — as a plain
intent question, never a correctness one.

**PR titles start with every increment ID the branch carries** (`TASK-012 TASK-013: settings key store`): the squash commit takes the title, and that subject on `origin/main` is how `plan-check.py` knows an increment is merged.

When all four hold the merge is authorised. A pull request that changes only records (`docs/`, the inventory, a design text) takes the same round: snapshot, Review B, `verify`, then `premerge`; `premerge` refuses a head whose snapshot has no verified mark, so there is no shorter way (release A1b). **Check `docs/RUN_PARAMETERS.md` first:** under
`Merge authority: owner`, stop here with **READY TO MERGE** — the PR link, the four
conditions with their evidence, and a one-line run sheet to merge — and wait; never arm
auto-merge. Under either authority, remove the review files with `git rm`, commit (that commit removes the review files and nothing else: a records edit in it is a change outside `run/review/`, which `premerge` refuses as GATE-INTEGRITY; the records move after the merge), push, and run `python ~/.claude/cursor-bridge/review-guard.py premerge <nnn> <n>`: `OK` means the head about to merge descends from the head the reviews approved, differs from it only under `run/review/`, and is the pull request's head on GitHub; it prints the merge command, `gh pr merge <n> --squash --match-head-commit <sha>`, which refuses to merge any other head. A head that does not descend from the reviewed one, or a change outside `run/review/`, is a gate-integrity flag. A branch updated from `main` on GitHub ("Update branch") is a new head: the reviews run again on it — a re-review, not a flag. Under `supervisor` (the default), arm `gh pr merge <n> --squash --auto --match-head-commit <sha>` (the sha `premerge` printed and recorded) and watch the
required `gate` check — **with one background command, never by ending your turn**: run `python ~/.claude/cursor-bridge/bridge-run.py --limit 3600 -- gh pr checks <n> --watch --required --fail-fast` in the background with the tool's `timeout` at the watch cap (`7200000`, step 3; `run_in_background`). Its completion notification is what wakes you; nothing else will. The launcher ends a watch that outlives an hour (exit 124: look at the pull request's checks yourself, then start a new watch); never prefix the command with anything else (`sleep`, `cd`, `timeout`): the rules match the command as written, and a wrapped command matches nothing. If it returns at once reporting no checks, CI has not registered the push yet: wait for the first check to appear (`gh pr checks <n>` once, a minute after the push), then start the same watch again; and when any watch ends green, confirm that the green run's head is the pushed head (`gh pr view <n> --json statusCheckRollup,headRefOid`) before `premerge` — a watch started right after a push once reported the previous commit's run (KP-051). The desktop app's CI monitor ("Auto-fix pull requests", `<ci-monitor-event>`) reports only problems — a failed check, a review comment — and **never a green gate**, so waiting for it after a green run waits forever (KP-028). Registering the PR with it is fine and its autofix of a failure is welcome, but it is never your wake-up. The owner authorises and requires this watch: it is one blocking command per PR, not a polling loop — never `sleep` loops, repeated status checks, or scheduled wake-ups for this. **While it runs, keep building:** if the next increment's Scope does not overlap the pending PR's files, start it now from `origin/main`; if it does overlap, prepare what does not depend on the merge (the next brief, reviews, docs), and only then end your turn — the watch will wake you. When the watch completes green (and the PR is mergeable), **complete the squash
directly with `gh pr merge <n> --squash --match-head-commit <sha>`** (the sha `premerge` printed) rather than waiting on GitHub's auto-merge queue,
which routinely lags by minutes. This is safe — branch protection enforces the required
check regardless of who triggers the merge, so a direct merge cannot bypass CI; the armed
`--auto` is only a safety net if the session ends first. Never complete a merge before the
required check is green or before both reviews APPROVE. No human correctness click is
involved; the merge is reversible, so a rare behavioural miss is caught retrospectively via
the change log, not by a gate the user cannot operate. If the watch completes red, the failure is a defect like any other: diagnose, re-delegate, re-run the gate — never merge around it.

**After every merge, mark the increment's runs healthy and bring local `main` along.** `python ~/.claude/cursor-bridge/bridge-run.py --healthy <run id>` for the builder run and for Review B, the id being the launch time on the first line of each `.err` file, given whole (a test run that passed is marked by the launcher itself): a healthy run is what the launcher learns a ceiling from, and a run never marked never raises one (release A2). Then `git switch main`, then `python ~/.claude/cursor-bridge/sync-check.py --apply`; it must end IN SYNC or FAST-FORWARDED before anything else happens, and the next branch starts from there. Under `Merge authority: owner`, do the same at the first resume after the owner has merged. A worktree the merged branch had is torn down now (rule 39).

## Extension points

This module offers the points below, each by its key in the extension-point registry (`~/.claude/cursor-bridge/workflow/extension-points.md`), which states the kinds of change each accepts and whether it applies per part or per project. A conditional workflow's additions at a point are made where the point's line places them, in the order the core states in "Main and conditional workflows".

- `delegation-loop.inspect-checks` — checks and reviews a conditional workflow adds to the inspect step, on every change of the part the loop checks (an increment, a fix, a refactoring candidate, or the refactoring branch's gate pass in step 9), each placed at the step that runs it: beside the scope and design-conformance checks or among the reviewer passes (step 4), or with the secret scan and the dependency admission (steps 5 and 5b); a finding is handled as that step handles its own: a blocking one re-delegates (step 7), a builder's objection goes to "Objections — bottom-up escalation", and a consequence the owner bears goes to the owner (rule 56).
- `delegation-loop.test-checks` — tests and checks run with the tests of every change of the part the loop checks (step 4: the change's tests, the suite, the new tests against the checkpoint), such as the observability tests of a part with screens or the benchmark floor (step 6); a failing one is a correctness-class block, re-delegated like any defect (step 7).
- `delegation-loop.brief-constraints` — constraints every brief for the part carries beside spec-packager's template, such as a frozen rule the builder must follow, written into the brief at step 2 and checked by `diff-reviewer` with the rest of the brief.
