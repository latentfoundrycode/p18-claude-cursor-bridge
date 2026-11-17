---
record: brief
header: 1
id: "TASK-083"
round: 1
satisfies: [R-083]
scope: ["bridge/cursor-bridge/review-guard.py", "bridge/cursor-bridge/permission-guard.py", "bridge/cursor-bridge/MANIFEST.json", "docs/cli-reference.json", "docs/CLI_REFERENCE.md", "tests/test_program_ready.py", "tests/test_review_guard.py", "tests/test_permission_guard.py", "tests/test_release_s_records_gate.py", "tests/test_d003_review_round_states.py", "tests/fixtures/github/", "docs/diagrams/D-003-review-round-states.md", "docs/BUILDER_NOTES.md", "handoff/TASK-083-r1-report.md"]
merge_unit: null
blocking_class: null
---
# TASK-083: `ready`, the proof that CI passed, as a program and a record the merge is held on (R-083)

Round cause: first round (no earlier round)

## Objective
Today the supervisor confirms by hand, after the CI watch, that CI passed on a pull request's head, and the permission guard lets a `gh pr merge` through on the premerge record alone. The field met a watch that returned green before CI had run (two app checks green while the workflow's jobs were still queued). This increment makes the proof a program and a second record the merge is held on. `review-guard.py` gains the command `ready <pr>`. It reads the pull request's head and base on GitHub through `bridge_env`'s reader (TASK-064, merged), compares that head with the local HEAD as `premerge` does, and requires the premerge record for that head. It then proves CI on the head from the head's latest checks, commit statuses and workflow runs, by the base branch's required contexts, by the default branch's where the base names none, or by the workflow runs where neither names one. On READY (exit 0) it writes the ready record `<git common dir>/bridge/ready/<pr>-<head>`. NOT READY (exit 1) and CANNOT CHECK (exit 2) write nothing. `premerge-records <pr>` makes the same check before it writes, and writes both records or neither. `permission-guard.py` takes the pull request's number from the merge command and refuses a merge that names no number, or that has no ready record for that number and the head it names. The reader in `bridge_env.py` is already built and does not change here. The launcher's wait before the watch (TASK-065) and the loop's text (TASK-082) are other increments.

Satisfies: R-083 - One reader of a repository's branch rule, and the proof that CI passed as a program (T-CONTEXT, C7): [...] `review-guard.py ready <pr>` prints `READY` (exit 0) and writes the ready record for the pull request and its head when the pull request's head on GitHub is the local branch's head, the premerge record for that head stands and CI is proven on it, read from the head's workflow runs, checks and commit statuses, of which only the latest of each source counts (a run by its workflow and event, by run number then attempt; a check a workflow run made only where its run, found by the check suite both name, is a latest run, and of its name there the last one, a check not completed after every completed one, the completed by start time then id; a check no workflow run made by its name and app; a status by its context), every result one of four, passed (completed with `success`), pending (not completed), skipped (concluded so: passing a required context under its condition, elsewhere neither proving nor failing) and failed (every other completed conclusion or state): every required context of the base, or of the default branch where the base names none, held by at least one check or status of that name on the head, by a check of the app alone where the rule names one, every latest one of that name passed, a `skipped` check passing where no latest check and no latest run of the head failed, or, where both branches were read and neither names one, the head's workflow runs (of the latest runs at least one succeeded, none pending, none failed, and no latest check or status of the head failed), the three lists read to their last page and a list not read whole being cannot read, the line saying which reading it used; `NOT READY` (exit 1) names each context or run that is missing, pending or failed, or the head that moved, and `CANNOT CHECK` (exit 2) is the answer where GitHub, a branch's rule, the pull request or the premerge record cannot be read, a rule that cannot be read never answered from the runs, neither writing anything; the permission guard refuses a `gh pr merge` that has no ready record for the pull request's number and the head it names, the record of another pull request with the same head proving nothing and a merge that names no number refused, as it refuses one without the premerge record; `premerge-records <pr>` makes the same check and writes both records or neither; the guard's docstring lists `ready`'s exits (J14); [...]. (Full text: its row in `docs/REQUIREMENTS.md`. This brief serves `ready`, its record, the permission guard's refusal, `premerge-records`' check and the docstring. The reader, the conformance row and the auto-merge line were TASK-064's. The loop's step 8, the policy and the digest are TASK-082's.)

## Scope
Files and directories you may create or modify:
- bridge/cursor-bridge/review-guard.py
- bridge/cursor-bridge/permission-guard.py
- bridge/cursor-bridge/MANIFEST.json
- docs/cli-reference.json
- docs/CLI_REFERENCE.md
- tests/test_program_ready.py
- tests/test_review_guard.py
- tests/test_permission_guard.py
- tests/test_release_s_records_gate.py
- tests/test_d003_review_round_states.py
- tests/fixtures/github/
- docs/diagrams/D-003-review-round-states.md
- docs/BUILDER_NOTES.md
- handoff/TASK-083-r1-report.md

Limits on these paths:
- `tests/test_program_ready.py`, everything under `tests/fixtures/github/` and `tests/test_d003_review_round_states.py` belong to the supervisor: the acceptance tests, the recorded replies, and D-003's tests already written for this increment. Read and run them. Edit none of them. Add no file under `tests/fixtures/github/` and delete none.
- `docs/diagrams/D-003-review-round-states.md` is in Scope only because the plan lists it. The supervisor edits it in a commit of its own after your build. Do not touch it.
- `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` change only by running `python tools/dump-cli.py` (Done). Afterwards `python tools/dump-cli.py --check` must exit 0. Never edit either by hand.
- `bridge/cursor-bridge/MANIFEST.json` changes only by running `python tools/make-manifest.py` (Done). Never edit it by hand. `bridge/cursor-bridge/VERSION` is outside Scope and reads `2026.11.12a`. `make-manifest.py` rewrites its line endings, so restore it with `git restore bridge/cursor-bridge/VERSION` right after (Done). Change it in no other way.
- `tests/test_permission_guard.py`: the case `test_a_merge_with_the_premerge_record_passes_and_one_without_is_refused` (line 194) and its fixture `recorded_repo` (lines 25-34) pin a merge allowed on the premerge record alone. Rewrite them **first**, before any product change, so that the repository holds both records: `.git/bridge/ready/12-<SHA>` beside `.git/bridge/premerge/<SHA>`. Keep the abbreviated-sha case (line 201) and every other assertion. You may add your own cases.
- `tests/test_review_guard.py`: you may add your own cases. You may change an existing case only where it pins the old rule. That covers two kinds of case: (a) a case that calls `premerge-records` with a pull request number and expects a record written (it now needs a READY head: use `use_standin` and `ready_routes` from `tests/test_program_ready.py`, as the supervisor did in `tests/test_program_release_s_rows.py` lines 53-56); (b) the case `test_premerge_and_the_permission_guard_agree_end_to_end` (line 278). Case (b) runs `premerge` and expects the permission guard to allow `gh pr merge 12 --squash --match-head-commit <sha>` from the checkout, a subfolder and a linked worktree (lines 291-296), on the premerge record alone. Rewrite it so the ready record `12-<sha>` stands in the repository's common git folder before `allowed` is asked, and keep every assertion (outside the repository it is still refused). Name each changed case and the change in the report.
- `tests/test_release_s_records_gate.py`: add your own cases where needed. Change an existing case only where it calls `cmd_premerge_records(..., "12")` and expects a record written: `test_with_the_pull_request_the_record_is_written_and_the_permission_guard_lets_the_merge_through` (line 339) and `test_a_lagging_head_is_read_again_and_one_that_still_differs_is_not_ready` (line 381). Each then needs a READY head (`use_standin` and `ready_routes` as above), and every assertion stays. Name each changed case in the report.
- `bridge/cursor-bridge/review-guard.py`: the module docstring (lines 1-91), a new `ready` command and the function that proves CI, `cmd_premerge_records` (line 1457) and `main` (line 1539). `cmd_premerge` (line 1185), `pr_head` (line 1173), `pr_state` (line 1441) and every other command, message and exit stay as they are.
- `bridge/cursor-bridge/permission-guard.py`: a new `ready_recorded` beside `premerge_recorded` (line 2426), and `merge_reason` (line 2451). Nothing else (plan's Scope note: "the merge's rule reads the ready record beside the premerge record, nothing else").

The supervisor already changed some tests, before this brief, that the plan's Scope omits but that the new rule reaches: `tests/test_allowlist.py` (a merge's `<n>` read as the number 12, and `ready_recorded` stubbed beside `premerge_recorded`, lines 108-112), `tests/test_program_branch_rule.py` and `tests/test_program_release_s_rows.py` (`premerge-records` on a READY head, both records expected). They are outside Scope. Run them and edit none of them.

Do not modify anything else.

## Out of scope
- .env and anything under secrets/
- CI configuration
- docs/ and handoff/, except the files the Scope section names. Every record under docs/ is the supervisor's.
- `bridge/cursor-bridge/bridge_env.py` and every other program under `bridge/cursor-bridge/`. The reader is TASK-064's and must not change. If it lacks something you need, stop and report it.
- `bridge/cursor-bridge/bridge-run.py` and the launcher's wait before the watch (TASK-065).
- The loop's text, the policy and the digest (TASK-082). D-003 (the supervisor's commit).
- `tools/make-manifest.py`, `tools/dump-cli.py`, and every test file not named in Scope (you run some of them, Done, and edit none).
- Any mutation script. The mutants file and the mutation run are the supervisor's, after your run.

## Context
**The design that binds this increment:** `docs/DESIGN.md`, "Change: the program release", the bullet group **The review guard, `review-guard.py`, and the rule's reader in `bridge_env.py`** (line 329), with the bullets *The rule's reader* (line 330), *T-CONTEXT* (line 331, the whole of `ready`: read it whole) and *C7* (line 332). Also *J14* inside *C23* (line 334): the exit lists of `review-guard.py`'s docstring are brought to its code (`ready`'s three exits). The F2 bullet (line 327) is the launcher's (TASK-065) and is context only. The decision row is in `docs/INVENTORY.md`, Decisions, the row beginning "The proof that CI passed is a program, and the branch rule has one reader" (line 219). The plan entry is `docs/BUILD_PLAN.md`, `### TASK-083` (line 1811): Scope, Scope notes and Done when.

**The supervisor's acceptance tests.** `tests/test_program_ready.py` fixes the interface and the exact lines; read it whole. Every case runs on GitHub's replies recorded from this repository (`tests/fixtures/github/`). The head states `ready-*.json` are built from TASK-064's captured replies, and each header names the captured reply and the fields changed. They are answered by TASK-064's stand-in `gh` (`tests/test_program_branch_rule.py`'s `STANDIN`) with one addition: the captured head sha (forty `1`s) is replaced in every reply by the case's local head. The test replaces `bridge_env.GH_COMMAND` on the guard's own `bridge_env` module (`use_standin`, line 71). A path the stand-in has no route for answers GitHub's 404 `Not Found`. Anything but a plain GET exits 99. The `case` fixture (line 89) makes a scratch repository, writes the premerge record for its head, sets `PR_HEAD_WAIT` to 0 and calls `guard.main()` with `argv = ["review-guard.py", "ready", <pr>]`. `records_case` (line 431) replaces `pr_state` and calls `cmd_premerge_records(repo, "12")`. The permission-guard cases (lines 337-425) run `permission-guard.py` as a child with a hook payload on both shells (`Bash`, `PowerShell`). The supervisor's section at the end of `tests/test_d003_review_round_states.py` (lines 677-758) holds one test per new D-003 state and transition, on the same fixtures.

**Known counts.** On the checkpoint code, `tests/test_program_ready.py` gives `58 failed, 7 passed`. The seven that pass are: the fixtures' headers; a merge with both records passing, on both shells; the ready record alone refused, on both shells; the unchanged forms, on both shells. All 65 must pass. The supervisor's red run (`run/agent/TASK-083-red.out`) over `tests/test_program_ready.py`, `tests/test_allowlist.py`, `tests/test_program_branch_rule.py`, `tests/test_program_release_s_rows.py` and `tests/test_d003_review_round_states.py` gave `173 failed, 341 passed, 20 skipped`. All of them must pass after your build. The skips are prose lines of `tests/test_allowlist.py` and stay skipped.

**The code as it stands** (line numbers verified on the checkpoint).
- `bridge/cursor-bridge/review-guard.py`:
  - The module docstring is lines 1-91. Its second paragraph (lines 5-8) is the usage block `main` prints (`print(__doc__.split("\n\n")[1])`, line 1548). It lists `snapshot`, `verify`, `premerge` and `premerge-records [<pr>]`. The `premerge-records` paragraph (lines 62-78) says, at lines 64-66, that the pull request "merges without the cross-family round, on CI, which the branch rule holds, and one Review A read, which is the supervisor's step: this command checks neither". The exit list is at lines 80-85.
  - `import bridge_env` is at line 104. `PR_HEAD_WAIT, PR_HEAD_STEP = 90, 15` is at line 112.
  - `pr_head(pr, root)` (line 1173) runs `gh pr view`. `cmd_premerge(nnn, cwd, pr=None)` (line 1185) compares heads at lines 1230-1246: it re-reads `while err is None and remote_head != head and waited < PR_HEAD_WAIT`, calling `time.sleep(PR_HEAD_STEP)` each time. It writes `<common>/bridge/premerge/<head>` at lines 1251-1258, prints the merge line at 1259 and the auto-merge line at 1260-1269 (through `bridge_env.repo_settings("{owner}/{repo}", cwd=cwd)`).
  - `pr_state(pr, root)` (line 1441) runs `gh pr view --json headRefOid,baseRefOid,baseRefName,files`.
  - `cmd_premerge_records(cwd, pr=None)` (line 1457). Its docstring (lines 1458-1465) says at lines 1460-1461 "CI is held by the repository's branch rule and the one Review A read by the supervisor's step, neither is checked here". Its head wait is at lines 1475-1486, its FULL GATE and CANNOT CHECK answers at lines 1487-1511, and SHORT GATE without a pull request at lines 1512-1515. It writes the premerge record at lines 1516-1523 and prints `review-guard: OK - records only, ...` (1524), the merge line (1525) and the auto-merge line last (1526-1535).
  - `main()` (line 1539) dispatches `premerge-records` first (lines 1541-1546, `CANNOT VERIFY` on `RuntimeError`/`TimeoutExpired`/`OSError`). It then prints the usage and returns 2 for any other first word, and only then checks the review-name grammar (line 1550, exit 125).
- `bridge/cursor-bridge/bridge_env.py` (TASK-064, read only). The names you call:
  - `GH_COMMAND = ["gh"]` (line 3838), `GH_API_TIMEOUT = 30` (line 3839), `ANSWER_VALUE = "value"`, `ANSWER_NONE = "none"`, `ANSWER_CANNOT = "cannot read"` (lines 3840-3842). `_gh_get(path, cwd=None)` (line 3887) is the one GET with that limit and no retry.
  - `branch_rule(repo, branch, cwd=None)` (line 4005) returns `answer`, `reason`, `source` (`protection` or `rules`) and `contexts`, a list of `{"context": str, "app_id": int or None}`.
  - `repo_settings(repo, cwd=None)` (line 4051) returns also `allow_auto_merge` and `default_branch` (source `repo`).
  - `pull_refs(repo, number, cwd=None)` (line 4067) returns also `base` and `head` (source `pull`). It accepts a positive int or a string of ASCII digits.
  - `head_state(repo, sha, cwd=None)` (line 4143) returns also `checks`, `statuses`, `runs` (source `checks`, `statuses` or `runs`), each list read to its last page.
  - `latest_of_each(state)` (line 4283) returns the same three keys holding only the latest of each source.
  - `ci_class(item, kind)` (line 4348), with `kind` one of `"check"`, `"run"`, `"status"`, returns `"passed"`, `"pending"`, `"skipped"` or `"failed"`.
  - Every reader returns a dict and never raises.
- `bridge/cursor-bridge/permission-guard.py`:
  - `GH_VALUE_FLAGS` (line 68) is quoted: `("-t", "--subject", "-b", "--body", "-F", "--body-file", "-A", "--author-email", "-R", "--repo", "--match-head-commit", "--hostname")`.
  - `PREMERGE_DIR = os.path.join("bridge", "premerge")` (line 75). `_time_left()` (line 203) is the hook's read budget.
  - `merge_reason` is called from `check` at line 2312.
  - `premerge_recorded(sha, cwd)` (lines 2426-2448) checks `[0-9a-fA-F]{7,64}`, runs `git -C <cwd or .> -c core.fsmonitor=false rev-parse --git-common-dir` with `timeout=_time_left()` and `creationflags=NO_WINDOW`, and returns False on any failure. It returns `any(n.lower().startswith(sha.lower()) for n in names)` over the folder's names.
  - `merge_reason(args, cwd)` (lines 2451-2472) takes the words after `merge`. It refuses `--admin`, allows `--disable-auto`, allows `--help`/`-h` unless it is a flag's value, then reads `--match-head-commit` (refusing it absent or malformed). Then it refuses without the premerge record with the message `gh pr merge for %s without the pre-merge check's record: run python ~/.claude/cursor-bridge/review-guard.py premerge <nnn> <n> in the checkout first (it writes the record when it prints OK)`.
  - `main()` (line 2480) fails open on unreadable hook input.
- `tests/test_allowlist.py` lines 98-115 (the supervisor's, outside Scope) replaces `guard.premerge_recorded` with `lambda sha, cwd: True` and `guard.ready_recorded` with `lambda pr, sha, cwd: True`, and rewrites `gh pr merge <n>` to `gh pr merge 12` in every instructed command. Every instructed command must then pass `guard.check(runnable, None)`.

**External service and the remote-wait limits (the trait External services).** GitHub's REST API, read through `gh api`, is a service run by others.
- Every remote call this increment makes is `bridge_env`'s `gh api` GET, with its time limit `GH_API_TIMEOUT` = 30 seconds per call and a retry limit of 0 (no retry). A reply that is not a success is read once and answered as cannot read.
- The head comparison re-reads the pull request at most every `PR_HEAD_STEP` = 15 seconds, up to `PR_HEAD_WAIT` = 90 seconds in all, as `premerge` does.
- Add no other remote call, no other wait, no `sleep` and no retry. `permission-guard.py` makes no remote call at all.
- "Done" means passing on the recorded replies through the stand-in, never on a reply you invent. If a case you need has no recorded reply, do not make one up and add no fixture. Stop and report it: a capture is the supervisor's to run. No test of yours, and no command you run, calls the real GitHub.

**Security context.** The ASVS level is 2 (INVENTORY, Decisions). `.cursor/rules/secure-coding.mdc` is in force for you. The trust boundaries:
- GitHub's replies are outside input. A reply the reader cannot read is cannot read, never none and never a pass. Reasons are printed as the reader clipped them (bounded, ASCII, credential shapes removed), as text only.
- The hook's command text is outside input to `permission-guard.py`. A merge whose number cannot be read is refused, never allowed.
- The guard's own records under `<git common dir>/bridge/` are inputs, not trusted state (KP-077). A record of another head or another pull request proves nothing. A record that is absent or unreadable fails closed. That an agent can write `.git/bridge` stays the recorded lead it is.
- The reads use the owner's `gh` login, GET only. No token, account name or repository name is printed beyond what the reader already prints. No reply is written to a file. The ready record holds `pr`, `head`, `reading` and `written`, nothing from GitHub's replies beyond that.

**Development data.** The inventory's decision (`docs/INVENTORY.md`, Decisions, the row beginning `Development data:`) reads: "the dev build is the Workspace sources under `bridge/`; a session in the repo always runs the *installed* bridge (`~/.claude`), never the one being edited, and installs reach running projects only through the owner's install run sheet". For you this means: run the programs only from tests, on scratch repositories under pytest's `tmp_path`, on the recorded replies. Never install anything. Never copy anything under `~/.claude`. Never run `review-guard.py` or `permission-guard.py` against this repository's own folder or its GitHub repository.

**Host.** Windows 11, with Python as on the owner's interpreter. `gh` 2.97.0 was the version of the captures; do not run `gh` yourself. This session has no `claude` on PATH (`claude --version`: command not found), so no Claude Code version is tested on. The permission guard's hook is exercised only through the tests' child processes.

**No owner's value** in this increment (rule 52). The 30-second limit and the 90/15-second head wait are the existing code's, fixed by the interface.

## Diagrams
`docs/diagrams/D-003-review-round-states.md` defines the states `ready_check` (row at line 27, a choice), `ready_recorded` (line 28) and `records_premerged` (line 31), and the edges at lines 86-106. The edges your code must make true, quoted:

```mermaid
        premerged --> premerged : by this design gh pr merge before READY refused by the permission guard, no ready record for the match-head-commit head, its message naming review-guard.py ready, nothing written
        premerged --> ready_check : by this design the CI watch returns, review-guard.py ready with the pull request number
        ready_check --> ready_recorded : READY exit 0, [...] the ready record for the pull request and the head written beside the premerge record
        ready_check --> premerged : NOT READY exit 1, a required check context or a workflow run missing, pending or failed on the head, each named, nothing written and nothing removed, back to the watch
        ready_check --> verified_ok : NOT READY exit 1, the head moved, [...] nothing written
        ready_check --> premerged : CANNOT CHECK exit 2, GitHub, a rule of the base or of the default branch where the base names none, the pull request or the premerge record cannot be read, a stop and never a pass, nothing written and nothing removed
        ready_recorded --> [*] : by this design merged, [...] the permission guard reads the premerge record and the ready record for that pull request and head, the number taken from the merge command
    short_gate --> records_premerged : premerge-records with the pull request number after CI, OK - records only, [...] by this design the ready record for the pull request and the head too, both or neither, the merge command printed
```

The edge `premerged --> [*] : as built today and removed by TASK-083, [...] the permission guard reads the premerge record alone` (line 88) is the behaviour your change removes. The supervisor removes the edge from the diagram after your build; do not edit the file.

`docs/diagrams/D-004-context-dfd.md` lines 190-192, quoted:

```mermaid
p_review_guard -->|"SECRET: owner's gh login, GET only, the rule's reader in bridge_env: ready, premerge-records (R-083)"| ext_github
ext_github -->|"a branch's required check contexts, the default branch's contexts, allow_auto_merge, the PR's head, its checks, commit statuses and workflow runs"| p_review_guard
p_review_guard -->|"READY, NOT READY, CANNOT CHECK; the auto-merge line"| p_supervisor
```

Every call is a GET through `bridge_env`; nothing is sent to GitHub but the path. Add no import between bridge programs: `review-guard.py` keeps its plain `import bridge_env`, and `permission-guard.py` gains no import of another bridge program. Everything the diagrams do not fix is yours to decide. If the task cannot be done within them, stop and report the conflict instead of deviating.

## Requirements
Use the labels R1-R14 in your report. The lines quoted below are pinned by the acceptance tests.

1. **R1. The command.**
   - `review-guard.py` gains `python ~/.claude/cursor-bridge/review-guard.py ready <pr>`. `main()` dispatches `ready` **before** the review-name grammar check (line 1550).
   - Any argument count other than exactly one after `ready` prints the usage text and exits 2.
   - An exception raised inside `ready` answers `review-guard: CANNOT CHECK - pull request <pr>: <reason>` with exit 2, never a traceback.
   - The module docstring's usage block (its second paragraph, which `main` prints) gains the line for `ready <pr>`. The usage line of `premerge-records [<pr>]` stays (`tests/test_release_s_records_gate.py` line 417 reads it).
   - The docstring states `ready`'s exits and its record, with these exact words somewhere in it: `READY (exit 0)`, `NOT READY (exit 1)`, `CANNOT CHECK (exit 2)`, `bridge/ready/<pr>-<head>` (J14).
   - Correct the sentence that says CI is not checked by `premerge-records` in both places: the module docstring (lines 64-66) and the function's docstring (lines 1460-1461).
2. **R2. The number.** The pull request number must be one or more ASCII digits `0`-`9`. Anything else (a branch name, `task-001`, a URL, an empty word) is CANNOT CHECK with exit 2, and no `gh` call is made at all. The number is used as given, as text, in the record's name and the lines.
3. **R3. The premerge record.**
   - `ready` requires the premerge record for the local head (`git rev-parse HEAD`): the file `<git common dir>/bridge/premerge/<head>` must be present and readable as a JSON object.
   - A record of another head is no record.
   - Absent or unreadable is CANNOT CHECK, exit 2, with the word `premerge` in the line. Unreadable includes the folder itself being unreadable or a file in its place.
4. **R4. One CI proof, through the reader.** The CI proof is one function shared by `ready` and `premerge-records` (its name is yours). Every GitHub read goes through `bridge_env`, with the repository named `"{owner}/{repo}"` and the checkout as `cwd`, as `premerge`'s auto-merge line already does:
   - `pull_refs` for the pull request's base and head (never `gh pr view`, never `pr_head`);
   - `branch_rule` for the base branch;
   - `repo_settings` for the default branch's name, only where the base names none;
   - `branch_rule` for the default branch, where it differs from the base;
   - `head_state` for the head's checks, statuses and runs;
   - `latest_of_each` to keep the latest of each source, and `ci_class` to class each entry.

   The proof makes no `gh` call of its own. The head comparison is `premerge`'s: while GitHub's head differs from the local one, re-read every `PR_HEAD_STEP` up to `PR_HEAD_WAIT`.
5. **R5. The readings, in this order.**
   - The base's rule cannot be read: CANNOT CHECK.
   - The base names contexts (answer value): the contexts reading, with the reading phrase `the base branch's required contexts (<base>)`.
   - The base names none: read the default branch's name with `repo_settings`. If it cannot be read: CANNOT CHECK.
   - The default branch's rule cannot be read: CANNOT CHECK.
   - The default branch names contexts: the contexts reading with `the default branch's required contexts (<default>)`.
   - Neither names one (both read, both none, or the default branch is the base): the runs reading, `the workflow runs`.

   A rule that cannot be read is never answered from the runs.
6. **R6. The contexts reading.** For each required context (its name and `app_id` from the reader):
   - Its holders are the latest checks of that name (only those whose app id, `app.id`, is the rule's app where the rule names one), and, only where the rule names no app, the latest commit statuses of that context.
   - No holder: `missing`. Where the rule names an app and a latest status of that name stands, add the note `(a commit status carries no app)`.
   - Any holder failed: `failed`. Where a failing holder concluded `neutral`, add the note `(neutral: stricter than GitHub)`.
   - Otherwise any holder pending: `pending`.
   - Otherwise a skipped holder passes only where no latest check and no latest run of the head is failed by `ci_class`. If one is, the context is `failed` with the note `(skipped beside a failure)`.
   - Otherwise: passed.

   READY only where every context passed.
7. **R7. The runs reading.**
   - Every latest run that is pending or failed is an item `run <name> (<event>): <class>`.
   - Every latest check that is failed is `check <name>: failed`.
   - Every latest status that is failed is `status <context>: failed`.
   - Where no latest run passed, add the item `no workflow run succeeded`.
   - A skipped run or check neither proves nor fails.

   READY only where there is no item.
8. **R8. The lines, exactly.** One verdict line per run, never two:
   - `review-guard: READY - pull request <pr>, head <first 12 of head>, <reading>`
   - `review-guard: NOT READY - pull request <pr>, head <12>, <reading>: <item>: <class>[; <item>: <class>]...`. A context's item is its name. A note goes in parentheses after the class.
   - `review-guard: NOT READY - pull request <pr>, head <local 12>: the head moved (GitHub's head is <GitHub's 12>)`
   - `review-guard: CANNOT CHECK - pull request <pr>: <reason>`. Where the reader answered cannot read, the reason names the reader's source and its reason in the form `(<source>: <reason>)`. The sources are `protection`, `rules`, `repo`, `pull`, `checks`, `statuses`, `runs`. For a rule the reason is `the base branch's rule cannot be read (<source>: <reason>)` or `the default branch's rule cannot be read (<source>: <reason>)`.
9. **R9. The record.**
   - READY (exit 0) writes `<git common dir>/bridge/ready/<pr>-<head>` beside the premerge record. It is a JSON object with the keys `pr`, `head`, `reading` and `written`.
   - A write failure is CANNOT CHECK, exit 2.
   - NOT READY (exit 1) and CANNOT CHECK (exit 2) write nothing and remove nothing.
   - A ready record of another head or another pull request is left in place and proves nothing.
10. **R10. `premerge-records <pr>`.**
    - Every existing check and answer is unchanged: SHORT GATE, FULL GATE, the head wait and its NOT READY line, and the CANNOT CHECK cases.
    - Only where they all pass, and before any record is written, it runs the same CI proof. The proof here has no premerge-record precondition, since this command writes that record.
    - READY: print the READY line, then write both records (the premerge record as today, and `ready/<pr>-<head>`). If either write fails, remove the one that was written and answer CANNOT CHECK, exit 2.
    - NOT READY (exit 1) or CANNOT CHECK (exit 2): print that line and write neither record.
    - Its OK line, its merge line and its auto-merge line stay, the auto-merge line last.
    - Without a pull request number nothing changes. `premerge` (line 1185) is untouched.
11. **R11. The permission guard.**
    - Add a module-level function `ready_recorded(pr, sha, cwd)` (that exact name and signature, since `tests/test_allowlist.py` replaces it) beside `premerge_recorded`.
    - It reads `<git common dir>/bridge/ready` the way `premerge_recorded` reads its folder: the same time budget through `_time_left`, the same `git rev-parse --git-common-dir`, failing closed to False.
    - It is true where a name starts with `<pr>-<sha lower-cased>`, so an abbreviated sha matches as it does today.
    - `merge_reason` keeps its checks of `--admin`, `--disable-auto`, `--help`/`-h` and `--match-head-commit` unchanged and first.
    - Then it reads the pull request's number: the first word after `merge` that is neither an option (a word starting with `-`) nor the value of an option in `GH_VALUE_FLAGS` given as a separate word. Where there is none, or it is not ASCII digits (a branch, a URL), refuse with a message holding the form `gh pr merge <n> --squash --match-head-commit <sha>`.
    - Then it calls `premerge_recorded`, as today, with its message unchanged.
    - Then it calls `ready_recorded(number, sha, cwd)`. If that is false, refuse with a message naming `review-guard.py ready <n>` with the number filled in. Example: `gh pr merge for <sha12> without the ready record of pull request 12: run python ~/.claude/cursor-bridge/review-guard.py ready 12 after the CI watch`.
    - Every other refusal and allowed form is unchanged, and unreadable hook input still fails open.
12. **R12. The generated files.** Regenerate the command reference with `python tools/dump-cli.py`; `python tools/dump-cli.py --check` then exits 0. Regenerate MANIFEST with `python tools/make-manifest.py`.
13. **R13. Your tests.** Rewrite the pinned cases first, as the Scope's limits say: `tests/test_permission_guard.py`'s case and fixture, `tests/test_review_guard.py`'s end-to-end case, and the two `tests/test_release_s_records_gate.py` cases. Add your own cases where the acceptance tests leave a gap you find. Examples:
    - `ready_recorded` failing closed outside a repository;
    - `premerge-records` where the ready record's write fails, leaving neither record;
    - `ready` with no argument or two printing the usage with exit 2;
    - an exception inside `ready` answering CANNOT CHECK.

    Drive the guard in process with `use_standin` on the recorded replies only, never through the real `gh`.
14. **R14. Naming.** Every case you add names `R-083` (and the D-003 element where it holds a state or transition) in its name, docstring or a comment. A parametrized case has a plain `ids=` list.

## Acceptance criteria
- [ ] The Done section's pytest command passes whole. `tests/test_program_ready.py` gives 65 passed (it gave `58 failed, 7 passed` before). The five supervisor files of the red run, which gave `173 failed, 341 passed, 20 skipped`, give no failure.
- [ ] `ready` answers READY, NOT READY and CANNOT CHECK with the exact lines of R8, writes the ready record only on READY, and never removes a record (R2-R9).
- [ ] A rule that cannot be read is CANNOT CHECK and never the runs' reading. A list not read whole is cannot read. A number that is not digits asks GitHub nothing (R2, R5).
- [ ] `premerge-records <pr>` writes both records or neither, its earlier answers unchanged and its auto-merge line last (R10).
- [ ] The permission guard refuses a merge with no number (with the form), or without the ready record of that number and head (naming `review-guard.py ready <n>`), after the premerge check. Every other form is unchanged (R11).
- [ ] The docstring lists `ready`'s usage, its three exits and its record (R1, J14).
- [ ] `python tools/dump-cli.py --check` exits 0. MANIFEST is regenerated. `bridge/cursor-bridge/VERSION` reads `2026.11.12a` and is not listed by `git status --short`. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` prints `RESULT: SOURCES MATCH`.
- [ ] `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks` passes.
- [ ] R-083 (for the parts this brief serves) is fully met: no stand-in, placeholder or "later" text in the product code, and at least one test of yours names R-083.
- [ ] No option added beyond the `ready` command. No new dependency, configuration key or environment variable. No new Semgrep high finding. No exception from a GitHub reply or a record escapes as a traceback, and none is swallowed into a pass (ASVS L2).

## Constraints
- Do not add dependencies (the standard library only).
- Do not read or write any file outside this workspace (the folder you were started in). Everything you need is inside it, and everything you produce goes inside it.
- Do not edit `tests/test_program_ready.py`, `tests/test_d003_review_round_states.py` or anything under `tests/fixtures/github/`. If a case there seems wrong, stop and report it by its test id instead of working around it.
- If the brief, the rules, or the tooling got in your way (an instruction that contradicted another, a check that fired wrongly, a step that cost time for no reason), append one dated line describing it to `docs/BUILDER_NOTES.md`. Do not try to fix the tooling. Do the same for anything you learned about a defect or a pitfall (a cause you found, a platform quirk that cost you a round): one dated line, so the supervisor can carry it forward.
- In any Markdown you write, never break a line inside a paragraph or a list item; one paragraph is one line. Line breaks only between blocks.
- **External service.** Every call to GitHub is `bridge_env`'s, with the time limit `GH_API_TIMEOUT` (30 seconds) and a retry limit of 0. The head wait is at most every 15 seconds up to 90 (`PR_HEAD_STEP`, `PR_HEAD_WAIT`). Add no other remote call, no other wait, no `sleep` beyond the head wait, and no retry. Tests replay the recorded real replies in `tests/fixtures/github/` through the stand-in. Do not invent a reply's shape, fields, hosts or messages, and add no fixture. If a reply you need is not recorded, stop and report it.
- **Windowless launches.** Every process your code starts is created with `creationflags=NO_WINDOW` (each module's existing constant). In tests a launch needs no `creationflags` argument, because `tests/conftest.py` makes every launch windowless. Where a test does write one, that line carries the literal text `CREATE_NO_WINDOW` (`tests/test_tests_windowless.py` refuses it otherwise). Every subprocess and git call in a test has a timeout, and each child ends before its test does.
- Never start a server, a watcher or a daemon that outlives a test. Run every command synchronously, in the foreground, and wait for it to end. Leave nothing running when you finish.
- **Do NOT run the full `tests/` tree** (`python -m pytest`, `python -m pytest tests`, or any command that collects all of it). Run only the commands the Done section names, exactly as written, from the Workspace root, with no `PYTHONPATH` or other environment change. The whole suite is CI's run.
- Do not refactor code outside the functions the Scope's limits name, even if it looks wrong.
- Never run the product, a migration, a seed or a test against the owner's live data or the real GitHub (Context, "Development data"). Do not run `gh` yourself.
- Follow existing conventions in the files you touch: ASCII program text and ASCII output, and results returned as values rather than raised inside the readers.
- These git commands are not yours to run: `commit`, `push`, `switch`, `checkout`, `merge`, `rebase`, `reset`, `stash`, `branch -d`, `worktree`. You read with `git status`, `git diff` and `git log` only. The single exception is `git restore bridge/cursor-bridge/VERSION` in the Done section. Your tests may run git inside their own temporary folders.
- **Numbers.**
  - The pull request number is checked as one or more ASCII digits (`"0" <= c <= "9"` for every character, not `str.isdigit`, which accepts other scripts' digits). It is used as text.
  - The sha is 7 to 64 hex characters in the guard, as `premerge_recorded` checks today.
  - The lines take `head[:12]`, the display form, from a value already validated; nothing is parsed by slicing.
  - Nothing is read from a reply by hand. The reader's dicts are the only source.
- **Mutation self-check (by hand, in process, no script in the diff).** The supervisor's mutants file sweeps `ready` and the guard's rule after your run, and every mutant must fail a test. Before you finish, apply each of these by hand, one at a time, run the Done section's pytest command (or the subset that holds the case), and revert. List each in the report by its label, with the test id that caught it:
  - M1 a missing context passed;
  - M2 a pending context passed;
  - M3 an earlier success taken beside a later failure;
  - M4 a skipped context passed beside a failure;
  - M5 a skipped context failed beside a superseded cancelled run;
  - M6 a superseded cancelled run counted;
  - M7 the statuses not read;
  - M8 a neutral context passed;
  - M9 a timed-out check not counted as failed;
  - M10 a run that failed at its start not counted as failed;
  - M11 another app's check taken;
  - M12 a status taken for a named app's check;
  - M13 a replaced run's check counted;
  - M14 a later page unread;
  - M15 the head not compared;
  - M16 cannot read taken as ready;
  - M17 an unreadable rule answered from the runs;
  - M18 a queued run passed;
  - M19 a base with no run passed;
  - M20 the record written on NOT READY;
  - M21 the merge allowed without the ready record;
  - M22 the ready record of another head accepted;
  - M23 the ready record of another pull request accepted;
  - M24 the default branch's contexts not read;
  - M25 a merge with no number allowed;
  - M26 `premerge-records` writing the premerge record where CI is not proven.

  A mutant no test catches is a gap: add a case for it (R13), or report it if you cannot.
- **Known failures.** On the checkpoint code, `tests/test_program_ready.py` gives `58 failed, 7 passed`, and the five files of the red run give `173 failed, 341 passed, 20 skipped`. None is known in `tests/test_permission_guard.py`, `tests/test_review_guard.py`, `tests/test_release_s_records_gate.py` or `tests/test_permission_guard_a4.py` before your change. If a case fails that your change did not cause, report it by its test id with its failure lines and fix none.
- Prefer reuse over new code: `bridge_env`'s readers for every GitHub read, `premerge_recorded`'s way of finding the common git folder for `ready_recorded`, `premerge`'s head-wait loop, the standard library, and the minimum that meets the acceptance criteria (the frozen `minimal-code.mdc` is in force). This never overrides a security, observability or accessibility requirement stated above.
- Rules in force for you: `.cursor/rules/secure-coding.mdc`, `.cursor/rules/workspace-boundary.mdc` and the frozen `minimal-code.mdc`.

## Done
Your report is the file `handoff/TASK-083-r1-report.md`, which you write as you go: what you did, what you changed, what you ran and what it printed, and what you could not do, so that nothing of it is lost if your run ends early. It names no computer path and no user name: write `<Workspace>` for the repository folder and `<tmp>` for a temporary folder, including in quoted command output.

When you finish, it holds:
- a list of every file you changed;
- a one-paragraph summary of what you did;
- for R1-R14, one line each on what meets it, naming the functions and their lines as the files stand after your change;
- each existing test case you changed, by name, with the change;
- the mutation self-check list, M1-M26, each with the test id that caught it (or `not caught` and why);
- every command of the list below with its output;
- a section headed exactly `Assumed, not verified`, as the report's last section.

The `Assumed, not verified` section lists every fact this change relies on that neither this brief nor the existing code settled, and that you did not confirm: the shape of a GitHub reply beyond the recorded ones, an ambiguous requirement you resolved one way, a platform or library behaviour you expected, a value you chose. Examples:
- that real `gh` resolves `{owner}/{repo}` from the checkout's remote as the stand-in's placeholders assume;
- that a pull request number with leading zeros (`012`) names the same record as `12` or not, and which you chose;
- that GitHub's `app.id` of a check is the integer a rule's `integration_id` names.

One item per line: what you assumed · why · what would confirm it. If there are none, write `Assumed, not verified: none`. Be specific: "edge cases" or "error handling" is not an item.

Run these from the Workspace root, in this order, after your last edit, each on its own, synchronously in the foreground, with no `PYTHONPATH` or other environment change:
1. `git status --short`
2. `python tools/dump-cli.py`
3. `python tools/dump-cli.py --check` (expect exit 0)
4. `python tools/make-manifest.py`
5. `git restore bridge/cursor-bridge/VERSION`
6. `python -m pytest -p no:cacheprovider -q tests/test_program_ready.py tests/test_d003_review_round_states.py tests/test_permission_guard.py tests/test_allowlist.py tests/test_program_branch_rule.py tests/test_program_release_s_rows.py tests/test_review_guard.py tests/test_release_s_records_gate.py tests/test_permission_guard_a4.py`
7. `python -m pytest -p no:cacheprovider -q tests/test_program_permission_guard.py tests/test_tests_windowless.py` (outside Scope. A failure here is reported by test id, never fixed in those files.)
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
