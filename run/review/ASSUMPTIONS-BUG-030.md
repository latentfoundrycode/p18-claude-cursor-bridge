# ASSUMPTIONS - BUG-030

From the `Assumptions:` sections of the branch's commit messages, whole, by commit (extra places to look, never the review's scope).

## 47906de BUG-030 r1: the builder's first delivery, rejected

- An untracked conftest.py can reach archive_checkpoint unchecked -> test: it
  can, and the copy followed a link (the security audit); round 2 refuses it
  (tests/test_mutation_run_supervisor.py, test_bug030_r2_ tests).
- make-manifest.py leaves VERSION unchanged -> test: git diff --quiet on
  VERSION, run by the builder and checked again at acceptance.

## 0f1f8b1 BUG-030 r2: round 1's three defects fixed

- The builder's list reads "none" -> noted; Review A named one it missed
  (an exception's text names its module), which round 3 settles by test.

## 93264fc BUG-030 r3: the internal-error line names every module that failed

- The builder's list reads "none" -> noted; Review A named two it missed:
  an exception text with a newline prints the line over several lines ->
  accepted, docs/HARDENING.md (BUG-030; the brief takes the text as Python
  gives it); a non-ASCII text on a cp1252 console -> accepted: the program sets
  stderr to `errors="backslashreplace"` (the audit), so the print cannot fail.

