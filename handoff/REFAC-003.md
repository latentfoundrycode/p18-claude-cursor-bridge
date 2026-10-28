# REFAC-003: pace-report.py prints the over-ceiling and stage-review lines from one loop

## Objective
Refactoring — remove duplication / simplify **without any change in behaviour**.

The pace report (`bridge/cursor-bridge/pace-report.py`, the supervisor's read-only weekly pace tables) ends each project section by listing the IDs over the review ceiling and then the stage reviews (`STAGE-<name>`). The function `def _project_section(name, root, weeks, ceiling, with_tokens, home, er):` collects these in two lists, `over` and `stage` (lines 815-838), and then prints them with two loops whose bodies are identical line for line (lines 840-853). This is refactor-scout's candidate 6 for stage B5 (COVERED: the lines are exercised by `tests/test_pace_report.py` and `tests/test_task033_supervisor*.py`).

Site: `bridge/cursor-bridge/pace-report.py`, lines 840-853, which today read exactly:

```python
    for ident, rnd in over:
        lifts = _lift_map(ws, common, ident)
        parts = ["%s: %d rounds" % (_ascii_name(ident), rnd)]
        for r in range(ceiling + 1, rnd + 1):
            lv = lifts.get(r, "unknown")
            parts.append("r%d %s" % (r, lv))
        lines.append("- " + "; ".join(parts))
    for ident, rnd in stage:
        lifts = _lift_map(ws, common, ident)
        parts = ["%s: %d rounds" % (_ascii_name(ident), rnd)]
        for r in range(ceiling + 1, rnd + 1):
            lv = lifts.get(r, "unknown")
            parts.append("r%d %s" % (r, lv))
        lines.append("- " + "; ".join(parts))
```

Proposed shape: one loop, `for ident, rnd in over + stage:`, with the six-line body written once, unchanged, at the same indentation. The printed lines keep exactly the same order: every `over` line in its current order, then every `stage` line in its current order.

Callers to update: none. The two loops are local to `_project_section`; no other code reads them, and `over` and `stage` are not used after line 853.

## Scope
Files and directories you may create or modify:
- bridge/cursor-bridge/pace-report.py (lines 840-853 only)
- docs/BUILDER_NOTES.md (append only)
- handoff/REFAC-003-r1-report.md

Do not modify anything else.

## Out of scope
- .env and anything under secrets/
- CI configuration, pre-commit configuration, anything under `tools/`. In particular, do **not** run `tools/make-manifest.py`, and do not run `tools/dump-cli.py` without `--check`
- docs/ and handoff/, except the files the Scope section names
- every file under `tests/`: no test file may be edited, renamed or created. This branch already carries the supervisor's tests-lane commit (`4a25d36 supervisor: REFAC-B5 tests lane: ...`), and you must not touch it
- `bridge/cursor-bridge/MANIFEST.json` and `bridge/cursor-bridge/VERSION`: the supervisor regenerates the manifest after your run
- `docs/CHANGES.md` and `bridge/cursor-bridge/CHANGELOG.md`: a refactoring has no change entry
- `docs/cli-reference.json` and `docs/CLI_REFERENCE.md`: no command changes, and the command reference must not change
- every other line of pace-report.py (the module docstring, the imports, the collection loop at lines 815-838, the `unknown_starts` block from line 855 on, and every other function) and every other file under `bridge/`

## Context
**What the code is today** (branch `refactor/B5`, head `4a25d36`, the supervisor's tests-lane commit). The supervisor's reality check before this brief, on this branch:
- Lines 840-853 are exactly the two loops quoted in the Objective; the bodies are identical character for character.
- `over` and `stage` are plain Python lists built at lines 815-816 (`over = []`, `stage = []`) and filled with `(ident, rnd)` tuples by `.append` at lines 836 and 838. `over + stage` is therefore a new list holding every `over` tuple in order, then every `stage` tuple in order; neither list is modified by the loops, and neither name is read after line 853.
- `_lift_map(ws, common, id_part)` (line 389) and `_ascii_name(name)` (line 85) are module functions; calling them in the same sequence of arguments as today keeps every call and every appended line in the same order.
- The program runs `main()` only under `if __name__ == "__main__":` (line 950), so importing it through importlib runs nothing.

**How the tests reach this code.** `tests/test_pace_report.py` runs the Workspace source as a subprocess (`PACE = os.path.join(WORKSPACE, "bridge", "cursor-bridge", "pace-report.py")`, `def pace(args, cwd):`) against git projects it builds under pytest's `tmp_path` (`class MiniProject`), with `GIT_CONFIG_GLOBAL` and `GIT_CONFIG_SYSTEM` set to `os.devnull`; some tests also load it through the `program` fixture (`program("pace-report")`, `tests/conftest.py` `def load_program(name):`). `tests/test_task033_supervisor.py`, `_r2.py`, `_r3.py` and `_r4.py` also cover the over-ceiling and stage lines; you do not run those (see Constraints), the supervisor does after your run.

**The manifest.** `bridge/cursor-bridge/MANIFEST.json` holds a sha256 of every file under `bridge/` (today line 89, `"cursor-bridge/pace-report.py": "4f0e44dc..."`). After your edit that hash no longer matches. Any test that compares the sources with the manifest fails on pace-report.py until the supervisor regenerates the manifest after your run. That is expected: you do not run those tests and you do not regenerate the manifest. Name the expectation in your report.

**The command reference.** `docs/cli-reference.json` is generated from each program's `build_parser()`. This change does not touch `build_parser()` (line 75), so `python tools/dump-cli.py --check` must stay green.

**Security context.** The pace report is logic surface: `.cursor/rules/secure-coding.mdc` is in force for you, and the project's ASVS level is 2 (`docs/INVENTORY.md`, Decisions: "The builder's secure-coding rule is ASVS level 2"). The trust boundary is the project roots given on the command line and the git history, handoff files and launcher/guard records the program reads from them (read-only). This change only merges two printing loops and does not touch that boundary.

**Development data** (`docs/INVENTORY.md`, Decisions): "the dev build is the Workspace sources under `bridge/`; a session in the repo always runs the *installed* bridge (`~/.claude`), never the one being edited, and installs reach running projects only through the owner's install run sheet". For you this means: the test below runs the Workspace source against pytest's temporary folders. Never run pace-report.py yourself against a real project root, the real `~/.claude` (your user profile's `.claude` folder) or with no root argument (its default roots are the owner's projects), and never run `bridge-install.py`.

## Diagrams
No normative diagram covers this file (the repository has no `docs/diagrams/`). Merging two loops inside one function touches no component, data, state or sequence element.

## Requirements
1. Lines 840-853 of `bridge/cursor-bridge/pace-report.py` are replaced by one loop headed exactly `    for ident, rnd in over + stage:` (four spaces of indentation, as today), followed by the existing six-line body once, byte-identical to today's body, with the file's existing line endings and no trailing whitespace.
2. The printed output keeps the same order: every `over` line, then every `stage` line, each group in its current order.
3. No other line of pace-report.py changes. The docstring, the imports, the blank lines, lines 815-838, line 855 onward and every other function stay byte-identical.
4. No other file changes, apart from your report and (if you have something to note) one appended line in `docs/BUILDER_NOTES.md`.

## Acceptance criteria
- [ ] Behaviour is identical: every output of pace-report.py (exit code, stdout, stderr) is byte-for-byte unchanged for every input.
- [ ] `python -m pytest -q tests/test_pace_report.py -p no:cacheprovider` passes, before and after the edit, with the **same** test set (the same count of passed tests, none skipped or failed; record both counts in the report).
- [ ] The importlib check (the command in Constraints) prints `ok` and exits 0.
- [ ] `python tools/dump-cli.py --check` exits 0 after the edit; `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` are unchanged.
- [ ] `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge` reports 0 FAIL.
- [ ] `git diff --stat` shows `bridge/cursor-bridge/pace-report.py` as the only product file changed, with 8 lines removed and 1 added (`1 insertion(+), 8 deletions(-)`). `git diff bridge/cursor-bridge/pace-report.py` shows only the first loop header changed to `over + stage` and the second loop (header and body) removed.
- [ ] No test file changed; `bridge/cursor-bridge/MANIFEST.json` and `bridge/cursor-bridge/VERSION` unchanged; no entry in `docs/CHANGES.md` or `bridge/cursor-bridge/CHANGELOG.md`.
- [ ] The duplicate code is gone: pace-report.py contains neither `for ident, rnd in over:` nor `for ident, rnd in stage:`, and `lifts = _lift_map(ws, common, ident)` appears exactly once in the file.

## Constraints
- Do not add dependencies.
- Do not read or write any file outside this workspace (the folder you were started in). Everything you need is inside it; everything you produce goes inside it.
- If the brief, the rules, or the tooling got in your way — an instruction that contradicted another, a check that fired wrongly, a step that cost time for no reason — append one dated line describing it to `docs/BUILDER_NOTES.md`. Do not try to fix the tooling. Do the same for anything you learned about a defect or a pitfall (a cause you found, a platform quirk that cost you a round): one dated line, so the supervisor can carry it forward.
- In any Markdown you write, never break a line inside a paragraph or a list item; one paragraph is one line. Line breaks only between blocks.
- This increment talks to no external service.
- Any console process your code launches on Windows is created windowless (`creationflags=subprocess.CREATE_NO_WINDOW` in Python — `0` on other platforms; `windowsHide: true` in Node). Capturing output does not prevent the window. A window is allowed only when it serves the user (they watch it or type into it); then write the reason at the call site as `windowless: visible-ok <reason>`. A spawn that needs a process group for a `CTRL_BREAK` stop is hidden only with a test of the stop path. This change launches no process and must not add one.
- Never start a server, a watcher or a daemon that outlives a test: a test that needs the product running starts it through the test framework's own fixture and stops it there. A server left running keeps your run from ending (plan 10.3, release A2).
- Do not refactor code outside the scope, even if it looks wrong.
- Never run the product, a migration, a seed or a test against the owner's live data. A development build uses the development data the design names (the inventory's `Development data` decision, quoted in Context) and refuses the installed product's data. Here that means the Workspace sources and pytest's temporary folders only, never the real `~/.claude` and never a real project root.
- No value in this task is marked as the owner's.
- Follow existing conventions in the files you touch.
- These git commands are not yours to run: `commit`, `push`, `switch`, `checkout`, `merge`, `rebase`, `reset`, `stash`, `branch -d`, `worktree`; you read with `git status`, `git diff` and `git log` only.
- Numbers from text, a file, a reply or an environment variable are parsed with the language's own parser, never by slicing or splitting a string. (This change parses no number.)
- An increment that starts a process meets the process checklist (windowless, stopped in a `finally`/teardown with its tree, nothing outlives the test, a browser on Windows launched attached, pipes closed or drained). This change starts none.
- Every verification command is written here in full. Run exactly these, each from the Workspace root (the folder you were started in):
  - Before the edit, and again after it: `python -m pytest -q tests/test_pace_report.py -p no:cacheprovider`
  - After the edit: `python -c "import importlib.util; s = importlib.util.spec_from_file_location('pace_report', 'bridge/cursor-bridge/pace-report.py'); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); print('ok')"`
  - After the edit: `python tools/dump-cli.py --check`
  - After the edit: `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge`
  - At the end: `git status` and `git diff --stat`, both pasted into the report.
  - Do not run the full suite, any other test file (including `tests/test_task033_supervisor*.py`), or `tools/make-manifest.py`. The supervisor regenerates the manifest and runs the full suite after your run, and the manifest-comparing tests fail on pace-report.py until then.
  Mutation checking is not asked for in this task.
- Prefer reuse over new code and write the minimum that meets the acceptance criteria (the frozen `minimal-code.mdc` is in force). This never overrides a security, observability, or accessibility requirement stated above.
- **Refactoring constraints.** Do not edit any test file. Do not add an entry to `docs/CHANGES.md` (or to `bridge/cursor-bridge/CHANGELOG.md`). Do not "improve" behaviour, messages, edge cases, or defaults you notice along the way; report them in your summary instead. Do not introduce an abstraction beyond what the listed duplicates need: no helper function, no `itertools.chain`, no renamed variable; the change is the one merged loop named above.

## Done
Your report is the file `handoff/REFAC-003-r1-report.md`, which you write as you go — what you did, what you changed, what you ran and what it printed, what you could not do — so that nothing of it is lost when your run ends early. When you finish, it holds:
- a list of every file you changed;
- a one-paragraph summary of what you did;
- the before and after outputs of the pytest command, with both counts;
- the output of the importlib check, of `python tools/dump-cli.py --check` and of the windowless check;
- `git status` and `git diff --stat`;
- one sentence stating why the behaviour is identical;
- a line saying that `bridge/cursor-bridge/MANIFEST.json` is now stale for `cursor-bridge/pace-report.py`, and that the manifest-comparing tests are expected to fail on it until the supervisor regenerates the manifest;
- anything you noticed but did not change (per the refactoring constraints);
- a final section headed exactly `Assumed, not verified`: every fact this change relies on that neither this brief nor the existing code settled, and that you did not confirm — the shape of an external service's request or response, an ambiguous requirement you resolved one way, a platform or library behaviour you expected, a value you chose. One item per line: what you assumed · why · what would confirm it. If there are none, write `Assumed, not verified: none`. Be specific: "edge cases" or "error handling" is not an item.

Your last message is the summary and the report file's path, and nothing follows it: the supervisor reads only the last message, and a message printed earlier and then followed by more work is lost.
