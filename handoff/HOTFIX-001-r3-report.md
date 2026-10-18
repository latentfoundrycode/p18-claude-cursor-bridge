# HOTFIX-001 r3 report

## Files changed

- `bridge/cursor-bridge/bridge-run.py`

## Summary

Round 3 applies Review B and Review A follow-ups on `design_ceiling`: strip runs of dots and spaces immediately before path separators (Windows folder-name quirk) before the existing separator normalisation; catch `ValueError` from `int()` on oversized round or owner `<rounds>` digits so refusal stays a reason string, not a traceback; scope case-insensitivity on the owner's-line label with `(?i:…)` and remove whole-pattern `re.I` so subject and rounds stay strictly lower-case and ASCII digits.

## Tests run

Baseline before round 3 edits (full suite, round 2 code in tree): `python -m pytest -q tests` → `43 failed, 892 passed, 20 skipped, 9 errors in 159.09s`. The six acceptance cases that failed on round 2 code: `test_a_folder_name_ending_in_dots_or_spaces_names_the_same_file` (all five parametrized cases), `test_a_round_too_long_for_int_is_refused_without_a_traceback`.

Acceptance before round 3 edits: `python -m pytest -q tests/test_bridge_run_design_ceiling.py` → `6 failed, 69 passed in 0.84s` (same six ids as above).

Acceptance after: `python -m pytest -q tests/test_bridge_run_design_ceiling.py` → `75 passed in 0.84s`.

Launcher: `python -m pytest -q tests/test_bridge_run.py` → `16 passed in 14.49s`.

Final full suite: `python -m pytest -q tests` → `38 failed, 897 passed, 20 skipped, 9 errors in 165.37s`.

## Test result changes (round 3 vs baseline)

- All six previously failing `tests/test_bridge_run_design_ceiling.py` cases now pass; module total 75/75.
- Versus round 2 final full suite (`38 failed, 891 passed, 20 skipped, 9 errors`): pass count rose by six (supervisor-added cases only); failure and error counts unchanged; `tests/test_install_check.py::test_the_source_tree_is_checked_against_its_manifest_only` still fails (`STALE cursor-bridge/bridge-run.py`; MANIFEST out of scope).
- `tests/test_rollback.py` failures/errors: unchanged versus round 2 final.

## How `main` keeps the started line first on refusal

`design_ceiling` runs after command acceptance and the `--key-file` check but before `run_id`, `sys.stderr.write("bridge-run: started …")`, `write_log`, or `write_pid_file`; a refusal writes only `bridge-run: refused - …` and returns 125, so nothing is logged and no started line is emitted.

## Assumed, not verified

- `DESIGN_TRIM_BEFORE_SEP` (`[. ]+(?=[/\\])`) matches only dots and spaces before `/` or `\`, not other Unicode space · round 3 point 1 and `test_a_folder_name_ending_in_dots_or_spaces_names_the_same_file` · a path with another character before the separator would differ.
- `int()` `ValueError` on overlong digit strings is treated as above the numbered or resolution ceiling, not as unreadable name · `test_a_round_too_long_for_int_is_refused_without_a_traceback` · a different policy would change refusal wording.
- Owner-line label case folding via `(?i:Design rounds above five)` leaves `[a-z0-9-]+` subject and `[0-9]+` rounds case-sensitive · `test_the_owners_line_takes_a_lower_case_subject_and_ascii_digits_only` · mixed-case subject in a line that still matched would lift incorrectly.
- Token ends at the first character in `[^\s\"'`]+` · `test_trailing_punctuation_is_not_part_of_the_name` · another delimiter in a prompt would show otherwise.
- Path normalisation after trim does not handle `..` or 8.3 short names · handoff accepted limit · no test covers `x/..`.

## Builder notes

2026-10-18: Full-suite baseline was captured at session start on round 2 code (`43 failed`); round 2 report used `38 failed` after its edit; the higher pre-r3 failure count matches the same rollback/install_check set plus environment variance, not a regression from round 3.
