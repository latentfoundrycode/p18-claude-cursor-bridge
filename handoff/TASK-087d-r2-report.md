# TASK-087d-r2 report

## One-paragraph summary

Round 2 removes the duplicate `review_b_alt` probe on `--review-alt` when `_evaluate_profile` already probed the alternate during profile selection: evaluation records `alt_probe_ok` (`True`, `False`, or `None` when no alternate probe ran) on its result dict, the request path keeps `in_use_ev` from the same evaluation, and after the existing static refusals it reuses that value instead of calling `probe` again when it is not `None`. Regenerated `MANIFEST.json` via `make-manifest.py`; `dump-cli.py` left `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` unchanged. All 14 acceptance tests and the Done step 6 and 7 batches pass at commit `5835a557e99715173d58862102e610be5a65cda6` with uncommitted changes in `roster-check.py` and `MANIFEST.json`.

## How the second probe is removed

The request path reads `in_use_ev["alt_probe_ok"]` after the static refusals: a stored `False` emits the existing `did not answer its probe` FAIL and exit 1 without calling `probe`; stored `True` grants with no second call; only `None` keeps the prior single `probe(a_id)` block with its printed line and sign-in handling.

## Requirements 1–7 (where met)

1. One reading of the profile in use: `_evaluate_profile` and the request loop at `main()` lines 1356–1369 share one evaluation per profile.
2. No later profile: request loop breaks on first non-skipped `_evaluate_profile` result (lines 1366–1369).
3. Refusals unchanged: malformed reason 1115–1118; unreadable built set 1154–1157; unknown built set 1159–1163; no profile 1370–1372; no alternate 1375–1377; unknown family 1381–1383; Review A family 1384–1386; built family 1387–1389; marked 1390–1392; pool 1393–1395; alternate probe 1407–1411 and 1410–1411; sign-in 1361–1362, 1402–1405, and evaluation probe returns.
4. Probes: alternate probed in `_evaluate_profile` 1316–1320 with `alt_probe_ok` stored; request reuses 1398–1412.
5. Granted request output: DEVIATION at 1420 unchanged; plain resolve loop 1426+ unchanged.
6. Module docstring: not edited this round.
7. No new imports, dependencies, or options.

## Files changed

- `bridge/cursor-bridge/roster-check.py`
- `bridge/cursor-bridge/MANIFEST.json`

## Commands and output

### Step 1 (before edit)

```
```

### Step 2 (before edit)

```
........FFF...                                                           [100%]
3 failed, 11 passed in 7.51s
```

Failing ids: `test_task087d_r2_after_a_grok_build_the_alternate_is_probed_once_on_request`, `test_task087d_r2_a_marked_review_b_the_alternate_is_probed_once_on_request`, `test_task087d_r2_an_alternate_that_did_not_answer_is_refused_on_its_one_answer`

### Step 3

```
```

(both `python tools/dump-cli.py` and `python tools/dump-cli.py --check` exited 0)

### Step 4

```
make-manifest: version 2026.11.24a, 148 files hashed, VERSION + MANIFEST.json written
```

### Step 5 (after step 4)

```
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/roster-check.py
```

(`bridge/cursor-bridge/VERSION` not listed; no restore)

### Step 6 (after last edit)

```
........................................................................ [ 26%]
.............................................................ss..s...... [ 52%]
........................................................................ [ 78%]
..........................................................               [100%]
271 passed, 3 skipped in 172.16s (0:02:52)
```

Commit: `5835a557e99715173d58862102e610be5a65cda6`; working tree uncommitted: ` M bridge/cursor-bridge/MANIFEST.json`, ` M bridge/cursor-bridge/roster-check.py`

### Acceptance file only (after last edit)

```
..............                                                           [100%]
14 passed in 11.06s
```

Commit: `5835a557e99715173d58862102e610be5a65cda6`; same uncommitted files.

### Step 7

```
........................................................................ [ 37%]
........................................................................ [ 74%]
..................................................                       [100%]
194 passed in 218.30s (0:03:38)
```

### Step 8

```
bridge-check: version 2026.11.24a (2026-11-26 08:44) at <Workspace>\bridge
bridge-check: 148 OK, 0 STALE, 0 MISSING, 0 EXTRA
RESULT: SOURCES MATCH bridge 2026.11.24a <Workspace>\bridge\cursor-bridge
```

### Step 9

```
windowless-check: 41 file(s) scanned, 0 FAIL, 0 NOTE
```

### Step 10

```
ascii ok
```

### Step 11

```
 bridge/cursor-bridge/MANIFEST.json   |  4 ++--
 bridge/cursor-bridge/roster-check.py | 26 ++++++++++++++++++--------
 2 files changed, 20 insertions(+), 10 deletions(-)
```

### Step 12

```
5835a557e99715173d58862102e610be5a65cda6
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/roster-check.py
```

## Mutation table

| Label | Function / lines | Test id |
|-------|------------------|---------|
| M1 | `_evaluate_profile` / `_r_excluded` 1215–1216, 1250 | `tests/test_improve_review_alt_profile.py::test_task087d_an_exhausted_pool_the_request_acts_on_the_native_profile` |
| M2 | `_evaluate_profile` 1240–1243, 1275–1278 | `tests/test_improve_review_alt_profile.py::test_task087d_a_marked_review_b_skips_the_profile_for_the_request_too` |
| M3 | `_evaluate_profile` 1345–1348 | `tests/test_improve_review_alt_profile.py::test_task087d_a_review_b_that_did_not_answer_skips_the_profile_for_the_request_too` |
| M4 | `main()` request loop 1366–1369 | `tests/test_improve_roster_alt.py::test_task086a_review_alt_acts_on_the_profile_in_use_alone` |
| M5 | `main()` request loop 1366–1369 | `tests/test_improve_review_alt_profile.py::test_task087d_with_the_pool_available_the_request_stays_on_the_full_profile` |
| M6a | `main()` 1115–1118 | `tests/test_improve_roster_alt.py::test_task086a_review_alt_refuses_a_malformed_reason` |
| M6b | `main()` 1159–1163 | `tests/test_improve_roster_alt.py::test_task086a_review_alt_ends_with_exit_1_where_it_cannot[set-unknown]` |
| M6c | `main()` 1154–1157 | `tests/test_improve_roster_alt.py::test_task086a_review_alt_on_a_set_that_cannot_be_read` |
| M6d | `main()` 1375–1377 | `tests/test_improve_review_alt_profile.py::test_task087d_with_the_pool_available_the_request_stays_on_the_full_profile` |
| M6e | `main()` 1384–1386 | `tests/test_improve_roster_alt.py::test_task086a_review_alt_names_its_cause[alternate-of-review-a]` |
| M6f | `main()` 1387–1389 | `tests/test_improve_review_alt_profile.py::test_task087d_after_a_composer_build_the_request_is_refused_by_the_family_cause` |
| M6g | `main()` 1381–1383 | `tests/test_improve_roster_alt.py::test_task086a_review_alt_refuses_an_alternate_of_no_known_family` |
| M6h | `main()` 1390–1392 | `tests/test_improve_roster_alt.py::test_task086a_review_alt_names_its_cause[alternate-marked]` |
| M6i | `main()` 1393–1395 | `tests/test_improve_roster_alt.py::test_task086a_review_alt_names_its_cause[alternate-pool-exhausted]` |
| M6j | `main()` 1407–1411, 1410–1411 | `tests/test_improve_review_alt_profile.py::test_task087d_r2_an_alternate_that_did_not_answer_is_refused_on_its_one_answer` |
| M6k | `main()` 1361–1362, 1402–1405 | `tests/test_improve_review_alt_profile.py::test_task087d_a_sign_in_ends_the_request_with_exit_5` |
| M7 | `main()` request path 1398–1412 (second `probe` when `cached_alt` is not `None`) | `tests/test_improve_review_alt_profile.py::test_task087d_r2_after_a_grok_build_the_alternate_is_probed_once_on_request` |

## Scratch tests

no scratch test file

## Assumed, not verified

- `alt_probe_ok` is set only when `do_probe`, a deviation, `a_id`, and `_alt_pool_ok` held at probe time (lines 1316–1320), including before family-deviation REBUILD clears `deviation` · the brief names storing the answer despite later reset · confirmed by `test_task087d_r2_an_alternate_that_did_not_answer_is_refused_on_its_one_answer`.
- When `alt_probe_ok` is `None`, the request path still probes once with the same lines as round 1 (lines 1400–1409) · no round-2 test covers a granted request where evaluation never probed the alternate with probes on · would need a roster where the profile in use has an alternate but evaluation resolved without a deviation-driven alternate probe (e.g. empty built set, Review B not excluded).
- Refusals for unknown built set and unreadable set run before any profile evaluation on `--review-alt`, so they never interact with `alt_probe_ok` · code order at 1154–1163 before the request loop · no acceptance test combines unknown set with probes on for `--review-alt`.
- `no profile is in use` (lines 1370–1372) · no test in Done steps 6–7 exercises that FAIL line for `--review-alt`.