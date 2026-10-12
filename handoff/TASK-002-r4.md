# TASK-002 — round 4 (correction after Review A)

Rounds 1–3 are largely accepted: the lockfile, the OSV-Scanner step, the `tests` job's lockfile install, the diff-aware Semgrep logic, and the job structure stay. Review A rejected round 3 on the points below. Fix exactly these.

**The test is supervisor-owned.** `tests/test_release_b_ci_floor.py` has been rewritten by the supervisor as the specification for this increment. Do **not** modify it. Your workflow must make it pass; today it passes 7 of 8 and fails `test_r002_least_privilege_permissions`.

## 1. Semgrep: OSS engine, no token (owner's decision, 2026-10-12)
- Keep `semgrep scan` with explicit `--config` rulesets, `--error`, and the diff-aware `--baseline-commit` logic for pull_request and push (with the all-zeroes fallback).
- **Remove the `SEMGREP_APP_TOKEN` env from the Semgrep step.** The rulesets are public (`p/python`, `p/secrets`) and the bridge rules are a local file, so the token does nothing in `semgrep scan` and should not sit in a job that runs third-party binaries. Do **not** add `--pro` or `install-semgrep-pro`.

## 2. No duplicated rules
`.semgrep.yml` is currently a verbatim copy of `bridge/cursor-bridge/semgrep-bridge-rules.yml`, and the step loads both, so every concat-SQL finding is reported twice and the copy will drift. Load the bridge rules **once**, from the canonical file, via `--config bridge/cursor-bridge/semgrep-bridge-rules.yml` (do not edit that file). Remove the duplicated rules from `.semgrep.yml`:
- If Semgrep accepts a rules-free config (`rules: []`), keep `.semgrep.yml` as the documented home for future project-specific rules (list the packs in comments) and keep it on the command.
- Otherwise drop `--config .semgrep.yml` from the command and delete `.semgrep.yml`.
Either way each rule loads exactly once; confirm with `semgrep --validate` on the command's exact `--config` set (the rule count must equal p/python + p/secrets + the bridge rules, with no duplicates). `python bridge/cursor-bridge/conformance-check.py . --offline` must still show its five security-floor lines OK; if it cannot without the copy, stop and report rather than restoring the copy.

## 3. Socket: drop the dead flag
`--files '["requirements.lock"]'` is not a flag of `@socketsecurity/cli@2.1.0`'s `socket ci` (it is silently ignored; `socket ci` scans `.` and picks up `requirements.lock` as a supported manifest). Remove it. Record the real mechanism in `docs/BUILDER_NOTES.md`.

## 4. Node and setup-node
Node 20 is end-of-life and setup-node v4 runs on the retiring node20 Actions runtime. Use the current setup-node major, pinned by its full 40-hex commit SHA (verify the SHA with `git ls-remote https://github.com/actions/setup-node <tag>`), with `node-version: "22"`.

## 5. Security hardening
- Add a least-privilege `permissions:` block — `contents: read` at workflow level (neither job needs more).
- Set `persist-credentials: false` on every `actions/checkout` step, so the GITHUB_TOKEN is not left in `.git/config` while third-party scanner binaries run. The Semgrep diff-aware logic needs history (`fetch-depth: 0`), not credentials; keep `fetch-depth: 0`.
- Pass the `github.event.*` values the Semgrep script uses through the step's `env:` and reference them as shell variables, rather than interpolating `${{ ... }}` directly inside the `run:` script.

## Scope
`.github/workflows/tests.yml`; `.semgrep.yml` (edit or delete per §2); `docs/BUILDER_NOTES.md`; your report `handoff/TASK-002-r4-report.md`. Nothing else — not the test, not `bridge/`, not `socket.yml`, `osv-scanner.toml`, or `requirements.lock`, not repository settings. No secret value anywhere; no new dependencies; no hard line wraps.

## Done when
- `python -m pytest tests/test_release_b_ci_floor.py -q` → 8 passed.
- `python -m pytest tests -q` passes (report counts); windowless and `bridge-check --sources` OK; conformance-check's five floor lines OK.
- `semgrep --validate` on the step's `--config` set shows each rule once (record the count).
- Teeth re-check: a throwaway fixture with `cur.execute("SELECT * FROM t WHERE id = " + user_id)` produces at least one finding under the step's `--config` set (OSS); record it; delete the fixture.
- End with a one-paragraph summary, the report path, and an `Assumed, not verified` list.
