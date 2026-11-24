# Assumptions of TASK-086a's branch

The branch's commit messages carry no `Assumptions:` section. The builder's reports carry these `Assumed, not verified` items, each with the supervisor's disposition. They are extra places to look, never the review's scope.

## Round 1 (handoff/TASK-086a-r1-report.md)
- none.

## Round 2 (handoff/TASK-086a-r2-report.md)
- `git symbolic-ref -q HEAD` on a detached head in a secondary worktree exits 1 with no usable ref. Accepted: git documents `-q` as exit 1 for a detached head; a detached head refuses the resolve (exit 1), so a wrong answer there fails closed.
- `git ls-tree -r -z --name-only --full-tree <commit> -- handoff/` on Linux CI emits NUL-separated paths with no quoting. Accepted: `-z` turns quoting off by git's documentation; CI's Linux job runs the acceptance file.
- `git rev-parse --show-toplevel` from a subfolder answers the same toplevel as from the root. Accepted: git's documented behaviour; the tests run from the scratch repository's root.
- `mkstemp` in the record's folder then `os.replace` over a file another process holds open on Windows. Accepted as a lead: the repair racing a launcher append is recorded in docs/HARDENING.md (TASK-086a, lead 5).

## Round 3 (handoff/TASK-086a-r3-report.md)
- git prints names as UTF-8 bytes on CI's Linux job as on Windows. Accepted: CI's Linux job runs the two code-page cases.
- `os.lstat` fills `st_reparse_tag` for junctions on Windows Python 3.12. Accepted, not exercised: no case makes a junction (docs/HARDENING.md, TASK-086a, lead 10).
- A report name printed with `ascii()` rather than `%r`. Accepted: stricter than the brief asked (both reviewers, round 3).

## Round 4 (handoff/TASK-086a-r4-report.md)
- The POSIX-only case and the two symbolic-link cases were not exercised on this host. Accepted: CI's Linux job runs them. (The report names the POSIX-only case `test_task086a_a_record_line_split_only_at_its_line_feed`, which is not POSIX-only; the POSIX-only case is `test_task086a_a_report_name_holding_a_line_feed_prints_no_line_of_its_own`: records.)
- CI's Linux git and Windows git agree on the family-deviation outcomes. Accepted: the round-4 cases replace `probe` in-process and read no git output beyond the scratch repository's.
