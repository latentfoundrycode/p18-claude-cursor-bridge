# SCOPE — BUG-024 (stage B4's stage review, round 4's fixes)

The supervisor's fix of stage B4's stage review, round 4. Review B approved it with no findings and every part of Review A approved it, and the convergence rule rejected it because two parts (core, tests) named the same defect. No builder ran and no program changed: governance text (bridge/cursor-bridge/workflow/traits/), tests and records only. The round's findings and the disposition of each (taken, not taken with the reason, or a lead) are in the diff's new docs/HARDENING.md section "The stage review, round 4 (2026-10-25): rejected by convergence, fixed by BUG-024". Read it first.

## What the fix must do
1. **The added-lenses sentence read where the critic applies it** (convergent): tests/test_traits_existing.py's test_r017 reads plan-critic.md's sentence "…the lenses the parts' conditional workflows add at `planning.critic-lenses`; apply each as one of your own, at the grade it states" from the "When reviewing a build plan" section, as it reads the lens, not from the whole file. Moved under "When reviewing a design document", the sentence now fails the test. Before this fix it passed.
2. **A paid service's time is in a speed budget by default** (conditional, should fix): traits/spends-money.md's brief constraints say a speed budget of an operation that calls a paid service includes the service's time unless the design records, in the owner's words, that it leaves that time out. Its inspect addition reads the benchmark results against the budgets file and the design's record, in the owner's words, of the speed budgets that leave that time out, and reads any other such budget as including it. A design that says nothing therefore fails closed: before, a stand-in benchmark under the budget's key passed (180 against a max of 2000, exit 0).
3. **The kept-out cases' place named once** (conditional, consider): traits/ai-models.md's test-checks addition names the kept-out cases' place as its configuration addition does, "outside the repository and the Workspace".

## Tests the supervisor changed, and the paragraph each enforces
- tests/test_traits_existing.py::test_r017_the_command_reference_reaches_every_approved_command_design: item 1 (plan-critic.md, "When reviewing a build plan").
- tests/test_traits_new.py::test_r020_spends_money_keeps_paid_results_records_the_cap_and_runs_dry_first: item 2, the default sentence and the inspect clause held whole with its grade.
- tests/test_traits_new.py::test_r022_ai_models_judge_by_evaluation_on_pinned_models_and_recorded_outputs: item 3.
- tests/test_b3_least_confident.py: the three edited sections' pins re-taken (ai-models' test checks; spends money's brief constraints and inspect checks), nothing else.
- Checkpoint run against origin/main: the two text tests and the three pins fail and test_r017 passes. test_r017 should pass there, because the text was already right and only the test was too loose. With the sentence moved under the design review on the old code, test_r017 fails at its last assertion.

## Also in this diff, expected
- docs/HARDENING.md: the round-4 section, and leads re-keyed to the event that picks each up (TASK-022's consider 4, TASK-019's sub-type lead, round 3's leads).
- docs/INVENTORY.md: the first trait files' row names the second form of new text, and the Decisions row on the plan critic's conditional plan lenses says the two command-reference lenses word the criterion differently, §4's words governing.
- docs/PROJECT_STATUS.md as at PR #78's merge (ISS-009).
- bridge/cursor-bridge/MANIFEST.json, regenerated.
- docs/ROSTER.resolved.json's stamp, in its own commit.

## Review A on the fix
APPROVE (0/1/5). The second commit takes the should-fix and three considers: the record now names the Decisions row; the inspect check reads the design's record in the owner's words; two leads name their events or the default's effect. Its section is in the HARDENING round-4 section.

## Out of scope
- The findings the HARDENING sections record as leads (round 4's included): installable's moved lens wording, which is a baseline unit; §4's currency check and an untracked file; planning.md's compaction list; the plan critic's missing-trait bullet and its citation path.
- The bridge's traits, which the owner decides at the stage close.
