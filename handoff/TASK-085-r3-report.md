# TASK-085 round 3 report

## Files changed

- `bridge/cursor-bridge/mutation-run.py`
- `bridge/cursor-bridge/MANIFEST.json` (via `python tools/make-manifest.py`)
- `docs/BUILDER_NOTES.md` (round 2 line rewritten per correction 3)

## Summary

Round 3 removes `PYTHONSAFEPATH` from `pytest_env` and disables unsafe-path prepending only on interpreter command lines via a new `interpreter_argv()` helper (`-P` on Python 3.11+), hardens the `import_roots` link walk with `os.lstat` and fail-closed refusals, and adds the round-2 review fixes (probe `OSError`, `map_probe_entries` `ValueError`, malformed `loaded_ws` with `repr(item)`). All twenty-six acceptance tests pass along with the Done-section regression suites and mutation checks M1–M16.

## Corrections 1–7

- **Correction 1** `interpreter_argv` (lines 51–54) returns `[sys.executable, "-P"]` when `sys.version_info >= (3, 11)`; `pytest_env` (lines 1393–1423) sets no `PYTHONSAFEPATH`; probe, resolution check, `run_mutant_tests`, and checkpoint pytest use `interpreter_argv() + [...]` at lines 307, 1550, 1682, and 1846.
- **Correction 2** `validate_import_roots` (lines 213–222): each component uses `os.lstat` with `FileNotFoundError`/`NotADirectoryError` ending the walk, other `OSError`/`ValueError` refusing with the link line, and `stat.S_ISLNK` or `st_reparse_tag` refusing as a link (no `lexists` or `bridge_env.is_link`).
- **Correction 3** `docs/BUILDER_NOTES.md`: the 2026-11-24 TASK-085-r2 line now states `-m` cwd-first behavior and that `-P` is preferred over inheriting `PYTHONSAFEPATH`.
- **Correction 4** `run_interpreter_path_probe` (lines 308–311): `run_process` is called inside `try`/`except OSError` returning `[]`.
- **Correction 5** `map_probe_entries` (line 282): `os.path.realpath` errors catch `ValueError` as well as `OSError` and `TypeError`.
- **Correction 6** `run_resolution_check` (lines 1593–1595): a non-dict `loaded_ws` item uses `place = repr(item)` with empty `mod`.
- **Correction 7** This report applies, runs, and reverts every M1–M16 mutation in this round with quoted pytest summary lines below; Done steps 1–12 were run after the last code edit (except this file).

## Scratch tests

no scratch test file

## Mutation self-check (M1–M16)

- **M1** (probe entries ignored): `6 failed, 20 passed in 52.45s` — `test_task085_path_entry_under_nested_source_folder_kills_the_mutant` (among five others)
- **M2** (mapped after copy root on `PYTHONPATH`): `1 failed, 25 passed in 60.63s (0:01:00)` — `test_task085_mapped_roots_stand_ahead_of_the_copy_root`
- **M3** (Windows case-sensitive compare): `26 passed in 64.75s (0:01:04)` — **not caught**; `test_task085_path_entry_compared_without_regard_to_letter_case_on_windows` still passes when comparison is not case-folded on this host
- **M4** (absolute refusal removed): `1 failed, 25 passed in 65.65s (0:01:05)` — `test_task085_import_roots_absolute_entry_refused`
- **M5** (`..` refusal removed): `3 failed, 23 passed in 66.00s (0:01:06)` — `test_task085_import_roots_entry_leaving_the_workspace_refused`
- **M6** (link refusal removed): `1 failed, 25 passed in 64.41s (0:01:04)` — `test_task085_import_roots_entry_through_a_link_refused`
- **M7** (`import_roots` out of cache key): `1 failed, 25 passed in 58.13s` — `test_task085_import_roots_is_part_of_the_cache_key`
- **M8** (dotted roots only `""` and `src/`): `2 failed, 24 passed in 65.82s (0:01:05)` — `test_task085_dotted_name_under_import_roots_refuses_a_module_resolving_outside`, `test_task085_mapped_folder_keeps_its_letter_case_for_the_dotted_name`
- **M9** (R7 cause/key dropped): `1 failed, 25 passed in 61.02s (0:01:01)` — `test_task085_finder_only_refused_with_the_cause_and_the_key_named`
- **M10** (checkpoint absent root refuses): `1 failed, 25 passed in 58.63s` — `test_task085_checkpoint_skips_an_import_root_absent_at_the_commit`
- **M11** (case-folded relpath in `map_probe_entries`): `26 passed in 61.40s (0:01:01)` — **not caught**; would need a layout where the copy folder path must preserve probe letter case on this host
- **M12** (Workspace as given not real): `1 failed, 25 passed in 58.45s` — `test_task085_workspace_reached_through_a_link_still_maps_its_entries`
- **M13** (`min_copy is None` path_ahead removed): `1 failed, 25 passed in 60.89s (0:01:00)` — `test_task085_workspace_entry_with_no_copy_entry_on_the_path_refused`
- **M14** (walk ends on unreadable `OSError`): `26 passed in 61.85s (0:01:01)` — **not caught**; would need a path component that raises `OSError` other than missing without presenting as a link on this host
- **M15** (`PYTHONSAFEPATH=1` back in `pytest_env`): `1 failed, 25 passed in 59.54s` — `test_task085_a_script_started_by_a_test_still_imports_its_neighbour`
- **M16** (`interpreter_argv` without `-P` on every version): `1 failed, 25 passed in 60.95s (0:01:00)` — `test_task085_mapped_roots_stand_ahead_of_the_copy_root`

## Missing acceptance cases

none

## Commands and output

Commit for counts: `19d73eac7318483f2343cdbbef3c4f33e226390b`. Working tree after step 12 holds uncommitted changes (`MANIFEST.json`, `mutation-run.py`, `docs/BUILDER_NOTES.md`, this report).

### 1. `git status --short`

```
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/mutation-run.py
 M docs/BUILDER_NOTES.md
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
 M docs/BUILDER_NOTES.md
```

(`bridge/cursor-bridge/VERSION` not listed.)

### 5. `python -m pytest -p no:cacheprovider -q -rs tests/test_improve_mutation_editable.py`

```
..........................                                               [100%]
26 passed in 61.70s (0:01:01)
```

### 6. `python -m pytest -p no:cacheprovider -q -rs tests/test_mutation_run.py tests/test_mutation_run_supervisor.py tests/test_program_mutation_baseline.py tests/test_bug030.py tests/test_bug032.py`

```
202 passed, 2 skipped in 927.41s (0:15:27)
=========================== short test summary info ===========================
SKIPPED [1] tests/test_mutation_run.py:979: this account cannot create a symbolic link here ([WinError 1314] A required privilege is not held by the client: '<tmp>/real_scratch' -> '<tmp>/link_scratch')
SKIPPED [1] tests/test_mutation_run_supervisor.py:1218: a symbolic link cannot be made here
```

### 7. `python -m pytest -p no:cacheprovider -q -rs tests/test_allowlist.py tests/test_bridge_run_driver.py tests/test_dump_cli.py tests/test_loop_text_pace.py tests/test_loop_text_windowless.py tests/test_program_trace_moves.py tests/test_release_b2_stamp.py tests/test_release_t_floor.py tests/test_release_t_merge.py tests/test_release_t_stage_close.py tests/test_release_t_stamp.py`

```
525 passed, 20 skipped in 166.72s (0:02:46)
```

### 8. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`

```
bridge-check: version 2026.11.23a (2026-11-24 13:12) at <Workspace>/bridge
bridge-check: 148 OK, 0 STALE, 0 MISSING, 0 EXTRA
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
 bridge/cursor-bridge/MANIFEST.json   |  4 ++--
 bridge/cursor-bridge/mutation-run.py | 40 +++++++++++++++++++++++-------------
 docs/BUILDER_NOTES.md                |  2 +-
 3 files changed, 29 insertions(+), 17 deletions(-)
```

### 12. `git rev-parse HEAD` and `git status --short`

```
19d73eac7318483f2343cdbbef3c4f33e226390b
 M bridge/cursor-bridge/MANIFEST.json
M  bridge/cursor-bridge/mutation-run.py
 M docs/BUILDER_NOTES.md
```

(`bridge/cursor-bridge/VERSION` not listed; no `tests/test_task085_scratch_` file.)

## Assumed, not verified

Assumed, not verified: none