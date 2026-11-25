# SCOPE: HOTFIX-004 (hotfix 2026.11.24a, the heavy slots)

The branch `hotfix-004`, based on `release/2026.11.23a`: three builder rounds (briefs `handoff/HOTFIX-004.md`, `handoff/HOTFIX-004-r2.md`, `handoff/HOTFIX-004-r3.md`), the supervisor's acceptance tests, and the release stamp. The diff under review is `run/review/REVIEW-HOTFIX-004-r1.diff` (merge base 669d3b4 to HEAD). The design is the owner-approved hotfix design summarised in the round-1 brief's Context and Requirements 1 to 25.

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

Rounds 2 and 3 carry the same Scope with their own report files (`handoff/HOTFIX-004-r2-report.md`, `handoff/HOTFIX-004-r3-report.md`).

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

Round 2 adds to Out of scope: the folder-to-slot waiting line stays as round 1 built it. Round 3 adds: round 2's non-blocking findings (recorded in `docs/HARDENING.md`, the hotfix's section).

## The threat model

`docs/INVENTORY.md`'s Decisions record no row for the heavy slots; the rows that cover what this diff changes are the launcher's target rule (R-073, R-078) and the bridge's threat model as a whole (R-050): outside input is what the builder and the reviewers write and the records of a project. For this hotfix the supervisor's working model, given to both auditors: files under `~/.cursor-bridge` (the setting `heavy-slots.json`, the lock files `heavy.lock`, `heavy-<k>.lock`, `heavy-folder-<sha256>.lock` and their holder files) and the mutation engine's scratch base (`.mutation-run-<run id>.lock`, `mutation-run-<run id>/`), on a single-user Windows or POSIX computer, where another process of the same user, a builder, or a planted link or hard link could redirect a write or a lock, or make one run delete another's files.

## The tests and what each enforces

- `tests/test_hotfix24a_heavy_slots.py`, round 1's 31 cases: the setting (absent: one slot; every malformed form, 12 parameters, gives one slot and the note line), `--heavy-slots` (writes atomically; out of range and not alone refused, 125), the slots (two slots, a second launch at once, a third waits on both; the waiting and not-free lines; the earliest end named), one heavy run per checkout (same folder and subfolder wait on the folder lock; the holder record; the not-free line names the folder holder), run ids (same-second launches get distinct ids), the run row's `slot`, lock errors refuse, and the mutation engine's per-run-id lock (test 10).
- Round 2's 11 cases (`test_hotfix24a_r2_*`): the identity follows the builder's `--workspace` and is read from the command, never the launcher's options (requirement 26); an early refusal leaves no pid file (cap, watch-only, key-file; 27); `--heavy-slots` after `--` belongs to the command (28); a hard-linked heavy.lock, heavy-2.lock or folder lock, and a hard-linked mutation lock, are refused (29); a failed setting write leaves no temporary file (30).
- Round 3's 2 cases (`test_hotfix24a_r3_*`): a refused mutation run leaves the live run's scratch folder (35); on POSIX a hard-linked lock file keeps its mode (36; skipped on Windows, runs on the POSIX CI).
- `tests/test_bridge_run_slot.py` line 866, the supervisor's one edit of an existing test: `test_r040_wait_timeout_exit_123_and_log` expects `"slot": 1` on the successful one-slot row (the design's run row). The regression batch (12 files: `test_bridge_run_slot.py`, `test_bridge_run.py`, `test_bridge_run_design_ceiling.py`, `test_bridge_run_review_ceiling.py`, `test_mutation_run.py`, `test_mutation_run_supervisor.py`, `test_loop_text_windowless.py`, `test_dump_cli.py`, `test_program_launcher_forms.py`, `test_release_t_strip.py`, `test_task032_supervisor_launcher.py`, `test_bug029_agent_name.py`) otherwise unedited.
- The supervisor's run on round 3: 712 passed, 6 skipped (POSIX-only or symlink privilege), 0 failed across the acceptance file and the regression batch.
- The mutants file `run/supervisor/HOTFIX-004-mutants.json` (31 mutants, made by `run/supervisor/hotfix004_mutants_make.py`): 31 killed, 0 survived, 0 errors. Both are gitignored supervisor files, present in the checkout.

## Expected bookkeeping and record files in the diff

- `docs/BUILDER_NOTES.md` (round 1's dated lines), the builders' reports `handoff/HOTFIX-004-r1-report.md`, `-r2-report.md`, `-r3-report.md`, the briefs `handoff/HOTFIX-004.md`, `-r2.md`, `-r3.md`.
- The release stamp: `bridge/cursor-bridge/VERSION` (2026.11.24a), `MANIFEST.json` (from `tools/make-manifest.py`, 148 files), `CHANGELOG.md` (the 2026.11.24a entry), `docs/HARDENING.md` (the hotfix's section).
- `docs/cli-reference.json` and `docs/CLI_REFERENCE.md`, regenerated by `tools/dump-cli.py`.
- `run/review/` (this file, the diff, the assumptions file), removed before the merge.
