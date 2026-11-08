# SCOPE - TASK-048, the plan's and the briefs' headers (R-059)

Review B's round 1 by the guard's count. Three builder rounds ran (composer-2.5); the launcher's count is 3, the review ceiling, reached and not passed, so no round here is lifted and no Blocking class line applies.

## The increment's Scope and Done when

`docs/BUILD_PLAN.md`, section "TASK-048 - The plan's and the briefs' headers (R-059)": read its Scope, Scope notes and Done when there whole. The plan's Scope: bridge/cursor-bridge/plan-check.py; scope-check.py; completion-check.py; bridge-run.py; review-guard.py; bridge_env.py; MANIFEST.json; tests/test_header_plan.py; tests/test_plan_check.py; tests/test_scope_check.py; tests/test_completion_check.py; tests/test_bridge_run_review_ceiling.py; tests/test_review_guard_ceiling.py; tests/test_task032_supervisor_launcher.py; docs/BUILDER_NOTES.md; handoff/TASK-048-r<N>-report.md.

The round-3 brief (handoff/TASK-048-r3.md) adds tests/test_header_plan_r2.py and tests/test_header_plan_r3.py, the supervisor's reproduction tests for rounds 2 and 3.

Out of scope, quoted from the round-3 brief: TASK-046's reader code in bridge_env.py (read_header, check_header, header_agrees, HeaderError, HEADER_SCHEMAS and their private helpers), compared by the supervisor with 4bdac19 each round: "checked 32 names; changed: none"; TASK-047's status readers; the tabular records' headers (TASK-049); the run parameters' header and its lifts (TASK-050); records-migrate.py (TASK-051); the duplicated helpers TASK-047's HARDENING section names; the quadratic patterns in parse_scope / split_entry, STAGE_RX and BLOCKING_CLASS_RE (a HARDENING item, their rule unchanged). No command changes. Design for later increments is not this diff's defect.

## Also in the diff, on purpose

- Supervisor commits: 1ffcddb (tests/test_header_plan.py, the acceptance tests, written first); 4bdac19 (the checkpoint: tests that pinned the retired readings (6) and (11) rewritten first, in tests/test_a4_review_fixes.py, tests/test_pace_report.py, tests/test_plan_check.py, tests/test_task033_supervisor.py and tests/test_task033_supervisor_r2.py); 90f1b8f (two harnesses given bridge_env: tests/test_plan_check.py and tests/test_bug038.py); bd47c5e and 04e91ab (the reproduction tests of rounds 2 and 3, 04e91ab also revising the round-2 no-git parenthesis test from a failure to a note); 86ab1d9 (two launcher tests that passed for the wrong reason tightened after the mutation sweep).
- handoff/: the four briefs (TASK-048.md, -r2.md, -r3.md) and the three builder reports.
- The records, in their own commit 4061b48: docs/HARDENING.md (TASK-048's section: the split verdict ruled, the leads, the advisories, the proofs), docs/INVENTORY.md (the Features row), docs/REQUIREMENTS.md (R-059 built), docs/PROJECT_STATUS.md as at PR #139's merge (ISS-009).
- run/review/ files of this round.

## The split verdict, ruled (read it)

On round 3 the security audit passed and Review A rejected on one finding, B-1: in a plan with no header, an increment with two `Satisfies:` lines keeps only the last in completion-check's planned set (walk_plan_prose_body keeps the last value per field key), so the first line's R-ids read unplanned. The supervisor ruled it not blocking: the planning template gives one `Satisfies:` line per increment, this repository's plan has 54 for 54 increments, plan-check's parse always kept the last value, it fails closed (an R-id reported unplanned, never one let through), and the header-less path is transitional (TASK-051 and TASK-054). It is recorded in HARDENING with Review A's fix. Judge it yourself on an ordinary plan.

## The tests and the paragraph each enforces

- tests/test_header_plan.py (supervisor's, names R-059 and D-002): the Done when's paragraphs one by one: plan-check's header first, the per-field agreement under each normalisation, the heading pairing, the stage fields, the historic exemption only where the merged set holds the ID and the mark refused otherwise, the --no-git note, the dash-prefixed --base refusal, the unbalanced parenthesis (a failure unmerged, read as today merged); scope-check's per-key comparison and malformed refusal; completion-check's agreement rule and its retired whole-text search; plan_increment_ids over every plan file; the launcher's and the guard's refusals; the moved readers living in bridge_env; the retired readings (5), (6), (11) gone as uses.
- tests/test_header_plan_r2.py (supervisor's): round 1's findings: scope-check enforces the Scope the header was compared with; a class with no prose line never lifts the ceiling; wrong-kind and empty headers refused in every program; a ### comment inside a plan header is no increment; the field reading linear; the guard refuses an unreadable first brief; the launcher refuses a malformed plan header and one whose increments have no heading (since 86ab1d9, a merge unit naming a heading with no header entry, refused by the header comparison alone); the parenthesis note under --no-git.
- tests/test_header_plan_r3.py (supervisor's): round 2's findings: plan-check compares a brief with an agreeing header; a heading outside any stage of a headed plan is a failure and a launcher refusal (since 86ab1d9, the header refusal's own words); a merged unbalanced Scope can agree with its header; a bare-CR brief refused by the launcher; an unreadable plan file refused; nothing read from inside a malformed header; plan-check and completion-check walk no plan themselves.

Against the checkpoint 4bdac19's bridge (run/supervisor/task048_new_tests.py): 83 failing (the new tests, all confirmed failing by `mutation-run.py --checkpoint 4bdac19`), 22 passing (invariants: an agreeing header reads as its prose, and structural checks).

## The mutants

run/supervisor/TASK-048-mutants.json, written by run/supervisor/task048_mutants_make.py (both gitignored, read here on purpose); new_tests written by run/supervisor/task048_new_tests.py. 37 mutants (F4 R18 C4 K4 H7), 37 killed (`counts: run=37 cached=0 killed=37 survived=0 not applied=0 error=0 expected survive=0`, run/agent/TASK-048-mutation.out). The sweep on 41 left five survivors: r16 a wrong-reason pass, closed by 86ab1d9; r17, c05, c06 and k05 equivalent and dropped, each reason written in the generator. The header-less regression driver, run/supervisor/task048_headerless_regress.py, ran 4bdac19's and round 3's programs over a copy of this repository's records: plan-check --base main identical, completion-check identical, scope-check over 107 briefs 0 differ, plan-check --no-git differing only by the new parenthesis note.

## What the supervisor's reviews said

Round 1: the audit FAIL (B1 scope enforcement on the whole text; B2 the class lift with an empty line), Review A REJECT. Round 2: the audit FAIL (the brief comparison inverted; an orphan heading), Review A REJECT (four plan walkers; the merged parenthesis sentinel). Round 3: the audit PASS with advisories A1 to A5, Review A REJECT on B-1 alone, ruled above. HARDENING's TASK-048 section holds the leads not taken.

## Threat model

docs/INVENTORY.md, Decisions: no row is recorded for the header readers themselves. The plan and the briefs are records the supervisor writes (the builder's brief forbids docs/ and handoff/ but its report), so a finding is judged by the five blocking classes on an ordinary plan and brief, a security finding by whether untrusted input can reach it. The launcher's and the guard's refusals are safety mechanisms: a header that lets a builder past its Scope, the review ceiling or the merge unit is a defeated safety mechanism. For the guard, the row beginning "The review guard's threat model".

## Checks to run with the source tree's program

Run the source tree's programs (`python bridge/cursor-bridge/<program>.py`), never the installed ones, which are release 2026.11.03a and predate this increment.

## Bookkeeping expected in the diff

docs/BUILDER_NOTES.md where the builder wrote it; handoff/TASK-048-r1-report.md, -r2-report.md, -r3-report.md; the records above; run/review/REVIEW-TASK-048-r1.diff, ASSUMPTIONS-TASK-048-r1.md and SCOPE-TASK-048.md (removed before the merge).
