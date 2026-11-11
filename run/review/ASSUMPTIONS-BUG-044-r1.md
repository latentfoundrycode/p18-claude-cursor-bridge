# Assumptions, BUG-044

The builder's Assumed, not verified list with the supervisor's dispositions, from the branch's commit messages. Extra places to look, never the review's scope.

## From 4ad4eb0 BUG-044: the migration refuses a plan its headed readers would refuse (R-062)
- a plan's bold-line R-id held plainly in another plan file is refused
  per file, while completion-check reads the union across files ->
  accepted (stricter, the plan stays header-less with its gate as
  before; HARDENING lead)
- plan_header_refusal finding nothing else on a freshly composed header
  -> test (F3's read-back net stops any finding with exit 3; Review A
  showed the header and body IDs equal by construction)
- glob.escape on a drive or UNC root -> accepted (the standard library
  leaves the drive or UNC prefix as written; the auditor probed both)
