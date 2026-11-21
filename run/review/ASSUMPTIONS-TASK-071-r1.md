# Assumptions, TASK-071

The builder's `Assumed, not verified` list (handoff/TASK-071-r1-report.md) and the supervisor's, each with its disposition. Extra places to look, never the review's scope.

## Round 1
- The builder wrote none. Review A named three the code settles -> accepted: both programs strip a byte-order mark alike (inventory-check reads utf-8-sig, the migration decode_record_bytes); check_header refuses a header value that is not a string before the helper sees it (probed: 5, null, true, [] each "wrong type"); records-migrate.py imports bridge_env without a guard list, so an older bridge_env beside it raises on the new name as on every other name it uses, the two files installed together.

## The supervisor's
- Empty means exactly the empty string -> accepted: it is what the fallback gives for a missing line or a bare label, and what a header gives as ""; a header value of spaces only is not refused (no test pins it).
- A refused record under --check now exits 0 where it exited 1 -> accepted, the plan's "the exit rule for a cannot read unchanged"; calibration's text names the new reason with TASK-078 (HARDENING lead 5).
