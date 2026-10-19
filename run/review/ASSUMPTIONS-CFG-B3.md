# ASSUMPTIONS - CFG-B3

From the branch's commit messages (`git log 823f0c5..HEAD --format=%B`), sections `Assumptions:`:

Assumptions: none

Assumptions: none

Assumptions: none (supervisor-written records)

Assumptions: none

Assumptions: the afterFileEdit hook runs under the shim's Git Bash launch -> test (a live probe before the first delegation, KP-008/KP-038)

Places to look all the same: each configuration file against the bridge reference it comes from; the hook and the pre-commit gate for anything that could block a builder run or skip a check; any computer path in a committed file.
