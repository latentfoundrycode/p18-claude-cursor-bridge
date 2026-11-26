# REFAC-016 round 1 report

## Files changed

- `bridge/cursor-bridge/mutation-run.py`
- `bridge/cursor-bridge/MANIFEST.json`
- `handoff/REFAC-016-r1-report.md`

## Summary

Part 1 introduced `run_paths()` so checkpoint and ordinary `main()` paths share one seven-step probe-and-map sequence and return `(ir_active, mapped_active, path_kw)`. Part 2 replaced the inlined checkpoint pytest driver with `run_mutant_tests(..., [item], ...)`, discarding only the still-alive return value. Part 3 merged `pytest_env`'s two root loops into one pass over `list(import_roots_rel) + list(mapped_roots_rel)` without the `"."` branch. Part 4 added module-level `DEFAULT_DOTTED_PREFIXES` and routed all five former literal sites through it. Part 5 collapsed the generated resolution plugin's `_in_workspace` and `_in_copy` into `_under(ap, a, b)` with the same call argument order. Regenerated `MANIFEST.json` via `tools/make-manifest.py`. Behaviour is unchanged except the ephemeral generated plugin source text; JSON output and all runtime paths, env vars, and exit codes stay the same.

## Start state

```text
$ git status --short
(empty)

$ git rev-parse HEAD
bc3bcd78e44220847efdecea1b33cb3a20d5708d
```

Working tree at start: clean (no uncommitted changes).

## Requirement 1 (before any edit)

```text
$ git grep -n -e "run_interpreter_path_probe(" -e "map_probe_entries(" -e "dotted_ps" -- bridge/cursor-bridge/mutation-run.py
bridge/cursor-bridge/mutation-run.py:306:def map_probe_entries(probe_paths, workspace, copy_root):
bridge/cursor-bridge/mutation-run.py:341:def run_interpreter_path_probe(plugin_dir, tree_root, env, timeout_sec):
bridge/cursor-bridge/mutation-run.py:1848:            probe_paths = run_interpreter_path_probe(plugin_dir, copy_root, env, timeout_sec)
bridge/cursor-bridge/mutation-run.py:1849:            mapped_all = map_probe_entries(probe_paths, workspace, copy_root)
bridge/cursor-bridge/mutation-run.py:1852:            dotted_ps = module_dotted_prefixes(ir_active, mapped_active)
bridge/cursor-bridge/mutation-run.py:1854:                import_roots_rel=ir_active, mapped_roots_rel=mapped_active, dotted_prefixes=dotted_ps)
bridge/cursor-bridge/mutation-run.py:1947:        probe_paths = run_interpreter_path_probe(plugin_dir, copy_root, env, timeout_sec)
bridge/cursor-bridge/mutation-run.py:1948:        mapped_all = map_probe_entries(probe_paths, workspace, copy_root)
bridge/cursor-bridge/mutation-run.py:1951:        dotted_ps = module_dotted_prefixes(ir_active, mapped_active)
bridge/cursor-bridge/mutation-run.py:1953:            import_roots_rel=ir_active, mapped_roots_rel=mapped_active, dotted_prefixes=dotted_ps)
```

The two seven-line sites (checkpoint 1848–1854 at 12-space indent, ordinary 1947–1953 at 8-space indent) are identical apart from indentation: same calls in the same order (`run_interpreter_path_probe`, `map_probe_entries`, `active_mapped_roots`, `active_import_roots`, `module_dotted_prefixes`, `path_kw` dict with the same three keys).

```text
$ git grep -n -w -e run_mutant_tests -e run_process -e pytest_env -e read_pytest_results -e run_process_still_alive_after_timeout -- tests
tests/test_mutation_run.py:1259:    """R-041, TASK-031 S7, handoff/TASK-031-r7.md item 3: a grandchild holding run_process's real pipes is bounded.
tests/test_mutation_run_supervisor.py:511:rc, out, err, timed = mod.run_process([sys.executable, sys.argv[2], sys.argv[3], sys.argv[4]], None, sys.argv[5], 2)
tests/test_mutation_run_supervisor.py:519:    parent gone; on POSIX a session of its own) cannot keep run_process waiting: it returns timed out within the
tests/test_mutation_run_supervisor.py:530:        pytest.fail("run_process waited on the pipes past the bound")
```

None of these lines assign or monkeypatch `run_mutant_tests`, `run_process`, `pytest_env`, `read_pytest_results`, or `run_process_still_alive_after_timeout` on the loaded program; they are docstrings, a direct call to `mod.run_process`, or assertion text. Known monkeypatches elsewhere (not among the hits above): `git` (`tests/test_mutation_run.py:275`), `kill_tree` (`tests/test_mutation_run.py:1410`, `:1487`), `git_try` (`tests/test_bug032.py:254`), `bridge_env.is_link` (`tests/test_mutation_run_supervisor.py:1244`).

```text
$ git grep -n -w -e pytest_env -- bridge/cursor-bridge/mutation-run.py
bridge/cursor-bridge/mutation-run.py:342:    probe_env = pytest_env(plugin_dir, tree_root, env)
bridge/cursor-bridge/mutation-run.py:1429:def pytest_env(plugin_dir, tree_root, env, results_path=None, import_roots_rel=(), mapped_roots_rel=()):
bridge/cursor-bridge/mutation-run.py:1581:    run_env = pytest_env(
bridge/cursor-bridge/mutation-run.py:1714:    run_env = pytest_env(
bridge/cursor-bridge/mutation-run.py:1903:                run_env = pytest_env(
```

```text
$ git grep -n -F -e src/ -- bridge/cursor-bridge/mutation-run.py
bridge/cursor-bridge/mutation-run.py:271:    prefixes = ["", "src/"]
bridge/cursor-bridge/mutation-run.py:882:    for prefix in dotted_prefixes or ("", "src/"):
bridge/cursor-bridge/mutation-run.py:1465:    for prefix in dotted_prefixes or ("", "src/"):
bridge/cursor-bridge/mutation-run.py:1552:    prefixes = dotted_prefixes or ("", "src/")
bridge/cursor-bridge/mutation-run.py:1573:    dp = dotted_prefixes or ("", "src/")
```

```text
$ git grep -n -w -e _in_workspace -e _in_copy -- bridge tests
bridge/cursor-bridge/mutation-run.py:1357:def _in_workspace(ap, nw, nwr):
bridge/cursor-bridge/mutation-run.py:1360:def _in_copy(ap, nc, ncr):
bridge/cursor-bridge/mutation-run.py:1391:        if _in_copy(ap, nc, ncr):
bridge/cursor-bridge/mutation-run.py:1397:        if _in_workspace(ap, nw, nwr):
bridge/cursor-bridge/mutation-run.py:1405:        if not _in_workspace(af, nw, nwr):
bridge/cursor-bridge/mutation-run.py:1407:        if _in_copy(af, nc, ncr):
tests/test_improve_mutation_editable.py:399:            "def _in_copy(p):\n"
tests/test_improve_mutation_editable.py:402:            "_sys.path[:] = [p for p in _sys.path if not (p and _in_copy(p))]\n"
```

```text
$ git grep -n -w -e run_paths -e DEFAULT_DOTTED_PREFIXES -e _under -- bridge
(no output, exit 1)
```

```text
$ python -c "import os; t = os.path.join(os.getcwd(), 'bridge'); print(os.path.abspath(os.path.join(t, '.')) == os.path.abspath(t), os.path.isdir(os.path.join(t, '.')) == os.path.isdir(t), os.path.normcase(os.path.abspath(os.path.join(t, '.'))) == os.path.normcase(os.path.abspath(t)))"
True True True
```

## Pytest (before edit, commit bc3bcd78e44220847efdecea1b33cb3a20d5708d, clean tree)

```text
$ python -m pytest -p no:cacheprovider -q -rs tests/test_improve_mutation_editable.py tests/test_mutation_run.py tests/test_mutation_run_supervisor.py tests/test_program_mutation_baseline.py tests/test_bug032.py
223 passed, 2 skipped in 1017.85s (0:16:57)
```

## Pytest (after last edit, commit bc3bcd78e44220847efdecea1b33cb3a20d5708d, uncommitted mutation-run + MANIFEST)

```text
$ python -m pytest -p no:cacheprovider -q -rs tests/test_improve_mutation_editable.py tests/test_mutation_run.py tests/test_mutation_run_supervisor.py tests/test_program_mutation_baseline.py tests/test_bug032.py
223 passed, 2 skipped in 970.57s (0:16:10)
```

Same counts: 223 passed, 2 skipped, none failed.

## Post-edit verification

```text
$ python tools/make-manifest.py
make-manifest: version 2026.11.24a, 148 files hashed, VERSION + MANIFEST.json written
```

```text
$ python tools/dump-cli.py --check
(empty output, exit 0)
```

```text
$ python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet
bridge-check: version 2026.11.24a (2026-11-26 03:52) at <Workspace>\bridge
bridge-check: 148 OK, 0 STALE, 0 MISSING, 0 EXTRA
RESULT: SOURCES MATCH bridge 2026.11.24a <Workspace>\bridge\cursor-bridge
```

```text
$ git diff --numstat -- bridge/cursor-bridge/VERSION
(empty)
```

```text
$ git diff --numstat -- bridge/cursor-bridge/mutation-run.py
28	50	bridge/cursor-bridge/mutation-run.py
```

### Acceptance criterion git grep (after edit)

```text
$ git grep -n -w -e run_paths -- bridge
bridge/cursor-bridge/mutation-run.py:367:def run_paths(plugin_dir, copy_root, workspace, import_roots, env, timeout_sec):
bridge/cursor-bridge/mutation-run.py:1846:            ir_active, mapped_active, path_kw = run_paths(plugin_dir, copy_root, workspace, import_roots, env, timeout_sec)
bridge/cursor-bridge/mutation-run.py:1931:        ir_active, mapped_active, path_kw = run_paths(plugin_dir, copy_root, workspace, import_roots, env, timeout_sec)
```

```text
$ git grep -n -e "run_interpreter_path_probe(" -- bridge/cursor-bridge/mutation-run.py
bridge/cursor-bridge/mutation-run.py:342:def run_interpreter_path_probe(plugin_dir, tree_root, env, timeout_sec):
bridge/cursor-bridge/mutation-run.py:368:    probe_paths = run_interpreter_path_probe(plugin_dir, copy_root, env, timeout_sec)
```

```text
$ git grep -n -w -e pytest_env -- bridge/cursor-bridge/mutation-run.py
bridge/cursor-bridge/mutation-run.py:343:    probe_env = pytest_env(plugin_dir, tree_root, env)
bridge/cursor-bridge/mutation-run.py:1438:def pytest_env(plugin_dir, tree_root, env, results_path=None, import_roots_rel=(), mapped_roots_rel=()):
bridge/cursor-bridge/mutation-run.py:1579:    run_env = pytest_env(
bridge/cursor-bridge/mutation-run.py:1712:    run_env = pytest_env(
```

```text
$ git grep -n -w -e OUTCOMES_PLUGIN_MOD -- bridge/cursor-bridge/mutation-run.py
bridge/cursor-bridge/mutation-run.py:61:OUTCOMES_PLUGIN_MOD = "_mutation_outcomes"
bridge/cursor-bridge/mutation-run.py:1716:    argv = interpreter_argv() + ["-m", "pytest", "-p", OUTCOMES_PLUGIN_MOD, "-p", "no:cacheprovider"] + cfg + tests
```

```text
$ git grep -n -F -e "os.path.normcase(ap)" -- bridge/cursor-bridge/mutation-run.py
bridge/cursor-bridge/mutation-run.py:1445:            nk = os.path.normcase(ap)
```

```text
$ git grep -n -F -e src/ -- bridge/cursor-bridge/mutation-run.py
bridge/cursor-bridge/mutation-run.py:62:DEFAULT_DOTTED_PREFIXES = ("", "src/")
```

```text
$ git grep -n -w -e DEFAULT_DOTTED_PREFIXES -- bridge
bridge/cursor-bridge/mutation-run.py:62:DEFAULT_DOTTED_PREFIXES = ("", "src/")
bridge/cursor-bridge/mutation-run.py:272:    prefixes = list(DEFAULT_DOTTED_PREFIXES)
bridge/cursor-bridge/mutation-run.py:894:    for prefix in dotted_prefixes or DEFAULT_DOTTED_PREFIXES:
bridge/cursor-bridge/mutation-run.py:1463:    for prefix in dotted_prefixes or DEFAULT_DOTTED_PREFIXES:
bridge/cursor-bridge/mutation-run.py:1550:    prefixes = dotted_prefixes or DEFAULT_DOTTED_PREFIXES
bridge/cursor-bridge/mutation-run.py:1571:    dp = dotted_prefixes or DEFAULT_DOTTED_PREFIXES
```

```text
$ git grep -n -w -e _in_workspace -e _in_copy -- bridge
(no output, exit 1)
```

```text
$ git grep -n -w -e _under -- bridge
bridge/cursor-bridge/mutation-run.py:1369:def _under(ap, a, b):
bridge/cursor-bridge/mutation-run.py:1400:        if _under(ap, nc, ncr):
bridge/cursor-bridge/mutation-run.py:1406:        if _under(ap, nw, nwr):
bridge/cursor-bridge/mutation-run.py:1414:        if not _under(af, nw, nwr):
bridge/cursor-bridge/mutation-run.py:1416:        if _under(af, nc, ncr):
```

## End state

```text
$ git status --short
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/mutation-run.py
?? handoff/REFAC-016-r1-report.md
```

```text
$ git diff --stat
 bridge/cursor-bridge/MANIFEST.json   |  4 +-
 bridge/cursor-bridge/mutation-run.py | 78 +++++++++++++-----------------------
 2 files changed, 30 insertions(+), 52 deletions(-)
```

```text
$ git rev-parse HEAD
bc3bcd78e44220847efdecea1b33cb3a20d5708d
```

Working tree at end: uncommitted changes to `mutation-run.py` and `MANIFEST.json`; new report file.

## Behaviour identity

Every refactor is a straight extraction or alias of existing logic: `run_paths` and the unified `pytest_env` loop perform the same operations in the same order with the same deduplication; checkpoint items use `run_mutant_tests` which already encoded that sequence; `DEFAULT_DOTTED_PREFIXES` is the same tuple values; `_under` is logically identical to `_in_workspace` and `_in_copy` with renamed parameters. Child `PYTHONPATH` construction, pytest argv, resolution JSON, stdout/stderr, and exit codes are therefore unchanged.

## Noticed, not changed

The checkpoint loop still ignores `run_process_still_alive_after_timeout()` from `run_mutant_tests` (as before). `active_mapped_roots` still skips `"."`. `run_resolution_check` still uses path comparisons with `startswith(croot_abs)` as in the base tree.

## Assumed, not verified

Assumed, not verified: none.