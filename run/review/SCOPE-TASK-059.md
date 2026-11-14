# SCOPE: TASK-059 (R-078), the resolution round on round 6's regression

Branch `task-059`, base `origin/main`. This snapshot is the Review B read of round 6's code (009e42f) for the resolution round whose material is `handoff/RESOLUTION-TASK-059.md`; the reviewer is asked for a reasoned vote on that file's question, not for a review of the diff.

Blocking class: security - security audit, round 5, B1 (a folder value whose trailing dots Windows drops runs npm through a planted junction)

The line lifts round 6, the round it was written for; its brief's commit, against which it is confirmed or denied, is 19dd44e (handoff/TASK-059-r6.md). Review A and the security auditor confirmed it at round 6 against that commit, and both found the hole closed at 009e42f.

## Scope

The scope of TASK-059 is its briefs' Scope sections (handoff/TASK-059.md to handoff/TASK-059-r6.md). The question this round settles is how round 7 removes R1 (a behaviour regression round 6 caused) while keeping round 5's B1 closed.
