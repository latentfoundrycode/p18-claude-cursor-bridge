# TASK-002 round 5 report

## Files changed

- `.github/workflows/tests.yml` (Socket step only)
- `docs/BUILDER_NOTES.md`
- `handoff/TASK-002-r5-report.md`

## Summary

Pinned `@socketsecurity/cli@1.7.0` (replacing deprecated `2.1.0`) and set `SOCKET_CLI_ORG_SLUG: ${{ vars.SOCKET_ORG_SLUG }}` beside the existing `SOCKET_CLI_API_TOKEN` mapping so `socket ci` can resolve the organization (404 on PR #16 when org was unset).

## npm view (recorded)

```
$ npm view @socketsecurity/cli@1.7.0 deprecated
(empty — no output)

$ npm view @socketsecurity/cli dist-tags
{ staged: '1.1.152', latest: '1.7.0' }

$ npm view @socketsecurity/cli@1.7.0 engines
{ node: '>=18.20.8', pnpm: '>=10.33.0' }
```

Node 22 from `actions/setup-node` satisfies `engines.node`.

## `socket ci` env and exit behavior (@socketsecurity/cli@1.7.0)

| Claim | Where confirmed |
|-------|-----------------|
| `SOCKET_CLI_API_TOKEN` | README “Environment variables” (`node_modules/@socketsecurity/cli/README.md`, lines 128–140) |
| `SOCKET_CLI_ORG_SLUG` | Same README section (line 138); also line 58 for paid/CI auth |
| Non-zero exit when scan is unhealthy | `socket ci --help` (“exits with error if unhealthy”; “exit code will be non-zero when the scan does not pass your security policy”) |

Step remains unguarded: `npm install -g @socketsecurity/cli@1.7.0` then `socket ci` with no `||` status swallowers.

## Verification

```
python -m pytest tests/test_release_b_ci_floor.py -q
```

12 passed.

```
python -m pytest tests -q
```

887 passed, 20 skipped.

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

## Assumed, not verified

- Live Socket API accepts the org slug from `vars.SOCKET_ORG_SLUG` once the owner sets the repository variable · CLI README documents `SOCKET_CLI_ORG_SLUG` · PR CI after owner configures `SOCKET_ORG_SLUG`.
- `socket ci` at repo root still discovers `requirements.lock` under `socket.yml` policy on 1.7.0 · same command as r4, prior live run found two files · next green Socket step in CI.
