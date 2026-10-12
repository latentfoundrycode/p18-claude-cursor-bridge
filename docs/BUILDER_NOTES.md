# Builder notes

2026-10-12 TASK-002-r2: Semgrep CLI 1.176.1 rejects `semgrep scan --dry-run` (suggests `--dryrun`, which is autofix-only); used `semgrep --validate --config …` to confirm rule load counts per the handoff report.

2026-10-12 TASK-002-r3: Push-to-`main` Semgrep uses `--baseline-commit ${{ github.event.before }}` (skip baseline when `before` is the all-zero SHA) so the floor gates only code introduced by the push; PR path still uses `git merge-base`.

2026-10-12 TASK-002-r4: `@socketsecurity/cli@2.1.0` `socket ci` has no `--files` flag (it is ignored); the step runs `socket ci` from the repo root and the CLI scans `.`, picking up `requirements.lock` as a supported manifest.
