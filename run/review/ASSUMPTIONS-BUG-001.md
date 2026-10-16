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

