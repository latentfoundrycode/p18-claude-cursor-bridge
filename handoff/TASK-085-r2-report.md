# TASK-085 round 2 report

## Files changed

- `bridge/cursor-bridge/mutation-run.py`
- `bridge/cursor-bridge/MANIFEST.json` (via `python tools/make-manifest.py`)
- `docs/BUILDER_NOTES.md` (one dated line at end)

## Summary

Round 2 fixes Review A defects in the editable-install path mapping, `import_roots` link walk, interpreter probe parsing, resolution-plugin Workspace detection, R7 refusal text, path-ahead when no copy path exists, and dead `tree_path_at_commit` code; `pytest_env` sets `PYTHONSAFEPATH=1` so mapped roots stay ahead of the copy when a stale top-level package shadows them. All twenty-four acceptance tests and Done regression commands pass.

## Corrections 1–8

- **Correction 1 (R7 line):** `run_resolution_check` (lines 1577–1586) raises one line whose format text is `module from Workspace path %s was loaded`; non-dict `loaded_ws` items use the same line with `place` set from the value. The dead fallback at the old line 1570 is removed.
- **Correction 2 (`map_probe_entries`):** lines 260–292 resolve `wr` and `ar` with `realpath`, compare with `normcase`, and form `wrel` via `relpath(ar, wr)` so case and junction-linked Workspaces map correctly.
- **Correction 3 (plugin Workspace paths):** `write_resolution_plugin` embeds `WORKSPACE_REAL` (lines 1245–1372); generated `_in_workspace`, `_in_copy`, and `pytest_sessionfinish` use both given and real paths under `normcase`.
- **Correction 4 (`import_roots` link walk):** `validate_import_roots` (lines 202–212) walks components from the Workspace root; `refuse_links_under` is not called. `OSError` on a component refuses with the link line; a missing component ends the walk.
- **Correction 5 (probe):** `run_interpreter_path_probe` (lines 295–313) runs `import sys; print(repr(sys.path))` and parses with `ast.literal_eval`.
- **Correction 6 (`path_ahead`):** plugin `pytest_sessionfinish` (lines 1348–1350) appends when `min_copy is None or i < min_copy`.
- **Correction 7 (dead code):** `tree_path_at_commit` removed; `active_import_roots` (lines 239–246) only checks `os.path.isdir` on the tree; unreachable `import_root_is_absolute` branches after `/` normalization removed (lines 173–181).
- **Correction 8 (report):** this file quotes the R7 format string and pytest summaries below.

**R7 line as held in source (format string unbroken):**

```
mutation-run: module from Workspace path %s was loaded (module %s; an editable install of the project is the usual cause; use import_roots for a finder-style install)
```

## Scratch tests

no scratch test file (a temporary `tests/test_task085_scratch_po_path.py` was deleted before finish).

## Mutation self-check (M1–M14)

- **M1** (probe entries ignored): `1 failed in 2.50s` — `test_task085_path_entry_under_nested_source_folder_kills_the_mutant`
- **M2** (mapped after copy root on PYTHONPATH): `1 failed in 5.67s` — `test_task085_mapped_roots_stand_ahead_of_the_copy_root`
- **M3** (Windows case-sensitive compare): not re-run (same `normcase` gate as round 1); round 1: **not caught** (`test_task085_path_entry_compared_without_regard_to_letter_case_on_windows` still passes when compare is case-folded only on this host)
- **M4** (absolute refusal removed): round 1: `1 failed in 0.73s` — `test_task085_import_roots_absolute_entry_refused`
- **M5** (`..` refusal removed): round 1: `3 failed in 8.28s` — `test_task085_import_roots_entry_leaving_the_workspace_refused[...]`
- **M6** (link refusal removed): round 1: `1 failed in 3.84s` — `test_task085_import_roots_entry_through_a_link_refused`
- **M7** (`import_roots` out of cache key): round 1: `1 failed in 8.76s` — `test_task085_import_roots_is_part_of_the_cache_key`
- **M8** (dotted roots only `""` and `src/`): round 1: **not caught** — would need a case where resolution depends on dotted prefix alone without path ordering
- **M9** (R7 cause/key dropped): `1 failed in 2.59s` — `test_task085_finder_only_refused_with_the_cause_and_the_key_named`
- **M10** (checkpoint absent root refuses): round 1: `1 failed in 1.51s` — `test_task085_checkpoint_skips_an_import_root_absent_at_the_commit`
- **M11** (case-folded relpath in `map_probe_entries`): `1 failed in 11.59s` — `test_task085_mapped_folder_keeps_its_letter_case_for_the_dotted_name`
- **M12** (Workspace as given not real): `1 failed in 3.04s` — `test_task085_workspace_reached_through_a_link_still_maps_its_entries`
- **M13** (`ci is None` path_ahead removed): `1 passed in 2.17s` on `test_task085_workspace_entry_ahead_of_the_copy_refused_by_its_own_line` — **not caught**; a case with a Workspace path entry and no copy path on `sys.path` at all would catch it
- **M14** (walk passes unreadable component): `1 passed in 0.53s` on link test — **not caught**; would need a component that raises `OSError` other than missing without being a link on the acceptance host

## Missing acceptance cases

none

## Commands and output

Commit for counts: `28d07111ed48bbb50d61d39c120cd652b24c7880`. Working tree after step 12 holds uncommitted changes (`MANIFEST.json`, `mutation-run.py`, `docs/BUILDER_NOTES.md`, `handoff/TASK-085-r2-report.md`).

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

(`bridge/cursor-bridge/VERSION` not listed after `git restore`.)

### 5. `python -m pytest -p no:cacheprovider -q -rs tests/test_improve_mutation_editable.py`

```
........................                                                 [100%]
24 passed in 59.47s
```

### 6. `python -m pytest -p no:cacheprovider -q -rs tests/test_mutation_run.py tests/test_mutation_run_supervisor.py tests/test_program_mutation_baseline.py tests/test_bug030.py tests/test_bug032.py`

```
202 passed, 2 skipped in 921.31s (0:15:21)
```

### 7. `python -m pytest -p no:cacheprovider -q -rs tests/test_allowlist.py tests/test_bridge_run_driver.py tests/test_dump_cli.py tests/test_loop_text_pace.py tests/test_loop_text_windowless.py tests/test_program_trace_moves.py tests/test_release_b2_stamp.py tests/test_release_t_floor.py tests/test_release_t_merge.py tests/test_release_t_stage_close.py tests/test_release_t_stamp.py`

```
525 passed, 20 skipped in 168.98s (0:02:48)
```

### 8. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`

```
RESULT: SOURCES MATCH bridge 2026.11.23a <Workspace>/bridge/cursor-bridge
```

### 9. `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks`

```
windowless-check: 41 file(s) scanned, 0 FAIL, 0 NOTE
```

### 10. `python -c "open('bridge/cursor-bridge/mutation-run.py','rb').read().decode('ascii'); print('ascii ok')"`

```
ascii ok
```

### 11. `git diff --stat HEAD`

```
 bridge/cursor-bridge/MANIFEST.json   |   4 +-
 bridge/cursor-bridge/mutation-run.py | 109 ++++++++++++++++++++---------------
 docs/BUILDER_NOTES.md                |   2 +
 3 files changed, 66 insertions(+), 49 deletions(-)
```

### 12. `git rev-parse HEAD` and `git status --short`

```
28d07111ed48bbb50d61d39c120cd652b24c7880
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/mutation-run.py
 M docs/BUILDER_NOTES.md
?? handoff/TASK-085-r2-report.md
```

## Assumed, not verified

Assumed, not verified: on every CI Python build, `PYTHONSAFEPATH=1` on the child pytest and probe processes is enough to keep mapped folders ahead of the copy root when pytest would otherwise prepend the rootdir · acceptance test `test_task085_mapped_roots_stand_ahead_of_the_copy_root` on Windows only · re-run that test on Linux CI without skips.

Assumed, not verified: `ast.literal_eval` on `repr(sys.path)` is always safe and complete for every probe output the venv emits · brief requires this parser · a hostile or huge repr could prove otherwise.

Assumed, not verified: `active_import_roots` skipping `tree_path_at_commit` still matches R9 for every archive layout where a root appears only in git history but not as a directory in the archived tree · `--checkpoint` acceptance cases passed once here · edge roots only in index metadata might differ.