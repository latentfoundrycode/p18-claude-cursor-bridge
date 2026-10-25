# SCOPE - B4-CLOSE (PR #82)

Stage B4's reflection point, records only (bridge/cursor-bridge/workflow/phases/reflection.md, items 2b and 5; the status-file convention in docs/PROJECT_STATUS.md, "How this file is written (ISS-009)"). The stage review closed at its round 7 under the owner's three-round ceiling, applied by hand from 2026-10-25 (docs/INVENTORY.md, Decisions); no round 8 runs.

Allowed files: docs/HARDENING.md, docs/PROJECT_STATUS.md, project.json, the review files under run/review/, and docs/ROSTER.resolved.json, whose `resolved_at` stamp the roster check rewrites before every Review B and which every pull request of release B commits as a stamp commit of its own (bookkeeping, not a record of this change). No program, test, bridge, CI or other record file.

What the change must do:
- docs/HARDENING.md, under "Stage B4":
  - in the round-7 section, BUG-027's Review B verdict (APPROVE) and its one should fix, outside the five blocking classes, recorded as a lead for the next plan revision: spends-money.md:21's "only by the stand-in's endpoint and key" for the deployed-layout test against round 6's lead that the store's place must be a value a test may set;
  - a "The demonstration (stage close, 2026-10-25)" section with the live run's result on main at 5408ab1;
  - a "Least confident (stage close, 2026-10-25)" list of three specific items, each with a concrete check (none is settled by a test the supervisor can write before stage B5's first delegation: two are checks at a later point named in the item, one is the owner's answer).
- docs/PROJECT_STATUS.md: the position at this pull request's merge (Last accepted names PR #82 first; In flight none; Next stage B5 from TASK-023, the owner's traits question asked in the report, the ceiling applied by hand); Stage: B4 closed 2026-10-25; Last reflection stage B4's close 2026-10-25; Open issues ISS-014 fixed and ISS-015 mitigated; Working files names the reflection scripts; under 12,000 characters.
- project.json: state.stage and state.updated, the stage's first word matching the status file's Stage: line (conformance-check.py).
- The pull-request title names no plan ID inside a closing parenthesis (ISS-013).

Not in the diff, written at this reflection point outside the repository (Documents/ is not under git): the Issues file (ISS-014 completed, ISS-015 added), the Feedback file (FB-042 to FB-050) and the Project Summary's stage B4 section.

## Round 2 (Review B, round 1: REJECT 3/3, all taken)
- The roster stamp is named above as expected bookkeeping.
- The status file's Next says the stage-close report puts the traits question to the owner (the owner did not ask it).
- Least confident 3 names Cursor's agent and GitHub as the external services, as the round-1 finding and HARDENING's round-1 section do; Socket is dropped.
- BUG-027's Review B record cites round 6's lead where it stands (Review A on BUG-026, in the round-6 section), not external-services.md:31 as its words.
- The 104 tests are named by their selection.
- The conformance figures are named as the supervisor's run, signed in to gh; a run without the owner's identity (the reviewer's) prints the required-check row and the private-memory rows otherwise.

## Round 3 (Review B, round 2: REJECT 1/0, taken)
- BUG-027's Review B record names its selection exactly: tests/test_traits_new.py, tests/test_traits_existing.py's test_r019_the_two_checks_exist_only_in_external_services (the three whole-section `==` are one test) and the two item-2 tests of tests/test_b3_least_confident.py, which pass 102 (the supervisor's run and Review A's: 102 passed, 17 deselected); BUG-027's reply had said 104, which the record keeps as that reply's figure.
- This is the increment's third Review B round, the last under the owner's ceiling: past it only the five blocking classes send the work back.

Checks run on this branch: conformance-check.py (installed) 22 OK / 1 MISSING (the recorded no-diagram-index decision) / 5 NOTE; inventory-check.py OK; completion-check.py --mode plan OK; plan-check.py OK (TASK-023 READY); git worktree list shows no worktree under Worktrees/.
