# ASSUMPTIONS for TASK-077 (Review B, round 2)

No builder ran in this round: the change is the supervisor's test setup fix. Its own assumptions, each with how it was checked:

- On GitHub's ubuntu-latest runners gh and git both live in /usr/bin -> the CI log's setup assertion on all 97 Bench cases, and the 3 cases without Bench passing there.
- Ubuntu's packaged git, started through a symlink, finds its exec path as compiled in, not from the link's folder -> Review A's reading; the WSL reproduction ran git through the link.
- The program runs git by the bare name, so the link folder first on the PATH is what it starts -> evaluate-reports.py and pace-report.py read by Review A; neither changes PATH in its git environment.
- Round 1's ASSUMPTIONS file stands for the increment (git show e38999ca7098:run/review/ASSUMPTIONS-TASK-077-r1.md).
