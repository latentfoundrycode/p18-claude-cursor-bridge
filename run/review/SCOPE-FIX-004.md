# SCOPE - FIX-004

A supervisor increment of tests and records, with no builder run and no program change, like FIX-002 (squash 0a186da on main). Its brief is docs/HARDENING.md, Stage B3, "Least confident (stage close, 2026-10-24)", items 1 and 2, as they read on origin/main.

## Scope
- tests/phase_modules.py: trace_headings moved in from tests/test_phase_modules_close.py; headings(), section() and a new section_span() read through it; a section's title must have one heading in its file, at the requested level.
- tests/test_phase_modules_close.py: its local trace_headings removed, the shared one imported.
- tests/test_b3_least_confident.py (new, supervisor-written, 60 tests).
- Records: docs/HARDENING.md, docs/BUILD_PLAN.md (Scope lines of TASK-017, TASK-018, TASK-022, TASK-030, TASK-035 and TASK-034 only), docs/PROJECT_STATUS.md and project.json as at this pull request's merge.

## Out of scope
- Every program under bridge/, and every phase module's text: nothing there changes.
- The interface variant files' pins in tests/test_phase_modules_close.py (EXCUSED_SECTIONS): unchanged.
- Stage B3's least-confident item 3 (the survival lists on a real resume): left to TASK-030, as HARDENING says.

## The tests the supervisor wrote, and the paragraph each enforces
- test_item1_the_helpers_read_each_module_s_headings_as_trace_check_does (per file under workflow/phases/): item 1. The helpers' headings equal trace-check.py's own parse_units.
- test_item1_the_round4_probe_is_seen: item 1's own proof. The indented ` ### Keeping the position` is listed by headings() and refused by section().
- test_item1_fences_open_and_close_as_trace_check_reads_them: item 1. The fence cases, checked against the helpers and parse_units.
- test_item2_the_pins_are_derived_from_the_entries: item 2. The pin set equals the excused phase-module sections derived from trace-exceptions.md.
- test_item2_each_excused_module_section_has_one_heading_and_is_pinned (42 sections): item 2. One heading per excused title, and the section's length and sha256.

Hand proofs, not in the diff: the round-4 probe passed every old phase-module test in a worktree of origin/main (the release stamp test alone failed, as it does for any byte change) and failed the STRUCTURE test, the position test and the pin with the new helpers; a one-word edit of an excused section and an unpinned new entry each failed item 2's tests. Full suite on the first commit: 2023 passed, 33 skipped.

## Expected bookkeeping and record files in the diff
docs/HARDENING.md, docs/BUILD_PLAN.md, docs/PROJECT_STATUS.md, project.json, and run/review/ (these three files, removed before the merge).

## What to judge
Does each test enforce its paragraph and fail on the defect it targets? Is the helper change behaviour-preserving for every existing caller, the one wider section being design.md's "The gate", now read past a fenced line as trace-check.py reads it? Is the pin set derived right? Are the Scope additions complete for the unmerged increments that edit an excused section? Are the records accurate against the code? Apply the anti-gaming checks: no test weakened, no assertion loosened.
