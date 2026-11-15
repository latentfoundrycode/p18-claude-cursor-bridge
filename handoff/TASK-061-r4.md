---
record: brief
header: 1
id: "TASK-061"
round: 4
satisfies: [R-079]
scope: ["bridge/cursor-bridge/bridge-run.py", "bridge/cursor-bridge/bridge_env.py", "bridge/cursor-bridge/MANIFEST.json", "tests/test_program_review_rows.py", "tests/test_bridge_run.py", "docs/BUILDER_NOTES.md", "handoff/TASK-061-r4-report.md"]
merge_unit: null
blocking_class: "security"
---
# TASK-061 round 4: A review run's own launcher rows (R-079)

Round cause: security - bridge/cursor-bridge/bridge_env.py:1311 and bridge/cursor-bridge/bridge-run.py:1419, a `seconds` that is a JSON whole number too big for a float (`1` followed by 400 zeros, or its negative) passes the type and sign checks as a Python int and makes `math.isfinite` raise OverflowError, so a review row of it breaks every `--limit auto` launch of every kind and a healthy row of it breaks its own kind (security audit, round 3, B1)

Blocking class: security - security audit, round 3, B1

## Objective
This is round 4 of TASK-061, above the code gate's ceiling of three rounds, lifted by the class line above. Round 3's code is committed ("checkpoint before TASK-061-r4", `git log` shows it). Rounds 2 and 3 each closed one spelling of a length in the run log that makes `learned_limit` raise (NaN and Infinity, then a healthy row's), and round 3's security audit found a third (a whole number too big for a float). The cause is one: the length is read in two places by checks that can themselves raise. So this round changes the design instead of adding a fourth check: one reader of a row's length, in `bridge_env.py`, that never raises, read by both places. The supervisor's acceptance file `tests/test_program_review_rows.py` gained two cases (committed, HEAD); both fail on round 3's code. Your work is the minimum change that makes every test in that file pass, meets the correction, keeps every existing test green, and edits nothing in the acceptance file. Rounds 1 to 3's briefs (`handoff/TASK-061.md`, `-r2.md`, `-r3.md`) stay in force for everything this brief does not change.

Satisfies: R-079 - A review run's own launcher rows neither teach the limit nor go unseen (C8, J2): `learned_limit` ignores every row whose start lies inside a `review` row's run, read from the log; `review-guard.py verify` names, as a note and never a flag, the launcher rows written during the review's run by id and kind, the review's own row apart; the bridge's own launcher tests write their rows under a temporary folder, never into the checkout's `run/launcher/`.

## Scope
Files and directories you may create or modify:
- bridge/cursor-bridge/bridge-run.py
- bridge/cursor-bridge/bridge_env.py
- bridge/cursor-bridge/MANIFEST.json
- tests/test_program_review_rows.py
- tests/test_bridge_run.py
- docs/BUILDER_NOTES.md
- handoff/TASK-061-r4-report.md

Limits on these files: `bridge_env.py`: one new function beside `review_run_interval`, and `review_run_interval` reading it; nothing else. `bridge-run.py`: `learned_limit`'s healthy filter reading it; nothing else. `MANIFEST.json` only as regenerated. `tests/test_program_review_rows.py` is the supervisor's, read only. `tests/test_bridge_run.py`: you may add cases; change no existing case.

Do not modify anything else.

## Out of scope
As round 1's brief. In particular: `review-guard.py`, `read_runs_jsonl` and every other program untouched; no option, no environment variable, no new dependency, no module docstring of a program changed; the supervisor's mutants file is not yours.

## Correction
**One length reader that never raises (security audit, round 3, B1).** Add to `bridge_env.py` a function (name it `log_seconds`) that takes a row's `seconds` value and returns it where it is an `int` or `float`, not a `bool`, and strictly between `-10**9` and `10**9`, and `None` for every other value, by comparisons alone (Python compares an int with a float exactly, never overflowing, and NaN fails every comparison), with no conversion to float, no `math.isfinite` and no `try`. Then:
- `review_run_interval` reads the length through it: `None`, or a length below 0, is no end (as today), and the run ends at its start plus `int(length)`;
- `learned_limit`'s healthy filter takes a row only where `bridge_env.log_seconds(r.get("seconds"))` is not `None`, in place of round 3's type, bool and finiteness tests, its other conditions unchanged.

The acceptance cases `test_r079_a_review_row_whose_seconds_is_too_big_for_a_float_ignores_nothing` and `test_r079_a_healthy_row_whose_seconds_is_too_big_for_a_float_teaches_nothing` pin it; every earlier case (NaN, Infinity, 1e400, a bool, a string, a negative length) stays green. `10**9` seconds is about 31 years, longer than any run the launcher allows.

## Context
Round 3's code: `bridge_env.py` lines 1302 to 1314, `review_run_interval`, whose checks are `isinstance(sec, bool) or not isinstance(sec, (int, float)) or sec < 0`, then `math.isfinite(sec)`; `bridge-run.py` lines 1417 to 1420, the healthy filter's `isinstance(r.get("seconds"), (int, float)) and not isinstance(r.get("seconds"), bool) and math.isfinite(r.get("seconds"))`. Python's json reads a whole number of any length up to 4300 digits as an int; `math.isfinite` of an int too big for a float raises OverflowError. `review-guard.py`'s note reads `review_run_interval` too and is fixed by the same change.

## Acceptance criteria
- [ ] Every test in `tests/test_program_review_rows.py` passes (it names R-079); `test_r079_the_launcher_tests_write_no_row_into_the_checkout` passes, not skipped, in your run from the Workspace root.
- [ ] The correction met, named in the report with the function and lines; the length is read in one place.
- [ ] Rounds 1 to 3's requirements and corrections stay met; every test of round 1's Done list passes.
- [ ] Every line added ASCII; no option, environment variable or dependency.

## Constraints
Round 1's brief's Constraints all stand (foreground commands only, named test files only with the Done commands, no `python -c` or script of your own, no git command that writes, never write the checkout's `run/launcher/runs.jsonl`, ASCII, windowless subprocesses with a timeout in tests, the report's form). Mutations by hand, in-process, each reverted, listed by label with the pytest line that shows a test failing, else `not run`: (T1) the upper bound dropped; (T2) the bool test dropped; (T3) the healthy filter not reading the reader. Prefer the smallest change; refactor nothing else.

## Done
Your report is `handoff/TASK-061-r4-report.md`, written as you go, in round 1's form (files changed; summary; the correction in one sentence with the function and lines; every command below with its output, verbatim, in fenced blocks; the mutations T1 to T3; a last section headed exactly `Assumed, not verified`). It names no computer path: `<Workspace>` for the repository folder, `~` for the home folder.

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
