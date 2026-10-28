# TASK-033-r4 report

## Files changed

- `bridge/cursor-bridge/pace-report.py`
- `bridge/cursor-bridge/bridge_env.py`
- `bridge/cursor-bridge/MANIFEST.json` (via `tools/make-manifest.py`)

## G1 — The drain ignores the deadline

- `pace-report.py:59` — module sentinel `_READ_LINE_TIMED_OUT`.
- `pace-report.py:473-490` — `_read_line_capped` returns `_READ_LINE_TIMED_OUT` when `past_deadline()` is true before the first chunk or in the over-cap drain loop (replacing `if past_deadline(): pass` at the old `:476-484` drain).
- `pace-report.py:557-562` — `_read_tokens` / `handle_file` treats `_READ_LINE_TIMED_OUT` like a session limit (`return "timeout"`), yielding empty token cells and the existing limit line; initial read stays `f.readline(cap + 1)`.

## G2 — The letter rule asks the disk

- Removed `_has_brief_file` and `os.path.isfile` brief checks (former `pace-report.py:216-217`).
- `pace-report.py:217-226` — `_letter_err_belongs(brief_ids, id_part, token)` uses the tracked-ID set (`token in brief_ids` / `id_part in brief_ids`).
- `pace-report.py:242-258`, `:273-287`, `:666`, `:682`, `:822-825` — `_err_rounds`, `_has_rounds_reading`, and `_rounds_for_id` take `brief_ids` from `_ids_with_brief(ls_out)` in `_project_section` (`:626`).

## G3 — `R-nnn` no longer merges under the grammar

- `bridge_env.py:555-561` — `_parenthesis_bare_item` tests `_id_token_hyphen_and_digit` first, then `_R_BARE_RX`, so grammar-pattern subjects merge `R-nnn` while the plan pattern still skips `R-nnn` in `_parenthesis_merged_ids` (`:574-577`).

## Verification

| Command | Result |
| --- | --- |
| `python -m pytest tests/test_task033_supervisor.py tests/test_task033_supervisor_r2.py tests/test_task033_supervisor_r3.py tests/test_task033_supervisor_r4.py -q -p no:cacheprovider` | 205 passed, 0 failed, 0 skipped |
| `python -m pytest tests/test_plan_check.py tests/test_pace_report.py tests/test_task032_supervisor_launcher.py tests/test_task032_supervisor_guard.py tests/test_task032_supervisor_r4.py tests/test_bridge_run_review_ceiling.py tests/test_review_guard_ceiling.py tests/test_evaluate_reports.py tests/test_dump_cli.py tests/test_tests_windowless.py -q -p no:cacheprovider` | 396 passed, 0 failed, 0 skipped |
| `git diff --quiet 858da29 -- tests/test_task033_supervisor.py` | exit 0 |
| `git diff --quiet a44c878 -- tests/test_task033_supervisor_r2.py` | exit 0 |
| `git diff --quiet 11aeafc -- tests/test_task033_supervisor_r3.py` | exit 0 |
| `git diff --quiet HEAD -- tests/test_task033_supervisor_r4.py` | exit 0 |
| `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge/bridge_env.py bridge/cursor-bridge/pace-report.py` | 0 FAIL |
| `python tools/dump-cli.py --check` | pass |
| `python tools/make-manifest.py` | pass |
| `python bridge/cursor-bridge/bridge-check.py --root bridge --sources` | OK |

## Mutation check

1. Restored drain `if past_deadline(): pass` (kept pre-read timeout return). Ran `python -m pytest tests/test_task033_supervisor.py tests/test_task033_supervisor_r2.py tests/test_task033_supervisor_r3.py tests/test_task033_supervisor_r4.py -q -p no:cacheprovider` — **caught by** `test_task033r4_the_drain_of_an_over_cap_line_stops_at_the_deadline` (AssertionError: elapsed 9.5 s &gt; 6.0 s).
2. Changed initial `f.readline(cap + 1)` to `f.readline()`. Ran the four supervisor files — **caught by** `test_task033r4_every_transcript_read_is_given_a_size` (AssertionError: sizes `[None, None, None]`).
3. Restored `_has_brief_file` and disk-based `_letter_err_belongs(ws, ...)`. Ran the four supervisor files — **caught by** `test_task033r4_the_letter_rule_asks_the_tracked_list` (AssertionError: draft rounds `(2.0, 2.0)` vs plain `(3.0, 3.0)`).
4. Swapped `_parenthesis_bare_item` to test `_R_BARE_RX` before `_id_token_hyphen_and_digit`. Ran the four supervisor files — **caught by** `test_task033r4_r_nnn_is_a_bare_item_merging_only_under_the_grammar` (three parametrized failures; grammar set missing `R-027`).

## Tests outside Scope failing under this change

None observed; all listed verification pytest runs passed after the final diff.

## Summary

Round 4 closes the three blocking-class defects from round 3’s reviews: over-cap transcript drains now abort on the session deadline instead of ignoring it, the letter rule for review `.err` files uses tracked handoff IDs rather than on-disk `isfile`, and `_parenthesis_bare_item` again prefers the shared hyphen-and-digit helper before the `R-nnn` regex so grammar-pattern squash subjects merge requirement IDs correctly. Supervisor r1–r4 and the broader regression suites all pass; manifest and bridge-check are updated.

## Assumed, not verified

Assumed, not verified: none.
