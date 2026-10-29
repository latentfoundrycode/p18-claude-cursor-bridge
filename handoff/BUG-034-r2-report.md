# BUG-034 round 2 report

## Initial git status

```
(empty — git status --porcelain produced no output)
```

## Files changed

- `bridge/cursor-bridge/bridge-install.py` (docstring item 1 and `install()` only)
- `bridge/cursor-bridge/MANIFEST.json` (via `python tools/make-manifest.py`)
- `docs/cli-reference.json` (via `python tools/dump-cli.py`)
- `docs/CLI_REFERENCE.md` (via `python tools/dump-cli.py`)
- `handoff/BUG-034-r2-report.md` (this file)

## Verification commands

1. `python tools/make-manifest.py` — exit 0; output: `make-manifest: version 2026.10.25a, 144 files hashed, VERSION + MANIFEST.json written`
2. `git diff --quiet -- bridge/cursor-bridge/VERSION` — exit 0
3. `python tools/dump-cli.py` — exit 0
4. `python tools/dump-cli.py --check` — exit 0
5. `PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider tests/test_bug034.py tests/test_rollback.py tests/test_install_check.py tests/test_install_check_a4.py tests/test_dump_cli.py` — exit 0; `155 passed in 251.54s (0:04:11)`
6. `git diff --quiet HEAD -- tests/test_bug034.py` — exit 0

### Final `git status --porcelain`

```
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/bridge-install.py
 M docs/CLI_REFERENCE.md
 M docs/cli-reference.json
?? handoff/BUG-034-r2-report.md
```

### Final `git diff --stat`

```
 bridge/cursor-bridge/MANIFEST.json     |  4 ++--
 bridge/cursor-bridge/bridge-install.py | 17 +++++++++++------
 docs/CLI_REFERENCE.md                  |  2 +-
 docs/cli-reference.json                |  2 +-
 4 files changed, 15 insertions(+), 10 deletions(-)
```

## Summary

Round 2 made the `--anyway` same-version override visible: `install()` now always runs the installed-vs-release fingerprint comparison when versions match, stores the differing path list once in `same_version_differing`, refuses before the banner when `--anyway` is absent (unchanged round 1 behavior), and after the install banner prints one S4-shaped WARNING naming that list when `--anyway` is set, then proceeds with `replace_release` as before. The module docstring item 1 notes that `--anyway` prints a warning that no way back was kept. Manifest and CLI reference were regenerated with the prescribed tools.

## Warning line (reproduction test case)

```
  WARNING        the installed 2026.01.01a was replaced by other files of the same version (1 file(s): cursor-bridge/old-only.md); no way back to it was kept; installed with --anyway.
```

## Cause

The named cause was the `--anyway` path skipping the same-version comparison entirely (`old_version == new_version and not anyway`), so replacement happened with no message and no `save_previous`. The fix keeps a single comparison block: the differing list either triggers refusal or the new WARNING after the banner, without changing what `--anyway` installs.

## Assumed, not verified

- The dry-run case with `--anyway` prints the same WARNING after a `(dry run)` banner and changes nothing on disk · Requirement 3 has no dedicated test in the allowed suite; logic places the WARNING after the banner for all non-refusal paths including dry run · A targeted dry-run assertion in a future brief or manual run with `--dry-run --anyway` on the two_releases fixture would confirm it.
- The exact warning string above matches pytest output byte-for-byte · Derived from test fixture layout (one changed file `cursor-bridge/old-only.md`, version `2026.01.01a` from `test_rollback.OLD_VERSION) · Capturing stdout from the reproduction test would confirm the full line including any path formatting.
