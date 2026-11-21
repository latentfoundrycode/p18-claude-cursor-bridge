# Assumptions, TASK-069

The builder's `Assumed, not verified` lists of both rounds and the supervisor's own, each with its disposition. Extra places to look, never the review's scope.

## Round 1 (handoff/TASK-069-r1-report.md)
- A seeded guard round is not a start, a cause, a pass, nor a holder of its round against a review-b pass line -> accepted (a seeded round records no review read).
- Of several builder rows of one round each stating a cause, the first stated in log order is kept -> accepted.
- Of several commits on main closing the same `(#n)`, the earliest decides the fold and the merge time -> accepted.
- An ID found only in a trailer sorts after every counted ID the subject names -> accepted.
- A folded PR-<n>'s own launcher rows and guard record are counted under the name it folds into -> accepted; their start does not enter the target's start (HARDENING, TASK-069, lead 1).
- A non-seeded guard entry whose time does not parse holds its round against a review-b pass line and is no pass itself -> accepted; it suppresses that pass line (lead 2).
- With handoff/ untracked, an ID the subject names occupies the commit for folding -> accepted.

## Round 2 (handoff/TASK-069-r2-report.md)
- A SCOPE file over 1,048,576 bytes is `unstated` even where its first line states a cause -> accepted (the brief's bound; D-003 states it).
- With handoff/ untracked, a STAGE- or DESIGN- subject stays PR-<n> -> accepted (the supervisor's ruling in both modes).
- The cause's remainder is stripped with `lstrip()` with no argument after the prefix is stripped of spaces and tabs -> accepted (only the text after a matched cause).

## The supervisor's
- H4 (the stamp's `[0-9]` mutated to a digit class) is an equivalent mutant on Python 3.12: `strptime` refuses every non-ASCII digit block probed -> accepted, run/supervisor/task069_digits.py (local, not in the diff).
- The two supervisor-edited test files outside the plan's Scope are needed by the eighth cause alone -> accepted, Review A read both.
