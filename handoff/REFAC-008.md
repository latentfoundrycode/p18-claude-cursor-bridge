---
record: brief
header: 1
id: REFAC-008
round: 1
satisfies: [R-083, R-085]
scope: ["bridge/cursor-bridge/bridge_env.py", "bridge/cursor-bridge/bridge-run.py", "bridge/cursor-bridge/review-guard.py", "bridge/cursor-bridge/MANIFEST.json", "docs/BUILDER_NOTES.md", "handoff/REFAC-008-r1-report.md"]
merge_unit: null
blocking_class: null
---
# REFAC-008: one reader of a GitHub check's app id and suite id, in bridge_env

## Objective
Refactoring — remove duplication / simplify **without any change in behaviour**.

This brief carries one candidate of stage P2's refactoring pass: three copies of the same two readers (a GitHub check's app id, and a check's or a workflow run's check suite id) and one copy-pair of an "is this an id" test, which TASK-064, TASK-065 and TASK-083 left in `bridge/cursor-bridge/bridge_env.py`, `bridge/cursor-bridge/bridge-run.py` and `bridge/cursor-bridge/review-guard.py`; and the manifest regenerated after it. Behaviour stays exactly the same: every printed line, every error string, every exit code, every refusal. Line numbers below are as the files stand at `45e4322` (the head of `main` that branch `refactor/P2` was cut from), before your edit.

**The sites.**

1. `bridge/cursor-bridge/bridge_env.py` lines 4260-4280, used only by `latest_of_each` (line 4283; calls at lines 4296, 4309, 4319 and 4326):

```python
def _suite_id(item, key):
    if key == "check_suite":
        suite = item.get("check_suite")
        if not isinstance(suite, dict):
            return None
        value = suite.get("id")
    else:
        value = item.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value


def _app_id_of(item):
    app = item.get("app")
    if not isinstance(app, dict):
        return None
    value = app.get("id")
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value
```

2. `bridge/cursor-bridge/bridge-run.py` (the CI watch's wait, R-085): `_watch_suite(item)` lines 2137-2144 (`item["check_suite"]["id"]`, with `if isinstance(item, dict) else None` on the first line), `_run_suite(run)` lines 2147-2153 (`run["check_suite_id"]`, returning None first where `run` is not a dict), `_watch_app(item)` lines 2182-2190 (`item["app"]["id"]`, with the same dict guard, and the docstring `"""The check's app id, an int. A bool is not an id. A commit status has no app."""`), and `_watch_app_tied(app_id)` lines 2193-2194 (`return isinstance(app_id, int) and not isinstance(app_id, bool)`). Their callers: `_checks_of_run` lines 2158 and 2161, `_check_holds` lines 2204-2205, `_missing_contexts` line 2220.

3. `bridge/cursor-bridge/review-guard.py` (`ready`, R-083): `_check_app(item)` lines 1538-1545 (the same body as `_watch_app`, no docstring) and `_named_app(app_id)` lines 1548-1549 (the same body as `_watch_app_tied`). Their callers: `_context_result` lines 1565 and 1568, and `prove_ci` line 1691 (`if app_id is not None and not _named_app(app_id):`).

**What the reality check found about their semantics** (the supervisor's packaging read every copy). Every copy reads the same nested key paths (`item["app"]["id"]`, `item["check_suite"]["id"]`) or the same flat key (`run["check_suite_id"]`), excludes a `bool` before testing `int`, and gives `None` for anything else, including a missing key and a non-dict at the inner level. The one difference: the two scripts' copies return `None` where the outer argument is not a dict, while bridge_env's `_suite_id` and `_app_id_of` call `item.get` directly and would raise `AttributeError` there. That input never reaches bridge_env's copies: `latest_of_each` skips every run (line 4294) and every check (line 4317) that is not a dict before calling them, and `latest_runs` holds only those dict runs. So the dict guard can be added to the single implementation with no reachable change. `_watch_app_tied` and `_named_app` are character-identical. No copy is kept on account of a difference.

**The proposed shape.** `bridge_env.py` gains three public functions, in place of its two private ones, beside `latest_of_each`: `app_id_of(item)`, `suite_id(item, key)` and `is_int_id(value)`, each giving exactly what the copies give today, with the outer dict guard (a non-dict `item` gives `None`). `suite_id(item, "check_suite")` reads `item["check_suite"]["id"]`; any other key is read flat, as `_suite_id` does today (`suite_id(run, "check_suite_id")`). `is_int_id(value)` is true exactly where `isinstance(value, int) and not isinstance(value, bool)`. bridge_env's private `_suite_id` and `_app_id_of` are removed and `latest_of_each`'s four calls use the public names (no test, tool or other program names the private ones; Requirements 1 checks it). In the two scripts the six copies are deleted and their callers call `bridge_env.app_id_of`, `bridge_env.suite_id` and `bridge_env.is_int_id` at the call site, in the module's existing `bridge_env.<name>(...)` form; bind no module-level alias (no `_watch_app = bridge_env.app_id_of`). Whether `app_id_of` and the `int` test share code inside bridge_env is yours to decide.

**Callers to update**, each in the named line only, every other token of the line and every line around it as it is: bridge-run.py 2158 (`_run_suite(run)` to `bridge_env.suite_id(run, "check_suite_id")`), 2161 (`_watch_suite(item)` to `bridge_env.suite_id(item, "check_suite")`; the `isinstance(item, dict) and` before it stays), 2204 and 2220 (`_watch_app_tied(...)` to `bridge_env.is_int_id(...)`), 2205 (`_watch_app(item)` to `bridge_env.app_id_of(item)`); review-guard.py 1565 and 1691 (`_named_app(...)` to `bridge_env.is_int_id(...)`), 1568 (`_check_app(item)` to `bridge_env.app_id_of(item)`); bridge_env.py 4296, 4309, 4319 and 4326.

**And the manifest:** `bridge/cursor-bridge/MANIFEST.json` regenerated once, after your last source edit, by `python tools/make-manifest.py`. The version stays `2026.11.12a` (the newest `## ` entry of `bridge/cursor-bridge/CHANGELOG.md`, which make-manifest picks, and today's content of `bridge/cursor-bridge/VERSION`).

Satisfies: no new requirement. This keeps as they are R-083 (one reader of a repository's branch rule, and the proof that CI passed as a program: `review-guard.py ready`, and bridge_env's `latest_of_each`, built by TASK-064 and TASK-083) and R-085 (a CI watch never returns before CI has run: the launcher's wait, built by TASK-065).

## Scope
Files and directories you may create or modify:
- bridge/cursor-bridge/bridge_env.py
- bridge/cursor-bridge/bridge-run.py
- bridge/cursor-bridge/review-guard.py
- bridge/cursor-bridge/MANIFEST.json
- docs/BUILDER_NOTES.md
- handoff/REFAC-008-r1-report.md

Do not modify anything else. `docs/BUILDER_NOTES.md` is append only.

## Out of scope
- .env and anything under secrets/
- CI configuration, pre-commit configuration, anything under `tools/` (you run `tools/make-manifest.py` and `tools/dump-cli.py`; you do not edit them)
- docs/ and handoff/, except the files the Scope section names; `docs/diagrams/` included (this change needs no diagram change, see Diagrams); `docs/HARDENING.md` included, although its item (10) of TASK-065 names `_watch_app`, `_watch_app_tied`, `_check_app` and `_named_app` as history; `docs/CLI_REFERENCE.md` and `docs/cli-reference.json` included (this change touches no `build_parser` and no module docstring)
- every file under `tests/`: no test file may be edited, renamed or created (the supervisor's purity check, `refactor-check.py main --max-lines 400`, fails the branch on any test edit). If the working tree shows a test file modified before your run, leave it exactly as it is
- `bridge/cursor-bridge/VERSION`: its content must still read `2026.11.12a` after make-manifest rewrites it; make-manifest writes it with an LF line ending; report what `git diff --numstat -- bridge/cursor-bridge/VERSION` prints, do not try to restore the file
- everything under `run/`: the supervisor's, gitignored
- `docs/CHANGES.md` and `bridge/cursor-bridge/CHANGELOG.md`: a refactoring has no change entry
- every other function of the three programs (in particular the rest of `latest_of_each`, `_last_by`, `_int_rank`, `_freeze`, `ci_class`, `head_state`, `branch_rule`, `GH_COMMAND` and the gh call path in bridge_env; `_failed_check`, `watch_loop` and the rest of the wait in bridge-run.py; `_rule_contexts`, `_failure_beside`, `_runs_items` and the rest of `prove_ci` in review-guard.py), each module docstring, and every other file under `bridge/`

## Context
**What the code is today** (`45e4322`). All three programs have CRLF line endings on every line (bridge_env.py 4370 lines, bridge-run.py 3199, review-guard.py 1869); keep them, and add no trailing whitespace. Both scripts already `import bridge_env` (bridge-run.py line 115, review-guard.py line 113) and call it throughout in the form `bridge_env.<name>(...)`; nothing new is imported. The copies exist because TASK-065's brief forbade bridge-run.py importing review-guard.py (docs/HARDENING.md, TASK-065, item (10)); bridge_env is the module both already share, and `latest_of_each` there is the one reader of the head's runs and checks whose output both scripts consume.

**Names.** `git grep -n -e app_id_of -e suite_id -e is_int_id` at `45e4322` finds only bridge_env's private `_suite_id` and `_app_id_of` and the string `check_suite_id` (bridge_env line 4210 and the callers above; fixtures and tests use it only as a JSON key); the three public names are free. No file under `tests/` or `tools/` names any of the eight helpers (`_suite_id`, `_app_id_of`, `_watch_suite`, `_run_suite`, `_watch_app`, `_watch_app_tied`, `_check_app`, `_named_app`).

**How the tests reach this code.** `tests/test_program_watch_wait.py` (43 tests, TASK-065) drives bridge-run.py's `watch_loop` (`_checks_of_run`, `_check_holds`, `_missing_contexts`); `tests/test_program_ready.py` (29 tests, TASK-083) drives review-guard.py's `ready` (`_context_result`, `prove_ci`, including the app-tied rule `rules-app.json`); `tests/test_program_branch_rule.py` (53 tests, TASK-064) covers bridge_env's readers and `latest_of_each`; `tests/test_bridge_run.py` and `tests/test_review_guard.py` hold the programs' other cases (the `test_r085_` and `test_r083_` ones among them). `tests/test_header_currency.py` reads, by syntax tree, the names every program under `bridge/cursor-bridge/` defines and uses, bridge-run.py and review-guard.py among them; it is in the command below because this change moves names. Every case answers GitHub from recorded replies under `tests/fixtures/github/` through a stand-in program: the tests set `bridge_env.GH_COMMAND` to this interpreter and the stand-in, so the real `gh` never runs and no network call is made. Some cases are marked POSIX-only (a stand-in `gh` on PATH as a shell script) and are skipped on Windows; that is expected, and the skip count must be the same before and after.

**Time and retry limits.** This change makes no call and adds no retry. The existing limits stay as they are and are not to be touched: `bridge_env.GH_API_TIMEOUT = 30` (seconds per gh call), `bridge_env._GH_MAX_PAGES = 100`, `bridge_env.GIT_TIMEOUT = 30`, review-guard.py's `GIT_TIMEOUT = 120`, bridge-run.py's `WATCH_POLL = 15` (seconds between the wait's polls). This brief does not test on Claude Code: no `claude` command is part of it and no `claude --version` line is recorded.

**The manifest.** `MANIFEST.json` holds a normalized sha256 (CRLF folded to LF, BOM dropped) of every file under `bridge/`. After your edit it is stale for the three programs; `python tools/make-manifest.py` rewrites `VERSION` (to `2026.11.12a` and a line feed) and the manifest, whose `generated` stamp changes, and prints `make-manifest: version 2026.11.12a, <n> files hashed, VERSION + MANIFEST.json written`. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` then compares the tree with it and is expected to print `RESULT: SOURCES MATCH bridge 2026.11.12a`. `python tools/dump-cli.py --check` is expected to print nothing and exit 0 (it prints the path of each reference file that differs and exits 1); if it prints a path, stop and report it, since this change must not alter the command reference.

**Security context.** This is a logic and input-handling surface: the readers validate values out of GitHub's JSON replies (`gh api`), the trust boundary here, before the watch and `ready` compare them; `.cursor/rules/secure-coding.mdc` is in force for you, and the project's ASVS level is 2 (`docs/INVENTORY.md`, Decisions). This change moves no boundary: a `bool`, a string, a float, `None` or a missing key is still not an id, and a check whose app or suite cannot be read still matches no rule's app and no run's suite, so `ready` still answers as today and the wait still waits as today.

**Development data** (`docs/INVENTORY.md`, Decisions): "the dev build is the Workspace sources under `bridge/`; a session in the repo always runs the *installed* bridge (`~/.claude`), never the one being edited, and installs reach running projects only through the owner's install run sheet". For you: the tests run the Workspace sources against pytest's temporary folders and the recorded fixtures. Never run bridge-run.py, review-guard.py or `bridge-install.py` yourself, against this repository or any other, and never call GitHub.

## Diagrams
`docs/diagrams/D-002-components.md` — the elements `bridge_env` (`bridge/cursor-bridge/bridge_env.py`), `bridge_run` (`bridge/cursor-bridge/bridge-run.py`) and `review_guard` (`bridge/cursor-bridge/review-guard.py`). Both scripts already draw an edge to bridge_env:

```mermaid
    bridge_run --> bridge_env
    review_guard --> bridge_env
```

The change adds no import and no edge (bridge-run.py must not import review-guard.py, nor the reverse; bridge_env imports neither), so the diagram does not change. **If the task cannot be done within them, stop and report the conflict (an objection) instead of deviating.**

## Requirements
1. **Checks first, before any edit; paste each command and its output in the report.** From the Workspace root, run `git grep -n -e _suite_id -e _app_id_of -e _watch_suite -e _run_suite -e _watch_app -e _check_app -e _named_app -- bridge tools tests` and confirm that apart from the string `check_suite_id` every line is in one of the three programs, at the definitions and calls listed in the Objective (line numbers may differ by a few). Run `git grep -n -w -e app_id_of -e suite_id -e is_int_id` and confirm it shows nothing. If a check does not hold, stop, change nothing, and report it.
2. bridge_env.py defines `app_id_of(item)`, `suite_id(item, key)` and `is_int_id(value)` once each, public, with the semantics stated in the Objective, and no longer defines `_suite_id` or `_app_id_of`; `latest_of_each` calls the public names and is otherwise unchanged.
3. bridge-run.py no longer defines `_watch_suite`, `_run_suite`, `_watch_app` or `_watch_app_tied`; review-guard.py no longer defines `_check_app` or `_named_app`. Their callers call the bridge_env functions at the lines the Objective lists, and each caller gets, for every input, the value the deleted copy gave.
4. No other line of the three programs changes. Each keeps its CRLF line endings and gains no trailing whitespace. No docstring or comment you leave states something the code no longer does.
5. After your last source edit, run `python tools/make-manifest.py` once, then the remaining verification commands in the Constraints.

## Acceptance criteria
- [ ] Behaviour is identical: the same printed lines, error strings, exit codes and refusals of `bridge-run.py` (the wait before a CI watch) and `review-guard.py ready`, and the same return of `bridge_env.latest_of_each`, for every input.
- [ ] The full test suite passes with the **same** test set (the supervisor's run and CI's, not yours); in your own run the pytest command below passes before and after the edit with the same count passed, none failed, the same count skipped, both summary lines quoted in the report. No test file edited.
- [ ] Every listed caller uses the single implementation in bridge_env; the six copies in the scripts and bridge_env's two private helpers are gone (`git grep -n -e "def _suite_id" -e "def _app_id_of" -e "def _watch_suite" -e "def _run_suite" -e "def _watch_app" -e "def _check_app" -e "def _named_app" -- bridge` shows nothing).
- [ ] No public signature outside the listed sites changed; the only new names are `bridge_env.app_id_of`, `bridge_env.suite_id` and `bridge_env.is_int_id`.
- [ ] Neither script imports anything new, and neither imports the other.
- [ ] `python tools/dump-cli.py --check` exits 0 with no output.
- [ ] `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` prints `RESULT: SOURCES MATCH bridge 2026.11.12a`.
- [ ] `git diff --numstat -- bridge/cursor-bridge/VERSION` prints nothing (if it prints a line, it is quoted in the report and the file's content is shown to read `2026.11.12a`).
- [ ] `git diff --stat` shows only the three programs, `bridge/cursor-bridge/MANIFEST.json`, and if written `docs/BUILDER_NOTES.md` (the report is a new file); `docs/CHANGES.md`, `bridge/cursor-bridge/CHANGELOG.md` and every file under `tests/` unchanged; no mutation script in the diff.

## Constraints
- Do not add dependencies.
- Do not read or write any file outside this workspace (the folder you were started in). Everything you need is inside it; everything you produce goes inside it. Run the Workspace copies of the tools, as the commands below do, never a copy under a home folder.
- If the brief, the rules, or the tooling got in your way (an instruction that contradicted another, a check that fired wrongly, a step that cost time for no reason), append one dated line describing it to `docs/BUILDER_NOTES.md`. Do not try to fix the tooling. Do the same for anything you learned about a defect or a pitfall (a cause you found, a platform quirk that cost you a round): one dated line, so the supervisor can carry it forward.
- In any Markdown you write, never break a line inside a paragraph or a list item; one paragraph is one line. Line breaks only between blocks.
- This increment talks to no external service: its tests replay the recorded real responses under `tests/fixtures/github/` through the stand-in the tests install; do not invent a mock of GitHub's responses, and do not add or change a fixture.
- Any console process your code launches on Windows is created windowless (`creationflags=subprocess.CREATE_NO_WINDOW` in Python, `0` on other platforms; `windowsHide: true` in Node). Capturing output does not prevent the window. A window is allowed only when it serves the user (they watch it or type into it); then write the reason at the call site as `windowless: visible-ok <reason>`. A spawn that needs a process group for a `CTRL_BREAK` stop is hidden only with a test of the stop path. This change adds no launch.
- Never start a server, a watcher or a daemon that outlives a test: a test that needs the product running starts it through the test framework's own fixture and stops it there. A server left running keeps your run from ending (plan 10.3, release A2).
- Do not refactor code outside the scope, even if it looks wrong.
- Never run the product, a migration, a seed or a test against the owner's live data. A development build uses the development data the design names (the inventory's `Development data` decision, stated in Context) and refuses the installed product's data. Here that means the Workspace sources, the recorded fixtures and pytest's temporary folders only.
- No value in this task is marked as the owner's.
- Follow existing conventions in the files you touch.
- These git commands are not yours to run: `commit`, `push`, `switch`, `checkout`, `merge`, `rebase`, `reset`, `stash`, `branch -d`, `worktree`; you read with `git status`, `git diff`, `git grep`, `git rev-parse` and `git log` only.
- Numbers from text, a file, a reply or an environment variable are parsed with the language's own parser, never by slicing or splitting a string. This change parses no number: the ids are already `int` values out of `json` and are only type-checked.
- An increment that starts a process meets the process checklist (windowless, stopped in a `finally` or a fixture's teardown with its whole tree, nothing outlives the test or the command, a browser on Windows launched attached, pipes closed or drained). This change starts none.
- Every verification command is written here in full. Run exactly these, each from the Workspace root (the folder you were started in), each in the foreground, never in the background; run pytest directly as written, never through a launcher:
  - At the start: `git status --short` and `git rev-parse HEAD`, pasted into the report.
  - Before the edit, and again after the last edit: `python -m pytest -p no:cacheprovider -q -rs tests/test_program_watch_wait.py tests/test_program_ready.py tests/test_program_branch_rule.py tests/test_bridge_run.py tests/test_review_guard.py tests/test_header_currency.py`
  - After the last source edit, in this order: `python tools/make-manifest.py`; `python tools/dump-cli.py --check`; `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`; `git diff --numstat -- bridge/cursor-bridge/VERSION`; the `git grep` of the third acceptance criterion.
  - At the end: `git status --short`, `git diff --stat` and `git rev-parse HEAD`, pasted into the report.
  - Do not run the whole `tests/` tree or any other test file; the supervisor runs the full suite and the purity check after your run. If a test fails before your edit, stop and report it; do not fix it.
- Mutation checking is the supervisor's in this task. Run no mutation, write no mutation script, and let none land in the diff.
- Prefer reuse over new code and write the minimum that meets the acceptance criteria (the frozen `minimal-code.mdc` is in force). This never overrides a security, observability, or accessibility requirement stated above.
- **Refactoring constraints.** Do not edit any test file. Do not add an entry to `docs/CHANGES.md`. Do not "improve" behaviour, messages, edge cases, or defaults you notice along the way (for example a check whose app id is a large float, or the outer `isinstance(item, dict)` at bridge-run.py line 2161 that the new guard makes redundant); report them in your summary instead. Do not introduce an abstraction beyond what the listed duplicates need: the three functions in bridge_env; no class, no new parameter, no module-level alias in either script, nothing new outside the three programs.
- **No computer path in the report.** Where quoted output holds the repository's absolute folder, write `<Workspace>` in its place; paste no other absolute path of this machine.

## Done
Your report is the file `handoff/REFAC-008-r1-report.md`, which you write as you go (what you did, what you changed, what you ran and what it printed, what you could not do) so that nothing of it is lost when your run ends early. When you finish, it holds:
- a list of every file you changed;
- a one-paragraph summary of what you did;
- the Requirements 1 grep commands with their output as the evidence;
- the before and after outputs of the pytest command, with both summary lines;
- the outputs of make-manifest, dump-cli `--check`, bridge-check, `git diff --numstat -- bridge/cursor-bridge/VERSION` and the acceptance criterion's `git grep`, each line that shows the result quoted (an empty output written as such);
- `git status --short`, `git diff --stat` and `git rev-parse HEAD` at the start and at the end, and whether the working tree held uncommitted changes then;
- one sentence stating why the behaviour is identical;
- anything you noticed but did not change (per the refactoring constraints);
- a final section headed exactly `Assumed, not verified`: every fact this change relies on that neither this brief nor the existing code settled, and that you did not confirm (an ambiguous requirement you resolved one way, a platform or library behaviour you expected, a value you chose). One item per line: what you assumed · why · what would confirm it. If there are none, write `Assumed, not verified: none`. Be specific: "edge cases" or "error handling" is not an item.

Every command you ran is quoted in the report with the lines it printed, verbatim (with `<Workspace>` in place of the repository's folder), in a fenced block; a count, or a claim that a check passed, quotes the output line that shows it. A command you did not run is written `not run`, never described as run. Run this brief's pytest command once more after your last edit, and write the report's results after that run, naming the commit its counts belong to (`git rev-parse HEAD`) and whether the working tree then held uncommitted changes (`git status --short`).

Your last message is the summary and the report file's path, and nothing follows it: the supervisor reads only the last message, and a message printed earlier and then followed by more work is lost.
