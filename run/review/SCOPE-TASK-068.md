# SCOPE for TASK-068 (Review B, round 1)

TASK-068 is the in-flight program (R-088, C15, J3): in-flight.py appends one clock-stamped line to the Workspace's run/supervisor/in-flight.md, from a text, a file under run/supervisor/, or a review pass's tagged line; the round causes stand once, in bridge_env.py, read by the launcher, the pace report and the program; the loop guard's refusal names the in-flight log and the program. Branch task-068 from main 618292e (PR #184's merge, FIX-006). Three builder rounds; round 3 was the code gate's ceiling round, graded by the five blocking classes. This is the review guard's first round for TASK-068.

Where the increment ends: the plan's Scope list below. The row R-088 stays planned at this merge: its three texts (rule 54, calibration's step 0, the parallel builders' paragraph) and KP-041's retirement are TASK-078's, the plan's rule for a row with a program and a sentence. The reviews' leads (HARDENING, TASK-068, leads 1 to 10) are recorded, not this diff's defects: among them the second folder check reading the path and not the handle, os.path.isjunction naming junctions only, an empty file created before a refusal, PASS variants with emphasis, Unicode spaces in a text, the guard's emphasised Paused forms, and correction 3 without a distinguishing test.

Read the commit messages (git log origin/main..HEAD, the full bodies) for the quoted lines.

## The plan entry, quoted (docs/BUILD_PLAN.md, TASK-068)
Scope: bridge/cursor-bridge/in-flight.py; bridge/cursor-bridge/bridge_env.py; bridge/cursor-bridge/bridge-run.py; bridge/cursor-bridge/pace-report.py; bridge/cursor-bridge/loop-guard.py; bridge/cursor-bridge/settings.bridge.json; bridge/cursor-bridge/MANIFEST.json; docs/diagrams/D-002-components.md; docs/cli-reference.json; docs/CLI_REFERENCE.md; tests/test_program_in_flight.py; tests/test_loop_guard.py; tests/test_bridge_run.py; tests/test_pace_report.py; tests/test_dump_cli.py; tests/test_allowlist.py; docs/BUILDER_NOTES.md; handoff/TASK-068-r<N>-report.md
Satisfies: R-088
Done when: see docs/BUILD_PLAN.md, TASK-068 (the program's two sources, the pass line, the refusals with exit 2 and nothing written, one append per run, the loop guard's refusal naming the log and the program, the tests, the command reference and the manifest regenerated, no new dependency).

## Two departures from the plan entry, both ruled by the supervisor
- The loop guard's decision changed (told to the owner, rule 58): the plan kept it unchanged, but the guard read the first Paused: line of the log, and in an append-only log the first pause would stand for ever. The guard now reads the last Paused: line (a new helper, last_field, in loop-guard.py), an empty Paused: line lifting the pause; its white space after the colon is spaces and tabs only, so it never takes the next line.
- The Scope notes say bridge_env's list holds the seven causes and unstated; the brief (handoff/TASK-068.md) fixed ROUND_CAUSES as the seven, the pace report adding unstated where it reads a missing cause, so the program refuses unstated as a cause it writes. The test bridge_env.ROUND_CAUSES == the seven pins it.

## The supervisor's tests, each with the clause it enforces
- tests/test_program_in_flight.py (names R-088 and D-002; committed at the checkpoint 48bcfa6, red there: 36 failed, 1 skipped; cases added after round 1 and round 2 in the checkpoint commits of those rounds): the append with the clock's stamp and its print; append-only; the Workspace from a subfolder; --file's line breaks made spaces, a Paused: line kept; the --pass line's form, the seven reviewers and the seven causes; the refusals (a word outside a list, a round not a number, outside a Workspace, no or empty text, a file and a text, a control character, a file outside run/supervisor/, a link); eight concurrent runs each a whole line; the one list of causes and no copy of it; the loop guard's message. Round 2: LF only; a later Paused: lifts or replaces an earlier one; an empty --file with a text refused; a text beginning PASS refused; run/ or run/supervisor/ as a junction refused. Round 3: an empty Paused: line never takes the next line (through the guard's own paused_in_flight); a log hard-linked to a file outside the Workspace refused, the outside file unchanged; run/supervisor/ linked to another folder of the same Workspace refused.
- tests/test_loop_guard.py: the builder's test_r088_ cases (the last Paused: line decides; an empty Paused: line reads as no wait).

## Evidence
- Review A: round 1 REJECT (CRLF on Windows; the first Paused: line), round 2 APPROVE, round 3 APPROVE
- security audit: round 1 BLOCK, round 2 BLOCK (the empty Paused: line taking the next line; the hard-linked log), round 3 PASS, both closed
- targeted run on round 3, stripped, eight test files: 566 passed, 22 skipped; the record-reading tests over the records commit: see the records commit's message
- completion-check.py --mode plan OK (89 built, 2 deferred, 14 planned); inventory-check.py OK

## Expected bookkeeping and records in the diff
handoff/TASK-068.md, handoff/TASK-068-r2.md, handoff/TASK-068-r3.md and their reports, docs/BUILDER_NOTES.md, docs/HARDENING.md, docs/INVENTORY.md (the in-flight program's Features row), docs/PROJECT_STATUS.md (as at this pull request's merge), and run/review/ (these files).
