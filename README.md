# Claude-Cursor Bridge

The Claude-Cursor Bridge is a governance layer for Claude Code: instructions, subagents and small programs under which a Claude Code session supervises a software project and delegates the implementation to the Cursor CLI. This repository holds its sources, its tests and the tool that stamps a release. It is not installed from here by copying.

## Layout

- **`bridge/`** — the governance sources, in the layout they have once installed under `~/.claude`:
  - `commands/` — `supervisor` (the supervising architect's instructions) and `calibrate-bridge` (aligns a running project with the installed release).
  - `agents/` — the subagents: `spec-packager`, `diff-reviewer`, `design-auditor`, `security-auditor`, `plan-critic`, `diagram-specialist`, `refactor-scout`, `test-runner`, `secret-sentinel`, `cursor-configurator`.
  - `skills/` — `explain-for-decision`, `root-cause-first`, `design-sense`.
  - `cursor-bridge/` — the conventions and policies (`Merge-Verification-Policy.md`, `Known-Pitfalls.md`, and the rest), the bridge's programs (`bridge-install.py`, `bridge-check.py`, `bridge-run.py`, `review-guard.py`, `scope-check.py`, `plan-check.py`, and the others), the bridge's entries for the owner's settings (`settings.bridge.json`), and the release stamp (`VERSION`, `MANIFEST.json`, `CHANGELOG.md`).
- **`tests/`** — the test suite for the programs and for the consistency of the instructions; run in CI on Windows and Linux.
- **`tools/make-manifest.py`** — stamps a release.

The sources are deliberately **not** in a folder named `.claude`: Claude Code loads agents, commands, settings and hooks from a project's `.claude` folder, so a session working here would run the half-edited bridge instead of the installed one (`Known-Pitfalls.md`, KP-037).

## Changing the bridge

`main` is protected: both CI jobs are required and every change arrives through a pull request. Before a commit that changes `bridge/`, add a `## <version>` entry to `bridge/cursor-bridge/CHANGELOG.md` (what changed; what running projects must do, by phase; what a project restores if the release is rolled back), then run:

```bash
python tools/make-manifest.py
```

It writes `VERSION` and `MANIFEST.json`. Run the tests with `python -m pytest tests -q`.

## Installing and taking back a release

```bash
python bridge/cursor-bridge/bridge-install.py
```

copies the sources into `~/.claude`, merges the bridge's entries into the owner's `settings.json` without touching the owner's own keys, installs the `cursor-agent` shim, keeps the previously installed release, and verifies the result. Restart the Claude app afterwards and run `/calibrate-bridge` in each project. `python bridge/cursor-bridge/bridge-install.py --rollback` puts the previous release back (run it from here, not from the installed copy, which is replaced during the rollback). The install takes only `main` as merged and stamped; `--anyway` with `--target <folder>` installs a branch for a rehearsal; note that a rehearsal still prepares the agent's home folder in the real profile (`%USERPROFILE%\.cursor-bridge\agent-home`), because that folder is per computer (KP-038). The bridge is installed once per computer, so both reach every project on it at once.

The owner's guides (setting up, starting a project), the Project Summary and the restructuring plan live in `Documents/` beside this repository's folder and are not part of the repository.
