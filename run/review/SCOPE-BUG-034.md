# SCOPE - BUG-034

BUG-034 is a fix increment on branch bug-034, cut from origin/main 1f5ef8e (after stage B5's close, PR #104). It comes from TASK-026's release-level review, pass 1, finding M2. bridge-install.py kept the installed release as the way back only when the two versions differed. A release folder that carried the installed release's version but other files (main before its stamp) therefore replaced the installed release with no previous copy kept, and --rollback then had nothing to restore. There were two builder rounds. Round 1's brief is handoff/BUG-034.md, its report is handoff/BUG-034-r1-report.md and its accept commit is "BUG-034 r1". Round 2's brief is handoff/BUG-034-r2.md and its report handoff/BUG-034-r2-report.md. Round 2 came from round 1's Review A and security audit, which converged on one point: --anyway replaced a same-version tree with no way back kept and said nothing.

## Scope (both briefs)

Files the builder may create or modify:
- bridge/cursor-bridge/bridge-install.py
- bridge/cursor-bridge/MANIFEST.json (only by running `python tools/make-manifest.py`)
- docs/cli-reference.json and docs/CLI_REFERENCE.md (only by running `python tools/dump-cli.py`)
- docs/BUILDER_NOTES.md (append only)
- handoff/BUG-034-r1-report.md and handoff/BUG-034-r2-report.md

What the code must do:
- When the installed version equals the release folder's version and the two manifests' fingerprints differ, install() refuses with exit 2 before anything changes, under --dry-run too. --anyway is the exception. The refusal names the version and the differing files with few().
- With --anyway, install() prints one `  WARNING        the installed <version> was replaced by other files of the same version (<n> file(s): <few>); no way back to it was kept; installed with --anyway.` line after the banner and then installs as before.
- The differing list is computed once.
- An identical release still installs again, the repair the installer's own messages name.
- The docstring's item 1 says all of this.

## Out of scope

- .env, secrets/, CI configuration.
- Every file under tests/ (the supervisor's).
- bridge/cursor-bridge/VERSION, which must come out byte-identical.
- Every other file under bridge/, every CHANGELOG and tools/.
- In bridge-install.py: rollback(), replace_release(), save_previous(), read_inputs(), fingerprints_of(), manifest_of(), not_as_released(), few() and main(). The command line does not change.
- In install(), for round 2: the round 1 refusal's sentence and conditions, the identical-release path, the first install, and the other-version path with its S4 warning.
- The release stamp, the CHANGELOG entry and the install run sheet. These are TASK-027's and are later work, not this diff's defect. Without the stamp, main still says 2026.10.25a, and this fix is what stops an install of it from replacing the installed release silently.

## Tests the supervisor wrote (tests/test_bug034.py; enforces: R-037 and bridge-install.py's docstring, the previous release kept and put back with --rollback)

- test_bug034_a_release_of_the_installed_version_with_other_files_is_refused: exit 2 with the refusal's words and the version. The installed tree and its manifest are unchanged. An older kept copy is neither rotated nor changed. This is the reproduction, and it failed on origin/main.
- test_bug034_a_file_listed_in_one_manifest_only_is_named: a file present in one manifest only is counted and named.
- test_bug034_the_refusal_holds_under_a_dry_run: exit 2 and no "(dry run)" banner. It failed on round 1's first form.
- test_bug034_a_dry_run_with_anyway_warns_and_changes_nothing: exit 0, "(dry run)", the WARNING, and the installed tree unchanged. This was the builder's round-2 assumption, turned into a test.
- test_bug034_the_same_release_installed_again_is_still_allowed: the repeated install of the identical release still works.
- test_bug034_anyway_installs_it_for_the_maintainers_rehearsals: --anyway installs the other files and prints the WARNING with "no way back to it was kept". It failed on round 1's code.

## Expected bookkeeping and records in the diff

- bridge/cursor-bridge/MANIFEST.json, regenerated.
- docs/cli-reference.json and docs/CLI_REFERENCE.md, regenerated: the docstring's item 1 only.
- handoff/BUG-034.md, handoff/BUG-034-r2.md and both builder reports.
- docs/HARDENING.md: the advisory points of BUG-034's gate.
- docs/PROJECT_STATUS.md, as at this PR's merge (ISS-009).
- run/review/: this file, the diff and the assumptions file.

## Checks run

- Round 1: Review A APPROVE (0/0/8); security-auditor PASS (0 blocking, 3 advisory).
- Round 2: Review A and the security-auditor, verdicts in the PR body.
- Round 2's tests: test_bug034, test_rollback, test_install_check, test_install_check_a4 and test_dump_cli, 155 passed.
- `dump-cli --check` OK; `bridge-check --sources --root bridge` 144 OK; the secret sentinel.
- The owner's three-round ceiling applies by hand until release B installs. This is Review B's round 1.
