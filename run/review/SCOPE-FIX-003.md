# SCOPE - FIX-003

FIX-003 hardens one program, the session-start hook `bridge/cursor-bridge/session-start.py`, before TASK-012 writes the first module pointer line. Two builder rounds (composer-2.5): `handoff/FIX-003.md` (round 1) and `handoff/FIX-003-r2.md` (round 2, Review A's should-fix and considers).

## Scope (both briefs)
- bridge/cursor-bridge/session-start.py
- bridge/cursor-bridge/MANIFEST.json and bridge/cursor-bridge/VERSION (only through tools/make-manifest.py)
- docs/cli-reference.json and docs/CLI_REFERENCE.md (only through tools/dump-cli.py)
- docs/BUILDER_NOTES.md
- handoff/FIX-003-r1-report.md, handoff/FIX-003-r2-report.md

## Out of scope (both briefs)
- every file under tests/ (the supervisor's)
- bridge/cursor-bridge/workflow-check.py and every other program under bridge/ or tools/
- the phase table PHASE_MODULES (the reflection.md lead is not this fix)
- the HARDENING leads outside the hook's threat model: checker objects freed after the handler (`__del__`), `atexit` callbacks, threads, `os.write` to file descriptors 1 and 2 or `sys.__stdout__`, the unbounded discard buffer, the stale `.pyc` read
- refactoring `pointers_part`'s nesting
- bridge/cursor-bridge/CHANGELOG.md (no release note for this fix)
- .env, secrets/, CI configuration, .githooks/

## What each round asked
- Round 1: R1 read an exception's type name inside a stdout/stderr redirection of its own (both handlers); R2 a line from the checker's file_lines that is not an exact str raises TypeError, so the part prints `cannot be used (TypeError)` and names no pointer-line or conditional file; R3 no per-path right-strip, a path taken as written between `; ` separators; R4 three docstring edits; R5 the stamps regenerated.
- Round 2: rewrap the two edited docstring paragraphs to at most 94 characters a line, no word changed but one; narrow the non-str sentence to the lines of a phase module file; remove the per-path `type(p) is not str` check, which after R2 cannot fire; the stamps regenerated.

## The tests the supervisor wrote first (tests/test_session_start_module.py), each with what it enforces
- test_r005_a_pointer_line_that_is_not_a_plain_string_names_nothing[sly|plain] (changed: now expects `~/.claude/cursor-bridge/workflow-check.py: cannot be used (TypeError)`) — R2, R-005's "one plain line" for a checker it cannot use; red against 17f9006.
- test_r005_a_line_that_is_not_a_str_makes_the_checker_unusable[uniform|fence] — R2, the HARDENING lead (Stage B3, TASK-010 with TASK-015, the latent bytes/fence lead); red against 17f9006.
- test_r005_the_type_name_is_read_where_the_checker_cannot_print[load|use] — R1, the HARDENING lead "the exception's type name is read in the except handler, after the redirection ends"; red against 17f9006.
- test_r005_a_pointer_path_is_taken_as_written_between_separators — R3, the docstring's pointer-line grammar; red against 17f9006.
- test_r005_the_docstring_states_the_grammar_and_the_streams_as_the_code_reads_them — R4 and round 2: the new wording present, the old gone, the narrowed sentence, no docstring line over 94 characters; red against 17f9006 and against 0c491f8 (round 1's code).
No mutation driver: each builder round ran the brief's hand mutation check (undo R1, R2, R3 one at a time), and Review A re-ran it on a scratch copy in round 1.

## Expected bookkeeping and record files in the diff
- handoff/FIX-003.md, handoff/FIX-003-r2.md (the briefs) and handoff/FIX-003-r1-report.md, handoff/FIX-003-r2-report.md (the builder's reports)
- docs/ROSTER.resolved.json (the supervisor's roster resolutions, checkpoint commits)
- docs/HARDENING.md (four leads marked closed, the audit's advisory on the `__del__` lead, a FIX-003 section), docs/INVENTORY.md (the hook's Features row, one Decisions row), docs/REQUIREMENTS.md (R-005's evidence), docs/PROJECT_STATUS.md (as at the merge of PR #54, ISS-009)
- run/review/ (these review files)
