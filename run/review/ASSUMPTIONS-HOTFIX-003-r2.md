# Assumptions: HOTFIX-003, round 2

The branch's commit messages (`git log origin/release/2026.11.03..HEAD --format=%B`) hold two Assumptions sections, both the supervisor's:

- The first text commit (171418c): "Assumptions: none (text written by the supervisor)."
- The commit after the code gate's round 1 (subject: "the intake hotfix after the code gate's round 1"): "Assumptions: none (text written by the supervisor)."

No builder ran on this branch; every commit is the supervisor's (`supervisor:` subjects). One correction to a commit message, which is not rewritten since the commits are the critique's history: the round-4 file's commit (74505a1) says the file holds "the 40 text mutants"; it held 39 (the mutants file at that commit), and the branch's head holds 42 with the stamp's three.

Round 2's checks before this file: the full suite with the pull request's variables at round 1 showed exactly Review A's fourteen failures and no others; after the fixes, the seven affected test files pass (218 tests), the trace check prints `RESULT: OK` at 89 excused, and the mutation run prints `counts: run=42 cached=0 killed=42 survived=0 not applied=0 error=0 expected survive=0`. The full suite on this head is running and its counts line goes into the pull request's description.
