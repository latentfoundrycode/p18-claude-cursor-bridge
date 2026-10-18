# HOTFIX-001 r1 report

## Files changed

- `bridge/cursor-bridge/bridge-run.py`

## Summary

Added `design_ceiling(argv, folder)` and helpers in `bridge-run.py` to scan joined `cursor-agent` arguments for `run/review/DESIGN-<name>.md` paths (case-insensitive folders, either separator), parse subject and round, enforce the default ceiling (numbered rounds 1–5 and `R1`) or an owner's `Design rounds above five:` line in `docs/RUN_PARAMETERS.md`, and return a one-line `design ceiling:` reason when a name is unreadable or over the ceiling. `main()` calls it immediately after the `--key-file` refusal and returns 125 before kind, limit, or `bridge-run: started`. One module docstring line documents the refusal.

## Tests run

Baseline (before edits): `python -m pytest -q tests` → `76 failed, 835 passed, 20 skipped, 9 errors in 274.86s (0:04:34)`. Failing ids: all 51 in `tests/test_bridge_run_design_ceiling.py`; 25 in `tests/test_rollback.py` (listed in baseline log); 9 errors in `tests/test_rollback.py` (same log).

Acceptance: `python -m pytest -q tests/test_bridge_run_design_ceiling.py` → `51 passed in 0.76s`.

Launcher: `python -m pytest -q tests/test_bridge_run.py` → `16 passed in 13.76s`.

Final full suite: `python -m pytest -q tests` → `38 failed, 873 passed, 20 skipped, 9 errors in 161.35s (0:02:41)`.

## Test result changes

- All 51 `tests/test_bridge_run_design_ceiling.py` cases: failed → passed.
- `tests/test_install_check.py::test_the_source_tree_is_checked_against_its_manifest_only`: passed → failed (`STALE cursor-bridge/bridge-run.py`; MANIFEST not restamped per scope; supervisor restamps).
- Twelve further `tests/test_install_check.py` and `tests/test_install_check_a4.py` cases failed in the final run (install/check flows that copy the source tree and hit the stale manifest); they were not in the baseline failure list and are attributed to the same unstamped `bridge-run.py` edit, not to design-ceiling logic.
- `tests/test_rollback.py` failures and errors: unchanged in count and ids versus baseline (25 failed, 9 errors).

## How `main` keeps the started line first on refusal

`design_ceiling` runs after command acceptance and the `--key-file` check but before `run_id`, `sys.stderr.write("bridge-run: started …")`, `write_log`, or `write_pid_file`; a refusal writes only `bridge-run: refused - …` and returns 125, so nothing is logged and no started line is emitted.

## Assumed, not verified

Assumed, not verified: none.

## Builder notes

2026-10-18: Baseline full-suite run took ~4.5 minutes while design-ceiling tests were still failing; parallel work started after baseline began but before it finished.
