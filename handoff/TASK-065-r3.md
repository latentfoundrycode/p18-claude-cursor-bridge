---
record: brief
header: 1
id: "TASK-065"
round: 3
satisfies: [R-085]
scope: ["bridge/cursor-bridge/bridge-run.py", "bridge/cursor-bridge/MANIFEST.json", "tests/test_bridge_run.py", "docs/BUILDER_NOTES.md", "handoff/TASK-065-r3-report.md"]
merge_unit: null
blocking_class: "behaviour"
---
# TASK-065 round 3: the watch starts early only for a failure gh will report (R-085)

Round cause: defect - bridge/cursor-bridge/bridge-run.py:2296-2297 with 2171-2175, under the base's list the early start reads only the first failed latest check, so a failed check the rule names that is listed after one it does not name never starts the watch (Review A, round 2, BLOCKING 1); defect - bridge/cursor-bridge/bridge-run.py:2296-2297, a check concluding neutral or cancelled starts the watch early, though gh puts neutral in its skipping bucket and cancelled in its cancel bucket and exits 0 for both, so the watch returns before the jobs that need security floor are listed, the field's case F2 again (security audit, round 2, BLOCKING 1); defect - bridge/cursor-bridge/bridge-run.py:3082-3090, on Windows the child's timeout path ends the launcher's own process before it removes the pid file, so the file is left behind (Review A, round 2, SHOULD FIX 1)

Blocking class: behaviour - against the brief and the register (R-085, "A CI watch never returns before CI has run"): reproduced in process on round 2's tree by the supervisor's round-3 cases (`wait-checks-lint-failed-first.json`: lint's failed job listed before security floor's failure, no watch started at once; `wait-checks-floor-neutral.json` and `wait-checks-floor-cancelled.json`: the watch started at once under both lists), the gh side read in gh's source (cli/cli, `pkg/cmd/pr/checks/aggregate.go` and `checks.go`)

## Objective
Fix the following confirmed defects in the launcher's wait before a CI watch, and nothing else.

This is round 3 of TASK-065, the last round the review ceiling allows. Rounds 1 and 2 built `WATCH_POLL`, `watch_loop` and its helpers, and `main()`'s watch block; all of that stays except what H1 to H3 below change. The supervisor commits round 2's tree together with this brief and the new tests before your run, so the line numbers below hold when you start.

**The confirmed defects:**
- H1. `_failed_check` (2171-2175) returns the first latest check `ci_class` calls failed, and `_watch_decision` (2296-2297) applies round 2's G4 to that one check alone. Under the base's list, where a failed check no rule names (lint's job of a second workflow) is listed before a failed check the rule names (security floor), the wait goes on instead of starting the watch at once.
- H2. The early start takes every check `ci_class` calls failed, and `ci_class` calls failed every completed conclusion but `success` and `skipped`. gh pr checks (cli/cli, `pkg/cmd/pr/checks/aggregate.go`) buckets a check by its state: `SUCCESS` pass; `SKIPPED` and `NEUTRAL` skipping; `ERROR`, `FAILURE`, `TIMED_OUT` and `ACTION_REQUIRED` fail; `CANCELLED` cancel; every other state (`STARTUP_FAILURE`, `STALE`, the pending ones) pending. `checks.go` ends a `--fail-fast` watch early only on the fail bucket, ends `--watch` as soon as nothing it lists is pending (a job not yet listed is not counted), and exits non-zero only for fail (1) or pending (8). So a watch started for a neutral or cancelled check returns 0 once security floor completes, before the bridge programs jobs that need it are listed.
- H3. On Windows the child's timeout path calls `killer()` (3083), which ends the launcher's own process through its job object, before `remove_pid_file(box["pid_file"])` (3090). The pid file is left behind, against round 2's G2 ("No pid file is left after the run").

**The reproduction tests:** `tests/test_program_watch_wait.py`, the section headed `# ================================================================ round 3: the supervisor's case after round 2's Review A`. On round 2's tree the result is quoted under Constraints, "Known failures"; every case in the file must pass.

Satisfies: R-085 - A CI watch never returns before CI has run (F2, both cases, and J6): before any `gh pr checks <n> --watch`, with `--required` or without, the launcher waits, inside the run's own limit, until every required check context of the pull request's base branch has a check or a commit status on the pushed head or a check of that head has failed, then starts the watch as given and prints what it waited for; [...]. (Full text: its row in `docs/REQUIREMENTS.md`. This round serves "or a check of that head has failed" as gh reads a failure, so that the watch it starts reports it.)

## Scope
Files you may create or modify:
- bridge/cursor-bridge/bridge-run.py
- bridge/cursor-bridge/MANIFEST.json
- tests/test_bridge_run.py
- docs/BUILDER_NOTES.md
- handoff/TASK-065-r3-report.md

Limits on these files:
- `bridge/cursor-bridge/bridge-run.py`: only `_failed_check` (2171-2175), the first two lines of `_watch_decision`'s body (2296-2297) with its docstring, one new module constant beside `WATCH_POLL` (H2), and in `main()`'s watch block the child's timeout path (3072-3091), as H1 to H3 say. Every other function, line, refusal, message and exit stays byte-identical to round 2's tree. The module docstring does not change, so the command reference is not regenerated.
- `tests/test_bridge_run.py`: add your own cases there. Change no existing case.
- `bridge/cursor-bridge/MANIFEST.json` changes only by running `python tools/make-manifest.py` (Done). Never edit it by hand. Restore `bridge/cursor-bridge/VERSION` with `git restore bridge/cursor-bridge/VERSION` right after (Done).

Do not modify anything else. `tests/test_program_watch_wait.py` and everything under `tests/fixtures/github/` are the supervisor's: read and run them, edit none of them, add no fixture.

## Out of scope
- .env and anything under secrets/
- CI configuration
- docs/ and handoff/, except the files the Scope section names. `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` stay as round 2 left them.
- `bridge/cursor-bridge/bridge_env.py` and its `ci_class`, `review-guard.py`, `bridge-stop.py` and every other program under `bridge/cursor-bridge/`. `ci_class` keeps its meaning everywhere else: round 2's G5 (a failed run after the watch) and the runs' readings are unchanged.
- Round 1's and round 2's reports: they stay as they are.
- Any finding of round 2's reviews not named in H1 to H3. The supervisor records them in `docs/HARDENING.md`.

## Context
**Rounds 1 and 2 govern everything this brief does not change:** `handoff/TASK-065.md` (R1-R14, the lines W1-W6) and `handoff/TASK-065-r2.md` (G1-G9). Read both. Their Context sections hold for this round unchanged.

**The supervisor's tests** (round 3's section; the fixtures are built from the captured `check-runs.json`, each header naming what changed):
- `test_r085_r3_under_the_base_s_list_a_named_failed_check_after_an_unnamed_one_starts_the_watch_at_once`: `wait-checks-lint-failed-first.json` with `wait-runs-two-running.json`. `latest_of_each` keeps the checks a latest run made in GitHub's order, then the app checks, so lint's failed job comes before security floor's.
- `test_r085_r3_only_a_conclusion_gh_counts_as_failed_starts_the_watch_at_once`, under the base's list and the default branch's: security floor concluding `neutral`, `cancelled` (no early start: one interval, then the green head) and `action_required` (an early start, W1 naming it).

**Known counts.** On round 2's tree (the supervisor's run, run/agent/TASK-065-r3-known.out): `tests/test_program_watch_wait.py` gives `5 failed, 44 passed, 5 skipped`. The five child-launcher cases are skipped on Windows; the supervisor ran them under Linux on round 2's tree, and all five pass.

**The code as it stands** (round 2's tree, line numbers verified):
- `bridge/cursor-bridge/bridge-run.py`: `WATCH_POLL` (line 1998); `_failed_check(latest)` (2171-2175) returns the first latest check `ci_class(item, "check") == "failed"`, or None; `_check_holds(item, entry)` (2193) is round 2's G8 rule; `_watch_decision` (2289) begins `failed = _failed_check(latest)` and `if failed is not None and (named["kind"] != "base" or any(_check_holds(failed, entry) for entry in named["contexts"] or [])):` (2296-2297). In `main()`, `run_child`'s timeout path (3072-3091): the LIMIT line, `report_git_config()`, `report_boundary()`, the exit line, the log entry, `killer()` (3083, which on Windows ends this process), `proc.wait(timeout=30)`, then `remove_pid_file(box["pid_file"])` (3090).
- A check's conclusion in GitHub's REST reply is lowercase (`failure`, `timed_out`, `action_required`, `neutral`, `cancelled`, `skipped`, `stale`, `startup_failure`), as the recorded replies hold it.

## Requirements
1. **H1. Every failed check is read.** The early start reads every latest check, in `latest_of_each`'s order, not only the first that has failed. Under the base's list it takes the first one that both counts as failed by H2 and holds a named context (`_check_holds`, round 2's G8). Under the default branch's list and the runs it takes the first one that counts as failed by H2. W1's `<what>` names the check it took: `check <name> failed (<conclusion>)`.
2. **H2. A failure gh reports.** A latest check counts as failed for the early start only where its `status` is `completed` and its `conclusion` is one of `failure`, `timed_out` or `action_required` (gh's fail bucket). Hold the three in one module constant beside `WATCH_POLL` (for example `WATCH_FAIL_FAST = ("failure", "timed_out", "action_required")`) with a one-line comment naming gh's `aggregate.go`. Any other conclusion (`neutral`, `cancelled`, `stale`, `startup_failure`, an unknown or missing one) never starts the watch early: the wait goes on as R5, R6 and R8 say, and the check still holds its context as round 2 holds it.
3. **H3. The pid file before the kill.** In `run_child`'s timeout path, remove the pid file (`remove_pid_file(box["pid_file"])`) before `killer()`, after the log entry. Keep the second call after `proc.wait` harmless or drop it; `main()`'s own removal after `watch_loop` stays.
4. **H4. Your tests.** Add your own cases to `tests/test_bridge_run.py` where the supervisor's leave a gap you find, in process only (never `main()`), with the acceptance tests' `Case`, `Clock` and stand-in imported from `test_program_watch_wait`, on the recorded replies only. Each names `R-085` in its name, docstring or a comment; a parametrized case has a plain `ids=` list. Example: under the runs, a neutral check does not start a watch that the runs' reading would not start.

## Acceptance criteria
- [ ] The Done section's pytest commands pass whole. `tests/test_program_watch_wait.py` gives no failure (it gave `5 failed, 44 passed, 5 skipped` on round 2's tree), the five child-launcher cases skipped on Windows only.
- [ ] H1-H3 hold as written; every requirement of rounds 1 and 2 still holds.
- [ ] `bridge/cursor-bridge/VERSION` reads `2026.11.12a` and is not listed by `git status --short`. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` prints `RESULT: SOURCES MATCH`. `python tools/dump-cli.py --check` exits 0.
- [ ] `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks` passes.
- [ ] No option added. No new dependency, configuration key or environment variable. No exception from a GitHub reply escapes as a traceback, and none is swallowed into a pass (ASVS L2).

## Constraints
- Do not add dependencies (the standard library only).
- Do not read or write any file outside this workspace (the folder you were started in).
- Do not edit `tests/test_program_watch_wait.py`, `tests/test_hotfix25a_roster_launcher.py` or anything under `tests/fixtures/github/`. If a case there seems wrong, stop and report it by its test id instead of working around it.
- If the brief, the rules, or the tooling got in your way, append one dated line describing it to `docs/BUILDER_NOTES.md`. Do not try to fix the tooling.
- In any Markdown you write, never break a line inside a paragraph or a list item.
- **External service.** Every call to GitHub is `bridge_env`'s, with its time limit `GH_API_TIMEOUT` (30 seconds) and no retry of its own. Add no remote call, no wait and no retry. Do not invent a reply's shape, fields or messages, and add no fixture.
- **Windowless launches.** Every process your code starts is created with `creationflags=NO_WINDOW`. In tests a launch needs no `creationflags` argument; where a test does write one, that line carries the literal text `CREATE_NO_WINDOW`. Every subprocess and git call in a test has a timeout.
- Never start a server, a watcher or a daemon that outlives a test. Run every command synchronously, in the foreground. Leave nothing running when you finish.
- **Do NOT run the full `tests/` tree.** Run only the commands the Done section names, exactly as written, from the Workspace root, with no `PYTHONPATH` or other environment change.
- **Never call `main()` of `bridge-run.py` in process** in a test of yours. H3 is held by reading: no test can end a launcher's job object inside pytest.
- Do not refactor code outside the parts the Scope's limits name, even if it looks wrong.
- Never run the product or a test against the owner's live data or the real GitHub. Do not run `gh` yourself.
- Follow existing conventions in the file you touch: ASCII program text and ASCII output.
- These git commands are not yours to run: `commit`, `push`, `switch`, `checkout`, `merge`, `rebase`, `reset`, `stash`, `branch -d`, `worktree`. You read with `git status`, `git diff` and `git log` only. The single exception is `git restore bridge/cursor-bridge/VERSION` in the Done section.
- **Mutation self-check (by hand, in process, no script in the diff).** Before you finish, apply each of these by hand, one at a time, run `tests/test_program_watch_wait.py`, and revert. List each in the report by its label, with the test id that caught it:
  - M26 only the first failed check read (H1);
  - M27 `neutral` counted as a failure gh reports (H2);
  - M28 `cancelled` counted as a failure gh reports (H2);
  - M29 `action_required` not counted (H2).

  A mutant no test catches is a gap: add a case for it (H4), or report it if you cannot.
- **Known failures.** On round 2's tree, `tests/test_program_watch_wait.py` gives `5 failed, 44 passed, 5 skipped`. None is known in the other files of the Done section. If a case fails that your change did not cause, report it by its test id with its failure lines and fix none.
- Prefer reuse over new code: `_check_holds`, `ci_class`, `remove_pid_file`, and the minimum that meets the acceptance criteria (the frozen `minimal-code.mdc` is in force).
- Rules in force for you: `.cursor/rules/secure-coding.mdc`, `.cursor/rules/workspace-boundary.mdc` and the frozen `minimal-code.mdc`.

## Done
Your report is the file `handoff/TASK-065-r3-report.md`, which you write as you go. It names no computer path and no user name: write `<Workspace>` for the repository folder and `<tmp>` for a temporary folder, including in quoted command output.

When you finish, it holds:
- a list of every file you changed;
- a one-paragraph summary of what you did;
- for H1-H4, one line each on what meets it, naming the functions and their lines as the file stands after your change;
- the mutation self-check list, M26-M29, each with the test id that caught it (or `not caught` and why);
- every command of the list below with its output;
- a section headed exactly `Assumed, not verified`, as the report's last section: one item per line, what you assumed · why · what would confirm it, or `Assumed, not verified: none`.

Run these from the Workspace root, in this order, after your last edit, each on its own, synchronously in the foreground, with no `PYTHONPATH` or other environment change:
1. `git status --short`
2. `python tools/make-manifest.py`
3. `git restore bridge/cursor-bridge/VERSION`
4. `python tools/dump-cli.py --check` (expect exit 0)
5. `python -m pytest -p no:cacheprovider -q -rs tests/test_program_watch_wait.py tests/test_bridge_run.py tests/test_hotfix25a_roster_launcher.py tests/test_program_branch_rule.py`
6. `python -m pytest -p no:cacheprovider -q tests/test_program_ready.py tests/test_program_strip_names.py tests/test_allowlist.py tests/test_tests_windowless.py` (outside Scope. A failure here is reported by test id, never fixed in those files.)
7. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` (expect `RESULT: SOURCES MATCH`)
8. `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks`
9. `git rev-parse HEAD` and `git status --short` (`bridge/cursor-bridge/VERSION` must not be listed; if it is, report it)

Quoting rules:
- Every command you ran is quoted in the report with the lines it printed, verbatim, in a fenced block.
- Each pytest summary line is quoted verbatim in a fenced block. Never restate a count in prose.
- A claim that a check passed quotes the output line that shows it.
- A command you did not run is written `not run`, never described as run.
- Write the report's results after step 9, naming the commit its counts belong to and whether the working tree then held uncommitted changes.

Your last message is the summary and the report file's path, and nothing follows it. The supervisor reads only the last message, and a message printed earlier and then followed by more work is lost.
