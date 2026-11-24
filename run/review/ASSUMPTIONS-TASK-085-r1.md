# TASK-085: the branch's assumption lists

From the `Assumptions:` section of the branch's commit messages (`git log origin/main..HEAD`), the builder's `Assumed, not verified` lists of its three rounds as the supervisor dispositioned them. Extra places to look, never the review's scope.

- r1: realpath and letter case on Windows: test (the case tests).
- r1: the probe sees the runs' import path: test (the mapping tests; one helper and one environment for both).
- r1: tree_path_at_commit: removed in round 2.
- r2: PYTHONSAFEPATH enough on every Python: replaced by -P in round 3 (test: a script started by a test imports its neighbour).
- r2: ast.literal_eval on the probe's repr: contract (literals only; read by Review A and the security audit).
- r2: active_import_roots without the commit lookup: accepted, ruled (one extra prefix where the archived copy creates the folder).
- r3: none; Review A's note on -P reaching a child through subprocess._args_from_interpreter_flags: accepted, a HARDENING lead.
