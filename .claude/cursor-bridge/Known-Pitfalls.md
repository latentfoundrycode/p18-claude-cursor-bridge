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

### KP-016 — Loop artifacts written outside `Workspace/` break as soon as the boundary is installed
- **Surfaced:** Technical Documentation Provider, 2026-09-20 (ISS-003). Calibration installed
  the always-on workspace-boundary rule; the very next Review B hand-off failed because the
  reviewer's diff file had been written to a scratch folder outside the project, which the
  builder/reviewer now (correctly) refused to read.
- **Correction:** every artifact the loop writes lives inside `Workspace/` at a named path —
  `run/review/` for reviewer diffs and resolution-round files, `bench/` for results and
  profiles, the artifacts dir for debug captures. A calibration that installs the boundary
  relocates any existing scratch files first. Standing rule 36.
- **Applies:** every project; every calibration that adds the boundary.

### KP-017 — `git diff` from the working tree omits untracked new files, so a reviewer gets an incomplete diff
- **Surfaced:** the same project, twice in one stage: a new module, then a new test file,
  absent from the diff written for Review B because they had not been committed yet. The
  reviewer refused the incomplete diff — the gate held, but a round was lost each time.
- **Correction:** the reviewer's diff is generated only from committed state:
  `git status --porcelain` must be empty, then `git diff <merge-base>...HEAD`. Never a
  working-tree diff for a reviewer. (`scope-check.py` already counts untracked files; the
  reviewer diff must too.)
- **Applies:** every Review B invocation; any diff handed to a reviewer from a file.

### KP-018 — A dependency added to the manifest without its lockfile passes every reviewer and fails CI
- **Surfaced:** the same project, 2026-09-21 (ISS-004). `apscheduler` was added to
  `pyproject.toml`; plan-critic, four reviewers, and secret-sentinel all passed the diff —
  the sentinel even read "no lockfile churn" as a clean sign — and CI failed at test
  collection with `ModuleNotFoundError`, because CI installs from `requirements.lock`.
- **Correction:** reviewers read what is *in* a diff; the missing lockfile change was an
  absence nothing looked for. `lock-check.py` now fails a manifest change without its
  lockfile change, at the admission gate and in secret-sentinel, before any reviewer. The
  general lesson: for every "must also change" pair, add an *expected-file-missing* check;
  a reviewer cannot notice an absence.
- **Applies:** every dependency admission; every project with a lockfile CI installs from.

### KP-019 — "Approved in the plan" is not "fits the data"; and CI events can simply be late
- **Surfaced:** the same project, three times: a web-fallback feature in the approved plan
  had no valid target because the corpora were pinned local snapshots; a per-snapshot cost
  field had no home in the schema; a cost figure had no requirement behind it. Separately,
  a `gate` workflow run appeared ~5 minutes after the pull-request event and, read as
  dropped, prompted empty commits and close/reopen nudges that were not needed.
- **Correction:** spec-packager runs a **reality check** before every brief — the schema,
  configuration, data sources, and interfaces the increment assumes must exist as built;
  a mismatch comes back as a scope question, never as a brief. And for CI: poll for the
  run against the exact head SHA with a patient timeout (several minutes) before
  concluding an event was lost; never stack empty commits to force one.
- **Applies:** every brief; every wait on a CI run.

### KP-020 — A mock the builder wrote tests the builder's assumption, not the external service
- **Surfaced:** SFVF, Stage P (2026-09-20). Six provider adapters merged green — RED
  contract, decorrelated review, CI — against mocked responses. Every one failed on its
  first real call. The mocks encoded each adapter author's assumption about hosts, required
  fields, and next-step URLs; a wrong assumption produced a self-consistent green test.
- **Correction:** for any external service, the first increment is a **contract capture**:
  an attended live call (owner's key; the usual once-per-service escalation) whose real
  responses are recorded as fixtures with secrets scrubbed; adapter tests replay them, and
  "done" means passing against recorded real responses or a live smoke. The brief forbids
  invented mocks; plan-critic blocks an integration plan without a capture; diff-reviewer
  fails an adapter tested only against a builder-written mock. Standing rule 37.
- **Applies:** every project integrating a third-party API, SDK, or provider.

### KP-021 — A status-gated error scrub hides real errors; redact by pattern instead
- **Surfaced:** SFVF, Stage P. A hardening change blanked error bodies on 401/403 to stop a
  reflected API key leaking — correct aim — and thereby blanked a legitimate Google 403
  body during live diagnosis, forcing a separate raw diagnostic.
- **Correction:** redact credential *patterns* from all error output; never blank a whole
  body on a status code. Both security and diagnosability survive. Added to
  `secure-coding.snapshot.md` (V15) and to `security-auditor`'s review.
- **Applies:** every error-handling or logging hardening.

### KP-022 — The builder silently ran on a reviewer's model family; nothing enforced the roster
- **Surfaced:** SFVF, Stage P. The delegated builder had been run as an OpenAI-family model —
  the same family as Review B — for several increments, collapsing the decorrelation the
  merge gate depends on. Caught only when calibration re-read the merge policy.
- **Correction:** `docs/ROSTER.json` names the three models; `roster-check.py` fails a shared
  or unknown family and a delegate command without `--model <builder>`; it runs at
  configuration, at every calibration, and at every checkpoint. Standing rule 38.
- **Applies:** every project; every time a model is changed.

### KP-023 — A worktree with a real, briefly locked environment fails teardown; it is not the junction hazard
- **Surfaced:** SFVF, Stage P, on every increment that built a real `.venv` inside its
  worktree: `git worktree remove` hit `Permission denied` (antivirus or a lingering handle),
  leaving an orphaned directory that a later delete removed cleanly.
- **Correction:** distinguish the two cases. A linked environment → the junction primitive
  (KP-011). A real, locked environment → wait and retry, else defer the delete to the next
  checkpoint; `--force` unlocks nothing and is still forbidden without a link check.
  `Cursor-Project-Configuration.md` §1.
- **Applies:** every Windows worktree teardown with a real environment inside.

### KP-024 — Quota exhaustion cannot be probed; it is detected from the error and reversed by the calendar
- **Surfaced:** 2026-09-25. The owner's Cursor "other models" usage (every third-party
  model: OpenAI, Google, Anthropic, …) stood at 99% used — unusable for a build — yet a one-word
  probe to GPT-5.6 Sol still answered. A call succeeds at 1% remaining exactly as at 90%,
  so no probe can see exhaustion coming; only the dashboard can.
- **Correction:** `docs/ROSTER.json` carries an `other_pool` field. It flips to exhausted
  **automatically** when a call returns a usage-limit message or a model fails twice in a
  row (`roster-check.py --record-failure`; the loop re-resolves and restarts the
  interrupted step from its checkpoint — the owner may be asleep), or pre-emptively when
  the owner says "usage exhausted". `roster-check.py` then falls to the **native** profile
  (builder Composer 2.5, Review B Grok 4.7 — roles swapped so the stronger
  native reasoner reviews). The return is a **calendar fact**: the roster's `reset_day` (UTC) after the
  exhaustion stamp restores the pool automatically; a probe is never used for it, because
  a probe cannot tell a reset from 1% remaining and would oscillate. The exact usage-limit text
  Cursor prints was unknown when the classifier was written; every auto-switch records the
  stderr excerpt in the Issues file so the patterns can be sharpened. Standing rule 38.
- **Addendum (2026-09-25):** the first roster template put Grok 4.6 in the native profile
  and classed `grok-4.7-*` as metered — inferred from the id's shape, without reading
  Cursor's documentation, which the maintainer could have fetched in one call. The docs say
  Grok 4.7 is in the Cursor Models pool. Vendor facts (pools, limits, reset rules) are read
  from the vendor's page at the time of the decision, never inferred from naming — the same
  verify-first rule the bridge imposes on the loop (KP-008).
- **Applies:** every project; every time a usage limit is reached or reset.
### KP-025 — A worktree per increment is habit, not need; loose worktrees pile up in the project root
- **Surfaced:** SFVF, project end. The supervisor created a worktree for essentially every
  increment as a loose `wt-<thing>` sibling of `Workspace/`; the work was sequential, so none
  was needed, and four were left behind, three of them empty. The bridge itself had nudged
  it: the loop said "commit to the worktree branch", vocabulary inherited from Cursor's
  parallel-agents feature, where every agent gets a worktree.
- **Correction:** sequential increments are branches in the single checkout. A worktree only
  while two branches must be live at once; then under `<project-root>/Worktrees/<name>`,
  recorded in `PROJECT_STATUS.md`, removed at merge (KP-011 / KP-023 for the teardown) and
  checked at every reflection point. Never nested inside `Workspace/`: jscpd, test discovery
  and `scope-check.py` walk into it. Supervisor rule 39 and "The project layout".
- **Applies:** every project, every time the word worktree comes to mind.

### KP-026 — A finished project's local copy lagged the remote; nothing brought local `main` along
- **Surfaced:** an earlier project concluded with the latest version on the remote and the local repository behind it. The supervisor merges with a squash merge on GitHub, which completes on the remote; nothing in the loop then fast-forwarded local `main`, so after the last merge the local copy was behind by design — and a new branch cut from it would have started from stale code.
- **Correction:** `sync-check.py` (deterministic: IN SYNC / BEHIND / AHEAD / DIVERGED / NO REMOTE / OFFLINE / UNPUBLISHED) at every start and resume, after every merge (`git switch main` + `--apply` fast-forwards), before every new branch (cut from `origin/main`, never local `main`), at every reflection point, and `--strict` at project end, where only IN SYNC or NO REMOTE allows "Project complete". Stranded commits on protected `main` are rescued to a branch, never deleted. Supervisor rule 40.
- **Applies:** every project with a remote; every merge.

### KP-027 — The status file grew into a log; the supervisor forgot what the software already had
- **Surfaced:** across completed projects, 2026-09. The video factory's supervisor had the owner create a second OpenRouter key when one existed; the documentation provider's supervisor proposed demoting the local corpus, reversing a decision taken early for a good reason. Both status files had become append-only logs (1,390 and 566 lines; 158,000 and 58,000 characters), one of them declaring its own plan stale and pointing at the supervisor's private memory for the real state. A resuming session reads such a file in slices (rule 20) and misses the fact it needed; design decisions were scattered over several files and a "do not relitigate" section buried in the log.
- **Correction:** two bounded files, read whole: `PROJECT_STATUS.md` (current position, rewritten, capped) and `docs/INVENTORY.md` (Features, Resources, Decisions, Deferred — current state, edited in place, updated with each `CHANGES.md` entry). Look it up before asking or proposing. `inventory-check.py` at every reflection point: status cap, absorbed change-log entries, every environment variable and CI secret named in Resources, no secret values. A code graph would not have prevented either failure: the facts were not in the code. Supervisor rule 41.
- **Applies:** every project, from the design gate on; every resume; every change request.
