# TASK-086a round 1 report

## Files changed

- `bridge/cursor-bridge/roster-check.py`
- `bridge/cursor-bridge/MANIFEST.json` (regenerated)
- `docs/cli-reference.json` (regenerated)
- `docs/CLI_REFERENCE.md` (regenerated)

## Summary

`roster-check.py` now reads the branch built-family set from `runs.jsonl` via `built_families()`, applies the clean-rebuild drop rule, handles unknown and cannot-read states, resolves profiles by the design ten-row table including `review_b_alt` and DEVIATION, adds `--repair-record` and `--review-alt <reason>`, and keeps `built_by()` unchanged for the launcher.

## Requirements (R1-R16)

- R1: `built_families(run_log, branch=None, cwd=None)` at line 352 returns status `empty`, `known`, `unknown`, or `unreadable` with families or causes; TASK-086b calls the same signature with the record path and checkout folder.
- R2: `_apply_drop_rule()` lines 269-294 drops earlier rows only when a later row has `clean` exactly `true` and a valid `start_commit` that equals or is an ancestor of the earlier start, by `git merge-base --is-ancestor`.
- R3: `built_families()` lines 364-366 returns the empty set when `_in_git_repo()` is false and does not read the record.
- R4: Unreadable exits before resolve; example cause line: `FAIL  cannot read the families that built this branch (git)` (main ~952).
- R5: Unknown when a line does not parse or a report lacks its brief row; example: `unknown  the built set is not known (runs.jsonl)` (main ~968).
- R6: Profile loop in `main()` lines 991-1109 applies the design table including unknown-set REBUILD versus review_b and family/unavailable alternates.
- R7: Collision skip at lines 1012-1014 unchanged; alternate never rescues; `review_b_alt` may match the builder family.
- R8: Example DEVIATION line: `DEVIATION  review_b is gpt-5.6-sol-high instead of grok-4.7-medium (family)`; `deviation` entry with sorted `built` list.
- R9: REBUILD prints: default ending text at 1147; with checkpoint at 1148; with `--repair-record` at 1149-1150; with `new branch` at 1151-1152.
- R10: `repair_record()` lines 467-502; counts line e.g. `repair-record  kept 5  moved 3`.
- R11: `--review-alt` parsed at 916-919; deviation at 1017-1038 or exit 1 at 1111-1113.
- R12: `_probe_roles()` lines 971-982 probes all listed models; alternate failure can revert to REBUILD at 1089-1095.
- R13: `built_by()` lines 147-173 and its print at 965-966 unchanged in behavior.
- R14: `_git_run()` lines 179-184 uses argument list, `NO_WINDOW`, 20s timeout.
- R15: Module docstring lines 1-77 updated; `dump-cli.py` regenerated.
- R16: No new dependencies or bridge imports; MANIFEST regenerated.

`rebuild.built_by` is always the model id from `built_by(run_log, branch)` (the last builder row on the branch), not the multi-family set.

## Scratch tests

no scratch test file

## Mutation code points (N1-N13)

- N1: `built_families()` lines 397-401 vs using `built_by` only — `test_task086a_one_family_is_the_built_set`
- N2: `_apply_drop_rule()` lines 269-294 — `test_task086a_a_rebuild_from_the_checkpoint_leaves_the_rebuilding_family_alone`
- N3: `_apply_drop_rule()` line 271 `clean is not True` — `test_task086a_a_later_run_that_is_no_rebuild_counts_both_families[tree-not-clean]`
- N4: `_git_is_ancestor()` lines 207-211 — `test_task086a_a_later_run_that_is_no_rebuild_counts_both_families[descendant-commit]`
- N5: `_apply_drop_rule()` lines 279-280 skip drop without valid start — `test_task086a_a_row_git_cannot_place_drops_nothing`
- N6: `_parsing_row_families()` lines 458-464 on unknown — `test_task086a_table_row_6_unknown_set_review_b_of_no_builders_family`
- N7: `built_families()` lines 408-409 bad lines — `test_task086a_a_record_line_that_does_not_parse_makes_the_set_unknown`
- N8: `built_families()` lines 419-424 report rows — `test_task086a_a_report_the_branch_adds_without_its_row_makes_the_set_unknown`
- N9: `_alt_independent()` lines 454-455 — `test_task086a_review_alt_ends_with_exit_1_where_it_cannot[alternate-of-review-a]`
- N10: `_alt_pool_ok()` / main pool checks ~998-1002 — `test_task086a_table_row_4_the_alternate_where_review_b_is_unavailable[pool]`
- N11: main row-2 branch lines 1056-1060 — `test_task086a_table_row_2_the_alternate_where_review_b_s_family_built`
- N12: main unknown-set lines 1042-1044 — `test_task086a_table_row_5_the_profile_skipped_where_no_rebuild_removes_the_cause[set-unknown]`
- N13: `repair_record()` lines 479-484 keep parsing lines — `test_task086a_repair_record_keeps_every_parsing_line_in_place_and_moves_the_others`

## Missing acceptance cases

none found

## Commands

### 1. git status --short (before edit)

```
```

### 2. Checkpoint acceptance tests

```
49 failed, 25 passed in 37.93s
```

Failing ids included: `test_task086a_a_later_run_that_is_no_rebuild_counts_both_families` (all four param cases), `test_task086a_two_briefs_on_one_branch_the_second_rebuilt_keep_the_first_briefs_family`, `test_task086a_a_row_git_cannot_place_before_a_rebuild_stays_counted_and_the_rebuild_takes_a_new_branch` (both params), `test_task086a_a_row_git_cannot_place_drops_nothing` (both params), `test_task086a_a_branch_rebased_between_two_runs_is_rebuilt_under_a_new_branch`, `test_task086a_a_report_the_branch_adds_without_its_row_makes_the_set_unknown` (all four cases), and the other red cases the checkpoint run listed through `test_task086a_after_the_repair_and_the_rebuild_the_review_guards_first_snapshot_seeds_no_round`.

### 3. python tools/dump-cli.py

```
(no output)
```

### 3b. python tools/dump-cli.py --check

```
(exit 0, no output)
```

### 4. python tools/make-manifest.py

```
make-manifest: version 2026.11.23a, 148 files hashed, VERSION + MANIFEST.json written
```

### 5. git status --short (after manifest)

```
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/roster-check.py
 M docs/CLI_REFERENCE.md
 M docs/cli-reference.json
```

### 6. python -m pytest -p no:cacheprovider -q -rs tests/test_improve_roster_alt.py

```
74 passed in 44.35s
```

### 7. Checkpoint regression batch

```
458 passed in 300.63s (0:05:00)
```

### 8. Second regression batch

```
155 passed in 200.71s (0:03:20)
```

### 9. python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet

```
bridge-check: version 2026.11.23a (2026-11-24 16:45) at <Workspace>/bridge
bridge-check: 148 OK, 0 STALE, 0 MISSING, 0 EXTRA
RESULT: SOURCES MATCH bridge 2026.11.23a <Workspace>/bridge/cursor-bridge
```

### 10. python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks

```
windowless-check: 41 file(s) scanned, 0 FAIL, 0 NOTE
```

### 11. ASCII check

```
ascii ok
```

### 12. git diff --stat HEAD

```
 bridge/cursor-bridge/MANIFEST.json   |   4 +-
 bridge/cursor-bridge/roster-check.py | 555 ++++++++++++++++++++++++++++++++---
 docs/CLI_REFERENCE.md                |  28 +-
 docs/cli-reference.json              |   2 +-
 4 files changed, 542 insertions(+), 47 deletions(-)
```

### 13. git rev-parse HEAD and git status --short

```
6c7f651bc806b0529766d4331368dd066ce220d7
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/roster-check.py
 M docs/CLI_REFERENCE.md
 M docs/cli-reference.json
```

Counts above belong to commit `6c7f651bc806b0529766d4331368dd066ce220d7` with uncommitted changes listed in step 13.

## Assumed, not verified

Assumed, not verified: none