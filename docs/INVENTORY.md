# Inventory — Claude-Cursor Bridge
Reflected through: none
Updated: 2026-10-12

The bridge already exists (releases 0, A1a–A5). This inventory is opened as the bridge becomes a supervised project (release B). Features accrue to the register as release B's increments merge; the rows below record the decisions and resources release B rests on.

## Features
| Feature | What it does | Where | Tests | Since |
|---|---|---|---|---|
| Supervisor workflow | The governing instructions the supervisor runs a project by | bridge/commands/supervisor.md | tests/ | pre-B |
| Bridge programs | The one-shot checks and launchers the loop relies on | bridge/cursor-bridge/*.py | tests/ | pre-B |
| Governance conventions | The reference texts (merge policy, delivery, diagrams, performance, observability, pitfalls) | bridge/cursor-bridge/*.md | tests/ | pre-B |
| Install & lifecycle | Install, upgrade-in-place, take-back of the bridge on one computer | bridge/cursor-bridge/bridge-install.py | tests/ | release A1a |
| Conditional-workflow model | The core's statement of the five layers, add/replace/set, inheritance and the order additions apply in | bridge/commands/supervisor.md, "Main and conditional workflows" | tests/test_workflow_model.py | release B (TASK-003) |
| The open list | Every product type, sub-type and trait with its definition, default traits, workflow name and written flag; the add/change procedure | bridge/cursor-bridge/workflow/open-list.md | tests/test_open_list.py | release B (TASK-004) |
| The extension-point registry | Every phase module with its replaceable flag, and every point a conditional workflow may change, each with its declaring module, the kinds of change it accepts and whether it applies per part or per project; how a conditional workflow names a point | bridge/cursor-bridge/workflow/extension-points.md | tests/test_extension_points.py | release B (TASK-005) |
| The CI security floor | Semgrep (OSS engine, explicit rulesets, diff-aware), OSV-Scanner and Socket run in the `security floor` job beside the tests; the tests install from a committed lockfile; every action pinned by commit SHA, checkouts without persisted credentials, secrets only in step-level env | .github/workflows/tests.yml; requirements.lock; .semgrep.yml; osv-scanner.toml; socket.yml | tests/test_release_b_ci_floor.py | release B (TASK-002) |
| The `Workflows:` status line | One line per part beside `Phase:`, naming the part's product type, sub-type and traits by the open list's workflow and trait names, in a stated grammar; `not yet classified` before intake | bridge/commands/supervisor.md, "Project state" | tests/test_workflows_line_text.py | release B (TASK-007) |

## Resources
| Name | Kind | Where it lives | Used by | Provided |
|---|---|---|---|---|
| Cursor (`cursor-agent`) | tool | installed, signed in on this computer | the builder and Review B | pre-B |
| Model roster | config | docs/ROSTER.json; resolved to docs/ROSTER.resolved.json | every delegation and Review B | 2026-10-11 |
| Python 3.12 + pytest 9.1.1 + pyyaml 6.0.3 (with their closure) | tool | requirements.lock (CI installs from it since TASK-002); Python pinned in .github/workflows/tests.yml | the bridge's CI | pre-B; lockfile since TASK-002 |
| GitHub repository (protected `main`) | config | github.com/latentfoundrycode/p18-claude-cursor-bridge | the gate, every PR | pre-B |
| Semgrep 1.176.1 / OSV-Scanner 2.7.0 / Socket CLI 1.7.0 | tool | .github/workflows/tests.yml, job `security floor` (Semgrep through pipx at its version; OSV-Scanner's binary checked by SHA-256; Socket CLI at its version) | the bridge's CI gate | TASK-002 |
| SOCKET_SECURITY_API_KEY | repo secret | GitHub repository secrets (name only) | the Socket step of the security floor (`SOCKET_CLI_API_TOKEN`) | the owner, 2026-10-12; free tier, no spend possible |
| SEMGREP_APP_TOKEN | repo secret | GitHub repository secrets (name only) | nothing: Semgrep runs the OSS engine without a token (owner, 2026-10-12) | the owner; unused, no spend possible |
| SOCKET_ORG_SLUG, SOCKET_CLI_ORG_SLUG | repo variable (an identifier, public) | SOCKET_ORG_SLUG is a GitHub repository variable, value `latent-foundry`; SOCKET_CLI_ORG_SLUG is only the Socket step's environment name for it | the Socket step of the security floor: `socket ci` 1.7.0 reads SOCKET_CLI_ORG_SLUG before it asks the API (handoff/TASK-002-r6-report.md) | the owner, 2026-10-12 |
| BRIDGE_RUN_ALLOW_ANY | config | an optional override read by bridge-run.py (lets any command through the launcher); unset in normal use | bridge/cursor-bridge/bridge-run.py | pre-B; no value stored |
| ROSTER_NOW | config | an optional clock override read by roster-check.py (for deterministic reset-day tests); unset in normal use | bridge/cursor-bridge/roster-check.py | pre-B; no value stored |
| GH_TOKEN, GH_CONFIG_DIR, GIT_CONFIG_GLOBAL, GIT_TERMINAL_PROMPT | test-only | set and read by the test harness to isolate subprocesses (tests/test_bridge_run.py); not real credentials | the bridge's test suite | pre-B; no value stored |
| MODAL_TOKEN_ID, THING_API_KEY | test-only | fixture env names used by the conformance/secret-scan tests to exercise detection (tests/); not real credentials | the bridge's test suite | pre-B; no value stored |

No paid API key is needed to build the bridge itself; the roster uses the owner's Cursor subscription (native profile while the Other Models pool shows a usage limit).

## Decisions
| Decision | Reason | Settled | Revisit only if |
|---|---|---|---|
| The bridge is a supervised project from release B | §15: release B and later are large enough to earn the full loop; the maintainer built releases 0–A5 | 2026-10-11, §15 / owner | the full loop proves unworkable for the bridge |
| Product type: host extension → Claude Code extension; trait: installable | §6.3 classification | 2026-10-11, owner (decision 6 confirmed) | the bridge gains a new interface or trait |
| Decision 6 confirmed: the §6.3 product-type revisions and all classifications — video factory & reAngle = web app → local web app; TDP = software on your own computer → local service; the bridge = host extension → Claude Code extension. Note (owner, 2026-10-11): the SFVF's "web app" label is loose and approximate, not a precise fit — do not over-read it in future | §6.3 / §18 decision 6, asked at release B start | 2026-10-11, owner | a project's interface changes |
| R-038: release B is installed by pausing and switching this checkout to `main` at stage B6 (after all increments merge); an urgent mid-build install uses the maintainer's separate clone (§15 exception) | the normal flow installs once at B6, when main holds the release; no second clone to maintain | 2026-10-11, owner | a mid-build install becomes routine |
| Merge authority: supervisor (see RUN_PARAMETERS.md) | possible once the bridge became a supervised project; §15 cond 5's earlier reading applied before that | 2026-10-12, owner | — |
| The Socket CLI runs with `--no-banner`: its banner prints the first 5 characters of the API key, which GitHub does not mask and this public repository's CI logs would show (PR #16's six earlier runs) | no part of a key in a public log | 2026-10-12, supervisor (Review A, raised to blocking) | the CLI changes how it prints the key |
| Semgrep runs the OSS engine with explicit rulesets and no token | the bridge's own code has no SQL or web surface, where the Pro engine's taint analysis earns its place | 2026-10-12, owner | the bridge gains code with a SQL or web surface |
| Stage pause: run; refactoring pass: on; parallel increments: off; kind: private | owner's run-parameter answers | 2026-10-11, owner | the owner changes a run parameter |
| Governance text is the supervisor's to write; programs are the builder's | §15 condition 3, keeping N4 intact | 2026-10-11, §15 | — |
| Development data: the dev build is the Workspace sources under `bridge/`; a session in the repo always runs the *installed* bridge (`~/.claude`), never the one being edited, and installs reach running projects only through the owner's install run sheet (§15 condition 1, A1a condition 1) | a session must never load the half-edited bridge, and an install must never run unreleased code on a running project | 2026-10-11, §15 | — |
| Who decided is recorded: owner / supervisor / design(the plan) / maintainer; no agent recorded as a person | rule 51 | 2026-10-11 | — |
| Baseline measurement (precondition 3) met before release B: the compaction baseline was taken 2026-10-11 (Reports/Maintainer/2026-10-11-compaction-baseline.md) — about one compaction per active day per project before the digest hook | release B's precondition §14.3 | 2026-10-11, maintainer | the measure is re-taken after release B |
| Release B2 (machine-readable YAML front-matter headers on the dual-read records) is a confirmed post-B release — taken up at the planning point after release B is done and accepted; built through the gate like B. Scope in the plan §16 and run/supervisor/maintainer-b2.md | §16; added by the maintainer at the owner's decision | 2026-10-12, owner | — |
| No diagram index for release B | the design is the plan's prose and its §6.2 layering / §6.11 file layout tables; this is governance text, not a code architecture with components to draw | 2026-10-11, supervisor | a later release adds code whose architecture is load-bearing |

## Deferred
| Item | Why deferred | Since | Owner decision needed |
|---|---|---|---|
| (none) | — | — | — |

Note: the release-B install mechanics (the second-checkout question) were settled 2026-10-11 — see Decisions, R-038 (pause & switch at B6).
