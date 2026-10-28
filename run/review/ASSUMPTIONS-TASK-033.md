# ASSUMPTIONS - TASK-033

From the `Assumptions:` sections of the branch's commit messages (extra places to look, never the review's scope).

- r1: the regression test over main allows a legitimate TASK-031 merge (`former - new <= {TASK-031}`) -> test (superseded by round 3's F11: per commit, 9f6ace6's answer loses exactly {TASK-031} and every other commit's answer equals the former rule's, tests/test_plan_check.py)
- r1: a launcher row with a non-zero exit still counts as the increment's start -> accepted (docs/INVENTORY.md, Decisions, TASK-033's settled points: the plan's start is the first builder launch, and a failed launch is a launch)
- r1: a seeded guard round with an empty time is no start -> accepted (the same row; a seeded round has no launch time to read)
- r2 and r4: "none" -> noted (the reviewers hunt unaided)
- r3: `datetime.fromtimestamp(33000000000)` raises OSError on Windows -> test (tests/test_task033_supervisor_r3.py, test_task033r3_a_commit_dated_past_the_calendar_is_skipped, passing on Windows, where the commit is skipped, and on CI's Linux, where it falls outside the weeks read)
- fromtimestamp(33000000000) raises OSError on Windows -> test (the
- The builder's list reads "none" -> noted; the reviewers hunt unaided.
