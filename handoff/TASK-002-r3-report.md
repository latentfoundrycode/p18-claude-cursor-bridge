# TASK-002 round 3 report

## Files changed

- `.github/workflows/tests.yml` (Semgrep step only)
- `docs/BUILDER_NOTES.md`
- `handoff/TASK-002-r3-report.md`

## Summary

Extended the Semgrep floor so pushes to `main` are diff-aware: on `push` events the step adds `--baseline-commit` from `github.event.before`, skipping the baseline when `before` is the all-zero SHA (first-push edge case). Pull requests are unchanged (`git merge-base` against the PR base). `--error`, the full ruleset, `fetch-depth: 0`, and the unguarded `ubuntu-latest` step are retained.

## Verification

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

- `github.event.before` on pushes to `main` is always the prior tip of `main` (or the all-zero SHA on first push) · GitHub `push` webhook payload docs · first green `security-floor` job on a merge to `main`.
- Semgrep `--baseline-commit` with `github.event.before` reports only findings introduced between that commit and `github.sha` · Semgrep baseline docs · same behavior as the PR merge-base path validated in r2 locally.
- Force-pushes and empty pushes still behave acceptably with this baseline choice · GitHub event semantics · not exercised locally.
- Registry packs and `--error` behavior in CI are unchanged from r2 · prior report assumptions · `SEMGREP_APP_TOKEN` still required in CI.
