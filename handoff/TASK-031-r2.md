# TASK-031 round 2: fix mutation-run.py's defects and finish its tests

## Objective

Round 1 built `bridge/cursor-bridge/mutation-run.py` and `tests/test_mutation_run.py` from `handoff/TASK-031.md`. That brief still governs everything this file does not change. The supervisor's inspection found code defects, cases of the brief's Requirement 11 with no test, and tests that do not prove what their docstrings claim. The supervisor wrote seven tests of its own, committed in `tests/test_mutation_run_supervisor.py`. Five fail on round 1's code, one passes and one skips where no link can be made. This round fixes the code, so that every supervisor test passes, and completes and corrects `tests/test_mutation_run.py`.

Satisfies:
- R-041 (quoted whole in `handoff/TASK-031.md`).

## Scope

One brief carries one increment's scope; work that needs a second scope is a second brief, never a second section here.

Files you may create or modify:
- bridge/cursor-bridge/mutation-run.py
- tests/test_mutation_run.py
- docs/cli-reference.json and docs/CLI_REFERENCE.md (written only by `python tools/dump-cli.py`, and only if the parser's text changes)
- docs/BUILDER_NOTES.md
- handoff/TASK-031-r2-report.md

Do not modify anything else.

## Out of scope

- `tests/test_mutation_run_supervisor.py`. It is the supervisor's: read it, run it, never edit it. A test there that you believe is wrong is reported in your report with the reason, never changed or skipped.
- `tests/test_dump_cli.py` (round 1's one line stands), `tests/conftest.py`, and every other existing test file
- `bridge/cursor-bridge/MANIFEST.json` (the supervisor regenerates it; never run `tools/make-manifest.py`) and every other file under `bridge/`
- Everything `handoff/TASK-031.md` lists as out of scope

## Context

`handoff/TASK-031.md` governs: its Context, Requirements 1 to 11, Constraints and Done hold unchanged except where this brief changes them. Read it whole first.

The supervisor ran `python -m pytest tests/test_mutation_run_supervisor.py -q -p no:cacheprovider -rA` on round 1's code (Windows; the link test made a junction, since this account cannot make a symbolic link):

```
PASSED tests/test_mutation_run_supervisor.py::test_task031_req7_a_change_reruns_only_the_mutants_it_keys
PASSED tests/test_mutation_run_supervisor.py::test_task031_req5_a_test_loading_the_workspace_is_refused
FAILED tests/test_mutation_run_supervisor.py::test_task031_req9_an_expected_survivor_that_survives_exits_0
FAILED tests/test_mutation_run_supervisor.py::test_task031_req7_a_root_level_file_keys_its_whole_folder
FAILED tests/test_mutation_run_supervisor.py::test_task031_req1_a_link_inside_an_untracked_folder_is_refused
FAILED tests/test_mutation_run_supervisor.py::test_task031_req4_a_resolution_check_past_its_bound_exits_3
FAILED tests/test_mutation_run_supervisor.py::test_task031_req8_the_checkpoint_check_collects_the_listed_new_tests
```

Round 1's report ran one of the ten by-hand mutants and left several cases of Requirement 11 to the supervisor. That is not how this brief divides the work. Every case Requirement 11 lists is yours to test. The by-hand mutation check is dropped in this round, because the supervisor's own driver runs on the program after your run.

## Requirements

### A. Code defects (each with its cause in round 1's code)

1. **An expected survivor is counted as survived** (Requirements 6 and 9). At `main`'s `if m["survive"]:` branch, a survived `expect: survive` mutant adds to `counts["survived"]`, and its killed form adds to `counts["killed"]`, so a survivor that was correctly declared gives exit 1. An `expect: survive` mutant counts only under `expected survive`, never as killed or survived. Exit 1 comes from it only when it was killed (run or cached). The summary line still shows its outcome (`expected survive (<reason>)`, or the wrong-equivalence line). Supervisor test: `test_task031_req9_an_expected_survivor_that_survives_exits_0`.

2. **A root-level file's key leaves its folder out** (Requirement 7). `key_file_set` adds only the file itself when `os.path.dirname(mutant["file"])` is empty, and only the test file itself when a test file's folder is empty. The folder of a root-level file is the root, so the key covers every tracked file. Treat an empty folder as the root, for both the mutated file and the test files. Supervisor test: `test_task031_req7_a_root_level_file_keys_its_whole_folder`.

3. **A link inside a listed untracked folder is followed** (Requirements 1 and 2). `validate_untracked` checks only the listed path and its parents, and `copy_tracked` then calls `shutil.copytree(src, dst, symlinks=False)`, which reads through every link inside the folder. That includes a junction, which `copytree` treats as a folder. Walk every listed folder before any copy, without following links (`os.walk(..., followlinks=False)`, testing each entry, folders included, with `bridge_env.is_link`). Refuse with exit 2, naming the path, when anything inside is a link. The same rule applies to the copy of tracked paths and of the root `.env`: a tracked path that is a link, or lies under a linked folder of the Workspace, and a root `.env` that is a link, are refused with exit 2 before any copy. Test only the components from the Workspace down, never the Workspace's own parents, so that a project kept under a linked folder still runs. `link_on_path` today walks up to the drive root, and that applies to `validate_untracked` too. Supervisor test: `test_task031_req1_a_link_inside_an_untracked_folder_is_refused`. Its symbolic-link form runs on Linux in CI, and its junction form on Windows.

4. **A timed-out resolution check exits 2** (Requirement 4, round 1's S7 addition: "a timed-out resolution check exits 3, naming the bound"). `run_resolution_check` raises `Refuse` on a timeout. Exit 3 instead, with one stderr line beginning `mutation-run: ` that names the bound in seconds. Caching nothing and removing `mutation-run-<id>/` stay as they are. Supervisor test: `test_task031_req4_a_resolution_check_past_its_bound_exits_3`.

5. **The checkpoint's resolution check collects the wrong tests** (Requirements 5 and 8). In `--checkpoint` mode, `main` passes the mutants (or, with none, a stand-in naming `pyproject.toml` and the folder `tests`) to `run_resolution_check`. So the listed new tests are not what is collected, and a new test outside `tests/` is never checked. In `--checkpoint` mode, collect exactly the file parts of `new_tests`. Run check (i) for every mutant in the file, if there are any. Supervisor test: `test_task031_req8_the_checkpoint_check_collects_the_listed_new_tests`.

6. **Check (i) skips what it should check** (Requirement 5). The plugin's `_dotted` treats a path as a module path when `mod.replace(".", "").replace("_", "").isalnum() or "_" in mod`. That accepts `bridge.cursor-bridge.bridge_env` and rejects nothing useful. A namespace package (no `__init__.py`), whose `spec.origin` is `None`, is then skipped. A path is a module path when every component is `str.isidentifier()`, after an optional leading `src/`. For a namespace package, every entry of `spec.submodule_search_locations` must lie inside the copy. Write a test of yours for the namespace case.

7. **The key's framing is ambiguous** (Requirement 7: "each part length-prefixed or JSON-encoded"). `key_bytes` writes each relative path's bytes with no length before them, so a path's end cannot be told from the data that follows. Length-prefix the path as the data is length-prefixed. Separate the file part from `mutant_key_part`'s JSON by its own length prefix.

8. **`old` is counted in a partly mutated text** (Requirement 3: "a mutant whose `old` texts are not each found exactly once in the original is `not applied`"). `apply_mutant` counts each `old` in the text after the earlier pairs were applied. Count each `old` in the original. An `old` or `new` written with `\r\n` must not become `\r\r\n` in a CRLF file: normalise it to `\n` first, then convert.

9. **The Workspace is not checked to be the work tree's top** (S1: "which must be the top of a git work tree"). `main` checks only `--is-inside-work-tree`. Compare `git rev-parse --show-toplevel` with the working folder (`os.path.normcase(os.path.realpath(...))` on both) and refuse with exit 2 when they differ. A mutants file on another drive, where `os.path.relpath` raises `ValueError`, is exit 2, not an internal error.

### B. Tests of Requirement 11 that round 1 did not write

Each test's docstring names `R-041` and the clause it enforces, as `handoff/TASK-031.md` Requirement 11 says. The time ceilings of that Requirement hold.

10. **The killed run.** A run with at least three mutants is stopped after N of them have finished (N at least 1): the whole tree is ended, through `bridge-run.py --limit` or a windowless `taskkill /T /F` on Windows and `os.killpg` elsewhere. Assert that the cache holds exactly the N lines it flushed, that the tracked tree is byte-identical, and that the relaunch runs only the mutants not kept as killed. To stop it after N, a mutant's test may wait on a marker file the test writes. A `bridge-run.py` run in a test sets `HOME` and `USERPROFILE` to the test's temporary home, which `tests/conftest.py`'s autouse fixture already does for the process. It must never take the real `~/.cursor-bridge/heavy.lock`. Truncating the cache by hand, as `test_r041_relaunch_after_partial_cache` does, is a separate test of the torn-line rule, not this case.
11. **The editable install, flat and under `src/`.** In both cases the mutant mutates the package's code, never a test file. The test then shows that the copy's package ran: the mutant is killed. The other case, where the Workspace's package ran and the mutant survived, would fail the test. The `src/` fixture names `src` in its `pytest.ini` `pythonpath` (or a `conftest.py` insert relative to its own file).
12. **The editable-only `src/` package is refused.** A `src/` fixture that relies on the editable install alone, run with the venv's interpreter, exits 2 and caches nothing. The same holds in `--checkpoint` mode.
13. **`--checkpoint` with the root `.env`.** A listed new test that reads the root `.env` passes on the old code (exit 4).
14. **Requirement 1's refusals not yet tested**, each exit 2 with nothing cached:
    - an untracked test file;
    - an `untracked` path that is itself a link (symbolic link, or a junction on Windows; skip with the reason where neither can be made);
    - an unknown top-level field;
    - a duplicate id;
    - an `expect` that does not start `survive `;
    - an empty `expect_fail`;
    - a `new_tests` entry that is not tracked.
15. **Requirement 2's refusals not yet tested:** a scratch folder that contains the Workspace, and a scratch path through a link. Each exits 2.
16. **The default scratch folder, proven.** Before the run, create `<temporary home>/.cursor-bridge/scratch/proj/mutation-run-<id>/stale.txt`, where `proj` is the fixture's project folder. Run the program without `--scratch`, under that home. Assert that the folder is gone afterwards: the program removes a left-behind `mutation-run-<id>/` at its default location. Assert also that nothing was created under the real home. Compare the real home's `.cursor-bridge` listing before and after, read through `bridge_env.real_home` of the environment the suite started with. Where that cannot be read, assert only on the temporary home.
17. **The timeout goes on.** Extend `test_r041_timeout_error_continues`. After the looping mutant, a second mutant is killed in the same run. Assert that it ran, and that the exit is 3. Assert also that the looping test's process does not outlive the run. That test writes `os.getpid()` to a file under the test's `tmp_path` before it loops. After the run, the test asserts that this pid has ended: `os.kill(pid, 0)` raising `OSError` elsewhere, and on Windows `ctypes` `OpenProcess` with `SYNCHRONIZE`, then `WaitForSingleObject(handle, 0)` returning `WAIT_OBJECT_0`, or the open failing.

### C. Tests that do not prove their claim

18. `test_r041_done_c_mutated_file_reruns` asserts `m2: killed (cached`. Both of its mutants mutate `tests/test_calc.py`, and the change is to `demo/calc.py`, so nothing it names reruns. Rewrite it so that a change to the mutated file reruns that file's mutants and no other. The supervisor's `test_task031_req7_a_change_reruns_only_the_mutants_it_keys` shows one form.
19. `test_r041_default_scratch_under_temp_home` asserts `not list(...) if scratch.exists() else True`, which holds whatever the program did. Replace it with item 16.
20. `test_r041_editable_install_overridden` mutates the test file, so it cannot tell which package ran. Replace it with item 11.
21. `test_r041_tree_unchanged_after_run` and the killed-run test compare the whole tree, `.git` excluded. Also compare `git status --porcelain` before and after, which must be equal.

## Acceptance criteria

- [ ] `python -m pytest tests/test_mutation_run_supervisor.py -q -p no:cacheprovider -rA` passes, with the link test passing or skipped with its reason. The file is unchanged (`git diff --quiet -- tests/test_mutation_run_supervisor.py`).
- [ ] `python -m pytest tests/test_mutation_run.py -q -p no:cacheprovider --durations=0` passes, each test within its ceiling, and every item of B and C has its test.
- [ ] Every code defect of A is fixed at the cause named, never by special-casing a test's fixture.
- [ ] `python tools/dump-cli.py --check` exits 0, and `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge/mutation-run.py` prints `0 FAIL`. The program is ASCII only.
- [ ] `python -m pytest tests/test_dump_cli.py tests/test_tests_windowless.py tests/test_bridge_run_driver.py -q -p no:cacheprovider` passes.
- [ ] `git status --porcelain` shows no changed or new file outside Scope.

## Constraints

Every constraint of `handoff/TASK-031.md` holds, except its by-hand mutation check, which is dropped in this round. In particular:
- Run nothing with this Workspace as the program's working folder.
- Never touch the real `~/.cursor-bridge/` or `~/.claude/`.
- Every launch is windowless, and nothing outlives a test.
- No dependencies are added.
- The git commands of that brief stay forbidden in this Workspace.

## Verification commands

Run each from the Workspace folder, in this order:
1. `python -m pytest tests/test_mutation_run_supervisor.py -q -p no:cacheprovider -rA`
2. `python -m pytest tests/test_mutation_run.py -q -p no:cacheprovider --durations=0`
3. `python tools/dump-cli.py --check` (run `python tools/dump-cli.py` first only if the parser's text changed)
4. `python -m pytest tests/test_dump_cli.py tests/test_tests_windowless.py tests/test_bridge_run_driver.py -q -p no:cacheprovider`
5. `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge/mutation-run.py`
6. `python -c "d=open('bridge/cursor-bridge/mutation-run.py','rb').read(); print(all(b < 128 for b in d))"`
7. `python -m pytest tests -q -p no:cacheprovider`. The full suite takes about eleven minutes: let it finish. The install-stamp failures that name `mutation-run.py (not in the manifest)` are expected. List them by test id, and treat any other failure as a defect.
8. `git status --porcelain`

## Done

Your report is the file `handoff/TASK-031-r2-report.md`. Write it as you go. Never paste a computer path or a user name into it.

State only what you ran, and quote pytest's own output for each run, at least its summary line. Do not round, summarise or reconstruct a figure. Do not repeat a figure from round 1's report as this round's. The supervisor and both reviewers re-run every command, and a claim they cannot reproduce rejects the round.

The report holds:
- the files you changed;
- one paragraph on what you did;
- for each item of A, the cause you fixed and where;
- for each item of B and C, the test's name;
- the quoted output of each verification command, with the durations table and the install-stamp failures by test id;
- a section headed exactly `Assumed, not verified`, one item per line (what you assumed · why · what would confirm it), or `Assumed, not verified: none`.

Your last message is the summary and the report file's path, and nothing follows it.
