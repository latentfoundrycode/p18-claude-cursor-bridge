# TASK-002 round 4 report

## Files changed

- `.github/workflows/tests.yml`
- `.semgrep.yml`
- `docs/BUILDER_NOTES.md`
- `handoff/TASK-002-r4-report.md`

## Summary

Addressed Review A: workflow-level `permissions: {contents: read}`; `persist-credentials: false` on both checkout steps; Semgrep OSS without `SEMGREP_APP_TOKEN`, with `github.event.*` passed via step `env` and shell variables; deduplicated Semgrep configs (empty `.semgrep.yml` plus canonical bridge rules only); Socket `socket ci` without the ignored `--files` flag; `actions/setup-node` v5.0.0 at commit `a0853c24544627f65ddf259abe73b1d18a591444` with Node 22.

## Verification

```
python -m pytest tests/test_release_b_ci_floor.py -q
```

8 passed.

```
python -m pytest tests -q
```

883 passed, 20 skipped.

```
python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge
```

0 FAIL, 0 NOTE.

```
python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet
```

SOURCES MATCH.

```
python bridge/cursor-bridge/conformance-check.py . --offline
```

Five security-floor lines OK: Semgrep, OSV-Scanner, and Socket in the gate; Semgrep bridge rules or Pro engine; CI actions pinned by commit.

```
semgrep --validate --config p/python --config p/secrets --config .semgrep.yml --config bridge/cursor-bridge/semgrep-bridge-rules.yml
```

Configuration is valid — 204 rule(s) (202 community from `p/python` + `p/secrets`, 2 custom bridge rules; no duplicate bridge IDs).

Teeth (throwaway `_task002_r4_teeth_fixture.py`, deleted): one blocking finding `bridge-sql-string-concat-py` on `cur.execute("SELECT * FROM t WHERE id = " + user_id)`.

`git ls-remote https://github.com/actions/setup-node v5.0.0` → `a0853c24544627f65ddf259abe73b1d18a591444`.

## Assumed, not verified

- Semgrep registry packs and bridge rules behave the same in GitHub Actions without `SEMGREP_APP_TOKEN` · prior r2/r3 local `pipx run semgrep==1.176.1` · first green `security-floor` job after merge.
- `socket ci` from the repo root discovers `requirements.lock` with the repository `socket.yml` policy · Socket CLI 2.1.0 docs and r4 builder note · live Socket step in CI.
- `persist-credentials: false` with `fetch-depth: 0` still allows merge-base / baseline Semgrep logic · GitHub checkout action docs · not exercised in a fork PR locally.
- Node 22 on `ubuntu-latest` matches the runner image Socket and npm expect · setup-node v5 release notes · CI only.
- Workflow `permissions: contents: read` is sufficient for checkout, pip, and scanner steps · GitHub default token scopes · not tested with a deliberately restricted token.
