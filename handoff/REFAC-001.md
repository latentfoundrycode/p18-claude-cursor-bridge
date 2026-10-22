# REFAC-001: pointers_part's workflow read as one helper with plain returns

## Objective
Refactoring — remove duplication / simplify **without any change in behaviour**.

The session-start hook (`bridge/cursor-bridge/session-start.py`) builds its "pointers" part in `def pointers_part(status, source):` (line 475). Inside it, lines 499-544 on this branch read the installed workflow tables and the phase modules' pointer lines inside a stdout/stderr redirection, and the failure paths of that read nest eight levels deep (`if not tables_at_installed_paths(wc):` / `else:` / `if link_err:` / `else:` / `if table_err:` / `else:` / `for key in module_keys:` ...). The refactor-scout candidate (stage B3, candidate 1; `docs/HARDENING.md`, Stage B3, the lead ending "`pointers_part`'s failure paths nest eight levels, where a function returning (blocks, lines, error) would give each a plain return and make the `i < len(pointer_blocks)` guard go (a refactoring candidate for stage B3's pass)") is to flatten it.

Site: `bridge/cursor-bridge/session-start.py`, lines 506-531 (the body of the `with contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink):` block inside `pointers_part`) and lines 543-544 (the `if i < len(pointer_blocks):` guard in the output loop).

Proposed shape: the chain that runs inside the redirection — `tables_at_installed_paths(wc)` → `workflow_table_link_error(wc)` → `load_tables_from_checker(wc)` → the per-module pointer blocks → `collect_conditional_files(...)` — moves into one new private module-level helper that returns a tuple `(pointer_blocks, conditional_lines, read_error)`, with a plain early return for each failure: `TABLES_NOT_INSTALLED`, the link error, the table error, each returned with an empty list of blocks and an empty list of lines, and `read_error` `None` on success. Optionally the per-module loop body may become a second private helper. The caller `pointers_part` is the only caller to update; no other function in the repository calls into this block.

## Scope
Files and directories you may create or modify:
- bridge/cursor-bridge/session-start.py
- bridge/cursor-bridge/MANIFEST.json (regenerated only, with the command in Requirements; never edited by hand)
- docs/BUILDER_NOTES.md
- handoff/REFAC-001-r1-report.md

Do not modify anything else.

## Out of scope
- .env and anything under secrets/
- CI configuration, pre-commit configuration, anything under `tools/` (you run `tools/make-manifest.py`; you do not edit it)
- docs/ and handoff/, except the files the Scope section names
- every file under `tests/` — no test file may be edited, not even a rename; the refactoring purity check fails any test-file change
- `docs/CHANGES.md` and `bridge/cursor-bridge/CHANGELOG.md` — a refactoring has no change entry
- `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` — the module docstring of session-start.py is rendered into them, so the docstring does not change in this task (see Constraints)
- `bridge/cursor-bridge/workflow-check.py` and every other file under `bridge/`
- any other function in session-start.py (`load_checker_module`, `safe_exc_type_name`, `collect_conditional_files`, `can_read_module_pointers`, `pointer_paths_from_module`, the table helpers, `main`) — they are called, not changed

## Context
**What the code is today** (`bridge/cursor-bridge/session-start.py`, branch `refactor/B3`, cut from `origin/main` d6433f1). The block to restructure, lines 496-547, verbatim:

```python
    if module_keys:
        out.append("BEFORE YOUR NEXT ACTION, re-read these files whole with the Read tool:")
        printed_paths = {PHASE_PREFIX + key + ".md" for key in module_keys}
        if needs_workflow_read(module_keys, status):
            wc, load_err = load_checker_module()
            if load_err:
                read_error = load_err
            else:
                sink = io.StringIO()
                try:
                    with contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink):
                        if not tables_at_installed_paths(wc):
                            read_error = TABLES_NOT_INSTALLED
                        else:
                            link_err = workflow_table_link_error(wc)
                            if link_err:
                                read_error = link_err
                            else:
                                tables, table_err = load_tables_from_checker(wc)
                                if table_err:
                                    read_error = table_err
                                else:
                                    for key in module_keys:
                                        block = []
                                        if can_read_module_pointers(wc, key):
                                            mod_path = phase_module_installed(key)
                                            text, _shown, err = wc.read_utf8(mod_path)
                                            if err is None:
                                                for rel in pointer_paths_from_module(text, wc):
                                                    shown = PHASE_PREFIX + rel
                                                    if shown not in printed_paths:
                                                        printed_paths.add(shown)
                                                        block.append("  - %s" % shown)
                                        pointer_blocks.append(block)
                                    conditional_lines = ["  - %s" % p for p in collect_conditional_files(
                                        wc, tables, module_keys, status, printed_paths)]
                except BaseException as err:
                    read_error = "%s: cannot be used (%s)" % (CHECKER_SHOWN, safe_exc_type_name(err))
                    pointer_blocks = []
                    conditional_lines = []
        if not pointer_blocks:
            pointer_blocks = [[] for _ in module_keys]
        for i, key in enumerate(module_keys):
            line = "  - %s%s.md" % (PHASE_PREFIX, key)
            if key == "project-end" and phase in ("building", "changing"):
                line += " " + PROJECT_END_NOTE
            out.append(line)
            if i < len(pointer_blocks):
                out.extend(pointer_blocks[i])
        if read_error is not None:
            out.append(read_error)
        out.extend(conditional_lines)
```

Just above it (lines 492-495): `module_keys = PHASE_MODULES.get(phase)`, `read_error = None`, `pointer_blocks = []`, `conditional_lines = []`.

Signatures of what the block calls, quoted from the file (none of them changes):
- `def load_checker_module():` — "Return (mod, error_line). error_line is None on success." It does its own redirection and its own `except BaseException`.
- `def safe_exc_type_name(err):` — reads `type(err).__name__` inside a redirection of its own (FIX-003; `docs/HARDENING.md`, Stage B3, the lead "**Closed by FIX-003**"); returns the name or `"an exception"`.
- `def tables_at_installed_paths(wc):` → `True`/`False`.
- `def workflow_table_link_error(wc):` → an error line or `None`.
- `def load_tables_from_checker(wc):` — "Return (tables, error_line). error_line is None on success."
- `def can_read_module_pointers(wc, key):`, `def phase_module_installed(key):`, `def pointer_paths_from_module(text, wc):`, and the checker's `wc.read_utf8(path)` which returns `(text, shown, err)`.
- `def collect_conditional_files(wc, tables, module_keys, status, already):` — mutates `already` (the `printed_paths` set) and returns the named paths; it must run after every pointer block has been built, because it skips paths the blocks already added.
- Constants used: `TABLES_NOT_INSTALLED`, `CHECKER_SHOWN`, `PHASE_PREFIX`, `PROJECT_END_NOTE`.
- Imports already present (lines 75-81): `contextlib`, `importlib.util`, `io`, `json`, `os`, `re`, `sys`. Nothing new is needed.

Why the output-loop guard is always true: `if module_keys:` excludes an empty or missing key list; on success the helper's loop appends exactly one block per key; on every failure (load error, the three early returns, an exception) `pointer_blocks` is empty and `if not pointer_blocks: pointer_blocks = [[] for _ in module_keys]` refills it to one block per key. So `i < len(pointer_blocks)` holds for every `i`; `out.extend(pointer_blocks[i])` stays.

**Trust boundaries and security context.** This is logic surface: `.cursor/rules/secure-coding.mdc` is in force for you, and the project's ASVS level is 2 (`docs/INVENTORY.md`, Decisions: "The builder's secure-coding rule is ASVS level 2"). The binding threat model is `docs/INVENTORY.md`, Decisions, the row beginning "The session-start hook's threat model": "a partial, mismatched or hand-edited install, not a hostile checker: workflow-check.py runs in the hook's process and could write to its output directly. Inside it, nothing the checker returns reaches the output except as an exact str matching its pattern". The boundary is the installed checker module `wc` and the files it reads: everything the checker does (each `wc.*` call and every helper that calls one) runs inside the stdout/stderr redirection, so what it prints is discarded, and any exception it raises is caught by the one `except BaseException` and turned into the fixed "cannot be used" line. FIX-003's guarantee: the exception's type name is read only through `safe_exc_type_name`, which does its own redirection. A reviewer will read the diff for exactly these properties.

**Development data** (`docs/INVENTORY.md`, Decisions): "the dev build is the Workspace sources under `bridge/`; a session in the repo always runs the *installed* bridge (`~/.claude`), never the one being edited, and installs reach running projects only through the owner's install run sheet". For you: the tests below run the edited `bridge/cursor-bridge/session-start.py` against temporary homes they build under pytest's `tmp_path`; never run the hook, the installer or any test against the real `~/.claude` (your user profile's `.claude` folder), and never run `bridge-install.py` yourself.

**The manifest.** `tools/make-manifest.py` rewrites `bridge/cursor-bridge/MANIFEST.json` with a normalized sha256 of every file under `bridge/` and rewrites `bridge/cursor-bridge/VERSION` from the newest `## <version>` heading in `bridge/cursor-bridge/CHANGELOG.md`. Today both VERSION and the manifest's `"version"` are `2026.10.18a` and that is the newest CHANGELOG heading, so the run should leave VERSION byte-identical and change only the manifest's `"generated"` stamp and the `cursor-bridge/session-start.py` hash. `tests/test_core_carve.py::test_r003_the_modules_install_from_the_manifest` installs from the manifest.

**The tests that pin the behaviour** (all run the hook as a subprocess against a temporary home, or read its docstring): `tests/test_session_start_module.py` (whole file, including `test_r005_what_the_checker_writes_is_not_the_hooks_output` for the redirection and the docstring tests at lines 728-745 and 796-803), `tests/test_session_start.py`, and the hook tests in `tests/test_phase_modules_build.py` and `tests/test_phase_modules_interface_planning.py`.

## Diagrams
No normative diagram covers this file (the repository has no `docs/diagrams/`). The change adds private functions inside one module and no import, so no component, data or sequence element is touched.

## Requirements
1. A new private module-level helper in `bridge/cursor-bridge/session-start.py` (name of your choice, with a leading underscore or in the file's existing plain style; no other code may call it) performs, in today's order, `tables_at_installed_paths(wc)`, `workflow_table_link_error(wc)`, `load_tables_from_checker(wc)`, the per-module pointer blocks, and `collect_conditional_files(wc, tables, module_keys, status, printed_paths)`, and returns `(pointer_blocks, conditional_lines, read_error)`.
2. Each failure is a plain early return: tables not at their installed paths → `([], [], TABLES_NOT_INSTALLED)`; a link error → `([], [], link_err)`; a table error → `([], [], table_err)`. Success returns one block per module key, the conditional lines, and `None`.
3. `pointers_part` keeps, unchanged in text and order: `printed_paths = {PHASE_PREFIX + key + ".md" for key in module_keys}` (or the same set built at the same point in the helper), `if needs_workflow_read(module_keys, status):`, `wc, load_err = load_checker_module()` and `if load_err: read_error = load_err`, `sink = io.StringIO()`, one `try:` whose body is `with contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink):` around the single helper call, and the `except BaseException as err:` handler exactly as it is (its three lines unchanged).
4. The three results are assigned from the helper's returned tuple only when the helper returns, inside the redirection; an exception raised anywhere in the helper leaves the handler to set `read_error`, `pointer_blocks = []` and `conditional_lines = []` as today, so no partial result survives.
5. Optionally, the per-module loop body (one module's pointer block) becomes a second private helper; if so it is called only from the first helper, inside the same redirection, and builds the block exactly as today (same `can_read_module_pointers` check, same `phase_module_installed`, same `wc.read_utf8` call, same `err is None` test, same `pointer_paths_from_module(text, wc)`, same `printed_paths` de-duplication and `"  - %s"` format).
6. The output loop drops `if i < len(pointer_blocks):` and keeps `out.extend(pointer_blocks[i])` for every key; `if not pointer_blocks: pointer_blocks = [[] for _ in module_keys]` stays.
7. After the edit, regenerate the manifest from the Workspace root: `python tools/make-manifest.py` (no arguments). Do not edit `MANIFEST.json` by hand.

## Acceptance criteria
- [ ] The full test suite passes with the **same** test set (same test count and same pass/skip/fail counts as your before-run, recorded in the report).
- [ ] `python -m pytest tests/test_session_start_module.py tests/test_session_start.py tests/test_phase_modules_build.py tests/test_phase_modules_interface_planning.py -q` (working folder: the Workspace root) reports the same counts before and after the change, all passing; both outputs are pasted in the report.
- [ ] `python -m pytest tests/test_core_carve.py::test_r003_the_modules_install_from_the_manifest -q` passes after the manifest is regenerated.
- [ ] The single caller, `pointers_part`, now uses the helper; the nested `if`/`else` chain inside the `with` is gone, the deepest indentation level in `pointers_part` is at most the `with` body's, and the `if i < len(pointer_blocks):` guard is gone.
- [ ] No public name, signature, constant, message string, exit code, or import changed; `git diff` of session-start.py shows only the moved block, the new helper(s), the dropped guard, and (if any) a comment adjusted where it named the old structure.
- [ ] The module docstring (lines 2-74) is byte-identical (its tests at `tests/test_session_start_module.py` lines 728-745 and 796-803 pass, and `docs/cli-reference.json` therefore needs no regeneration).
- [ ] `git diff --stat` lists exactly `bridge/cursor-bridge/session-start.py` and `bridge/cursor-bridge/MANIFEST.json` among product files (plus, if written, `docs/BUILDER_NOTES.md`); `bridge/cursor-bridge/VERSION` shows no change. The session-start.py change is about 55 lines; it must stay well under 114 changed lines (the stage pass's remaining budget).
- [ ] Every requirement and invariant in this brief holds by reading the diff; no test file changed.

## Constraints
- Do not add dependencies.
- Do not read or write any file outside this workspace (the folder you were started in). Everything you need is inside it; everything you produce goes inside it.
- If the brief, the rules, or the tooling got in your way — an instruction that contradicted another, a check that fired wrongly, a step that cost time for no reason — append one dated line describing it to `docs/BUILDER_NOTES.md`. Do not try to fix the tooling. Do the same for anything you learned about a defect or a pitfall (a cause you found, a platform quirk that cost you a round): one dated line, so the supervisor can carry it forward.
- In any Markdown you write, never break a line inside a paragraph or a list item; one paragraph is one line. Line breaks only between blocks.
- This increment talks to no external service.
- Any console process your code launches on Windows is created windowless (`creationflags=subprocess.CREATE_NO_WINDOW` in Python — `0` on other platforms; `windowsHide: true` in Node). Capturing output does not prevent the window. A window is allowed only when it serves the user (they watch it or type into it); then write the reason at the call site as `windowless: visible-ok <reason>`. A spawn that needs a process group for a `CTRL_BREAK` stop is hidden only with a test of the stop path. The hook launches no process and this change must not add one (the project's windowless-check pre-commit gate reads the diff).
- Never start a server, a watcher or a daemon that outlives a test: a test that needs the product running starts it through the test framework's own fixture and stops it there. A server left running keeps your run from ending (plan 10.3, release A2).
- Do not refactor code outside the scope, even if it looks wrong.
- Never run the product, a migration, a seed or a test against the owner's live data. A development build uses the development data the design names (the inventory's `Development data` decision, quoted in Context) and refuses the installed product's data; here that means the tests' temporary homes only, never the real `~/.claude`.
- No value in this task is marked as the owner's; every message string in the hook is nonetheless fixed by the behaviour-preservation rule below.
- Follow existing conventions in the files you touch (plain module-level functions, no type hints, `%` formatting, ASCII-only source apart from what it already quotes).
- These git commands are not yours to run: `commit`, `push`, `switch`, `checkout`, `merge`, `rebase`, `reset`, `stash`, `branch -d`, `worktree`; you read with `git status`, `git diff` and `git log` only.
- Numbers from text, a file, a reply or an environment variable are parsed with the language's own parser, never by slicing or splitting a string. (This change parses no new number.)
- An increment that starts a process meets the process checklist (windowless, stopped in a `finally`/teardown with its tree, nothing outlives the test, a browser on Windows launched attached, pipes closed or drained). This change starts none; the existing tests start the hook as a subprocess through their own helpers, which you do not change.
- Every verification command is written here in full; run exactly these, each from the Workspace root (the folder you were started in):
  - Before any edit, and again after the edit and the manifest regeneration: `python -m pytest tests/test_session_start_module.py tests/test_session_start.py tests/test_phase_modules_build.py tests/test_phase_modules_interface_planning.py -q`
  - After the edit: `python tools/make-manifest.py`
  - After the regeneration: `python -m pytest tests/test_core_carve.py::test_r003_the_modules_install_from_the_manifest -q`
  - Do not run the full suite: the supervisor runs it after your run, through the bridge's launcher.
  - At the end: `git status` and `git diff --stat`, pasted into the report.
  Mutation checking is not asked for in this task.
- Prefer reuse over new code and write the minimum that meets the acceptance criteria. This never overrides a security, observability, or accessibility requirement stated above.
- **Refactoring constraints.** Do not edit any test file. Do not add an entry to `docs/CHANGES.md` (or to `bridge/cursor-bridge/CHANGELOG.md`). Do not "improve" behaviour, messages, edge cases, or defaults you notice along the way — report them in your summary instead. Do not introduce an abstraction beyond what the listed duplicates need (one helper, optionally a second for the per-module block; no class, no new constant, no new module).
- **Behaviour-preservation invariants (a reviewer checks each against the diff):**
  - Every output string is byte-identical in every case: success, load error, `TABLES_NOT_INSTALLED`, link error, table error, an exception at any point, a phase with no module installed.
  - The order of every call is unchanged: `printed_paths` is filled by the pointer blocks before `collect_conditional_files` runs; `can_read_module_pointers`, `phase_module_installed`, `wc.read_utf8` and `pointer_paths_from_module` are called per key, in key order, under the same conditions as now; nothing is called that is not called today, and nothing is skipped that runs today.
  - The helper runs entirely inside the `contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink)` redirection; no `wc.*` call and no helper that makes one runs outside it.
  - `safe_exc_type_name(err)` stays inside the `except BaseException as err:` handler and nowhere else in this block; do not move it into the helper and do not wrap the helper in another `try`.
  - `load_checker_module()` and its error path stay in `pointers_part`, outside the `try`.
  - No public name, signature, constant, message or exit code changes; no new import.
  - The module docstring stays byte-identical. Comments in the touched block stay true; adjust a comment only where it names the old structure.

## Done
Your report is the file `handoff/REFAC-001-r1-report.md`, which you write as you go — what you did, what you changed, what you ran and what it printed, what you could not do — so that nothing of it is lost when your run ends early. When you finish, it holds a list of every file you changed, a one-paragraph summary of what you did, the before and after outputs of the targeted pytest command, the manifest test's result, `git status` and `git diff --stat`, one sentence stating why the behaviour is identical, anything you noticed but did not change (per the refactoring constraints), and a section headed exactly `Assumed, not verified`: every fact this change relies on that neither this brief nor the existing code settled, and that you did not confirm — the shape of an external service's request or response, an ambiguous requirement you resolved one way, a platform or library behaviour you expected, a value you chose. One item per line: what you assumed · why · what would confirm it. If there are none, write `Assumed, not verified: none`. Be specific: "edge cases" or "error handling" is not an item.
Your last message is the summary and the report file's path, and nothing follows it: the supervisor reads only the last message, and a message printed earlier and then followed by more work is lost.
