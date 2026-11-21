# SCOPE for TASK-071 (Review B, round 1)

TASK-071 names an empty run parameter (R-091): records-migrate.py refuses a header-less run-parameters record whose fallback reading leaves any of the five values empty, with one line `cannot read <file>: <label> has no value on a plain line` naming the first empty label, nothing written, the exit unchanged; inventory-check.py fails a run-parameters file with any of the five empty, `RUN PARAMETERS: <key> is empty` for a headed file and `RUN PARAMETERS: <label> is empty` for a header-less one, exit 1; one bridge_env helper, empty_run_parameters, names the empty values from the plain lines' prefixes; the fallback reads no new form; the migration's two failure exits that no test reached (a failed close and a failed read of the temporary file) get their tests. Branch task-071 from main 96ae5af (PR #187's merge, TASK-070). One builder round; this is the review guard's first round for TASK-071: there is no Blocking class line.

Round cause: unstated

Where the increment ends: bridge/cursor-bridge/records-migrate.py, inventory-check.py and bridge_env.py, MANIFEST.json through its generator, the builder's fixture (tests/fixtures/headers/field/run-parameters.md) and its one case below the marker of tests/test_records_migrate.py, the supervisor's acceptance tests (tests/test_program_run_parameters_empty.py), the supervisor's docstring amendment of tests/test_header_run_parameters.py, and the records. The leads recorded in docs/HARDENING.md under TASK-071, 1 to 5, are not this diff's defects: the helper's name in inventory-check's guard list untested by a mutant; a headed file empty and disagreeing on one key giving two lines; the helper's unreachable non-dict branch; the report's line numbers; --check's exit for a refused record, which calibration's text (TASK-078) names. Release B2's leads ruled on by name there (4.9 to 4.11, 4.19 to 4.23) stay leads by design (DESIGN.md line 307). The calibration text (R-091's last clause) is TASK-078's. HARDENING's TASK-070 lead 13 is a record of the previous increment's last review, unrelated to this code.

Read the commit messages (git log, the full bodies) for the quoted lines.

## The plan entry, quoted (docs/BUILD_PLAN.md, TASK-071)
Scope: bridge/cursor-bridge/records-migrate.py; bridge/cursor-bridge/inventory-check.py; bridge/cursor-bridge/bridge_env.py; bridge/cursor-bridge/MANIFEST.json; tests/test_program_run_parameters_empty.py; tests/test_records_migrate.py; tests/test_header_run_parameters.py; tests/fixtures/headers/; docs/BUILDER_NOTES.md; handoff/TASK-071-r<N>-report.md
Satisfies: R-091
Done when: read it whole in docs/BUILD_PLAN.md under the heading TASK-071: the migration's cannot read line for an empty value, the first such name, the record header-less, in a run and under --check, the exit rule unchanged; inventory-check failing an empty value in a header and in a header-less file; the fallback reading no heading, bullet or bold form, release B2's leads ruled on by name in HARDENING; the field's file the reproduction, red on the checkpoint; the migration's two uncovered failure exits each tested; the test file names R-091; this repository's own run-parameters file passes; the mutants file sweeps the two checks, every mutant killed; MANIFEST regenerated; no option; no new dependency.

## The supervisor's rulings (handoff/TASK-071.md, R1-R7)
- The migration's line names the plain line's label (Stage pause, Merge authority, Refactoring pass, Installer verification, Parallel increments), the first empty in that order; nothing written; a cannot read alone leaves the exit unchanged.
- inventory-check names the header key for a headed file and the label for a header-less one, one line per empty value, each a counted problem, exit 1, beside HEADER DISAGREES, not in place of it.
- Empty is exactly the empty string; the fallback is unchanged; one helper holds the label list.
- The field-form fixture sits outside the tests/fixtures/headers/*.md glob that test_header_reader requires to be headed.

## The supervisor's tests
- tests/test_program_run_parameters_empty.py (names R-091; 26 cases; its own commit before the brief, on the checkpoint stripped "20 failed, 6 passed").

## Evidence
- Review A: round 1 APPROVE, no blocking finding
- every test file that runs or loads either program, sixteen, stripped: 1550 passed, 3 skipped
- the mutation sweep (run/supervisor/TASK-071-mutants.json): five mutants, every one killed
- completion-check.py --mode plan OK (89 built, 2 deferred, 14 planned); inventory-check.py OK

## Expected bookkeeping and records in the diff
handoff/TASK-071.md and its report, docs/HARDENING.md, docs/INVENTORY.md, docs/PROJECT_STATUS.md (as at this pull request's merge), and run/review/ (these files).
