# ASSUMPTIONS - TASK-028

From the `Assumptions:` sections of the branch's commit messages, whole, by commit (extra places to look, never the review's scope).

## eb48123 TASK-028: windowless launches enforced by the bridge, the launcher's driver kind and the suite's frozen default

- the builder's list reads none (handoff/TASK-028-r1-report.md) -> unknown, not none: the reviewers hunt unaided, and the brief's settled gaps (healthy at exit 0 or 1 only; no ALLOW_ANY exemption; py -3 refused; the installed mutation-run.py path not link-checked) are the places to look.

## d8cad91 TASK-028 r2: the driver kind's path check closed, the windowless floor never crashes

- os.path.isfile is false for a folder named x.py and for an
  alternate data stream token -> test (the folder and ADS refusal
  tests run on Windows; the ADS token is also refused by the `:` rule
  before any file test).
- pytest's own handling of a testpaths entry outside the project ->
  test (not relied on: the floor applies the brief's containment rule,
  pinned by the outside-root tests; it reads only the project's files).
- the re-check test relies on a patched verify function -> test (no
  longer: the supervisor's rewrite swaps the program in branch_of and
  calls the real re-check).

## 57672d4 TASK-028 r3: link-safe test roots, no crash on nesting, the runner word escaped, hard links refused

- the alternate-data-stream token is refused by the `:` rule, not only
  by isfile -> test (the rewritten test asserts the stream is a file
  before the run; that the test dies with the rule removed is the
  reviewers' mutation to confirm). Round 2's disposition of this item,
  "test", rested on a test that never created the stream (Review A,
  round 2): that disposition was wrong.
- st_nlink is 2 for a hard link on this file system -> test (asserted
  before the refusal).
- deeply nested TOML and JSON raise RecursionError on Python 3.12 ->
  test (the two nesting tests).
- shlex with backslashes held keeps `TOKEN="abc4x def7z"` grouped ->
  test.
- a copied conformance-check.py without bridge_env.py beside it uses an
  inline is_link -> defect (fails open, a second copy), for the next
  round.

## 4dedcfd TASK-028 r4: uv_run_pytest restored, testpaths entries holding `..` dropped

- the builder's list reads none (handoff/TASK-028-r4-report.md) ->
  unknown, not none: a two-line change; the reviewers hunt unaided.

## 2985faf TASK-028 r5: the windowless floor never crashes and prints no control character

- a NUL makes os.lstat raise ValueError before any other os.path call
  on the entry -> test (test_r039_nul_in_testpaths_dropped).
- escape_field renders U+202E as \u202e and keeps `/` -> test
  (test_r039_ok_row_path_is_escaped, on a UTF-8 console).
- SystemExit and KeyboardInterrupt are not caught by the backstop ->
  accepted (docs/INVENTORY.md, Decisions).
- the NUL case would reach the backstop, not MISSING, with requirement
  1 removed -> test: the NUL test expects the MISSING row, so the
  backstop's NOTE fails it; the report's doubt is unfounded.

