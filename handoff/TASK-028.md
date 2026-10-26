# TASK-028: Windowless launches enforced by the bridge: the launcher's driver kind and the suite's frozen default

## Objective

On 2026-10-19/20 the owner's computer crashed during a flood of terminal windows while a builder ran the test suite (ISS-011). The owner decided the fix lives in the bridge, not in each project. This increment does the launcher half of that fix and the suite-default half. First, `bridge/cursor-bridge/bridge-run.py` gains a kind of its own for mutation runs, `--kind driver`. It accepts only `python <program> [args]`, where the program is a Python file under the project's `run/supervisor/` or the installed `mutation-run.py` (TASK-031 builds that file later; the launcher accepts its path now). The kind has its own ceiling and its own health rule. Like every command the launcher starts, a driver run is started windowless, and a test proves on Windows that a grandchild of a driver run has a console with no window. Second, the bridge ships the suite's windowless default (FIX-001's block in `tests/conftest.py`) as frozen text in `bridge/cursor-bridge/windowless-default.snapshot.md`. A test keeps the snapshot and `tests/conftest.py` identical. Third, `conformance-check.py` gains a floor, `Windowless test suite`, that reports whether a project's suite carries that default. The loop's text that uses all of this (TASK-030), the machine-wide slot (TASK-029) and `mutation-run.py` (TASK-031) are later increments.

Satisfies: R-039 — Windowless launches are enforced by the bridge for every project, never by a per-project fix: every heavy run of the loop (a builder, a project's test suite, a mutation run) starts through the launcher (`bridge-run.py`) in the background, which starts it with no window so that every process it creates inherits that unless it detaches itself; and every project's test suite whose runner the bridge ships a default for carries the bridge's frozen windowless default (FIX-001's `tests/conftest.py` default, shipped as a snapshot; pytest in release B, the Node runners' default deferred), reported by the conformance check as a floor.

## Scope

One brief carries one increment's scope; work that needs a second scope is a second brief, never a second section here.

Files and directories you may create or modify:
- bridge/cursor-bridge/bridge-run.py
- bridge/cursor-bridge/conformance-check.py
- bridge/cursor-bridge/windowless-default.snapshot.md (new)
- bridge/cursor-bridge/settings.bridge.json
- bridge/cursor-bridge/MANIFEST.json (regenerated only, by the command in Done)
- tests/conftest.py
- tests/test_bridge_run_driver.py (new)
- tests/test_conformance_windowless.py (new)
- tests/test_allowlist.py
- docs/cli-reference.json
- docs/CLI_REFERENCE.md
- docs/BUILDER_NOTES.md
- handoff/TASK-028-r1-report.md

Do not modify anything else.

## Out of scope

- .env and anything under secrets/
- CI configuration (`.github/`, `.githooks/`)
- docs/ and handoff/, except the files the Scope section names
- `bridge/cursor-bridge/mutation-run.py`: it is TASK-031's. Do not create it, not even as a stub. The launcher accepts its path whether or not the file exists.
- `bridge/cursor-bridge/loop-guard.py` and its `KIND_CEILING` (TASK-029 adds the driver kind there), the machine-wide slot (TASK-029), and every text file of the loop: `delegation-loop.md`, `supervisor.md`, `calibrate-bridge.md`, `Cursor-Project-Configuration.md`, `Known-Pitfalls.md` and the agents (TASK-030).
- `calibration_workflows_grades`, `judge_workflows_line` and the `Workflows line` / `Workflows classification` / `Unwritten trait` floors in `conformance-check.py` (TASK-024 just built them). Leave them byte-for-byte unchanged.
- `project.json`, and the conformance check's `project.json` NOTEs (an unescaped Phase value is a separate lead in `docs/HARDENING.md`; it is not this increment's).
- `tests/test_tests_windowless.py`: do not edit it. It must stay green against your rearranged `tests/conftest.py`.
- Any other test file, including the existing conformance and bridge-run tests. They must keep passing unchanged.

## Context

**Development data.** The inventory's decision, copied verbatim: "Development data: the dev build is the Workspace sources under `bridge/`; a session in the repo always runs the *installed* bridge (`~/.claude`), never the one being edited, and installs reach running projects only through the owner's install run sheet". So the tests run the Workspace's `bridge/cursor-bridge/*.py` by file path, never the installed copy under the real `~/.claude`. Every launcher run in a test runs with a temporary folder as its working folder, because `write_log` writes `run/launcher/runs.jsonl` wherever a `run/` folder exists, and the Workspace has one. `tests/conftest.py`'s autouse fixture `home_of_the_tests` sets `HOME` and `USERPROFILE` to a temporary folder for every test. So `os.path.expanduser("~")`, in the test process and in any child that copies `os.environ`, resolves to that temporary home. That is where a test puts its `<home>/.claude/cursor-bridge/mutation-run.py`. Nothing reads or writes the owner's real home.

**Security context.** ASVS level 2 (INVENTORY, Decisions: "The builder's secure-coding rule is ASVS level 2"). `.cursor/rules/secure-coding.mdc` is in force for you. The trust boundary is the launcher's allow rule. The new rule `bridge-run.py --limit * --kind driver -- *` lets the supervisor's session run any command after `--` without asking the owner. So the launcher's own check of the driver form is the only thing standing between that rule and arbitrary code. That check must fail closed: anything it cannot positively accept is refused before any process starts. Paths are compared after they are made absolute and normalised (case-insensitive on Windows). A link anywhere on the way from the project folder to the program is refused. `bridge_env.is_link(path)` (bridge/cursor-bridge/bridge_env.py:59) already detects a symbolic link and a Windows junction (any reparse point). Reuse it.

**The launcher as built** (bridge/cursor-bridge/bridge-run.py):
- `KINDS = {"builder": 7200, "review": 3600, "watch": 3600, "test": 1800}` (:88), `LEARN_FACTOR = 1.5`, `CAP_FACTOR = 2` (:90-91). `cap_for(kind, folder)` (:236) gives twice the default, or the owner's `Ceiling above twice:` line in `docs/RUN_PARAMETERS.md`.
- `learned_limit(kind, folder)` (:349) learns only from runs with `healthy is True` and `exit in (0, 124)`.
- `main()` (:666) checks `accepted(cmd, folder)` (:198) **before** it reads `--kind` (:688). `accepted` today knows only commands `kind_of` names (cursor-agent, `gh pr checks`, the named test suites). Anything else passes only under `BRIDGE_RUN_ALLOW_ANY=1`, which the existing tests set (`tests/test_bridge_run.py`'s `env_for`). The refusal message is at :679. The unknown-kind message is at :692 and lists `(builder, review, watch, test)`. `usage()` (:105) lists `builder|review|watch|test`.
- The healthy flag is set at :825: `healthy=(True if kind == "test" and rc == 0 else None)`. `mark_healthy(run_id, folder, kind=None)` (:365) is the `--healthy` path.
- The test kind's interpreter decision is inline in `test_suite(argv, folder=None)` at :169-170. The head is the bare runner name (`head_of` strips `.exe`/`.cmd`), so `python`, `python3` and `py` are accepted bare. A path-qualified head is accepted only when `head in ("python", "python3") and own_venv_python(argv[0], folder)` (:143: the project's own `.venv/Scripts/python[3].exe` or `.venv/bin/python[3]` under the launch folder). The driver kind must accept exactly the same interpreters, by the same decision. Factoring it into one helper both kinds call is the expected reuse. Do not keep two copies.
- How it starts commands: `NO_WINDOW = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0` (:86). On Windows the launcher puts itself into a `Job` (kill-on-close) and starts the command with `creationflags=NO_WINDOW | 0x00000200` and explicit standard handles (:782-783). Elsewhere it uses `preexec_fn=os.setsid, creationflags=NO_WINDOW` (:791). `resolve(argv)` (:593) resolves a bare name through `shutil.which` on Windows. `branch_of`, `gh_pr_state` and `local_head` pass `creationflags=NO_WINDOW` already. The driver kind goes through the same start path. Requirement 6 makes this explicit and testable; it does not ask you to build a new mechanism.
- The log entry is built at :742 (`id`, `kind`, `head`, `model`, `branch`, `limit`, `seconds`, `exit`, `healthy`, then `pid`, `child_pid`). `head_text` (:407) never logs an argument.
- The program's module docstring is its command reference (`tools/dump-cli.py` reads it: the `docstring` source). A docstring change means the reference must be regenerated.

**The suite default as built** (tests/conftest.py): `NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)` is at :12, separated from the rest by the `BRIDGE_REVIEW_HASHES` line (:15). `def windowless_kwargs(kwargs):` with its FIX-001 docstring is at :18-32. The `Popen.__init__` wrapper, installed under `if sys.platform == "win32" and not getattr(subprocess.Popen.__init__, "windowless_default", False):`, is at :35-42. `tests/test_tests_windowless.py` does `import conftest` and uses `conftest.windowless_kwargs` and `conftest.NO_WINDOW` at module level. Its `scan()` excludes `conftest.py` and itself, and **scans every other `.py` under tests/, your two new test files included**. A line holding `creationflags=` without `CREATE_NO_WINDOW` on the same line fails `test_fix001_no_test_starts_a_program_around_the_default`, and so does any `os.system` / `os.startfile` / `os.spawn*` / `os.exec*` / `multiprocessing` / `ProcessPoolExecutor` / `CreateProcess`. The window-handle probe is `PRINT_WINDOW` (tests/test_tests_windowless.py:20-21), and `window_and_console` reads its output line. The bridge has no linter in its gate (`.githooks/pre-commit`). The `BRIDGE_REVIEW_HASHES` assignment must still run at conftest import, before any test module is imported.

**The conformance check as built** (bridge/cursor-bridge/conformance-check.py): `main()` (:458) collects rows through `add(verdict, floor, detail="")`. Each row is printed as `"  %-8s %s%s" % (verdict, floor, ("  - " + detail) if detail else "")` (:914). The workspace is `ws` from `resolve_workspace`, and `read(path)` (:98) reads a file. Exit 1 when any row is MISSING. The existing tests' fixture `make_workspace` (tests/test_conformance_check.py:61) has a `package.json` of `{}` and no `tests/` folder. With your floor it gets the "none seen" NOTE. That is fine: `tests/test_b2_least_confident.py` compares a shaped workspace's NOTE lines with `plain_notes` (both built by `make_workspace` in differently named folders), and `tests/test_calibrate_program.py` filters rows by floor. **Your NOTE detail must therefore never contain the project's path or folder name** (also rule 54). The bridge's own Workspace has no `pytest.ini`, `pyproject.toml` or `setup.cfg`. Its suite is seen through `tests/` holding `test_*.py`, and its conftest is `tests/conftest.py`.

**The allow rule as built** (bridge/cursor-bridge/settings.bridge.json:8): `"Bash(python ~/.claude/cursor-bridge/bridge-run.py --limit * --kind test -- *)"`. `tests/test_allowlist.py` checks rules with `decide(cmd, ALLOW, DENY)` and `rule_matches(rule, cmd)` from `tests/permission_rules.py`. No test there names the test kind's rule explicitly today.

**`mutation-run.py` absent.** Nothing in the bridge imports or lists it today, and `tools/dump-cli.py` and `tools/make-manifest.py` read only the files that exist. The launcher only compares the path, so the file's absence breaks nothing.

**The Node default is deferred.** INVENTORY, Deferred: release B ships the pytest default only. A Node suite gets a NOTE naming the runner and KP-059's verified mechanism (`detached: false` on a helper's launch).

## Diagrams

None. The build plan's `Diagrams:` field for TASK-028 is `none`, and the inventory records "No diagram index for release B".

## Requirements

1. **The driver kind.** `bridge-run.py --limit <seconds|auto> --kind driver -- <interpreter> <program> [args...]` is accepted only when all of these hold:
   - (a) `<interpreter>` is one the test kind accepts, by the one shared decision described in Context: bare `python`, `python3` or `py`, or the project's own `.venv` interpreter.
   - (b) The token right after the interpreter is the program. Any interpreter option before it is refused. That covers `-c`, `-m` and any other leading `-` token (`-I`, `-X`, `py -3`).
   - (c) The program is either:
     - a path ending in `.py` whose absolute, normalised form lies inside `<launch folder>/run/supervisor/` (subfolders allowed), with no link at any component from the launch folder down to the program itself (`run`, `run/supervisor`, any subfolder, the file), checked with `bridge_env.is_link`, and with `..` resolved before the comparison, so that `run/supervisor/../../x.py` is outside; or
     - exactly `<home>/.claude/cursor-bridge/mutation-run.py`, `<home>` being `os.path.expanduser("~")`, given absolute or with a literal leading `~/` (or `~\`), compared case-insensitively on Windows and with either separator. Whether that file exists is not checked.
   - Arguments after the program are passed to it unchanged.
2. **Refusals.** Every other command under `--kind driver` is refused with exit 125 before anything starts, and nothing is written to `runs.jsonl`. The single stderr line begins exactly `bridge-run: refused - driver kind: ` and contains the substrings `run/supervisor/` and `mutation-run.py`. This includes a driver form whose program is elsewhere, a link on the way, `-c`, `-m`, an interpreter the test kind refuses, and a non-`.py` file. `BRIDGE_RUN_ALLOW_ANY=1` does not exempt a `--kind driver` command from this check. A driver form launched without `--kind driver` is refused as today (exit 125, the existing :679 message), outside `BRIDGE_RUN_ALLOW_ANY=1`. Every other kind keeps its current acceptance exactly: `tests/test_bridge_run.py` and `tests/test_bridge_run_design_ceiling.py` stay green unchanged.
3. **Ceiling.** `KINDS["driver"]` is 7200. Its cap is `CAP_FACTOR` times that, 14400, by the existing `cap_for` rule (the owner's `Ceiling above twice: driver <seconds> (...)` line lifts it as for any kind). `--limit auto` prints `bridge-run: limit 7200s for driver (the default for driver)` with no healthy driver run on record. An explicit limit above the cap is refused with the existing "above twice the default" message. `usage()`, the unknown-kind message and the docstring name `driver` among the kinds.
4. **Health and learning.** At exit 0 or exit 1 (the set completed), the launcher itself records a driver run `healthy: true`. At any other exit (124, 2, 3, 4, 125...) the run is recorded with `healthy` not true. `learned_limit("driver", folder)` learns from healthy driver runs at exit 0 **and** 1, and from no other exit. `--healthy <id>` naming a driver run whose recorded exit is neither 0 nor 1 exits 1, leaves `runs.jsonl` unchanged, and prints one line beginning `bridge-run: refused - ` that names the rule (a driver run is healthy at exit 0 or 1 only). The other kinds' health and learning rules are unchanged (the test kind at exit 0; others by `--healthy`; learning at 0 and 124).
5. **Log line.** A driver run's `runs.jsonl` entry has `"kind": "driver"`. Its `head` is the interpreter's name as `head_text` gives it, with no program path, argument or option. Its `limit` is the limit used, plus `seconds`, `exit` and `healthy` per requirement 4, and the same other fields as every run.
6. **Windowless start.** Every process `bridge-run.py` starts, the driver's included, is started with `CREATE_NO_WINDOW` on Windows (the existing start path; no `visible-ok` exemption is added). `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge/bridge-run.py bridge/cursor-bridge/conformance-check.py` prints `0 FAIL`.
7. **The snapshot.** `bridge/cursor-bridge/windowless-default.snapshot.md` holds a short heading and prose saying what the block is, where it comes from (FIX-001, rule 24, KP-014, R-039) and that a project's test root `conftest.py` carries it verbatim. It also holds exactly one fenced block opened by a line of three backticks followed by `python` and closed by a line of three backticks. The block is self-contained: its own `import subprocess` and `import sys`, the `NO_WINDOW` constant, `windowless_kwargs` with its FIX-001 docstring unchanged in meaning, and the `if sys.platform == "win32" and not getattr(...)` wrapper installation. Only the block's text is code, and the file is `.md` so that `dump-cli.py` and `windowless-check.py` read no program there.
8. **conftest rearranged.** `tests/conftest.py` holds the block's text verbatim as one contiguous run of lines, byte-for-byte equal to the fenced block's content apart from line endings. The rest of the file is ordered around it so that `import subprocess` and `import sys` appear only inside the block, `BRIDGE_REVIEW_HASHES` is still set at import, `load_program`, `program` and `home_of_the_tests` are unchanged, and `conftest.windowless_kwargs` and `conftest.NO_WINDOW` stay module attributes. `tests/test_tests_windowless.py` passes unchanged.
9. **The floor `Windowless test suite`** in `conformance-check.py`, added after the existing `Windowless check` row (:579) and before the lockfile rows. It reads only the project's own files, never a value of `.env` or any secret, and prints no absolute path. All three NOTE and MISSING rows below are produced from the Workspace's files alone.
   - A **pytest suite** is seen when any of these holds: the Workspace root has a `pytest.ini`; `pyproject.toml` has a `[tool.pytest.ini_options]` table; `setup.cfg` has a `[tool:pytest]` section; or a `tests/` folder holds at least one `test_*.py`.
   - Its **test roots** are the folders that configuration's `testpaths` names, else `tests/`. Its **rootdir** is the Workspace root.
   - It is OK when the rootdir's `conftest.py` holds the three tokens, or every test root's `conftest.py` does. The three tokens are `windowless_kwargs`, `Popen.__init__` and `CREATE_NO_WINDOW`, each anywhere in the file. The row is exactly `  OK       Windowless test suite (<relative path of the conftest.py that satisfied it, forward slashes>)`, e.g. `  OK       Windowless test suite (tests/conftest.py)`.
   - Otherwise it is MISSING, with the floor `Windowless test suite` and a detail that names `windowless-default.snapshot.md` and `Cursor-Project-Configuration.md` (its windowless-default item), and the three tokens.
   - A **Node suite** is seen when the root `package.json`'s `scripts.test` names `vitest`, `jest`, `playwright` or `node --test`. It gives a NOTE on the floor `Windowless test suite` whose detail names that runner, says release B ships no default for it (INVENTORY, Deferred), and names `detached: false` and KP-059. When both a pytest and a Node suite are seen, both rows are printed.
   - When neither is seen, one NOTE on the floor `Windowless test suite` whose detail names what the check saw. If a root `package.json` has a `test` script, the detail quotes that script's first word. Otherwise the detail says no pytest configuration, no `tests/test_*.py` and no `package.json` test script were found.
   - The module docstring's "What it checks" list gains one bullet for this floor.
10. **Allow rule.** `settings.bridge.json`'s `permissions.allow` gains `"Bash(python ~/.claude/cursor-bridge/bridge-run.py --limit * --kind driver -- *)"`, placed beside the test kind's rule. No other entry changes.
11. No new dependency. Parse `package.json` with `json`, an `.ini`/`.cfg` with `configparser`, and `pyproject.toml` with the standard library. Numbers read from argv (`--limit`) keep the existing `float` parse.

## Acceptance criteria

- [ ] **`tests/test_bridge_run_driver.py`** (module docstring names R-039; every test name or docstring names R-039). Each launcher run uses a temporary launch folder holding `run/`, and the program files are built in the test. It covers:
  - Accepted, each launched end to end and exiting with the program's code: a program under `run/supervisor/`, given relative and absolute, and in a subfolder; `<home>/.claude/cursor-bridge/mutation-run.py` (written by the test into the temporary home), given absolute and as `~/.claude/cursor-bridge/mutation-run.py`.
  - Each accepted interpreter: `python`, `python3`, `py` and `<launch folder>/.venv/Scripts/python.exe` (`.venv/bin/python` off Windows). These are asserted through the launcher's own acceptance function loaded with `program("bridge-run")`, so no interpreter needs to be installed.
  - Each refused form launched without `BRIDGE_RUN_ALLOW_ANY`, and again with it set to `1`, asserting `returncode == 125`, a stderr line starting `bridge-run: refused - driver kind: ` and containing `run/supervisor/` and `mutation-run.py`, and no `runs.jsonl` line. The refused forms: a program in the launch folder outside `run/supervisor/`; `run/supervisor/../x.py`; a program reached through a junction (Windows) or symbolic link (elsewhere) at `run/supervisor` or at a subfolder (make it as `tests/test_workflow_check.py`'s `_link_folder` does, without privilege on Windows); `-c "print(1)"`; `-m pytest`; `py -3 <program>`; a `.txt` program; `C:/anywhere/python.exe` as the interpreter.
  - A driver form under `--kind test` refused with exit 125.
  - The ceiling: `learned_limit("driver", ...) == (7200, "the default for driver")` on an empty log; `cap_for("driver", ...)[0] == 14400`; `--limit 14401 --kind driver` refused with exit 125 and `above twice the default`.
  - Health: exit 0 and exit 1 logged `healthy: true`; exits 2, 3 and 124 logged with `healthy` not `True`.
  - Learning: a log built in the test where a healthy driver run at exit 1 of 6000 s gives `learned_limit("driver", ...)[0] == 9000`, and a driver row at exit 3 marked `healthy: true` by hand is not learned from.
  - `--healthy` on a driver run at exit 3: exit 1, the `bridge-run: refused - ` line, the log unchanged.
  - The log line's `kind == "driver"` and `head` with no program path.
- [ ] **The windowless grandchild** (Windows; on other platforms `pytest.mark.skipif(sys.platform != "win32", reason="console windows exist only on Windows")`). A driver program under `run/supervisor/` starts a grandchild with plain `subprocess.run([sys.executable, "-c", PRINT_WINDOW], capture_output=True, text=True)` (no creation flags) and prints its own pid and the grandchild's line, as `tests/test_tests_windowless.py`'s `GRANDCHILD` does. Run through `bridge-run.py --limit 120 --kind driver -- python <program>` with exit 0, the test asserts:
  - the grandchild's `GetConsoleWindow()` is 0;
  - the driver's pid and the grandchild's pid are on that console;
  - the launcher's own pid (the `pid` field of the run's `runs.jsonl` entry) is **not** on it, which proves the launcher gave the driver a new windowless console rather than letting it inherit its own.
  Processes are named, never counted (a virtual environment's `python.exe` may add a process of its own). `python` must resolve to the test's interpreter. Giving the launcher an environment whose `PATH` starts with `os.path.dirname(sys.executable)` does that.
- [ ] **`tests/test_conformance_windowless.py`** (names R-039). Fixtures are built in the test under `tmp_path`, never from a real project's files. It asserts the exact `Windowless test suite` row(s) of `python bridge/cursor-bridge/conformance-check.py <root> --offline` for:
  - OK at the test root (`tests/conftest.py` holding the three tokens): the row `  OK       Windowless test suite (tests/conftest.py)`;
  - OK at the rootdir (`conftest.py` at the root, `tests/conftest.py` absent): `(conftest.py)`;
  - OK through `pytest.ini`'s `testpaths = checks` with `checks/conftest.py`;
  - MISSING for a `tests/test_x.py` suite with a conftest lacking one of the tokens, and again for each of the three pytest configurations with no conftest, each with the detail naming `windowless-default.snapshot.md` and `Cursor-Project-Configuration.md`, and exit 1;
  - the Node NOTE for each of `vitest`, `jest`, `playwright` and `node --test`, the detail naming the runner, `detached: false` and KP-059;
  - the "other runner" NOTE for a `package.json` test script `mocha`, naming `mocha`;
  - the "none seen" NOTE for an empty Workspace with `docs/`;
  - both a pytest and a Node row for a project with both;
  - the bridge's own Workspace (the repository root of this checkout) graded OK with `(tests/conftest.py)`.
  Every row asserted is one row; there is never a second `Windowless test suite` row except in the both-suites case. No asserted detail contains the fixture's folder name.
- [ ] **The snapshot, in `tests/test_conformance_windowless.py`.** One test asserts that the snapshot file has exactly one fenced `python` block and that `tests/conftest.py`'s text (line endings normalised) contains that block's text verbatim as one contiguous run. A second test writes the block alone as `conftest.py` into a temporary project with a one-line test that asserts `getattr(subprocess.Popen.__init__, "windowless_default", False) is (sys.platform == "win32")`, then runs `python -m pytest -q -p no:cacheprovider` there with `cwd` that project, with exit 0. A third asserts that `windowless-check.py` and `dump-cli.py` read no `.md` file (the snapshot's name is in neither's scanned set).
- [ ] **`tests/test_allowlist.py`** gains one test (named for R-039) asserting `"Bash(python ~/.claude/cursor-bridge/bridge-run.py --limit * --kind driver -- *)" in ALLOW`, and that `decide(cmd, ALLOW, DENY)[0] == "allow"` for `python ~/.claude/cursor-bridge/bridge-run.py --limit auto --kind driver -- <interpreter> run/supervisor/task028_mutants.py` with each of `python`, `python3`, `py`, `.venv/Scripts/python.exe`, and for the installed `~/.claude/cursor-bridge/mutation-run.py run/supervisor/TASK-028-mutants.json` form. Its existing tests pass unchanged.
- [ ] `tests/test_tests_windowless.py`, `tests/test_bridge_run.py`, `tests/test_bridge_run_design_ceiling.py`, `tests/test_conformance_check.py`, `tests/test_conformance_check_a4.py`, `tests/test_hotfix25a_conformance_semgrep.py`, `tests/test_calibrate_program.py`, `tests/test_workflows_line_check.py`, `tests/test_b2_least_confident.py`, `tests/test_a4_followups.py` and `tests/test_dump_cli.py` pass unchanged.
- [ ] `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge/bridge-run.py bridge/cursor-bridge/conformance-check.py` prints `0 FAIL`. `python tools/dump-cli.py --check` passes after regeneration. `MANIFEST.json` is regenerated and lists the snapshot.
- [ ] Every requirement under "Satisfies" is fully met: no stand-in, placeholder screen, "coming soon" or "arrives in a later stage" text, and at least one test names each requirement ID (in its name, docstring or a comment) so the trace is checkable.

## Constraints

- Do not add dependencies.
- Do not read or write any file outside this workspace (the folder you were started in). Everything you need is inside it; everything you produce goes inside it. The tests' temporary folders and temporary home are the only exception, and they come from pytest's `tmp_path` and `home_of_the_tests`.
- If the brief, the rules, or the tooling got in your way (an instruction that contradicted another, a check that fired wrongly, a step that cost time for no reason), append one dated line describing it to `docs/BUILDER_NOTES.md`. Do not try to fix the tooling. Do the same for anything you learned about a defect or a pitfall (a cause you found, a platform quirk that cost you a round): one dated line, so the supervisor can carry it forward.
- In any Markdown you write, never break a line inside a paragraph or a list item; one paragraph is one line. Line breaks only between blocks. (The snapshot's fenced block is code and keeps its own lines.)
- This increment talks to no external service.
- Any console process your code launches on Windows is created windowless (`creationflags=subprocess.CREATE_NO_WINDOW` in Python, `0` on other platforms). Capturing output does not prevent the window. A window is allowed only when it serves the user (they watch it or type into it); then write the reason at the call site as `windowless: visible-ok <reason>`. A spawn that needs a process group for a `CTRL_BREAK` stop is hidden only with a test of the stop path. In tests, a launch either sets no creation flags (the suite default applies) or sets them with `CREATE_NO_WINDOW` on the same line, so that `tests/test_tests_windowless.py`'s scan stays empty.
- Never start a server, a watcher or a daemon that outlives a test: a test that needs the product running starts it through the test framework's own fixture and stops it there. A server left running keeps your run from ending.
- Do not refactor code outside the scope, even if it looks wrong.
- If an existing test outside the Scope fails because of this increment's change (for example a test that counts the conformance check's NOTE rows), do not edit that test: stop, leave the tree as it is, and report the test, its failure and why your change causes it.
- Never run the product, a migration, a seed or a test against the owner's live data. Here that means: never run the launcher with the Workspace (or any real project) as its working folder in a test, and never touch the real `~/.claude` or `~/.cursor-bridge`.
- No value in this increment is marked as the owner's. The figures 7,200 s, 14,400 s and exits 0/1 are the build plan's.
- Follow existing conventions in the files you touch: ASCII-only program text (both programs say so), the `bridge-run: refused - ` message form, the `add(verdict, floor, detail)` rows, and tests in the style of `tests/test_bridge_run.py` (subprocess runs of `PROG` with `capture_output=True, text=True`, the program loaded through the `program` fixture for its functions).
- These git commands are not yours to run: `commit`, `push`, `switch`, `checkout`, `merge`, `rebase`, `reset`, `stash`, `branch -d`, `worktree`. You read with `git status`, `git diff` and `git log` only.
- Numbers from text, a file, a reply or an environment variable are parsed with the language's own parser (`int`, `float`, `json`), never by slicing or splitting a string. The units: `--limit` is seconds, a positive number, at most the kind's cap. Exit codes are integers.
- An increment that starts a process (a server, a browser, a worker, a child for a test) meets every point of this checklist: the process is windowless (above); it is stopped in a `finally` or a fixture's teardown, and its whole tree with it; nothing it started outlives the test or the command; its output pipes are closed or drained. Every launcher run in your tests passes a `timeout=` to `subprocess.run`. A driver program a test writes ends by itself within seconds.
- Mutation check: after your tests pass, mutate by hand in your own run, in-process, each of these and confirm a test fails:
  - the `run/supervisor/` containment check;
  - the link check;
  - the leading-option refusal;
  - `KINDS["driver"]`;
  - the exit set `(0, 1)` in health and in learning;
  - the `BRIDGE_RUN_ALLOW_ANY` non-exemption;
  - `CREATE_NO_WINDOW` on the Windows start path;
  - each of the three tokens in the floor;
  - the rootdir alternative;
  - the snapshot's verbatim comparison.
  Restore the code after each. List each mutation with the test that caught it in your report. Write no mutation script, and none lands in the diff (the driver is the supervisor's).
- Prefer reuse over new code (existing helpers, the standard library, native platform features, already-installed dependencies), and write the minimum that meets the acceptance criteria (the frozen `minimal-code.mdc` is in force). This never overrides a security, observability, or accessibility requirement stated above.
- **Your own shell's window, a hint for the record (KP-014, KP-006, KP-010).** You are running under the launcher. Once, in your own shell during this run, run exactly this command from the Workspace folder: `python -c "import ctypes, os; k = ctypes.windll.kernel32; a = (ctypes.c_uint * 64)(); n = k.GetConsoleProcessList(a, 64); print(k.GetConsoleWindow(), os.getpid(), *a[:n])"` (it is `PRINT_WINDOW` from `tests/test_tests_windowless.py:20-21`). Paste its printed line into your report under a heading `Window-handle probe (a hint, KP-010)`. Say whether the first number (the console window handle) is 0, and how many process ids followed. Label it a hint: the owner's screen during the run is the observation, and the supervisor records it. If the command fails (not Windows, no `ctypes.windll`), paste the error's last line instead.
- Verification commands, each from the Workspace folder (the folder you were started in):
  - the increment's tests and the files its changes touch: `python -m pytest tests/test_bridge_run_driver.py tests/test_conformance_windowless.py tests/test_allowlist.py tests/test_tests_windowless.py tests/test_bridge_run.py tests/test_bridge_run_design_ceiling.py tests/test_conformance_check.py tests/test_conformance_check_a4.py tests/test_hotfix25a_conformance_semgrep.py tests/test_calibrate_program.py tests/test_workflows_line_check.py tests/test_b2_least_confident.py tests/test_a4_followups.py tests/test_dump_cli.py -q -p no:cacheprovider`. This must pass.
  - the windowless check: `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge/bridge-run.py bridge/cursor-bridge/conformance-check.py`
  - the command reference: `python tools/dump-cli.py`, then `python tools/dump-cli.py --check`
  - the manifest: `python tools/make-manifest.py --version 2026.10.25a`
  - the full suite, once, at the end: `python -m pytest tests -q -p no:cacheprovider`. In your environment some install and rollback tests may fail because of your home folder, as they did for TASK-024. Do not fix them. Report each full-suite failure outside the list above as an environment observation (test id and its last error line), and say whether it also fails with your changes reverted, if you can tell from the failure's cause.

## Done

Your report is the file `handoff/TASK-028-r1-report.md`, which you write as you go (what you did, what you changed, what you ran and what it printed, what you could not do) so that nothing of it is lost when your run ends early. Never paste a computer path or a user name into it: write `<temporary folder>`, `<home>` or `<Workspace>` instead.

When you finish, it holds:
- a list of every file you changed;
- a one-paragraph summary of what you did;
- the window-handle probe's line under its heading, labelled a hint;
- the mutation list (each mutation and the test that caught it);
- the full-suite environment observations;
- a section headed exactly `Assumed, not verified`. List every fact this change relies on that neither this brief nor the existing code settled, and that you did not confirm: an ambiguous requirement you resolved one way, a platform or library behaviour you expected, a value you chose. One item per line: what you assumed · why · what would confirm it. If there are none, write `Assumed, not verified: none`. Be specific: "edge cases" or "error handling" is not an item.

Your last message is the summary and the report file's path, and nothing follows it: the supervisor reads only the last message, and a message printed earlier and then followed by more work is lost.
