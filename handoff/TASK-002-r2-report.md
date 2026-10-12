# TASK-002 round 2 report

## Files changed

- `.semgrep.yml`
- `.github/workflows/tests.yml` (Semgrep step only; OSV/Socket/pip unchanged)
- `docs/BUILDER_NOTES.md`
- `handoff/TASK-002-r2-report.md`

## Summary

Replaced the non-matching Semgrep probe with a real floor: `.semgrep.yml` documents registry packs `p/python` and `p/secrets`, embeds the OSS concat-SQLi rules (same ids as `bridge/cursor-bridge/semgrep-bridge-rules.yml`), and the `security-floor` job runs `pipx run semgrep==1.176.1 scan` with `--config p/python`, `--config p/secrets`, `--config .semgrep.yml`, `--config bridge/cursor-bridge/semgrep-bridge-rules.yml`, and `--error`, with `fetch-depth: 0` and `--baseline-commit` from `git merge-base` on pull requests; pushes to `main` run a full-tree scan.

## Semgrep verification

### Rule load (dry-run)

`semgrep scan --config .semgrep.yml --dry-run` is not accepted by Semgrep 1.176.1 (`unknown option '--dry-run'`). Equivalent checks:

```
semgrep --validate --config .semgrep.yml
```

```
Configuration is valid - found 0 configuration error(s), and 2 rule(s).
```

```
semgrep --validate --config p/python --config p/secrets --config .semgrep.yml --config bridge/cursor-bridge/semgrep-bridge-rules.yml
```

```
Configuration is valid - found 0 configuration error(s), and 204 rule(s).
```

### Teeth fixture (deleted before commit)

Command:

```
semgrep scan --config .semgrep.yml _task002_teeth_fixture.py
```

Finding count: **1** (`bridge-sql-string-concat-py` on `cur.execute("SELECT * FROM t WHERE id = " + user_id)`). Fixture file removed after the run.

### Full scan on current tree (supervisor follow-up)

Without `--baseline-commit`, the combined ruleset reports one blocking finding in existing `bridge/` code (not edited per brief):

- `bridge/cursor-bridge/bridge-install.py` — `python.lang.security.audit.insecure-file-permissions.insecure-file-permissions` at `os.chmod(dst, 0o755)`.

PR diff-aware scan against `git merge-base origin/main HEAD` on this branch: **0** findings (5 targets).

## Other verification

```
python -m pytest tests/test_release_b_ci_floor.py -q
```

6 passed.

```
python -m pytest tests -q
```

881 passed, 20 skipped.

```
python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge
```

0 FAIL, 0 NOTE.

```
python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet
```

SOURCES MATCH.

## Assumed, not verified

- `SEMGREP_APP_TOKEN` in CI resolves registry packs the same as local OSS fetches for `p/python` and `p/secrets` · token enables Pro/registry in Semgrep docs · first green `security-floor` job on the PR.
- `--baseline-commit` with `fetch-depth: 0` and `git merge-base` matches GitHub’s PR merge base in all edge cases · Semgrep baseline docs · PR job on this branch.
- A full scan on `main` after merge will fail until the `bridge-install.py` chmod finding is accepted or fixed out of band · local full scan with `--error` · supervisor decision on the finding above.
- `semgrep scan --config .semgrep.yml --dry-run` in the brief means “confirm rules load”; CLI uses `--validate` instead on 1.176.1 · `docs/BUILDER_NOTES.md` · `--validate` rule counts.
