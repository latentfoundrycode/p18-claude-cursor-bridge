# ASSUMPTIONS-002d — from the branch's commit messages (git log origin/main..HEAD)

Extra places to look, never the review's scope. Items from rounds 1–5 and the records round (002c) stand as listed in run/review history; the PR CI runs settled them (Semgrep, OSV-Scanner and Socket ran green on 0517c5b).

Round 6 (`TASK-002 r6: socket ci runs with --no-banner`), the builder's `Assumed, not verified` list with the supervisor's dispositions:
- The pushed CI run no longer shows the banner or any part of the key → test: the supervisor reads the Socket step's log on the pushed head before the merge.
- `--no-banner` changes nothing but the banner; `socket ci` still fails the step on an unhealthy scan → accepted: the cited source ties the flag to the banner only (shouldSuppressBanner); the exit path is unchanged from r5, which Review A verified.
