# ASSUMPTIONS - BUG-014

From the branch's commit messages (`git log 7f0593a..HEAD --format=%B`), sections `Assumptions:`:

Assumptions: none (the supervisor's own change; no builder run)

Places to look all the same: each survivor class in docs/HARDENING.md round 12 against an input that would separate it; each new test against the paragraph its docstring names.
