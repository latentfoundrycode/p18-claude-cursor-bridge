# Assumptions, TASK-055

No builder ran: TASK-055 is supervisor-authored (tests only). The supervisor's own assumptions, each with its disposition. Extra places to look, never the review's scope.

- The pull request takes number 158 (one above #157, the latest pull request): the status file's Last accepted names it -> test (CI's status-file test reads the pull request's number).
- The launcher adds a key file's names after the strip, so a secret-like name in a stripped run is the launcher's by design and not a leak the strip test must find (bridge-run.py, the key file read after stripped_env) -> accepted (Review A read the narrowing as compensated: stripped_env's own pins here, test_r055 in tests/test_bridge_run.py through a real launch, tests/test_bug043.py OTHER_API_KEY through a real --strip launch); a launcher that adds a secret-like name of its own after the strip has no real-launch test reading for it, recorded in docs/HARDENING.md (tests/test_bridge_run.py is outside this Scope).
- BRIDGE_TESTS_LAUNCH_APPDATA reaches the programs the tests start; nothing outside the two test files reads it (a search of the Workspace) -> accepted (said in conftest's comment).
- The first whole stripped run's one failure, tests/test_mutation_run.py:492 (mutation-run's own 3 s resolution check under the suite's load), is load and not this increment's: the test passes alone stripped -> test (the second whole stripped run's line in Evidence; a HARDENING lead).
