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

## 5c. Security tooling — [Claude], with [Escalate] only for the Socket token

Parallel to §5b. All file-based and local except the one commercial secret (the Socket API
token), which the owner has already authorised and sets once as a repo secret. The supervisor
decides and records; `cursor-configurator` writes the files. See `Cursor-File-Formats.md` for
exact shapes. Pick the ASVS level (L1/L2/L3) from data sensitivity in Phase 0/1. Steps:

1. **Deterministic floor configs.** Write `.semgrep.yml` (pinned ruleset), `osv-scanner.toml`
   (empty `[[IgnoredVulns]]`), and `socket.yml` (empty ignores). Pin and record in
   `docs/PROJECT_STATUS.md`: the Semgrep CLI version + ruleset, the OSV-Scanner version, and
   the Socket setup.

2. **Frozen secure-coding rules.** Write `.cursor/rules/secure-coding.mdc` from the bundled
   `~/.claude/cursor-bridge/secure-coding.snapshot.md`, level-filtered to the chosen ASVS
   tier (+ the LLM supplement for AI-bearing products). ASVS is **stable**, so this pins
   `v5.0.0` and needs **no** live-fetch-validation dance — the bundled snapshot is the
   source. Record the ASVS version and level in `docs/PROJECT_STATUS.md`.

3. **CI floor steps (where the project has CI).** Add Semgrep (on `ubuntu-latest`),
   OSV-Scanner (PR diff, explicit exit-code handling — `128`/no-packages **fails**), and
   `socket ci` as **steps inside the existing required `gate` job** — the same job that runs
   the tests and `impeccable detect`. This is **one required check**, so branch protection
   and the merge-watch are unchanged; a high-severity/primary finding turns the single `gate`
   check red. Where the project has **no** CI, the supervisor runs the same three locally at
   the merge gate. Record the ignore mechanisms (`nosemgrep`, `osv-scanner.toml` IgnoredVulns
   with reason+expiry, `@SocketSecurity ignore`) as the security analogue of `impeccable
   ignores` — empty until a reasoned exception is agreed.

4. **The security-detect hook.** Add the *third* `afterFileEdit` entry to the existing
   `.cursor/hooks.json` (see `Cursor-File-Formats.md`): Semgrep run locally, **advisory and
   best-effort** — the exit code never blocks a write; a no-op on a host that cannot run it is
   acceptable because CI is authoritative.

5. **SHA-pin everything.** Every security tool and every CI action is pinned to a **full
   commit SHA, never a mutable tag** (`@v2` is the March-2026 Trivy-compromise vector), the
   SHA recorded in `docs/PROJECT_STATUS.md`. Scanners get only the minimum environment — no
   secrets on a scanner's path beyond Socket's read-scoped token.

**Escalation:** only the **Socket API token** — a repo secret, already owner-authorised; set
once, referenced as a secret, never written to a file or a prompt. Everything else here the
supervisor decides and records; it does not escalate.

---

## 6. Explicitly skipped, and why — [Skip]

On record so nobody wonders whether configuration missed them:

- **Cursor's permission system** (`permissions.json`, `terminalAllowlist`,
  `mcpAllowlist`, run modes, Auto-review, Sandbox). Neutralised by `--force` — Cursor
  does not prompt in a bridge run. The CLI also uses a *separate* file
  (`~/.cursor/cli-config.json`) that must not be mixed with `permissions.json`. The
  bridge's real gate is Claude's own `settings.json` allowlist on the `cursor-agent`
  command plus the review loop.
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

1. §1 repo hygiene (`.gitattributes` → renormalise, `.cursorignore`, `.worktreeinclude`).
2. §2 feedback loop: escalate any new linter deps, commit configs, fix command strings, wire the edit hook, handle the empty-target case.
3. §3 Context7 in `~/.cursor/mcp.json` if the project uses third-party libraries.
4. §4 any other MCP tools the build needs (escalate secrets).
5. §5 at most one cross-cutting rule, only if warranted; surface any inherited config.
6. §5b design tooling (UI-bearing projects): write `.impeccable/config.json`; run the
   Vercel fetch-and-freeze into `.cursor/rules/vercel-interface.mdc` (validate or fall back
   to the bundled snapshot, and record source date + pinned Impeccable version in
   `PROJECT_STATUS.md`); append the second `afterFileEdit` detect hook.
7. §5c security tooling: write `.semgrep.yml`, `osv-scanner.toml`, `socket.yml`, and the
   frozen `.cursor/rules/secure-coding.mdc` from the bundled ASVS snapshot at the chosen
   level; append the third (Semgrep, advisory) `afterFileEdit` hook; pin and record the
   Semgrep/OSV/Socket versions, ASVS level, and every SHA in `PROJECT_STATUS.md`. The Socket
   token escalates once (repo secret).
8. §5b step 5 + §5c step 3 — the design and security floor steps added **inside the existing
   `gate` job** (one required check); where there is no CI, the supervisor runs them locally
   at the gate.
9. Commit the configuration changes as their own checkpoint before `TASK-001`.
10. Record in `docs/PROJECT_STATUS.md` what was configured, so a resuming session
    doesn't redo it.
