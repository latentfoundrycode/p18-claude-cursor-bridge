# ASSUMPTIONS: HOTFIX-004-CARRY round 1

No builder ran on this branch; its commits carry no Assumptions section. The hotfix's own builder assumptions were dispositioned on the release branch (handoff/HOTFIX-004-r1-report.md to handoff/HOTFIX-004-r4-report.md and their accept commits).

The supervisor's one assumption of the carry: the hunks of mutation-run.py that applied by the 3-way merge sit where the hotfix meant them inside TASK-085's code, the run-id lock taken before anything is removed or written. Review A checked it line by line; the mutation run's 34 kills on the carry tree are the evidence.
