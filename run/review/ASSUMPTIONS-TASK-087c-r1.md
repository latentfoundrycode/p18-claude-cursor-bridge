# ASSUMPTIONS: TASK-087c (Review B, round 1)

Supervisor-written text: no builder ran, so there is no builder's `Assumed, not verified` list. The accept commit's Assumptions section and the records' leads, as places to look, never as your scope:

1. docs/ROSTER.json and the policy's template name review_b_alt in the native profile only; the reason is roster-check.py's resolution of a profile whose Review B its pool excludes (the SCOPE file's deviation 1).
2. The step 3b sentence "is rebuilt by the new profile's builder before any Review B reads it" is kept whole because tests/test_release_t_ceiling.py holds it; the next sentence says the rebuild comes last.
3. A reviewer's tests run from the checkout write __pycache__; this repository ignores it and verify's cache folders stand apart (a HARDENING lead).
4. The policy's Phase 2 sentence names a third failure or an exit 5 as the design's wait, not FAIL, which the design module makes the owner's decision (a HARDENING lead).
5. diff-reviewer's stripped test command assumes the launcher's test kind admits `-p no:cacheprovider` after pytest and runs in the foreground of a subagent.
