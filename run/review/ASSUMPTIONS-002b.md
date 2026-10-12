# TASK-002 — assumptions still open after the first live CI run (extra places to look, not the scope)

Confirmed by the live run on PR #16:
- Socket reads the token from `SOCKET_CLI_API_TOKEN`.
- `socket ci` discovers files to scan (2 found).
- Semgrep and OSV-Scanner pass in Actions.
- The test jobs pass on Windows and Ubuntu.

Still open:
- The live Socket API accepts the organization slug from `vars.SOCKET_ORG_SLUG`. Disposition: **test** (the PR's CI, once the owner sets the variable).
- The token in `SOCKET_SECURITY_API_KEY` belongs to that organization. Disposition: **test** (the PR's CI).
- `socket ci` in 1.7.0 still discovers `requirements.lock`. Disposition: **test** (the PR's CI).
