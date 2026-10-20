# Design critique: the window flood's fix (subject `windowless`), round 1

## What is criticised

A scoped revision of the Claude-Cursor Bridge's release B plan, mid-build, at the owner's decision of 2026-10-20. On the night of 2026-10-19/20 many visible terminal windows opened on the owner's computer while they slept; Windows Terminal crashed under them and the frozen frames still crash the PC when clicked (ISS-011). The maintainer's process-start record (06:54-10:20 local only) shows 218k process starts in 3.5 h, about 202k of them the bridge supervisor's: 52k launches of session-start.py by a mutation driver (run/supervisor/task015_mutants.py) that ran its whole set about twelve times, once per review round, at up to 758 launches a minute; no window opened inside the recorded window, so the window source is earlier and unproven; the bridge's own tests and drivers hide their windows (FIX-001), but another project running at the same time (the TDP) ran its suite and drivers directly, not through the launcher, with no suite-wide default. The owner decided: the fix goes into the bridge and is installed and calibrated, never fixed per project; a rate limit on heavy runs that cuts redundancy but never coverage or certainty; running where no window can exist (WSL) is a later release; and this is an update inserted at the right spot of the plan, not a hotfix.

The revision: three rows of the register (R-039 windowless launches enforced by the bridge; R-040 one heavy job at a time; R-041 mutation reruns that skip only what is unchanged), two Decisions rows recording the owner's words, and three increments in stage B5 before the acceptance increment: TASK-028 (builder: the launcher's driver kind, every launch windowless, the suite's frozen default shipped as a snapshot, the conformance floor), TASK-029 (builder: the machine-wide slot in the launcher; mutation-run.py with its cache), TASK-030 (supervisor: the loop's, the configuration's and calibration's text). The register rows and the Decisions rows are the design revision; the increments are the plan addendum; one subject holds both (design.md, Phase 2: a scoped revision mid-build is one change). The texts are read by an AI supervisor who will write the briefs from the Done when lines and by the builder who implements them.

Judge: whether the increments do what the owner's words ask and no more (the fix in the bridge for every project; redundancy cut, coverage and certainty kept; the right spot); whether each Done when is checkable by a specific observable outcome and can be met as written on Windows (the lock file's location and takeover, the wait's bound and its reporting, the cache key, the Node runner's default); the author split (programs by the builder, text by the supervisor); ordering and file collisions (bridge-run.py, conformance-check.py, delegation-loop.md, configuration.md, calibrate-bridge.md are edited by other increments too); the R-032 bound of delegation-loop.md (at 92% after TASK-013); whether every new requirement is satisfied by an increment; what INVENTORY already settles (FIX-001's default, the windowless check in the pre-commit gate, the conformance floors, the launcher's accepted commands, the mutation drivers written by the supervisor and run on a scratch copy outside the Workspace) and whether anything here rebuilds or reverses it; and the pitfalls (KP-014 windows, KP-053 the Bash tool's thirty minutes, KP-056 interrupted drivers, KP-061 the ten-minute foreground limit, KP-033 orphans).

## The record so far

## Subject: windowless (the window flood's fix: windowless launches and a rate limit, a scoped revision mid-build, 2026-10-20)

**What is criticised:** a scoped revision of release B's plan at the owner's decision (ISS-011), one subject holding both its design revision — three rows of the register, R-039 to R-041, and the INVENTORY Decisions rows that record the owner's words — and its plan addendum: TASK-028, TASK-029 and TASK-030 in stage B5 before TASK-025, the stage's demonstration extended, TASK-025's and TASK-027's lines amended. The design revision is three rows because the design is the owner's words as relayed and confirmed; the subject is one because a scoped revision mid-build is one change (design.md, "The procedure": the subjects). The critics read `run/review/DESIGN-windowless-<round>.md`, built from the committed records.

**Accepted** (finding, critic, round, the reason):
- (none yet)

**Rounds** (round, kind, the commit its file was built from, critic, Blocking / Should fix / Consider, what was fixed):
- (none yet)

**Resolution**: (none yet)

## Grades

- **Blocking**: the plan cannot go to its gate with it.
- **Should fix**: the supervisor fixes it or accepts it with a reason.
- **Consider**: worth a thought; no round follows from it.

End with the counts per grade. Four rounds at the most, then a confirming read if the text changed, then one resolution round for what is still open.

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

## The new and changed passages, whole as they now read

### REQUIREMENTS.md, the register's revision note

````markdown
Revised 2026-10-20 at the owner's decision on the window flood of 2026-10-19/20 (ISS-011; the maintainer's findings relayed with the owner's words, confirmed in the supervisor's chat): rows R-039–R-041 added, their source the owner's decision rather than the Restructuring Plan; critiqued as the subject `windowless` (docs/DESIGN_CRITIQUE.md).
````

### REQUIREMENTS.md, the new rows

````markdown
| R-039 | Windowless launches are enforced by the bridge for every project, never by a per-project fix: every heavy run of the loop — a builder, a project's test suite, a mutation driver the supervisor writes under `run/supervisor/` — starts through the launcher (`bridge-run.py`), which starts it with no window so that every process it creates inherits that; and every project's test suite carries the bridge's frozen windowless default (FIX-001's `tests/conftest.py` default, shipped as a snapshot like the secure-coding rule), written at configuration, reported by the conformance check as a floor at every calibration and reflection point, and installed into a running project by calibration. | the owner's decision of 2026-10-20 (ISS-011): "I'd rather have the solution implemented in the bridge … and afterwards installed and calibrated, than fixing it in each session"; rule 24; KP-014 | planned | — |
| R-040 | One heavy job at a time on the computer: a builder run, a full test suite and a mutation run each hold a machine-wide slot in the launcher while they run, a second heavy run waiting for the slot and saying so; a review and a CI watch take none. | the owner's decision of 2026-10-20 (ISS-011): "There definitely needs to be a rate limit on the tests that necessitate evoking a terminal" | planned | — |
| R-041 | Mutation reruns skip only what is unchanged: a mutation driver reruns a mutant only when the code it mutates or the tests it runs changed since the mutant's last killed result, every survived or unapplied mutant runs again, and every mutant runs against the final code once before the gate — the redundancy cut, the coverage and its certainty kept. | the owner's decision of 2026-10-20 (ISS-011): "what we decide here must not cut down on quality or certainty of proper test coverage. Redundancy should be cut" | planned | — |
````

### INVENTORY.md, the Decisions rows

````markdown
| The window flood of 2026-10-19/20 (ISS-011) is fixed in the bridge, as release B's TASK-028 to TASK-030 in stage B5 before the acceptance increment, installed and calibrated with release B — not per project, and not as a hotfix: windowless launches enforced by the launcher and a frozen suite default every project carries (R-039); one heavy job at a time on the computer (R-040); mutation reruns that skip only what is unchanged and run every mutant once against the final code before the gate (R-041) | the owner's words of 2026-10-20, relayed by the maintainer with its findings (the process-start record of 06:54–10:20 local: 218k process starts, about 202k the bridge's, 52k of them session-start.py launched by run/supervisor/task015_mutants.py, up to 758 a minute, about twelve runs of the whole set; the window source earlier and unproven) and confirmed in this session's chat: "I'd rather have the solution implemented in the bridge as a quick fix and afterwards installed and calibrated, than fixing it in each session"; "There definitely needs to be a rate limit on the tests that necessitate evoking a terminal. However, what we decide here must not cut down on quality or certainty of proper test coverage. Redundancy should be cut"; "This problem seems to have been an outlier though. I still want it to be fixed, but not as a quick fix, but instead an update that will be inserted or appended on the right spot" | 2026-10-20, owner (the placement the supervisor's, approved in the chat) | the flood recurs before release B installs (then a hotfix of the installed release, as 2026.10.18a was) |
| Builders and test suites running where no window can exist (for example WSL) is a release after B, planned at the planning point after release B is done and accepted, beside release B2; release B's TASK-028 to TASK-030 are the nearer fix | the owner, 2026-10-20: "Long term this seems worth it" | 2026-10-20, owner | — |
````

### BUILD_PLAN.md, the plan's revision note

````markdown
Revised 2026-10-20 at the owner's decision on the window flood of 2026-10-19/20 (ISS-011; R-039 to R-041): TASK-028 to TASK-030 added to stage B5 before TASK-025, the fix made in the bridge and installed by calibration rather than per project, as a planned update and not a hotfix (INVENTORY, Decisions); critiqued as the subject `windowless` (docs/DESIGN_CRITIQUE.md).
````

### BUILD_PLAN.md, stage B5 whole (the demonstration, TASK-023 to TASK-025)

````markdown
## Stage B5 — Calibration and acceptance
Demonstration: a fresh session walked intake→configuration reads only its core, its current phase module, and its own conditional workflows; the four projects each classify under §6.3 on fixtures with `workflow-check` green; a mutation run and a test suite started together through the launcher run one after the other, the second saying what it waits for, and no window appears; the mutation run repeated with nothing changed runs no mutant, and with `--all` runs every one.

### TASK-023 — Calibration aware of conditional workflows (text)
Author: supervisor.
Parent: none
Depends on: TASK-015, TASK-017, TASK-018, TASK-019, TASK-020, TASK-021
Parallel: no
Diagrams: none
Scope: bridge/commands/calibrate-bridge.md; bridge/cursor-bridge/MANIFEST.json; tests/test_calibrate_text.py
Satisfies: R-027
Done when: calibrate-bridge.md applies a conditional workflow to a running project of that type by phase, reopens no gate, states the applied text takes effect from the next design phase or change cycle, **adds a running project's `Workflows:` line from its recorded §6.3 classification and confirms it with the owner** (the A2 precedent: calibration added `project.json`), and keeps the project's existing `Phase:` value (mapped by the hook's shared table); `test_calibrate_text.py` (names R-027) asserts those statements.

### TASK-024 — Calibration aware of conditional workflows (program)
Author: builder.
Parent: none
Depends on: TASK-023, TASK-006, TASK-008
Parallel: no
Diagrams: none
Scope: bridge/cursor-bridge/conformance-check.py; bridge/cursor-bridge/MANIFEST.json; tests/test_calibrate_program.py; docs/cli-reference.json; docs/CLI_REFERENCE.md
Satisfies: R-027, R-033
Done when: `conformance-check.py` runs `workflow-check` at calibration over a running project's status file and reports an unclassified line or one naming an unwritten workflow; `test_calibrate_program.py` (names R-027, R-033) covers a classified and an unclassified project.

### TASK-028 — Windowless launches enforced by the bridge: the launcher's driver kind and the suite's frozen default
Author: builder.
Parent: none
Depends on: TASK-024
Parallel: no
Diagrams: none
Scope: bridge/cursor-bridge/bridge-run.py; bridge/cursor-bridge/conformance-check.py; bridge/cursor-bridge/windowless-default.snapshot.py; bridge/cursor-bridge/MANIFEST.json; tests/test_bridge_run_driver.py; tests/test_conformance_windowless.py; docs/cli-reference.json; docs/CLI_REFERENCE.md
Satisfies: R-039
Done when: (a) `bridge-run.py` accepts a supervisor's mutation driver as a kind of its own — `--limit auto --kind driver -- python run/supervisor/<name>.py [args]`, a Python program whose path resolves inside the project's `run/supervisor/` with no link on the way, with no option that runs other code (`-c`, `-m`), the kind's default ceiling the test kind's (1800 s) and learned like the others, logged in `run/launcher/runs.jsonl`; a program elsewhere or another form is refused with exit 125 and a message naming the rule; (b) every command the launcher starts, the driver included, is started with `CREATE_NO_WINDOW`, and a test proves on Windows that a grandchild of a driver run through the launcher has a console with no window (the probe `tests/test_tests_windowless.py` uses; skipped elsewhere with the reason); (c) the bridge ships the suite's windowless default as frozen text, `bridge/cursor-bridge/windowless-default.snapshot.py` — `tests/conftest.py`'s `windowless_kwargs` and the `Popen` wrapper it installs (FIX-001), with the docstring that says why — and a test asserts the bridge's own `tests/conftest.py` holds that text verbatim, so the snapshot and its source cannot drift; (d) `conformance-check.py` gains the floor `Windowless test suite`: a project whose suite is pytest is OK when its root `tests/conftest.py` (or the `conftest.py` beside its `pytest.ini`/`pyproject.toml`) defines `windowless_kwargs` and installs the wrapper on `subprocess.Popen.__init__` guarded by `CREATE_NO_WINDOW`, else MISSING naming the snapshot and `Cursor-Project-Configuration.md`'s item; a project whose suite is a Node runner (a `test` script naming vitest, jest, playwright or `node --test`) is OK when a setup file the runner's configuration loads sets `windowsHide: true` as the default of `child_process`'s launches, else MISSING the same way; a project with another runner, or none the check can see, is a NOTE naming what it saw — values are never read, and the check reads only the project's files; (e) `tests/test_bridge_run_driver.py` (names R-039) covers the accepted driver, each refused form, the kind's ceiling and its log line, and the windowless grandchild; `tests/test_conformance_windowless.py` (names R-039) covers OK, MISSING and NOTE for pytest and for a Node runner on fixtures built in the test, never a real project's file, and the bridge's own Workspace as OK; the command reference regenerated and `windowless-check.py` green over the two programs; no new dependency.

### TASK-029 — One heavy job at a time, and mutation reruns that skip what is unchanged
Author: builder.
Parent: none
Depends on: TASK-028
Parallel: no
Diagrams: none
Scope: bridge/cursor-bridge/bridge-run.py; bridge/cursor-bridge/mutation-run.py; bridge/cursor-bridge/MANIFEST.json; tests/test_bridge_run_slot.py; tests/test_mutation_run.py; docs/cli-reference.json; docs/CLI_REFERENCE.md
Satisfies: R-040, R-041
Done when: (a) the slot: a run of kind `builder`, `test` or `driver` takes one machine-wide slot before its command starts — a lock file under the user's local application data (`%LOCALAPPDATA%\claude-cursor-bridge\heavy.lock`; the home's equivalent elsewhere), one for the computer, never under a project — and releases it when the run ends however it ends; a lock whose holder process is gone is taken over with a line saying so; a second heavy run prints `bridge-run: started <time>Z` first, as every run does, then `bridge-run: waiting for the slot held by <kind> <run id> since <time>` once a minute until it starts, the wait not counted against the run's ceiling and bounded at twice the kind's default, its end reported distinctly from the command's own limit (exit 124 with a line naming the holder); a `review` or `watch` run takes no slot; (b) `mutation-run.py`, which the launcher's driver kind also accepts by its installed path: `python ~/.claude/cursor-bridge/mutation-run.py <mutants file> [--all] [--scratch <folder outside the Workspace>]` reads a JSON file the supervisor writes (`run/supervisor/<id>-mutants.json`: per mutant an id, the file, the old text, the new text and the test files to run), copies the tracked folders the mutants name to the scratch folder, applies one mutant at a time there, runs its tests there with no window, and never edits the Workspace, so an interrupted run leaves nothing to restore (KP-056); each outcome — killed, survived, not applied (old text not found, or found twice) or error — is recorded in `run/supervisor/mutation-cache/<id>.json` under a key made of the sha256 of the mutated file's current content, of each named test file's content and of the mutant's old and new text; on a later run a mutant whose key matches a recorded killed is skipped and listed as `killed (cached <time>)`, every survived, not-applied or errored mutant runs again, and `--all` runs every mutant and refreshes the cache; the summary lists every mutant with its outcome and whether it ran, then the counts (run, cached, killed, survived, not applied, error); exit 0 when every mutant is killed, 1 when any survived or did not apply, 2 for a malformed file or a scratch folder inside the Workspace; (c) `tests/test_bridge_run_slot.py` (names R-040): two heavy runs started together run one after the other and the second's stderr shows the waiting line naming the first's kind and id, a review takes no slot, a dead holder's lock is taken over with its line, the wait's bound ends with its distinct line; `tests/test_mutation_run.py` (names R-041), on a fixture package and tests built in the test: a first run kills and records, a run with nothing changed runs no mutant, a change to a mutated file reruns only that file's mutants, a change to a named test file reruns the mutants naming it, a survived mutant reruns every time, `--all` reruns all, the Workspace copy is byte-identical after a run, an old text not found is not applied with exit 1, a malformed file exits 2; the command reference regenerated; `windowless-check.py` green over both programs; no new dependency.

### TASK-030 — The loop's text for windowless runs and the rate limit
Author: supervisor.
Parent: none
Depends on: TASK-029, TASK-017, TASK-018, TASK-023
Parallel: no
Diagrams: none
Scope: bridge/cursor-bridge/workflow/phases/delegation-loop.md; bridge/cursor-bridge/workflow/phases/delegation-loop/; bridge/cursor-bridge/workflow/phases/configuration.md; bridge/commands/supervisor.md; bridge/commands/calibrate-bridge.md; bridge/cursor-bridge/Cursor-Project-Configuration.md; bridge/cursor-bridge/workflow/trace-exceptions.md; bridge/cursor-bridge/MANIFEST.json; tests/test_loop_text_windowless.py
Satisfies: R-039, R-040, R-041
Done when: the delegation loop's step 4 says the supervisor writes the mutation list as `run/supervisor/<id>-mutants.json` and runs it with `mutation-run.py` through the launcher's driver kind, that between rounds only the mutants whose code or tests changed rerun, and that `--all` runs on the final code before step 8's snapshot; the suite, a driver and every other heavy run start only through `bridge-run.py` (rule 8; the `# wake` exception narrowed to a runner the launcher does not know, named with its reason in the status file), and a run that waits for the slot is the launcher's business — never a reason to start it another way, never the owner's question; `configuration.md` and `Cursor-Project-Configuration.md` (§2 and the order of operations) gain the windowless default as a configuration item the configurator writes from the snapshot into the project's test configuration, with the conformance floor that checks it; `calibrate-bridge.md` names the floor among the MISSING items calibration applies (a configuration item, no gate reopened); the core's rule 8 names the suite and the drivers, and rule 24 names the suite's default; `delegation-loop.md` stays within the R-032 bound, another step moved into a sub-file first if it would not (TASK-013's precedent, the pointer line extended); `trace-check` green with the increment's `reword` and `new` entries; `tests/test_loop_text_windowless.py` (names R-039, R-040, R-041) asserts each sentence and that the snapshot the text names is the one TASK-028 ships.

### TASK-025 — Acceptance: reads-only, classification, and full trace
Author: supervisor (tests).
Parent: none
Depends on: TASK-023, TASK-024, TASK-030, TASK-009, TASK-015, TASK-011, TASK-016
Parallel: no
Diagrams: none
Scope: tests/test_reads_only_applicable.py; tests/test_running_projects_classify.py; tests/test_trace_full_split.py
Satisfies: R-029, R-030, R-031
Done when: `test_reads_only_applicable.py` (names R-030) walks a sample project intake→configuration and asserts only the core + current phase module + its own conditionals are named for reading; `test_running_projects_classify.py` (names R-031) asserts the bridge, reAngle, the video factory, and the TDP each classify per §6.3 on the committed fixtures (TASK-019–021) with `workflow-check` green; `test_trace_full_split.py` (names R-029) asserts `trace-check` green over the finished split (nothing dropped across all modules and traits, no passage in two homes).
````

### BUILD_PLAN.md, TASK-027's Done when

````markdown
### TASK-027 — Install run-sheet, stamp, install, and the trial
Author: supervisor (run-sheet text, CHANGELOG entry, VERSION/MANIFEST stamp — all records) / owner (completes the merge and runs the install run sheet).
Parent: none
Depends on: TASK-026
Parallel: no
Diagrams: none
Scope: bridge/commands/calibrate-bridge.md; bridge/cursor-bridge/CHANGELOG.md; bridge/cursor-bridge/VERSION; bridge/cursor-bridge/MANIFEST.json; docs/PROJECT_STATUS.md; docs/INVENTORY.md; tests/test_release_b_stamp.py
Satisfies: R-031, R-037, R-038
Done when: the install run sheet reflects R-038 (pause & switch this checkout to `main` at B6); the CHANGELOG entry names release B with its "if rolled back" notes and its "Running projects must" items, the windowless default among them (TASK-030); VERSION is bumped and MANIFEST regenerated; `bridge-check.py --sources` green on the stamped tree; `test_release_b_stamp.py` (names R-037, R-038) asserts VERSION/CHANGELOG/manifest agree and the run sheet says pause-and-switch; the projects are paused; `bridge-install.py` runs and `bridge-check.py` is green on `~/.claude`; reAngle calibrates (its `Workflows:` line valid, no gate reopened), resumes, and its field acceptance is met — after reAngle's first compaction under release B the hook names its current phase's module(s) read whole (visible in the transcript / `run/supervisor/`), its `Workflows:` line passes `workflow-check`, and one increment goes through the loop with no gate reopened; the video factory and the TDP each calibrate and resume per the owner's standing pause/resume policy (one calibration each, none pausing) — recorded as an owner-dated deferral at B6 if not resumed by then, so `completion-check --mode done` is not blocked by events outside release B.
````

## The committed diff of the records against origin/main before the revision (8a4f3e5)

````diff
diff --git a/docs/BUILD_PLAN.md b/docs/BUILD_PLAN.md
index b2c256e..2a4665c 100644
--- a/docs/BUILD_PLAN.md
+++ b/docs/BUILD_PLAN.md
@@ -1,6 +1,6 @@
 # Build plan — Claude-Cursor Bridge, Release B
 
-The design is the Restructuring Plan's release B (§16) and the sections it rests on (§6, §15). This plan decomposes that scope into increments. Per §15 condition 3, **governance text is design: the supervisor authors it, gated by the two-critic design review; programs are implementation: the builder writes them, gated by the delegation loop.** Each increment marks its author. Status is derived from `origin/main` by `plan-check.py`, never written here. Revised 2026-10-11 after two-critic rounds 1–3 (converging: Blocking 7→6→1 and 5→1→2).
+The design is the Restructuring Plan's release B (§16) and the sections it rests on (§6, §15). This plan decomposes that scope into increments. Per §15 condition 3, **governance text is design: the supervisor authors it, gated by the two-critic design review; programs are implementation: the builder writes them, gated by the delegation loop.** Each increment marks its author. Status is derived from `origin/main` by `plan-check.py`, never written here. Revised 2026-10-11 after two-critic rounds 1–3 (converging: Blocking 7→6→1 and 5→1→2). Revised 2026-10-20 at the owner's decision on the window flood of 2026-10-19/20 (ISS-011; R-039 to R-041): TASK-028 to TASK-030 added to stage B5 before TASK-025, the fix made in the bridge and installed by calibration rather than per project, as a planned update and not a hotfix (INVENTORY, Decisions); critiqued as the subject `windowless` (docs/DESIGN_CRITIQUE.md).
 
 ## Standing constraints (every increment)
 - **Manifest:** any increment that adds, moves, removes, **or edits** a file under `bridge/` regenerates `bridge/cursor-bridge/MANIFEST.json` (`python tools/make-manifest.py`) in the same commit (a hash change fails `bridge-check --sources` in CI otherwise); `MANIFEST.json` is named in its Scope.
@@ -252,7 +252,7 @@ Satisfies: R-026
 Done when: contract design covers a protocol's operations/inputs/outputs/errors/versioning as a contract file tests enforce; command design covers commands, help text, output formats; `test_interface_text.py` (names R-026) asserts both files' required sections. (The variant files are declared in TASK-012, each with its heading and its declaring paragraph, which names its artifact; this fills their bodies.) Added at TASK-012's gate, 2026-10-20 (Review A and the security audit, convergent): command-design.md writes `docs/design/COMMANDS.md`, one section per command, and contract-design.md writes `docs/design/CONTRACT.md` and the contract file it names, the names interface.md and planning.md already cite; each body states its artifact and its **Gate:**; an added contract operation, like a breaking change, escalates to the owner; each operation says who may call it and how a refused call fails, so the contract-enforcement increment tests refusals as well as shapes; a secret is never a command's option value (it comes from a key file, a prompt or the product's store) and example sessions use plain placeholders; test_interface_text.py asserts those names, the gates and the three rules, and applies completion-check's stand-in patterns to both files. TASK-012's first drafts of both bodies and their test are kept in run/supervisor/drafts/task012/ (gitignored) and in commit 552458b, PR #55's first head.
 
 ## Stage B5 — Calibration and acceptance
-Demonstration: a fresh session walked intake→configuration reads only its core, its current phase module, and its own conditional workflows; the four projects each classify under §6.3 on fixtures with `workflow-check` green.
+Demonstration: a fresh session walked intake→configuration reads only its core, its current phase module, and its own conditional workflows; the four projects each classify under §6.3 on fixtures with `workflow-check` green; a mutation run and a test suite started together through the launcher run one after the other, the second saying what it waits for, and no window appears; the mutation run repeated with nothing changed runs no mutant, and with `--all` runs every one.
 
 ### TASK-023 — Calibration aware of conditional workflows (text)
 Author: supervisor.
@@ -274,10 +274,40 @@ Scope: bridge/cursor-bridge/conformance-check.py; bridge/cursor-bridge/MANIFEST.
 Satisfies: R-027, R-033
 Done when: `conformance-check.py` runs `workflow-check` at calibration over a running project's status file and reports an unclassified line or one naming an unwritten workflow; `test_calibrate_program.py` (names R-027, R-033) covers a classified and an unclassified project.
 
+### TASK-028 — Windowless launches enforced by the bridge: the launcher's driver kind and the suite's frozen default
+Author: builder.
+Parent: none
+Depends on: TASK-024
+Parallel: no
+Diagrams: none
+Scope: bridge/cursor-bridge/bridge-run.py; bridge/cursor-bridge/conformance-check.py; bridge/cursor-bridge/windowless-default.snapshot.py; bridge/cursor-bridge/MANIFEST.json; tests/test_bridge_run_driver.py; tests/test_conformance_windowless.py; docs/cli-reference.json; docs/CLI_REFERENCE.md
+Satisfies: R-039
+Done when: (a) `bridge-run.py` accepts a supervisor's mutation driver as a kind of its own — `--limit auto --kind driver -- python run/supervisor/<name>.py [args]`, a Python program whose path resolves inside the project's `run/supervisor/` with no link on the way, with no option that runs other code (`-c`, `-m`), the kind's default ceiling the test kind's (1800 s) and learned like the others, logged in `run/launcher/runs.jsonl`; a program elsewhere or another form is refused with exit 125 and a message naming the rule; (b) every command the launcher starts, the driver included, is started with `CREATE_NO_WINDOW`, and a test proves on Windows that a grandchild of a driver run through the launcher has a console with no window (the probe `tests/test_tests_windowless.py` uses; skipped elsewhere with the reason); (c) the bridge ships the suite's windowless default as frozen text, `bridge/cursor-bridge/windowless-default.snapshot.py` — `tests/conftest.py`'s `windowless_kwargs` and the `Popen` wrapper it installs (FIX-001), with the docstring that says why — and a test asserts the bridge's own `tests/conftest.py` holds that text verbatim, so the snapshot and its source cannot drift; (d) `conformance-check.py` gains the floor `Windowless test suite`: a project whose suite is pytest is OK when its root `tests/conftest.py` (or the `conftest.py` beside its `pytest.ini`/`pyproject.toml`) defines `windowless_kwargs` and installs the wrapper on `subprocess.Popen.__init__` guarded by `CREATE_NO_WINDOW`, else MISSING naming the snapshot and `Cursor-Project-Configuration.md`'s item; a project whose suite is a Node runner (a `test` script naming vitest, jest, playwright or `node --test`) is OK when a setup file the runner's configuration loads sets `windowsHide: true` as the default of `child_process`'s launches, else MISSING the same way; a project with another runner, or none the check can see, is a NOTE naming what it saw — values are never read, and the check reads only the project's files; (e) `tests/test_bridge_run_driver.py` (names R-039) covers the accepted driver, each refused form, the kind's ceiling and its log line, and the windowless grandchild; `tests/test_conformance_windowless.py` (names R-039) covers OK, MISSING and NOTE for pytest and for a Node runner on fixtures built in the test, never a real project's file, and the bridge's own Workspace as OK; the command reference regenerated and `windowless-check.py` green over the two programs; no new dependency.
+
+### TASK-029 — One heavy job at a time, and mutation reruns that skip what is unchanged
+Author: builder.
+Parent: none
+Depends on: TASK-028
+Parallel: no
+Diagrams: none
+Scope: bridge/cursor-bridge/bridge-run.py; bridge/cursor-bridge/mutation-run.py; bridge/cursor-bridge/MANIFEST.json; tests/test_bridge_run_slot.py; tests/test_mutation_run.py; docs/cli-reference.json; docs/CLI_REFERENCE.md
+Satisfies: R-040, R-041
+Done when: (a) the slot: a run of kind `builder`, `test` or `driver` takes one machine-wide slot before its command starts — a lock file under the user's local application data (`%LOCALAPPDATA%\claude-cursor-bridge\heavy.lock`; the home's equivalent elsewhere), one for the computer, never under a project — and releases it when the run ends however it ends; a lock whose holder process is gone is taken over with a line saying so; a second heavy run prints `bridge-run: started <time>Z` first, as every run does, then `bridge-run: waiting for the slot held by <kind> <run id> since <time>` once a minute until it starts, the wait not counted against the run's ceiling and bounded at twice the kind's default, its end reported distinctly from the command's own limit (exit 124 with a line naming the holder); a `review` or `watch` run takes no slot; (b) `mutation-run.py`, which the launcher's driver kind also accepts by its installed path: `python ~/.claude/cursor-bridge/mutation-run.py <mutants file> [--all] [--scratch <folder outside the Workspace>]` reads a JSON file the supervisor writes (`run/supervisor/<id>-mutants.json`: per mutant an id, the file, the old text, the new text and the test files to run), copies the tracked folders the mutants name to the scratch folder, applies one mutant at a time there, runs its tests there with no window, and never edits the Workspace, so an interrupted run leaves nothing to restore (KP-056); each outcome — killed, survived, not applied (old text not found, or found twice) or error — is recorded in `run/supervisor/mutation-cache/<id>.json` under a key made of the sha256 of the mutated file's current content, of each named test file's content and of the mutant's old and new text; on a later run a mutant whose key matches a recorded killed is skipped and listed as `killed (cached <time>)`, every survived, not-applied or errored mutant runs again, and `--all` runs every mutant and refreshes the cache; the summary lists every mutant with its outcome and whether it ran, then the counts (run, cached, killed, survived, not applied, error); exit 0 when every mutant is killed, 1 when any survived or did not apply, 2 for a malformed file or a scratch folder inside the Workspace; (c) `tests/test_bridge_run_slot.py` (names R-040): two heavy runs started together run one after the other and the second's stderr shows the waiting line naming the first's kind and id, a review takes no slot, a dead holder's lock is taken over with its line, the wait's bound ends with its distinct line; `tests/test_mutation_run.py` (names R-041), on a fixture package and tests built in the test: a first run kills and records, a run with nothing changed runs no mutant, a change to a mutated file reruns only that file's mutants, a change to a named test file reruns the mutants naming it, a survived mutant reruns every time, `--all` reruns all, the Workspace copy is byte-identical after a run, an old text not found is not applied with exit 1, a malformed file exits 2; the command reference regenerated; `windowless-check.py` green over both programs; no new dependency.
+
+### TASK-030 — The loop's text for windowless runs and the rate limit
+Author: supervisor.
+Parent: none
+Depends on: TASK-029, TASK-017, TASK-018, TASK-023
+Parallel: no
+Diagrams: none
+Scope: bridge/cursor-bridge/workflow/phases/delegation-loop.md; bridge/cursor-bridge/workflow/phases/delegation-loop/; bridge/cursor-bridge/workflow/phases/configuration.md; bridge/commands/supervisor.md; bridge/commands/calibrate-bridge.md; bridge/cursor-bridge/Cursor-Project-Configuration.md; bridge/cursor-bridge/workflow/trace-exceptions.md; bridge/cursor-bridge/MANIFEST.json; tests/test_loop_text_windowless.py
+Satisfies: R-039, R-040, R-041
+Done when: the delegation loop's step 4 says the supervisor writes the mutation list as `run/supervisor/<id>-mutants.json` and runs it with `mutation-run.py` through the launcher's driver kind, that between rounds only the mutants whose code or tests changed rerun, and that `--all` runs on the final code before step 8's snapshot; the suite, a driver and every other heavy run start only through `bridge-run.py` (rule 8; the `# wake` exception narrowed to a runner the launcher does not know, named with its reason in the status file), and a run that waits for the slot is the launcher's business — never a reason to start it another way, never the owner's question; `configuration.md` and `Cursor-Project-Configuration.md` (§2 and the order of operations) gain the windowless default as a configuration item the configurator writes from the snapshot into the project's test configuration, with the conformance floor that checks it; `calibrate-bridge.md` names the floor among the MISSING items calibration applies (a configuration item, no gate reopened); the core's rule 8 names the suite and the drivers, and rule 24 names the suite's default; `delegation-loop.md` stays within the R-032 bound, another step moved into a sub-file first if it would not (TASK-013's precedent, the pointer line extended); `trace-check` green with the increment's `reword` and `new` entries; `tests/test_loop_text_windowless.py` (names R-039, R-040, R-041) asserts each sentence and that the snapshot the text names is the one TASK-028 ships.
+
 ### TASK-025 — Acceptance: reads-only, classification, and full trace
 Author: supervisor (tests).
 Parent: none
-Depends on: TASK-023, TASK-024, TASK-009, TASK-015, TASK-011, TASK-016
+Depends on: TASK-023, TASK-024, TASK-030, TASK-009, TASK-015, TASK-011, TASK-016
 Parallel: no
 Diagrams: none
 Scope: tests/test_reads_only_applicable.py; tests/test_running_projects_classify.py; tests/test_trace_full_split.py
@@ -305,4 +335,4 @@ Parallel: no
 Diagrams: none
 Scope: bridge/commands/calibrate-bridge.md; bridge/cursor-bridge/CHANGELOG.md; bridge/cursor-bridge/VERSION; bridge/cursor-bridge/MANIFEST.json; docs/PROJECT_STATUS.md; docs/INVENTORY.md; tests/test_release_b_stamp.py
 Satisfies: R-031, R-037, R-038
-Done when: the install run sheet reflects R-038 (pause & switch this checkout to `main` at B6); the CHANGELOG entry names release B with its "if rolled back" notes; VERSION is bumped and MANIFEST regenerated; `bridge-check.py --sources` green on the stamped tree; `test_release_b_stamp.py` (names R-037, R-038) asserts VERSION/CHANGELOG/manifest agree and the run sheet says pause-and-switch; the projects are paused; `bridge-install.py` runs and `bridge-check.py` is green on `~/.claude`; reAngle calibrates (its `Workflows:` line valid, no gate reopened), resumes, and its field acceptance is met — after reAngle's first compaction under release B the hook names its current phase's module(s) read whole (visible in the transcript / `run/supervisor/`), its `Workflows:` line passes `workflow-check`, and one increment goes through the loop with no gate reopened; the video factory and the TDP each calibrate and resume per the owner's standing pause/resume policy (one calibration each, none pausing) — recorded as an owner-dated deferral at B6 if not resumed by then, so `completion-check --mode done` is not blocked by events outside release B.
+Done when: the install run sheet reflects R-038 (pause & switch this checkout to `main` at B6); the CHANGELOG entry names release B with its "if rolled back" notes and its "Running projects must" items, the windowless default among them (TASK-030); VERSION is bumped and MANIFEST regenerated; `bridge-check.py --sources` green on the stamped tree; `test_release_b_stamp.py` (names R-037, R-038) asserts VERSION/CHANGELOG/manifest agree and the run sheet says pause-and-switch; the projects are paused; `bridge-install.py` runs and `bridge-check.py` is green on `~/.claude`; reAngle calibrates (its `Workflows:` line valid, no gate reopened), resumes, and its field acceptance is met — after reAngle's first compaction under release B the hook names its current phase's module(s) read whole (visible in the transcript / `run/supervisor/`), its `Workflows:` line passes `workflow-check`, and one increment goes through the loop with no gate reopened; the video factory and the TDP each calibrate and resume per the owner's standing pause/resume policy (one calibration each, none pausing) — recorded as an owner-dated deferral at B6 if not resumed by then, so `completion-check --mode done` is not blocked by events outside release B.
diff --git a/docs/DESIGN_CRITIQUE.md b/docs/DESIGN_CRITIQUE.md
index 99a2f93..5bb11e6 100644
--- a/docs/DESIGN_CRITIQUE.md
+++ b/docs/DESIGN_CRITIQUE.md
@@ -568,4 +568,18 @@ The fixes from stage B2's review, round 2: the builder made workflow-check.py pr
 
 **Resolution**: none due. Nothing is open after the confirming read: no Blocking finding and no non-convergence in any round, so no resolution round runs, and the subject goes to its gate.
 
+## Subject: windowless (the window flood's fix: windowless launches and a rate limit, a scoped revision mid-build, 2026-10-20)
+
+**What is criticised:** a scoped revision of release B's plan at the owner's decision (ISS-011), one subject holding both its design revision — three rows of the register, R-039 to R-041, and the INVENTORY Decisions rows that record the owner's words — and its plan addendum: TASK-028, TASK-029 and TASK-030 in stage B5 before TASK-025, the stage's demonstration extended, TASK-025's and TASK-027's lines amended. The design revision is three rows because the design is the owner's words as relayed and confirmed; the subject is one because a scoped revision mid-build is one change (design.md, "The procedure": the subjects). The critics read `run/review/DESIGN-windowless-<round>.md`, built from the committed records.
+
+**Accepted** (finding, critic, round, the reason):
+- (none yet)
+
+**Rounds** (round, kind, the commit its file was built from, critic, Blocking / Should fix / Consider, what was fixed):
+- (none yet)
+
+**Resolution**: (none yet)
+
+## Subject: ceiling — after the critique
+
 **After the critique** (supervisor, at the brief, for the code gate's reviewers): the change log's and KP-062's migration notes gain one sentence, a round file named other than by its number (`-confirm`) is refused and its next file takes the next number (the spec-packager's note: release B's own plan critique used `DESIGN-plan-confirm.md`); the brief matches `run`, `review` and `DESIGN-` in any case, with a test. Not criticised by the two critics; reviewed at the code gate with the whole diff.
diff --git a/docs/INVENTORY.md b/docs/INVENTORY.md
index 0cc0bfd..6060ac9 100644
--- a/docs/INVENTORY.md
+++ b/docs/INVENTORY.md
@@ -85,6 +85,8 @@ No paid API key is needed to build the bridge itself; the roster uses the owner'
 | A record the plan does not name, added by TASK-012: run/supervisor/interface-notes.md, every change the owner asks for on a variant's artifact and whether it is made (gitignored, on the Working files: line) | the interface phase iterates with the owner and the requests live only in the conversation, which a compaction does not keep (R-004; rule 54's place, as intake-notes.md) | 2026-10-20, supervisor (TASK-012) | the requests move into a tracked record |
 | A record the plan does not name, added by TASK-013: run/supervisor/refactor-<stage>-candidates.md, the refactoring scout's two ranked lists and each candidate's outcome (committed, dropped, beyond budget) while the stage-close pass runs (gitignored, on the Working files: line) | the lists are returned only in the scout's reply, which a compaction does not keep, and no other file says which candidates remain (R-004; Review A, TASK-013 round 1, S3; rule 54's place, as intake-notes.md) | 2026-10-20, supervisor (TASK-013) | the pass's candidates move into a tracked record |
 | The hook's docstring says a non-str line from the checker's file_lines makes the checker unusable for the lines of a phase module file only, since the hook calls file_lines in one place, pointer_paths_from_module (FIX-003's round-2 assumption, accepted) | the sentence is narrowed to what the code checks (Review A, FIX-003 round 1); no test sees a second call site | 2026-10-20, supervisor (FIX-003) | the hook calls file_lines elsewhere |
+| The window flood of 2026-10-19/20 (ISS-011) is fixed in the bridge, as release B's TASK-028 to TASK-030 in stage B5 before the acceptance increment, installed and calibrated with release B — not per project, and not as a hotfix: windowless launches enforced by the launcher and a frozen suite default every project carries (R-039); one heavy job at a time on the computer (R-040); mutation reruns that skip only what is unchanged and run every mutant once against the final code before the gate (R-041) | the owner's words of 2026-10-20, relayed by the maintainer with its findings (the process-start record of 06:54–10:20 local: 218k process starts, about 202k the bridge's, 52k of them session-start.py launched by run/supervisor/task015_mutants.py, up to 758 a minute, about twelve runs of the whole set; the window source earlier and unproven) and confirmed in this session's chat: "I'd rather have the solution implemented in the bridge as a quick fix and afterwards installed and calibrated, than fixing it in each session"; "There definitely needs to be a rate limit on the tests that necessitate evoking a terminal. However, what we decide here must not cut down on quality or certainty of proper test coverage. Redundancy should be cut"; "This problem seems to have been an outlier though. I still want it to be fixed, but not as a quick fix, but instead an update that will be inserted or appended on the right spot" | 2026-10-20, owner (the placement the supervisor's, approved in the chat) | the flood recurs before release B installs (then a hotfix of the installed release, as 2026.10.18a was) |
+| Builders and test suites running where no window can exist (for example WSL) is a release after B, planned at the planning point after release B is done and accepted, beside release B2; release B's TASK-028 to TASK-030 are the nearer fix | the owner, 2026-10-20: "Long term this seems worth it" | 2026-10-20, owner | — |
 | No diagram index for release B | the design is the plan's prose and its §6.2 layering / §6.11 file layout tables; this is governance text, not a code architecture with components to draw | 2026-10-11, supervisor | a later release adds code whose architecture is load-bearing |
 
 ## Deferred
diff --git a/docs/REQUIREMENTS.md b/docs/REQUIREMENTS.md
index af688cc..2e1fc33 100644
--- a/docs/REQUIREMENTS.md
+++ b/docs/REQUIREMENTS.md
@@ -1,6 +1,6 @@
 # Requirements — Claude-Cursor Bridge (Release B)
 
-Drawn from the Restructuring Plan's release B (§16), its scope and "Accepted when", and the design it rests on (§6.2–6.12, §6.6, §6.7, §6.8, §15 condition 6). This register governs release B only; the rules and programs that already shipped (releases 0, A1a–A5) are the baseline, not rows here. "Done" for release B is every row below built and tested or deferred/dropped by the owner with a date. Revised 2026-10-11 after the two-critic review (round 1): rows R-032–R-038 added; R-005, R-029, R-031 extended.
+Drawn from the Restructuring Plan's release B (§16), its scope and "Accepted when", and the design it rests on (§6.2–6.12, §6.6, §6.7, §6.8, §15 condition 6). This register governs release B only; the rules and programs that already shipped (releases 0, A1a–A5) are the baseline, not rows here. "Done" for release B is every row below built and tested or deferred/dropped by the owner with a date. Revised 2026-10-11 after the two-critic review (round 1): rows R-032–R-038 added; R-005, R-029, R-031 extended. Revised 2026-10-20 at the owner's decision on the window flood of 2026-10-19/20 (ISS-011; the maintainer's findings relayed with the owner's words, confirmed in the supervisor's chat): rows R-039–R-041 added, their source the owner's decision rather than the Restructuring Plan; critiqued as the subject `windowless` (docs/DESIGN_CRITIQUE.md).
 
 | ID | Requirement | Source | Status | Evidence |
 |---|---|---|---|---|
@@ -42,3 +42,6 @@ Drawn from the Restructuring Plan's release B (§16), its scope and "Accepted wh
 | R-036 | A new or defined-but-unwritten trait is handled by writing its extra handling into the project's design, flagging it at the design gate (where the owner may still pause), and putting it to the promotion pass at project end. | DESIGN §6.7 | planned | the design and the gate: tests/test_phase_modules_intake_design.py (test_r036_; TASK-011, the `Flagged trait:` row); the promotion pass follows in TASK-014 |
 | R-037 | Release B is delivered: a release-level review by a fresh context (one pass, fixes, a second pass); the stamp (VERSION, a regenerated MANIFEST, a CHANGELOG entry with its "if rolled back" notes); the projects paused; `bridge-install.py` run; `bridge-check.py` green on the installed tree; the trial project (reAngle) calibrated and resumed; field acceptance met; the others resumed. | DESIGN §15 conditions 4–5; §16 | planned | — |
 | R-038 | The install mechanics while the supervisor builds on branches (installing from a second checkout that holds only `main`, or pausing and switching this checkout) are settled by the owner, recorded, and reflected in the install run sheet. | DESIGN §16 / A1a "settled at release B's intake" | planned | — |
+| R-039 | Windowless launches are enforced by the bridge for every project, never by a per-project fix: every heavy run of the loop — a builder, a project's test suite, a mutation driver the supervisor writes under `run/supervisor/` — starts through the launcher (`bridge-run.py`), which starts it with no window so that every process it creates inherits that; and every project's test suite carries the bridge's frozen windowless default (FIX-001's `tests/conftest.py` default, shipped as a snapshot like the secure-coding rule), written at configuration, reported by the conformance check as a floor at every calibration and reflection point, and installed into a running project by calibration. | the owner's decision of 2026-10-20 (ISS-011): "I'd rather have the solution implemented in the bridge … and afterwards installed and calibrated, than fixing it in each session"; rule 24; KP-014 | planned | — |
+| R-040 | One heavy job at a time on the computer: a builder run, a full test suite and a mutation run each hold a machine-wide slot in the launcher while they run, a second heavy run waiting for the slot and saying so; a review and a CI watch take none. | the owner's decision of 2026-10-20 (ISS-011): "There definitely needs to be a rate limit on the tests that necessitate evoking a terminal" | planned | — |
+| R-041 | Mutation reruns skip only what is unchanged: a mutation driver reruns a mutant only when the code it mutates or the tests it runs changed since the mutant's last killed result, every survived or unapplied mutant runs again, and every mutant runs against the final code once before the gate — the redundancy cut, the coverage and its certainty kept. | the owner's decision of 2026-10-20 (ISS-011): "what we decide here must not cut down on quality or certainty of proper test coverage. Redundancy should be cut" | planned | — |
````
