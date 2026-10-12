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

## Resolution
| Question | Settled | How |
|---|---|---|
| (none) | | |
