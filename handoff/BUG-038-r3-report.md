# BUG-038 round 3 report

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
6 passed in 1.82s
```

### Done step 3 (widest line in STAND-IN paragraph)

```
widest: 92
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
?? handoff/BUG-038-r3-report.md
 bridge/cursor-bridge/completion-check.py | 15 +++++++--------
 1 file changed, 7 insertions(+), 8 deletions(-)
diff --git a/bridge/cursor-bridge/completion-check.py b/bridge/cursor-bridge/completion-check.py
index 86592fc..fc0a620 100644
--- a/bridge/cursor-bridge/completion-check.py
+++ b/bridge/cursor-bridge/completion-check.py
@@ -26,14 +26,13 @@ docs/REQUIREMENTS.md holds one table (see supervisor.md, "The requirements regis
               the requirement ID (a comment, docstring, or test name) - that is the trace.
 --only R-001,R-002  limits every check to those IDs (an older project brought under the
               register part by part, or one stage's requirements; release A4).
-  STAND-IN    shipped (non-test) code shows a user-visible stand-in: a feature said to arrive
-              later (a later stage, version, release or update); phrasing that something will
-              land soon; wording that a capability is not ready yet (implemented behavior
-              missing, available or supported status lacking, not built, or work still
-              outstanding); a notice that a page is still being built (a construction notice);
-              an identifier with Placeholder followed by View, Page, Screen, Tab, Panel or
-              Section; or a call of the todo or unimplemented macro (Rust), with or without
-              arguments.
+  STAND-IN    shipped (non-test) code shows a user-visible stand-in, in any of these forms:
+              arrive or arrives, then in a later stage, version, release or update; the word
+              coming directly followed by soon; not and yet before implemented, available,
+              built or supported; not, implemented and yet in a row; to be and implemented
+              in a row; under and construction in a row; an identifier ending in Placeholder
+              plus one of View, Page, Screen, Tab, Panel or Section; a call of the todo or
+              unimplemented macro (Rust), with or without arguments.
               Allowed only on a line that names the ID of an owner-deferred requirement.
 Notes never fail: TODO/FIXME counts and NotImplementedError sites (often legitimate
 abstract methods) in shipped code.
```

## Files changed

- `bridge/cursor-bridge/completion-check.py` (module docstring STAND-IN paragraph only)
- `handoff/BUG-038-r3-report.md` (this file)

## New paragraph (quoted)

```
  STAND-IN    shipped (non-test) code shows a user-visible stand-in, in any of these forms:
              arrive or arrives, then in a later stage, version, release or update; the word
              coming directly followed by soon; not and yet before implemented, available,
              built or supported; not, implemented and yet in a row; to be and implemented
              in a row; under and construction in a row; an identifier ending in Placeholder
              plus one of View, Page, Screen, Tab, Panel or Section; a call of the todo or
              unimplemented macro (Rust), with or without arguments.
              Allowed only on a line that names the ID of an owner-deferred requirement.
```

## Summary

Round 3 replaced the STAND-IN docstring paragraph with supervisor-checked wording that describes each `STANDIN_RX` branch without embedding matched phrases, fixing Review A's round-2 objections about "will land soon" and missing "yet" qualifiers while keeping `matches: 0` and the owner-deferred closing sentence unchanged.

## Assumed, not verified

Assumed, not verified: none
