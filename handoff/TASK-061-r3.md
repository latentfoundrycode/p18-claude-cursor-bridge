---
record: brief
header: 1
id: "TASK-061"
round: 3
satisfies: [R-079]
scope: ["bridge/cursor-bridge/bridge-run.py", "bridge/cursor-bridge/bridge_env.py", "bridge/cursor-bridge/MANIFEST.json", "tests/test_program_review_rows.py", "tests/test_bridge_run.py", "docs/BUILDER_NOTES.md", "handoff/TASK-061-r3-report.md"]
merge_unit: null
blocking_class: "security"
---
# TASK-061 round 3: A review run's own launcher rows (R-079)

Round cause: security - bridge/cursor-bridge/bridge-run.py:1418 and 1424, a healthy row of the learned kind whose `seconds` is NaN, Infinity or 1e400 makes `int(longest["seconds"])` raise, so every `--limit auto` launch of that kind ends in a traceback (security audit, round 2, B1); security - bridge/cursor-bridge/bridge_env.py:1364, a log line nested too deep for Python's json raises RecursionError, which `read_runs_jsonl` does not catch, so `learned_limit` raises for every kind (security audit, round 2, B2)

Blocking class: security - security audit, round 2, B1 and B2

## Objective
This is round 3 of TASK-061. Round 2's code is committed ("checkpoint before TASK-061-r3", `git log` shows it): Review A approved it; the security auditor failed it on two inputs of the run log, a file any run started in the checkout can write, a reviewer's run included, that still make `learned_limit` raise. Both holes predate this increment, and round 1's brief already requires that nothing read from the log raises in `learned_limit`. The supervisor's acceptance file `tests/test_program_review_rows.py` gained two cases after the audit (committed, HEAD); both fail on round 2's code and pin corrections 1 and 2. Your work is the minimum change that makes every test in that file pass, meets corrections 1 and 2, keeps every existing test green, and edits nothing in the acceptance file. Round 1's brief `handoff/TASK-061.md` and round 2's `handoff/TASK-061-r2.md` stay in force for everything this brief does not change.

Satisfies: R-079 - A review run's own launcher rows neither teach the limit nor go unseen (C8, J2): `learned_limit` ignores every row whose start lies inside a `review` row's run, read from the log; `review-guard.py verify` names, as a note and never a flag, the launcher rows written during the review's run by id and kind, the review's own row apart; the bridge's own launcher tests write their rows under a temporary folder, never into the checkout's `run/launcher/`.

## Scope
Files and directories you may create or modify:
- bridge/cursor-bridge/bridge-run.py
- bridge/cursor-bridge/bridge_env.py
- bridge/cursor-bridge/MANIFEST.json
- tests/test_program_review_rows.py
- tests/test_bridge_run.py
- docs/BUILDER_NOTES.md
- handoff/TASK-061-r3-report.md

Limits on these files: `bridge-run.py`: the healthy filter of `learned_limit` only. `bridge_env.py`: `read_runs_jsonl` only, and only as correction 2 says; this round lifts round 1's limit that it keep its behaviour, for that one change. `MANIFEST.json` only as regenerated. `tests/test_program_review_rows.py` is the supervisor's, read only. `tests/test_bridge_run.py`: you may add one case per correction; change no existing case.

Do not modify anything else.

## Out of scope
As round 1's brief. In particular: `review-guard.py` and every other program untouched; no option, no environment variable, no new dependency, no module docstring of a program changed; the supervisor's mutants file is not yours.

## Corrections
1. **A healthy row's length must be finite to teach (security audit B1).** `learned_limit`'s healthy filter takes a row only where its `seconds` is an `int` or `float` that is not a `bool` and is finite (`math.isfinite`); any other row of the kind is skipped like an unhealthy one, whatever its id. The acceptance case `test_r079_a_healthy_row_whose_seconds_is_not_finite_teaches_nothing` pins it.
2. **A line too deep to read is skipped (security audit B2).** `bridge_env.read_runs_jsonl` skips a line whose `json.loads` raises `RecursionError`, as it skips one that raises `ValueError`; nothing else in it changes. The acceptance case `test_r079_a_line_nested_too_deep_to_read_is_skipped` pins it.

## Context
Round 2's code: `bridge-run.py` lines 1415 to 1419, `rows = read_log(folder)`, `intervals = bridge_env.review_run_intervals(rows)`, and the healthy filter `isinstance(r.get("seconds"), (int, float))`; then `longest = max(healthy, key=lambda r: r["seconds"])` and `int(longest["seconds"])`. `bridge_env.py` lines 1356 to 1370, `read_runs_jsonl`, whose inner `try` catches only `ValueError`. Python's json reads `NaN`, `Infinity` and `-Infinity` and reads `1e400` as infinity. The other observations of the round-2 reviews are the supervisor's records, not this round's work.

## Acceptance criteria
- [ ] Every test in `tests/test_program_review_rows.py` passes (it names R-079); `test_r079_the_launcher_tests_write_no_row_into_the_checkout` passes, not skipped, in your run from the Workspace root.
- [ ] Corrections 1 and 2 met, each named in the report with the function or line.
- [ ] Rounds 1 and 2's requirements and corrections stay met; every test of round 1's Done list passes.
- [ ] Every line added ASCII; no option, environment variable or dependency.

## Constraints
Round 1's brief's Constraints all stand (foreground commands only, named test files only with the Done commands, no `python -c` or script of your own, no git command that writes, never write the checkout's `run/launcher/runs.jsonl`, ASCII, windowless subprocesses with a timeout in tests, the report's form). Mutations by hand, in-process, each reverted, listed by label with the pytest line that shows a test failing, else `not run`: (S1) the finiteness check dropped from the healthy filter; (S2) `RecursionError` not caught. Prefer the smallest change; refactor nothing else.

## Done
Your report is `handoff/TASK-061-r3-report.md`, written as you go, in round 1's form (files changed; summary; corrections 1 and 2 each in one sentence with the function or line; every command below with its output, verbatim, in fenced blocks; the mutations S1 and S2; a last section headed exactly `Assumed, not verified`). It names no computer path: `<Workspace>` for the repository folder, `~` for the home folder.

Run these from the Workspace root, in this order, after your last edit, each in the foreground, with no `PYTHONPATH` or other environment change; run steps 1 to 9 again in order if you edit anything after them, and quote the last run:
1. `python tools/make-manifest.py`
2. `python tools/dump-cli.py --check` (expect the reference current)
3. `python -m pytest -p no:cacheprovider -q -rs tests/test_program_review_rows.py`
4. `python -m pytest -p no:cacheprovider -q tests/test_bridge_run.py tests/test_bridge_run_slot.py`
5. `python -m pytest -p no:cacheprovider -q tests/test_bridge_run_driver.py tests/test_release_s_launcher.py`
6. `python -m pytest -p no:cacheprovider -q tests/test_review_guard.py tests/test_task032_supervisor_launcher.py tests/test_dump_cli.py`
7. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` (expect the sources to match)
8. `git diff --stat HEAD`
9. `git rev-parse HEAD` and `git status --short`

Every pytest summary line quoted verbatim; never restate a count in prose. Your last message is the summary and the report file's path, and nothing follows it.
