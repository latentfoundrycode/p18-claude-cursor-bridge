---
record: brief
header: 1
id: "TASK-061"
round: 2
satisfies: [R-079]
scope: ["bridge/cursor-bridge/bridge-run.py", "bridge/cursor-bridge/review-guard.py", "bridge/cursor-bridge/bridge_env.py", "bridge/cursor-bridge/MANIFEST.json", "tests/test_program_review_rows.py", "tests/test_bridge_run.py", "tests/test_review_guard.py", "docs/BUILDER_NOTES.md", "handoff/TASK-061-r2-report.md"]
merge_unit: null
blocking_class: null
---
# TASK-061 round 2: A review run's own launcher rows (R-079)

Round cause: behaviour - bridge/cursor-bridge/bridge_env.py:1310, a review row whose `seconds` is NaN or Infinity makes `int(sec)` raise, breaking every `--limit auto` launch and turning verify's exit 0 into a traceback after its OK line (security audit B1, Review A B1); behaviour - bridge/cursor-bridge/review-guard.py:473, a row whose kind is not a plain word drops out of the note, id and all (Review A B2); test that does not test - tests/test_review_guard.py:332 and 349 (Review A B3); correctness - bridge/cursor-bridge/bridge_env.py:1282, the id pattern accepts a trailing newline and non-ASCII digits (Review A S1, security audit advisory); test that does not test - tests/test_bridge_run.py:503 (Review A S2); security - bridge/cursor-bridge/review-guard.py:452, the note takes the first review row with the launch id, so an earlier row written during the run silences it (security audit advisory)

## Objective
This is round 2 of TASK-061. Round 1's code is committed ("checkpoint before TASK-061-r2", `git log` shows it) and was rejected: Review A returned REJECT and the security auditor FAIL. The supervisor's acceptance file `tests/test_program_review_rows.py` gained cases after the reviews (committed, HEAD); the new ones fail on round 1's code and pin corrections 1 to 4 below. Your work is the minimum change to round 1's code and tests that makes every test in that file pass, meets corrections 1 to 6, keeps every existing test green, and edits nothing in the acceptance file. Round 1's brief, `handoff/TASK-061.md`, stays in force for everything this brief does not change (read it for the full requirements, context and Done list); its Requirements 1 to 7 must stay met.

Satisfies: R-079 - A review run's own launcher rows neither teach the limit nor go unseen (C8, J2): `learned_limit` ignores every row whose start lies inside a `review` row's run, read from the log; `review-guard.py verify` names, as a note and never a flag, the launcher rows written during the review's run by id and kind, the review's own row apart; the bridge's own launcher tests write their rows under a temporary folder, never into the checkout's `run/launcher/`.

## Scope
Files and directories you may create or modify:
- bridge/cursor-bridge/bridge-run.py
- bridge/cursor-bridge/review-guard.py
- bridge/cursor-bridge/bridge_env.py
- bridge/cursor-bridge/MANIFEST.json
- tests/test_program_review_rows.py
- tests/test_bridge_run.py
- tests/test_review_guard.py
- docs/BUILDER_NOTES.md
- handoff/TASK-061-r2-report.md

Limits on these files: as round 1's brief (`handoff/TASK-061.md`, Scope); `tests/test_program_review_rows.py` is the supervisor's, read only. `bridge/cursor-bridge/bridge-run.py` needs no change this round unless your design for correction 1 makes one.

Do not modify anything else.

## Out of scope
As round 1's brief. In particular: no launcher or guard option added or changed, no environment variable, no new dependency, no module docstring of a program changed, `read_runs_jsonl` and `_valid_log_row` unchanged for every caller, the three launcher test files round 1 did not change untouched; the supervisor's mutants file is not yours. The note keeps reading `<root>/run/launcher/runs.jsonl` as round 1 does (which log folder it reads is the supervisor's record, not this round's work).

## Corrections
1. **A length that is not finite is no end (security audit B1, Review A B1).** `review_run_interval` treats a `seconds` that is not finite (NaN, Infinity, -Infinity; Python's json reads `1e400` as Infinity) as no end, like a negative one: it returns no interval and nothing raises. The acceptance cases `test_r079_a_review_row_whose_seconds_is_not_finite_ignores_nothing` (in `learned_limit`) and `test_r079_a_review_row_whose_seconds_is_not_finite_leaves_verify_s_exit` (in `verify`) pin it.
2. **The note cannot change verify's exit (Requirement 4).** In `cmd_verify`, a failure of any kind while the note is computed or printed is caught where the note is called, so that `verify` still returns 0 after its OK line and prints no traceback; nothing is printed in place of the note.
3. **Every row inside the run is named (Review A B2).** The note names every row whose start lies inside the review's own run by its id, whatever its kind: a kind that is a plain word of ASCII letters is printed as it stands, and any other kind (with spaces or other characters, not a string, or absent) is printed as `?`. The acceptance case `test_r079_a_row_of_any_kind_is_named_by_its_id` pins it.
4. **The review's own row is the last one with its id (security audit advisory).** The launcher appends the review's row when the run ends, so where more than one review row matches the launch time, the note reads the last one in the log's order. The acceptance case `test_r079_verify_reads_the_review_s_own_row_the_last_one_with_its_id` pins it.
5. **Only the whole launcher form has a start (Review A S1).** `_LAUNCHER_ID_RE` matches the whole id and ASCII digits only (`re.fullmatch`, or `\Z`, with `[0-9]` or `re.ASCII`), so an id ending in a newline or written in other digits has no start. The acceptance case `test_r079_only_the_whole_launcher_form_has_a_start` pins it.
6. **Your tests test what they name (Review A B3, S2).**
   - `test_r079_verify_missing_err_prints_no_note` (round 1, tests/test_review_guard.py line 349): write a log holding a review row and a row inside its run (as the acceptance file's `test_r079_verify_names_the_rows_written_during_the_review` does), leave the `.err` file out, and assert rc 0 and nothing after the OK line. Drop the dead `if err.is_file(): err.unlink()`.
   - `test_r079_verify_tolerates_malformed_log_lines` (line 332): add a valid row inside the review's run and assert it is named while the bogus-id row is not, with rc 0.
   - `test_r079_learned_limit_bad_review_seconds_ignores_nothing` (tests/test_bridge_run.py line 503): add a row with id `2026-10-07T10:00:00Z-2` (the review's start) that must still teach, so that a review row with a bad length taken as ending at its start fails it, and add NaN and `1e400` written as raw JSON text to its parameters.

## Context
Round 1's code, as committed: `bridge_env.py` lines 1282 to 1333 (`_LAUNCHER_ID_RE`, `row_start_utc`, `review_run_interval`, `review_run_intervals`, `row_inside_review_run`); `review-guard.py` lines 438 to 478 (`_KIND_WORD_RE`, `_launcher_rows_during_review_note`) and lines 1161 to 1163 (the note's call in `cmd_verify`); `review-guard.py` `main()` catches only `RuntimeError`, `subprocess.TimeoutExpired` and `OSError`. `bridge_env.read_runs_jsonl` uses `json.loads`, which accepts `NaN`, `Infinity`, `-Infinity` and reads `1e400` as `inf`. The reviews' other observations are the supervisor's records, not this round's work: the note's log folder (`launcher_log_folder` in a linked worktree), the cost of the interval check on a very large log, and the review row's `seconds` counted from after the launcher's pre-start checks.

## Acceptance criteria
- [ ] Every test in `tests/test_program_review_rows.py` passes (it names R-079); `test_r079_the_launcher_tests_write_no_row_into_the_checkout` passes, not skipped, in your run from the Workspace root.
- [ ] Corrections 1 to 6 met, each named in the report with the function or line.
- [ ] Round 1's Requirements 1 to 7 stay met; every test of round 1's Done list passes, unchanged but for the cases correction 6 changes.
- [ ] Nothing read from the log raises, in `learned_limit` or in `verify`; the note prints ids and kinds (`?` for any other kind) and no other field; every line added to the three Python programs ASCII; no option, no environment variable, no dependency.

## Constraints
Round 1's brief's Constraints all stand (foreground commands only, named test files only with the Done commands, no `python -c` or script of your own, no git command that writes, never write the checkout's `run/launcher/runs.jsonl`, ASCII, windowless subprocesses with a timeout in tests, the report's form). Mutations by hand, in-process, each reverted, listed by label with the pytest line that shows a test failing, else `not run`: (R1) the finiteness check dropped; (R2) the note's call in `cmd_verify` not guarded; (R3) a row with an odd kind dropped from the note; (R4) the first matching review row read instead of the last; (R5) `.match` with `$` put back; (R6) a review row with a bad length taken as ending at its start. Prefer the smallest change; refactor nothing else.

## Done
Your report is `handoff/TASK-061-r2-report.md`, written as you go, in round 1's form (files changed; summary; corrections 1 to 6 each in one sentence with the function or line; the tests you changed and why; every command below with its output, verbatim, in fenced blocks; the mutations R1 to R6; a last section headed exactly `Assumed, not verified`). It names no computer path: `<Workspace>` for the repository folder, `~` for the home folder.

Run these from the Workspace root, in this order, after your last edit, each in the foreground, with no `PYTHONPATH` or other environment change:
1. `python tools/make-manifest.py`
2. `python tools/dump-cli.py --check` (expect the reference current)
3. `python -m pytest -p no:cacheprovider -q -rs tests/test_program_review_rows.py`
4. `python -m pytest -p no:cacheprovider -q tests/test_bridge_run.py tests/test_bridge_run_slot.py`
5. `python -m pytest -p no:cacheprovider -q tests/test_bridge_run_driver.py tests/test_release_s_launcher.py`
6. `python -m pytest -p no:cacheprovider -q tests/test_review_guard.py`
7. `python -m pytest -p no:cacheprovider -q tests/test_review_guard_a4.py tests/test_review_guard_ceiling.py tests/test_d003_review_round_states.py tests/test_release_t_ceiling.py tests/test_release_t_stamp.py tests/test_bug036.py tests/test_bug039.py tests/test_bug041.py tests/test_hotfix25a_guard_scope_invisible.py tests/test_task032_supervisor_guard.py tests/test_task032_supervisor_launcher.py tests/test_release_s_records_gate.py tests/test_dump_cli.py`
8. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` (expect the sources to match)
9. `git diff --stat HEAD`
10. `git rev-parse HEAD` and `git status --short`

Every pytest summary line quoted verbatim; never restate a count in prose. Your last message is the summary and the report file's path, and nothing follows it.
