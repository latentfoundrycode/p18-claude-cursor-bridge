# ASSUMPTIONS - BUG-029

From the `Assumptions:` sections of the branch's commit messages, whole, by commit (extra places to look, never the review's scope).

## 38ca64b BUG-029: the launcher knows cursor-agent by one exact name, and publishes its record before the slot-taken line

- os.path.dirname of a bare agent name is empty on every platform ->
  test (the exact-name tests run on Windows here and on CI's ubuntu).
- another process reading the record on the slot-taken line sees it
  -> accepted (os.replace is atomic, KP-047; the line follows the
  replace in program order; the test reads in-process).
- the full run's nine errors were the install-stamp tests only -> test
  (the supervisor's suite after the manifest's regeneration: 0 errors).

