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

## Resolution
| Question | Settled | How |
|---|---|---|
| (none) | | |
