# TASK-074 round 3 report

## Files changed or created

- `bridge/cursor-bridge/bridge-check.py`
- `bridge/cursor-bridge/MANIFEST.json` (regenerated via `python tools/make-manifest.py`)
- `handoff/TASK-074-r3-report.md`

## Summary

Round 3 replaces round 2's program-tree formula with `os.path.dirname(os.path.realpath(HERE))`, adds a `cursor-bridge` folder-name refusal, runs manifest hashing and the EXTRA walk under the resolved `--root`, escapes C0 control characters and embedded double quotes on folders printed under `--sources`, and relabels the refusal line so the fourth quoted path is `(cursor-bridge: ...)` rather than `(tree: ...)`.

## R1–R7

- **R1:** `main()` lines 179–181 set `here_tree = os.path.dirname(here_folder)` after `here_folder = os.path.realpath(HERE)`; line 202 compares `here_tree` to `check_tree` with `os.path.normcase`.
- **R2:** `main()` lines 198–201 refuse when `os.path.basename(here_folder)` is not `cursor-bridge` (compared with `os.path.normcase`).
- **R3:** `main()` line 208 assigns `root = check_tree` before the manifest hash loop (lines 213–225) and EXTRA walk (lines 256–263); lines 265–267 and 276–282 print paths through `escape_folder` where `--sources` names the tree or program folder.
- **R4:** `escape_folder()` lines 39–57 escape U+0000–U+001F as `\n`, `\r`, `\t`, or `\xNN`, and `"` as `\"`; backslashes and spaces are left literal.
- **R5:** `main()` lines 179–190 catch only `(OSError, ValueError)` around resolving `HERE` and `root`, set `resolve_failed`, and lines 192–197 refuse without hashing.
- **R6:** `here_abs` and `root_abs` are gone; refusal prints use labels `program`, `cursor-bridge` (for the asked tree's `cursor-bridge` folder), and a single `RESULT: REFUSED` line per run.
- **R7:** Refusal samples and mutation output are quoted below.

## Done step 5 refusal line

Command:

```
python bridge/cursor-bridge/bridge-check.py --root 'no such/tree B' --sources --quiet
```

```
RESULT: REFUSED - this program stands in tree "<Workspace>/bridge" (program: "<Workspace>/bridge/cursor-bridge") but was asked to check tree "<Workspace>/no such/tree B" (cursor-bridge: "<Workspace>/no such/tree B/cursor-bridge"); run "<Workspace>/no such/tree B/cursor-bridge/bridge-check.py" instead.
```

## Done step 6 refusal line

Command:

```
python bridge/cursor-bridge/bridge-check.py --root '\\.\CON\sub' --sources --quiet
```

```
RESULT: REFUSED - this program stands in tree "<Workspace>/bridge" (program: "<Workspace>/bridge/cursor-bridge") but was asked to check tree "<Workspace>/CON/sub" (cursor-bridge: "<Workspace>/CON/sub/cursor-bridge"); run "<Workspace>/CON/sub/cursor-bridge/bridge-check.py" instead.
```

## Mutation self-check

**M1** — the program's tree computed as `os.path.realpath(os.path.join(HERE, os.pardir))` again (replace `here_tree = os.path.dirname(here_folder)` with `here_tree = os.path.realpath(os.path.join(HERE, os.pardir))`).

```
python -m pytest -p no:cacheprovider -q tests/test_program_release_tooling.py
```

```
2 failed, 13 passed in 7.80s
```

Caught by `test_r093_r3_a_program_reached_through_a_link_from_another_tree_is_refused_for_that_tree` and `test_r093_r3_a_program_whose_own_folder_is_a_link_into_a_tree_checks_that_tree`.

**M2** — the `cursor-bridge` name check of R2 removed (delete the `os.path.basename(here_folder)` block).

```
python -m pytest -p no:cacheprovider -q tests/test_program_release_tooling.py
```

```
1 failed, 14 passed in 8.37s
```

Caught by `test_r093_r3_a_copy_of_the_program_in_a_folder_of_another_name_is_refused`.

**M3** — the hashing (and the EXTRA walk) under the unresolved `root` again (omit `root = check_tree`).

```
python -m pytest -p no:cacheprovider -q tests/test_program_release_tooling.py
```

```
15 passed in 8.03s
```

not caught — every acceptance layout that agrees on trees uses a `--root` whose resolved path equals the spelling passed to `os.path.join` for file access.

**M4** — the escape of R4 removed (`escape_folder` returns `path` unchanged).

```
python -m pytest -p no:cacheprovider -q tests/test_program_release_tooling.py
```

```
1 failed, 14 passed in 8.10s
```

Caught by `test_r093_r3_a_folder_name_cannot_add_a_result_line`.

**M5** — the `except` of R5 removed (bare `os.path.realpath` for `HERE` and `root`, no `resolve_failed` branch).

```
python -m pytest -p no:cacheprovider -q tests/test_program_release_tooling.py
```

```
1 failed, 14 passed in 7.66s
```

Caught by `test_r093_r3_a_folder_that_raises_while_resolved_is_refused_without_a_traceback`.

## Verification commands

**1.** `git status --short`

```
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/bridge-check.py
```

**2.** `python tools/make-manifest.py`

```
make-manifest: version 2026.11.12a, 148 files hashed, VERSION + MANIFEST.json written
```

**3.** `python -m pytest -p no:cacheprovider -q tests/test_program_release_tooling.py tests/test_install_check.py`

```
................................                                         [100%]
32 passed in 29.95s
```

**4.** `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`

```
bridge-check: version 2026.11.12a (2026-11-22 05:07) at <Workspace>/bridge
bridge-check: 148 OK, 0 STALE, 0 MISSING, 0 EXTRA
RESULT: SOURCES MATCH bridge 2026.11.12a <Workspace>/bridge/cursor-bridge
```

(exit 0)

**5.** See R7 section above (exit 2).

**6.** See R7 section above (exit 2, no `Traceback`).

**7.** `python tools/dump-cli.py --check`

```
docs/cli-reference.json
docs/CLI_REFERENCE.md
```

(exit non-zero; docstring exit-2 clause added for R2 — supervisor regenerates CLI docs.)

**8.** `python -c "[open(p,'rb').read().decode('ascii') for p in ('bridge/cursor-bridge/bridge-check.py','tools/make-manifest.py')]; print('ascii ok')"`

```
ascii ok
```

**9.** `git diff -- bridge/cursor-bridge/VERSION`

```
(no output)
```

**10.** `git rev-parse HEAD` and `git status --short`

```
7fdc7fc84a08c70f458838ef78cd0caae799111f
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/bridge-check.py
```

Results above belong to commit `7fdc7fc84a08c70f458838ef78cd0caae799111f` with uncommitted changes as shown.

## Assumed, not verified

- DEL (U+007F) and line-breaking characters U+0085, U+2028, and U+2029 are not escaped in `escape_folder` — only C0 (U+0000–U+001F) and `"` are — because no test supplies them and the brief allows naming that gap.
- POSIX `os.path.realpath` behaviour when the program's own directory is a symlink into another tree is exercised on CI's Ubuntu runner but not on this Windows-only builder run — reliance is on `test_r093_r3_a_program_whose_own_folder_is_a_link_into_a_tree_checks_that_tree` in CI.
- M3 would only fail if a test used a `--root` spelling that resolves differently from the path used for `os.path.join` while the tree-comparison still agreed — no such layout appears in the acceptance file.