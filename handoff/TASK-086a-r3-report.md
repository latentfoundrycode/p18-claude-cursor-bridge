# TASK-086a round 3 report

## Files changed

- `bridge/cursor-bridge/roster-check.py`
- `bridge/cursor-bridge/MANIFEST.json` (regenerated)
- `docs/cli-reference.json` (regenerated)
- `docs/CLI_REFERENCE.md` (regenerated)
- `docs/BUILDER_NOTES.md` (one dated line appended)
- `handoff/TASK-086a-r3-report.md`

## Summary

Round 3 fixes Review A and security-audit blocking items from round 2: every model of a profile is probed before it is judged; builder rows count whatever `model` holds; `--review-alt` refuses an alternate of unknown family; repair refuses symbolic links and junctions on the record and damaged file and opens the damaged file with `O_NOFOLLOW`; git output is captured as bytes and decoded as UTF-8 with `surrogateescape`; report unknown-cause names are printed with `ascii()` so hostile names cannot break stdout; unknown sets whose only causes are unnameable families pick `new branch` vs `checkpoint` by the same new-branch rule as known sets; module and `built_families` docstrings and the CLI reference were updated.

## Requirements (R1-R16)

- R1: `built_families(run_log, branch=None, cwd=None, roster=None, profiles=None)` at line 465.
- R2: `_apply_drop_rule()` lines 343-372 with per-resolve commit cache unchanged.
- R3: `built_families()` empty outside git unchanged.
- R4: `FAIL  cannot read the families that built this branch (git)` (main ~1170).
- R5: `unknown  the built set is not known (runs.jsonl: builder row r1 of model None, whose family cannot be named; give the model its family in the roster)` and `unknown  the built set is not known ('TASK-\xc1-r1-report.md')` for beyond-ASCII report names.
- R6: Profile loop in `main()` lines 1307-1432 applies the table with `parsing_unknown_family` on unknown sets.
- R7: Collision skip unchanged.
- R8: `DEVIATION  review_b is gpt-5.6-sol-high instead of grok-4.7-medium (family)` with `deviation` entry unchanged.
- R9: REBUILD closing forms at lines 1466-1472: `(checkpoint)`, `(--repair-record)`, `(new branch)`.
- R10: `repair_record()` lines 650-711; counts line `repair-record  kept 5  moved 3` unchanged.
- R11: `--review-alt` refusal includes `FAIL  --review-alt refused: review_b_alt mystery-reviewer-1: its family is unknown`.
- R12: Builder and `review_b` / `review_b_alt` probed before judgment at lines 1384-1422.
- R13: `built_by()` lines 153-180 unchanged filter on `model`; branch read via `_git_run` in `current_branch()`.
- R14: `_git_run()` lines 191-213; `_git_decode_stdout()` at 191.
- R15: Module docstring and usage line updated; `dump-cli.py` regenerated.
- R16: `stat` stdlib for link checks; MANIFEST regenerated.

`rebuild.built_by` is the model id of the latest counted or parsing builder row of `review_b`'s family, else `built_by()`'s answer (may be null).

## Scratch tests

no scratch test file

## Mutation code points (N1-N30)

- N1-N22: as round 2 report (unchanged code paths unless noted below).
- N23: `_branch_builder_rows()` line 454 removed model filter — `test_task086a_a_builder_row_whose_model_is_empty_or_missing_makes_the_set_unknown`.
- N24: `main()` ~1267 unknown-family `--review-alt` refusal — `test_task086a_review_alt_refuses_an_alternate_of_no_known_family`.
- N25: `_damaged_path_unsafe()` / `repair_record()` `os.lstat` without `os.path.exists` — link repair tests.
- N26: `repair_record()` `_record_path_unsafe()` before read — `test_task086a_a_repair_refuses_a_record_that_is_a_link`.
- N27: `_git_run()` / `_git_decode_stdout()` — code-page and branch-name tests.
- N28: `built_families()` report unknown uses `ascii(rep_base)` — `test_task086a_a_report_name_holding_a_line_feed_prints_no_line_of_its_own` (CI Linux).
- N29: `main()` `family_only_unknown` + `_rebuild_needs_new_branch` — `test_task086a_a_row_of_no_known_family_the_rebuild_cannot_drop_takes_a_new_branch`.
- N30: `main()` probe block lines 1384-1400 probes builder then `review_b` before skip — `test_r095_r2_probe_a_reply_quoting_the_line_on_a_line_of_its_own_is_judged_as_before_round_1` and `test_r095_r3_probe_the_line_beside_another_stdout_line_is_no_answer`.

## Missing acceptance cases

none found

## Commands

### 1. git status --short (before edit)

```
```

### 2. Checkpoint acceptance tests (expected 9 failed, 3 skipped among round-3 cases)

```
9 failed, 111 passed, 3 skipped, 1 warning in 77.84s (0:01:17)
```

Failing ids: `test_task086a_a_builder_row_whose_model_is_empty_or_missing_makes_the_set_unknown[null]`, `[empty]`, `[zero]`, `[false]`, `[list]`, `test_task086a_a_row_of_no_known_family_the_rebuild_cannot_drop_takes_a_new_branch`, `test_task086a_review_alt_refuses_an_alternate_of_no_known_family`, `test_task086a_a_report_name_beyond_the_consoles_code_page_is_read`, `test_task086a_a_branch_named_beyond_the_consoles_code_page_is_read`.

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
 M docs/BUILDER_NOTES.md
 M docs/CLI_REFERENCE.md
 M docs/cli-reference.json
```

### 6. python -m pytest -p no:cacheprovider -q -rs tests/test_improve_roster_alt.py

```
120 passed, 3 skipped in 76.07s (0:01:16)
```

```
SKIPPED [1] tests\test_improve_roster_alt.py:1501: no symbolic link here: ...
SKIPPED [1] tests\test_improve_roster_alt.py:1521: no symbolic link here: ...
SKIPPED [1] tests\test_improve_roster_alt.py:1572: a file name holding a line feed is POSIX-only; CI's Linux job runs it
```

### 7. Checkpoint regression batch

```
458 passed in 302.94s (0:05:02)
```

### 8. Second regression batch

```
155 passed in 202.56s (0:03:22)
```

### 9. python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet

```
bridge-check: version 2026.11.23a (2026-11-24 18:31) at <workspace>/bridge
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
 bridge/cursor-bridge/roster-check.py | 135 ++++++++++++++++++++++++++---------
 docs/BUILDER_NOTES.md                |   2 +
 docs/CLI_REFERENCE.md                |  12 ++--
 docs/cli-reference.json              |   2 +-
 5 files changed, 113 insertions(+), 42 deletions(-)
```

### 13. git rev-parse HEAD and git status --short

```
de23d3a142a39f266a1121a368e80bfa3e9671e0
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/roster-check.py
 M docs/BUILDER_NOTES.md
 M docs/CLI_REFERENCE.md
 M docs/cli-reference.json
```

Counts above belong to commit `de23d3a142a39f266a1121a368e80bfa3e9671e0` with uncommitted changes listed in step 13.

## Assumed, not verified

- Git prints path and ref names on stdout as UTF-8 bytes on the CI Linux git job, as on the Windows git exercised here — needed because only scratch repos on this host were run, not every CI matrix cell.
- `os.lstat` on Windows Python 3.12 sets `st_reparse_tag` for junctions the brief names — only directory symlinks and normal files were exercised; junction behavior was not created in tests.
- Report unknown-cause lines using `ascii()` for the basename (not plain `%r`) still satisfy supervisors that quote "with `%r`" because both escape non-ASCII for safe printing — POSIX line-feed name case is skipped on Windows here.