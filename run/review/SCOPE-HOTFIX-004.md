# SCOPE: HOTFIX-004 (hotfix 2026.11.24a, the heavy slots)

The branch `hotfix-004`, based on `release/2026.11.23a`: four builder rounds (briefs `handoff/HOTFIX-004.md`, `handoff/HOTFIX-004-r2.md`, `handoff/HOTFIX-004-r3.md`, `handoff/HOTFIX-004-r4.md`), the supervisor's acceptance tests, the release stamp, and one supervisor fix after CI. The diff under review is `run/review/REVIEW-HOTFIX-004-r3.diff` (merge base 669d3b4 to HEAD).

Review B's first round rejected the branch for two defects in `create_pid_file_exclusive`; round 4 (requirements 37 and 38) fixed them, and Review B's second round approved the branch. CI on pull request 207 then failed 5 tests (7444 passed): the stamp had left `project.json`'s `version` and `state.bridge` and `docs/PROJECT_STATUS.md`'s header `bridge_version` and `Bridge version:` line at 2026.11.23a (three stamp tests and the bridge's own conformance test want them equal to `bridge/cursor-bridge/VERSION`, as the program release's stamp wrote them); and two `creationflags` lines of the acceptance file named the flag through a variable, which `tests/test_tests_windowless.py` cannot read as `CREATE_NO_WINDOW`. The last commit, `HOTFIX-004: CI's findings on pull request 207`, changes exactly those four values and those two lines. What changed since your second round is that commit alone.

## The brief's Scope (round 1, quoted)

Files you may create or modify, each only as the paragraph after the list allows:
- bridge/cursor-bridge/bridge-run.py
- bridge/cursor-bridge/mutation-run.py
- tests/test_hotfix24a_heavy_slots.py
- docs/cli-reference.json
- docs/CLI_REFERENCE.md
- docs/BUILDER_NOTES.md
- handoff/HOTFIX-004-r1-report.md

What each entry allows, exactly: `bridge-run.py` and `mutation-run.py` are the two programs you change. `tests/test_hotfix24a_heavy_slots.py` is listed so the scope check reads it; it is the supervisor's acceptance test: read it and run it, never edit it. `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` change only by running `python tools/dump-cli.py` (checked with `python tools/dump-cli.py --check`); never edit them by hand. `docs/BUILDER_NOTES.md` takes one or more dated lines appended at its end, nothing else in it changes. `handoff/HOTFIX-004-r1-report.md` is your report, a new file. Do not modify anything else.

Rounds 2 and 3 carry the same Scope with their own report files; round 4's Scope is `bridge-run.py`, the acceptance file (read only), `docs/BUILDER_NOTES.md` and `handoff/HOTFIX-004-r4-report.md`.

## The brief's Out of scope (round 1, quoted)

- `.env` and anything under `secrets/`.
- CI configuration (`.github/`).
- `docs/` and `handoff/`, except the files the Scope section names.
- `bridge/cursor-bridge/MANIFEST.json`, `bridge/cursor-bridge/VERSION` and `bridge/cursor-bridge/CHANGELOG.md`: the supervisor stamps 2026.11.24a after your run. Do not run `tools/make-manifest.py`.
- Every other file under `bridge/`: `bridge_env.py`, `bridge-stop.py`, `bridge-install.py`, `loop-guard.py`, `Glossary.md`, `supervisor.md`, the loop's texts (`delegation-loop.md`, `run-parameters.md`) and every other program stay exactly as they are. The design's section "The loop's text" decides that the sentences that say one slot stay in this hotfix; the supervisor's change log names them.
- Every other test file, `tests/conftest.py` included. A failure in another test file is reported by its test id, never fixed in that file.
- `tools/`, all of it (you only run `tools/dump-cli.py`).
- `run/`, which holds the supervisor's records (read `run/supervisor/hotfix-004-design.md`, write nothing there), and `.git/`.
- Never run `bridge-run.py`, `mutation-run.py` or `bridge-install.py` against the real home folder (`~/.cursor-bridge`, `~/.claude`), this repository's real run record (`run/launcher/`), or the real `cursor-agent`. The tests below run them only under pytest's temporary folders with a temporary home.

Round 2 adds to Out of scope: the folder-to-slot waiting line stays as round 1 built it. Rounds 3 and 4 add: the earlier rounds' non-blocking findings (recorded in `docs/HARDENING.md`, the hotfix's section) and `write_pid_file` (the rewrite at the child's start).

## The threat model

`docs/INVENTORY.md`'s Decisions record no row for the heavy slots; the rows that cover what this diff changes are the launcher's target rule (R-073, R-078) and the bridge's threat model as a whole (R-050): outside input is what the builder and the reviewers write and the records of a project. For this hotfix the supervisor's working model, given to both auditors: files under `~/.cursor-bridge` (the setting `heavy-slots.json`, the lock files `heavy.lock`, `heavy-<k>.lock`, `heavy-folder-<sha256>.lock` and their holder files), the pid files under `run/launcher/pids/` (read by `bridge-stop.py`), and the mutation engine's scratch base (`.mutation-run-<run id>.lock`, `mutation-run-<run id>/`), on a single-user Windows or POSIX computer, where another process of the same user, a builder, or a planted link or hard link could redirect a write or a lock, or make one run delete another's files.

## The tests and what each enforces

- `tests/test_hotfix24a_heavy_slots.py`, round 1's 31 cases: the setting (absent: one slot; every malformed form, 12 parameters, gives one slot and the note line), `--heavy-slots` (writes atomically; out of range and not alone refused, 125), the slots (two slots, a second launch at once, a third waits on both; the waiting and not-free lines; the earliest end named), one heavy run per checkout (same folder and subfolder wait on the folder lock; the holder record; the not-free line names the folder holder), run ids (same-second launches get distinct ids), the run row's `slot`, lock errors refuse, and the mutation engine's per-run-id lock (test 10).
- Round 2's 11 cases (`test_hotfix24a_r2_*`): the identity follows the builder's `--workspace` and is read from the command, never the launcher's options (requirement 26); an early refusal leaves no pid file (cap, watch-only, key-file; 27); `--heavy-slots` after `--` belongs to the command (28); a hard-linked heavy.lock, heavy-2.lock or folder lock, and a hard-linked mutation lock, are refused (29); a failed setting write leaves no temporary file (30).
- Round 3's 2 cases (`test_hotfix24a_r3_*`): a refused mutation run leaves the live run's scratch folder (35); on POSIX a hard-linked lock file keeps its mode (36; skipped on Windows, runs on the POSIX CI).
- Round 4's 4 cases (`test_hotfix24a_r4_*`): an unusable pids folder refuses the launch with 125 before its started line (38); the reservation answers None only without `run/`, False only for a taken name, and raises otherwise (37); a permission error on the pid file's open raises (37); a failed write leaves no pid file (37).
- `tests/test_bridge_run_slot.py` line 866, the supervisor's one edit of an existing test: `test_r040_wait_timeout_exit_123_and_log` expects `"slot": 1` on the successful one-slot row (the design's run row). The regression batch (12 files) otherwise unedited.
- The records the CI fix touches are read by `tests/test_program_stamp.py`, `tests/test_release_b2_stamp.py`, `tests/test_release_t_stamp.py` (project.json against VERSION), `tests/test_calibrate_program.py::test_r027_r033_bridge_own_status_file` (the status file against VERSION) and `tests/test_tests_windowless.py` (the two lines).
- The supervisor's runs: on round 4, 714 passed, 6 skipped across the acceptance file and the regression batch; after the CI fix, the five failing files, the records tests and the acceptance file, 375 passed, 2 skipped. CI's suite on the head before the fix: 5 failed, 7444 passed, 69 skipped (ubuntu-latest).
- The mutants file `run/supervisor/HOTFIX-004-mutants.json` (34 mutants, made by `run/supervisor/hotfix004_mutants_make.py`): 34 killed, 0 survived, 0 errors. Both are gitignored supervisor files, present in the checkout.

## Expected bookkeeping and record files in the diff

- `docs/BUILDER_NOTES.md` (round 1's dated lines), the builders' reports `handoff/HOTFIX-004-r1-report.md` to `-r4-report.md`, the briefs `handoff/HOTFIX-004.md`, `-r2.md`, `-r3.md`, `-r4.md`.
- The release stamp: `bridge/cursor-bridge/VERSION` (2026.11.24a), `MANIFEST.json` (from `tools/make-manifest.py`, 148 files), `CHANGELOG.md` (the 2026.11.24a entry), `docs/HARDENING.md` (the hotfix's section), `project.json` (`version`, `state.bridge`, `updated`), `docs/PROJECT_STATUS.md` (`bridge_version`, `Bridge version:`).
- `docs/cli-reference.json` and `docs/CLI_REFERENCE.md`, regenerated by `tools/dump-cli.py`.
- `run/review/` (this file, the diff, the assumptions file), removed before the merge.
