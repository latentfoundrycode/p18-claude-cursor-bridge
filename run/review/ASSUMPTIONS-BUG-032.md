# ASSUMPTIONS - BUG-032

From the `Assumptions:` sections of the branch's commit messages, whole, by commit (extra places to look, never the review's scope).

## 5acc8f6 BUG-032: round 1, the builder's change to the four programs

- pytest's exit-4 line form for a conftest that fails to load -> test
  (round 2's last exact stderr line, test_bug032_r2_a_conftest_that_writes_...)
- the relpath form of the reported conftest on Windows and Linux -> test
  (CI runs on Linux; the round-2 tests run there)

## 977e816 BUG-032: round 2, the builder's corrections to causes 1 and 4

- the builder's report said none; it assumed pytest's own line is always
  a line of its own -> test (round 3, test_bug032_r3_a_conftest_hides_...)

## 1623026 BUG-032: round 3, the builder's per-file confirmation and the snapshot rule

- git ls-tree prints nothing for a path absent at the commit -> test
  (test_bug032_r3_a_git_failure_..., round 2's unchanged-conftest test)
- the single-file runs plus the joint run stand for the old final full
  check -> test (round 2's two-conftest test)
- PY_COLORS=0 keeps pytest's own line plain -> accepted (pytest reads
  PY_COLORS before FORCE_COLOR; a conftest that forces colour only gets
  the run refused)

## b1a402d BUG-032: round 4, a checkpoint file is blocked only by its own run

- none in the builder's report; Review A's note that every stored
  conftest is on its own file's way rests on the off-the-way refusal ->
  test (rounds 2 and 3's tests, indirectly; recorded in HARDENING)

