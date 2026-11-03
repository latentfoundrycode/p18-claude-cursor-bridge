# REFAC-004 round 1 report

## Files changed

- `bridge/cursor-bridge/review-guard.py`

## Summary

Refactored `record_flagged_launch` so snapshot-time rejection runs only when `snap is not None` and before any rounds read, then a single `isfile`/`load_rounds`/entry lookup handles both branches; removed the duplicate read block and names `data_pre`, `err_pre`, and `round_time`. Removed dead code in `write_rounds` (local `import tempfile`) and in `cmd_verify` (`rounds_data = None`, `rpath = None`, and the second `id_part, rnd = parsed`). Behaviour, exit codes, and record semantics are unchanged per the brief's case table.

## Pytest (six files)

Before edit:

```
........................................................................ [ 56%]
........................................................                 [100%]
128 passed in 196.10s (0:03:16)
```

After edit:

```
........................................................................ [ 56%]
........................................................                 [100%]
128 passed in 197.06s (0:03:17)
```

## `python bridge/cursor-bridge/review-guard.py` (no arguments)

Before edit:

```
  python ~/.claude/cursor-bridge/review-guard.py snapshot <nnn>          before launching Review B
  python ~/.claude/cursor-bridge/review-guard.py verify   <nnn>          after it returns
  python ~/.claude/cursor-bridge/review-guard.py premerge <nnn> [<pr>]   after the review files are removed, committed and pushed
exit=2
```

After edit: same usage lines and `exit=2`.

## Git

```
On branch refactor/T2
Your branch is ahead of 'origin/main' by 2 commits.
  (use "git push" to publish your local commits)

Changes not staged for commit:
  (use "git add <file>..." to update what will be committed)
  (use "git restore <file>..." to discard changes in working directory)
	modified:   bridge/cursor-bridge/review-guard.py

no changes added to commit (use "git add" and/or "git commit -a")
 bridge/cursor-bridge/review-guard.py | 29 ++++++-----------------------
 1 file changed, 6 insertions(+), 23 deletions(-)
```

## Requirement checks

- **`_launch_time_ge_round` on empty time:** Confirmed in source: `if not launched_at or not round_time: return False` (lines 364–367). The `snap is None` guard uses `_launch_time_ge_round(launched_at, entry.get("time"))` only; no extra `not round_time` test was kept.
- **`rounds_data` and `rpath`:** Before edit, both were set to `None` then assigned only inside `if parsed:`; reads were at lines 1072 (inside `if parsed:`) and 1081–1086 (inside `if parsed and exit_code == 0 and launch_ok:`). No earlier path read them unbound. Removed `rounds_data = None` and `rpath = None`.
- **`id_part` / `rnd` between the two `cmd_verify` blocks:** After `if parsed:` binds them at the first unpack, neither name is rebound before the `if parsed and exit_code == 0 and launch_ok:` block. Removed the second `id_part, rnd = parsed`.
- **Lines kept under Requirements 2, 5, or 6:** None.

## Behaviour identical (one sentence)

Every branch in the Context table is preserved: snapshot-before-read when `snap` is given, one `load_rounds` with the same tamper side effect, the same early returns for `snap is None` including no `write_rounds` when there is no matching entry, and `write_rounds` still run when `snap` is given even without a matching round entry.

## Manifest

`bridge/cursor-bridge/MANIFEST.json` is now stale for `cursor-bridge/review-guard.py`; the supervisor should regenerate it.

## Noticed, not changed

Nothing beyond the scoped refactor was changed.

## Assumed, not verified

Assumed, not verified: none.
