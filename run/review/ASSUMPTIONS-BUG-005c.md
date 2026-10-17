# ASSUMPTIONS — BUG-005, gate round 3

No builder ran on this branch. Its commits are the supervisor's own (cd0266a, 577d51c, 0005913). Each commit message reads "Assumptions: none (no builder run)".

The supervisor's own unverified points, as extra places to look:
- **Not run against the checkpoint's code.** No program changed, so the checkpoint's code is the code under test. The mutation drivers stand in: 106/106 and 42/42.
- **The registry's fence sentence describes the check's common case.** It does not cover the gaps HARDENING records: container blocks and HTML blocks.
- **Line endings.** The fixtures are written with LF and checked out with CRLF on Windows; there is no .gitattributes. The check reads universal newlines.
