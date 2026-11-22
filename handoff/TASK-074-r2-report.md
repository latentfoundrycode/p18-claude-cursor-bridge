# TASK-074 round 2 report

## Files changed or created

- `bridge/cursor-bridge/bridge-check.py`
- `tools/make-manifest.py`
- `bridge/cursor-bridge/MANIFEST.json` (via `python tools/make-manifest.py` only)
- `tests/test_install_check.py` (marker line and two R6 cases appended)
- `handoff/TASK-074-r2-report.md`

## Summary

Round 2 hardens `bridge-check.py --sources` so refusal compares the whole `--root` tree to the program's tree, catches resolve failures without a traceback, and prints a single labelled `RESULT: REFUSED` line that names both trees and points at the checked tree's own `bridge-check.py`; the SOURCES DO NOT MATCH line labels the checked folder. `make-manifest.py` now reads VERSION in a `with` block, assembles UTF-8 bytes before writing, and drops the redundant LF `elif`. Two R-093 line-ending cases were appended below the marker in `tests/test_install_check.py`. MANIFEST was regenerated; all scoped tests pass.

## Requirements (R1-R8)

- **R1:** `main()` lines 160-172 catch `OSError` and `ValueError` from `os.path.realpath` on `HERE`, its parent, and `root`; `resolve_failed` forces refusal at 174-179 with exit 2 and no hashing.
- **R2:** `main()` line 174 compares `os.path.normcase(here_tree)` to `os.path.normcase(check_tree)` where `here_tree` is `realpath` of `dirname(HERE)` and `check_tree` is `realpath(root)`; round 1's `cursor-bridge`-only comparison was removed in favour of this whole-tree check.
- **R3:** `main()` lines 176-178 print one `RESULT: REFUSED` line with quoted `program` and `tree` folders plus the alternate `bridge-check.py` path; for `--root CON` on Windows the line is `RESULT: REFUSED - this program stands in tree "<Workspace>/bridge" (program: "<Workspace>/bridge/cursor-bridge") but was asked to check tree "\\.\CON" (tree: "\\.\CON\cursor-bridge"); run "\\.\CON\cursor-bridge\bridge-check.py" instead.`; for `--root "<tmp>/tree B"` with program in `<tmp>/tree A` the same template names both spaced trees and their `cursor-bridge` subpaths in quotes.
- **R4:** `main()` line 247 appends `(checked: <folder>)` on the SOURCES DO NOT MATCH line; the SOURCES MATCH line at 253 is unchanged.
- **R5:** `main()` in `tools/make-manifest.py` lines 93-100 read VERSION inside `with open`, set `version_bytes` at 98 before the write `open` at 99, use UTF-8 encode, and omit the dead `elif` for LF.
- **R6:** Appended `test_r093_make_manifest_keeps_a_lf_version_file_lf` and `test_r093_make_manifest_writes_a_new_version_file_with_lf` below the marker in `tests/test_install_check.py`.
- **R7:** This report quotes mutants and pytest summaries in fenced blocks from the listed commands.
- **R8:** Without `--sources` behaviour is unchanged; docstring exit-2 line 28 adds "or a folder cannot be resolved"; no new options; VERSION untouched (`git diff -- bridge/cursor-bridge/VERSION` empty).

## Mutation self-check

**M1** skip the whole-root comparison (only the `cursor-bridge` comparison kept):

```python
        check_cursor_bridge = os.path.realpath(os.path.join(root, "cursor-bridge"))
        refuse = resolve_failed or os.path.normcase(here_folder) != os.path.normcase(check_cursor_bridge)
```

Command: `python -m pytest -p no:cacheprovider -q tests/test_program_release_tooling.py`

```
2 failed, 8 passed in 6.21s
```

Caught: `test_r093_r2_a_tree_whose_cursor_bridge_is_linked_into_the_program_tree_is_refused`

**M2** the resolve failure of R1 is not caught:

```python
        here_folder = os.path.realpath(HERE)
        here_tree = os.path.realpath(os.path.join(HERE, os.pardir))
        check_tree = os.path.realpath(root)
        check_cursor_bridge = os.path.join(check_tree, "cursor-bridge")
        refuse = os.path.normcase(here_tree) != os.path.normcase(check_tree)
```

Command: `python -m pytest -p no:cacheprovider -q tests/test_program_release_tooling.py`

```
10 passed in 5.47s
```

not caught: with whole-tree comparison, `--root CON` refuses on tree mismatch before any path that raised in round 1; a case that calls `os.path.realpath` on `root` where that alone raises (not merely mismatches) would catch this mutant.

**M3** the refusal line loses `RESULT: REFUSED`:

```python
            print('RESULT: DENIED - this program stands in tree "%s" ...
```

Command: `python -m pytest -p no:cacheprovider -q tests/test_program_release_tooling.py`

```
1 failed, 9 passed in 5.94s
```

Caught: `test_r093_r2_the_refusal_says_it_refused_and_names_both_folders`

**M4** make-manifest opens VERSION for writing before encoding: not caught; `version_bytes = ("%s" % version).encode("utf-8") + line_ending` is built at `tools/make-manifest.py` line 98 before `with open(version_path, "wb")` at line 99, and the version has already passed the CHANGELOG pattern at line 76 so the encode cannot fail in practice.

## Verification commands

Commit for counts: `100850a64f8be10f7f8d7b450fed37c3f696a282` (unchanged); working tree had uncommitted changes at report time.

**1.** `git status --short`

```
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/bridge-check.py
 M tests/test_install_check.py
 M tools/make-manifest.py
```

**2.** `python tools/make-manifest.py`

```
make-manifest: version 2026.11.12a, 148 files hashed, VERSION + MANIFEST.json written
```

**3.** `python -m pytest -p no:cacheprovider -q tests/test_program_release_tooling.py tests/test_install_check.py`

```
27 passed in 28.00s
```

**4.** `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`

```
bridge-check: version 2026.11.12a (2026-11-22 04:54) at <Workspace>/bridge
bridge-check: 148 OK, 0 STALE, 0 MISSING, 0 EXTRA
RESULT: SOURCES MATCH bridge 2026.11.12a <Workspace>/bridge/cursor-bridge
```

(exit 0)

**5.** `python tools/dump-cli.py --check`

```
docs/cli-reference.json
docs/CLI_REFERENCE.md
```

(exit 1; docstring exit-2 clause changed; supervisor regenerates CLI reference)

**6.** `python -c "[open(p,'rb').read().decode('ascii') for p in ('bridge/cursor-bridge/bridge-check.py','tools/make-manifest.py')]; print('ascii ok')"`

```
ascii ok
```

**7.** `git diff -- bridge/cursor-bridge/VERSION`

```
(no output)
```

**8.** `git rev-parse HEAD` and `git status --short`

```
100850a64f8be10f7f8d7b450fed37c3f696a282
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/bridge-check.py
 M tests/test_install_check.py
 M tools/make-manifest.py
```

(`bridge/cursor-bridge/VERSION` not listed)

## Assumed, not verified

- Other Windows device names besides `CON` (`NUL`, `COM1`, reserved names with extensions) that make `os.path.realpath(root)` raise versus refuse only on tree mismatch — brief pins `CON` only; exercising each name in pytest would confirm.
- Whether the quoted refusal line renders cleanly on a strict cp1252 console when paths contain characters outside that code page — tests use ASCII temp paths; a manual cp1252 run with non-ASCII path segments would confirm.
- A `VERSION` file whose last line ending is neither bare LF nor CRLF (e.g. mixed or no final newline) — R5 leaves default LF for new bytes; deleting and re-stamping on such a file would confirm behaviour.