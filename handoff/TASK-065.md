---
record: brief
header: 1
id: "TASK-065"
round: 1
satisfies: [R-085]
scope: ["bridge/cursor-bridge/bridge-run.py", "bridge/cursor-bridge/MANIFEST.json", "docs/cli-reference.json", "docs/CLI_REFERENCE.md", "tests/test_program_watch_wait.py", "tests/test_bridge_run.py", "tests/fixtures/github/", "docs/BUILDER_NOTES.md", "handoff/TASK-065-r1-report.md"]
merge_unit: null
blocking_class: null
---
# TASK-065: the watch waits for the required checks (R-085)

Round cause: first round (no earlier round)

## Objective
Before a CI watch (`gh pr checks <n> --watch`), the launcher `bridge-run.py` today waits up to 120 seconds for any first check on the pushed head, then starts the watch anyway with advice to start it again by hand (`wait_for_first_check`). The field met the watch returning before CI had run, in two forms. With `--required`, the required check was a job with `needs:`: it had no check until the jobs before it ended, and the watch answered at once. Without `--required`, on a base branch with no rule, the watch returned exit 0 at once while two app checks were green and the workflow's jobs were still queued. This increment replaces that wait with one that reads what CI must show. Before any `gh pr checks <n> --watch`, with `--required` or without, the launcher reads the pull request's base and head and the base's required contexts through `bridge_env`'s reader (TASK-064, merged). It waits, polling every `WATCH_POLL` seconds inside the run's own limit, until every required context has a check or a commit status on that head, or a check of the head has failed. Where the base names no required context, it waits for the default branch's contexts. Where none is named anywhere, or a rule cannot be read, it waits for the head's workflow runs. In those three cases it starts a `--required` watch without that option. Where no list could be named, it reads the runs again when the watch returns 0, and starts the same watch again while a run is not completed. The proof that CI passed stays `review-guard.py ready` (TASK-083). The loop's text is TASK-082's.

Satisfies: R-085 - A CI watch never returns before CI has run (F2, both cases, and J6): before any `gh pr checks <n> --watch`, with `--required` or without, the launcher waits, inside the run's own limit, until every required check context of the pull request's base branch has a check or a commit status on the pushed head or a check of that head has failed, then starts the watch as given and prints what it waited for; on a base branch with no required context the launcher waits for the default branch's contexts, and where there are none anywhere or a rule cannot be read, until the head has a workflow run and each of its latest runs has a check listed or is completed; in each of those cases it says so and starts a `--required` watch without that option, and where no list could be named it reads the runs again when the watch returns with exit 0 and, while a latest run is not completed, waits at its interval until each such run has a check listed that is not completed, or all are completed, and starts the watch again, inside the limit, a watch that returns with another exit ending the launcher with it; a poll that fails is retried inside the limit; [...]. (Full text: its row in `docs/REQUIREMENTS.md`. This brief serves the launcher. The loop's step 8 sentence and the policy's pointer are TASK-082's.)

## Scope
Files and directories you may create or modify:
- bridge/cursor-bridge/bridge-run.py
- bridge/cursor-bridge/MANIFEST.json
- docs/cli-reference.json
- docs/CLI_REFERENCE.md
- tests/test_program_watch_wait.py
- tests/test_bridge_run.py
- tests/fixtures/github/
- docs/BUILDER_NOTES.md
- handoff/TASK-065-r1-report.md

Limits on these paths:
- `tests/test_program_watch_wait.py` and everything under `tests/fixtures/github/` belong to the supervisor: the acceptance tests and the recorded replies. Read and run them. Edit none of them. Add no file under `tests/fixtures/github/` and delete none.
- `tests/test_bridge_run.py`: add your own cases there. Change no existing case.
- `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` change only by running `python tools/dump-cli.py` (Done). Afterwards `python tools/dump-cli.py --check` must exit 0. Never edit either by hand.
- `bridge/cursor-bridge/MANIFEST.json` changes only by running `python tools/make-manifest.py` (Done). Never edit it by hand. `bridge/cursor-bridge/VERSION` is outside Scope and reads `2026.11.12a`. `make-manifest.py` rewrites its line endings, so restore it with `git restore bridge/cursor-bridge/VERSION` right after (Done).
- `bridge/cursor-bridge/bridge-run.py`: the module docstring's sentence on the watch's wait (lines 59-62), the block from `WATCH_WAIT` to the end of `wait_for_first_check` (lines 1992-2037), and in `main()` the call of the old wait (lines 2532-2536) and the child's start and wait (lines 2616-2693), as far as running the watch through `watch_loop` needs. Every other function, refusal, message and exit stays as it is.

The supervisor already changed one test file, before this brief, that the plan's Scope omits: `tests/test_hotfix25a_roster_launcher.py` held the old wait's two cases (`wait_for_first_check`'s 20-second and 120-second lines). They are replaced there by a comment pointing to `tests/test_program_watch_wait.py`. That file is outside Scope. Run it and edit nothing in it.

Do not modify anything else.

## Out of scope
- .env and anything under secrets/
- CI configuration
- docs/ and handoff/, except the files the Scope section names. Every record under docs/ is the supervisor's.
- `bridge/cursor-bridge/bridge_env.py` and every other program under `bridge/cursor-bridge/`. The reader is TASK-064's and must not change. If it lacks something you need, stop and report it.
- `bridge/cursor-bridge/review-guard.py` and `ready` (TASK-083, merged).
- The loop's text, the policy and the digest (TASK-082).
- `tools/make-manifest.py`, `tools/dump-cli.py`, and every test file not named in Scope (you run some of them, Done, and edit none).
- Any mutation script. The mutants file and the mutation run are the supervisor's, after your run.

## Context
**The design that binds this increment:** `docs/DESIGN.md`, "Change: the program release", the bullet group **The launcher, `bridge-run.py`** (line 320), the bullet *F2, both cases, and J6* (line 327): read it whole. The rule's reader is the bullet group on the review guard and `bridge_env.py` (line 329, the bullet *The rule's reader*, line 330). The plan entry is `docs/BUILD_PLAN.md`, `### TASK-065` (line 1822): Scope, Scope notes and Done when.

**The supervisor's acceptance tests.** `tests/test_program_watch_wait.py` fixes the interface; read it whole. It drives one function in process, `watch_loop`, never `main()`: on Windows `main()` puts its own process in a job object that ends the whole process tree at the limit, so `main()` cannot run inside pytest. Each case does the following:
- It makes a scratch repository (`test_task032_supervisor_guard.make_repo`), whose HEAD is the pushed head.
- It replaces the launcher module's name `time` by a clock of its own (`Clock`): `time.monotonic()` reads it, `time.sleep(s)` advances it and records `s`, and nothing else moves it.
- It replaces `bridge_env.GH_COMMAND` on the launcher's own `bridge_env` module by TASK-064's stand-in `gh`, with two additions. The captured head (forty `1`s) is replaced in every reply by the repository's HEAD. The replies are a list of states: the n-th read of the pull request (the n-th poll) answers from the n-th state, and every later read from the last. A path with no route answers GitHub's 404 `Not Found`. Anything but a plain GET exits 99.
- It calls `watch_loop(argv, folder, limit, start)` with a `start` that records `(words, seconds)`, advances the clock by its duration (60 seconds unless the case says otherwise) and returns the case's next exit.

The head states are `tests/fixtures/github/wait-*.json` (this increment's), built by the supervisor from TASK-064's captured replies, each header naming the captured reply and the fields changed, and TASK-083's `ready-*.json`. The last case, `test_r085_the_launcher_waits_then_runs_the_watch_it_was_given`, starts the launcher as a child with a shell-script stand-in `gh` on PATH. It is skipped on Windows and runs in CI's ubuntu job. It is the one case that runs `main()`, so read it for what `main()` must do.

**Known counts.** On the checkpoint code, `tests/test_program_watch_wait.py` gives `30 failed, 2 skipped` (the supervisor's run over this file, `tests/test_hotfix25a_roster_launcher.py` and `tests/test_program_branch_rule.py` gave `30 failed, 167 passed, 2 skipped in 55.49s`, run/agent/TASK-065-known.out). Every case fails because the launcher has no `watch_loop` and keeps the old wait. The child-launcher case is skipped on Windows. All of them must pass, the skips aside.

**The code as it stands** (line numbers verified on the checkpoint).
- `bridge/cursor-bridge/bridge-run.py`:
  - `import time` is at line 103 and `import bridge_env` at line 107. `NO_WINDOW` is at line 109, and `KINDS` (line 111) gives the watch kind 3600 seconds.
  - The docstring's lines 59-62 say a watch "waits up to two minutes for the pushed head (the local HEAD) to be the pull request's head on GitHub with a check registered, and says how long it waited, so a watch neither ends at once with "no checks reported" nor takes the previous commit's run (KP-051)".
  - `WATCH_WAIT = 120` and `WATCH_STEP = 10` are at lines 1992-1993. `gh_pr_state` (line 1996) runs `gh pr view` and is used only by the old wait. `local_head(folder)` (line 2009) reads `git rev-parse HEAD`. `wait_for_first_check(argv, folder)` is at lines 2017-2037.
  - `main()` (line 2341) prints `bridge-run: started <id>` as its first line (line 2489). Review guard and `pr-activity-check` read that line, so it must stay first. `main()` calls the old wait at lines 2532-2536 for `kind == "watch"`. It starts the child at lines 2616-2653, inside a job object on Windows (`Job().assign_self()`). It waits with `proc.wait(timeout=limit)` (line 2660). At the limit it prints `bridge-run: LIMIT ...` and `bridge-run: exit 124`, writes the log entry and kills the tree (lines 2661-2679). Otherwise it prints `bridge-run: exit <rc>` and writes the log entry (lines 2680-2693).
- `bridge/cursor-bridge/bridge_env.py` (TASK-064, read only). The names you call:
  - `GH_COMMAND = ["gh"]` (line 3838) and `GH_API_TIMEOUT = 30` (line 3839).
  - `ANSWER_VALUE = "value"`, `ANSWER_NONE = "none"` and `ANSWER_CANNOT = "cannot read"` (lines 3840-3842).
  - `pull_refs(repo, number, cwd=None)` (line 4067) returns `answer`, `reason`, `source` (`pull`), `base` and `head`.
  - `branch_rule(repo, branch, cwd=None)` (line 4005) returns `contexts`, a list of `{"context": str, "app_id": int or None}`, its answer `value`, `none` or `cannot read` (source `protection` or `rules`).
  - `repo_settings(repo, cwd=None)` (line 4051) returns `default_branch` (source `repo`).
  - `head_state(repo, sha, cwd=None)` (line 4143) returns `checks`, `statuses` and `runs`, each read to its last page.
  - `latest_of_each(state)` (line 4283) keeps the latest of each. A check a latest run made carries that run's suite: the check's `check_suite.id` equals the run's `check_suite_id`.
  - `ci_class(item, kind)` (line 4348) returns `"passed"`, `"pending"`, `"skipped"` or `"failed"`. Every reader returns a dict and never raises.
  - `review-guard.py`'s `prove_ci` (lines 1643-1706) makes the same reading of the base, the default branch and the runs for `ready`. Follow its order and its repository name `"{owner}/{repo}"` with `cwd=folder`. Do not import or change it.

**External service and the wait's limits (the trait External services).** GitHub's REST API, read through `gh api`, is a service run by others.
- Every remote call this increment makes is one of `bridge_env`'s `gh api` GETs, each with its time limit `GH_API_TIMEOUT` (30 seconds) and no retry of its own.
- The wait polls every `WATCH_POLL` = 15 seconds (a module constant you add), up to the run's own limit, counted from the wait's start. A poll whose read fails is retried at the next interval, its reason printed once. That is the only retry.
- The watch itself is `gh pr checks`, started as today. Add no other remote call.
- "Done" means passing on the recorded replies through the stand-in, never on a reply you invent. If a case you need has no recorded reply, do not make one up and add no fixture. Stop and report it: a capture is the supervisor's to run. No test of yours, and no command you run, calls the real GitHub.

**Security context.** The ASVS level is 2 (INVENTORY, Decisions). `.cursor/rules/secure-coding.mdc` is in force for you. GitHub's replies are outside input. A reply the reader cannot read is never a pass, and never a list of contexts. It is a failed poll (the pull request, the head's lists) or a rule that cannot be read (the base's or the default branch's rule, the default branch's name). Reasons are printed as the reader clipped them, as text only. The reads use the owner's `gh` login, GET only, and print nothing beyond what the lines below name. The watch's command line is never built from a reply: it is the given words, with `--required` removed where the lines below say.

**Development data.** The inventory's decision (`docs/INVENTORY.md`, Decisions, the row beginning `Development data:`) reads: "the dev build is the Workspace sources under `bridge/`; a session in the repo always runs the *installed* bridge (`~/.claude`), never the one being edited, and installs reach running projects only through the owner's install run sheet". For you this means: run the launcher only from tests, on scratch repositories under pytest's `tmp_path`, on the recorded replies. Never install anything. Never copy anything under `~/.claude`. Never start a watch against this repository's own pull requests.

**Host.** Windows 11, with Python as on the owner's interpreter. `gh` 2.97.0 was the version of the captures; do not run `gh` yourself. This session has no `claude` on PATH (`claude --version`: command not found), so no Claude Code version is tested on.

**No owner's value** in this increment (rule 52). `WATCH_POLL` = 15 is the supervisor's choice, the same pace as `review-guard.py`'s `PR_HEAD_STEP`.

## Diagrams
`docs/diagrams/D-004-context-dfd.md` draws the flow your code makes true (line 155, quoted):

```mermaid
p_bridge_run -->|"SECRET: owner's gh login, GET only, the rule's reader in bridge_env: the wait before a CI watch (R-085)"| ext_github
```

The wait reads GitHub only through `bridge_env`'s readers, by GET, with the owner's `gh` login, and writes nothing to GitHub. No new flow is drawn: the watch's own edge (line 152) is unchanged.

## Requirements
1. **R1. `WATCH_POLL` and `watch_loop`.**
   - Add the module constant `WATCH_POLL = 15` and the function `watch_loop(argv, folder, limit, start)`, those exact names and that signature.
   - `argv` is the watch's words (`gh pr checks <n> ...`), `folder` the launch folder, and `limit` the run's seconds. `start(words, seconds)` runs one watch for at most `seconds` and returns its exit.
   - `watch_loop` returns the launcher's exit. It reads its clock with `time.monotonic()` and pauses with `time.sleep()`, both through the module's name `time` (never `from time import ...`), because the tests replace that name. It prints its lines on `sys.stderr`, each a whole line beginning `bridge-run: `, and flushes after each.
2. **R2. No wait without `--watch`.** Where `--watch` is not among the words, `watch_loop` returns `start(argv, limit)` with the words unchanged. It reads nothing from GitHub and prints nothing. Where the word after `checks` is not a pull-request number of ASCII digits, it prints `bridge-run: the watch names no pull request number; it starts without the wait` and returns `start(argv, limit)`.
3. **R3. A poll.** Each poll begins with one read of the pull request, `bridge_env.pull_refs("{owner}/{repo}", <n>, cwd=folder)`. The tests count polls by that read.
   - Where the pull request cannot be read, the poll has failed (R9).
   - Where its head is not the local head (`local_head(folder)`, kept), and the local head can be read, the head's lists prove nothing: the poll reads no list and the wait goes on. This is KP-051, kept from the old wait.
   - Otherwise the poll reads the head's lists with `head_state("{owner}/{repo}", <head>, cwd=folder)` and `latest_of_each`. Where they cannot be read, the poll has failed (R9).
4. **R4. The list, read once.** At the first poll that reads the pull request, the wait names what it waits for, as `prove_ci` does:
   - the base's contexts (`branch_rule` of the base), where it names some: the reading `the base branch's required contexts (<base>)`;
   - else, where the base's rule answers none, the default branch (`repo_settings`): where it is another branch and its rule names contexts, the reading `the default branch's required contexts (<default>)`;
   - else the reading `the workflow runs` (no list), where both answer none, or where the default branch is the base, or where a rule or the default branch's name cannot be read.

   The rule is not read again in the run.
5. **R5. Waiting on a list.** The wait ends where:
   - every required context has a latest check of that name, or a latest commit status of that context, on the head, whatever its class (a pending check holds its context);
   - or a latest check of the head, any check, is failed by `ci_class` (a timed-out check among them). The watch then starts at once, so that `--fail-fast` reports it.
6. **R6. Waiting on the runs (no list).** The wait ends where:
   - the head has at least one workflow run, and each latest run (`latest_of_each`) is completed or has a latest check listed whose `check_suite.id` is the run's `check_suite_id`. App checks no run made never count. A queued run with no check holds the wait. A run that completed without a check does not;
   - or a latest check of the head is failed by `ci_class`.
7. **R7. The watch started.**
   - Where the reading is the base's list, the watch starts as given.
   - In the three other cases (the default branch's list, the runs where both rules name none, a rule that cannot be read), it starts without the word `--required`, every other word unchanged and in order.
   - `start` gets the seconds left of `limit`, counted from the wait's start.
8. **R8. Started again (no list only).** Where the reading is the workflow runs, and the watch returned 0:
   - Poll again at once. Where every latest run of the head is completed, return 0.
   - Otherwise wait, at `WATCH_POLL`, until each latest run that is not completed has a latest check of its suite that is not completed, or every run is completed. Then start the same words again with the seconds left, print the line W5, and repeat.
   - A watch that returns any other exit ends `watch_loop` with that exit, and nothing is read after it.
   - Where the reading is a list, a watch's exit is the launcher's at once (no read after it).
9. **R9. A failed poll and the limit.**
   - A poll that fails (the pull request or the head's lists cannot be read) is retried at the next interval. The first failure prints W4, once per run.
   - The wait never sleeps past the limit: each pause is `min(WATCH_POLL, seconds left)`. Where the limit is reached before the wait ends, print W3 and return 124, starting no watch.
10. **R10. The lines** (the tests read the words in quotes; `<head12>` is the head's first twelve characters, `<s>` whole seconds waited in this wait):
    - W1, the wait ended: `bridge-run: waited <s>s for <reading> on head <head12>: <what>; the watch starts`. `<what>` is one of `every required context has a check or a status`, `every latest run has a check listed or is completed`, or `check <name> failed (<conclusion>)`.
    - W2, printed once before waiting wherever the reading is not the base's list: `bridge-run: <why>; waiting for <reading>`, followed by `, and the watch starts without --required` where `--required` was given. `<why>` is one of:
      - `the base branch <base> names no required context` (the default branch's list);
      - `the base branch <base> names no required context, nor does the default branch <default>`;
      - `the base branch <base> names no required context and is the default branch`;
      - `the rule of <branch> cannot be read (<source>: <reason>)`;
      - `the default branch cannot be read (<source>: <reason>)`.
    - W3, the limit: `bridge-run: LIMIT <limit>s reached while waiting for <reading> on head <head12>: <left>`. `<reading>` is `the pull request <n>` before any read of it, and `<head12>` is the local head where GitHub's is not read. `<left>` is one of:
      - `missing <context>, <context>...` (only those with neither check nor status);
      - `no workflow run started`;
      - `run <name> (<event>) has no check listed` (each such run, comma-separated);
      - `the pull request's head on GitHub is <gh head12>, not the pushed head <local head12>`;
      - `a poll failed (<source>: <reason>)`;
      - after a watch, `run <name> (<event>) is not completed and has no check listed that is not completed`.
    - W4, a failed poll: `bridge-run: a poll failed (<source>: <reason>); retrying every <WATCH_POLL>s until the limit`.
    - W5, started again: `bridge-run: the watch returned 0 while <k> latest run(s) of head <head12> are not completed; waited <s>s; the watch starts again`.
    - W6, the end after a watch: `bridge-run: every latest workflow run of head <head12> is completed; the watch's exit 0 stands`.
11. **R11. `main()`.**
    - For the watch kind, `main()` runs the watch through `watch_loop(<the words after -->, folder, limit, start)`. Its `start` runs one child exactly as `main()` runs one today, with `seconds` in place of `limit` in `proc.wait(timeout=...)`, and returns its exit; at that timeout it ends the run with 124 as today.
    - The first line `bridge-run: started <id>` stays first. The last line is `bridge-run: exit <rc>` with the run's final exit. The run log gets one entry with the run's total seconds and final exit, as today.
    - Where `watch_loop` returns 124 from the wait, no child was started: print `bridge-run: exit 124` and log it, as at the limit today.
    - The watch's command line, its kind, its default limit and its allow rule are unchanged, and a `gh pr checks` without `--watch` runs as before.
    - Delete `WATCH_WAIT`, `WATCH_STEP`, `wait_for_first_check` and its message, and `gh_pr_state` if nothing else uses it. Rewrite the docstring's sentence (lines 59-62) to say what the wait now does, in one paragraph.
12. **R12. The generated files.** Regenerate the command reference with `python tools/dump-cli.py`; `python tools/dump-cli.py --check` then exits 0. Regenerate MANIFEST with `python tools/make-manifest.py`.
13. **R13. Your tests.** Add your own cases to `tests/test_bridge_run.py` where the acceptance tests leave a gap you find. Examples:
    - R2's line for a watch with no number;
    - W6 printed;
    - the run log's single entry after a second watch, if you can reach it without `main()` in process.

    Drive `watch_loop` in process with the acceptance tests' `Case`, `Clock` and stand-in, on the recorded replies only. Import them from `test_program_watch_wait`; do not copy them.
14. **R14. Naming.** Every case you add names `R-085` (and D-004 where it draws the flow) in its name, docstring or a comment. A parametrized case has a plain `ids=` list.

## Acceptance criteria
- [ ] The Done section's pytest commands pass whole. `tests/test_program_watch_wait.py` gives no failure (it gave `30 failed, 2 skipped` before), the child-launcher case skipped on Windows only.
- [ ] The wait ends only as R5 and R6 say, starts the watch as R7 says, starts it again only as R8 says, and ends at the limit with 124 and W3 (R3-R9).
- [ ] A reply that cannot be read is never a pass or a list (R3, R4, R9).
- [ ] The lines are W1-W6 of R10.
- [ ] `main()` runs the watch through `watch_loop`, its first and last lines and its log entry as today (R11).
- [ ] `python tools/dump-cli.py --check` exits 0. MANIFEST is regenerated. `bridge/cursor-bridge/VERSION` reads `2026.11.12a` and is not listed by `git status --short`. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` prints `RESULT: SOURCES MATCH`.
- [ ] `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks` passes.
- [ ] R-085 (for the parts this brief serves) is fully met: no stand-in, placeholder or "later" text in the product code, and at least one test of yours names R-085.
- [ ] No option added. No new dependency, configuration key or environment variable. No new Semgrep high finding. No exception from a GitHub reply escapes as a traceback, and none is swallowed into a pass (ASVS L2).

## Constraints
- Do not add dependencies (the standard library only).
- Do not read or write any file outside this workspace (the folder you were started in). Everything you need is inside it, and everything you produce goes inside it.
- Do not edit `tests/test_program_watch_wait.py`, `tests/test_hotfix25a_roster_launcher.py` or anything under `tests/fixtures/github/`. If a case there seems wrong, stop and report it by its test id instead of working around it.
- If the brief, the rules, or the tooling got in your way (an instruction that contradicted another, a check that fired wrongly, a step that cost time for no reason), append one dated line describing it to `docs/BUILDER_NOTES.md`. Do not try to fix the tooling. Do the same for anything you learned about a defect or a pitfall: one dated line, so the supervisor can carry it forward.
- In any Markdown you write, never break a line inside a paragraph or a list item; one paragraph is one line. Line breaks only between blocks.
- **External service.** Every call to GitHub is `bridge_env`'s, with the time limit `GH_API_TIMEOUT` (30 seconds) and no retry of its own. The wait polls every `WATCH_POLL` (15) seconds up to the run's limit. Add no other remote call, no other wait and no other retry. Tests replay the recorded real replies in `tests/fixtures/github/` through the stand-in. Do not invent a reply's shape, fields, hosts or messages, and add no fixture.
- **Windowless launches.** Every process your code starts is created with `creationflags=NO_WINDOW`. In tests a launch needs no `creationflags` argument, because `tests/conftest.py` makes every launch windowless. Where a test does write one, that line carries the literal text `CREATE_NO_WINDOW` (`tests/test_tests_windowless.py` refuses it otherwise). Every subprocess and git call in a test has a timeout, and each child ends before its test does.
- Never start a server, a watcher or a daemon that outlives a test. Run every command synchronously, in the foreground, and wait for it to end. Leave nothing running when you finish.
- **Do NOT run the full `tests/` tree** (`python -m pytest`, `python -m pytest tests`, or any command that collects all of it). Run only the commands the Done section names, exactly as written, from the Workspace root, with no `PYTHONPATH` or other environment change. The whole suite is CI's run.
- **Never call `main()` of `bridge-run.py` in process** in a test of yours: on Windows it would put the test process in its job object.
- Do not refactor code outside the parts the Scope's limits name, even if it looks wrong.
- Never run the product, a migration, a seed or a test against the owner's live data or the real GitHub (Context, "Development data"). Do not run `gh` yourself.
- Follow existing conventions in the file you touch: ASCII program text and ASCII output, and results returned as values.
- These git commands are not yours to run: `commit`, `push`, `switch`, `checkout`, `merge`, `rebase`, `reset`, `stash`, `branch -d`, `worktree`. You read with `git status`, `git diff` and `git log` only. The single exception is `git restore bridge/cursor-bridge/VERSION` in the Done section. Your tests may run git inside their own temporary folders.
- **Mutation self-check (by hand, in process, no script in the diff).** The supervisor's mutants file sweeps the wait after your run, and every mutant must fail a test. Before you finish, apply each of these by hand, one at a time, run `tests/test_program_watch_wait.py`, and revert. List each in the report by its label, with the test id that caught it:
  - M1 the wait skipped without `--required`;
  - M2 a pending context taken as present on another head;
  - M3 a queued run taken as started;
  - M4 a run with no check taken as ready to watch;
  - M5 a completed run with no check holding the wait;
  - M6 the second watch not started;
  - M7 the interval dropped before the second watch;
  - M8 a non-zero watch started again;
  - M9 the limit ignored;
  - M10 a failed poll taken as an answer;
  - M11 `--required` kept in one of the three cases;
  - M12 the default branch not read;
  - M13 a failed check not starting the watch at once;
  - M14 the head's mismatch ignored;
  - M15 W4 printed at every failed poll;
  - M16 a named list read again after the watch.

  A mutant no test catches is a gap: add a case for it (R13), or report it if you cannot.
- **Known failures.** On the checkpoint code, `tests/test_program_watch_wait.py` gives `30 failed, 2 skipped`. None is known in the other files of the Done section. If a case fails that your change did not cause, report it by its test id with its failure lines and fix none.
- Prefer reuse over new code: `bridge_env`'s readers and `ci_class` for every GitHub read and class, `local_head` for the local head, `main()`'s present child start for `start`, the standard library, and the minimum that meets the acceptance criteria (the frozen `minimal-code.mdc` is in force). This never overrides a security, observability or accessibility requirement stated above.
- Rules in force for you: `.cursor/rules/secure-coding.mdc`, `.cursor/rules/workspace-boundary.mdc` and the frozen `minimal-code.mdc`.

## Done
Your report is the file `handoff/TASK-065-r1-report.md`, which you write as you go: what you did, what you changed, what you ran and what it printed, and what you could not do, so that nothing of it is lost if your run ends early. It names no computer path and no user name: write `<Workspace>` for the repository folder and `<tmp>` for a temporary folder, including in quoted command output.

When you finish, it holds:
- a list of every file you changed;
- a one-paragraph summary of what you did;
- for R1-R14, one line each on what meets it, naming the functions and their lines as the file stands after your change;
- the mutation self-check list, M1-M16, each with the test id that caught it (or `not caught` and why);
- every command of the list below with its output;
- a section headed exactly `Assumed, not verified`, as the report's last section.

The `Assumed, not verified` section lists every fact this change relies on that neither this brief nor the existing code settled, and that you did not confirm: the shape of a GitHub reply beyond the recorded ones, an ambiguous requirement you resolved one way, a platform or library behaviour you expected, a value you chose. Examples:
- that `gh pr checks --watch` started again on the same head reports the run's present state and does not end at once on the earlier return;
- that a watch whose `--required` was removed still honours `--fail-fast`.

One item per line: what you assumed · why · what would confirm it. If there are none, write `Assumed, not verified: none`. Be specific: "edge cases" or "error handling" is not an item.

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
- A claim that a check passed quotes the output line that shows it. A number of failing or skipped cases is backed by the pytest lines naming them.
- Each mutation is listed by its label and text, with what caught it.
- A command you did not run is written `not run`, never described as run.
- Write the report's results after step 10, naming the commit its counts belong to (`git rev-parse HEAD`) and whether the working tree then held uncommitted changes (`git status --short`).

Your last message is the summary and the report file's path, and nothing follows it. The supervisor reads only the last message, and a message printed earlier and then followed by more work is lost.
