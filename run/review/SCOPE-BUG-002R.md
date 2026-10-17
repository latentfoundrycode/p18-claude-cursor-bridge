# SCOPE-BUG-002R — BUG-002's post-merge records (PR #28)

The diff is `run/review/REVIEW-BUG-002R.diff` (`git diff origin/main...HEAD`, base 55fd516, BUG-002's squash). No builder ran: every change is the supervisor's.

## The test (the one finding of BUG-002 round 2 that was the supervisor's)
`tests/test_workflow_check.py::test_r014_trait_in_head_is_only_the_shape_finding` enforces R-014 ("every project's `Workflows:` line names ... traits, all in the open list"; a trait's Name is in the open list, so a trait in the head is not `unknown`) and supervisor.md "Project state" (the head is `<Workflow name>[ → <Sub-workflow name>]`, so a trait in it is the shape `form`). It asserts the exact findings of `tests/fixtures/workflows/status/form-trait-in-head.md` (`Workflows: Host Extension Development, Installable; traits: none`): one line, the shape finding, and no `unknown`. Review A (BUG-002 round 2) showed that putting round 1's `else:` back in `check_head` survived every test, printing a wrong `FAIL (unknown) ...: Installable`. The test passes on main's code (the code is right; the test closes a gap); the supervisor's mutation driver (run/supervisor/mutate_workflow_check.py, temporary copies, not in the diff) gained the mutant "trait branch dropped" (`elif name not in tables["trait_by_name"]:` back to `else:`), which this test kills: 82 of 82 killed.

## Records (expected bookkeeping)
docs/DESIGN_CRITIQUE.md (BUG-002's grade rows; the dispositions of its rounds 1 and 2), docs/HARDENING.md (a section for BUG-002: the per-part lead's copy into the Restructuring Plan's §16 carried to stage B2's reflection; TASK-019's brief packaged with the default-traits line; one failing fixture now exact), docs/PROJECT_STATUS.md (BUG-002 accepted at 55fd516; next steps).

Checks: suite 1152 passed, 23 skipped (the skips environmental, as before); secret-sentinel CLEAR; inventory-check OK.
