# ASSUMPTIONS - TASK-048, round 1 of Review B

The builder's `Assumptions` sections from the branch's commit messages (`git log 3555c51..4061b48 --format=%B`), each with the supervisor's disposition. Extra places to look, never the review's scope.

## Round 1 (46c7dc0)

- test_plan_check.py's merged-set helper needed bridge_env on sys.path. Disposition: fixed by the supervisor before round 1 ran its tests (90f1b8f), a harness change in a supervisor commit.
- test_bug038.py's fixture copied completion-check.py without bridge_env.py. Disposition: fixed by the supervisor (90f1b8f), the fixture copies bridge_env.py beside it.
- read_blocking_class_line with a header class and no prose line. Disposition: Review A and the audit found it defeated the review ceiling (a class lift with an empty line); fixed in round 2 (a class with no prose line carrying a finding never reads as a lift), pinned by tests/test_header_plan_r2.py.

## Round 2 (7dacef3)

- The header comparison's token for a scope the fallback refused for an unbalanced parenthesis. Disposition: rejected by Review A (the sentinel could never agree, 15 of this repository's merged increments); round 3 splits a merged Scope on ';' with no parenthesis refusal, the parenthesis rule plan-check's shape rule for an unmerged increment alone, a note under --no-git.
- The wording of the launcher's plan-header refusal beyond its prefix and file name. Disposition: accepted; the tests hold the prefix `bridge-run: refused - header: ` and the file name, and since 86ab1d9 the orphan heading's words `outside any stage`.

## Round 3 (62c3f6d)

- The wording of PlanFileReadRefusal for a plan HeaderError inside plan_increment_ids. Disposition: accepted; the launcher reaches it only after plan_header_refusal has passed the same file, so in practice the earlier refusal speaks (the audit's A5, the plan read twice, recorded in HARDENING).
- The R3-6 note's wording (an unbalanced parenthesis under --no-git). Disposition: accepted; tests/test_header_plan_r2.py holds a note naming the increment and the word parenthes.
- The R3-2 SHAPE line's wording (a heading outside any stage of a headed plan). Disposition: accepted; Review A's H-1 notes it is printed twice, recorded in HARDENING.
