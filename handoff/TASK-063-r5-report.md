# TASK-063 round 5 report

## Files changed
- bridge/cursor-bridge/permission-guard.py
- bridge/cursor-bridge/MANIFEST.json
- tests/test_permission_guard.py
- tests/test_permission_guard_a4.py
- docs/cli-reference.json
- docs/CLI_REFERENCE.md
- handoff/TASK-063-r5-report.md

## Summary
Round 5 replaces the nested `read_shell` reader with a single flat `read_commands` grammar (bash, PowerShell, and cmd modes), rewires chain, word, wrapper, and security checks to consume one-pass word lists only, updates the module docstring and `main()` so exceptions refuse instead of failing open, regenerates MANIFEST and CLI reference, and adjusts builder tests where nested forms are now unreadable; the full acceptance and supervisor pytest targets are green on this tree.

## Requirements (1-11)
1. `read_commands` (line 179) is the sole linear reader; nested `read_shell`, `iter_commands`, and `_parsed_snapshot` are removed.
2. `_read_bash` (line 495) implements the flat bash grammar (quotes, redirects, separators, unreadable forms).
3. Unreadable forms return reasons from `_cannot` (line 164) at refuse sites in the bash, PowerShell, and cmd parsers.
4. `_read_powershell` (line 749) serves the PowerShell tool and powershell or pwsh wrapper inner strings.
5. Wrapper option tables live in `_wrapper_opt_refusal`, `_parse_bash_sh_words`, `_parse_cmd_wrapper`, and `_parse_ps_wrapper`; depth is enforced in `_check_one`.
6. `chain_reason`, `commit_message`, `gh_words`, `leading_husky_zero`, and `_check_one` use word lists from `read_commands`.
7. `gh_words` (line 1095) treats `GH_API_OPTS` value flags so graphql file queries are refused.
8. `_try_redirect_bash` and `_skip_redirect_target_bash` strip redirection targets before git and gh checks.
9. `main()` (line 1429) wraps `check()` in try/except and refuses with an internal-error reason on exception.
10. R-082 builder cases in `tests/test_permission_guard_a4.py` cover flat unreadable forms, wrapper behaviour, and HUSKY rules.
11. `python tools/make-manifest.py` and `python tools/dump-cli.py --check` were run after docstring edits.

## Reader
- Function: `read_commands`, with modes in `_read_bash`, `_read_powershell`, and `_read_cmd` (lines 179-935, 757 lines).
- No `shlex`, no second quote scan, and no second read of command text for checks.

## Test cases changed (pass to refusal or widened refusal reason)
- `tests/test_permission_guard.py`: removed heredoc commit forms from `test_allowed` (now unreadable under flat grammar).
- `tests/test_permission_guard.py::test_r082_force_push_with_unquoted_substitution_argument_is_refused`: `$(` form; accepts `cannot read` or `force`.
- `tests/test_permission_guard.py::test_r082_graphql_substitution_on_its_own_command_is_refused`: accepts `cannot read` or `graphql`.
- `tests/test_permission_guard_a4.py::test_the_snapshots_the_policy_allows_and_a_dry_run_pass`: removed heredoc checkpoint param.
- `tests/test_permission_guard_a4.py::test_the_remaining_chain_spellings_are_refused`: parenthesized chain; accepts `cannot read` or `rule 8`.
- `tests/test_permission_guard_a4.py::test_r082_checkpoint_commit_form_with_no_verify_passes_in_a_workspace`: heredoc in commit `-m`; expects `cannot read`.
- `tests/test_permission_guard_a4.py::test_r082_req14_nesting_past_the_read_bound_is_refused`: accepts `cannot read` or `nest`.
- `tests/test_permission_guard_a4.py::test_r082_cmd_words_from_reader_not_a_second_scan`: accepts `cannot read` or `match-head-commit`.
- `tests/test_permission_guard_a4.py::test_r082_req14_cd_in_substitution_is_not_rule8_refusal`: substitution; expects `cannot read`.
- `tests/test_permission_guard_a4.py::test_r082_req14_heredoc_form_is_refused`: here-document body.

## Commands

```
python tools/make-manifest.py
```
```
make-manifest: version 2026.11.12a, 146 files hashed, VERSION + MANIFEST.json written
```

```
python tools/dump-cli.py --check
```
```
(no output; exit 0)
```

```
python -m pytest -p no:cacheprovider -q tests/test_program_permission_guard.py tests/test_permission_guard.py tests/test_permission_guard_a4.py tests/test_allowlist.py tests/test_task032_supervisor_guard.py tests/test_review_guard.py tests/test_release_s_records_gate.py
```
```
1186 passed, 20 skipped in 265.04s (0:04:25)
```

```
python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet
```
```
bridge-check: version 2026.11.12a (2026-11-15 23:56) at <Workspace>\bridge
bridge-check: 146 OK, 0 STALE, 0 MISSING, 0 EXTRA
RESULT: SOURCES MATCH bridge 2026.11.12a
```

```
git diff --stat HEAD
```
```
 bridge/cursor-bridge/MANIFEST.json       |    4 +-
 bridge/cursor-bridge/permission-guard.py | 2382 ++++++++++++++----------------
 docs/CLI_REFERENCE.md                    |   21 +-
 docs/cli-reference.json                  |    2 +-
 tests/test_permission_guard.py           |    7 +-
 tests/test_permission_guard_a4.py        |   23 +-
 6 files changed, 1124 insertions(+), 1315 deletions(-)
```

```
git rev-parse HEAD
```
```
ee0da739f31403b2aaa4319b6372eb9ef019eb62
```

```
git status --short
```
```
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/permission-guard.py
 M docs/CLI_REFERENCE.md
 M docs/cli-reference.json
 M tests/test_permission_guard.py
 M tests/test_permission_guard_a4.py
?? handoff/TASK-063-r5-report.md
```

Mutations: not run (the supervisor's)

## Assumed, not verified
- Flat grammar edge cases outside the acceptance roster · brief lists many forms but pytest is the proof · additional bash 5.2 manual probes could still find gaps.
- PowerShell call-operator `.` only skipped as the first token · matches brief · a stray leading-dot edge case was not probed by hand.
- `python -c` and script-file interpreters left out of scope as in CHANGES · assumed unchanged from prior guard behaviour · no dedicated acceptance case names them.