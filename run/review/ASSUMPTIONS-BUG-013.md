# ASSUMPTIONS - BUG-013

From the branch's commit messages (`git log e1a97de..HEAD --format=%B`), sections `Assumptions:`:

Assumptions:
- none from a builder (supervisor's tests).
- the 196 survivors are equivalent, or separable only by a symbolic
  link this computer cannot make (2, run on CI's ubuntu leg) -> accepted,
  HARDENING round 11; Review B reads every class.

Assumptions:
- none from a builder: no builder ran; the tests and fixtures are the
  supervisor's (N4 permits tests).
- the 202 classed survivors are equivalent or unseparable by any input
  of the check -> accepted, HARDENING round 11 (separate_strings.py's
  corpus of 9,230 inputs found no separator for them).
- test_r014_a_name_ending_in_white_space_is_no_conditional_work... runs
  where the file system keeps a trailing space -> test, on CI's ubuntu
  leg (skip count compared with the windows leg).

Assumptions:
- none from a builder: no builder run in BUG-013; the cases are the supervisor's.

Places to look all the same: each survivor class in docs/HARDENING.md round 11 against an input that would separate it; each new test against the paragraph its docstring names.
