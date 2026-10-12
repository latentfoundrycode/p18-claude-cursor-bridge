# Review B scope (second round) — TASK-002 (PR #16): the security floor in the bridge's CI

You approved this pull request at head `b92a4be`. Since then, two things changed:

1. **The first live CI run failed on the Socket step.** The output was `npm warn deprecated @socketsecurity/cli@2.1.0: bad build`, a banner reading `org: (not set)`, and `Socket API Request failed (404): Organization not found`. The fix (round 5) is in `.github/workflows/tests.yml`'s Socket step:
   - The CLI is pinned to `@socketsecurity/cli@1.7.0`, which npm lists as `latest` and does not mark deprecated.
   - The step's env gains `SOCKET_CLI_ORG_SLUG: ${{ vars.SOCKET_ORG_SLUG }}`. The organization slug is a repository **variable** that the owner sets. It is an identifier, not a secret.
2. **The supervisor's spec test** `tests/test_release_b_ci_floor.py` gained `test_r002_socket_names_its_organization`, which requires exactly `${{ vars.SOCKET_ORG_SLUG }}`. A supervisor-side mutation driver (gitignored, not in the diff) kills 11 single-point mutants of the workflow.

Everything else is unchanged from the head you approved: Semgrep (OSS, explicit rulesets, `--error`, diff-aware), OSV-Scanner, the lockfile, the SHA pins, `permissions: contents: read` and `persist-credentials: false`.

## Where the increment ends
The CI security floor for the bridge's own repository (R-002). In scope: `.github/workflows/tests.yml`, `.semgrep.yml`, `osv-scanner.toml`, `socket.yml`, `requirements.lock`, `tests/test_release_b_ci_floor.py`. Design for later increments is not this diff's defect.

## Decisions already taken (do not re-litigate)
- OSS Semgrep engine with no token (the owner, 2026-10-12).
- Diff-aware scanning on pull requests and pushes. A full-tree audit of pre-existing code is a separate follow-up.
- `actions/setup-node` stays at v5.0.0, which runs on node24.

## Bookkeeping in the diff (not defects)
`docs/BUILDER_NOTES.md`, `handoff/TASK-002*-report.md`, the supervisor's briefs `handoff/TASK-002*.md`, the supervisor's records `docs/PROJECT_STATUS.md` and `docs/INVENTORY.md`, `docs/ROSTER.resolved.json`, and `run/review/`.

## What only CI can confirm
The live Socket scan cannot pass until the owner sets the repository variable `SOCKET_ORG_SLUG`. Until then the Socket step fails loudly, and that is correct. Do not count that failure against the code. Judge whether the step will work once the variable exists.
