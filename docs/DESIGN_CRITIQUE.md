# Design & plan critique — Claude-Cursor Bridge

Two critics of different makes (plan-critic on Fable 5.1; Review B = grok-4.7-medium, native profile) read the same committed text in fresh contexts and grade each finding Blocking / Should fix / Consider. The design (the Restructuring Plan's release B) is already approved by the owner; this record covers the **build plan** and the **requirements register** for release B.

## Accepted
| Finding | Critic | Round | Reason |
|---|---|---|---|
| bridge-install.py may need no change to carry `workflow/` (it already globs `cursor-bridge/` from the manifest) | both | 1 | kept as a *proof* obligation on TASK-010: a test shows `workflow/**` installs without a code change; if it does not, a builder increment is added. Dropped from the carve's Scope either way. |

## Rounds
| Subject | Round | Critic | Blocking | Should fix | Consider | Fixed |
|---|---|---|---|---|---|---|
| plan | 1 | plan-critic | 7 | 10 | 3 | yes — plan revised (see below) |
| plan | 1 | Review B | 5 | 7 | 2 | yes — plan revised (see below) |
| plan | 2 | plan-critic | 6 | 7 | 5 | yes — round-3 revision (see below) |
| plan | 2 | Review B | 1 | 10 | 3 | yes — round-3 revision (see below) |
| plan | 3 | plan-critic | 1 | 13 | 5 | yes — round-4 revision (see below) |
| plan | 3 | Review B | 2 | 7 | 3 | yes — round-4 revision (see below) |
| plan | 4 | plan-critic | 0 | 7 | 8 | yes — fixed; confirming read pending |
| plan | 4 | Review B | 3 | 3 | 2 | yes — fixed; confirming read pending |

### Round 1 — consolidated findings and disposition
Both critics converged on the first six; convergence is treated as strongly blocking.

1. **No acceptance criteria on any increment; the four extracted lessons attach to nothing** (plan-critic B1, Review B #1). FIX: every increment gains a `Done when:` block of observable outcomes, each text increment's structural test assertions naming its R-ID; the lessons are attached literally (digest cap on the carve; module read-whole on the modules; has-screens *adds* the mockup variant; workflow-check fails an unwritten-type line; open-list written column).
2. **R-012 / interface-variant homes muddled; playable prototype missing; variant text has several homes** (plan-critic B3, Review B #5). FIX: `phases/interface.md` declares all four variants (mockups, command design, contract design, playable prototype); each variant's text in one place; the register row R-012 moves to the interface-module increment; has-screens *activates* the mockup variant and holds only the §6.8 extras.
3. **Author split breached** (plan-critic B5, Review B SF/Consider). FIX: split the Workflows-line increment into supervisor (template+semantics) and builder (inventory/conformance checks); the calibration increment into supervisor (calibrate-bridge.md text) and builder (conformance-check.py); drop bridge-install.py from the carve.
4. **The carve breaks existing tests and the hook mapping** (plan-critic S1/S3, Review B #2). FIX: carve increments carry the existing structure-pinning tests ("kept and re-pointed, never deleted"); the hook increment carries the Phase→module table, reflection.md, the extra re-reads, and the conditional-file pointers.
5. **The traceability comparison is insufficient and mis-ordered** (plan-critic B7, Review B #3). FIX: R-029 extended — a pinned pre-split baseline commit; covers the project-layout/boundary section; verbatim-move policy with a listed-exceptions file; checks `~/.claude/...` references and cited sections; runs incrementally from the carve on.
6. **No release/install stage; the bridge is installable software** (plan-critic B4, Review B SF). FIX: new Stage B6 "Release & install" (release-level review by a fresh context, stamp: VERSION/MANIFEST/CHANGELOG with rollback notes, projects paused, install, bridge-check on the installed tree, reAngle as the trial, field acceptance, the others resumed) + R-037; the install-from-second-checkout owner decision gets R-039, settled in B6.
7. **Requirements present in the design but absent from the register** (plan-critic B2). FIX: add R-032 (module size bound), R-033 (workflow-check runs at release and calibration), R-034 (trait additions apply in a stated order), R-035 (traits proposed at intake, settled at the design gate), R-036 (§6.7 second half — a new trait's design handling, design-gate flag, promotion pass).
8. **Ordering** (plan-critic B6, Review B SF): B2 wrote procedure text into the monolith that B3 then moves. FIX: carve first; pause/flag procedure folded into the intake/design modules; traits/types depend on the phase modules they gather from; glossary moved to B2.
9. **MANIFEST regeneration + CI enforcement** (plan-critic S2). FIX: MANIFEST.json in every `bridge/`-touching Scope + a standing brief constraint to regenerate it.
10. **TASK-002 lockfile for OSV/Socket** (plan-critic S9, KP-005/KP-018). FIX: add `requirements.lock`; CI installs from it; explicit exit-code handling; ubuntu authoritative for Semgrep.
11. **TASK-010 is secretly four phases** (plan-critic S10). FIX: split the phase-module increments (intake+design / interface+planning / run-params+config+loop / change-cycle+reflection+project-end).
12. **Demonstrations read other projects' status files** (Review B #4, plan-critic C1): B4's R-031 was only satisfiable in B5/B6. FIX: B4 classifies on committed fixtures; the real cross-project no-pause calibration is R-031's install-stage half (B6).
13. **Extension points for Definition-of-done and Delivery; §6.10 procedure** (plan-critic S7/C3). FIX: the registry (TASK-005) names which module declares each point; §6.10 (adding/changing a conditional workflow) recorded in the framework text.
14. **Minor:** baseline measurement recorded in the inventory as a met precondition (plan-critic S8); Stage B1 has two increments and that is acceptable for this release (Consider, no change).

Also recorded as a **release-B issue (ISS-001):** the Phase-2 two-critic-loop mechanics use a `.err` filename (`REVIEW-DESIGN-<subject>-<round>.err`) that `review-guard verify` does not recognize as the run's own `.err` (it expects `REVIEW-<nnn>.err` matching the snapshot id), producing a false GATE-INTEGRITY flag on a clean, restored tree. Candidate bridge-feedback item for A3's design-critique machinery; recorded at the reflection point.

### Round 2 — consolidated findings and disposition
Round 1's six converged Blocking findings were confirmed resolved by both critics. Round 2's findings are new consequences of the carve-first reordering, plus two owner decisions. Convergent items first.

1. **trace-check ordering (CONVERGENT Blocking: plan-critic B3, Review B Blocking).** FIX: TASK-016 builds `trace-check.py` and pins the baseline (`workflow/trace-baseline.txt`) *before* the carve (depends on TASK-003, TASK-005); TASK-010 and the module increments depend on TASK-016; the carve's `Done when` requires trace-check green on the moved sections; TASK-025 requires a full trace-check pass over the finished split.
2. **The carve must move phase sections into modules in the same commit** (plan-critic B2). FIX: TASK-010's Scope gains the ten module paths and it moves each section verbatim; the hook (TASK-015) depends only on TASK-010 and lands immediately after; no release is stamped between them (release B only stamps at B6, so this holds). TASK-011–014 then enrich the modules (compaction list, declared points, new §6.3/§6.5/§6.7 text).
3. **Decision 6 and R-038 are owner decisions due at intake** (plan-critic B1, B5). DONE: both put to the owner 2026-10-11 and recorded in INVENTORY (owner confirmed decision 6; R-038 = pause & switch at B6). TASK-001's `Done when` records the asking.
4. **R-035 → TASK-011; R-036 also in project-end.md (TASK-014)** (plan-critic B6, Review B SF). FIX applied in the plan.
5. **Open-list "written" column flipped by the workflow-writing increments** (Review B SF): `open-list.md` added to TASK-017–021's Scope.
6. **Author-split file collisions ordered** (Review B SF): TASK-010 depends on TASK-007 (both edit supervisor.md); TASK-006 depends on TASK-002 (both edit tests.yml); TASK-024 depends on TASK-008 (both edit conformance-check.py).
7. **The hook prints the digest and the pointers as two runs** (Review B SF): TASK-015 `Done when` corrected.
8. **trace-exceptions.md is supervisor-appended** (plan-critic S3, Review B SF): TASK-016 (builder) creates the empty file + program; each rewording supervisor-text increment lists its exception (file added to those Scopes).
9. **Type-workflow correctness** (Review B SF): local service also runs command design where it has admin commands (the TDP); interface variants are *added* per interface kind, not set as one value; host-extension delivery is a *set*. Folded into TASK-020/021 `Done when`.
10. **TASK-017 `Done when` describes all four traits**; **TASK-025 depends on TASK-015 and TASK-011**; **exact size bounds + a sub-file fallback** (R-032, Review B/plan-critic S4); **field acceptance named** (plan-critic S5, TASK-027); **TASK-022 depends on TASK-012 only** (the backwards TASK-020 dep removed); **the standing "workflow-check exits 0" constraint applies only from TASK-006 on**; **the glossary term set is closed** (TASK-009); **the issues-rule compaction line** added to TASK-014. All applied.

### Round 3 — consolidated findings and disposition
Both critics confirmed the round-2 fixes resolved, the graph acyclic, all 38 requirements traced (Blocking fell 7→6→1 for plan-critic, 5→1→2 for Review B). The round-3 findings converge on a small, precise set; all fixed in round 4.

1. **Move-vs-point for the gathered traits (CONVERGENT Blocking: plan-critic B1, Review B B1).** SETTLED: §6.8 says *move* (the main workflow shrinks). TASK-017 MOVES the four gathered passages out of the phase modules (Scope gains the source modules per trait); the mockup-variant text lives in `interface/mockups.md` (TASK-012) and the *has screens* trait activates the variant + holds only the §6.8 extras (no double-ownership); `trace-check` accepts a passage moved twice (baseline → module → trait, "found verbatim anywhere"); new module text is declared in `trace-exceptions.md` (two entry kinds: `reword` and `new`).
2. **CI red through B3 (CONVERGENT Blocking: plan-critic S2, Review B B2).** FIX: TASK-006's CI invocation checks `workflow/**` and `tests/fixtures/workflows/` only (never the bridge's own tracked `docs/PROJECT_STATUS.md`, which already carries a Workflows line); the failure cases run on fixtures; the tree-wide registry↔module cross-check is a Done-when of TASK-014 (when every module declares its points); the status-line clause runs at calibration (TASK-024) and in TASK-025.
3. **project-end is not a top-level section — it is the block inside Reflection points** (Review B B1): the carve names reflection→project-end as a *declared split* in `trace-exceptions.md`; `project-end.md` is only in TASK-014's Scope (dropped from TASK-011).
4. **The hook table (CONVERGENT SF).** One shared table (TASK-015 program; TASK-023 text depends on TASK-015); it maps every live `Phase:` value (planning→planning+run-parameters; building→delegation-loop+reflection; changing→change-cycle+delegation-loop; mockups/interface/configuration/done) and the convention re-reads (merge-policy+pitfalls while building/changing; diagram-conventions+glossary at design; project-config+pitfalls at configuration); "exactly one phase module" is redefined as the `Phase` value's module(s) + reflection + the table's further files; the test asserts every live value, the convention files, and the R-034 trait order.
5. **Smaller convergent/precise fixes:** TASK-026 one author (→ the stamp is supervisor records); the stale INVENTORY Deferred row for R-038 closed (TASK-001 Done-when); TASK-016 depends on TASK-007 (baseline includes the Workflows template); TASK-015 depends on TASK-006; TASK-013 Scope gains `workflow/phases/delegation-loop/`; TASK-012's planning.md also opens with its compaction list and declares points; open-list rows carry default traits + workflow-name column, and the local-web-app sub-type replaces personal-data with installable + long-running (TASK-004, TASK-019); the registry marks replaceable phases and workflow-check adds the one-type/at-most-one-sub-type/sub-belongs cases (TASK-005, TASK-006); calibration ADDS a running project's Workflows line from its classification and confirms with the owner (TASK-023); B6 reordered to review→fixes (TASK-026) then stamp→install→trial (TASK-027), §15 condition 4's order; R-031's live half for the video factory and the TDP is the fixture classification + reAngle live, their live calibration an owner-dated deferral at B6 if not resumed; glossary gains workflow name / sub-workflow name / compaction-survival list; the no-release-between-carve-and-hook rule enforced by a release-blocker test; spends-money also carries §13.1's paid-results store and dry-run-on-copy.

### Round 4 (the ceiling) — consolidated findings and disposition
plan-critic returned 0 Blocking (round-3 findings confirmed resolved, graph acyclic, all 38 traced, author split clean). Review B returned 3 Blocking, all legitimate and uncontested (not a disagreement — no resolution round). The union, all fixed:

1. **Carve/hook test window (Review B B1, plan-critic S4):** `test_session_start.py` requires the old headings until the hook changes, so the suite is red between TASK-010 and TASK-015. FIX: TASK-010 and TASK-015 are one **merge unit** (one PR, both IDs in the title) so CI is never red on `main`; `test_session_start.py` is in both Scopes and updated in that combined change (never weakened — the digest-length and status-at-limits assertions kept).
2. **The Phase→module table must map every template value (Review B B2):** FIX: TASK-015/R-005 table — intake→intake; design→design; mockups→interface (+ mockups variant); planning→planning+run-parameters; configuration→configuration; building→delegation-loop+reflection (+project-end at the last stage close); done→change-cycle (a request on a done project is a change cycle); changing→change-cycle+delegation-loop+reflection+project-end.
3. **MANIFEST.json needed on an edit, not only add/move/remove (Review B B3):** FIX: the standing constraint now says "adds, moves, removes, or edits"; MANIFEST.json added to TASK-008, TASK-015, TASK-024 Scope.
4. **Which text is the mockup variant (CONVERGENT: plan-critic S1, Review B SF):** FIX: `interface/mockups.md` holds the Phase-3 mockup procedure; the *has screens* trait activates that variant AND gathers (by moving) the build-phase interface-project passages (the frozen-rule brief constraint, the design-auditor review step, the observability tests) from planning/configuration/delegation-loop/reflection. R-016 reworded accordingly; TASK-012/TASK-017 aligned.
5. **A founding rule stays in the core (plan-critic S2):** FIX: *long-running process* points at founding rule N1/§8.1 (which stays in the core) and adds the start/stop/health procedure + nothing-left-running check (R-021 reworded); *has screens* points at N7/N9 (they stay in the core).
6. **trace-check move-not-copy both directions (plan-critic S3):** FIX: a passage's home is `supervisor.md` or any file under `workflow/**`; a baseline passage found in more than one home fails as COPY unless a reword/new entry explains it; a `copy (fails)` test case added (TASK-016).
7. **Unwritten type vs unwritten trait (Review B SF, R-014/R-036):** FIX: workflow-check *fails* an unwritten type/sub-type (pauses the project) but *flags* (non-fatal) an unwritten trait (work continues, §6.7) — stated in TASK-006 and R-014.
8. **Smaller:** TASK-026 depends on TASK-025 and TASK-022 (R-026 lands before the release review, §15 cond 4); TASK-010 depends on TASK-006; `workflow/phases/delegation-loop/` added to TASK-017 Scope; R-020 includes §13.1's paid-results store + dry-run-on-copy; TASK-025 names R-029 (the full-split trace); R-005 and the B3 demonstration say "module(s)"; the release review checks the core is readable in one read; open list is canonical for default traits.

**Confirming read (the ceiling reached) — DONE, both critics clean.** plan-critic: "no residual Blocking — fit for the owner's Phase-4 gate" (0 Blocking, 1 Should-fix, 3 Consider). Review B: "the plan is sound and ready for the owner's gate; the round-4 fixes hold" (0 Blocking, 2 Should-fix, 1 Consider). Both dropped out — no resolution round. The only remaining findings were convergent register/record wording (R-014, R-020, R-021 lagged the critique record) plus three minor plan wordings (merge-unit title starts with the IDs; the hook lists variant files from the declared-variants line rather than naming `mockups.md`; the glossary Phase entry lists all eight values) — all applied before the gate. **The plan goes to the owner's Phase-4 gate.**

| Subject | Round | Critic | Blocking | Should fix | Consider | Fixed |
|---|---|---|---|---|---|---|
| plan | confirming | plan-critic | 0 | 1 | 3 | yes — applied |
| plan | confirming | Review B | 0 | 2 | 1 | yes — applied |

## Build rounds — supervisor-authored governance text

Each supervisor-authored text increment takes one combined round that serves as both the two-critic design review and the merge gate: Review A (diff-reviewer with the plan-critic lenses) and Review B (cross-family, with execution) on the committed diff. Convergent findings are blocking.

| Subject | Round | Critic | Blocking | Should fix | Consider | Fixed |
|---|---|---|---|---|---|---|
| TASK-003 | 1 | Review A | 0 | 4 | 6 | yes — round 2 (see below) |
| TASK-003 | 1 | Review B | 0 | 2 | 2 | yes — round 2 (see below) |

### TASK-003 round 1 — disposition
Both APPROVE. Two findings converged and were treated as blocking:

1. **"Siblings are exclusive" was pinned only as a label** (Review A Should fix, Review B Should fix). FIX: the test asserts the meaning, "a part has at most one sub-type of its product type".
2. **"The core governs" was loose and unpinned** (Review A Should fix, Review B Consider: read loosely it would cancel replace and set). FIX: scoped to the floor ("a conditional workflow's text that would do any of these does not apply, and on these points the core governs") and pinned.

Also fixed: the order is stated per extension point; "module or modules" (planning and building map to two); the transitional sentence says this file is still read whole until the phases move into modules, and maps the plan's phase names to this file's headings (Review B Consider); the open list governs the trait order and places a later trait at its end; several parts are taken in the status file's order; the Read-when cells are pinned exactly and the Holds cells by their items (Review B Should fix; the round-2 fix, reviewed in round 3, pinned the Holds cells whole).

| Subject | Round | Critic | Blocking | Should fix | Consider | Fixed |
|---|---|---|---|---|---|---|
| TASK-003 | 2 | Review A | 0 | 2 | 4 | yes — round 3 (see below) |
| TASK-003 | 2 | Review B | 0 | 0 | 3 | yes — round 3 (see below) |

### TASK-003 round 2 — disposition
Both APPROVE; the round-1 fixes confirmed. Two findings converged and were treated as blocking:

1. **The sub-workflow's Holds cell was not pinned whole** ("a more detailed version of its type workflow" could go unnoticed; Review A Should fix, Review B Consider), and the record overstated the pinning. FIX: every Holds cell is pinned by equality.
2. **The status file's Next line was stale** (both, Consider). FIX: rewritten.

Also fixed:
- **"Still read whole" collided with rule 28** (Review A Should fix). After a compaction the hook names the sections to re-read, so the sentence now says read whole "at every start and calibration (after a compaction, re-read what the hook names, rule 28)".
- **The heading crosswalk was unpinned** (Review B Consider). It is now pinned, and each named heading is checked to exist.
- **"The interface phase is Phase 3" could be misread** on a project without screens (Review A Consider). It now says Phase 3 "today holds only the mockup variant".
- **The type workflow's Read-when said "the phase module"** (Review A Consider). It now says "the phase's module or modules".
- **How parts and extension points nest was unstated** (Review A Consider). It is now stated: the phase module's own content comes once, then each part's type, sub-workflow and trait additions in status-file order. A trait two parts share applies once, at the first part that has it. This is pinned.

Deferred, each to the increment that owns it (design for later increments is not this diff's defect):
- how a replaced phase and a trait's attachment point are declared → TASK-005 (registry) and TASK-012 (declared points);
- a guard against a conditional workflow's sentence that contradicts the core → TASK-006 (workflow-check);
- R-007 is `built` on the text; it is exercised once the phases are modules and the hook names them → TASK-010 and TASK-015;
- TASK-004's brief carries "a sub-type must earn its place" (§6.5) and cross-checks the open list's trait order against the order stated here.

| Subject | Round | Critic | Blocking | Should fix | Consider | Fixed |
|---|---|---|---|---|---|---|
| TASK-003 | 3 | Review A | 0 | 1 | 3 | yes — round 4 (see below) |
| TASK-003 | 3 | Review B | 1 | 0 | 2 | yes — round 4 (see below) |

### TASK-003 round 3 — disposition
Review A APPROVE, Review B REJECT.

**REVIEWERS DISAGREE on the transitional reading sentence** (supervisor.md, the paragraph after the layer table). Review A approved it. Review B blocked it: it named start, calibration and compaction but not resume, and "reading only the current phase at those points" would replace the core's always-whole read. The crux is correctness, not intent. It is settled for Review B, because rule 28 is an established invariant: it re-reads the governing files whole on every start, resume and calibration, and after every compaction or resume it reads what the hook names. FIX: the sentence now defers to rule 28 unchanged. Once the phases are modules, the core is still read whole at those points, and the current phase's module or modules and the applicable conditional workflows are read with it. A test forbids the phase-only wording.

One finding converged and was treated as blocking:
- **"A trait two parts share is applied once, at the first part that has it"** (Review A Should fix, Review B Consider). It could be read as the trait's work being done for one part only, which is off-source (§6.2 applies a trait per part). FIX: "a conditional workflow two parts share is read once, but its additions apply to every part that has it, in each part's own place in this order". The parts sentence also restates "at each extension point" (Review A Consider).

Also fixed: the crosswalk test checks every phase heading the Holds cell names (intake, design, run parameters, the change cycle; Review A Consider); the round-1 note above names the round that pinned the Holds cells (Review A Consider); the status file's Remote sync line names PR #17 (Review B Consider).

| Subject | Round | Critic | Blocking | Should fix | Consider | Fixed |
|---|---|---|---|---|---|---|
| TASK-003 | 4 | Review A | 0 | 0 | 4 | deferred (see below) |
| TASK-003 | 4 | Review B | 0 | 0 | 0 | — |

### TASK-003 round 4 — disposition
Both APPROVE; the round-3 fixes confirmed. Merged as f00f12e (2026-10-12). Nothing converged. Review A's four Consider findings are deferred, each to the increment that owns it:
- "the conditional workflows that apply" in the transitional sentence could be read as whole files; it should say "their changes to the current phase" → TASK-010 (the carve), re-pinned there;
- the core's Read-when cell lacks "resume", and the phase modules' cell lacks start and resume, beside rule 28 → reconciled at TASK-010;
- a project-wide addition from a trait two parts share (a run parameter, an intake question): asked once or per part → the TASK-005 and TASK-012 briefs;
- the negative test against the phase-only wording is narrow; the positive pins of the sentence are the guard → no change.

| Subject | Round | Critic | Blocking | Should fix | Consider | Fixed |
|---|---|---|---|---|---|---|
| TASK-004 | 1 | Review A | 1 | 1 | 8 | yes — round 2 (see below) |
| TASK-004 | 1 | Review B | 0 | 3 | 2 | yes — round 2 (see below) |

### TASK-004 round 1 — disposition
Review A REJECT, Review B APPROVE. The split is settled for Review A on the approved plan, an established invariant: BUILD_PLAN TASK-020 scopes `workflow/types/own-computer.md` and its `own-computer/local-service.md`, so the key `software-on-your-own-computer` would put the type workflow at a path the plan does not name. FIX: the key is `own-computer` (the type's row, its four sub-types' Of type, the tests); the workflow name follows the plan's shape, "Own-Computer Software Development".

Three findings converged and were treated as blocking:
1. **Six sub-types' default traits were checked only as a superset** of their type's (Review B Should fix, Review A Consider), though a sub-type's cell is its complete set. FIX: every sub-type is pinned by equality.
2. **§6.10 step 2 asked every new entry for a workflow name** (Review B Should fix, Review A Consider): a trait has none, a sub-type has a sub-workflow name, and "its written flag set" was ambiguous. FIX: the entry joins with every column of its own table; step 3 sets Written to `yes` in the same change, once the check passes.
3. **The §6.7 trait bullet stopped at the promotion pass** (both Consider). FIX: "from which the maintainer may write it as trait additions", as §6.7 says; pinned.

Also fixed:
- **Name and Workflow name both claimed the `Workflows:` line** (Review A Should fix). §6.3 (plan line 216) is kept: the workflow or sub-workflow name is what the line names; Name is plain words for prose and intake; a trait, which has no workflow name, is named by its Name.
- **§6.7 was pinned by its titles only** (Review B Should fix). The pause conditions ("fits no product type, fits two equally, or fits one whose workflow is not yet written"), "stops before design" and the unwritten-trait sentence are pinned.
- **The table shape was implied, not stated** (Review A Consider). "How this file is read" states it: the first table after its heading, rows to the first non-table line, columns by header name, no `|` in a cell, no meaning in the order inside a Default traits cell. The test's parser reads only that first table. The GUI cell is in trait order.
- **The canonical-source sentence named product types only** (Review A Consider). It now covers a type workflow or sub-workflow.
- **An all-`no` test would break on the first written workflow** (Review A Consider). It is replaced by the invariant: Written is `yes` exactly when the file exists at the key's path.
- **The Planned cells outside release B were unpinned** (Review B Consider). Every cell is pinned.
- The status file's Remote sync line names PR #18 (Review A Consider).

Not taken: pinning every definition verbatim (Review A Consider) duplicates the text; the reviewers check the definitions against §6.3 each round. "And its entry here" in the changing paragraph stays: it follows from the file being the canonical source.

Deferred: the `Workflows:` line's grammar (which column names a type, a sub-type and a trait on it, and the bridge's own line rewritten to match) → TASK-007's brief.

| Subject | Round | Critic | Blocking | Should fix | Consider | Fixed |
|---|---|---|---|---|---|---|
| TASK-004 | 2 | Review A | 0 | 1 | 4 | yes — round 3 (see below) |
| TASK-004 | 2 | Review B | 0 | 0 | 0 | — |

### TASK-004 round 2 — disposition
Both APPROVE; round 1's fixes confirmed by both. The first launch of this round (snapshot 004b) gave Review B an empty plan-sections file and was stopped before a verdict (ISS-004); the round ran again whole as 004c. Nothing converged. REVIEWERS DISAGREE on whether the derived workflow and sub-workflow names need pinning (correctness, not intent): Review B accepted the scoped choice to pin only the owner's two, Review A asked for every name. Settled for Review A on §6.3, which calls the names "fixed here": a fixed value is fixed in a test.

Fixed:
- **Only Game Development and Roblox Game were pinned** (Review A Should fix). Every workflow and sub-workflow name is pinned by equality; renaming one changes the file and its pin together.
- The status file's Next named the abandoned 004b (Review A Consider). It names round 3.
- The opening sentence cited the core's "Main and conditional workflows" for classification at intake (Review A Consider); it now points to "When something does not fit" and §6.7.
- §6.10 step 2's colon read as the full column list (Review A Consider); it says "filled, including".
- The test's parser did not compare the separator's cell count with the header's (Review A Consider); it does.

Noted, no change: a key unique within its table is enough, since the three tables are read apart (Review A); the Written flag's "the check passes" half belongs to TASK-006.

| Subject | Round | Critic | Blocking | Should fix | Consider | Fixed |
|---|---|---|---|---|---|---|
| TASK-004 | 3 | Review A | 0 | 0 | 4 | deferred (see below) |
| TASK-004 | 3 | Review B | 0 | 0 | 0 | — |

### TASK-004 round 3 — disposition
Both APPROVE; round 2's fixes confirmed. Review B's first launch (15:10:49Z) was ended at four minutes for the owner's pause and ran again whole on the same head (18:24:01Z, a fresh snapshot). Merged as f40bf82 (2026-10-12). Nothing converged. Review A's four Consider findings, none taken on the reviewed head:
- the §6.10 test pins "Its entry joins this list with every column of its table" but not the "filled, including" that round 2 added, and the test's comment "types with their workflow names where the owner fixed them" is stale now that every name is pinned → `tests/test_open_list.py` is in no later increment's Scope, so both go to release B's stage-close pass, test-infrastructure lane (supervisor.md step 9, 3b), recorded in `docs/HARDENING.md` there;
- the opening paragraph and the paragraph after it both point to "When something does not fit" → wording, in TASK-017, the first increment with `open-list.md` in its Scope;
- the status file listed ISS-004 under Open issues while calling it fixed → its cause is recorded in the Issues document (reproduced: `git show <rev>:<path> --output=<file>` creates the file empty and prints the content to standard output; the plan file is now copied with a redirect and its size checked), and the status file drops it (TASK-005's branch).

| Subject | Round | Critic | Blocking | Should fix | Consider | Fixed |
|---|---|---|---|---|---|---|
| TASK-005 | 1 | Review A | 1 | 3 | 5 | yes — round 2 (see below) |
| TASK-005 | 1 | Review B | 0 | 2 | 1 | yes — round 2 (see below) |

### TASK-005 round 1 — disposition
Review A REJECT, Review B APPROVE. One finding converged and is treated as blocking beside Review A's own.

Blocking:
1. **The delivery kind was set at a point the project-end module declares** (Review A), so a type workflow's `Set at` would first be read at the last stage close, though intake confirms the kind and design and planning act on it (`supervisor.md` Phase 1). FIX: `intake.delivery-kind` (`add, set`) beside `intake.budget-kind`, both stated as refinements of §6.4; `project-end.delivery` holds the procedure for the kind and is `add` only. TASK-014's "project-end declares Delivery" and the type workflows' "sets delivery" (TASK-019, TASK-021) still hold.
2. **`project` Applies against the core's shared-workflow sentence** (converged: Review A Should fix, Review B Should fix): `supervisor.md` says a shared conditional workflow's additions apply to every part that has it, each in its own place; the registry said a `project` addition is made once and did not say where. FIX: the core's order governs every point; its per-part rule is the rule for `part` points; a `project` point is the one exception, made once in the place of the first part, in the status file's order, that has the workflow. The core is to cite this when it is carved (TASK-010, which has `supervisor.md` in its Scope).

Also fixed:
- **What becomes of a replaced module's points** (Review A Should fix): a replacement declares the same points as the module it replaces, so the trait *has screens* still adds the mockup variant to a replaced interface phase (§6.5, "Today's interface conditions stay together"). The check of it → TASK-006's brief.
- **A set at a point that opens no value** (Review A Should fix) is named among what fails the workflow check; → TASK-006's brief, beside its Done when (a)–(f).
- **`configuration.items` was `part`** (Review B Should fix). REVIEWERS DISAGREE (correctness, not intent): Review A called it the author's call and raised nothing; Review B asked for `project`. Settled for Review B on the registry's own definition: Configuration sets up one project environment (`supervisor.md` Phase 5), so a tool two parts share is installed once.
- A completion condition read only at project end could not shape the plan (Review A Consider): one the plan must build toward is also added at intake (`intake.requirement-sources`), so it enters the requirements register.
- The change cycle's module has no `## Extension points` section (Review A Consider), one answer for TASK-014's cross-check.
- The Applies column is pinned whole; the test cites BUILD_PLAN's Scope for the file's path, not §6.11; the `workflow/phases/<module>.md` statement is pinned (Review A Consider).
- An addition at a point that holds a value adds to what is asked or recorded about it, never a second value (Review A Consider).
- "The test step" names where the tests run today, inside step 4 (Inspect) and step 6 (Review B Consider).
- The status file's Remote sync line names PR #19 (Review A Consider).

| Subject | Round | Critic | Blocking | Should fix | Consider | Fixed |
|---|---|---|---|---|---|---|
| TASK-005 | 2 | Review A | 0 | 1 | 3 | yes — round 3 (see below) |
| TASK-005 | 2 | Review B | 0 | 1 | 0 | yes — round 3 (see below) |

### TASK-005 round 2 — disposition
Both APPROVE; round 1's fixes confirmed by both (Review A ran the tests against the round-1 file: the 8 new or changed assertions fail there). Nothing converged. Every finding taken:
- **A delivery addition had no tie to its kind** (Review A Should fix, new with round 1's fix): with `project-end.delivery` add-only, a type workflow's deployment procedure would reach a sub-type that delivers an installer in its place (§6.9; TASK-019), and the trait *installable*'s installer a part whose kind is installation into a host (TASK-021). FIX: each addition there names the kind it is for and applies only to a part of that kind; pinned. → TASK-006's brief, beside round 1's two checks.
- **"The test step" was placed in step 6 as well** (Review B Should fix): the tests run in step 4 (Inspect); step 6 adds the benchmark floor to tests already run (`supervisor.md` step 6 opens so). FIX: the point is the run in step 4, and step 6 is not it; pinned.
- A replacement "declares" the same points without a form to declare them in (Review A Consider): it keeps them, without declaring them again under its `## Replace` heading.
- The core's duty to cite the Applies rule was recorded here only (Review A Consider): it joins the carry list for TASK-010's brief (`run/supervisor/in-flight.md`, copied into the status file's Next at TASK-010).
- A completion condition copied at intake could drift from its original (Review A Consider): the intake addition names that completion condition as its source.

| Subject | Round | Critic | Blocking | Should fix | Consider | Fixed |
|---|---|---|---|---|---|---|
| TASK-005 | 3 | Review A | 0 | 2 | 2 | yes — round 4 (see below) |
| TASK-005 | 3 | Review B | 0 | 0 | 0 | — |

### TASK-005 round 3 — disposition
Both APPROVE; round 2's fixes confirmed by both (each ran the tests against the round-2 file: exactly the 4 new or changed tests fail there). Nothing converged. The gate would have allowed the merge; Review A's two Should fix items are taken first, on this branch, because the registry is in no later increment's Scope (TASK-017 could not repair it without a scope deviation):
- **The benchmark floor had no point** (Review A Should fix, new with round 2's fix): "step 6 … is not this point" left the floor, which the trait *performance budgets* carries (§6.8; TASK-017), with nowhere to be added. FIX: step 6 runs no tests of its own; its benchmark floor is a check at the test step. Review B's correction holds: the tests run in step 4.
- **The delivery kinds came from two lists, and an unset kind was unstated** (Review A Should fix): the registry named §6.4's four, the core's intake confirms the kinds of `Delivery-Conventions.md` §1, and a part no workflow sets a kind for (the TDP's path, TASK-020) would have got no procedure from the trait *installable*. FIX: one list (`installer`, `install-script`, `package`, `web-deployment`, `store-package`, `host-installation`) for both the value set and the kind an addition names; where no workflow sets it, the kind confirmed at intake is the part's kind. → TASK-006's brief (the form of the name), TASK-020's brief (its kind confirmed at intake).
- Where the inspect step's checks fall against the test run (Review A Consider): both sit in step 4, the checks of the diff first, then the tests and the checks that run with them.
- The core has no notion yet of an addition scoped to a delivery kind (Review A Consider): joins TASK-010's carry list beside the Applies rule.

| Subject | Round | Critic | Blocking | Should fix | Consider | Fixed |
|---|---|---|---|---|---|---|
| TASK-005 | 4 | Review A | 0 | 1 | 1 | yes — round 5 (see below) |
| TASK-005 | 4 | Review B | 0 | 0 | 0 | — |

### TASK-005 round 4 — disposition
Both APPROVE; round 3's fixes confirmed by both (each ran the tests against the round-3 file: exactly the 3 new or rewritten tests fail there). Nothing converged. Review A's items taken before the merge, for round 3's reason:
- **The design auditor's pass had no point** (Review A Should fix, round 3's defect class again): "the inspect step's checks are step 4's checks of the diff before the tests run" left out the design auditor, which runs after the tests and which the trait *has screens* moves out of the loop (TASK-017). The cause was the same in rounds 2 to 4: each fix defined the two points by where today's text places a check, and each placement left some check out. FIX: the two points divide every check of an increment between them, wherever the module's text places it: the test step is the test run and the checks that run with it (the benchmark floor among them); the inspect step is every other check or review of the diff before the accept decision, before or after the tests (the design auditor among them). Pinned.
- The kind confirmed at intake is recorded by its key from the list (Review A Consider), so a check reading a part's kind (TASK-006) finds a key.

| Subject | Round | Critic | Blocking | Should fix | Consider | Fixed |
|---|---|---|---|---|---|---|
| TASK-005 | 5 | Review A | 0 | 1 | 4 | yes — round 6 (see below) |
| TASK-005 | 5 | Review B | 0 | 0 | 0 | — |

### TASK-005 round 5 — disposition
Both APPROVE; round 4's fixes confirmed by both (each ran the tests against the round-4 file: exactly the 2 rewritten tests fail there). Nothing converged. Review A's items taken before the merge, for round 3's reason:
- **The stage refactoring pass fell outside both points** (Review A Should fix): "every check of an increment … before the accept decision" left out step 9's per-candidate inspection and test run and its single gate pass, where the design auditor also runs, so the trait *has screens*'s addition (TASK-017) would not have reached a screen project's refactoring. FIX: the two points divide every check and review the loop makes of a change, whatever the change is (an increment, a fix, a refactoring candidate, the gate pass of a stage's refactoring branch); the merge gate's conditions (step 8) belong to the core and offer no point, and a CI check a conditional workflow needs is added at `configuration.items`. With no qualifier left on either point, the placement class of rounds 2 to 5 is closed.
- "Of the diff" narrowed the inspect point (Review A Consider): dropped; the triage of the builder's assumptions, the secret scan and the dependency admission are named there.
- "Today both sit inside step 4" contradicted the new definition (Review A Consider): replaced by where an addition is placed (at the step that runs it).
- The pin of round 2's correction was lost in round 5's rewrite (Review A Consider): "step 6 runs no tests of its own, the tests having run in step 4" is pinned again.
- Where the confirmed kind's key is recorded (Review A Consider) is a later increment's design: → TASK-006's and TASK-011's briefs.

| Subject | Round | Critic | Blocking | Should fix | Consider | Fixed |
|---|---|---|---|---|---|---|
| TASK-005 | 6 | Review A | 0 | 0 | 3 | not taken on the reviewed head (see below) |
| TASK-005 | 6 | Review B | 0 | 0 | 0 | — |

### TASK-005 round 6 — disposition
Both APPROVE; round 5's fixes confirmed by both. Nothing converged. Merged as 82f0e44 (2026-10-12) on Consider findings only; Review A's three, none taken on the reviewed head:
- "every check and review" reads against the merge gate's conditions, which the same paragraph exempts → wording only; the exemption stands two sentences later in the same paragraph, so nothing is ambiguous for a check.
- an addition whose check runs at several steps (a check repeated before and after the tests) has no stated placement → TASK-010's brief (the core's carry list) and TASK-017's (the trait *has screens*, whose design auditor is the case).
- three statements are unpinned: the CI route through `configuration.items`, the members named at the inspect step, and the placement sentence → `tests/test_extension_points.py` is in no later increment's Scope, so they go to release B's stage-close pass, test-infrastructure lane, beside TASK-004 round 3's two.

| Subject | Round | Critic | Blocking | Should fix | Consider | Fixed |
|---|---|---|---|---|---|---|
| TASK-007 | 1 | Review A | 0 | 1 | 6 | yes — round 2 (see below) |
| TASK-007 | 1 | Review B | 0 | 0 | 1 | yes — round 2 (see below) |

### TASK-007 round 1 — disposition
Both APPROVE (each ran the new tests against origin/main's text: 8 of 9 fail there, the ninth testing the checker alone). Nothing converged. The gate would have allowed the merge; the items are taken first because TASK-008's builder writes its check from this paragraph:
- **The part prefix "begins a line"** (Review A Should fix) while the grammar puts it after `Workflows: `: a literal reading would accept `<part>: Workflows: …`. FIX: it follows `Workflows: `; the checker refuses the prefix before it.
- What the grammar left open for a check (Review A Consider): a part's name contains no `:`, `;` or `→`; with several parts the lines stand together after `Phase:` in the parts' order, the order the core's "for each part in the order the status file lists them" reads; the line carries the traits proposed at intake and is rewritten at the design gate if they changed.
- The pause had no time anchor (Review A Consider): it is at intake (§6.7). Every entry of the open list is still unwritten, the bridge's own type included, so TASK-008's check reads the line's form and the names' membership, never the Written flag, and its brief says which copy of the open list it reads → TASK-008's brief (the carry list).
- The checker's refusals were asserted without their reason, and some paths were unexercised (Review A Consider); the out-of-order sample was also out of alphabetical order, so an alphabetical sort would have passed (Review B Consider). FIX: each refusal names its fault; repeated traits, an unknown sub-workflow name, a prefixed `not yet classified`, and a pair alphabetical order accepts but the Traits table does not are added; the bridge's own line is checked to stand right after `Phase:`.
- The status file's Remote sync and Next lines were stale (Review A Consider): PR #20 is named, and TASK-008 beside TASK-009.
- task-002's status copy still carries the old form of the line (Review A Consider): when main is merged into task-002, the status file takes main's form (the step is in the supervisor's position file).
- The plan excerpt the reviewers read began at §6.3 (Review A Consider): round 2's excerpt carries §6.1–6.2 as well.

| Subject | Round | Critic | Blocking | Should fix | Consider | Fixed |
|---|---|---|---|---|---|---|
| TASK-007 | 2 | Review A | 0 | 0 | 5 | not taken on the reviewed head (see below) |
| TASK-007 | 2 | Review B | 0 | 0 | 1 | not taken on the reviewed head (see below) |

### TASK-007 round 2 — disposition
Both APPROVE; round 1's fixes confirmed by both (each ran the round-2 test against round 1's text: the 2 rewritten pins fail there). Nothing converged. Merged as d4023f6 (2026-10-12) on Consider findings only, none taken on the reviewed head; the paragraph moves with "Project state" in TASK-010, which takes the wording:
- the parts' order is defined by the status file itself, which the sentence states in a circle; and "beside `Phase:`" for one part against "right after `Phase:`" for several (Review A) → wording, TASK-010.
- part names are not required to be distinct (Review A); each trait appearing at most once is checked but not stated (Review B) → TASK-010 states both; TASK-008's brief checks both.
- "At intake" names only one of the times a pause can happen: the workflow check also fails a line at a release and at a calibration (§6.6, §6.8) (Review A) → TASK-006's and TASK-024's briefs.
- a change cycle that changes a part's traits, or adds a part, rewrites the line, which the paragraph does not say (Review A) → the brief of the increment that writes the change-cycle module.

| Subject | Round | Critic | Blocking | Should fix | Consider | Fixed |
|---|---|---|---|---|---|---|
| TASK-002 | re-review 002c (main merged in) | Review A | 0 | 2 | 4 | yes — round 6 (see below) |
| TASK-002 | re-review 002c (main merged in) | Review B | 0 | 1 | 2 | yes — on the same branch |
| TASK-002 | 6 | Review A | 0 | 2 | 2 | routed (see below) |
| TASK-002 | 6 | Review B | 0 | 0 | 0 | — |

### TASK-002 — disposition of its last rounds
Rounds 1 to 5 and why the floor took six builder rounds are in the Issues document (ISS-002, ISS-005). The re-review of the head that took main in (002c): both APPROVE. Review A's Should fix, the Socket CLI's banner printing 5 characters of the key into CI logs, was raised to Blocking because the repository is public → round 6 (`socket ci --no-banner`, the supervisor's test `test_r002_socket_prints_no_banner`); Review B's Should fix, the inventory's spending-limit wording, fixed on the branch. Round 6: both APPROVE. Review A's two Should fix (the test's docstring citation; the inventory's reword of what the 5 characters are and the remedy) and its Considers (the guard over every job; a stale working file) went to stage B1's close, where they were taken (BUG-001). Merged as fba63bc (2026-10-13).

| Subject | Round | Critic | Blocking | Should fix | Consider | Fixed |
|---|---|---|---|---|---|---|
| Stage B1 | 1 | Review A | 2 | 5 | 5 | BUG-001 and the owner's run sheet (see below) |
| Stage B1 | 1 | Review B | 1 | 3 | 1 | BUG-001 (see below) |

### Stage B1 review round 1 — disposition (2026-10-16)
Both REJECT. Converged (both reviewers): the status file on main was stale, describing PR #16 as unmerged; the stage tests were weak (the Deferred check, no trigger check); the Socket key was in the environment while npm installed the CLI (Review A Should fix, Review B Consider: blocking by convergence). Taken in BUG-001:
- **The status file and the inventory** (both, Blocking): the status file is current and self-sufficient; the inventory records the required check, the Socket file coverage, the full-tree audit and the fork rule.
- **Three logs still show part of the key** (Review A, Blocking): runs 38241764324, 38244794839 and 38309209568 survived the owner's deletion of 2026-10-13. The supervisor counted the banner lines in the logs of every run since 2026-10-12 without printing them: these three hold one each, no other run holds any. Deleting them and replacing the key are the owner's; asked with a run sheet 2026-10-16. The stage's review is repeated after the owner reports back.
- **The key beside npm install** (converged): the CLI is installed in a step without the key, with `--ignore-scripts` (builder, BUG-001); the supervisor's tests pin it.
- **The stage tests** (both): the Deferred check parses rows (fails on a settled decision or an undated deferral, allows TASK-027's dated one); the phase is compared with project.json; the triggers, each scanner's exit deciding its step, the OSV lockfile argument, the lock's exact closure, `; true` in the disabler guard, --no-banner in every job are pinned.
- **No full-tree Semgrep scan** (Review A Should fix): run once on 2026-10-16 with CI's rulesets — one finding, the shim's `chmod 0o755`, accepted with its reason; re-run at each release (INVENTORY Decisions).
- **Does Socket read requirements.lock** (Review A Should fix): Socket's supported-file list matches `requirements{.bazel,}.lock` for PyPI; the dashboard listing is a least-confident check in docs/HARDENING.md.
- Considers: the unpinned Semgrep rule packs and the unused Semgrep token → docs/HARDENING.md leads; forks get no secrets → a Decision; the stale mutation driver → updated (run/supervisor/mutate_ci_floor.py); the stage label and R-002's merge commit → project.json and the register.

| Subject | Round | Critic | Blocking | Should fix | Consider | Fixed |
|---|---|---|---|---|---|---|
| BUG-001 | 1 | Review A | 0 | 1 | 6 | yes — on the branch (see below) |
| BUG-001 | 1 | Review B | 0 | 4 | 1 | yes — on the branch (see below) |

### BUG-001 round 1 — disposition (PR #21)
Both APPROVE; the builder's change matches the brief; CI on the head shows the CLI installed without scripts (24 packages), the scan run, no banner. Converged, so taken as blocking: `--ignore-scripts` matched as a substring (`--ignore-scripts=false` passed; Review B Should fix, Review A Consider) and a deferral passed on any date in its row (Review B Should fix, Review A Consider). FIX in the supervisor's tests: the flag matched whole; a secret found in any expression form (`secrets.X` and `secrets['X']`, Review B); the install pattern widened to `npm ci`, `npx`, `pip3`, `uv`, `go`/`gem`/`cargo install` (Review A); the CLI held at its recorded 1.7.0 (Review A); `pull_request` must run on open, update and reopen (`types: [closed]` passed, Review B); a deferral needs the owner named with a date in its decision cell. Driver: 35 mutants, all killed, the six new ones among them. Records: HARDENING's npm lead said the dependencies run "without the key in reach", true at install only — reworded for scan time (Review A Should fix); the runner-image date marked unconfirmed (Review A); the status file names PR #21 and what lives in `run/supervisor/` (Review A); this record's wording on the three logs (Review B). The bridge's own CI guidance lacking `--no-banner` and the keyless install (Review A Consider) → FB-007, widened. The diff file's trailing whitespace (Review B Consider) is the diff's own content, not taken.

| Subject | Round | Critic | Blocking | Should fix | Consider | Fixed |
|---|---|---|---|---|---|---|
| BUG-001 | 2 | Review A | 0 | 2 | 5 | yes — on the branch (see below) |
| BUG-001 | 2 | Review B | 1 | 0 | 0 | yes — on the branch (see below) |

### BUG-001 round 2 — disposition (PR #21)
Review A APPROVE, Review B REJECT. Converged (Review B Blocking, Review A Consider): `--ignore-scripts --ignore-scripts=false` passed while npm takes the last setting. FIX: an npm install line's one mention of the setting must be the bare `--ignore-scripts`; no env at any level sets npm's ignore-scripts config; npm's install and clean-install aliases (`add`, `isntall`, `clean-install`, …) are all checked. Review A's Should fix: an open "yes" naming the owner and a date passed — the row rule now follows the template (`<yes — the question · no>`) and completion-check's owner-dated convention: a deferral reads `no` in its decision cell and names the owner with a date in the row, and an open question waits on the status file's Awaiting line (this also answers Review A's Consider that a template row failed); `${{ toJSON(secrets) }}` passed — the secret pattern now matches any expression reading the secrets context. Considers taken: `uvx`, `pnpm dlx`, `yarn dlx`, `bunx` in the install pattern; a self-test of the secret and install patterns; HARDENING's npm lead says its settle changes the pin test. The driver counts only an assertion as a kill (a crash is reported), and holds 41 mutants, all killed; the round-2 SCOPE file's stale count is replaced by round 3's.

| Subject | Round | Critic | Blocking | Should fix | Consider | Fixed |
|---|---|---|---|---|---|---|
| BUG-001 | 3 | Review A | 0 | 3 | 4 | yes — on the branch (see below) |
| BUG-001 | 3 | Review B | 2 | 0 | 0 | yes — on the branch (see below) |

### BUG-001 round 3 — disposition (PR #21)
Review A APPROVE, Review B REJECT; both blocking items converged with Review A's own findings. **A weakening:** round 3's secret pattern stopped at the first `}`, so `${{ format('{0}', secrets.X) }}` passed where the substring check on main had caught it (Review B Blocking, Review A Should fix). FIX: the pattern reads each expression to its closing `}}`, keeps the bare `secrets.X` / `secrets['X']` form, and adds `github.token`. **A continuation:** `--ignore-scripts` followed by `--ignore-scripts=false` on a backslash-continued line passed (Review B Blocking, Review A Consider). FIX: commands are read with their continuations joined. Review A's other findings: `--ignore-scripts false` (npm reads a bare value after a boolean flag) is refused; a deferral's decision cell may read `no — the owner, <date>` (it begins `no`, and the owner and date are looked for across the row); the records no longer say a template row passes — this project narrows the template's `<yes — the question · no>`, an open question waits on the status file's Awaiting line (the round-2 disposition's "also answers Review A's Consider" overstated it); the env check refuses only a value that is not `true`, so a workflow-level `npm_config_ignore_scripts: 'true'` passes, and its mutant is named for what it proves; the undated-row mutant now reaches the owner-and-date check; npm options before the command (`npm -g install`), `npm exec`, `npm it`. Driver: 47 mutants, all killed by an assertion; stage tests 26.

| Subject | Round | Critic | Blocking | Should fix | Consider | Fixed |
|---|---|---|---|---|---|---|
| BUG-001 | 4 | Review A | 0 | 3 | 5 | yes — on the branch (see below) |
| BUG-001 | 4 | Review B | 4 | 0 | 0 | yes — on the branch (see below) |

### BUG-001 round 4 — disposition (PR #21)
Review A APPROVE (nothing weaker than on main); Review B REJECT with four new bypasses of the structural test: an early `exit 0` in the Semgrep step, `code=0` after OSV's status, a secret handed to a third-party action step, `npm --prefix /x install` in the step holding the key. **REVIEWERS DISAGREE** on whether further bypasses of the structural test block (Review A: tail; Review B: blocking) — a correctness crux, settled by the supervisor. Every round since stage B1's review has found new ways past pattern checks of shell inside YAML while the CI change itself has been approved in every round: the tail of one hard subsystem, and a pattern check of it never ends. Decision: stop pattern-matching the floor and pin it. `test_r002_floor_job_is_the_pinned_one` compares the `security floor` job, every step verbatim, with a committed copy, so a skipped scanner, an overwritten status or an added step fails unless the same diff changes the pin, where both reviewers read it (§Anti-gaming); `test_r002_one_step_holds_a_secret` allows exactly one step in the whole workflow to refer to a repository secret, the Socket scan. These close all four of Review B's findings and Review A's chained second install. The pattern checks stay as a second line for the other job and later steps, tightened where cheap: chained commands split at `&&`, `||`, `;`, `|`; npm options with a separate value (`--prefix /x`), `cit`, `update`; expression names case-insensitive, `github['token']`; the job token kept apart from the step-env rule, so `with: token: ${{ github.token }}` stays allowed (Review A Should fix); a deferral names the owner and a date in either order; the env docstring says `true` or `1`. The mutation driver now counts a kill only when the named assertion fired (three mutants had been killed by the version pin, Review A Should fix; they now add a line beside the intact pinned install); 53 mutants, all killed. The remaining forms the patterns do not model (installs by pnpm or yarn without a script check) are moot for the pinned job and recorded in docs/HARDENING.md.

| Subject | Round | Critic | Blocking | Should fix | Consider | Fixed |
|---|---|---|---|---|---|---|
| BUG-001 | 5 | Review A | 0 | 1 | 3 | yes — on the branch (see below) |
| BUG-001 | 5 | Review B | 2 | 0 | 0 | yes — on the branch (see below) |

### BUG-001 round 5 — disposition (PR #21)
Review A APPROVE, Review B REJECT, on the same two gaps (converged): the job pin did not cover the workflow's top level, so a workflow-level `defaults: run: shell: "true {0}"` skipped the Socket step with every test green (and a workflow `env:` could set a registry, NODE_OPTIONS or BASH_ENV); and a reusable-workflow job with `secrets: inherit` passed the one-secret rule. FIX: `test_r002_workflow_is_the_pinned_one` pins the whole workflow verbatim (every top-level key and every job), so any change to `.github/workflows/tests.yml` must change the pin in the same diff; the one-secret rule also refuses a job that passes secrets on. Considers: the round-5 SCOPE file's stale count (replaced by round 6's); the deferral docstring says the either-order rule differs from completion-check's register convention. Driver: 56 mutants, all killed by the named assertion. **Consequence for later increments:** an increment that changes the workflow (TASK-006 adds the workflow check to CI) regenerates `WORKFLOW_PIN` in the same diff; its brief says so, and the reviewers read the pin's change as the workflow's.

| Subject | Round | Critic | Blocking | Should fix | Consider | Fixed |
|---|---|---|---|---|---|---|
| BUG-001 | 6 | Review A | 0 | 1 | 2 | Should fix on the follow-up branch (see below); Considers to HARDENING |
| BUG-001 | 6 | Review B | 0 | 0 | 0 | — |

### BUG-001 round 6 — disposition (PR #21, merged 6743b25)
Both APPROVE; Review A confirmed `WORKFLOW_PIN` equals the committed workflow and nothing is weaker than on main. Should fix (Review A alone, not converged): the pin and the one-secret rule read `tests.yml` only, so a second file under `.github/workflows/` could hand the key to an install and still merge with every test green (the tests guard the merge, not that pull request's own CI run; HARDENING) — the edge of what the pin covers, not a bypass of it, and a new file that scope-check lists and every reviewer reads. By-class line: merged, and fixed on the follow-up branch before stage B1's review runs again: `test_r002_workflow_is_the_only_one` requires the workflow folder to hold the pinned workflow alone (driver mutant: a second workflow beside it; 57 mutants, all killed). Considers, to docs/HARDENING.md: PyYAML (YAML 1.1) and GitHub's parser read some spellings differently; the scanners' own configuration files sit outside the pin.

| Subject | Round | Critic | Blocking | Should fix | Consider | Fixed |
|---|---|---|---|---|---|---|
| BUG-001 follow-up (PR #22) | 1 | Review A | 0 | 1 | 2 | yes — on the branch |
| BUG-001 follow-up (PR #22) | 1 | Review B | 0 | 0 | 1 | yes — on the branch |

### BUG-001 follow-up round 1 — disposition (PR #22)
Both APPROVE; both named the status file's stale Remote sync line (converged, so blocking): fixed. Review A's Considers: the bridge's own Semgrep rules file added to the scanner-configuration lead; a new lead that the structural tests guard the merge and not a pull request's own CI run (the key in a GitHub Environment, or on pushes to main only), and round 6's disposition reworded so it does not read as preventing that.

| Subject | Round | Critic | Blocking | Should fix | Consider | Fixed |
|---|---|---|---|---|---|---|
| BUG-001 follow-up (PR #22) | 2 | Review A | 0 | 0 | 1 | yes — on TASK-006's branch (HARDENING) |
| BUG-001 follow-up (PR #22) | 2 | Review B | 0 | 0 | 0 | — |

### BUG-001 follow-up round 2 — disposition (PR #22, merged 4d0f77b)
Both APPROVE. Review A's Consider (the HARDENING lead on the key's reach should state what each remedy costs the owner) is written on TASK-006's branch.

### TASK-006 — the brief's decisions (the supervisor, 2026-10-16)
- Carry item 5 (where a part's delivery kind is recorded so a check can read it): no as-built text records it in a readable form, and none of the check's rules needs it; out of TASK-006's scope, carried to TASK-011's brief (intake), where the kind is confirmed.
- Carry item 4 read with the registry: an addition at `project-end.delivery` must name its kind (`## Add at project-end.delivery for <kind>`); the kind confirmed at intake is a part's kind where no workflow sets one, never an addition's.
- A type or sub-workflow's statement of its default traits has no form yet, so it is not checked (the open list's promise stands for the increment that gives it a form); the guard against a conditional workflow's sentence contradicting the core is a reading, not a check: it is the reviewers' (both reviewers of every increment that writes a conditional workflow).
- The tests and the fixtures are the supervisor's, written before the delegation from the brief's interface; the builder's report found one test that renamed the prose citation of a heading rather than the heading, fixed by the supervisor; the mutation driver (30 mutants) found the missing-kind test not naming its offending name, tightened.

| Subject | Round | Critic | Blocking | Should fix | Consider | Fixed |
|---|---|---|---|---|---|---|
| TASK-006 | 1 | Review A | 1 | 1 | 8 | yes — round 2 (handoff/TASK-006-r2.md) |
| TASK-006 | 1 | Review B | 2 | 1 | 1 | yes — round 2 |
| TASK-006 | 1 | security auditor | 0 | 5 advisory | — | yes — round 2 |

### TASK-006 round 1 — disposition (PR #23)
Converged, so blocking: a misspelt change word (`## Adds at`) read as prose, so the change silently did nothing (Review A and Review B; the brief contradicted itself, its example right and its definition wrong: the definition now names the change words case-insensitively, or `at` as the second word); a trait list without its `, ` separator accepted (Review B blocking, Review A Consider); an unreadable folder skipped silently (all three). Also taken in round 2: a byte-order mark hid a first-line heading, so a trait's set escaped (b) (Review A Should fix); an invalid single-line prefix checked further (Review B Should fix); links and junctions followed out of the root, control characters printed raw (a newline in a file name could start a GitHub workflow command), quadratic section search, a docstring slip (the auditor); the separator row unchecked, a repeated unwritten trait flagged twice, an empty head name reported as unknown, a usage error without its RESULT line (Review A Considers); the constraint on hard-coded keys now names the two delivery point keys. The supervisor's side: the usage test now looks for each code as printed; the mutation driver gained the rules it lacked (Review A C8) and round 2's, 49 mutants, all killed.

| Subject | Round | Critic | Blocking | Should fix | Consider | Fixed |
|---|---|---|---|---|---|---|
| TASK-006 | 2 | Review A | 0 | 2 | 4 | yes — round 3 (handoff/TASK-006-r3.md) |
| TASK-006 | 2 | Review B | 1 | 2 | 0 | yes — round 3 |
| TASK-006 | 2 | security auditor | 0 | 2 advisory | — | yes — round 3 |

### TASK-006 round 2 — disposition (PR #23)
Every round-1 finding was confirmed settled by probes (Review A, Review B and the auditor each ran their own). Review B blocked on the usage error's message, written to standard error unescaped (an argument holding a newline could start a GitHub workflow command): escaped (R3-1). Also taken, each a remaining way for input to pass unseen: a separator row with the wrong cell count (Review B); a link inside an unknown type folder, and a dangling or top-level link at `types`/`traits` (Review B, the auditor); a change word with punctuation attached (`## Set:`, so a trait's set escaped again) and `adding`/`setting` (Review A); whitespace around a part name, so `app` and `app ` counted as two parts (Review A; round 2's rewrite had dropped round 1's check); an unclosed fence hiding every later heading, and headings indented up to three spaces or with a tab (Review A Consider); junctions unseen on a Python without `os.path.isjunction` (the auditor). On the supervisor's side: a negative test without its precondition replaced by one that would fail if the misspelt section were read (Review A Consider), tests for links at the top level and under an unknown folder, and the driver's mutants for round 3's rules (59, all killed). Not taken, recorded: prose headings that R2-1 now fails (`## Set up the host`, `## Notes at intake`) fail loudly, the safe direction; the authors of the first written type and trait workflows are told by the registry's naming section when they are written (the increments that write them).

| Subject | Round | Critic | Blocking | Should fix | Consider | Fixed |
|---|---|---|---|---|---|---|
| TASK-006 | 3 | Review A | 1 | 0 | 3 | yes — round 4 (handoff/TASK-006-r4.md); one Consider to HARDENING |
| TASK-006 | 3 | Review B | 0 | 0 | 0 | — |
| TASK-006 | 3 | security auditor | 0 | 2 advisory | — | yes — round 4 |

### TASK-006 round 3 — disposition (PR #23)
Review B approved with no findings; every round-2 finding was confirmed settled by the three reviewers' own probes. Review A blocked, and the auditor's first advisory named the same defect (convergence, so blocking): R3-7's fallback, as the brief worded it, counted a path that does not exist as a link, so on a Windows Python without `os.path.isjunction` a root lacking `types/` or `traits/` (the bridge's own workflow folder) failed as `form`. The cause was the brief (R3-3's link-before-folder order with R3-7's every-OSError-is-a-link), and the supervisor's test called `is_link` only on paths that exist. Taken in round 4: a missing layer path is skipped and a missing path is not a link on either branch (R4-1); the isjunction branch follows the same error rule (R4-2, the auditor's second advisory); fences indented up to three spaces are fences, so a trait's `## Set` can no longer escape between indented fences (R4-3, Review A Consider 1). On the supervisor's side: tests that run `main()` in-process with isjunction removed over the bridge's own folder and a root without `traits/`, error-policy tests for both branches, four fence fixtures, and driver mutants for each rule. Not taken, recorded in HARDENING by the by-class line (the long tail of heading parsing; the core is correct): change words wrapped in markup (Review A Consider 2); reparse-point results that differ by Python version (Review A Consider 3).

| Subject | Round | Critic | Blocking | Should fix | Consider | Fixed |
|---|---|---|---|---|---|---|
| TASK-006 | 4 | Review A | 0 | 0 | 2 | yes — round 5 (handoff/TASK-006-r5.md) |
| TASK-006 | 4 | Review B | 0 | 0 | 0 | — |
| TASK-006 | 4 | security auditor | 0 | 2 advisory | — | yes — round 5 |

### TASK-006 round 4 — disposition (PR #23)
All three approved, and every round-3 finding was confirmed settled by probes. Review A's Consider 1 and the auditor's second advisory named the same defect independently, so it blocked (convergence): the fence rule toggled on any fence-like line, so a four-backtick fence closed on a line of three, a backtick line with text after it closed a fence, and tilde fences were not fences, which let a trait's `## Set` sit between two such lines unseen (the case existed before round 4; R4-3 widened it slightly). Taken in round 5: fences as CommonMark reads them (R5-3). Also taken, since round 5 runs anyway: the auditor's first advisory, that R4-2's error rule on the `os.path.isjunction` branch can never run (CPython's `isjunction` catches its own errors), by one `os.lstat` rule on every Python (R5-2), which also ends round 3's Consider 3 (results that differed by Python version); and Review A's Consider 2, that on POSIX a root whose layer folders cannot be examined was checked as empty and passed, by examining each layer with `os.lstat` and stopping the check on an error other than a missing path (R5-1), which replaces the round-4 HARDENING line about `lexists`. Not taken, recorded in HARDENING: a fence inside an HTML `<pre>` block (the auditor).

| Subject | Round | Critic | Blocking | Should fix | Consider | Fixed |
|---|---|---|---|---|---|---|
| TASK-006 | 5 | Review A | 0 | 0 | 3 | partly — round 6 (handoff/TASK-006-r6.md); one to HARDENING |
| TASK-006 | 5 | Review B | 1 | 0 | 0 | yes — round 6 |
| TASK-006 | 5 | security auditor | 0 | 4 advisory | — | partly — round 6; three to HARDENING |

### TASK-006 round 5 — disposition (PR #23)
Every round-4 finding was confirmed settled by probes, R5-3 against a CommonMark reference (markdown-it). Review B blocked: `cells_of` stripped every pipe at a row's ends, so a row ending `||` lost an empty cell and a row with the wrong cell count passed (R6-1). Review A's Consider 1 and the auditor's first advisory named the same defect, so it blocked (convergence): lines were split at form feed, vertical tab, NEL, U+2028 and other characters Markdown does not end a line at, so two fence lines joined to text by one could hide a heading (R6-2). On the supervisor's side: a pass-root block pinning that a backtick in a tilde fence's info string still opens the fence (Review A's test gap; the other two gaps it named are cosmetic or unreachable). Review A's Consider 2 and the auditor's second advisory also named one class together, fences and headings inside container blocks (list items, block quotes): both graded it for recording by class rather than a fix, and the supervisor agrees: it is the tail of heading parsing the by-class line was drawn under at round 3, files under `types/` and `traits/` are written by the bridge's own maintainer and supervisor, and modelling CommonMark's containers is a parser, not a check; recorded in HARDENING with the auditor's third and fourth advisories (headings inside containers; any HTML block, not only `<pre>`).

| Subject | Round | Critic | Blocking | Should fix | Consider | Fixed |
|---|---|---|---|---|---|---|
| TASK-006 | 6 | Review A | 0 | 0 | 1 | to HARDENING (by-class line) |
| TASK-006 | 6 | Review B | 0 | 0 | 0 | — |
| TASK-006 | 6 | security auditor | 0 | 2 advisory | — | to HARDENING (by-class line) |
| TASK-008 | 1 | Review A | 1 | 1 | 3 | REJECT: the blocking and should-fix items are the supervisor's tests, fixed at the round 2 checkpoint |
| TASK-008 | 1 | Review B | 0 | 0 | 0 | — |
| TASK-008 | 1 | security auditor | 0 | 4 advisory | — | one convergent with Review A (blocking), two to round 2, one to HARDENING |
| TASK-008 | 2 | Review A | 0 | 2 | 3 | APPROVE; all five are the supervisor's tests, added on task-009 |
| TASK-008 | 2 | Review B | 0 | 0 | 0 | — |
| TASK-008 | 2 | security auditor | 0 | 0 | — | — |
| TASK-009 | 1 | Review A | 3 | 2 | 5 | REJECT; all ten taken in round 2 |
| TASK-009 | 1 | Review B | 2 | 2 | 0 | REJECT; all four taken in round 2 (each converges with Review A) |
| TASK-009 | 2 | Review A | 1 | 1 | 3 | REJECT; the blocking item, the should-fix and two considers taken in round 3, one consider to HARDENING |
| TASK-009 | 2 | Review B | 0 | 1 | 0 | APPROVE; the should-fix taken in round 3 |
| TASK-009 | 3 | Review A | 0 | 0 | 3 | APPROVE; the three considers taken in round 4 |
| TASK-009 | 3 | Review B | 1 | 0 | 0 | REJECT; taken in round 4 |
| TASK-009 | 4 | Review A | 1 | 1 | 3 | REJECT; all taken in round 5 |
| TASK-009 | 4 | Review B | 1 | 0 | 0 | REJECT; converges with Review A's should-fix; taken in round 5 |
| TASK-009 | 5 | Review A | 0 | 1 | 2 | APPROVE; all taken in round 6 |
| TASK-009 | 5 | Review B | 1 | 0 | 0 | REJECT; converges with Review A's should-fix; taken in round 6 |
| TASK-009 | 6 | Review A | 0 | 0 | 3 | APPROVE; the three considers taken in the post-merge records |
| TASK-009 | 6 | Review B | 0 | 0 | 0 | APPROVE |
| REFAC-B2 | 1 | Review A | 0 | 3 | 3 | APPROVE; S1 converges with Review B's should-fix (blocking); all three should-fix and two considers taken in round 2 |
| REFAC-B2 | 1 | Review B | 0 | 1 | 0 | APPROVE; the should-fix converges with Review A's S1; taken in round 2 |
| REFAC-B2 | 2 | Review A | 0 | 1 | 1 | APPROVE; both taken in the post-merge records |
| REFAC-B2 | 2 | Review B | 0 | 0 | 0 | APPROVE |

### TASK-006 round 6 — disposition (PR #23, merged)
All three approved; R6-1 and R6-2 were confirmed by probes at every site, against a CommonMark reference. The remaining findings are the long tail of reading Markdown-like text, in files only the maintainer and the supervisor write, and the by-class line drawn at round 3 holds: Review A's Consider (a heading or `Workflows:` line after a form feed or line separator is now invisible to the check, as to Markdown, though a raw-text reader would see it) and the auditor's two advisories (cells trimmed of any Unicode whitespace rather than spaces and tabs, so a separator followed by such a character is accepted where Markdown shows no table; an escaped pipe inside a cell split as a boundary) are recorded in HARDENING. They are different defects, not one named twice, so convergence does not apply. Carried to TASK-008's brief: any reader of the `Workflows:` line splits lines exactly as `workflow-check.py`'s `file_lines` does.

### TASK-008 round 1 — disposition (PR #24)
Review B approved; the security auditor passed with four advisories; Review A rejected. Its blocking finding was the supervisor's: the tests that unwritten types and traits are not malformed ran against the live open list, which TASK-017 and TASK-021 will mark written, after which they would assert nothing; they now run on a bridge copy whose open list marks every entry unwritten, with the f/FLAG precondition asserted. Its should-fix (two of Requirement 2's four not-checked causes untested) became six not-loadable cases in both programs. Convergent: Review A (Consider) and the auditor (advisory) both named the `__pycache__` that loading the checker writes beside the installed programs, against conformance-check's "Never writes"; two reviewers on one defect make it blocking → R2-1, no bytecode while loading. Taken into the same round as cheap fail-closed fixes: the auditor's `field()` fallback to the raw value (R2-3) and `abspath` for the checker's folder (R2-2), Review A's SystemExit at load (R2-4). Recorded in HARDENING: names echoed from the status file can carry text such as `RESULT: OK` on one output line (no line can be forged; readers use the last line or the exit code, and the supervisor's conformance test now reads the last line); `Workflows: not yet classified` passes indefinitely (the design: intake classifies, calibration adds the line, TASK-023); a `.pyc` already in the bridge folder is still read (the existing `bridge_env` class, needs write access to the bridge).

### TASK-008 round 2 — disposition (PR #24, merged as bcd3bb4)
All three approved; R2-1 to R2-4 confirmed in both programs, byte-identical. CI green on the pushed head (ubuntu 1113 passed, 26 skipped; windows 1117 passed, 22 skipped); R2-2, whose tests skip on Windows without the link privilege, was observed under Linux (WSL Ubuntu 24.04) on the merged head: through a link, the real code loads the checker beside its real file and an abspath mutant loads the one beside the link. Review A's five remaining items were all gaps in the supervisor's tests, not the code, so they did not hold the merge; they are added on task-009 and reviewed in its gate: the no-bytecode test also drops PYTHONPYCACHEPREFIX, checks that each run judged the line, and carries a positive control; a check that exits after a successful load is a not-loadable case; the no-escape-field cause names AttributeError; the symlink test fails on a crash; the bytecode switch's restore is tested in-process. The driver gained the two mutants Review A named (SystemExit after load, the switch not restored).

### TASK-009 round 1 — disposition (PR #25)
Both reviewers rejected; no security auditor (glossary text and tests, no program logic). Four items converged: the Sub-workflow name entry contradicted open-list.md's Names (a sub-workflow is named for the kind of product, not the work); the Open list entry gave traits default traits and a workflow name; the glossary test's own-term check compared one word against multi-word terms; the no-bytecode test's inventory half could pass on a run that never judged the line. Review A's other blocking items: Phase (the status value, "the only meaning") collided with Phase module (ten procedure files, several not Phase values) against the glossary's one-term rule, now the Phase entry points to phase modules and Phase module is a registry-listed procedure file selected by the phase's value; Main workflow core is today the non-phase sections of supervisor.md, not the whole file. Its should-fix (the compaction-survival list claimed what the hook names) and considers (Phase list bound both ways to the template, Sub-type as a narrower kind, Extension point vs replacement, add/replace/set scoped as kinds of change) were all taken; none needed a resolution round. Probes after the fix: a multi-word tautology, a ninth phase value and a reordered list each fail the glossary test.

### TASK-009 round 2 — disposition (PR #25)
Review B approved; Review A rejected, with all ten of its round 1 items resolved. Its blocking item: the Phase module entry's "planning and building each take two" contradicted TASK-015's table (building takes three at the last stage close, changing four) and read as the complete list; the count is gone, the entry says several phases take more than one, as the session-start hook's table maps them. Its should-fix: the status file's Terms fixed senses of phase module and extension point no longer matched the glossary; both are realigned and marked for re-anchoring at the next report. Considers taken: project end is today part of the Reflection points section; the core is the sections other than those that are phase modules. To HARDENING: extension-points.md's Phase column and two sentences of the core use "phase" in the module sense, a lead for TASK-010 and TASK-014, which rewrite them. Review B's should-fix: the own-term check now strips Markdown emphasis and code marks, so a bold-wrapped tautology fails (probed).

### TASK-009 round 3 — disposition (PR #25)
Review A approved; Review B rejected on one item: the Conditional workflow, Type workflow and Sub-workflow entries said every change is made at extension points, while the Extension point entry and the registry ("How a conditional workflow names a point") have a replacement target a whole module. All three entries now say a conditional workflow adds and sets at extension points and, for a type workflow or sub-workflow, may replace a whole module the registry marks replaceable. [Correction, added at round 6 (round 4 had overwritten this sentence): that wording let a trait addition set (Review A, round 4); round 5 writes the entries from one rule: any conditional workflow adds at extension points, and only a type workflow or a sub-workflow also sets, at a point that accepts it, or replaces a whole module the registry marks replaceable.] The core's own opening sentence ("only at the extension points") has the same looseness; it joins the HARDENING lead for TASK-010 and TASK-014, together with the glossary's "the interface phase" (Review A's consider: Glossary.md is in neither increment's scope, so the glossary follows in the same change). Review A's other considers: the own-term check also strips quotes (a quoted tautology fails, probed); the two revised Terms fixed entries are Risky (the owner was told the earlier sense), to re-anchor at the next report.

### TASK-009 round 4 — disposition (PR #25)
Both rejected. Review A: round 4's Conditional workflow entry attached the type-or-sub-workflow condition to replacing only, so it let a trait addition set, against the Set and Trait addition entries, the core and the registry. Converged (Review A should-fix, Review B blocking): the status file's Terms fixed still held conditional workflow's old sense ("only at extension points"). Round 5 writes every entry that says who may change what from one rule (any conditional workflow adds at extension points; only a type workflow or a sub-workflow also sets, at a point that accepts it, or replaces a whole module the registry marks replaceable; a trait addition only adds), checks each entry against it before committing (Extension point, Conditional workflow, Sub-workflow, Set reworded), realigns Terms fixed's conditional workflow and marks it Risky. Considers taken: the Sub-workflow entry no longer reads as limited to its type workflow's replaced modules; curly quotes join the own-term strip (probed); the HARDENING lead names the core's layer-table row and inheritance sentence too. The round 3 disposition's paraphrase of the rule is corrected. The defect class (the glossary's statement of who may change what) has moved from one entry to another without leaving the class; each round's finding was new and fixed, the core of the increment (18 terms, the Phase entry, the tests) has held since round 2.

### TASK-009 round 5 — disposition (PR #25)
Review A approved; Review B rejected; both named the same item: the status file's Terms fixed sense of extension point still said a conditional workflow "may add or set", letting a trait set. Round 5's rule check had covered the glossary section only; round 6's covers the Terms fixed line too, and the sense now reads that any type, sub-type or trait file may add and only a type or sub-type file may set, where the point allows. Review A's considers: Conditional workflow, Type workflow and Sub-workflow now qualify setting with "where a point accepts it", as Extension point and Set do; open-list.md's "adds, replaces or sets at each" joins the HARDENING lead. Its note on the round 3 disposition, edited after the fact: the first wording is restored with a correction note beside it.

### TASK-009 round 6 — disposition (PR #25, merged as 2509383)
Both approved (Review A 0/0/3, Review B 0/0/0); CI green on the pushed head. The defect class of rounds 3 to 5 (who may change what) is closed: every entry and the Terms fixed line were checked against the one rule by script before the commit, and both reviewers checked them again. Review A's three considers, taken in these records: C1, the HARDENING lead was routed to TASK-010 and TASK-014, whose scopes hold neither workflow/open-list.md nor workflow/extension-points.md nor Glossary.md; it is now routed by file (supervisor.md to TASK-010; open-list.md to TASK-017, the first increment with it in scope; extension-points.md and Glossary.md to TASK-010's brief, which widens its Scope to them for the rename, recorded when the brief is written). C2, the Terms fixed sense of conditional workflow now qualifies setting and replacing as extension point's sense and the glossary do. C3, round 4's disposition had been edited in round 6 without a marker: its sentence stands again as first written, and the round 3 correction note says the round that added it. Noted: round 5's disposition quotes the qualifier as "where a point accepts it", while the Conditional workflow entry reads "at a point that accepts it" (Type workflow and Sub-workflow use the former); same meaning, left as written.

### REFAC-B2 round 1 — disposition (PR #26)
Both approved the test lane as behaviour-preserving (collected set identical; each probed the shared parser: a parser that ignores its text, or a registry row with one cell too many, fails the registry's tests). Converged on one record (Review A should-fix, Review B should-fix, so blocking): the inventory said jscpd 5.3.3 was the newest release older than two weeks, but 5.4.0 (2026-09-30) was too; the row now says 5.3.3 was run, 5.4.0 was overlooked, and the next pass takes the newest such release; it also says the pin covers the top-level package only (Review A's consider). Review A's other should-fix items: the `judge_workflows_line` closure overstated the loader's share (about fourteen of forty code lines) and did not weigh moving the judging into workflow-check.py; that alternative is now recorded, declined for this pass because it changes the tested no-escape-field cause from AttributeError to NameError, a behaviour change, and kept as a lead for a later change to the two programs. The TASK-010 widening for the registry's Phase column also names tests/test_extension_points.py, which asserts the column; TASK-009 round 6's disposition above names only extension-points.md and Glossary.md and stands as written, the HARDENING lead holding the full list. Review A's consider taken: TASK-010's Done when is a verbatim move, so its brief carries the core's rewording as an added requirement with `reword` entries in trace-exceptions.md. Noted, no change: the registry's tests now fail at collection if open-list.md is unreadable, the price of one parser.

### REFAC-B2 round 2 — disposition (PR #26, merged as 9bb26e0)
Both approved (Review A 0/1/1, Review B 0/0/0); CI green on the pushed head. Review A's should-fix, a false clause in one inventory row that no other reviewer named, did not hold the merge; it is corrected in these post-merge records, which the next branch's gate reviews. Review A confirmed round 1's three should-fix items true against their sources (npm's dates; the NameError, probed on a copy; the registry's test and BUILD_PLAN), and found round 2's new clause false: jscpd 5.3.3's only dependencies are its platform binaries, optional and pinned to the same version, with none of their own, so the pin fixes the whole tree, not the top-level package only. The clause came from its own round 1 consider, which round 2 took without checking it against the registry; the supervisor checked it this time (`npm view`) and the row now says so. Round 1's disposition above, which records that clause, stands as written. Its consider taken: the rule that a change to one judge copy is made to both is routed to TASK-024's brief, whose Scope holds only conformance-check.py and whose report of unwritten workflows is the likeliest reason for the copies to diverge.

## Resolution
| Question | Settled | How |
|---|---|---|
| (none) | | |
