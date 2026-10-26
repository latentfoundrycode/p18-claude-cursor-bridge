# TASK-028 (round 5): Windowless launches enforced by the bridge: the windowless floor's unusual input, three fixes and a backstop

## Objective

This is round 5 of TASK-028. The increment is past the owner's three-round review ceiling, so only defects of the five blocking classes may send work back: behaviour against the brief, security, data integrity, a defeated safety mechanism, a failing test. Round 4's work is in this checkout (branch `task-028`, commit 4dedcfd) and stays as it is, apart from the work below. The decisions of `handoff/TASK-028.md`, `handoff/TASK-028-r2.md`, `handoff/TASK-028-r3.md` and `handoff/TASK-028-r4.md` stand. Round 4's reviews are `run/supervisor/task028-reviewA-r4.md` (REJECT, three findings in the blocking classes) and `run/supervisor/task028-security-r4.md` (PASS, with one HARDENING finding that is the same as Review A's first, so the two converge). Read them for the reviewers' wording; where they differ from this brief, the brief governs. All three findings break sentences of round 3's brief: 9(c)'s "No input makes the check print a traceback", and requirement 9's "prints no absolute path, no folder name of the project, no name of a folder outside it and no control character". (1) A `testpaths` entry holding a NUL character makes `os.lstat` raise `ValueError` in `_ws_walk_component_ok`, which catches only `OSError`: a traceback with the program's absolute path. (2) A `tests/` folder that passes `_tests_dir_listable` but cannot be listed makes `os.listdir` in `_pytest_suite_seen` raise `PermissionError`: a traceback with the Workspace's absolute path. (3) The OK row's path comes from a `testpaths` entry and is printed unescaped, so an entry such as `t` U+202E `x` puts a raw control character on the console. The three are also the long tail of one subsystem, the floor's handling of unusual input, which rounds 2 to 4 kept finding. So this round does two things: it fixes the three findings, and it closes the class with a backstop, so that any exception the floor's judgement raises becomes exactly one NOTE row instead of a traceback. The tests are the supervisor's and are already written. You change code only, in one file.

Satisfies: R-039 — Windowless launches are enforced by the bridge for every project, never by a per-project fix: every heavy run of the loop (a builder, a project's test suite, a mutation run) starts through the launcher (`bridge-run.py`) in the background, which starts it with no window so that every process it creates inherits that unless it detaches itself; and every project's test suite whose runner the bridge ships a default for carries the bridge's frozen windowless default (FIX-001's `tests/conftest.py` default, shipped as a snapshot; pytest in release B, the Node runners' default deferred), reported by the conformance check as a floor.

## Scope

One brief carries one increment's scope; work that needs a second scope is a second brief, never a second section here.

Files you may create or modify:
- bridge/cursor-bridge/conformance-check.py
- bridge/cursor-bridge/MANIFEST.json
- docs/cli-reference.json
- docs/CLI_REFERENCE.md
- docs/BUILDER_NOTES.md
- handoff/TASK-028-r5-report.md

`MANIFEST.json` is regenerated only, by the manifest command in Constraints, never edited by hand. `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` are regenerated only, by the commands in Constraints, and only if you change a docstring of `conformance-check.py`; you need not change one. Do not modify anything else. Two run-time outputs are expected and are not part of the diff, because `run/` is gitignored: the line the launcher appends to `run/launcher/runs.jsonl`, and the suite's output file `run/agent/TASK-028-r5-suite.out`, both written by the full-suite command in Constraints. Do not edit either by hand. The manifest command also rewrites `bridge/cursor-bridge/VERSION` with the same version it already holds; if `git status` nevertheless shows `VERSION` changed, say so in the report and do not edit it.

## Out of scope

- .env and anything under secrets/
- CI configuration (`.github/`, `.githooks/`)
- docs/ and handoff/, except the files the Scope section names. That includes the earlier briefs and reports of TASK-028, this brief, `docs/HARDENING.md` and the review files under `run/supervisor/`. Read them; do not edit them.
- **Every test file.** `tests/test_conformance_windowless.py` and `tests/test_bridge_run_driver.py` carry the supervisor's round-5 tests, uncommitted in the working tree. Do not edit them, do not revert them and do not restore them from git. The same holds for every other file under `tests/`, `tests/conftest.py` included.
- `bridge/cursor-bridge/bridge-run.py`: out of scope this round, wholly. Its round-4 fix stands; the widened `test_r039_uv_run_without_pytest_still_refused` must pass against it as it is.
- `bridge/cursor-bridge/bridge_env.py`, `workflow-check.py`, `settings.bridge.json`, `windowless-default.snapshot.md`, and every other file of the bridge.
- **Every item `docs/HARDENING.md` records under `### TASK-028`.** Do not change these, even where the reviews name them. Among them: the `_load_bridge_env` fallback in `conformance-check.py`, with its inline `is_link`, its `sys.path.insert(0, HERE)` and its exec; the dead branch in `_pytest_test_roots`; the runner-word rules of round 3's 9(f) (the `=` and leading-`-` skips, the basename reduction, `shlex`, the runner word's `escape_field`); hard-linked `conftest.py` files and the link checks on the root configuration files; `tox.ini` never being read; `RecursionError` at the other JSON floors; the uv test's missing `BRIDGE_RUN_ALLOW_ANY` forms.
- Every other floor of the conformance check, and every function of `conformance-check.py` that requirements 1 to 4 do not name.

## Context

**Development data.** The inventory's decision, copied verbatim: "Development data: the dev build is the Workspace sources under `bridge/`; a session in the repo always runs the *installed* bridge (`~/.claude`), never the one being edited, and installs reach running projects only through the owner's install run sheet". The tests run the Workspace's `bridge/cursor-bridge/*.py` by file path (as a subprocess) or load them in-process through the `program` fixture of `tests/conftest.py` (`load_program(name)` imports `bridge/cursor-bridge/<name>.py`), never the installed copy. `tests/conftest.py`'s autouse fixture `home_of_the_tests` points `HOME` and `USERPROFILE` at a temporary folder for every test.

**Security context.** ASVS level 2 (INVENTORY, Decisions: "The builder's secure-coding rule is ASVS level 2"). `.cursor/rules/secure-coding.mdc` is in force for you. The trust boundary is the project under check: its configuration files (`pytest.ini`, `pyproject.toml`, `setup.cfg`, `package.json`) and its folder names are untrusted input to the conformance check. The check reads only the project's own files, never a file reached through a link out of the Workspace, never a value of `.env`, and prints no absolute path, no folder name of the project, no name of a folder outside it and no control character (rule 54, KP-021). It fails closed: an input it cannot judge never yields OK.

**The sentences of earlier briefs this round restores** (quoted from `handoff/TASK-028-r3.md`):
- Requirement 9: "It reads only the project's own files, never a value of `.env` or any secret, and prints no absolute path, no folder name of the project, no name of a folder outside it and no control character."
- 9(b), the walk: "A component whose `os.lstat` raises `FileNotFoundError` is absent, not a link: the walk stops there, the root is kept, and its absent `conftest.py` fails the token check as in round 2. A component whose `os.lstat` raises any other `OSError` counts as a link. An entry that fails either rule is dropped without a row, as an outside entry is. When no entry remains, the test root is `tests/`, judged by the same link rule".
- 9(b2): "The floor never lists a `tests` folder that is a link, or whose `os.lstat` raises an error other than `FileNotFoundError`: such a `tests/` shows no `test_*.py`. So with no pytest configuration a linked `tests/` makes no pytest suite seen, and the Node or neither-seen rows of (e) and (f) apply."
- 9(c): "No input makes the check print a traceback or exit 2 or above."
- 9(d): "The rows are exactly, as built: `  OK       Windowless test suite (<relative path of the conftest.py that satisfied it>)` and `  MISSING  Windowless test suite  - copy windowless-default.snapshot.md into conftest.py (see Cursor-Project-Configuration.md, windowless-default); need windowless_kwargs, Popen.__init__ and CREATE_NO_WINDOW`." Round 5 changes only how the relative path inside the OK row is rendered (requirement 3).
- 9(f), the runner word: "`<word>` is the runner word exactly as `escape_field` of `bridge/cursor-bridge/workflow-check.py` renders it. Reuse that function (load `workflow-check.py` beside the program as `judge_workflows_line` does, without changing `judge_workflows_line`); write no second copy of it."

**The code as it stands** (`bridge/cursor-bridge/conformance-check.py`, 4dedcfd):
- `_ws_walk_component_ok(path)` (:240-247):

```python
def _ws_walk_component_ok(path):
    try:
        os.lstat(path)
    except FileNotFoundError:
        return True
    except OSError:
        return False
    return not bridge_env.is_link(path)
```

  It is called from `_test_root_path_ok(ws, entry)` (:254-270, on each component and on the root's `conftest.py`) and from `_root_conftest_counts(ws)` (:419-421). `_test_root_path_ok` is called from `_pytest_test_roots(ws)` (:328-335) and from `main()`'s floor (:912). `bridge_env.is_link` (`bridge/cursor-bridge/bridge_env.py:59-64`) catches only `OSError` from its own `os.lstat`. `_path_inside_workspace(entry, ws)` (:317-325) catches `ValueError` from `os.path.commonpath`; `_test_root_path_ok` catches `(ValueError, RecursionError)` from `os.path.relpath`.
- `_tests_dir_listable(ws)` (:273-285) and `_pytest_suite_seen(ws)` (:288-314), whose last lines are:

```python
    if _tests_dir_listable(ws):
        tests = os.path.join(ws, "tests")
        for name in os.listdir(tests):
            if name.startswith("test_") and name.endswith(".py"):
                return True
    return False
```

- `_load_escape_field()` (:382-396) loads `workflow-check.py` beside the program's real path and returns its `escape_field`, or `None` when it cannot be loaded. `escape_field` (`bridge/cursor-bridge/workflow-check.py:129-144`) keeps a character only when it is printable and below code point 128; every other character becomes `\xNN`, `\uNNNN` (lower-case hex) or `\UNNNNNNNN`. So `t` U+202E `x` renders as `t‮x`.
- `main()`'s floor block (:899-947), from `pytest_seen = _pytest_suite_seen(ws)` to the neither-seen `add("NOTE", "Windowless test suite", detail)`. It sits between the `Windowless check` row (:896-897) and the lockfile rows (:949 on). The OK row is `add("OK", "Windowless test suite (%s)" % rel_ok)` (:923), where `rel_ok` comes from `_rel_forward(ok_path, ws)` (:409-416). `add(verdict, floor, detail)` appends to `results`; the rows are printed at :1279-1282 as `"  %-8s %s%s" % (verdict, floor, ("  - " + detail) if detail else "")`. The exit code is 1 when any row is MISSING, else 0; a NOTE does not change it (:1285-1289).

**The supervisor's tests for this round** (in the working tree; read them, do not edit them). In `tests/test_conformance_windowless.py`, from the comment `# --- the supervisor's tests for round 5` (:635) to the end of the file:
- `test_r039_nul_in_testpaths_dropped` (:650-659): `pytest.ini` with `testpaths = a<NUL>b` (written as bytes), `tests/test_x.py` and no `conftest.py`. Subprocess. Expects rc below 2, no `Traceback`, rows exactly `[MISSING_ROW]`.
- `test_r039_unlistable_tests_folder_is_no_suite` (:662-679): in-process through `program("conformance-check")`; it replaces `os.listdir` so that listing `<root>/tests` raises `PermissionError`. No configuration, `tests/test_x.py`. Expects rows exactly `[NEITHER_NOTE]` (the `no pytest configuration, no tests/test_*.py and no package.json test script were found` row). Because the test patches `os.listdir`, the floor must keep listing `tests/` through `os.listdir`.
- `test_r039_ok_row_path_is_escaped` (:682-699): a folder `t` U+202E `x` holding the default `conftest.py`, `pyproject.toml` with `testpaths = ["t‮x"]`, run as a subprocess with `PYTHONIOENCODING=utf-8`. Expects no U+202E anywhere in the output and rows exactly `["  OK       Windowless test suite (t\\u202ex/conftest.py)"]` (a literal backslash before `u202e`). It skips only if the file system refuses the folder name.
- `test_r039_floor_backstop_turns_an_error_into_one_note` (:702-722): in-process; it replaces the module-level `_pytest_test_roots` with a function raising `RuntimeError("secret_zz91 " + str(ws))`, then calls `main()`. Expects rc below 2, `secret_zz91` nowhere in the output, the floor's rows exactly `["  NOTE     Windowless test suite  - the floor could not be judged (RuntimeError)"]`, and a row of a later floor (`Lockfile ...` or `Records ...`) or the summary line `conformance-check: <n> OK` still printed. Because the test patches the module global, `main()`'s floor must keep calling `_pytest_test_roots` through that global name.
- `test_r039_dotdot_entry_spellings_dropped` (:725-739), three cases (`a\..\b`, `a/..\b`, and the absolute `<root>/a/../b`): each expects `[MISSING_ROW]`. These pin round 4's `..` rule; they should already pass and must keep passing.

In `tests/test_bridge_run_driver.py`: `test_r039_uv_run_without_pytest_still_refused` (:539-552), its `kind_flags` parametrize widened to `["--kind", "test"]`, `["--kind", "builder"]` and `[]`, so nine cases. It runs against `bridge-run.py` as round 4 left it, and should already pass.

## Diagrams

None. The build plan's `Diagrams:` field for TASK-028 is `none`, and the inventory records "No diagram index for release B".

## Requirements

This list is the whole of round 5. All four requirements are in `bridge/cursor-bridge/conformance-check.py`'s `Windowless test suite` floor.

1. **A `ValueError` on a configured path counts as a link.** In `_ws_walk_component_ok`, and in every other `os` call the floor makes on a path built from a configured `testpaths` entry, a `ValueError` (such as an embedded NUL in the path) is treated like any `OSError` other than `FileNotFoundError`: the component counts as a link, so the entry is dropped without a row, as round 3's 9(b) drops one. With no entry left, the default `tests/` decides, under round 3's rules.
2. **An unlistable `tests/` shows no suite.** In `_pytest_suite_seen`, an `OSError` from listing `tests/` means that no `test_*.py` is seen, as 9(b2) treats an `os.lstat` error. The rest of 9(b2) and 9(e)-(f) then decide the rows.
3. **The OK row's path is escaped.** The relative path in the OK row (`  OK       Windowless test suite (<path>)`) is rendered by `escape_field` of `workflow-check.py`, loaded as the runner word's is, through `_load_escape_field`; write no second copy of `escape_field`. If `escape_field` cannot be loaded, the path is printed only when every character of it is printable ASCII (printable and below code point 128); otherwise the row is exactly `  OK       Windowless test suite (a test root's conftest.py)`. A path of printable ASCII prints as it does today, so `  OK       Windowless test suite (tests/conftest.py)` is unchanged.
4. **The backstop.** The floor's whole judgement, from reading the configuration to choosing its rows (today :899-947: `_pytest_suite_seen`, `_node_test_runner`, `_pytest_test_roots`, the parse NOTEs, the OK/MISSING choice, the Node row, the neither-seen rows and the loading of `escape_field`), runs so that any exception (`Exception` and its subclasses) raised from it gives exactly one row in place of all the floor's rows: `  NOTE     Windowless test suite  - the floor could not be judged (<the exception's class name>)`, the class name being `type(exception).__name__`. Nothing of the exception's message, arguments or traceback is printed, on stdout or stderr. No partial row of the floor (a parse NOTE added before the failure, say) is printed beside it. The check's other floors run on as before, the floor's rows (or the one NOTE) keep their place between the `Windowless check` row and the lockfile rows, and the exit code is as for any NOTE: it does not change it. One way to do this is to collect the floor's rows in a local list and add them to the results only when the judgement finishes; you may choose another that meets the rule. The backstop does not replace requirements 1 to 3: each of those inputs must give the row its requirement names, not the backstop's NOTE.

Nothing else in the code changes. The rows, their order, their wording and every other rule of round 3's requirement 9 and round 4's requirement 2 stay as built. The module docstring need not change; if you change it, regenerate the command reference with the commands in Constraints.

## Acceptance criteria

- [ ] `test_r039_nul_in_testpaths_dropped`, `test_r039_unlistable_tests_folder_is_no_suite`, `test_r039_ok_row_path_is_escaped` and `test_r039_floor_backstop_turns_an_error_into_one_note` pass.
- [ ] `test_r039_dotdot_entry_spellings_dropped` passes in its three cases, and `test_r039_uv_run_without_pytest_still_refused` in its nine.
- [ ] Every earlier test in `tests/test_conformance_windowless.py`, `tests/test_bridge_run_driver.py` and `tests/test_allowlist.py` passes unchanged, and so do `tests/test_tests_windowless.py`, `tests/test_bridge_run.py`, `tests/test_bridge_run_design_ceiling.py`, `tests/test_conformance_check.py`, `tests/test_conformance_check_a4.py`, `tests/test_hotfix25a_conformance_semgrep.py`, `tests/test_calibrate_program.py`, `tests/test_workflows_line_check.py`, `tests/test_b2_least_confident.py`, `tests/test_a4_followups.py` and `tests/test_dump_cli.py`.
- [ ] The full suite passes, apart from environment failures you report as such (see Constraints).
- [ ] The bridge's own Workspace still gives exactly `["  OK       Windowless test suite (tests/conftest.py)"]` (the existing test covers it).
- [ ] `git diff --stat` shows changes in `bridge/cursor-bridge/conformance-check.py`, `bridge/cursor-bridge/MANIFEST.json`, `docs/BUILDER_NOTES.md` (if you wrote a line) and the report, besides the supervisor's own uncommitted changes to the two test files. `bridge/cursor-bridge/bridge-run.py` is unchanged. No test file changes beyond the supervisor's. The cli-reference files appear only if a docstring changed.
- [ ] `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge/bridge-run.py bridge/cursor-bridge/conformance-check.py` prints `0 FAIL`. `python tools/dump-cli.py --check` passes. `MANIFEST.json` is regenerated and still lists `windowless-default.snapshot.md`.
- [ ] No new Semgrep high finding; no traceback, absolute path or control character reaches the floor's output for any input the supervisor's tests give.
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
- **Stop rule.** If any test fails after your change, do not work around it: no change to the code beyond requirements 1 to 4, no edit to a test, no fallback, no skip. Stop, leave the tree as it is, and report the test, its failure's last lines and why you think it fails. This holds for the supervisor's named tests and for every other test, and above all for a failing test whose cause lies outside the Scope (in `bridge-run.py`, say): that is the supervisor's to route, not yours to fix. Round 3's builder worked around an out-of-scope test instead of stopping, and that is how the `_load_bridge_env` fallback came to exist. The one exception is the full suite's environment failures described in the verification commands below.
- Never run the product, a migration, a seed or a test against the owner's live data. Here that means: never run the launcher or the conformance check with a real project as its working folder or target, and never touch the real `~/.claude` or `~/.cursor-bridge`. The conformance check's run on this checkout's own root (inside the existing test) only reads it. The full-suite command below runs this Workspace's own launcher, `bridge/cursor-bridge/bridge-run.py`, never the installed one.
- No value in this increment is marked as the owner's.
- Follow existing conventions in the files you touch: ASCII-only program text (the program says so), the `add(verdict, floor, detail)` rows.
- These git commands are not yours to run: `commit`, `push`, `switch`, `checkout`, `merge`, `rebase`, `reset`, `stash`, `branch -d`, `worktree`; you read with `git status`, `git diff` and `git log` only. In particular, never `checkout` or `restore` a test file: the supervisor's tests exist only in the working tree.
- Numbers from text, a file, a reply or an environment variable are parsed with the language's own parser (`int`, `float`, `json`), never by slicing or splitting a string. This round reads no new number.
- An increment that starts a process (a server, a browser, a worker, a child for a test) meets every point of this checklist: the process is windowless (above); it is stopped in a `finally` or a fixture's teardown, and its whole tree with it; nothing it started outlives the test or the command; a browser launched on Windows is launched attached; its output pipes are closed or drained, so a parent waiting on the pipe is not held open by a child left behind. This round adds no process. The suite's existing tests already meet it.
- **Mutation check.** After the tests pass, mutate by hand in your own run, in-process, and restore the code after each. Write no mutation script; none lands in the diff (the driver is the supervisor's). There are four mutants, one per requirement, each applied with the other three requirements in place: (1) the `ValueError` handling of requirement 1 removed, run against `tests/test_conformance_windowless.py -k nul_in_testpaths`; (2) the `OSError` handling of requirement 2 removed, run against `-k unlistable_tests_folder`; (3) the OK row's path printed raw again, run against `-k ok_row_path_is_escaped`; (4) the backstop of requirement 4 removed, run against `-k floor_backstop`. Before you write the report, confirm with `git diff` that all four are restored.
- Prefer reuse over new code — existing helpers, the standard library, native platform features, already-installed dependencies — and write the minimum that meets the acceptance criteria (the frozen `minimal-code.mdc` is in force). This never overrides a security, observability, or accessibility requirement stated above.
- Verification commands. Run each from the Workspace folder (the folder you were started in), exactly as written:
  - the interpreter's version, once, pasted into the report: `python --version`
  - the supervisor's named tests: `python -m pytest tests/test_bridge_run_driver.py tests/test_conformance_windowless.py -q -p no:cacheprovider -rs -k "nul_in_testpaths_dropped or unlistable_tests_folder_is_no_suite or ok_row_path_is_escaped or floor_backstop_turns_an_error_into_one_note or dotdot_entry_spellings_dropped or uv_run_without_pytest_still_refused"`. Expected result: 16 passed. If `test_r039_ok_row_path_is_escaped` is reported as skipped, copy its reason into the report: requirement 3 is then not verified in your run, and its mutant goes under **Survived**.
  - the increment's tests and the files its changes touch: `python -m pytest tests/test_bridge_run_driver.py tests/test_conformance_windowless.py tests/test_allowlist.py tests/test_tests_windowless.py tests/test_bridge_run.py tests/test_bridge_run_design_ceiling.py tests/test_conformance_check.py tests/test_conformance_check_a4.py tests/test_hotfix25a_conformance_semgrep.py tests/test_calibrate_program.py tests/test_workflows_line_check.py tests/test_b2_least_confident.py tests/test_a4_followups.py tests/test_dump_cli.py -q -p no:cacheprovider -rs`. This must pass. `-rs` prints each skipped test and its reason; copy them into the report.
  - the windowless check: `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge/bridge-run.py bridge/cursor-bridge/conformance-check.py`
  - the command reference: `python tools/dump-cli.py --check`. If it fails because you changed a docstring, run `python tools/dump-cli.py` once, then `python tools/dump-cli.py --check` again.
  - the manifest: `python tools/make-manifest.py --version 2026.10.25a`
  - the full suite, once, at the end, through this Workspace's launcher with no window: `python bridge/cursor-bridge/bridge-run.py --limit auto --kind test -- python -m pytest tests -q -p no:cacheprovider > run/agent/TASK-028-r5-suite.out 2>&1`. Create `run/agent/` first if it does not exist. If your shell can start a command in the background, start it that way and wait for it to end. The output file's last line is then `bridge-run: exit <code>`. Otherwise run it in the foreground; the launcher ends it at its limit. Then read the file. Some install and rollback tests may fail because of your home folder. Do not fix them. Report each full-suite failure outside the list above as an environment observation (test id and its last error line), and say whether it also fails with your changes reverted, if its cause tells you. A failure in any file of the list above falls under the stop rule.

## Done

Your report is the file `handoff/TASK-028-r5-report.md`, which you write as you go — what you did, what you changed, what you ran and what it printed, what you could not do — so that nothing of it is lost when your run ends early. Never paste a computer path or a user name into it: write `<temporary folder>`, `<home>` or `<Workspace>` instead.

When you finish, it holds:
- a list of every file you changed, and only those, checked against `git status` (the two test files' uncommitted changes are the supervisor's; name them as such);
- a one-paragraph summary of what you did;
- one line per finding (Review A 1 / audit HARDENING; Review A 2; Review A 3) and one for the backstop, each saying where in `conformance-check.py` it is fixed and which of the supervisor's tests pins it;
- the output of `python --version`, the named-tests run's last line, and the list of skipped tests with their reasons from `-rs`;
- the windowless check's, `dump-cli --check`'s and the manifest command's last lines, and the full suite's summary line with its `bridge-run: exit <code>` line;
- the mutation table, one row per requirement (1 to 4): the reverted code, the supervisor's test that failed on it, and the failing assertion's last line. A mutant that no test killed in your run goes under **Survived** with the reason. Never list as killed a mutant you did not see killed;
- the full-suite environment observations;
- a section headed exactly `Assumed, not verified`: every fact this change relies on that neither this brief nor the existing code settled, and that you did not confirm — the shape of an external service's request or response, an ambiguous requirement you resolved one way, a platform or library behaviour you expected, a value you chose. One item per line: what you assumed · why · what would confirm it. If there are none, write `Assumed, not verified: none`. Be specific: "edge cases" or "error handling" is not an item. Name only what the code relies on and you did not observe; a behaviour a test of yours observed is verified, not assumed. Name facts of the kind this round's code relies on. Examples: that `escape_field` renders U+202E as `‮` and leaves `/` as it is; that an embedded NUL makes `os.lstat` raise `ValueError` on POSIX as on Windows, and that no `os` call before the walk (`os.path.normpath`, `os.path.commonpath`, `os.path.abspath`) raises first; that `os.path.isfile` returns `False` rather than raising on a NUL; which exceptions the backstop can see from the floor (`OSError`, `ValueError`, `RecursionError`, `UnicodeError`, a failure inside `escape_field`) and that `SystemExit` and `KeyboardInterrupt`, which it does not catch, cannot arise there; that every exception class name the backstop prints is printable ASCII.

Your last message is the summary and the report file's path, and nothing follows it: the supervisor reads only the last message, and a message printed earlier and then followed by more work is lost.
