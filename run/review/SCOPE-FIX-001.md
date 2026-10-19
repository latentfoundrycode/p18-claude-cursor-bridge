# SCOPE — FIX-001 (every program the test suite starts is windowless)

No builder increment, no brief: supervisor-written test infrastructure (N4 permits tests), on the owner's agreement to the plan after the crash of 2026-10-19 (ISS-011). PR #48.

## Scope

- `tests/conftest.py` — on Windows only, `subprocess.Popen.__init__` is wrapped once (a marker attribute keeps a re-import from wrapping twice). A launch that sets no creation flags (absent or 0) gets `CREATE_NO_WINDOW`, plus `stdin=subprocess.DEVNULL` when it redirects none of stdin, stdout and stderr; a launch that sets its own flags is left alone. The rest of the file is unchanged.
- `tests/test_tests_windowless.py` — new, ten tests (below).
- Records: `docs/INVENTORY.md` (one Decisions row: the default, and why `windowless-check.py` is not run over `tests/`); `docs/HARDENING.md` (Stage B3, "FIX-001": why now, the fix, Review A's round, leads); `docs/PROJECT_STATUS.md` (written as it reads at this pull request's merge, the ISS-009 convention: Last accepted names PR #48 first, In flight none, Next the step after the merge; ISS-011 open).

## Why

The owner's computer crashed at 17:59 UTC on 2026-10-19 after a flood of terminal windows, while a headless builder (cursor-agent, a process with no console) ran this suite. 32 of the 34 test files that start programs passed no window flag, so each launch could get a visible console window (KP-014, rule 24). The cause is not proven; the owner's process-start recording will show it at the next builder run. The builder's own process tree outside pytest is not covered (a recorded lead).

## Tests the supervisor wrote, and what each enforces

All enforce supervisor.md standing rule 24 (windowless by default) and Known-Pitfalls KP-014, for the suite itself.

1. `test_fix001_a_launch_without_flags_gets_no_window_flags` — absent or zero flags get CREATE_NO_WINDOW and stdin=DEVNULL.
2. `test_fix001_a_launch_that_redirects_a_stream_keeps_its_streams` — no stdin is added when any stream is redirected.
3. `test_fix001_a_launch_with_its_own_flags_keeps_them`.
4. `test_fix001_the_wrapper_is_installed_on_windows_only` — on Linux CI the wrapper is absent.
5. `test_fix001_a_child_started_without_flags_has_no_console_window` (Windows) — GetConsoleWindow() is 0 and the test's own process is not on the child's console (an inherited console would hold it).
6. `test_fix001_a_grandchild_inherits_the_windowless_console` (Windows) — the child's own flagless child shares that console: window 0, the child on it, the test's process not.
7. `test_fix001_a_child_that_redirects_nothing_writes_to_the_suite_and_reads_end_of_input` (Windows, capfd) — the child's stdout and stderr reach the suite's streams and its stdin read returns at once with ''.
8. `test_fix001_the_rule_flags_each_way_around_the_default` — the per-line rule `bypasses_the_default` flags twelve known ways around the default (os.system, os.startfile, os.spawn*, os.exec*, `from os import system`, multiprocessing, ProcessPoolExecutor, CreateProcess, flags without CREATE_NO_WINDOW by keyword, with spaces, by a `**{...}` key, with a comment naming CREATE_NO_WINDOW) and none of three launches through it.
9. `test_fix001_the_scan_reports_a_launch_around_the_default` — `scan(folder)` over a temporary folder reports exactly the bypass planted in a subfolder, skips a conftest.py, and counts the one flags line.
10. `test_fix001_no_test_starts_a_program_around_the_default` — `scan(tests/)` finds nothing, and must have read test_bridge_run.py, test_workflows_line_check.py and helpers/sleep_tree.py and seen a flags line. It guards the INVENTORY decision not to run windowless-check.py over tests/.

Mutation driver (the supervisor's, on a scratch copy of tests/, restore byte-checked): nine mutants of the detector (the bypass regex emptied, the flags rule replaced by False, the walk over nothing, the rule's call replaced by False, conftest.py not skipped, no file recorded as read, comments not stripped, subfolders not walked, the flags regex keyword-only), each red.

Checked on copies: of the eight tests of the second commit, 6 fail against origin/main's conftest.py (1 to 6), 2 against the first version of the fix, 9dcbd6d (1, and 7 by timeout); all pass with the fix, also when run from a virtual environment's launcher python.exe (the first version's exact process counts failed there) and under a parent with no console (Review A).

## How the review rounds so far were settled

- secret-sentinel on 9dcbd6d: CLEAR.
- Review A on 9dcbd6d: APPROVE 0/3/7. Should-fix: (1) the counts "0 1"/"0 2" fail under a venv launcher, now checked by process ids; (2) a launch redirecting no stream lost its output to the hidden console and a stdin read would wait there, now stdin=DEVNULL (test 7); (3) the INVENTORY row overstated "every program" and its revisit trigger had no detector, now reworded and test 8. Its mutants (on a scratch copy) were all killed but "install on every platform", which only test 4 on CI's Linux leg kills.
- The full suite on 9dcbd6d: 1625 passed, 25 skipped, 302 s (the four runs of the day before the fix: 293 to 320 s).
- secret-sentinel on e48a456: CLEAR. The full suite on e48a456 (the conftest as it merges): 1628 passed, 25 skipped, 308 s.
- Review A on e48a456: REJECT 1/0/5. Blocking: the detector test had no positive control (its regex emptied, its flags rule dropped or its loop emptied, it still passed): fixed in 37671de (tests 8 and 10). Notes taken: the status line's wording, HARDENING's count, the line-not-syntax-tree limit as a lead.
- Review A on 37671de: APPROVE 0/1/3. Should-fix: a finding inside a scanned file was never shown to reach the result (`if False:` survived): fixed in 38d5c1a (test 9). Notes recorded as HARDENING leads (a `#` inside a string literal; a fixture holding a bypass as data).
- Review A reads 38d5c1a's delta while this review runs.

## Out of scope

Any program under `bridge/`, the CI workflow, `.githooks/`, the builder's own process tree. Design for later increments (CONFIG-B3b, the command reference) is not this diff's defect.

## Expected files in the diff

The five files above and `run/review/` (these review files, removed before the merge).
