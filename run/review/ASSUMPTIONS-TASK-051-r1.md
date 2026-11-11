# The builder's assumptions, TASK-051 (from the branch's commit messages)

Extra places to look, never the review's scope.

## 65eec3f TASK-051: records-migrate.py accepted, round 3 (R-062)

Assumptions:
- realpath resolves junctions on Windows -> test (the round-3 junction cases run here)
- a file symbolic link inside the root differs from the joined path -> accepted
  (realpath resolves the last component; the round-2 case skips on this host;
  HARDENING)
- closing the handle before os.remove on a write failure is needed on Windows ->
  test (test_r062_r2_a_write_failing_after_the_open_leaves_no_temporary_file)
- VERSION left as make-manifest left it -> accepted (restored by the supervisor)

## 5835161 TASK-051: records-migrate.py, round 2 as the builder delivered it (R-062)

Assumptions:
- F14 refuses only os.path.islink paths -> test (round 3: a junction parent, a defect,
  re-delegated)
- F15 exercised only with an in-process relpath stub -> accepted (a second drive is
  not available; HARDENING at the records commit)
- the OSError-on-open wording uses str(exc) -> accepted (a local program's own
  output; HARDENING at the records commit)

## 967c659 TASK-051: records-migrate.py, round 1 as the builder delivered it (R-062)

Assumptions:
- short-scalar flow lists match the heuristic -> test (the read-back through
  bridge_env.read_header and the round-2 digit-string case)
- a given record path that does not exist is skipped silently -> test (round 2: a
  missing path is listed as cannot read; a defect, re-delegated)
- the merged-set-unreadable wording -> accepted (pinned on the no-such-ref case;
  INVENTORY row at the records commit)
- a nonexistent explicit path produces no line -> test (the same round-2 case)
