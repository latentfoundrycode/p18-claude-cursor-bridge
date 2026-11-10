# REFAC-005 round-1 report

## Files changed

- `bridge/cursor-bridge/bridge_env.py`
- `bridge/cursor-bridge/session-start.py`
- `bridge/cursor-bridge/workflow-check.py`
- `bridge/cursor-bridge/diagram-check.py`
- `bridge/cursor-bridge/MANIFEST.json`
- `handoff/REFAC-005-r1-report.md`

`bridge/cursor-bridge/VERSION` appears in `git status --short` after `make-manifest.py` (content remains `2026.11.09a`; likely line-ending normalization). Per brief, reported here, not restored.

## Summary

REFAC-005 removed dead symbols and a bare alias from `bridge_env.py`, replaced session-start's unused `read_status` with `read_status_file` matching the inlined `main()` loop, dropped unreachable workflow-check logic after `status_workflow_line`'s problem sets, simplified a redundant branch in diagram-check `known_deviations`, and regenerated `MANIFEST.json` at version `2026.11.09a`; loop-guard.py was left untouched.

## Git at start

```
git status --short

(empty — clean working tree)

git rev-parse HEAD
c2f3ef2667a650ddbdf07c5335e9845faeb8015c
```

Uncommitted changes at start: no.

## Pre-edit grep checks (Requirement 1)

Command (per symbol):

```
git grep -n -e <name> -- . ":(exclude)run"
```

**parse_diagram_index_rows** — no caller in `bridge/`, `tests/`, or `docs/diagrams/`:

```
bridge/cursor-bridge/bridge_env.py:3094:def parse_diagram_index_rows(text):
docs/HARDENING.md:1802:... `bridge_env.parse_diagram_index_rows` is unused ...
handoff/REFAC-005.md:...
```

**_SCOPE_PAREN** — definition only in bridge:

```
bridge/cursor-bridge/bridge_env.py:332:_SCOPE_PAREN = "ScopeAgreementError"
docs/HARDENING.md:1791:...
handoff/...
```

**ScopeAgreementError** — in `bridge/` only at the constant string and class definition (lines 332, 3212); no `tests/` use:

```
bridge/cursor-bridge/bridge_env.py:332:...
bridge/cursor-bridge/bridge_env.py:3212:class ScopeAgreementError(ValueError):
...
```

**deviations_table** — one caller at `bridge_env.py:3114`:

```
bridge/cursor-bridge/bridge_env.py:3100:def deviations_table(text):
bridge/cursor-bridge/bridge_env.py:3114:    _hl, _orig, rows = deviations_table(text)
...
```

**read_status** — session-start definition only (no caller); loop-guard's `read_status` used by `tests/test_loop_guard.py:83`; `read_status_file` used by loop-guard `main()` line 595:

```
bridge/cursor-bridge/loop-guard.py:175:def read_status(cwd):
bridge/cursor-bridge/session-start.py:188:def read_status(cwd):
tests/test_loop_guard.py:83:        status = lg.read_status(str(cwd))
bridge/cursor-bridge/loop-guard.py:595:    status_path, status = read_status_file(cwd)
...
```

**status_workflow_line** problem lists (item 4): confirmed in code — `[p0]` via bad prefix; `[]` on successful parse; `[p2]` duplicate part; `[p1]` traits marker; `[p2,p1]` both; `[p3]` empty name; `[p2,p3]` duplicate + empty name. After `if p0 in line_problems or p1 in line_problems: continue`, the only two-item list remaining is `[p2,p3]`, which includes `p3`.

## Items

| Item | Status |
|------|--------|
| 1a | Done — deleted `parse_diagram_index_rows` |
| 1b | Done — deleted `_SCOPE_PAREN` |
| 1c | Done — deleted `ScopeAgreementError` |
| 1d | Done — deleted `deviations_table`; `parse_deviation_keys` calls `_first_markdown_table` |
| 2 | Done — `read_status_file(cwd)`; `main()` calls it |
| 3 | Not applicable — loop-guard `read_status` and `read_status_file` both have callers; file not edited |
| 4 | Done — removed lines 701-702 in `workflow-check.py` |
| 5 | Done — `elif hdr is not None` → `else` |
| 6 | Done — manifest regenerated |

Post-edit: `git grep` under `bridge/` finds none of `parse_diagram_index_rows`, `_SCOPE_PAREN`, `ScopeAgreementError`, `deviations_table`, `len(line_problems) > 1`, or `elif hdr is not None`. `session-start.py` has `read_status_file` at definition and `main()` call only.

## Pytest (before edit)

```
python -m pytest -p no:cacheprovider -q -rs tests/test_header_reader.py tests/test_header_tables.py tests/test_header_tables_r2.py tests/test_header_status.py tests/test_session_start.py tests/test_session_start_module.py tests/test_loop_guard.py tests/test_workflow_check.py tests/test_workflows_line_check.py tests/test_diagram_check.py tests/test_diagram_check_a4.py tests/test_header_currency.py tests/test_header_plan.py
```

```
1910 passed, 8 skipped in 139.24s (0:02:19)
```

## Pytest (after edit)

Same command as above.

```
1910 passed, 8 skipped in 151.72s (0:02:31)
```

## Post-edit verification commands

```
python tools/make-manifest.py --version 2026.11.09a
```

```
make-manifest: version 2026.11.09a, 145 files hashed, VERSION + MANIFEST.json written
```

```
python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet
```

```
bridge-check: version 2026.11.09a (2026-11-10 20:42) at <the Workspace>\bridge
bridge-check: 145 OK, 0 STALE, 0 MISSING, 0 EXTRA
RESULT: SOURCES MATCH bridge 2026.11.09a
```

```
python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge
```

```
windowless-check: 35 file(s) scanned, 0 FAIL, 0 NOTE
```

```
python bridge/cursor-bridge/refactor-check.py HEAD --max-lines 400
```

```
base: HEAD | lane: production | files: 5 | changed lines: 47 (budget 400) | allowed test files: 0
PURE: no test change, no CHANGES.md entry, within size budget.
```

## Git at end

```
git status --short
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/VERSION
 M bridge/cursor-bridge/bridge_env.py
 M bridge/cursor-bridge/diagram-check.py
 M bridge/cursor-bridge/session-start.py
 M bridge/cursor-bridge/workflow-check.py
?? handoff/REFAC-005-r1-report.md
```

```
git diff --stat
 bridge/cursor-bridge/MANIFEST.json     | 10 +++++-----
 bridge/cursor-bridge/bridge_env.py     | 18 +-----------------
 bridge/cursor-bridge/diagram-check.py  |  2 +-
 bridge/cursor-bridge/session-start.py  | 15 ++++-----------
 bridge/cursor-bridge/workflow-check.py |  2 --
 5 files changed, 11 insertions(+), 36 deletions(-)
```

```
git rev-parse HEAD
c2f3ef2667a650ddbdf07c5335e9845faeb8015c
```

Uncommitted changes at end: yes (this increment only).

## Behaviour identical

Every edit removes unused definitions, inlines equivalent logic (`read_status_file` matches the former loop byte-for-byte on paths and encoding), deletes a branch that cannot run given `status_workflow_line`'s return sets, or swaps a tautological `elif` for `else` with the same body; callers and public signatures outside the listed sites are unchanged.

## Noticed but not changed

- `diagram_index_body_table` remains a bare alias of `_first_markdown_table` (noted in `docs/HARDENING.md`; out of scope for this brief).
- `bridge/cursor-bridge/VERSION` listed modified by git after manifest rewrite though content is still `2026.11.09a`.

## Assumed, not verified

Assumed, not verified: none.
