# Known Pitfalls — Bridge (cross-project lessons)

A curated, **cross-project** catalogue of misconceptions and mistakes the loop has made,
how each surfaced, and what the correct behaviour is — so the same mistake is not re-learned
on a fresh project. This is governance (installed at `~/.claude/cursor-bridge/`), **read by
the supervisor** at the configure/build phases and by `plan-critic`, and it is distinct from
the per-project `docs/HARDENING.md` (project-local hardening) and `docs/CHANGES.md`
(project-local behaviour log).

**How it flows (respecting the governance/loop boundary):**
- The supervisor **reads** this file — it is instructions, like every other bridge doc.
- When the loop discovers a *generalizable* misconception/mistake during a run, the supervisor
  **records it in the project's `Documents/<Name> Issues During Development and Their
  Solutions.md`** under its `ISS-nnn`, marked `generalizable: yes` — not here.
- The **maintainer promotes** generalizable entries from a project's Issues file up into this
  file when the owner brings it. Governance changes at maintenance time, not mid-run.

**Curation rule:** keep entries *generalizable* (they recur across projects). Project-specific
trivia stays in that project's Issues file. Prune entries that a later bridge change has
made obsolete. Each entry: **misconception/mistake → how it surfaced → the correction → where
it applies.**

---

## Tooling / platform (Cursor · Windows · the security & design stack)

### KP-001 — OSS Semgrep does not catch string-concatenation SQL injection
- **Misconception:** the token-free Semgrep floor (`p/default`, `p/secrets`, `p/owasp-top-ten`)
  would catch injected SQL built by string concatenation.
- **Surfaced:** the security S10 self-test — a planted `db.prepare('…' + term)` passed the gate;
  only a CSRF advisory fired.
- **Correction:** interprocedural taint SQLi lives in **Semgrep Pro**. The bridge ships a
  token-free heuristic supplement (`semgrep-bridge-rules.yml`, added to every project's gate)
  that catches the concat shape, and **prefers the CI gate with the Pro engine**
  (`semgrep ci` + `SEMGREP_APP_TOKEN`) for real SQLi/taint coverage. The bundled rule is a
  shape-matcher, not taint — validate it per project and rely on Pro for the real catch.
- **Applies:** every UI/logic project with a database.

### KP-002 — `beforeShellExecution` hooks break under Git Bash on Windows
- **Misconception:** a `beforeShellExecution` hook wired for a Git-Bash-launched `cursor-agent`
  would run.
- **Surfaced:** the shell-guard `--force` verification — it PASSED under a PowerShell-launched
  builder but the hook errored under Git Bash (Cursor emits PowerShell runner syntax
  `| & { … }` that bash cannot execute); being fail-closed it would have blocked *every*
  command and bricked the build.
- **Correction:** it is a documented Cursor bug with **no config fix** (no `--shell` flag, no
  `cli-config.json` shell field). The shell-guard ships **opt-in**, enabled only for a
  PowerShell-launched builder. Do not enable a fail-closed `beforeShellExecution` hook on the
  default Git-Bash path.
- **Applies:** any project considering the shell-guard on Windows.

### KP-003 — `sandbox.json` network egress is NOT enforced under `--force`
- **Misconception:** a deny-by-default `sandbox.json` network policy would constrain the
  builder's egress in a bridge run.
- **Surfaced:** the sandbox egress verification — a policy allowing only `registry.npmjs.org`
  still let `example.com` through (200/200) under `cursor-agent -p --force`.
- **Correction:** confirmed neutralised by `--force`. Do not rely on `sandbox.json` for egress.
  Exfil/malicious-network risk is covered by the dependency-admission gate + Socket + the
  (opt-in) shell-guard instead.
- **Applies:** any project where egress restriction was being considered.

### KP-004 — `socket package score` needs an ecosystem argument (and often a token)
- **Misconception:** `socket package score <pkg>` is the admission-gate command.
- **Surfaced:** the CLI requires the ecosystem: `socket package score npm <pkg>`. Package
  *scoring* works on the free tier; full `socket ci` reporting needs `SOCKET_CLI_API_TOKEN`,
  and some orgs require a token/login even for scoring.
- **Correction:** always pass the ecosystem; treat the Socket token as an authorized repo
  secret for CI reporting.
- **Applies:** every dependency-admission-gate run.

### KP-005 — OSV-Scanner exit code 128 ("no packages found") must FAIL, not pass
- **Misconception:** a clean/zero-finding OSV run means green.
- **Correction:** handle exit codes explicitly — `0` clean, `1` findings (fail), `127`
  execution failed (fail), **`128` no packages found (FAIL)** — never let an empty inventory
  pass as green; preserve the raw exit code as the pass/fail signal.
- **Applies:** every CI/local OSV step.

### KP-006 — The Cursor Agent CLI on Windows always uses PowerShell for command execution
- **Misconception:** the builder runs commands under the shell it was launched from (e.g. Git
  Bash).
- **Correction:** on Windows the CLI hardcodes PowerShell for command execution (no `--shell`
  flag, no `cli-config.json` shell field, `$SHELL`/`$COMSPEC` ignored). Write hook/probe
  commands accordingly (e.g. `curl.exe`, PowerShell-safe redirections).
- **Applies:** any Windows project wiring hooks or driving the builder's shell.

### KP-007 — Local Windows Semgrep breaks from global Python dependency drift
- **Misconception:** a working local Semgrep stays working.
- **Surfaced:** mid-session, Semgrep failed to start (pydantic-core / `mcp` version clash in the
  shared global Python install).
- **Correction:** install Semgrep isolated (`pipx`/dedicated venv), or rely on **CI-on-Linux**
  as authoritative; treat local Windows Semgrep as best-effort. A scanner that won't start is a
  hard RED, never a pass.
- **Applies:** any project relying on local Semgrep on Windows.

---

## Process / discipline

### KP-008 — Verify-first for any Cursor beta capability under `--force` on Windows
- **Lesson:** repeatedly, documented/assumed behaviour was stale or wrong (Semgrep-on-Windows,
  `beforeShellExecution`, `sandbox.json`). Before relying on any Cursor beta capability
  (hooks, sandbox, run-modes) in a `--force`/headless/Windows context, **confirm it engages
  empirically** with a throwaway probe — do not assume from docs.
- **Applies:** every new capability the bridge considers adopting.

### KP-009 — Inline task content in the `cursor-agent` prompt gets mangled by the shell
- **Mistake:** passing code, paths, or corrections inline in the CLI argument
  (`cursor-agent -p "...code..."`), especially during re-delegation.
- **Surfaced:** field use — Git Bash consumed backticks and `${…}` before Cursor saw them; the
  builder "improvised" and twice skipped the exact fix requested (once a CI-breaker). The same
  instructions in a committed file worked every time.
- **Correction:** the delegate command is a **constant pointer** to `handoff/TASK-<nnn>.md`
  and carries no content. Corrections and re-delegations go into the brief file (revised in
  place or `TASK-<nnn>-r2.md`); never into the prompt.
- **Applies:** every delegation and re-delegation.

### KP-010 — The builder's self-report is not evidence
- **Mistake:** treating Cursor's printed "files I changed" / "done, N passed" as status.
- **Surfaced:** field use — summaries claimed fixes that were not made and described
  unrequested changes as the requested ones; caught only by `git diff` + re-running the gate.
- **Correction:** the working tree is the only manifest. Derive the changeset from git, run
  the deterministic `scope-check.py` (file-level `SCOPE DRIFT` surfaced before any reviewer),
  and re-run the gate. Never surface a builder claim as fact. A builder-produced "structured
  manifest" would still be a self-report — do not ask for one; derive it.
- **Applies:** every increment.

### KP-011 — `git worktree remove --force` follows a live junction and deletes the real target
- **Mistake:** tearing down a worktree that held a junction (a per-worktree venv /
  `node_modules` linked to the main checkout) with `git worktree remove --force`, after a
  `rmdir` issued through Git Bash had silently failed on a mangled path and left the junction
  alive.
- **Surfaced:** field use — the main checkout's `tools/…/node_modules` was destroyed.
- **Correction:** the safe primitive (`Cursor-Project-Configuration.md` §1): remove the link
  first with a **native Windows path** from PowerShell (`cmd /c rmdir` — on a junction it
  removes only the link), `Test-Path`-verify the link is gone **and** the target survives,
  *then* `git worktree remove` — `--force` only after that check. Never `rm -rf` /
  `Remove-Item -Recurse` a junction. The shell-guard now also denies
  `git worktree remove --force` for the builder.
- **Applies:** every worktree teardown on Windows, especially with linked environments.

### KP-012 — Gate-critical streams must reach a reviewer whole; never trim the diff to save tokens
- **Temptation:** saving tokens by truncating, slicing, or summarizing the diff, scanner
  output, or test results before a reviewer sees them.
- **Surfaced:** the Review B "no diff received → APPROVE-shaped reply" failure already
  recorded in the merge policy; the context-economy work made the boundary explicit.
- **Correction:** context economy — *slice, don't slurp* — applies **only** to high-volume,
  low-stakes material no verdict rests on (long logs, orientation reads of big files). The
  diff, scanner output, test results, and the Review B input file always reach the reviewer
  complete; trimming one is a gate-integrity flag. To keep verbose output out of the
  supervisor's context, use the existing summarizer subagents (`test-runner`,
  `diff-reviewer`) — faithful compression by a model told to preserve what matters — rather
  than a lossy compressor in front of a reviewer.
- **Applies:** every review; any future compression-tool trial.

### KP-013 — `cursor-agent` auto-update can trip Windows Smart App Control (field-reported)
- **Surfaced:** a supervisor running the loop for days — the CLI's self-update replaced the
  binary with one Smart App Control then blocked, breaking every delegation until the agent
  version was pinned. (Field report; not independently verified here.)
- **Correction:** pin `cursor-agent` to a known-good version and disable/skip its auto-update;
  record the pinned version in `PROJECT_STATUS.md`; adopt an agent bump only on a verified
  pass, never automatically — the same discipline as every other tool in the loop.
- **Applies:** every Windows host running the bridge.

### KP-014 — Hook-launched console programs pop visible terminal windows on Windows (field-reported, fixed in-project)
- **Surfaced:** a supervisor's project (2026-09-16): during headless runs, dozens of terminal
  windows flashed on the user's desktop and cascaded over their own work. Cause: the
  `afterFileEdit` hook scripts launched `ruff`, `prettier`, `taskkill`, and the Python
  launcher as ordinary console subprocesses. Cursor is a GUI process with no console, so
  Windows allocates each child a **new visible console**; capturing output does not prevent
  it. Hooks fire once per file edit, hence the count. The same project had already fixed the
  identical problem once, locally, in its video renderer — and never generalized it.
- **Correction:** windowless by default — `creationflags=CREATE_NO_WINDOW` (Python; `0` off
  Windows) / `windowsHide: true` (Node) at every launch site in hooks, agent tooling, and
  product code; direct-command hook entries wrapped in the bundled `run-hidden.py`; the
  bundled `windowless-check.py` in the pre-commit gate so the flag is enforced, not
  remembered. Exceptions only where the window serves the user, marked
  `windowless: visible-ok <reason>`. Signal caveat: a `CREATE_NEW_PROCESS_GROUP` spawn used
  for a `CTRL_BREAK` stop is hidden only after its stop path is tested.
- **Applies:** every Windows-hosted project; every hook script and every subprocess the
  builder writes. The meta-lesson is the report's own: a fix made once, locally, recurs in
  the next subsystem unless it is promoted to a rule — which is what the Issues file →
  `Known-Pitfalls.md` is for.

### KP-015 — Fixing from the symptom: a corrected brief without a diagnosed cause makes the builder guess
- **Temptation:** a test fails or a reviewer rejects; the supervisor writes "fix X" from the
  symptom and re-delegates. The builder, with no cause to repair, makes the symptom go away —
  a retry, a broader catch, a widened assertion — and the test goes green. The cause stays.
- **Surfaced:** the owner's observation (2026-09-19) that Claude Code "appears to be guessing"
  on bug fixes; the loop's only guard was "same defect twice → stop", which fires *after* the
  guessed round. Cursor's Debug Mode names the same failure and the cure — runtime evidence
  before a fix — but its mechanism (an IDE extension log server, a human reproducer) does not
  exist headless.
- **Correction:** the `root-cause-first` skill and standing rule 26 — reproduce
  deterministically first (a failing test / an observability test driving the exact state,
  under test-mode determinism), write ≥2 hypotheses each with a discriminating observation,
  instrument only to discriminate (`DEBUG-BUG-<nnn>` tags, never committed — dirty-tree rule +
  `secret-sentinel` block), capture the run to the artifacts dir, confirm one cause with
  evidence, then a `BUG-<nnn>` fix brief that names the cause and forbids suppression;
  `test-runner` labels diagnoses OBSERVED / INFERRED and INFERRED never grounds a fix.
  Proportionality: a failure that *is* its own cause (a named missing import, an omitted
  requirement) is fixed directly.
- **Applies:** every behaviour defect in the loop; every Claude Code session fixing a bug —
  the skill needs no bridge machinery.
