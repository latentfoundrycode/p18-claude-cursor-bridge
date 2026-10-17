# ASSUMPTIONS — BUG-004

No builder ran on this branch, so there is no builder's `Assumed, not verified` list. The supervisor's own:

- GitHub-flavoured Markdown accepts a one-dash table separator (`|-|`), so workflow-check.py's acceptance of one (Review B's consider) is routed to HARDENING as a lead, not fixed → accepted (HARDENING round-3 section).
- The suite's 1240 passed was collected before the last two tests (the not-checked-path tests) were added; they were run on their own afterwards and passed → test (CI runs the whole suite on the pushed head).
