# Assumptions on the branch task-063 (from the commit messages' Assumptions: sections)

The builders' own `Assumed, not verified` lists are in their reports, handoff/TASK-063-r<N>-report.md, each dispositioned in the round's reviews.

## c1e4cb7
- An append whose name begins GIT_CONFIG or BASH_FUNC_ meets the same refusals as NAME=value: test (the acceptance cases git-config-appended and exported-function-appended).
- sudo's strict reading still refuses X+=1 as a name that is not an identifier: test (append-after-sudo-stays-strict).
- The hook-runner test stays exact and case-sensitive, husky+=0 passing: test (test_r082_a_lower_case_husky_append_passes).
