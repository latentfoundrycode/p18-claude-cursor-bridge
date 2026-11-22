# TASK-074 round-1 report

## Files changed or created

- `bridge/cursor-bridge/bridge-check.py`
- `tools/make-manifest.py`
- `bridge/cursor-bridge/MANIFEST.json` (regenerated via `make-manifest.py`, not hand-edited)
- `handoff/TASK-074-r1-report.md`

## Summary

Under `--sources`, `bridge-check.py` now compares `os.path.realpath(HERE)` with `os.path.realpath(<--root>/cursor-bridge)` after the manifest is read from `HERE` but before any manifest file under `--root` is hashed; on mismatch it prints `RESULT:` naming both resolved folders and exits 2 with no per-file verdict lines. When the folders agree, success and failure RESULT lines under `--sources` include the resolved `cursor-bridge` folder after `bridge <version>`. The non-`--sources` path is unchanged. `make-manifest.py` preserves the existing `VERSION` line ending (CR LF or LF; new file gets LF). The manifest was regenerated; no new tests were appended to `tests/test_install_check.py`.

## Requirements R1–R7

- **R1:** `main()` lines 156–161 run the folder comparison after manifest JSON is read (lines 148–154) and before the hash loop (lines 166–178). On mismatch it prints `RESULT: <tmp>/A/cursor-bridge <tmp>/B/cursor-bridge` (both `os.path.realpath` values) and returns 2.
- **R2:** `main()` lines 229 and 235 append `os.path.realpath(HERE)` to the `SOURCES DO NOT MATCH` and `SOURCES MATCH` RESULT lines when `--sources` is set and the tree is checked.
- **R3:** The comparison block is guarded by `if sources:` only; installed-tree RESULT at line 237 and all non-`--sources` checks are as before.
- **R4:** Module docstring lines 27–28 extend exit 2 to name the `--sources` tree refusal.
- **R5:** `main()` in `make-manifest.py` lines 91–100 read existing `VERSION` bytes, pick `line_ending`, and write via binary `open(..., "wb")`.
- **R6:** Both programs were verified with the Done-section ASCII one-liner.
- **R7:** `MANIFEST.json` regenerated; `git diff -- bridge/cursor-bridge/VERSION` is empty and `VERSION` does not appear in `git status --short`.

## Builder tests added to `tests/test_install_check.py`

None.

## Mutation self-check

- **M1** (skip folder comparison): `2 failed, 5 passed in 6.24s` — `test_r093_a_check_of_another_tree_is_refused_naming_both_folders`
- **M2** (refusal exits 1 instead of 2): `2 failed, 5 passed in 4.94s` — `test_r093_a_check_of_another_tree_is_refused_naming_both_folders`
- **M3** (`RESULT: SOURCES MATCH` omits folder): `3 failed, 4 passed in 5.40s` — `test_r093_the_tree_the_program_stands_in_matches_and_its_result_names_the_folder`
- **M4** (`make-manifest.py` always writes LF): `1 failed in 1.26s` — `test_r093_make_manifest_keeps_a_crlf_version_file_crlf`

## Commands and output

Commit for counts below: `ebb4c23a399ca1933bafddd31fd6e6cf23280ca8`. Working tree had uncommitted changes (`M` on the three bridge/tool files above).

### 1. `git status --short`

```
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/bridge-check.py
 M tools/make-manifest.py
```

### 2. `python tools/make-manifest.py`

```
make-manifest: version 2026.11.12a, 148 files hashed, VERSION + MANIFEST.json written
```

### 3. `python -m pytest -p no:cacheprovider -q tests/test_program_release_tooling.py tests/test_install_check.py`

```
......................                                                   [100%]
22 passed in 26.31s
```

### 4. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`

```
bridge-check: version 2026.11.12a (2026-11-22 04:42) at <Workspace>/bridge
bridge-check: 148 OK, 0 STALE, 0 MISSING, 0 EXTRA
RESULT: SOURCES MATCH bridge 2026.11.12a <Workspace>/bridge/cursor-bridge
```

(exit code 0)

### 5. `python tools/dump-cli.py --check`

```
docs/cli-reference.json
docs/CLI_REFERENCE.md
```

(exit code 1; docstring exit list changed — supervisor regenerates CLI docs)

### 6. `python -c "[open(p,'rb').read().decode('ascii') for p in ('bridge/cursor-bridge/bridge-check.py','tools/make-manifest.py')]; print('ascii ok')"`

```
ascii ok
```

### 7. `git diff -- bridge/cursor-bridge/VERSION`

(no output)

### 8. `git rev-parse HEAD` and `git status --short`

```
ebb4c23a399ca1933bafddd31fd6e6cf23280ca8
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/bridge-check.py
 M tools/make-manifest.py
```

## Assumed, not verified

Assumed, not verified: none.