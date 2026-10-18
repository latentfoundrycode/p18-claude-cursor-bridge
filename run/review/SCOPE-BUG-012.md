# SCOPE — BUG-012

## Scope
BUG-011's gate round 3 (snapshot BUG-011c): Review B and Review A APPROVE, and BUG-011 merged on that head (e9ed1b2, PR #37). Review A's one should-fix: docs/HARDENING.md's round-10 section, "Considers, recorded, not taken", the Tests line, still held one mutant equivalent on a rule the program does not check: allows_set (bridge/cursor-bridge/workflow-check.py:284-285) read as `"set" in cell`, argued equivalent because every registry Changes cell is add or set. A rule-breaking cell `add, reset` separates it: the program refuses a Set there, the mutant accepts it. BUG-011 adopted the standard that a survivor any input separates gets a case, rule-breaking inputs included; this increment applies it here.

## Out of scope
- Any change to the programs. The program leads in HARDENING (the Of type finding, the Key format) stay for the next change of workflow-check.py.
- Review A's notes on BUG-011 (the scope file's "five", which left with BUG-011's review files; program lead (1)'s examples, now recorded as one example per kind of line).
- Design for later increments is not this diff's defect.

## The test the supervisor wrote, and what it enforces
- tests/test_workflow_check.py, test_r014_set_changes_cell_is_split_on_commas_and_stripped gains a third registry: the pass root's point intake.target-environment with the Changes cell `add, reset`, expecting `FAIL (set) ... point does not accept set`. It enforces handoff/TASK-006.md Requirement 4, the `set` finding: "a `Set at` names a registry point whose Changes cell, split on commas and stripped, does not contain `set`". The docstring says such a cell breaks the registry's own rules and the finding is the one the text fixes. The supervisor ran it on a copy of the Workspace: it passes on the program and fails with allows_set as `"set" in cell` (run/supervisor-side script, not in the diff). Nothing in the test was removed or loosened; the two earlier cells stand.

## Expected bookkeeping in the diff
docs/HARDENING.md (the round-10 considers line; the "BUG-011's gate round 3" paragraph), docs/PROJECT_STATUS.md (BUG-012 in flight, BUG-011 accepted), run/review/ (the review files).
