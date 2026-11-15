# SCOPE for TASK-061 (Review B, round 1)

TASK-061 is a review run's own launcher rows (R-079): the launcher's learned limit ignores every row started inside a review row's run, read from the log's own times; review-guard verify names, after its verdict and as a note only, the launcher rows written during the review's own run by id and kind; the bridge's own launcher tests start the launcher in temporary folders of their own, so no row of theirs reaches the checkout's run log. Branch task-061 from main 72a4d03 (PR #167's merge, TASK-060). Four builder rounds; this is the review guard's first round for TASK-061. The builder rounds went past the code gate's ceiling of three: round 4 was lifted by its class line, below.

Blocking class: security - security audit, round 3, B1

The class line lifted builder round 4 (handoff/TASK-061-r4.md). Its finding stands against the code at 8c4a6c6, the commit the round-4 builder was launched on (its brief's commit): there, a run/launcher/runs.jsonl row whose seconds is a JSON whole number too big for a float (1 followed by 400 zeros) passes the type and sign checks as a Python int and makes math.isfinite raise OverflowError, a review row of it in learned_limit for every kind, a healthy row of it in its own kind. Review A and the security audit each confirmed it against 8c4a6c6.

Where the increment ends: three programs, bridge-run.py (learned_limit only), review-guard.py (the note beside cmd_verify and its call) and bridge_env.py (the row-start and review-run helpers, log_seconds, and read_runs_jsonl skipping a line too deep to read), MANIFEST.json, tests/test_bridge_run.py (its launches moved to temporary folders and its R-079 cases), tests/test_review_guard.py (its R-079 cases), the supervisor's acceptance file, the four briefs and their reports, and the records. The reviews' leads (HARDENING, TASK-061, leads 1 to 11) are recorded, not this diff's defects: among them the note reading the root's log rather than launcher_log_folder in a linked worktree, a review row appended after the launcher's own, a non-launcher id teaching but never named, the interval check's cost on a crafted log, and round 2's import math left unused in bridge_env.py.

Read the commit messages (git log, the full bodies) for the quoted lines.

## The plan entry, quoted (docs/BUILD_PLAN.md, TASK-061)
Scope: bridge/cursor-bridge/bridge-run.py; bridge/cursor-bridge/review-guard.py; bridge/cursor-bridge/bridge_env.py; bridge/cursor-bridge/MANIFEST.json; tests/test_program_review_rows.py; tests/test_bridge_run.py; tests/test_bridge_run_slot.py; tests/test_bridge_run_driver.py; tests/test_release_s_launcher.py; tests/test_review_guard.py; docs/BUILDER_NOTES.md; handoff/TASK-061-r<N>-report.md
Satisfies: R-079
Done when: learned_limit ignores every row whose start lies between the start and the end of a review row's run, read from the log's own times (a review row with no end ignoring nothing), so a suite a reviewer ran in its scratch folder teaches no limit; review-guard.py verify prints, after its verdict and never changing it or the exit code, one note naming the launcher rows written during the review's own run by id and kind, the review's own row apart, and no note where there is none; after the bridge's own launcher tests have run, the checkout's run/launcher/runs.jsonl holds no row of theirs (a test that reads the file's size before and after a launcher test's run in a subprocess); tests/test_program_review_rows.py names R-079; MANIFEST regenerated; no option added; no new dependency.

## The supervisor's tests, each with the clause it enforces
- tests/test_program_review_rows.py (names R-079; committed at the checkpoint b9a8dd0, with cases added after each round's reviews in 9ab1024, 6d3c35d and 7366745): learned_limit ignores the rows inside a review's run (a suffixed id, every kind), a review row with no end ignoring nothing, a row after the end teaching; a review length that is NaN, Infinity, 1e400 or a whole number too big for a float is no end and never raises; a healthy row whose length is not finite or too big teaches nothing and never raises; a line nested too deep is skipped; only the whole launcher id in ASCII digits has a start; verify names the rows inside the review's run after its OK line in one line, a row at the last second, every row whatever its kind (an odd kind as ?), reading the last review row with the launch id and a suffixed one, and prints nothing where none lies inside or the review row has no finite end, exit 0 throughout; the launcher tests, run in a subprocess, leave the checkout's run log byte for byte as it was.

## The departures from the briefs
None in the code. The supervisor's own: the rounds-2 and -3 acceptance cases were added after each round's reviews (each red on the round before), and round 2's split (Review A approving, the security audit failing on two inputs older than the increment) was decided on the merits for a round 3 (docs/CHANGES.md).

## The mutants
run/supervisor/TASK-061-mutants.json (28 mutants, each listing only the tests that check what it breaks). counts: run=5 cached=23 killed=24 survived=0 not applied=0 error=0 expected survive=4 (m16: a negative length taken, an interval nothing lies inside; m28: the lower bound dropped, a length below it never the longest and no end; m15: the launch time not guarded, the guard printing nothing either way; m20: the guard itself removed, no log content reaching it once lengths are read by log_seconds). The first run errored on m4, a kill its list missed; listed, killed on the rerun.

## Evidence
- Review A: round 1 REJECT, round 2 APPROVE, round 3 REJECT, round 4 APPROVE (its read of the whole increment against origin/main included)
- security audit: round 1 FAIL, round 2 FAIL, round 3 FAIL, round 4 PASS
- targeted run on round 4: 518 passed, 3 skipped; whole suite with the records: 5314 passed, 42 skipped
- inventory-check.py OK

## Expected bookkeeping and records in the diff
handoff/TASK-061.md, handoff/TASK-061-r2.md, -r3.md, -r4.md and their reports, docs/CHANGES.md, docs/HARDENING.md, docs/INVENTORY.md, docs/REQUIREMENTS.md, docs/PROJECT_STATUS.md (as at PR #168's merge), and run/review/ (these files).
