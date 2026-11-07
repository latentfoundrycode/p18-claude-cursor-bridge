# SCOPE — TASK-047 (release B2's status-file header in its six readers), Review B round 1

Where the increment ends: the status file's header read first by `loop-guard.py`, `session-start.py`, `conformance-check.py`, `workflow-check.py --status`, `inventory-check.py` and `evaluate-reports.py` through `bridge_env.status_values`, the one prose fallback per field in `bridge_env` (`status_fallback`, `status_workflows`, `status_workflow_line`, `STATUS_WORKFLOWS_PROBLEMS` and their private helpers), the malformed and disagreement lines, `inventory-check.py`'s caps counting the body after the header, and `MANIFEST.json`'s hashes. The other records' headers (the plan, the briefs, the inventory, the register, the index, the deviations file, the run parameters) are TASK-048 to TASK-050; the migration of this repository's records is TASK-054. Design for those later increments is not this diff's defect.

## The briefs' Scope, quoted

Round 1 (handoff/TASK-047.md): bridge/cursor-bridge/bridge_env.py, loop-guard.py, session-start.py, conformance-check.py, workflow-check.py, inventory-check.py, evaluate-reports.py, MANIFEST.json; docs/cli-reference.json, docs/CLI_REFERENCE.md; tests/test_header_status.py (only below its marker line), test_loop_guard.py, test_session_start.py, test_session_start_module.py, test_conformance_check.py, test_workflows_line_check.py, test_workflow_check.py, test_evaluate_reports.py (only added cases, or a correction of a test pinning a retired reading (1) to (4)); docs/BUILDER_NOTES.md; the round's report.

Round 2 (handoff/TASK-047-r2.md): the same files and the round's report; the test files changed only as its harness limits say (a copy of `bridge_env.py` beside a copied checker; the windowless flag on one launch line).

Round 3 (handoff/TASK-047-r3.md): bridge/cursor-bridge/bridge_env.py, workflow-check.py, MANIFEST.json (regenerated only), docs/BUILDER_NOTES.md, the round's report; every test file out of scope.

## The briefs' Out of scope, quoted in short

- .env, secrets/, CI configuration; docs/ and handoff/ except the files named; every record under docs/ is the supervisor's.
- The other records' headers (TASK-048 to TASK-050), `records-migrate.py` (TASK-051), the retired readings (5) to (11) of the design's list.
- Any edit of `read_header`, `check_header`, `header_agrees`, `HeaderError`, `HEADER_SCHEMAS` or the reader's private helpers (TASK-046's code).
- The loop guard's run-parameters comparisons and its `Ceiling above twice:` regex (TASK-049, TASK-050).
- Any mutation script.

## The threat model

None is recorded in `docs/INVENTORY.md`'s Decisions for these readers, so the five blocking classes stand unbounded. The status file is text the supervisor writes; a builder or a reviewer can write it too, so a security finding is judged by whether such input can reach it.

## The rounds and the ceiling

The review guard has counted 0 rounds for TASK-047; this snapshot, `TASK-047-r1`, opens round 1. The launcher has counted 3 builder rounds (2026-11-07T03:09:49Z, 2026-11-07T04:20:18Z, which ended at its limit with its work kept, ISS-030, and 2026-11-07T06:59:53Z), so a fix needing a fourth builder round needs a `Blocking class:` line: grade every finding by the five blocking classes first (behaviour against the brief or the register, security, data integrity, a defeated safety mechanism the increment relies on, a failing test). A finding of the five must reproduce as a regression or a false result on an ordinary, realistic status file; one that needs a contrived setup goes to `docs/HARDENING.md`. This round carries no `Blocking class:` line.

## The tests the supervisor wrote, and the paragraph each enforces

`tests/test_header_status.py`, above its marker line, is the supervisor's, written before each builder round (commits f95403c, 62602e9, 3dc9c97) and after the mutation sweep (8e4c778); its docstring names the design's paragraphs it enforces (`docs/DESIGN.md`, Change: release B2, "The records and their headers", "The fallback readers, one copy each", "Header first; fallback; malformed"), the requirement R-058 and D-002. Its 156 tests against the checkpoint f68a883 (`mutation-run.py --checkpoint`): 156 failing on old code, none passing, none not run. The builder's edits to other test files are within the limits quoted above.

## The mutants and the driver

`run/supervisor/TASK-047-mutants.json`, written by the supervisor's driver `run/supervisor/task047_mutants_make.py` (not in this diff; gitignored working files), whose docstring states the operator set by each id's first letter: F the fallback taken where a header exists, R a refusal removed, C a comparison inverted, K a key dropped, H a retired reading restored, B a bound raised. 47 mutants over bridge_env and the six programs: 46 expected killed on a named set of failing tests, one `expect: survive` (h07, the unterminated body's lone `---`, which no prose reader matches). The mutation run (`run/agent/TASK-047-mutation.out`): "counts: run=47 cached=0 killed=46 survived=0 not applied=0 error=0 expected survive=1", exit 0. The full suite on 3f63558: "4573 passed, 41 skipped".

## Bookkeeping and record files in the diff that are expected

- the briefs `handoff/TASK-047.md`, `handoff/TASK-047-r2.md`, `handoff/TASK-047-r3.md` and the builder's reports `handoff/TASK-047-r1-report.md`, `-r2-report.md`, `-r3-report.md` (round 1's with two computer paths redacted by the supervisor before its commit, rule 54)
- the supervisor's records: `docs/INVENTORY.md` (the Features row), `docs/REQUIREMENTS.md` (R-058 built), `docs/HARDENING.md` (TASK-047's section), `docs/PROJECT_STATUS.md` (as at this pull request's merge, #138)
- `run/review/` (this file, the round's diff and its assumptions file)

## Already recorded, not new

`docs/HARDENING.md`, TASK-047's section: round 2's findings outside the five on an ordinary layout (the CR kept on a raw string; the printable-ASCII test; conformance-check's `project.json` comparison without `bridge_env`; the three `escape_field` copies; the checkers' `hasattr` test of `status_values` only; loop-guard's import without a sink), the audit's advisories (a Markdown rule on a header-less file's first line; a partial install's fail-open), round 1's kept decisions (a package or `.pyd` loaded first; the path shown; `read_status` kept), round 3's notes (the unreachable branch; two empty names; a part named three times; the report's missing sentence).
