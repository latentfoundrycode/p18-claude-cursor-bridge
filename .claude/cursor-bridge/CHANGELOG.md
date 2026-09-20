# Claude-Cursor Bridge — CHANGELOG

One entry per release. `VERSION` and `MANIFEST.json` are stamped by the maintainer's
`tools/make-manifest.py`, which refuses to stamp a version that has no entry here.

Each entry has two parts. **What changed** is for the maintainer and the curious.
**Running projects must** is the part `/calibrate-bridge` acts on: every item names the
**phase** it belongs to, so a project that has already passed that phase does not reopen
it, a project in it applies the item now, and a project before it applies the item when it
arrives. An item marked *(all phases)* applies immediately.

---

## 2026.09.20

First stamped release. Covers everything since the observability integration (commit
`c34b235`) up to and including the calibration mechanism itself.

**What changed**
- `explain-for-decision` skill (rule 21) and the **run sheet** section (rule 27).
- Fixed project layout `<id>-<name>/Documents` + `/Workspace`; Workspace boundary
  (`workspace-boundary.mdc` + `boundary-check.py` hook); the four human-facing Documents;
  reflection points; issue IDs `ISS-nnn` (rules 22–23).
- Windowless-by-default policy (`run-hidden.py`, `windowless-check.py`, KP-014, rule 24).
- Phase 4 step 0 — prior-project lessons from an earlier project's Issues file.
- Stage-close refactoring pass (`refactor-scout`, `refactor-check.py`, rule 25).
- Root-cause-first debugging (`root-cause-first` skill, `BUG-nnn` fix briefs, OBSERVED /
  INFERRED diagnoses, KP-015, rule 26).
- `/calibrate-bridge`, `bridge-check.py`, `VERSION`, `MANIFEST.json`, this file (rule 28).
- Earlier in the same span: minimal-code rule, context-economy boundary, scope-check,
  constant-pointer delegation, safe worktree teardown, reviewer routing table.

**Running projects must**
- *(all phases)* Add to `docs/PROJECT_STATUS.md`: `Bridge version:`, `Software name:`,
  `Layout:`, `Terms fixed:`, `Stage:`, `Open issues:` (see the supervisor's Project state
  template). Resolve `../Documents`; create it if missing.
- *(all phases)* Confirm the folder pair: the supervisor runs in `Workspace/`. If the
  project predates the layout and the repo root is not named `Workspace`, do **not** move
  anything — record the actual paths under `Layout:` and treat the repo root as the
  Workspace boundary; the rename is the owner's call, offered once as a run sheet.
- *(Phase 2 passed)* Create `Documents/<Name> Project Summary.md` at the next reflection
  point if it does not exist.
- *(Phase 4 — planning)* If the build plan is not yet approved: run step 0
  (prior-project lessons) and add the per-stage **refactoring dial** before presenting.
  If the plan is already approved: group existing increments into stages if they are not,
  set the dial to **on** for remaining stages, and tell the owner in one line that they may
  switch it off — do not re-present the plan.
- *(Phase 5 — configuration, or later)* Via `cursor-configurator`, **append** what is
  missing: `.cursor/rules/workspace-boundary.mdc`, `.cursor/rules/minimal-code.mdc`, the
  `boundary-check` hook entry + script, `run-hidden.py` + `windowless-check.py`, the
  windowless idiom in every existing hook script, `run-hidden.py` on every direct-command
  hook entry, the windowless check in `.githooks/pre-commit`. Never overwrite `hooks.json`.
  Verify once with a throwaway edit while watching the desktop.
- *(Phase 6 — building)* From the next increment: `scope-check.py` at Inspect,
  `BOUNDARY_VIOLATIONS.md` read at Inspect, the routing table, the root-cause-first
  procedure on the next defect, the refactoring pass at the next stage close, the
  reflection point at the next stage close. An increment already delegated finishes under
  the brief it has; the next brief uses the current spec-packager template.
- *(all phases)* Nothing already approved is re-presented. No gate is reopened.

---
