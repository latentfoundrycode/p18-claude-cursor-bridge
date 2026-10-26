# TASK-031 round 3: one code defect, and the tests the supervisor's mutants showed missing

## Objective

Round 2 fixed every defect `handoff/TASK-031-r2.md` named, and all seven of that round's supervisor tests pass. The supervisor's inspection of round 2 found one more code defect, in `--checkpoint` mode. The supervisor's own mutation driver then ran 25 mutants on round 2's program. Eight survived every test in `tests/test_mutation_run.py` and `tests/test_mutation_run_supervisor.py`, so eight behaviours the brief requires are not held by any test. This round fixes the defect and writes the eight tests. `handoff/TASK-031.md` and `handoff/TASK-031-r2.md` still govern everything this file does not change.

This is the third and last round under the owner's three-round review ceiling. After it, only a defect of the five blocking classes sends the work back. Every test asked for here must therefore fail on the mutant named beside it, and the report must show that it does.

Satisfies:
- R-041 (quoted whole in `handoff/TASK-031.md`).

## Scope

One brief carries one increment's scope; work that needs a second scope is a second brief, never a second section here.

Files you may create or modify:
- bridge/cursor-bridge/mutation-run.py
- tests/test_mutation_run.py
- docs/cli-reference.json and docs/CLI_REFERENCE.md (only through `python tools/dump-cli.py`, and only if the parser's text changes)
- docs/BUILDER_NOTES.md
- handoff/TASK-031-r3-report.md

Do not modify anything else.

## Out of scope

- `tests/test_mutation_run_supervisor.py` (the supervisor's: read and run it, never edit it), `tests/test_dump_cli.py`, `tests/conftest.py` and every other existing test file
- `bridge/cursor-bridge/MANIFEST.json` and every other file under `bridge/` (never run `tools/make-manifest.py`)
- `run/supervisor/` (the supervisor's driver lives there; do not read, run or copy it)
- Everything the two earlier briefs list as out of scope

## Context

The supervisor's new test is `tests/test_mutation_run_supervisor.py::test_task031_req8_a_module_the_increment_adds_does_not_refuse_the_checkpoint_run`. On round 2's code it fails:

```
E       assert 2 == 0
... stderr='mutation-run: module demo.newmod does not resolve inside the copy\n'
FAILED tests/test_mutation_run_supervisor.py::test_task031_req8_a_module_the_increment_adds_does_not_refuse_the_checkpoint_run
```

The supervisor's driver applied each mutant below to round 2's `bridge/cursor-bridge/mutation-run.py`, ran both test files with `-x`, and restored the file byte for byte. Each of these survived, with `57 passed, 1 skipped`. Each item in Requirements B says why no test caught it.

## Requirements

### A. The code defect

1. **A mutated module that the increment adds refuses the checkpoint run** (Requirements 5 (i) and 8 of `handoff/TASK-031.md`). In round 2's `run_resolution_check`, every dotted path of every mutant must resolve inside the copy, and one that resolves nowhere is refused with `does not resolve inside the copy`. That was the supervisor's wording in round 2's item 5, and it is right for a normal run, where the mutated file is in the copy. At a checkpoint, a module the increment adds is absent, so it resolves nowhere. Its new test then fails to collect, and Requirement 8 lists that test `not run`. In `--checkpoint` mode, refuse a mutant's module only when it resolves *outside* the copy. One that resolves nowhere passes. Normal mode is unchanged. The supervisor's test above must pass.

### B. Tests for the mutants that survived

Each test's docstring names `R-041` and the clause it enforces. Each test must fail on the mutant beside it, and pass on the fixed program. To show that, apply the mutant by hand, run the one test, quote pytest's summary line, then restore the file. Record the file's sha256 before the first mutant and confirm it after each restore. The supervisor's driver runs again after you.

2. **M06: the program's test run started without `creationflags=NO_WINDOW`** (the Windows `Popen` in `run_process`). `test_r041_pytest_child_windowless` survives it, because its probe runs in a grandchild that `tests/conftest.py`'s fixture starts with its own `CREATE_NO_WINDOW`. That grandchild has a console of its own whatever the program did. Probe the pytest process itself, the one the program starts. Its `pytest_sessionstart` hook, in the fixture's conftest, computes `GetConsoleWindow()` and the process ids on its own console in-process, using `ctypes` as `PRINT_WINDOW` does. It writes them to the probe file without starting any process. The test asserts that the window is 0 and that the mutation program's own pid (`proc.pid` of the program you start) is not on that console. Without the flag, the pytest process shares the program's console, so the program's pid is on it.
3. **M07: `crlf = False`.** The CRLF test's `old` text, `return a + b`, has no newline, so it matches with or without the conversion. Use a CRLF fixture and a mutant whose `old` and `new` texts span two lines, written with `\n` in the mutants file. Assert that it is killed. Without the conversion it is `not applied`.
4. **M11: no `conftest.py` above the test folder in the key** (`conftest_paths`). Use a test file in `tests/unit/`, with a tracked `tests/conftest.py`. Run once (killed and recorded), change `tests/conftest.py`, then run again and assert the mutant ran again (its cache gains a line).
5. **M13: no refusal of a tracked link** (`validate_tracked_copy` returning at once). Commit a tracked file `data/x.txt`. Then replace the folder `data` with a link to a folder outside the Workspace holding `x.txt`. That is a junction on Windows (`cmd /c mklink /J`, windowless, as `tests/test_mutation_run_supervisor.py` makes one), and a symbolic link elsewhere. `git ls-files` still lists `data/x.txt`. Assert exit 2, with stderr naming the link, and nothing cached. Skip with the reason only where neither kind of link can be made.
6. **M21: `..` accepted by `path_bad`.** `test_r041_refuse_dotdot` passes on the mutant, because `demo/../demo/calc.py` is then refused as not in the git index. Assert that the stderr names the path's form, round 1's `file path is not relative` or an equivalent message naming `..`, and not the git index.
7. **M22: `old` accepted when it is found more than once in the original** (`< 1` in place of `!= 1`). Use a file whose `old` text occurs twice. Assert `not applied` and exit 1.
8. **M23: the root `.env` not copied in a normal run** (`copy_tracked`). `test_r041_env_and_untracked_in_copy` survives, because its mutant is killed whether or not the `.env` is there. Use a mutant of `demo/calc.py` whose `tests` are `tests/test_calc.py` and a `tests/test_env.py` that passes only when the root `.env` holds the fixture's value, with `expect_fail` naming only `tests/test_calc.py`'s test. Assert exit 0, `killed`. Without the copy, `test_env` fails unexpectedly, and the run is `error` with exit 3.
9. **M25: a pytest ERROR not counted an error** (`classify_outcome`). Use a mutant whose `tests` include a test with a fixture that raises in its setup, which pytest reports as `ERROR`, and whose `expect_fail` test does fail. Assert `error` and exit 3, never `killed`.

## Acceptance criteria

- [ ] `python -m pytest tests/test_mutation_run_supervisor.py tests/test_mutation_run.py -q -p no:cacheprovider -rA --durations=0` passes, each test within its ceiling. `git diff --quiet -- tests/test_mutation_run_supervisor.py` holds.
- [ ] For items 2 to 9, the report quotes the one test's pytest summary line on its mutant, failing, and the sha256 confirmation after each restore.
- [ ] `python tools/dump-cli.py --check` exits 0. `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge/mutation-run.py` prints `0 FAIL`. The program is ASCII only.
- [ ] `python -m pytest tests/test_dump_cli.py tests/test_tests_windowless.py tests/test_bridge_run_driver.py -q -p no:cacheprovider` passes.
- [ ] `git status --porcelain` shows no changed or new file outside Scope.

## Constraints

Every constraint of `handoff/TASK-031.md` and `handoff/TASK-031-r2.md` holds. The by-hand mutants of items 2 to 9 are the only mutation work: apply each in place, run, and restore. Write no mutation script, and leave nothing of it in the diff.

## Verification commands

Run each from the Workspace folder, in this order:
1. `python -m pytest tests/test_mutation_run_supervisor.py tests/test_mutation_run.py -q -p no:cacheprovider -rA --durations=0`
2. Items 2 to 9's mutants, one at a time, as Requirements B says.
3. Command 1 again, after the last restore.
4. `python tools/dump-cli.py --check`
5. `python -m pytest tests/test_dump_cli.py tests/test_tests_windowless.py tests/test_bridge_run_driver.py -q -p no:cacheprovider`
6. `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge/mutation-run.py`
7. `python -c "d=open('bridge/cursor-bridge/mutation-run.py','rb').read(); print(all(b < 128 for b in d))"`
8. `git status --porcelain`

The supervisor runs the full suite after your run, so you need not.

## Done

Your report is the file `handoff/TASK-031-r3-report.md`. Write it as you go. Never paste a computer path or a user name into it. State only what you ran, quoting pytest's own output, at least its summary line, for every run. Do not repeat a figure from an earlier round's report.

The report holds:
- the files you changed;
- one paragraph on what you did;
- item 1's cause and fix;
- for items 2 to 9, the test's name, the mutant's summary line and the sha256 confirmation;
- the quoted output of each verification command;
- a section headed exactly `Assumed, not verified`, one item per line (what you assumed · why · what would confirm it). Round 2's `none` overlooked at least the item 1 case, so look again. Name at least what your Windows-only and POSIX-only branches assume about the platform you did not run.

Your last message is the summary and the report file's path, and nothing follows it.
