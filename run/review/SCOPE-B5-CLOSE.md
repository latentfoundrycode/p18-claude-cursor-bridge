# SCOPE - B5-CLOSE (PR #104)

Stage B5's reflection point, records only (bridge/cursor-bridge/workflow/phases/reflection.md, items 2b and 5; the status-file convention in docs/PROJECT_STATUS.md, "How this file is written (ISS-009)"). The stage review closed at its round 3, the first at the three-round ceiling (applied by hand until release B installs, docs/INVENTORY.md, Decisions), with nothing of the five blocking classes; no round 4 runs.

Allowed files: docs/HARDENING.md, docs/INVENTORY.md, docs/REQUIREMENTS.md, docs/PROJECT_STATUS.md, docs/archive/STATUS_HISTORY.md, project.json, the review files under run/review/, and docs/ROSTER.resolved.json, whose `resolved_at` stamp the roster check rewrites before every Review B (a stamp commit of its own, bookkeeping). No program, test, bridge, CI or other record file.

What the change must do:
- docs/HARDENING.md, under "Stage B5": a "Stage B5's review, round 3" section (the round, its Should-fix findings each ruled against the five classes with its lead or mitigation, the Consider findings recorded); a "Stage B5's demonstration" section with the live run's result on main at ad1ad0a (run/supervisor/demo_b5.py, output run/agent/demo-b5.out, both local); a "Least confident (stage close, 2026-10-29)" list of three specific items, each with a concrete check (all three are checks at stage B6, after the install; none is settled by a test the supervisor can write before TASK-026); two existing entries corrected (a stale line citation; BUG-033's entry lacked Review B's round-2 APPROVE).
- docs/INVENTORY.md: row 40 (BUG-032's per-file conftest judgement and its limits, its tests), row 88 (the slot holds builders once release B installs), row 103 (the core's and the modules' sizes at the stage's close, measured as characters with universal newlines), row 140 (a launch refused the slot is no start).
- docs/REQUIREMENTS.md: R-041's Evidence names tests/test_bug032.py.
- docs/PROJECT_STATUS.md: the position at this pull request's merge (Last accepted names PR #104 first; In flight none; Next stage B6 from TASK-026, TASK-027 stamping and installing); Stage: B5 closed 2026-10-29; Last reflection stage B5's close; Open issues rewritten; the two replaced lines moved word for word to docs/archive/STATUS_HISTORY.md; under 12,000 characters.
- project.json: state.stage and state.updated.
- The pull-request title names no plan ID inside a closing parenthesis (ISS-013).

Sources of the records' claims: the round-3 verdicts in run/supervisor/in-flight.md (lines beginning `r3 RA` and `STAGE-B5 r3 DONE`); Review B's round-3 reply in run/supervisor/stage-b5-r3-reviewB.txt; the installed conformance check run by the supervisor at the reflection point, 21 OK / 1 MISSING (the recorded no-diagram-index decision) / 6 NOTE (in-flight.md). All local, gitignored.

Not in the diff, written at this reflection point outside the repository (Documents/ is not under git): the Issues file (ISS-011 and ISS-015 updated, ISS-017 and ISS-018 completed, ISS-019 added), the Feedback file (FB-051 to FB-062) and the Project Summary's stage B5 section.

Checks run on this branch: inventory-check.py OK; completion-check.py --mode plan OK; git worktree list shows no worktree under Worktrees/; the full suite 3246 passed, 41 skipped (before Review A's wording fixes; after them the record-reading tests, 150 passed, 1 skipped); Review A APPROVE 0/2/6, all taken; secret-sentinel PASS.

## Round 2 (Review B, round 1: REJECT 2/1, all taken)
- The status file's Next names the install ruling as HARDENING records it: an increment in flight at the install with no report file is seeded by hand (it had said no item in flight on any project).
- Least confident 2 describes the guard's seeding as review-guard.py does it: every review-<ID>-r<N>.json snapshot skipped, the letter-named snapshots and the report files' rounds counted, the larger taken.
- Open issues: ISS-016 fixed by BUG-028 (before this close); ISS-017 to ISS-019 completed at it.
- This is the records' second Review B round of three.
