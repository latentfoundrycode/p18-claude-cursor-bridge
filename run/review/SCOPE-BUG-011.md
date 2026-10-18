# SCOPE — BUG-011 (stage B2's review, round 10: fixes)

No builder ran. Every change is the supervisor's: tests, fixtures and records. No program changed: bridge/cursor-bridge/workflow-check.py, inventory-check.py and conformance-check.py, and every other file under bridge/, are byte-identical to origin/main b7f6ec3.

## Scope (what this increment is)
Stage B2's review, round 10 (snapshot STAGE-B2j, 368f859): Review B APPROVE; Review A APPROVE on eight of nine parts; Review A's tests part REJECT. Its blocking item: no test holds a status file's lines judged one by one, so the program reading them with repeats dropped (`list(dict.fromkeys(lines))`, or `len(set(lines))`) turns two identical unprefixed lines from two (form) findings into `RESULT: OK`, and two identical prefixed lines from (e) into another finding. Its should-fix: a separator cell's "at least one dash" has no failing case (the cell test without its `bool(text)`, rewritten as `all(c == "-" ...)`). Its consider: a head naming a product type twice. The class is ISS-007's (rules of the workflow check no test fails for), here in an operator no sweep had tried: a rule rewritten in another idiom. So the supervisor wrote an idiom sweep for the class before any case, and every survivor an input separates has a case; the rest are recorded by class in docs/HARDENING.md, "the stage review (round 10)".

## Out of scope
- Any change to the three programs. The programs' leads (conformance-check.py's reason for an unreadable status file; the empty traits text's wording) stay for the next change of those programs (TASK-024, and HARDENING's leads).
- The texts part's considers (supervisor.md:1821's "every name on the line", the Glossary's Open list entry) and fixtures 1's (the registry's BOM sentence): texts, recorded in HARDENING for the next change of those files; no rule changes here.
- Design for later increments is not this diff's defect.

## The tests and fixtures the supervisor wrote, and what each enforces
- tests/fixtures/workflows/status/, four new files, each in STATUS_EXACT and STATUS_TEXT:
  - e-same-part-identical.md, form-prefix-missing-identical.md — handoff/TASK-006.md Requirements 11 and 12: each `Workflows:` line is checked; several lines each carry a prefix, and two lines naming one part are (e). test_r014_each_line_of_a_repeated_pair_is_valid_alone shows each pair's line alone gives the output a check that dropped repeats would print.
  - e-type-named-twice.md, e-sub-type-named-twice.md — Requirement 11, step 4: the names that are Workflow (Sub-workflow) names count as product types (sub-types), each one given; exactly one product type, at most one sub-type (supervisor.md "Project state").
- tests/test_workflow_check.py:
  - test_r014_separator_cell_count_differs[last-cell-blank, last-cell-colon-only] — R3-2 and the rule files' "How this file is read": every separator cell is at least one dash.
  - IDIOM_STATUS_CASES / test_r014_a_repeated_name_is_counted_each_time — Requirement 11: a product type named in two segments is two.
  - IDIOM_ROOT_CASES / test_r014_a_paths_repeated_parts_are_read_as_given — extension-points.md:72 (a folder under types/ that is no product type, reported once, nothing inside read; a folder under traits/) and :68 (the `for <kind>` form is an addition's; a Set at project-end.delivery owes no kind).
  - test_r014_a_heading_of_at_at_is_a_change_heading[`## at at`, `## at at the gate`] — extension-points.md:72: a heading whose second word is `at` is a malformed change heading.
  - test_r014_a_table_whose_header_repeats_a_column_is_read — no document says a repeated column stops the check; the test pins the program's choice (as round 9's first-row tests do).
  - test_r014_an_error_without_its_reason_still_names_one, test_r014_a_read_error_without_its_reason_names_the_error — Requirement 3: every argument that cannot be checked is an ERROR line with a reason; the program's own words stand in where the system's error carries none.
  - test_r014_a_line_without_the_traits_marker_is_not_checked_further — Requirement 11, step 3, with its precondition (round 10: fixtures 4).
  - Strengthened or reworded (considers): test_r014_indented_or_tabbed_change_heading_is_form pins its three headings (fixtures 2); the comments at FILE_EXACT form-misspelt-change-word (fixtures 2), STATUS_EXACT unknown-trait-key (fixtures 6) and form-bad-prefix-bodies-unchecked (fixtures 4); ROUND7_PRECONDITIONS holds the pass root README's change heading (fixtures 3); the four order tests' docstrings cite their document or say none fixes the order (round 9's carried should-fix).
- tests/fixtures/workflows/pass/README.md gains `## Add at nowhere.at-all`, which would fail were the file read (fixtures 3).
- tests/test_workflows_line_check.py: test_r015_a_repeated_finding_is_reported_each_time (handoff/TASK-008.md: one WORKFLOWS LINE per finding, the conformance row every finding joined by `; `) and test_r015_two_identical_lines_stand_together (check_placement).

## The sweep (local, run/supervisor/, readable)
sweep_idiom.py (repeats dropped from every `for`, `len` and assigned list, each operand of an `and` or `or` dropped, `all` and `any` swapped; repeats of unhashable items dropped by identity): run on main's tests, then against these tests; write_idiom_list.py (`--check`) puts each survivor in its class and stops on a survivor no class names. Every test was only added or strengthened; none was removed or loosened, so the earlier sweeps' and drivers' kills stand.

Since no program changed, every new test passes on the checkpoint's code as well; what each proves is the mutant it kills, named in its docstring or comment (Review A's two named mutants, and the sweep's lines), and the sweep's runs show each killed: run/supervisor/sweep_idiom_r1.out (main's tests) against sweep_idiom_final.out (these).

## Expected bookkeeping in the diff
docs/HARDENING.md ("the stage review (round 10)"), docs/PROJECT_STATUS.md, run/review/ (the review files).
