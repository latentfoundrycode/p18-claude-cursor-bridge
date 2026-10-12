# SCOPE-002d — TASK-002 round 6: the Socket CLI must not print part of its key

PR #16. Both reviewers approved the merged head 0517c5b (re-review 002c). Review A's Should fix — the Socket CLI's banner prints the first 5 characters of the API key into the CI log (`token: <5 chars>*** (env)`), which GitHub does not mask — was raised to blocking because the repository is public. Round 6 fixes it through the builder.

## Files
- run/review/REVIEW-002d.diff — the whole branch against origin/main (read it whole; the review's subject).
- run/review/REVIEW-002d-round.diff — round 6 alone (0517c5b..HEAD), for orientation: it removes the 002c review files and adds the brief, the test, the fix, the report and the records.
- run/review/ASSUMPTIONS-002d.md — extra places to look.

## Round 6's brief (handoff/TASK-002-r6.md), quoted in short
- Scope: `.github/workflows/tests.yml` (the Socket step only); `docs/BUILDER_NOTES.md`; the report `handoff/TASK-002-r6-report.md`. Satisfies R-002.
- Fix: `socket ci --no-banner`, after confirming in 1.7.0's help or bundled source that the flag exists and that no other place on the `socket ci` path prints the key; never filter the step's output; stop and report rather than improvise.
- Report (not change) how `socket ci` 1.7.0 takes its organization.
- Out of scope: everything else in the floor, which both reviewers approved at 0517c5b and which is unchanged since (`git diff --stat 0517c5b HEAD -- .semgrep.yml osv-scanner.toml socket.yml requirements.lock` prints nothing; the workflow differs by the one line).

## What to check
1. The workflow's one-line change: `socket ci` → `socket ci --no-banner` (.github/workflows/tests.yml). It must not weaken the step: no skip, no swallowed status, no output filter.
2. The builder's evidence in handoff/TASK-002-r6-report.md: the flag's source (`dist/utils.js` shouldSuppressBanner / getAsciiHeader / getVisibleTokenPrefix), the search for other prints of the key prefix (only `outputOrganizationList`, another command), and the organization path (`SOCKET_CLI_ORG_SLUG` read in `getDefaultOrgSlug` before the API). You may verify by installing `@socketsecurity/cli@1.7.0` in a scratch folder outside the checkout and reading it; never run it with a key.
3. The CI run on this head (PR #16): the Socket step's log must show no `CLI: v1.7.0 | … | token:` line and still end with the scan result; the step must still succeed.
4. The records: docs/INVENTORY.md (the secret rows read "no spend possible", Review B's Should fix from 002c; the variable's row; the `--no-banner` decision row); docs/PROJECT_STATUS.md. `python ~/.claude/cursor-bridge/conformance-check.py . --offline` gives the five floor lines and "Spending limit recorded" OK (its other MISSING lines are configuration items already missing on main).
5. Gate integrity on the CI workflow, explicitly.

## Tests the supervisor wrote
- tests/test_release_b_ci_floor.py :: `test_r002_socket_prints_no_banner` — enforces Merge-Verification-Policy §Security (no secret in a log) and R-002: every `socket ci` line carries `--no-banner`; at least one `socket ci` exists (no vacuous pass). It failed against the checkpoint's workflow (`'socket ci'`) and passes now. The other 12 tests are unchanged.
- Full suite: 940 passed, 20 skipped. secret-sentinel CLEAR. Scope check: SCOPE CLEAN.

## Expected bookkeeping and record files
- handoff/TASK-002-r6.md (the brief), handoff/TASK-002-r6-report.md, docs/BUILDER_NOTES.md, docs/INVENTORY.md, docs/PROJECT_STATUS.md, run/review/ (these files).
