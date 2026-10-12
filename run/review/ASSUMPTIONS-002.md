# TASK-002 — the builder's "Assumed, not verified", with dispositions

These are extra places to look. They are not the review's scope. All six are verified by this PR's own CI run, the first time the floor executes with network access and the Socket token.

- Semgrep's registry packs (`p/python`, `p/secrets`) and the bridge rules behave in GitHub Actions without `SEMGREP_APP_TOKEN` as they did locally. Disposition: **test** (the PR's `security floor` job).
- `socket ci` run from the repository root discovers `requirements.lock` as a Python manifest under the `socket.yml` policy. Disposition: **test** (the PR's Socket step).
- `persist-credentials: false` together with `fetch-depth: 0` still lets `git merge-base` find the PR's base. Disposition: **test** (the PR's Semgrep step).
- Node 22 on ubuntu-latest suits `@socketsecurity/cli@2.1.0`. Disposition: **test** (the PR's Socket step).
- `permissions: contents: read` is enough for checkout, pip and every scanner step. Disposition: **test** (the PR run).
- OSV-Scanner v2.7.0 reads `requirements.lock` through `--lockfile='requirements.txt:requirements.lock'` and does not exit 128. Disposition: **test** (the PR's OSV step).
