# TASK-031 round 9: the blocking finding of round 8's gate

## Objective

Fix the following confirmed defect: repair the named cause, nothing else. Round 8's head, 63b09a3, went through the gate, and Review A and the security audit found, convergently, one blocking defect of the classes data integrity (a false kill, cached) and behaviour against R-041 and `handoff/TASK-031-r6.md` item 3 (B-3). This increment is past the owner's three-round review ceiling, so this round carries that one finding only. Every other finding of round 8's reviews is recorded in `docs/HARDENING.md`, under "TASK-031 (round 8; the builder's assumptions; recorded, not taken)", and is not yours to fix. **Nothing else in `mutation-run.py` changes**: not its messages, its exit codes, its configuration names, their order, its order of checks, the `.toml` branch, or any behaviour the requirements below do not name.

**Root cause, in one sentence.** `_pytest_config_dict_from_file` in `bridge/cursor-bridge/mutation-run.py` reads `.ini` and `.cfg` files with `configparser`, a second parser emulating the `iniconfig` that pytest 9.1.1 reads them with, and rounds 7 and 8 showed that each patch of the emulation leaves another shape the two parsers read differently, each giving a false, cached kill.

**Evidence (round 8's Review A and security audit, reproduced by the supervisor).**
- A column-0 line `[pytest] x`, `[pytest] trailing` or `[pytest]x` (text after the `]`, or `[pytest] x # c`) after a key line is, to iniconfig 2.3.x (`_parse.py`, `_parseline`: a line starting with `[` is cut at `#` and at `;`, right-stripped, and is a section header only if it then ends in `]`; otherwise it is a continuation of the key above), a value continuation, so the `tox.ini` holds no pytest section and pytest uses `setup.cfg`; `configparser`'s `SECTCRE.match` reads the same line as the section `pytest`, so the program takes `tox.ini`, runs the mutant under a configuration pytest does not use, and caches `killed`.
- iniconfig splits a file's lines with `str.splitlines`, which also splits on `\x0b`, `\x0c`, `\x1c` to `\x1e`, `\x85`, ` ` and ` `; `configparser` splits on `\n` and `\r` only, so `envlist = py312\x1c[pytest]` hides from the program a section pytest reads.

**The approach changes, and why.** The ban on importing `iniconfig` in rounds 7 and 8 (`handoff/TASK-031-r8.md`, Requirement 1 and the first added constraint) was the supervisor's choice, and it is lifted for this round: the program reads these files with `iniconfig` itself, as pytest does, instead of emulating it. iniconfig is already a dependency of pytest, pinned in `requirements.lock` (`iniconfig==2.3.1`, beside `pytest==9.1.1`), and present wherever the program can run pytest at all, because the program runs pytest with its own interpreter (`sys.executable, "-m", "pytest"`, `mutation-run.py` around :1151, :1192 and :1312). This is not a new dependency: nothing is added to any manifest, requirements file or lockfile.

**Reproduction tests (red on 63b09a3 with `swap: killed (ran)`, must pass).** In `tests/test_mutation_run_supervisor.py`:
- `test_task031_r9_a_header_line_pytest_reads_as_a_value_is_not_read_as_a_section`, parametrized `[[pytest] x # the old section]`, `[[pytest] trailing]`, `[[pytest]x]`;
- `test_task031_r9_a_pytest_section_after_a_line_separator_only_iniconfig_splits_on_is_read`, parametrized `[\x1c]`, `[\x0c]`.

Each accepts either exit 2 with no cache line, or a cached outcome `survived`; never `killed`. With iniconfig, each is `survived`.

`handoff/TASK-031.md` and `-r2.md` to `-r8.md` still govern everything this file does not change; where `handoff/TASK-031-r8.md` Requirement 1 or its ban on importing `iniconfig` disagrees with this file, this file wins. This round refines `handoff/TASK-031-r6.md` item 3 (B-3), "Find the copy's configuration file as pytest 9 does, at the copy's root", `handoff/TASK-031-r7.md` item 2 (N-2) and `handoff/TASK-031-r8.md` Requirement 1.

Satisfies:
- R-041 (quoted whole in `handoff/TASK-031.md`). The clause at stake is "gives every mutant a result against the version the gate reads": a mutant run under a configuration the gate's pytest does not read gives a result against another version, and a false kill is cached and skipped on every later run. The brief clause at stake is `handoff/TASK-031-r6.md` item 3 (B-3): the configuration found as pytest 9.1.1 finds it.

## Scope

One brief carries one increment's scope; work that needs a second scope is a second brief, never a second section here.

Files you may create or modify:
- bridge/cursor-bridge/mutation-run.py (only `_pytest_config_dict_from_file`, the removal of `_refuse_ini_cfg_if_configparser_section_names_disagree`, and the `import configparser` line)
- tests/test_mutation_run.py (optional: at most one new builder test, of the not-importable refusal; see Requirement 6)
- docs/BUILDER_NOTES.md
- handoff/TASK-031-r9-report.md

Do not modify anything else.

## Out of scope

- `.env` and anything under `secrets/`
- CI configuration (`.github/`, `.githooks/`)
- `docs/` and `handoff/`, except the files the Scope section names. This covers `docs/HARDENING.md`, `docs/INVENTORY.md`, `docs/cli-reference.json` and `docs/CLI_REFERENCE.md`. The parser does not change in this round, so the command reference does not either; never run `python tools/dump-cli.py` without `--check`.
- `tests/test_mutation_run_supervisor.py`. It is the supervisor's: read and run it, never edit it. A test you believe wrong is reported with the reason, never changed or skipped. This covers the Round 9 tests.
- Every existing test in `tests/test_mutation_run.py`; `tests/conftest.py` and every other test file.
- `requirements.lock`, every requirements file and every manifest. `bridge/cursor-bridge/MANIFEST.json` and every other file under `bridge/`. Never run `tools/make-manifest.py`.
- `run/supervisor/`
- Every other function of `mutation-run.py`: `_PYTEST_CONFIG_NAMES`, `copy_pytest_config_file`, `pytest_config_argv`, the `.toml` branch of `_pytest_config_dict_from_file`, and everything else.
- The installed iniconfig: 2.3.0 is installed on this machine, 2.3.1 is locked. Do not install, upgrade, downgrade or uninstall anything, and do not create an environment.
- The advisories recorded in `docs/HARDENING.md` under TASK-031 (rounds 6, 7 and 8), among them the `setup.cfg` holding a plain `[pytest]` section (see Requirement 2) and the toml conflict rule.
- Any other difference between the program and pytest's configuration search that you find: report it, do not fix it.
- A mutation-driver script of any kind. The supervisor's driver runs after you and is its own.

## Context

**Development data.** The inventory's decision, copied verbatim: "Development data: the dev build is the Workspace sources under `bridge/`; a session in the repo always runs the *installed* bridge (`~/.claude`), never the one being edited, and installs reach running projects only through the owner's install run sheet". The tests run the Workspace's `bridge/cursor-bridge/mutation-run.py` by file path, on fixtures under `tmp_path`. `tests/conftest.py`'s autouse fixture `home_of_the_tests` sets `HOME` and `USERPROFILE` to a fresh temporary folder for every test, so the scratch copy and the cache fall under that temporary home. Never run `mutation-run.py` with this Workspace or a real project as its working folder. Never touch the real `~/.cursor-bridge/` or `~/.claude/`. Never take or remove `heavy.lock`.

**Security context.** ASVS level 2 (`docs/INVENTORY.md`, Decisions). `.cursor/rules/secure-coding.mdc` and `.cursor/rules/workspace-boundary.mdc` are in force, and so is the frozen minimal-code rule (`bridge/cursor-bridge/minimal-code.snapshot.md`). The trust boundary this round touches: the project's pytest configuration at the copy's root. It is the project's own file, its content is untrusted text, and the program must read it as the gate's pytest reads it or refuse it; reading it a second way gives a result against a version the gate never ran.

**The code as it is (`bridge/cursor-bridge/mutation-run.py` at 63b09a3; checked).** The line numbers are approximate; read the code.
- `import configparser` (:13). Nothing else in the file uses `configparser` than the lines below.
- `_PYTEST_CONFIG_NAMES` (:828-831): `"pytest.toml", ".pytest.toml", "pytest.ini", ".pytest.ini", "pyproject.toml", "tox.ini", "setup.cfg"`.
- `_refuse_ini_cfg_if_configparser_section_names_disagree(cp, refuse_message)` (:834-837), round 8's helper, called only from the two branches below. It is made redundant by this round and is removed.
- `_pytest_config_dict_from_file(filepath)` (:840-892). The `.ini` branch (:843-859) builds `configparser.ConfigParser(interpolation=None)`, calls `cp.read(filepath, encoding="utf-8")` and the helper inside a `try`; `pytest.ini` and `.pytest.ini` return the `[pytest]` section's items, or `{}` with no `[pytest]` section; `tox.ini` returns the `pytest` section's items, or `None` without one. Its `except (configparser.Error, UnicodeDecodeError)` raises `Refuse("mutation-run: invalid ini file %s" % name)`, `name` being the base name. The `.cfg` branch (:860-870) does the same for a `tool:pytest` section, returning `None` without one, and its `except` raises `Refuse("mutation-run: invalid cfg file %s" % name)`. The `.toml` branch (:871-891) is not part of this round.
- `copy_pytest_config_file(copy_root)` (:895-903) walks `_PYTEST_CONFIG_NAMES`, calls `_pytest_config_dict_from_file` for each file that exists, and returns the path of the first whose result `is not None`; it is the function's only caller. A `None` from `tox.ini` or `setup.cfg` is how a file is passed over.
- `run_main` maps `Refuse` to exit 2. A refusal from the configuration search happens before any mutant runs, so no cache line is written.

**Pytest and iniconfig.** pytest 9.1.1 reads `.ini` and `.cfg` candidates in `_pytest/config/findpaths.py`, functions `_parse_ini_config` and `load_config_dict_from_file`. Read that installed source, read only, located by `python -c "import _pytest.config.findpaths as f; print(f.__file__)"`, and the installed iniconfig by `python -c "import iniconfig; print(iniconfig.__file__)"`, both run from the Workspace folder. CI runs Python 3.12 on Windows and Ubuntu (`.github/workflows/tests.yml`) and installs from `requirements.lock`.

**Test helpers in `tests/test_mutation_run.py`.** `run_mr(ws, mutants_file, scratch=None, timeout=60, extra=(), home_env=None, harness_slack=30)` runs the program as a subprocess; `test_conftest.windowless_kwargs({...})` supplies the windowless creation flags; several tests already build their own `env` and call `subprocess.run(cmd, cwd=str(ws), capture_output=True, text=True, env=env, timeout=120, **test_conftest.windowless_kwargs({}))`. Follow those patterns.

**The working tree at delegation.** The supervisor's checkpoint commit before this round holds the Round 9 tests in `tests/test_mutation_run_supervisor.py` and its own edit to `docs/HARDENING.md`. If `git status --porcelain` shows `tests/test_mutation_run_supervisor.py` or `docs/HARDENING.md` changed before you have changed anything, stop and report it, because the `git diff --quiet` criterion below cannot hold then.

## Diagrams

None. The build plan's `Diagrams:` field for TASK-031 is `none`.

## Requirements

1. **Read the `.ini` and `.cfg` candidates with iniconfig, as pytest does** (data integrity; behaviour against R-041 and `handoff/TASK-031-r6.md` item 3, B-3). In `_pytest_config_dict_from_file`, every `.ini` candidate (`pytest.ini`, `.pytest.ini`, `tox.ini`) and the `.cfg` candidate (`setup.cfg`) is parsed with `iniconfig.IniConfig(<the path as str>)`, the call pytest 9.1.1's `_parse_ini_config` makes. If the installed `_parse_ini_config` makes a different call (another constructor, or keyword arguments), make pytest's call instead, and quote both in the report.

2. **Make the decisions pytest's `load_config_dict_from_file` makes.**
   - `.ini`: `"pytest" in ini` gives the section's items as a dict; otherwise `{}` for `pytest.ini` and `.pytest.ini`, and `None` for `tox.ini`.
   - `.cfg`: `"tool:pytest" in ini.sections` gives that section's items as a dict; otherwise `None`. A `setup.cfg` with a plain `[pytest]` section and no `[tool:pytest]` keeps the program's current behaviour (passed over, `None`), where pytest stops with an error; that difference is recorded in `docs/HARDENING.md` (round 6) and is not this round's.

3. **Refusals.** `iniconfig.ParseError` and `UnicodeDecodeError` raised while reading such a file raise `Refuse` with the existing messages, unchanged: `mutation-run: invalid ini file <base name>` for an `.ini`, `mutation-run: invalid cfg file <base name>` for the `.cfg` (exit 2, before any mutant runs, no cache line). Catch exactly these two, not a broader class.

4. **iniconfig not importable.** When an `.ini` or `.cfg` candidate is read and `iniconfig` cannot be imported, raise `Refuse("mutation-run: pytest's iniconfig is not importable")` (exit 2). Import `iniconfig` at that point, inside the function's `.ini` and `.cfg` handling, not at module top, so a run whose copy root holds no `.ini` or `.cfg` candidate needs nothing new. The message text is fixed by this brief; keep it ASCII (the apostrophe is U+0027).

5. **Remove the emulation.** Remove `configparser` from `_pytest_config_dict_from_file`, remove `_refuse_ini_cfg_if_configparser_section_names_disagree`, and remove the `import configparser` line, since nothing else in the file uses it. The toml branch, the candidate names and their order, `copy_pytest_config_file` and everything else stay as they are.

6. **Builder test (optional).** You may add at most one test to `tests/test_mutation_run.py`, of Requirement 4's refusal: the program run as a subprocess with an interpreter setting that hides `iniconfig` from it (for example through the child's environment), on a fixture under `tmp_path` holding a `tox.ini` or `pytest.ini`, expecting exit 2, the message, and no cache line. It must not touch, rename or shadow anything in the installed packages, must write nothing outside `tmp_path` and the tests' temporary home, and must keep the child's `HOME` and `USERPROFILE` at the temporary home. Its docstring names `R-041`, `TASK-031 S7` and `handoff/TASK-031-r9.md`. It may not change any existing test. If it cannot be done within these limits, write no test and list the refusal under `Assumed, not verified`.

7. **Mutation check, by hand, in process, no script in the diff.** In your own run apply each mutant below to `mutation-run.py`, run the named tests, record what caught each and the line pytest printed, then restore the program's bytes exactly and confirm with `git diff -- bridge/cursor-bridge/mutation-run.py` that only your fix remains:
   1. Put `configparser` back: round 8's code for this function and its helper (`git show 63b09a3:bridge/cursor-bridge/mutation-run.py` shows it). The five Round 9 test cases must fail with `killed`.
   2. Catch `iniconfig.ParseError` but not `UnicodeDecodeError`: `test_task031_r7_n2_a_pytest_configuration_that_does_not_decode_is_refused` must fail.
   3. Make `tox.ini` return `{}` instead of `None` when it holds no pytest section: name the test or tests that fail; if none does, say so and list it under `Assumed, not verified`.

## Acceptance criteria

- [ ] All five cases of the two Round 9 tests pass: `test_task031_r9_a_header_line_pytest_reads_as_a_value_is_not_read_as_a_section` (three) and `test_task031_r9_a_pytest_section_after_a_line_separator_only_iniconfig_splits_on_is_read` (two).
- [ ] `test_task031_r8_a_section_header_holding_a_comment_is_not_read_otherwise_than_pytest_reads_it` (both cases), the `test_task031_r7_n2_*` tests (the percent signs; a file that does not decode exits 2 naming the file) and every other test of `tests/test_mutation_run_supervisor.py` and `tests/test_mutation_run.py` pass. Only the machine skip `test_r041_scratch_through_link` is allowed, with its reason quoted. `git diff --quiet -- tests/test_mutation_run_supervisor.py` exits 0.
- [ ] The named cause is addressed at the mechanism the evidence points at: the `.ini` and `.cfg` candidates are parsed by the same iniconfig call pytest 9.1.1 makes, and the decision whether a file counts is pytest's decision (Requirement 2). No `configparser` is left in `mutation-run.py`, and the round-8 helper is gone. The fix is not a special case of the tests' fixtures (not a match on `usefixtures`, on `ready`, on a separator character, or on one header's text).
- [ ] An `iniconfig.ParseError` or a `UnicodeDecodeError` gives exit 2 with the existing `invalid ini file` / `invalid cfg file` message naming the base name; iniconfig not importable gives exit 2 with `mutation-run: pytest's iniconfig is not importable`; each before any mutant runs, with no cache line. `iniconfig` is imported only where an `.ini` or `.cfg` candidate is read.
- [ ] Only `_pytest_config_dict_from_file`, the removed helper and the removed import changed in `mutation-run.py`. Every other message, every exit code, and the configuration names and order are unchanged. No manifest, requirements file or lockfile changed.
- [ ] The three by-hand mutants were applied as Requirement 7 says, and the report lists each with what caught it (or, for the third, that nothing did).
- [ ] `python tools/dump-cli.py --check` exits 0. `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge/mutation-run.py` prints `0 FAIL`. The program is ASCII only.
- [ ] `git status --porcelain` shows no changed or new file outside Scope.
- [ ] `handoff/TASK-031-r9-report.md` exists, with its `Assumed, not verified` section, and holds no computer path and no user name.

## Constraints

Every constraint of the eight earlier briefs holds: `handoff/TASK-031.md`, `-r2.md` to `-r8.md`, except `handoff/TASK-031-r8.md`'s ban on importing `iniconfig`, which this round lifts for the program (Requirement 1). There is no mutation run in this round apart from the three by-hand mutants of Requirement 7. Write no mutation script.

This round adds the following:
- Do not add dependencies. iniconfig, already installed as pytest's dependency and pinned in `requirements.lock`, is the one import this round allows beyond the standard library and pytest; add it to no manifest, requirements file or lockfile. Do not install, upgrade or downgrade any package, and create no environment.
- Do not read or write any file outside this workspace (the folder you were started in). The exceptions are pytest's `tmp_path` and the tests' temporary home, and reading the installed `_pytest/config/findpaths.py` and iniconfig source, read only.
- Every test that runs the program, as a subprocess or in-process, runs it with `HOME` and `USERPROFILE` set to a temporary folder. The autouse `home_of_the_tests` does this; never override it with a real home. No test touches the real `~/.cursor-bridge/` or `~/.claude/`, takes `heavy.lock`, or starts the real `cursor-agent`.
- Do not fix by suppressing the symptom. That rules out a retry, a broad `try/except` (catch exactly `iniconfig.ParseError` and `UnicodeDecodeError` when reading, and `ImportError` when importing), a widened tolerance, an added `sleep`, a check that hides a wrong value, and a fix keyed to the test fixtures' text.
- Do not edit `tests/test_mutation_run_supervisor.py`. Do not change any existing test in `tests/test_mutation_run.py`.
- Do not leave any `DEBUG-BUG-` line, `faulthandler` probe or stray print in the program or the tests.
- If you believe the real cause is different from the one named, stop, do not change code, and report why in your summary. The supervisor will re-diagnose.
- Every process your code or your test starts is windowless (`creationflags=subprocess.CREATE_NO_WINDOW`, `0` elsewhere). In `tests/test_mutation_run.py`, including the source text of a fixture, write `CREATE_NO_WINDOW` on the same line as every `creationflags`, as the scan of `tests/test_tests_windowless.py` requires, or use `test_conftest.windowless_kwargs` as the existing tests do. Nothing a test starts outlives it: each process is stopped in the test's own `finally` or a fixture's teardown, with its whole tree, and its pipes are closed or drained. Every `subprocess.run` or `communicate` in a test carries a timeout.
- Never start a server, a watcher or a daemon that outlives a test.
- If the brief, the rules or the tooling got in your way, append one dated line to `docs/BUILDER_NOTES.md`. Do the same for anything you learned about a defect or a pitfall (a cause you found, a platform quirk that cost you a round). In any Markdown you write, never break a line inside a paragraph or a list item: one paragraph is one line.
- These git commands are not yours to run: `commit`, `push`, `switch`, `checkout`, `merge`, `rebase`, `reset`, `stash`, `branch -d`, `worktree`, `add`. In this Workspace you read with `git status`, `git diff`, `git show` and `git log` only. The tests' fixture repositories under `tmp_path` may use any git command.
- Do not run `plan-check`: TASK-031 is past its plan entry, and the supervisor runs the checks.
- Prefer reuse over new code: the existing `Refuse` messages, the existing `try` of each branch, and iniconfig's own API. Write the minimum that meets the acceptance criteria. This never overrides a security requirement stated above.

## Verification commands

Run each one from the Workspace folder, in this order. Run only these two test files, never the whole suite.
1. `python -m pytest tests/test_mutation_run_supervisor.py tests/test_mutation_run.py -q -p no:cacheprovider -rA` (expected: all pass; the one machine skip `test_r041_scratch_through_link` is allowed)
2. `python tools/dump-cli.py --check`
3. `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge/mutation-run.py`
4. `python -c "d=open('bridge/cursor-bridge/mutation-run.py','rb').read(); print(all(b < 128 for b in d))"` (expected: `True`)
5. `git status --porcelain`, then `git diff --quiet -- tests/test_mutation_run_supervisor.py`, and report its exit code

## Done

Your report is the file `handoff/TASK-031-r9-report.md`. Write it as you go: what you did, what you changed, what you ran and what it printed, and what you could not do. That way nothing of it is lost if your run ends early. **Never paste a computer path or a user name into it**, not even inside quoted command output: round 8's report quoted a temporary-folder path that carried the user name. Write `<temporary folder>`, `<home>`, `<site-packages>` or `<Workspace>` in its place, also where you quote pytest's output or the location printed by the `__file__` commands. State only what you ran, quoting pytest's own output, at least its summary line, for every run. Do not repeat a figure from an earlier round's report.

When you finish, the report holds:
- the files you changed;
- one paragraph on what you did;
- one sentence on how the change addresses the named cause;
- the call pytest 9.1.1's `_parse_ini_config` makes and the decisions its `load_config_dict_from_file` makes for `.ini` and `.cfg` files, as you read them (quoted briefly), and the iniconfig version the local interpreter imports;
- what a `pytest.ini` holding no `[pytest]` section and a `setup.cfg` holding only a plain `[pytest]` section do now (each must be what it did before);
- the three by-hand mutants, each with the test or tests that caught it and the line pytest printed;
- the quoted output of each verification command, including the `-rA` lines of the five Round 9 cases and the two Round 8 cases, any skip with its reason, and the exit code of `git diff --quiet`;
- a section headed exactly `Assumed, not verified`, one item per line (what you assumed; why; what would confirm it). If there are none, write `Assumed, not verified: none`. Be specific: "edge cases" or "error handling" is not an item. Name at least:
  - that iniconfig 2.3.0 (installed here) and 2.3.1 (locked, what CI installs) read the same files the same way for the decisions of Requirement 2, and raise the same `ParseError`;
  - that iniconfig opens the file as UTF-8 on both Windows and Ubuntu, so a file that does not decode raises `UnicodeDecodeError` there as here;
  - the not-importable refusal, if you wrote no test of it;
  - the third by-hand mutant, if no test caught it;
  - any other difference between the program's configuration search and pytest 9.1.1's that you found while reading `findpaths.py`, with which way it goes (a file counted that pytest would pass over, or passed over that pytest would read).

Your last message is the summary and the report file's path, and nothing follows it: the supervisor reads only the last message, and a message printed earlier and then followed by more work is lost.
