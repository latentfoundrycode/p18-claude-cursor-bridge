# BUG-036 builder report

## Initial git status

```
(clean — no output from git status --porcelain)
```

## Files changed

- `bridge/cursor-bridge/review-guard.py`
- `handoff/BUG-036-r1-report.md`

## Pre-edit test run

Command: `$env:PYTHONDONTWRITEBYTECODE = "1"; python -m pytest -q -p no:cacheprovider tests/test_bug036.py`

Exit code: 1. Summary: `3 failed in 2.19s` (all three `test_bug036_*` tests failed as expected).

## What changed

Added `_release_b_builder_rounds`, which reads `run/launcher/runs.jsonl` via `bridge_env.launcher_log_folder` and `bridge_env.read_runs_jsonl`, collects round numbers from rows with `kind` `"builder"`, `brief` equal to the increment ID, and `round` an `int` that is not a `bool`. Updated `_report_file_rounds` to take the maximum report `<N>` only among tracked `handoff/<ID>-r<N>[letter]-report.md` files whose `<N>` is not in that set, with a one-line comment stating the rule. `_seed_rounds` is unchanged aside from calling the updated `_report_file_rounds`.

## Verification (post-fix)

1. `tests/test_bug036.py` — exit 0, `3 passed in 4.52s` (final re-run after mutations).
2. `tests/test_task032_supervisor_guard.py` + `tests/test_task032_supervisor_r4.py` — exit 0, `147 passed in 119.99s` (final re-run).
3. Broad review-guard set (deselect `test_r003_...`) — exit 0, `529 passed, 1 deselected in 178.13s`.
4. Mutations (each reverted before the next):
   - **(a) Row exclusion dropped** (`logged = set()` in `_report_file_rounds`): exit 0 pytest but `3 failed, 143 passed` — all three `test_bug036_*` tests failed; caught the regression.
   - **(b) `kind == "builder"` check removed**: exit 0, `146 passed in 117.76s` — nothing caught it (review rows carry no `brief`, so they never entered the set anyway).
   - **(c) Match via `brief_name` regex instead of `brief` + `round`**: exit 0, `146 passed in 118.99s` — nothing caught it; test 3 still passed because cross-ID rows use a different `brief_name` prefix.
5. `git diff --quiet HEAD -- tests/` — exit 0 (`tests_diff:0`). `git status --porcelain` and `git diff --stat`:

```
 M bridge/cursor-bridge/review-guard.py
?? handoff/BUG-036-r1-report.md
 bridge/cursor-bridge/review-guard.py | 20 +++++++++++++++++++-
 1 file changed, 19 insertions(+), 1 deletion(-)
```

## Summary

The guard no longer seeds Review B rounds from builder report files when release B's launcher already logged a builder row for the same increment ID and round, so builder-only history under release B leaves the counted Review B rounds at zero until the first snapshot, while pre-install report files without matching builder rows still seed as before.

## Named cause

`_seed_rounds` used `_report_file_rounds`'s maximum over all tracked reports; excluding rounds that have a matching release-B builder row in `runs.jsonl` stops builder report files from inflating the seeded reply count.

## Mutations

| Mutation | Result |
|----------|--------|
| (a) No row exclusion | All three `test_bug036_*` failed |
| (b) No `kind == "builder"` | No test failed |
| (c) `brief_name` instead of `brief`/`round` | No test failed |

## Assumed, not verified

- A `handoff/<ID>-r<N><letter>-report.md` file is excluded from the seed when `<N>` has a release-B builder row for that ID, even though the letter suffix is ignored for launcher `round` · the brief requires comparing report `<N>` from the existing regex to the row's `round` field only · a test with a letter-suffixed report and a builder row for the same `<N>` would confirm.
- Launcher rows with `kind` `"builder"` but missing `brief` or `round` never occur in practice · malformed rows are skipped by `_valid_log_row` or fail the `brief`/`round` checks · reading `bridge-run.py` production paths or log samples would confirm.
- `read_runs_jsonl` on a missing log yields no builder rounds so all reports still count · `bridge_env.read_runs_jsonl` swallows `OSError` · already implied by existing guard tests that seed from reports without a log.
