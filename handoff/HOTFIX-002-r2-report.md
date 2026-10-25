# HOTFIX-002 round 2 builder report

## Files changed or created

- `bridge/cursor-bridge/conformance-check.py` (module docstring only)
- `handoff/HOTFIX-002-r2-report.md` (this file)

## Summary

Replaced the parenthesised absolute-path examples in the `conformance-check.py` module docstring with prose that names the same patterns `ABSOLUTE_PATH` matches (Windows drive letter with colon and slash, macOS home under root Users, Linux home under root home), without embedding drive-letter paths or the `/Users/` or `/home/` substrings that `test_dump_cli.py` rejects in generated CLI reference text.

## Verification

### 1. `git status --porcelain` (before)

```
```

### 2. Pytest (before)

Command: `python -m pytest "tests/test_dump_cli.py::test_cfgb3b_output_is_identical_on_two_computers_and_holds_no_path" -q -p no:cacheprovider`

```
1 failed in 2.13s
```

### 3. Pytest (after)

Command: `python -m pytest "tests/test_dump_cli.py::test_cfgb3b_output_is_identical_on_two_computers_and_holds_no_path" -q -p no:cacheprovider`

```
1 passed in 25.23s
```

Command: `python -m pytest tests/test_hotfix25a_conformance_semgrep.py tests/test_conformance_check.py -q -p no:cacheprovider`

```
27 passed in 18.27s
```

### 4. Docstring check (after)

Command: `python -c "import ast,re; d=ast.get_docstring(ast.parse(open('bridge/cursor-bridge/conformance-check.py',encoding='utf-8').read()),clean=False); print(bool(re.search(r'(?<![A-Za-z])[A-Za-z]:[\\\\/]', d)), '/Users/' in d, '/home/' in d)"`

```
False False False
```

### 5. `git diff -- bridge/cursor-bridge/conformance-check.py`

```
diff --git a/bridge/cursor-bridge/conformance-check.py b/bridge/cursor-bridge/conformance-check.py
index 16d0fab..f2d5e7d 100644
--- a/bridge/cursor-bridge/conformance-check.py
+++ b/bridge/cursor-bridge/conformance-check.py
@@ -35,8 +35,9 @@ What it checks, with the file it reads (the 0b review corrected several of these
   - the records: docs/PROJECT_STATUS.md, INVENTORY.md, REQUIREMENTS.md, RUN_PARAMETERS.md,
     ROSTER.json, DESIGN.md (a design under other names is a NOTE naming them), and
     docs/diagrams/INDEX.md (missing = a diagram retrofit item); a tracked (or, outside a git
-    repository, any) docs/PROJECT_STATUS.md holding an absolute path (`E:\\`, `C:/`, `/Users/`,
-    `/home/`) is MISSING (rule 54: no computer path enters a commit; FB-026);
+    repository, any) docs/PROJECT_STATUS.md holding an absolute path (a drive letter with a
+    colon and a slash, or a macOS home under root Users, or a Linux home under root home) is
+    MISSING (rule 54: no computer path enters a commit; FB-026);
   - the Workflows: line in docs/PROJECT_STATUS.md: missing, malformed, or not right after
     Phase: is MISSING (R-015);
   - with --screens (or a docs/mockups folder): the design detector in the gate;
```

### 6. `git status --porcelain` (after)

```
 M bridge/cursor-bridge/conformance-check.py
?? handoff/HOTFIX-002-r2-report.md
```

## Behaviour unchanged

The edit is documentation inside the module docstring only; `ABSOLUTE_PATH`, file-reading logic, printed messages, and exit codes are byte-for-byte the same as before.

## Builder notes

Builder notes: none

## Assumed, not verified

Assumed, not verified: none
