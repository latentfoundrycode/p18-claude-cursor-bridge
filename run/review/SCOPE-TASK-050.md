# SCOPE for TASK-050 (Review B, round 1)

The increment: TASK-050, the run parameters' header (R-061; R-057 flips built here, its last clause the currency test). Branch task-050 from main 52d18be (PR #140's merge). Two builder rounds (composer-2.5, native profile): round 1 (handoff/TASK-050.md, commit 8c35020) and round 2 (handoff/TASK-050-r2.md, commit 7b45aa1); this is the review guard's first round for the increment, below the ceiling of three; no Blocking class line.

Where the increment ends: docs/RUN_PARAMETERS.md's header read first by bridge-run.py, review-guard.py and loop-guard.py through bridge_env, compared by inventory-check.py, with the one copy of each line reading in bridge_env. The migration program, the templates and this repository's records gaining headers (TASK-051 to TASK-054) are later increments, not this diff's defect. This repository's docs/RUN_PARAMETERS.md stays header-less in this increment.

## The supervisor's tests, each with the paragraph it enforces
- tests/test_header_run_parameters.py (committed 4e58e84, before the checkpoint; above its marker): enforces docs/DESIGN.md, Change: release B2, "The fallback readers, one copy each" and "Header first; fallback; malformed", and handoff/TASK-050.md R1 to R8 (the fallback's nine keys, the values, the refusal, the launcher's, the guard's, the loop guard's and inventory-check's behaviour, no program keeping its own line reading). Below its marker: the builder's cases.
- tests/test_header_currency.py (committed 4e58e84; above its marker): enforces R-057's currency clause and the design's "The retired readings, enumerated" (eleven readings matched as uses over twelve programs; every kind's schema and fallback; every key typed).
- tests/test_header_run_parameters_r2.py (the supervisor's whole): the reproduction tests of round 1's findings (1b4b3fd; enforces handoff/TASK-050.md R13, R8, R5 and R1, R2 and R3: a real 0xff byte, inventory-check's guard, a lift at or below its default lifting nothing, lines ending at a line feed only, an unreadable Agent ceiling line skipped, linear time) and the criterion tests from the mutation sweep (8cd17f2: CRLF and lone-CR text reads as with line feeds; a header with a schema finding is malformed at line 1 in the values, the refusal and inventory-check; a header-less review lift lifts only above three).

## The mutants
run/supervisor/TASK-050-mutants.json (33 mutants over bridge_env's run-parameters readers, the launcher's, the guard's and the loop guard's refusals and inventory-check's check; operators F the fallback taken where a header exists, R a refusal removed, C a comparison inverted, K a key dropped from the fallback, H a retired reading restored), written by run/supervisor/task050_mutants_make.py; new_tests by run/supervisor/task050_new_tests.py (86 ids, all failing on 52d18be, mutation-run --checkpoint exit 0). The mutation run: "counts: run=33 cached=0 killed=29 survived=0 not applied=0 error=0 expected survive=4", exit 0; the four expected survivors (f02, f04, f05, f06) are the header read first or the lines in a reader whose every caller refuses a disagreeing header on that key first, so they are equivalent in the programs; judge that claim.

## The threat model
docs/INVENTORY.md, Decisions (ASVS level 2, D-004): docs/RUN_PARAMETERS.md is the owner's record, written by the supervisor on the owner's words, but a builder or a reviewer can write a file in the checkout, so a gate program refuses rather than guesses and a header lift with no matching owner's line, or at or below its default, never lifts a ceiling; the loop guard, a hook, fails open on a malformed header and refuses the stop on a disagreement. A security finding is judged by whether such untrusted input reaches it.

## Expected bookkeeping and records in the diff
docs/BUILDER_NOTES.md (if touched), handoff/TASK-050.md, handoff/TASK-050-r2.md, handoff/TASK-050-r1-report.md, handoff/TASK-050-r2-report.md, bridge/cursor-bridge/MANIFEST.json (regenerated), and the supervisor's records commits: docs/INVENTORY.md (the intake hotfix's Decisions row of 2026-11-08 and TASK-050's feature row), docs/PROJECT_STATUS.md (as at PR #141's merge), docs/HARDENING.md (TASK-050's section), docs/REQUIREMENTS.md (R-061 and R-057 built), and run/review/ (these files).

## The briefs' Scope and Out of scope, quoted

### handoff/TASK-050.md

#### Scope
Files and directories you may create or modify:
- bridge/cursor-bridge/bridge_env.py
- bridge/cursor-bridge/bridge-run.py
- bridge/cursor-bridge/loop-guard.py
- bridge/cursor-bridge/review-guard.py
- bridge/cursor-bridge/inventory-check.py
- bridge/cursor-bridge/MANIFEST.json
- tests/test_header_run_parameters.py
- tests/test_header_currency.py
- tests/test_loop_guard.py
- tests/test_bridge_run_design_ceiling.py
- tests/test_bridge_run_review_ceiling.py
- tests/test_review_guard_ceiling.py
- tests/test_release_b_bootstrap.py
- docs/BUILDER_NOTES.md
- handoff/TASK-050-r1-report.md

Limits on these files:
- `bridge/cursor-bridge/MANIFEST.json` changes only as regenerated by `python tools/make-manifest.py`. Never edit it by hand.
- `tests/test_header_run_parameters.py` and `tests/test_header_currency.py` are the supervisor's, committed at the checkpoint 4e58e84. In each, add your own cases only below its marker line, which reads exactly `# ---------------------------------------------------------------- builder's cases below this line`. Edit nothing above that line.
- `tests/test_loop_guard.py`, `tests/test_bridge_run_design_ceiling.py`, `tests/test_bridge_run_review_ceiling.py` and `tests/test_review_guard_ceiling.py`: you may only add cases (the header path beside the existing line cases). Do not rewrite or delete an existing test. If you find one that pins a retired reading, do not change it: name it by its test id in your report and in your last message.
- `tests/test_release_b_bootstrap.py`: add the header-path cases beside the existing tests, which stay; the one existing test you change is `test_r001_run_parameters_owner_values` (Requirement 10).

Do not modify anything else.

#### Out of scope
- .env and anything under secrets/
- CI configuration
- docs/ and handoff/, except the files the Scope section names. Every record under docs/ is the supervisor's: `RUN_PARAMETERS.md` itself (this repository's file stays header-less in this increment), `REQUIREMENTS.md` (R-057's and R-061's rows are flipped by the supervisor's records commit, never by you), `BUILD_PLAN.md`, `DESIGN.md`, `INVENTORY.md`, `HARDENING.md`, the diagrams, `cli-reference.json` and `CLI_REFERENCE.md` (no command changes).
- Every test file not listed in the Scope, including the existing tests that exercise the moved readers (they must stay green unchanged; Requirement 9).
- TASK-046's reader code in `bridge_env.py` (`read_header`, `check_header`, `header_agrees`, `HeaderError`, `HEADER_SCHEMAS` and their private helpers), TASK-047's status readers, TASK-048's brief and plan readers and TASK-049's tabular readers: call them, change none. The one earlier function you change is `review_owner_lifts` (header first, Requirement 2).
- `records-migrate.py` and writing headers into any record (TASK-051, TASK-054).
- The leads `docs/HARDENING.md` records for TASK-046 to TASK-049, among them: the duplicated helpers of TASK-047's section (the `escape_field` copies, `_safe_exc_type_name`, `_bridge_env_refuse_line` copied between workflow-check and inventory-check; add no copy of these or of any helper); loop-guard's import without a stdout sink (TASK-047 C2); the partial-install tracebacks (TASK-047 C1 and C3, TASK-049 A-2) in programs this increment does not touch; the refusal prefix spelled in bridge_env and the doubled `PlanFileReadRefusal` prefix (TASK-048 H-6, A4); TASK-046's dead code and its A2 (format characters). Act on none of them, beyond the guard extensions Requirements 6 and 7 name for the names this increment calls.
- Refusal, help and usage texts that quote a line's form (for example bridge-run.py lines 39-40, 452, 747 and 1562, and loop-guard.py's comments and docstrings): leave them as they stand.
- Any mutation script. The mutants file and the mutation run are the supervisor's.

### handoff/TASK-050-r2.md

#### Scope
Files you may modify:
- bridge/cursor-bridge/bridge_env.py
- bridge/cursor-bridge/bridge-run.py
- bridge/cursor-bridge/inventory-check.py
- bridge/cursor-bridge/MANIFEST.json
- tests/test_header_run_parameters.py
- tests/test_bridge_run_design_ceiling.py
- docs/BUILDER_NOTES.md
- handoff/TASK-050-r2-report.md

Limits on these files:
- `bridge/cursor-bridge/MANIFEST.json` changes only as regenerated by `python tools/make-manifest.py`. Never edit it by hand.
- `tests/test_header_run_parameters.py`: the one change is R1's deletion of the case `test_r061_loop_guard_reads_agent_ceiling_with_a_non_utf8_byte` (lines 464-468 at 1b4b3fd, below the marker line `# ---------------------------------------------------------------- builder's cases below this line`). Nothing above the marker changes; no other case below it changes; add no case.
- `tests/test_bridge_run_design_ceiling.py`: the one change is R4's (Requirement R4 says exactly what).
- `tests/test_header_run_parameters_r2.py` is the supervisor's reproduction file: read it whole, change nothing in it, add no case to it.
- Round 2 adds no test case of yours anywhere.

Do not modify anything else.

#### Out of scope
- .env and anything under secrets/
- CI configuration
- docs/ and handoff/, except the files the Scope section names. Every record under docs/ is the supervisor's (`RUN_PARAMETERS.md`, `REQUIREMENTS.md`, `BUILD_PLAN.md`, `DESIGN.md`, `INVENTORY.md`, `HARDENING.md`, the diagrams, `cli-reference.json`, `CLI_REFERENCE.md`).
- `loop-guard.py` and `review-guard.py`: round 1's code there stands (R1's product code is already right; the B1 case passes on it).
- Every test file not named in the Scope, including `tests/test_header_currency.py`, `tests/test_loop_guard.py`, `tests/test_bridge_run_review_ceiling.py`, `tests/test_review_guard_ceiling.py` and `tests/test_release_b_bootstrap.py`: they must stay green unchanged.
- Recorded by the supervisor in `docs/HARDENING.md`, not to be acted on in this round: the empty words after the date (a lift whose parenthesis is only `, YYYY-MM-DD`); `run_parameters_refusal`'s fail-open on a read error after `isfile` and its second read; the loop guard taking the first readable `RUN_PARAMETERS.md` among the status candidates; the duplicated value logic between `run_parameters_values`, `run_parameters_refusal` and inventory-check (no refactoring in this round); the BOM-first-line lift (accepted).
- Everything round 1's brief (`handoff/TASK-050.md`, Out of scope) put out of scope stays out of scope: TASK-046's reader code (`read_header`, `check_header`, `header_agrees`, `HeaderError`, `HEADER_SCHEMAS` and their helpers), TASK-047's status readers, TASK-048's brief and plan readers and TASK-049's tabular readers (call them, change none; the other `splitlines()` calls in `bridge_env.py`, at lines 457, 517, 651, 813, 823, 2952, 3007, 3024, 3039, 3221, 3266 and 3280, belong to those readers and stay); the duplicated helpers (`escape_field`, `_safe_exc_type_name`, `_bridge_env_refuse_line`; add no copy of any helper); refusal, help and usage texts; `records-migrate.py` and writing headers into any record; any mutation script.
