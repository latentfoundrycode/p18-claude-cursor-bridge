# TASK-087b round 1 report

## Summary

The SessionStart hook now splits the supervisor digest at `<!-- digest:part -->`, prints the first slice on `--part digest` and the second on `--part digest-2` with its own header, applies `cap` at `MAX_OUTPUT` with part-specific cut labels, and `--part all` emits pointers plus both slices; `settings.bridge.json` gained a second `SessionStart` group for `digest-2`, the four tests that pinned the old 9,500 whole-digest cap now use 10,500, `test_release_s_budgets.py`'s docstring names the new caps, and CLI reference plus MANIFEST were regenerated.

## Files changed

- `bridge/cursor-bridge/session-start.py`
- `bridge/cursor-bridge/settings.bridge.json`
- `bridge/cursor-bridge/MANIFEST.json`
- `docs/CLI_REFERENCE.md`
- `docs/cli-reference.json`
- `tests/test_session_start.py`
- `tests/test_loop_text_pace.py`
- `tests/test_a5_followups.py`
- `tests/test_release_s_budgets.py`
- `handoff/TASK-087b-r1-report.md`

`tests/test_allowlist.py`: no edit (no hook-entry assertions in that file).

## Requirements

- **R1:** `split_digest` (lines 248-256) and `main` (lines 674-675) pass `digest1` to `digest_part`; the first header line remains `CLAUDE-CURSOR BRIDGE core digest (bridge 2026.11.24a) - the condensed core of ~/.claude/commands/supervisor.md; the full text governs:` as `test_r109_part_digest_prints_its_header_and_the_text_before_the_line` holds.
- **R2:** `digest_part_2` (lines 632-635) and `main` (lines 676-677); second header includes `second part` and `(bridge 2026.11.24a)` per `test_r109_part_digest_2_prints_a_header_of_its_own_and_the_text_after_the_line`.
- **R3:** `main` (lines 662-677) keeps pointers unchanged and joins digest plus digest-2 under `all`; `test_r109_part_all_prints_the_pointers_and_both_parts` passes.
- **R4:** `cap` (lines 259-262) at `MAX_OUTPUT` (line 95); first-part cut note uses `the digest`, second uses `the digest's second part` per `test_r109_each_part_is_cut_by_the_cap_and_the_note_names_the_part`.
- **R5:** `settings.bridge.json` second `SessionStart` group with `--part digest-2`; `test_r109_the_settings_gain_a_second_session_start_group_for_the_second_part` and merge or rollback test pass.
- **R6:** Module docstring documents three registrations and `--part digest-2`; `python tools/dump-cli.py --check` exit 0.
- **R7:** Plan quote 9,477 characters before the marker (checkpoint context); scratch assertion `whole_slice=9522 part1=4181 part2=5294 digest_stripped=9499` (marker included in slice, stripped digest 9,499 before marker text); caps held by updated assertions and `test_r109_the_whole_digest_is_at_most_10500_and_each_part_at_most_8800`.
- **R8:** `git grep` output classed below; no non-history hits in editable files except those updated.
- **R9:** No new imports; pointers unchanged; MANIFEST and CLI reference regenerated; `VERSION` still `2026.11.24a`.

## R7 assertion changes

### `tests/test_session_start.py`

- Before: `assert len(TEXT[a:b]) <= 9500, "the digest part (digest + its header line) must stay under the hook's cap with margin"`
- After: `assert len(TEXT[a:b]) <= 10500, "the whole digest must stay at most 10,500 characters"`
- Other `9500` in file: none.

### `tests/test_loop_text_pace.py`

- Before: `assert len(d) <= 9500, len(d)`
- After: `assert len(d) <= 10500, "the whole digest must stay at most 10,500 characters (%d)" % len(d)`
- Other `9500` in file: none.

### `tests/test_a5_followups.py`

- Before: `assert len(SV[a:b]) <= 9500, "a text release adds nothing to the digest"`
- After: `assert len(SV[a:b]) <= 10500, "a text release adds nothing to the digest (whole at most 10,500 characters)"`
- Other `9500` in file: none.

### `tests/test_b2_least_confident.py`

- Line 55 `"chars": 9500` unchanged (status-file shape fixture, not the digest cap).

## Scratch test

- `tests/test_task087b_scratch_digest_sizes.py`: intentional failure printed `whole_slice=9522 part1=4181 part2=5294 digest_stripped=9499`; deleted after the run.

## Mutation code points (K1-K4)

- **K1** (second part never printed): `main` lines 676-677; caught by `test_r109_part_digest_2_prints_a_header_of_its_own_and_the_text_after_the_line`.
- **K2** (marker printed inside a part): `split_digest` lines 253-255; caught by `test_r109_part_digest_prints_its_header_and_the_text_before_the_line`.
- **K3** (first part prints whole digest): `main` line 675 uses `digest1` not full `digest`; caught by `test_r109_part_digest_prints_its_header_and_the_text_before_the_line`.
- **K4** (second part uncut by cap): `main` line 677 `cap(digest_part_2(...), MAX_OUTPUT, ...)`; caught by `test_r109_each_part_is_cut_by_the_cap_and_the_note_names_the_part[digest-2]`.

## Missing acceptance cases

None.

## Commands and output

Commit for final counts: `3680b22d61e73a55f775dbffc08fb2f1ba3fff59` (working tree uncommitted after step 12).

### 1. `git status --short` (before first edit)

```
```

### 2. `python -m pytest -p no:cacheprovider -q -rs tests/test_improve_digest_parts.py` (checkpoint)

```
9 failed, 5 passed in 2.01s
```

Failing ids: `test_r109_part_digest_prints_its_header_and_the_text_before_the_line`, `test_r109_part_digest_2_prints_a_header_of_its_own_and_the_text_after_the_line`, `test_r109_part_all_prints_the_pointers_and_both_parts`, `test_r109_each_part_is_cut_by_the_cap_and_the_note_names_the_part[digest-2]`, `test_r109_a_part_of_8800_characters_300_of_three_bytes_prints_whole_under_the_host_cap[first]`, `test_r109_a_part_of_8800_characters_300_of_three_bytes_prints_whole_under_the_host_cap[second]`, `test_r109_each_part_of_the_digest_as_it_stands_prints_whole_under_the_host_cap`, `test_r109_the_settings_gain_a_second_session_start_group_for_the_second_part`, `test_r109_the_installer_appends_the_new_group_once_and_the_rollback_removes_it_alone`.

Cases that passed on the checkpoint and still pass: `test_r109_a_digest_without_the_line_is_printed_whole_and_the_second_part_prints_nothing`, `test_r109_max_output_is_unchanged`, `test_r109_each_part_is_cut_by_the_cap_and_the_note_names_the_part[digest]`, `test_r109_the_digest_holds_the_line_once_directly_before_its_standing_rules`, `test_r109_the_whole_digest_is_at_most_10500_and_each_part_at_most_8800`.

### 3. `python tools/dump-cli.py` then `python tools/dump-cli.py --check`

```
```

(Exit code 0 for both; `--check` prints nothing on success.)

### 4. `python tools/make-manifest.py`

```
make-manifest: version 2026.11.24a, 148 files hashed, VERSION + MANIFEST.json written
```

### 5. `git status --short` (after manifest)

```
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/session-start.py
 M bridge/cursor-bridge/settings.bridge.json
 M docs/CLI_REFERENCE.md
 M docs/cli-reference.json
 M tests/test_a5_followups.py
 M tests/test_loop_text_pace.py
 M tests/test_release_s_budgets.py
 M tests/test_session_start.py
```

(`bridge/cursor-bridge/VERSION` not listed; no restore needed.)

### 6. Scoped pytest (final)

```
328 passed, 20 skipped in 16.95s
```

`tests/test_improve_digest_parts.py` (final):

```
14 passed in 2.61s
```

### 7. Out-of-scope pytest (final)

```
389 passed, 4 skipped in 330.92s (0:05:30)
```

### 8. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`

```
bridge-check: version 2026.11.24a (2026-11-25 17:47) at <Workspace>\bridge
bridge-check: 148 OK, 0 STALE, 0 MISSING, 0 EXTRA
RESULT: SOURCES MATCH bridge 2026.11.24a <Workspace>\bridge\cursor-bridge
```

### 9. `git grep -n -e "9,500" -e "9500" -- bridge tests`

```
bridge/cursor-bridge/CHANGELOG.md:119:- **The tests that pin wording alone are retired** ... Kept: the digest's cap of 9,500 characters ...
tests/test_b2_least_confident.py:55:        "chars": 9500,
tests/test_improve_digest_parts.py:330:    end marker, as the four tests measured 9,500) and each part at most 8,800 ...
```

- `CHANGELOG.md:119`: history (S1 release note).
- `test_b2_least_confident.py:55`: not digest cap (fixture field); left unchanged in scope.
- `test_improve_digest_parts.py:330`: history in supervisor acceptance docstring (out of scope to edit).

### 10. `git diff --stat`

```
 bridge/cursor-bridge/MANIFEST.json        | 10 +++----
 bridge/cursor-bridge/session-start.py     | 44 +++++++++++++++++++++++++------
 bridge/cursor-bridge/settings.bridge.json | 10 +++++++
 docs/CLI_REFERENCE.md                     | 21 ++++++++++-----
 docs/cli-reference.json                   |  2 +-
 tests/test_a5_followups.py                |  2 +-
 tests/test_loop_text_pace.py              |  2 +-
 tests/test_release_s_budgets.py           |  4 +--
 tests/test_session_start.py               |  2 +-
 9 files changed, 71 insertions(+), 26 deletions(-)
```

### 11. `git diff -- bridge/cursor-bridge/session-start.py bridge/cursor-bridge/settings.bridge.json`

Non-ASCII added in these diffs: none.

### 12. `git rev-parse HEAD` and `git status --short`

```
3680b22d61e73a55f775dbffc08fb2f1ba3fff59
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/session-start.py
 M bridge/cursor-bridge/settings.bridge.json
 M docs/CLI_REFERENCE.md
 M docs/cli-reference.json
 M tests/test_a5_followups.py
 M tests/test_loop_text_pace.py
 M tests/test_release_s_budgets.py
 M tests/test_session_start.py
```

(`VERSION` not listed; no `test_task087b_scratch_` file remains.)

## Assumed, not verified

Assumed, not verified: none.