# BUG-038 round 2 report

## Initial git status

```
```

(empty; `git status --porcelain` printed nothing)

## Verification commands

### Done step 1

```
[]
matches: 0
```

### Done step 2

```
......                                                                   [100%]
6 passed in 1.78s
```

### Done step 3 (widest line in STAND-IN paragraph)

```
widest: 94
```

### Done step 4

```
exit:0
```

(`python tools/dump-cli.py --check`)

### Done step 5

```
tests_diff_exit:0
 M bridge/cursor-bridge/completion-check.py
?? handoff/BUG-038-r2-report.md
 bridge/cursor-bridge/completion-check.py | 13 ++++++++-----
 1 file changed, 8 insertions(+), 5 deletions(-)
diff --git a/bridge/cursor-bridge/completion-check.py b/bridge/cursor-bridge/completion-check.py
index 78be819..86592fc 100644
--- a/bridge/cursor-bridge/completion-check.py
+++ b/bridge/cursor-bridge/completion-check.py
@@ -26,11 +26,14 @@ docs/REQUIREMENTS.md holds one table (see supervisor.md, "The requirements regis
               the requirement ID (a comment, docstring, or test name) - that is the trace.
 --only R-001,R-002  limits every check to those IDs (an older project brought under the
               register part by part, or one stage's requirements; release A4).
-  STAND-IN    shipped (non-test) code shows a user-visible stand-in: a feature deferred to a
-              later release or version; phrasing that something will come soon; behavior that is
-              not implemented or still unavailable; copy saying the product is under active
-              construction; a named placeholder component suffix (View, Page, Screen, Tab, Panel,
-              Section); or Rust code calling the todo or unimplemented macros with arguments.
+  STAND-IN    shipped (non-test) code shows a user-visible stand-in: a feature said to arrive
+              later (a later stage, version, release or update); phrasing that something will
+              land soon; wording that a capability is not ready yet (implemented behavior
+              missing, available or supported status lacking, not built, or work still
+              outstanding); a notice that a page is still being built (a construction notice);
+              an identifier with Placeholder followed by View, Page, Screen, Tab, Panel or
+              Section; or a call of the todo or unimplemented macro (Rust), with or without
+              arguments.
               Allowed only on a line that names the ID of an owner-deferred requirement.
 Notes never fail: TODO/FIXME counts and NotImplementedError sites (often legitimate
 abstract methods) in shipped code.
```

## Files changed

- `bridge/cursor-bridge/completion-check.py` (module docstring STAND-IN paragraph only)
- `handoff/BUG-038-r2-report.md` (this file)

## Summary

Round 2 reworded only the STAND-IN paragraph in `bridge/cursor-bridge/completion-check.py` so each clause truthfully describes its `STANDIN_RX` branch while no line matches the scan, keeping the owner-deferred closing sentence byte-identical. The new paragraph reads: `STAND-IN    shipped (non-test) code shows a user-visible stand-in: a feature said to arrive later (a later stage, version, release or update); phrasing that something will land soon; wording that a capability is not ready yet (implemented behavior missing, available or supported status lacking, not built, or work still outstanding); a notice that a page is still being built (a construction notice); an identifier with Placeholder followed by View, Page, Screen, Tab, Panel or Section; or a call of the todo or unimplemented macro (Rust), with or without arguments. Allowed only on a line that names the ID of an owner-deferred requirement.`

## Review A findings (1–6)

1. **todo/unimplemented macros:** The clause now says `a call of the todo or unimplemented macro (Rust), with or without arguments`, matching the branch that hits the macro name, `!`, and `(` regardless of what follows, in any listed code file type.
2. **Under construction:** Replaced the false example with `a notice that a page is still being built (a construction notice)`, which names the kind without writing `under construction` or `under active construction`.
3. **Later arrival:** Replaced `deferred to a later release or version` with `a feature said to arrive later (a later stage, version, release or update)`, listing all four scan alternatives and avoiding the word `deferred`.
4. **Coming soon and not-yet kinds:** `will come soon` became `will land soon` (keeps `soon` without `coming soon`); the not-yet / not-implemented-yet / to-be-implemented kinds are described as `wording that a capability is not ready yet (implemented behavior missing, available or supported status lacking, not built, or work still outstanding)` without placing a matched phrase on any single line.
5. **Placeholder suffix:** Replaced the vague suffix list with `an identifier with Placeholder followed by View, Page, Screen, Tab, Panel or Section`, aligned with the regex (word ending in Placeholder immediately followed by one of the six suffixes).
6. **Line width:** Wrapped so the widest line in the paragraph is 94 characters (`widest: 94`).

## Named cause

The program’s docstring no longer contains literal or line-local text that `STANDIN_RX` matches, so `--mode done` does not report the completion check’s own STAND-IN paragraph as a stand-in while the scan and patterns stay unchanged.

## Assumed, not verified

Assumed, not verified: none
