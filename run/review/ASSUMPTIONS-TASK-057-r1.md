# Assumptions, TASK-057

The builder's Assumed, not verified lists (handoff/TASK-057-r1-report.md, handoff/TASK-057-r2-report.md) and the supervisor's own, each with its disposition. Extra places to look, never the review's scope.

## Round 1
- git accepts --end-of-options before a revision in rev-parse and merge-base -> test (git 2.53 here; the dash test; an older git fails every base closed, exit 2, never a pass).
- Two alike passages at the base need two entries; one entry excuses one passage -> test (test_r077_one_entry_excuses_one_passage_even_where_two_are_alike, the supervisor's, after round 1).
- Matching pairs one entry with one dropped passage in order -> test (the same test).
- A passage's normal form is never empty -> cannot occur (parse_units: a paragraph starts on a non-blank line, a table on |, a fence keeps its fence line; Review A, round 1).

## Round 2
- The help test's whole-file SUPPRESS check was meant for the two options only -> the supervisor's test fault, fixed (it reads every option's help value; HARDENING, TASK-057).
- A dashed --base without --moves meets the requires-moves usage error first -> accepted (a usage error before any git call either way; Review A, round 2, ran it).

## The supervisor's
- The pull request takes number 160 (GitHub's latest is 159): the status file and HARDENING's TASK-057 heading name it -> test (CI's status-file test reads the pull request's number).
- CI's tests job fetching the full history on pull requests lets the own-history test run there -> test (that test never skips on a pull request).
