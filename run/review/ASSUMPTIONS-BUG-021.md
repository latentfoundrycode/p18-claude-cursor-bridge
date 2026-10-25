# ASSUMPTIONS - BUG-021

From the `Assumptions:` sections of the branch's commit messages (extra places to look, never the review's scope).

- none new.
- none new (the supervisor's scheduler assumption stands as recorded).
- No builder ran, so no builder list; the supervisor's own: Claude Code fires a wall-time cron twice in the repeated hour and never in the skipped one -> accepted, recorded in docs/HARDENING.md (Stage B4, the stage review round 1) with its check.
