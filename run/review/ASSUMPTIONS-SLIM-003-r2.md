# Assumed, not verified: SLIM-003, round 2

Extra places to look, never the reviewer's scope.

1. That the whole suite passes on this head. It ran once on the prepared branch before the rebase (one failure, fixed); since then only the files that bear on each change ran. CI's run of the pull request is the proof.
2. That the changelog entry now says nothing false of a text. Round 1 found two such sentences and Review A one; a read-only agent then checked the entry sentence by sentence and fourteen more were corrected, and Review A's confirming read found one of the corrections false in turn (fixed). The agent named what it did not check: the entry's statements about the programs beyond those two reviewers had verified (C1, C18, M2, the program half of S2 to S5), the count "34 prose-literal tests", and the seventeen lines of retired tests (retired with #153). Review A's last read covered the one sentence of its commit, not the entry.
3. That the passage comparison saw every removed rule. It was one read-only agent's reading by meaning of the branch's first commit; the fact check of the changelog found that four pitfall Corrections had been condensed to pointers, which the comparison had filed under carried rows and weakened items.
4. That the pinned checkout SHA is the one upstream tags v7.0.1: Review A's security auditor read it from GitHub's API in round 1; nothing in this repository verifies it.
5. That no project's running state depends on the status file's `Increment:` and `Last accepted:` lines. No program of the bridge reads them (searched); a project's own tooling was not searched.
6. That the trace check's `0 dropped` covers what it is meant to: a deletion under an excused section shows only in the excused count (106), which no test pins any longer (#153).
