# Claude-Cursor Bridge — CHANGELOG

One entry per release. `VERSION` and `MANIFEST.json` are stamped by the maintainer's
`tools/make-manifest.py`, which refuses to stamp a version that has no entry here.

Each entry has three parts. **What changed** is for the maintainer and the curious.
**Running projects must** is the part `/calibrate-bridge` acts on: every item names the
**phase** it belongs to, so a project that has already passed that phase does not reopen
it, a project in it applies the item now, and a project before it applies the item when it
arrives. An item marked *(all phases)* applies immediately. **If rolled back** (since
2026.10.05a) says what a project that calibrated to the release must restore when the
release is taken back with `bridge-install.py --rollback`; an entry without it restores
nothing. A release with new mechanisms also names its **field acceptance**: what the trial
project must show before the other projects resume.

---

## 2026.10.05a

**Release A1a of the restructuring plan: the bridge's own house.** Its sources leave the folder where a session working on the bridge loaded them half-edited; a release can be taken back; four contradictions in the bridge's own text are removed.

**What changed**
- **The governance sources moved from `.claude/` to `bridge/` in the bridge's repository** (plan review R8, KP-037). Claude Code loads agents, commands, settings and hooks from a project's `.claude` folder, prefers a project's agents over the installed ones and reloads them while a session runs, so a branch that edited a reviewer changed the reviewer of that branch. On an installed machine nothing moves: the install program still copies `commands/`, `agents/`, `skills/` and `cursor-bridge/` into `~/.claude`. **The install command's path changes** to `<the bridge's repository>/bridge/cursor-bridge/bridge-install.py`. The repository's generated `settings.json`, which existed to give sessions there the bridge's hooks, is gone.
- **A release can be taken back** (`bridge-install.py --rollback`). An install over another version first keeps that version's own files under `~/.claude/cursor-bridge-previous/<version>/` (one previous release is kept). A rollback puts the kept release back, keeps every key of the owner's, restores the previous shim, and writes the newer release's **If rolled back** items to `cursor-bridge/ROLLED-BACK.md`, which `/calibrate-bridge` applies in a project whose recorded version is newer than the installed one. The bridge is installed once per computer, so both an install and a rollback reach every project at once; the release flow in the restructuring plan (section 15) pauses the projects for that reason.
- **Installing and taking back are one replacement,** so every install exercises the way back. Either way the files, the allow and deny rules and the hooks that only the replaced release owned are removed (an install used to add and never remove, except the entries on the `retired` list). The order is fixed so that `settings.json` never names a hook whose program is not there, also when a run is interrupted and repeated: a hook that runs a missing program ends with exit status 2, which Claude Code reads as "block", for every matching tool call or the end of every turn, in every session on the computer. `settings.json` is written whole or not at all. A kept copy is never written twice (a repeated run after an interruption would otherwise save a mixture of two releases as "the previous one"), and a kept copy that is not complete is refused before anything changes. The install check now reports a hook that runs a `cursor-bridge` program which is not installed.
- **Changelog entries gain a third part, "If rolled back",** stating what a project that calibrated to the release must restore when it is taken back.
- **What a builder may write is said once** (R17). The delegate command read "do not modify … anything under docs/", while every brief told the builder to append to `docs/BUILDER_NOTES.md` and the delivery conventions required `docs/cli-reference.json` regenerated in the same change. The command now ends that clause with "unless the Scope section names the file"; every brief's Scope lists `docs/BUILDER_NOTES.md`, and `docs/cli-reference.json` when a command changes; the brief's Out of scope says the same.
- **Review A answers in the merge policy's words** (R17). `diff-reviewer` returned PASS, PASS WITH FINDINGS or FAIL while the policy waited for APPROVE, REJECT or ESCALATE-INTENT, which left a question of intent no channel. It now returns those three; an approval may still carry findings. The auditors keep PASS and FAIL as inputs to it.
- **Five run parameters everywhere** (R17): rule 29 and the status template named three of the five.
- **Pinned versions and configured modes are recorded in the inventory's Resources** (R17), no longer in the status file, which is capped at 120 lines and had no place for them: 21 places in the conventions now say so.
- Tests: the rollback and the replacement (16, among them a replacement interrupted at each of its steps in both directions), the install check's two additions, the text contradictions (6), and the whole suite from the new folder.

**Running projects must**
- *(all phases)* Install with `python <the bridge's repository>/bridge/cursor-bridge/bridge-install.py`, restart the app, run `/calibrate-bridge`. This is the first release installed under the trial rule: every project is paused before the install, one is calibrated and resumed, and the others resume on the owner's word.
- *(building, changing)* From the next brief on, the delegate command is the one step 3 shows and every brief's Scope lists `docs/BUILDER_NOTES.md`; a brief already delegated finishes under its own command. Review A's verdict reads APPROVE, REJECT or ESCALATE-INTENT from the next review on; a verdict already recorded as PASS or FAIL stands.
- *(all phases, record-keeping)* At the next reflection point, move the pinned versions and configured modes recorded in `docs/PROJECT_STATUS.md` (tool versions, scanner rulesets, action commits, the observability tier) to `docs/INVENTORY.md` → Resources, and remove them from the status file.

**If rolled back**
- *(all phases)* Nothing in a project's files has to be restored: this release changes no record's format. Briefs written under it stay valid, and their next delegation uses the previous release's command. Records moved to the inventory stay there. Set `Bridge version:` to the installed version. The release this one is taken back to, 2026.10.04e, has a calibration command that does not know a rollback and does not read this note: in a project that had calibrated to this release, the owner tells the supervisor "the bridge was taken back to 2026.10.04e; set the `Bridge version:` line to it".

**Field acceptance on the trial project.** With every project paused: the release is installed, taken back with `--rollback`, and installed again, and the install check passes each time. Then the trial project calibrates, and one increment goes through the loop: its brief's Scope names `docs/BUILDER_NOTES.md`, the scope check passes with the builder's note written, and Review A answers with one of the three verdict words.

---

## 2026.10.04e

**Account keys are withheld from builder and reviewer runs, and the advice of 2026.10.04c is corrected.** Found by the first evaluation of the projects' reports, in two projects independently.

**What changed**
- **The advice was wrong.** 2026.10.04c told projects to move paid keys out of `Workspace/.env` "to the user's environment". A variable in the Windows user environment is handed to every program the owner starts, and the launcher withheld only the GitHub variables, so the keys would have reached every builder run and every Review B run, and Review B executes code. The TDP's supervisor saw this and chose a key file outside the Workspace; reAngle's wrote its run sheet as instructed.
- **The launcher and the shim withhold every key-like variable** (`bridge_env.stripped_env`, `cursor-agent.shim`, one test of the name in both): a whole-word `TOKEN` or `SECRET`, `PASSWORD`, `PASSWD`, `CREDENTIAL`, an API, access or private key, or a name ending in `_KEY`. Cursor's own variables (`CURSOR_*`) are kept. A test runs both recipes on the same sample and requires the same answer.
- **No secret through an environment variable the owner sets** (the owner, 2026-10-05). Founding rule N2 itself said keys live in "the owner's environment", and the inventory template offered "user env var"; both now name a key file outside the Workspace, the product's encrypted store or the system's credential store. A store's unlock passphrase counts as a key (the video factory's `SFVF_SECRETS_PASSPHRASE` is given through a variable today), and the launcher's filter withholds it. The run-sheet guidance forbids asking the owner to set a secret as a variable. The conformance check gains the floor: an inventory row that says a secret arrives through an environment variable is `MISSING`.
- **The conformance check** advises a key file outside the Workspace (for example under `%APPDATA%\<product>\`) or the product's encrypted store, and never the user environment; it notes key-like variable names found in the session's own environment. KP-032 records it.

**Running projects must**
- *(all phases)* Install with `python <release .claude folder>/cursor-bridge/bridge-install.py`, restart the app, run `/calibrate-bridge`. **Where a run sheet of 2026.10.04c asked the owner to put account keys into the Windows user environment (reAngle: `MODAL_TOKEN_ID`, `MODAL_TOKEN_SECRET`, `HF_TOKEN`), replace it:** the keys go into a key file outside the Workspace that the product, or the supervisor's own paid scripts, read; any of them already set in the user environment are removed from it by a run sheet. A project's tests that need a local service's password read it from the project's `.env`, not from the environment: the builder no longer inherits key-like variables.
- *(all phases)* **A product that takes a secret or an unlock passphrase from an environment variable the owner sets** (the conformance check names them from the inventory: the video factory's store passphrase; the TDP's and reAngle's account keys where the product reads them from its process environment) gets one increment that makes the product read it from a key file outside the Workspace or the system's credential store, and its run sheets and User Manual change with it. Until that increment has merged, the owner is asked for no new variable; a paid run the supervisor itself starts loads the key file into that one process only.

---

## 2026.10.04d

**The models each role runs on, and Review A off a legacy model.** The owner's decision of 2026-10-04 after the verified fact that Fable is not a second usage pool (it draws from the weekly limit, at most half of it, faster — KP-036).

**What changed**
- **Review A was pinned to `claude-opus-4-8` since 2026-09-05** — a legacy model two generations behind the supervisor — in four reviewer definitions and the roster template. Now: `diff-reviewer`, `security-auditor`, `design-auditor`, `refactor-scout` on `claude-opus-5-5` at `effort: high`; `spec-packager` and `diagram-specialist` on `claude-opus-5-5`; `plan-critic` on `claude-fable-5-1`; `test-runner`, `secret-sentinel`, `cursor-configurator` on `claude-sonnet-5-5`. No definition inherits the session's model any more. The roster template's `review_a` is `claude-opus-5-5`.
- **Rule 48: the session's model follows the phase** — Fable 5.1 through intake, design, interface and plan and in any design revision; Opus 5.5 from configuration on. The switch is the owner's by hand (the app refuses a session re-pricing itself), so the report that closes the stage before a switch names it right after the decision it leads with: the plan gate, the arrival of a change request, the design revision's gate. A supervisor whose system prompt names another model than the phase's leads its next report with the switch. The calibration report now carries a `Session model for this phase` line.
- Tests: every agent definition names a current model, the reviewers carry high effort, the roster template matches `diff-reviewer`, and no legacy id remains in the tree.

**Running projects must**
- *(all phases)* Install with `python <release .claude folder>/cursor-bridge/bridge-install.py`, restart the app, run `/calibrate-bridge`: the calibration sets `review_a` in `docs/ROSTER.json` to `claude-opus-5-5` and its report tells the owner the session model for the project's phase (Opus 5.5 for every project in build or done; Fable 5.1 only while a design revision is open). Subagents spawned before the restart ran on the old definitions; their results stand.

---

## 2026.10.04c

**Release 0b of the restructuring plan: the rules that survive a compaction, the founding rules in the core, the conformance check, the guides corrected — and, from its own pre-install review, the checkpoint guard for a reviewer with execution.** Built on a branch and brought in through the bridge's own pull-request gate: `main` is now protected (both CI jobs required, administrators included, no force-push).

**What changed**
- **KP-035: the core survives a compaction.** `supervisor.md` now opens with a **digest** of the core (the founding rules, the loop with its literal commands, the escalation list, the reporting rules, every standing rule in one line; inside the 20,000 characters a compaction keeps), and the new `session-start.py` hook (SessionStart, matchers `compact`, `resume` and `fork`) re-injects it after every compaction, resume and fork together with the project's phase and the exact sections of `supervisor.md` to re-read before the next action, with their line ranges, and whether to continue or to wait for the owner. Claude Code caps a hook's output at 10,000 characters and swaps a longer one for a file path, and the pre-install review measured the single-run form being cut on all three projects (the cut part was the pointers): the hook is registered **twice** for the event, one run printing the pointers and one the digest. Headings inside code blocks no longer end a section early; `Phase: configuration` is mapped; the message tells a session that is not the supervisor to ignore it and a forked session not to continue the loop (it fails open on purpose: a gate on the transcript silenced two live supervisor sessions in the review's second pass). Measured cause: a compaction re-attached exactly 20,000 of the file's 150,000 characters, and the record shows rule-breaking within minutes of several compactions. Tests run the hook for every phase the status template allows, on a status file at the template's limits, and check that the digest names every rule, carries the literal delegate command and the merge-authority check. Rule 28 says to read the re-injected sections, never to work from memory of the rules.
- **The founding rules N1–N9 are stated in the core**, in a section of their own after the digest, each with what enforces it, restated as the restructuring plan decided: N1 (files are the truth, programs one-shot, a background process only under five conditions) and N6 (the verified gate, the owner choosing who merges). The Project Summary's N1, N5 and N6 are aligned; the merge policy no longer says "Team plan".
- **Review B keeps execution, on a guarded checkpoint.** 2026.10.04b had moved the cross-family reviewer to the CLI's read-only mode; the TDP's supervisor reported that this removed the reviewer's ability to run the tests and build its own reproductions, where its strongest findings had come from, and the owner decided to keep that ability. Review B runs with `--force` again, through the launcher (identity withheld, one-hour limit), **in the background**, on a committed checkpoint that the new **`review-guard.py`** snapshots before the launch (`snapshot <nnn>`: HEAD, the branch, every ref, the stash list, `.git/config`, the hooks folder, the ignored entries; it refuses a dirty tree) and verifies after it (`verify <nnn>`: the configuration is read as a file before any git command runs; the tree is put back with `git reset --hard` and `git clean -fd`; a commit, a moved HEAD, a new ref or stash, a changed configuration, hook file or `.env` is `GATE-INTEGRITY`), and `premerge <nnn> <pr>` proves the head about to merge descends from the reviewed one, differs only under `run/review/`, and is the pull request's head, merged with `--match-head-commit`. The pre-install review showed that `git status` plus `git checkout -- .` saw none of these; its second pass showed the guard's own `git checkout` running a hook planted in `.githooks`, so every git command of the guard runs with the repository's hooks and file monitor off and the active hooks folder is hashed before any git command; local refs are put back; records the project gitignores are protected; the launcher's `.err` file is kept; the snapshot's hash is printed at both ends. The supervisor writes nothing to the checkout while the review runs; the merge policy says what the guard covers and what it does not. The activity check stays.
- **The project conformance check** (`conformance-check.py`, review R4): compares a project's configuration with the floors the bridge requires and prints `OK`/`MISSING`/`NOTE` per floor: scanners as workflow **steps** (a step guarded by `if:` is `MISSING`, it is skipped silently; Semgrep must run the bridge rules or the Pro engine, public rulesets alone are not the floor; an unpinned scanner version is a note), actions pinned by commit, the required status check and the repository's visibility read through `gh` (GET only; `--offline` skips), the boundary, windowless and secure-coding rules, lockfiles (a root `requirements.txt` needs a transitive lock; an editable sub-project is covered by it), the records (a design under other names is a note naming them), the diagram index, the command reference checked in CI or by a test, account keys in `.env`, `.env.*` and `<folder>/.env` within the builder's reach (local service passwords and the product's own tokens are notes), a record the project gitignores (missing: the records are versioned), a scanner step that guards itself in its script (a note), the private memory notes by name, the recorded bridge version. It accepts the project root, where sessions start. It runs at step 1b of `/calibrate-bridge` and first at every reflection point; every `MISSING` is a calibration item. Run on the three projects today: the video factory lacks every scanner, the detector, the secure-coding rule, a transitive lock and the diagram index, and its repository is public; the TDP's Socket step is guarded and its Semgrep runs public rulesets only, and its paid keys sit in `.env`; reAngle's account tokens sit in `.env`. Values are never read.
- **`/calibrate-bridge` step 2b reviews the private memory notes** the check lists: a note that restates a bridge rule or holds project state is deleted or reduced to a pointer (rule 41); the TDP's notes still described a retired builder as current.
- **The setup guide** corrects the worktree statement (a bridge project is opened at its root, which is not a repository, so no worktree is made), the auto-merge lines (under `Merge authority: supervisor` the supervisor completing the merge is the design), and asks for one manual `/compact` after this install to see the hook's message live.

**Running projects must**
- *(all phases)* Install with `python <release .claude folder>/cursor-bridge/bridge-install.py`, restart the app, run `/calibrate-bridge`: it runs the conformance check at step 1b (every `MISSING` floor becomes a calibration item for the next stage) and the memory-note review at step 2b. **Before the first Review B with execution on a project whose `.env` holds account keys** (the check names them: the TDP's `ANTHROPIC_API_KEY`, `OPENROUTER_API_KEY`, `AZURE_DI_API_KEY`; reAngle's `MODAL_TOKEN_*`, `HF_TOKEN`), the keys leave `.env` — a run sheet to the owner to set them in the user's environment, and the increment that makes the product read them from there, delegated first — because a reproduction can spend on those accounts.
- *(building, changing)* From the next increment, Review B runs as step 8 now says: `review-guard.py snapshot`, the launcher in the background, `review-guard.py verify`, the activity check, `review-guard.py premerge`. A review already running finishes under the old step.

---

## 2026.10.04b

**The fixes from the pre-install review of 2026.10.04a** (`Claude-Cursor Bridge Release 2026.10.04a Review.md`, findings F1-F12). Install this release, not 2026.10.04a.

**What changed**
- **F1: the model switch can no longer undo itself, and a dead line no longer loops forever.** The roster's changing state (the pool's exhaustion, the marks, the failure counts) moved out of the tracked `docs/ROSTER.json` into the repository's own `.git/bridge/roster-state.json`, which no reset, clean or checkout touches; a roster from an older release seeds it once. The failure window is eight hours, longer than any run limit. A connection failure or a hit run limit is retried twice, then exit 5: stop and tell the owner, because no model switch fixes a network. A legacy integer count is treated as expired (F9). A test runs record → reset → re-resolve in a git repository.
- **F2: the supervisor's own merge step now matches the merge policy.** Review B is launched through the launcher with `--trust --mode ask`, the launch time is read from the launcher's first stderr line, and `pr-activity-check.py` printing `OK` is part of condition 3. The parallel delegation step no longer says "starting with `cursor-agent`". A test checks every `cursor-agent` invocation in the instructions: all go through the launcher, every read-only review carries `--trust --mode ask` and never `-f`.
- **F3, F7: the guardrails hold in both shells and every form.** New `permission-guard.py`, a PreToolUse hook for the Bash and PowerShell tools that parses each command and refuses `gh pr merge --admin`, the REST merge, and every force-push form (`--force`, `--force-with-lease`, `-f`, `-fu`, `--mirror`, a `+` refspec), through chains, wrappers and `git -C`, in every permission mode; 73 tests. The deny rules are mirrored for the PowerShell tool, which also refuses `cursor-agent` and `bridge-run` from PowerShell (where `~` is not expanded and the shim does not apply). The instructions say to run the bridge's commands with the Bash tool only, and the text no longer calls the rules a boundary.
- **F4: the tests touch nothing outside their temporary folders.** `LOCALAPPDATA` points at a temporary folder in every test run; the shim and the `gh-empty` folder are created there. The install program keeps a previous, different shim as `cursor-agent.bak-<date>-<time>`, and names the settings backup with the time too.
- **F5: honest claims and a closed window.** `pr-activity-check.py` refuses a `--since` without a time zone, and also flags what the owner's account did elsewhere in the repository since the launch that an agent would cause (a comment or review on another pull request, a merge, a push to `main`); the supervisor's own task-branch pushes are not flagged. The texts in KP-032, the merge policy and the setup guide say what the mechanism is (identity withheld, so an accidental post or push fails) and is not (a sandbox).
- **F6: the launcher accepts only the loop's commands**, `cursor-agent` and `gh pr checks`, and refuses anything else (exit 125); its allow rules name those two forms.
- **F8: rule 8's reason corrected** to Claude Code's documented behaviour: `timeout`, `time`, `nice`, `nohup` and `stdbuf` are stripped before matching, `cd` and a shell are not; deny and ask rules see through chains and wrappers.
- **F10: the launcher puts itself into the job before starting the command**, so every child is born inside it; at a normal end the job's closing kills any orphan the command left (proven on a dev-server-like child). Signatures declared for the Windows calls (the pseudo-handle was truncated before).
- **F11: tests added** for the activity check (with canned `gh` answers), the shim's recipe against the Python one, the stripped environment reaching the child, a program printing a character the console lacks, and the consistency of the instructions; CI actions pinned by commit and `pytest` by version.
- **F12: retired entries are removed at install** (`settings.bridge.json` lists them: the old worktree, jscpd and impeccable patterns and the first launcher rule); the setup guide names the release's `.claude` folder correctly; the usage-limit text in step 3b matches the classifier; a project's own commands go to the classifier and are not called defects.

**Running projects must**
- *(all phases)* Install with `python <release .claude folder>/cursor-bridge/bridge-install.py`, restart the app, run `/calibrate-bridge`; the items of 2026.10.04a apply unchanged. At the first `roster-check.py` run the roster's state moves to `.git/bridge/roster-state.json` (a `note  migrated` line); nothing to do.

---

## 2026.10.04a

**Release 0a of the restructuring plan: the safety fixes the plan review of 2026-10-04 ranked above everything else, shipped ahead of the TDP.** Every program change carries tests under `Workspace/tests/`, run by the bridge's own CI from this release on.

**What changed**
- **KP-032: the owner's identity is withheld from every `cursor-agent` process.** The shim that Claude Code's Bash tool runs for `cursor-agent` (`cursor-bridge/cursor-agent.shim`, installed by the new install program) and the new launcher `bridge-run.py` start the agent with `gh` logged out, no token variable, and git without a credential helper and without prompts. Review B runs with `--trust --mode ask`, the Cursor CLI's read-only mode, never `-f`. New `pr-activity-check.py`, run after every Review B and before every merge, lists what was written to the pull request since the launch and flags anything written as the owner. New **deny rules**, enforced in every permission mode: no `gh pr merge --admin`, no force-push. (Verified cause: on 2026-10-02 Review B posted its verdict on TDP #182 under the owner's account.)
- **KP-033: every background run has a limit that ends it.** `bridge-run.py --limit <s> -- <command>` runs a command inside a Windows Job Object and kills the whole process tree at the limit (exit 124), so an orphaned child can no longer hold the output pipe and the supervisor always wakes. Delegations run under 7,200 s, Review B under 1,800 s, the CI watch under 3,600 s. On exit 124 the supervisor inspects the tree before discarding anything, because a builder that hung on its way out may have finished (TDP ISS-005).
- **KP-034: the roster check no longer misfires.** A `--record-failure` argument that is not a model of the roster is refused (reAngle ran five days on its backup pairing because a file path was recorded as a model); a connection error is transient and never counted; a failure count expires after two hours and `--record-success` clears it; an automatic "unavailable" mark expires after six hours; a rate limit or the word "billing" no longer counts as a usage limit; step 3b resets the tree *before* re-resolving, so the reset can no longer revert the roster files and reinstate the exhausted model. The probe runs with the stripped environment.
- **KP-030, finished: installing is one command.** New `bridge-install.py` copies the release, **merges** the bridge's entries (`cursor-bridge/settings.bridge.json`, now the single source of the allowlist, the deny rules and the hooks) into the owner's `settings.json` without touching any other key, installs the shim, and runs the check. `bridge-check.py` no longer fingerprints `settings.json`: it verifies that the bridge's entries are present and that the installed shim equals the release's. `make-manifest.py` regenerates the tree's own `settings.json` from the bridge file.
- **The allowlist matches what the instructions issue.** Entries corrected to Claude Code's documented matching (`git worktree add ../Worktrees/*`, `npx --yes jscpd@*`, `npx impeccable@*`); missing commands added (`git log`, `git rev-parse`, `git rm`, `git revert`, `git reset --hard`, `git clean -fd`, `git config core.hooksPath`, `pytest --collect-only`, the new programs). A test (`tests/test_allowlist.py`) collects every command from the instructions and checks it against the rules, and checks that the deny rules catch the override merge and force-push in every spelling. Found on the way: the merge policy said `git pr merge` (a typo), and the instructions said both `git checkout -B` and `git switch -c`; both fixed.
- **The permission mode is stated.** The supervisor's instructions now say that sessions run in *auto* mode, that the deny rules are the hard guardrails, and that a command the rules do not cover is a bridge defect, never a question for the owner. Rule 8's reason is corrected: each part of a compound command is matched on its own and a wrapper is not stripped, so chained or wrapped commands match nothing.
- **The loop guard works wherever a session starts.** It finds `docs/PROJECT_STATUS.md` from `Workspace`, from the project root above it, from a subfolder, and from a worktree under `Worktrees/` (it read the worktree's own copy before); it reads `**Phase:**`, bulleted and backticked variants of the status lines; it treats a server started with the PowerShell tool like one started with Bash. The start-folder instruction accepts the project root (`cd Workspace` first), which is where the desktop app starts sessions.
- **Programs never crash on a character the console lacks** (`→`, `≤`, `✗` crashed `scope-check`, `plan-check`, `sync-check` and `roster-check`): every program reconfigures its output with a replacement. Every subprocess call now carries the no-window flag; the bridge's own `windowless-check` passes over its programs.
- **The bridge has a committed test suite and CI**: `Workspace/tests/` (the loop guard, the roster check, the launcher, the install program and the check, the allowlist) and `.github/workflows/tests.yml` on Windows and Linux.
- Setup guide: install by program (Step 3), permissions explained instead of hand-edited (Step 6), the guardrail statements corrected (Step 7). `/calibrate-bridge` points at the install program.

**Running projects must**
- *(all phases)* Install this release with `python <release>/cursor-bridge/bridge-install.py` (never by copying files; it merges `settings.json`), restart the app, run `/calibrate-bridge`. From then on every delegation and Review B goes through `bridge-run.py` as the instructions now show, Review B with `--trust --mode ask`, and `pr-activity-check.py` runs before every merge.
- *(building, changing)* On the next checkpoint, run `python ~/.claude/cursor-bridge/roster-check.py docs/ROSTER.json` once (superseded by 2026.10.04b: the state migrates to `.git/bridge/`). Keys of paid providers (Modal, Hugging Face, OpenRouter) must not sit in `Workspace/.env` where the builder reads them: move them to the user's environment or the product's encrypted store, as the next increment of the part that uses them, and record where in the inventory.
- *(configure, building)* The video factory: add the security floor to its gate (Semgrep with the Pro engine, OSV-Scanner, Socket), pin its CI actions by commit, and move the gate to Linux runners, as the next increment. The TDP: run Semgrep's Pro engine and the bundled bridge rules in its gate, as the next increment.

---

## 2026.10.03a

**What changed**
- **KP-031: a running server is not a wake source.** `loop-guard.py` now counts a background command as something that will wake the supervisor only if it is of a kind that finishes: the builder (`cursor-agent`), the CI watch (`gh pr checks … --watch`), or a command marked with the comment `# wake`; servers, workers and probes no longer satisfy the guard. It also reads completion notices from queue records and queued-command attachments, which it had missed, so a finished task no longer counts as pending for six hours. Rule 43 states the marker. Replayed against the reAngle transcript: the old guard saw two pending tasks at the stop that stalled the loop for seven hours; the new guard sees none and would have refused the stop with its nudge. Tests: seven wake-source cases, a finished run, a background agent, and the transcript replay (in the maintainer's harness; the bridge's own test suite is release A of the restructuring plan).

**Running projects must**
- *(building, changing)* Append `# wake` to any background command you start and intend to wait for that is neither the builder nor the CI watch. Nothing else changes.

---

## 2026.10.01a

**What changed**
- **Every cost names who charges it.** When the supervisor states an amount the owner will pay (a test, a live call, a benchmark, any paid service), the platform and the account charged are named in the same sentence as the amount; several platforms charged by one action are each listed with their share. Reporting section of the supervisor's instructions and guard 7 of `explain-for-decision`. Owner-reported: a figure without its platform cannot be checked against the account's balance. Governance text only.

**Running projects must**
- *(all phases)* From the next report on, state every cost with its platform and account.

---

## 2026.09.29a

**What changed**
- **KP-030**: `~/.claude/settings.json` is shared with Claude Code, which writes its own keys into it (`switchModelsOnFlag`, `/fast`, `/effort`, `/advisor`, some approvals). A difference confined to keys the bridge does not own is not a failed install. Until `bridge-check.py` verifies only the bridge-owned entries and installation merges instead of copying (Restructuring Plan, release A), the calibration procedure compares the bridge-owned content by hand and continues with the difference recorded; the owner is never asked to remove a key the bridge does not own. Also: a vendor fact quoted to the owner is read from that setting's own documentation page. Governance text only; no program changed.

**Running projects must**
- *(all phases)* Apply KP-030 at the next `/calibrate-bridge`: if `settings.json` is the only STALE file and its bridge-owned content matches, record the exception and continue.

---

## 2026.09.27c

**What changed**
- **Diagram-based planning** (the owner's method, adopted after review). The design is a Project Design Document: `docs/DESIGN.md` plus normative Mermaid diagrams in `docs/diagrams/`. New `Diagram-Planning-Conventions.md`: an 18-kind catalogue over five levels (functional workflows; infrastructure; components; data structures; runtime logic), selected per project with every omission reasoned; three rules — top-down, Level 4-5 detail only where load-bearing (concurrency, security, integrity, performance, protocol, prior-failure), normative only if enforced (deterministic check, tests, or named review item). Notation conventions verified against the Mermaid 12.0 docs (use cases stay flowcharts because Typora bundles Mermaid 11.13; no element named `end`; spaces around links).
- **`diagram-specialist`** subagent drafts diagrams level by level (parallel kinds at once, mutually dependent pairs in one run); the supervisor integrates; `plan-critic` gains diagram lenses (selection, load-bearing detail, enforcement, meaning across diagrams).
- **`diagram-check.py`** (22 tests, including an untracked new file): index and catalogue coverage, notation per kind, refinement only upward, sequence participants against the diagrams they refine, use cases and screens traced to requirement IDs; in code mode, imports checked against the component diagram (Python, JavaScript, TypeScript), the schema dump against the entity-relationship diagram, and state machines against their tests. Step 4 of the loop runs it on every increment.
- **Explicit build plans**: every increment states Parent, Depends on, Parallel, Satisfies, Diagrams, Scope; stages are vertical slices; status is derived from `origin/main` commit subjects, so PR titles now start with the increment IDs. **`plan-check.py`** (13 tests) validates the fields and lists ready increments.
- **Parallel increments** — run parameter 5, `off` by default. With `on`, the builders of ready independent increments run at once, each in its own worktree (`cursor-agent --workspace`), committing a hand-off snapshot; the supervisor never works inside a worktree (Claude Code prompts for git in another folder and for files outside the working directory) and processes the finished branches one at a time in its own checkout. Not yet exercised on a real project.
- **Objections and bottom-up escalation**: a new section and rules 45-47; `Glossary.md` fixes the bridge's vocabulary (phase vs stage, brief vs contract, specialist vs auditor vs supervisor, objection, autonomous resolution); `/calibrate-bridge` now re-reads the conventions and the glossary. Reviewers fail design regression; the refactoring scout treats normative diagrams as constraints; the security auditor checks trust-boundary crossings drawn in data flow diagrams.

**Running projects must**
- *(all phases)* Re-read `Diagram-Planning-Conventions.md` and `Glossary.md`, and use the glossary's terms from now on.
- *(intake, design)* Design by diagram-based planning now: write the diagram index, draft with specialists, pass `diagram-check.py --mode design` before the design gate.
- *(mockups, planning)* The design gate has passed and is not reopened. Write or finish the build plan with the placement fields and vertical stages; `plan-check.py` must pass at the plan gate.
- *(building, changing)* No gate is reopened: no retroactive diagrams and no rewrite of the approved plan. New plan addenda use the placement fields; PR titles start with the increment IDs from the next pull request on; add `Parallel increments: off` to `docs/RUN_PARAMETERS.md` with a one-line notice to the owner that it can be switched on. The next change cycle's design revision builds at least the component diagram with its element map, and the entity-relationship diagram where data is stored.
- *(done)* Nothing until the next change cycle, which applies the item above.

---

## 2026.09.27b

**What changed**
- **Done is measured against the requirements, not the plan** (KP-029: SFVF shipped its specified Settings tab as a placeholder reading "Arrives in a later stage" and was declared done). New requirements register `docs/REQUIREMENTS.md` — one ID per requirement from intake, the owner's requirements document, the design, and every mockup screen and state — written at the design gate and confirmed by the owner. Increments name the IDs they satisfy; tests carry the IDs; briefs list them and forbid stand-ins; plan-critic blocks an untraced requirement; diff-reviewer fails a stand-in presented as the feature.
- **Deferral is the owner's.** A requirement becomes `deferred` or `dropped` only with the owner's dated answer; a stand-in screen is never a deferral (escalation list, Scope).
- **`completion-check.py`** (16 tests; run read-only on three real projects: it found the SFVF Settings placeholder and a 501 "not implemented yet" admin function in the documentation provider, with no false positives). `--mode plan` at the plan gate and every stage close; `--mode done` must pass before "Project complete" and runs first in every change cycle, so an inherited "done" is verified. Rule 44. Allowlisted.

**Running projects must**
- *(all phases after design)* **Build `docs/REQUIREMENTS.md` now** from the intake record, any requirements document, `DESIGN.md` (and its Change sections), and the approved mockup's screens and states; mark each row `built` (with the tests that prove it — add the ID to those tests), `planned` (and name it in a build-plan increment), or put it to the owner for a dated deferral. Present the register to the owner once as an FYI with any requirement found unbuilt.
- *(done)* Run `completion-check.py --mode done`. Every failure is a gap in the delivered product: report it to the owner plainly and open a change cycle for it unless they defer it.
- *(building, changing)* From the next brief on, briefs carry `Satisfies:`; the plan passes `--mode plan` at the next stage close.

---

## 2026.09.27

**What changed**
- **The loop no longer stalls after a green CI run** (KP-028). The Claude desktop app now tells Claude Code to register PRs with its CI monitor and not to watch CI itself, and that monitor reports failures and review comments only, never a green gate; supervisors armed auto-merge, registered the PR, ended their turn, and waited forever. Seen at least eight times in three projects from 2026-09-24. The merge step now names the mechanism: one background `gh pr checks <n> --watch --required --fail-fast` per PR, whose completion wakes the supervisor; the owner authorises it; the app's monitor is never the wake-up. While it runs, the supervisor keeps building what does not overlap the pending PR.
- **Rule 43 + `loop-guard.py` Stop hook** (registered in `settings.json`). During `building` / `changing`, a turn may end only with a background task pending or with `Awaiting user on:` naming an owner wait. The hook refuses such a stop once (exit 2, reason to the model), never twice in a row (`stop_hook_active`), never outside a bridge Workspace or in other phases, and fails open on any error; it re-reads the transcript after 2 s because the transcript is written asynchronously. Contract verified against the Claude Code hooks reference; tested on 21 cases and read-only against three real transcripts. `Awaiting user on:` semantics documented in "Project state". This is the pinned Unlazy stop-hook idea, adopted because its trigger occurred.

**Running projects must**
- *(all phases)* Make `Awaiting user on:` in `docs/PROJECT_STATUS.md` true now: `nothing` if the loop is running, otherwise the specific wait. A stale entry either lets the loop idle unseen or makes the guard nudge a session that is legitimately waiting.
- *(building, changing)* For the next PR and every one after: arm auto-merge, then start the background watch; do not end the turn to wait for the app's CI monitor.

---

## 2026.09.26

**What changed**
- **The builder reports where it guessed.** Every brief's Done section (all variants) now requires an `Assumed, not verified` list: each fact the change relies on that neither the brief nor the code settled — what, why, what would confirm it — or an explicit `none`. The run is one-shot, so the question must be in the brief; asked afterwards, a fresh session no longer knows.
- **The supervisor triages it** at step 4: copied verbatim first; a missing list is unknown, not none; each item gets one disposition — test, contract (rule 37), council, or accepted (an inventory Decisions row) — recorded in the accept commit's `Assumptions:` body. At merge the branch's lists go to Review B in `run/review/ASSUMPTIONS-<nnn>.md` beside the diff.
- **Reviewers use it as extra places to look, never as scope.** diff-reviewer checks each item and hunts unlisted ones (an unlisted external-service assumption is a `FAIL`); new anti-gaming bullet in the merge policy.
- **Least confident, at every stage close and project end** (reflection item 2b): the supervisor names its three least-sure parts with the check that settles each, in `HARDENING.md`; testable ones become tests before the next stage. Rule 42; KP-020 cross-reference.

**Running projects must**
- *(building, changing)* From the next delegation on, every brief carries the `Assumed, not verified` section (spec-packager does this); a brief already written but not yet delegated gets the section added. Triage each list at step 4 and record dispositions in the accept commit.
- *(building, changing)* At the next merge, include `run/review/ASSUMPTIONS-<nnn>.md` for Review B (increments accepted before this release have no lists; say so in the file).
- *(building, changing)* At the next stage close, run reflection item 2b.

---

## 2026.09.25g

**What changed**
- **Current-state record.** `docs/PROJECT_STATUS.md` is current position only — rewritten in place, capped at 120 lines / 12,000 characters. New `docs/INVENTORY.md` holds what the software is: Features, Resources (every environment variable, CI secret, key, account, and tool — names and locations, never values), Decisions (with reasons), Deferred. Created at the design gate, updated in the same commit as each `CHANGES.md` entry (`Reflected through:` marker), both files read whole at every start and resume (rule 20 exception). Private memory is declared not to be project state.
- **Look it up before you ask or propose.** Never ask the owner for a listed resource, never propose a listed feature, never reverse a Decision without quoting its reason and what changed. Change-cycle intake reads the inventory first; spec-packager's reality check starts from it; plan-critic blocks a plan that rebuilds, re-asks, or silently reverses.
- **`inventory-check.py`** (tested; also run read-only on two finished projects, where it flagged both status files and 11 and 15 unlisted configuration variables) at every reflection point. Rule 41, KP-027. Allowlisted.

**Running projects must**
- *(all phases)* **Build `docs/INVENTORY.md`** in the format in supervisor.md → "Project state", from what exists: the design document(s) and any "settled" or "do not relitigate" notes → Decisions, with reasons; `CHANGES.md` and the User Manual → Features; `.env` examples, the code's environment reads, CI secrets, the app's own secret store listing (names only), and anything the owner provided according to the status file, the Documents, or private memory → Resources; backlog and deferred items → Deferred. Set `Reflected through:` to the newest `CHANGES.md` heading once Features covers it.
- *(all phases)* **Shrink `docs/PROJECT_STATUS.md` under the cap**: move its current content verbatim to `docs/archive/PROJECT_STATUS-<date>.md` (nothing is deleted; the archive is never read at resume), then rewrite the status file from the template. Fold any project state held only in Claude Code's private memory into the two files.
- *(all phases)* Run `inventory-check.py` until it prints `RESULT: OK`; commit the inventory on the next branch so it reaches `main` through a PR.

---

## 2026.09.25f

**What changed**
- **Several bugs in one report are triaged before diagnosis.** New step 0 in the `root-cause-first` skill: reproduce each, compare on concrete signals (code path, trigger, component, first-bad commit), bin only on evidence with one discriminator that must move every member, split out any member that does not respond, and default to one diagnosis per bug when nothing is apparent. A confirmed group gets one fix brief (spec-packager) and one gate pass; every member keeps its own reproduction test; diff-reviewer fails a partly fixed group. Rule 26, change-cycle intake.
- **Local and remote must agree.** New `sync-check.py` (tested against a local bare remote across all seven states). Runs at start and resume, before every new branch (now cut from `origin/main`, never local `main`), after every merge (`git switch main` + `--apply`), at reflection points, and `--strict` at project end, where only IN SYNC or NO REMOTE allows "Project complete". Stranded commits on protected `main` are rescued to a branch, never deleted. New `Remote sync:` status line; the status file may stay local only uncommitted. Rule 40, KP-026. Allowlist: `sync-check.py`, `git fetch`, `git switch`.
- **Remaining pool/Grok staleness removed.** The checkpoint text still called `other_pool` owner-set and quoted Grok 4.6; KP-024, the merge policy's invariant paragraph and Review B note, and the roster-check docstring still placed "unprefixed Grok" in the Other Models pool or used Grok 4.6. All now match Cursor's documentation and the automatic switch.

**Running projects must**
- *(all phases)* Run `sync-check.py --apply` now. BEHIND is fast-forwarded; AHEAD or DIVERGED: follow the printed rescue, carry what is still needed through a PR, open an issue. Add the `Remote sync:` line to `docs/PROJECT_STATUS.md`. If the status file is committed on local `main`, it is stranded: rescue it.
- *(building, changing)* Cut every new branch from `origin/main`; after every merge `git switch main` and `sync-check.py --apply`.
- *(done)* A project already marked done runs `sync-check.py --apply --strict` once; anything other than IN SYNC or NO REMOTE is resolved and recorded as an issue.

---

## 2026.09.25e

**What changed**
- **Worktree convention** (SFVF feedback item 8). Sequential work is branches in the single
  checkout; a git worktree exists only while two branches must be live at once, lives under
  `<project-root>/Worktrees/<name>` (sibling of `Workspace/`, never inside it, never a loose
  `wt-*` folder), is recorded in `PROJECT_STATUS.md` (`Worktrees:`), removed at merge with
  the safe primitive, and checked at every reflection point (`git worktree list`). The
  boundary is now "the checkout the builder was launched in". The loop's "worktree branch"
  became "increment branch" and the Review B note no longer says the reviewer runs in a
  worktree — that vocabulary was the nudge. Rule 39, KP-025, layout section, status block.

**Running projects must**
- *(all phases)* Run `git worktree list`. Any worktree you still need moves under
  `<project-root>/Worktrees/`; every other one is removed with the safe teardown primitive
  (link check first). Add the `Worktrees:` line to `docs/PROJECT_STATUS.md`. From now on,
  no worktree for sequential increments.

---

## 2026.09.25d

**What changed**
- **Roster corrected from Cursor's documentation.** Grok 4.7 is in the *Cursor Models*
  pool ("Grok 4.7, Grok 4.6, Grok 4.5, and Composer 2.5"); the template had inferred
  "metered" from the id's shape and fallen back to Grok 4.6. Now: full profile builder
  `grok-4.7-high` / Review B `gpt-5.6-sol-high`; native profile builder `composer-2.5` /
  Review B `grok-4.7-high`. `roster-check.py` classes any Grok or Composer id as native.
  The merge policy now says pools and ids are read from the docs and `--list-models` at
  configuration, and the strongest model in each pool at that time is picked. KP-024
  addendum.

**Running projects must**
- *(all phases)* Replace `cursor-grok-4.6-high` with `grok-4.7-high` in both profiles of
  `docs/ROSTER.json` and re-run `roster-check.py`; the next delegation and Review B use the
  re-resolved ids.

---

## 2026.09.25c

**What changed**
- **Automatic return on the reset day.** `docs/ROSTER.json` gains `reset_day` (day of month,
  UTC; the owner's subscription resets on the 15th, so `16`). Exhaustion is stamped in UTC
  (automatically on a usage-limit failure, or by `--mark-exhausted` when the owner says so);
  at the first checkpoint on or after 00:00 UTC of the first reset day after that stamp,
  `roster-check.py` restores `other_pool` to available, clears the failure and unavailable
  marks, prints `AUTO-RESET`, and the preferred profile is used again — no owner action.
  `--mark-reset` still brings it earlier. `ROSTER_NOW` overrides the clock for tests
  (eight cases pass, including the 23:59 / 00:00 boundary and a same-month vs next-month
  exhaustion).

**Running projects must**
- *(all phases)* Add `"reset_day": 16` to `docs/ROSTER.json`. If the pool is currently
  marked exhausted without a UTC `exhausted_at`, set it to the date the owner reported
  (2026-09-25T00:00 UTC) so the October reset is computed.

---

## 2026.09.25b

**What changed**
- **Automatic model switch — the owner is never in the loop for it.** Every `cursor-agent`
  call sets `--model` from `docs/ROSTER.resolved.json` and captures stderr to a file. On a
  failure, `roster-check.py --record-failure <model> --stderr-file <file>` classifies it: a
  usage-limit message (or a second consecutive failure) marks the pool exhausted / the model
  unavailable in `docs/ROSTER.json` by itself (exit 3); a first non-limit failure is a
  transient retry (exit 4). On exit 3 the supervisor re-resolves the roster and **restarts
  the interrupted step from its checkpoint** with the new models — a delegation from the
  pre-delegation commit, a Review B on the same committed diff — records the stderr excerpt
  as an issue, and puts the switch in the next report's first line. Only the return to the
  preferred profile waits for the owner's "usage reset". Phase 6 step 3b; rule 38; KP-024.

**Running projects must**
- *(Phase 6)* Add `--model <builder>` from `docs/ROSTER.resolved.json` and
  `2> run/agent/TASK-<nnn>.err` to the delegate command; the same for Review B launches
  (`run/review/REVIEW-<nnn>.err`); gitignore `run/agent/`. Apply step 3b from the next
  failure on.

---

## 2026.09.25

**What changed**
- **Roster profiles and the owner-set pool state.** `docs/ROSTER.json` now lists
  **profiles** tried in order — *full* (builder Cursor-hosted Grok 4.6, Review B GPT-5.6
  Sol) and *native* (builder Composer 2.5, Review B Cursor-hosted Grok 4.6; roles swapped so
  the stronger native reasoner reviews) — plus `other_pool: available | exhausted`, set by
  the owner because a probe cannot see a nearly-empty quota (the owner's pool stood at 99%
  used while a one-word call still answered). `roster-check.py` skips profiles that need
  the exhausted pool, probes the rest through the real CLI (refusal / empty / timeout =
  unusable), verifies three families, writes `docs/ROSTER.resolved.json`, and the delegate
  and Review B commands read their model ids from it. Family mapping fixed: `cursor-grok-*`
  is xAI hosted by Cursor, not Cursor's own family. KP-024; rule 38.

**Running projects must**
- *(all phases)* Rewrite `docs/ROSTER.json` to the two-profile template with
  `"other_pool": "exhausted"` (the owner's pool is exhausted as of 2026-09-25), run
  `roster-check.py`, and switch the delegate and Review B commands to read
  `docs/ROSTER.resolved.json`. Report in the first line that the native profile is in use.
  When the owner says "usage reset", set `other_pool` to `available`.

---

## 2026.09.24b

**What changed** — from the SFVF Bridge Feedback document (Stage P).
- **External services: contract capture, never an invented mock.** The first increment on
  any third-party API/SDK is an attended live call recorded to fixtures the tests replay;
  "done" means passing against recorded real responses. Brief constraint; plan-critic
  Blocking; diff-reviewer FAIL on a builder-written mock. Standing rule 37; KP-020.
- **Test-infrastructure lane in the stage-close pass.** The supervisor consolidates its own
  test helpers in a separate commit on the same branch; `refactor-check.py --lane tests`
  asserts no production file changed; the collected test set must be identical before and
  after. Same one gate pass.
- **Reviewers review the design a diff embodies**, not only fidelity to the brief; a flawed
  brief is a finding (diff-reviewer, security-auditor).
- **Redact by pattern, never blank by status** (`secure-coding.snapshot.md` V15;
  security-auditor; KP-021).
- **Teardown: a real, briefly locked environment** is retried then deferred, never forced
  (configuration §1; KP-023).
- **Model roster is checked**: `docs/ROSTER.json` + new `roster-check.py` (three distinct
  families; delegate command sets `--model <builder>`) at configuration, calibration, and
  every checkpoint. Standing rule 38; KP-022.

**Running projects must**
- *(all phases)* Create `docs/ROSTER.json` from the merge policy's roster and run
  `roster-check.py` now; fix the delegate command if it lacks `--model`.
- *(Phase 6, projects with external integrations)* For each adapter whose tests replay a
  builder-written mock: add a contract-capture increment (an addition to the plan — tell the
  owner in one line; needs the service key once) and re-point the tests at the recorded
  fixtures before the next increment on that adapter.
- *(Phase 6)* The next stage-close pass may run the tests lane; the next brief carries the
  external-fixture constraint; reviewers apply the design lens from the next diff.

---

## 2026.09.24

**What changed** — from the first Bridge Feedback document to come through the channel
(Technical Documentation Provider, three stage closes).
- `scope-check.py` strips a trailing annotation from a scope entry (`path (new)`,
  `path - note`, `path # note`) instead of reading it as a different path (false drift).
- New `lock-check.py`: a dependency-manifest change without its lockfile change fails at the
  admission gate and in `secret-sentinel` before any reviewer — an *expected-file-missing*
  check reviewers cannot perform (ISS-004, KP-018).
- The reviewer's diff is generated only from committed state and lives inside the workspace
  at `run/review/REVIEW-<nnn>.diff` (committed on the branch, removed before merge) —
  never a working-tree diff (omits untracked new files, KP-017), never a temp path outside
  `Workspace/` (the boundary blocks it, KP-016 / ISS-003). Standing rule 36.
- `spec-packager` runs a **reality check** before every brief: what the increment assumes
  must exist as built; a mismatch returns as a scope question (KP-019).
- **Convergence is a signal:** two or more reviewers naming the same line is blocking even
  if each called it advisory (merge policy; step 8).
- The design records a **migration policy** (pre-release rebuild vs shipped migrations);
  plan-critic checks it.
- KP-016–KP-019 (artifacts outside the workspace; untracked-file diffs; lockfile; plan vs
  data, and CI event lag: poll the head SHA patiently, never stack empty commits).

**Running projects must**
- *(all phases)* Move any loop artifact written outside `Workspace/` (reviewer diffs,
  resolution files, captures) to its in-workspace path; from now on generate reviewer diffs
  from committed state only.
- *(Phase 5 or later)* Record the project's lock command and lockfile in `PROJECT_STATUS.md`;
  `lock-check.py` runs at the next dependency admission.
- *(Phase 6)* The next brief goes through the reality check; the next split or advisory
  convergence follows the new rule.
- *(Phase 2 not yet passed)* Add the migration policy to the design; *(later phases)* record
  the regime in `PROJECT_STATUS.md` at the next reflection point.

---

## 2026.09.22c

**What changed**
- **`Performance-Patterns.md`** — the bridge's catalogue of recurring causes of slowness
  and cost, in Known-Pitfalls' discipline: fixed entry shape (pattern, symptom, fix,
  measure, applies to, evidence), nine seeded entries `PP-001`–`PP-009` (N+1 calls, full
  scans, recomputation, synchronous IO on hot paths, unbounded growth, large-object
  serialization, interface-thread work, per-item model calls, eager startup), admission
  rule (recurs across projects, not covered, measurable), promotion from optimization
  commits with their numbers. Three readers wired: `plan-critic`'s performance lens names
  the `PP-nnn` a design walks into; `refactor-scout` uses the symptom column as its search
  list and names the entry (or `PP-new`) per candidate; the supervisor writes a failing
  benchmark's corrected brief from the named pattern's fix. Promotion pass proposes entries.
  Rule 15 extended.

**Running projects must**
- *(all phases)* Nothing to change in the project; the readers pick the catalogue up at
  their next use.

---

## 2026.09.22b

**What changed**
- **Optimization is measured or it does not exist.** New `Performance-Conventions.md`:
  owner-set **budgets** at intake (`bench/budgets.json`: one operation, one condition, one
  number, one measurement; speed, memory, size, and money/tokens alike; "no budgets" is an
  answer); the design names the **mechanism and hot path** per budget (plan-critic
  performance lens: scaling, per-item calls, unbounded growth, thread blocking,
  measurability); a **benchmark increment per budget** before any optimization; the
  **benchmark floor** — fixed dataset and seed, median of ≥5 runs, committed
  `bench/baseline.json`, new `bench-check.py` (OVER BUDGET / REGRESSION / NOT MEASURED
  fail; IMPROVED noted; `--update-baseline` only in optimization commits; tested) in the CI
  gate and at stage close; the stage-close pass gains a **performance lens**
  (`refactor-scout` ranks optimization candidates by measured impact on a budgeted metric)
  under the same one-branch one-gate mechanics, every optimization commit carrying its
  before/after numbers and moving the baseline; **anti-gaming**: loosening a budget, moving
  the baseline outside an optimization commit, deleting/skipping a benchmark, shrinking its
  dataset, or measuring warm where cold was stated is a gate-integrity flag. Configuration
  §5e. Standing rule 35.

**Running projects must**
- *(Phase 6 — building, or done)* At the next reflection point, propose budgets to the owner
  for the operations whose speed or cost they care about (a decision brief; "none" is a
  valid answer). If budgets are set: add the benchmark increments and the `bench-check.py`
  gate step as an addition to the plan (tell the owner in one line; reopens no gate), commit
  a baseline, then the performance lens applies from the next stage close.
- *(Phases 1–5)* Budgets are asked at intake going forward; a project already past intake
  asks them at its next gate as one extra decision.

---

## 2026.09.22

**What changed**
- **The change cycle.** A request on a finished project (`Phase: done`) runs the same
  workflow scaled to the delta: intake of the change (impact on existing behaviour; this
  project's own Issues file in place of prior-project lessons), a dated **Change:** section
  in `docs/DESIGN.md` with plan-critic on the delta, mockups only for touched screens, a
  plan addendum of new stages with a version bump and the Packaging & installer stage
  re-run last, run parameters kept, configuration only for new tooling, the loop, project
  end again with the manual patched and the deliverable rebuilt. Same three gates, no
  others. `Phase: changing` + `Change cycle:` in `PROJECT_STATUS.md`. Standing rule 34;
  plan-critic checks the addendum.
- **A process question is never the owner's.** "Should I follow the workflow for this?"
  is settled by the governance; where it is silent, the supervisor follows the closest
  defined procedure, says which, and records the gap as bridge feedback. Cause: a
  finished project's supervisor asked the owner whether a minor design change should go
  through the workflow.

**Running projects must**
- *(Phase: done, a change request pending or already being discussed)* Treat the request
  as a change cycle from step 1; nothing discussed so far is lost — fold it into the change
  intake summary and confirm it.
- *(all other phases)* Nothing.

---

## 2026.09.21d

**What changed**
- Inno Setup is a **standard machine prerequisite** of the bridge (setup guide Step 10),
  not a desktop-only optional step. `Delivery-Conventions.md` §2.1 tells the supervisor to
  locate `ISCC.exe` in both possible folders (per-user winget install under
  `%LOCALAPPDATA%\Programs\Inno Setup 6\`, all-users under `%ProgramFiles(x86)%`), record
  the resolved path, and hand the owner the Step 10 run sheet if neither exists.

**Running projects must**
- *(all phases)* Nothing.

---

## 2026.09.21c

**What changed**
- **Project end is a defined trigger.** The close of the approved plan's last stage *is*
  project end: the project-end items (final refactoring pass, User Manual, promotion pass,
  installer delivery) run in the same turn as that stage close, `Phase: done` is set, and
  the report opens with "Project complete". Deferred increments do not postpone it. The
  procedure existed since 2026.09.20 but had no trigger, so a finished project (Technical
  Documentation Provider, 2026-09-21) closed its last stage and never produced its manual.
  Standing rule 33; plan-critic checks the last stage is named.
- **Delivery broadened from desktop apps to all installable software.**
  `Packaging-Conventions.md` → `Delivery-Conventions.md`: §1 which kind ships what; §2 the
  desktop installer (unchanged); **§3 command-line tools and local servers** — a
  double-clickable `install.cmd` + `install.ps1` that checks prerequisites, builds an
  isolated environment from the lock file under `%LOCALAPPDATA%\Programs\<Name>`, puts the
  command on the user PATH via a launcher, registers an Apps & features entry and an
  uninstaller, offers Upgrade / Uninstall / Cancel when already installed, keeps data on
  uninstall, supports `-Silent`; the project writes its own `scripts/install-check.ps1`
  lifecycle test. Run parameter 4 applies to all installable kinds. Standing rule 31.
- **Command reference — never a made-up command again.** A project with a CLI keeps
  `docs/cli-reference.json`, generated from the real command tree by `scripts/dump-cli.py`
  in the increment that first adds a command, kept current by a CI diff check and the
  pre-commit gate; `diff-reviewer` fails a command change without a reference change;
  every run sheet, report, and manual passage copies commands from it or from a `--help`
  just run. Cause: the same project's supervisor instructed the owner with commands that
  did not exist. Standing rule 32; run-sheet rule; plan-critic check.

**Running projects must**
- *(Phase 6 — building, last stage already closed without a project-end reflection)* Run
  the project-end items now: final refactoring pass (if on), User Manual, promotion pass,
  deliverable; set `Phase: done`; report "Project complete" with deferred items listed.
- *(all phases, projects with a command-line surface)* Add the command-reference generator
  and its CI currency check as an increment in the current or next stage (an addition to
  the approved plan — tell the owner in one line; reopens no gate). Until it exists, run
  `--help` before every instruction that names a project command.
- *(all phases, installable software of any kind)* If the plan has no "Packaging &
  installer" last stage, add it (tell the owner in one line). Ask `Installer verification`
  if not yet in `docs/RUN_PARAMETERS.md` (default `local`).
- *(all phases, other projects)* Nothing.

---

## 2026.09.21b

**What changed**
- **Desktop applications ship as an installer.** New `Packaging-Conventions.md`: Windows 11
  x64, one `dist/<Name>-Setup-<version>-x64.exe`, per-user by default (no UAC), registered
  in Apps & features with a working uninstall, **upgrade in place** keeping user data,
  the installer offering Upgrade / Uninstall / Cancel when already installed, uninstall
  keeping data unless opted out, one-command build, single version source, unsigned by
  default (code signing is the one Phase-2 escalation). Toolchain per stack (Electron /
  Tauri bundlers; Inno Setup for .NET, Python, Rust, Go, C++) with a committed Inno
  template. New `installer-check.ps1` proves install / smoke / upgrade-in-place / uninstall
  silently and reversibly. Intake captures it; Phase 2 designs it; the plan's last stage is
  "Packaging & installer" (plan-critic blocks a desktop plan without it); a fourth run
  parameter `Installer verification` (`local` default / `ci-only`); project end delivers
  the installer and the manual's install chapter. Standing rule 31.

**Running projects must**
- *(all phases, desktop applications only)* If the plan has no "Packaging & installer"
  stage, add it as the final stage — this is an addition to the approved plan, so tell the
  owner in one line; it reopens no gate. Add `Installer verification` to
  `docs/RUN_PARAMETERS.md` (ask; default `local`). Add the Packaging & distribution
  section to `docs/DESIGN.md` at the next reflection point, and raise the code-signing
  question once.
- *(all phases, other projects)* Nothing.

---

## 2026.09.21

**What changed**
- **One Issues document.** `docs/LESSONS.md` is gone. The project's record of issues,
  misconceptions, causes, and fixes is the single
  `Documents/<Name> Issues During Development and Their Solutions.md`, written by the
  supervisor **for the next project's supervisor (an AI)**, one entry per `ISS-nnn`,
  `generalizable: yes` marking Known-Pitfalls candidates. The human reads the Project
  Summary instead.
- **Builder channel widened.** `docs/BUILDER_NOTES.md` now carries both tooling friction
  (→ Bridge Feedback) and anything the builder learned about a defect or pitfall (→ the
  Issues file); the supervisor sorts it at every reflection point.
- **No hard line wraps** in any Markdown the supervisor or the builder writes: one
  paragraph is one line; breaks only between blocks (rule 30; brief constraint;
  `workspace-boundary.mdc`).
- The User Manual at project end was already in place (Reflection points → project end);
  no change, restated for clarity.

**Running projects must**
- *(all phases)* If `docs/LESSONS.md` exists, fold each entry into the Documents Issues
  file under its `ISS-nnn` at the next reflection point, then delete `docs/LESSONS.md`.
- *(all phases)* Write without hard wraps from now on; do not reflow existing files
  mid-stage (a reflow is a noisy diff); the Documents may be reflowed at the next
  reflection point.
- *(Phase 6 — building)* The next brief carries the widened `BUILDER_NOTES.md` line and
  the no-wrap constraint (spec-packager template).

---

## 2026.09.20d

**What changed**
- **Run parameters** — asked once, together, right after the plan is approved and before
  configuration; recorded in `docs/RUN_PARAMETERS.md`: `Stage pause` (`run` default:
  report a stage close and continue in the same turn; `pause`: wait for "continue"),
  `Merge authority` (`supervisor` default; `owner`: stop at READY TO MERGE, never arm
  auto-merge), `Refactoring pass` (`on` default; moved here from the plan gate). The
  escalation list and the gate are unchanged under every setting. Standing rule 29;
  plan-critic no longer checks a dial in the plan.

**Running projects must**
- *(Phase 6 — building)* Ask the three run parameters at the next stage close or, if the
  loop is between increments, now — as one decision brief; this is the one decision line
  of the calibration report. Until answered, keep the behaviour the project has had
  (`Stage pause: pause`, `Merge authority` as the repo is set up, `Refactoring pass: on`),
  and say so. Write `docs/RUN_PARAMETERS.md` from the answers.
- *(Phase 4 — planning, plan not yet approved)* Nothing extra: the step follows the plan
  gate as written.
- *(Phase 5 — configuration)* Ask the run parameters before continuing configuration.

---

## 2026.09.20c

**What changed**
- `/calibrate-bridge` takes no argument. The `check` keyword was redundant: the command is
  the check. Run in a folder with no `docs/PROJECT_STATUS.md`, it verifies the install,
  re-reads the governing files, reports "no project in this folder", and stops.

**Running projects must**
- *(all phases)* Nothing.

---

## 2026.09.20b

**What changed**
- `/supervisor` takes no keywords. New vs resume is decided solely by whether
  `docs/PROJECT_STATUS.md` exists; text after the command is the seed description of a new
  project (or a message to a resumed one). `new` and `resume` were removed from the
  argument hint — `new` never had a distinct meaning, and `resume` duplicated the file check.

**Running projects must**
- *(all phases)* Nothing. Type `/supervisor` to resume, as before; the word `resume` is
  simply no longer needed.

---

## 2026.09.20

First stamped release. Covers everything since the observability integration (commit
`c34b235`) up to and including the calibration mechanism itself.

**What changed**
- `explain-for-decision` skill (rule 21) and the **run sheet** section (rule 27).
- Fixed project layout `<id>-<name>/Documents` + `/Workspace`; Workspace boundary
  (`workspace-boundary.mdc` + `boundary-check.py` hook); the four human-facing Documents;
  reflection points; issue IDs `ISS-nnn` (rules 22–23).
- Windowless-by-default policy (`run-hidden.py`, `windowless-check.py`, KP-014, rule 24).
- Phase 4 step 0 — prior-project lessons from an earlier project's Issues file.
- Stage-close refactoring pass (`refactor-scout`, `refactor-check.py`, rule 25).
- Root-cause-first debugging (`root-cause-first` skill, `BUG-nnn` fix briefs, OBSERVED /
  INFERRED diagnoses, KP-015, rule 26).
- `/calibrate-bridge`, `bridge-check.py`, `VERSION`, `MANIFEST.json`, this file (rule 28).
- Earlier in the same span: minimal-code rule, context-economy boundary, scope-check,
  constant-pointer delegation, safe worktree teardown, reviewer routing table.

**Running projects must**
- *(all phases)* Add to `docs/PROJECT_STATUS.md`: `Bridge version:`, `Software name:`,
  `Layout:`, `Terms fixed:`, `Stage:`, `Open issues:` (see the supervisor's Project state
  template). Resolve `../Documents`; create it if missing.
- *(all phases)* Confirm the folder pair: the supervisor runs in `Workspace/`. If the
  project predates the layout and the repo root is not named `Workspace`, do **not** move
  anything — record the actual paths under `Layout:` and treat the repo root as the
  Workspace boundary; the rename is the owner's call, offered once as a run sheet.
- *(Phase 2 passed)* Create `Documents/<Name> Project Summary.md` at the next reflection
  point if it does not exist.
- *(Phase 4 — planning)* If the build plan is not yet approved: run step 0
  (prior-project lessons) and add the per-stage **refactoring dial** before presenting.
  If the plan is already approved: group existing increments into stages if they are not,
  set the dial to **on** for remaining stages, and tell the owner in one line that they may
  switch it off — do not re-present the plan.
- *(Phase 5 — configuration, or later)* Via `cursor-configurator`, **append** what is
  missing: `.cursor/rules/workspace-boundary.mdc`, `.cursor/rules/minimal-code.mdc`, the
  `boundary-check` hook entry + script, `run-hidden.py` + `windowless-check.py`, the
  windowless idiom in every existing hook script, `run-hidden.py` on every direct-command
  hook entry, the windowless check in `.githooks/pre-commit`. Never overwrite `hooks.json`.
  Verify once with a throwaway edit while watching the desktop.
- *(Phase 6 — building)* From the next increment: `scope-check.py` at Inspect,
  `BOUNDARY_VIOLATIONS.md` read at Inspect, the routing table, the root-cause-first
  procedure on the next defect, the refactoring pass at the next stage close, the
  reflection point at the next stage close. An increment already delegated finishes under
  the brief it has; the next brief uses the current spec-packager template.
- *(all phases)* Nothing already approved is re-presented. No gate is reopened.

---
