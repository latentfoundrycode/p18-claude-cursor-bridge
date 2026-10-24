# SCOPE - TASK-017

A supervisor-authored increment of governance text and its tests, with no builder run and no program change. Its brief is docs/BUILD_PLAN.md, "### TASK-017 — Trait files: has screens, installable, performance budgets, external services" (Scope, Satisfies R-010 and R-016 to R-019, Done when), as revised and approved on 2026-10-24 (subject `traits`, PR #67). The decisions it rests on are docs/INVENTORY.md's Decisions rows on stage B4's trait increments, the two §6.4 refinements, the `Installer verification` parameter, external services' new checks and the plan critic's lenses.

## Scope (quoted from the plan)
bridge/cursor-bridge/workflow/traits/has-screens.md; .../installable.md; .../performance-budgets.md; .../external-services.md; bridge/cursor-bridge/workflow/phases/intake.md; .../design.md; .../planning.md; .../configuration.md; .../delegation-loop.md; .../project-end.md; bridge/cursor-bridge/workflow/extension-points.md; bridge/agents/plan-critic.md; bridge/cursor-bridge/workflow/open-list.md; bridge/cursor-bridge/workflow/trace-exceptions.md; bridge/cursor-bridge/MANIFEST.json; tests/test_traits_existing.py; tests/test_extension_points.py; tests/test_phase_modules_intake_design.py; tests/test_phase_modules_interface_planning.py; tests/test_phase_modules_build.py; tests/test_phase_modules_close.py; tests/test_session_start_module.py; tests/test_text_consistency.py; tests/test_b2_least_confident.py; tests/test_core_carve.py; tests/test_b3_least_confident.py; tests/instructions.py

tests/test_phase_modules_build.py and tests/test_text_consistency.py are in the Scope and unchanged: no pin of theirs broke (the suite passes).

## Out of scope
- reflection.md, interface.md, run-parameters.md, change-cycle.md and the delegation loop's sub-file folder: unchanged.
- Every passage the Done when keeps whole in the main workflow: the configurator paragraph with its performance-floor clause, the reviewer-routing table with its UI-bearing row, intake's security-context paragraph ("Alongside it" unchanged), planning's two-critic paragraph with its UI clause, project end's User Manual item, run-parameters.md's template fence with its `Installer verification` gloss, the refactoring pass's performance inputs and optimization candidates, the promotion pass's Performance-Patterns entries, the change cycle's re-run of the packaging stage, reflection item 2b's external-service clause, interface.md's sentences naming what activates each variant, step 6's title and first sentence.
- The leads docs/HARDENING.md places elsewhere: the template gloss (TASK-034), intake's "Alongside it" and configuration's "the same way" (the next edit that pays its `reword`).
- The trait files of TASK-018 (spends money, long-running process, AI models) and the type files of TASK-019 to TASK-021. Design for those increments is not this diff's defect.
- Every program under bridge/.

## The tests the supervisor wrote, and the paragraph each enforces
tests/test_traits_existing.py (new, 27 tests, naming R-010 and R-016 to R-019), each enforcing TASK-017's Done when (the 27th, test_r017_installable_s_new_sentences_name_their_kinds, and the stronger R-019 and absence assertions came with Review A's round 1):
- each trait file is one `#` title and `## Add at <point key>` sections, `###` headings unique and only inside a named section;
- the four open-list rows are written;
- every `## Add at` section is moved units, with new text only under a following `###`, or new text throughout under its own `new` entry; no moved unit lies under a `###`;
- the sources (the phase modules and the plan critic) no longer hold the moved passages;
- the lens sections equal the bullets plan-critic.md lost, against its pre-move text held as constants;
- each of the three splits: its parts, put back in the baseline unit's sentence order, equal that unit as trace-check.py reads it (the pre-move text held as constants, never read from git history), and the Observability remainder reworded as a constant of its own;
- has screens activates the mockup variant and holds the interface's build conditions;
- R-019's two checks exist only in external-services.md, the inspect check naming its reviewer and retrying only a call that may run twice, the brief giving a zero limit to one that may not, the layout test for an increment that deploys or prepares a deployment;
- installable's three scoping sentences name the kinds `installer` and `install-script` and what a part of another kind does, the packaging stage's the `n/a` pass-over, and the install-script delivery the project's `install-check.ps1` and no dialog;
- the plan critic keeps its design lenses and flags a missing trait;
- design.md's trait gate carries the traits' plan lenses and asks a trait added there its questions (R-035's gate);
- workflow-check.py passes over workflow/; N7 and N9 remain in the core.

Run once against the checkpoint 899e847 before round 2: 24 of the 26 then written fail; the two that pass there are guards that hold on both sides (the workflow check passes; N7 and N9 stay in the core).

The pins the moves break, re-taken (the Done when names each):
- tests/test_extension_points.py: S64 gains `planning.acceptance-criteria`, `planning.stages` reads "Mandatory stages and increments", the message counts three refinements, and the registry paragraph's pin is re-taken sentence by sentence.
- tests/test_phase_modules_intake_design.py: design's STRUCTURE gains `#### A part without screens`.
- tests/test_phase_modules_interface_planning.py: the three build-condition phrases are now asserted in traits/has-screens.md and absent from both the delegation loop and mockups.md (before: present in the loop, absent from mockups.md).
- tests/test_phase_modules_close.py: project end's survival line and delivery-point line re-taken; the whole-file-entry guard now also reads every entry on a file under workflow/traits/ or workflow/types/ (at least ten such entries must be seen).
- tests/test_b2_least_confident.py: the FLAG line for Installable dropped, as the Done when says; the two (f) findings and `RESULT: 2 problem(s)` remain.
- tests/test_b3_least_confident.py: the derivation reads entries on traits/ and types/ files (keyed under workflow/), five module pins re-taken (design "Traits at the design gate", planning "Extension points" and "What the interface phase hands to the plan", project-end "Extension points" and "What must survive a compaction"), two module pins added (delegation-loop "2. Package the brief", design "A part without screens") and sixteen trait sections pinned.
- tests/test_core_carve.py: the trace pin reads 255 under workflow/ and 14 excused, with three new NOTE lines in output order.
- tests/test_session_start_module.py: the unwritten-workflow case names Mobile App Development and personal data; a new case names the installed traits/installable.md for intake and building, and not for the mockups phase, where interface.md is named.
- tests/instructions.py: instruction_paths() reads the type and trait files after the phase modules.

Of these, run against 899e847: 33 failed, 235 passed, 4 skipped across the eight changed files; the failures are the re-taken and added pins and the new session-start case.

## Expected bookkeeping and record files in the diff
docs/REQUIREMENTS.md (R-010, R-016 to R-019 built), docs/INVENTORY.md (a Features row; the delegation loop's size in the size row), docs/HARDENING.md (TASK-017's section: FIX-004's lead and stage B3's session-start consider taken; the checkpoint run), docs/PROJECT_STATUS.md and project.json as at this pull request's merge, bridge/cursor-bridge/MANIFEST.json regenerated, docs/ROSTER.resolved.json (the roster check's resolved_at stamp, rewritten at each check before Review B), and run/review/ (these three files, removed before the merge).

## What to judge
Does the diff meet every clause of the Done when? Is every moved unit word for word and in a section of moved units only, and every `###` after the moved units of its section? Does any passage that must stay in the main workflow move anyway? Is the new text (the mockups' activation, installable's three scoping sentences and its install-script delivery, external services' three checks, plan-critic.md's missing-trait sentence, design.md's addition to "Traits at the design gate", design.md's reworded remainder, the registry's widened and new point) sound and consistent with the core, the registry and the open list? Do the tests enforce their paragraphs and fail on a regression? Are the records accurate? Apply the anti-gaming checks: a re-taken pin must hold the new text at least as strictly as the old pin held the old.
