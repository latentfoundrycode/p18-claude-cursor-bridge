## Phase 5 — Configure the Cursor build environment

### What must survive a compaction

After a compaction or a resume in this phase, read these before your next action:

- this module, whole, with `~/.claude/cursor-bridge/Cursor-Project-Configuration.md` and `~/.claude/cursor-bridge/Known-Pitfalls.md`, each whole (the session-start hook names both for this phase);
- the approved design and plan: `docs/DESIGN.md`, `docs/REQUIREMENTS.md`, `docs/BUILD_PLAN.md` and `docs/RUN_PARAMETERS.md`, whole: only the items that are load-bearing for this project are applied;
- `docs/PROJECT_STATUS.md`, whole: its `Next:` line names the items configured so far and the next one ("Keeping the position"), its `Awaiting user on:` line an escalation that waits for the owner, and its `Workflows:` line the conditional workflows that add items at `configuration.items`;
- `docs/INVENTORY.md`, whole: its Resources rows record each pinned tool and version, each mode in force and each spending limit as the items are configured.

### The procedure

Once, after the plan is approved and before the first delegation, set up the headless
builder so it can produce and self-correct good code. Work through
`~/.claude/cursor-bridge/Cursor-Project-Configuration.md` — read it by that absolute path;
it is user-level, not in the repo, so it is not `@`-mentionable. Apply only the items
that are load-bearing for *this* project. The handoff brief carries per-task constraints,
so do not author a wall of persistent rules and skills that duplicate it.

The guiding split, set out in that file: file-based configuration you write yourself;
anything needing a secret, a new dependency, a decision the design does not settle, or a
Cursor GUI or dashboard action you cannot reach, escalate to the user. Cursor's own
permission system does not apply here — `--force` bypasses it — so do not try to
configure it.

Delegate the actual file-writing to **cursor-configurator**, which writes
`.gitattributes`, `.cursorignore`, `.worktreeinclude`, linter configs, `hooks.json`,
`.githooks/pre-commit`, `mcp.json`, the frozen `.cursor/rules/minimal-code.mdc` (every
project — the write-the-least-code ladder, with safety rules taking precedence), and the
model roster `docs/ROSTER.json` (the two-profile template in
`Merge-Verification-Policy.md` §Model roster — a *full* profile and a *native* profile with
the roles swapped, plus the `other_pool` state and the subscription's `reset_day`; written at intake since release A3 and re-resolved by `roster-check.py`
here and at every checkpoint), the
performance floor where budgets exist (`bench/budgets.json`, the bench runner script, the
`bench-check.py` step in CI, the pinned profiler — `Performance-Conventions.md` §3), the
always-on `.cursor/rules/workspace-boundary.mdc` plus the `boundary-check` after-edit hook
(every project — the Workspace boundary from "The project layout") on your
instruction and reports back. You keep the
decisions and the escalations; it never adds dependencies, handles secrets, or authors rules
on its own. Clear every escalation with the user before instructing it.

After it writes `.githooks/pre-commit`, set the git-native lint gate live once for this clone:
`git config core.hooksPath .githooks` (run on its own line). From then on a failing lint
blocks any plain `git commit`; your pre-delegation checkpoint commits bypass it with
`--no-verify` (below).

Work the **security-tooling** steps in `Cursor-Project-Configuration.md` §5c the same way:
the configurator writes `.semgrep.yml`, `osv-scanner.toml`, `socket.yml`, the frozen
`.cursor/rules/secure-coding.mdc` (from the bundled
`~/.claude/cursor-bridge/secure-coding.snapshot.md`, level-filtered to the ASVS level from
Phase 1/2 + the LLM supplement for AI-bearing products), the third advisory Semgrep hook, and the
three floor steps **inside the existing `gate` job**. You pin and record the Semgrep/OSV/
Socket versions, the ASVS level, and the workflow file that pins every CI action by commit in `docs/INVENTORY.md` (Resources). The
escalations are the two **API tokens** — **Socket** and **Semgrep** (`SEMGREP_APP_TOKEN`, for
the Pro engine) — repo secrets, already owner-authorised; set once and referenced as secrets,
never in a file, a prompt, or the allowlist.

**Prefer the CI / remote gate for a real project.** Semgrep runs reliably on Linux in CI and,
with the Semgrep token, uses the Pro (taint) engine that catches the SQL-injection/injection
classes the token-free OSS packs miss. Local-only mode inherits the OSS coverage gap (only
partly closed by the bundled heuristic bridge rules) and Windows-local Semgrep fragility — fine
for a throwaway, but steer a real project to the CI gate (see `Cursor-Project-Configuration.md`
§5c). Record which mode is in force in `docs/INVENTORY.md` (Resources).

The fail-closed `beforeShellExecution` **shell-guard** is **opt-in and off by default**. It
blocks the *builder's* destructive/irreversible/exfil shell commands before they run (and does
not touch your own `git reset --hard HEAD` recovery, which runs through the Bash tool, not
`cursor-agent`). But a verified Cursor bug (2026-09-09) makes `beforeShellExecution` hooks
error under **Git Bash** — the bridge's default builder shell — which, being fail-closed, would
block *every* command. So enable it only when the builder runs under **PowerShell** on Windows,
and only after confirming it fires with the verification harness. It is defense-in-depth; the
gate does not depend on it. If enabled and the builder is legitimately blocked by it, that is a
brief/plan question — never a reason to weaken the guard.

Commit the configuration as its own checkpoint before `TASK-001`, and record in
`docs/PROJECT_STATUS.md` what was configured so a resuming session does not redo it.

**Spending limits (rule 56's neighbour, the owner's money).** For every key or account in
`docs/INVENTORY.md` that can spend money, hand the owner a run sheet to set a spending limit
at the provider, and record it in the Resources row (`limit $20/month, set 2026-10-06`; or
`no spend possible` where the account cannot be charged). The conformance check reports a
row without one. A limit the owner names is theirs: ask for the figure in the question form.

**Gate:** if configuration surfaced anything that meets the escalation bar — a secret or
account, or a dependency carrying a consequence the owner bears (money, privacy, lock-in) —
resolve it with the user before delegating. Routine technical configuration choices you decide
yourself and record; do not escalate them.

### The windowless test suite

Every project's test suite carries the bridge's frozen windowless default (rule 24), written by **cursor-configurator** with the items above (`Cursor-Project-Configuration.md` §2, its windowless-default item). For a pytest suite the default is the fenced block of `~/.claude/cursor-bridge/windowless-default.snapshot.md`, which gives every launch the suite makes without creation flags of its own the flag that opens no window: the configurator creates the test root's `conftest.py` from the block only where the test root has none (`tests/conftest.py`, with its folder, where the project has no test root yet), and where one exists inserts the block once, at the file's end, unless the file already holds its three tokens (`windowless_kwargs`, `Popen.__init__`, `CREATE_NO_WINDOW`), leaving every other line as it stands. The conformance check's floor `Windowless test suite` checks it at every calibration and reflection point. A Node suite has no default yet: the check gives it a NOTE naming its runner and KP-059's mechanism, which you record in the status file. Whatever the runner, the suite itself runs through the launcher, which starts it windowless (`delegation-loop.md`, step 4).

### Keeping the position

While the phase runs, keep the status file's `Next:` line naming the items configured so far and the next one, rewritten as each is finished, so that a resume after a compaction neither redoes an item nor skips one. It names each item by its name only, never a key's value or a path on this computer (rules 53 and 54). Once the configuration's checkpoint is committed, the line names the first increment, and what was configured stands in the status file, as "Commit the configuration as its own checkpoint" above asks, with each tool's pinned version in `docs/INVENTORY.md` (Resources).

## Extension points

This module offers the points below, each by its key in the extension-point registry (`~/.claude/cursor-bridge/workflow/extension-points.md`), which states the kinds of change each accepts and whether it applies per part or per project. A conditional workflow's additions at a point are made where the point's line places them, in the order the core states in "Main and conditional workflows".

- `configuration.items` — configuration items, tools and checks a conditional workflow adds to those above, each worked as they are: written by **cursor-configurator** on your instruction, each tool's pinned version recorded in `docs/INVENTORY.md` (Resources), and committed with the configuration's checkpoint; made once for the whole project.
