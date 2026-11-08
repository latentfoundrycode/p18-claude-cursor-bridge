# SCOPE - TASK-049, the tabular records' headers (R-060)

Review B's round 1 by the guard's count. Two builder rounds ran (composer-2.5); the launcher's count is 2, below the review ceiling of three, so no round here is lifted and no Blocking class line applies.

## The increment's Scope and Done when

`docs/BUILD_PLAN.md`, section "TASK-049 — The tabular records' headers (R-060)": read its Scope, Scope notes and Done when there whole. The plan's Scope: bridge/cursor-bridge/inventory-check.py; conformance-check.py; completion-check.py; diagram-check.py; plan-check.py; bridge_env.py; MANIFEST.json; tests/test_header_tables.py; tests/test_conformance_check.py; tests/test_completion_check.py; tests/test_diagram_check.py; tests/test_plan_check.py; tests/test_text_consistency.py; docs/BUILDER_NOTES.md; handoff/TASK-049-r<N>-report.md.

The round-2 brief (handoff/TASK-049-r2.md) adds tests/test_header_tables_r2.py, the supervisor's reproduction tests for round 1's findings.

Out of scope, quoted from the round-2 brief: ".env and anything under secrets/"; "CI configuration"; "docs/ and handoff/, except the files the Scope section names"; "Every test file not listed in the Scope."; "TASK-046's reader code in `bridge_env.py`: `read_header`, `check_header`, `header_agrees`, `HeaderError`, `HEADER_SCHEMAS` and their private helpers"; "TASK-047's status readers ... and TASK-048's brief and plan readers ..., except to call them"; "The run parameters' header (TASK-050) and `records-migrate.py` (TASK-051)"; "The duplicated helpers that `docs/HARDENING.md`'s TASK-047 section names ... Add no copy of these or of any helper"; "The quadratic patterns `docs/HARDENING.md` records"; "The findings the supervisor ruled no change and recorded in `docs/HARDENING.md`"; "Any mutation script." bridge_env.py's diff is one hunk of added lines after `status_values`; no existing line of TASK-046's, TASK-047's or TASK-048's code changed. No command changes. Design for later increments (the run parameters' header, the migration, the templates, this repository's records gaining their headers) is not this diff's defect.

## Also in the diff, on purpose

- Supervisor commits: b6e35b3 (tests/test_header_tables.py, the acceptance tests, written first); 6de9944 (tests/test_header_tables_r2.py, round 1's reproduction tests, written before the round-2 brief); c318582 (two cases telling round 1 from round 2, after round 2's reviews: a header comment `## Features` with an empty body; the header-less index reading's first-table check); a868a4b (twelve cases closing the mutation sweep's survivors, two of them wrong-reason passes in the supervisor's own tests).
- handoff/: the two briefs (TASK-049.md, TASK-049-r2.md) and the two builder reports (their quoted bridge-check line's drive path replaced by `<Workspace>`).
- The records, in their own commit fccaf01: docs/HARDENING.md (TASK-049's section: the rounds, the audit's advisories A-1 to A-5, Review A's leads, the accepted notes, the supervisor's slips, the proofs; and TASK-048's carry-overs), docs/INVENTORY.md (the Features row), docs/REQUIREMENTS.md (R-060 built), docs/PROJECT_STATUS.md as at PR #140's merge (ISS-009).
- run/review/ files of this round.

## The rulings to judge yourself

- One owner per table prints `HEADER DISAGREES` (inventory-check the inventory's; completion-check the register's; diagram-check the index's and the deviations'); the other reader (conformance-check; diagram-check on the register; plan-check on the index) reads the header and trusts the owner. This is the design's rule.
- With a register header, every declared column's cell must be non-empty except the evidence role's (the standard order gives exactly the header-less `all(r[:4])`); the requirement's text is the first declared column that is no role's column.
- With an index header, the rows are the body's first table split by the declared columns, with no first-word check; column agreement is `header_agrees`'s. Without a header, the first-table check stays (`diagram_index_table`), in diagram-check and in plan-check alike.
- The inventory's column-count SHAPE rule is the template's (`INVENTORY_SECTIONS`) in both paths; a headed inventory is read from its body alone; an agreeing header with `reflected_through: null` keeps `SHAPE: no 'Reflected through:' line` and the absorption check, as header-less.
- Recorded, not fixed (HARDENING): the audit's A-1 (a header-less inventory headed `## Resources (keys and accounts)` drops its Resources rows, so conformance-check's spending-limit floor reads OK where main read MISSING; inventory-check, the owner, fails such a file on main and here; ruled contrived by the tail rule); A-2 (a traceback on a partial install, failing closed); A-3 (a role-only headed register passes); trailing heading words read as no section (the one reading); roles naming each other's columns agree (TASK-046's A1). Judge each on an ordinary record.

## The tests and the paragraph each enforces

- tests/test_header_tables.py (supervisor's above its marker, names R-060 and D-002): the Done when per table and program: the header path and the fallback on the same fixture giving the same answer; a declared column the table lacks (`HEADER DISAGREES: columns` from the owner, the other reader silent); a section the header lacks; a role's column absent from the table's header row; a role naming a column outside the header's columns (malformed); a fifth status word and three words (malformed); a Status cell with another word (the register check's finding); `development_data` and `reflected_through` differing; an R-id in the register's prose counted by nothing; the rows split by the declared columns (register, index, deviations); malformed headers refused per program (`HEADER MALFORMED: <path>:<line>`, exit 2); the retired readings (7), (8), (9) gone as uses. Below its marker, the builder's cases.
- tests/test_header_tables_r2.py (supervisor's above its marker): round 1's findings B1 to B4 and should-fix 1 to 4 reproduced (a null `reflected_through`; empty register cells; the requirement's text; a reordered declared index; one copy of each moved reading; known_deviations raising; no traceback without bridge_env; the stand-in's floors not checked); c318582's two cases; a868a4b's twelve: a header block the reader refuses stops five readers, conformance-check refuses an inventory header lacking a section, a register with ID second and Evidence third read by role in --mode plan and --mode done, the register's ids and the deviations' keys read by role on moved columns, an inventory section found by its whole heading, a reordered declared index selecting as many diagrams as the header-less one. Below its marker, the builder's four cases (two of them weak, HARDENING).

Against the checkpoint 4dac0f8's bridge (run/supervisor/task049_new_tests.py): 52 failing (the new tests, all confirmed failing by `mutation-run.py --checkpoint 4dac0f8`), 16 passing (invariants: an agreeing header reads as its prose, a reader trusts the owner, the header-less rules kept).

## The mutants

run/supervisor/TASK-049-mutants.json, written by run/supervisor/task049_mutants_make.py (both gitignored, read here on purpose); new_tests written by run/supervisor/task049_new_tests.py. 49 mutants (F5, R20, C3, K7, H14 over bridge_env's tabular readings and the five readers), 49 killed (`counts: run=49 cached=0 killed=49 survived=0 not applied=0 error=0 expected survive=0`, run/agent/TASK-049-mutation.out). The first sweep of 50 left 12 survivors: eleven gaps in the supervisor's tests, closed by a868a4b; h15 (conformance-check's sections read from the whole text) equivalent on any realistic inventory and dropped, its reason written in the generator. The header-less regression driver, run/supervisor/task049_headerless_regress.py, ran 4dac0f8's and round 2's programs over a copy of this repository's records: inventory-check, conformance-check, completion-check (plan, done), diagram-check (design, code, done), plan-check (--no-git, --base main): RESULT: IDENTICAL.

## What the supervisor's reviews said

Round 1: Review A REJECT (B1 to B4, should-fix 1 to 4), the audit FAIL (B1 and B2, convergent with Review A). Round 2: Review A APPROVE (leads in HARDENING), the audit PASS WITH FINDINGS (A-1 to A-5, HARDENING). The full suite on round 2: 4737 passed, 41 skipped.

## Threat model

docs/INVENTORY.md, Decisions: no row is recorded for the record readers themselves. The inventory, the register, the index and the deviations are records the supervisor writes (the builder's brief forbids docs/), so a finding is judged by the five blocking classes on an ordinary record, a security finding by whether untrusted input can reach it. A reader that lets a malformed or disagreeing header pass silently, or that reads a header-less record differently from main, is behaviour against the register (R-060).

## Checks to run with the source tree's program

Run the source tree's programs (`python bridge/cursor-bridge/<program>.py`), never the installed ones, which are release 2026.11.03a and predate this increment.

## Bookkeeping expected in the diff

docs/BUILDER_NOTES.md where the builder wrote it; handoff/TASK-049-r1-report.md and -r2-report.md; the records above; run/review/REVIEW-TASK-049-r1.diff, ASSUMPTIONS-TASK-049-r1.md and SCOPE-TASK-049.md (removed before the merge).
