## The decision (Phase 6, step 7)

### Where this sub-file belongs

This file is a sub-file of the delegation-loop module (`delegation-loop.md`, "The procedure"), read whole with it. It holds the loop's step 7, which runs for every increment after step 6 and before step 8, the merge: the decision on the increment, and the mutation run each pass through the step launches before step 8's snapshot. It stands in a file of its own to keep the module within its size bound.

### 7. Decide (accept the increment)

- **Accept** — local review, scan, and tests pass. Run `scope-check.py` once more just
  before this commit (its base is the commit that committed the brief, so a builder's own
  commits are inside the diff; release A4). Commit to the increment branch with a
  message referencing the task ID, every count and every claim of a check in it quoting the output line that shows it (a reviewer compares each count with its line). Then the records go in a records-only commit after the accept commit: update `docs/PROJECT_STATUS.md` (rewrite the fields; never append history) and, when the increment changes behaviour or needs a new resource, `docs/INVENTORY.md`, with the increment's `CHANGES.md` entry in the same records commit, moving `Reflected through:` to that entry (rule 41); when the increment completes a requirement, set its row in `docs/REQUIREMENTS.md` to `built` and name the tests — which carry the requirement's ID — in its Evidence cell, in that records commit. Move to the next
  increment. Increments accumulate on the branch; merging to `main` is a separate,
  verified step (below), not something you do per increment.
- **Iterate** — something is wrong and you understand why. Write the next numbered brief,
  `handoff/<ID>-r<N>.md`, with specific corrections (never a revision in place, step 3), commit
  it, and re-issue the same constant delegate command, naming it. Never inline the corrections into the CLI prompt (step 3).
- **Re-delegate on a review REJECT** — if a reviewer rejects the work (see step 8), that
  is a code defect, which is the loop's problem, not the user's. Feed the reasons into the
  next numbered brief and re-delegate — again via the file, never the prompt. This does
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
(spec-packager's fix variant) carrying the confirmed cause, the
evidence, and the reproduction test that must go red to green. Inside an increment's gate the fix
brief is the increment's next numbered brief, `handoff/<ID>-r<N>.md`, so that no fix within a gate
opens a budget of its own; `handoff/BUG-<nnn>.md` is the brief of a defect found after a merge. Three diagnostic rounds
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
  increment's PR branch) and merge. A late finding blocks the merge only if it is of one of
  the five **blocking classes** — behaviour against the brief or the register, security, data
  integrity, a defeated safety mechanism this increment relies on (a bug in the very timeout or
  kill path built to protect the run is core, not tail), a failing test. What a defect of the five is for the project is bounded by its threat model, recorded in `docs/INVENTORY.md` (Decisions) with its reason and what would reopen it and given to the reviewers with the diff, for the parts the model names: a finding in those parts outside it is recorded, not blocking, whatever its label and however many reviewers name it, and where the inventory records none for the part a finding is in, the five stand unbounded. Within it, a finding is a member of a blocking class when it reproduces as a regression or a false result on an ordinary, realistic project layout, a reviewer's label alone never deciding: one that needs a contrived setup goes to `docs/HARDENING.md` with the increment, and a security finding is judged instead by whether untrusted input can reach it (files a builder or reviewer writes, a cloned or third-party repository), never by the layout's ordinariness. Two reviewers naming the same late finding make it certain, never blocking of itself: it blocks only where its content is of the five (step 8, "Convergence is a signal"). The class is the
  defect, not the operator that exposed it: a further mutant, input or operator family that
  shows a class already recorded in `docs/HARDENING.md` under the by-class line for the
  increment or the stage is that class and never a new one, while a defect of one of the five blocks
  whatever was recorded before. Below the ceiling, drawing this line is a decision you make and
  record, not one you bring to the user; at and above it the line is the rule ("The review
  ceiling", below).
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

#### The review ceiling

The code gate stops at three rounds per increment, the owner's number at the plan's gate (2026-10-24), held by two programs (R-042). **A round** is one version of the increment the gate's reviewers read: each builder run of a numbered brief (`handoff/<ID>.md`, then `handoff/<ID>-r<N>.md`, step 3), and each Review B read that `review-guard.py snapshot <ID>-r<N>` opens (step 8), spent when its reply arrived. A fix you make and Review A re-reads before step 8's snapshot is no round, and a failed launch's re-run re-snapshots the same tree under the same name. **The count the gate reads** is the guard's count of rounds opened for the increment, which your report names; the launcher's count of builder rounds holds the briefs to it. The two move independently — a Review A rejection spends a builder round with no snapshot, a fix of yours after a Review B REJECT a guard round with no builder run — so where a next count matters, take the larger of the guard's and the launcher's.

**Below the ceiling** the brake above is your judgment, and the by-class line yours to draw. **At and above it** — the guard's count of rounds opened for the increment at three or more — only a finding of one of the five blocking classes (behaviour against the brief or the register, security, data integrity, a defeated safety mechanism the increment relies on, a failing test) sends the work back; every other finding goes to `docs/HARDENING.md` under the increment and merges with it. Every reviewer and auditor grades each finding by the five first, a convergent finding included (step 8).

**A round above the ceiling is lifted** one of two ways:

- **A class line**, `Blocking class: <class> - <the finding>`, its `<class>` one of `behaviour`, `security`, `data integrity`, `safety mechanism` and `failing test`, its finding naming the reviewer's finding it answers (`Review A, round 3, B1`, say). You write it into the brief before the builder launch, where the launcher reads it, and into `run/review/SCOPE-<ID>.md` before the snapshot, where the guard reads it; a line lifts the one round it was written for. The reviewers are told of the line and confirm or deny it against the code of the round it lifted as that round's builder found it — the commit that round's builder was launched on, its brief's commit (for a round of your own fix, with no builder run, the head the previous round's snapshot recorded), which you name beside the line at step 4 and in the SCOPE file, the brief carrying the line alone — never against the fixed code under review: a reviewer's denial voids the round's result and withholds the merge as GATE-INTEGRITY does, and the breach is recorded in `docs/HARDENING.md` under the increment and as an issue.
- **The owner's line** in `docs/RUN_PARAMETERS.md`, `Review rounds above the ceiling: <ID> <rounds> (<their words>, <date>)`, written only on the owner's own words and never asked for; its `<rounds>` is at least the larger of the guard's and the launcher's next counts for the increment, the count your report names when the ceiling is reached.

**The refusals are stops, not failures.** The launcher's `bridge-run: refused - review ceiling: ` and the guard's `review-guard: refused - review ceiling: `, and their other refusals of the ceiling's rules (the launcher's `brief rule: ` and `revised in place: `, the `branch rule: ` either prints, a brief revised after a completed run, a new round under a name whose round already has its reply or off the count, a brief or a snapshot under another ID on a counted branch), are the ceiling's programs holding: neither a failed launch nor a model's failure (step 3b), never retried as one and never passed to `roster-check.py`. Read the refusal; then write the next numbered brief or the round's right name, write the class line where a blocking-class finding stands, or record the finding in `docs/HARDENING.md`.

A stage review is bounded the same way (`STAGE-<name>-r<N>`, the reflection module's step 7).

#### The mutation run

The increment's mutants are in its mutants file, `run/supervisor/<id>-mutants.json`, which you wrote at step 4 with the criterion tests, never the builder. The mutation run is launched here, on every pass through this step: once Review A and the auditors have accepted the increment's behaviour, and before step 8's snapshot; never at every round's step 4 (the owner's decision of 2026-10-20: the mutation run comes when the increment is otherwise accepted, not every round). The new tests' run against the checkpoint (`--checkpoint`) stays at step 4, before any reviewer. The Accept bullet's commit may come before the run; the move to the next increment waits for its result. Launch the run in the background through the launcher's driver kind, under the heavy launch's `timeout` (`delegation-loop.md`, step 3):

```bash
python ~/.claude/cursor-bridge/bridge-run.py --limit auto --kind driver -- python ~/.claude/cursor-bridge/mutation-run.py run/supervisor/<id>-mutants.json > run/agent/<id>-mutation.out 2>&1
```

Its completion wakes you, and the step resumes when it arrives. The `python` after the `--` is the project's own interpreter, the one its recorded suite command runs, since mutation-run.py runs every mutant's and every checkpoint test's pytest with the interpreter that started it: where the project has a virtual environment it is `.venv/Scripts/python.exe` (`.venv/bin/python` off Windows), which the driver kind accepts; a bare `python` that is not the project's lacks its packages and fails closed. The program reruns only what changed: a mutant whose keyed inputs (the mutated file's folder, the test folders it runs, the suite's configuration and the mutant itself) are byte-identical since its last kill keeps that kill, and every survived, unapplied or erred mutant runs again. Add `--all` for the full run where a round changed files outside every key.

**Before the run, cut the duplicates and estimate the count.** Before the increment's first mutation run, before any `--all` run, and whenever the mutants file has changed since its last estimate:

1. **Cut what the file itself shows redundant.** A mutant whose `file`, `pairs` and expectations (`tests`, `expect_fail`, `expect`) equal another's is the same mutant under a second `id`: remove its entry from the mutants file before the launch, so the program never applies it. This needs no run and no kill, and nothing else is cut: never a criterion test, and nothing on the strength of a kept kill (the cache's skipping is the program's own, and an `--all` run is chosen exactly where a kept kill is distrusted).
2. **Estimate the run's process count** to its order of magnitude, from the file as it stands after the cut. For each distinct `tests` list among the mutants the run will apply (every mutant for `--all`, otherwise those with no kept kill; two lists naming the same test files in any order are one list), count the processes one completed run of that list starts: the pytest process, plus every launch its tests make, counted once per pass the run makes through it (each parametrization, each loop iteration), plus the programs those launched programs start in turn. Read the launches from the launcher's run log (`run/launcher/runs.jsonl`) where they go through the launcher, since it holds the launcher's runs and nothing else, and otherwise from the launch sites in the tests and in the programs they launch, with their pass counts; a counting run is launched the way step 4 launches a run of its kind. Reuse each list's count for every mutant that lists it: the sum over the mutants to apply, plus the one collection check, is the estimate.
3. **Write both down**: the cuts made and the estimate go on `run/supervisor/in-flight.md`, with the mutants file's name.

A driver rerun whole between review rounds once launched one program 52,000 times in a morning (the bridge's ISS-011); the cut removes the redundancy the file shows, and the coverage and its certainty stay (the owner's words of 2026-10-20: the fix "must not cut down on quality or certainty of proper test coverage. Redundancy should be cut").

**What the run's result does:**

- **Exit 0** — every mutant was killed, or keeps its kill: go on to step 8.
- **Exit 1** — a mutant survived or was not applied, or an `expect: survive` mutant was killed. Take the larger of the two next counts: the review guard's rounds opened for the increment plus one, and the launcher's round of the brief that would carry a code fix. Where it is at or below the code gate's ceiling of three rounds, the mutant is fixed: a criterion test's fix is yours and no round; a code fix is a re-delegation (above) and a round. A mutant not applied (its text no longer in its file) is re-anchored in the mutants file, yours and no round; a fix of yours after Review A's read stands in the diff Review B reads at step 8. Above the ceiling, the mutant goes to `docs/HARDENING.md` under the increment and never to a re-delegation, unless the code it shows untested is a safety mechanism the increment relies on, or the result shows a defect of a blocking class (behaviour against the brief or the register, security, data integrity, a defeated safety mechanism, a failing test).
- **Exit 2** — the mutants file or a path in it was refused: correct the file and launch again. Or the program's resolution check refused the run; where the cause is an editable install of the package (KP-054; step 4 tells it apart and records it as an issue the first time), no correction helps, so the run is not made, `mutation run not made: editable install` goes on `run/supervisor/in-flight.md` and into the SCOPE file, and the reviewers' reading of each mutant against its name stands in; it is the run's own result, never a model failure.
- **Exit 3** — a mutant erred or the program failed: the step stops, and the result is the run's own, recorded as such, never a model failure; no exit of the program is passed to `roster-check.py`. A run that ended at its limit or was killed from outside is relaunched as step 3b says.
