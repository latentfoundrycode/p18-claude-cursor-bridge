# TASK-004 — assumptions on the branch (round 3)

Collected from the `Assumptions:` sections of the branch's commit messages (`git log origin/main..HEAD`). Extra places to look, never the review's scope. The builder did not run: this is supervisor-authored text, so every item is the supervisor's own.

## From the first commit (the open list)
- Workflow names other than Game Development / Roblox Game are derived by the supervisor from the owner's naming shape → accepted (reported to the owner as a notice they can stop). Superseded in round 3: every name is now pinned by a test.
- A sub-type's Default traits cell is the complete default set for that sub-type, in place of its type's → test (test_open_list.py pins it by equality).

## From round 1's fixes
- The workflow names other than Game Development / Roblox Game, now including "Own-Computer Software Development", are supervisor-derived from the owner's naming shape → accepted; a rename is one line plus its test (true from round 3, which pins every name).
- The `Workflows:` line's grammar (which column names a type, sub-type, trait) → deferred to TASK-007's brief.

## From round 2's fixes (this round)
- The seven workflow names and nine sub-workflow names beside the owner's two follow §6.3's stated shape; they are now pinned, so a rename is a change to the file and its test together → test.
