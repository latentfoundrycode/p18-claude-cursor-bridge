# TASK-085 round 1 report

## Files changed

- `bridge/cursor-bridge/mutation-run.py`
- `bridge/cursor-bridge/MANIFEST.json` (via `python tools/make-manifest.py`)

## Summary

Implemented R-106 (C27): the mutation run probes the venv interpreter's `sys.path` once per run, maps Workspace path entries onto matching copy folders ahead of the tree root, accepts and validates `import_roots` in the mutants file, extends dotted module resolution and the cache key with those roots, improves resolution refusals for finder-style editable installs, and keeps the path-ahead check without the old `sys.path` module line. All sixteen acceptance tests pass, along with the regression suites from the Done section.

## Requirements R1–R12

- **R1** `run_interpreter_path_probe` (line 302): after the copy exists, `main` (lines 1768–1775, 1856–1863) calls it once; failures leave `mapped_roots` empty.
- **R2** `map_probe_entries` (line 271): `os.path.normcase` compares probe entries to the Workspace; only entries under the copy are kept.
- **R3** `pytest_env` (line 1367): `PYTHONPATH` order is `plugin_dir`, then `import_roots` folders in file order, then mapped probe folders in probe order, then the tree root.
- **R4** `validate_import_roots` (line 187): refusal lines — explicit `null`: `mutation-run: import_roots must be a list of strings`; absent folder (ordinary mode): `mutation-run: import_roots entry %r is not in the working tree`; path that is a file: `mutation-run: import_roots entry %r is not a folder`.
- **R5** `module_dotted_prefixes`, `dotted_module_paths` (lines 232, 888), plugin `_dotted` and `module_file_at_commit` (lines 1300+, 1401).
- **R6** `run_path_key_part` and `compute_key` (lines 921, 929): normalized `import_roots` and active mapped roots are hashed before the mutant JSON part.
- **R7** `run_resolution_check` (lines 1564–1569): example line shape: `mutation-run: module pkg from Workspace path sdk/src/pkg/calc.py was loaded (editable install is the usual cause; use import_roots for a finder-style install)` (contains `module from Workspace path %s was loaded`).
- **R8** `run_resolution_check` (lines 1560–1562) raises `mutation-run: import path entry %r stands ahead of the copy on the import path`; plugin `path_ahead` (lines 1339, 1355).
- **R9** `active_import_roots` (line 247) and checkpoint `main` branch (lines 1755–1760) skip roots missing at the commit; probe/mapping reused in checkpoint.
- **R10** Existing refusals unchanged; R7/R8 replace the old `sys.path` loaded_ws marker only.
- **R11** Help text unchanged; `python tools/dump-cli.py --check` passes.
- **R12** No new options, env vars, exit codes, or bridge imports; manifest regenerated.

## Scratch tests

no scratch test file

## Mutation self-check (M1–M10)

- **M1** (probe entries ignored): `2 failed in 37.07s` — `test_task085_path_entry_under_nested_source_folder_kills_the_mutant`, `test_task085_checkpoint_reads_the_path_entry_roots`
- **M2** (mapped after tree root on PYTHONPATH): `16 passed in 44.27s` — **not caught** (path entry still wins when mapped folders follow tree root on `PYTHONPATH`; a stricter ordering test would catch it)
- **M3** (Windows case-sensitive compare): `1 passed in 5.22s` on case test alone — **not caught** (`os.path.realpath` on this host normalizes case before comparison)
- **M4** (absolute refusal removed): `1 failed in 0.73s` — `test_task085_import_roots_absolute_entry_refused`
- **M5** (`..` refusal removed): `3 failed in 8.28s` — `test_task085_import_roots_entry_leaving_the_workspace_refused[...]`
- **M6** (link refusal removed): `1 failed in 3.84s` — `test_task085_import_roots_entry_through_a_link_refused`
- **M7** (`import_roots` out of cache key): `1 failed in 8.76s` — `test_task085_import_roots_is_part_of_the_cache_key`
- **M8** (dotted roots only `""` and `src/`): `16 passed in 39.20s` — **not caught** (`import_roots` still places `sdk/src` on the path; resolution does not require the extra dotted prefix here)
- **M9** (R7 cause/key dropped): `1 failed in 2.26s` — `test_task085_finder_only_refused_with_the_cause_and_the_key_named`
- **M10** (checkpoint absent root refuses): `1 failed in 1.51s` — `test_task085_checkpoint_skips_an_import_root_absent_at_the_commit`

## Missing acceptance cases

none

## Commands and output

Commit for counts: `6c92cf7929e5d2fc9a89c779bc718d8f97d7f88c`. Working tree after step 12 holds uncommitted changes (`MANIFEST.json`, `mutation-run.py`).

### 1. `git status --short`

```
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/mutation-run.py
```

### 2. `python tools/dump-cli.py --check`

```
(no output; exit 0)
```

### 3. `python tools/make-manifest.py`

```
make-manifest: version 2026.11.23a, 148 files hashed, VERSION + MANIFEST.json written
```

### 4. `git status --short`

```
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/mutation-run.py
```

(`bridge/cursor-bridge/VERSION` not listed.)

### 5. `python -m pytest -p no:cacheprovider -q -rs tests/test_improve_mutation_editable.py`

```
................                                                         [100%]
16 passed in 39.34s
```

### 6. `python -m pytest -p no:cacheprovider -q -rs tests/test_mutation_run.py tests/test_mutation_run_supervisor.py tests/test_program_mutation_baseline.py tests/test_bug030.py tests/test_bug032.py`

```
202 passed, 2 skipped in 905.64s (0:15:05)
```

(Skip reasons: symbolic link privilege on `test_r041_scratch_through_link0` and supervisor link test.)

### 7. `python -m pytest -p no:cacheprovider -q -rs tests/test_allowlist.py tests/test_bridge_run_driver.py tests/test_dump_cli.py tests/test_loop_text_pace.py tests/test_loop_text_windowless.py tests/test_program_trace_moves.py tests/test_release_b2_stamp.py tests/test_release_t_floor.py tests/test_release_t_merge.py tests/test_release_t_stage_close.py tests/test_release_t_stamp.py`

```
525 passed, 20 skipped in 168.40s (0:02:48)
```

### 8. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`

```
RESULT: SOURCES MATCH bridge 2026.11.23a <Workspace>\bridge\cursor-bridge
```

### 9. `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks`

```
windowless-check: 41 file(s) scanned, 0 FAIL, 0 NOTE
```

### 10. ASCII check

```
ascii ok
```

### 11. `git diff --stat HEAD`

```
 bridge/cursor-bridge/MANIFEST.json   |   4 +-
 bridge/cursor-bridge/mutation-run.py | 333 ++++++++++++++++++++++++++++++-----
 2 files changed, 291 insertions(+), 46 deletions(-)
```

### 12. `git rev-parse HEAD` and `git status --short`

```
6c92cf7929e5d2fc9a89c779bc718d8f97d7f88c
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/mutation-run.py
```

## Assumed, not verified

- `os.path.realpath` on Windows may fold path letter case before `map_probe_entries` compares entries, which would explain M3 not failing on the upper-case `.pth` test · the M3 self-check used only `realpath` without `normcase` and the case test still passed · CI Linux or a path that does not canonicalize case the same way.
- Probe with `sys.executable -c` sees the same `sys.path` as pytest in the venv for these fixtures · all mapping tests passed · comparing raw probe JSON to pytest's `sys.path` inside a one-off test on the same venv layout.
- `tree_path_at_commit` treating a tree listing or any file under a prefix as sufficient to keep an `import_roots` entry in checkpoint mode · checkpoint skip test passed · explicit negative test with an empty git tree at that prefix only.