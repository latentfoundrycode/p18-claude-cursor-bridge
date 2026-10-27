# TASK-031: Mutation reruns that skip what is unchanged: `mutation-run.py`

## Objective

Build `bridge/cursor-bridge/mutation-run.py`, the bridge's one mutation engine, and its tests. Today every increment's mutation check is a throwaway driver script the supervisor writes under `run/supervisor/`. That script patches the product file in the Workspace, runs the named tests, and restores the bytes in a `finally`. A killed run leaves mutants in the product (KP-056), and every rerun runs every mutant again, which is where the window flood of 2026-10-19/20 came from (ISS-011). The new program reads a mutants file the supervisor writes. It applies each mutant to a scratch copy of the project, never to the Workspace, and runs the mutant's tests there with no window. It caches each outcome under a key over the inputs that decide it, so a rerun skips only what is unchanged. A kept kill holds for byte-identical keyed inputs, and every survived, unapplied or errored mutant runs again. The launcher already accepts the installed path `~/.claude/cursor-bridge/mutation-run.py` as `--kind driver` (TASK-028). The plan entry's `Done when` (a)-(d) (`docs/BUILD_PLAN.md`, "### TASK-031") is the contract. This brief quotes it and settles the points it leaves open. Where the two differ, this brief governs, and every such point is listed under Context, "Settled by this brief".

Satisfies:
- R-041: "Mutation reruns skip only what is unchanged: every mutation run is a run of the bridge's `mutation-run.py` on a mutant list the supervisor writes, which reruns a mutant only when the folder of the code it mutates, the test folders it runs, the suite's configuration or the mutant's own expectations (its expected tests and whether it is expected to survive) changed since the mutant's last killed result (a kill is a named expected test failing in the report, for whatever reason; the run crashing, failing to collect, or an unexpected test failing is an error, never a kill), reruns every survived, unapplied or errored mutant, and gives every mutant a result against the version the gate reads ... `--all` being the full run the supervisor chooses where a round changed files outside every key — the redundancy cut, the coverage and its certainty kept."

## Scope

One brief carries one increment's scope; work that needs a second scope is a second brief, never a second section here.

Files you may create or modify:
- bridge/cursor-bridge/mutation-run.py (new)
- tests/test_mutation_run.py (new)
- tests/test_dump_cli.py (one change only: `"mutation-run.py"` added to the `ARGPARSE` tuple, line 32)
- docs/cli-reference.json and docs/CLI_REFERENCE.md (written only by `python tools/dump-cli.py`, never by hand)
- bridge/cursor-bridge/MANIFEST.json: in the plan's Scope, but **the supervisor regenerates it after your run**. Do not edit it and do not run `tools/make-manifest.py`.
- docs/BUILDER_NOTES.md
- handoff/TASK-031-r1-report.md

Do not modify anything else.

## Out of scope

- .env and anything under secrets/. You never read, copy or print the Workspace's own `.env`. The tests build their own `.env` with a made-up value.
- CI configuration (`.github/`, `.githooks/`)
- docs/ and handoff/, except the files the Scope section names
- `bridge/cursor-bridge/bridge-run.py`, `bridge_env.py`, `loop-guard.py`, `VERSION`, `MANIFEST.json` and every other file under `bridge/`. This covers the launcher's path-only acceptance of the installed `mutation-run.py` (docs/HARDENING.md: "The installed mutation-run program is matched by path only"), which is not this increment's work.
- `tests/conftest.py`, `tests/test_tests_windowless.py`, `tests/test_bridge_run_driver.py` and every other existing test file except the one line of `tests/test_dump_cli.py`
- The loop's text (`delegation-loop.md`, `supervisor.md`, the agents, Known-Pitfalls): that is TASK-030, the supervisor's
- Every `run/supervisor/*_mutants.py` driver. They are the supervisor's gitignored scripts. Read `run/supervisor/task029_mutants.py` and `run/supervisor/bug029_mutants.py` to see what the program replaces, but do not edit, run or import them, and do not cite them as product.

## Context

**Scope compared by hand (ISS-013).** `plan-check.py` derives TASK-031 as merged by mistake, from 9f6ace6's subject "(... TASK-031's Scope ...)". Its BRIEF comparison therefore skips this brief, so the supervisor's packager compared Scope with the plan entry's Scope by hand. The plan's Scope is `bridge/cursor-bridge/mutation-run.py; bridge/cursor-bridge/MANIFEST.json; tests/test_mutation_run.py; docs/cli-reference.json; docs/CLI_REFERENCE.md; tests/test_dump_cli.py`. This brief's Scope holds exactly those six, plus the two bookkeeping files (`docs/BUILDER_NOTES.md` and the report). MANIFEST.json stays the supervisor's to write.

**What your report is checked against.** In TASK-029 a builder's report claimed mutant kills that the supervisor's driver then disproved, and it repeated first-run figures as re-run figures. The supervisor and both reviewers re-run every command in your report and check every claim against their own run. Report only what you ran, and quote pytest's own output for it. At inspection the supervisor adds its own tests wherever a criterion is not covered, and it runs a mutation driver of its own on the program.

**Development data.** The inventory's decision, copied verbatim: "Development data: the dev build is the Workspace sources under `bridge/`; a session in the repo always runs the *installed* bridge (`~/.claude`), never the one being edited, and installs reach running projects only through the owner's install run sheet". The tests run the Workspace's `bridge/cursor-bridge/mutation-run.py` by file path, on fixture projects built under `tmp_path`. `tests/conftest.py`'s autouse fixture `home_of_the_tests` (:62-70) sets `HOME` and `USERPROFILE` to a fresh temporary folder for every test, so the default scratch folder `~/.cursor-bridge/scratch/<project>/` falls under that temporary home. You must never create, read or remove anything under the owner's real `~/.cursor-bridge/` or `~/.claude/`. A by-hand run of the program outside pytest must meet three conditions: it sets `HOME` and `USERPROFILE` to a temporary folder you created; its working folder is a temporary fixture project, never this Workspace or any real project; and you remove both afterwards. Never run `mutation-run.py` against this Workspace itself. The supervisor does that after your run.

**Security context.** ASVS level 2 (`docs/INVENTORY.md`, Decisions). `.cursor/rules/secure-coding.mdc` and `.cursor/rules/workspace-boundary.mdc` are in force. The minimal-code rule is frozen in this repository as `bridge/cursor-bridge/minimal-code.snapshot.md`, and it is in force too. These are the trust boundaries:
- The mutants file and every path in it. Any program of the owner's account can write under `run/supervisor/`, so each path is confined to the Workspace's tracked tree.
- The scratch folder in the owner's home. Something may already be there, including a link. The program writes and removes only its own `mutation-run-<id>/` subfolder.
- The root `.env`. It holds local service passwords (KP-032). It is copied into the scratch copy and nowhere else, never printed, logged or keyed.
- The `--checkpoint` argument, which is handed to git.
- The run cache under `run/supervisor/mutation-cache/`. A link anywhere on that path would carry a write out of the Workspace.

Running the project's own test code in the copy is what the program is for.

**The launcher's driver kind, as built (bridge/cursor-bridge/bridge-run.py on this branch; checked).**
- `DRIVER_REFUSE` :106-107 names `~/.claude/cursor-bridge/mutation-run.py`.
- `_mutation_run_path()` :215-216 is `~/.claude/cursor-bridge/mutation-run.py` under `os.path.expanduser("~")`.
- `resolve_driver_program(argv, folder=None)` :283-299 accepts `python <program> [args]`. The interpreter is the one `python_interpreter_ok` :201-208 accepts: a bare `python`, `python3` or `py`, or the project's own `.venv` interpreter. The program is a `.py` file under `run/supervisor/`, or the installed `mutation-run.py`. The installed one is matched by path equality only (`_mutation_program_ok` :278-280).
- `verify_driver_program_abs(abs_prog, folder)` :307-316 re-checks the path after the slot's wait.
- The driver is started with the launcher's own working folder (`folder = os.getcwd()`, :1219; `Popen` passes no `cwd`).
- It is started with `CREATE_NO_WINDOW` inside a kill-on-close Job on Windows (:1377-1401). At the limit the whole tree is terminated with no `finally` run (exit 124).
- A driver run is healthy at exit 0 or 1 only (:1444), so exits 2, 3 and 4 are never marked healthy. The kind's default ceiling is 7,200 s (`KINDS` :105).

Nothing in the bridge imports or lists `mutation-run.py` today.

**The command reference (tools/dump-cli.py, tests/test_dump_cli.py; checked).**
- `dump-cli.py` classifies every `bridge/cursor-bridge/*.py` that has a module-level `__main__` block. A program that uses `ArgumentParser` must have a top-level `build_parser()`, or the generator exits 1 (:182-189). Its entry is the parser's `description`, positionals and options (:273-291). The module docstring does not reach the reference.
- The generator imports the module with `exec_module` (:60-67), so module-level code must write nothing and start nothing.
- An absolute default outside the bridge folder is refused (:102-109).
- Every string of the entry is checked for the repository's folder, the home folder and the current folder in any written form (:200-271). So `--scratch`'s default must be `None` and resolved at run time, and no help text may hold an expanded path. A literal `~/.cursor-bridge/scratch/<project>/` is fine.
- In `tests/test_dump_cli.py`, `test_cfgb3b_docstring_entries_hold_the_whole_docstring` (:200-210) asserts that every command not in `ARGPARSE` is a docstring entry. An argparse `mutation-run.py` left out of `ARGPARSE` fails it, which is why the tuple gains the name. `test_cfgb3b_argparse_entry_matches_its_parser` (:170-185) then checks the new entry. `test_cfgb3b_committed_reference_is_current` (:407-412) needs the committed reference regenerated.
- docs/HARDENING.md records that "TASK-031's widening assumes mutation-run.py has a top-level build_parser()".
- **You run the generator** (`python tools/dump-cli.py`) once your parser is final. Without that, the full suite fails `test_cfgb3b_committed_reference_is_current`. The generator writes only the two reference files, and both are in Scope. This follows TASK-028 r1 and TASK-029 r1. The manifest stays the supervisor's.

**The windowless rules (checked).**
- `bridge/cursor-bridge/windowless-check.py` flags every `subprocess.run/Popen/call/check_call/check_output`, `os.system` and `os.popen` call that does not carry `creationflags=...CREATE_NO_WINDOW` (`0` elsewhere), as `NO_WINDOW = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0` does in `stage-diff.py` :52 and `bridge-run.py` :103.
- `tests/conftest.py` wraps `Popen.__init__` on Windows (:34-41), so the tests' own launches are windowless already. Inside the program, the flag must be the program's own.
- `tests/test_tests_windowless.py::test_fix001_no_test_starts_a_program_around_the_default` (:145-151) scans every `.py` file under `tests/`, string literals included. A line of `tests/test_mutation_run.py` that holds `os.system(`, `os.startfile`, `os.spawn*`, `os.exec*`, `multiprocessing`, `ProcessPoolExecutor`, `CreateProcess`, or `creationflags` without `CREATE_NO_WINDOW` fails it, even inside a fixture's source text.
- The window probe to reuse is `PRINT_WINDOW` (:20-21), which prints `GetConsoleWindow()`, the process id and the ids on its console. Its docstring (:5-9) gives the reading: a child started with the flag has a console of its own, with window 0, and its parent is not on it. Inherited, the parent's console holds the parent. A virtual environment's `python.exe` adds a launcher process of its own, so name processes, never count them.

**Reuse in the bridge.** `bridge_env.real_home(env)` (:54-56) resolves the home from `USERPROFILE`, then `~`. The launcher resolves `~/.cursor-bridge/` the same way (`heavy_state_paths`, bridge-run.py :615-619), never from `LOCALAPPDATA` or `APPDATA` (KP-055). `bridge_env.is_link(path)` (:59-64) sees symlinks and Windows reparse points (junctions). Import `bridge_env` as `bridge-run.py` does (:99-101); it is installed beside the program. `stage-diff.py`'s `git()` helper (:62-71) shows the bridge's form for git: `-c core.fsmonitor=false -c core.quotepath=false`, windowless, output captured, errors raised with git's stderr. The `__main__` block of `bridge-run.py` (:1452-1456) reconfigures stdout and stderr with `errors="backslashreplace"`.

**Platform facts and pitfalls.**
- KP-054: `python -m` and a `PYTHONPATH` entry come before an editable install's `.pth` entry on `sys.path`. Pytest's own `pythonpath` ini option and a `conftest.py` `sys.path.insert` change that order, which is why the resolution check runs inside pytest.
- KP-056: a killed process runs no `finally`, and on Windows a killed parent's children live on. The scratch copy is the plan's answer.
- KP-047: a file another process reads while it may be written is published atomically. The cache is append-only and read only at the start of the next run, so it uses a flushed append with a torn last line ignored, as the plan says.
- Pytest stops the whole session at a collection error unless `--continue-on-collection-errors` is given.
- `git ls-files -z` reads a path with spaces or non-ASCII characters whole.
- The Workspace's working copies are CRLF.
- Pytest 9.1.1 is installed (`requirements.lock`). CI runs Python 3.12 on Windows and Ubuntu (`.github/workflows/tests.yml`).
- The temporary home has no global git identity, so a commit in a fixture repository needs `-c user.name=... -c user.email=...` (or the `GIT_AUTHOR_*` and `GIT_COMMITTER_*` variables).
- **To verify, and say in your report:** how pytest names a node id in the `-rA` report when the copy has no configuration file. Requirement 6 needs ids relative to the copy's root.

**Settled by this brief: points the plan entry leaves open or where its clauses disagree.** Each is restated in Requirements.
- (S1) The run's `<id>` is the mutants file's name without `-mutants.json`. The file must lie under `<Workspace>/run/supervisor/` and be named that way, with the `<id>` matching `[A-Za-z0-9][A-Za-z0-9._-]*` and holding no `..`. The Workspace is the folder the program is started in (the launcher's folder), which must be the top of a git work tree.
- (S2) The key also covers the mutated file's relative path, the mutant's list of test files, and every `conftest.py` on the way from the root to each test file's folder. Done when (d) asks a change to "a `conftest.py` on its path" to rerun, and (c)'s folder rule alone misses a `conftest.py` above the test folder. Adding inputs only adds reruns, never fewer (R-041: certainty kept).
- (S3) A mutant is `error`, not `killed`, when any of the following holds, even if an expected test also FAILED: a test outside its expected ids FAILED or ERRORed; any test is ERROR; an expected id is absent from the report; or the pytest process ended without its final summary line. R-041: "an unexpected test failing is an error, never a kill".
- (S4) A cached kill of an `expect: survive` mutant is still reported as a wrong claim of equivalence and still gives exit 1.
- (S5) Any exception the program did not expect exits 3 (a crash is an error, which ranks first), never 0, 1 or 2. This is the supervisor's standing note, "mutation-run.py must exit 2 or above on an internal error" (docs/HARDENING.md), with 3 chosen.
- (S6) `--all` together with `--checkpoint` is refused with exit 2.
- (S7) The plan sets no per-mutant time limit; the supervisor adds one (its decision, recorded at acceptance). A mutant that makes the code loop forever is a common mutation outcome, and with no bound it would hold the run until the launcher's 7,200 s limit and, never getting an outcome, rerun on every relaunch, so the mutants file could never finish. `--mutant-timeout <seconds>` (a positive integer, default 900) bounds each mutant's test run and the resolution check's collection; at the bound the test process's whole tree is ended and the mutant is `error` (`timed out`), never a kill (R-041: a crash is an error).
- (S8) The resolution check (Requirement 5) is defined for a mutated file that is no importable package module, such as the bridge's own `bridge/cursor-bridge/*.py`, which the tests load by path.
- (S9) The mutants file's field names (Requirement 1) are fixed here, since TASK-030's text and the supervisor's files will name them.

## Diagrams

None. The build plan's `Diagrams:` field for TASK-031 is `none`.

## Requirements

1. **The command and the mutants file (Done when (a)).**
   - The command is `python ~/.claude/cursor-bridge/mutation-run.py <mutants file> [--all] [--checkpoint <commit>] [--scratch <folder>] [--mutant-timeout <seconds>]`, built by a module-level `build_parser()` that takes no argument. `--mutant-timeout` is a positive integer, default 900 (S7); zero, a negative or a non-integer value exits 2.
   - The parser's `description` states the usage in one paragraph, the scratch default as the literal `~/.cursor-bridge/scratch/<project>/`, and the exit codes of Requirement 8. It holds no expanded path.
   - The program text is ASCII only, opens with `#!/usr/bin/env python3` and a module docstring, and writes or starts nothing at import.
   - The file is JSON, one object:
     - `mutants` (a list, which may be empty only with `--checkpoint`). Each mutant is an object with:
       - `id`: a non-empty string, unique in the file;
       - `file`: a relative path, `/`-separated;
       - `pairs`: a non-empty list of `{"old": <str>, "new": <str>}`, where `old` is non-empty;
       - `tests`: a non-empty list of test-file paths;
       - `expect_fail`: a non-empty list of test ids `path::name[...]`, each in one of the mutant's `tests` files;
       - optional `expect`: a string `survive <reason>`, where the reason is non-empty.
     - Optional `new_tests`: a list of test ids or test files, used with `--checkpoint`.
     - Optional `untracked`: a list of relative paths of files or folders, copied beside the tracked tree.
   - Anything else is malformed and exits 2, naming the problem: invalid JSON, a missing or wrong-typed field, an unknown top-level field, a duplicate id, or an `expect` that does not start `survive `.
   - Refused with exit 2:
     - a path, in any field, that is absolute or holds a `..` component;
     - a mutated file or test file that `git ls-files` does not list (the index is read, so the increment's new test files must be staged first, and the message says so);
     - an `untracked` path that lies outside the Workspace or is reached through a link (any component, or anything inside a listed folder);
     - a mutants file that breaks (S1);
     - with `--checkpoint`: a missing or empty `new_tests`, a `new_tests` path that is not tracked, and a listed test *file* that the checkpoint commit holds. The message for that last one is to list its new tests by id.
   - A refusal happens before any copy or test and writes nothing, not even a cache line.

2. **The scratch copy (Done when (b)).**
   - `--scratch` defaults to `<home>/.cursor-bridge/scratch/<project>/`. `<home>` is `bridge_env.real_home(os.environ)`. `<project>` is the folder name of the Workspace's parent.
   - A scratch folder is refused (exit 2) when it lies inside the Workspace, contains it, or is reached through a link: any existing component of its path, or an existing `mutation-run-<id>/` itself.
   - The program creates the scratch folder if it is absent. Inside it, it creates and removes only `mutation-run-<id>/`. It first removes one a killed run left behind, then builds the copy there, and removes it at the end of every run that reaches its end, exit 2 to 4 included.
   - The copy holds the following, as the working tree holds them:
     - every path `git ls-files` lists. A tracked path missing from the working tree is left out, and your report says how you handled it;
     - the root `.env` where present;
     - the `untracked` paths.
   - Nothing else is copied: no `.git`, `.venv`, `node_modules` or other untracked file. Nothing outside the Workspace is read through a link while copying.

3. **One mutant at a time (Done when (b)).**
   - Each mutant is applied in the copy to its file's original bytes, and those bytes are written back before the next mutant, so two mutants of one file whose old texts both match the original are each applied to the original.
   - An `old` or `new` text written with `\n` is matched and written in the file's own newline convention, so a CRLF file's mutant applies.
   - All pairs of a mutant are applied together. A mutant whose `old` texts are not each found exactly once in the original is `not applied`, and its tests do not run.

4. **The test run (Done when (b)).**
   - The mutant's `tests` run from the copy's root with the interpreter that runs the program (`sys.executable`), as `-m pytest` with `-rA`.
   - The environment is the program's own with `PYTHONPATH` set to the copy's root alone.
   - The run is started with `CREATE_NO_WINDOW` (`0` elsewhere) and `stdin=subprocess.DEVNULL`, its output read whole (no pipe left undrained).
   - Each test run, and the resolution check's collection, is bounded by `--mutant-timeout` (S7). At the bound the process's whole tree is ended: on Windows by `taskkill /T /F /PID <pid>` started windowless with its output drained, elsewhere by starting the run in a new session and killing its process group; the pipes are then drained and closed. A timed-out mutant is `error` with the reason `timed out`; a timed-out resolution check exits 3, naming the bound.
   - Every git command is read-only, windowless and has its output drained.
   - The program writes nothing in the Workspace but `run/supervisor/mutation-cache/`. It refuses with exit 2 when `run`, `run/supervisor` or `run/supervisor/mutation-cache` is a link. After any run, killed ones included, the Workspace's tracked tree is byte-identical (KP-056).

5. **The resolution check, before any test runs, in `--checkpoint` mode too (Done when (b), (S8)).**
   - Before the first mutant's tests (or the checkpoint's tests) run, one pytest invocation of all the named test files runs with `--collect-only` in the copy, under the same environment. A plugin of the program reports two things:
     - (i) for each mutated file whose path relative to the copy's root, or to its `src/` folder, is a dotted path of identifiers (`pkg/mod.py`, `src/pkg/mod.py`), where its top-level package resolves;
     - (ii) every loaded module whose `__file__` lies inside the Workspace at a path `git ls-files` lists.
   - The check passes when every (i) lies inside the copy and (ii) is empty. Otherwise it refuses with exit 2, naming the module and where it resolved, and caches nothing.
   - The plugin's own file lives inside `mutation-run-<id>/`, shadows no project module, and is never collected as a test.
   - So an editable install of the fixture package is overridden by the copy and runs, flat or under `src/`. The `src/` fixture names `src` in its pytest `pythonpath` or by a `conftest.py` insert relative to its own file; a `src/` fixture that relies on the editable install alone is the refused case.
   - A `conftest.py` that inserts the Workspace's absolute path is refused.

6. **Outcomes (Done when (c), (S3)).**
   - `killed`: at least one of the mutant's `expect_fail` ids is FAILED in the run's `-rA` report, and none of the conditions of `error` holds.
   - `survived`: none is FAILED and no condition of `error` holds.
   - `not applied`: Requirement 3.
   - `error`: the tests did not collect, the run crashed (a pytest exit code other than 0 or 1, or no final summary line), the run reached `--mutant-timeout` (S7), a test outside `expect_fail` FAILED or ERRORed, any test is ERROR, or an `expect_fail` id is absent from the report.
   - Test ids are written and matched relative to the Workspace's root, with `/`, exactly as the mutants file names them.
   - An `expect: survive` mutant is reported apart and counts as neither killed nor survived. Killed, it is reported as a wrong claim of equivalence.

7. **The cache and the key (Done when (c), (S2), (S4)).**
   - Each outcome is one JSON line in `run/supervisor/mutation-cache/<id>.jsonl` (mutant id, key, outcome, UTC time), appended and flushed before the next mutant starts. A last line that does not parse is ignored on reading.
   - The key is a sha256 over a framing in which no two different inputs give the same byte stream (each part length-prefixed or JSON-encoded). It covers:
     - the sorted `/`-separated relative paths and the working-tree bytes of the tracked files under the mutated file's own folder (recursively), under each test file's folder (recursively), every `conftest.py` from the root down to each test file's folder, and the root's `conftest.py`, `pytest.ini`, `pyproject.toml` and `setup.cfg` where present;
     - the mutated file's relative path, the mutant's `tests`, its `pairs`, its `expect_fail`, and whether it carries `expect: survive`.
   - Untracked files (`.env` and the `untracked` list included) never enter the key.
   - On a later run, a mutant whose key equals that of a recorded `killed` line is skipped and listed `killed (cached <time>)`. The latest line for one mutant id and key decides. Every survived, not-applied or errored mutant runs again.
   - `--all` runs every mutant and appends fresh lines.
   - A run stopped at the launcher's limit, by `bridge-stop.py` or by a dropped session keeps every line it flushed, and its relaunch runs only the mutants not kept as killed.

8. **`--checkpoint <commit>` (Done when (c)).**
   - A commit that begins with `-` or does not resolve (`rev-parse --verify <commit>^{commit}`) is refused with exit 2.
   - The copy is built from `git archive <commit>`, run in the Workspace. No archive member is written outside `mutation-run-<id>/`.
   - The working tree's version of each `new_tests` file (the file part of an id) is copied over it, with the root `.env` and the `untracked` paths as in a normal run.
   - Requirement 5's check runs on that tree. Then only the listed new tests run there.
   - Each test that passes is listed as passing on the old code. Each that fails to collect there, for example by importing a module the increment added, is listed `not run`, neither a pass nor a failure. Each that fails is listed as failing.
   - Nothing else runs and nothing is cached in that mode.

9. **Summary and exit codes (Done when (c), (S5), (S6)).**
   - The summary on stdout lists every mutant with its outcome and whether it ran or was cached. Then it gives the counts: run, cached, killed, survived, not applied, error, expected to survive.
   - Normal mode exits, in this precedence:
     - 3 when any mutant is `error`;
     - else 1 when any mutant survived, was not applied, or was `expect: survive` and killed (cached or run);
     - else 0.
   - `--checkpoint` mode exits 4 when any listed test passed, else 0.
   - Both modes exit 2 for a malformed file, a refused path or argument, a refused resolution check, or `--all` with `--checkpoint`. Argparse's own usage error is 2 too.
   - Any exception the program did not expect, in either mode, is caught at the top: one line on stderr beginning `mutation-run: internal error - `, then exit 3. It writes no cache line for the mutant in progress and removes `mutation-run-<id>/` where it can.

10. **The command reference.** `"mutation-run.py"` joins `ARGPARSE` in `tests/test_dump_cli.py` (that line only). `python tools/dump-cli.py` regenerates `docs/cli-reference.json` and `docs/CLI_REFERENCE.md`, and `--check` passes.

11. **The tests: `tests/test_mutation_run.py` (Done when (d)).**
   - The tests run on fixture packages, tests and git repositories built in the test under `tmp_path`, laid out as `<tmp>/<project>/Workspace`. They never use this Workspace's own files as a fixture.
   - Each test's docstring names `R-041` and the Done-when clause it enforces, for example `R-041, TASK-031 Done when (c): ...`.
   - Every case below has its own test, or its own clearly named part of one:
     - a first run kills and records;
     - a run with nothing changed runs no mutant;
     - a change to a mutated file reruns only that file's mutants;
     - each of these reruns the mutants it keys: a change to a named test file, to a `conftest.py` on its path, to a sibling of the mutated file, or to the root's `pytest.ini`, and a change to a mutant's expected test ids or to its `expect: survive` flag;
     - a survived mutant reruns every time;
     - two mutants of one file whose old texts both match the original are each applied to the original;
     - a CRLF fixture's mutant is killed;
     - a test reading the root `.env` and one reading a listed untracked fixture run in the copy;
     - a crash is `error` with exit 3, never a kill, and outranks a survived mutant's 1. An example of a crash is a mutant that ends the test process before pytest reports;
     - a mutant that makes the code loop forever is `error` (`timed out`) under a short `--mutant-timeout` (for example 5), exit 3, the run then going on to the next mutant, and no process of its tree left running after the program ends (S7);
     - a test not expected to fail that fails is `error`;
     - an equivalent mutant is reported apart, and a killed one gives exit 1;
     - `--all` reruns all;
     - a run killed after N mutants keeps N lines; a torn last line is ignored; the relaunch runs only the rest;
     - `--checkpoint` lists a new test that passes on the old code with exit 4, lists one importing a module absent at the checkpoint as `not run`, runs a listed new test reading the root `.env`, and refuses a listed file the commit holds with exit 2;
     - the tracked tree is byte-identical after a run, and after the killed run;
     - an old text not found is `not applied`, with exit 1;
     - a package resolving outside the scratch tree is refused with exit 2 and nothing cached, in `--checkpoint` mode too;
     - an editable install of the fixture package, flat and under `src/`, is overridden by the copy and runs;
     - on Windows, the test process the program starts reports no console window (`PRINT_WINDOW`: window 0, and the program's own process not on the child's console), skipped elsewhere with the reason;
     - a malformed file exits 2.
   - Beyond (d), these cases are tested too:
     - each refusal of Requirement 1 (absolute, `..`, untracked mutated or test file, linked untracked path, bad file name);
     - the scratch refusals of Requirement 2 (inside, containing, through a link);
     - the default scratch folder lies under the tests' temporary home;
     - `--all` with `--checkpoint` exits 2;
     - an internal error (for example, the program loaded in-process with `conftest.load_program("mutation-run")` and one of its functions replaced by one that raises) exits 3, and never 0, 1 or 2.
   - The killed-run case stops the whole process tree: on Windows a parent's kill alone leaves its children running (KP-056). For example, the run goes through `bridge-run.py --limit` with the program copied to the temporary home's `~/.claude/cursor-bridge/mutation-run.py`, or the tree is ended with `taskkill /T /F` started windowless. Nothing it started outlives the test, and its pipes are closed.
   - The editable install is simulated without touching any real environment. For example, use a virtual environment the test creates under `tmp_path` (`python -m venv --without-pip --system-site-packages`, plus a `.pth` naming the original source folder) and run the program with that interpreter. Never use `pip` into this Workspace's or the user's environment, and use no network. If the interpreter running the suite cannot provide pytest to such an environment, stop and report it rather than weakening the case.
   - **Time ceilings.** A test that starts no process finishes within 10 s. A test that starts the program, and so pytest, finishes within 60 s. The two editable-install cases, which create a virtual environment, finish within 120 s. Every `subprocess.run` or `communicate` in the tests carries a `timeout` no larger than its test's ceiling. Report each test's duration from `--durations=0`.

## Acceptance criteria

- [ ] `python -m pytest tests/test_mutation_run.py -q -p no:cacheprovider --durations=0` passes, and every duration is within its ceiling (Requirement 11). The report quotes the summary line and the durations table.
- [ ] Every case of Done when (d) and of Requirement 11 has a test whose docstring names `R-041` and its clause.
- [ ] `python -m pytest tests/test_dump_cli.py tests/test_tests_windowless.py tests/test_bridge_run_driver.py -q -p no:cacheprovider` passes.
- [ ] `python -m pytest tests -q` passes except the install-stamp tests that compare `bridge/` with `MANIFEST.json`. Those fail on the new file until the supervisor regenerates the manifest, and each is reported by its test id as "MANIFEST.json not regenerated (expected)". Any other failure is a defect.
- [ ] `python tools/dump-cli.py --check` exits 0 after `python tools/dump-cli.py`. `docs/CLI_REFERENCE.md` shows `mutation-run.py` with its options and its description naming the exit codes.
- [ ] `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge/mutation-run.py` prints `0 FAIL`.
- [ ] The program is ASCII only. The exit codes follow Requirement 9's precedence. An internal error exits 3.
- [ ] After every test, the fixture's tracked tree is byte-identical and the program has written nothing in the fixture Workspace but `run/supervisor/mutation-cache/`.
- [ ] `git status --porcelain` shows no changed or new file outside Scope, and `git diff -- tests/test_dump_cli.py` shows the one `ARGPARSE` change.
- [ ] R-041 is fully met by the program, with no stand-in, placeholder or "arrives later" text. The loop's use of it is TASK-030's and is not asked here.

## Constraints

- Do not add dependencies: the standard library and pytest only.
- Do not read or write any file outside this workspace (the folder you were started in). Everything you need is inside it, and everything you produce goes inside it. The only exceptions are temporary folders: pytest's `tmp_path` and `home_of_the_tests`, and, for a by-hand run, a temporary home and fixture project that you create and remove.
- If the brief, the rules or the tooling got in your way, append one dated line describing it to `docs/BUILDER_NOTES.md`. That covers an instruction that contradicted another, a check that fired wrongly, or a step that cost time for no reason. Do not try to fix the tooling. Do the same for anything you learned about a defect or a pitfall, such as a cause you found or a platform quirk that cost you a round: one dated line, so the supervisor can carry it forward.
- In any Markdown you write, never break a line inside a paragraph or a list item; one paragraph is one line. Line breaks only between blocks.
- This increment talks to no external service. No test uses the network.
- Any console process your code launches on Windows is created windowless (`creationflags=subprocess.CREATE_NO_WINDOW` in Python, `0` on other platforms). Capturing output does not prevent the window. The program has no `windowless: visible-ok` exemption. In `tests/test_mutation_run.py`, respect the scan described in Context.
- Never start a server, a watcher or a daemon that outlives a test. A test that starts the program waits for it, or stops its whole tree in a `finally`.
- Do not refactor code outside the scope, even if it looks wrong. Report it instead.
- Never run the product, a migration, a seed or a test against the owner's live data. Never run `mutation-run.py` with this Workspace or a real project as its working folder. Never touch the real `~/.cursor-bridge/` or `~/.claude/`. A by-hand run outside pytest sets `HOME` and `USERPROFILE` to a temporary folder.
- No value in this increment is marked as the owner's. The exit codes 2, 3 and 4 and the cache path are the plan's. The time ceilings and `--mutant-timeout`'s default of 900 s are this brief's.
- Follow the bridge's program conventions: the shebang, the module docstring, ASCII text, a top-level `build_parser()`, `NO_WINDOW` as a module constant, git through one helper as in `stage-diff.py`, messages prefixed `mutation-run: `, and the `__main__` block's stream reconfiguration as in `bridge-run.py`.
- These git commands are not yours to run: `commit`, `push`, `switch`, `checkout`, `merge`, `rebase`, `reset`, `stash`, `branch -d`, `worktree`, and `add`, since you stage nothing in this Workspace. In this Workspace you read with `git status`, `git diff`, `git show` and `git log` only. The tests' own fixture repositories under `tmp_path` may use any git command.
- Numbers are parsed with the language's own parser: JSON with `json`, and pytest's counts if you read them with `int`. No number is read by slicing a string. A cache line whose fields do not parse is ignored like a torn line.
- An increment that starts a process meets every point of this checklist. The process is windowless. It is stopped in a `finally` or a fixture's teardown, and its whole tree with it. Nothing it started outlives the test or the command. Its output pipes are closed or drained.
- **Mutation check, by hand, in your own run.** Once your tests pass, record the sha256 of `bridge/cursor-bridge/mutation-run.py`: `python -c "import hashlib; print(hashlib.sha256(open('bridge/cursor-bridge/mutation-run.py','rb').read()).hexdigest())"`. The file is untracked, so `git diff` cannot show its restoration. Then apply each mutant below in place, one at a time. For each one, run `python -m pytest tests/test_mutation_run.py -q -p no:cacheprovider -x`, restore the code exactly, and confirm that the sha256 equals the recorded one. Write no mutation script, and leave nothing of it in the diff. The supervisor's own driver runs after your run. For each mutant, report what you changed, the test that caught it (or that none did), and pytest's summary line.
  1. The key leaves out the `expect: survive` flag.
  2. A mutant counts as killed when any test FAILED, expected or not.
  3. Exit 1 is checked before exit 3.
  4. The top-level handler of an unexpected exception returns 1.
  5. `PYTHONPATH` is not set for the test run.
  6. The original bytes are not written back between mutants, so mutants accumulate.
  7. The `creationflags` argument is removed from the test run's launch. Expected on Windows: the console-window test fails.
  8. The old text is matched without the file's own newlines.
  9. In `--checkpoint` mode, a passing new test does not set exit 4.
  10. A timed-out mutant is recorded `killed` instead of `error`.
- Prefer reuse over new code: `bridge_env.real_home`, `bridge_env.is_link`, the standard library's `json`, `hashlib`, `shutil`, `tarfile` and `subprocess`, and pytest's own `-rA` report and plugin hooks. Write the minimum that meets the acceptance criteria. This never overrides a security requirement stated above.
- **Verification commands.** Run each from the Workspace folder (the folder you were started in), in this order:
  1. `python -m pytest tests/test_mutation_run.py -q -p no:cacheprovider --durations=0`
  2. `python tools/dump-cli.py`, then `python tools/dump-cli.py --check`
  3. `python -m pytest tests/test_dump_cli.py tests/test_tests_windowless.py tests/test_bridge_run_driver.py -q -p no:cacheprovider`
  4. `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge/mutation-run.py`
  5. `python -c "d=open('bridge/cursor-bridge/mutation-run.py','rb').read(); print(all(b < 128 for b in d))"` (expected: `True`)
  6. The mutation check above. Once the code is restored, run command 1 again.
  7. `python -m pytest tests -q`: the full suite takes about ten minutes. Let it finish; do not stop it early.
  8. `git status --porcelain` and `git diff -- tests/test_dump_cli.py`
  9. After the runs, on Windows: `tasklist /FI "IMAGENAME eq python.exe"`. Say whether any process the tests started is still running.

## Done

Your report is the file `handoff/TASK-031-r1-report.md`. Write it as you go: what you did, what you changed, what you ran and what it printed, and what you could not do. That way nothing of it is lost if your run ends early. Never paste a computer path or a user name into it. Write `<temporary folder>`, `<home>` or `<Workspace>` instead.

State only what you ran. For every run you report, quote pytest's own output as it printed it, at least the summary line. Do not round, summarise or reconstruct a figure. The supervisor and both reviewers re-run every command and check every claim, and a claim they cannot reproduce rejects the round.

When you finish, the report holds:
- a list of every file you changed, and only those (`git status` tells you);
- a one-paragraph summary of what you did;
- the mutants file's format as you implemented it, with one example, and the summary's format, for TASK-030's text;
- how pytest named the node ids in the copy (the "to verify" item), and how you handled a tracked path missing from the working tree;
- the quoted output of each verification command, the durations table, the install-stamp failures listed by test id, and the leftover-process check;
- the mutation list: each mutant, what caught it or that nothing did, and pytest's summary line, plus the sha256 confirmation after each restore;
- a section headed exactly `Assumed, not verified`. List every fact this change relies on that neither this brief nor the existing code settled, and that you did not confirm. Examples: that pytest's `-rA` lines name every test of a session that ended at a collection error; that `git archive` applies the same line endings as the working tree; that a POSIX run of the tests behaves as the Windows one; that the plugin's file can shadow no module of a real project. One item per line: what you assumed · why · what would confirm it. If there are none, write `Assumed, not verified: none`. Be specific: "edge cases" or "error handling" is not an item.

Your last message is the summary and the report file's path, and nothing follows it: the supervisor reads only the last message, and a message printed earlier and then followed by more work is lost.
