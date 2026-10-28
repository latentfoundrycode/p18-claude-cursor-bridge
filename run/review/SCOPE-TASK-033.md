# SCOPE - TASK-033

TASK-033 - One reading of a squash subject: the plan check's title rule and `pace-report.py`. Author: builder (composer-2.5, four runs); the supervisor wrote the acceptance tests before each run. Satisfies R-044 in part: the program (`pace-report.py`), the one squash-subject reader in `bridge_env.py` that `plan-check.py` and `pace-report.py` import, and the closing-parenthesis rule of ISS-013; the report cycle's text that runs the program is TASK-034's, so R-044 stays planned.

Blocking class: safety mechanism - the session read's deadline is not acted on while an over-cap transcript line is drained (pace-report.py:476-484, `if past_deadline(): pass`; Review A round 3 B1 and the security audit's round 3 B, converged), with two findings of the class behaviour in the same round: the letter rule's tracked list and R-nnn under the grammar

## The ceiling (the owner's decision of 2026-10-24, applied by hand from 2026-10-25)
This is the increment's fourth round: builder runs of handoff/TASK-033.md, -r2.md, -r3.md and -r4.md. Round 4 is past the three-round ceiling and was lifted by the class line above. Grade every finding by the five blocking classes first: behaviour against the brief or the register, security, data integrity, a defeated safety mechanism the increment relies on, a failing test. Only a finding of those classes is a REJECT. Every other finding is a HARDENING note: name it as such, and the supervisor records it in docs/HARDENING.md with the increment. docs/HARDENING.md's "TASK-033" section already lists what the supervisor recorded from rounds 1 to 4; a finding listed there is recorded, not new.

## Scope (docs/BUILD_PLAN.md, TASK-033, quoted)
bridge/cursor-bridge/plan-check.py; bridge/cursor-bridge/pace-report.py; bridge/cursor-bridge/bridge_env.py; bridge/cursor-bridge/MANIFEST.json; tests/test_plan_check.py; tests/test_pace_report.py; tests/test_dump_cli.py; docs/cli-reference.json; docs/CLI_REFERENCE.md

## Done when
docs/BUILD_PLAN.md, TASK-033, the `Done when:` paragraph (clauses (a) to (c)), read whole in the checkout. The briefs are normative in the precedence handoff/TASK-033-r4.md > -r3.md > -r2.md > handoff/TASK-033.md; -r2.md's R1 to R17, -r3.md's F1 to F12 and -r4.md's G1 to G3 fold in each round's review, and each brief records the readings it settled (the reader's two form orders, -r2.md; clause (b)'s three rounds readings, -r3.md).

## Out of scope (handoff/TASK-033.md, quoted)
- .env and anything under secrets/
- CI configuration (`.github/`, `.githooks/`)
- docs/ and handoff/, except the files the Scope section names
- `bridge/cursor-bridge/bridge-run.py`, `review-guard.py`, `evaluate-reports.py` and every other program: you read them, you do not change them
- every test file not in Scope, including `tests/test_task032_supervisor_*.py` and `tests/test_evaluate_reports.py`
- these `docs/HARDENING.md` "TASK-032" leads: N3, the ID pattern written three times (`_REVIEW_NAME_RX`, `REVIEW_LIFT_RE`, `MERGE_UNIT_RE`); the lapse reading the local `main` ref; a closing parenthesis of bare IDs on a plan-revision subject still lapsing a claim (by the Done when's own rule, bare IDs merge); the malformed-record tracebacks; the test suite's rows in the real `runs.jsonl`; the Merges-trailer form reading a one-word subject under the grammar's pattern. Do not add a fourth literal copy of the ID pattern, but do not remove the three that exist.

Later briefs add (handoff/TASK-033-r2.md to -r4.md): `tests/test_dump_cli.py` untouched after round 1; nothing imported from `review-guard.py`; the reader's two form orders kept; from round 4, `plan-check.py`, the tests in the earlier Scope and every other program (round 3's other findings are the supervisor's records). Each brief's Scope names the builder's report file and docs/BUILDER_NOTES.md.

## Tests the supervisor wrote, and the paragraph each enforces
The builder runs these and never edits them (each brief says so; `git diff --quiet` against each file's own commit passes at the branch's head). Each docstring names R-044 and the brief paragraph or plan clause it enforces.
- tests/test_task033_supervisor.py (858da29, before round 1): every case of the plan's clauses (a) to (c) through the programs' command lines on repositories and records built in the test; on the checkpoint's code 78 failed, 25 passed (the passes the plan check's unchanged forms and the ISS-013-free subjects, behaviour the increment keeps).
- tests/test_task033_supervisor_r2.py (a44c878, 27 tests): one test per round-1 finding R1 to R16; on round 1's code 22 failed, each for its finding, 5 passed.
- tests/test_task033_supervisor_r3.py (11aeafc, 68 tests): one or more per round-2 finding F1 to F11, round 1's parenthesis regex used as an oracle over 19 subject shapes; on round 2's code 42 failed, each for its finding, 26 passed.
- tests/test_task033_supervisor_r4.py (b97b24c, 7 tests): round 3's three convergent findings G1 to G3 and two pins (every transcript readline given a size; a tracked file at `refs/heads/main`); on round 3's code the five finding tests fail, each for its finding, and the two pins pass.
No mutation driver: the briefs' mutation lists are the builder's own in-process checks; Review A re-ran them on a scratch copy at rounds 3 and 4.

## Checks run on the branch
- The full suite on 401251a: 3122 passed, 39 skipped, 0 failed (23 min).
- scope-check.py handoff/TASK-033.md (base df85e0d): every code and test file in scope; the records the supervisor's; one drift line, docs/archive/STATUS_HISTORY.md, the supervisor's archive of the status file's older Last accepted part (8578461, a commit of its own), which the installed check's record list does not name.
- The builder's final test files (tests/test_pace_report.py, tests/test_plan_check.py) against the checkpoint df85e0d, a read-only worktree, torn down: 10 failed, 4 passed: every one of the 10 new test_r044_ tests fails on the old code (pace-report.py absent; the plan check reading the ISS-013 subject as merging TASK-031), the 4 passes the plan check's earlier tests, unchanged by the increment.
- No write outside the Workspace after any of the four builder runs (the marker and `find` check).

## Expected files
handoff/TASK-033.md, -r2.md, -r3.md, -r4.md (the briefs) and handoff/TASK-033-r1-report.md to -r4-report.md (the builder's reports); docs/BUILDER_NOTES.md where the builder wrote to it; docs/cli-reference.json and docs/CLI_REFERENCE.md (regenerated); bridge/cursor-bridge/MANIFEST.json (regenerated); the records committed by the supervisor (docs/HARDENING.md, docs/INVENTORY.md, docs/PROJECT_STATUS.md, docs/REQUIREMENTS.md, docs/archive/STATUS_HISTORY.md, project.json); run/review/ (this file, the diff, the assumptions), which the diff excludes.

## Rounds
- Round 1 (80c2a8b): Review A REJECT (B1 to B6: the grammar's parenthesis took a capitalised word, the default roots exited 2, a missing `main` read as a timeout, malformed transcript lines crashed the run, the token sources not named, one untracked brief made `handoff/` untracked) and the security audit FAIL (the same crash, with nine advisories); seven findings converged.
- Round 2 (bd7c8bb): Review A REJECT (B1 to B7) and the security audit FAIL: a widened trailing-version form let free words follow, `git log main` without `--`, an uncaught OverflowError on edge timestamps, the line cap applied after a whole read, stage IDs not filtered, and a regression test that compared sets; most converged.
- Round 3 (b5a55c2): round 2's findings closed at their cause. Review A REJECT and the security audit FAIL on three convergent findings of the blocking classes (the drain's deadline, a defeated safety mechanism; the letter rule asking the disk and `R-nnn` under the grammar, behaviour against the brief), the rest recorded in docs/HARDENING.md, "TASK-033".
- Round 4 (401251a): the three fixes only. Review A APPROVE (no blocking, no should-fix; the four mutations of the brief re-run and caught); the security audit PASS (each fix closed at its cause; 120,000 random subjects read alike by rounds 2 and 4). Their notes are in docs/HARDENING.md, "TASK-033".
