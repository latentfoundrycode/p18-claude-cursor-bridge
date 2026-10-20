## Run parameters — asked once, after the plan is approved, before configuration

### What must survive a compaction

After a compaction or a resume in this step, read these before your next action:

- this module, whole;
- `docs/RUN_PARAMETERS.md` as written so far, whole: each answer is written there as the owner gives it ("Writing the answers down"), so the questions still to ask are the parameters it does not yet hold;
- `docs/BUILD_PLAN.md`, the approved plan, whole: a refactoring answer may name its stages, and parallel increments apply only where the plan marks increments `Parallel: yes`;
- `docs/PROJECT_STATUS.md`, whole: its `Workflows:` line names each part's conditional workflows, which add parameters at `run-parameters.parameters` and show whether a part is installable, as installer verification needs, and its `Awaiting user on:` line names the question that waits for the owner.

### The procedure

The plan says *what* will be built; the run parameters say *how the loop proceeds* while
building it. They are the owner's settings, asked **once, right after the plan gate and
before Phase 5, each as a question of its own in the app's question form** (`AskUserQuestion`,
the default named first, each explained under the `explain-for-decision` skill), never as
one combined brief (rule 29). The parameters:

1. **Stage pause** — what happens when a stage closes (its last increment merged, the
   refactoring pass merged if on, the reflection point written).
   - `run` *(default)* — report the stage close as a notification and **continue into the
     next stage without waiting.** In practice: do not end your turn at a stage close; the
     stage-close report is text in the transcript, and the next action follows in the same
     turn. Only the escalation list (below) and project end stop the loop.
   - `pause` — stop at every stage close with "Stage <name> closed — say *continue*" and
     wait. The owner chooses this when they want to look at each milestone before the next
     begins.
2. **Merge authority** — who completes a merge to `main` once the full gate holds (CI green,
   Review A and Review B APPROVE, no gate-integrity flag).
   - `supervisor` *(default)* — you arm and complete the merge yourself (step 8, the merge
     policy). This is what "AI-handled automatic merging" in the guides means, and it needs
     the per-repo setup the startup guide describes.
   - `owner` — you do everything up to the merge, then stop with **"READY TO MERGE"**: the
     PR link, the four gate conditions with their evidence, and the one-line run sheet to
     merge it. You never arm auto-merge under this setting. This is a deliberate pause per
     PR, so with `stage pause = run` the loop still waits here; say so when the owner picks
     it.
3. **Refactoring pass** — whether Phase 6 step 9 runs at each stage close: `on` *(default)*
   or `off`, for the whole project or for named stages. It costs one extra gate pass per
   stage (one cross-family review) and buys a codebase that does not accumulate duplicates;
   the builder runs it needs are cheap.
4. **Installer verification** *(installable software: desktop applications, command-line
   tools, local servers)* — where the packaging stage's install / upgrade-in-place /
   uninstall lifecycle check runs (`installer-check.ps1` for a desktop installer; the
   project's `scripts/install-check.ps1` for an install script).
   - `local` *(default)* — on this machine, per-user, silently, fully reversed at the end
     (nothing is left installed, user data is never touched). Say plainly that the check
     installs and uninstalls the app on the owner's PC while it runs. Your own run is a
     rehearsal of the installer's logic; the delivery's proof is the owner's run from their
     terminal by a run sheet (KP-055, release A5).
   - `ci-only` — only on a `windows-latest` CI runner; nothing is ever installed here.
5. **Parallel increments** — whether independent increments the plan marks `Parallel: yes` may have their builders run at the same time (Phase 6 step 3, "Parallel increments").
   - `off` *(default)* — one builder at a time.
   - `on` — ready independent increments are built at once, each builder in its own worktree; reviews, tests, and merges stay one at a time. It saves elapsed time on plans with many independent increments. Say the price plainly: a builder in a worktree cannot run the project's tests, so its first delivery may need one more round; and this mode has not yet run on a real project, so its first use is a trial.

Record the answers in **`docs/RUN_PARAMETERS.md`**, which you read at every resume and
before every stage close and merge:

```markdown
# Run parameters
Set: <date>   (owner may change any of these at any time by saying so; update this file)
Stage pause: run | pause
Merge authority: supervisor | owner
Refactoring pass: on | off | off for <stages>
Installer verification: local | ci-only | n/a (not a desktop application)
Parallel increments: off | on
```

Three optional lines are never asked and are written only on the owner's recorded word (release A2; the third 2026.10.18a): `Agent ceiling: <seconds>` raises the hour a background agent may run before the loop guard stops counting it, `Ceiling above twice: <kind> <seconds> (<the owner's words>, <date>)` lets the launcher's learned limit for one kind of run (builder, review, watch, test) exceed twice its default, and `Design rounds above five: <subject> <rounds> (<the owner's words>, <date>)` lets one subject's design critique run past its ceiling (Phase 2; written before this step when the subject is the design or the plan).

The **model pool state** is not a run parameter — it changes with the owner's usage, not
with the project. `"other_pool"` in `docs/ROSTER.json` is flipped to `exhausted`
**automatically** when a call returns a usage-limit error (Phase 6 step 3b) or by the owner
saying "usage exhausted" pre-emptively; it returns to `available` **automatically on the
roster's `reset_day` (UTC)** after the exhaustion, or earlier when the owner says "usage
reset".

**What no parameter changes.** The "Escalate to the user when" list stays in force under
every setting: product behaviour, scope, a user-level consequence, something only the owner
can provide, an irreversible or out-of-repo action, a change to what "correct" means. Those
stop the loop whether stage pause is `run` or `pause`. Project end always stops. And no
parameter loosens the gate: `run` means *no waiting between stages*, never *less checking
within them*. The owner may change a parameter mid-project by saying so; you update the
file and apply it from the next stage close or merge on, never retroactively.

### Writing the answers down

Write each answer into `docs/RUN_PARAMETERS.md` as the owner gives it, in the form above, the `Set:` line with the first: a compaction between two questions then loses no answer, and a resume asks only the parameters the file does not yet hold. A parameter that does not apply to the project, such as installer verification for software that installs nothing, is written as `n/a` when it is passed over, so a resume does not ask it. A parameter a conditional workflow adds at `run-parameters.parameters` is asked and written the same way. A parameter is a setting, never a key: a key, token or password the owner pastes in an answer is never written to the file, rule 53 applies to it, and no path on this computer is written there either (rule 54).

## Extension points

This module offers the points below, each by its key in the extension-point registry (`~/.claude/cursor-bridge/workflow/extension-points.md`), which states the kinds of change each accepts and whether it applies per part or per project. A conditional workflow's additions at a point are made where the point's line places them, in the order the core states in "Main and conditional workflows".

- `run-parameters.parameters` — parameters a conditional workflow adds to the five above, each asked as a question of its own in the same form with its default named first, and written as a line of its own in `docs/RUN_PARAMETERS.md`; made once for the whole project.
