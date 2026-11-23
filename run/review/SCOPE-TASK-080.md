# SCOPE - TASK-080: Context7 for the Claude side (R-100)

The supervisor's own text increment, stage P4's second; pull request #201, branch task-080 from origin/main 052ff83. The spec is docs/BUILD_PLAN.md, the section on TASK-080 (Scope, Scope notes, Done when), docs/REQUIREMENTS.md row R-100, docs/DESIGN.md's bullet on Context7 for the Claude side and its host-facts rows, and docs/diagrams/D-004-context-dfd.md (its note and the two flows between p_claude_subagents and ext_docs_service). It changes instruction text, an agent's tools line and a test, so it takes the full gate.

## Round 1 (rejected)
The diff is run/review/REVIEW-TASK-080-r1.diff (origin/main...HEAD, the review files excepted):
- the probe, recorded in docs/HARDENING.md's TASK-080 section, was observed in the supervisor's session after the owner installed the claude command and added the server at user scope; it cannot be re-run from a review: judge whether what was built follows from it;
- bridge/agents/spec-packager.md and diff-reviewer.md: mcp__context7__* on the tools line and a paragraph with the lookup's rules; bridge/cursor-bridge/Cursor-Project-Configuration.md section 3: the Claude side; MANIFEST.json regenerated; tests/test_program_context7.py new;
- records: R-100 built; HARDENING (TASK-079's merge and its CI run across a Monday; TASK-080); INVENTORY's threat-model row for the documentation service and the whole-model row's list; two TRACE_MOVES entries; PROJECT_STATUS (Next, the Deviations line).
Review A (diff-reviewer): round 1 REJECT on two Must fix (the allow-entry test's precondition; a HARDENING count against its run), both fixed in round 2 with four Should fix and two Considers; round 2 APPROVE, its one Consider taken. settings.bridge.json and D-004 unchanged. trace-check --moves OK (2 excused), the pinned mode OK; the rulebook 149,858 words of 150,000; the digest unchanged.
Check each change against the spec and the probe's record, the records against the runs they quote, and that nothing else moved. Review B round 1: REJECT on one Must fix, HARDENING's lead word count (149,859, round 1's) against the tree's 149,858; everything else confirmed.

## Round 2
The commit after "Review files for round TASK-080-r1", whose diff is run/review/REVIEW-TASK-080-r2.diff: docs/HARDENING.md's TASK-080 section gives the tree's count first (149,858 words of 150,000; 149,554 before; 149,859 at the accept commit) and records Review B's round 1; run/review/REVIEW-TASK-080-r1.diff removed. Check the line against round 1's finding and the tree (tests/test_release_s_budgets.py's measure), and that nothing else moved. This is Review B's round 2.
