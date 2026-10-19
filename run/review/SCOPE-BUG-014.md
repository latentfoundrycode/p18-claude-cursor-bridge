# SCOPE — BUG-014 (stage B2's review, round 12: the convergent items)

The diff at `run/review/REVIEW-BUG-014.diff` is branch `bug-014` against `main` (its merge base, 7f0593a), the `run/review/` records left out.

## What it answers

Stage B2's review, round 12: Review B (grok-4.7-medium, the native profile) APPROVE with no findings; Review A's nine parts APPROVE. The round was judged by defect class under standing rule 6. Two items were named by two or more reviewers, which the code gate's convergence rule makes blocking, and one part had a should-fix; this diff fixes those and two docstrings. The round's full record is `docs/HARDENING.md`, "Stage B2 — the stage review (round 12, 2026-10-19)". No reviewer rejected, so the stage review does not run again on the stage's whole change (the stage close's step 7 runs it again after a REJECT); this diff takes the gate as an increment.

## What the diff changes

**No program.** The workflow check and its judges are unchanged. The tests are the supervisor's (N4 permits tests):

- `tests/test_workflow_check.py`, test_r014_the_bridge_tables_still_say_what_the_fail_roots_rely_on and FAIL_ROOT_NAMES: the fail roots under `tests/fixtures/workflows/fail/` are checked against the bridge's own open list and registry, so the test reads every key (folder and file names), point (the `Add at`, `Add at … for` and `Set at` headings), module (`Replace` headings) and delivery kind (a `for` kind, a Set at intake.delivery-kind value as the program normalizes it) the fail roots name, reading each file as the program does (utf-8-sig, the program's own `heading_spans` and `parse_heading`, so a name inside a fence is no reliance), and pins what those two tables say of each, and for a kind whether the program's `DELIVERY_KINDS` holds it (extension-points.md: that constant changes with the registry's list). It enforces nothing in a document: it is the precondition of the FILE_EXACT cases (TASK-006 Requirements 4 to 10, as each case's comment names), so that a later row of the tables names the entry a case relied on instead of failing a case's output with no cause given. Convergent: fixtures 1 (noted), fixtures 2 (consider), tests (consider).
- test_r014_a_key_is_looked_up_as_written: the open list it rewrites is the status cases' own (`tests/fixtures/workflows/status/open-list.md`), not the bridge's, its precondition's counts those of that file; it enforces `bridge/cursor-bridge/workflow/open-list.md`:11 and pins the program's reading of an open list keyed in capitals, as before. Tests part, consider (converging with the above).
- The comment above STATUS_EXACT names the multi-line status files as having no Phase line too. Fixtures 4 and 5, consider (convergent).
- `tests/fixtures/workflows/fail/unknown-trait-file/traits/claude-code-extension.md` (new), pinned in FILE_EXACT, with the comment above it extended: a sub-type's key at a trait file's path is no trait key (TASK-006 Requirement 4, `unknown`). Fixtures 3, should-fix: a mutant of workflow-check.py:568 reading the sub-types' keys too survived.
- Docstrings: test_r014_an_indented_heading_line_stays_in_its_section (`extension-points.md`:72, at most three spaces before `##`) and test_r014_a_head_split_on_a_comma_without_its_space (`handoff/TASK-006.md` Requirement 11, step 4). Tests part, considers.

The supervisor's mutation driver for the three cases is `run/supervisor/bug014_mutants.py` (gitignored, not in the diff; it copies `bridge/` and `tests/` to a scratch folder): the 568 mutant, the interface module made not replaceable in the registry, and 568's key lowered, each killing its named test, the unmutated copy passing.

## BUG-014's gate so far

Review A: APPROVE, one should-fix taken (the delivery kinds added to FAIL_ROOT_NAMES; Review A's own seven table edits on a copy each failed the test) and its considers (the fixtures read with utf-8-sig; the driver's byte check after every restore, with a fourth mutant, `docker-image` added to DELIVERY_KINDS, killed). Secret sentinel: CLEAR. Full suite before the should-fix: 1614 passed, 24 skipped; tests/test_workflow_check.py after it: 484 passed, 2 skipped.

## Records in the diff, expected

`docs/HARDENING.md` (the round-12 section, placed before the hotfix's section: the verdicts, the convergent items, the survivors recorded under rule 6 and the considers not taken); `docs/PROJECT_STATUS.md` (the position and its BUG-014 section).

## Platform skips

On Windows the suite gives the same skips as on main (24); this diff adds none.
