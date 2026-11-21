# Assumptions, TASK-070 round 3

The builder's `Assumed, not verified` list (handoff/TASK-070-r3-report.md) and the supervisor's, each with its disposition. Extra places to look, never the review's scope. Rounds 1 and 2's lists (ASSUMPTIONS-TASK-070-r1.md and -r2.md, in their review commits) stand.

## Round 3
- The builder wrote none. Review A named the one it relies on: the baseline copy, a second read of the Workspace after the cache keys, holds the bytes the keys read -> accepted for ordinary use (no Workspace edit during a gate run), recorded as HARDENING lead 8's remainder with its fix (build base from the mutants' copy, or compare compute_key on base with the keys).

## The supervisor's
- The moved Windows assertion keeps the test's claim -> accepted: the holder's working folder is the folder pytest ran in, now the baseline copy; base stays while the holder lives, and its .env is absent (added after Review A, which showed the tree/.env check could no longer fail).
- test_r090_r3_baseline_copy_holds_env_and_untracked_entries catches a baseline copy built without .env and the untracked entries -> accepted on Review A's probe of that mutation on the same fixture (exit 5); the case passes on the builder's code.
- The folder name base differs from tree only in contrived layouts -> accepted, HARDENING lead 11.
