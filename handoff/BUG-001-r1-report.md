# BUG-001 round 1 report

## Files changed

- `.github/workflows/tests.yml`
- `handoff/BUG-001-r1-report.md`

`docs/BUILDER_NOTES.md` was not changed: nothing in the brief, the rules, or the tooling blocked the fix, and no new defect or pitfall turned up beyond the named cause.

## Summary

In job `security-floor` of `.github/workflows/tests.yml`, the Socket CLI install was moved out of the `Socket` step into a new step named `Install the Socket CLI`, placed after `actions/setup-node` and immediately before `Socket`, with no `env` block, running exactly `npm install -g --ignore-scripts @socketsecurity/cli@1.7.0`; the `Socket` step keeps its name and its `env` (`SOCKET_CLI_API_TOKEN` from `secrets.SOCKET_SECURITY_API_KEY`, `SOCKET_CLI_ORG_SLUG` from `vars.SOCKET_ORG_SLUG`) and now runs only `socket ci --no-banner`.

The step-level `env` that holds `secrets.SOCKET_SECURITY_API_KEY` no longer covers any install line: the install runs in a step whose environment carries no secret, and with `--ignore-scripts`.

GitHub Actions was not run locally and no CI result is claimed.

## What changed

Only the `Socket` step of job `security-floor` and the new install step. The install line left the `Socket` step; the new step has no `if:`, `continue-on-error`, `shell:`, `working-directory`, or status swallower, and the `Socket` step has none of those either. The CLI pin stays `@socketsecurity/cli@1.7.0`. No other step, job, trigger, pin, permission, comment, or blank line was edited. `tests/test_release_b_ci_floor.py` was not edited.

## Commands

Working folder for every command: `E:\p18-claude-cursor-bridge\Workspace`.

### 1. `python -m pytest tests/test_release_b_ci_floor.py -q`

Exit code 0.

```
................                                                         [100%]
16 passed in 0.11s
```

### 2. `python -m pytest tests -q`

Exit code 0.

```
........................................................................ [  7%]
.............s...ss..........s.s........................................ [ 14%]
....sss........ss...................................s...ss..........s.s. [ 22%]
...........................................sss........ss................ [ 29%]
........................................................................ [ 37%]
........................................................................ [ 44%]
........................................................................ [ 52%]
........................................................................ [ 59%]
........................................................................ [ 67%]
........................................................................ [ 74%]
........................................................................ [ 82%]
........................................................................ [ 89%]
........................................................................ [ 96%]
.............................                                            [100%]
945 passed, 20 skipped in 223.76s (0:03:43)
```

### 3. `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge`

Exit code 0.

```
windowless-check: 29 file(s) scanned, 0 FAIL, 0 NOTE
```

### 4. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`

Exit code 0.

```
bridge-check: version 2026.10.11d (2026-10-12 22:42) at E:\p18-claude-cursor-bridge\Workspace\bridge
bridge-check: 106 OK, 0 STALE, 0 MISSING, 0 EXTRA
RESULT: SOURCES MATCH bridge 2026.10.11d
```

### 5. `python bridge/cursor-bridge/conformance-check.py . --offline`

Exit code 1. The five security-floor lines are OK (Semgrep in the gate, OSV-Scanner in the gate, Socket in the gate, Semgrep bridge rules or Pro engine, CI actions pinned by commit). The exit code is from other floors the checker reports as missing; this change does not touch those rules, hooks, or docs.

```
conformance-check: E:\p18-claude-cursor-bridge\Workspace
  OK       Semgrep in the gate
  OK       OSV-Scanner in the gate
  OK       Socket in the gate
  OK       Semgrep bridge rules or Pro engine
  OK       CI actions pinned by commit
  NOTE     Required check on the default branch  - not checked (--offline)
  MISSING  Workspace boundary rule  - the builder's always-on boundary rule (rule 22)
  MISSING  Secure-coding rule  - the frozen ASVS-derived rule the builder self-applies (N8)
  MISSING  Boundary-check hook  - .cursor/hooks.json does not run boundary-check (rule 22)
  MISSING  Windowless check  - no windowless-check in the hooks; rule 24 puts it in the pre-commit gate
  OK       docs/PROJECT_STATUS.md
  OK       docs/INVENTORY.md
  OK       docs/REQUIREMENTS.md
  OK       docs/RUN_PARAMETERS.md
  OK       docs/ROSTER.json
  OK       project.json
  NOTE     docs/DESIGN.md  - the design exists under other names (DESIGN_CRITIQUE.md); the diagram retrofit (plan 8.7) gives it the fixed name or a DESIGN.md that points at them
  MISSING  docs/diagrams/INDEX.md  - no diagram index: a diagram retrofit item (restructuring plan 8.7), scheduled at the next natural pause
  OK       Spending limit recorded
  OK       Development data kept apart
  OK       No secret through an environment variable
  OK       Calibrated to the installed bridge (2026.10.11d)
conformance-check: 15 OK, 5 MISSING, 2 NOTE
RESULT: 5 floor(s) missing - each is a calibration item, applied as configuration work in the next stage
```

### 6. `git diff -- .github/workflows/tests.yml`

```
diff --git a/.github/workflows/tests.yml b/.github/workflows/tests.yml
index 6340c71..579c59f 100644
--- a/.github/workflows/tests.yml
+++ b/.github/workflows/tests.yml
@@ -75,10 +75,10 @@ jobs:
       - uses: actions/setup-node@a0853c24544627f65ddf259abe73b1d18a591444 # v5.0.0
         with:
           node-version: "22"
+      - name: Install the Socket CLI
+        run: npm install -g --ignore-scripts @socketsecurity/cli@1.7.0
       - name: Socket
         env:
           SOCKET_CLI_API_TOKEN: ${{ secrets.SOCKET_SECURITY_API_KEY }}
           SOCKET_CLI_ORG_SLUG: ${{ vars.SOCKET_ORG_SLUG }}
-        run: |
-          npm install -g @socketsecurity/cli@1.7.0
-          socket ci --no-banner
+        run: socket ci --no-banner
```

## Could not do

GitHub Actions was not run locally (no `act`, no workflow runner, no network calls to GitHub). No CI result is claimed. The Socket CLI was not installed.

## Assumed, not verified

Assumed, not verified: none
