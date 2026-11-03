# BUG-042-r2 builder report

## Files changed

- `bridge/cursor-bridge/conformance-check.py`
- `bridge/cursor-bridge/review-guard.py`

## Summary

Round 1 limited `steps` to gate workflows (excluding the weekly `dependency-scan` file), which left ISS-005 and FB-007 blind to Socket key hazards in that weekly workflow. This increment adds `all_steps` built from every workflow file, switches the two Socket key-exposure rows to read `all_steps`, and updates the conformance-check module docstring so those two floors are documented as scanning all workflows including the weekly file. The review-guard module docstring alone was corrected so exit code 2 and verify-time voiding match what the code actually does; no guard code changed.

## Named cause

The two Socket rows now use `all_steps` from `workflows`, so a hazardous step in `dependency-scan.yml` is flagged the same as in any other workflow, while `steps` and `gate_wf_text` still exclude the weekly file for gate scanner floors.

## Rows reading every workflow

- CI gate (presence of any workflow under `.github/workflows/`)
- CI actions pinned by commit
- Runner OS (NOTE)
- Design detector in the gate (when screens/mockups apply)
- Socket runs without its banner (ISS-005)
- Socket CLI installed without the key (FB-007)
- CLI reference check in CI (reads `wf_text` later in `main()`)

## Rows reading the gate alone (weekly dependency-scan excluded)

- Semgrep in the gate
- OSV-Scanner in the gate
- Socket in the gate
- Semgrep bridge rules or Pro engine
- `<scanner> step guards itself` (NOTE, per scanner)
- `<scanner> version pinned` (NOTE, per scanner)

## Test output

```
python -m pytest tests/test_bug042.py tests/test_conformance_check.py -q
...................................                                      [100%]
35 passed in 12.59s
```

```
git diff bridge/cursor-bridge/review-guard.py
diff --git a/bridge/cursor-bridge/review-guard.py b/bridge/cursor-bridge/review-guard.py
index 7a5dfd4..d80cbbe 100644
--- a/bridge/cursor-bridge/review-guard.py
+++ b/bridge/cursor-bridge/review-guard.py
@@ -61,9 +61,9 @@ What each step does:
 
 Exit 0 = OK; 1 = GATE-INTEGRITY (open the flag, condition 4, and an issue; do not merge);
 a snapshot deleted after it was taken, its hash copy standing, is GATE-INTEGRITY;
-2 = cannot verify (a snapshot never taken, dirty tree, git or gh failure); 125 = refused
+2 = cannot verify (no copy of the snapshot's hash, dirty tree, git or gh failure); 125 = refused
 (review round ceiling, grammar, branch rule; writes no snapshot). A GATE-INTEGRITY from
-`verify` voids the Review B launch for round counting; `premerge` voids nothing. Never prints
+`verify` voids a qualifying Review B launch for round counting; `premerge` voids nothing. Never prints
 a value of anything. ASCII-only.
 
 What it does not cover, said plainly (KP-032): the contents of cache folders, anything
```

```
python -c "open('bridge/cursor-bridge/review-guard.py','rb').read().decode('ascii'); open('bridge/cursor-bridge/conformance-check.py','rb').read().decode('ascii'); print('ascii ok')"
ascii ok
```

## Assumed, not verified

Assumed, not verified: none
