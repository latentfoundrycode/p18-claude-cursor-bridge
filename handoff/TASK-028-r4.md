# TASK-028 (round 4): Windowless launches enforced by the bridge: two code fixes past the review ceiling

## Objective

This is round 4 of TASK-028. The increment is past the owner's three-round review ceiling, so only defects of the five blocking classes may send work back: behaviour against the brief, security, data integrity, a defeated safety mechanism, a failing test. This round is two code fixes and nothing else. Round 3's work is in this checkout (branch `task-028`, commit 57672d4) and stays as it is, apart from the two lines of work below. The decisions of `handoff/TASK-028.md`, `handoff/TASK-028-r2.md` and `handoff/TASK-028-r3.md` stand. Round 3's reviews are `run/supervisor/task028-reviewA-r3.md` (B1 and S1) and `run/supervisor/task028-security-r3.md` (items 1 and 2). Read them for the reviewers' wording. Where they differ from this brief, the brief governs. Fix 1: round 3 broke `uv_run_pytest` in `bridge/cursor-bridge/bridge-run.py`. Its last line now refers to a name that does not exist there, so `--kind test -- uv run --frozen` and the other `uv` forms with no `pytest` crash with a `NameError` traceback (exit 1, the program's absolute path printed) instead of being refused with exit 125. That is against round 3's requirement 2 ("Every other kind keeps its current acceptance exactly"). Fix 2: on POSIX, the conformance check's `Windowless test suite` floor can be led outside the Workspace by a `testpaths` entry such as `lnk/../tests`. The link check walks the normalised path, `main()` opens the raw join, and the kernel follows `lnk` before it applies `..`. That defeats the floor. The tests for both fixes are the supervisor's and are already written. You change code only.

Satisfies: R-039 — Windowless launches are enforced by the bridge for every project, never by a per-project fix: every heavy run of the loop (a builder, a project's test suite, a mutation run) starts through the launcher (`bridge-run.py`) in the background, which starts it with no window so that every process it creates inherits that unless it detaches itself; and every project's test suite whose runner the bridge ships a default for carries the bridge's frozen windowless default (FIX-001's `tests/conftest.py` default, shipped as a snapshot; pytest in release B, the Node runners' default deferred), reported by the conformance check as a floor.

## Scope

One brief carries one increment's scope; work that needs a second scope is a second brief, never a second section here.

Files you may create or modify:
- bridge/cursor-bridge/bridge-run.py
- bridge/cursor-bridge/conformance-check.py
- bridge/cursor-bridge/MANIFEST.json (regenerated only, by the manifest command in Constraints)
- docs/cli-reference.json (regenerated only, and only if you change a docstring; you need not)
- docs/CLI_REFERENCE.md (regenerated only, and only if you change a docstring; you need not)
- docs/BUILDER_NOTES.md
- handoff/TASK-028-r4-report.md

Do not modify anything else. Two run-time outputs are expected and are not part of the diff, because `run/` is gitignored: the line the launcher appends to `run/launcher/runs.jsonl`, and the suite's output file `run/agent/TASK-028-r4-suite.out`, both written by the full-suite command in Constraints. Do not edit either by hand.

## Out of scope

- .env and anything under secrets/
- CI configuration (`.github/`, `.githooks/`)
- docs/ and handoff/, except the files the Scope section names. That includes the earlier briefs and reports of TASK-028, this brief, `docs/HARDENING.md` (the supervisor's uncommitted edit is in the working tree; leave it alone) and the review files under `run/supervisor/`. Read them; do not edit them.
- **Every test file.** `tests/test_bridge_run_driver.py` and `tests/test_conformance_windowless.py` carry the supervisor's new tests, uncommitted in the working tree. Do not edit them, do not revert them and do not restore them from git. The same holds for every other file under `tests/`, `tests/conftest.py` included.
- `bridge/cursor-bridge/bridge_env.py`, `workflow-check.py`, `settings.bridge.json`, `windowless-default.snapshot.md`, and every other file of the bridge.
- **Kept as built, recorded by the supervisor in `docs/HARDENING.md` (section `### TASK-028`, Stage B5).** Do not change these, even though the reviews name them:
  - the `_load_bridge_env` fallback in `conformance-check.py`, with its inline `is_link`, its `sys.path.insert(0, HERE)` and its exec (Review A H1, audit 3);
  - the dead branch in `_pytest_test_roots` (`if _test_root_path_ok(ws, "tests"): return notes, ["tests"]` followed by the same return; Review A H4);
  - the runner-word rules of round 3's 9(f): the `=` and leading-`-` skips, the basename reduction, `shlex`, `escape_field` (Review A H2, H5, H6; audit 4);
  - hard-linked `conftest.py` files and the link checks on the root configuration files (audit 5 and 6);
  - every other item that file lists under TASK-028.
- Every other function of `bridge-run.py` and of `conformance-check.py`, and every other floor of the conformance check.

## Context

**Development data.** The inventory's decision, copied verbatim: "Development data: the dev build is the Workspace sources under `bridge/`; a session in the repo always runs the *installed* bridge (`~/.claude`), never the one being edited, and installs reach running projects only through the owner's install run sheet". The tests run the Workspace's `bridge/cursor-bridge/*.py` by file path, never the installed copy. `tests/conftest.py`'s autouse fixture `home_of_the_tests` points `HOME` and `USERPROFILE` at a temporary folder for every test. Every launcher run in the tests uses a temporary launch folder.

**Security context.** ASVS level 2 (INVENTORY, Decisions: "The builder's secure-coding rule is ASVS level 2"). `.cursor/rules/secure-coding.mdc` is in force for you. Fix 1 sits on the launcher's acceptance check, the control between the allow rule `"Bash(python ~/.claude/cursor-bridge/bridge-run.py --limit * --kind test -- *)"` and arbitrary commands. That check fails closed: a form it does not accept is refused with exit 125, never a crash. Fix 2 sits on the conformance check's boundary: it reads only the project's own files, never a file reached through a link out of the Workspace, and prints no absolute path, no folder name of the project and no control character (rule 54, KP-021).

**Fix 1, as the code stands** (`bridge/cursor-bridge/bridge-run.py:134-149`):

```python
def uv_run_pytest(argv):
    """`uv run [--project x] [--directory x] [--frozen|--locked|--no-sync] pytest ...`: only these options
    before pytest, never --with, --python or a script (the first review of A3, finding 9)."""
    i = 2
    while i < len(argv):
        if argv[i] in UV_VALUE_OPTIONS:
            i += 2
            continue
        if "=" in argv[i] and argv[i].split("=", 1)[0] in UV_VALUE_OPTIONS:         # --project=x
            i += 1
            continue
        if argv[i] in UV_FLAGS:
            i += 1
            continue
        return argv[i] == "pytest"
    return any(":" in p for p in parts)
```

Line 149's `parts` is a local of `_colon_in_path_after_drive` (:190-197). Before TASK-028 (commit 309ed382f4662f424b801d1cf3a7b1a2fce8d2b3) that line was `    return False`. The security audit reproduced the crash for `--kind test -- uv run --frozen`, `--kind builder -- uv run`, and `-- uv run --frozen` with and without `BRIDGE_RUN_ALLOW_ANY=1`. Each gives rc 1 with a `NameError` traceback, no `started` line and no log line.

**Fix 2, as the code stands** (`bridge/cursor-bridge/conformance-check.py`, 57672d4):
- `_ws_walk_component_ok(path)` (:240-247) and `_test_root_path_ok(ws, entry)` (:250-266). The latter checks `_path_inside_workspace` (:313-321), then walks the components of `os.path.relpath(os.path.normpath(<entry joined to ws>), ws)`, so `lnk/../tests` is walked as `tests`.
- `_pytest_test_roots(ws)` (:324-331): `kept = [p for p in raw if _test_root_path_ok(ws, p)]`, else `["tests"]`. It returns the raw entries.
- `main()`'s floor block (:895-921): for each `rel` in `roots`, `_test_root_path_ok(ws, rel)` again (:908), then `cpath = os.path.join(ws, rel, "conftest.py")` (:911) is opened with `rel` raw, and `ok_path = os.path.join(ws, roots[0], "conftest.py")` (:916).
- The driver's rule 1(c), which fix 2 copies, is `_token_has_dotdot(token)` in `bridge-run.py:186-187`: `return ".." in [p for p in re.split(r"[/\\]", token) if p]`.
- **Round 3's 9(b), quoted in full** (`handoff/TASK-028-r3.md`, requirement 9(b)): "Round 3: an entry is kept only when both hold: its absolute, normalised path lies inside the Workspace folder (as round 2), and no component from the Workspace folder down to the root folder, and down to the root's `conftest.py`, is a link, checked with `bridge_env.is_link` on each component below the Workspace folder (the Workspace's own path is not walked). A component whose `os.lstat` raises `FileNotFoundError` is absent, not a link: the walk stops there, the root is kept, and its absent `conftest.py` fails the token check as in round 2. A component whose `os.lstat` raises any other `OSError` counts as a link. An entry that fails either rule is dropped without a row, as an outside entry is. When no entry remains, the test root is `tests/`, judged by the same link rule: a `tests/` (or a `tests/conftest.py`) that is a link satisfies nothing, so the floor's OK can then come only from the rootdir's `conftest.py` of (d), and is otherwise MISSING; it is never OK from a file outside the Workspace. `testpaths` entries are literal folder names: a glob such as `tests/*` is not expanded (round 2's behaviour, now pinned by a test). The rootdir is the Workspace root."

**The supervisor's tests for this round** (already in the working tree; read them, do not edit them):
- `tests/test_bridge_run_driver.py`:
  - `test_r039_uv_run_without_pytest_still_refused` (:539-552), six cases: `--kind test` and no `--kind`, each with `uv run --frozen`, `uv run`, `uv run --project x`. Each asserts exit 125, no `Traceback`, a stderr line starting `bridge-run: refused - the launcher runs only cursor-agent`, and `runs_of(folder) == []`.
  - The exact-line assertions in `test_r039_healthy_refused_for_driver_exit_3` (:510) and `test_r039_limit_auto_driver_empty_log` (:536), which check `... in p.stderr.splitlines()`.
- `tests/test_conformance_windowless.py`:
  - `test_r039_testpaths_dotdot_component_dropped` (:501-514): `testpaths = a/../b`, with `b/conftest.py` holding the default and `tests/` holding only `test_x.py`. It expects rows exactly `[MISSING_ROW]`.
  - `test_r039_testpaths_link_then_dotdot_posix` (:517-534): `testpaths = lnk/../tests`, with `lnk` a link to `outside_r5n8/a` and `outside_r5n8/tests/conftest.py` holding the default. It expects `[MISSING_ROW]` and `outside_r5n8` on no line. It is skipped on Windows; Linux CI runs it.
  - `test_r039_linked_testpaths_entry_falls_back_to_tests` (:537-549): `testpaths = checks`, with `checks` a link outside and `tests/conftest.py` holding the default. It expects exactly `["  OK       Windowless test suite (tests/conftest.py)"]`.

## Diagrams

None. The build plan's `Diagrams:` field for TASK-028 is `none`, and the inventory records "No diagram index for release B".

## Requirements

This list is the whole of round 4.

1. **`uv_run_pytest`'s last line.** In `bridge/cursor-bridge/bridge-run.py:149`, `    return any(":" in p for p in parts)` goes back to `    return False`, as it stood before TASK-028. Nothing else in `uv_run_pytest` changes, and nothing else in `bridge-run.py` changes. The effect: every `uv` form with no `pytest` after uv's own options is refused exactly as before TASK-028, with exit 125 and the launcher's `bridge-run: refused - the launcher runs only cursor-agent, ...` line, or under `BRIDGE_RUN_ALLOW_ANY=1` handled as before. It never raises.
2. **The floor's test roots, round 3's 9(b) plus one rule.** Round 3's 9(b), quoted in Context, stands whole, with this rule added: a `testpaths` entry holding a `..` component is dropped without a row, as an outside entry is. Its components are split on both `/` and `\`, as the driver's rule 1(c) splits them (`_token_has_dotdot` in `bridge-run.py`). The rule applies to the entry as the configuration gives it, before any normalisation, whether the entry is relative or absolute. With no entry left, the default `tests/` decides, under round 3's link rule. Nothing the floor opens may be reached through a path holding `..`. The rows, their order, their wording and every other rule of round 3's requirement 9 stay as built.
3. **Nothing else in the code changes.** In particular, the `_load_bridge_env` fallback, the dead branch in `_pytest_test_roots` and the runner-word rules stay exactly as they are (see Out of scope). The docstrings need not change. If you do change one, regenerate the command reference with the commands in Constraints.

## Acceptance criteria

- [ ] `test_r039_uv_run_without_pytest_still_refused` passes in all six cases.
- [ ] `test_r039_healthy_refused_for_driver_exit_3` and `test_r039_limit_auto_driver_empty_log` pass with their exact-line assertions.
- [ ] `test_r039_testpaths_dotdot_component_dropped` and `test_r039_linked_testpaths_entry_falls_back_to_tests` pass. `test_r039_testpaths_link_then_dotdot_posix` passes where it runs, and on Windows it is reported as skipped with its reason.
- [ ] Every round-2 and round-3 test in `tests/test_bridge_run_driver.py`, `tests/test_conformance_windowless.py` and `tests/test_allowlist.py` passes unchanged, and so do `tests/test_tests_windowless.py`, `tests/test_bridge_run.py`, `tests/test_bridge_run_design_ceiling.py`, `tests/test_conformance_check.py`, `tests/test_conformance_check_a4.py`, `tests/test_hotfix25a_conformance_semgrep.py`, `tests/test_calibrate_program.py`, `tests/test_workflows_line_check.py`, `tests/test_b2_least_confident.py`, `tests/test_a4_followups.py` and `tests/test_dump_cli.py`.
- [ ] The full suite passes, apart from environment failures you report as such (see Constraints).
- [ ] The bridge's own Workspace still gives exactly `["  OK       Windowless test suite (tests/conftest.py)"]` (the existing test covers it).
- [ ] `git diff --stat` shows changes in `bridge/cursor-bridge/bridge-run.py`, `bridge/cursor-bridge/conformance-check.py`, `bridge/cursor-bridge/MANIFEST.json`, `docs/BUILDER_NOTES.md` (if you wrote a line) and the report, besides the supervisor's own uncommitted changes to `docs/HARDENING.md` and the two test files. It touches no test file beyond the supervisor's changes. The cli-reference files appear only if a docstring changed.
- [ ] `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge/bridge-run.py bridge/cursor-bridge/conformance-check.py` prints `0 FAIL`. `python tools/dump-cli.py --check` passes. `MANIFEST.json` is regenerated and still lists `windowless-default.snapshot.md`.
- [ ] Every requirement under "Satisfies" is fully met — no stand-in, placeholder screen, "coming soon" or "arrives in a later stage" text — and at least one test names each requirement ID (in its name, docstring, or a comment) so the trace is checkable. (The supervisor's tests above name R-039.)

## Constraints

- Do not add dependencies.
- Do not read or write any file outside this workspace (the folder you were started in). Everything you need is inside it; everything you produce goes inside it. The tests' temporary folders and temporary home are the only exception, and they come from pytest's `tmp_path` and `home_of_the_tests`.
- If the brief, the rules, or the tooling got in your way — an instruction that contradicted another, a check that fired wrongly, a step that cost time for no reason — append one dated line describing it to `docs/BUILDER_NOTES.md`. Do not try to fix the tooling. Do the same for anything you learned about a defect or a pitfall (a cause you found, a platform quirk that cost you a round): one dated line, so the supervisor can carry it forward.
- In any Markdown you write, never break a line inside a paragraph or a list item; one paragraph is one line. Line breaks only between blocks.
- This increment talks to no external service.
- Any console process your code launches on Windows is created windowless (`creationflags=subprocess.CREATE_NO_WINDOW` in Python — `0` on other platforms). Capturing output does not prevent the window. A window is allowed only when it serves the user (they watch it or type into it); then write the reason at the call site as `windowless: visible-ok <reason>`. A spawn that needs a process group for a `CTRL_BREAK` stop is hidden only with a test of the stop path. This round adds no launch.
- Never start a server, a watcher or a daemon that outlives a test: a test that needs the product running starts it through the test framework's own fixture and stops it there. A server left running keeps your run from ending.
- Do not refactor code outside the scope, even if it looks wrong.
- **Stop rule.** If any test fails after your change, do not work around it: no change to the code beyond requirements 1 and 2, no edit to a test, no fallback, no skip. Stop, leave the tree as it is, and report the test, its failure's last lines and why you think it fails. This holds for the supervisor's named tests and for every other test. Round 3's builder worked around an out-of-scope test instead of stopping, and that is how the `_load_bridge_env` fallback came to exist. The one exception is the full suite's environment failures described in the verification commands below.
- Never run the product, a migration, a seed or a test against the owner's live data. Here that means: never run the launcher with a real project as a test's working folder, and never touch the real `~/.claude` or `~/.cursor-bridge`. The conformance check's run on this checkout's own root (inside the existing test) only reads it. The full-suite command below runs this Workspace's own launcher, `bridge/cursor-bridge/bridge-run.py`, never the installed one.
- No value in this increment is marked as the owner's.
- Follow existing conventions in the files you touch: ASCII-only program text (both programs say so), the `bridge-run: refused - ` message form, the `add(verdict, floor, detail)` rows.
- These git commands are not yours to run: `commit`, `push`, `switch`, `checkout`, `merge`, `rebase`, `reset`, `stash`, `branch -d`, `worktree`; you read with `git status`, `git diff` and `git log` only. In particular, never `checkout` or `restore` a test file: the supervisor's tests exist only in the working tree.
- Numbers from text, a file, a reply or an environment variable are parsed with the language's own parser (`int`, `float`, `json`), never by slicing or splitting a string. This round reads no new number. `--limit` keeps its existing `float` parse (seconds, positive, at most the kind's cap).
- An increment that starts a process (a server, a browser, a worker, a child for a test) meets every point of this checklist: the process is windowless (above); it is stopped in a `finally` or a fixture's teardown, and its whole tree with it; nothing it started outlives the test or the command; its output pipes are closed or drained. This round adds no process. The suite's existing tests already meet it.
- **Mutation check.** After the tests pass, mutate by hand in your own run, in-process, and restore the code after each. Write no mutation script; none lands in the diff (the driver is the supervisor's). There are two mutants: (a) `uv_run_pytest`'s last line put back to `return any(":" in p for p in parts)`, run against `tests/test_bridge_run_driver.py -k uv_run_without_pytest`; (b) the `..`-component rule of requirement 2 removed, run against `tests/test_conformance_windowless.py -k "dotdot or linked_testpaths"`. Before you write the report, confirm with `git diff` that both are restored.
- Prefer reuse over new code — existing helpers, the standard library, native platform features, already-installed dependencies — and write the minimum that meets the acceptance criteria (the frozen `minimal-code.mdc` is in force). This never overrides a security, observability, or accessibility requirement stated above.
- Verification commands. Run each from the Workspace folder (the folder you were started in), exactly as written:
  - the interpreter's version, once, pasted into the report: `python --version`
  - the supervisor's named tests: `python -m pytest tests/test_bridge_run_driver.py tests/test_conformance_windowless.py -q -p no:cacheprovider -rs -k "uv_run_without_pytest or healthy_refused_for_driver_exit_3 or limit_auto_driver_empty_log or testpaths_dotdot_component_dropped or testpaths_link_then_dotdot_posix or linked_testpaths_entry_falls_back_to_tests"`. Expected result: 10 passed and 1 skipped on Windows (the POSIX test).
  - the increment's tests and the files its changes touch: `python -m pytest tests/test_bridge_run_driver.py tests/test_conformance_windowless.py tests/test_allowlist.py tests/test_tests_windowless.py tests/test_bridge_run.py tests/test_bridge_run_design_ceiling.py tests/test_conformance_check.py tests/test_conformance_check_a4.py tests/test_hotfix25a_conformance_semgrep.py tests/test_calibrate_program.py tests/test_workflows_line_check.py tests/test_b2_least_confident.py tests/test_a4_followups.py tests/test_dump_cli.py -q -p no:cacheprovider -rs`. This must pass. `-rs` prints each skipped test and its reason; copy them into the report.
  - the windowless check: `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge/bridge-run.py bridge/cursor-bridge/conformance-check.py`
  - the command reference: `python tools/dump-cli.py --check`. If it fails because you changed a docstring, run `python tools/dump-cli.py` once, then `python tools/dump-cli.py --check` again.
  - the manifest: `python tools/make-manifest.py --version 2026.10.25a`
  - the full suite, once, at the end, through this Workspace's launcher with no window: `python bridge/cursor-bridge/bridge-run.py --limit auto --kind test -- python -m pytest tests -q -p no:cacheprovider > run/agent/TASK-028-r4-suite.out 2>&1`. Create `run/agent/` first if it does not exist. If your shell can start a command in the background, start it that way and wait for it to end. The output file's last line is then `bridge-run: exit <code>`. Otherwise run it in the foreground; the launcher ends it at its limit. Then read the file. Some install and rollback tests may fail because of your home folder. Do not fix them. Report each full-suite failure outside the list above as an environment observation (test id and its last error line), and say whether it also fails with your changes reverted, if its cause tells you. A failure in any file of the list above falls under the stop rule.

## Done

Your report is the file `handoff/TASK-028-r4-report.md`, which you write as you go — what you did, what you changed, what you ran and what it printed, what you could not do — so that nothing of it is lost when your run ends early. Never paste a computer path or a user name into it: write `<temporary folder>`, `<home>` or `<Workspace>` instead.

When you finish, it holds:
- a list of every file you changed, and only those, checked against `git status` (the supervisor's uncommitted `docs/HARDENING.md` and the two test files are not yours; name them as the supervisor's);
- a one-paragraph summary of what you did;
- one line per fix (Review A B1 / audit 1; Review A S1 / audit 2), each saying where it is fixed and which of the supervisor's tests pins it;
- the output of `python --version`, the named-tests run's last line, and the list of skipped tests with their reasons from `-rs`;
- the windowless check's, `dump-cli --check`'s and the manifest command's last lines, and the full suite's summary line with its `bridge-run: exit <code>` line;
- the mutation table, one row per mutant: the reverted code, the supervisor's test that failed on it, and the failing assertion's last line. A mutant that no test killed in your run goes under **Survived** with the reason. Never list as killed a mutant you did not see killed. On Windows, `test_r039_testpaths_link_then_dotdot_posix` is skipped, so it cannot be the killing test there;
- the full-suite environment observations;
- a section headed exactly `Assumed, not verified`: every fact this change relies on that neither this brief nor the existing code settled, and that you did not confirm — the shape of an external service's request or response, an ambiguous requirement you resolved one way, a platform or library behaviour you expected, a value you chose. One item per line: what you assumed · why · what would confirm it. If there are none, write `Assumed, not verified: none`. Be specific: "edge cases" or "error handling" is not an item. Name only what the code relies on and you did not observe; a behaviour a test of yours observed is verified, not assumed. Name facts of the kind this round's code relies on. Examples: that every `testpaths` entry reaching the new rule is a `str` from all three configuration readers; that on POSIX the kernel resolves `lnk/..` through the link while Windows collapses `..` textually; that `uv_run_pytest` returning `False` leads to the refusal through `accepted()` for every kind and under `BRIDGE_RUN_ALLOW_ANY=1`.

Your last message is the summary and the report file's path, and nothing follows it: the supervisor reads only the last message, and a message printed earlier and then followed by more work is lost.
