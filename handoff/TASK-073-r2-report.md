# TASK-073 round 2 report

## Files changed or created

- `bridge/cursor-bridge/bridge-install.py`
- `bridge/cursor-bridge/MANIFEST.json`
- `tests/test_rollback.py`
- `docs/BUILDER_NOTES.md`
- `handoff/TASK-073-r2-report.md`

## Summary

Round 2 fixes the installer's `--keep` rotation, marker handling, kept-folder listing, and CLI validation so R-094 matches the acceptance tests: `save_previous()` now honors this run's `--keep` before rotating copies, `read_keep_marker()` treats unreadable markers as no mark (with `utf-8-sig` for BOM), `kept_release_names()` lists every non-`.partial` folder, rotation clears stale `.partial` entries and stray files, and `main()` runs name checks inside the `OSError`/`ValueError` handler; `test_r094_keep_with_rollback_is_refused` asserts the target is unchanged on refusal.

## Requirements met

- **B1:** `save_previous()` (lines 472-496) takes `keep` from `install()` (line 770); when `keep` is set, rotation spares that name or none before the marker is written after `run_check` (lines 781-788). A failed install check (exit 1) leaves copies already rotated by `save_previous()` and the marker unchanged (no `write_keep_marker` because `result != 0`).
- **S1:** `read_keep_marker()` (lines 388-396) uses `utf-8-sig` and returns `None` on any read/decode failure; unreadable markers are treated as no mark (one-previous rule only).
- **S2:** `kept_release_names()` (lines 366-372) lists every directory not ending `.partial`; `KEPT_NAME` removed.
- **S3:** `save_previous()` (lines 487-496) removes every entry except `KEEP_MARKER`, the marked copy, and the version being saved, including `.partial` folders and loose files.
- **S4:** `main()` (lines 866-887) calls `kept_release_names()` for `--keep` and `--rollback <version>` inside the same `try` as install/rollback.
- **S5:** `test_r094_keep_with_rollback_is_refused` (lines 456-464 in `tests/test_rollback.py`) asserts installed version, kept `OLD_VERSION` folder, and no `ROLLED-BACK.md`.

## Optional item 8

Done: after a passing real `--keep`, `install()` prints `  keep           ...` (lines 785-788).

## Mutation self-check

Each mutant was reverted from a saved good copy (not `git checkout`) before the final tree.

- **K1** an unknown word beginning with `-` is ignored instead of refused — `8 failed, 56 passed in 152.98s (0:02:32)` — `test_r094_a_word_the_installer_does_not_know_is_refused_with_the_usage[help-alone]`
- **K2** an option given twice is accepted — `5 failed, 59 passed in 157.61s (0:02:37)` — `test_r094_a_word_the_installer_does_not_know_is_refused_with_the_usage[twice-rollback]`
- **K3** the name match is case-insensitive — `2 failed, 62 passed in 151.08s (0:02:31)` — `test_r094_a_keep_value_that_is_not_a_kept_folders_name_is_refused[other-case]`
- **K4** the name match is made by `os.path.isdir` of the value joined to `cursor-bridge-previous/` instead of against the listing's names — `1 failed, 63 passed in 152.58s (0:02:32)` — `test_r094_a_keep_value_that_is_not_a_kept_folders_name_is_refused[other-case]`
- **K5** the next install ignores the marker (the one-previous rule removes the marked copy) — `12 failed, 52 passed in 121.97s (0:02:01)` — `test_r2_a_marker_saved_with_a_byte_order_mark_still_keeps_its_copy`
- **K6** `--rollback <version>` ignores the version and restores the newest kept copy — `2 failed, 62 passed in 135.19s (0:02:15)` — `test_r094_rollback_to_the_older_kept_copy`
- **K7** `save_previous` ignores this run's `--keep` value (uses only the stored marker) — `1 failed, 63 passed in 140.08s (0:02:20)` — `test_r2_keep_given_with_the_install_of_a_new_version_keeps_the_named_copy`

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
................................................................         [100%]
64 passed in 150.02s (0:02:30)
```

### 6. python -m pytest -p no:cacheprovider -q -rs tests/test_install_check.py tests/test_install_check_a4.py tests/test_rollback.py tests/test_bug034.py

```
..............................................................           [100%]
62 passed in 184.35s (0:03:04)
```

### 7. python tools/dump-cli.py --check

```
(exit 0)
```

### 8. python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet

```
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

```
7b22b5d36f1787b63a30ce252a3c2970bcebbdc1
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/bridge-install.py
 M tests/test_rollback.py
```

Results above are for commit `7b22b5d36f1787b63a30ce252a3c2970bcebbdc1` with uncommitted changes as shown; `bridge/cursor-bridge/VERSION` is not listed.

## Assumed, not verified

- A stale `.keep` whose version folder is already gone is treated as no mark in `save_previous()` and cleared after rollback when the name is missing (`rollback()` lines 844-847) — an acceptance test with a hand-placed orphan `.keep` would confirm end-to-end.
- Stray non-folder entries under `cursor-bridge-previous/` are removed on rotation (`save_previous()` lines 494-496) — only covered by the round-2 `.partial` acceptance case, not arbitrary junk files.
- Refusal and `  keep           ` lines render legibly on a cp1252 Windows console — not run on that encoding in this session.