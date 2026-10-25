# ASSUMPTIONS - BUG-020

From the `Assumptions:` sections of the branch's commit messages (extra places to look, never the review's scope).

- How fromtimestamp with tz=None reads an instant in the repeated hour on Windows -> test (corrected): probed on this computer on 2026-10-25, 00:49, 01:09, 01:49 and 02:09 UTC read as 02:49 (fold 0), 02:09 (fold 1), 02:49 (fold 1) and 03:09; the fixed cron_next with no zone returns 01:09 UTC for `9 2 25 10 *` from 00:35 UTC and 01:49 UTC for `49 2 25 10 *` from 01:20 UTC (the supervisor and Review A, apart).
- The builder listed none. The brief's named item, how fromtimestamp with tz=None reads an instant in the repeated hour on Windows -> test: test_the_hook_input_is_read_in_its_live_forms passed at 01:38 UTC on 2026-10-25, inside this computer's repeated hour (observed).
- cron_next now returns an int, where it returned a float -> accepted: its one caller compares it with numbers only.
- The timedelta import is now used by no code in loop-guard.py -> accepted: the brief kept every line outside cron_next unchanged; a lead for the next refactoring pass.
