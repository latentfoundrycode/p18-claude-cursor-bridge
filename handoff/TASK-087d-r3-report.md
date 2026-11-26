# TASK-087d round 3 report

## Files changed

- `bridge/cursor-bridge/roster-check.py`
- `bridge/cursor-bridge/MANIFEST.json`

## Summary

Round 3 adds a per-run dict `alt_probe_answers` in `main()` and a helper `_alt_probe_result` that reads or records each `review_b_alt` probe answer by model id; `_evaluate_profile` and the `--review-alt` request path both call it so a model probed (and failing) on an earlier skipped profile is not probed again when the request needs the same alternate. `MANIFEST.json` was regenerated; CLI reference dumps were unchanged.

## One sentence (record)

A lookup in `alt_probe_answers` before every `review_b_alt` probe ensures the first answer in a run is stored and all later readers reuse it without calling `probe` again.

## One sentence (plain resolve output change)

When a later profile names the same `review_b_alt` an earlier profile's evaluation already probed, the plain resolve prints no second `probe review_b_alt` line and uses the recorded answer instead.

## Requirements 1–7

1. One reading of the profile in use: `_evaluate_profile` (lines 1233–1367) shared by the request loop (1372–1382) and the plain resolve loop (1431–1450).
2. Request never passes to a later profile: request loop (1372–1382) breaks at first non-None evaluation; refusals use the in-use profile only (1386–1408).
3. Refusals: malformed reason (1111–1118), unreadable set (1154–1157), unknown set for request (1159–1163), static request refusals (1388–1408), probe failure (1415–1417), sign-in (1225–1228, 1413–1414).
4. Probes: `alt_probe_answers` (1219), `_alt_probe_result` (1221–1231), evaluation alternate probe (1329–1333), request alternate probe (1411–1417).
5. Granted request output: DEVIATION and `chosen` (1420–1425).
6. Module docstring: unchanged (out of scope).
7. No new dependency, import, or option.

## Commands

### Step 1 (before edit)

```
git status --short
```

(empty)

### Step 2 (before edit)

```
python -m pytest -p no:cacheprovider -q -rs tests/test_improve_review_alt_profile.py
```

```
............F....
================================== FAILURES ===================================
_ test_task087d_r3_an_alternate_that_did_not_answer_for_an_earlier_profile_is_not_probed_again _
...
1 failed, 16 passed in 9.51s
```

### Step 3

```
python tools/dump-cli.py
python tools/dump-cli.py --check
```

(exit 0, no output on --check)

### Step 4

```
python tools/make-manifest.py
```

```
make-manifest: version 2026.11.24a, 148 files hashed, VERSION + MANIFEST.json written
```

### Step 5

```
git status --short
```

```
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/roster-check.py
```

(`bridge/cursor-bridge/VERSION` not listed; no restore)

### Step 6

```
python -m pytest -p no:cacheprovider -q -rs tests/test_improve_review_alt_profile.py tests/test_improve_roster_alt.py tests/test_improve_roster_launch.py tests/test_program_roster_sign_in.py
```

```
274 passed, 3 skipped in 173.66s (0:02:53)
```

### Step 7

```
python -m pytest -p no:cacheprovider -q -rs tests/test_roster_check.py tests/test_roster_check_a4.py tests/test_a4_review_fixes.py tests/test_hotfix25a_roster_launcher.py tests/test_agent_models.py tests/test_release_t_ceiling.py tests/test_bug030.py tests/test_bug032.py tests/test_dump_cli.py
```

```
194 passed in 218.94s (0:03:38)
```

### Step 8

```
python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet
```

```
RESULT: SOURCES MATCH bridge 2026.11.24a <Workspace>/bridge/cursor-bridge
```

### Step 9

```
python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks
```

```
windowless-check: 41 file(s) scanned, 0 FAIL, 0 NOTE
```

### Step 10

```
python -c "open('bridge/cursor-bridge/roster-check.py','rb').read().decode('ascii'); print('ascii ok')"
```

```
ascii ok
```

### Step 11

```
git diff --stat HEAD
```

```
 bridge/cursor-bridge/MANIFEST.json   |  4 ++--
 bridge/cursor-bridge/roster-check.py | 31 ++++++++++++++++++-------------
 2 files changed, 20 insertions(+), 15 deletions(-)
```

### Step 12

```
git rev-parse HEAD
git status --short
```

```
832d4866b9a327be3c70b7d7894baf7b575082a5
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/roster-check.py
```

Post-change acceptance file (commit `832d4866b9a327be3c70b7d7894baf7b575082a5`, uncommitted changes above):

```
python -m pytest -p no:cacheprovider -q -rs tests/test_improve_review_alt_profile.py
```

```
17 passed in 9.19s
```

## Scratch tests

no scratch test file

## Mutation table

| Label | Function and lines | Test |
| --- | --- | --- |
| M1 | `_evaluate_profile`, `_r_excluded` gate before `review_b` probe (1325–1328) | `tests/test_improve_review_alt_profile.py::test_task087d_a_review_b_that_did_not_answer_skips_the_profile_for_the_request_too` |
| M2 | `_evaluate_profile`, `_r_excluded` / `r_excl` unavailable branch (1263, 1308–1316) | `tests/test_improve_review_alt_profile.py::test_task087d_a_marked_review_b_skips_the_profile_for_the_request_too` |
| M3 | `_evaluate_profile`, non-deviation `review_b` probe failure skip (1358–1361) | `tests/test_improve_review_alt_profile.py::test_task087d_a_review_b_that_did_not_answer_skips_the_profile_for_the_request_too` |
| M4 | request profile loop `break` (1379–1382) | `tests/test_improve_roster_alt.py::test_task086a_review_alt_acts_on_the_profile_in_use_alone` |
| M5 | same break choosing first in-use profile (1379–1382) | `tests/test_improve_review_alt_profile.py::test_task087d_an_exhausted_pool_the_request_acts_on_the_native_profile` |
| M6a | `main`, malformed `--review-alt` reason (1111–1118) | `tests/test_improve_roster_alt.py::test_task086a_review_alt_refuses_a_malformed_reason` |
| M6b | `main`, unknown built set before profiles (1159–1163) | `tests/test_improve_roster_alt.py::test_task086a_review_alt_ends_with_exit_1_where_it_cannot[set-unknown]` |
| M6c | `main`, unreadable built set (1154–1157) | `tests/test_improve_roster_alt.py::test_task086a_review_alt_on_a_set_that_cannot_be_read` |
| M6d | request, no alternate named (1388–1390) | `tests/test_improve_review_alt_profile.py::test_task087d_with_the_pool_available_the_request_stays_on_the_full_profile` |
| M6e | request, Review A family (1397–1399) | `tests/test_improve_roster_alt.py::test_task086a_review_alt_names_its_cause[alternate-of-review-a-review a]` |
| M6f | request, built family (1400–1402) | `tests/test_improve_review_alt_profile.py::test_task087d_after_a_composer_build_the_request_is_refused_by_the_family_cause` |
| M6g | request, unknown alternate family (1394–1396) | `tests/test_improve_roster_alt.py::test_task086a_review_alt_refuses_an_alternate_of_no_known_family` |
| M6h | request, marked unavailable (1403–1405) | `tests/test_improve_roster_alt.py::test_task086a_review_alt_names_its_cause[alternate-marked-marked]` |
| M6i | request, exhausted pool (1406–1408) | `tests/test_improve_roster_alt.py::test_task086a_review_alt_names_its_cause[alternate-pool-exhausted-pool]` |
| M6j1 | request, recorded failure via `_alt_probe_result` (1411–1417) | `tests/test_improve_review_alt_profile.py::test_task087d_r3_an_alternate_that_did_not_answer_for_an_earlier_profile_is_not_probed_again` |
| M6j2 | request, own fresh failed probe (1229–1230, 1415–1417) | `tests/test_improve_review_alt_profile.py::test_task087d_r2_an_alternate_the_evaluation_did_not_probe_is_probed_once_by_the_request` (refused parametrization) |
| M6k1 | request loop, sign-in from `_evaluate_profile` (1373–1375) | `tests/test_improve_review_alt_profile.py::test_task087d_a_sign_in_ends_the_request_with_exit_5` |
| M6k2 | request, sign-in from `_alt_probe_result` (1412–1414) | no test exercises it |
| M7 | request re-probe when record exists (would bypass 1222–1223) | `tests/test_improve_review_alt_profile.py::test_task087d_r3_an_alternate_that_did_not_answer_for_an_earlier_profile_is_not_probed_again` |
| M8 | per-run record omitted (`alt_probe_answers` / `_alt_probe_result`) | `tests/test_improve_review_alt_profile.py::test_task087d_r3_an_alternate_that_did_not_answer_for_an_earlier_profile_is_not_probed_again` |

## Assumed, not verified

- `alt_probe_answers` holds only boolean success after a real probe · brief requires recording the answer and never recording sign-in · confirmed by `test_task087d_r3_an_alternate_that_did_not_answer_for_an_earlier_profile_is_not_probed_again` (one probe line, exit 1).
- `alt_probe_ok` remains on the evaluation dict for round-2 skip logic but the request no longer reads `in_use_ev["alt_probe_ok"]` · brief allows keeping the key if the request uses the record alone · request path uses only `_alt_probe_result` at 1411–1417.
- When probes are off or the alternate is not probed in evaluation (no deviation / pool), the record has no entry and the request may probe once · matches `test_task087d_r2_an_alternate_the_evaluation_did_not_probe_is_probed_once_by_the_request`.
- A recorded `False` in a later profile's evaluation reuses failure without a probe line and drives the same skip / REBUILD branches as a live failure · same code paths use `ok_alt` from `_alt_probe_result` at 1329–1357 · not separately asserted beyond round-3 and round-2 refusal tests.
- Static refusals (1394–1408) run before the request reads the record · code order · no test combines a static refusal with a prior recorded alternate failure on the same `a_id`.