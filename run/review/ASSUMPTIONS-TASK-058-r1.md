# Assumptions, TASK-058

No builder ran: TASK-058 is supervisor-authored (tests only). The supervisor's own assumptions, each with its disposition. Extra places to look, never the review's scope.

- The pull request takes number 161 (GitHub's latest is 160): the status file and HARDENING's TASK-058 heading name it -> test (CI's status-file test reads the pull request's number).
- Each kind's reader in the test is the one its own check uses -> accepted, Review A compared each with inventory-check.py, completion-check.py, diagram-check.py and plan-check.py.
- The plan's merged set: origin/main where the clone is full, none where it is shallow or has no .git (CI's push run at depth 1, the mutation engine's copy), as plan-check.py derives it -> accepted, Review A ran the test in a depth-1 clone and a full single-branch clone; the HEAD fallback where origin/main is missing is a HARDENING lead.
- release B2's three refused briefs (TASK-002-r2 to r4) are the only header-less records -> test (the equality assertion; Review A counted 123 headed records independently).
