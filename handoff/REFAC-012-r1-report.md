# REFAC-012 round 1 report

## Files changed

- `bridge/cursor-bridge/evaluate-reports.py`
- `bridge/cursor-bridge/MANIFEST.json`
- `handoff/REFAC-012-r1-report.md` (this file)

## Summary

Refactored `scan_project` and `classify_window_runs` in `evaluate-reports.py` per REFAC-012: removed `ledger_skip` in favor of `scan_unreadable` for ledger updates, consolidated eight duplicate failed-read side effects into a single `failure` tuple and one block before `_read_alerts`, folded non-dict and non-list runs-body checks into `_validate_runs_list`, removed the always-true `if not scan_unreadable` guard, and introduced module-level `DEP_SCAN_RERUN` for the dependency-scan rerun command text. Regenerated `MANIFEST.json`; all 192 targeted tests passed unchanged before and after.

## Start state

```text
git status --short

```

```text
git rev-parse HEAD
f03f1de611caced148ca0fddaf58892d86acc6ec
```

Working tree held no uncommitted changes at start.

## Requirements 1 (pre-edit grep)

```text
git grep -n -w ledger_skip -- bridge
bridge/cursor-bridge/evaluate-reports.py:919:    ledger_skip = False
bridge/cursor-bridge/evaluate-reports.py:929:        ledger_skip = True
bridge/cursor-bridge/evaluate-reports.py:937:            ledger_skip = True
bridge/cursor-bridge/evaluate-reports.py:959:                    ledger_skip = True
bridge/cursor-bridge/evaluate-reports.py:965:                    ledger_skip = True
bridge/cursor-bridge/evaluate-reports.py:973:                        ledger_skip = True
bridge/cursor-bridge/evaluate-reports.py:981:                            ledger_skip = True
bridge/cursor-bridge/evaluate-reports.py:998:                                    ledger_skip = True
bridge/cursor-bridge/evaluate-reports.py:1028:                                            ledger_skip = True
bridge/cursor-bridge/evaluate-reports.py:1060:    if ledger_skip:
```

```text
git grep -n -F "read_failure_remedy(False)" -- bridge
bridge/cursor-bridge/evaluate-reports.py:931:        remedy = read_failure_remedy(False)
bridge/cursor-bridge/evaluate-reports.py:939:            remedy = read_failure_remedy(False)
bridge/cursor-bridge/evaluate-reports.py:961:                    remedy = read_failure_remedy(False)
bridge/cursor-bridge/evaluate-reports.py:967:                    remedy = read_failure_remedy(False)
bridge/cursor-bridge/evaluate-reports.py:975:                        remedy = read_failure_remedy(False)
bridge/cursor-bridge/evaluate-reports.py:983:                            remedy = read_failure_remedy(False)
bridge/cursor-bridge/evaluate-reports.py:1000:                                    remedy = read_failure_remedy(False)
bridge/cursor-bridge/evaluate-reports.py:1030:                                            remedy = read_failure_remedy(False)
```

```text
git grep -n -F "gh workflow run dependency-scan.yml --repo %s/%s" -- bridge
bridge/cursor-bridge/evaluate-reports.py:835:    rerun = "gh workflow run dependency-scan.yml --repo %s/%s" % (owner, repo)
bridge/cursor-bridge/evaluate-reports.py:949:                rerun = "gh workflow run dependency-scan.yml --repo %s/%s" % (owner, repo)
bridge/cursor-bridge/evaluate-reports.py:1037:                                            remedy = "gh workflow run dependency-scan.yml --repo %s/%s" % (owner, repo)
```

```text
git grep -n -F -e "if not scan_unreadable:" -e "not isinstance(runs_body, dict)" -e "not isinstance(all_runs, list)" -- bridge
bridge/cursor-bridge/evaluate-reports.py:963:                elif not isinstance(runs_body, dict):
bridge/cursor-bridge/evaluate-reports.py:971:                    if not isinstance(all_runs, list):
bridge/cursor-bridge/evaluate-reports.py:1010:                                if not scan_unreadable:
```

```text
git grep -n -w -e ledger_skip -e scan_unreadable -e scan_project -e classify_window_runs -e read_failure_remedy -e _validate_runs_list -- tests
```

(empty)

```text
git grep -n -F "dependency-scan.yml --repo %s" -- tests
```

(empty)

## Pytest (before edit, HEAD f03f1de)

```text
python -m pytest -p no:cacheprovider -q -rs tests/test_program_security_step.py tests/test_header_currency.py
........................................................................ [ 37%]
........................................................................ [ 75%]
................................................                         [100%]
192 passed in 46.91s
```

## Pytest (after last edit, HEAD f03f1de, uncommitted changes present)

```text
python -m pytest -p no:cacheprovider -q -rs tests/test_program_security_step.py tests/test_header_currency.py
........................................................................ [ 37%]
........................................................................ [ 75%]
................................................                         [100%]
192 passed in 47.52s
```

## Post-edit verification

```text
python tools/make-manifest.py
make-manifest: version 2026.11.12a, 148 files hashed, VERSION + MANIFEST.json written
```

```text
python tools/dump-cli.py --check
```

(empty output, exit 0)

```text
python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet
bridge-check: version 2026.11.12a (2026-11-22 18:10) at <Workspace>/bridge
bridge-check: 148 OK, 0 STALE, 0 MISSING, 0 EXTRA
RESULT: SOURCES MATCH bridge 2026.11.12a <Workspace>/bridge\cursor-bridge
```

```text
git diff --numstat -- bridge/cursor-bridge/VERSION
```

(empty)

```text
git diff --numstat -- bridge/cursor-bridge/evaluate-reports.py
59	91	bridge/cursor-bridge/evaluate-reports.py
```

## Acceptance criterion 4 greps (after edit)

```text
git grep -n -w ledger_skip -- bridge
```

(empty)

```text
git grep -n -F "read_failure_remedy(False)" -- bridge
bridge/cursor-bridge/evaluate-reports.py:1007:        remedy = read_failure_remedy(False)
```

```text
git grep -n -F "gh workflow run dependency-scan.yml --repo %s/%s" -- bridge
bridge/cursor-bridge/evaluate-reports.py:88:DEP_SCAN_RERUN = "gh workflow run dependency-scan.yml --repo %s/%s"
```

```text
git grep -n -F -e "if not scan_unreadable:" -e "not isinstance(runs_body, dict)" -e "not isinstance(all_runs, list)" -- bridge
```

(empty)

```text
git grep -n -F "scan_unreadable = True" -- bridge
bridge/cursor-bridge/evaluate-reports.py:1005:        scan_unreadable = True
```

## End state

```text
git status --short
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/evaluate-reports.py
```

```text
git diff --stat
 bridge/cursor-bridge/MANIFEST.json       |   4 +-
 bridge/cursor-bridge/evaluate-reports.py | 150 ++++++++++++-------------------
 2 files changed, 61 insertions(+), 93 deletions(-)
```

```text
git rev-parse HEAD
f03f1de611caced148ca0fddaf58892d86acc6ec
```

Working tree holds uncommitted changes at end (evaluate-reports.py and MANIFEST.json only).

## (a) `ledger_skip` redundant with `scan_unreadable`

Every assignment `ledger_skip = True` sat on the same branch as `scan_unreadable = True`, and `ledger_skip = False` was initialized alongside `scan_unreadable = False` with no other writers. The sole reader chose `update = None` when `ledger_skip` was true, which is exactly when a scan read had failed and `scan_unreadable` was true. Replacing `if ledger_skip` with `if scan_unreadable` preserves ledger skip semantics.

## (b) `if not scan_unreadable` always true in the for-loop else

The `for run in failures` loop runs only after `runs_err` is clear, so every earlier failed-read path was taken in a sibling branch of the nested `if`/`else` chain and never reached this loop. Inside the loop, `scan_unreadable` is set only in the `if fail:` branch immediately before `break`, which skips the loop's `else`. Any path that enters the `else` at line 1009 (old numbering) therefore still has `scan_unreadable` false; the guard was tautological and its body could run unconditionally one indent level out.

## (c) Shape checks redundant with `_validate_runs_list`

`_validate_runs_list` returns `"reply could not be parsed"` when its argument is not a `list` (lines 747–749). The removed `elif not isinstance(runs_body, dict)` and `if not isinstance(all_runs, list)` branches each appended `("runs list", "reply could not be parsed")`. Using `all_runs = runs_body.get("workflow_runs") if isinstance(runs_body, dict) else None` then `_validate_runs_list(all_runs)` yields the same message for a non-dict body, for a dict missing a list `workflow_runs`, and for a malformed list, because `bridge_env._gh_get` supplies a parsed JSON object when the GET succeeds so `.get` on a dict is the only use on the success path.

## (d) Failed reads still stop later reads

Control flow remains the nested `if`/`else`: a workflows failure leaves `failure` set without entering the runs branch; a runs failure does not enter the window classification or jobs loop; a jobs/log failure sets `failure` and `break`s so the loop `else` (standing and pending-failure handling) does not run; pending-failure jobs failure sets `failure` without setting `kind`/`remedy` for scanner paths. Only after the full scan branch structure does the single block set `scan_unreadable`, `kind`, `remedy`, and append `failure` to `read_failures`, then `_read_alerts` runs unchanged.

## Behaviour

The refactor only relocates duplicate assignments and deletes redundant predicates; it does not add or remove GitHub GETs, change tuple strings, or alter when `update` is `None`, so `tests/test_program_security_step.py` exercising R-097 through `main()` still sees the same outputs, exit codes, call order, ledger, and `_meta.last_extract` handling.

## Not changed (noted)

- `classify_window_runs` still unpacks unused `marker_at` and sets `advance_last` equal to `bool(completed)` (brief item (e)).
- The pending-failure branch still calls `_run_exit_code` a second time on `completed[-1]` after the failure loop may have already read that run (brief item (e)); removing it would change GitHub read count.
- Line 948's `enable` workflow text remains a separate inline format string.

## Assumed, not verified

Assumed, not verified: none.