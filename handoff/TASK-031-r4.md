# TASK-031 round 4: the blocking findings of the gate's reviews

## Objective

Round 3's head, 989181d, went through the gate. Review A rejected it, and the security audit failed it. This round is past the owner's three-round review ceiling, so it carries only findings of the five blocking classes: behaviour against the brief or the register, security, data integrity, a defeated safety mechanism, and a failing test. Each item below names its class. Every other finding is recorded in `docs/HARDENING.md` and is not yours to fix.

The supervisor wrote one test or more for each item in `tests/test_mutation_run_supervisor.py`, under the heading comment "Round 4". All 15 fail on round 3's code, each for the reason its item names. This round makes them pass. `handoff/TASK-031.md`, `-r2.md` and `-r3.md` still govern everything this file does not change.

Satisfies:
- R-041 (quoted whole in `handoff/TASK-031.md`).

## Scope

One brief carries one increment's scope; work that needs a second scope is a second brief, never a second section here.

Files you may create or modify:
- bridge/cursor-bridge/mutation-run.py
- tests/test_mutation_run.py
- docs/cli-reference.json and docs/CLI_REFERENCE.md (only through `python tools/dump-cli.py`, and only if the parser's text changes)
- docs/BUILDER_NOTES.md
- handoff/TASK-031-r4-report.md

Do not modify anything else.

## Out of scope

- `tests/test_mutation_run_supervisor.py`: read and run it, never edit it. A test you believe wrong is reported with the reason, never changed or skipped.
- `tests/conftest.py`, `tests/test_dump_cli.py` and every other existing test file
- `bridge/cursor-bridge/MANIFEST.json` and every other file under `bridge/`. Never run `tools/make-manifest.py`.
- `run/supervisor/`
- Every finding not listed below, including the advisories the reviewers raised: they are recorded, not yours.

## Context

The supervisor ran the round-4 tests on round 3's code. These are the failure lines, abridged:

```
B1 [addopts -q]   m: error (no pytest summary) (ran)
B1 [colour forced] m: error (no pytest summary) (ran)
B2  mutation-run: new_tests lists file 'tests/test_calc.py' which exists at the checkpoint; list new tests by id
B3  tests/test_new.py: failing                       (exit 0)
B4  gate: killed (ran)                               (the second run ran only `gate`; `later` stayed cached)
S1  m: killed (ran)                                  (a scratch inside the Workspace in other case was accepted)
S3  m: killed (ran)                                  (for `.`, `.git` and `fixtures/./data.txt`)
S2  m: killed (ran)                                  (the cache hard link to an outside file was written through)
B7  m: error (expected id absent) (ran) / internal error - 'int' object has no attribute 'replace' / ... not iterable
B8  mutation-run: resolution check failed (pytest exit 5)   (a pytest.ini in the home configured the copy's run)
B6  m: killed (wrong equivalence claim) (ran)        (counts: killed=1)
```

The supervisor also removed round 1's `test_r041_pytest_child_windowless`. `test_r041_pytest_process_windowless` supersedes it, and its key was spelled to pass the windowless scan.

## Requirements

1. **B1: a kill read from the terminal text** (behaviour against Requirement 6 and R-041's "a kill is a named expected test failing in the report"). `SUMMARY_RX`, `^=+ .+ in [\d.]+s =+$`, misses three cases:
   - pytest's final line for a run of 60 s or more (`in 75.32s (0:01:15)`);
   - a run under `addopts = -q`, whose line has no `=` separators;
   - a run whose inherited environment forces colour.

   A kill then reads as `error (no pytest summary)`, which is never cached, so the mutant reruns forever. Stop parsing the terminal text for outcomes. Run each mutant's tests, and the `--checkpoint` mode's tests, with a plugin of the program's own (`-p <its module>`). The plugin writes to a JSON file inside `mutation-run-<id>/`, outside the copy's tree:
   - each test's node id and its outcome, from `pytest_runtest_logreport`. A failure in setup or teardown is `error`, a failure in the call is `failed`, a pass is `passed`, and a skip is `skipped`;
   - a marker that the session finished, from `pytest_sessionfinish`, with its exit status;
   - every collection error, from `pytest_collectreport`.

   Use the plugin's module for the resolution check too, or a second one beside it. Neither shadows a project module, and neither is ever collected. Node ids are as pytest names them from the copy's root, matched with `/`. A missing results file, or one with no session-finished marker, is `error` (`no pytest result`). Requirement 6's classification is otherwise unchanged, now read from these records. Supervisor tests: `test_task031_r4_b1_a_kill_is_read_from_the_outcomes_not_the_terminal_text[addopts -q]` and `[colour forced]`.

   In `tests/test_mutation_run.py`, every rerun test that asserts only `run=1` (`test_r041_done_c_*` and the other rerun cases) also asserts that the rerun's outcome is `killed`, from the cache file's last line. That is how B1 stayed hidden.

2. **B2: an id in a file the checkpoint holds is refused** (behaviour against Requirements 1 and 8). `validate_checkpoint` applies its "file exists at the checkpoint" refusal to `path::name` items as well as to files. Apply it only to items without `::`. Supervisor test: `test_task031_r4_b2_a_new_test_in_an_existing_file_is_checked_at_the_checkpoint`.

3. **B3: a listed item judged as a whole** (behaviour against Requirements 8 and 9, and a defeated safety mechanism: the checkpoint mode exists to catch a new test that cannot fail). A listed file, or a parametrized id, holding one test that passes on the old code and one that fails is printed `failing`, and the run exits 0. List every test the plugin reports, each by its id with its outcome:
   - `passing on old code`, for a test that passed;
   - `failing`, for a test that failed;
   - `not run`, for an item that could not collect.

   Exit 4 when any of them passed. Supervisor test: `test_task031_r4_b3_each_listed_test_is_judged_alone_at_the_checkpoint`.

4. **B4: a key computed from bytes that did not run** (data integrity of the cache; R-041: a kill is kept only for keyed inputs byte-identical to those of the run). The copy is taken once, but each mutant's key is read from the Workspace when the loop reaches it. A keyed file edited during a run therefore keeps a later mutant `killed` under bytes that never ran. Compute every key from the copy's bytes, before any mutant is applied: the tree as copied, which is what runs. Also add the root's `tox.ini` to the configuration files the key covers, beside `pytest.ini`, `pyproject.toml` and `setup.cfg`, since it can hold pytest's configuration. Supervisor test: `test_task031_r4_b4_a_kill_is_keyed_by_the_bytes_that_ran`.

5. **B5: archive member names not checked** (security; Requirement 8, "No archive member is written outside `mutation-run-<id>/`"). `archive_checkpoint` joins `member.name` to the copy's root with no check. A tree entry may be absolute, hold `..`, or (written on Windows) hold `\` or `:`. Refuse the whole run with exit 2, naming the member, when a member's name is any of these, or when `os.path.normpath(os.path.join(dest, name))` does not lie under `dest + os.sep`. Refuse it too when the member is neither a regular file nor a folder. Factor the extraction into a function that takes the tar bytes, and test it in-process in `tests/test_mutation_run.py` with crafted tar archives (`tarfile` and `io.BytesIO`), one per refused form, plus a well-formed one that extracts.

6. **S1: the scratch containment compared case-sensitively** (security and data integrity; found by both reviewers). `validate_scratch` compares `abspath` strings, so on Windows a `--scratch` inside the Workspace written in other letter case passes. The copy, the root `.env` with it, is then written into the Workspace, and `shutil.rmtree` runs there. Compare `os.path.normcase(os.path.realpath(...))` of both paths with `os.path.commonpath`, for "inside" and for "contains". Apply the same comparison to `validate_untracked`'s inside-the-Workspace test. Supervisor test: `test_task031_r4_s1_a_scratch_folder_inside_the_workspace_in_another_case_is_refused`.

7. **S2: the cache file itself not checked** (security: a write outside the Workspace through a link; found by both reviewers). Before reading or appending, refuse with exit 2 when `run/supervisor/mutation-cache/<id>.jsonl` is a link (`bridge_env.is_link`) or a regular file with more than one hard link (`os.stat(...).st_nlink > 1`). Supervisor test: `test_task031_r4_s2_a_cache_file_that_is_a_link_is_refused`.

8. **S3: `untracked` naming the Workspace or `.git`** (behaviour against Requirement 2: "Nothing else is copied: no `.git`"). `path_bad` accepts `.`, and `validate_untracked` accepts the Workspace itself. So `untracked: ["."]` copies the whole Workspace into the copy, `.git` and its configuration included. Refuse, in every path field, a path that is `.`, holds an empty or `.` component, or whose first component is `.git` (compared case-insensitively). Supervisor test: `test_task031_r4_s3_an_untracked_entry_naming_the_workspace_or_git_is_refused` (three cases).

9. **B6: an expected survivor's kill counted as killed** (behaviour against `handoff/TASK-031-r2.md` item 1). Whether run or cached, a kill of an `expect: survive` mutant also adds to `counts["killed"]`. It counts only under `expected survive`. Supervisor test: `test_task031_r4_b6_an_expected_survivor_killed_is_not_counted_killed`.

10. **B7: malformed fields that crash or run** (behaviour against Requirement 1: "a missing or wrong-typed field ... exits 2"; `expect_fail` ids "each in one of the mutant's `tests` files"; "a refusal writes nothing, not even a cache line"). Check the type of every field before using it: `file`, every `tests`, `untracked` and `new_tests` entry, and every `pair` text. Refuse each `expect_fail` id that is not `<path>::<name>` with `<path>` one of the mutant's `tests`. Every such case is exit 2, before any copy. Supervisor test: `test_task031_r4_b7_a_malformed_mutant_is_refused_with_2` (three cases).

11. **B8: a pytest configuration above the copy is read** (behaviour against the register: R-041's "a result against the version the gate reads"). The copy lies under `~/.cursor-bridge/scratch/<project>/`, and pytest looks for a configuration file upward from its arguments. A `pytest.ini`, `pyproject.toml`, `tox.ini` or `setup.cfg` in a folder above the copy therefore configures the mutant's run, which the gate's run from the Workspace never reads. When the copy's root holds a pytest configuration file, the runs read it as they do now. When it holds none, pass `-c <an empty file named pytest.ini inside mutation-run-<id>/, outside the tree>` and `--rootdir <the copy's root>`, for the mutant runs, the resolution check and the checkpoint's runs alike. Node ids must still be named from the copy's root. Supervisor test: `test_task031_r4_b8_a_pytest_configuration_above_the_copy_is_not_read`.

12. **The bound's kill can hang** (a defeated safety mechanism: S7's per-mutant bound). `kill_tree`'s `taskkill` run has no timeout, and `run_process`'s last `proc.communicate()` after `proc.kill()` has none either. A grandchild that holds the pipes therefore holds the run past its bound. Give `taskkill` a timeout of 30 s. After the kill, close the pipes rather than wait on them without a bound: `communicate(timeout=30)`, then on a second `TimeoutExpired`, close `proc.stdout` and `proc.stderr` and `proc.wait(timeout=30)`. Test it in `tests/test_mutation_run.py`. A mutant's test starts a grandchild that inherits the pipes and sleeps, so the run must end within the bound plus 60 s, the mutant `error` (`timed out`). The grandchild is ended by the test's own teardown, not left behind.

## Acceptance criteria

- [ ] `python -m pytest tests/test_mutation_run_supervisor.py tests/test_mutation_run.py -q -p no:cacheprovider -rA --durations=0` passes, each test within its ceiling. `git diff --quiet -- tests/test_mutation_run_supervisor.py` holds.
- [ ] Every item is fixed at the cause named, never by special-casing a test's fixture.
- [ ] `python tools/dump-cli.py --check` exits 0. `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge/mutation-run.py` prints `0 FAIL`. The program is ASCII only.
- [ ] `python -m pytest tests/test_dump_cli.py tests/test_tests_windowless.py tests/test_bridge_run_driver.py -q -p no:cacheprovider` passes.
- [ ] `git status --porcelain` shows no changed or new file outside Scope.

## Constraints

Every constraint of the three earlier briefs holds. There is no by-hand mutation in this round: the supervisor's driver runs after you. Write no mutation script.

## Verification commands

Run each from the Workspace folder, in this order:
1. `python -m pytest tests/test_mutation_run_supervisor.py tests/test_mutation_run.py -q -p no:cacheprovider -rA --durations=0`
2. `python tools/dump-cli.py --check`
3. `python -m pytest tests/test_dump_cli.py tests/test_tests_windowless.py tests/test_bridge_run_driver.py -q -p no:cacheprovider`
4. `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge/mutation-run.py`
5. `python -c "d=open('bridge/cursor-bridge/mutation-run.py','rb').read(); print(all(b < 128 for b in d))"`
6. `git status --porcelain`

## Done

Your report is the file `handoff/TASK-031-r4-report.md`. Write it as you go. Never paste a computer path or a user name into it. State only what you ran, quoting pytest's own output, at least its summary line, for every run. Do not repeat a figure from an earlier round's report.

The report holds:
- the files you changed;
- one paragraph on what you did;
- for each item, the cause you fixed and where, and the test or tests that hold it;
- the quoted output of each verification command;
- a section headed exactly `Assumed, not verified`, one item per line (what you assumed · why · what would confirm it). Name at least:
  - what the plugin's records assume about pytest's hooks under `xdist`, `-p no:` options or a project's own plugins;
  - what `-c` with an empty file changes beyond the configuration search.

Your last message is the summary and the report file's path, and nothing follows it.
