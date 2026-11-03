# BUG-042 round 1 builder report

## Files changed

- `bridge/cursor-bridge/conformance-check.py`
- `bridge/cursor-bridge/review-guard.py`

## Summary

The conformance check now builds `gate_workflows` and `gate_wf_text` from every workflow under `.github/workflows/` except files whose basename is `dependency-scan` with a `.yml` or `.yaml` suffix (case-insensitive), and uses those for `steps` and for each scanner's `scanner_lines`, while `workflows` and `wf_text` still include the weekly dependency scan so action pinning, runner OS, design detector, and the CLI reference check behave as before; the module docstring documents that exclusion. In `review-guard.py`, only the module docstring and `snapshot_rewritten`'s docstring were updated so exit code 1 covers a snapshot deleted with its hash copy still present, exit 2 wording matches a never-taken snapshot, and `verify`'s voiding of a Review B launch is stated separately from `premerge`.

## Named cause

Filtering `dependency-scan.yml` / `.yaml` out of the lists that feed `steps` and `scanner_lines` stops the weekly OSV-Scanner step from satisfying the gate floor when the real gate workflow lacks or guards that scanner.

## Floors that read `steps` or `scanner_lines` (gate-only now)

- `Semgrep in the gate` (`steps`)
- `Socket in the gate` (`steps`)
- `Semgrep version pinned` (`scanner_lines`)
- `OSV-Scanner version pinned` (`scanner_lines`)
- `Socket version pinned` (`scanner_lines`)
- `Semgrep step guards itself` (`steps`, via `hits`)
- `OSV-Scanner step guards itself` (`steps`, via `hits`)
- `Socket step guards itself` (`steps`, via `hits`)
- `Semgrep bridge rules or Pro engine` (`steps`)
- `Socket runs without its banner` (`steps`)
- `Socket CLI installed without the key` (`steps`)

## Test and verification commands

```
python -m pytest tests/test_bug042.py tests/test_conformance_check.py -q
```

```
................................                                         [100%]
32 passed in 10.26s
```

```
git diff bridge/cursor-bridge/review-guard.py
```

```
diff --git a/bridge/cursor-bridge/review-guard.py b/bridge/cursor-bridge/review-guard.py
index 36ce152..7a5dfd4 100644
--- a/bridge/cursor-bridge/review-guard.py
+++ b/bridge/cursor-bridge/review-guard.py
@@ -60,9 +60,11 @@ What each step does:
             with `--match-head-commit`.
 
 Exit 0 = OK; 1 = GATE-INTEGRITY (open the flag, condition 4, and an issue; do not merge);
-2 = cannot verify (no snapshot, dirty tree, git or gh failure); 125 = refused (review round
-ceiling, grammar, branch rule; writes no snapshot). Never prints a value of anything.
-ASCII-only.
+a snapshot deleted after it was taken, its hash copy standing, is GATE-INTEGRITY;
+2 = cannot verify (a snapshot never taken, dirty tree, git or gh failure); 125 = refused
+(review round ceiling, grammar, branch rule; writes no snapshot). A GATE-INTEGRITY from
+`verify` voids the Review B launch for round counting; `premerge` voids nothing. Never prints
+a value of anything. ASCII-only.
 
 What it does not cover, said plainly (KP-032): the contents of cache folders, anything
 outside the checkout (the owner's profile, the installed bridge, other projects), and a
@@ -297,8 +299,9 @@ def hash_copy_path(common, nnn):
 
 def snapshot_rewritten(common, nnn):
     """'rewritten' when the snapshot file's hash differs from the copy `snapshot` wrote outside the
-    checkout (FB-037), 'missing' when there is no copy (fail closed: a snapshot taken before this
-    release or a deleted copy is taken again), None when it matches."""
+    checkout (FB-037), or the file is gone while the copy stands, 'missing' when there is no copy
+    (fail closed: a snapshot taken before this release or a deleted copy is taken again), None when
+    it matches."""
     try:
         with open(hash_copy_path(common, nnn), encoding="utf-8") as f:
             recorded = f.read().strip()
```

```
python -c "open('bridge/cursor-bridge/review-guard.py','rb').read().decode('ascii'); open('bridge/cursor-bridge/conformance-check.py','rb').read().decode('ascii'); print('ascii ok')"
```

```
ascii ok
```

## Assumed, not verified

Assumed, not verified: none
