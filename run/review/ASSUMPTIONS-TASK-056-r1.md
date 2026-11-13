# Assumptions, TASK-056

No builder ran: TASK-056 is supervisor-authored (records and tests). The supervisor's own assumptions, each with its disposition. Extra places to look, never the review's scope.

- The pull request takes number 159 (GitHub's latest issue or pull request is 158): the status file and HARDENING's TASK-056 heading name it -> test (CI's status-file test reads the pull request's number).
- The reality check (an agent's read of main 77dbdf3) found every test that holds a program row's clause; a clause it missed would read built on a test that does not hold it -> accepted, with Review A's read of every named test, and the four clauses it found unheld tested in tests/test_program_release_s_rows.py, each red on a mutant.
- Each text entry's heading states its row's clause (completion-check checks the heading exists and the pull request changed the file, never what the section says) -> accepted, Review A read each section for its clause.
- R-042's P2 entry names decide.md's step 7, not the plan's supervisor.md :: Standing rules, because release S moved the membership sentence there -> accepted (Review A: supervisor.md's Standing rules no longer hold the sentence); recorded in the row and in HARDENING's TASK-056 entry.
- Holders outside the Scope (tests/test_account_keys.py, tests/test_install_check.py, tests/test_session_start_module.py, tests/test_release_t_merge.py, tests/test_release_b_ci_floor.py, tests/test_dependency_scan.py) are named in Evidence without the rows' IDs in them -> accepted, a HARDENING lead for each file's next edit.
