# SCOPE — CONFIG-B3b (the generated command reference and its CI check)

A builder increment (composer-2.5), four rounds; the last calibration item of release B's stage B3 (rule 32; Delivery-Conventions.md §4). PR #49. The branch also carries a merge of origin/main (FIX-001, PR #48, already reviewed and merged); the diff is taken from the merge base, 42b1c40, so FIX-001's changes are not in it.

## Scope (the union of the four briefs, handoff/CONFIG-B3b.md, -r2.md, -r3.md, -r4.md)

- `tools/dump-cli.py` — new: the generator. It reads each bridge program in `bridge/cursor-bridge/`: an argparse program by importing it and calling its top-level `build_parser()` (with `sys.dont_write_bytecode` set and restored, nothing run); a hand-parsed program from its module docstring's usage; a library (no `__main__` block) is skipped. It writes `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` (rendered from the JSON); `--check` compares both with the programs, names the stale one and writes nothing. A default (and, from round 4, a choice) that is an absolute path under the bridge's folder becomes `<bridge folder>/...`; any other absolute path, the folder itself, a type the walk cannot write, a dict key that does not walk to a distinct string, and NaN or an infinity are refused, naming the program and the option. Every string of the built data (usage, description, sub-command names, option strings, dest, type, help, choices, default leaves) is refused if, in one canonical form (`normcase`, runs of `\` or `/` to one `/`), it holds the repository, home or current folder, whole or without its drive.
- `docs/cli-reference.json`, `docs/CLI_REFERENCE.md` — generated.
- Six bridge programs (completion-check, plan-check, diagram-check, inventory-check, sync-check, evaluate-reports): their argument parser moved into a top-level `build_parser()`, behaviour unchanged (the supervisor compared every parser before and after: equal); `bridge/cursor-bridge/MANIFEST.json` regenerated (VERSION byte-identical).
- `.github/workflows/tests.yml`: a step "the command reference docs/cli-reference.json matches the programs" running `python tools/dump-cli.py --check`, after the manifest step; the windowless step now also scans `.cursor/hooks`. `.githooks/pre-commit`: the same `--check` after the windowless check. `tests/test_release_b_ci_floor.py`: WORKFLOW_PIN updated for the workflow change.
- Records: docs/BUILDER_NOTES.md (the builder's dated lines; round 4's corrected by the supervisor after Review A); handoff/CONFIG-B3b*.md (the four briefs and the four reports); docs/HARDENING.md (Stage B3, CONFIG-B3b), docs/INVENTORY.md (a Features row, a Decisions row), docs/PROJECT_STATUS.md (as at this pull request's merge, ISS-009); docs/ROSTER.resolved.json (the roster's resolve times).

## Tests the supervisor wrote

`tests/test_dump_cli.py`, all of it (92 tests with their parameters): 37 of round 1, 10 of round 2 (`test_cfgb3b_r2_*`), 19 of round 3 (`test_cfgb3b_r3_*`), 25 of round 4 (`test_cfgb3b_r4_*`, 23 written before the run and 2 after it). They enforce Delivery-Conventions.md §4 (the reference is generated from the programs, and a stale one fails CI) and supervisor rule 54 (no computer path enters a commit; this repository is public), as each docstring states. Each round's new tests were red against the previous round's code where they test new behaviour (round 3: 7 of 19; round 4: 16 of 23); the others pin behaviour against mutants the reviewers found surviving.

Mutation drivers (the supervisor's, on scratch copies, restore byte-checked): round 3's (q), normcase removed on either or both sides, each caught by three tests; round 4's (y), only string choices checked, caught by test_cfgb3b_r4_a_choice_holding_a_path_inside_a_string_is_refused.

## How the rounds were settled

- Round 1: Review A REJECT; S1 a list default leaked a path and S2 relpath raised across drives (both reviewers, convergent), S3 a program without a docstring crashed, test gaps, bytecode written, abbreviations accepted, duplication, Markdown. Round 2's brief.
- Round 2: Review A REJECT 2/2/6 (B1 the default check read json.dumps text, which doubles backslashes; B2 the Markdown list marker lost), security FAIL on B1 (convergent). Round 3's brief.
- Round 3: sentinel CLEAR, suite 1696/25, Review A APPROVE 0/2/6, security re-check FAIL (a folder found in one written form only: doubled backslashes from a repr or JSON, Git Bash, WSL, no drive). REVIEWERS DISAGREE on whether the path check is complete (correctness): decided for the security side, which aligns with rule 54. The dict-key traceback was convergent (supervisor, security, Review A S1): blocking. Round 4's brief.
- Round 4: sentinel CLEAR; suite 1722 passed, 25 skipped; security re-check PASS with advisories (contrived encodings, the type callable, nargs; recorded in HARDENING); Review A APPROVE 0/2/6. S1 (the drive-less fragment refuses a clean reference for a one-level folder such as D:\docs; fails closed; not hit today) recorded as a lead by the by-class line; S2 (a wrong lesson in BUILDER_NOTES) taken. The builder's refusal of a default equal to the program's folder itself accepted and recorded.
- The gate, round 1 (snapshot of ffb8a9c): Review B APPROVE (verify OK, pr-activity OK); Review A on the records APPROVE 0/1/3, its should-fix taken in this round's records commit: the INVENTORY Features row and the status file's Last accepted said any folder of this computer, in any form, is refused, broader than the code (three folders; the other forms are HARDENING leads); now worded as the code holds it, the Features row naming choices too; one HARDENING lead made precise (a non-string type name) and the folder-kind message marked as worth taking at the next touch. This round reviews that records change: no code or test changed since ffb8a9c.
- The builder's assumptions, every round, with their dispositions: in the accept commit's message (run/review/ASSUMPTIONS-CONFIG-B3b.md).

## Verification

- `python tools/dump-cli.py --check` exits 0 on the branch; the pre-commit gate ran it on every commit since round 1.
- conformance-check --installable: 22 OK / 1 MISSING (the recorded no-diagram-index decision) / 5 NOTE; the command reference floor and its CI check are OK.
- test_r001_status_names_its_own_merge passes with PR #49's variables.
- No builder run wrote outside the Workspace (the marker and `find` check, every round).

## Out of scope

Folders of this computer other than the three, a link at an output file, contrived encodings (HARDENING leads); the User Manual's command-reference chapter (project end). Design for later increments is not this diff's defect.

## Expected files in the diff

The files above and `run/review/` (these review files, removed before the merge).
