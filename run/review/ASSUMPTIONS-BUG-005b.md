# ASSUMPTIONS — BUG-005, gate round 2

No builder ran on this branch. Its commits are the supervisor's: cd0266a and 577d51c. Each commit message reads "Assumptions: none (no builder run)".

The points below are the supervisor's own and are unverified. They are extra places to look, not the scope of the review.
- The new tests were not run against the checkpoint's code. No program changed, so the checkpoint's code is the code under test. The mutation drivers stand in for that check: 104/104 and 42/42 killed.
- The exact-output tests assert an empty standard error. HARDENING records this as a lead in case environmental noise ever appears there.
- The fixtures are written with LF and checked out with CRLF on Windows, because there is no .gitattributes. The check reads files with universal newlines.
