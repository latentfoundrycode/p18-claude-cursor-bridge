# Cursor File Formats — Bridge Reference

The exact formats for the config files the bridge writes headlessly, extracted from the
full `Cursor_Configuration_-_Checklist.md` (docs-verified 12 August 2026) so the bridge
does not depend on that GUI-oriented document. This covers only what `cursor-configurator`
actually writes. For anything deeper — the GUI setup, cloud features, run modes — consult
the full checklist separately; none of it applies to a headless `--force` run.

The Cursor CLI is beta. If any format below behaves unexpectedly, `web_fetch` the matching
page under `cursor.com/docs` before relying on it.

---

## `.gitattributes` (project root)

Not cosmetic on Windows: without it, committed shell scripts get CRLF endings and hook
scripts fail with misleading errors.

```gitattributes
* text=auto eol=lf
*.ps1 text eol=crlf
*.bat text eol=crlf
*.cmd text eol=crlf
*.png binary
*.jpg binary
*.mp4 binary
*.mp3 binary
*.wav binary
```

After creating it, run `git add --renormalize .` once. A one-per-file
`CRLF will be replaced by LF` warning on commit is the rule working, not an error.

---

## `.cursorignore` (project root)

Keeps secrets and heavy trees out of the agent's context. `.gitignore` syntax; `!`
negates. Best-effort only — it does **not** block terminal commands or MCP tools, so it
is not a security boundary. Audit and extend any existing file; never overwrite.

```text
**/.env
**/.env.*
**/*.pem
**/*.key
**/credentials.json
node_modules/
dist/
build/
```

Cursor already ignores everything in `.gitignore` plus a large built-in default list
(lockfiles, `node_modules/`, `__pycache__/`, `.venv/`, binaries, media). Don't re-declare
those. Use `**/.env` and `**/.env.*` — not `*.env`, which only matches names *ending* in
`.env`.

---

## `.worktreeinclude` (project root) — bridge-specific

Not a Cursor file. Lists gitignored files that must be copied into the desktop session's
worktree, normally the `.env` the test suite needs. One path per line.

```text
.env
```

---

## `hooks.json` — the linter feedback loop

Project scope `[PROJECT]/.cursor/hooks.json` (committed, and the only scope cloud agents
read) or user scope `~/.cursor/hooks.json`. Cursor reloads on save.

```json
{
  "version": 1,
  "hooks": {
    "afterFileEdit": [
      {
        "command": ".cursor/hooks/lint.py",
        "timeout": 20,
        "matcher": "Write"
      }
    ]
  }
}
```

- **Relative-path rule (usual failure):** project hooks run from the project root
  (`.cursor/hooks/script`), user hooks run from `~/.cursor/` (`./hooks/script`). Wrong
  form silently finds nothing.
- **`matcher`** for `afterFileEdit` targets the tool type: `Write`, `Read`, `Shell`,
  `Task`, `MCP:<tool_name>`.
- **Exit codes:** `0` succeeds, `2` blocks the action, anything else fails **open**.
- **`failClosed: true`** makes a crash/timeout/bad-JSON block instead of pass — use on
  anything security-critical.

### Windows quirks that silently break a hook

1. **Never point `command` at a bare `.sh` or extensionless script** — Windows Cursor
   tries to *open* it, not run it. Invoke an interpreter by explicit path and pass the
   script as an argument, e.g. `".\\.venv\\Scripts\\python.exe .cursor\\hooks\\lint.py"`
   (backslashes doubled for JSON). A hook runs in a fresh shell with no venv activated,
   so the explicit interpreter path is mandatory — same rule as the linter commands.
2. **Strip the UTF-8 BOM from stdin.** Windows Cursor prefixes the stdin JSON payload
   with a BOM (`\uFEFF`); a plain parse throws at column 1. Read stdin as bytes and decode
   `utf-8-sig`, or strip a leading `\uFEFF`. A security hook that catches the parse error
   and returns "allow" fails open — get this right.
3. **`chmod +x` is a no-op on Windows** and unneeded; executability comes from the
   interpreter, not a permission bit. (On POSIX, `chmod +x` the script.)

Script reads its payload on stdin, returns decisions on stdout. `CURSOR_PROJECT_DIR`,
`CURSOR_VERSION`, and `CURSOR_USER_EMAIL` are injected into the environment.

Full event-name list and per-event matcher targets are in full-checklist §15 if you need
an event other than `afterFileEdit`.

### Design-detect hook entry — a *second* `afterFileEdit` object

The design-tooling integration adds one more entry to the **same** `afterFileEdit`
array as the linter — never a second `hooks.json`. It runs the Impeccable detector on
the builder's edits so slop and design-system drift surface live:

```json
{
  "version": 1,
  "hooks": {
    "afterFileEdit": [
      {
        "command": ".cursor/hooks/lint.py",
        "timeout": 20,
        "matcher": "Write"
      },
      {
        "command": "node C:\\path\\to\\global\\node_modules\\impeccable\\dist\\cli.js detect",
        "timeout": 30,
        "matcher": "Write"
      }
    ]
  }
}
```

- **Explicit installed-binary path, not `npx`.** An `npx` cold-start on *every* file edit
  is the Windows latency that would sink this hook (the same activation-independent-path
  rule the linter hook follows). Invoke the interpreter (`node`) explicitly against the
  detector's installed entrypoint. The concrete path is resolved at config time from the
  global install (e.g. `npm root -g` → `impeccable/dist/cli.js`) and settled *before*
  wiring, exactly as the linter command string is — do not point `command` at a bare
  script or a `.cmd` shim, and double the backslashes for JSON.
- **Same Windows quirks as the linter hook apply:** no bare/extensionless script, strip
  the stdin UTF-8 BOM, explicit interpreter. See the quirks block above.
- **The exit code is advisory.** Findings are surfaced to the builder as a nudge; the hook
  is **never** used to block a write. Do not set `failClosed: true` on it and do not treat
  a non-zero exit as a gate — enforcement lives in CI and the `design-auditor`, not here
  (the hook only accelerates convergence). This is the opposite of a security hook.

### Security-detect hook entry — a *third* `afterFileEdit` object (advisory, best-effort)

A third entry in the **same** array runs Semgrep locally on the builder's edits *if* it is
runnable on the host, beside the linter and design-detect entries:

```json
{
  "command": "semgrep --config <pinned-ruleset> --error --quiet",
  "timeout": 40,
  "matcher": "Write"
}
```

- **Advisory and best-effort — CI is authoritative.** Like the design-detect hook, the exit
  code never blocks a write; enforcement is the CI floor and the `security-auditor`. Never
  set `failClosed: true`.
- **Best-effort on Windows.** Semgrep now supports native Windows (GA, no WSL), so this hook
  will usually run — but if the host cannot run it, the entry is a **no-op and that is
  acceptable**, because the CI `gate` job runs Semgrep on Linux authoritatively. Do not make
  the integration depend on the local hook.
- **Same Windows quirks apply** (no bare script, strip the stdin BOM, explicit interpreter);
  invoke Semgrep by its resolved installed path settled at config time, as with the other
  hooks.

---

## `mcp.json` — tools and library docs for the builder

User scope `~/.cursor/mcp.json` or project scope `[PROJECT]/.cursor/mcp.json`. Prefer
**user scope** for the bridge: a post-Customize bug stops some project-level servers from
registering, and user scope keeps keys out of the committed repo.

Local (`stdio`) server:

```json
{
  "mcpServers": {
    "my-server": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "mcp-server-package"],
      "env": { "API_KEY": "${env:MY_SERVER_API_KEY}" }
    }
  }
}
```

Remote server (OAuth-capable) uses `url` and `headers` instead of `command`/`args`:

```json
{
  "mcpServers": {
    "remote-server": {
      "url": "https://api.example.com/mcp",
      "headers": { "Authorization": "Bearer ${env:MY_SERVICE_TOKEN}" }
    }
  }
}
```

- **Interpolate secrets, never hardcode.** Cursor resolves `${env:NAME}`, `${userHome}`,
  `${workspaceFolder}`, `${workspaceFolderBasename}`, `${pathSeparator}` inside `command`,
  `args`, `env`, `url`, and `headers`. `stdio` servers also accept `envFile`. Any literal
  key is an escalation, not a file `cursor-configurator` writes.
- **`.cursor/` write block:** some builds stop agents writing `.json` inside `.cursor/`.
  If a project-scope write fails, the supervisor places the file by hand.

### Context7 (library docs) — the common case

Keyless free tier, remote, commit-safe. Put in `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "context7": { "url": "https://mcp.context7.com/mcp" }
  }
}
```

Under `--force` the first-use approval prompt is auto-approved, so it's available to the
builder immediately. A paid API key for higher limits is an escalation (goes in an env
var or `~/.cursor/mcp.json`, never a committed file).

---

## `.impeccable/config.json` (project root) — design detector context

Declares where the Impeccable detector looks for the visual design context, so it does
drift-checking (font/colour/radius against the documented system) rather than a generic
slop-only pass. **Schema docs-verified against `impeccable.style/docs/config` on
5 September 2026** (the CLI is beta — re-verify if behaviour looks off).

The load-bearing key is **`projectRoots`**, an **array of glob strings** (introduced in
CLI 3.3.0). Each folder a glob matches becomes a "project": it carries its own
`PRODUCT.md` and `DESIGN.md`, and falls back to the repo root per file for any context it
does not define. Pointing a root at `docs/design/` is what makes the detector read the
**visual** `docs/design/DESIGN.md` instead of assuming a repo-root/per-app location — and
is what keeps it from mistaking the architecture `docs/DESIGN.md` for the visual system.

Ignores are **not** a separate top-level object; they live under `detector` as three
arrays. Minimal config that points the context root at `docs/design/` and leaves ignores
empty:

```json
{
  "projectRoots": ["docs/design"],
  "detector": {
    "ignoreRules": [],
    "ignoreFiles": [],
    "ignoreValues": [],
    "designSystem": { "enabled": true }
  }
}
```

- **`projectRoots`** — globs of folders that each own a `DESIGN.md`/`PRODUCT.md`. `["docs/design"]`
  is the bridge's single visual root.
- **`detector.ignoreRules` / `ignoreFiles` / `ignoreValues`** — the recorded, intentional
  exceptions (`impeccable ignores` writes these); keep them empty until a real exception
  is agreed.
- **`detector.designSystem.enabled: true`** — turns on the drift-checking that reading a
  `DESIGN.md` unlocks; the reason the config exists at all.

A `hook` block (`enabled`/`quiet`/`auditLog`) also exists in the docs, but the bridge does
**not** use Impeccable's own installer hook — install `--no-hooks` and wire the detect hook
into the linter's `.cursor/hooks.json` array instead (see the design-detect hook entry
above). Leave the `hook` block out of the written config.

---

## Visual `DESIGN.md` — the visual contract

Lives at **`docs/design/DESIGN.md`**, in the Stitch / awesome-design-md format, and is
produced by **`/impeccable document`** (not hand-authored). It is the file the detector
reads (via the `projectRoots` above) for font, colour, and radius drift, and the visual
contract the builder and `design-auditor` hold to.

**Distinct from `docs/DESIGN.md`**, which stays the **architecture** document (the bridge's
existing convention, untouched). Three filename roles, no overload: `docs/DESIGN.md` =
architecture; `docs/design/DESIGN.md` = visual system; `.cursor/rules/vercel-interface.mdc`
= interface rules.

---

## `.semgrep.yml` (project root) — pinned SAST ruleset

Points the Semgrep floor at the ruleset the project builds against, pinned so a resumed
session runs the same rules. Either an inline `rules:` set or a reference to pinned registry
rulesets. **Docs-verified 6 September 2026** (Semgrep is beta — re-verify if behaviour looks
off; native Windows support is now GA, but the floor still runs Semgrep in CI on Linux).

```yaml
# Pinned ruleset reference — record the exact version/commit in PROJECT_STATUS.md
rules:
  - p/default
  - p/secrets
  - p/owasp-top-ten
```

- Prefer curated registry packs (`p/…`) pinned to a recorded version, or vendor a fixed
  rule file into the repo. Pin the **Semgrep CLI version** too (`PROJECT_STATUS.md`).
- Findings above the chosen severity block in CI. Inline `# nosemgrep` suppressions are a
  **gate-integrity flag** (see `Merge-Verification-Policy.md`) unless justified as a false
  positive with a stated reason.

---

## `osv-scanner.toml` (project root) — known-vuln / malicious-dep floor

Config for OSV-Scanner (OSV.dev + the OpenSSF Malicious Packages feed). Keep
`[[IgnoredVulns]]` **empty** until a real, reasoned, **expiring** exception is agreed (the
security analogue of `impeccable ignores`). **Docs-verified 6 September 2026** (OSV-Scanner
~v2.5.1; cross-platform incl. native Windows).

```toml
# osv-scanner.toml — no ignores until a reasoned, expiring exception is agreed
# [[IgnoredVulns]]
# id = "GHSA-xxxx-xxxx-xxxx"
# ignoreUntil = 2026-12-31
# reason = "why this is acceptable, who agreed, and when it is revisited"
```

- **Exit codes are load-bearing** and must be handled explicitly in CI: `0` clean, `1`
  findings (fail), `127` execution failed (fail), `128` no packages found (**fail** — never
  let an empty inventory pass as green). Parse JSON/SARIF for routing but preserve the raw
  exit code as the pass/fail signal.
- Run against the **PR diff** (base-vs-feature) so only *newly introduced* vulns/malware
  block.

---

## `socket.yml` (project root) — behavioural malicious-package floor

Socket policy/ignore config. Empty ignores until an exception is agreed. **Docs-verified
6 September 2026** (`@socketsecurity/cli`; Node-based, native Windows fine).

```yaml
# socket.yml — Socket policy; no ignores until agreed
version: 2
issueRules: {}
```

- CI runs `socket ci` (= `socket scan create --report`), non-zero on unhealthy alerts.
- The admission gate (§ configuration) uses `socket package score <ecosystem> <pkg>` (the
  ecosystem argument is required, e.g. `socket package score npm lodash`) on the **free
  tier**; full CI reporting needs `SOCKET_CLI_API_TOKEN` as a **repo secret** — never in a
  committed file, a prompt, or the allowlist. A `@SocketSecurity ignore` that silences a
  **real** alert is a gate-integrity flag.

---

## Security CI steps — inside the existing `gate` job

The three floor tools are added as **steps inside the project's existing required CI `gate`
job** (the same job that runs tests, lint, and `impeccable detect`) — **not** as new
required checks. One required check keeps branch protection and the merge-watch unchanged; a
high-severity/primary finding turns the single `gate` check red.

- **Semgrep** runs on `ubuntu-latest` (Linux, fully supported).
- **OSV-Scanner** runs on the PR diff; the step handles exit codes 0/1/127/128 as above.
- **Socket** runs `socket ci` with the token from the repo secret.

**SHA-pin rule (load-bearing — see `Merge-Verification-Policy.md` and the Trivy meta-risk):**
pin every security tool and every CI **action** to a **full commit SHA, never a mutable
tag**. `uses: some-action@v2` is the exact vector exploited in the March 2026 Trivy
supply-chain compromise. Record each pinned SHA in `PROJECT_STATUS.md`. Scanners get only
the minimum environment — no secrets on a scanner's path beyond Socket's read-scoped token.

---

## `.cursor/rules/*.mdc` — only for a cross-cutting invariant

The bridge adds a rule only for something true of *every* task and awkward to repeat in
each brief. Must be `.mdc` (a `.md` file here is ignored — use `AGENTS.md` for plain
markdown). Frontmatter at the very top:

```markdown
---
description: When this rule applies, so the agent can judge relevance
alwaysApply: false
globs: src/components/**/*.tsx, src/hooks/*.ts
---
```

`globs` is a bare comma-separated list — not quoted, not an array. Activation:

| `alwaysApply` | `description` | `globs` | Loads when |
|---|---|---|---|
| `true` | — | — | Always (globs/description ignored) |
| `false` | — | provided | A matching file is in context |
| `false` | provided | omitted | The agent judges it relevant |
| `false` | omitted | omitted | You `@`-mention it |

Keep under 500 lines. Rules do not affect Tab or Inline Edit — Agent/Chat only.

### `.cursor/rules/vercel-interface.mdc` — the frozen interface rules

The design-tooling integration writes one specific rule of this form: the **frozen Vercel
`AGENTS.md` snapshot** (interface-quality rules — keyboard, focus, forms, a11y, motion,
performance) so the builder self-applies them during generation. Use the `.mdc` format
above with:

```markdown
---
description: Web interface quality rules (Vercel), frozen for this project
alwaysApply: false
globs: **/*.tsx, **/*.jsx, **/*.ts, **/*.css
---
```

- **`alwaysApply: false`** with `globs` scoped to UI files, so it loads only when a UI file
  is in context. The `globs` value is a **bare comma-separated list** — not quoted, not an
  array (`**/*.tsx, **/*.jsx, **/*.ts, **/*.css`).
- **Body = the frozen Vercel `AGENTS.md` snapshot**, adopted once per project by the
  fetch-and-freeze step (see `Cursor-Project-Configuration.md`) and never re-derived. Keep
  it under the 500-line guidance (the current `AGENTS.md` is well under it).

### `.cursor/rules/secure-coding.mdc` — the frozen secure-coding rules

The security integration writes a second rule of this form: the **frozen ASVS-derived
secure-coding rules** so the builder self-applies secure-by-default patterns during
generation. Use the `.mdc` format above with:

```markdown
---
description: Secure-coding rules (OWASP ASVS 5.0.0), frozen for this project
alwaysApply: false
globs: **/*.ts, **/*.tsx, **/*.js, **/*.jsx, **/*.py, **/*.go, **/*.rb, **/*.java
---
```

- **`globs` scoped to source files** by stack (bare comma list, not quoted, not an array),
  so it loads when a source file is in context.
- **Body = the level-filtered slice of `~/.claude/cursor-bridge/secure-coding.snapshot.md`**
  for the project's chosen ASVS tier (L1/L2/L3), plus the LLM supplement for AI-bearing
  products. ASVS is **stable**, so the freeze pins `v5.0.0` and does **not** need the
  per-project live-fetch-validation the beta Vercel rules use — the bundled snapshot is the
  source. Record the ASVS version and level in `PROJECT_STATUS.md`.
