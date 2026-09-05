# Claude-Cursor Bridge — staging tree

A version-controlled **staging copy of the Claude-Cursor Bridge `~/.claude/` governance
tree**, extended with the **design-tooling integration** (Impeccable + the Vercel Web
Interface Guidelines + a vendored awesome-design-md seed corpus). These files are the
build loop's *instructions* — governance, not any product. They install over the live
`~/.claude/`.

## Layout

- **`.claude/`** — the bridge governance tree:
  - `commands/` — the `supervisor` command.
  - `agents/` — the specialist subagents (`cursor-configurator`, `spec-packager`,
    `diff-reviewer`, `design-auditor`, `plan-critic`, `test-runner`, `secret-sentinel`).
  - `cursor-bridge/` — the bridge references: `Cursor-File-Formats.md`,
    `Cursor-Project-Configuration.md`, `Merge-Verification-Policy.md`, the bundled
    `vercel-interface.snapshot.md` fallback, and `design-seeds/` (the vendored
    awesome-design-md corpus — one `DESIGN.md` per brand, a seed to bootstrap a project's
    own identity, never shipped as-is).
  - `skills/` — the `design-sense` house-design-sense skill.
  - `settings.json` — the bridge's permission allowlist.

Transient clones (`web-interface-guidelines/`, `impeccable/`) are **gitignored** and are
not part of the repo — they are consumed once during setup and deleted. Their content that
the bridge needs is already vendored (the Vercel snapshot; the design seeds).

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
