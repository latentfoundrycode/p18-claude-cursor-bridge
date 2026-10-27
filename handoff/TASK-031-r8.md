# TASK-031 round 8: the blocking finding of round 7's gate

## Objective

Fix the following confirmed defect: repair the named cause, nothing else. Round 7's head, b8de2a7, went through the gate, and its security audit found one blocking defect, confirmed by reproduction. This increment is past the owner's three-round review ceiling, so this round carries that one finding only, of the classes data integrity and behaviour against the brief. Every other finding of round 7's reviews is recorded in `docs/HARDENING.md`, under "TASK-031 (round 7; the supervisor's inspection and mutation run; recorded, not taken)", and is not yours to fix. **Nothing else in `mutation-run.py` changes**: not its messages, its exit codes, its parser, its configuration names, their order, its order of checks, or any behaviour the item below does not name.

**Root cause, in one sentence.** `_pytest_config_dict_from_file` in `bridge/cursor-bridge/mutation-run.py` reads `.ini` and `.cfg` files with `configparser.ConfigParser(interpolation=None)`, whose section-header pattern `\[(?P<header>.+)\]` is greedy up to the last `]` on the line, while pytest 9.1.1 reads the same files with `iniconfig`, which on a line starting with `[` first cuts the line at the first `#` and at the first `;` (each `line.split(c)[0].rstrip()`) and then takes the text between `[` and a final `]` as the section name, so a header such as `[pytest] # the ready fixture]` is the section `pytest` to pytest and the section `pytest] # the ready fixture` to the program.

**Evidence (the security audit, round 7, reproduced).** In a `tox.ini` whose pytest section is written `[pytest] # the ready fixture]` and sets `usefixtures = ready`, the program finds no `pytest` section in that file, passes over it to the next candidate, and runs the mutant under a configuration the gate's pytest does not use. An equivalent mutant is then recorded `killed`, and that kill is cached. The same holds for `setup.cfg` with `[tool:pytest] ; note]`.

**Reproduction test (red on b8de2a7, must pass).** `tests/test_mutation_run_supervisor.py::test_task031_r8_a_section_header_holding_a_comment_is_not_read_otherwise_than_pytest_reads_it`, parametrized `[tox.ini-...]` and `[setup.cfg-...]`. On round 7's code it fails with `swap: killed (ran)`. It accepts either exit 2 with no cache line, or a cached outcome `survived`; never `killed`.

`handoff/TASK-031.md` and `-r2.md` to `-r7.md` still govern everything this file does not change. This round refines `handoff/TASK-031-r6.md` item 3 (B-3), "Find the copy's configuration file as pytest 9 does, at the copy's root", and `handoff/TASK-031-r7.md` item 2 (N-2).

Satisfies:
- R-041 (quoted whole in `handoff/TASK-031.md`). The clause at stake is "gives every mutant a result against the version the gate reads": a mutant run under a configuration the gate's pytest does not read gives a result against another version, and a false kill is cached and skipped on every later run. The brief clause at stake is `handoff/TASK-031-r6.md` item 3 (B-3): the configuration found as pytest 9.1.1 finds it.

## Scope

One brief carries one increment's scope; work that needs a second scope is a second brief, never a second section here.

Files you may create or modify:
- bridge/cursor-bridge/mutation-run.py (only `_pytest_config_dict_from_file`, or a helper that it alone calls)
- tests/test_mutation_run.py (optional: at most one new builder test of the refusal, and only if it adds a case the supervisor's test does not)
- docs/BUILDER_NOTES.md
- handoff/TASK-031-r8-report.md

Do not modify anything else.

## Out of scope

- `.env` and anything under `secrets/`
- CI configuration (`.github/`, `.githooks/`)
- `docs/` and `handoff/`, except the files the Scope section names. This covers `docs/HARDENING.md`, `docs/INVENTORY.md`, `docs/cli-reference.json` and `docs/CLI_REFERENCE.md`. The parser does not change in this round, so the command reference does not either; never run `python tools/dump-cli.py` without `--check`.
- `tests/test_mutation_run_supervisor.py`. It is the supervisor's: read and run it, never edit it. A test you believe wrong is reported with the reason, never changed or skipped. This covers the Round 8 test.
- Every existing test in `tests/test_mutation_run.py`; `tests/conftest.py` and every other test file.
- `bridge/cursor-bridge/MANIFEST.json` and every other file under `bridge/`. Never run `tools/make-manifest.py`.
- `run/supervisor/`
- Every other function of `mutation-run.py`: `_PYTEST_CONFIG_NAMES`, `copy_pytest_config_file`, `pytest_config_argv`, the `.toml` branch, and everything else.
- The advisories recorded in `docs/HARDENING.md` under TASK-031 (round 7): the raw print of survive reasons and of a cached outcome's `time` field, the run id's `.match`, the grandchild fixture's pid order, the grandchild test's reused-pid window, and round 7's verification command 7. None of them is this round's.
- Any other difference between `configparser` and `iniconfig` that you find (see Requirement 3): report it, do not fix it.
- A mutation-driver script of any kind. The supervisor's driver runs after you and is its own.

## Context

**Development data.** The inventory's decision, copied verbatim: "Development data: the dev build is the Workspace sources under `bridge/`; a session in the repo always runs the *installed* bridge (`~/.claude`), never the one being edited, and installs reach running projects only through the owner's install run sheet". The tests run the Workspace's `bridge/cursor-bridge/mutation-run.py` by file path, on fixtures under `tmp_path`. `tests/conftest.py`'s autouse fixture `home_of_the_tests` sets `HOME` and `USERPROFILE` to a fresh temporary folder for every test, so the scratch copy and the cache fall under that temporary home. Never run `mutation-run.py` with this Workspace or a real project as its working folder. Never touch the real `~/.cursor-bridge/` or `~/.claude/`. Never take or remove `heavy.lock`.

**Security context.** ASVS level 2 (`docs/INVENTORY.md`, Decisions). `.cursor/rules/secure-coding.mdc` and `.cursor/rules/workspace-boundary.mdc` are in force, and so is the frozen minimal-code rule (`bridge/cursor-bridge/minimal-code.snapshot.md`). The trust boundary this round touches: the project's pytest configuration at the copy's root. It is the project's own file, its content is untrusted text, and the program must read it as the gate's pytest reads it or refuse it; reading it a third way gives a result against a version the gate never ran.

**The code as it is (`bridge/cursor-bridge/mutation-run.py` at b8de2a7; checked).** The line numbers are approximate; read the code.
- `_PYTEST_CONFIG_NAMES` (:828-831): `"pytest.toml", ".pytest.toml", "pytest.ini", ".pytest.ini", "pyproject.toml", "tox.ini", "setup.cfg"`.
- `_pytest_config_dict_from_file(filepath)` (:834-882). The `.ini` branch (:837-851) builds `configparser.ConfigParser(interpolation=None)` and calls `cp.read(filepath, encoding="utf-8")` inside a `try`. `pytest.ini` and `.pytest.ini` count whatever they hold (the `[pytest]` section's items, or `{}` with no `[pytest]` section); `tox.ini` counts with a `pytest` section and otherwise returns `None`. The `except (configparser.Error, UnicodeDecodeError)` raises `Refuse("mutation-run: invalid ini file %s" % name)`, `name` being the base name. The `.cfg` branch (:852-860) does the same for a `tool:pytest` section, and its `except` raises `Refuse("mutation-run: invalid cfg file %s" % name)`. The `.toml` branch (:861-881) is not part of this round.
- `copy_pytest_config_file(copy_root)` (:885-893) walks `_PYTEST_CONFIG_NAMES`, calls `_pytest_config_dict_from_file` for each file that exists, and returns the first whose result `is not None`. A `None` from `tox.ini` or `setup.cfg` is how a file is passed over today; that is the path the defect takes.
- `run_main` maps `Refuse` to exit 2. A refusal from the configuration search happens before any mutant runs, so no cache line is written.

**Pytest and iniconfig.** pytest 9.1.1 and iniconfig 2.3.1 are installed (`requirements.lock`). Find the installed iniconfig source with `python -c "import iniconfig; print(iniconfig.__file__)"` run from the Workspace folder. CI runs Python 3.12 on Windows and Ubuntu (`.github/workflows/tests.yml`).

**The working tree at delegation.** The supervisor's checkpoint commit before this round holds the Round 8 test and its own edit to `docs/HARDENING.md`. If `git status --porcelain` shows `tests/test_mutation_run_supervisor.py` or `docs/HARDENING.md` changed before you have changed anything, stop and report it, because the `git diff --quiet` criterion below cannot hold then.

## Diagrams

None. The build plan's `Diagrams:` field for TASK-031 is `none`.

## Requirements

1. **A section header that iniconfig reads as another name** (data integrity; behaviour against R-041 and `handoff/TASK-031-r6.md` item 3, B-3). For every `.ini` candidate (`pytest.ini`, `.pytest.ini`, `tox.ini`) and the `.cfg` candidate (`setup.cfg`), a section header line that pytest 9.1.1's iniconfig would read as a different section name than `configparser` does is never read otherwise than pytest reads it. Two ways meet this; the supervisor prefers (a), which fails closed:
   - (a) Refuse such a file with exit 2, with the existing messages `mutation-run: invalid ini file <base name>` and `mutation-run: invalid cfg file <base name>`, unchanged. The supervisor's form of the check: after `cp.read`, refuse when any section name `configparser` returns contains `#`, `;` or `]`. The refusal covers every section of the file, not only the pytest one, since a header such as `[pytest] # x]` is not named `pytest` to configparser.
   - (b) Read the section names the way iniconfig does.
   - If you take (b), say why in the report; do not import `iniconfig` in either case.

2. **Nothing else in the configuration search changes.** The names, their order, the condition under which each name counts, the `.toml` branch, `pytest.ini` and `.pytest.ini` with no `[pytest]` section returning `{}`, a `%` anywhere in the file never raising (round 7's N-2), and the refusal of a file that does not decode or parse all stay as they are. Every Round 7 test keeps passing.

3. **Confirm against iniconfig's source.** Read the installed iniconfig source (the version pytest 9.1.1 uses, located by the command in Context) and confirm that no other section-header difference between it and `configparser` reaches the decision whether the pytest section (`pytest` in an `.ini`, `tool:pytest` in `setup.cfg`) is present. List every other difference you find under `Assumed, not verified`, with which way it goes (the file counted when pytest would not count it, or passed over when pytest would read it). Do not fix them in this round.

4. **Builder test (optional).** You may add at most one test to `tests/test_mutation_run.py`, of the refusal, and only if it adds a case the supervisor's test does not hold. Its docstring names `R-041`, `TASK-031 S7` and `handoff/TASK-031-r8.md`. It may not change any existing test.

5. **Mutation check, by hand, in process, no script in the diff.** In your own run apply each mutant below to `mutation-run.py`, run the Round 8 test, record what caught it, then restore the program's bytes exactly and confirm with `git diff -- bridge/cursor-bridge/mutation-run.py` that only your fix remains:
   1. Remove the new check: the supervisor's Round 8 test must fail with `killed`.
   2. Make the check test for `#` alone (no `;`, no `]`): the `setup.cfg` case must fail.

## Acceptance criteria

- [ ] Both cases of `test_task031_r8_a_section_header_holding_a_comment_is_not_read_otherwise_than_pytest_reads_it` pass.
- [ ] Every test of `tests/test_mutation_run_supervisor.py` and `tests/test_mutation_run.py` passes. Only the machine skip `test_r041_scratch_through_link` is allowed, with its reason quoted. `git diff --quiet -- tests/test_mutation_run_supervisor.py` exits 0.
- [ ] A `tox.ini` or `setup.cfg` (and a `pytest.ini` or `.pytest.ini`) whose section header iniconfig would read as a different name than configparser does never configures a mutant's run otherwise than pytest reads it; with (a), it exits 2 with the existing `invalid ini file` / `invalid cfg file` message naming the base name, before any mutant runs, and writes no cache line.
- [ ] The named cause is addressed at the mechanism the evidence points at: the section names the program decides on are the section names pytest's iniconfig reads, or the file is refused. The fix is not a special case of the test's fixture (not a match on `usefixtures`, on `ready`, or on one header's text).
- [ ] Only `_pytest_config_dict_from_file` (or a helper it alone calls) changed in `mutation-run.py`. Every message, exit code and the configuration names and order are unchanged.
- [ ] Both by-hand mutants were caught as Requirement 5 says, and the report lists each with what caught it.
- [ ] `python tools/dump-cli.py --check` exits 0. `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge/mutation-run.py` prints `0 FAIL`. The program is ASCII only.
- [ ] `git status --porcelain` shows no changed or new file outside Scope.
- [ ] `handoff/TASK-031-r8-report.md` exists, with its `Assumed, not verified` section.

## Constraints

Every constraint of the seven earlier briefs holds: `handoff/TASK-031.md`, `-r2.md` to `-r7.md`. There is no mutation run in this round apart from the two by-hand mutants of Requirement 5. Write no mutation script.

This round adds the following:
- Do not add dependencies. Use the standard library and pytest only. Do not import `iniconfig` in the program or a test.
- Do not read or write any file outside this workspace (the folder you were started in). The exceptions are pytest's `tmp_path` and the tests' temporary home. Reading the installed iniconfig source for Requirement 3 is allowed, read only.
- Every test that runs the program, as a subprocess or in-process, runs it with `HOME` and `USERPROFILE` set to a temporary folder. The autouse `home_of_the_tests` does this; never override it with a real home. No test touches the real `~/.cursor-bridge/` or `~/.claude/`, takes `heavy.lock`, or starts the real `cursor-agent`.
- Do not fix by suppressing the symptom. That rules out a retry, a broad `try/except`, a widened tolerance, an added `sleep`, a check that hides a wrong value, and a fix keyed to the test fixture's text.
- Do not edit `tests/test_mutation_run_supervisor.py`. Do not change any existing test in `tests/test_mutation_run.py`.
- Do not leave any `DEBUG-BUG-` line, `faulthandler` probe or stray print in the program or the tests.
- If you believe the real cause is different from the one named, stop, do not change code, and report why in your summary. The supervisor will re-diagnose.
- Every process your code or your test starts is windowless (`creationflags=subprocess.CREATE_NO_WINDOW`, `0` elsewhere). In `tests/test_mutation_run.py`, including the source text of a fixture, write `CREATE_NO_WINDOW` on the same line as every `creationflags`, as the scan of `tests/test_tests_windowless.py` requires. Nothing a test starts outlives it: each process is stopped in the test's own `finally` or a fixture's teardown, with its whole tree, and its pipes are closed or drained. Every `subprocess.run` or `communicate` in a test carries a timeout.
- Never start a server, a watcher or a daemon that outlives a test.
- If the brief, the rules or the tooling got in your way, append one dated line to `docs/BUILDER_NOTES.md`. Do the same for anything you learned about a defect or a pitfall (a cause you found, a platform quirk that cost you a round). In any Markdown you write, never break a line inside a paragraph or a list item: one paragraph is one line.
- These git commands are not yours to run: `commit`, `push`, `switch`, `checkout`, `merge`, `rebase`, `reset`, `stash`, `branch -d`, `worktree`, `add`. In this Workspace you read with `git status`, `git diff`, `git show` and `git log` only. The tests' fixture repositories under `tmp_path` may use any git command.
- Do not run `plan-check`: TASK-031 is past its plan entry, and the supervisor runs the checks.
- Prefer reuse over new code: the existing `Refuse` messages and the existing `try` of each branch. Write the minimum that meets the acceptance criteria. This never overrides a security requirement stated above.

## Verification commands

Run each one from the Workspace folder, in this order. Run only these two test files, never the whole suite.
1. `python -m pytest tests/test_mutation_run_supervisor.py tests/test_mutation_run.py -q -p no:cacheprovider -rA` (expected: all pass; the one machine skip `test_r041_scratch_through_link` is allowed)
2. `python tools/dump-cli.py --check`
3. `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge/mutation-run.py`
4. `python -c "d=open('bridge/cursor-bridge/mutation-run.py','rb').read(); print(all(b < 128 for b in d))"` (expected: `True`)
5. `git status --porcelain`, then `git diff --quiet -- tests/test_mutation_run_supervisor.py`, and report its exit code

## Done

Your report is the file `handoff/TASK-031-r8-report.md`. Write it as you go: what you did, what you changed, what you ran and what it printed, and what you could not do. That way nothing of it is lost if your run ends early. Never paste a computer path or a user name into it; write `<temporary folder>`, `<home>`, `<site-packages>` or `<Workspace>` instead. State only what you ran, quoting pytest's own output, at least its summary line, for every run. Do not repeat a figure from an earlier round's report.

When you finish, the report holds:
- the files you changed;
- one paragraph on what you did, and whether you took (a) or (b), with the reason if (b);
- one sentence on how the change addresses the named cause;
- what iniconfig 2.3.1's source does with a line starting with `[`, as you read it (the function and the steps, quoted briefly), and what `configparser`'s `SECTCRE` does with the same line;
- what a `pytest.ini` holding no `[pytest]` section does now (it must be what it did before);
- the two by-hand mutants, each with the test or tests that caught it and the line pytest printed;
- the quoted output of each verification command, including the `-rA` lines of the Round 8 test's two cases, any skip with its reason, and the exit code of `git diff --quiet`;
- a section headed exactly `Assumed, not verified`, one item per line (what you assumed; why; what would confirm it). If there are none, write `Assumed, not verified: none`. Be specific: "edge cases" or "error handling" is not an item. Name at least:
  - that the iniconfig version you read is the one pytest 9.1.1 imports in CI on both Windows and Ubuntu;
  - every other section-header difference between iniconfig and `configparser` you found (for example leading whitespace before `[`, a header with no final `]`, a `[` inside the name, an empty name, a header holding `#` or `;` with no `]` after it, duplicate sections), each with which way it goes and whether it reaches the pytest-section decision;
  - that refusing a file for a `#`, `;` or `]` in a section other than the pytest one (a `[testenv:x]` or `[metadata]` section) refuses no file that a project actually uses, or say that it may.

Your last message is the summary and the report file's path, and nothing follows it: the supervisor reads only the last message, and a message printed earlier and then followed by more work is lost.
