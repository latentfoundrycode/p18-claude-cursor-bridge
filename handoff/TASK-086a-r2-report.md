# TASK-086a round 2 report

## Files changed

- `bridge/cursor-bridge/roster-check.py`
- `bridge/cursor-bridge/MANIFEST.json` (regenerated)
- `docs/cli-reference.json` (regenerated)
- `docs/CLI_REFERENCE.md` (regenerated)
- `docs/BUILDER_NOTES.md` (one dated line appended)

## Summary

Round 2 fixes defects and security items from Review A and the security audit: `chosen_rebuild_end` is no longer written into `ROSTER.resolved.json`; git answers only 0/1 for yes/no commands; the branch and `main` use full ref names; the run record is read in binary; `--repair-record` appends before replace with link checks; report briefs match case-insensitively; builder-row families come from roster entries; REBUILD `built_by` names the latest row of `review_b`'s family; probe failures follow the table (skip vs REBUILD); and `--review-alt` validates its reason, targets the profile in use, and refuses with named causes.

## Requirements (R1-R16)

- R1: `built_families(run_log, branch=None, cwd=None, roster=None, profiles=None)` at line 448; optional roster args keep TASK-086b's three-argument call valid.
- R2: `_apply_drop_rule()` lines 327-356 with per-resolve `_commit_exists` cache.
- R3: `built_families()` lines 460-462 empty set outside git unchanged.
- R4: `FAIL  cannot read the families that built this branch (git)` (main ~1119).
- R5: `unknown  the built set is not known (runs.jsonl: builder row r1 of model 'mystery-builder-2', whose family cannot be named; give the model its family in the roster)` (main ~1146).
- R6: Profile loop in `main()` lines 1254-1365 applies table rows with `parsing_unknown_family` on unknown sets.
- R7: Collision skip unchanged at lines 1272-1274.
- R8: `DEVIATION  review_b is composer-2.5 instead of grok-4.7-medium (family)` with `deviation` entry.
- R9: REBUILD closing forms: checkpoint / `--repair-record` / `new branch` at lines 1405-1411 only in stdout (`chosen_rebuild_end`, not in JSON).
- R10: `repair_record()` lines 607-662; counts line `repair-record  kept 5  moved 3`.
- R11: `--review-alt` validated at 1065-1070; refused lines at 1203-1235; success at 1192-1247.
- R12: Builder probed before `review_b` / `review_b_alt` at 1325-1355; family-row alt probe failure can fall through to REBUILD with `review_b` reprobe.
- R13: `built_by()` lines 151-178 and `current_branch()` unchanged; `built_by` catches `RecursionError` on hostile lines.
- R14: `_git_run()` lines 190-195; binary git readers at 213-225, 227-231.
- R15: Module docstring updated; `dump-cli.py` regenerated.
- R16: `tempfile` stdlib only; MANIFEST regenerated.

`rebuild.built_by` is the model id of the latest counted (or on unknown, parsing) builder row whose family matches `review_b`'s, else `built_by()`'s last-row answer (may be null).

## Scratch tests

no scratch test file

## Mutation code points (N1-N22)

- N1: `built_families()` lines 448-542 — `test_task086a_one_family_is_the_built_set`
- N2: `_apply_drop_rule()` lines 327-356 — `test_task086a_a_rebuild_from_the_checkpoint_leaves_the_rebuilding_family_alone`
- N3: `_apply_drop_rule()` line 336 `clean is not True` — `test_task086a_a_later_run_that_is_no_rebuild_counts_both_families[tree-not-clean]`
- N4: `_git_is_ancestor()` lines 227-231 — `test_task086a_a_later_run_that_is_no_rebuild_counts_both_families[descendant-commit]`
- N5: `_row_valid_start()` / `_valid_commit_name()` lines 209-324 — `test_task086a_a_row_git_cannot_place_drops_nothing`
- N6: `main()` unknown-set branch lines 1283-1290 — `test_task086a_table_row_6_unknown_set_review_b_of_no_builders_family`
- N7: `_parse_run_log_raw()` lines 408-433 — `test_task086a_a_record_line_that_does_not_parse_makes_the_set_unknown`
- N8: `built_families()` report loop lines 528-534 — `test_task086a_a_report_the_branch_adds_without_its_row_makes_the_set_unknown`
- N9: `_alt_independent()` lines 585-586 — `test_task086a_review_alt_ends_with_exit_1_where_it_cannot[alternate-of-review-a]`
- N10: `_alt_pool_ok()` / review-alt pool check lines 1222-1224 — `test_task086a_table_row_4_the_alternate_where_review_b_is_unavailable[pool]`
- N11: `main()` family deviation rows 1292-1305 — `test_task086a_table_row_2_the_alternate_where_review_b_s_family_built`
- N12: `main()` skip on unavailable deviation probe fail lines 1334-1335 — `test_task086a_table_row_5_the_profile_skipped_where_no_rebuild_removes_the_cause[set-unknown]`
- N13: `repair_record()` lines 607-662 — `test_task086a_repair_record_keeps_every_parsing_line_in_place_and_moves_the_others`
- N14: `_brief_from_report()` lines 241-244 — `test_task086a_every_report_file_the_branch_adds_needs_its_row[no-round-in-the-name]`
- N15: `_roster_model_family()` lines 375-387 — `test_task086a_a_family_named_in_the_roster_counts_for_a_builder_row`
- N16: `built_families()` family loop lines 515-525 — `test_task086a_a_builder_row_of_no_known_family_makes_the_set_unknown[family-unknown]`
- N17: `_valid_commit_name()` line 209 — `test_task086a_a_start_commit_is_a_full_object_name`
- N18: `_merge_base_with_main()` lines 296-312 — `test_task086a_main_and_the_branch_are_read_by_their_full_ref_names[tag-main]`
- N19: `_git_is_ancestor()` / `_commit_exists()` exit checks lines 227-231, 217-218 — `test_task086a_git_answering_neither_yes_nor_no_cannot_be_read`
- N20: `repair_record()` append-before-replace order lines 623-644 — `test_task086a_a_repair_that_fails_part_way_leaves_the_record_whole`
- N21: `_damaged_path_unsafe()` lines 589-604 — `test_task086a_a_repair_refuses_a_damaged_file_linked_to_another_file`
- N22: `main()` review-alt on profile in use lines 1192-1247 — `test_task086a_review_alt_acts_on_the_profile_in_use_alone`

## Missing acceptance cases

none found

## Commands

### 1. git status --short (before edit)

```
```

### 2. Checkpoint acceptance tests (expected 34 failed, 77 passed)

```
34 failed, 77 passed in 64.94s
```

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
111 passed in 72.99s (0:01:12)
```

### 7. Checkpoint regression batch

```
3 failed, 455 passed in 304.22s (0:05:04)
```

Failing ids (out of scope per brief): `test_r095_r2_probe_a_reply_quoting_the_line_on_a_line_of_its_own_is_judged_as_before_round_1`, `test_r095_r3_probe_the_line_beside_another_stdout_line_is_no_answer[banner-first]`, `test_r095_r3_probe_the_line_beside_another_stdout_line_is_no_answer[line-first]` in `tests/test_program_roster_sign_in.py`.

### 8. Second regression batch

```
155 passed in 200.89s (0:03:20)
```

### 9. python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet

```
bridge-check: version 2026.11.23a (2026-11-24 17:48) at <workspace>/bridge
bridge-check: 148 OK, 0 STALE, 0 MISSING, 0 EXTRA
RESULT: SOURCES MATCH bridge 2026.11.23a <workspace>/bridge/cursor-bridge
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
 bridge/cursor-bridge/roster-check.py | 722 +++++++++++++++++++++++------------
 docs/CLI_REFERENCE.md                |   9 +-
 docs/cli-reference.json              |   2 +-
 4 files changed, 497 insertions(+), 240 deletions(-)
```

### 13. git rev-parse HEAD and git status --short

```
3f3c354a1f3bfba4e81bdbf2b1a4c0104bea6bce
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/roster-check.py
 M docs/CLI_REFERENCE.md
 M docs/cli-reference.json
```

Counts above belong to commit `3f3c354a1f3bfba4e81bdbf2b1a4c0104bea6bce` with uncommitted changes listed in step 13.

## Assumed, not verified

- `git symbolic-ref -q HEAD` on a detached head in a secondary worktree still exits 1 with no usable ref on the platform's git — needed because only process cwd scratch repos were exercised, not multi-worktree checkouts.
- `git ls-tree -r -z --name-only --full-tree <commit> -- handoff/` on Linux CI git emits NUL-separated paths with no quoting surprises — acceptance tests run on Windows git here.
- `git rev-parse --show-toplevel` from a subdirectory of the repository returns the same toplevel as from the repo root when listing `handoff/` reports — tests always run from the scratch repo root.
- `tempfile.mkstemp` in the run-record directory followed by `os.replace` over a file another process holds open on Windows leaves the open handle on the old inode without truncating a shared damaged file — the hard-link refusal test uses `nlink > 1` instead of an open handle.