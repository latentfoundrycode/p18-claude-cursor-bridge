# SCOPE — BUG-009 (stage B2's review, round 8: fixes)

## r2 (gate round 2; commit 1ec4854 over the reviewed head f992d26 — run/review/DELTA-BUG-009.diff holds the change since that head alone)
Gate round 1: Review B APPROVE; Review A APPROVE with one should-fix and considers (docs/HARDENING.md, "BUG-009's gate round 1"). r2 changes no program. What it adds, and what each enforces:
- tests/test_workflows_line_check.py: test_r015_a_valid_line_is_judged_valid_with_no_rows[judge × case] — handoff/TASK-008.md, the judge's interface: a valid line is ("valid", []) from each judge (the widened sweep's inventory-check.py line 228, `if findings:` forced true, printed the same and survived).
- tests/test_workflow_check.py: a comment on OTHER_SPACE (a word ends at any Unicode white space, the program's `str.split()`, which the registry text does not settle); the folder test's docstring cites TASK-006.md line 159 and the `isfile` reading; the delivery points' control asserts `rc == 1` and an empty standard error.
- Drivers: mutate_workflows_line.py two new mutants, the valid line judged malformed with no rows in each judge (62 of 62, mutate_workflows_line_bug009r2.out); the widened sweep rerun (sweep_wide_r8.out: 351 survivors of 731, r7's less line 228, each in a class).
- Records: docs/HARDENING.md (the line driver's count corrected to five; "BUG-009's gate round 1"; the regenerated round-8 list, the "regex" and "printing" classes' texts and the runs' counts), this file (Requirement 5 corrected to TASK-008-r2.md R2-1).

The sections below are r1's, corrected where r2 says.

No builder ran. Every change is the supervisor's: tests, fixtures and records. No program changed: bridge/cursor-bridge/workflow-check.py, inventory-check.py and conformance-check.py are byte-identical to origin/main 23a1971.

## Scope (what this increment is)
Stage B2's review, round 8 (snapshot STAGE-B2h, 44705eb): Review B APPROVE; Review A REJECT on two parts (fixtures 2, tests), with fixtures 3 and fixtures 4 converging on the same class: rules of the workflow check no test fails for (ISS-007, recurring since round 5). Every finding is taken here or recorded in docs/HARDENING.md, "the stage review (round 8)", which lists each with its disposition. Rather than add the operators of one more finding, the widened sweep is given every white-space reading of each regex literal and a space dropped from each short string literal at once (run/supervisor/regex_mutants.py), and what it then found is killed by BUG-009's second cases or recorded by class.

## Out of scope
- Any change to the three programs. The programs' leads stay for the next change of workflow-check.py (an unlistable folder's ERROR order; line 323's backslash, with 342 and 360; 626's (e)-and-stop, now pinned by BUG-008's of-type tests as the program does it; the trailing-space heading reading).
- Design for later increments (TASK-010's carve and its rename of the registry's Phase column) is not this diff's defect; the routing is recorded.
- The judges' docstrings and the texts' core-floor wording (round 8's programs and texts considers), recorded for the next change of those files.

## The tests the supervisor wrote, and what each enforces
- tests/test_workflow_check.py, first cases (round 8's findings):
  - test_r014_the_four_forms_take_one_space_and_no_other_white_space — bridge/cursor-bridge/workflow/extension-points.md, "How a conditional workflow names a point", with the program's R3-6: each form with a tab, two spaces, a space and a tab, a no-break space, a form feed, a vertical tab or an ideographic space in place of any one of its spaces, indented one to three spaces, or with white space after it is (form); with such white space straight after `##` (other than a space or tab), indented four spaces, a tab or a no-break space it is prose; each form as written gives nothing. 135 variants, each a root of its own, in one run (fixtures 2, blocking).
  - test_r014_round8_the_loosened_heading_files_hold_their_headings — presence check: the 25 and the 11 `##` lines of form-heading-trailing-text and form-misspelt-change-word, whose identical (form) lines would not show an edited heading (fixtures 2, considers).
  - test_r014_a_folder_named_like_the_type_file_is_no_type_file — handoff/TASK-006.md (d): a folder named `types/<type>.md` is no type workflow; the folder's own (d) and the sub-workflow's (d) (tests, consider; `isfile` read as `exists`).
  - STATUS_EXACT: e-same-part-three's third line names the unknown trait Glitter, so a part's third line is still checked (fixtures 3); form-part-colon-no-space (new) — a part prefix's colon needs its space in a several-part head (fixtures 4); the comments on form-bad-prefix-single and form-trait-repeat-separated (fixtures 4, considers).
  - ROUND5_PRECONDITIONS: form-no-line holds `Workflows:Web App Development; traits: none`, a Workflows line without its space, which is no Workflows line (fixtures 4).
  - FILE_EXACT kind-two-backticks: a sub-workflow (new file) sets the delivery kind to a lone backtick, which is no pair and is printed as itself (the first sweep's line 485, `>= 2` read as `>= 1`, separable once its number operator worked); d-unknown-sub-type-key's file adds at `nowhere.at-all`, still checked (fixtures 1, consider).
  - Round 7's carried considers: an in-test control in test_r014_the_delivery_rules_apply_at_their_two_points_exactly (the two points exactly: (kind) on each) and in test_r015_loaded_as_a_module_the_check_runs_nothing (under `__main__` it runs and exits 2).
- tests/test_workflows_line_check.py, first cases:
  - test_r015_the_bytecode_switch_is_restored_when_the_checker_cannot_be_loaded[judge × how] — handoff/TASK-008-r2.md R2-1, the judges' restore in a `finally`: each judge loads workflow-check.py with the checker absent, not compiling, or exiting at load, and `sys.dont_write_bytecode` is back to its earlier value afterwards (tests, should-fix: the switch put back after a good load only survived).
- BUG-009's second cases (the widened sweep's separable survivors, sweep_wide_r6.out):
  - test_r014_the_four_forms_take_each_of_their_spaces_and_a_key — the same section of extension-points.md: each form's words separated by one space, its key or kind a word; a form with a space dropped or its key or kind left out is (form) where the line is a change heading (R3-4) and prose otherwise; 17 variants (fourteen (form), three prose controls).
  - test_r014_a_tab_is_no_fence_indent[opening-backticks, opening-tildes, closing] — R4-3 and R5-3: a fence is indented by zero to three spaces; a run after a tab opens no fence and closes none.
  - tests/test_workflows_line_check.py test_r015_placement_reads_the_prefixes_with_their_space — supervisor.md "Project state": check_placement places only `Workflows: ` and `Phase: ` lines, each with its space.

## The mutation drivers and the sweeps (local, run/supervisor/, readable)
- mutate_workflow_check.py: 23 named mutants for the first cases and 16 for the second, one per rule above; 300 of 300 killed (mutate_workflow_check_bug009b.out).
- mutate_workflows_line.py: five for the first and second cases (the bytecode switch put back after a good load only, once in each judge, and the three placement prefixes; 60 of 60, mutate_workflows_line_bug009b.out), two for r2 (below).
- sweep_workflow_check.py: its number operator now builds each mutant at the match's own position (it had made no mutant). 799 mutants, 754 compile, 49 survive after both sets of cases (sweep_workflow_check_r13.out): round 6's list less line 626, which BUG-008's of-type tests kill, with line 357's `2 -> 1`, equivalent as its dropped clause.
- sweep_wide.py with regex_mutants.py (new): every white-space reading of each regex literal (each space as a tab, any white space, a run, optional; the start indented; the end with trailing white space or anything; `\S+` as `[^ ]+`, `.+`, `\S*`; the indent's bound and class; the class after `##`; `re.I`) and each short string literal with one space dropped (read from the line's string tokens, one mutant per run of spaces). WIDESWEEP
- write_survivor_list.py (`--check`) and write_wide_list.py stop on a survivor no reason or class names.

## Expected bookkeeping and record files in the diff
docs/HARDENING.md (the round-8 section, with the generated class list), docs/PROJECT_STATUS.md, run/review/ (these review files).
