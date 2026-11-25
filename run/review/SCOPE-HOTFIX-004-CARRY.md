# SCOPE: HOTFIX-004-CARRY (hotfix 2026.11.24a carried onto main)

## What this branch is
Hotfix 2026.11.24a (HOTFIX-004, the machine-wide heavy slots as a setting, R-137) was built on the branch release/2026.11.23a (cut from main at 669d3b4), approved there through the full gate (Review A, the security audit, Review B rounds 1 to 3, CI green on both platforms, 34 of 34 mutants killed) and merged as PR #207 (squash 3ffd91a); the owner installed it on 2026-11-25. This branch carries it onto main, which has moved since 669d3b4: TASK-085 changed bridge/cursor-bridge/mutation-run.py (the mutation engine on an editable install) and TASK-086a changed roster-check.py.

## How the carry was made
- `git diff 669d3b4 3ffd91a` applied onto origin/main with `git apply --3way`, leaving out MANIFEST.json, project.json, docs/PROJECT_STATUS.md, docs/CLI_REFERENCE.md and docs/cli-reference.json. bridge-run.py, the CHANGELOG entry, VERSION, the eight HOTFIX-004 briefs and reports, the acceptance file and tests/test_bridge_run_slot.py are byte-identical to the release squash; mutation-run.py carries the hotfix's hunks over TASK-085's code. docs/BUILDER_NOTES.md and docs/HARDENING.md conflicted only where both sides appended; both kept.
- Regenerated or written for main: MANIFEST.json (tools/make-manifest.py, 148 files, 2026.11.24a), the command reference (tools/dump-cli.py), project.json (version and state.bridge 2026.11.24a, main's stage), the status file (as at this pull request's merge, with the calibration of 2026-11-25).
- Records: docs/DESIGN.md "Change: hotfix 2026.11.24a" (C62), docs/REQUIREMENTS.md R-137, docs/INVENTORY.md (a feature row, two Decisions rows), docs/HARDENING.md (leads 11 to 13, the carry).
- One test-file change beyond the release: the acceptance file's module docstring names R-137 (completion-check's evidence rule); no test body changes.

## Commits
1. HOTFIX-004: hotfix 2026.11.24a carried onto main, the heavy slots
2. HOTFIX-004: the heavy slots' records on main (R-137)
3. HOTFIX-004: Review A's notes on the carry taken in the records
4. HOTFIX-004: the acceptance file names R-137

## Evidence so far
- Review A (diff-reviewer) on commits 1 and 2: APPROVE, no Blocking; one Should fix (R-137's wording on a malformed file and the pid-file refusal) and three Consider, taken in commit 3.
- Own-file run on the carry tree, stripped through the launcher (the acceptance file, the slot test, the five mutation-engine files, the driver test, the command reference, the windowless checks, four stamp files, the bootstrap and the intake hotfix's tests): "1 failed, 570 passed, 7 skipped in 1248.35s (0:20:48)", the failure completion-check's NO EVIDENCE for R-137, fixed by commit 4 (completion-check --mode done then lists only the release's planned rows R-107 to R-136, which the test allows while the phase is changing).
- Mutation run of run/supervisor/HOTFIX-004-mutants.json on the carry tree: "counts: run=34 cached=0 killed=34 survived=0 not applied=0 error=0 expected survive=0".
- The status and stamp files run alone with the pull request's variables (refs/pull/208/merge, base main; KP-074): tests/test_release_b_bootstrap.py, tests/test_release_t_stamp.py, tests/test_program_stamp.py, tests/test_calibrate_program.py: "50 passed in 4.54s".
- inventory-check RESULT: OK; completion-check --mode plan RESULT: OK (107 built, 30 planned); plan-check RESULT: OK (READY: TASK-086b); diagram-check --mode code RESULT: OK; bridge-check --sources 148 OK.

## Threat model
The hotfix's own, as approved on the release branch (docs/HARDENING.md, "Hotfix 2026.11.24a"; the CHANGELOG's Known limits). The carry adds no behaviour.

## What the review asks
Is the carry faithful (every hotfix hunk present, nothing else changed in the code, TASK-085's behaviour intact in mutation-run.py, the lock taken before anything is removed or written), and do the records agree with the code and the CHANGELOG?
