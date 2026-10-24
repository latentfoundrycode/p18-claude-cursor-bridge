# SCOPE — BUG-019 (pull request #62): the fixes of stage B3's stage review, round 3

This is a supervisor-authored fix increment: no builder ran, so there is no brief under handoff/ and no assumption list (ASSUMPTIONS-BUG-019.md is empty). The supervisor writes tests and records (founding rule N4 permits tests). No program under bridge/ changed and no governance text changed: the diff is two test files and four records under docs/.

## What the stage review found (the "brief")
Stage B3's stage review, round 3: Review B and five of Review A's six parts approved; the records part rejected. docs/HARDENING.md, Stage B3, "### The stage review, round 3 (2026-10-24): rejected, fixed by BUG-019", is the whole record.
- Blocking (Review A records, confirmed): `plan-check.py` derives TASK-031 as merged from 9f6ace6's subject (BUG-018's squash), whose closing parenthesis names "TASK-031's Scope"; its `TRAIL_RX` (bridge/cursor-bridge/plan-check.py:168, the installed copy the same) takes the IDs of any closing parenthesis that holds one. The squash is on protected main and stays; the fix is in the records, the rule a lead for a builder increment (ISS-013).
- Convergent (Review A records and Review B, both consider): docs/INVENTORY.md:81 gave delegation-loop.md at its TASK-013 figure.
- Should-fix (Review A tests): tests/test_phase_modules_close.py's variant-section pins found each section by the first heading of its title, while trace-check.py excuses a passage under every heading of that title.
- Should-fix (Review A records): two recorded triggers passed unmet (tests/test_extension_points.py:40's comment; intake.md's and planning.md's extra-hop pointers).
- Should-fix (Review A core): four core-side `reword` entries name whole baseline sections; recorded with round 1's Standing rules lead.

## What the diff does
- docs/BUILD_PLAN.md: a dated note at the end of TASK-031's Done when (the plan check counts it merged; READY not trusted for TASK-031 or TASK-030; the brief compared by hand). `python ~/.claude/cursor-bridge/plan-check.py` prints the same as on main (17 merged; READY TASK-017, TASK-018, TASK-022): the note changes nothing it derives.
- docs/HARDENING.md: the round-3 section (verdicts, the blocking finding and its lead, the convergent figure, the should-fix items taken or recorded with their triggers, every part's considers).
- docs/INVENTORY.md: row 81 gains the close's figure for delegation-loop.md (574 lines, 55,464 characters, 92.4%); Updated 2026-10-24.
- docs/PROJECT_STATUS.md as at this pull request's merge (ISS-009: Last accepted names PR #62 first, In flight none, Remote sync PR #62); Next: says READY is not trusted for TASK-030 and TASK-031; Open issues names ISS-013.
- tests/test_phase_modules_close.py: test_each_excused_variant_section_is_pinned reads headings as trace-check.py does (trace_headings: up to three spaces of indent, none inside a fenced block, a fence closed as trace-check.py closes one), asserts the variant file has exactly one heading of the section's title, at any level, and ends the section where trace-check.py ends it (enforces: docs/HARDENING.md Stage B3, TASK-014's should-fix 3 and round 3's tests should-fix). Probed on a copy under the temporary folder with a second `## What this variant is` in command-design.md: it fails there, passes on the tree.
- tests/test_extension_points.py: a comment re-pointed from "(supervisor.md, Phase 1)" to workflow/phases/intake.md.

## Tests
The suite on the head: see the PR. The collected set is the same as main's (no test added or removed). `python bridge/cursor-bridge/trace-check.py` must print RESULT: OK with 0 dropped (no bridge file changed).

## Out of scope
Design for later increments; the leads recorded for later increments; the plan check's subject rule (a program, a builder increment's, placed by the pace plan revision); module text the considers name (baseline text whose edits take `reword` entries).

## The gate so far
Review A: round 1 APPROVE (0 blocking, 3 should-fix, 3 consider: all taken in aff662d: the heading reading as trace-check.py's, the growth's attribution to BUG-018, a trigger for the aliases item, TASK-025 named, C3/C4's fallback); confirming read APPROVE (0/1/1, both taken in 597fef7: a fence closes as trace-check.py closes one; the section starts at the heading found); its read of 597fef7 APPROVE 0/0/0. secret-sentinel CLEAR on b68e4cb, aff662d and 597fef7. The suite on 597fef7: 1,963 passed, 33 skipped. No security audit (no logic, input or data surface).
