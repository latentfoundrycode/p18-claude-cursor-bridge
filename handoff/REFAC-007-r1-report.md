# REFAC-007 round 1 report

## Files changed

- `bridge/cursor-bridge/trace-check.py`
- `bridge/cursor-bridge/MANIFEST.json`
- `handoff/REFAC-007-r1-report.md` (this file)

## Summary

Option (a): added module-level helper `instruction_paths_from_git(root, git_args)` with the shared git-listing body; `instruction_paths_in_rev` and `changed_instruction_paths` are one-line wrappers that pass the same argument lists as before. Regenerated `MANIFEST.json` via `make-manifest.py`. No CLI reference or docs changes were required.

## Start state

```text
git status --short

```

Working tree before edits: clean (no uncommitted changes).

```text
git rev-parse HEAD
d078757c3df387a2263cf76db95a230548010218
```

## Requirements 1 (grep before edit)

```text
git grep -n -e instruction_paths_in_rev -e changed_instruction_paths -- bridge/
bridge/cursor-bridge/trace-check.py:635:def instruction_paths_in_rev(root, rev):
bridge/cursor-bridge/trace-check.py:655:def changed_instruction_paths(root, base, head):
bridge/cursor-bridge/trace-check.py:677:    paths, err = instruction_paths_in_rev(root, head)
bridge/cursor-bridge/trace-check.py:738:    changed_paths, err = changed_instruction_paths(root, base, head)
```

Four lines, all in `bridge/cursor-bridge/trace-check.py`, as required.

```text
git grep -n -e instruction_paths_from_git -- bridge/cursor-bridge/trace-check.py

```

(exit code 1, no matches — helper name unused before edit.)

## Pytest (before edit)

Commit: `d078757c3df387a2263cf76db95a230548010218`. Working tree: clean.

```text
python -m pytest -p no:cacheprovider -q -rs tests/test_program_trace_moves.py tests/test_trace_check.py tests/test_trace_full_split.py
...........................................................s..sss....... [ 87%]
..........                                                               [100%]
=========================== short test summary info ===========================
SKIPPED [1] tests\test_trace_check.py:483: this account cannot create a symbolic link
SKIPPED [3] tests\test_trace_check.py:548: this account cannot create a symbolic link
78 passed, 4 skipped in 50.29s
```

## Post-edit verification

```text
python tools/make-manifest.py
make-manifest: version 2026.11.12a, 146 files hashed, VERSION + MANIFEST.json written
```

```text
python tools/dump-cli.py --check

```

(exit code 0, no output.)

```text
python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet
bridge-check: version 2026.11.12a (2026-11-14 02:03) at <Workspace>\bridge
bridge-check: 146 OK, 0 STALE, 0 MISSING, 0 EXTRA
RESULT: SOURCES MATCH bridge 2026.11.12a
```

```text
git diff --numstat -- bridge/cursor-bridge/VERSION

```

(empty — no diff.)

## Pytest (after last edit)

Commit: `d078757c3df387a2263cf76db95a230548010218`. Working tree: uncommitted changes (`M` on `trace-check.py` and `MANIFEST.json`, `??` this report).

```text
python -m pytest -p no:cacheprovider -q -rs tests/test_program_trace_moves.py tests/test_trace_check.py tests/test_trace_full_split.py
...........................................................s..sss....... [ 87%]
..........                                                               [100%]
=========================== short test summary info ===========================
SKIPPED [1] tests\test_trace_check.py:483: this account cannot create a symbolic link
SKIPPED [3] tests\test_trace_check.py:548: this account cannot create a symbolic link
78 passed, 4 skipped in 49.69s
```

## End state

```text
git status --short
 M bridge/cursor-bridge/MANIFEST.json
 M bridge/cursor-bridge/trace-check.py
?? handoff/REFAC-007-r1-report.md
```

Working tree after edits: uncommitted changes on the two bridge files plus this new report.

```text
git diff --stat
 bridge/cursor-bridge/MANIFEST.json  |  4 ++--
 bridge/cursor-bridge/trace-check.py | 26 +++++++-------------------
 2 files changed, 9 insertions(+), 21 deletions(-)
```

```text
git rev-parse HEAD
d078757c3df387a2263cf76db95a230548010218
```

## Behaviour unchanged

The helper runs the same `git_run` calls with byte-identical argument lists, preserves the same control flow and error strings (`"command failed"`, `"cannot be read as UTF-8"`), the same NUL split, filter, sort, and `(paths, None)` / `(None, err)` returns; wrappers leave public signatures and caller lines untouched.

## Noticed, not changed

The full-mode `git ls-tree` loop near line 953 remains a separate duplicate of similar listing logic (out of scope). Error branches for `"command failed"` and `"cannot be read as UTF-8"` in the two move-mode listings still lack dedicated tests (pre-existing).

## Assumed, not verified

Assumed, not verified: none
