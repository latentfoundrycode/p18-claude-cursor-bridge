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
  and carries no content. Corrections and re-delegations go into the brief file (a new numbered brief,
  `handoff/<ID>-r<N>.md`, never a revision in place, which the launcher refuses after a completed run); never into the prompt.
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
- **Correction (restated for release A1b):** `git worktree remove` is never run by hand, forced
  or not — Git for Windows follows a gitignored junction in an ordinary removal as well
  (verified 2026-10-06 on Git 2.53). `worktree-teardown.py` removes a worktree: it refuses
  while any link is inside, listing each with its target; the link is then removed by itself
  (`cmd /c rmdir` on the link from PowerShell; never `rm -rf` / `Remove-Item -Recurse`), the
  target verified intact with `Test-Path`, and the program run again. The `permission-guard`
  hook refuses the git command; the shell-guard denies the forced form for the builder.
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
  record the pinned version in `docs/INVENTORY.md` (Resources); adopt an agent bump only on a verified
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
  checkpoint; `--force` unlocks nothing, and `git worktree remove` is never run by hand at all (KP-011, release A1b).
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
- **Correction:** `loop-guard.py` counts a background command as a wake source only if it is of a kind that finishes: the builder (`cursor-agent`), the CI watch (`gh pr checks … --watch`), or a command the supervisor marks with the comment `# wake` because it is waiting for it (a test suite, a benchmark); background agents still count; completion notices are read from queue records and attachments as well. Rule 43 says the same. Since release A2 the guard reads the background tasks and scheduled wake-ups Claude Code hands it, counts a launched command only until its limit and a background agent only until its ceiling, and falls back to the session record only when that list is absent.
- **Applies:** every turn ended during the build; every background server, worker or probe the supervisor starts.

### KP-032 — The builder and the cross-family reviewer acted with the owner's GitHub identity
- **Surfaced:** the TDP, 2026-10-02 (found by the plan review of 2026-10-04). Review B, a model of another vendor launched through `cursor-agent`, posted its verdict as a comment on pull request #182 under the owner's GitHub account, the second time it had done so. Every `cursor-agent` process inherited the owner's `gh` login and git's stored credentials, so a builder or reviewer could comment, approve, push or merge as the owner; the merge policy's read-only guarantee, a `git status` check after the run, cannot see a post or a push. The reviewer was also launched with `-f`, which force-allows commands, where only the workspace-trust gate needed clearing.
- **Cause:** the agent ran as the owner's user with the owner's credential stores reachable, and no rule or check covered what it did outside the working tree.
- **Correction:** every `cursor-agent` process runs with the owner's identity withheld — `gh` sees an empty config folder, no token variable survives, git has no credential helper and never prompts — through the shim Claude Code's Bash tool runs (`cursor-agent.shim`, installed by `bridge-install.py`) and through `bridge-run.py`, which every delegation and review goes through. Review B keeps `--force` so it can run the tests and build reproductions (the owner's decision of 2026-10-04: a read-only mode was tried and found weaker), on a committed checkpoint that `review-guard.py` snapshots before the launch and verifies, restores and reports after it — tracked and untracked files put back; a commit, a moved HEAD, a new ref or stash, a changed `.git/config` or hook file, a changed `.env` reported as `GATE-INTEGRITY` (the 0b review showed that `git status` plus `git checkout -- .` saw none of these; its second pass showed the guard's own `git checkout` running a hook the reviewer had planted in `.githooks`, so every git command of the guard now runs with the repository's hooks and file monitor switched off, and the active hooks folder is hashed before any git command); a change to a record the project gitignores (`docs/`, `handoff/`, `run/review/`) is a flag too; and `premerge <nnn> <pr>` proving the merged head descends from the reviewed one and is the pull request's head, merged with `--match-head-commit`. The supervisor writes nothing to the checkout while the review runs. After every Review B and before every merge, `pr-activity-check.py` checks what was written to the pull request, and what the owner's account did in the repository, since the launch. The `permission-guard` hook refuses the override merge (`gh pr merge --admin`, or the REST merge) and every form of force-push in both shell tools and every permission mode; deny rules cover the usual spellings as a second layer; the repository's branch rules on GitHub refuse what neither can see. **Account keys (2026.10.04e):** release 2026.10.04c told projects to move paid keys out of `.env` "to the user's environment", and one supervisor wrote its run sheet that way. A variable in the Windows user environment is inherited by every program the owner starts, the builder and the cross-family reviewer included, and the launcher withheld only the GitHub variables: the keys would have moved from a file the builder can read into the environment the builder is handed. Now the launcher and the shim withhold every variable whose name looks like an account key (a token, a secret, a password, an API, access or private key; Cursor's own are kept), the conformance check advises a key file **outside the Workspace** and never the user environment, and it notes key-like variables it finds in the session's environment. Local service passwords the tests need stay in the project's `.env`, which the builder reads. **The general rule (the owner, 2026-10-05):** no secret reaches a product through an environment variable the owner sets, and no run sheet asks for one; a store's unlock passphrase is a secret like any key. Founding rule N2's own text had named "the owner's environment" as a home for keys, which is where the run sheets came from; it now names a key file outside the Workspace, the product's encrypted store, or the system's credential store, and the conformance check reports an inventory row that says otherwise. **What this is and is not:** it stops an agent from doing these things by accident or by habit, which is what happened; it is not a sandbox. The agents run as the owner's Windows user, and a process that deliberately reaches for the credential store (a `-c credential.helper=…` on its own git call) can still get the login. A separate low-privilege account for the builder is the only real boundary, and belongs to the watchdog release.
- **Applies:** every delegation, every Review B, every resolution round, every merge.

### KP-033 — Background runs had no limit that could end them, and a top-level kill leaves orphans
- **Surfaced:** reAngle and the TDP, September to October 2026: an eleven-hour reconnect loop (ISS-002), a builder that had finished its edits while `cursor-agent` sat reconnecting (TDP ISS-005), an orphaned dev server that held the output pipe for six hours (reAngle ISS-008), a reviewer's `find /` for seven hours. The bridge set no limit on any background task; the only ceiling in force was Claude Code's own two-hour limit on background commands, present in the installed version by accident of release and gone again in the next. On Windows a plain timeout kills only the first process: its children live on and keep the pipe open, so the supervisor is never woken.
- **Correction:** `bridge-run.py` puts itself into a Windows Job Object before it starts the command, so every process the command creates is born inside the job; at the limit the job is terminated and the whole tree dies with it (exit 124; the pipe closes; the supervisor wakes), and at a normal end the job's closing kills any orphan the command left, such as a dev server. It accepts only the loop's own commands by name (`cursor-agent`, `gh pr checks`, and since release A2 the test suites the supervisor awaits, without options that would run another program), so its allow rule cannot run anything else unseen; a benchmark or an unknown runner runs directly in the background with `# wake`. Builders start under 7,200 s, reviews and CI watches under 3,600 s; since release A2 the launcher learns a kind's ceiling from the project's healthy runs (`run/launcher/runs.jsonl`, `--limit auto`: one and a half times the longest healthy run, never below the default and never above twice it without the owner's words), and its first stderr line is the launch time in UTC, which is also the run's id. On exit 124 the supervisor inspects the tree before discarding anything: finished work goes through the normal gate (ISS-005's lesson). A hit limit is recorded like a connection failure: retried twice, then escalated. Release A2 added the learned ceilings and the run log, the test suites by name and the key file, the bound on background agents (an hour, a wake-up scheduled at the ceiling, `TaskStop` and a foreground re-run) and the loop guard's reading of Claude Code's own task list; no stall detection, because silence is not a stall and activity is not progress (plan 10.2).
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

### KP-037 — The bridge's own repository was a Claude Code project configuration, and a release could not be taken back
- **Surfaced:** the plan review of 2026-10-04 (R8) and its second pass (P1). The repository kept the governance tree at `Workspace/.claude/`, where Claude Code looks for a project's own agents, commands, settings and hooks. A project's agents take priority over the installed ones and are reloaded while a session runs, and a project's settings merge into the session. A session working on the bridge there ran the branch's half-edited reviewers and hooks: a branch that edited `diff-reviewer.md` changed the reviewer of that same branch. Separately, nothing described how to return to a previous release, and the plan's "install on one trial project" overlooked that the bridge is installed once per computer, so an install and a rollback each reach every project at once.
- **Cause:** the staging layout mirrored the installed one for convenience ("copy `.claude/` over `~/.claude/`"), which stopped being how the bridge is installed when `bridge-install.py` arrived, and nobody had asked what Claude Code does with that folder.
- **Correction:** the sources live in `bridge/`, which Claude Code does not read; `bridge-install.py` copies them into `~/.claude`. It keeps the previous release under `cursor-bridge-previous/<version>/` and puts it back with `--rollback`, together with that release's own settings entries and shim, leaving the owner's settings alone; changelog entries state what a project restores **if rolled back**, and `/calibrate-bridge` applies it. A release with new mechanisms is tried by time, not by place: the projects are paused before the install, one is calibrated and resumed, and the others resume on the owner's word.
- **Applies:** every bridge release; any session opened in the bridge's repository.

### KP-038 — cursor-agent imports Claude Code's hooks from `~/.claude/settings.json` and, under Git Bash, denies every tool call with them
- **Surfaced:** reAngle, 2026-10-05 and 06 (ISS-013), in the first increment under release 2026.10.05a: the builder delivered thirteen files it had never run, and its note said every Shell call was rejected; a supervisor probe reproduced `Rejected: Hook blocked with message: --: eval: line 1: syntax error near unexpected token '&'` on a PowerShell pipeline wrapped around `python "$HOME/.claude/cursor-bridge/permission-guard.py"`. Every builder run and every Review B on that computer since the permission guard was registered (2026-10-04, bridge 2026.10.04b) was affected, while the CLI exited 0 and reported success. CI still gated every merge, so nothing unchecked reached a `main`; the reviews of that time ran without execution.
- **Cause (vendor-confirmed):** Cursor imports third-party configuration by default: the hooks of `~/.claude/settings.json`, `.claude/settings.json` and `.claude/settings.local.json` (and the `enabledPlugins` of those files), with `PreToolUse` mapped to its own `preToolUse`, and the CLI has no switch to turn that off (the only switch is a setting of the editor; Cursor's staff: "no key in cli-config.json, no flag, and no env var"). On Windows with `MSYSTEM` set (Git Bash, which the Bash tool and the shim use), cursor-agent composes the imported hook as PowerShell and evaluates it with bash; bash's syntax error exits 2, which Cursor reads as "deny". Sources: Cursor's reference on third-party hooks and its hooks reference; Cursor forum threads 168129 and 166558, acknowledged by Cursor's staff, with the home-folder workaround as the interim fix. Once Cursor runs such a hook correctly, the imported guard itself would be harmless (an empty answer with exit 0 blocks only a hook marked fail-closed, which imported hooks are not); the import stays harmful all the same, because it also brings the supervisor's `Stop` and `SessionStart` hooks into the builder, and because Cursor loads `~/.claude/skills` and `~/.claude/agents` from the same home.
- **Correction (2026.10.06a):** every builder and reviewer run gets a home folder of its own, `%USERPROFILE%\.cursor-bridge\agent-home\`, holding one link `.cursor` to the owner's real `~/.cursor` (the CLI's account and state) and nothing else: no `.claude` to import from, and the owner's stores under the profile root (`.ssh`, `.aws`, `.docker` and the like) are no longer found by default; a store a tool reaches through `APPDATA` or `LOCALAPPDATA` still is, since the shim and `stripped_env` leave those two variables naming the owner's real folders until a probed release redirects them into the skeleton below (a program item for the maintainer: the shim and cursor-agent themselves live under `LOCALAPPDATA`, KP-008; `gh` is hidden by `GH_CONFIG_DIR` regardless; corrected 2026-11-01, release T's diagram retrofit having drawn the difference, D-004) (not out of reach: the run is the owner's account; the real controls stay the withheld tokens, the empty `gh` folder and git without a credential helper, KP-032). git keeps the owner's global configuration through `GIT_CONFIG_GLOBAL`; the caches the builders' tools read by default are passed through by their own variables (`HF_HUB_CACHE`, `TORCH_HOME`, `PUPPETEER_CACHE_DIR`, never `HF_HOME` or `XDG_CACHE_HOME`, which would show the owner's token file again). The shim and `bridge_env.stripped_env` apply one rule alike: the link exists, is a link and leads to the real `~/.cursor`, or the run is refused (exit 125) rather than started into silent denial; `bridge-install.py` prepares the folder and repairs a link that leads nowhere or elsewhere (by removing the link itself, never through it; a plain folder in its place is never removed); `bridge-check.py` verifies the link. The guard hook refuses the agent started around the shim (`agent`, `cursor-agent.cmd` and their kin), which would run it with the owner's real home. The folder sits in the profile root on purpose: on the owner's computer a rename into such a link placed under `AppData\Local\<folder>` (not `Temp`, not `Programs`) fails with "path not found", and cursor-agent writes its state by a rename; the same link in the profile root works. The cause was not found (not the ACL); the installer and the check run a write-and-rename through a scratch link beside the agent home each time, so the bridge learns of a change before a builder does. Since 2026.10.06b the folder also holds the empty skeleton of a profile (`AppData\Local`, `AppData\LocalLow`, `AppData\Roaming`, `Documents`, `Desktop`, `Downloads`): Windows resolves its known folders from `%USERPROFILE%`, and a program handed a folder that does not exist falls back to the current directory, so a builder's PowerShell had written its cache folder into reAngle's Workspace.
- **Applies:** every run of cursor-agent on Windows; any Claude Code hook the owner adds to `~/.claude/settings.json`; a project's own `.claude/settings*.json` with hooks or plugins, which the relocation does not cover and the conformance check reports. The sign: a builder note saying its commands "were not run", or `Hook blocked` in a reviewer's output, while the CLI reported success.

### KP-039 — A wake-up scheduled from a UTC stamp with an assumed offset fires an hour past the agent's ceiling
- **Surfaced:** reAngle, 2026-10-10, under release 2026.10.10a: the supervisor computed every `CronCreate` time of a session from the hook's UTC timestamps with an offset it assumed (UTC+4) instead of the computer's (UTC+2), so each wake-up was set an hour after the agent's ceiling; the loop guard's refusal showed the agent as unscheduled and the supervisor found the cause itself.
- **Cause:** Claude Code reads a session cron on the computer's clock, in its local time, while the hook input carries task starts as UTC stamps or epoch values; a supervisor that adds the ceiling to a UTC stamp and converts by an offset it believes in has no check against the clock, and a wrong belief shifts every wake-up of the session by the same amount.
- **Correction (2026.10.10c):** the loop guard's refusal prints the computer's clock reading with its offset, the ceiling's time on that clock, the one-shot schedule expression to copy, and any scheduled wake-up that is due after the ceiling; rule 43 says the schedule is read on the computer's clock, copied from the refusal or computed from `date` read at that moment, never converted from a UTC stamp by an assumed offset.
- **Applies:** every `CronCreate` a supervisor still schedules for an idle wait (a checkpoint on a quiet session); an agent's ceiling is a wake-timer since 2026.10.11a (KP-043); any arithmetic on the hook's timestamps. The sign: the guard refusing a stop although a wake-up is listed, or a wake-up firing long after the agent ended.

### KP-040 — The Stop hook's live input differs from its documented shape
- **Surfaced:** reAngle, 2026-10-10, the first day on release 2026.10.10a: the loop guard refused every stop while the supervisor waited, because a task's start arrived as epoch milliseconds (read as "now"), a one-shot wake-up carried its schedule only (no next time), and the launched builder came under a type other than `command` (read as an agent).
- **Cause:** the guard read the hook's input in the one shape the documentation showed; the app hands it in several.
- **Correction (2026.10.10b):** the guard reads a start as ISO or epoch, a wake-up by its next time or its cron expression, a launched command under any type name; it records its input under `run/supervisor/loop-guard-input.json` so the next such difference has evidence.
- **Applies:** every program that reads a hook's input. The sign: a refusal whose reason contradicts what the session can see (a builder "started 0s ago", a scheduled wake-up "not seen").

### KP-041 — Writing the In-flight line during a review is GATE-INTEGRITY
- **Surfaced:** reAngle, 2026-10-10: rule 43 said to write the waited-on agent on the status file's In-flight line, while a Review B ran on a snapshot of the tree; the write changed the reviewed tree, which `review-guard.py verify` reports.
- **Cause:** two rules met on one file.
- **Correction (2026.10.10b):** while a review runs on a snapshot, the line goes to `run/supervisor/in-flight.md` and is copied to the status file after `verify`.
- **Applies:** any write the supervisor makes while a snapshot is under review; `run/` is the one place for it.

### KP-042 — A test-writing subagent left polling loops behind, which the guard counted as the supervisor's agents
- **Surfaced:** reAngle, 2026-10-10 (pull request 86): four `until grep -q ^exit <task output>; do sleep 15; done` loops, left by a subagent polling task-output files that no longer existed, ran on; the loop guard (under 2026.10.10a's defects) listed them among the supervisor's agents.
- **Cause:** a subagent waited on its own background commands with a shell loop instead of the app's notification, and nothing ended the loops when their files vanished.
- **Correction (2026.10.11a):** the loop guard never counts a polling loop and names it in its refusal for `TaskStop`; the subagent definitions forbid leaving a waiter behind.
- **Applies:** every subagent that runs commands; the sign: a background shell task whose command is `until` or `while` with `sleep`.

### KP-043 — A scheduled wake-up does not fire while a background agent runs, so it cannot bound the agent it was set for
- **Surfaced:** reAngle, 2026-10-10/11 (ISS-021): the one-shot wake-up `58 23 10 10 *`, set at 23:00 for a background subagent's one-hour ceiling, was still listed unfired at 00:41; the owner noticed the agent running for an hour and forty minutes.
- **Cause (proven in the maintainer's session on 2026-10-11):** a session-scoped scheduled prompt fires only while the session is idle, and a session waiting on a background subagent is not idle for the scheduler. A one-shot set for 09:51 beside a background agent that ended at 09:52:59 did not fire; it fired at 09:53:34, thirty seconds after the session went idle with nothing in the background. The documentation says a missed fire runs "once when Claude becomes idle" and is silent on background agents.
- **Correction (2026.10.11a):** the bound of a waited-on background agent is a background command, `wake-timer.py <seconds> "<the agent>"`, whose completion notification does wake the session (a background command's completion arrived in the same experiment); the loop guard counts an agent as bounded only while a timer ending no later than its ceiling runs, and its refusal prints the timer command to copy. A scheduled wake-up stays right for an idle wait with nothing in the background (a checkpoint on a quiet session).
- **Applies:** every wait on a background subagent; any design that relies on a cron firing while background work runs. The sign: a one-shot still listed after its minute while an agent runs.

### KP-044 — A global tool older than the project's own, and a pre-commit check weaker than CI, let a stage's worth of drift through
- **Surfaced:** the TDP (memory `ci-config-gotchas`, items 1 and 2, 2026-09) and the video factory (Issue 14, 2026-09-26): a global `ruff` was an older version with laxer defaults than the project's `.venv` copy and missed three rule classes; CI ran the formatter check as a separate step that the local pre-commit hook omitted, so four files' layout drift passed every local commit and was caught by the cross-family reviewer at the stage's end.
- **Cause:** a tool resolved from `PATH` instead of the project's own environment, and a local gate that enforced less than CI.
- **Correction:** the project's own toolchain is authoritative (`.venv/Scripts/python.exe -m ruff`, never a bare `ruff`); `cursor-configurator` writes the pre-commit hook with the formatter's check beside the lint command where CI runs one (release A5; the projects configured before it add the line at their next configuration change); the inventory records the tool versions by the file that pins them.
- **Applies:** every project with a linter or formatter in CI. The sign: a reviewer or CI flagging formatting that local commits passed.

### KP-045 — CI is Linux, the workstation is Windows: default paths, platform stubs, the Python floor and the developer's `.env` differ
- **Surfaced:** the TDP (gotchas 3, 11, 12, 18: `subprocess.CREATE_NO_WINDOW` not narrowed by mypy on Linux; `msvcrt` stubs passing locally and failing CI; `os.path.isjunction` of Python 3.12 crashing the 3.11 CI; a "default runtime folder" test patching only `LOCALAPPDATA`) and reAngle (ISS-018, BUG-019: a test that let the CLI read the developer's `.env` passed on Windows, in WSL and in five review rounds, and failed on CI, which has no `.env`).
- **Cause:** every local check ran on the platform that wrote the code; nothing ran the increment the way CI runs it.
- **Correction:** before every push, the increment's new tests run once under Linux from a folder with no `.env` (reAngle's `run/tools/wsl_pgtest_noenv.sh`), and mypy runs with `--platform linux` where Windows-only code is touched; Windows-only attributes are read with `getattr(..., 0)` and bodies guarded by `sys.platform`; the Python floor CI uses is the floor the code is written to (`type(Path())`, not `pathlib.Path`, for a subclass).
- **Applies:** every Windows-developed project with Linux CI. The sign: a failure on CI only, after every review approved.

### KP-046 — One setting read on both sides of the WSL boundary named the other side's path
- **Surfaced:** reAngle, 2026-10-03 (ISS-010, BUG-016): the API on Windows read the shared budget folder from the setting that names it in its WSL form (`/mnt/c/...`), a folder that does not exist on Windows, and reported the spend record unreadable while the CLI read the same file; the tests had supplied a real temporary folder through the same setting, so the platform difference never showed.
- **Cause:** a path setting shared between the Windows and the WSL side without a per-side resolution.
- **Correction:** every setting read on both sides of a WSL, container or host boundary gets a per-side resolution function at design time (`%LOCALAPPDATA%\...` on Windows, `/mnt/c/...` in WSL), and a test on each side with the other side's form.
- **Applies:** Windows-and-WSL hybrids, container-and-host hybrids. The sign: a path setting whose value starts with `/mnt/` read by Windows code, or with a drive letter read by Linux code.

### KP-047 — A file another process polls was published half-written
- **Surfaced:** reAngle, 2026-09 (ISS-005, BUG-004): a stage process wrote its result file with `Path.write_text`, which truncates first and fills afterwards; the batch runner polled the folder meanwhile, read an empty file and recorded a contract error for a job that had succeeded; it failed once in a few hundred runs, on Linux under load only, and passed on every rerun.
- **Cause:** a writer and a poller sharing a path without an atomic publication.
- **Correction:** a file another process reads while it may be written is published atomically: written to a temporary file in the same folder, then moved into place with `os.replace`; "a writer and a poller share a path" is a design-time checklist item; a flaky test on CI only is examined for a race before it is rerun.
- **Applies:** every result file, lock file, status file or queue entry read by another process. The sign: an empty or truncated file read exactly once in many runs.

### KP-048 — A web framework writes instruction files into the repository, and a build empties a tracked folder
- **Surfaced:** reAngle (Feedback, 2026-10): Next.js 16 generates `frontend/AGENTS.md` and `frontend/CLAUDE.md` on `next dev` and `next build`, which reappear in the working tree after every build as untracked changes and would steer an agent that reads them; the video factory (Issue 12): the web build emptied `app/web/`, deleting the tracked `.gitkeep` that keeps the folder present, and the deletion was flagged by the reviewers after the scope check had missed it as a build side effect.
- **Cause:** build tools that write into the repository outside the build output folder.
- **Correction:** generated instruction files are listed in `.gitignore` and `.cursorignore` and never read as the project's rules (the project's rules are its own `.cursor/rules/` and the bridge's); a build that touches a tracked folder is a review checkpoint, and a tracked placeholder the build deleted shows in `git status` and is restored before any commit (the video factory restores it after every web build).
- **Applies:** Next.js 16 and later, any framework with agent-file generation, any build into a tracked folder. The sign: `AGENTS.md`, `CLAUDE.md` or a deleted `.gitkeep` in `git status` after a build.

### KP-049 — A container image pinned by name and tag stopped being pullable
- **Surfaced:** reAngle, 2026-09-25 (ISS-001): `docker compose up` aborted on `pull access denied` for the object store's image, pinned by name and release tag; the repository had left the public registry, the alternatives had been retired or needed a login, and the failure interrupted the other pulls of the same compose run.
- **Cause:** a pin by name and tag is a promise the registry can withdraw; nothing in the project held the image.
- **Correction (reAngle's):** the image is pinned by digest and a fallback registry is named in the compose file; the inventory records the image and its digest. The correction still to make where a project can afford it: a mirror the project holds (a registry the owner controls, or an exported archive), so a withdrawn image does not stop a stage.
- **Applies:** every container image a project depends on. The sign: a compose or CI step failing on `pull access denied` or `not found` for an image nobody changed.

### KP-050 — A vulnerability newly published against a pinned lock entry failed every pull request at once
- **Surfaced:** the TDP, 2026-09-29 and 2026-10-01 (DEP-001, DEP-002; gotcha 16): OSV-Scanner failed every open pull request after an advisory was published for a pinned dependency none of them touched; the supervisor had to invent the procedure.
- **Cause:** the scanner reads the lockfile, so a new advisory blocks every branch regardless of its diff.
- **Correction:** the merge policy's procedure (release A5): a separate `DEP-<nnn>` increment off `main` bumps the pin, writes the change-log entry and passes the sentinel, both reviews and CI; it merges first, then `main` is merged into each blocked branch; nothing in a blocked branch is edited to pass.
- **Applies:** every project with a lock-reading scanner in CI. The sign: several pull requests failing the scanner on the same advisory on the same day.

### KP-051 — A CI watch started right after a push reported the previous commit's finished run
- **Surfaced:** the TDP, 2026-09-30 (TASK-117-r2; gotcha 14): the watch ended green on the run of the commit before the push, since the new run had not started when the watch began.
- **Cause:** the watch takes the newest run it sees, not the run of the pushed head.
- **Correction:** when a watch ends, the green run's head is confirmed to equal the pushed head (`gh pr view <n> --json statusCheckRollup,headRefOid`) before the merge; `premerge` checks the pull request's head as well; the maintainer's own rule is the same (a release is handed over only after its checks ran green on the pushed head, 2026-10-11).
- **Applies:** every CI watch. The sign: a watch that ends within seconds of the push.

### KP-052 — An escape typed in a here-document arrived as the real character
- **Mistake:** a backslash escape typed into a file, through a shell or a writing tool, taken to arrive as typed.
- **Surfaced:** the TDP, 2026-09-29 (gotcha 10): a `\u202e` typed in a Bash here-document landed in a brief as the real right-to-left override, and the sentinel blocked it; the maintainer's own drafts were mangled the same way twice on 2026-10-10 (backslashes halved, backticks run as substitutions).
- **Cause:** a shell reads escapes and substitutions inside the text it is handed: KP-009's mechanism, met again in the files the supervisor and the maintainer write.
- **Correction (corrected 2026-11-01):** no tool is safe for a typed backslash-u escape, the Write and Edit tools included: each has turned one into the real character (a typed no-break space arrived as the character twice, the second time in the Feedback document; escapes typed in briefs arrived the same way; the bridge's FB-011 and FB-029). So a test builds such a character with `chr()` (`chr(0x202E)`), a document names it by its code point (U+202E), and a file whose text quotes an escape is searched for the character's bytes after it is written; files that carry backslashes or backticks are still written with the Write tool, never through a here-document or an inline command; `invisible-check.py` lists any such character in the changed files (release A4).
- **Applies:** every brief, note or file written through a shell. The sign: a character the writer never typed, or a backslash missing.

### KP-053 — The Bash tool ends a background command after thirty minutes unless its own timeout is set
- **Surfaced:** the TDP, 2026-10-06 (TASK-157 r13d; gotcha 22): the builder, launched through `bridge-run.py --limit 7200` in the background, was killed at thirty minutes, mid-work and with no report, before the launcher's limit.
- **Cause (observed once, not settled):** the TDP's note reads it as the app's own default timeout for a background command; reAngle's ISS-008 records a background task of 2026-10-02 that ran six hours with no timeout of its own, so the behaviour is not the same in every case (a version, a kind of command, or the app's state may decide), and no record shows a `timeout` of 7,200,000 ms honoured yet.
- **Correction (a precaution):** every background launch sets the Bash tool's `timeout` in milliseconds as `~/.claude/cursor-bridge/workflow/phases/delegation-loop.md`, step 3, gives it for its kind (a heavy launch's duration covers its wait for the computer's one slot), the same on a wake-timer; a run that ended without `bridge-run: exit` in its `.err` file was killed from outside and is inspected as step 3b says; the trial of 2026.10.11b records whether a launch with the timeout passes thirty minutes.
- **Applies:** every background launch through the Bash tool. The sign: a run ending at exactly thirty minutes with no exit line.

### KP-054 — The installed product, run from the Workspace, ran the development code against the owner's live data
- **Surfaced:** the TDP, 2026-10-02 (gotcha 17): a plain `tdp status` typed with the Workspace as the current folder spawned a server that imported the development package from the working directory (`python -m` puts the current folder first on `sys.path`) and migrated the owner's live corpus databases.
- **Cause:** a command name that resolves to the development install, and an import path that prefers the current folder.
- **Correction (the TDP's, in its own notes):** rule 55 keeps development data apart; in addition, no product command is run from the Workspace folder, the installed executable is called by its full path from a neutral folder (`C:\`), and the check is `python -c "import <package>; print(<package>.__file__)"` from that folder; an editable development install on `PATH` is a hazard to name in the inventory (the correction still to make).
- **Applies:** every installable product with a development install on the same computer. The sign: the installed command's `__file__` under the Workspace.

### KP-055 — A session run from the packaged desktop app writes into a hidden copy of the local application folder
- **Surfaced:** the restructuring plan's section 13.1 (2026-10-04), from the owner's own finding; no project record carries it yet. The maintainer verified the mechanism on the owner's computer on 2026-10-11: the desktop app is the packaged application `Claude_pzs8sxrjxfjjc`, and its `LocalCache\Local` folder under `%LOCALAPPDATA%\Packages` holds the copies of what sessions wrote under the user's local application folder, which the owner's own programs, the installer and the installer check never see.
- **Cause:** the packaged app's file-system virtualisation of `%LOCALAPPDATA%` and its siblings.
- **Correction:** anything others must see there is created by a run sheet the owner runs in their own terminal, and an installer is verified from the owner's terminal (`Delivery-Conventions.md` §2.3), never from the session; a session verifies only what it can read back in the same way the owner's programs do.
- **Applies:** every write under `%LOCALAPPDATA%`, `%APPDATA%` or the registry made from a session of the desktop app. The sign: a file the session wrote that the owner's program cannot find.

### KP-056 — Interrupted mutation-driver runs left mutants in the product code
- **Surfaced:** reAngle, 2026-10 (ISS-017, twice): a driver that patches a product file and restores it in `finally` was killed mid-run (a dropped builder connection; a `TaskStop` of a background bash loop on Windows, which leaves the loop and its children running), and mutants stayed in the product; once the builder re-anchored its drivers around the mutated code.
- **Cause:** a killed process never reaches its `finally`, and a stopped loop on Windows does not stop its children.
- **Correction:** a residue scan after every driver run, run from the loop (`run/tools/mutant_residue_scan.py` on reAngle; a diff of the product files against the last reviewed commit before any gate elsewhere); a verification run is stopped with `bridge-stop.py` (2026.10.11c), which ends the whole process tree, so the loop never advances into its next driver (before that release, only between drivers, its `bash.exe` first); the mutants are written on the supervisor's side, in its mutants file with the criterion tests, never by the builder (2026.10.11d), and since release B the bridge's `mutation-run.py` applies them on a scratch copy of the Workspace, launched through the launcher's driver kind, so a run killed at any point leaves no mutant in the product (`~/.claude/cursor-bridge/workflow/phases/delegation-loop.md`, step 4); and no driver of the supervisor's edits the product's files either, working on a scratch copy as the program does; a subagent never leaves a loop behind (KP-042).
- **Applies:** every mutation or fault-injection driver that edits product files. The sign: `git status` showing a product file changed after a test run.

### KP-057 — An orphaned server held a delegation open for six hours through an inherited output pipe
- **Surfaced:** reAngle, 2026-10-02 (ISS-008, TASK-015b round 6): the builder started the project's dev server for its observability suite and left it running; the supervisor's wrapper waited on the builder's output pipe, which the server's children had inherited, so the wrapper did not return until the owner noticed six hours later.
- **Cause:** waiting on a pipe instead of on the child process, with grandchildren holding the pipe open.
- **Correction:** the launcher waits on the process and kills the whole tree at the limit (KP-033); a brief forbids leaving a server behind and says how a test starts and stops it (the brief's checklist, release A5); a wrapper of the supervisor's own never captures output through a pipe it then waits on.
- **Applies:** every delegation that may start a server. The sign: a run that neither ends nor writes.

### KP-058 — A module reloaded in a test, and a log handler left behind, corrupted later tests
- **Surfaced:** the video factory (Issue 10): a test reloaded modules in-process to re-read start-time settings, which replaced the modules' classes, so later tests comparing classes by identity failed, and the first fix pushed an identity workaround into product code; reAngle (ISS-015, BUG-017): app construction bound a root log handler to the current `sys.stderr`, a `capsys` test left it bound to a closed stream, and a later CLI test failed intermittently with a logging traceback in its output.
- **Cause:** process-global state (module objects, root logging) changed by one test and seen by the next.
- **Correction:** start-time or environment-driven configuration is verified in a fresh subprocess, never by reloading modules; logging handlers are configured once per process, or an autouse fixture restores the root logger after every test; a test that passes alone and fails in the suite is examined for shared state before anything else.
- **Addendum (2026-11-01):** a test that runs a program with working-folder defaults reads the live state of the folder it runs from: the bridge's roster-check test resolved its temporary roster against the Workspace's own launcher log and failed once the last builder run was a Grok model's (the bridge's ISS-006, 2026-10-16; CI has no run log and never saw it). Such a program runs from a temporary folder (`cwd=`) or is handed its paths, and a suite that passes only on some developer state is examined for leaked state first.
- **Applies:** every test suite with settings read at import or with root logging configured by the app, and every test that runs a program whose defaults are paths relative to the working folder. The sign: a failure that depends on the order or the selection of tests, or on what the developer's own folders hold.

### KP-059 — A browser launched detached on Windows opened a console window for every helper process
- **Surfaced:** the video factory, 2026-10-06 (Issue 15): dozens of terminal windows titled with Chrome's headless shell accumulated on the owner's desktop during test runs; `@puppeteer/browsers` launches Chrome with `detached: true` on Windows, so the main process has no console and every helper (GPU, utility, renderer) allocates its own.
- **Cause:** a detached launch of a console program on Windows, inside a windowless parent: a cousin of KP-014 (hook-launched console programs), from inside a library rather than the project's own code.
- **Correction:** a browser is launched attached (`detached: false`) from the project's own code in every path that drives it, the brief's process checklist says so (release A5), and rule 24's windowless requirement covers the browser's helpers; the supervisor closes leftover windows after its own runs until the fix merges.
- **Applies:** every Windows project that drives puppeteer, Playwright's Chromium or another browser from a windowless parent. The sign: console windows titled with a browser's helper on the owner's desktop.

### KP-060 — Merge-conflict markers survived a crashed resolver and were committed
- **Surfaced:** the TDP, 2026-10-01 (gotcha 15): a resolver script crashed after writing part of a merged file; the conflict markers stayed and the commit went through.
- **Cause:** a commit after a resolution step that was not checked for its own failure.
- **Correction:** after resolving a merge conflict, `git grep -n '^<<<<<<<\|^>>>>>>>'` must print nothing before the commit; `secret-sentinel`'s checklist has the same grep (release A5).
- **Applies:** every merge of `main` into a branch. The sign: a line of seven `<` or `>` in a committed file.

### KP-061 — A test suite over ten minutes ended inside a subagent's foreground call
- **Mistake:** a suite that can take more than ten minutes run in a foreground call, whose limit is ten minutes.
- **Surfaced:** reAngle, 2026-10-11 (the walk of release A5, PR 90): `test-runner` ran the project's suite in its own foreground call; at the ten-minute limit the app moved the suite's command to the background, and the result was waited for and read, not lost (corrected 2026-11-01 from reAngle's FB-007; this line first said the result was lost). The rule stands: a foreground call is no place to wait for a suite.
- **Cause:** the Bash tool's foreground limit of 600 seconds, a different limit from the thirty-minute end of a background command (KP-053); a subagent cannot raise it past ten minutes.
- **Correction:** a suite that takes more than ten minutes runs through the launcher in the background (`bridge-run.py --limit auto --kind test`), its output to a file under `run/`, with the Bash tool's `timeout` at the heavy launch's duration (`~/.claude/cursor-bridge/workflow/phases/delegation-loop.md`, step 3); `test-runner` reads the file afterwards and never starts such a suite itself (step 4; test-runner.md; release 2026.10.11d). Since release B every suite runs that way, whatever its length (step 4).
- **Applies:** every project whose suite runs longer than ten minutes. The sign: a `test-runner` report that ends with a timeout and no result.

### KP-062 — A design critique ran 45 rounds on one change, and the four-round ceiling stopped nothing
- **Surfaced:** the TDP, 2026-10-18: the design two-critic loop on one change (the Azure monthly allowance) ran 45 rounds in about seventeen hours on Fable 5.1, one Cursor Review B call per round. It used up the owner's monthly Cursor pool for non-native models a few days after its reset, and about $156 of the day's $234 of price-weighted Claude usage, subagents not counted. Its `docs/DESIGN_CRITIQUE.md` shows the decay: rounds 1 to 4 found 34 Blocking findings; rounds 5 to 44 found 12 in all, most rounds none, and one to six Should-fix findings each, most of them restatements and paraphrase sweeps.
- **Cause:** three gaps in the text, which together made an endless loop. The four-round ceiling covered only what was still Blocking, so a Should-fix finding past round four had no cap. "The text leaving a fourth round gets one confirming read by both" restarted the loop: every fix changed the text, every confirming read found a few new Should-fix items, and every fix needed another read. The code gate's convergence rule (two reviewers naming one defect makes it blocking) was applied to the two design critics and restarted the loop after round four; the digest's rule 6 ("never a round count") invited the same reading. Nothing in a program held the written ceiling.
- **Correction (2026.10.18a):** at most four rounds per subject (the design, the plan, each change and each change's plan addendum), a non-convergent finding starting none; then, if the text changed, one confirming read by both critics, final whatever its number, whose findings are fixed or accepted and recorded; then one resolution round holding every question still Blocking or non-convergent; then the gate, whatever is still open, its record listing it. A subject is one token of lower-case letters, digits and hyphens, distinct from every other. A failed launch follows step 3b, every one recorded: it runs once more (exit 4), then once on the re-resolved profile (exit 3); then the design waits for the roster or the owner's word, and the file runs once more with no re-runs; if that fails too, the round stays not run and the subject goes on to its resolution round or its gate. The convergence rule is the code gate's only. `bridge-run.py` refuses, with exit 125 and a message beginning `bridge-run: refused - design ceiling: `, a `cursor-agent` launch naming `run/review/DESIGN-<name>.md` whose round is above five, is `R2` or later, or cannot be read (a round is a positive integer without a leading zero, or `R` and one, 1 to 5 and `R1` allowed; a name holding a space or a capital cannot be read); a `Design rounds above five: <subject> <rounds>` line in `docs/RUN_PARAMETERS.md`, written only on the owner's own words, allows that subject rounds up to `<rounds>` and `R2`, the same shape once more, once, and nothing beyond. The digest's rule 6 names the exception, and `plan-critic` raises only what is new, or Blocking, in a confirming read. A critique that has run four rounds or fewer when the release is installed follows the new text from where it stands. One that has run five or more, whatever its fifth was, gets no confirming read and no further round: its open findings go to its one resolution round, or to the gate if it has had one. Only that subject's owner's line allows more, and then it continues under Phase 2's shape from where it stands. A running subject whose name is not such a token takes one at calibration, written in its record's heading (a plan critique on the old `DESIGN-<round>.md` files takes `plan`); its next file carries it and its count continues. A round file named other than by its number (a confirming read written `DESIGN-<subject>-confirm.md`, say) cannot be read and is refused: its next file takes the next round's number. Its twin is the code gate's ceiling (release B, R-042): three rounds per increment and per stage review, held by `bridge-run.py` and `review-guard.py`, past which only the five blocking classes send work back (the delegation loop's step 7, "The review ceiling").
- **Applies:** every design, plan and change-cycle critique; any loop whose stop rule counts only one grade of finding. The sign: a critique past four rounds, rounds whose findings are restatements of earlier ones, or a design-mode `cursor-agent` started other than through `bridge-run.py`, which no ceiling holds (rule 8).

### KP-063 — A provider's bill is in its own unit, failed attempts included
- **Misconception:** a spending cap set on the caller's own estimate bounds what the provider charges, and the usage metric the product records is the bill.
- **Surfaced:** the TDP, 2026-10-12 to 17: a paid document read on Azure passed its cap at list price; the provider billed two failed attempts, the product's metric counted the pages twice, and a server left running added to the charge (the evaluation of 2026-10-18, D13).
- **Correction:** a cap is set in the provider's own billing unit, every failed or retried attempt counted at its price; before a run of size, one small paid probe is reconciled with the provider's cost view; the product's metric is checked against the bill and never stands in for it; a paid run leaves nothing running.
- **Applies:** every part classified *spends money*; every paid run and its cap. The sign: a provider's charge that differs from the product's own count.

### KP-064 — A harness that calls below the product's entry point creates a state the product cannot
- **Mistake:** a test or demonstration harness drives a function the product wraps, instead of the product's own entry point.
- **Surfaced:** reAngle, 2026-10 (its ISS-024): a harness called below the product's entry point and built a state the product itself cannot reach, so what the harness showed was not the product's behaviour (the evaluation of 2026-10-18, D3 and D13).
- **Correction:** a harness drives the product's own entry points (its command, its API, its screen), never a function the product wraps; a state a test or a demonstration needs is reached through the product, or the test says it tests the function alone and claims nothing about the product.
- **Applies:** every demonstration, observability test and integration harness. The sign: a harness that imports the product's internals to set up a state.

### KP-065 — A mutation driver anchored on a line a fix moved matches nothing while its results claim a kill
- **Mistake:** a driver finds each mutant by its anchor text; a fix moved or reworded the line, the mutant applied nowhere, and the driver's results file still recorded the kill of an earlier run.
- **Surfaced:** reAngle, 2026-10 (its ISS-022; the evaluation of 2026-10-18, D1 and D13).
- **Correction:** a mutant that applies nowhere is never a kill: `mutation-run.py` reports it not applied (exit 1) and runs again every mutant whose keyed inputs changed since its kill (release B, R-041); a fix that moves product code re-anchors every mutant on the moved file in the same pull request, the mutants file being the supervisor's (`~/.claude/cursor-bridge/workflow/phases/delegation-loop/decide.md`, "The mutation run"); a hand driver checks at HEAD that every live mutant applies exactly once before any review reads its results.
- **Applies:** every mutants file and every hand driver. The sign: a kill recorded for a mutant whose anchor text is no longer in its file.

### KP-066 — A security floor trusted before it ran against the real service
- **Misconception:** a scanner step configured in CI, with its token, is a working floor.
- **Surfaced:** the bridge, 2026-10-12 (TASK-002): `semgrep ci` with an empty policy passed having run no rules, the token enabled no paid engine, and a pin named a deprecated release; the floor's design and its review rounds had read the workflow, not what it ran.
- **Correction:** a floor's first increment runs each scanner against the real service and reads its log: the rules or advisories it ran are counted (a step that ran none is red, as OSV-Scanner's exit 128 is, KP-005), what a token enables is read from the vendor's documentation at the time, and each tool is pinned at a supported release; the check is repeated whenever a scanner, its token or its policy changes.
- **Applies:** every project's security floor, at configuration and at every change of a scanner. The sign: a scanner step green in seconds, or a log that names no rule count.

### KP-067 — `git show <rev>:<path> --output=<file>` creates the file empty
- **Mistake:** `--output` read as writing the blob into the file.
- **Surfaced:** the bridge, 2026-10-12 (ISS-004, TASK-004's second review round): the plan-sections file both reviewers were told to read was committed at 0 bytes; `git show --output` had created it empty and printed the blob to standard output, and nothing checked its size before the snapshot.
- **Correction:** a committed file is copied with a redirect (`git show <rev>:<path> > <file>`) or `git restore --source`, and its size read after; since hotfix 2026.10.25a `review-guard.py snapshot` lists every review input under `run/review/` with its size and refuses an empty one, citing this entry.
- **Applies:** every file a reviewer reads; any `git show` into a file. The sign: a review input of 0 bytes.

### KP-068 — A vendor CLI's banner printed part of a key into a public repository's CI logs
- **Mistake:** a key held in a repository secret was taken to be safe in the job's log.
- **Surfaced:** the bridge, 2026-10-12 (ISS-005, TASK-002): the Socket CLI's banner printed five characters of its key's secret part in six runs of this public repository's CI; GitHub masks a secret only where the whole value appears, so a part passes unmasked.
- **Correction:** a step that holds a secret has its first CI log read for any part of the key before the increment is accepted; vendor CLIs run with their banner, spinner and telemetry off where they offer it (`socket ci --no-banner`), pinned in the floor's test; on a public repository a partial print is an exposure, and deleting the logs and replacing the key are the owner's actions.
- **Applies:** every CI step that holds a secret, above all in a public repository. The sign: a log line holding a few characters of a key.

### KP-069 — A squash-merged status file describes the pre-gate state on `main`
- **Mistake:** the status file a pull request carries was written in the form true while its gate ran.
- **Surfaced:** the bridge, 2026-10-16 to 19 (ISS-009, stage B1's review rounds 1 to 3): on `main` the file named the merged increment as before its gate and its Next line the gate already run, so a session resuming from it would have gated a merged branch.
- **Correction:** every pull request carries the status file as it reads at that pull request's merge (Last accepted naming the pull request first, by number, since a squash cannot know its hash; In flight none; Next the step after the merge), checked in CI by a test that reads the pull-request variables; the live position between merges lives in `run/supervisor/in-flight.md`.
- **Applies:** every project whose records merge by squash. The sign: a status file on `main` naming a gate as still to run.

### KP-070 — A wall-clock schedule walked in naive local time never revisits the hour that repeats when summer time ends
- **Mistake:** a schedule's next time found by adding a minute at a time to a naive local `datetime`.
- **Surfaced:** the bridge, 2026-10-25 (ISS-014, BUG-020): the loop guard's `cron_next` never found a one-shot wake-up in the repeated hour on the night the clocks went back, and answered an hour early from inside it; CI on UTC never meets a fold.
- **Correction:** a schedule walk iterates over instants and converts each to wall time, so the repeated hour is visited twice and the skipped hour never; wall-clock code is tested on a named zone across both daylight-saving transitions.
- **Applies:** every program that walks or matches a local-time schedule. The sign: a failure only on the nights the clocks change.

### KP-071 — A test that patches a standard-library function records the library's own calls
- **Misconception:** `monkeypatch.setattr(mod.time, "sleep", ...)` patches the module under test.
- **Surfaced:** the bridge, 2026-10-26 (ISS-016, BUG-028): a review-guard test failed at random on Linux, recording subprocess's own 1 ms poll as the guard's sleep; `mod.time` is the process-wide module, and only the POSIX wait sleeps.
- **Correction:** a test that records a module's calls replaces the module's own binding (`monkeypatch.setattr(mod, "time", stand_in)`), never an attribute of a shared standard-library module; a test that fails only on Linux is checked first for a POSIX-only path in the standard library.
- **Applies:** every test that records calls by patching. The sign: a recorded call the code under test never makes.

### KP-072 — A count seeded from files another mechanism also writes
- **Misconception:** builder report files stand for replied Review B rounds.
- **Surfaced:** the TDP's first Review B under release B, 2026-10-30 (the bridge's ISS-021, BUG-036): the review guard's seed took the highest report number as the replied rounds, while release B has every builder round write a report, so builder rounds were counted and the review was refused above the ceiling.
- **Correction:** a seed names what writes its files before and after the release that seeds it, and a test drives the seed under the release's own writers; a field trial before the other projects resume finds what the release's tests did not.
- **Applies:** any program that infers a count from files. The sign: a count that rises with work of another kind.

### KP-073 — A check that scans shipped code found its own description
- **Misconception:** a program's docstring is not shipped code.
- **Surfaced:** the bridge, 2026-10-31 (ISS-023, BUG-038): `completion-check.py --mode done` flagged its own docstring, which quoted the stand-in phrases it scans for, at the bridge's project end, the first project shipping the check as its own code.
- **Correction:** a check that scans shipped code runs once on its own repository before its release, and its description is tested against its scan; a wording that must describe a pattern without matching it is drafted beside the pattern and checked before the brief.
- **Applies:** every scanner a project ships as tracked code. The sign: the check's own file among its findings.

### KP-074 — Status-file tests gated on CI variables skip locally
- **Mistake:** a local suite run taken for the CI run of a pull request.
- **Surfaced:** the bridge, 2026-10-30 (ISS-022, TASK-027's stamp): two tests every local run passed failed on CI, one gated on the GitHub pull-request variables and so skipped locally, one in a file no local selection included.
- **Correction:** before the first push of a pull request that changes `docs/PROJECT_STATUS.md`, `project.json` or a `VERSION`, the full suite runs once with `GITHUB_REF=refs/pull/<n>/merge`, `GITHUB_BASE_REF=main` and `GITHUB_EVENT_NAME=pull_request` set for the launcher's run, through a key file outside the Workspace (`--key-file`); a test gated on those variables names the gate in its skip reason.
- **Applies:** every pull request that changes the status file, `project.json` or a `VERSION`. The sign: a test skipped locally that CI runs.
