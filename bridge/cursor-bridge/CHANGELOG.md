# Claude-Cursor Bridge — CHANGELOG

One entry per release. `VERSION` and `MANIFEST.json` are stamped by the maintainer's
`tools/make-manifest.py`, which refuses to stamp a version that has no entry here.

Each entry has three parts. **What changed** is for the maintainer and the curious.
**Running projects must** is the part `/calibrate-bridge` acts on: every item names the
**phase** it belongs to, so a project that has already passed that phase does not reopen
it, a project in it applies the item now, and a project before it applies the item when it
arrives. An item marked *(all phases)* applies immediately. **If rolled back** (since
2026.10.05a) says what a project that calibrated to the release must restore when the
release is taken back with `bridge-install.py --rollback`; an entry without it restores
nothing. A release with new mechanisms also names its **field acceptance**: what the trial
project must show before the other projects resume.

---

## 2026.10.30c

**Text corrections from release B's stage review** (BUG-037; stage B6's review, round 1): the run sheet's install check, one sentence of 2026.10.30b's entry on an increment in flight at the install, and step 4's sentence on an increment under review. No program changed; against 2026.10.30b, no file new or removed.

**What changed**
- **The run sheet's install check** (`commands/calibrate-bridge.md`, step 1): every install's check is the installer's exit 0 with the line it prints last, `RESULT: INSTALLED TREE MATCHES bridge <the release's version>`. The two signs it gave for every install, `VERSION` changed and the `previous` line printed, are what an install over an older release installed whole also shows: the same release installed again shows neither, and a repeat after an interrupted install prints the `previous` line or none, as far as the first run got (the installer reads the installed `MANIFEST.json`'s version, which the first run may or may not have replaced). The `previous` line is named as the installer prints it, `previous <version> kept at <folder>` with the spaces that align its columns.
- **2026.10.30b's entry** said that an increment built before release B and in flight at its install "seeds as before". The guard seeds rounds 1 to the highest round release B's launcher did not log: rounds 1 and 2 run before the install and round 3 after it seed rounds 1 and 2, and the next snapshot is `<ID>-r3`. The entry now says so. 2026.10.30a's in-flight item (the highest `<N>` of a tracked report) describes 2026.10.30a's guard: a project calibrating from 2026.10.25a reads it with 2026.10.30b's change.
- **Step 4's increment under review** (`commands/calibrate-bridge.md`): it finishes under the brief it started with, and its review follows the installed guard, as the next item says.

**Running projects must**
- *(all phases)* Install with every project paused, restart, run `/calibrate-bridge` before the next increment, then `bridge-check.py`, as 2026.10.30b's entry says. On the real install the installer ends 0 with `RESULT: INSTALLED TREE MATCHES bridge 2026.10.30c`; over 2026.10.30b installed whole it also printed its `previous` line, `previous 2026.10.30b kept at <folder>`. The installer keeps one release as the way back, so 2026.10.30a's kept copy is removed then and the way back is 2026.10.30b.
- *(building, changing)* Nothing to rewrite: no program changed, and the guard counts rounds as under 2026.10.30b.

**If rolled back**
- *(all phases)* Nothing to restore: no program changed. 2026.10.30b's texts return, its run sheet's install check among them, which again gives every install the two signs, `VERSION` changed and the `previous` line printed. The installer still ends on its `RESULT: INSTALLED TREE MATCHES bridge <version>` line: an install that exits 0 on that line is installed, with or without the two signs.

---

## 2026.10.30b

**A fix of release B's review guard, found by its trial** (BUG-036; the trial project, the TDP, 2026-10-30, its ISS-016): an increment begun under 2026.10.30a had its first Review B counted as one round more than every builder round it had run, so three builder rounds before the first Review B left it no name below the ceiling. One program; against 2026.10.30a, no file new or removed.

**What changed**
- **The guard counts Review B rounds only** (`review-guard.py`; BUG-036): where an ID has no `rounds-<ID>.json`, its first snapshot seeds the record from a tracked `handoff/<ID>-r<N>-report.md` (a letter after `<N>` included) only for a round that release B's launcher (2026.10.30a or later) did not log, that is a round with no `run/launcher/runs.jsonl` builder row whose `brief` is the ID and whose `round` is `<N>`. Under 2026.10.30a every builder round wrote such a report, and the seed counted each as a replied Review B round (`reply` 0): one builder round made the first snapshot `<ID>-r2` (`round 1 is reviewed: write <ID>-r2`), three made it `<ID>-r4`, above the ceiling. An increment begun under release B now seeds nothing from its reports, and its first Review B is round 1; an increment built before release B and in flight at its install seeds rounds 1 to the highest round the launcher did not log (rounds 1 and 2 run before the install and round 3 after it seed rounds 1 and 2, and its next snapshot is `<ID>-r3`; corrected by 2026.10.30c); the letter snapshots, the refusals and the seeded entries' shape are unchanged. A missing launcher log seeds every report, as before.

**Running projects must**
- *(all phases)* Install with every project paused, restart, run `/calibrate-bridge` before the next increment, then `bridge-check.py`. Paused means no builder, review, CI watch or suite running and everything committed; the bridge's own checkout is switched to `main` for the install (R-038, calibration's step 1). On the real install the installed `VERSION` reads 2026.10.30b and the installer printed `previous 2026.10.30a kept at ...`.
- *(building, changing)* Nothing to rewrite. A `rounds-<ID>.json` that exists, written by the guard or by hand, is read as it stands: the fix changes only the seed of an ID that has none. An ID with no record whose builder rounds ran under 2026.10.30a needs no hand seed any more; its first snapshot is `<ID>` or `<ID>-r1`. A record the 2026.10.30a guard wrote with `seeded` rounds that no Review B replied to (an ID whose first snapshot followed the guard's own `round 1 is reviewed: write <ID>-r2`) is set right by hand before its next snapshot as 2026.10.30a's entry says: its hash copy removed first, then the record written with one entry per replied round. Where the ID's rounds are above the ceiling by the launcher's count, the take-the-larger rule of `delegation-loop/decide.md` ("The review ceiling") still decides what sends work back.

**If rolled back**
- *(building, changing)* The 2026.10.30a guard returns with its seed. Before the first snapshot of an ID that has no `rounds-<ID>.json` and whose builder rounds ran under release B, write the record by hand as 2026.10.30a's entry says, `{"id": "<ID>", "rounds": []}` where no Review B has replied, so the first Review B is round 1. Records written meanwhile stand.

**Field acceptance**
- On the trial project, the TDP: the first increment after the install that ran one or more builder rounds before its first Review B takes that snapshot as `<ID>` or `<ID>-r1` with no hand seed, and its `rounds-<ID>.json` shows round 1 unseeded. Then reAngle and the video factory calibrate when they resume, on the owner's word, from 2026.10.25a through both entries.

---

## 2026.10.30a

**Release B, the restructuring** (the Restructuring Plan's release B, built on the bridge's own branches from 2026-10-11 and reviewed whole by a fresh context in two passes, both APPROVE, TASK-026): the supervisor's instructions split into a core read at every start and ten phase modules read whole in their phase, the hook naming the current phase's files after every compaction; conditional workflows for three product types, their sub-types and seven traits, chosen per part by a `Workflows:` line the workflow check holds; the code gate's three-round ceiling and numbered briefs held by the launcher and the review guard; one heavy job at a time on the computer, every launch windowless, and the suite's windowless default written into every pytest project; mutation reruns that skip what is unchanged; a pace report; calibration that applies conditional workflows by phase. Text and programs; against the 2026.10.25a installed from its hotfix, the release every project calibrated to (106 files, the core whole), 38 files new and two allow entries new.

**What changed**
- **The core and its phase modules** (`commands/supervisor.md`, `cursor-bridge/workflow/phases/`; TASK-010, TASK-011, TASK-012, TASK-013, TASK-014, TASK-022, TASK-035, BUG-017 to BUG-019, BUG-035): the core holds the roles, the founding rules, the loop's shape, escalation and reporting, project state and the standing rules (874 lines, 98,327 characters), and is read in parts, each call starting where the last ended, to its last line. The procedure moved, verbatim but for its recorded rewordings, into ten modules: intake, design, interface (with its four variants: mockups, playable prototype, command design, contract design), planning, run-parameters, configuration, delegation-loop (with its sub-files `decide.md` and `refactoring-pass.md`), change-cycle, reflection and project-end, each opening with what must survive a compaction and declaring its extension points; every module is within R-032's bound, the largest delegation-loop.md (452 lines, 57,217 characters). Intake classifies each part against the open list and the design gate settles its traits; the interface phase runs one variant per kind of interface; a change cycle runs the variant of every kind it touches and reads the conditional workflows of the step it has reached.
- **The conditional-workflow model** (`workflow/open-list.md`, `workflow/extension-points.md`, `Glossary.md`; TASK-003, TASK-004, TASK-005, TASK-009): five layers (core, phase module, product type, sub-type, trait), each change an add, a replace or a set at a point a module declares, applied in a stated order; the open list names every type, sub-type and trait with its definition, default traits and whether its file is written; the registry names every point, its module, the changes it accepts and whether it applies per part or per project; the Glossary holds the closed set of terms and the eight `Phase:` values.
- **The type and trait workflows** (`workflow/types/`, `workflow/traits/`; TASK-017 to TASK-021, BUG-020 to BUG-027): web app and its sub-workflow local web app; software on your own computer and its sub-workflow local service; host extension and its sub-workflow Claude Code extension; the traits has screens, installable, performance budgets and external services, the main workflow's conditional passages moved there unit by unit; and the new traits spends money (which actions cost money, the owner's cap, every paid action approved first, the store of paid results outside the Workspace), long-running process (start, stop and health) and AI models (pinned models, recorded outputs, evaluation before and after a change).
- **The `Workflows:` line and the workflow check** (`workflow-check.py`, `inventory-check.py`, `conformance-check.py`; TASK-006, TASK-007, TASK-008, TASK-024, BUG-001 to BUG-014): one line per part right after `Phase:`, in the open list's grammar, `not yet classified` before intake; the check holds every conditional workflow against the open list and the registry and a status file's lines against the open list; the inventory and conformance checks fail a missing or malformed line, and the conformance check grades a line naming an unwritten type or sub-type MISSING and an unwritten trait NOTE. Allowed in `settings.bridge.json`.
- **The hook's module pointers** (`session-start.py`; TASK-015, FIX-003, BUG-035): after a compaction, resume or fork the hook names the current phase's module files, their sub-files and variants, and the type, sub-type and trait files that touch the phase, in the order additions apply; a table it cannot read gives one plain line.
- **Calibration aware of conditional workflows** (`commands/calibrate-bridge.md`, `conformance-check.py`; TASK-023, TASK-024): step 4b writes a missing `Workflows:` line from the classification the project recorded and confirms it with the owner, keeps the `Phase:` value, and applies a conditional workflow by phase from the next design phase or change cycle, reopening no gate; step 1b grades the line. Step 1's run sheet pauses the bridge's own build and switches its checkout to `main` before an install (R-038), and names the installer's same-version refusal as the maintainer's; step 4 sends an increment in flight under the older release to the release's items for it (TASK-027).
- **Windowless, everywhere** (`bridge-run.py`, `windowless-default.snapshot.md`, `conformance-check.py`, `Cursor-Project-Configuration.md`; FIX-001, TASK-028, TASK-030, BUG-029): every launch starts with CREATE_NO_WINDOW; `--kind driver` runs a program under `run/supervisor/` or the installed `mutation-run.py` and nothing else (allowed in `settings.bridge.json`); the suite's windowless default ships verbatim as a snapshot, configuration writes it into a pytest project's `conftest.py`, and the `Windowless test suite` floor checks it (a Node runner reads NOTE: no default ships for it); the launcher knows `cursor-agent` by its bare name alone (`cursor-agent`, `cursor-agent.cmd` or `cursor-agent.exe`), never by a path.
- **One heavy job at a time** (`bridge-run.py`, `loop-guard.py`, `scope-check.py`; TASK-029, BUG-030, BUG-032): a builder, driver or test run takes the computer's one slot, `~/.cursor-bridge/heavy.lock`, before its command starts; a waiter prints `waiting for the slot held by <kind> <run id> since <start>, ends by <end>` once a minute, then `slot taken`, or ends with 123 and `slot not free` at its bound; a review or watch run takes none. The delegation loop's step 3 gives each heavy launch's duration once (28,980 s for a builder or a mutation run, 18,180 s for a suite) as the Bash tool's `timeout`.
- **Mutation reruns** (`mutation-run.py`; TASK-031, TASK-030): the supervisor's mutants in `run/supervisor/<id>-mutants.json`, run in a copy under `~/.cursor-bridge/scratch/<project>/`, kills cached so a rerun skips what is unchanged (`--all` runs every one), new tests run against the checkpoint with `--checkpoint` instead of an old-tree worktree; launched with `--kind driver`.
- **The code gate's ceiling, held by programs** (`bridge_env.py`, `bridge-run.py`, `review-guard.py`, `permission-guard.py`, `delegation-loop/decide.md`, `Merge-Verification-Policy.md`; TASK-032, TASK-034, BUG-030 to BUG-033): one copy of the ceiling (three rounds), the five blocking classes and the name grammar (`<ID>` or `<ID>-r<N>`). Every re-delegation and fix inside a gate is a new numbered brief, `handoff/<ID>-r<N>.md`. The launcher has each builder launch name exactly one brief on a branch, logs `brief`, `round`, `brief_sha256`, `brief_name`, `lift`, `lift_line` and `merge_ids` in runs.jsonl, and refuses (exit 125) a brief revised after a completed run, an ID outside the branch's declared set and a fourth round without a `Blocking class: <class> - <finding>` line or the owner's `Review rounds above the ceiling:` line. The guard keeps each ID's rounds in `rounds-<ID>.json` beside its snapshots and refuses a snapshot off its count or above the ceiling likewise. The review files carry the round: `REVIEW-<ID>-r<N>.diff`, `ASSUMPTIONS-<ID>-r<N>.md`, `REVIEW-<ID>-r<N>.err`, with `SCOPE-<ID>.md` committed before the snapshot.
- **The pace report and one reading of a squash subject** (`pace-report.py`, `plan-check.py`, `bridge_env.py`; TASK-033): per ISO week, increments started and merged, rounds, lifts and the increments over the ceiling, read-only; the plan check reads a subject's IDs the same way.
- **The installer** (`bridge-install.py`; BUG-034): a release folder carrying the installed version with other files is refused before anything changes (`--anyway` is the maintainer's rehearsals, with a warning that no way back was kept), so the release installed now stays the way back.
- **The maintainer's** (outside the installed tree unless named): the bridge's CI security floor (TASK-002), its records (TASK-001), the generated command reference (CONFIG-B3b), the builder's configuration (CFG-B3), the traceability check over the split (`trace-check.py`, installed but run only inside the bridge's repository; TASK-016, TASK-025), the two hotfixes carried onto main (HOTFIX-001, HOTFIX-002), the stage refactoring passes (REFAC-B2 to REFAC-B5) and the tests that settled the least-confident items (FIX-002, FIX-004).

**Running projects must**
- *(all phases)* Install with every project paused, restart, run `/calibrate-bridge` before the next increment, then `bridge-check.py`. Paused means no builder, review, CI watch or suite running and everything committed; the bridge's own checkout is switched to `main` for the install (R-038, calibration's step 1). On the real install, never a dry run: the installed `VERSION` reads 2026.10.30a and the installer printed `previous 2026.10.25a kept at ...` (a dry run prints that line without keeping the copy; the same release installed again prints none and does not rotate the kept copy). A refusal saying the release folder carries the installed version `but not its files` means `main` has moved past this release's stamp: never pass `--anyway`; tell the maintainer.
- *(all phases)* Re-read as step 2 now says: the core in parts to its last line, then the current phase's modules whole with their sub-files and variants, then the conditional workflows the `Workflows:` line names that touch the phase. After every compaction the hook names the same files; read each one it names.
- *(all phases)* A project calibrated to 2026.10.25a meets two `MISSING` floors at step 1b, both written during this calibration. The `Workflows line` until step 4b writes the `Workflows:` line from the classification the project recorded (until then `inventory-check.py` fails too), confirmed with the owner on the report's first line; where the project's inventory holds no classification row, write it first from the bridge's Decision 6 (reAngle and the video factory: web app, local web app; the TDP: software on your own computer, local service). And, where the suite is pytest, the `Windowless test suite` floor until step 1b writes the windowless default from `windowless-default.snapshot.md` between two suite runs: a failure present before the write is the project's own and recorded, a failure present only after it reverts the insert and leaves the floor `MISSING`, named in the report. A Node runner's suite reads `NOTE` (no default ships for it; use `detached: false`, KP-059), recorded in the status file.
- *(building, changing)* Install at a merge boundary where you can, with no increment in flight: then nothing in this item applies. An increment in flight at the install finishes under its brief, and its review follows the new guard (`review-guard.py`), whose rules are these. A review name is `<ID>` or `<ID>-r<N>` with the ID starting with a capital letter (`bridge_env.parse_review_name`, `_REVIEW_NAME_RX`): a numeric name (`007`, whose files were `REVIEW-007.*`) is refused, `the name cannot be read by the grammar` (exit 125). A letter-suffix name (`TASK-012b`) is read as an ID of its own at round 1, and its first snapshot or brief claims the branch, so the increment's own ID is refused there afterwards (`branch rule: TASK-012 is not on this branch (counted: TASK-012b)`). The guard counts rounds in `rounds-<ID>.json`; where there is none, the ID's first snapshot seeds it (`_seed_rounds`) with the larger of two counts, every seeded round counting as reviewed: the ID's snapshots named `<ID>` or `<ID>` plus letters (`_letter_snapshot_rounds`: those of one branch, a lettered one only where `handoff/<ID>.md` exists and `handoff/<ID><letters>.md` does not; a snapshot named `<ID>-r<N>` by the previous guard is not counted, nor a numeric one), and the highest `<N>` of a tracked `handoff/<ID>-r<N>-report.md`, a letter after `<N>` included (`handoff/<ID>-r<N>b-report.md`; `_report_file_rounds`). A snapshot is admitted only for the round counted last or the next one (`snapshot_review_refusal`), so an in-flight `<ID>-r2` or `-r3` whose earlier rounds were not counted is refused, `round <N> is off the count (current <C>)`, and a counted round taken again on a changed tree is refused with the name to write, `round <N> is reviewed: write <ID>-r<N+1>`. A round counts as run only once its Review B reply came back: a snapshot taken before the install whose review had not replied is not a round, yet the guard seeds it as one, and retaking it is then refused (`round 1 is reviewed: write <ID>-r2`). So, before each in-flight ID's next snapshot: list it with the rounds its records show as replied and the count the guard will seed, and where they differ seed it by hand, writing `rounds-<ID>.json` in the `bridge/` folder of the repository's common git folder (for a worktree, the main repository's) before the guard first reads it, as an object `{"id": "<ID>", "rounds": [...]}` with one entry per replied round (`round`, `name`, `branch`, `tree` empty, `reply` 0, `seeded` true), or an empty `rounds` list when no round has replied, so the ceiling counts the rounds actually run. Then write the round's review files under the admitted name (`REVIEW-<ID>[-r<N>].diff`, `ASSUMPTIONS-<ID>[-r<N>].md`), commit `SCOPE-<ID>.md`, take the snapshot again under that name and run Review B again: a snapshot taken before the install is not verified under the new names.
- *(building, changing)* Briefs are numbered from the install: every re-delegation and every fix inside a gate writes `handoff/<ID>-r<N>.md`, never a revision in place, numbered by the rounds the increment's records show (the launcher reads the round from the name, `launcher_effective_round`); `BUG-<nnn>` is the brief of a defect found after a merge. The launcher refuses a brief whose bytes changed after a completed run (`revised in place: write handoff/<ID>-r<N+1>.md`), a launch naming no brief or two, a brief under an ID the branch has not declared, and a builder launch on `main`, a detached HEAD or outside git.
- *(building, changing)* The review ceiling is held by the programs from the install, so a project that held it by hand stops doing so: past round three, only a `Blocking class: <class> - <finding>` line, the class first, in the brief and in `run/review/SCOPE-<ID>.md`, or the owner's `Review rounds above the ceiling: <ID> <rounds> (<their words>, <date>)` line in `docs/RUN_PARAMETERS.md` opens a round; an in-flight brief already numbered above three needs one before its launch. A refusal is a stop, not a model's failure (step 3b).
- *(building, changing)* One heavy job at a time on the computer: every builder, driver and test run takes the slot, so a second waits, naming the holder, or ends with 123 at its bound (step 3b: a wake-timer until the holder's `ends by`, then one relaunch); `Parallel increments: on` no longer builds two at once on this computer. Every heavy launch sets the Bash tool's `timeout` from step 3; every suite runs through the launcher in the background for `test-runner` to read; every mutation run is `mutation-run.py` with `--kind driver`, its mutants in `run/supervisor/<id>-mutants.json`.
- *(all phases)* The conditional workflows this release adds, applied by step 4b to each part whose `Workflows:` line names them, reopening no gate: the types web app (sub-workflow local web app), software on your own computer (local service) and host extension (Claude Code extension), and the traits has screens, installable, performance budgets, external services, spends money, long-running process and AI models. Their additions at intake, design, interface and planning points, and a type's `Set at intake.delivery-kind`, take effect from the part's next design phase or change cycle, never backwards. Their additions at the delegation loop's points (`delegation-loop.brief-constraints`, `.inspect-checks`, `.test-checks`) bind in `building` and `changing` from the install, from the next brief packaged, since the hook names those files after every compaction: for has screens, external services and performance budgets this is mostly the main workflow's own text, moved; new are spends money's brief constraints, inspection and tests (reAngle), long-running process's brief constraints and tests, AI models' tests, and host extension's tests inside a real host. The new traits' `configuration.items` (spends money's store of paid results, long-running process's start, stop and health commands, AI models' pinned models and recorded outputs) are configuration additions for a phase already passed: applied now through `cursor-configurator`, append-only, before the next increment that makes a paid call, keeps a process running or calls a model. The `project-end.delivery` additions run at project end for the kind the inventory's `Delivery kind:` row names; a project past design without that row writes it now from its type and sub-type, a record-keeping addition.
- *(all phases)* The `Bridge version:` line is written by calibration's step 5 alone. A project whose line already reads 2026.10.30a takes the no-delta path (step 3), which runs no step 4, so one whose records were moved to this version before its calibration applies these items by hand.

**If rolled back**
- *(all phases)* The rollback restores the kept copy of the release installed before, removing what that copy lacks. Where that is the 2026.10.25a of the hotfix, the release every project calibrated to, it removes the 38 files only release B ships (the phase modules, their sub-files and variants, the open list, the registry, the type and trait files, the trace baseline and exceptions, `mutation-run.py`, `pace-report.py`, `trace-check.py`, `workflow-check.py`, `windowless-default.snapshot.md`) and the two allow entries only it added (`bridge-run.py --limit * --kind driver -- *`, `workflow-check.py`), and a project's records that point at them (`Calibration pending:` items, `Working files:`, a note naming a module) are pointed back at the restored core, which holds the whole procedure again and is read whole. These items are written for that tree. `main` carried the version 2026.10.25a from HOTFIX-002's merge to this stamp with part or all of release B in it, and no project installed from it; where the kept copy is such a tree (a maintainer's rehearsal), the rollback restores it as it is, and each item here applies only to what that tree lacks.
- *(all phases)* The `Workflows:` line stays: it is the project's classification, and the hotfix's 2026.10.25a reads none of it. The windowless block in the project's `conftest.py` stays: it is the project's own test code and keeps the suite windowless under any release.
- *(building, changing)* `rounds-<ID>.json` in the git folder's `bridge/`, with its hash copy `~/.cursor-bridge/review-hashes/<key>-rounds-<ID>.sha256`, is ignored by the previous guard, and the three-round ceiling goes back to the supervisor by hand. Before release B is installed again, an ID reviewed in between has its hash copy removed first (a copy without its record is refused, and a record changed while its copy stands is refused, `rounds record changed outside the guard`), then either its record removed too, so the guard seeds it again where no snapshot taken under release B lies beside it (one that does is refused, `rounds record missing beside snapshot with round field`), or otherwise its record written right by hand, since the count would otherwise stop at the rollback: a record whose copy is gone is trusted as found on first read.
- *(building, changing)* Numbered briefs stay as written; the next re-delegation follows the previous text. The new runs.jsonl fields (`brief`, `round`, `brief_sha256`, `brief_name`, `lift`, `lift_line`, `merge_ids`, the slot's `slot` and `waited`) stay in the log and the previous programs pass over them; rows logged in between carry none, so on a reinstall the launcher's count for an ID is its brief's name's round or, where release B's rows from before the rollback show more, one more than the distinct brief names completed there (exit 0; `launcher_effective_round`).
- *(building, changing)* The scratch folder `~/.cursor-bridge/scratch/<project>/` is read by nothing in the previous release: remove what a mutation run cut short left there. The mutants files under `run/supervisor/` stay. Mutation runs, the one heavy job at a time and the windowless driver go: builders are started one at a time by hand again.

**Field acceptance**
- reAngle, the trial, calibrates before the others resume: its `Workflows:` line valid, no gate reopened, and where its suite is pytest the `Windowless test suite` floor OK with no test failing after the write that passed before it (a failure present before the write recorded as its own), or its NOTE recorded where it runs a Node runner; an insert reverted for a failure present only after the write is recorded with the floor MISSING and stops the trial as a finding for TASK-026's fixes. It resumes; after its first compaction under this release the hook names its current phase's module or modules, read whole (visible in the transcript or `run/supervisor/`); its `Workflows:` line passes `workflow-check.py`; one increment goes through the loop with no gate reopened, its first builder run printing `slot taken` in its `.err` file, its runs.jsonl row carrying `brief`, `round` and `brief_sha256`, and the guard's count for each ID in flight at the install being the rounds its records show as replied. Then the video factory and the TDP calibrate and resume on the owner's standing policy, one calibration each, none pausing, with the same floor OK and no failure present only after the write, or its NOTE recorded.

---

## 2026.10.25a

**The report cycle's program follow-ups** (a hotfix of 2026.10.18a, cut from its release state, on the owner's word of 2026-10-25, decision D5): the program items of the Sunday evaluations of 2026-10-18 (C1 to C6, C8, C9; its C7 was 18a) and 2026-10-25 (C1 to C12). Programs, with one settings line; the text items of both runs ship as release T after release B (decision D4), except the three calibration items below.

**What changed**
- **The roster's switch** (`roster-check.py`; ISS-008, FB-001, FB-008, FB-013): the family rule governs Review B only. When the chosen profile's Review B is of the family that built the change in flight (a switch after a pool ran out), the profile still resolves, with a `REBUILD` line and a `"rebuild"` entry in `docs/ROSTER.resolved.json`: its builder rebuilds the change first. A branch with no builder run has no built family (another branch's run no longer counts). The service's `[unavailable]` line is a connection error, never the model's failure, and `--clear-unavailable <model>` removes a wrong mark. A probe reply that is not the word OK but not a usage-limit message counts as answered, off-script; FAIL stays for refusals, empty replies, time-outs and usage-limit text. `docs/ROSTER.resolved.json` is rewritten only when what it resolves changes (the time of each check goes to the untracked state as `last_resolved`), so a check before a snapshot leaves the tree clean.
- **The launcher** (`bridge-run.py`; ISS-010, FB-002, FB-034): a `--kind review` run whose `--model` is of the family of the branch's last builder run is refused (exit 125) until the rebuild; a builder run started with `--workspace <worktree>` is logged under the worktree's branch. A stage review's branch has no builder run of its own and is not checked. A builder or review run lists the files beside the Workspace (its parent, the Workspace and `Worktrees/` excluded) before and after and reports each new, changed or removed one as `bridge-run: BOUNDARY ...` on stderr and in the run log: the one detection of a write outside the Workspace, since the boundary hook does not run in a headless builder run. A `gh pr checks <n> --watch` waits up to two minutes for the pushed head to be the pull request's head with a check registered, and says how long. `-p no:cacheprovider` is accepted after `python -m pytest` and the project's `.venv` python.
- **The review guard** (`review-guard.py`; ISS-004, FB-003, FB-037): `snapshot` prints the size of every file under `run/review/` named for its id and refuses an empty one (KP-067); it writes the snapshot's hash outside the checkout the reviewer runs in (`~/.cursor-bridge/review-hashes/`), and `verify` and `premerge` compare it themselves: a rewritten snapshot is GATE-INTEGRITY, a missing copy CANNOT VERIFY (take the snapshot again). `premerge` reads a pull request's head on GitHub again every 15 seconds for up to 90 while it differs from the local head, and flags only if it still differs.
- **Scope, records and stage diffs**: `scope-check.py` counts `docs/DESIGN_CRITIQUE.md`, `docs/HARDENING.md` and `project.json` as records, takes `--base <commit>` before or after the brief (a re-delegation measured from the round's brief commit), and reads a commit of records and test files only whose subject starts with `supervisor:` as the supervisor's, not drift, unless it was made while a builder run was logged (a builder commits in the parallel variant; no readable run log, no exemption) (FB-004, FB-009, FB-014). New `records-check.py --since <commit> [--ref origin/main]`: every merged TASK, BUG or FIX id has its `docs/CHANGES.md` line (2026-10-18 C1). New `stage-diff.py <sha>... --out <folder> [--name <stage>]`: an interleaved stage's whole change and its parts from its own squash commits, a later stage's merges set back (FB-005, FB-017). Both are allowed in `settings.bridge.json`.
- **Invisible characters** (`invisible-check.py`; FB-010, FB-029): the no-break and fixed-width spaces (U+00A0, U+2000 to U+200A, U+202F, U+3000) are flagged; `--non-ascii` lists every non-ASCII character of the changed files without changing the exit code.
- **The conformance check** (`conformance-check.py`; ISS-005, ISS-010, FB-007, FB-026, FB-031, the TDP's FB-006): a negated environment-variable mention is no supply by environment; the boundary-check hook is NOTE (configured, not engaging) until `~/.cursor-bridge/boundary-probe.json` records it firing; MISSING for the hook without `docs/BOUNDARY_VIOLATIONS.md` ignored, `socket ci` without `--no-banner`, the Socket CLI installed in the step that holds its key, and an absolute computer path in a tracked `docs/PROJECT_STATUS.md` (only line numbers printed).
- **The Semgrep rules** (`semgrep-bridge-rules.yml`; 2026-10-18 C5): both operand orders at every sink, the literal-only exclusion at the top of the argument, `executemany` excluded like `execute`, the header narrowed to what the rules catch; planted-probe tests where Semgrep is installed.
- **The loop guard** (`loop-guard.py`; the TDP's FB-006, FB-027): a monitor task (an artifact live-update monitor, a Monitor tool task) is neither a wake source nor an agent and demands no wake-timer; an Agent task stays timer-bound and a shell command counts by its pattern. A `Paused:` line in `run/supervisor/in-flight.md` naming what the pause waits for is a wait (`Paused: no`, `none` or `resumed ...` is not), so a pause need not edit the tracked status file; the line is deleted on resume.
- **The report cycle** (`evaluate-reports.py`, the maintainer's tools): an entry written after a forced verdict is shown once as WRITTEN and fingerprinted; the bridge's own project is listed, its notes read from the `-Workspace` memory key only; a recurrence heading is an update of its entry; the incidents a status file's `Open issues:` line names as to write are shown; the extract says its times are UTC; `tools/compaction-baseline.py` reads the `-Workspace` transcript folders.
- **The installer** (`bridge-install.py`; FB-016): besides `main` as merged, it installs from a `release/*` branch whose head equals `origin/<that branch>` and is a pull request's merge made by GitHub (committer noreply@github.com, a subject ending `(#<n>)`; release branches are not protected like `main`), with nothing uncommitted; a hotfix no longer needs a `git archive` copy. The check stops an accidental push, cherry-pick or rebase, not a deliberately forged committer; a branch rule on GitHub for `release/*` would stop that too.
- **The suite is windowless** (`tests/conftest.py`, FIX-001 of release B carried back): every program a test starts gets CREATE_NO_WINDOW when it sets no flags.

**Running projects must**
- *(all phases)* Install, restart, `/calibrate-bridge`, then `bridge-check.py`.
- *(all phases)* Three items of the report cycle that protect the gate or money, until release T writes them into the instructions: (1) Review B and every reviewer write no file under the checkout and point no cache there (`pytest -p no:cacheprovider`); scratch files and test caches go to the system temporary folder; they edit nothing; add this to the directive's clauses as you launch it. (2) No plan ID anywhere in the title of a pull request that is not an increment's, the closing parenthesis included; an increment's title starts with its ID. (3) A vendor CLI in CI runs with its banner, spinner and telemetry off (`socket ci --no-banner`), is installed in a step that does not hold its key (with `--ignore-scripts`), and the first CI log of a step holding a secret is read for any part of it.
- *(all phases)* Run `conformance-check.py`. A new MISSING is fixed as a records or configuration commit through the gate before the next delegation: the status file's `Layout:` line names `Workspace/` and `Documents/` relative to the project root, no computer path; `docs/BOUNDARY_VIOLATIONS.md` in `.gitignore` where the boundary hook is configured; `--no-banner` on `socket ci`. The boundary floor reading NOTE is expected and asks nothing; the launcher's BOUNDARY lines are the detection.
- *(all phases)* A Review B snapshot taken before the install has no hash copy: take it again (`review-guard.py snapshot <nnn>`) and run Review B on it. A changed line that holds a no-break or fixed-width space is now an `invisible-check.py` finding: in code and tests write the character as `chr(0x00A0)` or an escape the language reads, and a finding in data that is itself under test (a formatted currency string) is dispositioned as intended in the sentinel's report, never left as a FAIL.
- *(building)* A `REBUILD` line from `roster-check.py` means the change in flight is re-delegated to the resolved builder (the brief revised in place with a run-r<n> section) before Review B; the launcher refuses that Review B until then. A `bridge-run: BOUNDARY` line after a builder or review run is a boundary violation (step 4): read it before anything else. The listing cannot tell who wrote a file, so a change in a folder another session or the owner writes during the run (the bridge's `Reports/`, a `Temp/` folder, the root's `.claude/`) is checked against that writer before it is called the builder's; a write the builder made is never cleared that way. Use `scope-check.py --base <the round's brief commit>` for a re-delegation, a `supervisor:` subject for your own records-and-tests commits, `records-check.py --since <the stage's first checkpoint>` before a stage review, `stage-diff.py` for a stage whose increments interleaved with another's, and `invisible-check.py --non-ascii` on a brief before its checkpoint commit.

**If rolled back**
- Nothing to restore. The hash copies under `~/.cursor-bridge/review-hashes/` and the roster state's `last_resolved` are ignored by the previous release; a REBUILD order then rests on the supervisor alone, and the previous roster check fails the switch as it did on 2026-10-18.

**Field acceptance**
- On the first project to resume: `roster-check.py` run twice leaves the tree clean; a builder run prints no BOUNDARY line it should not; the first CI watch prints how long it waited; `conformance-check.py` reports the boundary floor as NOTE.

---

## 2026.10.18a

**The design critique's ceiling** (a hotfix of 2026.10.11d, cut from its release state, on the owner's order of 2026-10-18; KP-062). The TDP ran its design two-critic loop for 45 rounds on one change. Text, with one program change

**What changed**
- **At most four rounds per subject** (the design, the plan, each change and its plan addendum, a mid-build scoped revision being a change), whatever the critics still find; a finding that reverses an earlier fix is non-convergence, starts no round and waits for the resolution round. Then, if the text changed after a critic last read it, one confirming read by both, final whatever its number: its file says it is the confirming read and holds the diff since each critic's last read, labelled by critic, and its findings are fixed (recorded as fixed, unverified) or accepted with a reason. Then one resolution round, `DESIGN-<subject>-R1.md`, holding every question still Blocking or non-convergent, answered in place of findings; Review B's reply, which arrives on the launch's output, is written to `REVIEW-DESIGN-<subject>-R<n>.md` for `plan-critic`. A subject is one token of lower-case letters, digits and hyphens, distinct from every other, a change's chosen from its name and written in its record's heading. Then the gate, whatever is still open, its critique record listing it (supervisor.md, Phase 2; the plan's critique, Phase 4, now names its file `run/review/DESIGN-plan-<round>.md`; the change cycle's steps 2 and 4 name their subjects). A failed launch runs once more on the same file and spends no round; the launches follow step 3b, every one recorded: the second failure (exit 3) marks the model and the file runs once on the re-resolved profile; then the design waits for the roster or the owner's word, and the file runs once more under its number with no re-runs; if that fails too, the round stays not run and the subject goes on to its resolution round or its gate; a round never run spends none of the four. The record gives each round's commit, and refused or not-run rounds.
- **The convergence rule is the code gate's only**: two critics naming one finding no longer makes it blocking or adds a round (supervisor.md step 8, Merge-Verification-Policy.md).
- **The launcher holds the ceiling**: `bridge-run.py` refuses, with exit 125, before anything starts, and with a message beginning `bridge-run: refused - design ceiling: ` that names the file, the round and the `docs/RUN_PARAMETERS.md` it looked in, a `cursor-agent` launch naming, anywhere in its arguments and with either path separator, a `run/review/DESIGN-<name>.md` whose round (the name's last hyphen-separated part: a positive integer without a leading zero, or `R` and one; 1 to 5 and `R1` allowed) is above five, is `R2` or later, or cannot be read (a name is read from `DESIGN-` up to `.md`, lower-case letters, digits, hyphens and the round's `R` only; a one-part name such as the plan's old `DESIGN-5.md` is a round with an empty subject); one refused name among several refuses the launch. A line `Design rounds above five: <subject> <rounds> (<their words>, <date>)` in `docs/RUN_PARAMETERS.md`, written only on the owner's own words and never asked for (`<rounds>` a round number: the last numbered round run, a resolution round not counted, plus the more rounds they name, or five more when they name none, never below six; the report says how `<rounds>` is spent), allows that subject rounds up to `<rounds>` and `R2`, and nothing beyond: the same shape once more, once, the first well-formed line standing and a later one ignored; a further send-back makes a scoped revision. The empty subject of the plan's old files is never lifted. A refusal is not a model's failure (step 3b); the subject goes on to its resolution round or its gate. Tests (`tests/test_bridge_run_design_ceiling.py`): rounds 1 to 5 and R1 allowed; round six, round 45, R2 and R3 refused; 0, 05, 06, R0, a round that is no number, a name holding a space or a capital and a design file with no `.md` after its name refused; `DESIGN-1.md` to `DESIGN-5.md` allowed and `DESIGN-45.md` refused; a subject holding hyphens or digits read whole; a backslash path, an absolute path, trailing punctuation, doubled separators, `.` segments and folder names ending in dots or spaces read; a round too long for `int` refused without a traceback; a launch naming an allowed and a refused file refused; any mode refused alike; other review files and commands untouched; the owner's line lifting one subject only, up to its rounds and R2; the first well-formed line for a subject standing and a later one ignored; a line lifting `plan` not lifting the old one-part files; a line without the owner's words, or not above five, lifting nothing; exit 125 before the launch line, the message beginning `bridge-run: refused - design ceiling: ` and naming the file, the round and `docs/RUN_PARAMETERS.md`, nothing logged.
- **The digest's rule 6** names the exception, its "stop only on non-convergence" kept to re-delegation (the digest's opening line, which the hook's header already says, and the report line's "explain for decision", which is rule 21, are dropped to pay for it). Standing rule 6 in full, the run parameters' optional lines and step 3b say the same. `plan-critic` raises only what is new, or Blocking, in a confirming read, only answers in a resolution round, lists a Blocking finding open after the last resolution round at the gate, and never grades up on agreement.

**Running projects must**
- *(all phases)* Install, restart, `/calibrate-bridge`. A design, plan or change critique that has run four rounds or fewer follows the new text from where it stands. One that has run five or more, whatever its fifth was, gets no confirming read and no further round: the last round's fixes are recorded as fixed, unverified; whatever is still Blocking or non-convergent goes to `DESIGN-<subject>-R1.md` if that subject has had no resolution round, else straight to the gate, whose critique record lists what is open. Only that subject's owner's line allows more, and then it continues under Phase 2's shape from where it stands. A running subject whose name is not such a token takes one at calibration, written in its record's heading (a plan critique on the old `DESIGN-<round>.md` files takes `plan`); its next file carries it and its count continues. A round file named other than by its number (a confirming read written `DESIGN-<subject>-confirm.md`, say) cannot be read and is refused: its next file takes the next round's number.

**If rolled back**
- Nothing to restore. The previous launcher does not refuse a sixth round, so the text's ceiling is then held by the supervisor alone.

---

## 2026.10.11d

**The report cycle's text items** (the follow-ups accepted by the evaluation of 2026-10-11, plan section 16 under A5's status; the A5 follow-up), with the trial's observations under A5 and the owner's decision D1. Text, with two small program changes for the builder's report file.

**What changed**
- **Step 8's quiet rule names the writing subagents**: while Review B runs on a snapshot, no `spec-packager` (the next brief waits for `verify`), no `diagram-specialist`, no `cursor-configurator`, nothing that writes under the checkout, the status file included (reAngle ISS-014: a brief written during a review flagged GATE-INTEGRITY, rightly).
- **The builder's report is a file it writes as it runs**, `handoff/TASK-<nnn>-r<N>-report.md` (`REFAC-` for a refactoring), its last message the summary and the path; twice a last message arrived as one line and the report with it would have been lost (A5 made the last message the report). The brief's Scope names the file beside `docs/BUILDER_NOTES.md`; the `Assumed, not verified` section stands in it and the accept commit keeps it; the SCOPE file for Review B lists it as expected; `diff-reviewer` reads it as the self-report it is. `scope-check.py` counts it as bookkeeping (never drift) and `plan-check.py` neither reads it as a brief nor flags it in a Scope — two program lines, each with a test. The constant pointer's last clause now asks for the summary and the report's path.
- **Mutation drivers are the supervisor's side's**: written in step 4 with the criterion tests, never by the builder, read by `diff-reviewer` mutant by mutant against the names, ended whole with `bridge-stop.py`; the builder's in-process mutation stays by hand, no script of it in the diff; a fix brief after a driver run asks for the code fix only (reAngle TASK-010c: three rounds on five mutants that did not model their names). The brief's mutation list stays.
- **A maintainer's request is recorded and answered without the owner** (decision D1, 2026-10-11): the status file gains a `Maintainer requests:` line; the answer goes into the project's Feedback document under its own `FB-nnn` entry when done (the one write to `Documents/` outside a reflection point besides an issue placeholder), and the next report to the owner states it in one FYI line (rule 57).
- **A stage review in parts**: a stage diff too large for one reading is written in parts from the same committed state, the test files' part at most 25 files; a part that ends at the reviewer's turn limit without a verdict is run again on what it had not reached (reAngle: a 79-file part hit the limit).
- **A suite over ten minutes** runs through the launcher in the background (`--kind test`), never inside `test-runner`'s foreground call, which the Bash tool ends at 600 seconds; `test-runner` hands such a suite back and reads the output file afterwards (KP-061, from reAngle's A5 walk).
- **The CI watch that returns at once**: wait for the first check to appear, start the same watch again, and confirm the green run's head is the pushed head before `premerge` (KP-051 named in step 8).

**Running projects must**
- *(building, changing)* Install, restart, `/calibrate-bridge`. Add the `Maintainer requests:` line to `docs/PROJECT_STATUS.md` (`none`). From the next brief on, the Scope names the builder's report file and the Done section asks for it (the packager's template has both); a mutation driver the builder wrote is replaced by one of the supervisor's side's at the increment's next touch; a suite over ten minutes runs through the launcher; a wrapper of the project's own that carries the constant pointer's text (reAngle's `run/tools/delegate_pg.py`) takes the new last clause at calibration; the accept commit adds the report with `git add -f` where the project ignores `handoff/`.
- *(all phases)* A maintainer's request received before this release and not yet answered goes on the `Maintainer requests:` line now and is answered in the Feedback document.

**If rolled back**
- The previous `plan-check.py` reads a report file under `handoff/` as a brief and flags the report line in a Scope: for every unmerged increment, move its `handoff/*-report.md` under `run/agent/` and drop the report line from the brief's Scope. Remove the `Maintainer requests:` line, or leave it (the previous texts ignore it). A wrapper of the project's own that carries the constant pointer takes the previous wording back. Set `Bridge version:` to the installed version.

**Field acceptance on the trial project.** One increment delivered with its report file in `handoff/`, the scope check listing it under BOOKKEEPING and `plan-check.py` not flagging it; one maintainer's request recorded on the status line and answered under an `FB-nnn` entry, stated in the next report; and, where a stage review falls in the window, its parts of at most 25 test files.

---

## 2026.10.11c

**The report cycle's program items** (the follow-ups accepted by the evaluation of 2026-10-11, plan section 16 under A5's status; the A4 follow-up). Each with a regression test that fails on 2026.10.11b.

**What changed**
- `pr-activity-check.py` reads the gh output as UTF-8: on a cp1252 console one character of a pull-request comment crashed the check and printed CANNOT VERIFY (a check that cannot run is a gate that passes by accident).
- The loop guard takes a kind from a project's own delegation wrapper marked `# wake builder` or `# wake review` (reAngle's `run/tools/delegate_pg.py`, which calls the launcher itself) and gives it that kind's ceiling; rule 43 says so where `# wake` is introduced.
- **`bridge-stop.py`** (new) ends a background task's whole process tree: a launcher run by its id, from the pid file the launcher now writes under `run/launcher/pids/` while it runs, after checking the pid is still that launcher (a stale file is removed, an ended run refused), or any process by `--pid` with its command line printed first; on Windows through `taskkill /T /F`, elsewhere the process group, never the caller's own. Stopping a verification loop with it never advances the loop into its next driver (KP-056); `TaskStop` ends the loop only.
- The credential helper is reset in a git config file of the bridge's own, `<profile>/.cursor-bridge/gitconfig`, which includes the owner's global config and holds an empty `helper =`; `GIT_CONFIG_GLOBAL` points at it, and `GIT_CONFIG_PARAMETERS="'credential.helper='"` (non-empty, so a wholesale restore keeps it) is read last of all, after the checkout's own `.git/config`, so a helper a builder writes there cannot re-enable the owner's stored login; the empty `GIT_CONFIG_VALUE_0` is gone (a wholesale environment restore on Windows dropped it, reAngle ISS-016, twenty builder-only test failures). The shim writes the same file with forward slashes and refuses the run when it cannot.
- `refactor-check.py`'s size budget leaves out `handoff/` and `run/` (a refactoring's driver re-anchors are bookkeeping); `test_*.py` and `*_test.py` count as test files only under a tests folder, so a product module named like a test is product.
- `conformance-check.py` recognises Socket's pin in `npm install -g @socketsecurity/cli@<version>`, and the adapter evidence accepts a folder of recordings (`fixtures/modal_contract/`) loaded through a helper.
- `evaluate-reports.py` does not count a stage heading's short preamble without a list item of its own (reAngle's "Bridge versions in force: ..." lines; its items are the `###` sections) as an entry, and an entry cut at the 6,000-character display limit of `unprocessed.md` says so.
- The subagent resumed by `SendMessage` (the evaluation's item 3) was reproduced on reAngle on 2026-10-11 before anything changed: the hook lists the resumed agent under its original id, type `subagent`, status `running`, which the loop guard already reads as a background agent; with its wake-timer running the stop was allowed. No change; the project's record (`run/supervisor/loop-guard-input-resumed-2026-10-11.json`) is the evidence.

**Running projects must**
- *(building, changing)* Install, restart, `/calibrate-bridge`. A delegation wrapper of the project's own carries `# wake builder` or `# wake review`; a verification loop is stopped with `bridge-stop.py`; nothing else changes in the loop.

**If rolled back**
- Nothing to restore: `run/launcher/pids/` may stay; the previous recipe sets the empty variable again. Set `Bridge version:` to the installed version.

**Field acceptance on the trial project.** reAngle's wrapper marked `# wake builder` counts under the builder's ceiling (the loop guard allows the stop); one builder or reviewer run under the new git config file finishes its git reads and writes as before (the identity kept, no credential prompt, no helper); `bridge-stop.py` ends one launcher run or one loop whole.

---

## 2026.10.11b

**Release A5 of the restructuring plan: the briefs, the reviewers' instructions and the pitfalls** (plan section 13.1 and the A5 scope). Text only: no program changes, no new numbered rule.

**What changed**
- **The tests run before the first reviewer** (step 4): the supervisor writes the missing tests first, each with `enforces: <document> §<section>`; `test-runner` runs them and the suite, told which test files are the increment's; a skipped test of the increment fails the step; every new or changed test is run once against the checkpoint's code in the supervisor's one worktree, `../Worktrees/old-<nnn>` (rule 39's exception), where the package resolves there (an editable install cannot be run against the checkpoint; the step says so and the reviewer's paragraph check stands in); step 6 keeps the benchmark floor and the observability tests; `diff-reviewer` is told which tests are the supervisor's.
- **The brief** (`spec-packager`): the git commands that are not the builder's to run; numbers parsed with the language's parser, with the unit and range stated; the checklist for an increment that starts a process (windowless, stopped in `finally`, no orphan, a browser attached on Windows, the pipes closed); every verification command written in full; the builder's last message is its report; one scope per brief; the mutation list.
- **Review B's prompt** (step 8, the policy): a committed `run/review/SCOPE-<nnn>.md` beside the diff carries the brief's Scope and Out of scope, the tests the supervisor wrote first with the paragraph each enforces, and the bookkeeping files in the diff that are expected (nothing of it inline through the shell); the prompt names it and says that design for later increments is not this diff's defect, that a claim about a build is verified by building it, and that the reply is one of the three verdicts; a reply with none of them is a failed launch, re-run once, then the roster's failure path.
- **The reviewers' lists**: a negative test shows its precondition (`diff-reviewer`, `security-auditor`); a path that changes data is tested on data the previous version made; libraries and drivers are tested against the real thing, as an external service is; `test-runner` reports a skipped test of the increment as a failure.
- **The merge policy**: the procedure for a vulnerability newly published in a pinned library nobody touched (a `DEP-<nnn>` increment off `main`, merged first, then `main` into each blocked branch); the CI watch's green run must be the pushed head's.
- **The delegate step**: the Bash tool's own `timeout` is set to the kind's cap on every background launch (the builder's, Review B's, the CI watch's, a suite's, a wake-timer's), since the tool once ended a background command after thirty minutes (observed once; KP-053).
- **The delivery conventions**: the delivery's proof is the owner's run of the installer check from their terminal by a run sheet, the supervisor's own run being a rehearsal, since the packaged desktop app writes into a hidden copy of the local application folder; `-AppId` in braces; `cursor-configurator` writes the pre-commit hook with the formatter's check beside the lint command where CI runs one; `secret-sentinel` greps for merge-conflict markers.
- **Known Pitfalls KP-044 to KP-060**, from the three projects: the local tool and the weaker pre-commit; Linux CI against a Windows workstation; a setting read on both sides of the WSL boundary; a polled file published half-written; a framework writing instruction files and a build emptying a tracked folder; an image pinned by name only; a vulnerability published after the pin; a watch reporting the previous run; an escape typed in a here-document; the Bash tool's thirty minutes; the installed product run from the Workspace; the packaged app's hidden folder copy; interrupted mutation drivers; an orphaned server holding a pipe; test isolation; a detached browser's console windows; surviving conflict markers.

**Running projects must**
- *(building, changing)* Install, restart, `/calibrate-bridge`. From the next increment on: the tests run before Review A and the new tests once against the checkpoint where the package resolves in the worktree; every background launch carries the Bash tool's `timeout` at the kind's cap; the next brief carries the new Constraints (the packager's template has them); the next Review B launch commits `run/review/SCOPE-<nnn>.md` beside the diff and names it in the prompt; a project configured before this release adds the formatter's check to its pre-commit hook at its next configuration change.
- *(building, changing)* A test the supervisor wrote before this release gets its `enforces:` line at the next stage close reflection; a negative test without its precondition is fixed when its file is next touched.
- *(all phases)* At the next reflection point, read KP-044 to KP-060 against the project's own records: a pitfall the project has already met and recorded elsewhere gets a pointer to the KP; one it has not met yet gets a checklist line where its sign would appear (the pre-commit hook, the CI job, the inventory).
- *(done, changing)* A project with an installer runs the installer check from the owner's terminal by a run sheet at its next delivery.

**If rolled back**
- Nothing to restore: the previous texts read the same files. A brief written under this release stays valid under the previous one. Set `Bridge version:` to the installed version.

**Field acceptance on the trial project.** One increment walked through the loop under the new texts: the tests ran before Review A and the new tests were run against the checkpoint, or the step said why not (the report names the worktree and the result); the brief carried the new Constraints; Review B read `run/review/SCOPE-<nnn>.md` and its reply carried one of the three verdicts on the first launch; and one background launch with the Bash tool's `timeout` at the cap ran past thirty minutes, or none needed to and the report says so.

---

## 2026.10.11a

**Release A4 of the restructuring plan: the bridge's programs** (plan section 13.1 and the plan review's R17; the A1b, A2 and A3 reviews' follow-ups; the field findings of 2026-10-10 and 11). One regression test per defect, each failing on the old program.

**What changed**
- **Part 1, the increment checks.** `scope-check.py`: any heading ends the Scope (a bullet under `### Out of scope` is not scope); a rename shows its deleted path; the default base is the commit that first added the brief, so a builder's own commit is inside the diff and a brief fixed later never moves the base; the supervisor's record files changed only by records-only commits since the checkpoint are listed as records, not drift; `.github/` keeps its dot; an ellipsis cannot be verified; one bullet may name several paths, quoted or in backticks, prose after a path is dropped; a bracketed folder (`[id]`) is a folder; the bookkeeping files a builder must write (`docs/BUILDER_NOTES.md`, `docs/BOUNDARY_VIOLATIONS.md`, `run/`) are never drift. `plan-check.py`: a commit merges an increment only when its subject starts with the ID or IDs, its IDs stand in parentheses at the subject's end, a merge commit's branch starts with the ID, or a `Merges:` trailer names it (a subject that only mentions an ID, `docs: plan split TASK-003 out of TASK-004`, merges nothing); an unreadable `Depends on` or `Parent` value (`TASK-02`) fails instead of vanishing; each brief under `handoff/` is compared with its unmerged increment (`BRIEF`); a dated addendum file is read with the plan. `completion-check.py`: planned means an increment's `Satisfies:` field; a `built` requirement whose Evidence names no test file fails in plan mode too; `--only R-001,R-002` limits a run. `refactor-check.py` counts the test files of Go, Java, Kotlin, C# and Ruby. `bench-check.py` takes a metric's direction from its budget (`direction`, `max`, `min`) or a unit it names whole, never from its last letters; an unknown direction fails a budget and is noted, not judged, for a baseline-only metric. `lock-check.py` raises no alarm for a manifest changed outside its dependencies or for a folder with no lockfile in use. `diagram-check.py` reads the project's own shortcut paths from `tsconfig.json` or `jsconfig.json`, treats a tracked `build/` or `dist/` as source, and keeps a column named like a keyword (`key`, `index`, `check`).
- **Part 2, the guards and the gate.** `permission-guard.py`: inside a Workspace (a folder holding `docs/PROJECT_STATUS.md`), a chain of commands carrying a state-changing git or gh command, or a command wrapped in `cd`, is refused by rule 8 (a chain once built an increment on a merged branch); a pipe into a reader and a chain of reads pass; a commit or push with `--no-verify`, commit's `-n` or a `-c core.hooksPath=` override is refused except for the two snapshots the merge policy allows, the checkpoint commit and a builder's hand-off, whose message says so; `*agent.cmd*` and `*agent.ps1*` join the deny rules as the backstop. `review-guard.py verify` never rewinds a branch that another worktree holds: when the recorded branch is checked out elsewhere, the restore stops with GATE-INTEGRITY before any reset and names the worktree (the plan review's second pass, P3). `roster-check.py` compares Review B's family with the builder that built the change, read from the launcher's run log (`model` is now logged per run), and skips a profile whose reviewer is of that family. `invisible-check.py` (new) lists every zero-width, bidirectional-control or soft-hyphen character in the changed files by code point; `secret-sentinel` runs it first.
- **Part 3, install, conformance, the loop guard, session start, the reviewers.** `bridge-install.py` refuses, instead of going ahead without a word, a checkout whose main-as-merged state git cannot confirm (no origin, git failed); Python's cache folder is no uncommitted change; a release is not installed over one that has a file changed on this computer (the way back to it would refuse), checked before the kept copy is rotated so that the older way back survives the refusal, with `--anyway` for the maintainer's rehearsals; the kept-copy refusal names `--anyway`; the calibration's run sheet for a failed install check names the setup guide's three steps; the ruleset comment says to record the file that pins it. `conformance-check.py`'s adapters floor counts a provider's word only in a host or URL string or an upper-case key name, never in any string (reAngle's health and weights modules). **The loop guard's bound for a background agent is a timer command**, `wake-timer.py <seconds> "<the agent>"` (new), whose completion wakes the session: a scheduled wake-up does not fire while a background agent runs (KP-043, ISS-021 reproduced and proven on 2026-10-11); the refusal prints the timer command to copy and names leftover polling loops for `TaskStop` (KP-042). `session-start.py` says the calibration is started by the owner or by the maintainer session's message (rule 57). The reviewers' turn limits: `diff-reviewer`, `security-auditor` and `refactor-scout` 60, `design-auditor` 50 (a four-part stage review hit 40). KP-040 to KP-043 record the loop guard's field defects of 2026-10-10 and 11.
- **Part 4, the templates and the small texts.** The `.semgrep.yml` template holds the project's own rules in Semgrep's schema; the registry packs go on the gate command (R24: packs listed as strings under `rules:` are not valid). The design detector's pin floor is 3.3.0, the first with `projectRoots`. The Inno Setup template defines the bare GUID and escapes it in `[Setup]` only, so the `[Code]` "already installed" check builds the registry key the installer wrote (the `{{` escape inside `[Code]` doubled the braces), and `x64os` replaces `x64compatible`, which admitted Arm64 hosts; `installer-check.ps1` checks the installed executable's machine type (`-Arch`). The six subagents that run commands never leave a background command or a polling loop behind (KP-042). Step 8 says the post-review commit removes the review files and nothing else.

**Running projects must**
- *(building, changing)* Install, restart, `/calibrate-bridge`. Run `plan-check.py` once after calibration: a `BRIEF` or `DEPENDS` finding on a brief or an increment already in the plan is fixed in the plan or the brief, never worked around; an increment merged under an older subject form (`feat(x): … (TASK-100, R-027)` is read; a subject that only mentions an ID is not) is recorded by a records-only pull request whose description carries `Merges: TASK-104, TASK-106b` (the squash merge keeps the description as the body, and the trailer lands on `main`); a `DIRECTION UNKNOWN` in a benchmark budget gets its `max`, `min` or `direction`. Run `completion-check.py --mode plan` once too: a `NO EVIDENCE` row names in its Evidence the test files that carry its ID (or goes back to `planned`): reAngle has five (R-061, R-072, R-078, R-079, R-080), the video factory three, the TDP none; an `UNPLANNED` row, a `planned` requirement no increment's `Satisfies:` names, gets its entry in an increment or a deferral: the video factory has twenty-three, planned in documents its `docs/BUILD_PLAN*.md` glob does not cover (`PROVIDER_LAYER_PLAN.md`) or in no plan at all, to be planned or deferred when it resumes. A `built` row needs no plan increment any more, so the rows built by plans since removed pass.
- *(building, changing)* From the next increment on, the accept step runs `scope-check.py` once more before the accept commit, and the secret scan runs `invisible-check.py` first.
- *(building, changing)* A chained command the guard refuses is rewritten as separate calls, never worked around; a `--no-verify` the guard refuses was on a commit that is not the checkpoint (whose subject says `checkpoint` and names the increment before any parenthesis, without an accept, merge or release word) nor a builder's hand-off inside a worktree: an accept or increment commit runs the hook.
- *(building, changing, done)* A project with a committed Inno Setup script applies the template's `AppGuid`, `[Code]` and `x64os` lines at its next installer change, and its `.semgrep.yml` holds rules only, the packs on the gate command (the TDP already passes them there).
- *(building, changing)* A background agent waited on from now on gets its wake-timer, not a `CronCreate` wake-up; a one-shot wake-up still scheduled for a running agent is deleted (`CronDelete`) and replaced by the timer the loop guard's refusal prints. The In-flight line names the timer.

**If rolled back**
- Nothing to restore: the previous programs read the same files. A budget given a `direction` keeps it (the previous `bench-check.py` ignores the field). A running wake-timer ends on its own; the previous loop guard asks for a `CronCreate` wake-up again, which does not fire while the agent runs (KP-043), so a stop refused under the previous release is answered by running the agent's task in the foreground. Set `Bridge version:` to the installed version.

**Field acceptance on the trial project.** One increment walked through the loop with the new checks: the scope check's base line names the brief's commit, a planted scope case from part 1 (a bullet under `### Out of scope`, or prose after a path) is read correctly, the plan check compares the brief with its increment without a false `BRIEF` finding, the guard refuses one chained command carrying a commit and allows the checkpoint commit's `--no-verify`, and the run log of the increment's builder run carries its model. One background agent waited on with its wake-timer: the timer's completion wakes the session at the ceiling, and the loop guard allowed the stop with the timer running.

---

## 2026.10.10c

**A wake-up is scheduled on the computer's clock** (reAngle's field finding of 2026-10-10 on release 2026.10.10a, KP-039; the owner asked for it to be covered before the A3 install).

**What changed**
- **The loop guard's refusal does the arithmetic:** when a background agent waits with no wake-up at its ceiling, the refusal prints the computer's clock reading with its offset from UTC, the time the ceiling falls on that clock, the one-shot `CronCreate` schedule expression to copy, and any scheduled wake-up that is due after the ceiling.
- **Rule 43** says the schedule is read on the computer's clock: copied from the refusal, or computed from `date` read at that moment, never from a UTC stamp converted by an assumed offset, which put every wake-up of a session an hour past the ceiling on reAngle. The digest says "(computer's clock)"; N7 lost "before the gate" to pay for it (the rule's text is unchanged). A ceiling within two minutes is not scheduled: the refusal says to stop the agent now and run its task in the foreground.
- **KP-039** records the pitfall.

**Running projects must**
- *(building, changing)* Install, restart, `/calibrate-bridge`. At the next wake-up a supervisor schedules, copy the loop guard's expression or read the clock with `date`; a wake-up already scheduled by hand is checked against the clock once.

**If rolled back**
- Nothing to undo: the refusal loses its clock line and rule 43 its sentence. Set `Bridge version:` to the installed version.

**Field acceptance on the trial project.** A refusal of the loop guard for an unscheduled agent shows the clock reading and the expression, and the wake-up the supervisor then schedules fires at or before the ceiling.

---

## 2026.10.10b

**Release A3 of the restructuring plan: the design critique, the report cycle, the retrofit's conventions** (plan 8.6, 8.7 and 12), the maintainer's channel, and the first field fixes of 2026.10.10a.

**What changed**
- **The roster is resolved at intake** (plan 8.6): intake states the Cursor program as a prerequisite and writes and resolves `docs/ROSTER.json`, so a cross-family reviewer exists from the first phase; Phase 5 only re-resolves it. When no profile is usable, the design waits and the report says so.
- **Review B gets a design mode:** the design, its diagrams, the register, the record of what was accepted so far and the critic's lenses are committed to `run/review/DESIGN-<subject>-<round>.md`, and the reviewer reads it read-only with the workspace trusted, through the launcher, answering in the critic's grades with the counts; the test that forbade the read-only mode now applies to code reviews only.
- **Two critics before the gate, as peers, with a stop rule and two brakes:** a round is `plan-critic` and Review B's design mode on the same committed text, each given `docs/DESIGN_CRITIQUE.md` (three parts per subject: the findings accepted with their reasons, each critic's grades per round, the resolutions); another round follows only on a Blocking finding or a Should-fix not accepted with a reason; a critic that returned nothing of that kind drops out; a reversal of an earlier fix and whatever is still Blocking after four rounds (the owner's ceiling) go to a read-only resolution round; a dropped-out critic re-reads what changed, and the text leaving a fourth or a resolution round gets one confirming read by both. The same loop runs on the plan, on a change cycle's design revision and on a scoped revision; every gate presents the record as one of its separate decisions; the review files go with the gate's commit.
- **A material change after a gate is announced** (rule 58, the owner's decision of 2026-10-10): a change to an approved design that alters what the software does, its scope or its cost leads the next report as a one-line notice the owner can stop; what the escalation list makes the owner's is asked first, as always; every other change goes into the design's change section.
- **The maintainer's channel** (rule 57, the owner's decision of 2026-10-10): a message in the chat labelled as coming from the bridge's maintainer session, or from any other session, is bridge mechanics only, never a gate, scope, money or a key.
- **The report cycle** (plan 12): `evaluate-reports.py` reads each project's Issues and Feedback documents in their own shapes and the supervisor's notes in place, keeps `Reports/ledger.json` by project and entry ID with a fingerprint of the entry's text (an unnumbered entry is identified by its first lines, a renamed heading changes nothing), collects the unprocessed and updated entries, prints per document how many entries it found and how many lines lie outside any entry, records verdicts, seeds the ledger from the first evaluation's tables (one file per project, matched to that project only, the columns found by their headers), and extracts the owner's own typed messages and question-form answers since the last run (only records the app marks as the owner's typing, no compaction summary, no other session's message, each record once, a screenshot's text kept, every key-shaped token withheld); the `/evaluate-reports` command; `FB-nnn` IDs in the Feedback document; the Sunday task the owner creates once.
- **The retrofit's conventions** (plan 8.7): the as-built variant of the diagram specialist (the code's structure drawn, every dependency the design forbids left out and reported as a deviation), the minimum set a calibration compares against with `docs/diagrams/RETROFIT.md`, the known-deviations file `docs/diagrams/DEVIATIONS.md` the diagram check reads (a listed crossing passes as a note, anything new fails, a deviation still listed at project end fails), a `review:` item naming its reviewer (a note before project end, a failure at it), the diagram check's done mode in the project-end items, the owner approving Level 1 only.
- **Field fixes from reAngle's first day on 2026.10.10a:** the loop guard reads a task's start in the hook's live form (ISO or epoch), a scheduled wake-up by its next time or its cron expression, and a launched command under any type name, and records its input under `run/supervisor/loop-guard-input.json`; the in-flight line goes to `run/supervisor/in-flight.md` while a review runs on a snapshot; the project file's stage is compared by name; the launcher accepts `uv run` with its project options and the project's own `.venv` python for the test modules, and nothing else at a path.

**Running projects must**
- *(all phases)* Install, restart, `/calibrate-bridge` (step 0 writes the position down). A project past intake without a resolved roster gets one at calibration. Calibration compares the project's diagrams with the minimum set and writes `docs/diagrams/RETROFIT.md` for the kinds it lacks (reAngle, the video factory), each a retrofit item for the next stage close.
- *(all phases)* From the next reflection point on, Feedback entries carry `FB-nnn` IDs; a `review:` item in the diagram index names its reviewer before project end (the TDP has five that do not, reAngle three).
- *(design, planning, changing)* The next design, plan or design revision goes through the two-critic loop before its gate; `docs/DESIGN_CRITIQUE.md` starts empty.
- *(all phases)* A message labelled as the maintainer session's, or any other session's, is followed as mechanics only (rule 57). A background agent awaited during a review goes on `run/supervisor/in-flight.md` until `verify`.
- *(the owner, once)* After the maintainer has seeded the ledger from the first evaluation's tables (`evaluate-reports.py seed`, once; it says so), create the report cycle's Sunday task in the app's scheduled-tasks form (the setup guide's Step 12) and start its first run by hand.

**If rolled back**
- *(all phases)* `docs/DESIGN_CRITIQUE.md`, `run/review/DESIGN-*`, `docs/diagrams/RETROFIT.md` and `run/supervisor/loop-guard-input.json` may stay; the design critique returns to one critic. **Empty `docs/diagrams/DEVIATIONS.md` first, or fix its rows:** the previous diagram check does not read it and fails every listed crossing at step 4 of every increment. Delete the Sunday task or let it run: the previous release has no `/evaluate-reports`, so it ends in one line. Set `Bridge version:` to the installed version.

**Field acceptance on the trial project.** A design, a plan or a design revision walked through its gate is criticised by both critics before it, the loop stops when both return nothing above Consider or at four rounds, and the record is in the gate presentation; a material change after a gate, if one occurs, produces the one-line notice; the report cycle's first run, started by hand, raises nothing that the first evaluation of 2026-10-04 already settled; reAngle's calibration writes a retrofit plan for the kinds it lacks; one stop refused by the loop guard on 2026.10.10a's two defects is allowed under this release.

---

## 2026.10.10a

**Release A2 of the restructuring plan: background tasks, the remainder** (plan 10.3, second table). Every run the loop starts has a ceiling it learns from the project's own healthy runs, every background agent has a ceiling with a wake-up at it, the loop guard reads what is in flight from Claude Code itself, and a run that ends at its limit is recorded.

**What changed**
- **Ceilings learned per kind of run.** The launcher logs every run to `run/launcher/runs.jsonl` (kind, limit, seconds, exit; never the prompt). `--limit auto` takes the kind's default (builder 7,200 s, review 3,600 s, watch 3,600 s, test 1,800 s) or, once a healthy run of that kind is on record, one and a half times the longest healthy run, never below the default and never above twice it unless `docs/RUN_PARAMETERS.md` carries the owner's words on a line `Ceiling above twice: <kind> <seconds> (<their words>, <date>)`; an explicit limit above the cap is refused without them. The supervisor marks a run healthy after its increment merged (`bridge-run.py --healthy <run id>`; the id is the launch time on the first stderr line), and the run that raised a ceiling is named when the ceiling is chosen. A slow but healthy task is never ended before its ceiling. The builder and Review B now run with `--limit auto` and their kind named (`--kind builder`, `--kind review`).
- **What else runs through the launcher.** The test suites the supervisor awaits are accepted by name (`pytest`, `python -m pytest`, `python -m unittest`, `uv run pytest`, `npm test`, `npm run test*`, `pnpm test`, `yarn test`, `npx vitest`, `npx jest`, `npx playwright test`, `node --test`, `go test`, `cargo test`, `dotnet test`; `--kind test`), by the runner's bare name; everything else is still refused. `--key-file <path>` hands a file of `NAME=value` lines, outside the Workspace, to the child's environment only, names printed and values never, and never to a `cursor-agent` run (for the additions of releases E and G; the owner's rule of 2026-10-05). An option that would run another program or delete a folder is refused, and an `npx` tool is accepted only when the project has it installed.
- **A bound on background agents** (cases 4 and 5 of plan 10.1). A background agent counts as a wake source only under its ceiling, an hour unless the run parameters' optional `Agent ceiling:` line says more, and only while a wake-up is scheduled no later than that ceiling: the loop guard refuses a stop that waits on an agent without one, whatever else is scheduled; a supervisor that ends a turn to wait for one writes it on the status file's `In flight:` line and schedules a one-shot wake-up at the ceiling (`CronCreate`), because a hung agent never completes; at the wake-up or at any checkpoint an agent past its ceiling is stopped (`TaskStop`) and its task run again in the foreground. Every agent definition carries a turn limit (`maxTurns`), and every reviewer searches only inside the project's `Workspace/` or the worktree it is given (rule 43).
- **The loop guard asks Claude Code what is in flight.** The Stop hook's input lists the background tasks and the scheduled wake-ups; the guard counts a launched command only until its limit, a background agent only until its ceiling, a server never, and reads the session record only when that list is absent (KP-031, KP-033).
- **No servers in a builder's run:** every brief forbids starting a server, a watcher or a daemon that outlives a test; tests use their framework's own start and stop (plan 10.3, case 3).
- **The project file** (the owner's requirement of 2026-10-10). Every project carries `project.json` at its Workspace root: `name`, `purpose`, `kind` (`private` or `commercial`; private is the default, asked once at intake as its own question), `version` (the product's) and `state` (`phase`, `stage`, `bridge`, `updated`). The supervisor writes it at intake and brings it up to date at every reflection point; the conformance check reports a missing one and notes a stale one.
- **Every run ended at its limit is recorded:** an Issues entry with what the inspection found, what was kept, the kind's ceiling and the longest healthy run on record, so a kind that keeps reaching its ceiling is diagnosed rather than retried forever (step 3b).
- Tests: the launcher's kinds, log, learned limit and cap, the owner's lifted cap, the healthy mark, the key file inside and outside the Workspace, the test suites by name; the loop guard on the hook's list (a running builder, one past its limit, a server, a completed task, an agent under and past its ceiling, a wake-up due and past, the empty list, the transcript fallback, the raised agent ceiling); every agent's turn limit and every searcher's folder rule; the literal commands with their kind.

**Running projects must**
- *(all phases)* Install with the setup guide's three steps, restart the app, run `/calibrate-bridge` (its step 0 has the supervisor write its position down first). The run log starts empty: the first runs after the install use the defaults.
- *(all phases)* Calibration writes `project.json` from the status file and the inventory (kind `private` for the three running projects); from then on it is brought up to date at every reflection point.
- *(building, changing)* From the next increment on, delegate and review with the commands as the instructions now spell them (`--limit auto --kind builder`, `--limit auto --kind review`); mark the builder's and Review B's runs healthy after each merge; await a test suite through the launcher (`--limit auto --kind test`, `# wake`) and a benchmark or an unknown runner directly in the background with `# wake`; write a background agent on `In flight:` with its ceiling and schedule the wake-up before ending the turn to wait for it; from the next brief on, the brief carries the no-server rule.

**If rolled back**
- *(all phases)* `run/launcher/runs.jsonl` and `project.json` may stay (the previous release ignores both). Delete any `Agent ceiling:` or `Ceiling above twice:` line from `docs/RUN_PARAMETERS.md` (the previous release does not read them) and any scheduled wake-up (`CronDelete`). Set `Bridge version:` to the installed version.

**Field acceptance on the trial project.** Calibration writes `project.json` and the conformance check reports it OK; one builder run and one Review B run are logged with their kind; after the first merge both are marked healthy and the next `--limit auto` run names the run it measured (the default stays until a healthy run needs more than two thirds of it); the loop guard allows a stop on a running builder read from the hook's list and refuses one once nothing is in flight; one background agent is written on `In flight:` with a wake-up scheduled at its ceiling (the agent may finish first: then the wake-up fires and finds nothing to stop, which the report says).

---

## 2026.10.06b

**Release A1b of the restructuring plan: the owner's authority, money and data.** The rules that keep what is the owner's in the owner's hands: what they are told and asked, which gates are theirs, how their money and their data are protected; a worktree teardown that never forces; and the pause that writes the project's place down.

**What changed**
- **What the owner is told and asked** (plan 8.8). A summary of any verification states its counts (rule 49). Every run sheet comes from one template that opens with `Purpose:`, `End state:` and `Terminal:` with how to open it; the loop guard sends back a turn whose last message holds a shell block and no line that begins `Terminal:` (rule 27; indented and `~~~` fences and PowerShell, batch and zsh blocks count; a numbered or bulleted `Terminal:` line and `Terminal (Git Bash):` count as the line; a command the supervisor ran itself goes in a plain block, which rule 27 and the skill now say; the hook reads its own copy of the final message, the transcript is the fallback). Each run parameter is asked as a question of its own in the app's question form (rule 29). The design gate presents its decisions separately: the behaviour, the requirements register, the Level 1 diagrams, and each item that costs money or needs an account (Phase 2). The technical escalations left the conventions: a benchmark's tolerance is the supervisor's to set with its measurement, and one dependency rule (rule 56) replaces three: the gate admits, the supervisor adds and records, the owner is asked only for a consequence they bear; no text puts a licence to the owner (their instruction of 2026-10-01), and an inherited rules file or the installer technology is the supervisor's call, recorded with its reason.
- **The owner's authority** (plan 13.1). Gates are the owner's and may be handed to the supervisor per named change, in the owner's recorded words, never for money, scope, keys or an irreversible step; each decision taken under them leads the next report (rule 50; the status file's `Delegated gates:` line). A product records who decided, never an agent as a person, and a per-item approval goes to a judge of another model family (rule 51). At every stage close, after the refactoring pass, both reviewers read the stage's whole change once on a `stage/<name>` branch with step 8's own protections (eight numbered steps: snapshot, Review A, Review B through the launcher, verify, the branch deleted), and the stage's demonstration runs live, named by a `Demonstration:` line under each stage heading of the build plan (`plan-check.py` notes a stage without one); from the first increment that makes the product startable, every stage close starts it. `review-guard.py verify` writes a verified mark when it prints OK (the snapshot's hash, the launch time and the exit code of the Review B run, read from `run/review/REVIEW-<nnn>.err`, whose last line the launcher now writes as `bridge-run: exit <code>`; `snapshot` and `verify` remove an older mark first), and `premerge` refuses a snapshot without that mark, a mark of another snapshot, a launch before the snapshot or a run that did not end with exit 0, so a merge that skipped the cross-family review, or whose review failed at once, has no way through, a records-only pull request included (what the mark proves: a Review B launched after the last snapshot that ended normally, and a clean verify after it); `premerge` then writes a record of the head it approved under the repository's git folder, and the `permission-guard` hook refuses a `gh pr merge` whose `--match-head-commit <sha>` has no such record, a merge without the sha, a `gh api` merge or merge-queue mutation or a query read from a file, and any of these behind `bash -c`, `bash -lc`, `cmd /c`, `powershell -Command` (quoted or not), a single `&`, the PowerShell call operator or the dot operator, `{`, `if`, `xargs`, `nice`, `timeout` and their values, `find -exec`, a `gh pr -R <repo> merge`, `powershell` without `-Command` or with `-com`, `-XPUT`, a git or gh alias or an abbreviated `--forc`; an encoded PowerShell command and a GraphQL query built by a command substitution are refused unread (the policy's armed form carries the sha too; `--help` passes unless it is a flag's value; a here-document's body is data unless a shell reads it). A value the owner chose is fixed in a test (rule 52; a constraint in every brief).
- **The owner's money.** Configuration asks the owner for a spending limit at every provider that can spend, recorded in the inventory's Resources row (`limit $20/month, set <date>`, or `no spend possible`); the conformance check reports every key, account or provider row that can charge and records no amount near the word limit (`spending limit not set yet` is not a limit; `spending limit set to $20/month` is), with its count; a setting and the row that records a limit are not keys; a local service's login (every name in the cell is looked at), the product's own token, a per-instance value, a test-only value, a store, model files, a registration and a `no spend possible` row are not reported. A key seen in the chat is exposed: the next report's first line asks for its replacement into the key file or the product's encrypted store, with a run sheet (rule 53); when several rules claim the first line, rule 12 gives the order (the owner's decision, the exposed key, a gate decision under rule 50, the model switch).
- **The owner's data.** N1 gains its conditions 6 to 8 (plan 8.1): starting a background process changes no data it does not own and migrates no live data outside a release; it never runs unreleased code against live data; it spends nothing unless asked. Development data stays apart from live data (rule 55): a design rule, a constraint in every brief, and two conformance floors, `Development data kept apart` (the inventory's `Development data:` decision, bold or backticked as the design shows it; the packager copies it into the brief's Context) and `Adapters tested against recorded replies`: the providers are the inventory's chargeable rows, one word each (the first segment of a key's name, or the provider's own name; a setting or the record of a limit is no provider), an adapter is a tracked source file of the project that uses a client library (or a JavaScript `fetch` of an absolute URL that is not the product's own) and names the provider as a whole word in a string of its code, never in a docstring or a comment, and the evidence is a cassette or fixture file the adapter's own test loads, vcr, respx, responses.activate, nock or msw in that test, or a test that names cassettes in a repository that tracks a cassettes folder; a mock transport fed by hand, and the words "contract" or "recorded" alone, are not evidence.
- **Nothing skipped as "gate passed" that is a test:** a calibration item that adds a test or a recorded reply is applied in every phase.
- **The safety of worktrees** (plan 8.5). `worktree-teardown.py` is the one way to remove a worktree: it refuses while a junction or symbolic link is inside, listing each with its target, never forces, and names a locked worktree as such; the guard hook refuses every `git worktree remove`, forced or not, because Git for Windows follows a gitignored junction in an ordinary removal as in a forced one (observed on Git 2.53 on 2026-10-06; a test records what git does and skips where a git does otherwise), and the plain removal's allow rule is retired (rule 19; KP-011 and KP-023 restated). The teardown program looks for links in any folder it is given, a leftover that git no longer lists included, and clears a plain delete only for such a leftover, never for a folder that holds a live worktree.
- A new project's `.gitignore` carries `run/` (the launcher's output, the review files, the supervisor's working files); the conformance check notes a project without it.
- **A pause and a calibration keep the project's place** (the owner's proposal of 2026-10-05, rule 54). A pause on the owner's word begins by writing the position down; the supervisor's working files live in `run/supervisor/`, listed on the status file's `Working files:` line, never in a session's temporary folder, which changes with every restart; `/calibrate-bridge` checks that first (its step 0) and ends by naming the next action; no path of this computer enters a commit, the secret scan reports one as it reports a key.
- The agent's home folder (KP-038) gets the empty skeleton of a profile, so a Windows program handed a known folder that does not exist no longer falls back to the builder's checkout.
- Tests: the guard's new refusals, the pre-merge record, the wrapped and aliased spellings, and what stays allowed; every command the bridge's texts instruct passes the guard; the loop guard's run-sheet check in every phase and on the hook's own copy of the message; the teardown program on clean, linked, locked and dirty worktrees, and why the plain removal is refused; the three conformance floors on false and true alarms; the profile skeleton; the digest names every rule; no text puts a dependency or a licence question to the owner.

**Running projects must**
- *(all phases)* Install with the setup guide's three steps, restart the app, run `/calibrate-bridge`; its step 0 has the supervisor write its position down first.
- *(all phases, record-keeping)* Add `Working files:` and `Delegated gates:` to the status file. In the inventory, give every key or account row its spending limit (asked of the owner as a run sheet at the next reflection point; `no spend possible` where the account cannot be charged) and add a `Development data:` Decisions row from the design, or `Development data: none, the product keeps no data of the owner's`. Run the conformance check; each new `MISSING` floor is a configuration item of the next stage.
- *(building, changing)* From the next brief on, the brief carries the development-data constraint and marks the owner's values; from the next stage close on, both reviewers read the stage's whole change and the demonstration runs live; worktrees are torn down with `worktree-teardown.py`, never with `git worktree remove`; every merge carries the `--match-head-commit <sha>` that `premerge` printed, after it printed OK, and every pull request, a records-only one included, takes the review round first (snapshot, Review B through the launcher, `verify`), because `premerge` refuses a snapshot without its verified mark. Add `run/` to `.gitignore`. Give every stage of the build plan not yet closed a `Demonstration:` line (calibration does it). Reconcile any private note that reads "proceed autonomously" as a standing permission with rule 50: a general "proceed autonomously" hands over nothing; only the owner's recorded words for a named change do.
- *(design)* A project at the design gate presents it as separate decisions and writes the development-data and who-decided rules into the design.

**If rolled back**
- *(all phases)* The status file's two new lines and the inventory's additions may stay; nothing else to restore. Set `Bridge version:` to the installed version. A delegation written on `Delegated gates:` lapses with the rollback: no rule of the previous release gives the line a meaning, so the owner's gates return to the owner until this release is installed again.

**Field acceptance on the trial project.** The loop guard sends back one run sheet that names no terminal (the supervisor corrects it in the same turn); a `gh pr merge` without the sha is refused and the merge goes through with it after `premerge` printed OK; `/calibrate-bridge` writes the position down before re-reading; the conformance check reports the new floors on the project and the supervisor schedules them as configuration items. Three clauses need a session, not a test, and are watched for: a supervisor paused in the middle of a review round (position written down) continues after an app restart from the project's files alone, its next report naming the round and the review it resumes; at the next design gate or design revision the decisions arrive separately, each as a question in the question form; at the next stage close both reviewers read the stage's whole change on the `stage/<name>` branch and the demonstration runs live, both named in the stage-close report.

---

## 2026.10.06a

**Urgent fix from release A1a's trial (reAngle ISS-013): the builder and Review B get their shell back.** Since 2026-10-04 cursor-agent on the owner's computer imported the bridge's own Claude Code hook from `~/.claude/settings.json` and, under Git Bash, ran it in a way that denied every tool call while reporting success; builders delivered code they had never run (KP-038).

**What changed**
- **Every builder and reviewer run gets a home folder of its own** (`%USERPROFILE%\.cursor-bridge\agent-home\`), holding a link `.cursor` to the owner's real `~/.cursor` and nothing else. cursor-agent finds no `~/.claude/settings.json` to import hooks from (Cursor's documented default, with no switch in the CLI), and the owner's `.ssh`, `.aws`, `.docker` and other stores are no longer found by default (not out of reach: the run is the owner's account, and the real controls stay the withheld tokens, the empty `gh` folder and git without a credential helper). git keeps the owner's global configuration through `GIT_CONFIG_GLOBAL`, and the caches the builders' tools read by default are passed through by their own variables (`HF_HUB_CACHE`, `TORCH_HOME`, `PUPPETEER_CACHE_DIR`; never `HF_HOME` or `XDG_CACHE_HOME`, which would show the owner's token file again), so a test that loads a model finds the 311 GB of models already on the computer and does not download them anew; a gated model still needs the project's own key handling, as 2026.10.04e intended. The shim (`cursor-agent.shim`) and the Python recipe (`bridge_env.stripped_env`) apply one rule alike: the link exists, is a link and leads to the real `~/.cursor`, or the run is refused with exit 125 instead of started into silent denial. `bridge-install.py` prepares the folder, repairs a link that leads nowhere or elsewhere (by removing the link itself, never through it; a plain folder in its place is never removed), and runs a write-and-rename through a scratch link beside it, the operation cursor-agent's state writes need and that fails under some folders on the owner's computer; `bridge-check.py` verifies both.
- **The guard hook refuses the agent started around the shim** (`agent.cmd`, `agent.ps1`, `cursor-agent.cmd`, `cursor-agent.ps1`, `cursor-agent.exe`, and a bare `agent` without a path or from the CLI's own folder; also as the program a shell wrapper names after `/c`, `-c`, `-Command` or `-File`, though not inside a quoted string, which the guard has never read), which would run it with the owner's real home and identity. The agent is started as `cursor-agent`, or through `bridge-run.py`. A project's own `./agent` is not refused.
- **The conformance check reports Claude Code hooks or plugins in a project's own `.claude/settings*.json`** (the root and `Workspace/`): the relocation does not cover them, and cursor-agent imports them the same way.
- Tests: the two recipes agree on the home folder and the caches as on everything else, and refuse alike a plain folder, a link that leads nowhere and one that leads elsewhere; the installer repairs the last two and never the first; the launcher's child runs in the home; the check reports a missing or damaged link; the guard's refusals; the conformance floor; no test touches the owner's real home.

**Running projects must**
- *(all phases)* Install with the three steps of the setup guide's Step 3, restart the app, run `/calibrate-bridge`. Nothing in the project's files changes.
- *(building, changing)* Every builder run and every Review B since 2026-10-04 ran without a working shell: builders delivered unrun code and the supervisor ran the checks (reAngle's record). From the next delegation on, the builder runs its own tests again, and the acceptance criteria the supervisor had been verifying by hand go back to the builder; Review B executes again where its mandate says so. A builder's first test run that needs a tool's cache other than the three passed through (for instance `~/.cache/hyperframes`) downloads it again, once.
- *(all phases, record-keeping)* At the next reflection point, mark every Review B verdict given between 2026-10-04 and the install of this release as "without execution" in the project's records (`CHANGES.md` or the status file's notes): CI gated every merge, so nothing unchecked reached `main`, but the record must not claim an execution that did not happen.

**If rolled back**
- *(all phases)* Nothing to restore in a project's files. The builder's shell is blocked again from the next delegation on (KP-038).

**Field acceptance on the trial project.** The next builder run's note shows that it ran its commands (tests, lint, the mutation driver), the next Review B output holds no `Hook blocked`, and the supervisor's probe of 2026-10-06 (`PROBE-059b`) passes when run again.

---

## 2026.10.05a

**Release A1a of the restructuring plan: the bridge's own house.** Its sources leave the folder where a session working on the bridge loaded them half-edited; a release can be taken back; four contradictions in the bridge's own text are removed.

**What changed**
- **The governance sources moved from `.claude/` to `bridge/` in the bridge's repository** (plan review R8, KP-037). Claude Code loads agents, commands, settings and hooks from a project's `.claude` folder, prefers a project's agents over the installed ones and reloads them while a session runs, so a branch that edited a reviewer changed the reviewer of that branch. On an installed machine nothing moves: the install program still copies `commands/`, `agents/`, `skills/` and `cursor-bridge/` into `~/.claude`. **The install command's path changes** to `<the bridge's repository>/bridge/cursor-bridge/bridge-install.py`. The repository's generated `settings.json`, which existed to give sessions there the bridge's hooks, is gone.
- **A release can be taken back** (`python <the bridge's repository>/bridge/cursor-bridge/bridge-install.py --rollback`). An install over another version first keeps that version's own files under `~/.claude/cursor-bridge-previous/<version>/` (one previous release is kept) and compares the kept copy with that release's fingerprints: a file that had been changed on the computer is named, because the way back refuses a copy that is not the release as shipped. A rollback puts the kept release back, keeps every key of the owner's, restores the previous shim, and writes the newer release's **If rolled back** items to `cursor-bridge/ROLLED-BACK.md`, which `/calibrate-bridge` applies in a project whose recorded version is newer than the installed one. The kept copy is removed only when the install check has passed on the result. **The rollback is run with the installer of a release folder, never with the installed copy,** which refuses: the installed copy is replaced during the rollback, and one that was interrupted could not be finished with it when the restored installer does not know the command (2026.10.04e's does not). The bridge is installed once per computer, so both an install and a rollback reach every project at once; the release flow in the restructuring plan (section 15) pauses the projects for that reason.
- **Installing and taking back are one replacement,** so every install exercises the way back. Either way the files, the allow and deny rules and the hooks that only the replaced release owned are removed (an install used to add and never remove, except the entries on the `retired` list). The order is fixed so that `settings.json` never names a hook whose program is not there, also when a run is interrupted and repeated: a hook that runs a missing program ends with exit status 2, which Claude Code reads as "block", for every matching tool call or the end of every turn, in every session on the computer. A program that some other hook in `settings.json` still runs (one the owner wrote) is not removed. `settings.json` is written whole or not at all, and is read again immediately before each write, because Claude Code writes the same file. A kept copy is never written twice (a repeated run after an interruption would otherwise save a mixture of two releases as "the previous one"). A file that cannot be written and a `settings.json` of an unexpected shape end in a sentence, not a traceback; the first can be repeated, the second is refused before anything changes. The install check reports a hook that runs a `cursor-bridge` program which is not installed. One limit: an entry is recognised by its text, so an allow or deny rule the owner wrote in the very words of a rule the leaving release owned goes with it (the removal is listed, and the backup holds it).
- **Only a release is installed.** The install refuses a folder whose files do not equal its own stamp or that holds a file the stamp does not list, and a checkout of the bridge's repository that is not `main` as merged (another branch, commits that were never merged, uncommitted changes): the install check passes on any stamped branch, so nothing else told a merged release from one under review. `--anyway` installs a checkout as it is, for the maintainer's rehearsals. `bridge-check.py --sources`, which CI runs, fails on an unlisted file as well, and `tools/make-manifest.py` writes nothing for an argument it does not know.
- **Changelog entries gain a third part, "If rolled back",** stating what a project that calibrated to the release must restore when it is taken back.
- **What a builder may write is said once** (R17). The delegate command read "do not modify … anything under docs/", while every brief told the builder to append to `docs/BUILDER_NOTES.md` and the delivery conventions required `docs/cli-reference.json` regenerated in the same change. The command now ends that clause with "unless the Scope section names the file"; every brief's Scope lists `docs/BUILDER_NOTES.md`, the fix and the refactoring briefs included, and `docs/cli-reference.json` with its rendered `docs/CLI_REFERENCE.md` when a command changes; the brief's Out of scope says the same.
- **Review A answers in the merge policy's words** (R17). `diff-reviewer` returned PASS, PASS WITH FINDINGS or FAIL while the policy waited for APPROVE, REJECT or ESCALATE-INTENT, which left a question of intent no channel. It now returns those three; an approval may still carry findings. The auditors keep PASS and FAIL as inputs to it. Six passages that still called a review's outcome a `FAIL` (the instructions, the diagram conventions, the glossary, the root-cause skill, the merge policy) say `REJECT`.
- **Five run parameters everywhere** (R17): rule 29 and the status template named three of the five.
- **Pinned versions and configured modes are recorded in the inventory's Resources** (R17), no longer in the status file, which is capped at 120 lines and had no place for them: 20 places in the conventions and six in the supervisor's instructions now say so. A row names the file that holds the pin, with a short version beside it; what no file holds (a level, a tier, a mode) is written there itself. **A commit pin is recorded by the file that pins it, never by its 40-character value:** the inventory check reads a long token as a key, and now says what to do when the token is a commit fingerprint.
- **The session-start hook names the installed release.** It labelled the digest with the version the project's status file records, which is wrong between an install or a rollback and the project's next calibration; it now names the release it belongs to, and tells a project whose status file records another version that it is not calibrated to the installed bridge.
- Tests: the rollback and the replacement (36, among them an install stopped after the n-th copied file in both directions and a rollback finished after the restored installer had replaced the newer one), the install check and the stamp (13), the text (9), and the whole suite from the new folder.

**Running projects must**
- *(all phases)* Install with `python <the bridge's repository>/bridge/cursor-bridge/bridge-install.py` (the repository on `main` as merged; the installer refuses anything else), restart the app, run `/calibrate-bridge`. This is the first release installed under the trial rule: every project is paused before the install, one is calibrated and resumed, and the others resume on the owner's word.
- *(building, changing)* From the next brief on, the delegate command is the one step 3 shows and every brief's Scope lists `docs/BUILDER_NOTES.md`; a brief already delegated finishes under its own command. Review A's verdict reads APPROVE, REJECT or ESCALATE-INTENT from the next review on; a verdict already recorded as PASS or FAIL stands.
- *(all phases, record-keeping)* At the next reflection point, move the pinned versions and configured modes recorded in `docs/PROJECT_STATUS.md` (tool versions, scanner rulesets, the observability tier; a pinned action by the workflow file that pins it, never its 40-character value) to `docs/INVENTORY.md` → Resources, and remove them from the status file.

**If rolled back**
- *(all phases)* Nothing in a project's files has to be restored: this release changes no record's format. Briefs written under it stay valid, and their next delegation uses the previous release's command. Records moved to the inventory stay there. Set `Bridge version:` to the installed version. The release this one is taken back to, 2026.10.04e, has a calibration command that does not know a rollback and does not read this note; run `/calibrate-bridge` all the same, because it re-reads the governing text of the release now installed, finds no newer entry and records the installed version. Only if its report does not show `Bridge version: 2026.10.04e` does the owner tell the supervisor "the bridge was taken back to 2026.10.04e; set the `Bridge version:` line to it".

**Field acceptance on the trial project.** With every project paused: the release is installed, taken back with `--rollback`, and installed again, each with the repository's installer, and the install check passes each time. Then the trial project calibrates, and one increment goes through the loop: its brief's Scope names `docs/BUILDER_NOTES.md`, the scope check passes with the builder's note written, and Review A answers with one of the three verdict words.

---

## 2026.10.04e

**Account keys are withheld from builder and reviewer runs, and the advice of 2026.10.04c is corrected.** Found by the first evaluation of the projects' reports, in two projects independently.

**What changed**
- **The advice was wrong.** 2026.10.04c told projects to move paid keys out of `Workspace/.env` "to the user's environment". A variable in the Windows user environment is handed to every program the owner starts, and the launcher withheld only the GitHub variables, so the keys would have reached every builder run and every Review B run, and Review B executes code. The TDP's supervisor saw this and chose a key file outside the Workspace; reAngle's wrote its run sheet as instructed.
- **The launcher and the shim withhold every key-like variable** (`bridge_env.stripped_env`, `cursor-agent.shim`, one test of the name in both): a whole-word `TOKEN` or `SECRET`, `PASSWORD`, `PASSWD`, `CREDENTIAL`, an API, access or private key, or a name ending in `_KEY`. Cursor's own variables (`CURSOR_*`) are kept. A test runs both recipes on the same sample and requires the same answer.
- **No secret through an environment variable the owner sets** (the owner, 2026-10-05). Founding rule N2 itself said keys live in "the owner's environment", and the inventory template offered "user env var"; both now name a key file outside the Workspace, the product's encrypted store or the system's credential store. A store's unlock passphrase counts as a key (the video factory's `SFVF_SECRETS_PASSPHRASE` is given through a variable today), and the launcher's filter withholds it. The run-sheet guidance forbids asking the owner to set a secret as a variable. The conformance check gains the floor: an inventory row that says a secret arrives through an environment variable is `MISSING`.
- **The conformance check** advises a key file outside the Workspace (for example under `%APPDATA%\<product>\`) or the product's encrypted store, and never the user environment; it notes key-like variable names found in the session's own environment. KP-032 records it.

**Running projects must**
- *(all phases)* Install with `python <release .claude folder>/cursor-bridge/bridge-install.py`, restart the app, run `/calibrate-bridge`. **Where a run sheet of 2026.10.04c asked the owner to put account keys into the Windows user environment (reAngle: `MODAL_TOKEN_ID`, `MODAL_TOKEN_SECRET`, `HF_TOKEN`), replace it:** the keys go into a key file outside the Workspace that the product, or the supervisor's own paid scripts, read; any of them already set in the user environment are removed from it by a run sheet. A project's tests that need a local service's password read it from the project's `.env`, not from the environment: the builder no longer inherits key-like variables.
- *(all phases)* **A product that takes a secret or an unlock passphrase from an environment variable the owner sets** (the conformance check names them from the inventory: the video factory's store passphrase; the TDP's and reAngle's account keys where the product reads them from its process environment) gets one increment that makes the product read it from a key file outside the Workspace or the system's credential store, and its run sheets and User Manual change with it. Until that increment has merged, the owner is asked for no new variable; a paid run the supervisor itself starts loads the key file into that one process only.

---

## 2026.10.04d

**The models each role runs on, and Review A off a legacy model.** The owner's decision of 2026-10-04 after the verified fact that Fable is not a second usage pool (it draws from the weekly limit, at most half of it, faster — KP-036).

**What changed**
- **Review A was pinned to `claude-opus-4-8` since 2026-09-05** — a legacy model two generations behind the supervisor — in four reviewer definitions and the roster template. Now: `diff-reviewer`, `security-auditor`, `design-auditor`, `refactor-scout` on `claude-opus-5-5` at `effort: high`; `spec-packager` and `diagram-specialist` on `claude-opus-5-5`; `plan-critic` on `claude-fable-5-1`; `test-runner`, `secret-sentinel`, `cursor-configurator` on `claude-sonnet-5-5`. No definition inherits the session's model any more. The roster template's `review_a` is `claude-opus-5-5`.
- **Rule 48: the session's model follows the phase** — Fable 5.1 through intake, design, interface and plan and in any design revision; Opus 5.5 from configuration on. The switch is the owner's by hand (the app refuses a session re-pricing itself), so the report that closes the stage before a switch names it right after the decision it leads with: the plan gate, the arrival of a change request, the design revision's gate. A supervisor whose system prompt names another model than the phase's leads its next report with the switch. The calibration report now carries a `Session model for this phase` line.
- Tests: every agent definition names a current model, the reviewers carry high effort, the roster template matches `diff-reviewer`, and no legacy id remains in the tree.

**Running projects must**
- *(all phases)* Install with `python <release .claude folder>/cursor-bridge/bridge-install.py`, restart the app, run `/calibrate-bridge`: the calibration sets `review_a` in `docs/ROSTER.json` to `claude-opus-5-5` and its report tells the owner the session model for the project's phase (Opus 5.5 for every project in build or done; Fable 5.1 only while a design revision is open). Subagents spawned before the restart ran on the old definitions; their results stand.

---

## 2026.10.04c

**Release 0b of the restructuring plan: the rules that survive a compaction, the founding rules in the core, the conformance check, the guides corrected — and, from its own pre-install review, the checkpoint guard for a reviewer with execution.** Built on a branch and brought in through the bridge's own pull-request gate: `main` is now protected (both CI jobs required, administrators included, no force-push).

**What changed**
- **KP-035: the core survives a compaction.** `supervisor.md` now opens with a **digest** of the core (the founding rules, the loop with its literal commands, the escalation list, the reporting rules, every standing rule in one line; inside the 20,000 characters a compaction keeps), and the new `session-start.py` hook (SessionStart, matchers `compact`, `resume` and `fork`) re-injects it after every compaction, resume and fork together with the project's phase and the exact sections of `supervisor.md` to re-read before the next action, with their line ranges, and whether to continue or to wait for the owner. Claude Code caps a hook's output at 10,000 characters and swaps a longer one for a file path, and the pre-install review measured the single-run form being cut on all three projects (the cut part was the pointers): the hook is registered **twice** for the event, one run printing the pointers and one the digest. Headings inside code blocks no longer end a section early; `Phase: configuration` is mapped; the message tells a session that is not the supervisor to ignore it and a forked session not to continue the loop (it fails open on purpose: a gate on the transcript silenced two live supervisor sessions in the review's second pass). Measured cause: a compaction re-attached exactly 20,000 of the file's 150,000 characters, and the record shows rule-breaking within minutes of several compactions. Tests run the hook for every phase the status template allows, on a status file at the template's limits, and check that the digest names every rule, carries the literal delegate command and the merge-authority check. Rule 28 says to read the re-injected sections, never to work from memory of the rules.
- **The founding rules N1–N9 are stated in the core**, in a section of their own after the digest, each with what enforces it, restated as the restructuring plan decided: N1 (files are the truth, programs one-shot, a background process only under five conditions) and N6 (the verified gate, the owner choosing who merges). The Project Summary's N1, N5 and N6 are aligned; the merge policy no longer says "Team plan".
- **Review B keeps execution, on a guarded checkpoint.** 2026.10.04b had moved the cross-family reviewer to the CLI's read-only mode; the TDP's supervisor reported that this removed the reviewer's ability to run the tests and build its own reproductions, where its strongest findings had come from, and the owner decided to keep that ability. Review B runs with `--force` again, through the launcher (identity withheld, one-hour limit), **in the background**, on a committed checkpoint that the new **`review-guard.py`** snapshots before the launch (`snapshot <nnn>`: HEAD, the branch, every ref, the stash list, `.git/config`, the hooks folder, the ignored entries; it refuses a dirty tree) and verifies after it (`verify <nnn>`: the configuration is read as a file before any git command runs; the tree is put back with `git reset --hard` and `git clean -fd`; a commit, a moved HEAD, a new ref or stash, a changed configuration, hook file or `.env` is `GATE-INTEGRITY`), and `premerge <nnn> <pr>` proves the head about to merge descends from the reviewed one, differs only under `run/review/`, and is the pull request's head, merged with `--match-head-commit`. The pre-install review showed that `git status` plus `git checkout -- .` saw none of these; its second pass showed the guard's own `git checkout` running a hook planted in `.githooks`, so every git command of the guard runs with the repository's hooks and file monitor off and the active hooks folder is hashed before any git command; local refs are put back; records the project gitignores are protected; the launcher's `.err` file is kept; the snapshot's hash is printed at both ends. The supervisor writes nothing to the checkout while the review runs; the merge policy says what the guard covers and what it does not. The activity check stays.
- **The project conformance check** (`conformance-check.py`, review R4): compares a project's configuration with the floors the bridge requires and prints `OK`/`MISSING`/`NOTE` per floor: scanners as workflow **steps** (a step guarded by `if:` is `MISSING`, it is skipped silently; Semgrep must run the bridge rules or the Pro engine, public rulesets alone are not the floor; an unpinned scanner version is a note), actions pinned by commit, the required status check and the repository's visibility read through `gh` (GET only; `--offline` skips), the boundary, windowless and secure-coding rules, lockfiles (a root `requirements.txt` needs a transitive lock; an editable sub-project is covered by it), the records (a design under other names is a note naming them), the diagram index, the command reference checked in CI or by a test, account keys in `.env`, `.env.*` and `<folder>/.env` within the builder's reach (local service passwords and the product's own tokens are notes), a record the project gitignores (missing: the records are versioned), a scanner step that guards itself in its script (a note), the private memory notes by name, the recorded bridge version. It accepts the project root, where sessions start. It runs at step 1b of `/calibrate-bridge` and first at every reflection point; every `MISSING` is a calibration item. Run on the three projects today: the video factory lacks every scanner, the detector, the secure-coding rule, a transitive lock and the diagram index, and its repository is public; the TDP's Socket step is guarded and its Semgrep runs public rulesets only, and its paid keys sit in `.env`; reAngle's account tokens sit in `.env`. Values are never read.
- **`/calibrate-bridge` step 2b reviews the private memory notes** the check lists: a note that restates a bridge rule or holds project state is deleted or reduced to a pointer (rule 41); the TDP's notes still described a retired builder as current.
- **The setup guide** corrects the worktree statement (a bridge project is opened at its root, which is not a repository, so no worktree is made), the auto-merge lines (under `Merge authority: supervisor` the supervisor completing the merge is the design), and asks for one manual `/compact` after this install to see the hook's message live.

**Running projects must**
- *(all phases)* Install with `python <release .claude folder>/cursor-bridge/bridge-install.py`, restart the app, run `/calibrate-bridge`: it runs the conformance check at step 1b (every `MISSING` floor becomes a calibration item for the next stage) and the memory-note review at step 2b. **Before the first Review B with execution on a project whose `.env` holds account keys** (the check names them: the TDP's `ANTHROPIC_API_KEY`, `OPENROUTER_API_KEY`, `AZURE_DI_API_KEY`; reAngle's `MODAL_TOKEN_*`, `HF_TOKEN`), the keys leave `.env` — a run sheet to the owner to set them in the user's environment, and the increment that makes the product read them from there, delegated first — because a reproduction can spend on those accounts.
- *(building, changing)* From the next increment, Review B runs as step 8 now says: `review-guard.py snapshot`, the launcher in the background, `review-guard.py verify`, the activity check, `review-guard.py premerge`. A review already running finishes under the old step.

---

## 2026.10.04b

**The fixes from the pre-install review of 2026.10.04a** (`Claude-Cursor Bridge Release 2026.10.04a Review.md`, findings F1-F12). Install this release, not 2026.10.04a.

**What changed**
- **F1: the model switch can no longer undo itself, and a dead line no longer loops forever.** The roster's changing state (the pool's exhaustion, the marks, the failure counts) moved out of the tracked `docs/ROSTER.json` into the repository's own `.git/bridge/roster-state.json`, which no reset, clean or checkout touches; a roster from an older release seeds it once. The failure window is eight hours, longer than any run limit. A connection failure or a hit run limit is retried twice, then exit 5: stop and tell the owner, because no model switch fixes a network. A legacy integer count is treated as expired (F9). A test runs record → reset → re-resolve in a git repository.
- **F2: the supervisor's own merge step now matches the merge policy.** Review B is launched through the launcher with `--trust --mode ask`, the launch time is read from the launcher's first stderr line, and `pr-activity-check.py` printing `OK` is part of condition 3. The parallel delegation step no longer says "starting with `cursor-agent`". A test checks every `cursor-agent` invocation in the instructions: all go through the launcher, every read-only review carries `--trust --mode ask` and never `-f`.
- **F3, F7: the guardrails hold in both shells and every form.** New `permission-guard.py`, a PreToolUse hook for the Bash and PowerShell tools that parses each command and refuses `gh pr merge --admin`, the REST merge, and every force-push form (`--force`, `--force-with-lease`, `-f`, `-fu`, `--mirror`, a `+` refspec), through chains, wrappers and `git -C`, in every permission mode; 73 tests. The deny rules are mirrored for the PowerShell tool, which also refuses `cursor-agent` and `bridge-run` from PowerShell (where `~` is not expanded and the shim does not apply). The instructions say to run the bridge's commands with the Bash tool only, and the text no longer calls the rules a boundary.
- **F4: the tests touch nothing outside their temporary folders.** `LOCALAPPDATA` points at a temporary folder in every test run; the shim and the `gh-empty` folder are created there. The install program keeps a previous, different shim as `cursor-agent.bak-<date>-<time>`, and names the settings backup with the time too.
- **F5: honest claims and a closed window.** `pr-activity-check.py` refuses a `--since` without a time zone, and also flags what the owner's account did elsewhere in the repository since the launch that an agent would cause (a comment or review on another pull request, a merge, a push to `main`); the supervisor's own task-branch pushes are not flagged. The texts in KP-032, the merge policy and the setup guide say what the mechanism is (identity withheld, so an accidental post or push fails) and is not (a sandbox).
- **F6: the launcher accepts only the loop's commands**, `cursor-agent` and `gh pr checks`, and refuses anything else (exit 125); its allow rules name those two forms.
- **F8: rule 8's reason corrected** to Claude Code's documented behaviour: `timeout`, `time`, `nice`, `nohup` and `stdbuf` are stripped before matching, `cd` and a shell are not; deny and ask rules see through chains and wrappers.
- **F10: the launcher puts itself into the job before starting the command**, so every child is born inside it; at a normal end the job's closing kills any orphan the command left (proven on a dev-server-like child). Signatures declared for the Windows calls (the pseudo-handle was truncated before).
- **F11: tests added** for the activity check (with canned `gh` answers), the shim's recipe against the Python one, the stripped environment reaching the child, a program printing a character the console lacks, and the consistency of the instructions; CI actions pinned by commit and `pytest` by version.
- **F12: retired entries are removed at install** (`settings.bridge.json` lists them: the old worktree, jscpd and impeccable patterns and the first launcher rule); the setup guide names the release's `.claude` folder correctly; the usage-limit text in step 3b matches the classifier; a project's own commands go to the classifier and are not called defects.

**Running projects must**
- *(all phases)* Install with `python <release .claude folder>/cursor-bridge/bridge-install.py`, restart the app, run `/calibrate-bridge`; the items of 2026.10.04a apply unchanged. At the first `roster-check.py` run the roster's state moves to `.git/bridge/roster-state.json` (a `note  migrated` line); nothing to do.

---

## 2026.10.04a

**Release 0a of the restructuring plan: the safety fixes the plan review of 2026-10-04 ranked above everything else, shipped ahead of the TDP.** Every program change carries tests under `Workspace/tests/`, run by the bridge's own CI from this release on.

**What changed**
- **KP-032: the owner's identity is withheld from every `cursor-agent` process.** The shim that Claude Code's Bash tool runs for `cursor-agent` (`cursor-bridge/cursor-agent.shim`, installed by the new install program) and the new launcher `bridge-run.py` start the agent with `gh` logged out, no token variable, and git without a credential helper and without prompts. Review B runs with `--trust --mode ask`, the Cursor CLI's read-only mode, never `-f`. New `pr-activity-check.py`, run after every Review B and before every merge, lists what was written to the pull request since the launch and flags anything written as the owner. New **deny rules**, enforced in every permission mode: no `gh pr merge --admin`, no force-push. (Verified cause: on 2026-10-02 Review B posted its verdict on TDP #182 under the owner's account.)
- **KP-033: every background run has a limit that ends it.** `bridge-run.py --limit <s> -- <command>` runs a command inside a Windows Job Object and kills the whole process tree at the limit (exit 124), so an orphaned child can no longer hold the output pipe and the supervisor always wakes. Delegations run under 7,200 s, Review B under 1,800 s, the CI watch under 3,600 s. On exit 124 the supervisor inspects the tree before discarding anything, because a builder that hung on its way out may have finished (TDP ISS-005).
- **KP-034: the roster check no longer misfires.** A `--record-failure` argument that is not a model of the roster is refused (reAngle ran five days on its backup pairing because a file path was recorded as a model); a connection error is transient and never counted; a failure count expires after two hours and `--record-success` clears it; an automatic "unavailable" mark expires after six hours; a rate limit or the word "billing" no longer counts as a usage limit; step 3b resets the tree *before* re-resolving, so the reset can no longer revert the roster files and reinstate the exhausted model. The probe runs with the stripped environment.
- **KP-030, finished: installing is one command.** New `bridge-install.py` copies the release, **merges** the bridge's entries (`cursor-bridge/settings.bridge.json`, now the single source of the allowlist, the deny rules and the hooks) into the owner's `settings.json` without touching any other key, installs the shim, and runs the check. `bridge-check.py` no longer fingerprints `settings.json`: it verifies that the bridge's entries are present and that the installed shim equals the release's. `make-manifest.py` regenerates the tree's own `settings.json` from the bridge file.
- **The allowlist matches what the instructions issue.** Entries corrected to Claude Code's documented matching (`git worktree add ../Worktrees/*`, `npx --yes jscpd@*`, `npx impeccable@*`); missing commands added (`git log`, `git rev-parse`, `git rm`, `git revert`, `git reset --hard`, `git clean -fd`, `git config core.hooksPath`, `pytest --collect-only`, the new programs). A test (`tests/test_allowlist.py`) collects every command from the instructions and checks it against the rules, and checks that the deny rules catch the override merge and force-push in every spelling. Found on the way: the merge policy said `git pr merge` (a typo), and the instructions said both `git checkout -B` and `git switch -c`; both fixed.
- **The permission mode is stated.** The supervisor's instructions now say that sessions run in *auto* mode, that the deny rules are the hard guardrails, and that a command the rules do not cover is a bridge defect, never a question for the owner. Rule 8's reason is corrected: each part of a compound command is matched on its own and a wrapper is not stripped, so chained or wrapped commands match nothing.
- **The loop guard works wherever a session starts.** It finds `docs/PROJECT_STATUS.md` from `Workspace`, from the project root above it, from a subfolder, and from a worktree under `Worktrees/` (it read the worktree's own copy before); it reads `**Phase:**`, bulleted and backticked variants of the status lines; it treats a server started with the PowerShell tool like one started with Bash. The start-folder instruction accepts the project root (`cd Workspace` first), which is where the desktop app starts sessions.
- **Programs never crash on a character the console lacks** (`→`, `≤`, `✗` crashed `scope-check`, `plan-check`, `sync-check` and `roster-check`): every program reconfigures its output with a replacement. Every subprocess call now carries the no-window flag; the bridge's own `windowless-check` passes over its programs.
- **The bridge has a committed test suite and CI**: `Workspace/tests/` (the loop guard, the roster check, the launcher, the install program and the check, the allowlist) and `.github/workflows/tests.yml` on Windows and Linux.
- Setup guide: install by program (Step 3), permissions explained instead of hand-edited (Step 6), the guardrail statements corrected (Step 7). `/calibrate-bridge` points at the install program.

**Running projects must**
- *(all phases)* Install this release with `python <release>/cursor-bridge/bridge-install.py` (never by copying files; it merges `settings.json`), restart the app, run `/calibrate-bridge`. From then on every delegation and Review B goes through `bridge-run.py` as the instructions now show, Review B with `--trust --mode ask`, and `pr-activity-check.py` runs before every merge.
- *(building, changing)* On the next checkpoint, run `python ~/.claude/cursor-bridge/roster-check.py docs/ROSTER.json` once (superseded by 2026.10.04b: the state migrates to `.git/bridge/`). Keys of paid providers (Modal, Hugging Face, OpenRouter) must not sit in `Workspace/.env` where the builder reads them: move them to the user's environment or the product's encrypted store, as the next increment of the part that uses them, and record where in the inventory.
- *(configure, building)* The video factory: add the security floor to its gate (Semgrep with the Pro engine, OSV-Scanner, Socket), pin its CI actions by commit, and move the gate to Linux runners, as the next increment. The TDP: run Semgrep's Pro engine and the bundled bridge rules in its gate, as the next increment.

---

## 2026.10.03a

**What changed**
- **KP-031: a running server is not a wake source.** `loop-guard.py` now counts a background command as something that will wake the supervisor only if it is of a kind that finishes: the builder (`cursor-agent`), the CI watch (`gh pr checks … --watch`), or a command marked with the comment `# wake`; servers, workers and probes no longer satisfy the guard. It also reads completion notices from queue records and queued-command attachments, which it had missed, so a finished task no longer counts as pending for six hours. Rule 43 states the marker. Replayed against the reAngle transcript: the old guard saw two pending tasks at the stop that stalled the loop for seven hours; the new guard sees none and would have refused the stop with its nudge. Tests: seven wake-source cases, a finished run, a background agent, and the transcript replay (in the maintainer's harness; the bridge's own test suite is release A of the restructuring plan).

**Running projects must**
- *(building, changing)* Append `# wake` to any background command you start and intend to wait for that is neither the builder nor the CI watch. Nothing else changes.

---

## 2026.10.01a

**What changed**
- **Every cost names who charges it.** When the supervisor states an amount the owner will pay (a test, a live call, a benchmark, any paid service), the platform and the account charged are named in the same sentence as the amount; several platforms charged by one action are each listed with their share. Reporting section of the supervisor's instructions and guard 7 of `explain-for-decision`. Owner-reported: a figure without its platform cannot be checked against the account's balance. Governance text only.

**Running projects must**
- *(all phases)* From the next report on, state every cost with its platform and account.

---

## 2026.09.29a

**What changed**
- **KP-030**: `~/.claude/settings.json` is shared with Claude Code, which writes its own keys into it (`switchModelsOnFlag`, `/fast`, `/effort`, `/advisor`, some approvals). A difference confined to keys the bridge does not own is not a failed install. Until `bridge-check.py` verifies only the bridge-owned entries and installation merges instead of copying (Restructuring Plan, release A), the calibration procedure compares the bridge-owned content by hand and continues with the difference recorded; the owner is never asked to remove a key the bridge does not own. Also: a vendor fact quoted to the owner is read from that setting's own documentation page. Governance text only; no program changed.

**Running projects must**
- *(all phases)* Apply KP-030 at the next `/calibrate-bridge`: if `settings.json` is the only STALE file and its bridge-owned content matches, record the exception and continue.

---

## 2026.09.27c

**What changed**
- **Diagram-based planning** (the owner's method, adopted after review). The design is a Project Design Document: `docs/DESIGN.md` plus normative Mermaid diagrams in `docs/diagrams/`. New `Diagram-Planning-Conventions.md`: an 18-kind catalogue over five levels (functional workflows; infrastructure; components; data structures; runtime logic), selected per project with every omission reasoned; three rules — top-down, Level 4-5 detail only where load-bearing (concurrency, security, integrity, performance, protocol, prior-failure), normative only if enforced (deterministic check, tests, or named review item). Notation conventions verified against the Mermaid 12.0 docs (use cases stay flowcharts because Typora bundles Mermaid 11.13; no element named `end`; spaces around links).
- **`diagram-specialist`** subagent drafts diagrams level by level (parallel kinds at once, mutually dependent pairs in one run); the supervisor integrates; `plan-critic` gains diagram lenses (selection, load-bearing detail, enforcement, meaning across diagrams).
- **`diagram-check.py`** (22 tests, including an untracked new file): index and catalogue coverage, notation per kind, refinement only upward, sequence participants against the diagrams they refine, use cases and screens traced to requirement IDs; in code mode, imports checked against the component diagram (Python, JavaScript, TypeScript), the schema dump against the entity-relationship diagram, and state machines against their tests. Step 4 of the loop runs it on every increment.
- **Explicit build plans**: every increment states Parent, Depends on, Parallel, Satisfies, Diagrams, Scope; stages are vertical slices; status is derived from `origin/main` commit subjects, so PR titles now start with the increment IDs. **`plan-check.py`** (13 tests) validates the fields and lists ready increments.
- **Parallel increments** — run parameter 5, `off` by default. With `on`, the builders of ready independent increments run at once, each in its own worktree (`cursor-agent --workspace`), committing a hand-off snapshot; the supervisor never works inside a worktree (Claude Code prompts for git in another folder and for files outside the working directory) and processes the finished branches one at a time in its own checkout. Not yet exercised on a real project.
- **Objections and bottom-up escalation**: a new section and rules 45-47; `Glossary.md` fixes the bridge's vocabulary (phase vs stage, brief vs contract, specialist vs auditor vs supervisor, objection, autonomous resolution); `/calibrate-bridge` now re-reads the conventions and the glossary. Reviewers fail design regression; the refactoring scout treats normative diagrams as constraints; the security auditor checks trust-boundary crossings drawn in data flow diagrams.

**Running projects must**
- *(all phases)* Re-read `Diagram-Planning-Conventions.md` and `Glossary.md`, and use the glossary's terms from now on.
- *(intake, design)* Design by diagram-based planning now: write the diagram index, draft with specialists, pass `diagram-check.py --mode design` before the design gate.
- *(mockups, planning)* The design gate has passed and is not reopened. Write or finish the build plan with the placement fields and vertical stages; `plan-check.py` must pass at the plan gate.
- *(building, changing)* No gate is reopened: no retroactive diagrams and no rewrite of the approved plan. New plan addenda use the placement fields; PR titles start with the increment IDs from the next pull request on; add `Parallel increments: off` to `docs/RUN_PARAMETERS.md` with a one-line notice to the owner that it can be switched on. The next change cycle's design revision builds at least the component diagram with its element map, and the entity-relationship diagram where data is stored.
- *(done)* Nothing until the next change cycle, which applies the item above.

---

## 2026.09.27b

**What changed**
- **Done is measured against the requirements, not the plan** (KP-029: SFVF shipped its specified Settings tab as a placeholder reading "Arrives in a later stage" and was declared done). New requirements register `docs/REQUIREMENTS.md` — one ID per requirement from intake, the owner's requirements document, the design, and every mockup screen and state — written at the design gate and confirmed by the owner. Increments name the IDs they satisfy; tests carry the IDs; briefs list them and forbid stand-ins; plan-critic blocks an untraced requirement; diff-reviewer fails a stand-in presented as the feature.
- **Deferral is the owner's.** A requirement becomes `deferred` or `dropped` only with the owner's dated answer; a stand-in screen is never a deferral (escalation list, Scope).
- **`completion-check.py`** (16 tests; run read-only on three real projects: it found the SFVF Settings placeholder and a 501 "not implemented yet" admin function in the documentation provider, with no false positives). `--mode plan` at the plan gate and every stage close; `--mode done` must pass before "Project complete" and runs first in every change cycle, so an inherited "done" is verified. Rule 44. Allowlisted.

**Running projects must**
- *(all phases after design)* **Build `docs/REQUIREMENTS.md` now** from the intake record, any requirements document, `DESIGN.md` (and its Change sections), and the approved mockup's screens and states; mark each row `built` (with the tests that prove it — add the ID to those tests), `planned` (and name it in a build-plan increment), or put it to the owner for a dated deferral. Present the register to the owner once as an FYI with any requirement found unbuilt.
- *(done)* Run `completion-check.py --mode done`. Every failure is a gap in the delivered product: report it to the owner plainly and open a change cycle for it unless they defer it.
- *(building, changing)* From the next brief on, briefs carry `Satisfies:`; the plan passes `--mode plan` at the next stage close.

---

## 2026.09.27

**What changed**
- **The loop no longer stalls after a green CI run** (KP-028). The Claude desktop app now tells Claude Code to register PRs with its CI monitor and not to watch CI itself, and that monitor reports failures and review comments only, never a green gate; supervisors armed auto-merge, registered the PR, ended their turn, and waited forever. Seen at least eight times in three projects from 2026-09-24. The merge step now names the mechanism: one background `gh pr checks <n> --watch --required --fail-fast` per PR, whose completion wakes the supervisor; the owner authorises it; the app's monitor is never the wake-up. While it runs, the supervisor keeps building what does not overlap the pending PR.
- **Rule 43 + `loop-guard.py` Stop hook** (registered in `settings.json`). During `building` / `changing`, a turn may end only with a background task pending or with `Awaiting user on:` naming an owner wait. The hook refuses such a stop once (exit 2, reason to the model), never twice in a row (`stop_hook_active`), never outside a bridge Workspace or in other phases, and fails open on any error; it re-reads the transcript after 2 s because the transcript is written asynchronously. Contract verified against the Claude Code hooks reference; tested on 21 cases and read-only against three real transcripts. `Awaiting user on:` semantics documented in "Project state". This is the pinned Unlazy stop-hook idea, adopted because its trigger occurred.

**Running projects must**
- *(all phases)* Make `Awaiting user on:` in `docs/PROJECT_STATUS.md` true now: `nothing` if the loop is running, otherwise the specific wait. A stale entry either lets the loop idle unseen or makes the guard nudge a session that is legitimately waiting.
- *(building, changing)* For the next PR and every one after: arm auto-merge, then start the background watch; do not end the turn to wait for the app's CI monitor.

---

## 2026.09.26

**What changed**
- **The builder reports where it guessed.** Every brief's Done section (all variants) now requires an `Assumed, not verified` list: each fact the change relies on that neither the brief nor the code settled — what, why, what would confirm it — or an explicit `none`. The run is one-shot, so the question must be in the brief; asked afterwards, a fresh session no longer knows.
- **The supervisor triages it** at step 4: copied verbatim first; a missing list is unknown, not none; each item gets one disposition — test, contract (rule 37), council, or accepted (an inventory Decisions row) — recorded in the accept commit's `Assumptions:` body. At merge the branch's lists go to Review B in `run/review/ASSUMPTIONS-<nnn>.md` beside the diff.
- **Reviewers use it as extra places to look, never as scope.** diff-reviewer checks each item and hunts unlisted ones (an unlisted external-service assumption is a `FAIL`); new anti-gaming bullet in the merge policy.
- **Least confident, at every stage close and project end** (reflection item 2b): the supervisor names its three least-sure parts with the check that settles each, in `HARDENING.md`; testable ones become tests before the next stage. Rule 42; KP-020 cross-reference.

**Running projects must**
- *(building, changing)* From the next delegation on, every brief carries the `Assumed, not verified` section (spec-packager does this); a brief already written but not yet delegated gets the section added. Triage each list at step 4 and record dispositions in the accept commit.
- *(building, changing)* At the next merge, include `run/review/ASSUMPTIONS-<nnn>.md` for Review B (increments accepted before this release have no lists; say so in the file).
- *(building, changing)* At the next stage close, run reflection item 2b.

---

## 2026.09.25g

**What changed**
- **Current-state record.** `docs/PROJECT_STATUS.md` is current position only — rewritten in place, capped at 120 lines / 12,000 characters. New `docs/INVENTORY.md` holds what the software is: Features, Resources (every environment variable, CI secret, key, account, and tool — names and locations, never values), Decisions (with reasons), Deferred. Created at the design gate, updated in the same commit as each `CHANGES.md` entry (`Reflected through:` marker), both files read whole at every start and resume (rule 20 exception). Private memory is declared not to be project state.
- **Look it up before you ask or propose.** Never ask the owner for a listed resource, never propose a listed feature, never reverse a Decision without quoting its reason and what changed. Change-cycle intake reads the inventory first; spec-packager's reality check starts from it; plan-critic blocks a plan that rebuilds, re-asks, or silently reverses.
- **`inventory-check.py`** (tested; also run read-only on two finished projects, where it flagged both status files and 11 and 15 unlisted configuration variables) at every reflection point. Rule 41, KP-027. Allowlisted.

**Running projects must**
- *(all phases)* **Build `docs/INVENTORY.md`** in the format in supervisor.md → "Project state", from what exists: the design document(s) and any "settled" or "do not relitigate" notes → Decisions, with reasons; `CHANGES.md` and the User Manual → Features; `.env` examples, the code's environment reads, CI secrets, the app's own secret store listing (names only), and anything the owner provided according to the status file, the Documents, or private memory → Resources; backlog and deferred items → Deferred. Set `Reflected through:` to the newest `CHANGES.md` heading once Features covers it.
- *(all phases)* **Shrink `docs/PROJECT_STATUS.md` under the cap**: move its current content verbatim to `docs/archive/PROJECT_STATUS-<date>.md` (nothing is deleted; the archive is never read at resume), then rewrite the status file from the template. Fold any project state held only in Claude Code's private memory into the two files.
- *(all phases)* Run `inventory-check.py` until it prints `RESULT: OK`; commit the inventory on the next branch so it reaches `main` through a PR.

---

## 2026.09.25f

**What changed**
- **Several bugs in one report are triaged before diagnosis.** New step 0 in the `root-cause-first` skill: reproduce each, compare on concrete signals (code path, trigger, component, first-bad commit), bin only on evidence with one discriminator that must move every member, split out any member that does not respond, and default to one diagnosis per bug when nothing is apparent. A confirmed group gets one fix brief (spec-packager) and one gate pass; every member keeps its own reproduction test; diff-reviewer fails a partly fixed group. Rule 26, change-cycle intake.
- **Local and remote must agree.** New `sync-check.py` (tested against a local bare remote across all seven states). Runs at start and resume, before every new branch (now cut from `origin/main`, never local `main`), after every merge (`git switch main` + `--apply`), at reflection points, and `--strict` at project end, where only IN SYNC or NO REMOTE allows "Project complete". Stranded commits on protected `main` are rescued to a branch, never deleted. New `Remote sync:` status line; the status file may stay local only uncommitted. Rule 40, KP-026. Allowlist: `sync-check.py`, `git fetch`, `git switch`.
- **Remaining pool/Grok staleness removed.** The checkpoint text still called `other_pool` owner-set and quoted Grok 4.6; KP-024, the merge policy's invariant paragraph and Review B note, and the roster-check docstring still placed "unprefixed Grok" in the Other Models pool or used Grok 4.6. All now match Cursor's documentation and the automatic switch.

**Running projects must**
- *(all phases)* Run `sync-check.py --apply` now. BEHIND is fast-forwarded; AHEAD or DIVERGED: follow the printed rescue, carry what is still needed through a PR, open an issue. Add the `Remote sync:` line to `docs/PROJECT_STATUS.md`. If the status file is committed on local `main`, it is stranded: rescue it.
- *(building, changing)* Cut every new branch from `origin/main`; after every merge `git switch main` and `sync-check.py --apply`.
- *(done)* A project already marked done runs `sync-check.py --apply --strict` once; anything other than IN SYNC or NO REMOTE is resolved and recorded as an issue.

---

## 2026.09.25e

**What changed**
- **Worktree convention** (SFVF feedback item 8). Sequential work is branches in the single
  checkout; a git worktree exists only while two branches must be live at once, lives under
  `<project-root>/Worktrees/<name>` (sibling of `Workspace/`, never inside it, never a loose
  `wt-*` folder), is recorded in `PROJECT_STATUS.md` (`Worktrees:`), removed at merge with
  the safe primitive, and checked at every reflection point (`git worktree list`). The
  boundary is now "the checkout the builder was launched in". The loop's "worktree branch"
  became "increment branch" and the Review B note no longer says the reviewer runs in a
  worktree — that vocabulary was the nudge. Rule 39, KP-025, layout section, status block.

**Running projects must**
- *(all phases)* Run `git worktree list`. Any worktree you still need moves under
  `<project-root>/Worktrees/`; every other one is removed with the safe teardown primitive
  (link check first). Add the `Worktrees:` line to `docs/PROJECT_STATUS.md`. From now on,
  no worktree for sequential increments.

---

## 2026.09.25d

**What changed**
- **Roster corrected from Cursor's documentation.** Grok 4.7 is in the *Cursor Models*
  pool ("Grok 4.7, Grok 4.6, Grok 4.5, and Composer 2.5"); the template had inferred
  "metered" from the id's shape and fallen back to Grok 4.6. Now: full profile builder
  `grok-4.7-high` / Review B `gpt-5.6-sol-high`; native profile builder `composer-2.5` /
  Review B `grok-4.7-high`. `roster-check.py` classes any Grok or Composer id as native.
  The merge policy now says pools and ids are read from the docs and `--list-models` at
  configuration, and the strongest model in each pool at that time is picked. KP-024
  addendum.

**Running projects must**
- *(all phases)* Replace `cursor-grok-4.6-high` with `grok-4.7-high` in both profiles of
  `docs/ROSTER.json` and re-run `roster-check.py`; the next delegation and Review B use the
  re-resolved ids.

---

## 2026.09.25c

**What changed**
- **Automatic return on the reset day.** `docs/ROSTER.json` gains `reset_day` (day of month,
  UTC; the owner's subscription resets on the 15th, so `16`). Exhaustion is stamped in UTC
  (automatically on a usage-limit failure, or by `--mark-exhausted` when the owner says so);
  at the first checkpoint on or after 00:00 UTC of the first reset day after that stamp,
  `roster-check.py` restores `other_pool` to available, clears the failure and unavailable
  marks, prints `AUTO-RESET`, and the preferred profile is used again — no owner action.
  `--mark-reset` still brings it earlier. `ROSTER_NOW` overrides the clock for tests
  (eight cases pass, including the 23:59 / 00:00 boundary and a same-month vs next-month
  exhaustion).

**Running projects must**
- *(all phases)* Add `"reset_day": 16` to `docs/ROSTER.json`. If the pool is currently
  marked exhausted without a UTC `exhausted_at`, set it to the date the owner reported
  (2026-09-25T00:00 UTC) so the October reset is computed.

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
