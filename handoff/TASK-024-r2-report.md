# TASK-024 round 2 report

## Files changed

- `bridge/cursor-bridge/conformance-check.py` (docstring of `calibration_workflows_grades` only)
- `bridge/cursor-bridge/MANIFEST.json` (regenerated)
- `tests/test_calibrate_program.py`
- `tests/test_workflows_line_check.py` (`test_r015_conformance_bridge_line_unwritten_is_missing_and_trait_note` only)

## Summary

Round 2 corrected TASK-024 calibration tests so they assert bridge copies with `check_status` preconditions, exact printed rows (no substring checks), a three-part multipart case, escape-character coverage for unwritten `f` findings and trait names, exact `intake` phase handling, and a tie between `calibration_workflows_grades` and `check_status` on a three-part status file. The grading function’s docstring now documents the `not-checked` return shape. Program logic is unchanged apart from that docstring.

## Requirements 1–11

| Req | Test or code change |
|-----|---------------------|
| 1 | `test_r027_r033_unwritten_product_type`, `test_r027_r033_unwritten_sub_type`, `test_r027_r033_unwritten_trait_on_written_names` |
| 2 | `test_r027_r033_multipart_mixed` |
| 3 | `test_r027_r033_unwritten_finding_output_is_escaped_ascii` |
| 4 | `test_r027_r033_not_yet_classified_past_intake`, `test_r027_r033_phase_first_word_only`, `test_r027_r033_unwritten_sub_type`, `test_r027_r033_unwritten_trait_on_written_names` |
| 5 | `test_r027_r033_phase_word_escaped_in_classification_note` |
| 6 | `test_r027_r033_unwritten_trait_name_escaped` |
| 7 | `test_r027_r033_intake_comparison_is_exact` (parametrised); case (b) unchanged |
| 8 | `test_r015_conformance_bridge_line_unwritten_is_missing_and_trait_note` |
| 9 | `calibration_workflows_grades` docstring in `conformance-check.py` |
| 10 | No code change (per-part parse unchanged) |
| 11 | `test_r027_r033_grades_match_check_status_on_three_part_file` |

## Verification commands

From `<Workspace>`:

- `python tools/dump-cli.py --check` — exited 0 (no output).
- `python tools/make-manifest.py --version 2026.10.25a` — `make-manifest: version 2026.10.25a, 140 files hashed, VERSION + MANIFEST.json written`
- `python -m pytest tests/test_calibrate_program.py tests/test_workflows_line_check.py tests/test_conformance_check.py tests/test_b2_least_confident.py -q --no-header -p no:cacheprovider` — `130 passed, 2 skipped in 25.52s`

## Mutation list

Each mutation was applied to `conformance-check.py` in a local run, the listed test was run, then the file was restored. No mutated code remains in the tree.

| Mutation | Test that failed |
|----------|------------------|
| `field(mod, phase)` → raw `phase` in classification NOTE | `test_r027_r033_phase_word_escaped_in_classification_note` |
| `field(mod, name)` → raw `name` in Unwritten trait NOTE | `test_r027_r033_unwritten_trait_name_escaped` |
| `phase != "intake"` → `not phase.startswith("intake")` | `test_r027_r033_intake_comparison_is_exact[intakes-intakes]` |
| `phase != "intake"` → `"intake" not in phase` | `test_r027_r033_not_yet_classified_at_intake` |
| Sort NOTE list so all Unwritten trait rows precede classification | `test_r027_r033_grades_match_check_status_on_three_part_file` |
| Print NOTE rows before Workflows line row in `main()` | `test_r027_r033_multipart_mixed` |
| Drop sub-type `f` findings from `f_items` | `test_r027_r033_unwritten_sub_type` |
| Skip `check_traits` in per-part FLAG collection | `test_r027_r033_grades_match_check_status_on_three_part_file` |

## Assumed, not verified

- Cases (a) and (j) still rely on the Workspace open list marking the bridge status names written, without copying or asserting that on a bridge copy · round 1 left them that way and Requirement 12 says they stay · a future brief could add copy-based preconditions.
- `calibration_workflows_grades` matches `check_status` on status files other than the Requirement 11 three-part fixture · only that one in-process test compares them · broader equivalence would need more fixtures.
- Open-list row replacements that target a `yes` Written cell are no-ops when the live list already has `no`, but preconditions on the copy still assert the intended `check_status` outcome · confirmed for the current `<Workspace>` list at test time, not for every future list edit.
- Renaming the `Personal data` trait row in the copy for Requirement 6 still loads tables successfully · asserted in the test precondition · not tried with every possible rename shape.
