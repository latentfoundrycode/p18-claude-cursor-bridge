# HOTFIX-002 builder report (r1)

## Files changed or created

- `bridge/cursor-bridge/records-check.py` (created)
- `bridge/cursor-bridge/stage-diff.py` (created)
- `handoff/HOTFIX-002-r1-report.md` (created)

## Summary

Created `records-check.py` and `stage-diff.py` from commit `c0822c0` by moving each program's `argparse.ArgumentParser` construction out of `main()` into a module-level `build_parser()` directly above `main()`, matching `sync-check.py`; `main()` now calls `build_parser().parse_args()` and all other logic is unchanged. Files were written with a short Python script that reads the git blobs in binary and applies a single in-place substitution so UTF-8 and line endings match the source commit.

## Verification

### 1. `git status --porcelain` (before)

```
```

### 2. Pytest

Command: `python -m pytest tests/test_hotfix25a_stage_records_install.py -q -p no:cacheprovider`

```
7 passed in 23.74s
```

### 3. `build_parser` check

Command: `python -c "import ast,sys; ..."` then exit code.

Exit code: `0`

### 4. `git diff --no-index` (records-check.py)

```
warning: in the working copy of '<temporary folder>/hotfix002-c0822c0-records-check.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'bridge/cursor-bridge/records-check.py', LF will be replaced by CRLF the next time Git touches it
diff --git "a/<temporary folder>/hotfix002-c0822c0-records-check.py" b/bridge/cursor-bridge/records-check.py
index 3bd4963..533d892 100644
--- "a/<temporary folder>/hotfix002-c0822c0-records-check.py"
+++ b/bridge/cursor-bridge/records-check.py
@@ -88,12 +88,16 @@ def commits(since, ref):
     return found
 
 
-def main():
+def build_parser():
     ap = argparse.ArgumentParser(description="Every TASK/BUG/FIX id merged since a commit has its docs/CHANGES.md line.")
     ap.add_argument("--since", required=True, help="the stage's first checkpoint commit")
     ap.add_argument("--ref", default="origin/main")
     ap.add_argument("--changes", default="docs/CHANGES.md")
-    a = ap.parse_args()
+    return ap
+
+
+def main():
+    a = build_parser().parse_args()
     if git("rev-parse", "--is-inside-work-tree") is None:
         print("records-check: not inside a git repository; cannot read")
         return 2
```

Exit code: `1` (expected; files differ)

### 5. `git diff --no-index` (stage-diff.py)

```
warning: in the working copy of '<temporary folder>/hotfix002-c0822c0-stage-diff.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'bridge/cursor-bridge/stage-diff.py', LF will be replaced by CRLF the next time Git touches it
diff --git "a/<temporary folder>/hotfix002-c0822c0-stage-diff.py" b/bridge/cursor-bridge/stage-diff.py
index 003f3fb..f5f1da9 100644
--- "a/<temporary folder>/hotfix002-c0822c0-stage-diff.py"
+++ b/bridge/cursor-bridge/stage-diff.py
@@ -144,14 +144,18 @@ def whole_tree(last, setback):
         shutil.rmtree(work, ignore_errors=True)
 
 
-def main():
+def build_parser():
     ap = argparse.ArgumentParser(description="Write a stage's whole change and its parts from its squash commits.")
     ap.add_argument("commits", nargs="*")
     ap.add_argument("--from-file")
     ap.add_argument("--out", required=True)
     ap.add_argument("--name", default="")
     ap.add_argument("--ref", default="origin/main")
-    a = ap.parse_args()
+    return ap
+
+
+def main():
+    a = build_parser().parse_args()
     if a.name and not NAME_RX.match(a.name):
         print("stage-diff: --name %r holds a character a file name should not; use letters, digits, '.', '_' or '-'. Nothing was written." % a.name)
         return 2
```

Exit code: `1` (expected; files differ)

### 6. `git status --porcelain` (after)

```
?? bridge/cursor-bridge/records-check.py
?? bridge/cursor-bridge/stage-diff.py
?? handoff/HOTFIX-002-r1-report.md
```

## Behavior vs `c0822c0`

Both programs still build the same `ArgumentParser` with the same arguments and defaults; only the call site moved from `ap.parse_args()` inside `main()` to `build_parser().parse_args()`, so runtime behavior, output, and exit codes are unchanged.

## Builder notes

- 2026-10-25: Verification commands in the brief name PowerShell (`$env:TEMP`, `$LASTEXITCODE`); this run used bash with `tempfile.gettempdir()` and `$?` for the same checks.

## Assumed, not verified

- The `c0822c0` blobs use LF line endings only · `git diff --no-index` showed only the parser-move hunks with CRLF warnings, not a whole-file rewrite · `python -c` comparing raw byte lengths and hashes of blob vs written file.
- Binary blob write preserved the em dash and en dash in `TRAIL_RX` on line 36 of `records-check.py` · substitution was on ASCII-only `def main()` block · acceptance tests passed including records-check behavior.
- Pytest success depended only on the two new programs and pre-existing branch fixtures · no other workspace files were modified · `git status --porcelain` after the run listed only the two programs and this report.
