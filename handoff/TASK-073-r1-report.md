# TASK-073 round 1 report

## Files changed or created

- bridge/cursor-bridge/bridge-install.py
- bridge/cursor-bridge/MANIFEST.json
- docs/cli-reference.json
- docs/CLI_REFERENCE.md
- tests/test_rollback.py
- handoff/TASK-073-r1-report.md

## Summary

`bridge-install.py` now parses and validates every command-line word in `parse_argv()` and `main()` before any install or rollback work, refusing unknown or inconsistent options with `USAGE` and exit 2. Install accepts `--keep <version>|none`, tracking the marked copy with a `.keep` marker file under `cursor-bridge-previous/` via `write_keep_marker()` after a successful install check, while `save_previous()` retains the marked folder when rotating the one previous release. Rollback accepts an optional version (`rollback(target, dry, rollback_version=None)`), removes kept copies newer than the target after a passing check, and clears a stale marker when the marked copy is gone. The module docstring and regenerated CLI reference document the new options.

## R1–R9

- **R1:** `parse_argv()` (422–471) and `main()` (846–877) read all words first; `refuse_usage()` (415–419) prints usage on refuse.
- **R2:** `name_value_problem()` (377–387), `kept_release_names()` (367–374), and checks in `main()` (856–869) match values to listing names only.
- **R3:** `write_keep_marker()` (401–412) writes `KEEP_MARKER` (`.keep`) after successful `run_check()` in `install()` (776–778); on install check failure the prior marker is left unchanged; marker cleared with `--keep none` on success.
- **R4:** `parse_argv()` (468–469) refuses `--keep` with `--rollback`; `test_r094_keep_with_rollback_is_refused` below the marker line.
- **R5:** `rollback()` with no version uses `saved[-1]` (797–798); an older marked copy (e.g. A) remains in `cursor-bridge-previous/` when rolling back to the newest kept copy only.
- **R6:** `rollback()` (792–797, 831–837) restores the named copy, removes newer kept folders on success, and clears `.keep` when the marked name is no longer among remaining folders.
- **R7:** Dry-run lines in `install()` (748–754) and unchanged dry paths in `rollback()` (824–825) name the copy and change nothing.
- **R8:** Module docstring (5–6, 50–61, 68–72); `dump-cli.py` regen keeps `"source": "docstring"` for bridge-install.
- **R9:** ASCII verified; messages are plain `bridge-install:` text.

## Added test

- `test_r094_keep_with_rollback_is_refused` in tests/test_rollback.py (below the marker line).

## Mutation self-check (K1–K6)

- **K1** an unknown word beginning with `-` is ignored instead of refused — `8 failed, 50 passed in 133.10s` — `test_r094_a_word_the_installer_does_not_know_is_refused_with_the_usage[unknown-version]`
- **K2** an option given twice is accepted — `1 failed in 13.83s` — `test_r094_a_word_the_installer_does_not_know_is_refused_with_the_usage[twice-dry-run]`
- **K3** the name match is case-insensitive — `1 failed in 7.74s` — `test_r094_a_keep_value_that_is_not_a_kept_folders_name_is_refused[other-case]`
- **K4** the name match is made by `os.path.isdir` of the value joined to `cursor-bridge-previous/` instead of against the listing's names — `1 failed in 13.82s` — `test_r094_a_keep_value_that_is_not_a_kept_folders_name_is_refused[other-case]`
- **K5** the next install ignores the marker (the one-previous rule removes the marked copy) — `1 failed in 7.77s` — `test_r094_the_named_copy_stays_over_two_later_installs`
- **K6** `--rollback <version>` ignores the version and restores the newest kept copy — `1 failed in 10.92s` — `test_r094_rollback_to_the_older_kept_copy`

Each mutation was reverted; `git diff` was empty for `bridge-install.py` after each revert.

## Verification commands

### 1. git status --short

```
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/bridge-install.py
 M docs/CLI_REFERENCE.md
 M docs/cli-reference.json
 M tests/test_rollback.py
?? handoff/TASK-073-r1-report.md
```

### 2. python tools/dump-cli.py

```
(no output; exit 0)
```

### 3. python tools/make-manifest.py

```
make-manifest: version 2026.11.12a, 148 files hashed, VERSION + MANIFEST.json written
```

### 4. git restore bridge/cursor-bridge/VERSION

```
(no output; exit 0)
```

### 5. python -m pytest -p no:cacheprovider -q -rs tests/test_program_install_keep.py

```
..........................................................               [100%]
58 passed in 123.54s (0:02:03)
```

### 6. python -m pytest -p no:cacheprovider -q -rs tests/test_install_check.py tests/test_install_check_a4.py tests/test_rollback.py tests/test_bug034.py

```
..............................................................           [100%]
62 passed in 175.27s (0:02:55)
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
81f7b3ee638e77ab3a52be19bebdf50b887767f4
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/bridge-install.py
 M docs/CLI_REFERENCE.md
 M docs/cli-reference.json
 M tests/test_rollback.py
?? handoff/TASK-073-r1-report.md
```

Results above are for commit `81f7b3ee638e77ab3a52be19bebdf50b887767f4` with uncommitted changes as shown; `bridge/cursor-bridge/VERSION` is not listed.

## Assumed, not verified

- A stale `.keep` file whose version folder is already gone does not block install or rollback — the marker is only consulted in `save_previous()` and cleared after rollback when the named folder is missing — an acceptance test with a hand-placed orphan `.keep` would confirm.
- Non-version files or folders left under `cursor-bridge-previous/` by older tooling are ignored by `kept_release_names()` and are not removed by `save_previous()` unless they are version-shaped directories — only exercised indirectly by the acceptance layout.
- Usage and refusal messages render legibly on a cp1252 Windows console — not run on that encoding in this session.