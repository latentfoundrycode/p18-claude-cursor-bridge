# ASSUMPTIONS - BUG-042-r1

From the `Assumptions:` sections of the branch's commit messages, whole, by commit (extra places to look, never the review's scope).

## db75a25 BUG-042: the scanner rows read the gate's workflows, and the guard's docstrings name the deletion (round 1)

- Assumed, not verified: none (handoff/BUG-042-r1-report.md) -> nothing to disposition; Review A found no unlisted assumption.

## 8703782 BUG-042: the Socket rows read every workflow again, and the guard's docstring says what it does (round 2)

- Builder: Assumed, not verified: none. Review A found one unlisted reading: Requirement 4's "each file read once" against Requirement 1's second loop beside the existing one, a file now read again -> accepted: Requirement 1 commissions the loop, the verdicts do not change (docs/HARDENING.md, BUG-042).

