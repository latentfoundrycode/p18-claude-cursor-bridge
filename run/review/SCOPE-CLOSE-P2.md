# SCOPE - CLOSE-P2 (stage P2's close records, pull request #183, round 1)

## What this is
The records of stage P2's close (bridge/cursor-bridge/workflow/phases/reflection.md, "At a stage close", items 1 to 5): no program, no test, no instruction text changes. It takes the full gate, not the short one, because `review-guard.py premerge-records` names two files that keep the round: docs/REQUIREMENTS.md (the text of the built rows R-080, R-081 and R-082 changed) and docs/INVENTORY.md (a line of the threat-model rows changed, the row on the strip's limits). The diff is run/review/CLOSE-P2-r1.diff, `git diff origin/main HEAD` at the records commit (seven files).

## What each change claims, and what to check it against
- docs/REQUIREMENTS.md, three built rows' text (their Status and Evidence unchanged):
  - R-080: a secret-like `CURSOR_` name is withheld from *stripped* test and driver runs. Check against bridge/cursor-bridge/bridge-run.py (the `is_agent` and strip handling near the environment build, about line 2849) and TASK-060's brief, Requirement 5.
  - R-081: the GIT-CONFIG line's word is `new`, `removed`, `changed` or `unreadable`. Check against bridge-run.py's `git_config_changes` (about line 2592) and the line it writes (about line 2952), and step 4 of bridge/cursor-bridge/workflow/phases/delegation-loop.md.
  - R-082: the text now states the flat grammar TASK-063's two resolution rounds chose (handoff/RESOLUTION-TASK-063.md, RESOLUTION-TASK-063-2.md; docs/CHANGES.md, the two TASK-063 resolution entries): a `$`, a backtick or a process substitution outside single quotes makes a command unreadable and refused. The removed clauses described a reading the guard does not do. Check against bridge/cursor-bridge/permission-guard.py and tests/test_program_permission_guard.py (the flat-grammar cases near lines 114 to 131). A row's text must say what the code does; it must not narrow or widen what the row requires beyond the built behaviour.
- docs/INVENTORY.md: six Features rows for what stage P2 built (each row's Where and Tests must name files that exist and hold what the row says); the threat-model row on the strip's limits now says the launcher's git-config comparison is built by R-081, a detection that restores nothing (it was "a program item"). That row bounds what a reviewer's finding blocks: check that the change states what was built and widens or narrows no boundary.
- docs/DESIGN.md: J17 names the fourth word; the context data-flow paragraph says the comparison is built.
- docs/HARDENING.md: the refactoring pass's gate end; stage P2's review, round 1 (every part's notes, convergent ones marked); the demonstration (43 of 44, push-scan's exit on the stage's own commits the one item drawn); least confident (three items). Check that each claim matches the review files and the demonstration output it cites where you can read them: the stage review's inputs are under the local tag stage-review/P2-1 (read with git cat-file -p stage-review/P2-1:run/review/SCOPE-STAGE-P2.md), and the demonstration's script is run/supervisor/demo_p2.py, its output run/agent/demo-p2.out (both gitignored, present in the checkout).
- docs/PROJECT_STATUS.md and project.json: stage P2 closed, stage P3 next, the header and the prose agreeing; the section "Release B - notes for a resuming session" moved word for word to docs/archive/STATUS_HISTORY.md to keep the status file under its cap (inventory-check.py now OK).

## Checks already run
conformance 25 OK, 0 MISSING, 5 NOTE; `completion-check.py --mode plan` OK (89 built, 2 deferred, 14 planned); `inventory-check.py` OK (status 28 lines, 11104 characters); invisible-check OK; the twenty test files that read the changed records, stripped through the launcher: "553 passed, 1 skipped".

## Out of this pull request
The Documents/ folder (the Issues file, Feedback FB-109 to FB-117, the Project Summary, the User Manual) lies outside the repository. Stage P3 and TASK-078's Scope notes are later work.
