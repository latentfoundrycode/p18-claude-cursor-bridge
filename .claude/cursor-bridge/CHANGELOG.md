# Claude-Cursor Bridge — CHANGELOG

One entry per release. `VERSION` and `MANIFEST.json` are stamped by the maintainer's
`tools/make-manifest.py`, which refuses to stamp a version that has no entry here.

Each entry has two parts. **What changed** is for the maintainer and the curious.
**Running projects must** is the part `/calibrate-bridge` acts on: every item names the
**phase** it belongs to, so a project that has already passed that phase does not reopen
it, a project in it applies the item now, and a project before it applies the item when it
arrives. An item marked *(all phases)* applies immediately.

---

## 2026.09.25b

**What changed**
- **Automatic model switch — the owner is never in the loop for it.** Every `cursor-agent`
  call sets `--model` from `docs/ROSTER.resolved.json` and captures stderr to a file. On a
  failure, `roster-check.py --record-failure <model> --stderr-file <file>` classifies it: a
  usage-limit message (or a second consecutive failure) marks the pool exhausted / the model
  unavailable in `docs/ROSTER.json` by itself (exit 3); a first non-limit failure is a
  transient retry (exit 4). On exit 3 the supervisor re-resolves the roster and **restarts
  the interrupted step from its checkpoint** with the new models — a delegation from the
  pre-delegation commit, a Review B on the same committed diff — records the stderr excerpt
  as an issue, and puts the switch in the next report's first line. Only the return to the
  preferred profile waits for the owner's "usage reset". Phase 6 step 3b; rule 38; KP-024.

**Running projects must**
- *(Phase 6)* Add `--model <builder>` from `docs/ROSTER.resolved.json` and
  `2> run/agent/TASK-<nnn>.err` to the delegate command; the same for Review B launches
  (`run/review/REVIEW-<nnn>.err`); gitignore `run/agent/`. Apply step 3b from the next
  failure on.

---

## 2026.09.25

**What changed**
- **Roster profiles and the owner-set pool state.** `docs/ROSTER.json` now lists
  **profiles** tried in order — *full* (builder Cursor-hosted Grok 4.6, Review B GPT-5.6
  Sol) and *native* (builder Composer 2.5, Review B Cursor-hosted Grok 4.6; roles swapped so
  the stronger native reasoner reviews) — plus `other_pool: available | exhausted`, set by
  the owner because a probe cannot see a nearly-empty quota (the owner's pool stood at 99%
  used while a one-word call still answered). `roster-check.py` skips profiles that need
  the exhausted pool, probes the rest through the real CLI (refusal / empty / timeout =
  unusable), verifies three families, writes `docs/ROSTER.resolved.json`, and the delegate
  and Review B commands read their model ids from it. Family mapping fixed: `cursor-grok-*`
  is xAI hosted by Cursor, not Cursor's own family. KP-024; rule 38.

**Running projects must**
- *(all phases)* Rewrite `docs/ROSTER.json` to the two-profile template with
  `"other_pool": "exhausted"` (the owner's pool is exhausted as of 2026-09-25), run
  `roster-check.py`, and switch the delegate and Review B commands to read
  `docs/ROSTER.resolved.json`. Report in the first line that the native profile is in use.
  When the owner says "usage reset", set `other_pool` to `available`.

---

## 2026.09.24b

**What changed** — from the SFVF Bridge Feedback document (Stage P).
- **External services: contract capture, never an invented mock.** The first increment on
  any third-party API/SDK is an attended live call recorded to fixtures the tests replay;
  "done" means passing against recorded real responses. Brief constraint; plan-critic
  Blocking; diff-reviewer FAIL on a builder-written mock. Standing rule 37; KP-020.
- **Test-infrastructure lane in the stage-close pass.** The supervisor consolidates its own
  test helpers in a separate commit on the same branch; `refactor-check.py --lane tests`
  asserts no production file changed; the collected test set must be identical before and
  after. Same one gate pass.
- **Reviewers review the design a diff embodies**, not only fidelity to the brief; a flawed
  brief is a finding (diff-reviewer, security-auditor).
- **Redact by pattern, never blank by status** (`secure-coding.snapshot.md` V15;
  security-auditor; KP-021).
- **Teardown: a real, briefly locked environment** is retried then deferred, never forced
  (configuration §1; KP-023).
- **Model roster is checked**: `docs/ROSTER.json` + new `roster-check.py` (three distinct
  families; delegate command sets `--model <builder>`) at configuration, calibration, and
  every checkpoint. Standing rule 38; KP-022.

**Running projects must**
- *(all phases)* Create `docs/ROSTER.json` from the merge policy's roster and run
  `roster-check.py` now; fix the delegate command if it lacks `--model`.
- *(Phase 6, projects with external integrations)* For each adapter whose tests replay a
  builder-written mock: add a contract-capture increment (an addition to the plan — tell the
  owner in one line; needs the service key once) and re-point the tests at the recorded
  fixtures before the next increment on that adapter.
- *(Phase 6)* The next stage-close pass may run the tests lane; the next brief carries the
  external-fixture constraint; reviewers apply the design lens from the next diff.

---

## 2026.09.24

**What changed** — from the first Bridge Feedback document to come through the channel
(Technical Documentation Provider, three stage closes).
- `scope-check.py` strips a trailing annotation from a scope entry (`path (new)`,
  `path - note`, `path # note`) instead of reading it as a different path (false drift).
- New `lock-check.py`: a dependency-manifest change without its lockfile change fails at the
  admission gate and in `secret-sentinel` before any reviewer — an *expected-file-missing*
  check reviewers cannot perform (ISS-004, KP-018).
- The reviewer's diff is generated only from committed state and lives inside the workspace
  at `run/review/REVIEW-<nnn>.diff` (committed on the branch, removed before merge) —
  never a working-tree diff (omits untracked new files, KP-017), never a temp path outside
  `Workspace/` (the boundary blocks it, KP-016 / ISS-003). Standing rule 36.
- `spec-packager` runs a **reality check** before every brief: what the increment assumes
  must exist as built; a mismatch returns as a scope question (KP-019).
- **Convergence is a signal:** two or more reviewers naming the same line is blocking even
  if each called it advisory (merge policy; step 8).
- The design records a **migration policy** (pre-release rebuild vs shipped migrations);
  plan-critic checks it.
- KP-016–KP-019 (artifacts outside the workspace; untracked-file diffs; lockfile; plan vs
  data, and CI event lag: poll the head SHA patiently, never stack empty commits).

**Running projects must**
- *(all phases)* Move any loop artifact written outside `Workspace/` (reviewer diffs,
  resolution files, captures) to its in-workspace path; from now on generate reviewer diffs
  from committed state only.
- *(Phase 5 or later)* Record the project's lock command and lockfile in `PROJECT_STATUS.md`;
  `lock-check.py` runs at the next dependency admission.
- *(Phase 6)* The next brief goes through the reality check; the next split or advisory
  convergence follows the new rule.
- *(Phase 2 not yet passed)* Add the migration policy to the design; *(later phases)* record
  the regime in `PROJECT_STATUS.md` at the next reflection point.

---

## 2026.09.22c

**What changed**
- **`Performance-Patterns.md`** — the bridge's catalogue of recurring causes of slowness
  and cost, in Known-Pitfalls' discipline: fixed entry shape (pattern, symptom, fix,
  measure, applies to, evidence), nine seeded entries `PP-001`–`PP-009` (N+1 calls, full
  scans, recomputation, synchronous IO on hot paths, unbounded growth, large-object
  serialization, interface-thread work, per-item model calls, eager startup), admission
  rule (recurs across projects, not covered, measurable), promotion from optimization
  commits with their numbers. Three readers wired: `plan-critic`'s performance lens names
  the `PP-nnn` a design walks into; `refactor-scout` uses the symptom column as its search
  list and names the entry (or `PP-new`) per candidate; the supervisor writes a failing
  benchmark's corrected brief from the named pattern's fix. Promotion pass proposes entries.
  Rule 15 extended.

**Running projects must**
- *(all phases)* Nothing to change in the project; the readers pick the catalogue up at
  their next use.

---

## 2026.09.22b

**What changed**
- **Optimization is measured or it does not exist.** New `Performance-Conventions.md`:
  owner-set **budgets** at intake (`bench/budgets.json`: one operation, one condition, one
  number, one measurement; speed, memory, size, and money/tokens alike; "no budgets" is an
  answer); the design names the **mechanism and hot path** per budget (plan-critic
  performance lens: scaling, per-item calls, unbounded growth, thread blocking,
  measurability); a **benchmark increment per budget** before any optimization; the
  **benchmark floor** — fixed dataset and seed, median of ≥5 runs, committed
  `bench/baseline.json`, new `bench-check.py` (OVER BUDGET / REGRESSION / NOT MEASURED
  fail; IMPROVED noted; `--update-baseline` only in optimization commits; tested) in the CI
  gate and at stage close; the stage-close pass gains a **performance lens**
  (`refactor-scout` ranks optimization candidates by measured impact on a budgeted metric)
  under the same one-branch one-gate mechanics, every optimization commit carrying its
  before/after numbers and moving the baseline; **anti-gaming**: loosening a budget, moving
  the baseline outside an optimization commit, deleting/skipping a benchmark, shrinking its
  dataset, or measuring warm where cold was stated is a gate-integrity flag. Configuration
  §5e. Standing rule 35.

**Running projects must**
- *(Phase 6 — building, or done)* At the next reflection point, propose budgets to the owner
  for the operations whose speed or cost they care about (a decision brief; "none" is a
  valid answer). If budgets are set: add the benchmark increments and the `bench-check.py`
  gate step as an addition to the plan (tell the owner in one line; reopens no gate), commit
  a baseline, then the performance lens applies from the next stage close.
- *(Phases 1–5)* Budgets are asked at intake going forward; a project already past intake
  asks them at its next gate as one extra decision.

---

## 2026.09.22

**What changed**
- **The change cycle.** A request on a finished project (`Phase: done`) runs the same
  workflow scaled to the delta: intake of the change (impact on existing behaviour; this
  project's own Issues file in place of prior-project lessons), a dated **Change:** section
  in `docs/DESIGN.md` with plan-critic on the delta, mockups only for touched screens, a
  plan addendum of new stages with a version bump and the Packaging & installer stage
  re-run last, run parameters kept, configuration only for new tooling, the loop, project
  end again with the manual patched and the deliverable rebuilt. Same three gates, no
  others. `Phase: changing` + `Change cycle:` in `PROJECT_STATUS.md`. Standing rule 34;
  plan-critic checks the addendum.
- **A process question is never the owner's.** "Should I follow the workflow for this?"
  is settled by the governance; where it is silent, the supervisor follows the closest
  defined procedure, says which, and records the gap as bridge feedback. Cause: a
  finished project's supervisor asked the owner whether a minor design change should go
  through the workflow.

**Running projects must**
- *(Phase: done, a change request pending or already being discussed)* Treat the request
  as a change cycle from step 1; nothing discussed so far is lost — fold it into the change
  intake summary and confirm it.
- *(all other phases)* Nothing.

---

## 2026.09.21d

**What changed**
- Inno Setup is a **standard machine prerequisite** of the bridge (setup guide Step 10),
  not a desktop-only optional step. `Delivery-Conventions.md` §2.1 tells the supervisor to
  locate `ISCC.exe` in both possible folders (per-user winget install under
  `%LOCALAPPDATA%\Programs\Inno Setup 6\`, all-users under `%ProgramFiles(x86)%`), record
  the resolved path, and hand the owner the Step 10 run sheet if neither exists.

**Running projects must**
- *(all phases)* Nothing.

---

## 2026.09.21c

**What changed**
- **Project end is a defined trigger.** The close of the approved plan's last stage *is*
  project end: the project-end items (final refactoring pass, User Manual, promotion pass,
  installer delivery) run in the same turn as that stage close, `Phase: done` is set, and
  the report opens with "Project complete". Deferred increments do not postpone it. The
  procedure existed since 2026.09.20 but had no trigger, so a finished project (Technical
  Documentation Provider, 2026-09-21) closed its last stage and never produced its manual.
  Standing rule 33; plan-critic checks the last stage is named.
- **Delivery broadened from desktop apps to all installable software.**
  `Packaging-Conventions.md` → `Delivery-Conventions.md`: §1 which kind ships what; §2 the
  desktop installer (unchanged); **§3 command-line tools and local servers** — a
  double-clickable `install.cmd` + `install.ps1` that checks prerequisites, builds an
  isolated environment from the lock file under `%LOCALAPPDATA%\Programs\<Name>`, puts the
  command on the user PATH via a launcher, registers an Apps & features entry and an
  uninstaller, offers Upgrade / Uninstall / Cancel when already installed, keeps data on
  uninstall, supports `-Silent`; the project writes its own `scripts/install-check.ps1`
  lifecycle test. Run parameter 4 applies to all installable kinds. Standing rule 31.
- **Command reference — never a made-up command again.** A project with a CLI keeps
  `docs/cli-reference.json`, generated from the real command tree by `scripts/dump-cli.py`
  in the increment that first adds a command, kept current by a CI diff check and the
  pre-commit gate; `diff-reviewer` fails a command change without a reference change;
  every run sheet, report, and manual passage copies commands from it or from a `--help`
  just run. Cause: the same project's supervisor instructed the owner with commands that
  did not exist. Standing rule 32; run-sheet rule; plan-critic check.

**Running projects must**
- *(Phase 6 — building, last stage already closed without a project-end reflection)* Run
  the project-end items now: final refactoring pass (if on), User Manual, promotion pass,
  deliverable; set `Phase: done`; report "Project complete" with deferred items listed.
- *(all phases, projects with a command-line surface)* Add the command-reference generator
  and its CI currency check as an increment in the current or next stage (an addition to
  the approved plan — tell the owner in one line; reopens no gate). Until it exists, run
  `--help` before every instruction that names a project command.
- *(all phases, installable software of any kind)* If the plan has no "Packaging &
  installer" last stage, add it (tell the owner in one line). Ask `Installer verification`
  if not yet in `docs/RUN_PARAMETERS.md` (default `local`).
- *(all phases, other projects)* Nothing.

---

## 2026.09.21b

**What changed**
- **Desktop applications ship as an installer.** New `Packaging-Conventions.md`: Windows 11
  x64, one `dist/<Name>-Setup-<version>-x64.exe`, per-user by default (no UAC), registered
  in Apps & features with a working uninstall, **upgrade in place** keeping user data,
  the installer offering Upgrade / Uninstall / Cancel when already installed, uninstall
  keeping data unless opted out, one-command build, single version source, unsigned by
  default (code signing is the one Phase-2 escalation). Toolchain per stack (Electron /
  Tauri bundlers; Inno Setup for .NET, Python, Rust, Go, C++) with a committed Inno
  template. New `installer-check.ps1` proves install / smoke / upgrade-in-place / uninstall
  silently and reversibly. Intake captures it; Phase 2 designs it; the plan's last stage is
  "Packaging & installer" (plan-critic blocks a desktop plan without it); a fourth run
  parameter `Installer verification` (`local` default / `ci-only`); project end delivers
  the installer and the manual's install chapter. Standing rule 31.

**Running projects must**
- *(all phases, desktop applications only)* If the plan has no "Packaging & installer"
  stage, add it as the final stage — this is an addition to the approved plan, so tell the
  owner in one line; it reopens no gate. Add `Installer verification` to
  `docs/RUN_PARAMETERS.md` (ask; default `local`). Add the Packaging & distribution
  section to `docs/DESIGN.md` at the next reflection point, and raise the code-signing
  question once.
- *(all phases, other projects)* Nothing.

---

## 2026.09.21

**What changed**
- **One Issues document.** `docs/LESSONS.md` is gone. The project's record of issues,
  misconceptions, causes, and fixes is the single
  `Documents/<Name> Issues During Development and Their Solutions.md`, written by the
  supervisor **for the next project's supervisor (an AI)**, one entry per `ISS-nnn`,
  `generalizable: yes` marking Known-Pitfalls candidates. The human reads the Project
  Summary instead.
- **Builder channel widened.** `docs/BUILDER_NOTES.md` now carries both tooling friction
  (→ Bridge Feedback) and anything the builder learned about a defect or pitfall (→ the
  Issues file); the supervisor sorts it at every reflection point.
- **No hard line wraps** in any Markdown the supervisor or the builder writes: one
  paragraph is one line; breaks only between blocks (rule 30; brief constraint;
  `workspace-boundary.mdc`).
- The User Manual at project end was already in place (Reflection points → project end);
  no change, restated for clarity.

**Running projects must**
- *(all phases)* If `docs/LESSONS.md` exists, fold each entry into the Documents Issues
  file under its `ISS-nnn` at the next reflection point, then delete `docs/LESSONS.md`.
- *(all phases)* Write without hard wraps from now on; do not reflow existing files
  mid-stage (a reflow is a noisy diff); the Documents may be reflowed at the next
  reflection point.
- *(Phase 6 — building)* The next brief carries the widened `BUILDER_NOTES.md` line and
  the no-wrap constraint (spec-packager template).

---

## 2026.09.20d

**What changed**
- **Run parameters** — asked once, together, right after the plan is approved and before
  configuration; recorded in `docs/RUN_PARAMETERS.md`: `Stage pause` (`run` default:
  report a stage close and continue in the same turn; `pause`: wait for "continue"),
  `Merge authority` (`supervisor` default; `owner`: stop at READY TO MERGE, never arm
  auto-merge), `Refactoring pass` (`on` default; moved here from the plan gate). The
  escalation list and the gate are unchanged under every setting. Standing rule 29;
  plan-critic no longer checks a dial in the plan.

**Running projects must**
- *(Phase 6 — building)* Ask the three run parameters at the next stage close or, if the
  loop is between increments, now — as one decision brief; this is the one decision line
  of the calibration report. Until answered, keep the behaviour the project has had
  (`Stage pause: pause`, `Merge authority` as the repo is set up, `Refactoring pass: on`),
  and say so. Write `docs/RUN_PARAMETERS.md` from the answers.
- *(Phase 4 — planning, plan not yet approved)* Nothing extra: the step follows the plan
  gate as written.
- *(Phase 5 — configuration)* Ask the run parameters before continuing configuration.

---

## 2026.09.20c

**What changed**
- `/calibrate-bridge` takes no argument. The `check` keyword was redundant: the command is
  the check. Run in a folder with no `docs/PROJECT_STATUS.md`, it verifies the install,
  re-reads the governing files, reports "no project in this folder", and stops.

**Running projects must**
- *(all phases)* Nothing.

---

## 2026.09.20b

**What changed**
- `/supervisor` takes no keywords. New vs resume is decided solely by whether
  `docs/PROJECT_STATUS.md` exists; text after the command is the seed description of a new
  project (or a message to a resumed one). `new` and `resume` were removed from the
  argument hint — `new` never had a distinct meaning, and `resume` duplicated the file check.

**Running projects must**
- *(all phases)* Nothing. Type `/supervisor` to resume, as before; the word `resume` is
  simply no longer needed.

---

## 2026.09.20

First stamped release. Covers everything since the observability integration (commit
`c34b235`) up to and including the calibration mechanism itself.

**What changed**
- `explain-for-decision` skill (rule 21) and the **run sheet** section (rule 27).
- Fixed project layout `<id>-<name>/Documents` + `/Workspace`; Workspace boundary
  (`workspace-boundary.mdc` + `boundary-check.py` hook); the four human-facing Documents;
  reflection points; issue IDs `ISS-nnn` (rules 22–23).
- Windowless-by-default policy (`run-hidden.py`, `windowless-check.py`, KP-014, rule 24).
- Phase 4 step 0 — prior-project lessons from an earlier project's Issues file.
- Stage-close refactoring pass (`refactor-scout`, `refactor-check.py`, rule 25).
- Root-cause-first debugging (`root-cause-first` skill, `BUG-nnn` fix briefs, OBSERVED /
  INFERRED diagnoses, KP-015, rule 26).
- `/calibrate-bridge`, `bridge-check.py`, `VERSION`, `MANIFEST.json`, this file (rule 28).
- Earlier in the same span: minimal-code rule, context-economy boundary, scope-check,
  constant-pointer delegation, safe worktree teardown, reviewer routing table.

**Running projects must**
- *(all phases)* Add to `docs/PROJECT_STATUS.md`: `Bridge version:`, `Software name:`,
  `Layout:`, `Terms fixed:`, `Stage:`, `Open issues:` (see the supervisor's Project state
  template). Resolve `../Documents`; create it if missing.
- *(all phases)* Confirm the folder pair: the supervisor runs in `Workspace/`. If the
  project predates the layout and the repo root is not named `Workspace`, do **not** move
  anything — record the actual paths under `Layout:` and treat the repo root as the
  Workspace boundary; the rename is the owner's call, offered once as a run sheet.
- *(Phase 2 passed)* Create `Documents/<Name> Project Summary.md` at the next reflection
  point if it does not exist.
- *(Phase 4 — planning)* If the build plan is not yet approved: run step 0
  (prior-project lessons) and add the per-stage **refactoring dial** before presenting.
  If the plan is already approved: group existing increments into stages if they are not,
  set the dial to **on** for remaining stages, and tell the owner in one line that they may
  switch it off — do not re-present the plan.
- *(Phase 5 — configuration, or later)* Via `cursor-configurator`, **append** what is
  missing: `.cursor/rules/workspace-boundary.mdc`, `.cursor/rules/minimal-code.mdc`, the
  `boundary-check` hook entry + script, `run-hidden.py` + `windowless-check.py`, the
  windowless idiom in every existing hook script, `run-hidden.py` on every direct-command
  hook entry, the windowless check in `.githooks/pre-commit`. Never overwrite `hooks.json`.
  Verify once with a throwaway edit while watching the desktop.
- *(Phase 6 — building)* From the next increment: `scope-check.py` at Inspect,
  `BOUNDARY_VIOLATIONS.md` read at Inspect, the routing table, the root-cause-first
  procedure on the next defect, the refactoring pass at the next stage close, the
  reflection point at the next stage close. An increment already delegated finishes under
  the brief it has; the next brief uses the current spec-packager template.
- *(all phases)* Nothing already approved is re-presented. No gate is reopened.

---
