# Assumptions - TASK-047, Review B round 2

The builder's `Assumed, not verified` lists from its four reports, each with the supervisor's disposition. Extra places to look, never the review's scope.

## Round 1 (handoff/TASK-047-r1-report.md)
- Isolated copies of `workflow-check.py`, `inventory-check.py` and `conformance-check.py` without a sibling `bridge_env.py` skip header enforcement when `status_values` is absent. Disposition: rejected; Review A's round-1 S6 and the audit's A5; round 2 made both checkers exit 2 naming `bridge_env.py` and conformance-check print a MISSING row (tests: `test_r058_a_checker_without_the_status_readers_refuses_and_never_skips_the_header`).
- The installed `diagram-check.py` was not available on the builder's host; `check:components` was run with the Workspace copy only. Disposition: accepted; the Workspace copy is the release's program, and the supervisor's runs of `diagram-check.py --mode code` print `RESULT: OK`.

## Round 2 (handoff/TASK-047-r2-report.md)
- `read_status` kept in `loop-guard.py` because `tests/test_loop_guard.py::test_status_file_is_found_from_every_start_folder` calls it, though Requirement 10 asked its removal. Disposition: accepted, recorded in `docs/HARDENING.md`, TASK-047.
- The full tree was started asynchronously and not seen to finish; an earlier run's five failures were said to be environmental. Disposition: superseded; the supervisor's full tree on round 2 gave 4567 passed and none failed, on round 3 4573 passed and none failed (ISS-030).

## Round 3 (handoff/TASK-047-r3-report.md)
- Assumed, not verified: none. Disposition: Review A of round 3 found no fact the diff relies on that the brief or the code leaves open.

## Round 4 (handoff/TASK-047-r4-report.md)
- Assumed, not verified: none. Disposition: Review A of round 4 found none open; the link case itself skips on Windows, which is why the round-4 test emulates the link through `os.path.realpath`, and CI's ubuntu-latest job runs the real link.
