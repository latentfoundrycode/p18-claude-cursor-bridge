# BUG-010-r2 report

## Summary

Per r2, `CheckArgumentParser.error` was restored to the pre-fix body from the brief, `make-manifest` was run, and the pre-fix suite showed 1453 passed, 23 skipped, 2 failed; the same two `is not None` guards were then applied again so `sys.stderr.write` and `sys.stdout.flush` are skipped when the corresponding stream is `None`, after which every Done verification passed including 1455 passed and 23 skipped on the full suite.

## How the change addresses the named cause

The method no longer calls `write` on `sys.stderr` or `flush` on `sys.stdout` when that stream is `None`, which is Python's state for a standard stream the program was started without, so the AttributeError that turned a usage error into exit 1 no longer occurs.

## Files changed

- `bridge/cursor-bridge/workflow-check.py` — body of `CheckArgumentParser.error` only: guard before `sys.stderr.write`, guard before `sys.stdout.flush` (working tree matches branch HEAD commit `4595974`; see Done step 7)
- `bridge/cursor-bridge/MANIFEST.json` — regenerated twice during r2 (`make-manifest` after restore and after fix); unstaged diff vs HEAD is only the `generated` timestamp (`2026-10-18 08:14` → `2026-10-18 10:38`), file hashes unchanged
- `handoff/BUG-010-r2-report.md` — this report

`bridge/cursor-bridge/VERSION` is not in the diff. `docs/BUILDER_NOTES.md` was not changed. Every file under `tests/` is unchanged.

## Restore (r2 step 1)

Before re-implementing the fix, `CheckArgumentParser.error` was set to exactly the Context text (unconditional `sys.stderr.write` and `sys.stdout.flush`). Command: `python tools/make-manifest.py --version 2026.10.11d` (exit 0). Command: `python -m pytest tests -q` (exit 1). Relevant output: `2 failed, 1453 passed, 23 skipped in 272.64s (0:04:32)`. Failures: `test_r014_usage_error_with_a_closed_stream_exits_2_without_traceback[stdout-closed]`, `[stderr-closed]`.

## Mutation check

- M1 · `test_r014_usage_error_with_a_closed_stream_exits_2_without_traceback[stderr-closed]` (1 failed, 1 passed)
- M2 · `test_r014_usage_error_with_a_closed_stream_exits_2_without_traceback[stdout-closed]` (1 failed, 1 passed)
- M3 · `test_r014_usage_error_ends_with_result_line`, `test_r014_usage_error_message_is_escaped`, `test_r014_usage_error_with_a_closed_stream_exits_2_without_traceback[stdout-closed]`, `test_r014_usage_error_with_a_closed_stream_exits_2_without_traceback[stderr-closed]` (4 failed, 412 deselected)

## Done

### 1. Before any edit (after restore, before fix)

Command: `python -m pytest tests -q`

Working folder: Workspace root.

Exit code: 1.

Relevant output: `2 failed, 1453 passed, 23 skipped in 272.64s (0:04:32)` (same run as Restore).

### 2. After the fix

Command: `python -m pytest "tests/test_workflow_check.py::test_r014_usage_error_with_a_closed_stream_exits_2_without_traceback" tests/test_workflow_check.py::test_r014_usage_error_ends_with_result_line tests/test_workflow_check.py::test_r014_usage_error_message_is_escaped tests/test_workflow_check.py::test_r033_usage_names_the_three_times_and_the_codes tests/test_workflow_check.py::test_r014_the_usage_line_names_the_options_in_their_order -q`

Working folder: Workspace root.

Exit code: 0.

Relevant output: `6 passed in 1.73s`.

### 3. Mutants, then the restored file

M1 command: `python -m pytest "tests/test_workflow_check.py::test_r014_usage_error_with_a_closed_stream_exits_2_without_traceback" -q`

Exit code: 1. Relevant output: `FAILED ...[stderr-closed]` and `1 failed, 1 passed in 6.14s`.

M2 command: the same command.

Exit code: 1. Relevant output: `FAILED ...[stdout-closed]` and `1 failed, 1 passed in 5.46s`.

M3 command: `python -m pytest tests/test_workflow_check.py -q -k "usage_error"`

Exit code: 1. Relevant output: four failures named in the mutation list and `4 failed, 412 deselected in 1.21s`.

Fixed code restored, then command: `python -m pytest tests/test_workflow_check.py -q`

Exit code: 0. Relevant output: `415 passed, 1 skipped in 30.56s`. No manifest-refusal failures.

### 4. Manifest and source check

Command: `python tools/make-manifest.py --version 2026.10.11d`

Exit code: 0. Relevant output: `make-manifest: version 2026.10.11d, 107 files hashed, VERSION + MANIFEST.json written`.

Command: `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`

Exit code: 0. Relevant output: `bridge-check: version 2026.10.11d (2026-10-18 10:38) at <Workspace>\bridge` (path redacted by the supervisor, rule 54), `bridge-check: 107 OK, 0 STALE, 0 MISSING, 0 EXTRA`, `RESULT: SOURCES MATCH bridge 2026.10.11d`.

### 5. Full suite after the manifest

Command: `python -m pytest tests -q`

Exit code: 0. Relevant output: `1455 passed, 23 skipped in 272.93s (0:04:32)`.

### 6. Windowless check

Command: `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge`

Exit code: 0. Relevant output: `windowless-check: 30 file(s) scanned, 0 FAIL, 0 NOTE`.

### 7. Diffs

Command: `git diff --stat`

Exit code: 0. Output:

```
warning: in the working copy of 'bridge/cursor-bridge/MANIFEST.json', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'bridge/cursor-bridge/VERSION', LF will be replaced by CRLF the next time Git touches it
 bridge/cursor-bridge/MANIFEST.json | 2 +-
 1 file changed, 1 insertion(+), 1 deletion(-)
```

`handoff/BUG-010-r2-report.md` is untracked. `bridge/cursor-bridge/VERSION` does not appear in the stat.

Command: `git diff -- bridge/cursor-bridge/workflow-check.py`

Exit code: 0. Output: (empty — working tree matches HEAD, which already contains the fix from commit `4595974`).

Logical change applied in this run (broken body from the brief → fixed body; same as `git diff 529f26d HEAD -- bridge/cursor-bridge/workflow-check.py` for this method):

```
@@ -752,9 +752,11 @@ class CheckArgumentParser(argparse.ArgumentParser):
     def error(self, message):
         self.print_usage(sys.stderr)
-        sys.stderr.write("%s: error: %s\n" % (self.prog, escape_field(message)))
+        if sys.stderr is not None:
+            sys.stderr.write("%s: error: %s\n" % (self.prog, escape_field(message)))
         print("RESULT: not checked")
-        sys.stdout.flush()
+        if sys.stdout is not None:
+            sys.stdout.flush()
         self.exit(2)
```

## Assumed, not verified

Assumed, not verified: none
