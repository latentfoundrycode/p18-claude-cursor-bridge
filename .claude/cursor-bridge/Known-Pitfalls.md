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
  fails an adapter tested only against a builder-written mock. Standing rule 37. Since
  2026.09.26 the builder's `Assumed, not verified` list (rule 42) also names such guesses at
  the end of the run, where a reviewer reading the code cannot see which facts were never
  checked.
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

### KP-028 — Waiting for a CI notification that never comes; the loop stalled after every green gate
- **Surfaced:** 2026-09-24 to 26, all three active projects (video factory, reAngle, documentation provider). After CI went green the supervisor sat idle until the owner prompted it — at least eight times ("It appears #160 merged but you paused your work", "The CI passed but you've come to a halt", "merge"). The Claude desktop app now tells Claude Code to register each PR with the app's CI monitor and not to watch CI itself; the monitor sends a `<ci-monitor-event>` only for a failed check or a review comment, never for a green gate. The supervisor armed GitHub's auto-merge, registered the PR, and ended its turn; GitHub merged, and nothing woke the supervisor. Until mid-September it had waited with a watch command whose completion woke it. The bridge's merge step said "watch the required check" without saying how, so the app's instruction filled the gap. Not a bridge regression and not a persisted chat state: the pattern crossed three projects and several context resets.
- **Correction:** the merge step names the mechanism — one background `gh pr checks <n> --watch --required --fail-fast` per PR, whose completion notification wakes the supervisor; the owner authorises it; the app's monitor is never the wake-up. While it runs, the supervisor keeps building what does not overlap. Rule 43 forbids ending a turn during the build unless a background task is pending or `Awaiting user on:` names an owner wait, and the `loop-guard` Stop hook enforces it (one nudge per stop, fail-open, bridge Workspaces only).
- **Applies:** every merge; every session run from the Claude desktop app.

### KP-029 — A specified screen shipped as a placeholder and the project was declared done
- **Surfaced:** SFVF, 2026-09-27. The requirements document lists five tabs "plus Settings" (API keys and connections, §8.7); the architecture names the settings page; the mockup has it. No build plan ever contained it; the shipped app showed a `PlaceholderView` reading "Arrives in a later stage"; keys could be entered only in a terminal; the project was marked done at 1.0.0, and the User Manual told the owner to add keys "in SFVF's settings". No deferral was recorded. The next change cycle repeated "the build is complete" without checking; the supervisor's own audit then also found the main screen's workflow card only partly built. The first run of the new check also found the documentation provider serving one of its ten declared admin functions as a 501 "not implemented yet" stub.
- **Cause:** nothing tied the requirements as a whole to "done". Every gate checked an increment against its own brief; project end fired on the last stage of a plan that had silently lost a requirement; a stand-in passed review because no brief asked for the real thing; and an inherited "done" was trusted.
- **Correction:** the requirements register (`docs/REQUIREMENTS.md`, one ID per requirement, mockup screens and states included), increments that name the IDs they satisfy, tests that carry the IDs, deferral only by the owner with a date, and `completion-check.py` — `--mode plan` at the plan gate and every stage close, `--mode done` before "Project complete" and first in every change cycle, failing on an unbuilt or untested requirement and on any stand-in text or placeholder component in shipped code. Supervisor rule 44.
- **Applies:** every project; every project end; every change cycle on a finished project.

### KP-030 — `settings.json` is shared with Claude Code; a personal setting is not a failed install
- **Surfaced:** reAngle, 2026-09-29. `/calibrate-bridge` stopped at step 1 because `bridge-check.py` reported `~/.claude/settings.json` STALE. The bridge's own content (the permission list and the Stop hook) had copied correctly; the one difference was a key Claude Code itself had written, `"switchModelsOnFlag": true`. The supervisor then recommended removing the key, telling the owner that `true` "isn't one of the documented values" — it had read the documentation of a different setting. `switchModelsOnFlag` is a documented Claude Code setting (`true` is its default; it decides whether a request flagged by a safety check switches model automatically or pauses to ask), and Claude Code writes several keys into this file on its own: `/fast`, `/effort`, `/advisor` (a "don't ask again" approval goes to the project's `.claude/settings.local.json`, not here). Removing them, or copying the release's file over the owner's as the setup guide instructs, discards the owner's own settings.
- **Cause:** the bridge treats a shared file as its own. It ships `settings.json` whole and the install check demands a byte-for-byte match, but the bridge owns only the `permissions.allow` entries it needs and its hook; every other key belongs to the owner and to Claude Code.
- **Correction (release 2026.10.04a):** `settings.json` is no longer fingerprinted. The bridge's part of it lives in `cursor-bridge/settings.bridge.json`; `bridge-install.py` merges those entries into the owner's file and keeps every other key, and `bridge-check.py` verifies only that the bridge's entries are present. An install is one command, never a copy of `settings.json`. And a vendor fact quoted to the owner (a setting's name, its values, its default) is read from that setting's own documentation page, not inferred from a neighbouring one (rule 42's "assumed, not verified" applies to the supervisor's own claims).
- **Applies:** every calibration; every install-check failure on `settings.json`; every explanation that cites Claude Code's or Cursor's documentation.

### KP-031 — A running server counted as a wake source; the loop stalled for seven hours
- **Surfaced:** reAngle, 2026-10-03. At 00:38 the supervisor started the project's development stack as a background command for a paid self-test, handled the failed redeploy that ended at 00:51, and ended its turn without a CI watch. The loop guard allowed the stop because its rule counted *any* background command started in the last six hours as a wake source, and the stack was one. CI then failed (a new `braces` advisory), nothing woke the supervisor, and it sat until the owner wrote at 08:00. A replay of the transcript against the guard shows two "pending" tasks at the stop: the dev stack and a git commit whose completion the guard had missed, because completion notices also arrive as queue records and queued-command attachments, which it did not read. The supervisor's own explanation, "CI did not notify me", named the symptom: the app's monitor never does (KP-028), and the thing that would have, the watch, was not running.
- **Cause:** a server never finishes, so a rule that treats every running background command as a wake source is satisfied forever by a server; and the guard's completion detection read only message text.
- **Correction:** `loop-guard.py` counts a background command as a wake source only if it is of a kind that finishes: the builder (`cursor-agent`), the CI watch (`gh pr checks … --watch`), or a command the supervisor marks with the comment `# wake` because it is waiting for it (a test suite, a benchmark); background agents still count; completion notices are read from queue records and attachments as well. Rule 43 says the same. The permanent fix is the watchdog of the restructuring plan (every background task gets a deadline, and the guard counts a task as pending only until it).
- **Applies:** every turn ended during the build; every background server, worker or probe the supervisor starts.

### KP-032 — The builder and the cross-family reviewer acted with the owner's GitHub identity
- **Surfaced:** the TDP, 2026-10-02 (found by the plan review of 2026-10-04). Review B, a model of another vendor launched through `cursor-agent`, posted its verdict as a comment on pull request #182 under the owner's GitHub account, the second time it had done so. Every `cursor-agent` process inherited the owner's `gh` login and git's stored credentials, so a builder or reviewer could comment, approve, push or merge as the owner; the merge policy's read-only guarantee, a `git status` check after the run, cannot see a post or a push. The reviewer was also launched with `-f`, which force-allows commands, where only the workspace-trust gate needed clearing.
- **Cause:** the agent ran as the owner's user with the owner's credential stores reachable, and no rule or check covered what it did outside the working tree.
- **Correction:** every `cursor-agent` process runs with the owner's identity withheld — `gh` sees an empty config folder, no token variable survives, git has no credential helper and never prompts — through the shim Claude Code's Bash tool runs (`cursor-agent.shim`, installed by `bridge-install.py`) and through `bridge-run.py`, which every delegation and review goes through. Review B keeps `--force` so it can run the tests and build reproductions (the owner's decision of 2026-10-04: a read-only mode was tried and found weaker), on a committed checkpoint that `review-guard.py` snapshots before the launch and verifies, restores and reports after it — tracked and untracked files put back; a commit, a moved HEAD, a new ref or stash, a changed `.git/config` or hook file, a changed `.env` reported as `GATE-INTEGRITY` (the 0b review showed that `git status` plus `git checkout -- .` saw none of these; its second pass showed the guard's own `git checkout` running a hook the reviewer had planted in `.githooks`, so every git command of the guard now runs with the repository's hooks and file monitor switched off, and the active hooks folder is hashed before any git command); a change to a record the project gitignores (`docs/`, `handoff/`, `run/review/`) is a flag too; and `premerge <nnn> <pr>` proving the merged head descends from the reviewed one and is the pull request's head, merged with `--match-head-commit`. The supervisor writes nothing to the checkout while the review runs. After every Review B and before every merge, `pr-activity-check.py` checks what was written to the pull request, and what the owner's account did in the repository, since the launch. The `permission-guard` hook refuses the override merge (`gh pr merge --admin`, or the REST merge) and every form of force-push in both shell tools and every permission mode; deny rules cover the usual spellings as a second layer; the repository's branch rules on GitHub refuse what neither can see. **Account keys (2026.10.04e):** release 2026.10.04c told projects to move paid keys out of `.env` "to the user's environment", and one supervisor wrote its run sheet that way. A variable in the Windows user environment is inherited by every program the owner starts, the builder and the cross-family reviewer included, and the launcher withheld only the GitHub variables: the keys would have moved from a file the builder can read into the environment the builder is handed. Now the launcher and the shim withhold every variable whose name looks like an account key (a token, a secret, a password, an API, access or private key; Cursor's own are kept), the conformance check advises a key file **outside the Workspace** and never the user environment, and it notes key-like variables it finds in the session's environment. Local service passwords the tests need stay in the project's `.env`, which the builder reads. **What this is and is not:** it stops an agent from doing these things by accident or by habit, which is what happened; it is not a sandbox. The agents run as the owner's Windows user, and a process that deliberately reaches for the credential store (a `-c credential.helper=…` on its own git call) can still get the login. A separate low-privilege account for the builder is the only real boundary, and belongs to the watchdog release.
- **Applies:** every delegation, every Review B, every resolution round, every merge.

### KP-033 — Background runs had no limit that could end them, and a top-level kill leaves orphans
- **Surfaced:** reAngle and the TDP, September to October 2026: an eleven-hour reconnect loop (ISS-002), a builder that had finished its edits while `cursor-agent` sat reconnecting (TDP ISS-005), an orphaned dev server that held the output pipe for six hours (reAngle ISS-008), a reviewer's `find /` for seven hours. The bridge set no limit on any background task; the only ceiling in force was Claude Code's own two-hour limit on background commands, present in the installed version by accident of release and gone again in the next. On Windows a plain timeout kills only the first process: its children live on and keep the pipe open, so the supervisor is never woken.
- **Correction:** `bridge-run.py` puts itself into a Windows Job Object before it starts the command, so every process the command creates is born inside the job; at the limit the job is terminated and the whole tree dies with it (exit 124; the pipe closes; the supervisor wakes), and at a normal end the job's closing kills any orphan the command left, such as a dev server. It accepts only the loop's own commands (`cursor-agent`, `gh pr checks`), so its allow rule cannot run anything else unseen. Builders run under 7,200 s, reviews under 1,800 s, CI watches under 3,600 s; its first stderr line is the launch time in UTC. On exit 124 the supervisor inspects the tree before discarding anything: finished work goes through the normal gate (ISS-005's lesson). A hit limit is recorded like a connection failure: retried twice, then escalated. The watchdog of the restructuring plan (release A2) replaces the fixed limits with learned durations and stall detection.
- **Applies:** every background command the loop starts.

### KP-034 — The roster check mistook a file path for a model, and a reset after a re-resolve undid the switch
- **Surfaced:** reAngle, 2026-09-29 (found by the plan review). A `--record-failure` call was given a file path instead of a model id; the path was treated as a model of the "other" pool, two such calls marked the pool exhausted, and the project ran on its backup pairing until the owner checked Cursor's dashboard five days later. Separately, step 3b re-resolved the roster and then reset the working tree to the checkpoint, which reverted the tracked roster files and put the exhausted model back; failure counts never reset, so two failures days apart counted as consecutive; and "rate limit" or the word "billing" counted as a usage limit, while a dropped connection counted against the model.
- **Correction:** the roster's changing state (the pool's exhaustion, the marks, the counts) lives in the repository's own `.git/bridge/roster-state.json`, which no reset, clean or checkout touches, never in the tracked roster; a roster from an older release seeds it once. `roster-check.py` refuses a `--record-failure` argument that is not a model of the roster (exit 2, nothing written); a connection error or a hit run limit is not the model's fault: retried twice within eight hours, then exit 5, stop and tell the owner; a failure count expires after eight hours, longer than any run limit, and `--record-success` clears it; an automatic "unavailable" mark expires after six hours; the usage-limit patterns no longer match a rate limit or a bare "billing"; an integer count from an older release is treated as expired. Step 3b resets the tree before it re-resolves, and the re-resolve rewrites `docs/ROSTER.resolved.json` after the reset. Tests cover each case, including record → reset → re-resolve in a git repository.
- **Applies:** every model failure during the loop; every automatic switch.

### KP-035 — A compaction keeps 13% of the supervisor's instructions, and the rules went missing for hours at a time
- **Surfaced:** found by the plan review of 2026-10-04 in the transcripts of all three projects. When a session's context is compacted, about once a day, Claude Code re-attaches an invoked command keeping only its first part: measured, exactly 20,000 of the supervisor's 150,000 characters, which ended in the design phase. The build loop, the merge gate, the escalation list and all standing rules were gone until the supervisor happened to re-read the file, days later in two projects. Rule-breaking followed within minutes of several compactions (a brief with inline task content, a loose worktree, Review B's input outside the workspace), and the supervisors' private memory notes filled the gap with stale or invented rules.
- **Cause:** the instructions were written as one long file read once at the start, with nothing that restored them when the context was replaced.
- **Correction:** the file opens with a **digest** of the core (the founding rules, the loop, the escalation list, the reporting rules, every standing rule in one line) that fits inside the part a compaction keeps, and the `session-start` hook re-injects that digest after every compaction, resume and fork, with the exact sections of the current phase to re-read before the next action. Claude Code caps a hook's output at 10,000 characters and swaps a longer one for a file path, so the hook is registered **twice** for the event, one run printing the pointers and one the digest, each under its own cap (the 0b review measured the single-run form being cut on all three projects, and the cut part was the pointers). The hook fails open: it prints for every session under the project and tells a session that is not the supervisor to ignore the message, and a forked session not to continue the loop — a gate on the transcript was tried and silenced two of three live supervisor sessions (one invoked through the Skill tool, one continuing an earlier transcript; the 0b review's second pass). Tests run the hook for every phase the status template allows on a status file at the template's limits. Private memory notes never hold a rule or project state (rule 41); `/calibrate-bridge` step 2b reviews them, and the conformance check lists them.
- **Applies:** every session, at every compaction and resume.

### KP-036 — Review A ran on a legacy model for a month, and Fable was taken for a second usage pool
- **Surfaced:** 2026-10-04, when the owner asked which models the agents use. Four reviewer definitions (`diff-reviewer`, `security-auditor`, `design-auditor`, `refactor-scout`) and the roster template's `review_a` had been pinned to `claude-opus-4-8` on 2026-09-05, when it was the current Opus; by October it was two generations behind (Opus 5, Opus 5.5) and still served, so nothing failed and nothing noticed: Review A judged every increment on a weaker model than the supervisor. Separately, the owner read the usage view's "Weekly · Fable" bar as a second pool and planned to move the supervisors to Fable to raise the ceiling.
- **Cause:** a model id is a release-time fact, and nothing re-checked the pins when newer models arrived. The usage view shows Fable's bar beside the weekly one without saying it is a share of it.
- **Correction:** verified on 2026-10-04: Fable models *draw from the plan's regular weekly usage limit*, may take at most half of it, and *use it faster* than other models (API price 2.5 times Opus 5.5 per token; the quota weighting is unpublished); the app's own usage reader labels the main bar "Weekly · all models". Moving volume work to Fable lowers the ceiling. Rule 48 therefore puts Fable where tokens are few and a mistake costs the most (the supervisor through Phase 4 and in design revisions, the plan critic), Opus 5.5 where the volume is (the supervisor from Phase 5, Review A and the auditors at high effort, the brief packager, the diagram specialist), and Sonnet 5.5 on the mechanical subagents; no definition inherits the session's model. The app refuses a session that changes its own model, so the switch is the owner's by hand and is announced in the report that closes the stage before it. Every bridge release re-checks every model id in the tree against Anthropic's models overview (legacy means replace), and a test refuses legacy ids in the agent definitions and the roster template.
- **Applies:** every release (the pins), every phase transition (the switch), every project (the allocation).
