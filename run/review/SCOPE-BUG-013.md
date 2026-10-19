# SCOPE — BUG-013 (stage B2's review, round 11: string-method cases)

The diff at `run/review/REVIEW-BUG-013.diff` is branch `bug-013` against `main` (its merge base, e1a97de, after `main` was merged in), the `run/review/` records left out.

## What it answers

Stage B2's review, round 11 (Review B, grok-4.7-medium, the native profile): REJECT, because rules of the workflow check (`bridge/cursor-bridge/workflow-check.py`) rewritten with another string method survived every test. Its named cases: the delivery-kind membership tests made on the kind case-folded (lines 527, 530, 536); a Changes cell split on `", "` or its parts lowered; a separator cell's colons removed with `lstrip(':')` or its dashes tested with `"-" in text`; the table reader and the heading candidate fed a stripped line; the placement prefixes read after `lstrip()` or `lower()`; a head split on `", "`; `casefold` made `lower`; a slice made a strip. The round's full record is `docs/HARDENING.md`, "Stage B2 — the stage review (round 11, 2026-10-18)".

## What the diff changes

**No program.** The workflow check and its judges are unchanged. The tests are the supervisor's (N4 permits tests), written from the supervisor's string-method sweep (`run/supervisor/sweep_strings.py`: from the program's syntax tree, every strip, case, split, prefix, regex-argument, comparison, slice and path mutant on one-line nodes), each test enforcing the paragraph or brief its docstring names:

- `tests/test_workflow_check.py`: the round's named cases and the sweep's cases, in the second round-11 block at the file's end and in the fixtures and exact outputs it pins (FILE_EXACT, STATUS_EXACT, STRING_STATUS_CASES). Each enforces `bridge/cursor-bridge/workflow/open-list.md` "How this file is read", `bridge/cursor-bridge/workflow/extension-points.md`, `bridge/commands/supervisor.md` "Main and conditional workflows" and "Project state" (the `Workflows:` grammar), or the brief of the increment that built the rule (`handoff/TASK-006.md`, `TASK-007.md`, `TASK-008.md`), as each docstring says.
- `tests/test_workflows_line_check.py`: test_r015_placement_reads_the_prefixes_exactly, test_r015_placement_reads_whole_lines_by_their_prefix and test_r015_conformance_a_status_folder_is_no_status_file, the last with its positive control (`supervisor.md` "Project state", the judges' placement rule; `conformance-check.py`'s reading of the status file).
- After Review A (gate round 1, APPROVE with should-fixes): test_r014_a_name_ending_in_a_no_break_space_is_no_conditional_workflow_file (a name ending in U+00A0 after `.md`, which NTFS keeps, so the case runs on Windows and not only on CI's ubuntu leg), and the control above; the HARDENING section's classes regenerated from the confirming sweep that followed.
- Fixtures under `tests/fixtures/workflows/fail/`: `unknown-type-file/types/claude-code-extension.md` and `installable.md`, `unknown-trait-file/traits/web-app.md` (new), and `form-third-level`'s nested `extra.md` (a new body that would give a finding were it read).

The sweep left 202 survivors of 433 on the final tests (`run/supervisor/sweep_strings_r3.out`, confirmed on the committed tests by `_r4`); each is in one class in the HARDENING section, the generator's `--check` stopping on any survivor no class names. Under standing rule 6 those are the recorded long tail of the test-strength class, not this diff's open defects; a new survivor class, or a survivor that a stated input separates, is.

## Records in the diff, expected

`docs/HARDENING.md` (the round-11 section, placed before the hotfix's section); `docs/PROJECT_STATUS.md`, `docs/INVENTORY.md` and `docs/ROSTER.resolved.json` (the calibration to bridge 2026.10.18a, the position after HOTFIX-001's merge, a Decisions row for the hotfix); the merge commit of `main` into the branch.

## Platform skips

On Windows the suite gives 1613 passed and 24 skipped (20 of them test_allowlist.py's prose lines). Of the increment's tests, test_r014_a_name_ending_in_white_space_is_no_conditional_workflow_file skips where the file system trims a trailing space from a name (NTFS) and runs on CI's ubuntu leg; its no-break-space sibling runs everywhere. The other three Windows skips (mode bits, two symbolic links) are earlier tests, also run on the ubuntu leg.
