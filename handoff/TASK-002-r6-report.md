# TASK-002 round 6 report

## Files changed

- `.github/workflows/tests.yml` (Socket step only)
- `docs/BUILDER_NOTES.md`
- `handoff/TASK-002-r6-report.md`

## Summary

Added `--no-banner` to the Socket step’s `socket ci` invocation so the CLI does not emit the compact CI header that prints the first five characters of the API token.

## `--no-banner` confirmation (@socketsecurity/cli@1.7.0)

Scratch install (outside the Workspace, removed after investigation):

```
mkdir -p /tmp/socket-cli-r6-scratch && cd /tmp/socket-cli-r6-scratch
npm install @socketsecurity/cli@1.7.0 --no-save
npx socket ci --help
npx socket --help
npx socket ci --no-banner --help
```

`socket --help` (global options) documents:

```
--no-banner                 Hide the Socket banner
```

`socket ci --help` does not repeat every global flag, but notes that all commands inherit them.

`socket ci --no-banner --help` printed only the help text (no ASCII or compact `CLI: v1.7.0 | …` line).

Bundled source:

| Claim | File:line |
|-------|-----------|
| `--no-banner` sets `banner: false` via meow’s negated flag | `dist/utils.js:3533-3537` (help lists `noBanner` explicitly) |
| Banner suppressed when `flags['banner'] === false` | `dist/utils.js:3255-3257` (`shouldSuppressBanner`) |
| Banner body with `token: ${tokenPrefix}***` in compact CI mode | `dist/utils.js:3196-3209` (`getAsciiHeader`) |
| Prefix from `apiToken.slice(TOKEN_PREFIX_LENGTH, TOKEN_PREFIX_LENGTH + TOKEN_VISIBLE_LENGTH)` | `dist/utils.js:1920-1922` (`getVisibleTokenPrefix`) |

## Other token-prefix printing (search result)

`rg 'getVisibleTokenPrefix|tokenPrefix' dist/*.js` in the installed package found only:

1. `dist/utils.js` — `getVisibleTokenPrefix` and `getAsciiHeader` (banner path above).
2. `dist/cli.js:17322-17324` — `outputOrganizationList` logs “starting with:” plus the visible prefix for the **organization** list command, not for `socket ci`.

`handleCi` (`dist/cli.js:7495-7567`) calls `getDefaultOrgSlug` and `handleCreateNewScan` with `outputKind: 'json'`; it does not call `getVisibleTokenPrefix` or `emitBanner` when `shouldSuppressBanner` is true. With `--no-banner`, the token prefix is not printed on the `socket ci` path.

## Organization slug for `socket ci` (no workflow change this round)

| Stage | File:line | Mechanism |
|-------|-----------|-----------|
| Env parsed into `ENV.SOCKET_CLI_ORG_SLUG` | `dist/constants.js:361-364` | `env['SOCKET_CLI_ORG_SLUG']`, with fallback `env['SOCKET_ORG_SLUG']` |
| `socket ci` resolves org | `dist/cli.js:7500` | `await utils.getDefaultOrgSlug()` inside `handleCi` |
| Env var used before API/token default org | `dist/utils.js:3898-3904` | If `constants.default.ENV.SOCKET_CLI_ORG_SLUG` is set, return it; else fetch organizations from the token |

The banner’s `org:` field (`dist/utils.js:3202-3208`) uses the `--org` flag or persisted config `defaultOrg`, not `SOCKET_CLI_ORG_SLUG`. That explains CI logs showing `org: (not set)` on the banner while the scan JSON still carries the correct `orgSlug` when the env var is set.

## Verification

```
python -m pytest tests/test_release_b_ci_floor.py -q
```

13 passed.

```
python -m pytest tests -q
```

940 passed, 20 skipped.

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

- Pushed CI run no longer contains the Socket compact header or token prefix in the log · supervisor-owned merge verification on the pushed head.
- `socket ci --no-banner` still fails the step on an unhealthy scan with the same policy as before · prior r5 behavior and CLI help text; not re-run with a real token.
