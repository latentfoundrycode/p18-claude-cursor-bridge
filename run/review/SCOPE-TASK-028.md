# SCOPE - TASK-028

TASK-028, the builder's increment for R-039's bridge half: windowless launches enforced by the launcher (its driver kind) and the suite's frozen default (docs/BUILD_PLAN.md, "### TASK-028"). Briefs: handoff/TASK-028.md (round 1), handoff/TASK-028-r2.md (round 2), handoff/TASK-028-r3.md (round 3) handoff/TASK-028-r4.md (round 4, a narrow fix past the owner's three-round review ceiling: uv_run_pytest's last line restored, and a testpaths entry holding `..` dropped) and handoff/TASK-028-r5.md (round 5, the floor's input handling closed: a NUL entry dropped, an unlistable tests/ seen as no suite, the OK row's path escaped, and a backstop turning any exception in the floor into one NOTE). Each later brief corrects the earlier ones in place; where they differ, the later governs. The builder is composer-2.5 in every round. The loop's text and the calibration's write of the default are TASK-030's, the machine-wide slot TASK-029's, mutation-run.py TASK-031's: design for those is not this diff's defect.

This review reads the whole increment past the ceiling: only the five blocking classes send the work back (behaviour against the brief or the register, security, data integrity, a defeated safety mechanism, a failing test); every other finding is recorded in docs/HARDENING.md, Stage B5, "TASK-028", where the findings of rounds 1 to 4 not taken already stand, with the supervisor's by-class line on the floor's input handling (a further such finding that fails closed is recorded there).

## The round-3 brief's Scope (quoted; round 4's is a subset of it)

One brief carries one increment's scope; work that needs a second scope is a second brief, never a second section here.

Files and directories you may create or modify:
- bridge/cursor-bridge/bridge-run.py
- bridge/cursor-bridge/conformance-check.py
- bridge/cursor-bridge/windowless-default.snapshot.md
- bridge/cursor-bridge/settings.bridge.json
- bridge/cursor-bridge/MANIFEST.json (regenerated only, by the command in Constraints)
- tests/conftest.py
- tests/test_bridge_run_driver.py
- tests/test_conformance_windowless.py
- tests/test_allowlist.py
- docs/cli-reference.json
- docs/CLI_REFERENCE.md
- docs/BUILDER_NOTES.md
- handoff/TASK-028-r3-report.md

Do not modify anything else.

## The round-3 brief's Out of scope (quoted)

- .env and anything under secrets/
- CI configuration (`.github/`, `.githooks/`)
- docs/ and handoff/, except the files the Scope section names. That includes `handoff/TASK-028.md`, `handoff/TASK-028-r2.md`, the round-1 and round-2 reports, this brief and the four review files under `run/supervisor/`: read them, do not edit them.
- `bridge/cursor-bridge/bridge_env.py`. Do not edit it. `bridge_env.is_link` returns `False` when `os.lstat` raises; the fail-closed handling this round asks for lives in `bridge-run.py` and `conformance-check.py`, never in `bridge_env.py`.
- `bridge/cursor-bridge/workflow-check.py`. Do not edit it; requirement 9(f) only reuses its `escape_field`.
- `bridge/cursor-bridge/mutation-run.py`: it is TASK-031's. Do not create it, not even as a stub. The launcher accepts its path whether or not the file exists.
- `bridge/cursor-bridge/loop-guard.py` and its `KIND_CEILING` (TASK-029), the machine-wide slot (TASK-029), and every text file of the loop: `delegation-loop.md`, `supervisor.md`, `calibrate-bridge.md`, `Cursor-Project-Configuration.md`, `Known-Pitfalls.md` and the agents (TASK-030).
- `calibration_workflows_grades`, `judge_workflows_line` and the `Workflows line` / `Workflows classification` / `Unwritten trait` floors in `conformance-check.py` (TASK-024). Leave them byte-for-byte unchanged. Leave every other floor of `conformance-check.py` unchanged too.
- `project.json` and the conformance check's `project.json` NOTEs.
- `tests/test_tests_windowless.py`: do not edit it. It must stay green.
- Any other test file, including the existing conformance and bridge-run tests. They must keep passing unchanged.
- **Findings not taken.** The supervisor records these in `docs/HARDENING.md`. Do not fix them, and do not write tests for them:
  - the window between the re-check, `subprocess.Popen` and the interpreter opening the script (the audit's advisory 8);
  - `tox.ini` precedence: pytest would read a `tox.ini` `[pytest]` section; the floor keeps never reading `tox.ini`;
  - the leading-option refusal of requirement 1(b) being redundant now: keep it exactly as it is;
  - `RecursionError` at the `project.json` read (`conformance-check.py:894-895`) and the settings-JSON read (`:976-977`): those floors stay unchanged;
  - the interpreter-name canonicalisation: `head_of` strips `.exe`/`.cmd` anywhere in the name, and `resolve` may run a `.cmd` through `cmd.exe`;
  - the allow rule also matching a command with a second `--`;
  - a `.venv` interpreter reached through a link;
  - the ambiguity of exit 1 meaning a healthy driver run (TASK-031's contract; exits 0 and 1 stay healthy).
- The round-1 test `test_r039_tools_ignore_snapshot_md` stays as it is.

## Tests the supervisor wrote

- tests/test_bridge_run_driver.py:
  - test_r039_recheck_refuses_tampered_program (round 2): enforces handoff/TASK-028-r2.md, Requirements 1(g) and the criterion "The re-check". The checked program becomes a folder inside a patched branch_of; Job and subprocess.Popen are fakes.
  - test_r039_uv_run_without_pytest_still_refused (round 4, six cases): enforces requirement 2, "every other kind keeps its current acceptance exactly". Red on 57672d4 (NameError).
  - The exact-line assertions in test_r039_healthy_refused_for_driver_exit_3 and test_r039_limit_auto_driver_empty_log (round 4): enforce round 3's criterion "Exact lines".
- tests/test_conformance_windowless.py:
  - test_r039_testpaths_dotdot_component_dropped: enforces round 4's 9(b) rule. Red on 57672d4.
  - test_r039_testpaths_link_then_dotdot_posix: the same rule, Linux only.
  - test_r039_linked_testpaths_entry_falls_back_to_tests: enforces round 3's 9(b) fallback to tests/.
  - test_r039_nul_in_testpaths_dropped, test_r039_unlistable_tests_folder_is_no_suite, test_r039_ok_row_path_is_escaped and test_r039_floor_backstop_turns_an_error_into_one_note (round 5): enforce round 5's Requirements 1 to 4 (round 3's 9(c), no traceback; requirement 9, no control character). Red on 4dedcfd.
  - test_r039_dotdot_entry_spellings_dropped (round 5): round 4's rule for `\` and an absolute entry.
  - After round 5's reviews (Review A's three test gaps): the backstop test's stderr assertion; test_r039_floor_backstop_drops_the_rows_made_before_the_error (round 5's requirement 4, no partial row: a parse NOTE exists before the failure and is not printed); test_r039_ok_row_path_without_escape_field (requirement 3's fallback when escape_field cannot be loaded). Each kills the mutant Review A named (the message on stderr, the partial rows kept, the raw path in the fallback; run/supervisor/task028_r5_mutants.py, restored byte for byte).
- Round 5's reviews (Review A APPROVE, the security audit PASS) both name one behaviour: the backstop's NOTE takes the place of a row that would have been MISSING, so a crashed floor does not count toward exit 1. The supervisor graded it outside the five classes (no project input reaches the backstop; the NOTE is never an OK; the brief chose the exit) and recorded it in docs/HARDENING.md, TASK-028, with its check. Judge that grading too.
- Every other test in the two new files is the builder's. Each round's new tests were run once against the round before:
  - round 1, against 309ed382: 57 failed;
  - round 2, against 15df87a7: 29 of 94 failed;
  - round 3, against 76569e00: 14 of 111 failed;
  - in every case, each failure was a behaviour that round added.
- Done when (f), the supervisor's half (outside the diff): from pythonw.exe a console program started without flags reported window handle 199054; the same program through the repository's launcher, started detached with --kind driver, reported 0 (recorded under ISS-011 in Documents/).

## Expected bookkeeping and record files

- handoff/TASK-028.md, -r2.md to -r5.md (the briefs); handoff/TASK-028-r1-report.md to -r5-report.md (the builder's reports).
- docs/HARDENING.md: Stage B5, "TASK-028", the findings of rounds 1 to 5 not taken, and the by-class line.
- docs/INVENTORY.md: Decisions, the backstop's accepted assumption (it catches Exception only).
- docs/REQUIREMENTS.md: R-039's evidence (stays planned until TASK-030).
- docs/INVENTORY.md: the Features row "Windowless launches enforced by the bridge".
- docs/PROJECT_STATUS.md: as at this pull request's merge, PR #88 (ISS-009); its Last accepted's older entries moved to docs/archive/STATUS_HISTORY.md.
- bridge/cursor-bridge/MANIFEST.json restamped; docs/cli-reference.json and docs/CLI_REFERENCE.md regenerated.
- run/review/: these review files.

## Evidence

- After round 5's reviews (4cf3134, the supervisor's tests and records): the two test files 130 passed, 2 skipped; full suite 2375 passed, 35 skipped; invisible-check OK; secret-sentinel CLEAR. Round 5: scope-check SCOPE CLEAN against f128c08a; the two test files 128 passed, 2 skipped; full suite 2373 passed, 35 skipped. Round 4: scope-check SCOPE CLEAN against 54dd9927; the two test files 118 passed, 2 skipped (the Linux-only test and the file-symlink test, which needs a privilege here); full suite 2363 passed, 35 skipped; dump-cli --check clean; the repository's bridge-check 141 OK; invisible-check OK.
