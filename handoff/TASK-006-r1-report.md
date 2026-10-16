# TASK-006 round 1 report

## Files changed

- `bridge/cursor-bridge/workflow-check.py` (created)
- `.github/workflows/tests.yml` (one step at the end of the `tests` job)
- `bridge/cursor-bridge/MANIFEST.json` (new `cursor-bridge/workflow-check.py` entry and the `generated` stamp)
- `bridge/cursor-bridge/VERSION` (rewritten by `tools/make-manifest.py`; `git diff` shows no content change; `git status` still lists it)
- `docs/BUILDER_NOTES.md` (one dated line on the heading test below)
- `handoff/TASK-006-r1-report.md` (this report)

## Summary

`workflow-check.py` checks conditional workflows under each root's `types/` and `traits/` and every `--status` file's `Workflows:` lines against the open list and the extension-point registry, prints `FAIL` / `FLAG` / `RESULT` lines, and is invoked from the bridge programs CI job with no secret and no status file; the manifest was regenerated after the last edit under `bridge/`.

## Contradiction

`tests/test_workflow_check.py::test_r014_registry_heading_missing` cannot pass without breaking the brief. The test replaces the first occurrence of the string `## Extension points` in `bridge/cursor-bridge/workflow/extension-points.md`. That occurrence is the prose citation on the "How this file is read" line (line 9), not the heading. After the replacement the heading line `## Extension points` is still line 37, the Extension points table is intact, and the check exits 0 with `RESULT: OK`. Requirement 3 and the registry's reading rule say exit 2 when the heading is missing, and that the program reads the first table after the heading line and nothing else in the file. Removing that heading line (not the prose citation) does exit 2 with `ERROR: ...: missing heading ## Extension points` and `RESULT: not checked`. The test was not edited.

## Commands

1. `python bridge/cursor-bridge/workflow-check.py bridge/cursor-bridge/workflow tests/fixtures/workflows/pass` — exit 0

```
RESULT: OK
```

2. `python bridge/cursor-bridge/workflow-check.py --help` — exit 0. The text names intake, release, and calibration, R-014 and R-033, and the finding codes `(a)` through `(f)`, `(set)`, `(kind)`, `(unknown)`, `(form)`, and `FLAG (trait)`.

3. `python -m pytest tests/test_workflow_check.py -q` — exit 1. 58 passed, 1 failed: `test_r014_registry_heading_missing` (`assert 0 == 2`, stdout `RESULT: OK`). See Contradiction.

4. `python -m pytest tests -q` — exit 1. `2 failed, 1009 passed, 20 skipped`. Failures: `test_r002_workflow_is_the_pinned_one` (`R-002: the workflow differs from the pinned one`) and `test_r014_registry_heading_missing`. This run was after the first `make-manifest.py`, so the source-tree manifest test passed. Step 6 then refreshed `generated` to `2026-10-16 20:40`; `bridge-check.py --sources` matched that stamp. The suite was not started again after that stamp.

5. `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge` — exit 0

```
windowless-check: 30 file(s) scanned, 0 FAIL, 0 NOTE
```

6. `python tools/make-manifest.py` — exit 0

```
make-manifest: version 2026.10.11d, 107 files hashed, VERSION + MANIFEST.json written
```

`python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` — exit 0

```
bridge-check: version 2026.10.11d (2026-10-16 20:40) at E:\p18-claude-cursor-bridge\Workspace\bridge
bridge-check: 107 OK, 0 STALE, 0 MISSING, 0 EXTRA
RESULT: SOURCES MATCH bridge 2026.10.11d
```

7. `git diff --stat` — exit 0. Untracked files are omitted; `git status --short` also shows `?? bridge/cursor-bridge/workflow-check.py` and `?? handoff/TASK-006-r1-report.md`, and lists `VERSION` with no diff hunk.

```
 .github/workflows/tests.yml        | 2 ++
 bridge/cursor-bridge/MANIFEST.json | 3 ++-
 docs/BUILDER_NOTES.md              | 2 ++
 3 files changed, 6 insertions(+), 1 deletion(-)
```

## Assumed, not verified

- A `## ` line is a change heading only when its first word is exactly `Add`, `Set`, or `Replace` · the definition says that, while the same requirement lists `## Adds at x` as a `form` example, and no fixture uses `Adds` · a fixture or ruling on `## Adds at x`.
- A fence is a line whose first three characters are backticks · the brief says lines starting with three backticks, and the pass fixture's fences start at column 0 · a heading inside an indented fence.
- A change heading with trailing spaces is `form` · the four forms are exact and the line is not stripped · a passing heading with one trailing space.
- The text after `; traits: ` is stripped, so `none` with a trailing space counts as no traits · the fixtures have no trailing space, and stripping avoids a false `unknown` on a wrapped line · a status line that ends with `none `.
- In the head, a Workflow name is tested before a Sub-workflow name and a trait Name · the brief says workflow names count as product types, and neither open list here has a name in two tables · a fixture whose Workflow name equals a trait Name.
- An unknown head name that leaves no product type also produces `FAIL (e)` · Requirement 4's `e` includes a part with no product type, and `unknown-name.md` only requires the `unknown` line, which is present alongside `e` · the intended finding count for that fixture.
- A directory deeper than `types/<type key>/` is itself `FAIL (form)`, and so is each file under it · Requirement 6 names a deeper path as `form`, and `form-third-level` only requires one line whose path starts with that directory · whether an empty third-level directory should fail.
- After one pair of enclosing backticks is removed from a delivery-kind line, spaces inside that pair are kept · Requirement 9 says strip surrounding whitespace and at most one backtick pair, and the pass fixture is `` `host-installation` `` with no inner spaces · the value `` ` host-installation ` ``.
- `types/<t>.md` counts as existing when `os.path.isfile` says so · Requirement 4 says the type workflow exists in the same root, and this run is on Windows, where that check is case-insensitive · the same tree on a case-sensitive filesystem with a differently cased filename.
