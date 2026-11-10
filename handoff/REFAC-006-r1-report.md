# REFAC-006 r1 report

## Files changed

- `bridge/cursor-bridge/conformance-check.py`
- `bridge/cursor-bridge/completion-check.py`
- `bridge/cursor-bridge/MANIFEST.json`
- `bridge/cursor-bridge/VERSION` (rewritten by make-manifest with LF line ending; left modified, reported below)
- `handoff/REFAC-006-r1-report.md`

## Summary

REFAC-006 deduplicated the Development data verdict in `conformance-check.py` via a single `dev_ok` assignment and one OK/MISSING pair, and removed the second plan read and second `plan_header_findings` pass in `completion-check.py` by caching headed plan text in `headed_texts` during the first loop; the manifest was regenerated at version `2026.11.09a` and all listed verification commands passed.

## Items

### Item 1 — done

Consolidated lines 1288–1296 in `conformance-check.py` to the `dev_ok` conditional expression plus one `if dev_ok` / `else` with byte-identical `add(...)` strings.

### Item 2 — done

Added `headed_texts`, append on headed plans in the first loop, and the disagreement loop iterates `headed_texts` only.

### Item 3 — done

Ran `python tools/make-manifest.py --version 2026.11.09a` and `bridge-check`; `RESULT: SOURCES MATCH bridge 2026.11.09a`.

## Requirements 1 — grep evidence

### Before edit

```text
$ git grep -n -e inventory_development_data -e inv_dev_from_header -- bridge/cursor-bridge/conformance-check.py
bridge/cursor-bridge/conformance-check.py:1243:    inv_dev_from_header = None
bridge/cursor-bridge/conformance-check.py:1249:        and hasattr(bridge_env, "inventory_development_data")
bridge/cursor-bridge/conformance-check.py:1266:            inv_dev_from_header = inv_hdr.get("development_data", "")
bridge/cursor-bridge/conformance-check.py:1288:            if inv_dev_from_header is not None:
bridge/cursor-bridge/conformance-check.py:1289:                if inv_dev_from_header:
bridge/cursor-bridge/conformance-check.py:1293:            elif bridge_env.inventory_development_data(inv_body_for_dev):
```

Confirmed: `inv_dev_from_header` assigned at 1243 and 1266; `inventory_development_data` called once at 1293 as `elif` condition.

```text
$ git grep -n -e plan_header_findings -e plan_r_ids_outside_headers -e headed_texts -- bridge/cursor-bridge/completion-check.py
bridge/cursor-bridge/completion-check.py:207:            fatal, _, hdr = bridge_env.plan_header_findings(p, text, None)
bridge/cursor-bridge/completion-check.py:225:                fatal, _, hdr = bridge_env.plan_header_findings(p, text, None)
bridge/cursor-bridge/completion-check.py:228:                for rid in bridge_env.plan_r_ids_outside_headers(text):
```

Confirmed: `plan_header_findings` at 207 and 225; `plan_r_ids_outside_headers` at 228; `headed_texts` not present.

### After edit

```text
$ git grep -n -e inventory_development_data -e inv_dev_from_header -- bridge/cursor-bridge/conformance-check.py
bridge/cursor-bridge/conformance-check.py:1243:    inv_dev_from_header = None
bridge/cursor-bridge/conformance-check.py:1249:        and hasattr(bridge_env, "inventory_development_data")
bridge/cursor-bridge/conformance-check.py:1266:            inv_dev_from_header = inv_hdr.get("development_data", "")
bridge/cursor-bridge/conformance-check.py:1288:            dev_ok = bool(inv_dev_from_header) if inv_dev_from_header is not None else bridge_env.inventory_development_data(inv_body_for_dev)
```

```text
$ git grep -n -e plan_header_findings -e plan_r_ids_outside_headers -e headed_texts -- bridge/cursor-bridge/completion-check.py
bridge/cursor-bridge/completion-check.py:205:        headed_texts = []
bridge/cursor-bridge/completion-check.py:208:            fatal, _, hdr = bridge_env.plan_header_findings(p, text, None)
bridge/cursor-bridge/completion-check.py:214:                headed_texts.append(text)
bridge/cursor-bridge/completion-check.py:225:            for text in headed_texts:
bridge/cursor-bridge/completion-check.py:226:                for rid in bridge_env.plan_r_ids_outside_headers(text):
```

## Pytest (before edit)

```text
$ python -m pytest -p no:cacheprovider -q -rs tests/test_conformance_check.py tests/test_conformance_check_a4.py tests/test_conformance_windowless.py tests/test_b2_least_confident.py tests/test_completion_check.py tests/test_bug038.py tests/test_header_tables.py tests/test_header_tables_r2.py tests/test_header_plan.py tests/test_header_plan_r2.py tests/test_header_plan_r3.py tests/test_header_status.py tests/test_header_currency.py
.................................................................s.s.... [ 13%]
........................................................................ [ 27%]
........................................................................ [ 40%]
........................................................................ [ 54%]
........................................................................ [ 67%]
........................................................................ [ 81%]
........................................................................ [ 94%]
.............................                                            [100%]
=========================== short test summary info ===========================
SKIPPED [1] tests\test_conformance_windowless.py:526: creating a file symbolic link needs a privilege here
SKIPPED [1] tests\test_conformance_windowless.py:551: Windows collapses `..` before it follows a link
531 passed, 2 skipped in 98.21s (0:01:38)
```

## Pytest (after edit)

```text
$ python -m pytest -p no:cacheprovider -q -rs tests/test_conformance_check.py tests/test_conformance_check_a4.py tests/test_conformance_windowless.py tests/test_b2_least_confident.py tests/test_completion_check.py tests/test_bug038.py tests/test_header_tables.py tests/test_header_tables_r2.py tests/test_header_plan.py tests/test_header_plan_r2.py tests/test_header_plan_r3.py tests/test_header_status.py tests/test_header_currency.py
.................................................................s.s.... [ 13%]
........................................................................ [ 27%]
........................................................................ [ 40%]
........................................................................ [ 54%]
........................................................................ [ 67%]
........................................................................ [ 81%]
........................................................................ [ 94%]
.............................                                            [100%]
=========================== short test summary info ===========================
SKIPPED [1] tests\test_conformance_windowless.py:526: creating a file symbolic link needs a privilege here
SKIPPED [1] tests\test_conformance_windowless.py:551: Windows collapses `..` before it follows a link
531 passed, 2 skipped in 96.22s (0:01:36)
```

## Post-edit verification

### make-manifest

```text
$ python tools/make-manifest.py --version 2026.11.09a
make-manifest: version 2026.11.09a, 145 files hashed, VERSION + MANIFEST.json written
```

### bridge-check

```text
$ python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet
bridge-check: version 2026.11.09a (2026-11-10 20:56) at <the Workspace>/bridge
bridge-check: 145 OK, 0 STALE, 0 MISSING, 0 EXTRA
RESULT: SOURCES MATCH bridge 2026.11.09a
```

### windowless-check

```text
$ python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge
windowless-check: 35 file(s) scanned, 0 FAIL, 0 NOTE
```

### refactor-check

```text
$ python bridge/cursor-bridge/refactor-check.py HEAD --max-lines 400
base: HEAD | lane: production | files: 4 | changed lines: 22 (budget 400) | allowed test files: 0
PURE: no test change, no CHANGES.md entry, within size budget.
```

## Git at start

```text
$ git status --short
(empty)

$ git rev-parse HEAD
0723dc2ac9146a1f2a2c486cf7b3600ef99c4f2c
```

Working tree was clean at start (no uncommitted changes).

## Git at end

```text
$ git status --short
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/VERSION
 M bridge/cursor-bridge/completion-check.py
 M bridge/cursor-bridge/conformance-check.py
?? handoff/REFAC-006-r1-report.md

$ git diff --stat
 bridge/cursor-bridge/MANIFEST.json        | 6 +++---
 bridge/cursor-bridge/completion-check.py  | 8 +++-----
 bridge/cursor-bridge/conformance-check.py | 8 ++------
 3 files changed, 8 insertions(+), 14 deletions(-)

$ git rev-parse HEAD
0723dc2ac9146a1f2a2c486cf7b3600ef99c4f2c
```

Working tree holds uncommitted changes. `bridge/cursor-bridge/VERSION` shows as modified (make-manifest LF line ending); left as written.

## Behaviour identical

The Development data branch still uses the header value when present (`bool(inv_dev_from_header)` for OK versus empty for MISSING) and calls `inventory_development_data` only when the header field was not supplied, with the same OK and MISSING messages; the header-disagreement pass still walks each headed plan in original glob order with the same `plan_r_ids_outside_headers` logic and the same `HEADER DISAGREES: satisfies` outcome, using the text already read in the first pass rather than re-reading files mid-run (the brief's undefended concurrent-edit case unchanged).

## Noticed, not changed

Nothing beyond the scoped duplicates; `VERSION` LF-only diff from make-manifest is expected and was not reverted.

## Assumed, not verified

Assumed, not verified: none.
