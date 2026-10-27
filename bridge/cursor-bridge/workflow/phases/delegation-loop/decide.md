## The decision (Phase 6, step 7)

### Where this sub-file belongs

This file is a sub-file of the delegation-loop module (`delegation-loop.md`, "The procedure"), read whole with it. It holds the loop's step 7, which runs for every increment after step 6 and before step 8, the merge: the decision on the increment, and the mutation run each pass through the step launches before step 8's snapshot. It stands in a file of its own to keep the module within its size bound.

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

#### The mutation run

The increment's mutants are in its mutants file, `run/supervisor/<id>-mutants.json`, which you wrote at step 4 with the criterion tests, never the builder. The mutation run is launched here, on every pass through this step: once Review A and the auditors have accepted the increment's behaviour, and before step 8's snapshot; never at every round's step 4 (the owner's decision of 2026-10-20: the mutation run comes when the increment is otherwise accepted, not every round). The new tests' run against the checkpoint (`--checkpoint`) stays at step 4, before any reviewer. The Accept bullet's commit may come before the run; the move to the next increment waits for its result. Launch the run in the background through the launcher's driver kind, under the heavy launch's `timeout` (`delegation-loop.md`, step 3):

```bash
python ~/.claude/cursor-bridge/bridge-run.py --limit auto --kind driver -- python ~/.claude/cursor-bridge/mutation-run.py run/supervisor/<id>-mutants.json > run/agent/<id>-mutation.out 2>&1
```

Its completion wakes you, and the step resumes when it arrives. The program reruns only what changed: a mutant whose keyed inputs (the mutated file's folder, the test folders it runs, the suite's configuration and the mutant itself) are byte-identical since its last kill keeps that kill, and every survived, unapplied or erred mutant runs again. Add `--all` for the full run where a round changed files outside every key.

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
