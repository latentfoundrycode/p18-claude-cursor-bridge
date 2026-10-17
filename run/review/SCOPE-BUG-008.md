# SCOPE — BUG-008 (stage B2's review, round 7: fixes)

No builder ran. Every change is the supervisor's: tests, fixtures, two sentences of governance text, the regenerated manifest, and records. No program changed: bridge/cursor-bridge/workflow-check.py, inventory-check.py and conformance-check.py are byte-identical to origin/main e20382a.

## Scope (what this increment is)
Stage B2's review, round 7 (snapshot STAGE-B2g, 99d5b83): Review B APPROVE; Review A REJECT on two parts, with two more parts converging on the same class. Every finding is taken here or recorded in docs/HARDENING.md, "the stage review (round 7)", which lists each with its disposition. The class (rules of the workflow check that no test fails for) has recurred since round 5 (ISS-007), so the supervisor's mutation sweep is widened and its survivors are killed or recorded by class.

## Out of scope
- Any change to the three programs. The programs' leads (an unlistable folder's ERROR order; the case of a Written or Replaceable cell; line 323's backslash; 626) stay for the next change of workflow-check.py.
- Design for later increments (TASK-010's rename of the registry's Phase column, TASK-011's placement wording) is not this diff's defect; their routing is recorded.

## The tests the supervisor wrote, and what each enforces
- tests/test_workflows_line_check.py:
  - test_r015_conformance_prints_each_finding_in_order — handoff/TASK-008.md Requirement 7: the malformed row is `malformed: ` and every finding `name - reason`, joined by `; `, in the judge's order, the placement's last (round 7: tests, blocking).
  - NOT_LOADABLE's `registry-absent` case, and the not-loadable tests of both programs now asserting each cause whole for the three rule-file cases (`_causes`, from the copy's own reader) and one cause for the load failures — Requirements 5 and 7: one line per cause, `<path>: <reason>`, joined by `; ` in conformance's row.
- tests/test_workflow_check.py:
  - FILE_EXACT form-heading-trailing-text (24 lines) — extension-points.md "How a conditional workflow names a point": the four forms matched exactly, one space between words, nothing after the key or the kind, not even a space; a `##` line is a heading only when a space or tab follows (the round-7 fixtures 2 finding and the widened sweep's lines 65 to 68 and 78).
  - FILE_EXACT form-not-markdown (6 lines) — the same section: a path that is not a conditional workflow at its key's path, here names ending `md` without the dot.
  - STATUS_EXACT form-traits-none-first, -none-last, form-prefix-missing-unclassified, form-unclassified-leading-space, -ending — supervisor.md "Project state", the Workflows grammar: `none` is the whole traits text; the part prefix applies to every line where several lines carry one, `not yet classified` included; `not yet classified` is the exact rest.
  - test_r014_separator_cell_count_differs[second-cell-not-dashes] — the rule files' "How this file is read": every separator cell is dashes.
  - test_r014_every_unreadable_file_is_reported — the program's usage text and R4: each ERROR line, then `RESULT: not checked`.
  - test_r014_round7_fixtures_hold_their_controls and test_r014_round7_trailing_spaces_are_bytes_of_the_fixture — presence checks: each fixture holds the text that makes its case a control (the pass root's ```` ```+ ```` inside a fence and `## Look atop the target` / `## Go combat it` as prose included).
  - Strengthened: test_r014_usage_error_ends_with_result_line (the usage line on standard error), test_r014_top_level_link_is_form_and_not_walked (the whole output), test_r014_change_word_with_punctuation_is_form (the ten headings), test_r014_commonmark_fence_cases_read_the_set (the inner run of fence-info-string-not-closing).

## The mutation drivers and the sweeps (local, run/supervisor/, readable)
- mutate_workflow_check.py: 20 new named mutants, one per rule above (220 of 220 killed, mutate_workflow_check_bug008.out).
- mutate_workflows_line.py: 13 new named mutants of the judges (55 of 55, mutate_workflows_line_bug008.out).
- sweep_wide.py (new): workflow-check.py with the new operators (regex literal loosened, string comparison widened, `".md"` shortened, a loop cut to `[:1]`, a join separator changed), and each judge's function and its printing lines with every operator. 370 compiling mutants: 255 survived before (sweep_wide_r1.out), 213 after (sweep_wide_r2.out); write_wide_list.py writes HARDENING's list by class and stops on a survivor no class names.
- sweep_workflow_check.py rerun (sweep_workflow_check_r11.out): the same 49 survivors as round 6's list.

## Expected bookkeeping and record files in the diff
docs/HARDENING.md (the round-7 section, with the generated class list), docs/PROJECT_STATUS.md, bridge/cursor-bridge/MANIFEST.json (regenerated for the two text sentences), run/review/ (these review files).

## Text changes (governance, the supervisor's)
- bridge/commands/supervisor.md, the Workflows grammar's traits bullet: "each at most once" (round 7: texts; check_traits fails a repeat).
- bridge/cursor-bridge/Glossary.md, the Workflow check entry: the judges use its "grammar and placement checks" (round 7: texts).
