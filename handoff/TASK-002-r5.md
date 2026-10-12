# TASK-002 — round 5 (fix the Socket step after the first live CI run)

Everything else in the floor is accepted (Review A and Review B approved; Semgrep and OSV-Scanner passed on the PR). **Fix only the Socket step**, in `.github/workflows/tests.yml`.

## What the live run showed (PR #16, run 38241764324)
- `npm warn deprecated @socketsecurity/cli@2.1.0: bad build`. The pinned version is a deprecated bad build. The npm `latest` dist-tag is `1.7.0`; 2.x is off the supported line.
- `CLI: v2.1.0 | cmd: socket ci | org: (not set) | token: … (env)`. The token was read from `SOCKET_CLI_API_TOKEN` (good). The organization was **not set**.
- `Socket API Request failed (404): Organization not found`. The step exits 1.
- `Found 2 files to include in scan`. Discovery of `requirements.lock` works.

## The fix
1. Pin the CLI to the current, **non-deprecated** release: `npm install -g @socketsecurity/cli@1.7.0` (or the current `latest` if newer). Confirm first, and record the output in your report:
   - `npm view @socketsecurity/cli@<version> deprecated` prints nothing;
   - `npm view @socketsecurity/cli dist-tags` names that version as `latest`.
2. Name the organization. Add `SOCKET_CLI_ORG_SLUG: ${{ vars.SOCKET_ORG_SLUG }}` to the Socket step's `env:`, beside the existing `SOCKET_CLI_API_TOKEN: ${{ secrets.SOCKET_SECURITY_API_KEY }}`. `SOCKET_CLI_ORG_SLUG` is the variable the 1.7.0 README documents. The owner sets the repository variable `SOCKET_ORG_SLUG`. It is an identifier, not a secret, so it goes in `vars`, never `secrets`, and is never written literally in the file.
3. Confirm, from the pinned version's own `--help` or its bundled source, that `socket ci` in that version:
   - reads `SOCKET_CLI_ORG_SLUG` and `SOCKET_CLI_API_TOKEN`;
   - still exits non-zero when the scan is unhealthy.
   Record where you confirmed each. If 1.7.0's `socket ci` differs from what step 2 assumes, stop and report; do not improvise flags.
4. Keep the step unguarded, with no `|| …` status swallowers. Keep `actions/setup-node` and Node 22 as they are, unless 1.7.0 declares an incompatible `engines.node`; check it and report.

## The test is supervisor-owned
`tests/test_release_b_ci_floor.py` already requires `SOCKET_CLI_ORG_SLUG: ${{ vars.SOCKET_ORG_SLUG }}` on the Socket step, and fails today. Do not modify it. Your change must make it pass (12 tests).

## Scope
- `.github/workflows/tests.yml` (the Socket step only)
- `docs/BUILDER_NOTES.md`
- your report `handoff/TASK-002-r5-report.md`
Nothing else. No secret value, no new dependencies beyond the CLI version change, no hard line wraps.

## Done when
- `python -m pytest tests/test_release_b_ci_floor.py -q` gives 12 passed.
- The full suite passes, and windowless, `bridge-check --sources`, and conformance-check's five floor lines are OK.
- The `npm view` deprecation and dist-tag outputs, and the `socket ci` env-var confirmation, are recorded in the report.
- End with a one-paragraph summary, the report path, and an `Assumed, not verified` list. The real API call is confirmed by the PR's CI once the owner has set `SOCKET_ORG_SLUG`.
