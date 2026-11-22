# TASK-073 round 3 report

## Files changed or created

- `bridge/cursor-bridge/bridge-install.py`
- `bridge/cursor-bridge/MANIFEST.json`
- `tests/test_rollback.py`
- `handoff/TASK-073-r3-report.md`

## Summary

Round 3 hardens R-094 rotation and marker handling in `bridge-install.py`: linked `cursor-bridge-previous` bases skip rotation and rollback cleanup through the link, stray or read-only entries are removed with `remove_kept_entry` (never following links), this run's `--keep` rewrites the marker during `save_previous` before `run_check`, version-shaped stray files are no longer spared, `.keep` is excluded from kept-folder listings and marker reads are capped at 512 bytes; `test_r094_marker_names_the_spare_after_a_failed_install_check` asserts F3; the manifest was regenerated after the last edit.

## Requirements met (F1–F6)

- **F1:** `previous_base_is_link()` (lines 474–485) detects a link or Windows reparse point via `os.lstat`; `save_previous()` (lines 532–533) skips rotation when `base` is a link and the install continues (exit 0 from `run_check` when the tree is valid); `rollback()` (lines 887–890) skips removing kept copies through a linked `base`.
- **F2:** `remove_kept_entry()` (lines 488–514) uses `lstat`, unlinks links and junctions without traversing them, and ignores `OSError` on every removal path; `save_previous()` calls it for each rotated entry (lines 540–541).
- **F3:** `save_previous()` (lines 544–545) calls `write_keep_marker()` immediately after rotation when this run passed `--keep` (not on dry runs); `install()` (lines 816–835) still returns `run_check`'s exit 1 without undoing that marker. After a failed install check (exit 1) with `--keep <version>`: kept copies reflect the rotation that already ran, the marker names the spared copy (or is absent for `--keep none`), and the next install still honours it.
- **F4:** The `n == version` spare in rotation is gone; stray files named like the version being saved go through `remove_kept_entry()` (lines 538–541). If one cannot be removed, errors are ignored and the install continues; a complete kept folder of that version still makes `save_previous` return early at line 526 without overwriting.
- **F5:** `kept_release_names()` (lines 373–374) excludes `KEEP_MARKER` from the listing.
- **F6:** `read_keep_marker()` (lines 390–396) reads at most `MARKER_READ_MAX` (line 91) bytes with `utf-8-sig` and treats any failure as no mark.

## Mutation self-check

Each mutant was reverted by copying back from `mutation-save.tmp/bridge-install.py` (folder removed before Done step 1); no `git checkout` or `git restore` for reverts.

- **K1** an unknown word beginning with `-` is ignored instead of refused — `8 failed, 59 passed in 159.50s (0:02:39)` — `test_r094_a_word_the_installer_does_not_know_is_refused_with_the_usage[help-alone]` — restored from saved copy.
- **K2** an option given twice is accepted — `5 failed, 62 passed in 163.17s (0:02:43)` — `test_r094_a_word_the_installer_does_not_know_is_refused_with_the_usage[twice-rollback]` — restored from saved copy.
- **K3** the name match is case-insensitive — `1 failed, 66 passed in 160.76s (0:02:40)` — `test_r094_a_keep_value_that_is_not_a_kept_folders_name_is_refused[other-case]` — restored from saved copy.
- **K4** the name match is made by `os.path.isdir` of the value joined to `cursor-bridge-previous/` instead of against the listing's names — `1 failed, 66 passed in 159.63s (0:02:39)` — `test_r094_a_keep_value_that_is_not_a_kept_folders_name_is_refused[other-case]` — restored from saved copy.
- **K5** the next install ignores the marker (the one-previous rule removes the marked copy) — `12 failed, 55 passed in 132.46s (0:02:12)` — `test_r2_a_marker_saved_with_a_byte_order_mark_still_keeps_its_copy` — restored from saved copy.
- **K6** `--rollback <version>` ignores the version and restores the newest kept copy — `2 failed, 65 passed in 156.74s (0:02:36)` — `test_r094_rollback_to_the_older_kept_copy` — restored from saved copy.
- **K7** `save_previous` ignores this run's `--keep` value (uses only the stored marker) — `1 failed, 66 passed in 134.93s (0:02:14)` — `test_r2_keep_given_with_the_install_of_a_new_version_keeps_the_named_copy` — restored from saved copy.
- **K8** the link check removed (the rotation lists a linked base) — `1 failed, 66 passed in 148.61s (0:02:28)` — `test_r3_a_linked_previous_folder_never_has_its_other_contents_removed` — restored from saved copy.

## Verification commands

### 1. git status --short

```
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/bridge-install.py
 M tests/test_rollback.py
```

### 2. python tools/dump-cli.py

```
(no output)
```

### 3. python tools/make-manifest.py

```
make-manifest: version 2026.11.12a, 148 files hashed, VERSION + MANIFEST.json written
```

### 4. git restore bridge/cursor-bridge/VERSION

```
(no output)
```

### 5. python -m pytest -p no:cacheprovider -q -rs tests/test_program_install_keep.py

```
...................................................................      [100%]
67 passed in 155.99s (0:02:35)
```

### 6. python -m pytest -p no:cacheprovider -q -rs tests/test_install_check.py tests/test_install_check_a4.py tests/test_rollback.py tests/test_bug034.py

```
...............................................................          [100%]
63 passed in 187.71s (0:03:07)
```

### 7. python tools/dump-cli.py --check

```
(exit 0, no output)
```

### 8. python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet

```
bridge-check: version 2026.11.12a (2026-11-22 00:43) at <Workspace>/bridge
bridge-check: 148 OK, 0 STALE, 0 MISSING, 0 EXTRA
RESULT: SOURCES MATCH bridge 2026.11.12a
```

### 9. python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks

```
windowless-check: 41 file(s) scanned, 0 FAIL, 0 NOTE
```

### 10. python -c "open('bridge/cursor-bridge/bridge-install.py','rb').read().decode('ascii'); print('ascii ok')"

```
ascii ok
```

### 11. git rev-parse HEAD and git status --short

Commit `75d6d2a3c60e5cdf52f84cdc015922f6fa0880b2`; verification step 5–6 counts belong to the tree with uncommitted changes below.

```
75d6d2a3c60e5cdf52f84cdc015922f6fa0880b2
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/bridge-install.py
 M tests/test_rollback.py
```

`bridge/cursor-bridge/VERSION` is not listed.

## Assumed, not verified

Assumed, not verified: none