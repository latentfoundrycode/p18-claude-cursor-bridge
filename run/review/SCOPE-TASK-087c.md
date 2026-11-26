# SCOPE: TASK-087c (Review B, round 1)

Increment: TASK-087c, "Stage I1's texts: the reviewers' one sentence, the report's outputs, an exhausted pool (R-107, R-108)". Supervisor-written instruction text: no builder, no brief; the plan entry is the specification (docs/BUILD_PLAN.md, the section "### TASK-087c": its Scope, Scope notes and Done when lines), with docs/DESIGN.md, Change: the improvements release, the paragraph beginning "*C39 (first), with T108 and T103.*", its table, and the paragraph after it beginning "The bridge's template roster names". The diff is the branch against origin/main at 91fc2d8, the review files left out: run/review/REVIEW-TASK-087c-r1.diff. Where the increment ends: stage I1's texts. R-107 stays planned (below); R-108 stays planned until TASK-096.

## Scope (the plan's)
- bridge/commands/supervisor.md: rule 38 and its digest line (each digest part within 8,800 characters).
- bridge/cursor-bridge/Merge-Verification-Policy.md: the roster section and template, the safety refusal, the Phase 2 wait, Review B's default and its prompt-as-preamble paragraph.
- bridge/cursor-bridge/Known-Pitfalls.md: KP-079's correction and KP-035's sentence on the hook's registrations, nothing else.
- bridge/cursor-bridge/workflow/phases/delegation-loop.md (step 1's FAIL sentence, step 3b), delegation-loop/merge.md (step 8's directive clause, verify's list, the failed launch), design.md (the critique's waits).
- bridge/agents/diff-reviewer.md, security-auditor.md, design-auditor.md (the one sentence; diff-reviewer's stripped runs, wanted probe and VERIFIED).
- bridge/agents/spec-packager.md: the report sentence of the brief's Done section and the Scope line (bullet and header) admitting run/agent/ output files, nothing else.
- bridge/cursor-bridge/workflow/trace-exceptions.md (one entry), docs/TRACE_MOVES.md (19 entries, each pasted from the move mode's failure line), bridge/cursor-bridge/MANIFEST.json (regenerated).
- docs/ROSTER.json: review_b_alt (see the deviation).
- tests/test_improve_roster_alt.py: one test holding the policy's template to the key.
- The records commit, outside Scope by the RECORDS rule: docs/HARDENING.md, docs/INVENTORY.md, docs/REQUIREMENTS.md, docs/PROJECT_STATUS.md.

## The one sentence (T75), as it stands in the merge step and the three agents
A reviewer writes nothing in the checkout: pytest's own temporary folders under the system's temporary folder are its to use, and one folder made by `tempfile.mkdtemp`, removed by its exact path, for notes and what a differential check writes; tests are run from the checkout, with `-p no:cacheprovider`, where the project's `conftest.py` loads, never from that folder.

## Deviations from Done when (recorded in INVENTORY, Decisions, and HARDENING, TASK-087c)
1. The full profile names no review_b_alt, in the policy's template and in docs/ROSTER.json (Done when says both profiles). With composer-2.5 in the full profile, roster-check.py resolves the full profile while the other pool is exhausted (Review B composer-2.5, builder Grok), against the order this increment writes (the next profile, the alternate, the rebuild) and the native profile's reason; the native profile names composer-2.5. Review A round 1 rejected the template that still carried it.
2. R-107 stays planned (Done when says built): Review A round 2 found that roster-check.py --review-alt reads the first profile whose builder is usable, not the profile the resolve picks (TASK-086a's program, outside this diff); its fix is planned at stage I2's start.

## Tests outside the Scope
Five old-wording tests held changed sentences whole (tests/test_bug043.py, tests/test_release_t_records.py, tests/test_release_t_ceiling.py twice, tests/test_release_b2_text.py's header-scope agreement). None was edited: each held sentence was kept whole, the new words beside it.

## The threat model
Instruction text and one record a program reads (docs/ROSTER.json). The risk: a sentence that states something a program does not do (roster-check.py's resolution and --review-alt, the launcher's stripped test kind, review-guard.py verify), so that a supervisor relies on a check it does not have, or a roster value that weakens the gate's Review B.

## Reviews so far
Review A round 1: REJECT (behaviour: the template's full-profile key), one should-fix (KP-079's wording); round 2: APPROVE, two should-fix (the policy's full-profile sentence now states its cost; --review-alt's defect recorded, R-107 kept planned); round 3: APPROVE (a confirming read of the clause and the records), four records notes taken in a second records commit (R-107's second open item, the template's full profile; HARDENING's roster lines attributed to a copy of the roster; the status file's design revision due before 2026-12-16; bridge-check's output line quoted).

## Proofs
trace-check.py RESULT: OK (0 dropped, 122 excused); trace-check.py --moves RESULT: OK (19 excused); the 82 test files that read the edited texts: first run 5 failed, 2497 passed, 36 skipped (the five held sentences), after the rewording 273 passed, 3 skipped; after Review A's fix 205 passed, 3 skipped; the status tests with this pull request's variables 426 passed, 3 skipped. Rulebook 149,754 before, 150,853 after; loop module 7,715 of 8,500; digest 9,656 of 10,500, parts 4,181 and 5,428 of 8,800.

## Round
Review B's first round for this increment (the guard's count 0).
