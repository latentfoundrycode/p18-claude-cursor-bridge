---
record: brief
header: 1
id: REFAC-011
round: 1
satisfies: [R-085]
scope: ["bridge/cursor-bridge/bridge-run.py", "bridge/cursor-bridge/MANIFEST.json", "docs/BUILDER_NOTES.md", "handoff/REFAC-011-r1-report.md"]
merge_unit: null
blocking_class: null
---
# REFAC-011: two re-checks that repeat a settled result, in the wait before a CI watch

## Objective
Refactoring — remove duplication / simplify **without any change in behaviour**.

This brief carries the fifth candidate of stage P2's refactoring pass: two re-checks that TASK-065 (the launcher's wait before a CI watch, R-085) left in `bridge/cursor-bridge/bridge-run.py`. Each recomputes a value the line before it has already settled, with a pure function on the same arguments. Both re-checks are deleted; the manifest is regenerated after it. No name is added or removed. Behaviour stays exactly the same: every printed `bridge-run:` line of the wait, every exit code (0, 1, 124, the watch's own), the head shown in every LIMIT line and after every failed poll, and the early start on a failed check under each of the three lists (the base's, the default branch's, the runs). Line numbers below are as the file stands at `494b630` (REFAC-010, the head of branch `refactor/P2`), before your edit.

**The sites.**

1. `_watch_decision(named, latest, restart)`, lines 2240-2263, its first test, lines 2248-2249:

```python
    failed = _failed_check(latest, named)
    if failed is not None and (named["kind"] != "base" or any(_check_holds(failed, entry) for entry in named["contexts"] or [])):
```

Why the parenthesised clause is always true when `failed is not None`: `_failed_check(latest, named)`, lines 2134-2141, reads

```python
    contexts = (named["contexts"] or []) if named["kind"] == "base" else None
    for item in latest.get("checks") or []:
        if isinstance(item, dict) and item.get("status") == "completed" and item.get("conclusion") in WATCH_FAIL_FAST:
            if contexts is None or any(_check_holds(item, entry) for entry in contexts):
                return item
    return None
```

Under `named["kind"] == "base"` it returns only an item for which `any(_check_holds(item, entry) for entry in (named["contexts"] or []))` already held: the same predicate, on the same item, over the same list the clause tests again. Under every other kind (`"default"`, `"runs"`) the clause's first operand, `named["kind"] != "base"`, is true. Neither operand can raise where `_failed_check` did not, since `_failed_check` has already read `named["kind"]` and `named["contexts"]`. `_check_holds(item, entry)` (lines 2144-2153) is pure: it reads two dicts and calls `bridge_env.is_int_id` and `bridge_env.app_id_of` (`bridge/cursor-bridge/bridge_env.py` lines 4260-4273), which only read their argument. So dropping the second evaluation changes nothing but time. `docs/HARDENING.md`, TASK-065's lead (9), records it (Review A, round 3). Line 2249 becomes `    if failed is not None:` (four spaces of indent, as now); the rest of `_watch_decision` (its docstring, the `what` line, the return, the runs branch and the missing-contexts branch) stays as it is.

2. `watch_loop(argv, folder, limit, start)`, lines 2291-2400, its fail branch, lines 2338-2341:

```python
        if polled["kind"] == "fail":
            head12 = _watch_head12(polled.get("local"), polled.get("github") if polled.get("base") else None)
            if not polled.get("base"):
                head12 = _watch_head12(polled.get("local"), None)
```

When `polled.get("base")` is falsy, line 2339 already passes `None` as `github`, so line 2341 computes the same value from the same arguments; when it is truthy, line 2341 is not reached. `_watch_head12(local, github)` (lines 2074-2076) is pure: `_watch_plain(local or github or "?")[:12]`, and `_watch_plain` (lines 2019-2027) builds a new string from its argument. `polled` is the dict `_watch_poll` returned; `.get` only reads it. Lines 2340 and 2341 are deleted; line 2339 stays exactly as it is, and the branch from line 2342 on (the `told_fail` line, `problem`, the pause, `continue`) is unchanged.

**Not a site.** Line 2376, `restart = seen_watch and named["kind"] == "runs"`, is also redundant (`seen_watch` is set at line 2399 only after line 2397 returned for every kind but `"runs"`, and `named` is never reassigned once set), but it is not this candidate: leave it exactly as it is and report it as noticed. `_watch_decision`'s docstring stays as it is; it remains true, the base's filter living in `_failed_check`.

**And the manifest:** `bridge/cursor-bridge/MANIFEST.json` regenerated once, after your last source edit, by `python tools/make-manifest.py`. The version stays `2026.11.12a` (the newest `## ` entry of `bridge/cursor-bridge/CHANGELOG.md`, which make-manifest picks, and today's content of `bridge/cursor-bridge/VERSION`).

Satisfies: no new requirement. This keeps as it is R-085 (a CI watch never returns before CI has run: before any `gh pr checks <n> --watch` the launcher waits, inside the run's own limit, until every required context of the base has a check or a status on the pushed head or a check of that head has failed, falling back to the default branch's contexts and then to the workflow runs, built by TASK-065).

## Scope
Files and directories you may create or modify:
- bridge/cursor-bridge/bridge-run.py
- bridge/cursor-bridge/MANIFEST.json
- docs/BUILDER_NOTES.md
- handoff/REFAC-011-r1-report.md

Do not modify anything else. `docs/BUILDER_NOTES.md` is append only.

## Out of scope
- .env and anything under secrets/
- CI configuration, pre-commit configuration, anything under `tools/` (you run `tools/make-manifest.py` and `tools/dump-cli.py`; you do not edit them)
- docs/ and handoff/, except the files the Scope section names; `docs/diagrams/` included (this change needs no diagram change, see Diagrams); `docs/HARDENING.md` included (its lead (9) is the supervisor's to close); `docs/CLI_REFERENCE.md` and `docs/cli-reference.json` included (this change touches no `build_parser` and no module docstring)
- every file under `tests/`, `tests/fixtures/github/` included: no test file or fixture may be edited, renamed or created (the supervisor's purity check, `refactor-check.py main --max-lines 400`, fails the branch on any test edit). If the working tree shows a test file modified before your run, leave it exactly as it is
- `bridge/cursor-bridge/VERSION`: its content must still read `2026.11.12a` after make-manifest rewrites it; make-manifest writes it with an LF line ending; report what `git diff --numstat -- bridge/cursor-bridge/VERSION` prints, do not try to restore the file
- everything under `run/`: the supervisor's, gitignored
- `docs/CHANGES.md` and `bridge/cursor-bridge/CHANGELOG.md`: a refactoring has no change entry
- in bridge-run.py, every line but 2249, 2340 and 2341: `_failed_check`, `_check_holds`, `_watch_head12`, `_watch_plain`, `_watch_poll`, `_watch_name`, `_watch_bits`, `_missing_contexts`, the runs functions (`_checks_of_run`, `_watch_runs`, `_all_runs_completed`, `_failed_run_notes`, `_runs_initial_ready`, `_runs_restart_ready`, `_runs_problem`, `_pending_run_count`), `_watch_limit_line`, `finish_limit`, the rest of `watch_loop` (line 2376 among it), `_watch_decision`'s docstring and its other lines, `WATCH_POLL` and `WATCH_FAIL_FAST`; the git-config watch (`GitConfigWatch` and its helpers, REFAC-010's); the module docstring, `build_parser`, and every other function
- every other file under `bridge/`, `bridge_env.py` and `review-guard.py` among them (review-guard.py's `prove_ci` holds no copy of either site)

## Context
**What the code is today** (`494b630`). bridge-run.py has CRLF line endings on every line; keep them, and add no trailing whitespace. Nothing new is imported and no name is added, renamed or removed: `_check_holds` keeps its two other callers (lines 2139 and 2166), `_watch_head12` its three other callers (lines 2339, 2351 and 2359). `WATCH_FAIL_FAST` (line 2001) is `("failure", "timed_out", "action_required")`, gh's fail bucket. REFAC-008, REFAC-009 and REFAC-010, committed on this branch before this brief, are this stage's earlier refactoring briefs; this one touches none of their code.

**How the tests reach this code.** `tests/test_program_watch_wait.py` (TASK-065, R-085) drives `watch_loop(argv, folder, limit, start)` in process, on a clock of the test's (it replaces the module's name `time`) and a stand-in `gh` answering from a list of states built from GitHub replies recorded from this repository (`tests/fixtures/github/`, the `wait-*.json` and `ready-*.json` files). No test names `_watch_decision`, `_failed_check`, `_check_holds` or `_watch_head12`; they are reached only through `watch_loop` and its standard error. Site 1 is reached by the early-start cases under the three lists, among them `test_r085_a_failed_check_starts_the_watch_at_once_with_contexts_still_missing` (the base's list), `test_r085_r2_under_the_base_s_list_a_failed_check_holding_no_named_context_does_not_start_the_watch`, `test_r085_r3_under_the_base_s_list_a_named_failed_check_after_an_unnamed_one_starts_the_watch_at_once`, `test_r085_r2_without_required_any_failed_check_starts_the_watch_at_once` (the default branch's list), `test_r085_a_failed_check_starts_the_watch_at_once_under_the_runs` and `test_r085_r3_only_a_conclusion_gh_counts_as_failed_starts_the_watch_at_once`. Site 2 is reached by the failed-poll cases, among them `test_r085_a_failed_poll_is_retried_and_its_reason_printed_once`, `test_r085_a_pull_request_that_cannot_be_read_is_retried`, `test_r085_a_poll_that_keeps_failing_ends_at_the_limit` and `test_r085_r2_a_local_head_that_cannot_be_read_is_a_failed_poll`. `tests/test_bridge_run.py` holds the launcher's other cases, eleven `test_r085_` ones among them. `tests/test_header_currency.py` reads, by syntax tree, the names the programs under `bridge/cursor-bridge/` define and use; it is in the command below as the guard that no name changed. The tests make no network call. Some cases are marked POSIX-only (a stand-in `gh` on PATH as a shell script) and are skipped on Windows; that is expected, and the skip count must be the same before and after.

**The expected count.** The supervisor ran the pytest command below at `494b630` with this brief untracked: `191 passed, 5 skipped` (the five skips in `tests\test_program_watch_wait.py` at lines 384 (two), 600, 613 and 622: `a stand-in gh on PATH is a shell script; CI's ubuntu job runs it`). Your before-edit run is the baseline, and the after-edit run must match it (the same count passed, none failed, the same count skipped).

**The manifest.** `MANIFEST.json` holds a normalized sha256 (CRLF folded to LF, BOM dropped) of every file under `bridge/`. After your edit it is stale for bridge-run.py; `python tools/make-manifest.py` rewrites `VERSION` (to `2026.11.12a` and a line feed) and the manifest, whose `generated` stamp changes, and prints `make-manifest: version 2026.11.12a, <n> files hashed, VERSION + MANIFEST.json written`. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` then compares the tree with it and is expected to print `RESULT: SOURCES MATCH bridge 2026.11.12a`. `python tools/dump-cli.py --check` is expected to print nothing and exit 0 (it prints the path of each reference file that differs and exits 1); if it prints a path, stop and report it, since this change must not alter the command reference.

**Security context.** This is a logic surface over untrusted input: the wait reads GitHub's replies through `bridge_env`'s readers and decides from them when to start a watch and what to print. The trust boundary is GitHub's reply and the local git answer for the pushed head. `.cursor/rules/secure-coding.mdc` is in force for you, and the project's ASVS level is 2 (`docs/INVENTORY.md`, Decisions). This change moves no boundary: the same checks count as failed, under the base's list only one that holds a named context (an app-tied context only by that app's check), the local head is still never replaced by GitHub's (KP-051), and every GitHub text printed still passes through `_watch_plain`.

**Development data** (`docs/INVENTORY.md`, Decisions): "the dev build is the Workspace sources under `bridge/`; a session in the repo always runs the *installed* bridge (`~/.claude`), never the one being edited, and installs reach running projects only through the owner's install run sheet". For you: the tests run the Workspace sources against pytest's temporary folders, the repositories they create there and the recorded replies. Never run bridge-run.py, review-guard.py or `bridge-install.py` yourself, against this repository or any other, never run `gh`, and never call GitHub.

## Diagrams
`docs/diagrams/D-002-components.md` — the element `bridge_run` (`bridge/cursor-bridge/bridge-run.py`), whose edges already exist:

```mermaid
    bridge_run --> bridge_env
    bridge_run -.-> roster_check
```

The change is internal to `bridge_run`: it adds no import and no edge, so the diagram does not change. **If the task cannot be done within them, stop and report the conflict (an objection) instead of deviating.**

## Requirements
1. **Checks first, before any edit; paste each command and its output in the report.** From the Workspace root, run `git grep -n -F -e "_check_holds(failed" -e "if not polled.get(" -- bridge`. Expected: exactly two lines, `bridge/cursor-bridge/bridge-run.py:2249:` (site 1's test) and `bridge/cursor-bridge/bridge-run.py:2340:` (site 2's `if not polled.get("base"):`). Then run `git grep -n -w -e _watch_decision -e _failed_check -e _check_holds -e _watch_head12 -- tests` and confirm it prints nothing (test names such as `test_r085_a_pending_check_holds_its_context` hold `_check_holds` inside a longer word and are not matched by `-w`). If a check does not hold (another hit, a missing hit, or a line number other than these), stop, change nothing, and report it.
2. Line 2249 reads `    if failed is not None:` and nothing else changes in `_watch_decision`.
3. Lines 2340 and 2341 are gone; line 2339 is unchanged and is the fail branch's only `head12 =` line.
4. No other line of bridge-run.py changes. It keeps its CRLF line endings and gains no trailing whitespace. No comment is added in place of the deleted lines.
5. After your last source edit, run `python tools/make-manifest.py` once, then the remaining verification commands in the Constraints.

## Acceptance criteria
- [ ] Behaviour is identical: the same `bridge-run:` lines of the wait in the same order, the same exit codes (0, 1, 124, the watch's own), the same head in every LIMIT line and after every failed poll (with and without a base in the failed poll), the same words passed to the watch, and the same early start or wait for a failed check under the base's list, the default branch's list and the runs.
- [ ] The report states, for each site, why the deleted evaluation always produced the value already in hand (site 1: `_failed_check`'s filter under `"base"` and the clause's first operand under every other kind; site 2: the same arguments to a pure function), from your reading of `_failed_check`, `_check_holds`, `bridge_env.is_int_id`, `bridge_env.app_id_of`, `_watch_head12` and `_watch_plain`.
- [ ] The full test suite passes with the **same** test set (the supervisor's run and CI's, not yours); in your own run the pytest command below passes before and after the edit with the same count passed, none failed, the same count skipped, both summary lines quoted in the report. No test file edited.
- [ ] The re-checks are gone: `git grep -n -F "_check_holds(failed" -- bridge` prints nothing; `git grep -n -F "if not polled.get(" -- bridge` prints nothing; `git grep -n -F "if failed is not None:" -- bridge` prints one line, in `bridge/cursor-bridge/bridge-run.py`, inside `_watch_decision`; `git grep -n -F "head12 = " -- bridge` prints four lines, all in bridge-run.py (the initial `head12 = "?"`, the fail branch's one, the mismatch branch's and the lists' line), where it printed five.
- [ ] `git diff --numstat -- bridge/cursor-bridge/bridge-run.py` prints `1`, `3` and the path (one line added, three deleted).
- [ ] No public signature changed; no name is added, renamed or removed; bridge-run.py imports nothing new.
- [ ] `python tools/dump-cli.py --check` exits 0 with no output.
- [ ] `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` prints `RESULT: SOURCES MATCH bridge 2026.11.12a`.
- [ ] `git diff --numstat -- bridge/cursor-bridge/VERSION` prints nothing (if it prints a line, it is quoted in the report and the file's content is shown to read `2026.11.12a`).
- [ ] `git diff --stat` shows only `bridge/cursor-bridge/bridge-run.py`, `bridge/cursor-bridge/MANIFEST.json`, and if written `docs/BUILDER_NOTES.md` (the report is a new file); `docs/CHANGES.md`, `bridge/cursor-bridge/CHANGELOG.md` and every file under `tests/` unchanged; no mutation script in the diff.

## Constraints
- Do not add dependencies.
- Do not read or write any file outside this workspace (the folder you were started in). Everything you need is inside it; everything you produce goes inside it. Run the Workspace copies of the tools, as the commands below do, never a copy under a home folder.
- If the brief, the rules, or the tooling got in your way (an instruction that contradicted another, a check that fired wrongly, a step that cost time for no reason), append one dated line describing it to `docs/BUILDER_NOTES.md`. Do not try to fix the tooling. Do the same for anything you learned about a defect or a pitfall (a cause you found, a platform quirk that cost you a round): one dated line, so the supervisor can carry it forward.
- In any Markdown you write, never break a line inside a paragraph or a list item; one paragraph is one line. Line breaks only between blocks.
- This increment's tests replay the **recorded real responses** in `tests/fixtures/github/` through the tests' own stand-in `gh`; do not invent a mock of GitHub's responses, hosts, fields, or next-step URLs, and do not add or change a fixture.
- Any console process your code launches on Windows is created windowless (`creationflags=subprocess.CREATE_NO_WINDOW` in Python, `0` on other platforms; `windowsHide: true` in Node). Capturing output does not prevent the window. A window is allowed only when it serves the user (they watch it or type into it); then write the reason at the call site as `windowless: visible-ok <reason>`. A spawn that needs a process group for a `CTRL_BREAK` stop is hidden only with a test of the stop path. This change adds no launch.
- Never start a server, a watcher or a daemon that outlives a test: a test that needs the product running starts it through the test framework's own fixture and stops it there. A server left running keeps your run from ending (plan 10.3, release A2).
- Do not refactor code outside the scope, even if it looks wrong.
- Never run the product, a migration, a seed or a test against the owner's live data. A development build uses the development data the design names (the inventory's `Development data` decision, stated in Context) and refuses the installed product's data. Here that means the Workspace sources, pytest's temporary folders and the recorded replies only.
- No value in this task is marked as the owner's.
- Follow existing conventions in the files you touch.
- These git commands are not yours to run: `commit`, `push`, `switch`, `checkout`, `merge`, `rebase`, `reset`, `stash`, `branch -d`, `worktree`; you read with `git status`, `git diff`, `git grep`, `git rev-parse` and `git log` only.
- Numbers from text, a file, a reply or an environment variable are parsed with the language's own parser, never by slicing or splitting a string. This change parses no number.
- An increment that starts a process meets the process checklist (windowless, stopped in a `finally` or a fixture's teardown with its whole tree, nothing outlives the test or the command, a browser on Windows launched attached, pipes closed or drained). This change starts none.
- Every verification command is written here in full. Run exactly these, each from the Workspace root (the folder you were started in), each in the foreground, never in the background; run pytest directly as written, never through a launcher:
  - At the start: `git status --short` and `git rev-parse HEAD`, pasted into the report.
  - Before the edit, and again after the last edit: `python -m pytest -p no:cacheprovider -q -rs tests/test_program_watch_wait.py tests/test_bridge_run.py tests/test_header_currency.py`
  - After the last source edit, in this order: `python tools/make-manifest.py`; `python tools/dump-cli.py --check`; `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`; `git diff --numstat -- bridge/cursor-bridge/VERSION`; `git diff --numstat -- bridge/cursor-bridge/bridge-run.py`; the four `git grep` commands of the fourth acceptance criterion.
  - At the end: `git status --short`, `git diff --stat` and `git rev-parse HEAD`, pasted into the report.
  - Do not run the whole `tests/` tree or any other test file; the supervisor runs the full suite and the purity check after your run. If a test fails before your edit, stop and report it; do not fix it.
- Mutation checking is the supervisor's in this task. Run no mutation, write no mutation script, and let none land in the diff.
- Prefer reuse over new code and write the minimum that meets the acceptance criteria (the frozen `minimal-code.mdc` is in force). This never overrides a security, observability, or accessibility requirement stated above.
- **Refactoring constraints.** Do not edit any test file. Do not add an entry to `docs/CHANGES.md`. Do not "improve" behaviour, messages, edge cases, or defaults you notice along the way (for example line 2376's `restart` test, `finish_limit` computing its own head, or the mismatch and lists branches' own `_watch_head12` calls); report them in your summary instead. Do not introduce an abstraction: this change deletes code and adds none; no helper, no new parameter, no alias, no comment, nothing new outside bridge-run.py except the regenerated manifest.
- **No computer path in the report.** Where quoted output holds the repository's absolute folder, write `<Workspace>` in its place; paste no other absolute path of this machine.

## Done
Your report is the file `handoff/REFAC-011-r1-report.md`, which you write as you go (what you did, what you changed, what you ran and what it printed, what you could not do) so that nothing of it is lost when your run ends early. When you finish, it holds:
- a list of every file you changed;
- a one-paragraph summary of what you did;
- the Requirements 1 grep commands with their output as the evidence;
- the before and after outputs of the pytest command, with both summary lines;
- the outputs of make-manifest, dump-cli `--check`, bridge-check, the two `git diff --numstat` commands and the fourth acceptance criterion's four `git grep` commands, each line that shows the result quoted (an empty output written as such);
- `git status --short`, `git diff --stat` and `git rev-parse HEAD` at the start and at the end, and whether the working tree held uncommitted changes then;
- for each site, the statement, from your reading of the functions the second acceptance criterion names, of why the deleted evaluation always produced the value already in hand;
- one sentence stating why the behaviour is identical;
- anything you noticed but did not change (per the refactoring constraints);
- a final section headed exactly `Assumed, not verified`: every fact this change relies on that neither this brief nor the existing code settled, and that you did not confirm (an ambiguous requirement you resolved one way, a platform or library behaviour you expected, a value you chose). One item per line: what you assumed · why · what would confirm it. If there are none, write `Assumed, not verified: none`. Be specific: "edge cases" or "error handling" is not an item.

Every command you ran is quoted in the report with the lines it printed, verbatim (with `<Workspace>` in place of the repository's folder), in a fenced block; a count, or a claim that a check passed, quotes the output line that shows it. A command you did not run is written `not run`, never described as run. Run this brief's pytest command once more after your last edit, and write the report's results after that run, naming the commit its counts belong to (`git rev-parse HEAD`) and whether the working tree then held uncommitted changes (`git status --short`).

Your last message is the summary and the report file's path, and nothing follows it: the supervisor reads only the last message, and a message printed earlier and then followed by more work is lost.
