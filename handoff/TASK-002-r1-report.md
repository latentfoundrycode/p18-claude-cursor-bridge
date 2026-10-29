# TASK-002 round 1 report

## Files changed

- `.github/workflows/tests.yml`
- `.semgrep.yml`
- `osv-scanner.toml`
- `socket.yml`
- `requirements.lock`
- `tests/test_release_b_ci_floor.py`
- `handoff/TASK-002-r1-report.md`

## Summary

Added `requirements.lock` as the sole Python install source for both matrix legs of the existing `tests` job, introduced a `security-floor` job on `ubuntu-latest` running Semgrep (`pipx run semgrep==1.176.1 ci` with `SEMGREP_APP_TOKEN` and `--config .semgrep.yml`), OSV-Scanner v2.7.0 (SHA-256–verified binary, explicit exit-code handling, `requirements.txt:requirements.lock` parser), and Socket (`npm install -g @socketsecurity/cli@2.1.0` then `socket ci --files '["requirements.lock"]'` with `SOCKET_CLI_API_TOKEN` from `SOCKET_SECURITY_API_KEY`), plus floor config files and `tests/test_release_b_ci_floor.py` asserting R-002 structural invariants.

## Pinned versions (no secrets)

| Item | Pin | File |
| --- | --- | --- |
| actions/checkout | `fbc6f3992d24b796d5a048ff273f7fcc4a7b6c09` (# v5) | `.github/workflows/tests.yml` |
| actions/setup-python | `ece7cb06caefa5fff74198d8649806c4678c61a1` (# v6) | `.github/workflows/tests.yml` |
| actions/setup-node | `49933ea5288caeca8642d1e84afbd3f7d6820020` (# v4.4.0) | `.github/workflows/tests.yml` |
| Semgrep CLI | `semgrep==1.176.1` (pipx) | `.github/workflows/tests.yml` |
| OSV-Scanner | release `v2.7.0`, binary SHA-256 `160c6253e2922e9e0a6a9771c5c4c40a4b3c6090b34a3cdd5e80c96cc2e4218b` | `.github/workflows/tests.yml` |
| Socket CLI | `@socketsecurity/cli@2.1.0` | `.github/workflows/tests.yml` |
| pytest / PyYAML | `9.1.1` / `6.0.3` | `requirements.lock` |

## Verification commands

### 1. `python -m pytest tests/test_release_b_ci_floor.py -q`

```
......                                                                   [100%]
6 passed in 5.84s
```

Exit code: 0

### 2. `python -m pytest tests -q`

```
881 passed, 20 skipped in 215.22s (0:03:35)
```

Exit code: 0

### 3. `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge`

```
windowless-check: 29 file(s) scanned, 0 FAIL, 0 NOTE
```

Exit code: 0

### 4. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`

```
bridge-check: version 2026.10.11d (2026-10-11 16:55) at <the Workspace>/bridge
bridge-check: 104 OK, 0 STALE, 0 MISSING, 0 EXTRA
RESULT: SOURCES MATCH bridge 2026.10.11d
```

Exit code: 0

### 5. `python bridge/cursor-bridge/conformance-check.py . --offline`

Relevant lines:

```
  OK       Semgrep in the gate
  OK       OSV-Scanner in the gate
  OK       Socket in the gate
  OK       Semgrep bridge rules or Pro engine
  OK       CI actions pinned by commit
```

No `… version pinned` NOTE for Semgrep, OSV-Scanner, or Socket.

Exit code: 1 overall (other floors outside TASK-002 scope).

### 6. `python bridge/cursor-bridge/lock-check.py origin/main`

```
lock-check: no dependency manifest changed against origin/main - nothing to verify
```

Exit code: 0

### 7. `python -m pip install --dry-run --ignore-installed -r requirements.lock`

```
Would install PyYAML-6.0.3 Pygments-2.21.0 colorama-0.4.6 iniconfig-2.3.1 packaging-26.3 pluggy-1.6.0 pytest-9.1.1
```

Exit code: 0 (Windows / Python 3.12; matches lockfile pins for this platform).

## Assumed, not verified

- Socket CLI reads the API token from `SOCKET_CLI_API_TOKEN` · bridge docs and KP-004 name that variable; repo secret is `SOCKET_SECURITY_API_KEY` · confirm with `socket --help` / env docs on `@socketsecurity/cli@2.1.0` in CI.
- OSV-Scanner v2.7.0 accepts `requirements.lock` via `--lockfile='requirements.txt:requirements.lock'` · filename is not auto-detected as pip format · green OSV step on PR without exit 128.
- Socket `socket ci --files '["requirements.lock"]'` treats the file as a Python manifest · `requirements.lock` is not listed in Socket manifest docs · green Socket step on PR with no “no manifest” outcome.
- `pipx run semgrep==1.176.1 ci --config .semgrep.yml` runs Pro with `.semgrep.yml` in one step when `SEMGREP_APP_TOKEN` is set · Semgrep version/token interactions vary · Semgrep step succeeds on PR.
- OSV exit codes 0/1/127/128 behave as documented in KP-005 for v2.7.0 · not run locally · PR workflow OSV step.
- No scanner findings on current tree · probe rule is non-matching; deps are current pins · first CI scanner run on PR.
