# SCOPE-BUG-003b — BUG-003 round 2 (PR #29)

The whole diff is `run/review/REVIEW-BUG-003b.diff` (`git diff origin/main...HEAD`, base 0f04c4f). What changed since round 1's reviewed head c20714a is `run/review/DELTA-BUG-003b.diff` (run/review excluded); read the delta first, then the whole.

## Round 1's outcome
Review A APPROVE (0 blocking, 0 should fix, 3 considers); Review B APPROVE (its first reply named nothing from the diff and was not counted; the re-run answered each round-2 finding by file and line, 0/0/1); the security auditor PASS (1 advisory). Converged, so blocking: Review A's consider and Review B's consider named the same line, `test_r014_sub_workflow_changes_are_checked`, which read only the FILE_EXACT table and could fail against no program.

## Round 2 (supervisor only; no builder ran)
- tests/test_workflow_check.py: `test_r014_sub_workflow_changes_are_checked` runs the program on fail/sub-workflow-changes and asserts its three findings exactly (R-014 across the three layers); the driver's mutant "sub-workflow changes not checked" names it too. `test_r014_output_is_ascii_on_every_console` also checks a trait name holding a character up to U+FFFF and one above it (the security auditor's advisory).
- bridge/commands/supervisor.md: a part's name has no whitespace at either end (was "no space"), as `prefix_of`'s `part != part.strip()` checks (Review A); tests/test_workflows_line_text.py's pin follows. MANIFEST.json regenerated.
- docs/HARDENING.md: two leads, the backslash ambiguity of `escape_field` (security auditor) and the `file` kind for a non-folder layer path (Review A); docs/PROJECT_STATUS.md names the second mutation driver (Review A).
- Not taken, recorded: the two leads above.

Checks on HEAD: suite 1228 passed, 23 skipped; the supervisor's driver 87 of 87 killed; secret-sentinel CLEAR; bridge-check SOURCES MATCH; inventory-check OK.

## Round 1's scope, for reference (unchanged)

# SCOPE-BUG-003 — stage B2's review, round 2, fixes (PR #29)

The diff is `run/review/REVIEW-BUG-003.diff` (`git diff origin/main...HEAD`, base 0f04c4f). Stage B2's review, round 2 (2026-10-17), rejected: Review B REJECT (1 blocking, 2 should fix, 1 consider); Review A's six parts all APPROVE, but three fixture parts named one weakness (a case asserts only its named finding, so a second finding can hide it), which converges and so blocks. Every finding and how it was taken is in docs/HARDENING.md, "Stage B2 — the stage review (round 2, 2026-10-17)".

## The builder's part (handoff/BUG-003.md; report handoff/BUG-003-r1-report.md)
Scope: bridge/cursor-bridge/workflow-check.py (`escape_field` with its docstring, and `collect`), MANIFEST.json (regenerated), docs/BUILDER_NOTES.md, the report. Out of scope: every test, fixture and text; inventory-check.py and conformance-check.py (their `ascii_text` wrapper stays, its output unchanged).
- Defect 1 (Review B): `escape_field` kept every printable character, non-ASCII included, so a finding line's bytes depended on the console's encoding (a name with é left as the raw byte 0xE9 under cp1252). Fix: a character stays only when printable and ASCII; the escape forms are unchanged and equal what `encode("ascii", "backslashreplace")` gives.
- Defect 2 (Review B): `collect` skipped a `types` or `traits` path that exists and is not a folder, so a malformed root passed. Fix: it is recorded as a layer link is, and reported by the same (form) line.
The builder's `Assumed, not verified` list: none.

## The supervisor's part (commits before the checkpoint 90f7d9e)
Tests (tests/test_workflow_check.py), each enforcing R-014 (and R-015 for the status cases):
- `FILE_EXACT` / `STATUS_EXACT` with `test_r014_file_case_gives_exactly_its_findings` and `test_r014_status_case_gives_exactly_its_findings`: every failing root under fail/ and every status file under status/ asserts its whole output of FAIL and FLAG lines, in order, and its exit code; `test_r014_every_case_has_its_exact_findings` keeps the tables complete. The lists were taken from the program's output and read against each fixture by hand; the review's three fixture parts had each run every case and confirmed what it gives.
- New fixtures: fail/sub-workflow-changes (a valid sub-workflow with an unknown point, a set at an add-only point and a replace of a non-replaceable module: a, set, c; Review B blocking) with `test_r014_sub_workflow_changes_are_checked`; status/form-part-empty, -semicolon, -arrow, -colon (the part-name rules, reached only in a file of several lines; Review B and fixtures part 3).
- Reproduction tests for the builder, failing on the checkpoint: `test_r014_output_is_ascii_on_every_console[utf-8, cp1252]` and `test_r014_layer_path_that_is_a_file_is_form`. The exact entry for status/form-part-arrow.md expects the arrow escaped (`\u2192`); it passed on Windows before the fix only because cp1252 cannot encode the arrow.
- Preconditions: the indented fences of fail/fence-indented-close and fail/form-indented-fence-open, the sub-workflow's `## Add at interface.variants` in the pass root; `assert_clean_end` added to the T-B1 and b-and-a tests; a vacuous assertion message dropped; the trait-in-head docstring qualified (PR 28's Review A).
- tests/test_open_list.py: `test_r011_the_names_a_workflows_line_reads_are_unique_across_the_tables` (the sentence it pins is new in open-list.md).
- tests/test_workflows_line_text.py: two pins follow supervisor.md's rewording.
Texts: supervisor.md's Workflows paragraph (the line stands directly after `Phase:`, as check_placement requires; a part's name is not empty and has no space at either end, as prefix_of requires); open-list.md (a part fitting a sub-type takes it, so an unwritten sub-type pauses; the names a Workflows line reads are unique across the tables); tests/fixtures/workflows/pass/README.md (three delivery kinds, not two). MANIFEST.json regenerated.
Mutation driver (run/supervisor/mutate_workflow_check.py, supervisor-side, temporary copies): 87 mutants, all killed; new: sub-workflow changes not checked, empty-name finding dropped, part-name characters not checked, empty part name accepted, printable non-ASCII kept, non-folder layer skipped; retired as equivalent: top-level link tested after isdir (after the fix both branches report alike, so the order changes no output).

## Records (expected bookkeeping)
docs/DESIGN_CRITIQUE.md (BUG-002's security-auditor rows; PR 28's grades and disposition), docs/HARDENING.md (round 2's routing), docs/PROJECT_STATUS.md, handoff/BUG-003.md and its report.

Checks on HEAD: scope-check SCOPE CLEAN; suite 1228 passed, 23 skipped (the skips environmental); secret-sentinel CLEAR; bridge-check SOURCES MATCH; inventory-check OK.
