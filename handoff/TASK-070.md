---
record: brief
header: 1
id: "TASK-070"
round: 1
satisfies: [R-090]
scope: ["bridge/cursor-bridge/mutation-run.py", "bridge/cursor-bridge/MANIFEST.json", "docs/cli-reference.json", "docs/CLI_REFERENCE.md", "tests/test_program_mutation_baseline.py", "tests/test_mutation_run.py", "tests/test_mutation_run_supervisor.py", "docs/BUILDER_NOTES.md", "handoff/TASK-070-r1-report.md"]
merge_unit: null
blocking_class: null
---
# TASK-070: The mutation run's ids and its baseline (R-090)

## Objective
`bridge/cursor-bridge/mutation-run.py` (run as `python ~/.claude/cursor-bridge/mutation-run.py <mutants file>`) applies each mutant in a scratch copy of the Workspace and runs the mutant's `tests` list with pytest, reading the outcomes from a small pytest plugin it writes into the scratch folder. It has two defects. (1) The plugin records every node id with all its backslashes turned into slashes, so a parametrized test whose id holds a backslash escape (pytest writes the value `'caf' + chr(0xE9)` as `caf\xe9` inside the brackets) is recorded under an id no `expect_fail` or `new_tests` entry can match: the mutant reads `error (expected id absent)`, and in `--checkpoint` mode the new test reads `not run`. (2) The program never checks that a mutant's tests pass on the unmutated code, so an `expect_fail` test that already fails unmutated reads as a kill, and a list that fails or errors unmutated turns every mutant into an error. This increment makes the plugin replace backslashes in the file part of a node id only, in both modes. It also adds a baseline: before the mutant loop, each distinct `tests` list of the mutants about to run (not those served from the cache) runs once on the unmutated copy. A failure or an error there ends the run with a new exit 5, one line per failing list and no mutant run. A list that times out has its mutants reported `error (timed out)` without being run. The docstring and the `--help` text name the new exit, and the generated files are regenerated.

Satisfies: R-090 - A mutation run matches its ids and proves its baseline (C17, C22): the outcomes record replaces backslashes in a node id's file part only, in `--checkpoint` mode too, so a parametrized id holding an escape matches its `expect_fail` entry; before the mutant loop each distinct `tests` list of the mutants about to run, none served from the cache, runs once on the unmutated copy, and a failure or an error there ends the run with exit 5 and a line naming the list and the ids, no mutant run and the cache untouched; step 7's list of the run's results names the exit. (Its row in `docs/REQUIREMENTS.md`, line 116. This brief serves the program. The clause "step 7's list of the run's results names the exit" is a workflow text and not this brief's.)

## Scope
Files and directories you may create or modify:
- bridge/cursor-bridge/mutation-run.py
- bridge/cursor-bridge/MANIFEST.json
- docs/cli-reference.json
- docs/CLI_REFERENCE.md
- tests/test_program_mutation_baseline.py
- tests/test_mutation_run.py
- tests/test_mutation_run_supervisor.py
- docs/BUILDER_NOTES.md
- handoff/TASK-070-r1-report.md

Limits on these paths:
- `bridge/cursor-bridge/mutation-run.py`: R1-R9 below. No new command-line option. No other behaviour changes.
- `tests/test_program_mutation_baseline.py`: the supervisor's acceptance tests, committed at 4763d95 (thirteen cases). Read it whole and run it. **Do not edit it.** If a case seems wrong, stop and report it by its test id.
- `tests/test_mutation_run.py` and `tests/test_mutation_run_supervisor.py`: listed so that you run them, and for one kind of edit only, described under Context, "Edits allowed in the two existing test files". Add no test to either, and do not edit the three fixtures the supervisor rewrote (Context).
- `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` change only by running `python tools/dump-cli.py` (Done), never by hand.
- `bridge/cursor-bridge/MANIFEST.json` changes only by running `python tools/make-manifest.py` (Done), never by hand. `bridge/cursor-bridge/VERSION` is outside Scope and reads `2026.11.12a`. `make-manifest.py` rewrites its line endings, so restore it with `git restore bridge/cursor-bridge/VERSION` right after (Done).

Do not modify anything else.

## Out of scope
- .env and anything under secrets/
- CI configuration
- docs/ and handoff/, except the files the Scope section names. Every record under docs/ is the supervisor's.
- Every other program under `bridge/cursor-bridge/`, the texts under `bridge/commands/`, `bridge/agents/` and `bridge/cursor-bridge/workflow/` (step 7's list of the run's results included), and `bridge/cursor-bridge/CHANGELOG.md`.
- `tools/make-manifest.py` and `tools/dump-cli.py`: you run them and edit neither.
- Every test file other than the three in Scope. Those named in the Done list's commands must pass unedited; report a failure there by its test id.
- `run/` (the supervisor's reproduction script and checkpoint output live there; you read them and write nothing there).
- Any mutation script or mutants file. The mutants file and the mutation run are the supervisor's, after your run.

## Context
**The design that binds this increment:** `docs/DESIGN.md` line 353, the bullet beginning `- *C17 and C22.*`: "`mutation-run.py`'s outcomes record replaces backslashes in a node id's file part only, so a parametrized id holding an escape matches its `expect_fail` entry, in `--checkpoint` mode too. Before the mutant loop each distinct `tests` list of the mutants about to run (none served from the cache) runs once on the unmutated copy; a failure or an error there ends the run with a new exit 5 and a line naming the list and the ids, which also catches an `expect_fail` test that fails unmutated and reads as a kill today." The plan entry is `docs/BUILD_PLAN.md`, `### TASK-070` (line 1892), its Done when at line 1901. The supervisor's rulings below settle what the design leaves open: the timeout, the other pytest exits, the placement.

**The reproduction (the supervisor's run before this brief, `run/supervisor/task070_repro.py`).** In a scratch git repository holding `mod.py` (`def double(x): return x * 2`) and `tests/test_mod.py` with one test parametrized with the value `'caf' + chr(0xE9)`, pytest's collected id is `tests/test_mod.py::test_double[caf\xe9]` (a literal backslash, then `x`, `e`, `9`). A mutant `x * 2` -> `x * 3` whose `expect_fail` names that id, run with `--all`, gives:

```
m1: error (expected id absent) (ran)
```

with exit 3. The same scenario with the ASCII value `cafe` (id `tests/test_mod.py::test_double[cafe]`) gives:

```
m1: killed (ran)
```

with exit 0. **The cause:** the outcomes plugin records `nodeid = report.nodeid.replace(chr(92), "/")` (`mutation-run.py` line 80), which also rewrites the backslash inside the parametrize brackets, so the recorded id is `...[caf/xe9]` and never equals the entry. Line 86 does the same for collection errors (`_state["collect_errors"].append(report.nodeid.replace(chr(92), "/"))`). The same plugin serves the `--checkpoint` mode (lines 1501-1510), where `checkpoint_records_for_item(item, tests_run)` (lines 1068-1076) compares the recorded id with the `new_tests` entry, so the escaped id reads `not run` there.

**The program as it stands (checkpoint 4763d95), the places this increment touches.**
- Docstring, lines 2-11. The exit list (lines 7-10): "Exit 0 when every mutant is killed (or cached kill); 1 when any survived, was not applied, or an expect-survive mutant was killed; 2 for a malformed file, refused path or resolution check, or --all with --checkpoint; 3 when any mutant errored or on an internal crash; 4 in --checkpoint mode when any listed new test passed on the old code." `build_parser()` (lines 1395-1412) repeats it in `desc` (lines 1400-1403). `tools/dump-cli.py` records both, so a change to either regenerates `docs/cli-reference.json` and `docs/CLI_REFERENCE.md`.
- `OUTCOMES_PLUGIN_CODE` (lines 50-93): `pytest_runtest_logreport` (64-81) records `{"nodeid", "outcome"}` with outcome `passed`/`failed`/`skipped`/`error` (a failure outside the call phase is `error`); `pytest_collectreport` (84-86) records collection errors; `pytest_sessionfinish` writes the JSON to `MUTATION_PYTEST_RESULTS`.
- `load_mutants(path, checkpoint)` (253-368) normalizes each `tests` entry with `normalize_rel` and checks each `expect_fail` id's file part (`tid.split("::", 1)[0]`) is in the mutant's `tests`. It keeps `tests` as a list in the order given.
- `run_process(argv, env, cwd, timeout_sec)` (533-558) returns `(rc, out, err, timed_out)` and sets `_last_run_process_still_alive` when the process outlived the kill; `run_mutant_tests(plugin_dir, copy_root, tests, env, timeout_sec, results_path)` (1351-1359) runs `python -m pytest -p _mutation_outcomes -p no:cacheprovider <config argv> <tests>` with `pytest_env(...)` and returns `(rc, out, err, timed, still_alive, data)`; `read_pytest_results` (1005-1015) returns `None` unless the session finished.
- `classify_outcome(data, expect_fail, timed_out)` (1036-1057): timed out -> `error (timed out)`; no data -> `error (no pytest result)`; collection errors -> `error (collection error)`; an `expect_fail` id absent -> `error (expected id absent)`; any `ERROR` -> `error (test error)`; a `FAILED` id not in `expect_fail` -> `error (unexpected failure)`; an `expect_fail` id `FAILED` -> `killed`; else `survived`. Today an `expect_fail` test that already fails unmutated reads `killed` here.
- `main()` (1415-1637), ordinary mode: the cache is read at lines 1443-1445 (`cache = read_cache(cache_path)`); the copy is made (1544-1545); the resolution check runs (1546-1549); the keys are computed at line 1550 (`mutant_keys = {m["id"]: compute_key(copy_root, m, tracked_set) for m in mutants}`); the mutant loop (1553-1613) serves a mutant from the cache when `cached and cached[0] == "killed" and not args.all` (1557-1558); a mutant's pytest `rc not in (0, 1)` that did not time out is `error (pytest exit <rc>)` (1587-1588); a pytest that outlived the kill sets `pytest_still_alive` and breaks the loop (1584-1586, 1612-1613); then the result lines `<id>: <outcome> (<ran|cached>)` (1614-1616), the `counts:` line (1617-1619), and at lines 1620-1626 the still-alive stop: `print("mutation-run: pytest did not exit within %d s after the mutant timeout" % timeout_sec, file=sys.stderr)` and `return 3`; then exit 3 for any error, 1 for a survivor, a not-applied or a wrong equivalence claim, else 0. The `finally` (1635-1637) removes the scratch subfolder.
- `--checkpoint` mode (1453-1543) returns at line 1543 (`return 4 if any_pass else 0`), before the copy of the ordinary mode and before any mutant loop.
- `--mutant-timeout` (default 900 seconds, `parse_mutant_timeout`, 243-250) is the per-run limit `timeout_sec` passed to every pytest run, the resolution check's included.
- The program's source is ASCII (its docstring says so on purpose: cp1252 consoles). Keep it so.

**The supervisor's rulings (they bind; R1-R9 restate them).**
1. The backslash replacement applies to the file part of a node id only, the text before the first `::`, at both line 80 and line 86, so the text after it is recorded as pytest gives it. The plugin is shared, so this holds in the ordinary and the `--checkpoint` mode.
2. A baseline list whose pytest run exits with any code other than 0 or 1 (5 no tests collected, 2 interrupted or usage error, 3, 4) is an error of that list: exit 5, its line naming the list and the pytest exit, and the failing ids where there are any. A collection error in a baseline list is an error: exit 5.
3. Placement: the baseline runs in the ordinary mode only. It runs after the resolution check and after the cache keys are computed (`mutant_keys`, line 1550), so that the mutants served from the cache are known, and before the mutant loop. Each distinct `tests` list (compared as a list, in the order given) of the mutants that will not be served from the cache runs once. The lists of cached mutants are left out, and when every mutant is served from the cache no baseline runs. It runs under the same per-run limit (`timeout_sec`) and the same environment, plugin and pytest configuration arguments as a mutant's run.
4. Exit 5: on any failure or error of a baseline list the run prints one line per failing list naming the list and its failing ids, runs no mutant, writes no cache line (the cache file stays byte for byte as it was, or absent), and exits 5. An `expect_fail` test that fails unmutated is such a failure.
5. Timeout: a baseline list whose pytest run hits the per-run limit is no failure and no error of the list, so it never ends the run with exit 5. Every mutant not served from the cache whose `tests` list timed out in the baseline is reported `<id>: error (timed out)` without being run, counted under `error` in the `counts:` line, and the run's exit is 3, as today for an errored mutant. A baseline pytest that outlives the kill stops the run exactly as lines 1620-1626 do for a mutant's run today: the stderr line naming the limit, exit 3.
6. The docstring's exit list (lines 7-10) and `build_parser`'s description (lines 1400-1403) name exit 5 and, in one clause, the timed-out rule. The command reference and MANIFEST are regenerated.

**The acceptance tests.** `tests/test_program_mutation_baseline.py` (thirteen cases) fixes the interface; read it whole. Each case builds a scratch Workspace under pytest's `tmp_path` (`<tmp>/proj/Workspace`, a git repository with `mod.py` and tests), writes `run/supervisor/<id>-mutants.json`, and runs `mutation-run.py <file> --scratch <tmp>/scratch` as a subprocess with a 60-second limit. It reads:
- a mutant's result line as a line of stdout starting `<id>:` (so no baseline line may start with a mutant id and a colon);
- the baseline line as **the one line of stdout plus stderr that holds the failing id** (`_baseline_line`). That line must name every file of its `tests` list and no passing id of that list. Nothing else of its wording, nor whether it goes to stdout or stderr, is fixed. So a failing id may appear on exactly one line of the whole output: echo no pytest output.
- the exit code, the cache file's bytes, and, in `test_r090_baseline_runs_each_distinct_tests_list_once`, a log a `conftest.py` writes for each pytest session that runs tests: exactly two unmutated sessions, one per distinct list, both before the first mutated session.

On the checkpoint with the implementation stripped (`run/agent/TASK-070-checkpoint.out`), the file gives `9 failed, 4 passed`. The four that pass today hold what stands: `test_r090_escaped_id_ascii_control_is_killed`, `test_r090_baseline_skipped_when_every_mutant_is_cached`, `test_r090_baseline_leaves_out_the_cached_mutants_lists`, `test_r090_baseline_green_mutants_run_as_before`. After your change all thirteen pass.

**The existing tests that must stay green unedited.**
- The four timeout tests of `tests/test_mutation_run.py`: `test_r041_timeout_error_continues` (line 469), `test_r041_grandchild_holding_pipes_times_out` (line 1245), `test_r041_pytest_survives_kill_stops_run` (line 1352), `test_r041_pipe_holder_outside_tree_cwd_in_copy_times_out` (line 1423). Each one's mutant changes nothing (`pass` -> `pass`, `time.sleep(0.2)` -> `time.sleep(0.2)`) on a test file that hangs unmutated, so its list times out in the baseline, and ruling 5 is what keeps each green. Each expects exit 3 and `<id>: error (timed out)` in stdout. The first also expects the other mutant `ok: killed`. The third patches `kill_tree` to do nothing, so the baseline's pytest outlives the kill. It expects `loop: error (timed out)` in stdout, no `two:` line, `mutation-run:` and `3` in stderr and no `internal error`. The second and fourth bound the elapsed time (`< 5 + 120` seconds) and check the processes the baseline's run started are gone or hold the copy as today.
- `tests/test_mutation_run_supervisor.py::test_task031_req4_a_resolution_check_past_its_bound_exits_3` (line 169): the resolution check's timeout, before any baseline; unchanged.
- The three fixtures that failed or waited unmutated by design were rewritten by the supervisor on this branch before the brief (commit "TASK-070: three fixtures fail only on mutated code"). Each now fails, errors or waits only on mutated code: `tests/test_mutation_run.py::test_r041_pytest_setup_error_is_run_error`, `tests/test_mutation_run.py::test_r041_killed_run_keeps_partial_cache`, and `tests/test_mutation_run_supervisor.py::test_task031_r4_b4_a_kill_is_keyed_by_the_bytes_that_ran`. Do not edit them. The supervisor's run of both files whole on today's code (implementation stripped): `161 passed, 2 skipped`.

**Edits allowed in the two existing test files.** None, except for an existing test that fails after your change for one of these two reasons. (a) Its harness time limit (`run_mr`'s `timeout + harness_slack`, or a `subprocess` `timeout=`) no longer covers the added baseline run: raise only that number, by the least that makes it pass. (b) Its fixture's `tests` list fails, errors or collects nothing on unmutated code by design, beyond the three the supervisor rewrote: rewrite only that fixture, so it fails, errors or waits only on mutated code as the supervisor's three do, and keep every assertion. Name each such edit in the report with the test id, the reason, (a) or (b), and the diff. A test that fails for any other reason is reported by its test id with its failure lines, and not edited.

**External services.** None. No network call. This session has no `claude` on PATH; nothing here needs it.

**Trust boundaries and security context.** ASVS level 2 (`docs/INVENTORY.md`, Decisions, line 138). `.cursor/rules/secure-coding.mdc` is in force for you. Outside input crossing into the program: the mutants file (validated by `load_mutants`), the copied project's tests and their output, and the outcomes JSON the plugin writes. A node id in that JSON may hold any character. Print a recorded id in a line only as the plugin recorded it. Every console write already survives an unencodable character (`reconfigure(errors="backslashreplace")`, line 1664). No exception may escape as a traceback: the existing `run_main` handlers stay the only way out. Any pytest run the baseline starts goes through `run_process`, which starts it windowless (`NO_WINDOW`) with its own process group on POSIX and kills its whole tree at the limit. Start no process any other way.

**Development data.** The inventory's decision (`docs/INVENTORY.md`, Decisions, line 133) reads: "the dev build is the Workspace sources under `bridge/`; a session in the repo always runs the *installed* bridge (`~/.claude`), never the one being edited, and installs reach running projects only through the owner's install run sheet". For you this means: run `mutation-run.py` only through the tests, on their scratch Workspaces under `tmp_path`. Never run it in this repository (it would write `run/supervisor/mutation-cache/` here and copy this Workspace into `~/.cursor-bridge/scratch/`). Never install anything and never copy anything under `~/.claude` or `~/.cursor-bridge`.

**Host.** Windows 11 with the owner's Python; CI also runs on Linux.

## Diagrams
None. The plan entry names no diagram for this increment.

## Requirements
1. **R1. The file part only.** In `OUTCOMES_PLUGIN_CODE`, both the recorded test id (line 80) and the recorded collection-error id (line 86) replace backslashes with `/` only in the text before the first `::`. The text from the first `::` on is kept exactly as `report.nodeid` gives it. An id with no `::` is treated as all file part. As a result, `tests/test_mod.py::test_double[caf\xe9]` is recorded as written, matches its `expect_fail` entry in the ordinary mode, and matches its `new_tests` entry in the `--checkpoint` mode, where it reads `failing` or `passing on old code` and no longer `not run` (the four `test_r090_escaped_id_*` cases).
2. **R2. Which lists run.** In the ordinary mode, after line 1550's keys and before the mutant loop, the program finds the mutants that will not be served from the cache (by the loop's own test: a cached `killed` under the mutant's key, and `--all` not given) and collects their `tests` lists. Two lists are the same when they are equal as lists (same entries, same order). Each distinct list runs once, in the order the mutants first name it. With no such mutant, no baseline runs.
3. **R3. How a list runs.** On the unmutated copy, with the same arguments, environment, plugin, pytest configuration arguments and per-run limit (`timeout_sec`) as a mutant's run (reuse `run_mutant_tests`), each run with a results file of its own under the scratch subfolder. Nothing in the copy is changed by the baseline.
4. **R4. When a list fails.** A baseline list passes only when its pytest run did not time out, exited 0, and its outcomes record is a finished session with no collection error and no test `failed` or `error`; a skipped test is no failure. A list fails when any test `failed` (an `expect_fail` test included: it is not a kill here), any test is `error`, there is a collection error, pytest exited with a code other than 0 or 1, or no finished outcomes record came back without a timeout.
5. **R5. Exit 5.** If any baseline list failed (R4), the run prints one line per failing list and nothing per mutant. The line names every file of the list and each failing id of that list (the recorded ids of its `failed` and `error` tests, and its collection-error ids). For a pytest exit other than 0 or 1 it also names that exit. It names no passing id. A failing id appears on no other line of the output. No baseline line starts with `<mutant id>:`. The run then runs no mutant, writes no cache line (an existing cache file stays byte for byte as it was; a missing one stays missing), and returns 5. The lines go to stdout or stderr (your choice, stated in the report). Every baseline list runs before exit 5 is decided, unless a pytest outlives its kill (R7), so every failing list is named.
6. **R6. When a list times out.** A baseline list whose pytest run hit the limit, and whose pytest did not outlive the kill, is neither passed nor failed. If no list failed (R5), the mutant loop runs as today for every other mutant. Each mutant not served from the cache whose `tests` list timed out is not run and is reported in the result lines as `<id>: error (timed out) (not run)`, a new tag beside `(ran)` and `(cached)`, since the mutant never ran. It is counted under `error` in the `counts:` line and not under `run`, and it makes the run's exit 3 by the existing rule. This holds for an `expect: survive` mutant too. No cache line is written for a mutant that was not run.
7. **R7. When a baseline pytest outlives the kill.** If `run_process` reports the baseline's pytest still alive after its timeout and kill, no further baseline list and no mutant runs. The mutants of that list not served from the cache are reported `<id>: error (timed out)`, no other mutant gets a result line, the `counts:` line is printed, the stderr line of lines 1621-1625 (`mutation-run: pytest did not exit within <n> s after the mutant timeout`) is printed, and the run returns 3. No cache line is written. If a list had already failed (R4) before this stop, its line is printed too, and the exit is still 3.
8. **R8. What stays.** The `--checkpoint` mode has no baseline, and its behaviour is unchanged apart from R1. The mutant loop, its outcomes (`classify_outcome`), the cache key, the cache format, the result and `counts:` line forms, and the exits 0-4 keep their present rules for every mutant that runs. No option, configuration key or environment variable is added.
9. **R9. The exit lists.** The module docstring's exit list and `build_parser`'s `desc` name exit 5 ("5 when a tests list fails or errors on the unmutated code before any mutant runs", or words to that effect). Each also says in one clause that a mutant whose tests list times out on the unmutated code is an error, not run. Regenerate the command reference (Done).

## Acceptance criteria
- [ ] `tests/test_program_mutation_baseline.py` passes whole, unedited (thirteen cases).
- [ ] `tests/test_mutation_run.py` and `tests/test_mutation_run_supervisor.py` pass; the four timeout tests and the supervisor's three rewritten fixtures unedited; any other edit is of the kind Context allows and is named in the report.
- [ ] Every other test file that runs `mutation-run.py` (the Done list's second and third commands) passes unedited.
- [ ] An escaped parametrized id matches its `expect_fail` entry (ordinary mode) and its `new_tests` entry (`--checkpoint` mode) (R1).
- [ ] The baseline runs each distinct `tests` list of the mutants about to run once, on unmutated code, before the first mutant, leaving out the cached mutants' lists, and runs none when every mutant is cached (R2, R3).
- [ ] A failing or erroring list (an `expect_fail` test failing unmutated, a collection error, a pytest exit other than 0 or 1 included) ends the run with exit 5, one line per failing list naming its files and failing ids, no mutant run, the cache untouched (R4, R5).
- [ ] A timed-out list's mutants read `error (timed out)` unrun, counted as error, exit 3; a baseline pytest that outlives the kill stops the run with exit 3 as a mutant's does (R6, R7).
- [ ] The docstring and `--help` text name exit 5 and the timed-out rule; `python tools/dump-cli.py --check` exits 0; MANIFEST regenerated; `bridge/cursor-bridge/VERSION` reads `2026.11.12a` and is not listed by `git status --short`; `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` prints `RESULT: SOURCES MATCH` (R9).
- [ ] `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks` passes.
- [ ] `mutation-run.py` stays ASCII; every line you add anywhere is ASCII.
- [ ] R-090 (the parts this brief serves) is fully met: no stand-in, placeholder or "later" text. The tests naming R-090 are the supervisor's acceptance tests.
- [ ] No new dependency, option, configuration key or environment variable. No new Semgrep high finding. No exception escapes as a traceback (ASVS L2).

## Constraints
- Do not add dependencies (the standard library and the pytest already used only).
- Do not read or write any file outside this workspace (the folder you were started in). Everything you need is inside it; everything you produce goes inside it.
- Do not edit `tests/test_program_mutation_baseline.py`, the four timeout tests, the supervisor's three rewritten fixtures, or anything else outside Scope. If a test case seems wrong, stop and report it by its test id instead of working around it.
- If the brief, the rules, or the tooling got in your way (an instruction that contradicted another, a check that fired wrongly, a step that cost time for no reason), append one dated line describing it to `docs/BUILDER_NOTES.md`. Do not try to fix the tooling. Do the same for anything you learned about a defect or a pitfall (a cause you found, a platform quirk that cost you a round): one dated line, so the supervisor can carry it forward.
- In any Markdown you write, never break a line inside a paragraph or a list item; one paragraph is one line. Line breaks only between blocks.
- **No owner's names, no paths.** Nothing you write (code, the notes line, the report) holds a path of this computer or a user name. In the report write `<Workspace>` for the repository folder and `<tmp>` for a temporary folder, including in quoted command output.
- This increment talks to no external service. Do not add a call to any service or the network.
- Any console process your code launches on Windows is created windowless (`creationflags=subprocess.CREATE_NO_WINDOW` in Python, `0` on other platforms). The program does so through `run_process` (`NO_WINDOW`). Capturing output does not prevent the window. Every pytest run you add goes through `run_process`, so it is windowless, bounded by the limit, and has its whole tree killed at the limit with its pipes drained. Start no process any other way.
- Never start a server, a watcher or a daemon that outlives a test. Run every command synchronously, in the foreground, and wait for it to end. Leave nothing running when you finish.
- Do not refactor code outside the scope, even if it looks wrong.
- Never run the product, a migration, a seed or a test against the owner's live data (Context, "Development data"): never run `mutation-run.py` in this repository; only the tests run it, on their scratch Workspaces.
- A value the brief marks as the owner's: none in this increment.
- Follow existing conventions in the file you touch: ASCII program text, the module docstring holding the usage and exits, `Refuse` for exit 2, `main()` returning the exit code, results printed as `<id>: <outcome> (<tag>)`.
- These git commands are not yours to run: `commit`, `push`, `switch`, `checkout`, `merge`, `rebase`, `reset`, `stash`, `branch -d`, `worktree`. You read with `git status`, `git diff` and `git log` only. The single exception is `git restore bridge/cursor-bridge/VERSION` in the Done section.
- Numbers: the per-run limit stays `timeout_sec` as `parse_mutant_timeout` parses it (a whole number of seconds from 1 up, `int`). A pytest exit code is the integer `run_process` returns. Parse nothing from pytest's printed text: read outcomes from the plugin's JSON only.
- Every verification command the Done section asks you to run is written there in full; run exactly those. **Do NOT run the whole `tests/` tree** (`python -m pytest`, `python -m pytest tests`, or any command that collects all of it): the whole suite is CI's run. The timeout tests take minutes; run each command in the foreground and wait.
- **Mutation self-check (by hand, in process, no script in the diff).** The supervisor's mutants file sweeps your change after your run. Before you finish, apply each of these by hand to `bridge/cursor-bridge/mutation-run.py`, one at a time, run the command given, and revert, confirming with `git diff` that the revert is exact. List each in the report by its label and text, with the pytest summary line and the id of a test it made fail, or `not caught` with one line on the case that would catch it (do not add that case; you add no test):
  - H1 the whole-id replacement restored at line 80 (`report.nodeid.replace(chr(92), "/")`). Command: `python -m pytest -p no:cacheprovider -q tests/test_program_mutation_baseline.py`.
  - H2 the baseline's exit 5 turned into a warning that lets the mutants run (the lines printed, then the loop runs). Command: as H1.
  - H3 the cached mutants' lists not left out of the baseline. Command: as H1.
  - H4 an `expect_fail` test failing unmutated read as a kill again (the baseline ignores a failure of an id in the list's mutants' `expect_fail`). Command: as H1.
  - H5 a timed-out baseline list ending the run with exit 5. Command: `python -m pytest -p no:cacheprovider -q tests/test_mutation_run.py -k "timeout_error_continues or grandchild_holding_pipes or pytest_survives_kill or pipe_holder_outside_tree"`.
- **Known failures.** Context lists the acceptance cases that fail before your change. If a case fails that your change did not cause, report it by its test id with its failure lines and fix none.
- Prefer reuse over new code: `run_mutant_tests`, `run_process_still_alive_after_timeout`, `read_pytest_results`, `outcome_map_from_results`, the loop's own cache test, and the standard library; write the minimum that meets the acceptance criteria (the frozen `minimal-code.mdc` is in force). This never overrides a security, observability or accessibility requirement stated above.
- Rules in force for you: `.cursor/rules/secure-coding.mdc`, `.cursor/rules/workspace-boundary.mdc` and the frozen `minimal-code.mdc`.

## Done
Your report is the file `handoff/TASK-070-r1-report.md`, which you write as you go: what you did, what you changed, what you ran and what it printed, and what you could not do, so that nothing of it is lost if your run ends early. It names no computer path and no user name: write `<Workspace>` for the repository folder and `<tmp>` for a temporary folder, including in quoted command output.

When you finish, it holds:
- a list of every file you changed;
- a one-paragraph summary of what you did;
- for R1-R9, one line each on what meets it, naming the functions and their lines as the file stands after your change; for R5, whether the baseline lines go to stdout or stderr and one example line; for R6, one example of a timed-out list's mutant line;
- every edit to `tests/test_mutation_run.py` or `tests/test_mutation_run_supervisor.py`, if any: the test id, the reason ((a) or (b) of Context), and the diff; otherwise `no existing test edited`;
- the mutation self-check list, H1-H5, each with its pytest summary line and the test id that caught it (or `not caught` and the case that would);
- every command of the list below with its output;
- a section headed exactly `Assumed, not verified`, as the report's last section.

The `Assumed, not verified` section lists every fact this change relies on that neither this brief nor the existing code settled, and that you did not confirm. Examples: how pytest forms a parametrized id on Linux as against Windows; what pytest's exit code is for a list whose every test is skipped; whether `taskkill /T` reaches a baseline pytest's grandchildren. One item per line: what you assumed · why · what would confirm it. If there are none, write `Assumed, not verified: none`. Be specific: "edge cases" or "error handling" is not an item.

Run these from the Workspace root, in this order, after your last edit, each on its own, synchronously in the foreground, with no `PYTHONPATH` or other environment change:
1. `git status --short`
2. `python tools/dump-cli.py`
3. `python tools/dump-cli.py --check` (expect exit 0)
4. `python tools/make-manifest.py`
5. `git restore bridge/cursor-bridge/VERSION`
6. `python -m pytest -p no:cacheprovider -q -rs tests/test_program_mutation_baseline.py tests/test_mutation_run.py tests/test_mutation_run_supervisor.py`
7. `python -m pytest -p no:cacheprovider -q -rs tests/test_allowlist.py tests/test_bridge_run_driver.py tests/test_bug030.py tests/test_bug032.py tests/test_dump_cli.py tests/test_loop_text_pace.py tests/test_loop_text_windowless.py`
8. `python -m pytest -p no:cacheprovider -q -rs tests/test_program_trace_moves.py tests/test_release_b2_stamp.py tests/test_release_t_floor.py tests/test_release_t_merge.py tests/test_release_t_stage_close.py tests/test_release_t_stamp.py`
9. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` (expect `RESULT: SOURCES MATCH`)
10. `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks`
11. `python -c "open('bridge/cursor-bridge/mutation-run.py','rb').read().decode('ascii'); print('ascii ok')"` (expect `ascii ok`)
12. `git rev-parse HEAD` and `git status --short` (`bridge/cursor-bridge/VERSION` must not be listed; if it is, report it)

Commands 7 and 8 cover every other test file that runs `mutation-run.py`. All of them are outside Scope, and a failure in any of them is reported by test id, never fixed in that file.

Quoting rules:
- Every command you ran is quoted in the report with the lines it printed, verbatim, in a fenced block.
- Each pytest summary line is quoted verbatim in a fenced block. Never restate a count in prose.
- A claim that a check passed quotes the output line that shows it. A number of failing or skipped cases is backed by the pytest lines naming them (`-rs` prints each skip's reason).
- Each mutation is listed by its label and text, with what caught it.
- A command you did not run is written `not run`, never described as run.
- Write the report's results after step 12, naming the commit its counts belong to (`git rev-parse HEAD`) and whether the working tree then held uncommitted changes (`git status --short`).

Your last message is the summary and the report file's path, and nothing follows it. The supervisor reads only the last message, and a message printed earlier and then followed by more work is lost.
