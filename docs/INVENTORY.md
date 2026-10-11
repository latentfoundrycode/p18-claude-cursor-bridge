# Inventory — Claude-Cursor Bridge
Reflected through: none
Updated: 2026-10-11

The bridge already exists (releases 0, A1a–A5). This inventory is opened as the bridge becomes a supervised project (release B). Features accrue to the register as release B's increments merge; the rows below record the decisions and resources release B rests on.

## Features
| Feature | What it does | Where | Tests | Since |
|---|---|---|---|---|
| Supervisor workflow | The governing instructions the supervisor runs a project by | bridge/commands/supervisor.md | tests/ | pre-B |
| Bridge programs | The one-shot checks and launchers the loop relies on | bridge/cursor-bridge/*.py | tests/ | pre-B |
| Governance conventions | The reference texts (merge policy, delivery, diagrams, performance, observability, pitfalls) | bridge/cursor-bridge/*.md | tests/ | pre-B |
| Install & lifecycle | Install, upgrade-in-place, take-back of the bridge on one computer | bridge/cursor-bridge/bridge-install.py | tests/ | release A1a |

## Resources
| Name | Kind | Where it lives | Used by | Provided |
|---|---|---|---|---|
| Cursor (`cursor-agent`) | tool | installed, signed in on this computer | the builder and Review B | pre-B |
| Model roster | config | docs/ROSTER.json; resolved to docs/ROSTER.resolved.json | every delegation and Review B | 2026-10-11 |
| Python 3.12 + pytest 9.1.1 + pyyaml 6.0.3 | tool | .github/workflows/tests.yml | the bridge's CI | pre-B |
| GitHub repository (protected `main`) | config | github.com/latentfoundrycode/p18-claude-cursor-bridge | the gate, every PR | pre-B |
| Semgrep / OSV-Scanner / Socket | tool | to be added to .github/workflows/tests.yml, pinned by commit (TASK-002) | the bridge's CI gate | planned (R-002) |
| SEMGREP_APP_TOKEN, Socket token | repo secret | GitHub repository secrets (names only) | the security floor in CI | n/a — set when TASK-002 lands; no spend possible beyond free tier |

No paid API key is needed to build the bridge itself; the roster uses the owner's Cursor subscription (native profile while the Other Models pool shows a usage limit).

## Decisions
| Decision | Reason | Settled | Revisit only if |
|---|---|---|---|
| The bridge is a supervised project from release B | §15: release B and later are large enough to earn the full loop; the maintainer built releases 0–A5 | 2026-10-11, §15 / owner | the full loop proves unworkable for the bridge |
| Product type: host extension → Claude Code extension; trait: installable | §6.3 classification | 2026-10-11, design (the plan) | the bridge gains a new interface or trait |
| Merge authority: owner | §15 condition 5: the app refuses a session that merges its own work | 2026-10-11, forced | — |
| Stage pause: run; refactoring pass: on; parallel increments: off; kind: private | owner's run-parameter answers | 2026-10-11, owner | the owner changes a run parameter |
| Governance text is the supervisor's to write; programs are the builder's | §15 condition 3, keeping N4 intact | 2026-10-11, §15 | — |
| Development data: the dev build is the Workspace sources under `bridge/`; a session in the repo always runs the *installed* bridge (`~/.claude`), never the one being edited, and installs reach running projects only through the owner's install run sheet (§15 condition 1, A1a condition 1) | a session must never load the half-edited bridge, and an install must never run unreleased code on a running project | 2026-10-11, §15 | — |
| Who decided is recorded: owner / supervisor / design(the plan) / maintainer; no agent recorded as a person | rule 51 | 2026-10-11 | — |
| No diagram index for release B | the design is the plan's prose and its §6.2 layering / §6.11 file layout tables; this is governance text, not a code architecture with components to draw | 2026-10-11, supervisor | a later release adds code whose architecture is load-bearing |

## Deferred
| Item | Why deferred | Since | Owner decision needed |
|---|---|---|---|
| Installing release B from a second checkout that only holds `main` | A1a left this "settled at release B's intake"; it affects only the install step at the end of release B, not the build | 2026-10-11 | yes — before the install run sheet |
