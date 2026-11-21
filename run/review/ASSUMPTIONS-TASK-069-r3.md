# Assumptions, TASK-069 (Review B, round 3)

The files of rounds 1 and 2 (run/review/ASSUMPTIONS-TASK-069-r1.md and -r2.md, kept locally) stand; this round changes tests only. The supervisor's assumptions on the test fix, each with its disposition. Extra places to look, never the review's scope.

- The (#n) endings dropped from seven fixture commits were incidental to what each case checks, the ID reader -> accepted, Review A: the ID reader reads an ID however the subject ends, and its two mutants of a reader that splits a subject each fail the separator or the carriage-return case.
- No other test still encodes the pre-R-089 rule -> accepted, Review A ran the five other files that run the report: 219 passed, 1 skipped.
- The ISS-013 form case shows TASK-031 unmerged only through its started count -> lead 14.
- No case shows a subject without (#n) merging an ID with a brief -> lead 15, older than this increment.
