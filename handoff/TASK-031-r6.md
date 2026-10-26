# TASK-031 round 6: the blocking findings of the gate's reviews on rounds 4 and 5

## Objective

Round 5's head, f3f304b, went through the gate for rounds 4 and 5 together. Review A rejected it, and the security audit failed it. This round is past the owner's three-round review ceiling, so it carries only findings of the five blocking classes: behaviour against the brief or the register, security, data integrity, a defeated safety mechanism, and a failing test. Each item below names its class. Every other finding of the two reviews is recorded in `docs/HARDENING.md` and is not yours to fix.

The supervisor wrote red tests in `tests/test_mutation_run_supervisor.py`, under the heading comment "Round 6". They fail on round 5's code, each for the reason its item names. This round makes them pass, and adds the builder's tests that items 6 and 7 ask for. `handoff/TASK-031.md`, `-r2.md`, `-r3.md`, `-r4.md` and `-r5.md` still govern everything this file does not change.

Satisfies:
- R-041 (quoted whole in `handoff/TASK-031.md`). The clauses at stake here: "gives every mutant a result against the version the gate reads" (item 3); "a kill is a named expected test failing in the report ...; the run crashing, failing to collect, or an unexpected test failing is an error, never a kill" (items 5 and 6); and TASK-031 Requirement 2, the scratch copy that holds no `.git` and never lies inside the Workspace (items 1 and 2).

## Scope

One brief carries one increment's scope; work that needs a second scope is a second brief, never a second section here.

Files you may create or modify:
- bridge/cursor-bridge/mutation-run.py
- tests/test_mutation_run.py
- docs/cli-reference.json and docs/CLI_REFERENCE.md (only through `python tools/dump-cli.py`, and only if the parser's text changes)
- docs/BUILDER_NOTES.md
- handoff/TASK-031-r6-report.md

Do not modify anything else.

## Out of scope

- `.env` and anything under `secrets/`
- CI configuration (`.github/`, `.githooks/`)
- `docs/` and `handoff/`, except the files the Scope section names. This covers `docs/HARDENING.md` and `docs/INVENTORY.md`.
- `tests/test_mutation_run_supervisor.py`: read and run it, never edit it. A test you believe wrong is reported with the reason, never changed or skipped. This covers every Round 6 test.
- `tests/conftest.py`, `tests/test_dump_cli.py` and every other existing test file
- `bridge/cursor-bridge/MANIFEST.json` and every other file under `bridge/`. Never run `tools/make-manifest.py`.
- `run/supervisor/`
- Every finding not listed below, including the advisories and the should-fix and consider items the reviewers raised and did not mark blocking: they are recorded, not yours.
- A Job object inside `mutation-run.py`. It is not asked for.

## Context

**Development data.** The inventory's decision, copied verbatim: "Development data: the dev build is the Workspace sources under `bridge/`; a session in the repo always runs the *installed* bridge (`~/.claude`), never the one being edited, and installs reach running projects only through the owner's install run sheet". The tests run the Workspace's `bridge/cursor-bridge/mutation-run.py` by file path, on fixtures under `tmp_path`. `tests/conftest.py`'s autouse fixture `home_of_the_tests` sets `HOME` and `USERPROFILE` to a fresh temporary folder, so the scratch copy falls under that temporary home. Never run `mutation-run.py` with this Workspace or a real project as its working folder. Never touch the real `~/.cursor-bridge/` or `~/.claude/`.

**Security context.** ASVS level 2 (`docs/INVENTORY.md`, Decisions). `.cursor/rules/secure-coding.mdc` and `.cursor/rules/workspace-boundary.mdc` are in force, and so is the frozen minimal-code rule (`bridge/cursor-bridge/minimal-code.snapshot.md`). The trust boundaries this round touches:
- The `--scratch` argument and the scratch folder in the owner's home. The program writes and removes only its own `mutation-run-<id>/` subfolder, and never inside the Workspace (items 1 and 6).
- The mutants file's `untracked` entries. Any program of the owner's account can write under `run/supervisor/`, so an entry may be crafted to reach the Workspace's `.git` (item 2).
- The folders above the copy. A pytest configuration there is outside the project and must not configure a mutant's run (item 3).
- The root `.env`, which holds local service passwords (KP-032). It is copied into the copy and nowhere else, never printed, logged or keyed. Your tests build their own `.env` with a made-up value.

**The code as it is (checked on this branch).** The line numbers are approximate; read the code.
- `path_bad(rel)` (about :129-141) refuses an absolute path, `..`, an empty or `.` component, and a first component equal to `.git` compared case-insensitively. It is used for every path field.
- `path_under_or_equal` (about :359-367) and `paths_overlap_workspace(a, b)` (about :370-382) compare `os.path.normcase(os.path.realpath(os.path.abspath(...)))` strings with `os.path.commonpath`, returning False on `ValueError`. `validate_scratch(scratch, workspace, run_id)` (about :405-415) calls `paths_overlap_workspace` at about :408.
- `validate_untracked(untracked, workspace)` (about :385-396) checks inside-the-Workspace with `path_under_or_equal` and links with `link_on_path` and `refuse_links_under`. `copy_tracked` (about :459-479) then copies each untracked entry with `shutil.copytree` or `shutil.copy2`.
- `copy_has_pytest_config(copy_root)` and `pytest_config_argv(plugin_dir, copy_root)` (about :733-747): a root `pytest.ini`, `pyproject.toml`, `tox.ini` or `setup.cfg` of any content returns `[]`; otherwise `["-c", <mutation-run-<id>/pytest-empty.ini>, "--rootdir", copy_root]`. The resolution check (about :971), `run_mutant_tests` (about :1012) and the `--checkpoint` loop (about :1131) all use it.
- `key_file_set` (about :574-597) adds the root's `conftest.py`, `pytest.ini`, `pyproject.toml`, `setup.cfg` and `tox.ini` at about :594.
- The outcomes plugin `OUTCOMES_PLUGIN_CODE` (about :38-81) records `tests`, `collect_errors`, `session_finished` and `exitstatus`, and writes them to the path in `MUTATION_PYTEST_RESULTS`. `classify_outcome(data, expect_fail, timed_out)` (about :781-800) never reads `collect_errors`.
- In `main`, `results_path = os.path.join(plugin_dir, "pytest-outcomes.json")` (about :1105) is one path for every mutant's run and every checkpoint item's run.
- The `--checkpoint` loop (about :1127-1165): an item with `::` is looked up with `outcome_by_id.get(item)` (about :1143-1151), so only a record of exactly that node id matches. A file item lists every record.
- `run_process(argv, env, cwd, timeout_sec)` (about :434-456): after the bound, `kill_tree(proc)` (about :418-431, which ignores `taskkill`'s result), then `proc.communicate(timeout=30)`; on a second `TimeoutExpired` it returns empty output after `proc.wait(timeout=30)`, whose own `TimeoutExpired` is passed over (about :451-454). It returns `(None, out, err, True)` on a timeout.
- `run_main` (about :1246-1260) maps `Refuse` to 2, `ResolutionTimeout` to 3, and any other exception to `mutation-run: internal error - ...` with exit 3.
- `tests/test_mutation_run.py`: `run_mr(ws, mutants_file, scratch=None, timeout=60, extra=(), home_env=None)` (about :67-77) caps the run at `timeout + 30` s. `conftest.load_program("mutation-run")` loads the Workspace's program by path as a module.

**What the supervisor's Round 6 tests printed on round 5's code.**
- B-1 (`test_task031_r6_b1_...`): the extended form ended in `mutation-run: internal error - ... [WinError 123] ...`; the administrative-share form ran, inside the Workspace.
- B-2 (`test_task031_r6_b2_...`): `.git.` and `.git::$INDEX_ALLOCATION` ran; `.git ` ended in an internal error.
- B-3: every no-section case exited 2 with `mutation-run: resolution check failed (pytest exit 5)`; `.pytest.ini` and `pytest.toml` the same. The `pyproject.toml` case of `test_task031_r6_b3_the_copys_own_pytest_configuration_is_read` passes today, a control.
- A-1: `not run`, exit 0.
- A-3: `m: killed (ran)`, exit 0.

**The working tree at delegation.** The supervisor's checkpoint commit before this round holds the Round 6 tests and its own edits to `docs/HARDENING.md` and `docs/INVENTORY.md`. If `git status --porcelain` shows any of those three files changed before you have changed anything, stop and report it: the `git diff --quiet` criterion below cannot hold then.

**Pytest.** Pytest 9.1.1 is installed (`requirements.lock`). CI runs Python 3.12 on Windows and Ubuntu (`.github/workflows/tests.yml`).

## Requirements

1. **B-1: a scratch folder inside the Workspace in another path form** (security; behaviour against TASK-031 Requirement 2: a scratch folder inside the Workspace is refused). `paths_overlap_workspace` compares realpath strings. On Windows the extended form (a `--scratch` beginning with the four characters `\\?\`) and the drive's administrative share (`\\localhost\C$\...`) are not mapped to the drive path, so `commonpath` differs or raises `ValueError`, and the overlap test returns False. Refuse with exit 2, creating nothing inside the Workspace, a scratch folder that is, contains or lies inside the Workspace, whatever its spelling. Compare by file identity (`os.path.samefile`, or `st_dev` and `st_ino`) over the existing ancestors, both ways: an existing ancestor of the scratch that is the Workspace, and an existing ancestor of the Workspace that is the scratch. Refuse outright a `--scratch` that begins with the extended prefix `\\?\`, the device prefix `\\.\`, or a UNC prefix (`\\server\share`). The refusal happens before any folder is created. Supervisor test: `test_task031_r6_b1_a_scratch_folder_inside_the_workspace_in_another_path_form_is_refused` (two cases; the administrative-share case skips where the share is not reachable).

2. **B-2: an `untracked` entry reaching `.git` by another name** (security; behaviour against TASK-031 Requirement 2: no `.git` is copied). `path_bad` and `validate_untracked` accept `.git.` and `.git ` (Windows drops trailing dots and spaces from a name), `.git::$INDEX_ALLOCATION` (a stream name), and the 8.3 short name `GIT~1`. `copy_tracked` then copies the Workspace's `.git` into the copy. Refuse with exit 2, caching nothing, an untracked entry that is or lies inside the Workspace's `.git`, by file identity over the entry and its existing ancestors under the Workspace. Also refuse an untracked entry any of whose components ends in a dot or a space or holds a colon. The Workspace's `.git` may be a folder or, in a linked worktree, a file; an entry that is it is refused either way. Neither check may end in an internal error. Supervisor test: `test_task031_r6_b2_an_untracked_entry_reaching_git_by_another_name_is_refused` (four cases; the short-name case skips where the volume makes no 8.3 names).

3. **B-3: the copy's pytest configuration decided by file name** (behaviour against the register, R-041's "a result against the version the gate reads", and against `handoff/TASK-031-r4.md` item 11, B8; the security audit's B-3 and Review A's blocking 2, convergent). Two failures:
   - (a) A root `pyproject.toml`, `setup.cfg` or `tox.ini` with no pytest section suppresses `-c`, so pytest climbs to a configuration above the copy (a `pytest.ini` in the home).
   - (b) `.pytest.ini` and `pytest.toml`, which pytest 9.1.1 reads, get the empty `-c`, so the project's own configuration is shut out (a regression of round 3).

   Find the copy's configuration file as pytest 9 does, at the copy's root. The names and their order, as the supervisor gives them: `pytest.toml`, `.pytest.toml`, `pytest.ini`, `.pytest.ini`, `pyproject.toml` with a `[tool.pytest.ini_options]` or `[tool.pytest]` table, `tox.ini` with a `[pytest]` section, `setup.cfg` with a `[tool:pytest]` section. Check this order, and the condition under which each name counts, in pytest 9.1.1's own installed source (`_pytest/config/findpaths.py`), follow the source where it differs, and state in your report what you read there. Every pytest run (the resolution check, each mutant's run, each checkpoint item's run) passes `-c` naming that file, or the empty file inside `mutation-run-<id>/` when there is none, and always `--rootdir <copy root>`. Node ids stay named from the copy's root. The cache key's file set (`key_file_set`, about :594) holds the same root names. Supervisor tests: `test_task031_r6_b3_a_root_file_with_no_pytest_section_keeps_the_configuration_above_unread` (three cases) and `test_task031_r6_b3_the_copys_own_pytest_configuration_is_read` (three cases, the `pyproject.toml` one a control that passes today).

4. **A-1: a parametrized or class id at the checkpoint** (a defeated safety mechanism, the checkpoint mode exists to catch a new test that cannot fail; behaviour against `handoff/TASK-031-r4.md` item 3, B3: "a listed file, or a parametrized id"; Review A's blocking 1). In the `--checkpoint` loop, an id item matches only a record of exactly that node id, so a parametrized function id or a class id prints `not run` and exits 0 though its tests ran (a regression of round 3). For an id item, print every record whose node id equals the item or begins with the item followed by `[` or by `::`, each by its own node id with its label. Print `<item>: not run` only when there is no such record. Exit 4 when any of them passed. Supervisor test: `test_task031_r6_a1_a_parametrized_or_class_id_is_judged_by_its_tests_at_the_checkpoint` (two cases).

5. **A-3: a collection error beside a kill** (behaviour against the brief, `handoff/TASK-031.md` Requirement 6: `error` when the tests did not collect; data integrity, since a false kill is cached and skipped on every later run; Review A's blocking 3). `classify_outcome` never reads the plugin's `collect_errors`. Under `--continue-on-collection-errors`, a mutant that breaks another listed file's import while its expected test fails reads `killed`. Any collection error in a mutant's run makes the mutant `error` with the reason `collection error`, so the run exits 3 and no `killed` line is cached for it. A timed-out run keeps the reason `timed out`, and a run with no results keeps `no pytest result`. The checkpoint mode's labels are unchanged. Supervisor test: `test_task031_r6_a3_a_collection_error_beside_a_kill_is_an_error`.

6. **A pytest run that outlives its kill** (data integrity; Review A's should-fix and the security audit's A-3, convergent, so blocking). Since round 5, `run_process` returns after the bounded `proc.wait` while pytest may still be alive, since `kill_tree` ignores `taskkill`'s result. The next mutant then runs on the same copy with the same results file (about :1105), so the live run's outcomes can be read as the next mutant's. Two things must hold:
   - Each pytest run (each mutant's run and each checkpoint item's run) writes its outcomes to a results file of its own, at a path unique to that run inside `mutation-run-<id>/`, and only that run's file is read for it.
   - When a mutant's pytest process is still alive after the kill and the bounded wait, the whole run ends with exit 3. Stderr gets one line beginning `mutation-run: ` that names the bound in seconds. Stdout gets the normal summary and counts for the mutants that ran, the timed-out one listed `error (timed out)`. No further mutant runs on that copy. The run never ends in `mutation-run: internal error - ...` for this case.

   Write the test for this in `tests/test_mutation_run.py`. One way: load the program with `load_program("mutation-run")`, replace `kill_tree` with a no-op so the pytest process survives the bound, and run `main` on a fixture with two mutants, the first looping forever. Assert exit 3, the stderr line, the first mutant `error (timed out)`, and that the second mutant did not run. The test ends every process it started, the surviving pytest's whole tree included, in its own `finally`, and its docstring names `R-041`, `TASK-031 S7` and this item. State in your report how you show that each run's results file is its own.

7. **The pipe-holder tests that never held the pipes** (gate integrity: a test weaker than its name, on the merge policy's anti-gaming list; Review A's should-fix). Your tests `test_r041_pipe_holder_outside_tree_cwd_in_copy_times_out` and `test_r041_grandchild_holding_pipes_times_out` in `tests/test_mutation_run.py` never hold `run_process`'s pipes. Under pytest's default capture, `sys.stdout` and `sys.stdout.fileno()` inside the fixture's test are pytest's capture file, and `run_mr` caps the run at its timeout plus 30 s. Make each fixture's holder hold the real pipes `run_process` reads (for example `addopts = -s` in the fixture's `pytest.ini`, or `capfd.disabled()` in the fixture's test). Give each run a harness timeout of at least the bound plus 90 s. Then:
   - In `test_r041_pipe_holder_outside_tree_cwd_in_copy_times_out`, whose holder lies outside the killed tree: assert that the hold happened (the run's elapsed time at least 30 s), and assert that the copied `.env` is absent from what remains of `mutation-run-<id>/` while the holder is still alive, as round 5's report claimed. If it is present, that is a finding of item 6's class: report it, and do not weaken the assertion.
   - In `test_r041_grandchild_holding_pipes_times_out`, assert that the hold happened in the same way. Its holder is a child of pytest, inside the killed tree, so the kill may end it and release the pipes before 30 s. If you find that so, do not fake a hold and do not drop the assertion silently: make the test show what its name says (a holder that really held the real pipes until the kill, then gone), and state in your report what you found and what the test now asserts.

   Each holder is ended by the test's own `finally` or teardown, never left behind.

## Acceptance criteria

- [ ] Every test of `tests/test_mutation_run_supervisor.py` and `tests/test_mutation_run.py` passes. The b1 administrative-share case and the b2 short-name case may skip where the machine lacks the share or 8.3 names, and only those. `git diff --quiet -- tests/test_mutation_run_supervisor.py` exits 0.
- [ ] Every item is fixed at the cause named, never by special-casing a test's fixture.
- [ ] Items 6 and 7 have the tests they ask for, each docstring naming `R-041` and its item. Each test that starts the program finishes within 60 s, except the tests of items 6 and 7, which finish within their bound plus 120 s; every `subprocess.run` or `communicate` in a test carries a timeout no larger than its test's ceiling.
- [ ] `python tools/dump-cli.py --check` exits 0. `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge/mutation-run.py` prints `0 FAIL`. The program is ASCII only.
- [ ] `python -m pytest tests/test_dump_cli.py tests/test_tests_windowless.py tests/test_bridge_run_driver.py -q -p no:cacheprovider` passes.
- [ ] `git status --porcelain` shows no changed or new file outside Scope.
- [ ] `handoff/TASK-031-r6-report.md` exists, with its `Assumed, not verified` section.

## Constraints

Every constraint of the five earlier briefs holds: `handoff/TASK-031.md`, `-r2.md`, `-r3.md`, `-r4.md` and `-r5.md`. There is no by-hand mutation in this round: the supervisor's driver runs after you. Write no mutation script.

This round adds the following:
- Do not fix by suppressing the symptom. That rules out a retry, a broad `try/except`, a widened tolerance, an added `sleep`, a longer or removed `--mutant-timeout` bound, and a check that hides a wrong value. The longer harness timeout of item 7 is the test's own cap on the program, not the program's bound, and is asked for. A `try/except` that turns an error into a refusal is limited to the named case, and the report says so.
- Do not edit any test in `tests/test_mutation_run_supervisor.py`.
- Do not leave any `DEBUG-BUG-` line, `faulthandler` probe or stray print in the program or the tests.
- If you believe the real cause of an item is different from the one named, stop work on that item, do not change code for it, and report why in your summary. The supervisor will re-diagnose.
- Every process your code or your test starts is windowless (`creationflags=subprocess.CREATE_NO_WINDOW`, `0` elsewhere). In `tests/test_mutation_run.py`, including the source text of a fixture, write `CREATE_NO_WINDOW` on the same line as every `creationflags`, as the scan of `tests/test_tests_windowless.py` requires (`handoff/TASK-031.md`, Context). Nothing it starts outlives the test, and its pipes are closed or drained.
- Do not read or write any file outside this workspace, except pytest's `tmp_path` and the tests' temporary home. Reading pytest's installed source for item 3 is allowed.
- If the brief, the rules or the tooling got in your way, append one dated line to `docs/BUILDER_NOTES.md`. Do the same for anything you learned about a defect or a pitfall. In any Markdown you write, one paragraph is one line.
- Only `git status`, `git diff`, `git show` and `git log` are yours to run in this Workspace.
- Prefer reuse over new code: the standard library (`os.path.samefile`, `os.stat`, `configparser`, `tomllib`) and what the program already has. Write the minimum that meets the acceptance criteria. This never overrides a security requirement stated above.

## Verification commands

Run each from the Workspace folder, in this order:
1. `python -m pytest tests/test_mutation_run_supervisor.py tests/test_mutation_run.py -q -p no:cacheprovider -rA --durations=0`
2. `python tools/dump-cli.py --check`
3. `python -m pytest tests/test_dump_cli.py tests/test_tests_windowless.py tests/test_bridge_run_driver.py -q -p no:cacheprovider`
4. `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge/mutation-run.py`
5. `python -c "d=open('bridge/cursor-bridge/mutation-run.py','rb').read(); print(all(b < 128 for b in d))"`
6. `git status --porcelain`
7. `git diff --quiet -- tests/test_mutation_run_supervisor.py`, then report its exit code

## Done

Your report is the file `handoff/TASK-031-r6-report.md`. Write it as you go. Never paste a computer path or a user name into it. State only what you ran, quoting pytest's own output, at least its summary line, for every run. Do not repeat a figure from an earlier round's report.

The report holds:
- the files you changed;
- one paragraph on what you did;
- for each item, the cause you fixed and where, one sentence on how the change addresses it, and the test or tests that hold it;
- item 3: pytest 9.1.1's configuration names, their order and the condition for each, as you read them in its installed source;
- item 6: how you show that each run's results file is its own;
- item 7: what remains of `mutation-run-<id>/` while the holder lives, whether the copied `.env` is among it, and what you found for the grandchild inside the killed tree;
- the quoted output of each verification command, including the `-rA` lines of the Round 6 tests, any skip with its reason, and the durations of the item 6 and 7 tests;
- a section headed exactly `Assumed, not verified`, one item per line (what you assumed; why; what would confirm it). Name at least:
  - pytest's configuration order and conditions as read from its source, and that `-c` with a `pytest.toml` or `pyproject.toml` file is read as the search would read it;
  - the POSIX behaviour of item 1 (no extended or share forms; file identity across bind mounts and links), if you could not run it there;
  - the POSIX behaviour of item 2 (`.git.` and `.git ` are other names there; what your refusal does to them), if you could not run it there;
  - the POSIX behaviour of item 6 (a process group that survives `os.killpg`), if you could not run it there.

Your last message is the summary and the report file's path, and nothing follows it.
