# ASSUMPTIONS - TASK-029

From the `Assumptions:` sections of the branch's commit messages, whole, by commit (extra places to look, never the review's scope).

## 18a713e TASK-029 r1: the launcher's machine-wide slot, as the builder left it (defects named)

- the record's field names -> accepted (the brief named the fields,
  not the keys; the record is the launcher's own).
- msvcrt.locking and fcntl.flock release when the holder is killed ->
  test (test_r040_killed_holder_frees_slot) and Done when (e).
- os.replace under a concurrent reader leaves a whole old or new file
  -> test, for round 2 (none exercises a concurrent reader).
- GetProcessTimes and /proc starttime agree with the record within
  0.01 s -> test, for round 2 (the creation-time check is the
  liveness mutation the builder reports surviving).
- the BRIDGE_RUN_SLOT_SCALE refusal comes before the started line ->
  test, for round 2.

## 8460ea6 TASK-029 r2: the slot's waits always end, its record is validated, its tests rewritten

- GetExitCodeProcess and WaitForSingleObject tell an exited process
  from a running one with the access mask used -> test
  (test_r040_untrusted_records_in_process, a dead pid; the review's to
  confirm it is a killed helper's).
- the 0.01 s creation-time tolerance holds on Linux CI -> test (CI's
  ubuntu job runs the in-process record tests).
- the stand-in gh on PATH is found before a real gh on Windows -> test
  (test_r040_review_and_watch_skip_slot passes locally; a real gh would
  reach the network, which the review checks).

## 2ef1060 TASK-029 r3: the record's read never raises or blocks, review runs carry only cursor-agent

- one os.read(fd, 4097) on a regular file returns every byte when the
  file is smaller -> test (test_r040_untrusted_records_in_process reads
  the well-formed twin live on Windows; CI's ubuntu job runs it too).
- O_NONBLOCK does not change a regular file's read on Windows -> test
  (os has no O_NONBLOCK there, getattr gives 0; the live read above).
- after five failed os.replace the temporary file still exists and is
  removed -> test (test_r040_unpublishable_record_keeps_the_slot lists
  no .tmp file left).

## 166cb97 TASK-029 r4: a driver's program checked again after the slot's wait

- the Windows Job's creation and assignment touch no file the second
  check relies on -> test (the [False] and [True] cases run with the
  Job on Windows; CI's ubuntu job runs the other branch).
- os.link leaves st_nlink 2 and _supervisor_file_ok refuses it -> test
  (the test asserts both as preconditions).
- the operating system frees the lock at the launcher's exit before
  the follow-up run -> accepted (docs/HARDENING.md, TASK-029 round 4:
  the release on refusal not pinned by a test).

