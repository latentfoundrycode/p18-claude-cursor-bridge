# ASSUMPTIONS — TASK-082, round 1

No commit of the branch (b213ea6..HEAD) carries an `Assumptions:` section: TASK-082 is a supervisor text increment with no builder run, so there is no builder's `Assumed, not verified` list. The supervisor's own readings, each recorded in docs/HARDENING.md (TASK-082) and open to challenge:

- "One range form" for push-scan.py is `push-scan.py origin/<the base>` (its one positional argument, the revision the range starts after), the form both the sentinel and step 8 name.
- The policy's "copy of step 8's merge and watch text" retired to a pointer is the paragraph "CI green means the run of the pushed head" and the paragraph "Completing the merge — do not depend on GitHub's auto-merge queue", with its safety-net sentence; "Enforcement at merge" keeps its opening, its steps 1 and 3 and the toggle warning, step 2 rewritten.
- The demonstration's `-B` sentence names `python -B -m pytest <its test files>` after `--kind test --` rather than a full launcher command, so that the four documented `--strip` launches tests/test_allowlist.py pins stay four.
- The three pinned tests outside the plan's first Scope are widened into it at the checkpoint, as earlier increments widened theirs (TASK-024, TASK-035), the plan's prose and header together.
