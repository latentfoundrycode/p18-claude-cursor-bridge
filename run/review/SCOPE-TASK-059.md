# SCOPE: TASK-059 (R-078), the launcher's command forms

Branch `task-059`, base `origin/main` at 16e7e89 (the squash of #165). The diff is `run/review/REVIEW-TASK-059-r2.diff`, taken from committed state (`git diff origin/main...HEAD`, the review files excluded). The briefs are `handoff/TASK-059.md` and `handoff/TASK-059-r2.md` to `handoff/TASK-059-r7.md`, each round's Scope and Out of scope standing for that round; the builder's reports beside them. This is the guard's round 2 for TASK-059: its round 1 was the Review B vote of the resolution round on round 6 (`handoff/RESOLUTION-TASK-059.md`).

## How the increment got here (seven builder rounds)

- Rounds 1 to 5: the interpreter's flags (C6), the package runners' folder options (F5), the two exit-125 messages (J4), `merge_ids` sorted (J9), the plan globs escaped (J12). Each of rounds 2 to 5 was sent back for a spelling of a folder value that the rule read as one folder and npm as another (abbreviations and clusters, a flag's `=` value, the runner's environment names, a leading `~`, a trimmed space, `${NAME}`, a trailing dot Windows drops), the design changing each time: an option list, the environment prefixes refused, a character list for the folder value, and from round 6 the runner handed the folder the rule checked. Rounds 4 to 6 were lifted above the ceiling by class lines (security), each confirmed by Review A and the security audit against its brief's commit.
- Round 6 caused R1 (a launch folder with a space under a spaced npm.cmd never ran; one holding a cmd.exe character was refused). A class line never lifts a round for a regression the previous fix caused, so it went to a resolution round: both reviewers voted A, the checked folder handed relative to the launch folder, beginning with `.`, refused where `relpath` raises (`docs/CHANGES.md`).
- **Round 7 is lifted by the owner's line**, `Review rounds above the ceiling: TASK-059 7 (Do round 7., 2026-11-14)` in `docs/RUN_PARAMETERS.md`, on the owner's words in the chat. There is no class line for round 7 to confirm.

## Scope (what this pull request is to do)

`bridge/cursor-bridge/bridge-run.py` and `bridge_env.py` as the briefs state (Requirements 1 to 24 of round 7's brief, Requirement 19 as amended there); `MANIFEST.json` and the command reference regenerated; the supervisor's acceptance tests (`tests/test_program_launcher_forms.py`, `tests/test_header_run_parameters.py`'s fallback test, `tests/test_release_s_launcher.py`'s windowless fix) and the builder's cases (`tests/test_bridge_run.py`, `tests/test_bridge_run_driver.py`, `tests/test_release_s_launcher.py`).

## Out of scope (not this diff's defect)

- HARDENING's leads under TASK-059, 1 to 17: among them resolve's cmd.exe quoting of a spaced argument the agent writes (1), lead 3's traceback for `\\.\GLOBALROOT`, a launch folder on a UNC path (10), the link walk trimming a middle trailing dot (13), case-sensitive folders (14), `main`'s refusal untested through `main` (15), pnpm and yarn read, not run (16), the mutation run's id normalisation (17).
- The register's R-078 stays `planned`: TASK-082 also satisfies it.

## Threat model

`docs/INVENTORY.md`, Decisions, the row "The launcher's target rule's threat model", as this diff revises it. Untrusted input: the command line an agent writes under the allow rule, the environment it runs in, and files a builder or reviewer can plant in the launch folder (junctions, folders named like options). For the five blocking classes a security finding is judged by whether that input reaches it.

## What Review A and the security audit found on round 7

Review A APPROVE, the security audit PASS, nothing blocking. Both ran the real npm.cmd under `C:\Program Files\nodejs` from launch folders holding a space, `(`, `)`, `&`, `^`, `%` and `!` (R1 gone in every form), against junctions `...`, `a..`, `....` planted through the `\\?\` prefix (never run), and compared rounds 5, 6 and 7 form by form (nothing that ran at round 5 fails now). Their advisories are HARDENING's leads 13 to 16. Review A re-read the supervisor's fix and the records: APPROVE, its should-fix taken (the row's "through no link" qualified by lead 13).

## Tests and counts

- The targeted run on round 7: 572 passed. The acceptance file alone: 69 passed.
- The mutation run: 26 mutants, 24 killed, 2 expected to survive (m6, m26, reasons in HARDENING).
- The whole suite on round 7 with the records: 1 failed, 5187 passed, 42 skipped; the one failure (`test_tests_windowless.py`, a launch whose flags the scan could not read) fixed by the supervisor, the two files 52 passed. On this head the whole suite is CI's run of the pull request.

## Expected bookkeeping and records in the diff

`docs/CHANGES.md` (new: the resolution round's decision), `docs/INVENTORY.md` (the row, Reflected through), `docs/HARDENING.md` (TASK-059's entries), `docs/RUN_PARAMETERS.md` (the owner's line), `docs/PROJECT_STATUS.md` (as at this pull request's merge), `handoff/` (the briefs, the reports, the resolution material), `run/review/` (this file and the diff, removed before the merge).
