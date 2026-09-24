# Claude-Cursor Bridge — staging tree

A version-controlled **staging copy of the Claude-Cursor Bridge `~/.claude/` governance
tree**, extended with the **design-tooling integration** (Impeccable + the Vercel Web
Interface Guidelines + a vendored awesome-design-md seed corpus). These files are the
build loop's *instructions* — governance, not any product. They install over the live
`~/.claude/`.

## Layout

- **`.claude/`** — the bridge governance tree:
  - `commands/` — the `supervisor` command and `calibrate-bridge` (verifies an installed tree
    against the release manifest, re-reads the governing files, applies a release's
    adjustments by phase without reopening a gate).
  - `agents/` — the specialist subagents (`cursor-configurator`, `spec-packager`,
    `diff-reviewer`, `design-auditor`, `security-auditor`, `refactor-scout`, `plan-critic`,
    `test-runner`, `secret-sentinel`).
  - `cursor-bridge/` — the bridge references (plus the bundled scripts `scope-check.py`,
    `shell-guard.py`, `boundary-check.py` — an advisory after-edit detector for builder
    writes outside `Workspace/` — and the windowless pair `run-hidden.py` /
    `windowless-check.py`, which keep hook- and tool-launched console programs from popping
    terminal windows on the user's desktop, and `refactor-check.py`, the purity check for a
    stage's refactoring diff; plus `bridge-check.py`, `VERSION`, `MANIFEST.json`, and
    `CHANGELOG.md` — the release stamp; and `installer-check.ps1`, the install / upgrade /
    uninstall lifecycle check for desktop installers; and `bench-check.py`, the benchmark floor
    checker against budgets and a committed baseline; and `lock-check.py`, which fails a
    dependency-manifest change that lacks its lockfile change; and `roster-check.py`, which
    fails a model roster whose three roles do not sit on three families): `Cursor-File-Formats.md`,
    `Delivery-Conventions.md`, `Performance-Conventions.md`, `Performance-Patterns.md`
    (the catalogue of recurring causes of slowness and cost, maintained like
    `Known-Pitfalls.md`),
    `Cursor-Project-Configuration.md`, `Merge-Verification-Policy.md`, the bundled
    `vercel-interface.snapshot.md` fallback, and `design-seeds/` (the vendored
    awesome-design-md corpus — one `DESIGN.md` per brand, a seed to bootstrap a project's
    own identity, never shipped as-is).
  - `skills/` — the `design-sense` house-design-sense skill, the `explain-for-decision`
    skill (how a technical matter is explained to the non-engineer owner when it surfaces for
    a decision: the selection heuristic, the nine guards, the decision-brief shape), and the
    `root-cause-first` skill (evidence-before-fix debugging: reproduce, hypothesize,
    instrument to discriminate, read the run, fix the confirmed cause — usable by any session).
  - `settings.json` — the bridge's permission allowlist.

Transient clones (`web-interface-guidelines/`, `impeccable/`) are **gitignored** and are
not part of the repo — they are consumed once during setup and deleted. Their content that
the bridge needs is already vendored (the Vercel snapshot; the design seeds).

## Release stamp (maintainer)

Before every commit that changes `.claude/`: add a `## <version>` entry to
`.claude/cursor-bridge/CHANGELOG.md` (with its **Running projects must** list, by phase),
then run `python tools/make-manifest.py` — it writes `VERSION` and `MANIFEST.json`. An
installed machine verifies the copy with `python ~/.claude/cursor-bridge/bridge-check.py`.

## Install

1. Copy this repo's `.claude/` over the live `~/.claude/`.
2. Do the environment setup (Part A, step A4 of the implementation instructions): Node 24+
   with `npx` reachable from Git Bash, and
   `npx impeccable install --providers=claude --scope=global --no-hooks`.
3. Restart the Claude desktop app (new files under `agents/` and `commands/` are only
   picked up on restart), then confirm `/supervisor` and the `design-auditor` subagent
   appear.

## The design and its rationale

- `Documents/Design-Tooling-Integration-Summary.md` — the settled design (the *why*).
- `Documents/Design-Tooling-Bridge-Implementation-Instructions.md` — the executable edit
  plan (the *how*).

This README documents the repo; it is not a second copy of those design docs.
