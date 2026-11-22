# ASSUMPTIONS for TASK-077 (Review B, round 1)

The builder's `Assumed, not verified` lists of rounds 1 to 4 (handoff/TASK-077-r1-report.md to -r4-report.md), each item with the supervisor's disposition. They are extra places to look, never the only ones.

- gh api -i tells the alerts check's 204 from its 404 by the status line -> contract: the 204 and the empty open list are captured replies; the 404 and the 403 are built from the captured forms (each fixture's header says how).
- A refused read exits non-zero with GitHub's JSON body -> contract: tests/fixtures/github/security-forbidden.json, built from the captured form.
- gh api --paginate without --slurp prints each page's JSON array one after another -> accepted: one page captured; the parse refuses anything but arrays of objects (HARDENING, TASK-077, lead 13).
- The logs endpoint's redirect yields the log's plain text on standard output -> contract: the captured success log.
- gh auth refresh -s repo is the scope the remedy names for every read -> accepted (HARDENING, lead 13).
- Several failed jobs in one run: the first exit line read -> accepted: the scan's workflow has one job.
- No _meta.last_extract and no entry: every listed run is in the window -> accepted.
- A disabled workflow's runs are not read; its kind is no completed run whatever its runs show -> accepted (the design's reading).
- One runs GET with per_page=100 holds a week's runs -> accepted (HARDENING, lead 13).
- The DEP- remedy is found by substring in the section's remedy -> accepted: an owner or repository named with DEP- hides it (HARDENING, lead 1).
- The second `finding` line under the week's kind beside a failed alerts read is the form the brief's word requires -> accepted (HARDENING, lead 10).
