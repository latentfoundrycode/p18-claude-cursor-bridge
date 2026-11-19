# ASSUMPTIONS - REFAC-P2

From the `Assumptions:` sections of the branch's commit messages (extra places to look, never the review's scope).

- The builder's list is "none"; the change relies only on facts the
  brief settled by reading the code (both re-checks pure, same
  arguments) (accepted: read by the supervisor).
- The builder's list is "none"; the one fact the change relies on (git
  prints --show-toplevel as a resolved absolute path) is the brief's,
  settled by reading _git_display_path and _git_file_state (accepted:
  read by the supervisor).
- `GitConfigWatch.after.__name__` now reads `before`; no caller or test
  reads it (accepted).
- The brief's word grep also hits the committed brief itself; those hits
  are the brief's words, not definitions or uses of the names in code
  (accepted: read by the supervisor, as at REFAC-008).
- The brief's greps also hit the committed brief and the substring
  `_check_app` inside a test name in tests/test_loop_guard.py; neither is a
  helper definition or a use of the new names (accepted: read by the
  supervisor).
