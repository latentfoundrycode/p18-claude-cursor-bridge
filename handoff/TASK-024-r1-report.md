# TASK-024 round 1 report

## Files changed

- bridge/cursor-bridge/conformance-check.py
- bridge/cursor-bridge/MANIFEST.json
- tests/test_calibrate_program.py (new)
- tests/test_workflows_line_check.py
- tests/test_b2_least_confident.py
- docs/cli-reference.json
- docs/CLI_REFERENCE.md
- handoff/TASK-024-r1-report.md

## Summary

Calibration’s conformance program now grades conditional workflows after `judge_workflows_line` returns valid: unwritten product types or sub-types (`f`) print a MISSING `Workflows line` with per-finding detail; unwritten traits (`FLAG`) print NOTE `Unwritten trait` rows while leaving the line OK when no `f` is present; `not yet classified` bodies past `Phase: intake` print NOTE `Workflows classification` with the Phase first word only, never MISSING. `judge_workflows_line` is unchanged. Tests cover cases (a)–(j); the bridge-line conformance case and `plain_notes` baseline were updated; CLI reference and manifest were regenerated.

## Mutation list

| Mutation | Test that caught it |
| --- | --- |
| Drop `f` findings (always OK on unwritten type) | `test_r027_r033_unwritten_product_type` |
| Stop emitting FLAG as NOTE | `test_r027_r033_unwritten_trait_on_written_names` |
| Invert intake comparison (`phase == "intake"` emits classification NOTE) | `test_r027_r033_not_yet_classified_at_intake` |
| Print whole Phase line text instead of first word | `test_r027_r033_phase_first_word_only` |
| Print NOTE rows before the `Workflows line` row | `test_r027_r033_not_yet_classified_past_intake` (order assertion) |
| Remove `escape_field` from unwritten-workflow detail | `test_r027_r033_unwritten_finding_output_is_escaped_ascii` |

## Verification

Ran `python -m pytest tests/test_calibrate_program.py tests/test_workflows_line_check.py tests/test_b2_least_confident.py tests/test_conformance_check.py tests/test_conformance_check_a4.py tests/test_a4_review_fixes.py tests/test_a4_followups.py tests/test_hotfix25a_conformance_semgrep.py tests/test_dump_cli.py -q --no-header -p no:cacheprovider` — **254 passed, 2 skipped** in about 118s.

Also ran the full suite `python -m pytest tests -q --no-header -p no:cacheprovider` — **2189 passed, 33 skipped, 40 failed, 9 errors** in about 405s; failures were confined to `tests/test_install_check.py`, `tests/test_install_check_a4.py`, and `tests/test_rollback.py` (environment/install fixtures), not to files in this task’s scope.

`python tools/dump-cli.py --check` passes after regenerating `docs/cli-reference.json` and `docs/CLI_REFERENCE.md`.

`python tools/make-manifest.py --version 2026.10.25a` — 140 files hashed, MANIFEST.json updated.

## Assumed, not verified

Assumed, not verified: none.
