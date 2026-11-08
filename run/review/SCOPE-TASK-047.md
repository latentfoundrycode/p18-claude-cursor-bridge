# SCOPE — TASK-047 (release B2's status-file header in its six readers), Review B round 2

Where the increment ends: the status file's header read first by `loop-guard.py`, `session-start.py`, `conformance-check.py`, `workflow-check.py --status`, `inventory-check.py` and `evaluate-reports.py` through `bridge_env.status_values`, the one prose fallback per field in `bridge_env` (`status_fallback`, `status_workflows`, `status_workflow_line`, `STATUS_WORKFLOWS_PROBLEMS` and their private helpers), the malformed and disagreement lines, `inventory-check.py`'s caps counting the body after the header, conformance-check loading `bridge_env.py` beside its real file, and `MANIFEST.json`'s hashes. The other records' headers (the plan, the briefs, the inventory, the register, the index, the deviations file, the run parameters) are TASK-048 to TASK-050; the migration of this repository's records is TASK-054. Design for those later increments is not this diff's defect.

## This round: what changed since Review B's round 1

Review B's round 1 (snapshot TASK-047-r1, head a592aa8) approved rounds 1 to 3. CI on the pull request then failed one test on ubuntu-latest, which Windows here skips (no symbolic-link privilege). Round 4 fixed it: the commits after 3bac886, which are d977515 (the supervisor's test), d7d9c3c (the brief), 47cd690 (the builder's one-line fix in `bridge/cursor-bridge/conformance-check.py`, line 98, and the regenerated `MANIFEST.json`, `docs/BUILDER_NOTES.md`, the round's report) and the records commit after it. The whole branch diff is under review; round 4's change is the new part.

Blocking class: failing test - CI on PR #138, bridge programs (ubuntu-latest), run 42359390308: tests/test_workflows_line_check.py::test_r015_checker_is_found_beside_the_real_file_not_the_link[conformance-check.py]

That line lifted the ceiling for round 4. The commit round 4's builder was launched on, with its brief: d7d9c3c. Confirm or deny the line against the code at d7d9c3c (conformance-check's `_load_bridge_env` building its path from `HERE`, the link's folder), never against the fixed code.

## The briefs' Scope, quoted

Round 1 (handoff/TASK-047.md): bridge/cursor-bridge/bridge_env.py, loop-guard.py, session-start.py, conformance-check.py, workflow-check.py, inventory-check.py, evaluate-reports.py, MANIFEST.json; docs/cli-reference.json, docs/CLI_REFERENCE.md; tests/test_header_status.py (only below its marker line), test_loop_guard.py, test_session_start.py, test_session_start_module.py, test_conformance_check.py, test_workflows_line_check.py, test_workflow_check.py, test_evaluate_reports.py (only added cases, or a correction of a test pinning a retired reading (1) to (4)); docs/BUILDER_NOTES.md; the round's report.

Round 2 (handoff/TASK-047-r2.md): the same files and the round's report; the test files changed only as its harness limits say (a copy of `bridge_env.py` beside a copied checker; the windowless flag on one launch line).

Round 3 (handoff/TASK-047-r3.md): bridge/cursor-bridge/bridge_env.py, workflow-check.py, MANIFEST.json (regenerated only), docs/BUILDER_NOTES.md, the round's report; every test file out of scope.

Round 4 (handoff/TASK-047-r4.md): bridge/cursor-bridge/conformance-check.py, MANIFEST.json (regenerated only), docs/BUILDER_NOTES.md, the round's report; every test file out of scope. In conformance-check, only the path `_load_bridge_env` builds; the stand-in module, the `sys.path` insertion and the other uses of `HERE` (lines 94, 833, 1119, 1351) stay.

## The briefs' Out of scope, quoted in short

- .env, secrets/, CI configuration; docs/ and handoff/ except the files named; every record under docs/ is the supervisor's.
- The other records' headers (TASK-048 to TASK-050), `records-migrate.py` (TASK-051), the retired readings (5) to (11) of the design's list.
- Any edit of `read_header`, `check_header`, `header_agrees`, `HeaderError`, `HEADER_SCHEMAS` or the reader's private helpers (TASK-046's code).
- The loop guard's run-parameters comparisons and its `Ceiling above twice:` regex (TASK-049, TASK-050).
- Round 4: every other program, and every finding earlier briefs named out of scope.
- Any mutation script.

## The threat model

None is recorded in `docs/INVENTORY.md`'s Decisions for these readers, so the five blocking classes stand unbounded. The status file is text the supervisor writes; a builder or a reviewer can write it too, so a security finding is judged by whether such input can reach it. Round 4's trust boundary: a program run through a link loads its own modules from beside its real file, never from beside the link (R-015's R2-2).

## The rounds and the ceiling

The review guard has counted 1 round for TASK-047; this snapshot, `TASK-047-r2`, opens round 2. The launcher has counted 4 builder rounds (2026-11-07T03:09:49Z, 2026-11-07T04:20:18Z, which ended at its limit with its work kept, ISS-030, 2026-11-07T06:59:53Z, and 2026-11-07T09:40:22Z), so the increment is above the ceiling of three: grade every finding by the five blocking classes first (behaviour against the brief or the register, security, data integrity, a defeated safety mechanism the increment relies on, a failing test). A finding of the five must reproduce as a regression or a false result on an ordinary, realistic status file or install; one that needs a contrived setup goes to `docs/HARDENING.md`.

## The tests the supervisor wrote, and the paragraph each enforces

`tests/test_header_status.py`, above its marker line, is the supervisor's, written before each builder round (commits f95403c, 62602e9, 3dc9c97, d977515) and after the mutation sweep (8e4c778); its docstring names the design's paragraphs it enforces (`docs/DESIGN.md`, Change: release B2, "The records and their headers", "The fallback readers, one copy each", "Header first; fallback; malformed"), the requirement R-058 and D-002. Round 4's test, `test_r058_r4_conformance_check_loads_bridge_env_beside_its_real_file`, enforces R-015's R2-2 for `bridge_env.py`: it emulates a link by replacing `os.path.realpath` in a child process and requires the loaded `bridge_env` to hold `status_workflow_line` and `status_values`. Its 157 tests against the checkpoint f68a883 (`mutation-run.py --checkpoint`): 157 failing on old code, none passing, none not run. The builder's edits to other test files are within the limits quoted above.

## The mutants and the driver

`run/supervisor/TASK-047-mutants.json`, written by the supervisor's driver `run/supervisor/task047_mutants_make.py` (not in this diff; gitignored working files), whose docstring states the operator set by each id's first letter: F the fallback taken where a header exists, R a refusal removed, C a comparison inverted, K a key dropped, H a retired reading restored, B a bound raised. 48 mutants over bridge_env and the six programs (round 4 added one: conformance-check's path back to `HERE`): 47 expected killed on a named set of failing tests, one `expect: survive` (h07, the unterminated body's lone `---`, which no prose reader matches). The mutation run: "counts: run=48 cached=0 killed=47 survived=0 not applied=0 error=0 expected survive=1", exit 0. The full suite with the pull request's variables on round 4: "4579 passed, 40 skipped in 1895.88s (0:31:35)".

## Bookkeeping and record files in the diff that are expected

- the briefs `handoff/TASK-047.md`, `handoff/TASK-047-r2.md`, `handoff/TASK-047-r3.md`, `handoff/TASK-047-r4.md` and the builder's reports `handoff/TASK-047-r1-report.md` to `-r4-report.md` (round 1's with two computer paths redacted by the supervisor before its commit, rule 54)
- the supervisor's records: `docs/INVENTORY.md` (the Features row), `docs/REQUIREMENTS.md` (R-058 built), `docs/HARDENING.md` (TASK-047's section), `docs/PROJECT_STATUS.md` (as at this pull request's merge, #138)
- `run/review/` (this file, the round's diff and its assumptions file)

## Already recorded, not new

`docs/HARDENING.md`, TASK-047's section: round 2's findings outside the five on an ordinary layout (the CR kept on a raw string; the printable-ASCII test; conformance-check's `project.json` comparison without `bridge_env`; the three `escape_field` copies; the checkers' `hasattr` test of `status_values` only; loop-guard's import without a sink), the audit's advisories (a Markdown rule on a header-less file's first line; a partial install's fail-open), round 1's kept decisions (a package or `.pyd` loaded first; the path shown; `read_status` kept), round 3's notes (the unreachable branch; two empty names; a part named three times; the report's missing sentence), round 4's notes (conformance-check's `sys.path.insert(0, HERE)` at line 94 putting the link's folder first, a planted `argparse.py` reached through a file symlink when it loads workflow-check; a hard link loading the `bridge_env.py` beside it; the Calibrated row's shown path at line 833), and the correction to TASK-028's note on line 94.
