# ASSUMPTIONS — BUG-010

From the branch's commit messages (`git log origin/main..HEAD --format=%B`), section `Assumptions:`:

Assumptions:
- the r2 builder's list: none (handoff/BUG-010-r2-report.md) -> accepted, as for r1: the
  facts the guards rely on are stated in the brief and confirmed in the installed argparse
  source.

Assumptions:
- the builder's list: none (handoff/BUG-010-r1-report.md) -> accepted: the facts the
  guards rely on (print to a None stdout writes nothing; argparse's print_usage and exit
  tolerate a None stream) are stated in the brief and confirmed by Review A in the
  installed argparse source.

Places to look all the same: the expected outputs of the supervisor's new tests were taken from the check's output and then read against the rule each case names; a wrong rule would make a wrong expected line look right. Where no document fixes the order of findings, the tests pin the order the program gives. The control-flow sweep's survivors are recorded in docs/HARDENING.md by class, and each class is the supervisor's reasoning, not a test.
