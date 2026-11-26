# ASSUMPTIONS: TASK-087c (Review B, round 2)

Supervisor-written records: no builder ran. Places to look, never your scope:

1. The moved deviations are history the owner was already told; the status file keeps only the current release's told deviation, with a pointer to the archive.
2. inventory-check.py's cap counts characters of the whole file as read; the CI test runs the same program on the same tree.
