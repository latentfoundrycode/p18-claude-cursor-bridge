# TASK-029 round 4 report

## Files changed

- `bridge/cursor-bridge/bridge-run.py`
- `handoff/TASK-029-r4-report.md`

## Summary

After `acquire_heavy_slot` returns for a driver run, `main()` now calls `verify_driver_program_abs(cmd[1], folder)` again immediately before the Windows Job setup and both `Popen` paths; on failure it releases the slot like the `Popen` `OSError` arms, writes `DRIVER_REFUSE`, returns 125, and does not call `write_log`, closing the TOCTOU gap between the pre-wait check and process start.

## Placement

The second check sits after `slot_fd, entry["waited"] = slot_result[0], slot_result[1]` (when the heavy slot is held) and before `killer = None` and the `if sys.platform == "win32":` split, so it runs once for every driver start on both platforms and only the existing Windows Job creation and assignment sit between a passing check and `Popen`.

## Non-Windows coverage

The new block is outside the `if sys.platform == "win32":` / `else` branches, so the same re-check runs on Linux and other non-Windows platforms before the `else` branch’s `subprocess.Popen`; only Windows-only code between check and start is the Job object, which the brief already allows.

## Verification commands

### Before change

```
python -m pytest "tests/test_bridge_run_slot.py::test_r040_driver_rechecked_after_the_wait" -q -p no:cacheprovider
```

```
.F                                                                       [100%]
================================== FAILURES ===================================
_______________ test_r040_driver_rechecked_after_the_wait[True] _______________
...
>           assert launcher.returncode == 125, err
E           AssertionError: bridge-run: slot taken 2026-10-26T11:15:08Z
E             bridge-run: exit 0
...
=========================== short test summary info ===========================
FAILED tests/test_bridge_run_slot.py::test_r040_driver_rechecked_after_the_wait[True]
1 failed, 1 passed in 3.58s
```

### After change (same command)

```
..                                                                       [100%]
2 passed in 3.51s
```

### Slot file

```
python -m pytest tests/test_bridge_run_slot.py -q
```

```
.....s............................s.............s                        [100%]
46 passed, 3 skipped in 110.68s (0:01:50)
```

### Full suite

```
python -m pytest tests -q
```

```
39 failed, 2382 passed, 38 skipped, 9 errors in 537.35s (0:08:57)
```

Representative failure with modified `bridge-run.py` (install stamp check):

```
python -m pytest tests/test_install_check.py::test_dry_run_writes_nothing -q --tb=short
```

```
E   AssertionError: bridge-install: <Workspace>\bridge is not release 2026.10.25a as stamped (1 file(s): cursor-bridge/bridge-run.py (changed)); nothing was changed. Tell the maintainer.
FAILED tests/test_install_check.py::test_dry_run_writes_nothing - AssertionEr...
1 failed in 14.41s
```

With `bridge-run.py` restored to the committed tree, the same test passes (`1 passed in 11.21s`). The full-suite failures are therefore from the allowed edit versus the stamped release, not from the slot/driver logic.

### After mutations restored (slot file and full suite again)

```
python -m pytest tests/test_bridge_run_slot.py -q
```

```
46 passed, 3 skipped in 110.68s (0:01:50)
```

```
python -m pytest tests -q
```

```
39 failed, 2382 passed, 38 skipped, 9 errors in 537.35s (0:08:57)
```

### Command reference

```
python tools/dump-cli.py --check
```

(no output, exit 0)

### Windowless check

```
python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge/bridge-run.py
```

```
windowless-check: 1 file(s) scanned, 0 FAIL, 0 NOTE
```

### Diff

```
git diff -- bridge/cursor-bridge/bridge-run.py
```

```
diff --git a/bridge/cursor-bridge/bridge-run.py b/bridge/cursor-bridge/bridge-run.py
index 59c4c36..c07cf68 100644
--- a/bridge/cursor-bridge/bridge-run.py
+++ b/bridge/cursor-bridge/bridge-run.py
@@ -1348,6 +1348,16 @@ def main():
             return 123
         slot_fd, entry["waited"] = slot_result[0], slot_result[1]
 
+    if kind == "driver" and len(cmd) >= 2 and not verify_driver_program_abs(cmd[1], folder):
+        if slot_fd is not None:
+            _unlock_byte(slot_fd)
+            try:
+                os.close(slot_fd)
+            except OSError:
+                pass
+        sys.stderr.write(DRIVER_REFUSE)
+        return 125
+
     killer = None
     if sys.platform == "win32":
         try:
```

### Tree

```
git status --porcelain
```

```
 M bridge/cursor-bridge/bridge-run.py
?? handoff/TASK-029-r4-report.md
```

### Leftover processes (Windows)

```
powershell -NoProfile -Command "Get-Process python -ErrorAction SilentlyContinue | Select-Object Id,ProcessName"
```

One `python` process (Id 29940) was present after the runs; it was not tied to a specific test PID and may be unrelated to pytest. Slot tests use `kill_tree` in `finally`.

## Mutation check

Code restored after each mutant; final `git diff` matches the fix above.

1. **Removed the second check block** (only the post-slot block). Caught by `test_r040_driver_rechecked_after_the_wait[True]`. Summary: `1 failed, 1 passed in 3.57s`.
2. **Second check only in the `else` (non-Windows) branch.** Caught by `[True]` on Windows. Summary: `1 failed, 1 passed in 3.59s`. Mirror mutant (check only inside the `win32` branch before Windows `Popen`) would skip the re-check on Linux; `[True]` would likely still fail there because the swapped hard link would run and write `evil.txt`, while `[False]` would still pass.
3. **Refuse after the wait without `_unlock_byte` / `os.close`.** Survived: both parametrizations passed. Summary: `2 passed in 3.53s`. The launcher exits 125 and the OS releases the byte lock on process exit before the test’s follow-up heavy run.
4. **`write_log(folder, entry)` before `return 125` on post-wait refusal.** Caught by `[True]` (no log row assertion). Summary: `1 failed, 1 passed in 3.53s`.

## Assumed, not verified

- The Windows Job `Job()` / `assign_self()` steps do not alter the driver program path or inode the second `verify_driver_program_abs` relies on · brief allows them between check and `Popen` · would confirm by tracing or documenting Job API side effects on disk.
- On this NTFS volume, `os.link` during the test leaves `st_nlink == 2` and `_supervisor_file_ok` refuses the path · test preconditions assert it · would confirm only on a volume where hard links behave differently.
- After `return 125`, the OS releases the heavy lock before the test’s follow-up `--limit 5` run acquires the slot · mutation 3 behaved as if true · would confirm with explicit lock probing between launcher exit and follow-up (not done here).
