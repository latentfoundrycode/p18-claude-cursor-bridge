# TASK-086b round 2 report

## Files changed

- `bridge/cursor-bridge/bridge-run.py`
- `bridge/cursor-bridge/MANIFEST.json`
- `docs/cli-reference.json`
- `docs/CLI_REFERENCE.md`

## Summary

Round 2 closes the eight security-review gaps in `bridge-run.py`: the unknown-set family refusal always unions parsing-row families with roster or resolved-builder stand-in families and fails closed on helper exceptions; `built_families` errors and non-object roster profiles refuse reviews with `bridge-check.py` wording; deviation no longer skips the brief-name check; every unknown cause is named; `write_log` treats only a line feed as a complete line; `clean` uses porcelain `-z` including rename source paths; git status failure after a good `rev-parse` nulls `start_commit`; and the built set is read once per launch via a log-mtime cache. Removed `_resolved_builder_model`. All 112 supervisor acceptance tests and the Done regression slices pass unchanged.

## Requirements (round 2 numbering)

- **B1 (R2):** `review_family_refusal` (2663–2689) unions `roster._parsing_row_families` (2665–2667) with roster builder families or `roster_builder_model` stand-in (2670–2683); example: `bridge-run: refused - Review B grok-4.7-medium is of the xai family, which built this change (the built set is unknown, TASK-002-r1-report.md): rebuild it with the builder in docs/ROSTER.resolved.json first (step 3b; roster-check prints REBUILD); resolve the roster again`.
- **B2 (R6):** `review_launch_refusal` (1434–1445) no longer returns after `_deviation_allows_builder_review`; brief check at 1443–1445 still refuses; example: `bridge-run: refused - a review launch must not name a brief (TASK-001.md); only the launcher counts builder briefs`.
- **B3 (R4/R2):** `_read_roster_json` (1224–1225) rejects non-object profile entries; `_built_set_at_launch` (1337–1339) maps `built_families` exceptions to `bset_error`; `review_family_refusal` (2643–2646); example: `bridge-run: refused - Review B gpt-5.6-sol-high cannot run: the built set could not be read (broken on purpose); run bridge-check.py on the installed tree`.
- **S1 (R8/R10):** `_git_launch_state` (1273–1274) returns `(None, False)` when `git status` exits non-zero after a good `rev-parse`.
- **S2 (R8):** `_git_launch_state` (1264–1298) uses `git status --porcelain -z` and checks every path plus rename/copy source paths against `docs/ROSTER.resolved.json` only.
- **S3 (R2/R5):** `_unknown_cause_text` (1348–1349) joins every unknown-cause label with `, `; example refusal includes both `TASK-002-r1-report.md` and `runs.jsonl` in the unknown clause.
- **S4 (R7):** `write_log` (1055–1063) begins a new line only when the last byte is not `b"\n"`; `newline="\n"` on append (1052).
- **S5 (R1/R6):** `_built_set_at_launch` (1319–1341) caches by `(folder, ws, branch, log mtime)` so `built_families` runs at most once per launch.
- **Tidy:** `_resolved_builder_model` removed; callers use `roster_builder_model` directly.

## Scratch tests

no scratch test file

## Mutation code points (M1–M12 and M14–M20)

| Label | Function / lines | Expected test id |
|-------|------------------|------------------|
| M1 | `_git_launch_state` 1295–1297 | `test_r8_clean_reads_the_tree_and_the_index_apart_from_the_resolved_roster[unstaged-change]` |
| M2 | `_git_launch_state` 1295–1297 | `test_r8_clean_reads_the_tree_and_the_index_apart_from_the_resolved_roster[resolved-modified]` |
| M3 | `review_family_refusal` 2653–2660 | `test_r1_a_branch_built_by_two_families_refuses_a_reviewer_of_either` |
| M4 | `_deviation_allows_builder_review` 1360–1361 | `test_r6_the_builder_model_is_refused_unless_the_entry_matches[another-branch]` |
| M5 | `_deviation_allows_builder_review` 1356–1357 | `test_r6_the_builder_model_is_refused_unless_the_entry_matches[another-model]` |
| M6 | `_load_deviation` / `_deviation_allows_builder_review` 1304–1355 | `test_r6_the_builder_model_is_refused_unless_the_entry_matches[deviation-a-list]` |
| M7 | `_deviation_allows_builder_review` 1367–1368 | `test_r6_the_builder_model_is_refused_unless_the_entry_matches[unknown-set]` |
| M8 | `_deviation_allows_builder_review` 1377–1381 | `test_r6_the_builder_model_is_refused_unless_the_entry_matches[built-differs-by-more]` |
| M9 | `review_family_refusal` 2653–2656 (no skip) | `test_r6_the_alternate_still_meets_the_family_refusal` |
| M10 | `review_family_refusal` 2647–2650 | `test_r3_a_detached_head_refuses_every_review` |
| M11 | `review_family_refusal` 2635–2637 | `test_r4_a_roster_program_that_cannot_be_loaded_refuses_the_review[raises]` |
| M12 | `write_log` 1055–1063 | `test_r7_a_row_after_a_torn_last_line_begins_a_new_line` |
| M14 | `review_family_refusal` 2665–2684 | `test_r2_parsing_rows_count_where_the_roster_file_cannot_be_read[absent]` |
| M15 | `review_launch_refusal` 1438–1442 | `test_r6_a_brief_named_in_a_review_launch_stays_refused[composer-2.5]` |
| M16 | `_built_set_at_launch` 1337–1339; `review_family_refusal` 2643–2646 | `test_r4_a_roster_program_whose_built_set_raises_refuses_every_review` |
| M17 | `_unknown_cause_text` 1348–1349 | `test_r2_the_refusal_names_each_unknown_cause` |
| M18 | `write_log` 1058–1059 | `test_r7_a_last_byte_of_a_carriage_return_is_a_torn_line` |
| M19 | `review_family_refusal` 2676–2683 | `test_r2_a_roster_file_naming_no_builder_family_lets_the_resolved_builder_stand_in` |
| M20 | `_git_launch_state` 1291–1294 | `test_r8_a_staged_rename_into_the_resolved_roster_is_not_clean` |

## Missing acceptance cases

none

## `claude --version`

```
--: line 1: claude: command not found
```

## Commands and output

### Step 1 — `git status --short`

```
(no output)
```

### Step 2 — checkpoint pytest (before edits)

```
9 failed, 103 passed in 73.06s (0:01:13)
```

Failing ids:

```
test_r2_parsing_rows_count_where_the_roster_file_cannot_be_read[absent]
test_r2_parsing_rows_count_where_the_roster_file_cannot_be_read[malformed]
test_r2_the_refusal_names_each_unknown_cause
test_r2_a_roster_file_naming_no_builder_family_lets_the_resolved_builder_stand_in
test_r4_a_roster_program_whose_built_set_raises_refuses_every_review
test_r4_a_roster_file_of_the_wrong_shape_never_opens_a_review_of_the_building_family[a-number-and-null]
test_r6_a_brief_named_in_a_review_launch_stays_refused[composer-2.5]
test_r7_a_last_byte_of_a_carriage_return_is_a_torn_line
test_r8_a_staged_rename_into_the_resolved_roster_is_not_clean
```

### Step 3 — `python tools/dump-cli.py` then `python tools/dump-cli.py --check`

```
(no output)
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

(`bridge/cursor-bridge/VERSION` not listed; `git restore` not run)

### Step 6 — acceptance pytest after edits

```
112 passed in 73.11s (0:01:13)
```

### Step 7 — regression slice 1

```
494 passed, 4 skipped in 500.79s (0:08:20)
```

### Step 8 — regression slice 2

```
280 passed, 3 skipped in 242.28s (0:04:02)
```

### Step 9 — `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`

```
bridge-check: version 2026.11.24a (2026-11-25 16:06) at <Workspace>/bridge
bridge-check: 148 OK, 0 STALE, 0 MISSING, 0 EXTRA
RESULT: SOURCES MATCH bridge 2026.11.24a <Workspace>/bridge/cursor-bridge
```

### Step 10 — `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks`

```
windowless-check: 41 file(s) scanned, 0 FAIL, 0 NOTE
```

### Step 11 — `git diff --stat HEAD`

```
 bridge/cursor-bridge/MANIFEST.json |   4 +-
 bridge/cursor-bridge/bridge-run.py | 125 ++++++++++++++++++++++++-------------
 2 files changed, 83 insertions(+), 46 deletions(-)
```

(`docs/cli-reference.json` and `docs/CLI_REFERENCE.md` were updated by dump-cli but appear only in working tree alongside the above; after regeneration they match MANIFEST.)

### Step 12 — non-ASCII in `bridge-run.py` diff

No non-ASCII characters were added in `bridge-run.py`; refusal strings remain ASCII via existing `_ascii_refusal` at the call site.

### Step 13 — `claude --version`

```
--: line 1: claude: command not found
```

### Step 14 — `git rev-parse HEAD` and `git status --short`

```
f8ea0e3b9974cb8bc13c9cc8692aa9cc4a0fec7d
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/bridge-run.py
 M docs/CLI_REFERENCE.md
 M docs/cli-reference.json
```

Results above are for commit `f8ea0e3b9974cb8bc13c9cc8692aa9cc4a0fec7d` with uncommitted changes listed in step 14. No `tests/test_task086b_scratch_` file. `bridge/cursor-bridge/VERSION` not listed.

## Assumed, not verified

Assumed, not verified: none