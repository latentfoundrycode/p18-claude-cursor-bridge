# TASK-002 — round 3 (small correction): gate changes, keep main green

Round 2's Semgrep floor is **accepted** — real pinned rulesets (`p/python`, `p/secrets`, `.semgrep.yml`, the bridge rules), `semgrep scan ... --error`, PR diff-aware, teeth proven. Keep all of it. OSV, Socket, the lockfile, and the test stay exactly as they are.

**One change only.** Round 2 runs a **full-tree** scan on pushes to `main` (no `--baseline-commit`). That would fail `main` on a pre-existing, benign finding (`os.chmod(dst, 0o755)` on the `cursor-agent` shim in `bridge/cursor-bridge/bridge-install.py` — 0o755 is correct for an executable launcher). Introducing the floor should gate **new and changed** code, not retroactively fail `main` on code written before the floor existed.

**Make the push-to-`main` scan diff-aware too.** In the Semgrep step, when the event is a push (not a pull request), add `--baseline-commit "${{ github.event.before }}"` so the scan reports only findings introduced by that push, just as the pull-request branch already uses `--baseline-commit` against the merge base. Keep `--error`, keep the full ruleset, keep `fetch-depth: 0`, keep the step unguarded on `ubuntu-latest`. The net effect: every PR and every merge gates the code it introduces; the existing tree is not re-litigated by this floor (a separate full-tree audit is tracked as a follow-up).

Guard against the first-push edge case where `github.event.before` is all-zeroes (a brand-new branch/first push): if `github.event.before` is `0000000000000000000000000000000000000000`, fall back to a full scan (no baseline) — acceptable because that case does not apply to `main`.

## Scope
`.github/workflows/tests.yml` only (the Semgrep step). Plus `docs/BUILDER_NOTES.md` and your report `handoff/TASK-002-r3-report.md`. Do not touch anything else — not `bridge/`, not `.semgrep.yml`, not the other scanners, not the test (unless the test asserts something about the push path, which it should not).

## Done when
- On a pull request the Semgrep step is diff-aware against the merge base (unchanged from r2).
- On a push the Semgrep step is diff-aware against `github.event.before`, with the all-zeroes fallback.
- `--error` and the full ruleset are retained; the step is unguarded on ubuntu.
- The full suite, windowless, manifest, and conformance checks still pass.
- End with a one-paragraph summary, the report path, and an `Assumed, not verified` list.
