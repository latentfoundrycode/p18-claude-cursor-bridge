# Assumptions, TASK-054

No builder ran: TASK-054 is supervisor-authored (records; the installed records-migrate.py run by the supervisor). The supervisor's own assumptions, each with its disposition. Extra places to look, never the review's scope.

- The pull request takes number 150 (one above #149, the latest pull request or issue): the status file's Last accepted names it, and the full suite ran with GITHUB_REF=refs/pull/150/merge -> test (the status-file test in CI); repeated with the real number if GitHub issues another.
- The installed program that wrote the migration is the reviewed one: the installed records-migrate.py and bridge_env.py hash the same as this repository's copies under bridge/cursor-bridge/ (Review A checked the sha256 of both) -> test (bridge-check 149 OK, INSTALLED TREE MATCHES 2026.11.11a).
- The status file's shortened lines lose nothing a resume needs: the fixed and closed issues stand in the Issues file in Documents/ and in docs/archive/STATUS_HISTORY.md; the TDP's older calibration history in HARDENING -> accepted (Review A read the shortening; its one loss, the TDP's pause at the owner's word, restored).
- The migrated status file renders on GitHub as a front-matter table above the prose -> contract (checked on the pushed branch before the merge; Typora not opened, told to the owner).
