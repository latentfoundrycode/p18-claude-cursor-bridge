# Assumptions, TASK-068

The builder's Assumed, not verified lists of its three rounds (handoff/TASK-068-report.md, TASK-068-r2-report.md, TASK-068-r3-report.md), each with the supervisor's disposition. Extra places to look, never the review's scope.

Round 1
- The byte lock plus one write keeps each run's line whole beyond the eight concurrent runs the test starts, and on Linux; a second writer that takes no lock -> CI's ubuntu job runs the concurrent case; the one writer without the lock is the supervisor's stand-in run/supervisor/append_inflight.py, retired at this merge (HARDENING, TASK-068, working practice).
- A junction under run/supervisor/ is refused, and a symbolic link whose target stays inside that folder -> the link case runs in CI's ubuntu job (it skips on this Windows account, which cannot create a symbolic link); a junction probed on Windows (run/supervisor/task068_probe.py): refused, the log unchanged; round 2 and round 3 added junction cases that run here.
- A log whose last byte is not LF gets one before the new line -> probed: the break added.
- A line of only Unicode space separators (Zs) is blank and dropped, and Zs spaces are removed from either end -> accepted, HARDENING lead 6.
- A lock timeout leaves an empty log the run created -> accepted, HARDENING lead 4.

Round 2
- The Linux arms (O_NOFOLLOW, fcntl) -> CI's ubuntu job.
- A short os.write is reported INCOMPLETE -> read in review (Review A).
- The folder check before Python 3.12 (no os.path.isjunction) reads the reparse attribute -> accepted, HARDENING lead 2.
- A reader still reads while the lock is held, and a second run gives up after 10 seconds -> probed (run/supervisor/task068_lockprobe.py): the reader reads; a second run exits 2 after 10.1 seconds, nothing appended.

Round 3
- O_NOFOLLOW makes a symbolic link at the log fail the open on Linux -> CI's ubuntu job. The report says Windows has O_NOFOLLOW; it has not (Python 3.12.10, Review A), so on Windows a link at the log is refused by the folder checks' reparse test alone (the junction cases pass here).
- os.lstat before the open disagrees with os.fstat when the --file path is swapped for a link between the check and the open -> not reproducible here (H3 left the acceptance file green; the link case skips); HARDENING lead 8.
- The second folder check after the open refuses a run/supervisor/ link that appears during the lock wait -> a race this host cannot stage; HARDENING leads 1 and 3.
