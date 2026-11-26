# TASK-087d round 1 report

## Summary

Replaced the separate `_profile_in_use` helper with a single `_evaluate_profile` function (lines 1220-1351) that applies the resolve loop's skip order, pool and mark exclusions, rebuild or deviation prelude, and probe answers; both `--review-alt` (lines 1353-1411, `verbose=False`) and the plain resolve loop (lines 1416-1435, `verbose=True`) call it so the request acts on the same profile the resolve would pick. Updated the module docstring roster example and `--review-alt` paragraph; regenerated MANIFEST and CLI reference via the prescribed tools.

## Files changed

- `bridge/cursor-bridge/roster-check.py`
- `bridge/cursor-bridge/MANIFEST.json` (via `make-manifest.py`)
- `docs/cli-reference.json` (via `dump-cli.py`)
- `docs/CLI_REFERENCE.md` (via `dump-cli.py`)
- `handoff/TASK-087d-r1-report.md`

## Requirements (functions and lines)

1. One reading of the profile in use: `_evaluate_profile` at lines 1220-1351; callers at 1355-1364 (`--review-alt`) and 1417-1435 (plain resolve).
2. Request never passes to a later profile: `--review-alt` loop breaks on the first non-`None` result from `_evaluate_profile` (1355-1364); missing alternate refuses on that profile only (1369-1372).
3. Every refusal kept: existing `FAIL` paths unchanged at 1154-1163, 1366-1401, and sign-in exit 5 via `_evaluate_profile` / review-alt probe block.
4. Probes: `_probe_roles` and probe branch inside `_evaluate_profile` (1305-1346); alternate probe on grant at 1393-1401.
5. Granted request output: DEVIATION and `chosen` with `deviation` entry at 1403-1410; plain resolve builds `chosen` from `ev` at 1426-1434.
6. Module docstring: roster example lines 16-18 and `--review-alt` paragraph lines 55-57.
7. No new imports or dependencies.

## Mutations (code points and catching tests)

| Label | Function / lines | Expected test |
|-------|------------------|---------------|
| M1 | `_evaluate_profile` 1295-1303 (`r_excl` no independent alt) | `test_task087d_an_exhausted_pool_the_request_acts_on_the_native_profile` |
| M2 | `_evaluate_profile` 1275-1278 (`r_id in unavailable`) | `test_task087d_a_marked_review_b_skips_the_profile_for_the_request_too` |
| M3 | `_evaluate_profile` 1343-1346 (`not ok_rb` skip) | `test_task087d_a_review_b_that_did_not_answer_skips_the_profile_for_the_request_too` |
| M4 | `--review-alt` loop 1362-1364 (remove `break` / continue to next on refuse) | `test_task086a_review_alt_acts_on_the_profile_in_use_alone` |
| M5 | Restore first-builder-only selection (delete `_evaluate_profile` use) | `test_task087d_the_plain_resolve_and_the_request_name_the_same_profile` |
| M6a | malformed reason 1115-1118 | `test_task087d_a_sign_in_ends_the_request_with_exit_5` (exit 2 cases in `test_improve_roster_alt.py`) |
| M6b | built set unreadable 1154-1157 | refusal tests in `test_improve_roster_alt.py` |
| M6c | built set unknown on request 1159-1163 | `test_task086a_review_alt_on_a_set_that_cannot_be_read` / unknown-set tests |
| M6d | no `review_b_alt` 1369-1372 | `test_task087d_with_the_pool_available_the_request_stays_on_the_full_profile` |
| M6e | Review A family 1379-1381 | `test_improve_roster_alt.py` family refusal tests |
| M6f | built branch family 1382-1384 | `test_task087d_after_a_composer_build_the_request_is_refused_by_the_family_cause` |
| M6g | unavailable mark 1385-1387 | `test_improve_roster_alt.py` unavailable alt tests |
| M6h | exhausted pool on alt 1388-1390 | `test_improve_roster_alt.py` pool exhaustion alt tests |
| M6i | unknown family 1376-1378 | `test_improve_roster_alt.py` unknown family alt tests |
| M6j | alt probe failure 1400-1402 | `test_improve_roster_alt.py` probe refusal tests |
| M6k | sign-in exit 5 | `test_task087d_a_sign_in_ends_the_request_with_exit_5` |

## Scratch test files

no scratch test file

## Commands and output

### Step 1 — `git status --short` (pre-edit)

```
(empty)
```

### Step 2 — pre-edit pytest

```
8 failed, 3 passed in 6.03s
```

Failing ids: `test_task087d_an_exhausted_pool_the_request_acts_on_the_native_profile`, `test_task087d_the_plain_resolve_and_the_request_name_the_same_profile`, `test_task087d_a_marked_review_b_skips_the_profile_for_the_request_too`, `test_task087d_after_a_grok_build_the_request_records_the_built_family`, `test_task087d_after_a_composer_build_the_request_is_refused_by_the_family_cause`, `test_task087d_a_review_b_that_did_not_answer_skips_the_profile_for_the_request_too`, `test_task087d_this_repositorys_roster_resolves_the_native_alternate_on_request`, `test_task087d_the_docstrings_roster_example_names_no_alternate_in_the_full_profile`

### Step 3 — `python tools/dump-cli.py` then `python tools/dump-cli.py --check`

```
(exit 0, no stdout)
```

### Step 4 — `python tools/make-manifest.py`

```
make-manifest: version 2026.11.24a, 148 files hashed, VERSION + MANIFEST.json written
```

### Step 5 — `git status --short`

```
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/roster-check.py
 M docs/CLI_REFERENCE.md
 M docs/cli-reference.json
?? handoff/TASK-087d-r1-report.md
```

(`bridge/cursor-bridge/VERSION` not listed; `git restore` not run.)

### Step 6 — pytest roster suites

```
268 passed, 3 skipped in 172.14s (0:02:52)
```

```
SKIPPED [1] tests\test_improve_roster_alt.py:1473: no symbolic link here: ...
SKIPPED [1] tests\test_improve_roster_alt.py:1473: no symbolic link here: ...
SKIPPED [1] tests\test_improve_roster_alt.py:1544: a file name holding a line feed is POSIX-only; CI's Linux job runs it
```

### Step 7 — pytest additional suites

```
194 passed in 220.77s (0:03:40)
```

### Step 8 — `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`

```
bridge-check: version 2026.11.24a (2026-11-26 08:24) at <Workspace>\bridge
bridge-check: 148 OK, 0 STALE, 0 MISSING, 0 EXTRA
RESULT: SOURCES MATCH bridge 2026.11.24a <Workspace>\bridge\cursor-bridge
```

### Step 9 — `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks`

```
windowless-check: 41 file(s) scanned, 0 FAIL, 0 NOTE
```

### Step 10 — ASCII check

```
ascii ok
```

### Step 11 — `git diff --stat HEAD`

```
 bridge/cursor-bridge/MANIFEST.json   |   4 +-
 bridge/cursor-bridge/roster-check.py | 278 ++++++++++++++++++-----------------
 docs/CLI_REFERENCE.md                |  12 +-
 docs/cli-reference.json              |   2 +-
 4 files changed, 155 insertions(+), 141 deletions(-)
```

### Step 12 — `git rev-parse HEAD` and `git status --short`

Commit: `0484070dc9e2675e525c846fa6f306789bb18d9b`

Working tree after tests (uncommitted changes):

```
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/roster-check.py
 M docs/CLI_REFERENCE.md
 M docs/cli-reference.json
?? handoff/TASK-087d-r1-report.md
```

Post-edit acceptance file (same commit base, uncommitted `roster-check.py`):

```
11 passed in 5.97s
```

## Assumed, not verified

Assumed, not verified: none