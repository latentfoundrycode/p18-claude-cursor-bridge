# SCOPE — BUG-023 (stage B4's stage review, round 3's fixes)

The supervisor's fix of stage B4's stage review, round 3, which Review B and every part of Review A approved and which the convergence rule rejected: two parts (core, modules) named the same defect. No builder ran and no program changed: governance text (bridge/agents/plan-critic.md, bridge/cursor-bridge/workflow/), tests and records only. The round's findings and the disposition of each (taken or a lead) are in the diff's new docs/HARDENING.md section "The stage review, round 3 (2026-10-25): rejected by convergence, fixed by BUG-023"; read it first.

## What the fix must do
1. **The criterion in §4's words** (convergent): planning.md's "What the interface phase hands to the plan" and plan-critic.md's command-reference lens quote the later-increment criterion as `Delivery-Conventions.md` §4's Acceptance row words it, "the reference regenerated and committed".
2. **A stand-in's time never stands under a service-time budget's name** (conditional, should fix): traits/spends-money.md's brief constraints say the part's own time on the stand-in is reported under a benchmark name of its own, never under the name of a budget that includes the service's time; its inspect addition makes a stand-in result under such a name a blocking finding. (bench-check.py fails a budget only when no result carries its benchmark and metric; a stand-in time under that key passed it.)
3. **A kept-out evaluation case stays out of the Workspace** (conditional, should fix): traits/ai-models.md keeps it outside the repository and the Workspace, as the stage's other users' data is kept (spends-money.md's live-data copy, web-app.md's backup).
4. **Tests read what they claim** (tests): a phrase assertion for AI models' scrubbing clause, for the benchmark sentence's subject and for spends money's inspect addition; test_r017 and the missing-trait test read their bullets from plan-critic.md's "When reviewing a build plan" section, so a lens moved out of the plan review fails them.
5. **Round 1's leads the last fix passed** (records): spends money's list of the loop's paid actions no longer names a dry run (which charges nothing); tests/test_traits_existing.py's dead assertion is removed; the other two leads are re-keyed.

## Tests the supervisor changed, and the paragraph each enforces
- tests/test_traits_existing.py::test_r017_the_command_reference_reaches_every_approved_command_design — item 1, and item 4's section reading.
- tests/test_traits_existing.py::test_r016_r019_the_plan_critic_keeps_its_design_lenses_and_catches_a_missing_trait — item 4's section reading. The dead assertion (item 5) was in the four trait files' moved-units test, at tests/test_traits_existing.py:183.
- tests/test_traits_new.py: test_r020_spends_money_asks_for_approval… (item 5's list), test_r020_spends_money_keeps_paid_results… (item 2, both halves, and the benchmark's subject), test_r022_ai_models… (item 3 and the scrubbing clause).
- tests/test_type_host_extension.py: a docstring that read the old sentence.
- tests/test_b3_least_confident.py: the five edited sections' pins re-taken (planning.md's hand-over; ai-models' configuration; spends money's intake questions, brief constraints and inspect checks), nothing else.
- Checkpoint run: against origin/main, the four tests that hold changed text fail (test_r017, both spends-money tests, test_r022) and the rest pass; the section readings characterise placement already right.

## Also in this diff, expected
- docs/HARDENING.md (the round-3 section; round 2's phrase-assertion claim corrected; two round-1 leads marked taken; TASK-021's suite arithmetic), docs/REQUIREMENTS.md (R-020's evidence), docs/INVENTORY.md (the first trait files' scoping wording; the core's size cell), docs/PROJECT_STATUS.md as at PR #77's merge (ISS-009), bridge/cursor-bridge/MANIFEST.json regenerated, docs/ROSTER.resolved.json's stamp in its own commit.

## Out of scope
The findings the HARDENING sections record as leads (round 3's included: the contract-enforcement lens, the NOT MEASURED routing for an undesigned budget, AI models' and host extension's paid-run edges, bench-check's fourth failure and its exit 2, BUILD_PLAN's TASK-018 Done when); the bridge's traits, which are the owner's to decide at the stage close.
