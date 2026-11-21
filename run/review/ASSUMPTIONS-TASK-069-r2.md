# Assumptions, TASK-069 (Review B, round 2)

Round 1's file, run/review/ASSUMPTIONS-TASK-069-r1.md, stands for builder rounds 1 and 2, with one change: round 1's assumption that the earliest of several commits closing the same (#n) decides is replaced by round 3's rule (below). Round 3's builder list and the supervisor's, each with its disposition. Extra places to look, never the review's scope.

## Round 3 (handoff/TASK-069-r3-report.md)
Read its section headed Assumed, not verified; each item there is accepted unless named here.

## The supervisor's
- Several commits closing the same (#n): a close whose subject names no counted name makes PR-<n> its own name, merged at that close; a close that folds counts only where no close is its own -> accepted, plan-consistent (the plan counts PR-<n> where a commit closes with (#n) and its subject names no name counted), Review A agreeing.
- The supervisor's r3 PR case reuses the fixture's (#1) and so tests the rule above with correction 1; the added case with (#3) tests correction 1 alone -> accepted, Review A ran the added case red on round 2's code.
- A padded PR-01 from a subject is still read as an ID -> lead 10, contrived.
