# SCOPE - FIX-005: stage P1's least-confident item 1 settled by a test (pull request #165)

A supervisor-written test and its records, no builder run: the program release's stage P1 closed on 2026-11-14 with three least-confident items (docs/HARDENING.md, "Least confident (stage P1's close, 2026-11-14)"); item 1, that a stripped launch withholds a secret-like name end to end, is one a test can settle, so it becomes a test before stage P2's first delegation (~/.claude/cursor-bridge/workflow/phases/reflection.md, item 2b). Precedents: FIX-002 (#50) and FIX-004 (#65). Branch fix-005 from origin/main at the merge of PR #164 (3d7010d). Four files: tests/test_program_strip_end_to_end.py (new), docs/HARDENING.md, docs/REQUIREMENTS.md, docs/PROJECT_STATUS.md. No program and no shipped bridge text changes.

## What the test must do
- Launch `bridge/cursor-bridge/bridge-run.py --limit 30 --strip --kind test` from a scratch Workspace with names set in the launching environment that `bridge_env.SECRET_LIKE` alone withholds, none of them a name D-004's note "Stripped environment" lists by name or `bridge_env.TOKEN_VARS` names, and assert that the child's environment lacks every one of them.
- Hold that precondition in a test of its own, so that the cases are known to reach the pattern's path through the launcher and not the list's (since TASK-055, tests/test_release_t_strip.py no longer reads secret-like names in its own run, and tests/test_bridge_run.py's `test_r055_d004_a_stripped_run_gets_the_notes_names` launches with the listed names only).
- Do the same beside a key file naming another variable (`--key-file`, the route the loop allows a suite; the launcher adds its names after the strip, bridge-run.py:1895-1906): the key file's name reaches the child, the made-up ones do not.
- Show each case can fail: the same launch without `--strip` hands the child every made-up name; and each name alone.
- Print no value: a value never appears on the launcher's output or the child's.

## Tests
This pull request adds one test file and changes no other; the anti-gaming checks apply. The test file names R-052 (the loop's suite and driver launches carry `--strip`; its Evidence cell now names the file). It enforces docs/REQUIREMENTS.md R-052, docs/diagrams/D-004-context-dfd.md's note "Stripped environment" and docs/HARDENING.md's item. Its eight tests passed in a stripped launcher run. It passes on main by construction, since it pins behaviour already built; no run against the checkpoint was made. The mutants are the evidence that it can fail: run/supervisor/FIX-005-mutants.json (gitignored, the supervisor's), six mutants, `mutation-run.py` through the launcher's driver kind, stripped, on the revised test: 6 of 6 killed. m1 the strip not applied to a test launch (bridge-run.py:1895, `if (is_agent or strip)` to `if is_agent`); m2 the key file bringing the launching environment back (bridge-run.py:1905, `env.update(keys)` to `env.update(dict(os.environ, **keys))`); m3 the pattern's path gone with the list kept (bridge_env.py:52, `secret_like` returns False); m4 the pattern losing PASSWORD (bridge_env.py:46); m5 the pattern losing a name ending in `_KEY` (bridge_env.py:46); m6 the key file's line printing its values (bridge-run.py:1906). The mutants file is reproduced here, since it is not tracked:

- m1 expect_fail: the no-key-file case, the key-file case, the five each-name cases.
- m2 expect_fail: the key-file case.
- m3 expect_fail: all eight.
- m4 expect_fail: the precondition, the no-key-file case, the key-file case, the PASSWORD case.
- m5 expect_fail: the precondition, the no-key-file case, the key-file case, the `_KEY` case.
- m6 expect_fail: the key-file case.

## What the records must do
- docs/HARDENING.md: stage P1's least-confident item 1 marked settled by FIX-005, with the test, its mutants and why no checkpoint run was made.
- docs/REQUIREMENTS.md: R-052's Evidence cell gains the test; the row stays built and its sentence is unchanged.
- docs/PROJECT_STATUS.md as it will read at this pull request's merge (ISS-009): In flight none, Awaiting user on nothing, Next stage P2 from TASK-059, the change cycle's step naming this pull request, Remote sync naming PR #165.

## What to check
- The test does what it says against bridge/cursor-bridge/bridge-run.py and bridge/cursor-bridge/bridge_env.py as they stand; it can fail (the controls and the mutants); it reaches no network, writes nothing under the real profile (LOCALAPPDATA in tmp_path, the suite's own home fixture), and prints no value.
- `~/.claude/cursor-bridge/completion-check.py --mode plan` (RESULT: OK, 78 built, 2 deferred, 25 planned), `~/.claude/cursor-bridge/inventory-check.py` (RESULT: OK, status 37 lines, 11408 characters), `~/.claude/cursor-bridge/plan-check.py` (RESULT: OK, READY naming TASK-059 first).
- No computer path, user name or e-mail address in a changed line.

## The threat model
docs/INVENTORY.md's Decisions record the bridge's threat model as a whole and D-004's stated limits on what stays in a session's own environment: the strip is instructed, reaches only what goes through the launcher, and withholds the owner's login and every secret-like name from code a builder wrote. This pull request adds no code and holds that limit by a test. The five blocking classes stand.

## Before this round
- Records tests and the strip's tests on the first commit's records: forty-two files, 2558 passed and 27 skipped, stripped; tests/test_release_b_bootstrap.py alone with the pull-request variables for PR #165, 15 passed.
- Review A (diff-reviewer, claude-opus-5-5) on 2958b52: APPROVE, no Blocking, one Should fix, three Consider, all taken in the commit after it. Should fix: the key file's value, the one value the launcher reads and reports on by name, was never checked absent from the output (now checked in the key-file case, and mutant m6 shows the check can fail). Consider: HARDENING called m3 the gap the item named, where the item names a name set after the strip, m1's and m2's class (reworded; m3 is held by the pin over `stripped_env` too); the five each-name cases had no control of their own (each now runs once without `--strip`); R-052's Evidence entry stood after T19 with a label of its own (moved into the T9 group). On the revised test: the own-file run, stripped, 8 passed; the mutation run, 6 of 6 killed. Review A ran the test file itself (8 passed) and the completion and inventory checks (both OK).

This is Review B's round 1 for FIX-005, below the ceiling.
