# ASSUMPTIONS: TASK-086b (Review B, round 1)

The builder's `Assumed, not verified` items of both rounds and the supervisor's disposition of each, as the accept commit d9cf322 records them (handoff/TASK-086b-r1-report.md and handoff/TASK-086b-r2-report.md hold the builder's own wording).

- r1: git status names docs/ROSTER.resolved.json repo-relative in a subfolder or worktree -> accepted (Review A traced porcelain v1; the worktree case is tested by test_r8_a_worktree_builders_keys_are_read_in_its_workspace).
- r1: an ignored run/ keeps the launcher's own files out of clean -> accepted (conformance's floor "run/ ignored" holds it in every project; HARDENING lead).
- r1: rev-parse HEAD prints 40 or 64 hex digits -> test (the r8 cases assert COMMIT_RX on start_commit).
- r1: built_families reads the launcher's branch as its own -> accepted (Review A traced _branch_from_head before branch_arg).
- r2: none listed by the builder. Review A named two: git's -z rename layout -> test (test_r8_a_staged_rename_into_the_resolved_roster_is_not_clean); the mtime cache key stable within a launch -> accepted (one process per launch, no write_log between the two reads).
