# ASSUMPTIONS - TASK-018

From the `Assumptions:` sections of the branch's commit messages (extra places to look, never the review's scope).

- Review A's intent note (persistent service against N1's idle stop) is settled for this trait by binding N1 to the runs the loop starts, as plan section 6.8 says -> accepted (HARDENING lead for TASK-020, where the owner's local service is designed).
- The project's cap is a Decisions row `Spending cap:`, the provider's own spending limit staying configuration's main-workflow item -> accepted (the trait's configuration addition names both).
- The store of paid results is named by place ("under the project's data folder", outside the disposable folders), not by a fixed path -> accepted (each project's design names it; its Resources row records it).
- tests/test_workflow_check.py's FLAG pins on Spends money read the fixtures' own open list, so writing the trait changes none of them -> test (the suite).
- The session-start case's unwritten trait (personal data) stays unwritten in release B -> test (the suite; open-list.md row personal-data).
