# Cursor Project Configuration for the Bridge (Headless)

The checklist Claude works through **once per project**, after the build plan is
approved and before the first `cursor-agent` delegation, to give the headless builder
the best possible environment.

This is the bridge-adapted subset of Cursor's configuration. The full
`Cursor_Configuration_-_Checklist.md` is a human-GUI setup document; most of it —
windows, palettes, the Customize sidebar, the cursor.com dashboard, Cloud Agents,
Bugbot, Linear, run modes, sandbox — is unreachable and irrelevant when Claude drives
`cursor-agent` headlessly. This checklist and its companion `Cursor-File-Formats.md`
(both in `~/.claude/cursor-bridge/`) carry everything the bridge needs, so it does not
depend on that GUI document. Use the companion for exact file formats; use this one to
decide what to do.

## Guiding principle

Configure only what is **load-bearing and cannot live in a per-task handoff brief.**
The bridge's design axiom is that the brief carries the constraints, not a persistent
builder role. So: set up the feedback loop and the tools; do **not** author a wall of
rules and skills that duplicate what a brief already says. When in doubt, leave it to
the brief.

## Tags used below

- **[Claude]** — file-based; Claude can create or edit it directly and commit it.
- **[Escalate]** — needs a secret, a dashboard/Customize-UI action Claude cannot reach,
  a new dependency, or a design decision. Route through the human gate; never silently
  do or skip it.
- **[Skip]** — interactive- or cloud-only, or neutralised by `--force`. Not applicable
  to the headless bridge. Listed so the reason is on record.

---

## 1. Repo hygiene the builder depends on — [Claude]

- **`.gitattributes`** for line endings. On Windows this is not cosmetic: without it,
  shell scripts committed from Windows acquire CRLF endings and hook scripts (§2) and
  worktree setup scripts fail with errors that name the wrong cause. Use the block from
  Use the block in `Cursor-File-Formats.md` (`* text=auto eol=lf`, `.ps1/.bat/.cmd` as `crlf`, binaries as
  `binary`), then `git add --renormalize .` once.
- **`.cursorignore`** to keep secrets and heavy trees out of the agent's context
  (`**/.env`, `**/.env.*`, `**/*.pem`, `**/*.key`, `node_modules/`, `dist/`, `build/`).
  Audit any pre-existing file and extend rather than overwrite. Caveat: `.cursorignore`
  is best-effort, not a security boundary — terminal commands and MCP tools are not
  blocked by it, which is exactly why secret handling still rests on the brief and
  `secret-sentinel`.
- **`.worktreeinclude`** (bridge-specific, not in the Cursor checklist) listing any
  gitignored file the tests need — normally `.env` — so it reaches the session worktree.
- **The Workspace boundary** (bridge-specific). The builder must never read or write outside
  `Workspace/` — the sibling `Documents/` folder is the user's and the supervisor's alone.
  Enforced as an instruction plus a detector, and nothing more: write
  `.cursor/rules/workspace-boundary.mdc` (always-on; format in `Cursor-File-Formats.md`) and
  append the advisory **`boundary-check`** `afterFileEdit` hook entry (§2 hook array), which
  copies `~/.claude/cursor-bridge/boundary-check.py` into `.cursor/hooks/` and logs any edit
  outside the workspace to `docs/BOUNDARY_VIOLATIONS.md`. It detects after the fact; only the
  opt-in shell guard (§5c step 6) can deny such a write beforehand. Same Windows quirks as
  every hook: explicit interpreter, no bare script, BOM-tolerant (the script strips it).

### Worktree & junction teardown — the safe primitive (Windows)

A session worktree that contains a **junction or symlink** (a per-worktree venv, a
`node_modules` linked to the main checkout) is a data-loss hazard on teardown:
`git worktree remove --force` **follows a live junction and deletes the real target**, and a
`rmdir` issued *through Git Bash* can silently fail on a mangled path — leaving the junction
alive for `--force` to follow. This has destroyed a main checkout's `node_modules` in
practice. Never hand-roll teardown; use this order every time:

1. **Remove the link first, with a native Windows path, not through Git Bash** — from
   PowerShell: `cmd /c rmdir "<worktree>\node_modules"`. `rmdir` on a junction removes
   **only the link**, never the target. Never `rm -rf` or `Remove-Item -Recurse` a junction —
   those follow it into the real directory.
2. **Verify both halves:** `Test-Path "<worktree>\node_modules"` → `False` (link gone) **and**
   `Test-Path "<main>\node_modules"` → `True` (target survived).
3. **Only then** `git worktree remove <worktree>` — without `--force`. Use `--force` only after
   step 2 has confirmed no live link remains inside the worktree.

Treat `git worktree remove --force` on a worktree you have not link-checked as forbidden. (The
opt-in shell-guard denies it for the builder too.)

**Warm environment (performance):** rebuilding a from-source toolchain (a mypy build, a large
`node_modules`) in every new worktree costs minutes per increment. Prefer a **cached/warm
environment reused across worktrees** — a shared cache the worktree points at — over
reinstalling per worktree. `.worktreeinclude` carries the gitignored *files* the tests need,
not a package tree, so plan the reuse explicitly and record it in `docs/PROJECT_STATUS.md`.

---

## 2. The feedback loop — highest value — [Claude], with [Escalate] for new deps

This is the single most valuable thing configuration does: make the builder able to see
and fix its own lint/type errors without a human in the loop.

- **Install linters/formatters/type-checkers as project dev dependencies**, not editor
  extensions. A terminal-run agent can only invoke what's in the manifest. Adding a new
  dependency is **[Escalate]** — name it, its licence, and why — per the bridge's
  dependency gate.
- **Commit a config file per tool** to the repo root so CLI, hook, and CI agree.
- **Make every command activation-independent.** Agents and hooks spawn a fresh shell
  that never ran your venv `activate`. Invoke tools by explicit interpreter path
  (`.\.venv\Scripts\python.exe -m ruff check .` on Windows) so the identical string
  works in the hook, in CI, and when Claude runs it by hand. Settle this string
  *before* wiring the hook.
- **Wire an `afterFileEdit` hook** (`hooks.json`; see `Cursor-File-Formats.md`, including
  the Windows quirks that silently break hooks) that runs the
  relevant linter and returns findings. This is what actually puts linter output in
  front of Cursor on every edit, including headless runs.
- **Empty-target gotcha:** a type checker like mypy exits non-zero when its target dirs
  contain no source files yet. Drop an empty `__init__.py` into each type-checked
  package so the check is green until real code exists — otherwise the first delegation
  "fails" for no real reason.
- **Windowless by default — the user works on the same machine.** Every console process a
  hook or any agent tooling launches on Windows pops a visible terminal window unless the
  launch site opts out (`creationflags=CREATE_NO_WINDOW` in Python, `windowsHide: true` in
  Node); capturing output does not prevent it. Because hooks fire per file edit, the
  windows come in dozens and cascade over the user's own work. Standing rule: **every hook
  script uses the idiom at every launch site; every direct-command hook entry is wrapped in
  `.cursor/hooks/run-hidden.py`**; the only visible processes are ones whose window serves
  the user (a dev server they follow, an interactive prompt, a deliberate debugging run),
  marked `windowless: visible-ok <reason>` at the call site. A spawn that relies on
  `CREATE_NEW_PROCESS_GROUP` for a `CTRL_BREAK` stop is hidden only after its stop path is
  tested (signal caveat). Idioms, wrapper, marker, and the check are in
  `Cursor-File-Formats.md` §"Windowless by default". Verify once with a throwaway edit while
  watching the desktop: no flash.
- **Gate commits on lint failure — the deterministic floor.** Add a committed
  `.githooks/pre-commit` (see `Cursor-File-Formats.md`) that runs the same settled lint
  command **and the windowless check** (`.cursor/hooks/windowless-check.py`) and blocks a
  failing commit, then set `git config core.hooksPath .githooks` once.
  Unlike the `afterFileEdit` hook (advisory, model can ignore) this is mechanical and
  un-skippable. **Lint only** (type-check stays with `test-runner`/CI). The supervisor's
  pre-delegation checkpoint commits use `git commit --no-verify` (recovery anchors that must
  always succeed); accept/increment commits pass the gate. This is the checklist's own "Gate
  Commits on Lint Failure" step.

---

## 3. Library documentation for the builder — [Claude], [Escalate] only for a key

Cursor's old `@Docs` indexer was removed (~3.14). The current mechanism for current,
version-specific library docs is the **Context7 MCP server** (see `Cursor-File-Formats.md`).

- Add it to **`~/.cursor/mcp.json`** (user scope), not the project file. Two reasons:
  a known post-Customize bug stops some project-level `.cursor/mcp.json` servers from
  registering, and user scope keeps any future API key out of the committed repo.
- The free tier is keyless — commit-safe, nothing to escalate. Adding a Context7 **API
  key** for higher limits is **[Escalate]** (it's a secret; it goes in an env var or
  `~/.cursor/mcp.json`, never a committed file).
- Note the interaction with `--force`: a normal Cursor session prompts before first use
  of an MCP tool. Under `--force` that prompt is auto-approved, so Context7 is available
  to the builder immediately once configured. This is a case where `--force` helps.

---

## 4. Other tools the builder needs — [Claude] config, [Escalate] for secrets

Anything the builder must reach that a brief cannot grant — a database, a browser, an
API — is an MCP server in `mcp.json` (see `Cursor-File-Formats.md`). A brief can tell Cursor
*what* to do; only an MCP server can give it the *capability*. Config with
`${env:NAME}` interpolation is **[Claude]**; the underlying secret is **[Escalate]**.

---

## 5. Rules and skills — deliberately minimal — mostly [Skip], rarely [Claude]

Default to **not** authoring these. The brief carries per-task constraints, and every
persistent rule is a second voice in every build that can drift from the brief.

- Add a **project rule** (`.cursor/rules/*.mdc`, note `.mdc` not `.md`) only for a
  genuine cross-cutting invariant that is true for *every* task and awkward to repeat in
  each brief — e.g. "this repo targets Python 3.11; never use 3.12-only syntax." Keep it
  under the 500-line guidance. **[Claude]**
- **The bridge's own frozen rules are the deliberate exception.** `cursor-configurator`
  writes them verbatim from the bundled snapshots, never authored ad hoc:
  `vercel-interface.mdc` (UI projects, §5b), `secure-coding.mdc` (§5c), and
  **`minimal-code.mdc` — every project** (the "write the least code that meets the
  acceptance criteria" ladder, with safety rules taking precedence; see
  `Cursor-File-Formats.md`). These are owned, frozen, and auditable — not a second drifting
  voice. **[Claude]**
- Do **not** port skills or subagents into Cursor. The bridge's specialists live on the
  Claude side; duplicating them in Cursor splits the source of truth. **[Skip]**
- If a pre-existing repo already ships `.cursor/rules`, `AGENTS.md`, or `CLAUDE.md`,
  surface them to the human — they will apply on every run and may conflict with the
  brief. Deciding to keep or retire them is a design call: **[Escalate]**.

---

## 5b. Design tooling — [Claude]

All file-based, all local, all Apache-2.0/MIT, no secrets — so **nothing here escalates.**
The supervisor decides and records; `cursor-configurator` writes the files. See
`Cursor-File-Formats.md` for the exact shapes. Five steps:

1. **Detector config.** Write `.impeccable/config.json` with
   `projectRoots: ["docs/design"]` so the Impeccable detector loads the visual system from
   `docs/design/DESIGN.md` and does font/colour/radius drift-checking, not just generic
   slop. Leave the `detector.ignore*` arrays empty until a real exception is agreed.

2. **Frozen Vercel rules (fetch-and-freeze) — the load-bearing new step.** Do this **once,
   here at config time** — never per review, never on resume:
   - **Fetch** the current Vercel interface rules from the canonical raw URL
     `https://raw.githubusercontent.com/vercel-labs/web-interface-guidelines/main/AGENTS.md`
     (docs-verified 5 September 2026; `AGENTS.md` is the superset that carries the
     hit-target and 16-px-input MUSTs the command sheet drops).
   - **Validate before adopting.** Confirm the fetched body actually holds the real rule
     headings (`## Interactions`, `## Animation`, `## Layout`, `## Content & Accessibility`,
     `## Performance`, …) and the MUST/SHOULD/NEVER rule lines — not an error page, an
     empty body, or a truncated file. **If it does not validate, fall back to the bundled
     snapshot at `~/.claude/cursor-bridge/vercel-interface.snapshot.md` and record that the
     fallback was used.** Never freeze an unvalidated fetch.
   - **Freeze it.** Write the adopted content as the body of
     `.cursor/rules/vercel-interface.mdc` (frontmatter per `Cursor-File-Formats.md`), frozen
     for the project's life so reviews stay reproducible, and **record the source
     version/date** in `docs/PROJECT_STATUS.md`.
   - **Optional FYI.** If the fresh fetch validates and differs from the bundled baseline,
     note "guidelines changed since your last project" as an FYI — do not block on it.

3. **Impeccable version pin.** Record the pinned CLI version in `docs/PROJECT_STATUS.md`.
   Every detector invocation — hook, CI, and manual — uses `npx impeccable@<pinned> detect`
   so a resumed session never silently changes what "clean" means (the rule count drifts
   between releases; pin ≥ v3.0.2, never hard-code the count).

4. **The design-detect hook.** Add the *second* `afterFileEdit` entry to the existing
   `.cursor/hooks.json` array (see `Cursor-File-Formats.md`): the Impeccable detector by
   **explicit installed-binary path** (not `npx`), advisory only — findings surface to the
   builder, the exit code never blocks a write.

5. **CI step (where the project has CI).** Add `npx impeccable@<pinned> detect --json <ui
   paths>` as a **step inside the project's existing CI `gate` job** — the same workflow
   that runs the test suite — so a **primary** finding turns the already-required `gate`
   check red. It is **not** a second, separate required check: there stays one required
   check, so branch protection and the supervisor's merge-watch are unchanged.
   `impeccable ignores` is how intentional exceptions are recorded (they land in
   `.impeccable/config.json`'s `detector.ignore*` arrays). Where the project has **no** CI,
   the supervisor runs this same command locally at the merge gate instead.

---

## 5c. Security tooling — [Claude], with [Escalate] only for the Socket and Semgrep tokens

Parallel to §5b. All file-based and local except two commercial secrets (the Socket and
Semgrep API tokens), which the owner has already authorised and sets once as repo secrets. The
supervisor decides and records; `cursor-configurator` writes the files. See
`Cursor-File-Formats.md` for exact shapes. Pick the ASVS level (L1/L2/L3) from data sensitivity
in Phase 1/2.

**Prefer the CI / remote gate for real projects.** Semgrep runs reliably on Linux in CI and,
with a token, uses the **Pro engine** (interfile taint) that catches the SQLi/injection classes
the token-free OSS packs miss. **Local-only** mode inherits two known weaknesses — the OSS
coverage gap (partly closed by the bundled bridge rules, but those are heuristic, not taint) and
Windows-local Semgrep fragility — so use it for throwaways, and steer a real project toward the
CI gate at Phase 1/config. Steps:

1. **Deterministic floor configs.** Write `.semgrep.yml` (pinned ruleset), copy
   `semgrep-bridge-rules.yml` in as `.semgrep/bridge-rules.yml` (the token-free concat-SQLi
   supplement — always added, validated per project), `osv-scanner.toml` (empty
   `[[IgnoredVulns]]`), and `socket.yml` (empty ignores). Pin and record in
   `docs/PROJECT_STATUS.md`: the Semgrep CLI version + ruleset, the OSV-Scanner version, and
   the Socket setup.

2. **Frozen secure-coding rules.** Write `.cursor/rules/secure-coding.mdc` from the bundled
   `~/.claude/cursor-bridge/secure-coding.snapshot.md`, level-filtered to the chosen ASVS
   tier (+ the LLM supplement for AI-bearing products). ASVS is **stable**, so this pins
   `v5.0.0` and needs **no** live-fetch-validation dance — the bundled snapshot is the
   source. Record the ASVS version and level in `docs/PROJECT_STATUS.md`.

3. **CI floor steps (where the project has CI — the preferred setup).** Add Semgrep (on
   `ubuntu-latest`), OSV-Scanner (PR diff, explicit exit-code handling — `128`/no-packages
   **fails**), and `socket ci` as **steps inside the existing required `gate` job** — the same
   job that runs the tests and `impeccable detect`. This is **one required check**, so branch
   protection and the merge-watch are unchanged; a high-severity/primary finding turns the
   single `gate` check red.
   - **CI / Pro (Semgrep).** Run the Semgrep step as `semgrep ci` with the **`SEMGREP_APP_TOKEN`
     repo secret** set in the job env — this runs the **Pro engine** (taint/interfile, the real
     SQL-injection catch and fewer false positives). When no token is configured, fall back to
     `semgrep --config <pinned packs> --config .semgrep/bridge-rules.yml` (OSS engine + the
     bundled bridge rules). Record which mode is in force in `docs/PROJECT_STATUS.md`.
   Where the project has **no** CI, the supervisor runs the three locally at the merge gate
   (token-free OSS + bridge rules for Semgrep). Record the ignore mechanisms (`nosemgrep`,
   `osv-scanner.toml` IgnoredVulns with reason+expiry, `@SocketSecurity ignore`) as the security
   analogue of `impeccable ignores` — empty until a reasoned exception is agreed.

4. **The security-detect hook.** Add the *third* `afterFileEdit` entry to the existing
   `.cursor/hooks.json` (see `Cursor-File-Formats.md`): Semgrep run locally, **advisory and
   best-effort** — the exit code never blocks a write; a no-op on a host that cannot run it is
   acceptable because CI is authoritative.

5. **SHA-pin everything.** Every security tool and every CI action is pinned to a **full
   commit SHA, never a mutable tag** (`@v2` is the March-2026 Trivy-compromise vector), the
   SHA recorded in `docs/PROJECT_STATUS.md`. Scanners get only the minimum environment — no
   secrets on a scanner's path beyond Socket's read-scoped token.

6. **The shell guard (fail-closed) — OPT-IN, off by default.** *Only* wire this when the
   supervisor has explicitly opted in **and** the builder is launched under PowerShell on
   Windows. When enabled: add a `beforeShellExecution` entry to `.cursor/hooks.json` with
   `failClosed: true`, and place the guard script at `.cursor/hooks/shell-guard.py` verbatim
   from the bundled `~/.claude/cursor-bridge/shell-guard.py` (see `Cursor-File-Formats.md`). It
   runs before the builder executes any shell command and **blocks** a tight deny-list of
   destructive / irreversible / exfil commands (recursive deletes of dangerous targets,
   history-rewriting or force git, download-piped-to-a-shell, outbound data transfer,
   privilege escalation, writes to protected paths); everything else passes.
   **Do not enable it for a Git-Bash-launched builder** (the bridge's default shim path): a
   verified Cursor bug (2026-09-09) makes `beforeShellExecution` hooks error under Git Bash,
   which — being fail-closed — would block *every* command and brick the build. Confirm it
   fires on the target setup with the verification harness before enabling. The gate does not
   depend on it (defense-in-depth only).

**Escalation:** only the two **API tokens** — the **Socket** token and the **Semgrep**
(`SEMGREP_APP_TOKEN`, for the Pro engine) token — both repo secrets, already owner-authorised;
set once, referenced as secrets, never written to a file, a prompt, or the allowlist.
Everything else here the supervisor decides and records; it does not escalate.

---

## 5d. Observability tooling — [Claude], with [Escalate] only for the driver dependency

For **UI-bearing** projects only (those with a Phase-1 screen-and-state inventory). Per
`Observability-Conventions.md` — gives the gate a view of the *running render*. The supervisor
owns the tier decision (Tier A default; Tier B opt-in) and records it. Steps:

1. **Observability e2e tests → the CI `gate` job.** Wire the supervisor-authored observability
   tests (drive each inventory state through the real render path; assert no runtime invariant
   fired, no `console.error`, required states present) as a step **inside the existing `gate`
   job** — one required check, on demand, no daemon. Locally (no CI) they run at the merge gate.
2. **Test-mode determinism.** Configure fixed clock/seed/locale in test mode so state dumps and
   screenshots are comparable; ensure the app is startable headlessly/reproducibly in CI.
3. **Artifacts + secret surface.** Gitignore the screenshot/log artifacts dir (ephemeral, never
   committed); confirm logs redact secrets/PII (already required by `secure-coding.mdc`); ensure
   any test-mode reachability hook is compiled out of production (ASVS V13). `secret-sentinel`
   scans retained runtime logs for secret shapes.
4. **Driver.** Web: **Playwright**, run in CI on Linux (primary), local optional. Mobile/desktop:
   a per-platform driver (Appium / WinAppDriver / Playwright-Electron). Pin and record the driver
   + version, the tier, the invariant set, and the state→reachability map in
   `docs/PROJECT_STATUS.md`.

**Escalation:** only the **driver dependency** (a new dev/CI dependency + CI minutes) — cleared
with the user like any dependency. The instrumentation the tests exercise is product code Cursor
builds from the brief; the tests are the supervisor's. Assertions are hand-rolled (no new dep).

---

## 5e. Performance floor — [Claude], only where budgets exist

Per `Performance-Conventions.md`. Write `bench/budgets.json` from the intake budgets; the
bench runner (`scripts/bench.ps1`, median of ≥5 runs for timings, peak for memory, accounted
total for cost) and the profiler wrapper (`scripts/profile.ps1`) are increments the builder
builds, not configuration; add the `bench-check.py` step to the CI `gate` job after the tests
(fail on exit 1); pin the benchmark and profiling tools for the stack; gitignore
`bench/results/` and `bench/profiles/`, commit `bench/baseline.json`. Where CI runners are too
noisy for an absolute budget, CI checks the regression band and the absolute number is checked
locally at stage close — record which in `docs/PROJECT_STATUS.md`.

## 6. Explicitly skipped, and why — [Skip]

On record so nobody wonders whether configuration missed them:

- **Cursor's permission system** (`permissions.json`, `terminalAllowlist`,
  `mcpAllowlist`, run modes, Auto-review, Sandbox). Neutralised by `--force` — Cursor
  does not prompt in a bridge run. The CLI also uses a *separate* file
  (`~/.cursor/cli-config.json`) that must not be mixed with `permissions.json`. The
  bridge's real gate is Claude's own `settings.json` allowlist on the `cursor-agent`
  command plus the review loop. **Sandbox specifically includes `sandbox.json` network
  egress control — empirically confirmed (2026-09-09) NOT enforced under `-p --force`** (a
  deny-by-default policy allowing only one domain still let a non-allowlisted request through),
  so it is not worth wiring; exfil/malicious-network risk is covered instead by the
  dependency-admission gate, Socket, and (opt-in) the shell-guard.
- **The Customize UI, command palette, keyboard shortcuts, window switching** —
  interactive-only.
- **Dashboard connections (GitHub/Linear), Cloud Agents, Bugbot, PR routing,
  Automations** — cloud features. The bridge deliberately keeps one actor per working
  tree; cloud agents run on a separate VM and would violate that.
- **Checkpoints, message queueing, `.cursorindexingignore`** — editor-session features;
  indexing tuning gives the headless builder nothing the brief and `.cursorignore` don't
  already cover.

---

## 7. Escalation summary — [Escalate]

Stop and ask the human, leading with the decision and a recommendation, whenever
configuration would require:

- a secret, key, or token (Context7 paid key, MCP server credentials, any auth);
- a new project dependency (linters included — name it, licence, reason);
- an action only reachable in Cursor's GUI or the cloud dashboard;
- a decision about pre-existing Cursor config in an adopted repo;
- anything the design document does not already settle.

---

## 8. Reliability and verification

The Cursor CLI is beta; flags and file formats move between releases. Two habits keep
this reliable:

- **Pin and date.** The formats in `Cursor-File-Formats.md` were verified against
  `cursor.com/docs` on 12 August 2026. Treat that as the baseline. When acting on any
  item, if the behaviour looks off, re-verify against the live docs before relying on it.
- **Fetch, don't guess.** For anything these two bridge files don't cover,
  `web_fetch` the relevant page under `cursor.com/docs` rather than working from memory.
  This is the reliable-doc-access mechanism for the supervisor: a distilled local
  reference (these two files) as primary, live docs as fallback — no external
  knowledgebase to build or maintain.

---

## Configuration run — order of operations

1. §1 repo hygiene (`.gitattributes` → renormalise, `.cursorignore`, `.worktreeinclude`,
   `.cursor/rules/workspace-boundary.mdc` + the `boundary-check` hook entry).
2. §2 feedback loop: escalate any new linter deps, commit configs, fix command strings, wire the edit hook **windowless** (idiom in every hook script; `run-hidden.py` on every direct-command entry), handle the empty-target case, and set up the pre-commit lint gate (`.githooks/pre-commit` running the lint command + `windowless-check.py`; `git config core.hooksPath .githooks`).
3. §3 Context7 in `~/.cursor/mcp.json` if the project uses third-party libraries.
4. §4 any other MCP tools the build needs (escalate secrets).
5. §5 at most one *project-specific* cross-cutting rule, only if warranted; write the
   bridge's frozen `minimal-code.mdc` for every project (§5b/§5c add `vercel-interface.mdc`
   and `secure-coding.mdc`); surface any inherited config.
6. §5b design tooling (UI-bearing projects): write `.impeccable/config.json`; run the
   Vercel fetch-and-freeze into `.cursor/rules/vercel-interface.mdc` (validate or fall back
   to the bundled snapshot, and record source date + pinned Impeccable version in
   `PROJECT_STATUS.md`); append the second `afterFileEdit` detect hook.
7. §5c security tooling: write `.semgrep.yml`, `osv-scanner.toml`, `socket.yml`, and the
   frozen `.cursor/rules/secure-coding.mdc` from the bundled ASVS snapshot at the chosen
   level; append the third (Semgrep, advisory) `afterFileEdit` hook; **(opt-in only, and only
   for a PowerShell-launched builder)** the fail-closed `beforeShellExecution` shell-guard hook
   (+ place `shell-guard.py`); pin and record the Semgrep/OSV/Socket versions, ASVS level, and
   every SHA in `PROJECT_STATUS.md`. The Socket token escalates once (repo secret).
8b. §5e performance floor (where budgets exist): `bench/budgets.json`, the `bench-check.py` CI step, pinned bench/profile tools, gitignores.
8. §5d observability (UI-bearing projects): wire the supervisor-authored observability e2e
   tests into the `gate` job, set test-mode fixed clock/seed/locale, gitignore the artifacts,
   confirm log redaction; escalate the driver dependency (Playwright / per-platform). Record
   the tier, driver + version, invariant set, and state→reachability map in `PROJECT_STATUS.md`.
9. §5b step 5 + §5c step 3 + §5d step 1 — the design, security, and observability floor steps
   added **inside the existing `gate` job** (one required check); where there is no CI, the
   supervisor runs them locally at the gate.
10. Commit the configuration changes as their own checkpoint before `TASK-001`.
11. Record in `docs/PROJECT_STATUS.md` what was configured, so a resuming session
    doesn't redo it.
