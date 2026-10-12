# Review B scope — TASK-002 (PR #16): the security floor in the bridge's CI

## Where the increment ends
The increment is the CI security floor for the Claude-Cursor Bridge's own repository (release B, R-002). In scope (from `handoff/TASK-002.md` and its corrections `-r2`, `-r3`, `-r4`): `.github/workflows/tests.yml`, `.semgrep.yml`, `osv-scanner.toml`, `socket.yml`, `requirements.lock`, `tests/test_release_b_ci_floor.py`. Out of scope: everything under `bridge/`, every other test, repository settings, `docs/` beyond the bookkeeping below.

Design for later increments (the conditional-workflow framework, phase modules, traits, type workflows) is not this diff's defect.

## Decisions already taken (do not re-litigate)
- The owner chose the **OSS Semgrep engine with no token** (2026-10-12): the bridge's own code does no SQL or web input, so the Pro engine's interfile taint adds nothing. R-002 is engine-agnostic.
- Semgrep is **diff-aware on pull requests and pushes**: the floor gates new and changed code. A full-tree audit of pre-existing code is a separate follow-up. One known pre-existing finding, `os.chmod(dst, 0o755)` on the `cursor-agent` shim in `bridge/cursor-bridge/bridge-install.py`, is benign, because an executable launcher needs 0o755.
- `actions/setup-node` stays at v5.0.0. It runs on the node24 runtime, which was the end-of-life concern. Moving to v7 is a follow-up.

## Tests the supervisor wrote, and what each enforces
`tests/test_release_b_ci_floor.py` is supervisor-authored. It is not the builder's. It enforces `docs/BUILD_PLAN.md` TASK-002 "Done when" and R-002. Each test asserts:
- the three scanners run unguarded on ubuntu: no step-level or job-level `if:`, no `continue-on-error`, and no `|| true`, `|| :`, `|| echo` or `|| exit 0`;
- Semgrep is a `scan` with `--error`, explicit `--config` rulesets including the bridge rules, a `--baseline-commit` on both the PR path and the push path, no `--pro` and no token;
- Semgrep does not run on the Windows leg;
- every `uses:` is pinned by commit SHA (non-vacuous);
- every checkout sets `persist-credentials: false`;
- pip installs exactly `-r requirements.lock`;
- the lockfile pins its closure with `==`;
- `secrets.` appears only in a step's `env:`, and Socket is authenticated by `secrets.SOCKET_SECURITY_API_KEY`;
- a least-privilege `permissions: {contents: read}` block exists;
- the disabler regex catches the usual exit-status swallowers, which is the negative test's own precondition.

A supervisor-side mutation driver (`run/supervisor/mutate_ci_floor.py`, gitignored, not in the diff) applied 9 single-point breakages, and every one was killed.

## Bookkeeping and records expected in the diff (not defects)
- `docs/BUILDER_NOTES.md`
- the builder's reports `handoff/TASK-002-r1..r4-report.md`
- the supervisor's briefs `handoff/TASK-002.md`, `-r2.md`, `-r3.md`, `-r4.md`
- the supervisor's status records `docs/PROJECT_STATUS.md` and `docs/INVENTORY.md` (B2 recorded as a confirmed post-B release; waiting states)
- `docs/ROSTER.resolved.json` (a re-resolution timestamp)
- `run/review/` (these review files)

## What only CI can confirm (this PR's checks)
- Semgrep's registry packs load in Actions without a token.
- `socket ci` discovers `requirements.lock`.
- OSV-Scanner reads it through the requirements.txt parser.
- `persist-credentials: false` with `fetch-depth: 0` still gives the merge-base.
- Node 22 suits the Socket CLI.
- `contents: read` is enough for every step.
