---
record: brief
header: 1
id: "TASK-065"
round: 2
satisfies: [R-085]
scope: ["bridge/cursor-bridge/bridge-run.py", "bridge/cursor-bridge/MANIFEST.json", "docs/cli-reference.json", "docs/CLI_REFERENCE.md", "tests/test_bridge_run.py", "docs/BUILDER_NOTES.md", "handoff/TASK-065-r2-report.md"]
merge_unit: null
blocking_class: null
---
# TASK-065 round 2: the wait's exit line, its pid file, its head and the lines it prints (R-085)

Round cause: behaviour - bridge/cursor-bridge/bridge-run.py:3023-3036, a wait that reaches the limit after a watch returned 0 prints no `bridge-run: exit 124` line, and bridge/cursor-bridge/bridge-run.py:3001, the child's LIMIT line names the seconds left, not the run's limit (security audit 1, Review A); behaviour - bridge/cursor-bridge/bridge-run.py:2997, no pid file while the wait runs, so `bridge-stop.py` cannot end it (security audit 2); security - bridge/cursor-bridge/bridge-run.py:2269, a local head that cannot be read lets GitHub's head stand in for it, against KP-051 (security audit 3); behaviour - bridge/cursor-bridge/bridge-run.py:2241, under the base's list a failed check no rule names starts a `--required` watch, which returns before the jobs that need `security floor` are listed (security audit 4); behaviour - bridge/cursor-bridge/bridge-run.py:2343, every run completed with one failed keeps the watch's exit 0 (security audit 5); behaviour - bridge/cursor-bridge/bridge-run.py:2289, a watch that names a repository (`--repo`, `-R`) waits on this checkout's (security audit 6); behaviour - bridge/cursor-bridge/bridge-run.py:2306 and 2361-2370, the limit line names a failed poll that never happened, and the line saying the watch starts is printed where no time is left to start it (Review A); correctness - bridge/cursor-bridge/bridge-run.py:2174, a context the rule ties to an app is held by any check of its name, or by a commit status (Review A)

## Objective
Fix the following confirmed defects in the launcher's wait before a CI watch, and nothing else.

This is round 2 of TASK-065. Round 1 built `WATCH_POLL`, `watch_loop` and its helpers, and ran the watch's child from `main()` through it. All of that stays except what G1 to G8 below change. The supervisor commits round 1's tree together with this brief and the new tests before your run, so the line numbers below hold when you start.

**The confirmed defects** (each now a red test of the supervisor's, the round-2 section of `tests/test_program_watch_wait.py`):
- G1. After a watch returned 0 (no list named), a wait that then reaches the limit returns 124, and `main()` skips the exit line for a 124 once a child ran (lines 3023-3036). The launcher's last line must be `bridge-run: exit <rc>` on every path. The child's own LIMIT line (3001-3002) prints the seconds left of the run where it printed the run's limit before this increment.
- G2. The pid file `run/launcher/pids/<run id>` is written only while a child runs (2997, 3017, 3019), so `bridge-stop.py <run id>` finds nothing to end while the launcher waits.
- G3. `_watch_poll` (2261, 2269) takes GitHub's head where `local_head` returns None, so a head the local checkout cannot name is read as the pushed head (KP-051).
- G4. `_watch_decision` (2241-2244) starts the watch at once for any failed latest check. Under the base's list the watch keeps `--required`, so gh watches only the named contexts: a failed app check no rule names starts a watch that returns before the jobs that need `security floor` are listed, the field's case F2 again.
- G5. After a watch returned 0 (no list named), every latest run completed and one of them failed (a run that failed at its start posts no check, so gh saw only the green app checks): W6 says the exit 0 stands, and the launcher exits 0.
- G6. A watch with `--repo` or `-R` is read against this checkout's repository (`{owner}/{repo}`), not the one gh is told to watch.
- G7. W3's `<left>` falls back to `poll failed (pull: cannot read)` where nothing failed: at limit 0, and where the last poll was ready but no time is left (2304-2306). In that second case W1 or W5 is printed first, saying the watch starts, and none starts (2361-2370).
- G8. `_missing_contexts` (2164-2179) holds a context by any check of that name, or by a commit status of that context, where the rule ties the context to an app (`app_id`). `prove_ci` (`review-guard.py`, `_context_result`, lines 1563-1578) holds such a context only by a check of that name made by that app; a commit status carries no app and never holds it.

Satisfies: R-085 - A CI watch never returns before CI has run (F2, both cases, and J6): before any `gh pr checks <n> --watch`, with `--required` or without, the launcher waits, inside the run's own limit, until every required check context of the pull request's base branch has a check or a commit status on the pushed head or a check of that head has failed, then starts the watch as given and prints what it waited for; [...] a poll that fails is retried inside the limit; [...]. (Full text: its row in `docs/REQUIREMENTS.md`. This round serves the wait's exit, its pid file, the pushed head it reads, the contexts it counts as held, and the lines it prints.)

## Scope
Files you may create or modify:
- bridge/cursor-bridge/bridge-run.py
- bridge/cursor-bridge/MANIFEST.json
- docs/cli-reference.json
- docs/CLI_REFERENCE.md
- tests/test_bridge_run.py
- docs/BUILDER_NOTES.md
- handoff/TASK-065-r2-report.md

Limits on these files:
- `bridge/cursor-bridge/bridge-run.py`: only the wait's block from `WATCH_POLL` (line 1998) to the end of `watch_loop` (line 2376), and in `main()` the watch kind's block (lines 2950-3037), as G1 to G8 say. The module docstring's watch paragraph (lines 59-70) may gain one clause for G5 and one for G6. `write_pid_file` and `remove_pid_file` (lines 1529-1549) are called, never changed. Every other function, refusal, message and exit stays byte-identical to round 1's tree.
- `tests/test_bridge_run.py`: add your own cases there. Change no existing case (round 1's `B1`-`B3` included).
- `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` change only by running `python tools/dump-cli.py` (Done), and only if the docstring changed. Afterwards `python tools/dump-cli.py --check` must exit 0. Never edit either by hand.
- `bridge/cursor-bridge/MANIFEST.json` changes only by running `python tools/make-manifest.py` (Done). Never edit it by hand. Restore `bridge/cursor-bridge/VERSION` with `git restore bridge/cursor-bridge/VERSION` right after (Done).

Do not modify anything else. `tests/test_program_watch_wait.py` and everything under `tests/fixtures/github/` are the supervisor's: read and run them, edit none of them, add no fixture.

## Out of scope
- .env and anything under secrets/
- CI configuration
- docs/ and handoff/, except the files the Scope section names. Every record under docs/ is the supervisor's.
- `bridge/cursor-bridge/bridge_env.py`, `review-guard.py`, `bridge-stop.py` and every other program under `bridge/cursor-bridge/`. If one lacks something you need, stop and report it.
- `tools/make-manifest.py`, `tools/dump-cli.py`, and every test file not named in Scope (you run some of them, Done, and edit none).
- Any mutation script. The mutants file and the mutation run are the supervisor's, after your run.
- Round 1's report `handoff/TASK-065-r1-report.md`: it stays as it is.

## Context
**Round 1's brief governs everything this brief does not change:** `handoff/TASK-065.md`, read it whole, Requirements R1-R14 and the lines W1-W6 above all. Its Context section (the design, the reader's names and lines in `bridge_env.py`, the trait External services, security, development data, host) holds for this round unchanged. One correction of the brief's own error, as round 1 built it: W3's `<left>` for a failed poll is `poll failed (<source>: <reason>)`, without the `a ` that W4 begins with, so that the tests count W4's line alone.

**The supervisor's tests.** `tests/test_program_watch_wait.py`, the section headed `# ================================================================ round 2: the supervisor's cases after round 1's two reviews`, read it whole. The in-process cases use round 1's `Case`, `Clock` and stand-in. Two of them add to that:
- `test_r085_r2_a_local_head_that_cannot_be_read_is_a_failed_poll` passes a `folder` that is no git checkout (with `GIT_CEILING_DIRECTORIES` set to the test's temporary folder).
- `test_r085_r2_a_ready_poll_that_ends_past_the_limit_names_what_it_found` replaces `bridge_env.head_state` on the launcher's own `bridge_env` module by a wrapper that calls it and then moves the test's clock 40 seconds: a poll that takes time. Keep calling `bridge_env.head_state` through the module (`bridge_env.head_state(...)`), as round 1 does.

The last three cases run the launcher as a child, with a shell-script stand-in `gh` on PATH that also records, at every call, what `run/launcher/pids/` holds. They are skipped on Windows and run in CI's ubuntu job: they are the cases for G1 and G2, which live in `main()`. You cannot run them on this host. Read them for what `main()` must do, and the supervisor runs them after your run.

**Known counts.** On round 1's tree (the supervisor's run, run/agent/TASK-065-r2-known.out): `tests/test_program_watch_wait.py` gives `11 failed, 31 passed, 5 skipped`. Every failure is a round-2 case. The skips are the five child-launcher cases (round 1's two and round 2's three). The supervisor ran the four POSIX child-launcher cases under Linux on round 1's tree: round 1's passes, round 2's three fail, each for the defect it names. All must pass, the Windows skips aside.

**The code as it stands** (round 1's tree, line numbers verified):
- `bridge/cursor-bridge/bridge-run.py`:
  - `write_pid_file(folder, run_id, pid, child_pid)` (line 1529) writes `"<pid> <child_pid>\n"` to `run/launcher/pids/<run id>`, only where `run/` exists, and returns its path or None. `remove_pid_file(path)` (line 1544) removes it.
  - `local_head(folder)` (line 2002) returns the local HEAD or None.
  - `_watch_pr_number` (2038), `_watch_left` (2051), `_watch_pause` (2055), `_watch_name` (2083), `_failed_check` (2157), `_missing_contexts` (2164), `_all_runs_completed` (2182), `_runs_problem` (2214), `_watch_decision` (2239), `_watch_poll` (2259), `_watch_limit_line` (2278), `watch_loop` (2282-2376).
  - `main()`'s watch block (2950-3037): `run_child(words, seconds)` (2955-3020) starts one child and writes the pid file at 2997; at the timeout it prints the LIMIT line (3001-3002), the exit line and the log entry, and ends the tree. After `watch_loop` returns (3022), lines 3023-3036 print the exit line and log the run, except for a 124 after a child ran.
- `bridge/cursor-bridge/bridge-stop.py` (read only): `bridge-stop.py <run id>` reads `run/launcher/pids/<run id>` as two pids, `<pid> <child_pid>` (line 124), ends the tree of `child_pid` (line 135), then that of `pid`.
- `bridge/cursor-bridge/bridge_env.py` (read only): a check's app is `check["app"]["id"]`, an int (not a bool); `review-guard.py`'s `_check_app` (line 1538) reads it that way. A context from `branch_rule` is `{"context": str, "app_id": int or None}`.

## Requirements
1. **G1. The exit line, always last.**
   - In `main()`, after `watch_loop` returns, where the run has not already printed its exit line (the child's timeout path prints it and logs the run), print what the run prints at its end today, whatever `rc` is and whether or not a child ran: the GIT-CONFIG lines (`report_git_config()`), the BOUNDARY lines (`report_boundary()`), then `bridge-run: exit <rc>` as the last line, and one log entry with the run's total seconds and `rc`.
   - The child's LIMIT line reads `bridge-run: LIMIT <limit>s reached after <s>s; terminating the whole process tree`, where `<limit>` is the run's limit (`limit` of `main()`) and `<s>` the whole seconds since the run's start (`mark`), as it read before this increment. The child is still given only the seconds left (`proc.wait(timeout=seconds)`).
2. **G2. The pid file names the launcher while it waits.**
   - Before `watch_loop` is called for a watch, write the pid file with the launcher's pid in both places: `write_pid_file(folder, run_id, os.getpid(), os.getpid())`.
   - When a child starts, write it with the child's pid second (as 2997 does). When the child ends, without the timeout, write it again with the launcher's pid in both places, so that the wait between two watches can be stopped too.
   - After `watch_loop` returns, remove it before the exit line. No pid file is left after the run.
3. **G3. A local head that cannot be read.** In `_watch_poll`, after the read of the pull request, where `local_head(folder)` returns None, the poll has failed: source `local`, reason `the pushed head cannot be read`. GitHub's head is never read in its place. W4 then reads `bridge-run: a poll failed (local: the pushed head cannot be read); retrying every 15s until the limit`, and W3's `<left>` `poll failed (local: the pushed head cannot be read)`.
4. **G4. A failed check starts the watch at once only where gh will see it.**
   - Under the base's list (the watch keeps `--required`), a failed latest check starts the watch at once only where it holds one of the named contexts (G8's rule: its name is the context's, and its app is the context's where the context names one).
   - Under the default branch's list and under the runs (the watch starts without `--required`, so gh watches every check), any failed latest check starts it at once, as round 1 does.
   - W1's `<what>` for it stays `check <name> failed (<conclusion>)`.
5. **G5. A failed run after the watch.** Where the reading is the workflow runs, a watch returned 0, and at the poll after it every latest run is completed:
   - where one or more latest runs are failed by `ci_class(run, "run")`, print W6b and return 1. W6b: `bridge-run: every latest workflow run of head <head12> is completed and <failed>; the launcher exits 1`, where `<failed>` is each such run as `run <name> (<event>) concluded <conclusion>`, joined by `, `;
   - otherwise W6 and return 0, as round 1 does.
6. **G6. A watch that names a repository.** After the `--watch` check of R2 and before the number check, where any word of the watch is `--repo` or `-R`, begins with `--repo=`, or is `-R` followed by more characters, print `bridge-run: the watch names another repository; it starts without the wait` and return `start(argv, limit)` with the words unchanged. Nothing is read from GitHub.
7. **G7. W3 names only what happened.**
   - Where no time is left before the first poll (`limit` is 0 or less), read nothing from GitHub and print W3 with the reading `the pull request <n>`, `<head12>` the local head's (or `?` where it cannot be read), and `<left>` `no time left before the first poll`; return 124.
   - Where a poll is ready (R5, R6, R8) but no time is left to start the watch, print neither W1 nor W5. Print W3 with `<left>` `ready (<what>), but no time left to start the watch`, `<what>` as W1 would have named it, and return 124.
   - Otherwise W3's `<left>` is what the last poll found (R10's list, with G3's reason). It is never `poll failed (...)` unless the last poll failed.
8. **G8. A context the rule ties to an app.** A required context whose `app_id` is an int (not a bool) is held only by a latest check whose name is the context and whose app id is that `app_id`. A latest commit status never holds it. A context whose `app_id` is None is held as round 1 holds it: a latest check of that name, or a latest commit status of that context. W3's `missing ...` names such a context like any other.
9. **G9. Your tests.** Add your own cases to `tests/test_bridge_run.py` where the supervisor's leave a gap you find, in process only (never `main()`), with the acceptance tests' `Case`, `Clock` and stand-in imported from `test_program_watch_wait`, on the recorded replies only. Each names `R-085` in its name, docstring or a comment; a parametrized case has a plain `ids=` list. Examples: W6b naming two failed runs; G6's line where `--repo` comes before the number.

## Acceptance criteria
- [ ] The Done section's pytest commands pass whole. `tests/test_program_watch_wait.py` gives no failure (it gave `11 failed, 31 passed, 5 skipped` on round 1's tree), the five child-launcher cases skipped on Windows only.
- [ ] G1-G8 hold as written; every round-1 requirement (R1-R14 of `handoff/TASK-065.md`) still holds.
- [ ] `main()`'s last line is `bridge-run: exit <rc>` on every path of the watch kind, and the pid file is written before the wait and removed after it (G1, G2).
- [ ] `python tools/dump-cli.py --check` exits 0. MANIFEST is regenerated. `bridge/cursor-bridge/VERSION` reads `2026.11.12a` and is not listed by `git status --short`. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` prints `RESULT: SOURCES MATCH`.
- [ ] `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks` passes.
- [ ] No option added. No new dependency, configuration key or environment variable. No new Semgrep high finding. No exception from a GitHub reply escapes as a traceback, and none is swallowed into a pass (ASVS L2).

## Constraints
- Do not add dependencies (the standard library only).
- Do not read or write any file outside this workspace (the folder you were started in). Everything you need is inside it, and everything you produce goes inside it.
- Do not edit `tests/test_program_watch_wait.py`, `tests/test_hotfix25a_roster_launcher.py` or anything under `tests/fixtures/github/`. If a case there seems wrong, stop and report it by its test id instead of working around it.
- If the brief, the rules, or the tooling got in your way, append one dated line describing it to `docs/BUILDER_NOTES.md`. Do not try to fix the tooling. Do the same for anything you learned about a defect or a pitfall.
- In any Markdown you write, never break a line inside a paragraph or a list item; one paragraph is one line.
- **External service.** Every call to GitHub is `bridge_env`'s, with its time limit `GH_API_TIMEOUT` (30 seconds) and no retry of its own. The wait polls every `WATCH_POLL` (15) seconds up to the run's limit. Add no other remote call, no other wait and no other retry. Do not invent a reply's shape, fields, hosts or messages, and add no fixture.
- **Windowless launches.** Every process your code starts is created with `creationflags=NO_WINDOW`. In tests a launch needs no `creationflags` argument (`tests/conftest.py` makes every launch windowless); where a test does write one, that line carries the literal text `CREATE_NO_WINDOW`. Every subprocess and git call in a test has a timeout.
- Never start a server, a watcher or a daemon that outlives a test. Run every command synchronously, in the foreground. Leave nothing running when you finish.
- **Do NOT run the full `tests/` tree.** Run only the commands the Done section names, exactly as written, from the Workspace root, with no `PYTHONPATH` or other environment change.
- **Never call `main()` of `bridge-run.py` in process** in a test of yours: on Windows it would put the test process in its job object. G1 and G2 are held by the supervisor's child-launcher cases.
- Do not refactor code outside the parts the Scope's limits name, even if it looks wrong.
- Never run the product or a test against the owner's live data or the real GitHub. Do not run `gh` yourself.
- Follow existing conventions in the file you touch: ASCII program text and ASCII output, and results returned as values.
- These git commands are not yours to run: `commit`, `push`, `switch`, `checkout`, `merge`, `rebase`, `reset`, `stash`, `branch -d`, `worktree`. You read with `git status`, `git diff` and `git log` only. The single exception is `git restore bridge/cursor-bridge/VERSION` in the Done section.
- **Mutation self-check (by hand, in process, no script in the diff).** Before you finish, apply each of these by hand, one at a time, run `tests/test_program_watch_wait.py`, and revert. List each in the report by its label, with the test id that caught it:
  - M17 a local head that cannot be read taken as GitHub's (G3);
  - M18 any failed check starting the watch under the base's list (G4);
  - M19 a failed run after the watch keeping exit 0 (G5);
  - M20 `--repo` not looked for (G6);
  - M21 `-R` joined to its value not looked for (G6);
  - M22 limit 0 reading the pull request (G7);
  - M23 W1 printed with no time left (G7);
  - M24 a check of another app holding an app's context (G8);
  - M25 a commit status holding an app's context (G8).

  The supervisor's mutants for G1 and G2 run under Linux after your run. A mutant no test catches is a gap: add a case for it (G9), or report it if you cannot.
- **Known failures.** On round 1's tree, `tests/test_program_watch_wait.py` gives `11 failed, 31 passed, 5 skipped`. None is known in the other files of the Done section. If a case fails that your change did not cause, report it by its test id with its failure lines and fix none.
- Prefer reuse over new code: round 1's helpers, `bridge_env`'s readers and `ci_class`, `write_pid_file` and `remove_pid_file`, the standard library, and the minimum that meets the acceptance criteria (the frozen `minimal-code.mdc` is in force). This never overrides a security, observability or accessibility requirement stated above.
- Rules in force for you: `.cursor/rules/secure-coding.mdc`, `.cursor/rules/workspace-boundary.mdc` and the frozen `minimal-code.mdc`.

## Done
Your report is the file `handoff/TASK-065-r2-report.md`, which you write as you go: what you did, what you changed, what you ran and what it printed, and what you could not do. It names no computer path and no user name: write `<Workspace>` for the repository folder and `<tmp>` for a temporary folder, including in quoted command output.

When you finish, it holds:
- a list of every file you changed;
- a one-paragraph summary of what you did;
- for G1-G9, one line each on what meets it, naming the functions and their lines as the file stands after your change;
- the mutation self-check list, M17-M25, each with the test id that caught it (or `not caught` and why);
- every command of the list below with its output;
- a section headed exactly `Assumed, not verified`, as the report's last section.

The `Assumed, not verified` section lists every fact this change relies on that neither this brief nor the existing code settled, and that you did not confirm: one item per line, what you assumed · why · what would confirm it. If there are none, write `Assumed, not verified: none`. Examples: that `bridge-stop.py` ending the launcher's own tree twice is harmless; that a failed run's `conclusion` is always a plain word.

Run these from the Workspace root, in this order, after your last edit, each on its own, synchronously in the foreground, with no `PYTHONPATH` or other environment change:
1. `git status --short`
2. `python tools/dump-cli.py`
3. `python tools/dump-cli.py --check` (expect exit 0)
4. `python tools/make-manifest.py`
5. `git restore bridge/cursor-bridge/VERSION`
6. `python -m pytest -p no:cacheprovider -q -rs tests/test_program_watch_wait.py tests/test_bridge_run.py tests/test_hotfix25a_roster_launcher.py tests/test_program_branch_rule.py`
7. `python -m pytest -p no:cacheprovider -q tests/test_program_ready.py tests/test_program_strip_names.py tests/test_allowlist.py tests/test_tests_windowless.py` (outside Scope. A failure here is reported by test id, never fixed in those files.)
8. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` (expect `RESULT: SOURCES MATCH`)
9. `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks`
10. `git rev-parse HEAD` and `git status --short` (`bridge/cursor-bridge/VERSION` must not be listed; if it is, report it)

Quoting rules:
- Every command you ran is quoted in the report with the lines it printed, verbatim, in a fenced block.
- Each pytest summary line is quoted verbatim in a fenced block. Never restate a count in prose.
- A claim that a check passed quotes the output line that shows it.
- Each mutation is listed by its label and text, with what caught it.
- A command you did not run is written `not run`, never described as run.
- Write the report's results after step 10, naming the commit its counts belong to (`git rev-parse HEAD`) and whether the working tree then held uncommitted changes (`git status --short`).

Your last message is the summary and the report file's path, and nothing follows it. The supervisor reads only the last message, and a message printed earlier and then followed by more work is lost.
