# ASSUMPTIONS - TASK-010 (with TASK-015)

From the branch's commit messages (`git log b17cb04..HEAD --format=%B`), sections `Assumptions:`:

Assumptions: the builder's one (mutation (v1) uncaught because the path
test is redundant with the line test) -> test, wrong as stated: a plain
subclass slices to exact strs, so only the line test holds it, and the
supervisor's plain case now kills (v1); Review A's unlisted one (the
checker does not touch sys.stdout.buffer or reconfigure at import) ->
accepted, true of workflow-check.py (both under its __main__ guard), and
a checker that does fails closed as "cannot be loaded (AttributeError)";
docs/HARDENING.md records it.

Assumptions: none listed by the builder; Review A's unlisted two (the
strings from wc.file_lines behave as plain str -> fixed in round 7,
R7-1; the SystemExit branch of the new guard works -> test, the
supervisor's checker-name-exits, green against this round).

Assumptions: none listed by the builder; Review A's unlisted three
(reading __name__ cannot raise -> false, fixed in round 6, R6-1;
load_tables returns the given path through slash unchanged -> accepted,
true at workflow-check.py:260, and a changed path falls to the fixed
"an unexpected table error"; the Linux kill of mutation (x) assumed ->
test, the supervisor's round-6 mapping test kills it on every platform).

Assumptions: none listed by the builder; Review A's unlisted two (equal
normcase(abspath()) means the same file is opened; type(err).__name__ is
a string) -> both fixed in round 5, R5-1 and R5-3.

Assumptions: none listed by the builder; Review A's unlisted one (the
link test's path and the read's path agree only on a standard install)
-> fixed in round 4, R4-3.

Assumptions:
- a pointer line split with ";" and no space ("a.md;b.md") is one path, which fails the pattern -> accepted (Requirement 4)
- table_error_shown maps only the open list's and the registry's paths -> not accepted: its fallback prints the returned path (Review A B2); round 3, R3-2

Assumptions:
- the cannot-read line's wording -> test (round 2's tests assert the line, its file and its home form)
- a trailing ";" on a pointer line -> accepted (Requirement 4: a path outside the pattern is ignored; the report's description is corrected in round 2, R2-7)
- sys.dont_write_bytecode keeps __pycache__ out -> test (test_r005_a_run_leaves_no_bytecode_under_the_home)
- pointer-line files suppressed when the tables fail -> accepted (Requirement 7's text; round 2 keeps it)

Places to look all the same: whether every passage moved verbatim and the core still says what it said (the traceability check traces passages, not their sense across a module boundary); every pointer from the core to a module and from a module back; whether a rule that holds in every phase stayed in the core; what the hook prints for every phase value and every failure of the checker or the tables; every path the hook reads or prints (links, junctions, `..`, the home form); whether each test fails on the defect its docstring names; whether the records claim more than the tests show; any computer path in a committed file.
