# TASK-002 — round 2 (correction): make the Semgrep floor real and deterministic

Round 1 is **mostly accepted**. Keep exactly as they are: `osv-scanner.toml`, `socket.yml`, `requirements.lock`, `tests/test_release_b_ci_floor.py`, the `tests` job's switch to `python -m pip install -r requirements.lock`, the OSV-Scanner step (binary pinned by SHA-256, explicit exit-code handling, `--lockfile='requirements.txt:requirements.lock'`), and the Socket step (`SOCKET_CLI_API_TOKEN` ← `secrets.SOCKET_SECURITY_API_KEY`). Do not change them.

**Fix only the Semgrep floor.** The problem: `.semgrep.yml` contains a single non-matching *probe* rule, and the step runs `semgrep ci --config .semgrep.yml`. `semgrep ci` applies the rules configured in the Semgrep AppSec **Platform policy**, which is empty on this brand-new account, and passing `--config` can override even that — so the Semgrep step has **no confirmed real rules**. A security floor that passes green while scanning with no meaningful rules is worse than none (N8: security must be *measured*, deterministically).

## What the corrected Semgrep floor must do

1. **`.semgrep.yml` is a real, pinned ruleset — not a probe.** Configure Semgrep to run meaningful rules for this codebase (it is Python). Use pinned registry rulesets that cover injection, dangerous calls, and secrets — at minimum `p/python` and `p/secrets` (and include the concat-SQLi coverage the bridge cares about, either through those packs or by referencing `bridge/cursor-bridge/semgrep-bridge-rules.yml`). Record the exact rulesets in the file as comments. Remove the `eval(...NO-MATCH)` probe.

2. **The scan applies those rules deterministically and blocks on findings — it must NOT depend on the Semgrep Platform policy.** Run `semgrep scan` (not `semgrep ci`) with explicit `--config` pointing at the ruleset(s) and `--error` so a finding fails the step. `SEMGREP_APP_TOKEN` stays set in the step env so the registry/Pro rules resolve. Confirm with `semgrep scan --config .semgrep.yml --dry-run` (locally, OSS, no token needed) that the intended rules actually load (a non-zero rule count, not one probe).

3. **Gate new/changed code, not the whole existing tree.** The scan must be diff-aware on pull requests so it checks what the PR changes, not re-litigate the entire existing `bridge/` tree (use `--baseline-commit` against the PR's merge base, or Semgrep's diff-aware mechanism). On a push to `main` a full scan is acceptable. If a full scan would flag existing `bridge/` code, do NOT edit `bridge/` and do NOT suppress anything — stop and report the findings so the supervisor can decide (a separate follow-up).

4. **Prove the floor has teeth.** Before finishing, create a throwaway fixture file containing a pattern your ruleset should catch (e.g. a Python `eval(` on a non-literal, or an obvious SQL string-concatenation), run `semgrep scan --config .semgrep.yml` against it locally (OSS engine, no token), and confirm it reports at least one finding. Record the command and the finding count in your report. Then delete the fixture so it is not committed. This demonstrates the floor is not a no-op.

5. Keep every GitHub Action pinned by full commit SHA, and the Semgrep CLI version pinned (`semgrep==1.176.1` or newer, pinned). Keep the Semgrep step unguarded on `ubuntu-latest` (no `if:`, no `continue-on-error`).

## Scope (unchanged from round 1)
`.github/workflows/tests.yml`, `.semgrep.yml`, `osv-scanner.toml`, `socket.yml`, `requirements.lock`, `tests/test_release_b_ci_floor.py`, plus `docs/BUILDER_NOTES.md` and your report `handoff/TASK-002-r2-report.md`. Do not touch anything else — not `bridge/`, not other tests, not `docs/` beyond BUILDER_NOTES, not repository settings. No secret value in any file (the tokens are repo secrets referenced by name). No new runtime dependencies. No hard line wraps.

## Done when
- `.semgrep.yml` loads a real ruleset (`semgrep scan --config .semgrep.yml --dry-run` shows more than the old single probe); the teeth fixture confirmed a finding (recorded, fixture deleted).
- The Semgrep step runs `semgrep scan` with explicit `--config` and `--error`, diff-aware on PRs, token in env, unguarded on ubuntu.
- `tests/test_release_b_ci_floor.py` still passes (update it only if needed so it still asserts an unguarded Semgrep step on ubuntu; it must NOT assert the probe).
- The full suite still passes; windowless, manifest, and conformance checks still OK.
- End with a one-paragraph summary, the report path, and an `Assumed, not verified` list (the real scanner behaviour on the PR remains CI-confirmed).
