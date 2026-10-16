BUG-001: remove round 5's review files

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>

BUG-001: records after PR #21's round 5 (records only)

docs/DESIGN_CRITIQUE.md: round 5's record; a workflow change regenerates WORKFLOW_PIN in the same diff (TASK-006). docs/HARDENING.md: the pattern checks' place under the whole-workflow pin.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>

BUG-001: pin the whole workflow; no job passes secrets on (supervisor, PR #21 round 5)

Round 5 (Review B Blocking twice, Review A Should fix and Consider: converged): the job pin left the workflow's top level open, so a workflow-level defaults run.shell of 'true {0}' skipped the Socket step with every test green, and a reusable-workflow job with secrets: inherit passed the one-secret rule. test_r002_workflow_is_the_pinned_one now pins the whole workflow verbatim (FLOOR_JOB is its security-floor job); the one-secret rule refuses a job that passes secrets on. The deferral docstring says its either-order rule differs from completion-check's register convention.

Mutation driver: 56 mutants, all killed by the named assertion. Stage tests 30; full suite 951 passed, 20 skipped.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>

BUG-001: review files for round 5 (diff, delta, scope, assumptions)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>

BUG-001: remove round 4's review files

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>

BUG-001: records after PR #21's round 4 (records only)

docs/DESIGN_CRITIQUE.md: round 4's record, the reviewers' disagreement and the supervisor's decision to pin the floor job. docs/HARDENING.md: the pattern checks' remaining reach.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>

BUG-001: pin the security floor job verbatim; one step may hold a secret (supervisor, PR #21 round 4)

Every round since stage B1's review found new ways past the pattern checks of shell inside YAML (round 4, Review B: an early `exit 0` in the Semgrep step, `code=0` after OSV's status, a secret handed to a third-party action, `npm --prefix /x install` beside the key), while the CI change itself was approved each time. The reviewers disagreed on whether such bypasses block (a correctness crux, settled by the supervisor): the floor is now pinned instead of pattern-matched.

- test_r002_floor_job_is_the_pinned_one: the `security floor` job equals a committed copy, every step verbatim; a skipped scanner, an overwritten status or an added step fails unless the same diff changes the pin, where both reviewers read it.
- test_r002_one_step_holds_a_secret: exactly one step in the whole workflow refers to a repository secret, the Socket scan.
- The pattern checks stay as a second line, tightened: chained commands split at `&&`, `||`, `;`, `|` (Review A Should fix: a second install after `&&`); npm options with a separate value, `cit`, `update`; expression names case-insensitive and `github['token']`; the job token kept apart from the step-env rule, so `with: token: ${{ github.token }}` stays allowed (Review A Should fix); the env docstring says `true` or `1`.
- A deferral names the owner and a date in either order.

Mutation driver: 53 mutants, all killed, a kill counted only when the named assertion fired (Review A Should fix: three had been killed by the version pin). Stage tests 29; full suite 950 passed, 20 skipped.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>

BUG-001: review files for round 4 (diff, delta, scope, assumptions)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>

BUG-001: remove round 3's review files

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>

BUG-001: records after PR #21's round 3 (records only)

docs/DESIGN_CRITIQUE.md: BUG-001 round 3's record and disposition, and the correction of round 2's overstatement (this project narrows the Deferred template).

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>

BUG-001: restore the secret check's reach and read continued commands whole (supervisor, PR #21 round 3)

- The secret pattern reads each `${{ }}` expression to its closing `}}`, so `${{ format('{0}', secrets.X) }}` counts again (round 3's pattern stopped at the first `}` and missed what main's substring check caught: a weakening; Review B Blocking, Review A Should fix); it keeps the bare `secrets.X` / `secrets['X']` form and adds `github.token`.
- Commands are read with backslash continuations joined, so `--ignore-scripts` followed by `--ignore-scripts=false` on a continued line fails (Review B Blocking, Review A Consider).
- `--ignore-scripts false` (npm reads a bare value after a boolean flag) is refused; an env setting npm's ignore-scripts config fails only when its value is not `true`; npm options before the command, `npm exec`, `npm it` are recognised.
- A Deferred row's decision cell may read `no — the owner, <date>`; the docstring says this project narrows the template (an open question waits on the Awaiting line).

Self-tests for each new form. Mutation driver: 47 mutants, all killed by an assertion. Stage tests 26; full suite 947 passed, 20 skipped.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>

BUG-001: review files for round 3 (diff, delta, scope, assumptions)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>

BUG-001: remove round 2's review files

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>

BUG-001: records after PR #21's round 2 (records only)

docs/DESIGN_CRITIQUE.md: BUG-001 round 2's record and disposition. docs/HARDENING.md: the npm lead's settle changes the pin test with it.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>

BUG-001: close the stage tests' remaining bypasses after PR #21's round 2 (supervisor)

- npm: the install line's one mention of the setting must be the bare `--ignore-scripts` (`--ignore-scripts --ignore-scripts=false` passed while npm takes the last; Review B Blocking, Review A Consider: converged); no env at any level sets npm's ignore-scripts config; npm's install and clean-install aliases are all checked.
- Secrets: the pattern matches any expression reading the secrets context, `${{ toJSON(secrets) }}` included (Review A Should fix).
- Deferred rows follow the template (`<yes — the question · no>`) and completion-check's owner-dated convention: a deferral reads `no` and names the owner with a date; an open question, even one naming the owner and a date, fails (Review A Should fix and Consider).
- Install pattern: `uvx`, `pnpm dlx`, `yarn dlx`, `bunx`; a self-test of the secret and install patterns (Review A Considers).

Mutation driver: 41 mutants, all killed by an assertion (a crash no longer counts as a kill). Stage tests 25 passed; the tests reading the records and the workflow 227 passed.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>

BUG-001: review files for round 2 (diff, delta, scope, assumptions)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>

BUG-001: remove round 1's review files

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>

BUG-001: records after PR #21's review (records only)

docs/HARDENING.md: the npm lead says the CLI's unpinned dependencies run with the key at scan time (BUG-001 closed install time only; Review A Should fix), the runner-image date marked unconfirmed. docs/PROJECT_STATUS.md: names PR #21 and what lives in run/supervisor/. docs/DESIGN_CRITIQUE.md: the three logs' wording (Review B) and BUG-001 round 1's record.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>

BUG-001: tighten the stage tests after PR #21's review (supervisor)

Both reviewers approved PR #21; two findings converged and are taken as blocking, the rest as cheap fixes:
- `--ignore-scripts` matched as a whole flag (`--ignore-scripts=false` passed; converged).
- A deferral needs the owner named with a date in its decision cell (any date in the row passed; converged).
- A secret found in any expression form, `secrets.X` and `secrets['X']`, in the placement and install tests (Review B).
- The install pattern covers `npm ci`, `npx`, `pip3`, `uv`, `go`/`gem`/`cargo install` (Review A).
- The Socket CLI held at its recorded 1.7.0 (Review A).
- `pull_request` must run on open, update and reopen (`types: [closed]` passed; Review B).

Mutation driver (run/supervisor/mutate_ci_floor.py): 35 mutants, all killed, six new for these checks. Stage tests 24 passed.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>

BUG-001: review files (diff, scope, assumptions)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>

BUG-001: records after stage B1's review (records only)

- docs/PROJECT_STATUS.md: current and self-sufficient (it was stale on main, describing PR #16 as unmerged; both stage reviewers, Blocking): last accepted TASK-002 fba63bc, BUG-001 in flight, the owner's run sheet (three logs, key replacement) on Awaiting, ISS-002 closed, the conformance NOTEs, no reliance on the gitignored position file.
- docs/INVENTORY.md: the required check (owner, 2026-10-13); the Socket install without the key (BUG-001); Socket reads requirements.lock (its supported-file list); the full-tree Semgrep audit of 2026-10-16 with its one accepted finding; forks get no secrets; the --no-banner row reworded (the 5 characters are of the key's secret part) with its remedy; the key's replacement asked.
- docs/DESIGN_CRITIQUE.md: TASK-002's last rounds (002c, r6) and stage B1's review round 1.
- docs/HARDENING.md (new): stage B1's least-confident three with their checks, the review's leads, stage B2's carried test-lane items.
- docs/REQUIREMENTS.md: R-002's evidence names its merge commit and BUG-001.
- project.json: stage B1 (closing), updated 2026-10-16.

inventory-check OK; every test that reads these records passes (210).

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>

BUG-001: run the roster-check tests from their own folder (ISS-006, test lane)

tests/test_roster_check.py ran roster-check.py with pytest's working folder, the Workspace, so its default run log (run/launcher/runs.jsonl, relative to the working folder) was the Workspace's live log. After BUG-001's builder run on grok-4.7-medium, the log's last builder was of the xai family, the native profile's Review B (grok) was refused as the builder's family, and test_state_survives_a_reset_of_the_working_tree failed with "no usable profile". CI has no run log and never saw it. The helper now runs the program from the temporary roster's folder. Test-only change; no production file.

Full suite: 945 passed, 20 skipped.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>

BUG-001: install the Socket CLI in a step without the key

The `Socket` step of the security floor held SOCKET_CLI_API_TOKEN in its step-level env while it ran `npm install -g @socketsecurity/cli@1.7.0`, so the key was in the environment of the package's and its unpinned dependencies' install. Found by stage B1's review (Review A Should fix, Review B Consider; converged). The CLI is now installed in its own step `Install the Socket CLI`, with no env and `--ignore-scripts`; the `Socket` step keeps its env and runs only `socket ci --no-banner`.

Builder: grok-4.7-medium (run 2026-10-16T16:21:22Z). Scope CLEAN. The supervisor's tests (d26d082) pass: stage tests 24, full suite 945 passed / 20 skipped; mutation driver 29/29 killed; secret-sentinel CLEAR.

Assumptions:
- builder's list: "none" (the list is thin; the supervisor adds the item below)
- `npm install -g --ignore-scripts` still links the `socket` command on the runner -> contract: proven by this pull request's CI run (the Socket step scans)
- @socketsecurity/cli 1.7.0, @socketsecurity/socket-patch 2.0.0 and form-data 4.0.6 declare no install scripts -> verified with npm view (2026-10-16)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>

checkpoint before BUG-001 (fix brief: the Socket key absent while npm installs the CLI)

BUG-001: tighten the stage B1 tests (supervisor, stage review findings)

Stage B1's review (Review A and Review B, 2026-10-16) found the stage's two tests too weak:
- test_release_b_bootstrap.py: the Deferred check passed with an open row beside "(none)" and would fail on any legitimate dated deferral (TASK-027 plans one); it now parses the rows, fails on a row about a settled decision (R-038, the second checkout) or a deferral without a dated owner approval; project.json's phase is compared with the status file's.
- test_release_b_ci_floor.py: the triggers (pull_request, push to main, no path filters), each scanner's exit status deciding its step (Semgrep's last line, OSV's lockfile argument and exit "$code", the Socket step running only `socket ci --no-banner`), no install or fetch in a step holding a secret and npm install with --ignore-scripts, the lock's exact admitted closure, `; true` / `; exit 0` in the disabler guard, --no-banner checked in every job, the V14 citation.

Two tests fail on purpose until BUG-001's workflow fix: test_r002_each_scanner_decides_its_step and test_r002_no_install_runs_beside_a_secret (the Socket key is in the environment while npm installs the CLI).

Assumptions:
- Socket's scan reads requirements.lock -> settled: api.socket.dev/v0/report/supported lists the PyPI pattern requirements{.bazel,}.lock (2026-10-16)
- @socketsecurity/cli 1.7.0 and its direct dependencies have no install lifecycle scripts -> verified with npm view (2026-10-16); --ignore-scripts is safe

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>

release B: resumed 2026-10-16 (usage reset, full roster); stage B1 close begins

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>

