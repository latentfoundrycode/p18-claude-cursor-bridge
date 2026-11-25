# TASK-086b round 1 report

## Files changed

- `bridge/cursor-bridge/bridge-run.py`
- `bridge/cursor-bridge/MANIFEST.json`
- `docs/cli-reference.json`
- `docs/CLI_REFERENCE.md`

## Summary

The launcher's `review_family_refusal` now calls `roster-check.py`'s `built_families` for the full branch built set (known, empty, unknown, and unreadable), fails closed on roster load errors, and applies the deviation exception in `review_launch_refusal`; every builder row gains `start_commit` and `clean` via `_git_launch_state`, and `write_log` starts a new line when the record's last byte is not a line feed. All 102 supervisor acceptance tests in `tests/test_improve_roster_launch.py` and `tests/test_hotfix25a_roster_launcher.py` pass unchanged, along with the Done regression slices.

## R1–R11

- **R1:** `review_family_refusal` (lines 2601–2651) calls `_built_set_at_launch` → `built_families`; known-set refusals name every family in the set.
- **R2:** Same function, unknown branch (lines 2629–2651); roster builders, parsing rows, or resolved stand-in; example: `bridge-run: refused - Review B grok-4.7-high is of the xai family, which built this change (the built set is unknown, TASK-002-r1-report.md): rebuild it ... resolve the roster again`.
- **R3:** Unreadable branch (lines 2615–2618); example: `bridge-run: refused - Review B gpt-5.6-sol-high cannot run: the branch's built set cannot be read (detached); resolve the roster again`.
- **R4:** `_roster_for_review` (lines 1225–1233) and early return in `review_family_refusal` (2607–2609); example: `bridge-run: refused - the roster program lacks built_families; run bridge-check.py on the installed tree`.
- **R5:** Family refusals through `_ascii_refusal` at the call site (line 3449); model names beyond ASCII backslash-escaped.
- **R6:** `review_launch_refusal` (1399–1418) with `_deviation_allows_builder_review` (1323–1354); example: `bridge-run: refused - review launch on the roster builder model (composer-2.5) is refused; resolve the roster again`.
- **R7:** `write_log` (1044–1059) inserts `\n` before append when the last byte is not a line feed.
- **R8:** `main` entry build (3568–3573) sets `start_commit` and `clean` from `_git_launch_state` (1237–1281) for `kind == "builder"`; example row keys: `"start_commit": "<40-hex HEAD>", "clean": true, "head": "cursor-agent"`.
- **R9:** `clean` ignores only `docs/ROSTER.resolved.json` in porcelain (`test_r9_step_3b_a_rebuild_after_the_resolve_reads_no_rebuild` passes).
- **R10:** `_git_launch_state` git calls use `NO_WINDOW`, `bridge_env.GIT_TIMEOUT`, `errors="replace"`.
- **R11:** No new dependencies; MANIFEST and CLI reference regenerated; `head` unchanged on rows; non-ASCII added only via `_ascii_refusal` backslashreplace in refusal paths.

## Scratch tests

no scratch test file

## Mutation code points (M1–M12)

| Label | Function / lines | Expected test id |
|-------|------------------|------------------|
| M1 | `_git_launch_state` 1273–1279 | `test_r8_clean_reads_the_tree_and_the_index_apart_from_the_resolved_roster[unstaged-change]` |
| M2 | `_git_launch_state` 1276–1277 | `test_r8_clean_reads_the_tree_and_the_index_apart_from_the_resolved_roster[resolved-modified]` |
| M3 | `review_family_refusal` 2621–2628 | `test_r1_a_branch_built_by_two_families_refuses_a_reviewer_of_either` |
| M4 | `_deviation_allows_builder_review` 1331–1332 | `test_r6_the_builder_model_is_refused_unless_the_entry_matches[another-branch]` |
| M5 | `_deviation_allows_builder_review` 1326–1327 | `test_r6_the_builder_model_is_refused_unless_the_entry_matches[another-model]` |
| M6 | `_load_deviation` / `_deviation_allows_builder_review` 1284–1324 | `test_r6_the_builder_model_is_refused_unless_the_entry_matches[deviation-a-list]` |
| M7 | `_deviation_allows_builder_review` 1337–1338 | `test_r6_the_builder_model_is_refused_unless_the_entry_matches[unknown-set]` |
| M8 | `_deviation_allows_builder_review` 1347–1353 | `test_r6_the_builder_model_is_refused_unless_the_entry_matches[built-differs-by-more]` |
| M9 | `review_family_refusal` 2621–2624 (no skip) | `test_r6_the_alternate_still_meets_the_family_refusal` |
| M10 | `review_family_refusal` 2615–2618 | `test_r3_a_detached_head_refuses_every_review` |
| M11 | `review_family_refusal` 2607–2609 | `test_r4_a_roster_program_that_cannot_be_loaded_refuses_the_review[raises]` |
| M12 | `write_log` 1053–1057 | `test_r7_a_row_after_a_torn_last_line_begins_a_new_line` |

## Missing acceptance cases

none

## Commands and output

### Step 1 — `git status --short`

```
```

### Step 2 — checkpoint pytest

```
62 failed, 40 passed in 56.43s
```

Failing ids included all parametrized `test_r6_the_builder_model_is_refused_unless_the_entry_matches[...]` cases, `test_r1_a_branch_built_by_two_families_refuses_a_reviewer_of_either`, R2/R3/R4/R5/R6/R7/R8/R9/R10 groups red on the checkpoint, and `test_the_launcher_refuses_a_review_b_of_a_family_whose_run_no_rebuild_dropped`.

### Step 3 — `python tools/dump-cli.py` then `python tools/dump-cli.py --check`

```
```

(exit code 0 for both)

### Step 4 — `python tools/make-manifest.py`

```
make-manifest: version 2026.11.24a, 148 files hashed, VERSION + MANIFEST.json written
```

### Step 5 — `git status --short`

```
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/bridge-run.py
 M docs/CLI_REFERENCE.md
 M docs/cli-reference.json
```

(`bridge/cursor-bridge/VERSION` not listed.)

### Step 6 — acceptance pytest

```
102 passed in 67.99s (0:01:07)
```

### Step 7 — regression pytest slice

```
494 passed, 4 skipped in 492.39s (0:08:12)
```

### Step 8 — roster and dump-cli pytest slice

```
280 passed, 3 skipped in 237.74s (0:03:57)
```

### Step 9 — `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`

```
RESULT: SOURCES MATCH bridge 2026.11.24a <Workspace>\bridge\cursor-bridge
```

### Step 10 — `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks`

```
windowless-check: 41 file(s) scanned, 0 FAIL, 0 NOTE
```

### Step 11 — `git diff --stat HEAD`

```
 bridge/cursor-bridge/MANIFEST.json |   4 +-
 bridge/cursor-bridge/bridge-run.py | 229 ++++++++++++++++++++++++++++++++++---
 2 files changed, 217 insertions(+), 16 deletions(-)
```

### Step 12 — non-ASCII in `bridge-run.py` diff

No non-ASCII characters were added in the diff (refusal paths use `_ascii_refusal` at the family-refusal call site).

### Step 13 — `claude --version`

```
claude: command not found
```

### Step 14 — `git rev-parse HEAD` and `git status --short`

```
1335cb59ecf42e6b43f932afbbfefa5d33113214
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/bridge-run.py
 M docs/CLI_REFERENCE.md
 M docs/cli-reference.json
```

Commit `1335cb59ecf42e6b43f932afbbfefa5d33113214`; working tree held uncommitted changes at step 14. No `tests/test_task086b_scratch_` file; `bridge/cursor-bridge/VERSION` not listed.

## Assumed, not verified

- `git status --porcelain` lists `docs/ROSTER.resolved.json` under the same path shape in worktrees as in the launch folder; the filter uses that exact slash form.
- Ignored content under `run/` never appears in porcelain on the suite's scratch repos, so it does not affect `clean`.
- `git rev-parse HEAD` on the fixture branches always returns a 40- or 64-character hex object name when the repo is usable.
- `built_families(..., branch=branch_of(ws), cwd=workspace_of(...))` matches the branch the resolve uses for the same launch.