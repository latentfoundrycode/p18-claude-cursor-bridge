# ASSUMPTIONS - FIX-001

From the branch's commit messages (`git log 2b10bfe..HEAD --format=%B`), sections `Assumptions:`:

Assumptions: none new (supervisor-written test infrastructure).

Assumptions: none new (supervisor-written test infrastructure).

Assumptions: none new (supervisor-written test infrastructure).

Assumptions:
- a grandchild started without flags by a program the suite does not patch shares the child's windowless console -> test (test_fix001_a_grandchild_inherits_the_windowless_console)
- no test sends a console control event to a child it started (CREATE_NO_WINDOW gives the child its own console) -> test (the full suite; grep of tests/ finds no CTRL_BREAK, send_signal or NEW_PROCESS_GROUP)

Places to look all the same: the Popen wrapper in tests/conftest.py (a launch with creationflags=0 on purpose, a launch with its own flags, a test that patches subprocess itself, Linux CI); whether each of the ten tests can fail (the stdin default, the detector); any computer path in a committed file.
