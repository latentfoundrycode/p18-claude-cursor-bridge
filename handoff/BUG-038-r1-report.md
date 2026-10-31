# BUG-038 builder report (round 1)

## Initial git status

Command: `git status --porcelain` from Workspace root (before any edit).

Output: (empty)

Note: the brief expected `tests/test_bug038.py` as untracked; on this tree it is already committed and the working tree was clean.

## Pre-edit verification

Command: `python tools/dump-cli.py --help`

Output includes: `--check     compare committed reference files without writing` (compare-only mode).

Command: `PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider tests/test_bug038.py tests/test_completion_check.py`

Exit code: 1. Summary: `3 failed, 3 passed in 1.85s`.

- `test_bug038_the_completion_check_finds_no_stand_in_in_its_own_source` — failed at `assert "STAND-IN" not in out` (STAND-IN on completion-check.py lines 30–31).
- `test_bug038_a_stand_in_elsewhere_is_still_found` — failed at `assert not [l for l in out.splitlines() if l.startswith("STAND-IN: ") and "completion-check.py" in l]`.
- `test_bug038_the_docstring_still_names_each_kind_it_scans_for` — failed at `para = doc[doc.index("STAND-IN"):...]` with `ValueError: substring not found` (the test’s `doc = text[:text.index('"""', 3)]` slice is only the shebang line because the opening `"""` is the first match after index 3).

The brief stated tests 1–2 fail and test 3 passes before edit; on this tree all three failed.

## Files changed

- `bridge/cursor-bridge/completion-check.py` (STAND-IN docstring paragraph only, lines 29–33 after edit)
- `docs/BUILDER_NOTES.md` (one dated line on test 3 doc extraction vs shebang)
- `handoff/BUG-038-r1-report.md` (this file)

## What changed

Reworded the `--mode done` STAND-IN paragraph in the module docstring so each line avoids `STANDIN_RX` while still describing the same stand-in kinds (including Section on placeholder suffixes) and keeping the closing sentence byte-identical.

New paragraph (STAND-IN block):

```
  STAND-IN    shipped (non-test) code shows a user-visible stand-in: a feature deferred to a
              later release or version; phrasing that something will come soon; behavior that is
              not implemented or still unavailable; copy saying the product is under active
              construction; a named placeholder component suffix (View, Page, Screen, Tab, Panel,
              Section); or Rust code calling the todo or unimplemented macros with arguments.
              Allowed only on a line that names the ID of an owner-deferred requirement.
```

The named cause is addressed because the line-by-line stand-in scan no longer matches its own docstring text; tests 1 and 2 now pass.

## Commands run (post-edit, Workspace root)

### Done step 1 (before step 2 in brief order; step 3 repeats)

```
$env:PYTHONDONTWRITEBYTECODE = "1"; python -c "import importlib.util as u; ..."
```

(bash equivalent run)

Output:

```
[]
matches: 0
```

Exit code: 0

### Done step 2

```
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider tests/test_bug038.py tests/test_completion_check.py
```

Exit code: 1. Summary: `1 failed, 5 passed in 1.93s`.

Failed: `test_bug038_the_docstring_still_names_each_kind_it_scans_for` at `doc.index("STAND-IN")` — `ValueError: substring not found` (same shebang/`text.index('"""', 3)` slice issue as pre-edit).

### Done step 3 (repeat step 1)

Output:

```
[]
matches: 0
```

### Done step 4

```
PYTHONDONTWRITEBYTECODE=1 python tools/dump-cli.py --check
```

Exit code: 0

### Done step 5

```
git diff --quiet HEAD -- tests/
```

Exit code: 0

```
git status --porcelain
 M bridge/cursor-bridge/completion-check.py
```

```
git diff --stat
 bridge/cursor-bridge/completion-check.py | 8 +++++---
 1 file changed, 5 insertions(+), 3 deletions(-)
```

(`git diff bridge/cursor-bridge/completion-check.py` — only the STAND-IN paragraph hunk, as recorded in shell output above.)

## Summary

Reworded the STAND-IN paragraph in `completion-check.py` so no source line matches `STANDIN_RX`, fixing the self-match that blocked `--mode done` on the shipped completion check; `matches: 0`, tests 1–2 and all of `test_completion_check.py` pass, and `dump-cli.py --check` passes. Test 3 still fails because `text[:text.index('"""', 3)]` does not include the module docstring when a shebang precedes the opening triple quote; the paragraph content satisfies test 3’s keyword checks when the docstring is extracted normally (e.g. `ast.get_docstring`).

## Assumed, not verified

- The brief’s claim that test 3 passes before edit on the supervisor tree · this workspace run showed test 3 failing pre-edit for the same doc-slice reason · a supervisor re-run on their host would confirm whether their tree differs.
- That rewording “under active construction” and “come soon” (not “coming soon”) is clear enough for readers · the brief asked for plain words naming each scan kind · a doc review would confirm.
- That omitting explicit prose for regex branches such as `to be implemented` and `not yet built/supported` is acceptable because the paragraph still describes the same stand-in families in other words · requirement 2 lists those patterns · supervisor judgment on the docstring requirement.
