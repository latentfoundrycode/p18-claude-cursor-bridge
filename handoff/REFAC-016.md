---
record: brief
header: 1
id: REFAC-016
round: 1
satisfies: [R-041, R-090, R-106]
scope: ["bridge/cursor-bridge/mutation-run.py", "bridge/cursor-bridge/MANIFEST.json", "docs/BUILDER_NOTES.md", "handoff/REFAC-016-r1-report.md"]
merge_unit: null
blocking_class: null
---
# REFAC-016: mutation-run.py's run paths, checkpoint test run, path loop, default prefixes and generated path test, each one copy

## Objective
Refactoring - remove duplication / simplify **without any change in behaviour**.

This brief carries five candidates of stage I1's refactoring pass, all in `bridge/cursor-bridge/mutation-run.py` (the editable-install code of TASK-085, R-106), in five named parts. The manifest is regenerated after them. Behaviour stays exactly the same: every line printed to stdout and stderr, every exit code, every file written in the scratch folder and the cache (one exception, named in Part 5: the text of the generated resolution plugin, whose behaviour and output file stay the same), every environment given to a child process, and the order of the entries of every `PYTHONPATH` built (and so of `sys.path` in each child). Line numbers below are as the file stands at `8b03c32` (TASK-087c, the base of branch `refactor/I1`). REFAC-015 (`bridge/cursor-bridge/roster-check.py`) may be committed on this branch before your run: it touches no source file of this brief; if it regenerated `bridge/cursor-bridge/MANIFEST.json`, that change is already committed and your regeneration after your edit covers both. Function names are the anchors; a line number in mutation-run.py that differs from the one given here is a reason to stop only where Requirement 1 says so.

**Part 1: the run paths, set up once.** `main()` sets up the run's paths twice with the same seven lines against `copy_root`, once in checkpoint mode (lines 1848-1854, indented 12 spaces) and once in ordinary mode (lines 1947-1953, indented 8 spaces):

```python
probe_paths = run_interpreter_path_probe(plugin_dir, copy_root, env, timeout_sec)
mapped_all = map_probe_entries(probe_paths, workspace, copy_root)
mapped_active = active_mapped_roots(copy_root, mapped_all)
ir_active = active_import_roots(copy_root, import_roots)
dotted_ps = module_dotted_prefixes(ir_active, mapped_active)
path_kw = dict(
    import_roots_rel=ir_active, mapped_roots_rel=mapped_active, dotted_prefixes=dotted_ps)
```

`probe_paths`, `mapped_all` and `dotted_ps` are used nowhere else in `main()`; `ir_active`, `mapped_active` and `path_kw` are used after both sites (checkpoint: `run_resolution_check(..., **rc_kwargs, **path_kw)` three times and the test loop's `pytest_env` call, lines 1903-1905; ordinary: line 1958, `compute_key(copy_root, m, tracked_set, import_roots, mapped_active)` line 1960, `run_baselines` line 1967-1969 and `run_mutant_tests` lines 2015-2017). The change: one top-level function `run_paths(plugin_dir, copy_root, workspace, import_roots, env, timeout_sec)` whose body is those seven lines in the same order (the same calls with the same arguments, the probe first) and which returns the tuple `(ir_active, mapped_active, path_kw)`, `path_kw` the same dict with the same three keys in the same order. Both sites become one line, `ir_active, mapped_active, path_kw = run_paths(plugin_dir, copy_root, workspace, import_roots, env, timeout_sec)`, at the site's indentation. Each site keeps its position: in checkpoint mode after `archive_checkpoint`, in ordinary mode after `copy_tracked(workspace, copy_root, tracked_list, untracked)`.

**Part 2: the checkpoint test run is run_mutant_tests.** The checkpoint loop in `main()`, lines 1900-1911, re-implements `run_mutant_tests` (line 1710):

```python
                chk_results = os.path.join(plugin_dir, "pytest-outcomes-chk-%d.json" % chk_idx)
                if os.path.isfile(chk_results):
                    os.remove(chk_results)
                run_env = pytest_env(
                    plugin_dir, copy_root, env, chk_results,
                    import_roots_rel=ir_active, mapped_roots_rel=mapped_active)
                cfg = pytest_config_argv(plugin_dir, copy_root)
                rc, out, err, timed = run_process(
                    interpreter_argv() + ["-m", "pytest", "-p", OUTCOMES_PLUGIN_MOD, "-p", "no:cacheprovider"]
                    + cfg + [item],
                    run_env, copy_root, timeout_sec)
                data = read_pytest_results(chk_results)
```

```python
def run_mutant_tests(plugin_dir, copy_root, tests, env, timeout_sec, results_path,
                     import_roots_rel=(), mapped_roots_rel=()):
    if os.path.isfile(results_path):
        os.remove(results_path)
    run_env = pytest_env(
        plugin_dir, copy_root, env, results_path,
        import_roots_rel=import_roots_rel, mapped_roots_rel=mapped_roots_rel)
    cfg = pytest_config_argv(plugin_dir, copy_root)
    argv = interpreter_argv() + ["-m", "pytest", "-p", OUTCOMES_PLUGIN_MOD, "-p", "no:cacheprovider"] + cfg + tests
    rc, out, err, timed = run_process(argv, run_env, copy_root, timeout_sec)
    data = read_pytest_results(results_path)
    return rc, out, err, timed, run_process_still_alive_after_timeout(), data
```

The same steps in the same order with `tests = [item]`; the only extra is the fifth value, `run_process_still_alive_after_timeout()` (line 731), a plain getter with no side effect: `return _last_run_process_still_alive`. After line 1911 the loop reads only `timed` and `data` (lines 1912-1943); `rc`, `out` and `err` are not read again before `return 4 if any_pass else 0` (line 1944). The change: the `chk_results = ...` line stays; the lines from `if os.path.isfile(chk_results):` through `data = read_pytest_results(chk_results)` become one call, `run_mutant_tests(plugin_dir, copy_root, [item], env, timeout_sec, chk_results, import_roots_rel=ir_active, mapped_roots_rel=mapped_active)`, unpacked into six names, the still-alive value ignored (the checkpoint loop does not read it today and must not start to). No test replaces `run_mutant_tests`, `run_process`, `pytest_env` or `read_pytest_results` (Requirement 1 checks it): the tests' monkeypatches of mutation-run are `git` (tests/test_mutation_run.py:275), `kill_tree` (tests/test_mutation_run.py:1410, :1487), `git_try` (tests/test_bug032.py:254) and `bridge_env.is_link` (tests/test_mutation_run_supervisor.py:1244).

**Part 3: one loop in pytest_env.** `pytest_env` (line 1429) runs the same loop twice, lines 1432-1450:

```python
    for rel in import_roots_rel:
        p = os.path.join(tree_root, rel.replace("/", os.sep))
        if os.path.isdir(p):
            ap = os.path.abspath(p)
            nk = os.path.normcase(ap)
            if nk not in seen:
                parts.append(ap)
                seen.add(nk)
    for rel in mapped_roots_rel:
        if rel == ".":
            p = tree_root
        else:
            p = os.path.join(tree_root, rel.replace("/", os.sep))
        if os.path.isdir(p):
            ap = os.path.abspath(p)
            nk = os.path.normcase(ap)
            if nk not in seen:
                parts.append(ap)
                seen.add(nk)
```

The change: one loop over `list(import_roots_rel) + list(mapped_roots_rel)` with the first loop's body, so the entries keep their order (import roots first, then mapped roots) and share the one `seen` set as today. The mapped loop's `rel == "."` branch is dropped, on this ground, which you verify before you edit (Requirement 1): for `rel == "."`, `os.path.join(tree_root, ".")` is a directory exactly when `tree_root` is, and `os.path.abspath` normalizes the `.` component away (`posixpath.abspath` through `normpath`, `ntpath.abspath` through the full-path call), so `ap` and `nk` are the same as from `tree_root`. If your check prints anything other than `True True True`, stop, change nothing, and report it. Everything else in `pytest_env` (the `parts = [plugin_dir]` start, the tree root appended last when not seen, the three environment keys) is unchanged. The callers pass lists or the default `()` (`run_interpreter_path_probe` line 342, `run_resolution_check` line 1581, `run_mutant_tests` line 1714); none passes an iterator.

**Part 4: one constant for the default prefixes.** The literal default prefixes appear five times:

- line 271, `module_dotted_prefixes`: `    prefixes = ["", "src/"]` (a list, appended to below);
- line 882, `dotted_module_paths`: `    for prefix in dotted_prefixes or ("", "src/"):`;
- line 1465, `module_file_at_commit`: `    for prefix in dotted_prefixes or ("", "src/"):`;
- line 1552, `checkpoint_collect_refused`: `    prefixes = dotted_prefixes or ("", "src/")`;
- line 1573, `run_resolution_check`: `    dp = dotted_prefixes or ("", "src/")` (passed on to `write_resolution_plugin`, which writes `json.dumps(list(dotted_prefixes))`, to `checkpoint_collect_refused` and to `dotted_module_paths`).

The change: one module-level constant `DEFAULT_DOTTED_PREFIXES = ("", "src/")`, placed among the module's constants near the top of the file (lines 50-61), not inside a function. Line 271 becomes `prefixes = list(DEFAULT_DOTTED_PREFIXES)` (a fresh list on every call, since the function appends to it; the constant itself is never mutated); the other four sites read `DEFAULT_DOTTED_PREFIXES` in place of the tuple literal, so each keeps its type (tuple there, list at line 271).

**Part 5: one path test in the generated plugin.** `write_resolution_plugin` (line 1294) writes a pytest plugin from the code string that starts at line 1300; that string defines two functions with identical bodies, lines 1357-1361:

```python
def _in_workspace(ap, nw, nwr):
    return ap == nw or ap.startswith(nw + os.sep) or ap == nwr or ap.startswith(nwr + os.sep)

def _in_copy(ap, nc, ncr):
    return ap == nc or ap.startswith(nc + os.sep) or ap == ncr or ap.startswith(ncr + os.sep)
```

called four times in the same string's `pytest_sessionfinish`: line 1391 `        if _in_copy(ap, nc, ncr):`, line 1397 `        if _in_workspace(ap, nw, nwr):`, line 1405 `        if not _in_workspace(af, nw, nwr):`, line 1407 `        if _in_copy(af, nc, ncr):`. The change: in the generated text, the two definitions become one, `_under(ap, a, b)`, whose body is the same expression with `a` and `b` (`ap == a or ap.startswith(a + os.sep) or ap == b or ap.startswith(b + os.sep)`), in the place of the two; the four calls become `_under(ap, nc, ncr)`, `_under(ap, nw, nwr)`, `not _under(af, nw, nwr)` and `_under(af, nc, ncr)`, each keeping its argument order. The code string is a `%`-formatted, non-raw, triple-single-quoted literal: the new text adds no `%`, no backslash and no `'''`. The generated file `_mutation_resolution_check.py` in the scratch folder is the one file whose bytes change; it is written and removed by each run, no test reads its text (`git grep` finds `_in_workspace` nowhere else in `bridge/` or `tests/`; `tests/test_improve_mutation_editable.py:399` defines an unrelated `_in_copy` inside a fixture's own text, which you do not touch), and the JSON it writes, `_resolution_out.json`, has the same content.

**And the manifest:** `bridge/cursor-bridge/MANIFEST.json` regenerated once, after your last source edit, by `python tools/make-manifest.py`. The version stays `2026.11.24a` (the newest `## ` entry of `bridge/cursor-bridge/CHANGELOG.md`, which make-manifest picks, and today's content of `bridge/cursor-bridge/VERSION`).

Satisfies: no new requirement. This keeps as they are R-041 (mutation reruns skip only what is unchanged: every mutation run is a run of `mutation-run.py` on a mutant list the supervisor writes, with its cache key, its per-mutant bound and its `--checkpoint` run of the new tests; TASK-031), R-090 (a mutation run matches its ids and proves its baseline: each distinct tests list runs once on the unmutated copy before the mutant loop; TASK-070) and R-106 (the mutation engine runs on a project installed in editable form: it reads the interpreter's import path in the run's environment, maps every entry inside the Workspace to the copy and puts those folders first on the run's `PYTHONPATH`, and its resolution check refuses a module loaded from the Workspace; TASK-085).

## Scope
Files and directories you may create or modify:
- bridge/cursor-bridge/mutation-run.py
- bridge/cursor-bridge/MANIFEST.json
- docs/BUILDER_NOTES.md
- handoff/REFAC-016-r1-report.md

Do not modify anything else. `docs/BUILDER_NOTES.md` is append only.

## Out of scope
- .env and anything under secrets/
- CI configuration, pre-commit configuration, anything under `tools/` (you run `tools/make-manifest.py` and `tools/dump-cli.py`; you do not edit them)
- docs/ and handoff/, except the files the Scope section names; `docs/diagrams/` included (this change needs no diagram change, see Diagrams); `docs/CLI_REFERENCE.md` and `docs/cli-reference.json` included (this change touches neither `build_parser` nor the module docstring)
- every file under `tests/`, `tests/fixtures/` included: no test file or fixture may be edited, renamed or created (the supervisor's purity check, `refactor-check.py main --max-lines 400`, fails the branch on any test edit). If the working tree shows a test file modified before your run, leave it exactly as it is
- `bridge/cursor-bridge/VERSION`: its content must still read `2026.11.24a` after make-manifest rewrites it; make-manifest writes it with an LF line ending; report what `git diff --numstat -- bridge/cursor-bridge/VERSION` prints, do not try to restore the file
- everything under `run/`: the supervisor's and the launcher's, gitignored; none of this brief's commands writes a file there, and you write none
- `docs/CHANGES.md` and `bridge/cursor-bridge/CHANGELOG.md`: a refactoring has no change entry
- `bridge/cursor-bridge/roster-check.py` (REFAC-015's) and every other file under `bridge/`
- in mutation-run.py, every line but those the five parts name: the two seven-line sites in `main()` and the added `run_paths`; the checkpoint loop's lines 1901-1911; `pytest_env`'s two loops; the five prefix sites and the added constant; the generated text's two definitions and four calls. `OUTCOMES_PLUGIN_CODE`, `run_baselines`, `run_resolution_check`'s other lines, the module docstring and `build_parser` stay exactly as they are

## Context
**What the code is today** (`8b03c32`). `bridge/cursor-bridge/mutation-run.py` has CRLF line endings on every line; keep them, and add no trailing whitespace. The generated plugin text is written with `newline="\n"` (line 1424), which you do not change. The module defines no `__all__`; no other program under `bridge/` imports mutation-run (it is a standalone program, run as `python mutation-run.py <mutants file> ...`); the tests load it in process by file path (`load_program("mutation-run")`, the `program` fixture) or run it as a child process.

**How the tests reach this code.** These covering tests must stay green, unedited:
- `tests/test_improve_mutation_editable.py` (TASK-085, R-106): editable installs imitated by `.pth` path entries and a meta-path finder in a scratch virtual environment; mutants under `sdk/src/pkg/`, import roots, the resolution check's refusals, and `--checkpoint` runs (Parts 1, 3, 4, 5).
- `tests/test_mutation_run.py` (TASK-031, R-041): the cache, the copy, untracked files, the per-mutant bound and the still-alive path (`kill_tree` replaced so a pytest outlives the bound), `--checkpoint` runs (Parts 1, 2, 3, 4).
- `tests/test_mutation_run_supervisor.py` (TASK-031, R-041): the supervisor's cases, `--checkpoint` runs and `run_process`'s pipe bound driven in a child (Parts 1, 2).
- `tests/test_program_mutation_baseline.py` (TASK-070, R-090): the baseline lists through `run_baselines` and `run_mutant_tests`, and `--checkpoint` (Parts 1, 2).
- `tests/test_bug032.py` (BUG-032, R-041): `--checkpoint` runs whose copied conftest fails to load, the per-file resolution checks, `not run` lines for blocked tests and the judged clear files (Parts 1, 2); it also holds launcher and guard cases that do not reach mutation-run.

There is no other `tests/test_mutation*.py`. Some tests take tens of seconds (the bound's 30-second waits); the whole command may take several minutes. Some cases may be skipped on Windows; the skip count must be the same before and after.

**The expected count.** No supervisor baseline count is given for this command. Your before-edit run is the baseline, and the after-edit run must match it (the same count passed, none failed, the same count skipped).

**The manifest.** `MANIFEST.json` holds a normalized sha256 (CRLF folded to LF, BOM dropped) of every file under `bridge/`. After your edit it is stale for mutation-run.py; `python tools/make-manifest.py` rewrites `VERSION` (to `2026.11.24a` and a line feed) and the manifest, whose `generated` stamp changes, and prints `make-manifest: version 2026.11.24a, <n> files hashed, VERSION + MANIFEST.json written`. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` then compares the tree with it and is expected to print `RESULT: SOURCES MATCH bridge 2026.11.24a`. `python tools/dump-cli.py --check` is expected to print nothing and exit 0 (it prints the path of each reference file that differs and exits 1; `tests/test_dump_cli.py` lists mutation-run.py among its argparse programs); if it prints a path, stop and report it, since this change must not alter the command reference.

**Security context.** mutation-run.py confines a test run to a scratch copy: the import path it builds puts the copy's folders first so that no module of the Workspace is loaded, and the generated resolution plugin refuses a module resolving outside the copy or a Workspace path ahead of the copy (R-106). The trust boundaries are the mutants file (supervisor-written, under `run/supervisor/`), the project's own code and conftest files run inside the copy, and the interpreter's import path read by the probe. `.cursor/rules/secure-coding.mdc` is in force for you, and the project's ASVS level is 2 (`docs/INVENTORY.md`, Decisions). This change moves no boundary: every `PYTHONPATH` holds the same entries in the same order, the same paths count as inside the Workspace and inside the copy, and each child runs with the same environment, arguments and bound.

**Development data** (`docs/INVENTORY.md`, Decisions): "Development data: the dev build is the Workspace sources under `bridge/`; a session in the repo always runs the *installed* bridge (`~/.claude`), never the one being edited, and installs reach running projects only through the owner's install run sheet (§15 condition 1, A1a condition 1)". For you: the tests run the Workspace sources against pytest's temporary folders and the repositories and environments they create there. Never run mutation-run.py yourself, against this repository or any other, and never run `bridge-install.py`.

## Diagrams
`docs/diagrams/D-002-components.md`: the element `mutation_run` (`bridge/cursor-bridge/mutation-run.py`), whose one edge is:

```mermaid
    mutation_run --> bridge_env
```

The diagram's note says the `import` lines inside the generated plugins' source strings (`OUTCOMES_PLUGIN_CODE`, `write_resolution_plugin`) are text, not imports; Part 5 adds no import to that text. The change adds no import and no edge, so the diagram does not change. `docs/diagrams/D-004-context-dfd.md` (`p_test_suite`, "Suite or mutation run") draws no flow this change adds or removes. **If the task cannot be done within them, stop and report the conflict (an objection) instead of deviating.**

## Requirements
1. **Checks first, before any edit; paste each command and its output in the report.** From the Workspace root, run:
   - `git grep -n -e "run_interpreter_path_probe(" -e "map_probe_entries(" -e "dotted_ps" -- bridge/cursor-bridge/mutation-run.py`. Expected: the defs of `run_interpreter_path_probe` (341) and `map_probe_entries` (306), and lines 1848, 1849, 1852, 1854, 1947, 1948, 1951, 1953; compare the two seven-line sites (1848-1854 and 1947-1953) and state in the report that they are identical apart from indentation.
   - `git grep -n -w -e run_mutant_tests -e run_process -e pytest_env -e read_pytest_results -e run_process_still_alive_after_timeout -- tests`. Expected: no line that assigns or monkeypatches one of these names on the loaded program (a line that only calls `mod.run_process(...)`, as `tests/test_mutation_run_supervisor.py:511` does, is a call, not a replacement); list each hit in the report.
   - `git grep -n -w -e pytest_env -- bridge/cursor-bridge/mutation-run.py`. Expected: five lines, 342, 1429, 1581, 1714, 1903.
   - `git grep -n -F -e src/ -- bridge/cursor-bridge/mutation-run.py`. Expected: five lines, 271, 882, 1465, 1552, 1573.
   - `git grep -n -w -e _in_workspace -e _in_copy -- bridge tests`. Expected: lines 1357, 1360, 1391, 1397, 1405, 1407 of mutation-run.py, and `tests/test_improve_mutation_editable.py:399:` and `:402:` (the fixture's own text).
   - `git grep -n -w -e run_paths -e DEFAULT_DOTTED_PREFIXES -e _under -- bridge`. Expected: nothing.
   - `python -c "import os; t = os.path.join(os.getcwd(), 'bridge'); print(os.path.abspath(os.path.join(t, '.')) == os.path.abspath(t), os.path.isdir(os.path.join(t, '.')) == os.path.isdir(t), os.path.normcase(os.path.abspath(os.path.join(t, '.'))) == os.path.normcase(os.path.abspath(t)))"`. Expected: `True True True` (Part 3's ground).
   If a check does not hold (another hit, a missing hit, sites that differ, a replacement of one of Part 2's names in a test, a line number other than these, or Part 3's check printing anything but `True True True`), stop, change nothing, and report it.
2. Part 1: `run_paths(plugin_dir, copy_root, workspace, import_roots, env, timeout_sec)` is a top-level function holding the seven lines in their order and returning `(ir_active, mapped_active, path_kw)`; both sites in `main()` are one call each, at their places; nothing else in `main()` changes for this part.
3. Part 2: the checkpoint loop calls `run_mutant_tests(plugin_dir, copy_root, [item], env, timeout_sec, chk_results, import_roots_rel=ir_active, mapped_roots_rel=mapped_active)` and ignores its still-alive value; `chk_results` is built as today; the loop's lines from `if timed or data is None:` on are unchanged.
4. Part 3: `pytest_env` holds one loop over `list(import_roots_rel) + list(mapped_roots_rel)`, without the `"."` branch; its signature and everything else in it are unchanged.
5. Part 4: `DEFAULT_DOTTED_PREFIXES = ("", "src/")` is a module-level constant; line 271 reads `list(DEFAULT_DOTTED_PREFIXES)`; the four other sites read the constant; no tuple or list literal `("", "src/")` / `["", "src/"]` remains.
6. Part 5: the generated text defines `_under(ap, a, b)` in place of `_in_workspace` and `_in_copy`, and its four calls read `_under` with their arguments in today's order; nothing else in the code string changes.
7. No other line changes in mutation-run.py. It keeps CRLF line endings and gains no trailing whitespace. No comment, docstring, alias or import is added; no public signature changes except the added `run_paths` and `DEFAULT_DOTTED_PREFIXES`.
8. After your last source edit, run `python tools/make-manifest.py` once, then the remaining verification commands in the Constraints.

## Acceptance criteria
- [ ] Behaviour is identical: the same lines printed, the same exit codes, the same files written (the generated plugin's text aside, whose output `_resolution_out.json` is the same), the same environment and `PYTHONPATH` entries in the same order for every child, in ordinary and in `--checkpoint` mode.
- [ ] The full test suite passes with the **same** test set (the supervisor's run and CI's, not yours); in your own run the pytest command below passes before and after the edit with the same count passed, none failed, the same count skipped, both summary lines quoted in the report. No test file edited.
- [ ] One copy each: `git grep -n -w -e run_paths -- bridge` prints three lines (the def and two calls, all in mutation-run.py); `git grep -n -e "run_interpreter_path_probe(" -- bridge/cursor-bridge/mutation-run.py` prints two lines (the def and the call in `run_paths`); `git grep -n -w -e pytest_env -- bridge/cursor-bridge/mutation-run.py` prints four lines (342, the def, `run_resolution_check`'s, `run_mutant_tests`'), where it printed five; `git grep -n -w -e OUTCOMES_PLUGIN_MOD -- bridge/cursor-bridge/mutation-run.py` prints two lines (the constant and `run_mutant_tests`'), where it printed three; `git grep -n -F -e "os.path.normcase(ap)" -- bridge/cursor-bridge/mutation-run.py` prints one line, where it printed two; `git grep -n -F -e src/ -- bridge/cursor-bridge/mutation-run.py` prints one line, the constant; `git grep -n -w -e DEFAULT_DOTTED_PREFIXES -- bridge` prints six lines, all in mutation-run.py; `git grep -n -w -e _in_workspace -e _in_copy -- bridge` prints nothing; `git grep -n -w -e _under -- bridge` prints five lines, all in mutation-run.py (the generated def and four calls).
- [ ] `python tools/dump-cli.py --check` exits 0 with no output.
- [ ] `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` prints `RESULT: SOURCES MATCH bridge 2026.11.24a`.
- [ ] `git diff --numstat -- bridge/cursor-bridge/VERSION` prints nothing (if it prints a line, it is quoted in the report and the file's content is shown to read `2026.11.24a`).
- [ ] `git diff --stat` shows only `bridge/cursor-bridge/mutation-run.py`, `bridge/cursor-bridge/MANIFEST.json`, and if written `docs/BUILDER_NOTES.md` (the report is a new file); `docs/CHANGES.md`, `bridge/cursor-bridge/CHANGELOG.md` and every file under `tests/` unchanged; no mutation script in the diff.

## Constraints
- Do not add dependencies.
- Do not read or write any file outside this workspace (the folder you were started in). Everything you need is inside it; everything you produce goes inside it. Run the Workspace copies of the tools, as the commands below do, never a copy under a home folder.
- If the brief, the rules, or the tooling got in your way (an instruction that contradicted another, a check that fired wrongly, a step that cost time for no reason), append one dated line describing it to `docs/BUILDER_NOTES.md`. Do not try to fix the tooling. Do the same for anything you learned about a defect or a pitfall (a cause you found, a platform quirk that cost you a round): one dated line, so the supervisor can carry it forward.
- In any Markdown you write, never break a line inside a paragraph or a list item; one paragraph is one line. Line breaks only between blocks.
- This increment talks to no external service; the tests make no network call.
- Any console process your code launches on Windows is created windowless (`creationflags=subprocess.CREATE_NO_WINDOW` in Python, `0` on other platforms; `windowsHide: true` in Node). Capturing output does not prevent the window. A window is allowed only when it serves the user (they watch it or type into it); then write the reason at the call site as `windowless: visible-ok <reason>`. A spawn that needs a process group for a `CTRL_BREAK` stop is hidden only with a test of the stop path. This change adds no launch: the checkpoint run's child is started by the same `run_process` (with `creationflags=NO_WINDOW`) as today, and `run_process` and `kill_tree` stay as they are.
- Never start a server, a watcher or a daemon that outlives a test: a test that needs the product running starts it through the test framework's own fixture and stops it there. A server left running keeps your run from ending (plan 10.3, release A2).
- Do not refactor code outside the scope, even if it looks wrong.
- Never run the product, a migration, a seed or a test against the owner's live data. A development build uses the development data the design names (the inventory's `Development data` decision, stated in Context) and refuses the installed product's data. Here that means the Workspace sources and pytest's temporary folders only.
- No value in this task is marked as the owner's.
- Follow existing conventions in the files you touch.
- These git commands are not yours to run: `commit`, `push`, `switch`, `checkout`, `merge`, `rebase`, `reset`, `stash`, `branch -d`, `worktree`; you read with `git status`, `git diff`, `git grep`, `git rev-parse` and `git log` only.
- Numbers from text, a file, a reply or an environment variable are parsed with the language's own parser, never by slicing or splitting a string. This change parses no number.
- An increment that starts a process meets the process checklist (windowless, stopped in a `finally` or a fixture's teardown with its whole tree, nothing outlives the test or the command, a browser on Windows launched attached, pipes closed or drained). This change starts no new process; the existing children keep today's bound, kill and pipe handling.
- Every verification command is written here in full. Run exactly these, each from the Workspace root (the folder you were started in), each in the foreground, never in the background; run pytest directly as written, never through a launcher:
  - At the start: `git status --short` and `git rev-parse HEAD`, pasted into the report.
  - The seven commands of Requirement 1, before any edit.
  - Before the edit, and again after the last edit: `python -m pytest -p no:cacheprovider -q -rs tests/test_improve_mutation_editable.py tests/test_mutation_run.py tests/test_mutation_run_supervisor.py tests/test_program_mutation_baseline.py tests/test_bug032.py`
  - After the last source edit, in this order: `python tools/make-manifest.py`; `python tools/dump-cli.py --check`; `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`; `git diff --numstat -- bridge/cursor-bridge/VERSION`; `git diff --numstat -- bridge/cursor-bridge/mutation-run.py`; the nine `git grep` commands of the third acceptance criterion.
  - At the end: `git status --short`, `git diff --stat` and `git rev-parse HEAD`, pasted into the report.
  - Do not run the whole `tests/` tree or any other test file; the supervisor runs the full suite and the purity check after your run. If a test fails before your edit, stop and report it; do not fix it.
- Mutation checking is the supervisor's in this task. Run no mutation, write no mutation script, and let none land in the diff.
- Prefer reuse over new code and write the minimum that meets the acceptance criteria (the frozen `minimal-code.mdc` is in force). This never overrides a security, observability, or accessibility requirement stated above.
- **Refactoring constraints.** Do not edit any test file. Do not add an entry to `docs/CHANGES.md`. Do not "improve" behaviour, messages, edge cases, or defaults you notice along the way (for example the checkpoint loop not reading the still-alive value, `active_mapped_roots` skipping `"."`, or the two path tests in `run_resolution_check` that compare with `startswith(croot_abs)`); report them in your summary instead. Do not introduce an abstraction beyond the two added names and the generated `_under`: no further helper, parameter, alias or comment.
- **No computer path in the report.** Where quoted output holds the repository's absolute folder, write `<Workspace>` in its place; paste no other absolute path of this machine.

## Done
Your report is the file `handoff/REFAC-016-r1-report.md`, which you write as you go (what you did, what you changed, what you ran and what it printed, what you could not do) so that nothing of it is lost when your run ends early. When you finish, it holds:
- a list of every file you changed;
- a one-paragraph summary of what you did, part by part;
- the Requirement 1 commands with their output as the evidence, your comparison of the two seven-line sites, and the list of test hits for Part 2's names;
- the before and after outputs of the pytest command, with both summary lines;
- the outputs of make-manifest, dump-cli `--check`, bridge-check, the two `git diff --numstat` commands and the third acceptance criterion's nine `git grep` commands, each line that shows the result quoted (an empty output written as such);
- `git status --short`, `git diff --stat` and `git rev-parse HEAD` at the start and at the end, and whether the working tree held uncommitted changes then;
- one sentence stating why the behaviour is identical;
- anything you noticed but did not change (per the refactoring constraints);
- a final section headed exactly `Assumed, not verified`: every fact this change relies on that neither this brief nor the existing code settled, and that you did not confirm (an ambiguous requirement you resolved one way, a platform or library behaviour you expected, a value you chose). One item per line: what you assumed · why · what would confirm it. If there are none, write `Assumed, not verified: none`. Be specific: "edge cases" or "error handling" is not an item.

Every command you ran is quoted in the report with the lines it printed, verbatim (with `<Workspace>` in place of the repository's folder), in a fenced block; a count, or a claim that a check passed, quotes the output line that shows it. A command you did not run is written `not run`, never described as run. Run this brief's pytest command once more after your last edit, and write the report's results after that run, naming the commit its counts belong to (`git rev-parse HEAD`) and whether the working tree then held uncommitted changes (`git status --short`).

Your last message is the summary and the report file's path, and nothing follows it: the supervisor reads only the last message, and a message printed earlier and then followed by more work is lost.
