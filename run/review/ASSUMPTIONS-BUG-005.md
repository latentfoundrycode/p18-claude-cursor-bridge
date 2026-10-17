# ASSUMPTIONS — BUG-005

No builder ran on this branch; its one commit is the supervisor's (cd0266a), whose message reads "Assumptions: none (no builder run)".

The supervisor's own unverified points, as extra places to look:
- The new tests were not run against the checkpoint's code: no program changed, so the checkpoint's code is the code under test; the mutation drivers stand in (104/104, 42/42).
- The exact-output tests assert an empty standard error; recorded in HARDENING as a lead should environmental noise appear.
- The fixtures are written with LF and checked out with CRLF on Windows (no .gitattributes); the check reads universal newlines, and form-part-tab.md's tab sits before the part prefix's `: `, away from the line end.
