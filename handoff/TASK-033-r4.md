Blocking class: safety mechanism - the session read's deadline is not acted on while an over-cap transcript line is drained (pace-report.py:476-484, `if past_deadline(): pass`; Review A round 3 B1 and the security audit's round 3 B, converged), with two findings of the class behaviour in the same round: the letter rule's tracked list and R-nnn under the grammar

# TASK-033-r4: One reading of a squash subject — round 4, past the ceiling, three findings of the blocking classes

## Objective
Round 3 (commit b5a55c2 on this branch) closed round 2's findings. Its two reviews found three defects of the blocking classes, both reviewers naming each. This is round 4, past the owner's three-round ceiling; the class line above lifts it. This round fixes those three and nothing else: every other finding of round 3 goes to `docs/HARDENING.md` with the increment (the supervisor's). `handoff/TASK-033.md`, `-r2.md` and `-r3.md` still govern everything this brief does not change: read all three first, then this file. Where they differ, this file wins, then r3, r2 and the first brief.

Satisfies: R-044 — the report cycle has a pace section for every project, computed by `pace-report.py`, read-only, from git and the launcher's and the guard's own records; the pace report and the plan check read a squash subject by one rule, one copy in `bridge_env.py`, under which a closing parenthesis merges an increment only when each of its comma-separated items is a bare ID (ISS-013). The full row is `docs/REQUIREMENTS.md` line 50.

## Scope
Files you may create or modify:
- bridge/cursor-bridge/pace-report.py
- bridge/cursor-bridge/bridge_env.py
- bridge/cursor-bridge/MANIFEST.json
- docs/BUILDER_NOTES.md
- handoff/TASK-033-r4-report.md

Do not modify anything else.

**Read-only, the supervisor's:** `tests/test_task033_supervisor.py` (unchanged since `858da29`), `tests/test_task033_supervisor_r2.py` (since `a44c878`), `tests/test_task033_supervisor_r3.py` (since `11aeafc`) and `tests/test_task033_supervisor_r4.py` (committed with a `supervisor:` subject before this run). Read them, run them, never edit them.

## Out of scope
- Everything the three earlier briefs put out of scope, unchanged.
- `plan-check.py`, the tests in your earlier Scope, `review-guard.py` and every other program: round 3's other findings (the guard's own git runner, the `ls-files` reads, the numstat ref, unused names) are the supervisor's records, not this round's work.
- Any line no Requirement below names.

## Context: the three findings, by number
- **G1. The drain ignores the deadline** (`pace-report.py:476-484`). `_read_line_capped`'s drain loop calls `past_deadline()` and does nothing with the answer (`if past_deadline(): pass`), so an over-cap line is read to its end however long the deadline has been past. Review A's probe: a line of 20 chunks with the deadline past from the first chunk made 20 checks, all true, and read all 20 chunks. The round-3 report says "drains ... with deadline checks". Test: `test_task033r4_the_drain_of_an_over_cap_line_stops_at_the_deadline`; `test_task033r4_every_transcript_read_is_given_a_size` pins round 3's `readline(LINE_CAP + 1)`, which round 3's tests did not.
- **G2. The letter rule asks the disk** (`pace-report.py:216-228`). `_letter_err_belongs` still calls `_has_brief_file`, which is `os.path.isfile`; round 3's Requirement 9 asked the tracked list. A brief written but not yet committed (`handoff/TASK-040b.md`) takes `REVIEW-TASK-040b.err` away from TASK-040. Test: `test_task033r4_the_letter_rule_asks_the_tracked_list`.
- **G3. `R-nnn` no longer merges under the grammar** (`bridge_env.py:555-561`, with `:574-577`). `_parenthesis_bare_item` now tests `_R_BARE_RX` before the pattern, so under the grammar `R-027` returns "r" and is never added: `docs: x (R-027)` went from {R-027} to set(), `(TASK-100, R-027) (#5)` from {R-027, TASK-100} to {TASK-100}. The first brief's Requirement 1 and r2's Requirement 1 say otherwise. Test: `test_task033r4_r_nnn_is_a_bare_item_merging_only_under_the_grammar`.
- `test_task033r4_a_tracked_path_named_like_the_ref_is_no_failure` pins round 3's `--` after `refs/heads/main`, which round 3's test could not tell from its absence; it passes today and must keep passing.

## Requirements
1. **G1.** When `past_deadline()` is true during the drain (or before any chunk), `_read_line_capped` returns a sentinel meaning "timed out", and the caller ends that project's session read as at the limit: empty tokens cells, the line naming the project and the limit, the exit unchanged. Every read of a transcript goes through `readline` with a size of at most `LINE_CAP + 1`.
2. **G2.** `_letter_err_belongs` (and whatever it calls to ask whether a token has a brief) asks the set of IDs read from the tracked list (`git ls-files handoff/`, as `_ids_with_brief` reads it), passed in from the caller; `_has_brief_file` and every other `os.path.isfile` test of a brief are removed.
3. **G3.** `_parenthesis_bare_item` tests an item first with the one helper (`_id_token_hyphen_and_digit`: fully matches the pattern, holds a hyphen and a digit), then, only when that fails, with `_R_BARE_RX`, as round 2 ordered them; under the plan pattern an `R-nnn` item stays bare and adds nothing; the one helper stays the only copy of the test.

## Acceptance criteria
- [ ] `python -m pytest tests/test_task033_supervisor.py tests/test_task033_supervisor_r2.py tests/test_task033_supervisor_r3.py tests/test_task033_supervisor_r4.py -q -p no:cacheprovider` passes whole.
- [ ] `git diff --quiet 858da29 -- tests/test_task033_supervisor.py`, `git diff --quiet a44c878 -- tests/test_task033_supervisor_r2.py`, `git diff --quiet 11aeafc -- tests/test_task033_supervisor_r3.py` and `git diff --quiet HEAD -- tests/test_task033_supervisor_r4.py` each exit 0.
- [ ] `python -m pytest tests/test_plan_check.py tests/test_pace_report.py tests/test_task032_supervisor_launcher.py tests/test_task032_supervisor_guard.py tests/test_task032_supervisor_r4.py tests/test_bridge_run_review_ceiling.py tests/test_review_guard_ceiling.py tests/test_evaluate_reports.py tests/test_dump_cli.py tests/test_tests_windowless.py -q -p no:cacheprovider` passes.
- [ ] `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge/bridge_env.py bridge/cursor-bridge/pace-report.py` reports no FAIL; `python tools/dump-cli.py --check` passes; `python bridge/cursor-bridge/bridge-check.py --root bridge --sources` ends OK.
- [ ] `pace-report.py` and `bridge_env.py` stay ASCII; no new dependency.

## Constraints
All of the three earlier briefs' Constraints hold, with these changes:
- **Verification commands.** Run exactly these, from the Workspace root, never the whole suite:
  - `python -m pytest tests/test_task033_supervisor.py tests/test_task033_supervisor_r2.py tests/test_task033_supervisor_r3.py tests/test_task033_supervisor_r4.py -q -p no:cacheprovider`
  - `python -m pytest tests/test_plan_check.py tests/test_pace_report.py tests/test_task032_supervisor_launcher.py tests/test_task032_supervisor_guard.py tests/test_task032_supervisor_r4.py tests/test_bridge_run_review_ceiling.py tests/test_review_guard_ceiling.py tests/test_evaluate_reports.py tests/test_dump_cli.py tests/test_tests_windowless.py -q -p no:cacheprovider`
  - the four `git diff --quiet` commands above (each prints nothing; check that each exit code is 0)
  - `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge/bridge_env.py bridge/cursor-bridge/pace-report.py`
  - `python tools/dump-cli.py --check`
  - `python tools/make-manifest.py`, last, after every program edit
  - `python bridge/cursor-bridge/bridge-check.py --root bridge --sources` (must end OK)
- **Mutation check, by hand.** Apply each, one at a time, run the four supervisor files, restore: (1) `if past_deadline(): pass` back; (2) `readline()` with no size; (3) `_has_brief_file` back in `_letter_err_belongs`; (4) `_R_BARE_RX` tested before the helper. List each with the test that caught it, or "survived" — run it; do not write what you expect.
- **Your report states only what the diff shows.** Round 3's report claimed deadline checks the code did not make and mutations that survived when the reviewers ran them. For each finding name the changed lines; for each mutation, what you ran and what it printed.

## Done
Your report is the file `handoff/TASK-033-r4-report.md`, written as you go: every file you changed; what you changed, with file:line, under G1 to G3; every verification command with its pass, fail and skip counts; the mutation list with what you ran and what caught each; every test file outside your Scope that fails under your change, without editing it; a one-paragraph summary; and a section headed exactly `Assumed, not verified`, one item per line, or `Assumed, not verified: none`.

Your last message is the summary and the report file's path, and nothing follows it.
