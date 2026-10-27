# TASK-031 round 7: the blocking findings of round 6's reviews

## Objective

Round 6's head, e435e0e, went through the gate. The security audit failed it (`run/supervisor/task031-security-r6.md`) and Review A rejected it (`run/supervisor/task031-reviewA-r6.md`). This increment is past the owner's three-round review ceiling, so this round carries only findings of the blocking classes: behaviour against the brief or the register, security, data integrity, a defeated safety mechanism, and a failing test. There are three items below, and each names its class. Every other finding of the two reviews is recorded in `docs/HARDENING.md`, under "TASK-031 (round 6's reviews; past the owner's three-round ceiling, recorded, not taken)", and is not yours to fix. **Nothing else in `mutation-run.py` changes**: not its messages, its exit codes, its parser, its configuration names, its order of checks, or any behaviour these three items do not name.

The supervisor wrote red tests in `tests/test_mutation_run_supervisor.py`, under the heading comment "Round 7". They fail on e435e0e, each for the reason its item names. This round makes them pass, and it repairs the builder test that item 3 names. `handoff/TASK-031.md`, `-r2.md`, `-r3.md`, `-r4.md`, `-r5.md` and `-r6.md` still govern everything this file does not change.

Satisfies:
- R-041 (quoted whole in `handoff/TASK-031.md`). The clauses at stake here are "gives every mutant a result against the version the gate reads" (item 2) and "a kill is a named expected test failing in the report ...; the run crashing ... is an error, never a kill" (item 1: a run that rewrites a file outside its scratch folder gives no result to trust). The brief clauses at stake are TASK-031 Requirement 1 (the mutants file is a trust boundary; anything malformed exits 2; a refusal happens before any copy or test and writes nothing) and Requirement 2 (the program writes and removes only its own `mutation-run-<id>/`) for item 1, `handoff/TASK-031-r6.md` item 3 (B-3) for item 2, and `handoff/TASK-031-r6.md` item 7 for item 3.

## Scope

One brief carries one increment's scope; work that needs a second scope is a second brief, never a second section here.

Files you may create or modify:
- bridge/cursor-bridge/mutation-run.py
- tests/test_mutation_run.py
- docs/BUILDER_NOTES.md
- handoff/TASK-031-r7-report.md

Do not modify anything else.

## Out of scope

- `.env` and anything under `secrets/`
- CI configuration (`.github/`, `.githooks/`)
- `docs/` and `handoff/`, except the files the Scope section names. This covers `docs/HARDENING.md`, `docs/INVENTORY.md`, `docs/cli-reference.json` and `docs/CLI_REFERENCE.md`. The parser does not change in this round, so the command reference does not either; never run `python tools/dump-cli.py` without `--check`.
- `tests/test_mutation_run_supervisor.py`. It is the supervisor's: read and run it, never edit it. A test you believe wrong is reported with the reason, never changed or skipped. This covers every Round 7 test.
- `tests/conftest.py` and every other test file
- `bridge/cursor-bridge/MANIFEST.json` and every other file under `bridge/`. Never run `tools/make-manifest.py`.
- `run/supervisor/`
- Every advisory, should-fix and consider finding of the two round-6 reviews other than Review A's Should fix 1 (item 3). Among them: the NT prefix `\??\`, the toml conflict rule, a `setup.cfg` holding a plain `[pytest]` section, the checkpoint loop's alive check, the untracked hard link, the UNC home, the alive message's wording, the `"3" in stderr` match, the `< 125` upper bounds, and the module-global side channel.
- A rule that mutant ids be unique compared case-insensitively. Do not add it: naming the results file by index (item 1) makes it moot.
- A mutation-driver script of any kind. The supervisor's driver runs after you and is its own.

## Context

**Development data.** The inventory's decision, copied verbatim: "Development data: the dev build is the Workspace sources under `bridge/`; a session in the repo always runs the *installed* bridge (`~/.claude`), never the one being edited, and installs reach running projects only through the owner's install run sheet". The tests run the Workspace's `bridge/cursor-bridge/mutation-run.py` by file path, on fixtures under `tmp_path`. `tests/conftest.py`'s autouse fixture `home_of_the_tests` sets `HOME` and `USERPROFILE` to a fresh temporary folder for every test, so the scratch copy falls under that temporary home. Never run `mutation-run.py` with this Workspace or a real project as its working folder. Never touch the real `~/.cursor-bridge/` or `~/.claude/`.

**Security context.** ASVS level 2 (`docs/INVENTORY.md`, Decisions). `.cursor/rules/secure-coding.mdc` and `.cursor/rules/workspace-boundary.mdc` are in force, and so is the frozen minimal-code rule (`bridge/cursor-bridge/minimal-code.snapshot.md`). The trust boundaries this round touches:
- The mutants file under `run/supervisor/`. Any program of the owner's account can write there, so every field of it, the mutant `id` included, is untrusted input (item 1).
- The scratch folder in the owner's home. The program writes and removes only its own `mutation-run-<id>/` subfolder (item 1).
- The project's pytest configuration at the copy's root. It is the project's own file, and its content is untrusted text that must not crash the program (item 2).

**The code as it is (`bridge/cursor-bridge/mutation-run.py` at e435e0e; checked).** The line numbers are approximate; read the code.
- `MUTANT_ID_RX = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")` (:35). Today it is applied only to the run id, in `mutants_file_ok` (:155-166, the check at :164). Python's `$` also matches before a trailing newline, so `MUTANT_ID_RX.match("x\n")` succeeds.
- `load_mutants(path, checkpoint)` (:243-356) checks each mutant's id only as a non-empty string (:270-272) and unique (:273-275). `main` calls it at :1251, before `ls_files_index`, before the scratch folder is created and before any test.
- The mutant loop (:1346-1406) names each mutant's results file `mut_results = os.path.join(plugin_dir, "pytest-outcomes-%s.json" % m["id"])` (:1373) and passes it to `run_mutant_tests(plugin_dir, copy_root, tests, env, timeout_sec, results_path)` (:1175-1183), which removes that path if it is a file (:1176-1177). The outcomes plugin's `_write` (:48-51) then opens the path from `MUTATION_PYTEST_RESULTS` for writing. So an id such as `x\..\..\..\victim` removes and rewrites `victim.json` three folders above `mutation-run-<id>/` (the security audit's N-1, reproduced there with exit 0 and `killed (ran)`).
- The `--checkpoint` loop already names its results by index: `chk_results = os.path.join(plugin_dir, "pytest-outcomes-chk-%d.json" % chk_idx)` (:1294), with `for chk_idx, item in enumerate(items):` (:1293).
- The mutant id is otherwise used as a key of `mutant_keys`, of the cache lookup and lines, and in the summary lines `"%s: %s (%s)"` (:1407-1409).
- `_PYTEST_CONFIG_NAMES` (:826-829) and `_pytest_config_dict_from_file(filepath)` (:832-880). The `.ini` branch (:835-849) and the `.cfg` branch (:850-858) build `configparser.ConfigParser()`, which interpolates `%`, and call `cp.read(filepath, encoding="utf-8")` inside a `try` that catches only `configparser.Error`. The `cp[...].items()` calls (:843, :848, :858) lie outside the `try`, and they are where interpolation raises. `pytest.ini` and `.pytest.ini` count as configuration whatever they hold (`{}` with no `[pytest]` section). `tox.ini` counts with a `[pytest]` section, `setup.cfg` with a `[tool:pytest]` section, and otherwise each returns `None`. The `.toml` branch (:859-879) is not part of this round.
- `copy_pytest_config_file(copy_root)` (:883-891) uses only whether the result `is not None`. Nothing reads the dict's values.
- `run_main` (:1433 on) maps `Refuse` to exit 2, `ResolutionTimeout` to exit 3, and any other exception to `mutation-run: internal error - ...` with exit 3.

**What the supervisor's Round 7 tests print on e435e0e.**
- `test_task031_r7_n1_a_mutant_id_that_is_not_a_plain_name_is_refused`: the run is not refused (exit 0), and `tmp_path/victim.json` is replaced.
- `test_task031_r7_n2_a_pytest_configuration_holding_a_percent_sign_is_read_as_pytest_reads_it[pytest.ini]`, `[tox.ini]` and `[setup.cfg]`: exit 3, `mutation-run: internal error - ...` (an interpolation error), before any mutant runs. Pytest 9.1.1 reads these sections through `iniconfig`, without interpolation, and runs them.

**The grandchild test as it is (`tests/test_mutation_run.py`, about :1244-1290; checked).** `test_r041_grandchild_holding_pipes_times_out` builds a fixture whose `pytest.ini` holds `addopts = -s`, and whose test `test_hold_pipes` starts `[sys.executable, "-c", "import time; time.sleep(3600)"]` with `stdout=sys.stdout, stderr=sys.stderr` and then loops forever. The fixture's `teardown_module` kills the holder. The outer test runs `run_mr(ws, mp, timeout=5, harness_slack=120)` and asserts `elapsed >= 5`, `elapsed < 5 + 120`, exit 3 and `pipe: error (timed out)`. Review A's Should fix 1 names three defects. First, `elapsed >= 5` proves nothing, because the fixture's test loops forever, so the bound is waited out whether or not any pipe is held. Second, nothing shows the holder gone after the run. Third, the holder is not ended by the outer test: `teardown_module` runs inside the pytest that the bound kills, so with `kill_tree` failing (a no-op), the test passes and leaves pytest and a 3600 s sleeper behind. Round 6's report found that `taskkill /T` ends this in-tree holder in about 7 s on Windows. The helpers you can reuse in the same file are `pid_dead(pid)` (:92-107) and `kill_proc_tree(proc)` (:110-124). `test_r041_pipe_holder_outside_tree_cwd_in_copy_times_out` (about :1364-1453) shows the file's pattern for a pid file in `tmp_path`, whose path is embedded in the fixture's source with `json.dumps`, and for ending it in a `finally`.

**The working tree at delegation.** The supervisor's checkpoint commit before this round holds the Round 7 tests and its own edit to `docs/HARDENING.md`. If `git status --porcelain` shows `tests/test_mutation_run_supervisor.py` or `docs/HARDENING.md` changed before you have changed anything, stop and report it, because the `git diff --quiet` criterion below cannot hold then.

**Pytest.** Pytest 9.1.1 is installed (`requirements.lock`). CI runs Python 3.12 on Windows and Ubuntu (`.github/workflows/tests.yml`).

## Diagrams

None. The build plan's `Diagrams:` field for TASK-031 is `none`.

## Requirements

1. **N-1: a mutant id that reaches a file path** (security and data integrity; the security audit's N-1). The fix goes at both causes:
   - (a) In `load_mutants`, every mutant id must match `MUTANT_ID_RX` as a whole string, so an id with a trailing newline is refused too. An id that does not match is refused with exit 2 and a message beginning `mutation-run: `. Like every refusal of `load_mutants`, it happens before any copy or test and writes nothing, not even a cache line. The run id's check in `mutants_file_ok` stays as it is.
   - (b) Each mutant's results file is named by the mutant's index in the loop, as the checkpoint loop names its own (:1294), and never from the mutant id. It is still a path of its own for each run, inside `mutation-run-<id>/` (`handoff/TASK-031-r6.md` item 6), and it never coincides with a checkpoint item's name.
   - Supervisor test: `test_task031_r7_n1_a_mutant_id_that_is_not_a_plain_name_is_refused`.

2. **N-2: a pytest configuration read with interpolation** (behaviour against `handoff/TASK-031-r6.md` item 3 and against R-041's "a result against the version the gate reads"; convergent, Review A's Blocking 1 and the security audit's N-2; a regression from round 5).
   - The `.ini` and `.cfg` branches of `_pytest_config_dict_from_file` read the file without interpolation (`configparser.ConfigParser(interpolation=None)`, as both reviewers name). They decide only whether the pytest section is present. A `%` anywhere in the file never raises.
   - `pytest.ini` and `.pytest.ini` count as configuration whatever they hold, as today.
   - A `.ini` or `.cfg` file that cannot be decoded as UTF-8 or cannot be parsed is a refusal, exit 2, with a message beginning `mutation-run: ` that names the file by its base name. It is never an internal error.
   - The names, their order (`_PYTEST_CONFIG_NAMES`), the condition for each name, and the `.toml` branch stay as they are.
   - Supervisor test: `test_task031_r7_n2_a_pytest_configuration_holding_a_percent_sign_is_read_as_pytest_reads_it`, three cases: `[pytest.ini]`, `[tox.ini]` and `[setup.cfg]`.

3. **The grandchild pipe-holder test** (behaviour against `handoff/TASK-031-r6.md` item 7: "Each holder is ended by the test's own `finally` or teardown, never left behind"; Review A's Should fix 1). Repair `test_r041_grandchild_holding_pipes_times_out` in `tests/test_mutation_run.py`. It keeps its name and stays a holder inside pytest's tree that holds `run_process`'s real pipes (`addopts = -s`, the holder's `stdout` and `stderr` the test's own `sys.stdout` and `sys.stderr`). When it is done:
   - The fixture's test writes the holder's pid, and the pid of its own pytest process, to files under the outer test's `tmp_path`. Each pid is written and flushed before the test starts looping. The holder is started with `creationflags` carrying `CREATE_NO_WINDOW` on the same line (`0` elsewhere).
   - Every check after the run sits inside a `try`, and its `finally` ends whatever is still alive: the holder, and the fixture's pytest with its whole tree. The `finally` uses each pid file that exists, and passes over a process already gone. It does not rely on the fixture's `teardown_module`, which may stay or go.
   - After the run, the test asserts that the holder's pid file exists, so the hold started. It then asserts that the holder and the fixture's pytest are both gone within 10 s of the run's end, polling with `pid_dead`. If either is still alive, the test fails, and the `finally` still ends it.
   - Drop the `elapsed >= 5` assertion, or reword it to say what it shows: that the run waited out the mutant bound, not that a pipe was held. The exit-3 and `pipe: error (timed out)` assertions stay.
   - The docstring names `R-041`, `TASK-031 S7` and `handoff/TASK-031-r7.md item 3`.
   - Check the repaired test against the case Review A names. With `kill_tree` failing, it must fail and leave nothing behind. You may check this by hand in your own run: make `kill_tree` return at once, run this one test, then restore the program's bytes exactly. Report what it printed, and confirm with `git diff -- bridge/cursor-bridge/mutation-run.py` that only your item 1 and item 2 changes remain. No script of this lands in the diff.

## Acceptance criteria

- [ ] The four red tests pass: `test_task031_r7_n1_a_mutant_id_that_is_not_a_plain_name_is_refused` and the three cases of `test_task031_r7_n2_a_pytest_configuration_holding_a_percent_sign_is_read_as_pytest_reads_it`.
- [ ] Every test of `tests/test_mutation_run_supervisor.py` and `tests/test_mutation_run.py` passes. The round-6 b1 administrative-share case and the b2 short-name case may skip where the machine lacks the share or 8.3 names, and only those. `git diff --quiet -- tests/test_mutation_run_supervisor.py` exits 0.
- [ ] No mutant's results file path is built from its id. `grep` for `pytest-outcomes-%s` in `bridge/cursor-bridge/mutation-run.py` finds nothing.
- [ ] A pytest section holding `%` is read with no error. A `.ini` or `.cfg` that does not decode or parse exits 2, never 3.
- [ ] `test_r041_grandchild_holding_pipes_times_out` asserts that the holder and the fixture's pytest are gone after the run, and ends both in its own `finally`. After the run of the two test files, no process the tests started is still running (verification command 7).
- [ ] The grandchild test finishes within its bound plus 120 s. Every other test that starts the program finishes within its ceiling of the earlier briefs. Every `subprocess.run` or `communicate` in a test carries a timeout no larger than its test's ceiling.
- [ ] Every item is fixed at the cause named, never by special-casing a test's fixture. Nothing else in `mutation-run.py` changes.
- [ ] `python tools/dump-cli.py --check` exits 0. `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge/mutation-run.py` prints `0 FAIL`. The program is ASCII only.
- [ ] `git status --porcelain` shows no changed or new file outside Scope.
- [ ] `handoff/TASK-031-r7-report.md` exists, with its `Assumed, not verified` section.

## Constraints

Every constraint of the six earlier briefs holds: `handoff/TASK-031.md`, `-r2.md` to `-r6.md`. There is no mutation run in this round apart from the single by-hand check that item 3 allows. Write no mutation script.

This round adds the following:
- Do not add dependencies. Use the standard library and pytest only. `configparser` with `interpolation=None` is the reuse both reviewers name; do not import `iniconfig`.
- Do not read or write any file outside this workspace (the folder you were started in). The exceptions are pytest's `tmp_path` and the tests' temporary home.
- Every test that runs the program, as a subprocess or in-process, runs it with `HOME` and `USERPROFILE` set to a temporary folder. The autouse `home_of_the_tests` does this; never override it with a real home. No test touches the real `~/.cursor-bridge/` or `~/.claude/`, and no test starts the real `cursor-agent`.
- Do not fix by suppressing the symptom. That rules out a retry, a broad `try/except`, a widened tolerance, an added `sleep`, a longer or removed `--mutant-timeout` bound, and a check that hides a wrong value. The `try/except` that item 2 asks for catches only the decode and parse errors of reading a configuration file, and turns them into a `Refuse`. The report says which exception types it catches.
- Do not edit any test in `tests/test_mutation_run_supervisor.py`. Do not change any test in `tests/test_mutation_run.py` other than `test_r041_grandchild_holding_pipes_times_out`.
- Do not leave any `DEBUG-BUG-` line, `faulthandler` probe or stray print in the program or the tests.
- If you believe the real cause of an item is different from the one named, stop work on that item, do not change code for it, and report why in your summary. The supervisor will re-diagnose.
- Every process your code or your test starts is windowless (`creationflags=subprocess.CREATE_NO_WINDOW`, `0` elsewhere). In `tests/test_mutation_run.py`, including the source text of a fixture, write `CREATE_NO_WINDOW` on the same line as every `creationflags`, as the scan of `tests/test_tests_windowless.py` requires. Nothing a test starts outlives it: each process is stopped in the test's own `finally`, with its whole tree, and its pipes are closed or drained.
- Never start a server, a watcher or a daemon that outlives a test.
- Pids read from a file are parsed with `int()`, never by slicing a string. A pid file that does not parse counts as absent in the `finally`, and as a failure in the assertion that it exists.
- If the brief, the rules or the tooling got in your way, append one dated line to `docs/BUILDER_NOTES.md`. Do the same for anything you learned about a defect or a pitfall. In any Markdown you write, never break a line inside a paragraph or a list item: one paragraph is one line.
- These git commands are not yours to run: `commit`, `push`, `switch`, `checkout`, `merge`, `rebase`, `reset`, `stash`, `branch -d`, `worktree`, `add`. In this Workspace you read with `git status`, `git diff`, `git show` and `git log` only. The tests' fixture repositories under `tmp_path` may use any git command.
- Prefer reuse over new code: `MUTANT_ID_RX`, the checkpoint loop's index naming, `configparser`, and the test file's `pid_dead` and `kill_proc_tree`. Write the minimum that meets the acceptance criteria. This never overrides a security requirement stated above.

## Verification commands

Run each one from the Workspace folder, in this order. Run only these two test files, never the whole suite.
1. `python -m pytest tests/test_mutation_run_supervisor.py tests/test_mutation_run.py -q -p no:cacheprovider -rA --durations=0`
2. `python -m pytest "tests/test_mutation_run.py::test_r041_grandchild_holding_pipes_times_out" -q -p no:cacheprovider -rA --durations=0`
3. `python tools/dump-cli.py --check`
4. `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge/mutation-run.py`
5. `python -c "d=open('bridge/cursor-bridge/mutation-run.py','rb').read(); print(all(b < 128 for b in d))"` (expected: `True`)
6. `git status --porcelain`, then `git diff --quiet -- tests/test_mutation_run_supervisor.py`, and report its exit code
7. On Windows: `tasklist /FI "IMAGENAME eq python.exe" /V`, run after commands 1 and 2 have finished. Say whether any process the tests started is still running, judged by the window titles and the timing, never by a count alone.

## Done

Your report is the file `handoff/TASK-031-r7-report.md`. Write it as you go: what you did, what you changed, what you ran and what it printed, and what you could not do. That way nothing of it is lost if your run ends early. Never paste a computer path or a user name into it; write `<temporary folder>`, `<home>` or `<Workspace>` instead. State only what you ran, quoting pytest's own output, at least its summary line, for every run. Do not repeat a figure from an earlier round's report.

When you finish, the report holds:
- the files you changed;
- one paragraph on what you did;
- for each item: the cause you fixed and where, one sentence on how the change addresses it, and the test or tests that hold it;
- item 1: how a mutant's results file is now named, and why it cannot collide with a checkpoint item's;
- item 2: the exception types the refusal catches, and what a `pytest.ini` holding no `[pytest]` section does now (it must be what it did before);
- item 3: what the repaired test now asserts, how long the holder lived after the bound on your machine, and what the by-hand `kill_tree` check printed;
- the quoted output of each verification command, including the `-rA` lines of the Round 7 tests, any skip with its reason, and the durations of the grandchild test and of the two round-6 item 6 and item 7 tests;
- a section headed exactly `Assumed, not verified`, one item per line (what you assumed; why; what would confirm it). If there are none, write `Assumed, not verified: none`. Be specific: "edge cases" or "error handling" is not an item. Name at least:
  - that `ConfigParser(interpolation=None)` and pytest 9.1.1's `iniconfig` agree on whether a file parses and whether the section is present. Name the differences you know of (duplicate sections or keys, lines without `=`, continuation lines, comments) and which way each one goes;
  - that the grandchild holder's `stdout` is `run_process`'s pipe under `addopts = -s`, not a capture file;
  - the POSIX behaviour of item 3 (the holder in pytest's process group, ended by `os.killpg`), if you could not run it there.

Your last message is the summary and the report file's path, and nothing follows it: the supervisor reads only the last message, and a message printed earlier and then followed by more work is lost.
