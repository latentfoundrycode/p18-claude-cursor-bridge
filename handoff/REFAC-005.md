---
record: brief
header: 1
id: REFAC-005
round: 1
satisfies: [R-058, R-060]
scope: ["bridge/cursor-bridge/bridge_env.py", "bridge/cursor-bridge/session-start.py", "bridge/cursor-bridge/workflow-check.py", "bridge/cursor-bridge/diagram-check.py", "bridge/cursor-bridge/MANIFEST.json", "docs/BUILDER_NOTES.md", "handoff/REFAC-005-r1-report.md"]
merge_unit: null
blocking_class: null
---
# REFAC-005: stage H1's dead code goes from bridge_env.py, session-start.py, workflow-check.py and diagram-check.py

## Objective
Refactoring — remove duplication / simplify **without any change in behaviour**.

This brief carries stage H1's refactoring pass of release B2 (the refactor scout's items 3 and 5): dead code and one bare alias left by TASK-046 to TASK-050 in four bridge programs, and the manifest regenerated after them. Behaviour stays exactly the same: every printed line, every exit code, every return value, the same order of reads. Line numbers below are as the files stand on branch `refactor/h1` (cut from origin/main `6426650`; the branch's commits before yours change only test files and this brief), before your edit.

**Item 1, `bridge/cursor-bridge/bridge_env.py`, the sites:**
- (1a) `def parse_diagram_index_rows(text):`, lines 3094-3097, deleted. A grep of the Workspace (run/ excluded) for `parse_diagram_index_rows` found only its definition and two mentions in `docs/HARDENING.md` naming it unused; no caller in `bridge/`, `tests/` or `docs/diagrams/`.
- (1b) `_SCOPE_PAREN = "ScopeAgreementError"`, line 332, deleted. The grep found `_SCOPE_PAREN` on that line only.
- (1c) `class ScopeAgreementError(ValueError):` with its docstring line, lines 3212-3213, deleted. The grep found `ScopeAgreementError` in `bridge/` only at line 332 (the string above) and line 3212, and nowhere under `tests/`; the other mentions are old briefs and reports under `handoff/`, which are history and stay.
- (1d) `def deviations_table(text):`, lines 3100-3102, a bare alias (`return _first_markdown_table(text)`), deleted, and its one caller, line 3114 in `parse_deviation_keys`, `    _hl, _orig, rows = deviations_table(text)`, becomes `    _hl, _orig, rows = _first_markdown_table(text)`. Nothing else in that line or that function changes.
- `diagram_index_body_table` (lines 3075-3077) stays exactly as it is: `diagram-check.py` line 785 and `bridge_env.py` line 3168 call it.

**Item 2, `bridge/cursor-bridge/session-start.py`:** `read_status(cwd)`, lines 188-193, has no caller (the grep found none in `bridge/` or `tests/`; `tests/test_loop_guard.py` line 83 calls the loop guard's own `read_status`, not this one), while `main()`, lines 612-619, inlines the same loop over `status_candidates(cwd)`, keeping the path too. Today's lines 612-619 read exactly:

```python
    status_path = None
    status = None
    for p in status_candidates(cwd):
        if os.path.isfile(p):
            status_path = p
            with open(p, encoding="utf-8-sig", errors="replace") as f:
                status = f.read()
            break
```

`read_status` is replaced by one function `read_status_file(cwd)` returning `(path, text)` for the first candidate that is a file, read as that loop reads it (`encoding="utf-8-sig", errors="replace"`), or `(None, None)` when none is; and those eight lines of `main()` become one call of it binding `status_path` and `status`. Line 620, `    if status is None:`, and everything after it stay as they are. For reference, the loop guard already holds a function of exactly this contract (`bridge/cursor-bridge/loop-guard.py` lines 183-188); do not import it or move anything into `bridge_env` (the two hooks share no module but `bridge_env`, and `docs/HARDENING.md` line 322 records that a shared import for these helpers is not a candidate).

**Item 3, `bridge/cursor-bridge/loop-guard.py`: not in Scope.** It holds `read_status(cwd)` (lines 175-180), called by `tests/test_loop_guard.py` line 83, and `read_status_file(cwd)` (lines 183-188), called by `main()` line 595. Neither is dead, so this pass leaves the file untouched. Your first check (Requirements 1) confirms this and reports item 3 as not applicable with that reason; if you find code in loop-guard.py that is dead, report it, do not edit the file.

**Item 4, `bridge/cursor-bridge/workflow-check.py`, `check_status`:** lines 701-702 are deleted:

```python
        if len(line_problems) > 1 and p3 not in line_problems:
            continue
```

They cannot fire: `bridge_env.status_workflow_line` (bridge_env.py lines 2704-2728) returns one of these problem lists: `[p0]`, `[]`, `[p2]`, `[p1]`, `[p2, p1]`, `[p3]`, `[p2, p3]`. After lines 699-700 (`if p0 in line_problems or p1 in line_problems: continue`) the only list of two items left is `[p2, p3]`, which holds `p3` (docs/HARDENING.md, TASK-047's round 3 notes). Lines 699 and 700 and line 703 (`        if body == "not yet classified":`) stay byte-identical; a mutant anchors on line 700.

**Item 5, `bridge/cursor-bridge/diagram-check.py`, `known_deviations`:** line 613, `        elif hdr is not None:`, becomes `        else:` at the same eight-space indentation. The branch before it (line 611, `if hdr is None:`) makes `hdr is not None` always true there (docs/HARDENING.md, TASK-049's leads: "a redundant `elif` in diagram-check's `known_deviations`"). Lines 614-616 keep their text and indentation. Line 617, `    elif header is not None:`, is a different test (of `header`, not `hdr`) and does not change.

**Item 6, `bridge/cursor-bridge/MANIFEST.json`:** regenerated once, after your last source edit, by `python tools/make-manifest.py --version 2026.11.09a`. The version stays `2026.11.09a`.

**Callers to update:** `parse_deviation_keys` (item 1d) and `main()` in session-start.py (item 2). No other caller exists of anything this brief deletes; no public signature outside these sites changes.

Satisfies: no new requirement. This keeps as they are R-058 (the status file's header read first by its six readers) and R-060 (the tabular records' headers read first by their readers), built by TASK-047 and TASK-049.

## Scope
Files and directories you may create or modify:
- bridge/cursor-bridge/bridge_env.py
- bridge/cursor-bridge/session-start.py
- bridge/cursor-bridge/workflow-check.py
- bridge/cursor-bridge/diagram-check.py
- bridge/cursor-bridge/MANIFEST.json
- docs/BUILDER_NOTES.md
- handoff/REFAC-005-r1-report.md

Do not modify anything else.

## Out of scope
- .env and anything under secrets/
- CI configuration, pre-commit configuration, anything under `tools/` (you run `tools/make-manifest.py`; you do not edit it)
- docs/ and handoff/, except the files the Scope section names; `docs/diagrams/` included: this change needs no diagram change (see Diagrams)
- every file under `tests/`: no test file may be edited, renamed or created (`refactor-check.py` fails the branch on any test edit). The working tree may already show test files as modified by the supervisor before your run; leave them exactly as they are
- `bridge/cursor-bridge/loop-guard.py` (item 3)
- `bridge/cursor-bridge/VERSION`: it must still read `2026.11.09a` after `make-manifest.py` rewrites it; if `git status` then shows it modified, report it, do not try to restore it
- `run/supervisor/TASK-046-mutants.json` to `run/supervisor/TASK-050-mutants.json` and everything else under `run/`: the supervisor's, gitignored; they anchor exact text in these files and the supervisor re-anchors them after your run
- `docs/CHANGES.md` and `bridge/cursor-bridge/CHANGELOG.md`: a refactoring has no change entry
- `docs/cli-reference.json` and `docs/CLI_REFERENCE.md`: no command changes
- in bridge_env.py: `diagram_index_body_table`, `diagram_index_table`, `diagram_index_fallback`, `deviations_fallback`, `_first_markdown_table`, `split_entry` and every other line not named in the Objective
- every other file under `bridge/`

## Context
**What the code is today** (branch `refactor/h1`, head `6426650`). All five product files have CRLF line endings on every line; keep them, and add no trailing whitespace. The facts in the Objective were checked against the code for this brief; the caller greps are re-run by you (Requirements 1) before you delete anything.

**Byte-identical neighbours.** The supervisor's mutants (`run/supervisor/TASK-046-mutants.json` to `TASK-050-mutants.json`) anchor exact text in these files. Every line you do not need to change stays byte-identical, in particular the lines next to each deletion: in bridge_env.py lines 331 and 333 around 1b, the end of `diagram_index_fallback` (3088-3091) and the whole of `deviations_fallback` (3105-3108) around 1a and 1d, the end of `requirement_ids_from_register` (ending `    return ids`, 3209) and `def split_entry(entry):` (3216) around 1c; in workflow-check.py lines 699-700 and 703; in diagram-check.py lines 611-612 and 614-617; in session-start.py the end of `status_candidates` (185) and `def installed_version():` (196), and lines 611 and 620 in `main()`. Top-level definitions stay separated by exactly two blank lines, as the file already does: when you delete a function or the class, delete it with the two blank lines that follow it, so the blank lines between the remaining neighbours are two.

**How the tests reach this code.** The test files in the Constraints load the Workspace sources (the programs by path, `bridge_env` from `bridge/cursor-bridge/`) and run them against folders under pytest's `tmp_path`. `tests/test_session_start.py` and `tests/test_session_start_module.py` drive session-start.py's `main()` through its stdin JSON; `tests/test_workflow_check.py` and `tests/test_workflows_line_check.py` reach `check_status`; `tests/test_header_tables.py`, `tests/test_header_tables_r2.py`, `tests/test_diagram_check.py` and `tests/test_diagram_check_a4.py` reach `known_deviations` and `parse_deviation_keys`; `tests/test_loop_guard.py` is run because it calls the loop guard's `read_status`, which this change must not disturb.

**The manifest.** `MANIFEST.json` holds a normalized sha256 (CRLF folded to LF, BOM dropped) of every file under `bridge/`. After your source edits it is stale for the four programs; `tools/make-manifest.py --version 2026.11.09a` rewrites `VERSION` (to `2026.11.09a` and a line feed) and the manifest, whose `generated` stamp changes. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` then compares the tree with it and prints `RESULT: SOURCES MATCH bridge 2026.11.09a`.

**Security context.** These are logic surfaces (record parsing, the session-start hook): `.cursor/rules/secure-coding.mdc` is in force for you, and the project's ASVS level is 2 (`docs/INVENTORY.md`, Decisions). The trust boundary here is the records a session or a builder writes (`docs/PROJECT_STATUS.md`, `docs/diagrams/DEVIATIONS.md`), which these programs read; this change moves no boundary: every header check (`check_header`, the `HeaderError` raise in `known_deviations`) runs on the same paths as today.

**Development data** (`docs/INVENTORY.md`, Decisions): "the dev build is the Workspace sources under `bridge/`; a session in the repo always runs the *installed* bridge (`~/.claude`), never the one being edited, and installs reach running projects only through the owner's install run sheet". For you: the tests run the Workspace sources against pytest's temporary folders. Never run session-start.py, loop-guard.py, workflow-check.py or diagram-check.py yourself against this repository's own records, and never run `bridge-install.py`.

## Diagrams
`docs/diagrams/D-002-components.md` — the elements `session_start`, `workflow_check`, `diagram_check` and `bridge_env`. Each program keeps its existing import of `bridge_env` and gains no other; no edge is added or removed, so the diagram does not change. `docs/diagrams/D-005-header-schemas.md` (the header schemas) is untouched: no schema or reader of a header changes. **If the task cannot be done within them, stop and report the conflict (an objection) instead of deviating.**

## Requirements
1. **Checks first, before any edit; paste each command and its output in the report.** From the Workspace root, grep the Workspace for each of `parse_diagram_index_rows`, `_SCOPE_PAREN`, `ScopeAgreementError`, `deviations_table` and `read_status`, excluding `run/` (for example `git grep -n -e <name> -- . ":(exclude)run"`), and confirm: no caller of 1a, 1b or 1c anywhere in `bridge/`, `tests/` or `docs/diagrams/`; `deviations_table` called once, at bridge_env.py line 3114; session-start.py's `read_status` called nowhere; loop-guard.py's `read_status` called by `tests/test_loop_guard.py` and its `read_status_file` by its `main()`, so nothing in loop-guard.py is dead (item 3 not applicable). Also confirm in `bridge_env.status_workflow_line` the list of problem lists the Objective gives for item 4. Where a check does not hold, leave that item undone, say so in the report, and go on with the others.
2. **Item 1.** Delete 1a, 1b and 1c, and delete 1d with its caller changed as the Objective says. `diagram_index_body_table` stays.
3. **Item 2.** session-start.py's `read_status` becomes `read_status_file(cwd)` with the contract the Objective states, at the same place in the file, and `main()` calls it in place of lines 612-619. `main()` prints, for every input, exactly what it prints today, and exits 0 as today.
4. **Item 4.** Delete workflow-check.py lines 701-702 only.
5. **Item 5.** diagram-check.py line 613 becomes `        else:` only.
6. **Item 6.** After your last edit to a source file, run `python tools/make-manifest.py --version 2026.11.09a` once, then the bridge-check command in the Constraints.
7. No other line of the four programs changes. Every file keeps its CRLF line endings and gains no trailing whitespace.

## Acceptance criteria
- [ ] Behaviour is identical: the same printed lines, exit codes and return values for every input.
- [ ] The named test files pass before and after the edit with the **same** test set: the same count passed, none failed, none newly skipped; both summary lines quoted in the report. None edited.
- [ ] Each item is done, or reported as not applicable with the reason (item 3 expected not applicable).
- [ ] `parse_diagram_index_rows`, `_SCOPE_PAREN`, `ScopeAgreementError` and `deviations_table` appear nowhere under `bridge/`; `read_status` appears in session-start.py nowhere, `read_status_file` in it twice (its definition and the one call in `main()`); `len(line_problems) > 1` appears nowhere in workflow-check.py; `elif hdr is not None` appears nowhere in diagram-check.py.
- [ ] Every caller now uses the single implementation: `parse_deviation_keys` calls `_first_markdown_table`; `main()` calls `read_status_file`. No public signature outside the listed sites changed.
- [ ] `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge` ends with `0 FAIL` and exit 0.
- [ ] `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` prints `RESULT: SOURCES MATCH bridge 2026.11.09a`.
- [ ] `python bridge/cursor-bridge/refactor-check.py HEAD --max-lines 400` prints a line starting `PURE:` (the base is the commit you were launched on: the branch already holds the supervisor's tests-lane commit, which a base of `origin/main` would count as a test edit).
- [ ] `git diff --stat` shows only the five Scope product files (plus the report and, if you wrote one, the builder-notes line); `bridge/cursor-bridge/loop-guard.py`, every file under `tests/` you did not find already modified, `docs/CHANGES.md` and `bridge/cursor-bridge/CHANGELOG.md` unchanged; no mutation script in the diff.

## Constraints
- Do not add dependencies.
- Do not read or write any file outside this workspace (the folder you were started in). Everything you need is inside it; everything you produce goes inside it. Run the Workspace copies of the bridge programs, as the commands below do, never a copy under a home folder.
- If the brief, the rules, or the tooling got in your way (an instruction that contradicted another, a check that fired wrongly, a step that cost time for no reason), append one dated line describing it to `docs/BUILDER_NOTES.md`. Do not try to fix the tooling. Do the same for anything you learned about a defect or a pitfall (a cause you found, a platform quirk that cost you a round): one dated line, so the supervisor can carry it forward.
- In any Markdown you write, never break a line inside a paragraph or a list item; one paragraph is one line. Line breaks only between blocks.
- This increment talks to no external service.
- Any console process your code launches on Windows is created windowless (`creationflags=subprocess.CREATE_NO_WINDOW` in Python, `0` on other platforms; `windowsHide: true` in Node). Capturing output does not prevent the window. A window is allowed only when it serves the user (they watch it or type into it); then write the reason at the call site as `windowless: visible-ok <reason>`. A spawn that needs a process group for a `CTRL_BREAK` stop is hidden only with a test of the stop path. This change launches no process and must not add one.
- Never start a server, a watcher or a daemon that outlives a test: a test that needs the product running starts it through the test framework's own fixture and stops it there. A server left running keeps your run from ending (plan 10.3, release A2).
- Do not refactor code outside the scope, even if it looks wrong.
- Never run the product, a migration, a seed or a test against the owner's live data. A development build uses the development data the design names (the inventory's `Development data` decision, stated in Context) and refuses the installed product's data. Here that means the Workspace sources and pytest's temporary folders only.
- No value in this task is marked as the owner's.
- Follow existing conventions in the files you touch.
- These git commands are not yours to run: `commit`, `push`, `switch`, `checkout`, `merge`, `rebase`, `reset`, `stash`, `branch -d`, `worktree`; you read with `git status`, `git diff`, `git grep` and `git log` only.
- Numbers from text, a file, a reply or an environment variable are parsed with the language's own parser, never by slicing or splitting a string. This change parses no number.
- An increment that starts a process meets the process checklist (windowless, stopped in a `finally` or a fixture's teardown with its whole tree, nothing outlives the test or the command, a browser on Windows launched attached, pipes closed or drained). This change starts none.
- Every verification command is written here in full. Run exactly these, each from the Workspace root (the folder you were started in), each in the foreground, never in the background:
  - At the start: `git status --short` and `git rev-parse HEAD`, pasted into the report (they show which test files, if any, were already modified before your run).
  - Before the edit, and again after the last edit: `python -m pytest -p no:cacheprovider -q -rs tests/test_header_reader.py tests/test_header_tables.py tests/test_header_tables_r2.py tests/test_header_status.py tests/test_session_start.py tests/test_session_start_module.py tests/test_loop_guard.py tests/test_workflow_check.py tests/test_workflows_line_check.py tests/test_diagram_check.py tests/test_diagram_check_a4.py tests/test_header_currency.py tests/test_header_plan.py`
  - After the last source edit, in this order: `python tools/make-manifest.py --version 2026.11.09a`; `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`; `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge`; `python bridge/cursor-bridge/refactor-check.py HEAD --max-lines 400`.
  - At the end: `git status --short`, `git diff --stat` and `git rev-parse HEAD`, pasted into the report.
  - Do not run the whole `tests/` tree or any other test file (a builder of this release that ran the whole tree reached its limit, ISS-030); the supervisor runs the full suite after your run. If a test fails before your edit, stop and report it; do not fix it. If `refactor-check.py` prints IMPURE naming only test files that `git status --short` already showed modified at the start, quote it, say so, and touch nothing.
- Mutation checking is the supervisor's in this task: it re-anchors and re-runs its mutants after your run. Run no mutation, write no mutation script, and let none land in the diff.
- Prefer reuse over new code and write the minimum that meets the acceptance criteria (the frozen `minimal-code.mdc` is in force). This never overrides a security, observability, or accessibility requirement stated above.
- **Refactoring constraints.** Do not edit any test file. Do not add an entry to `docs/CHANGES.md`. Do not "improve" behaviour, messages, edge cases, or defaults you notice along the way; report them in your summary instead. Do not introduce an abstraction beyond what the listed duplicates need: the one new name is `read_status_file` in session-start.py; no helper in `bridge_env`, no import between the two hooks.

## Done
Your report is the file `handoff/REFAC-005-r1-report.md`, which you write as you go (what you did, what you changed, what you ran and what it printed, what you could not do) so that nothing of it is lost when your run ends early. When you finish, it holds:
- a list of every file you changed;
- a one-paragraph summary of what you did;
- for each of items 1a, 1b, 1c, 1d, 2, 3, 4, 5 and 6: done, or not applicable with the reason; every deletion with its grep command and output as the evidence of no caller;
- the before and after outputs of the pytest command, with both summary lines;
- the outputs of make-manifest, bridge-check, windowless-check and refactor-check, each line that shows the result quoted;
- `git status --short`, `git diff --stat` and `git rev-parse HEAD` at the start and at the end, and whether the working tree held uncommitted changes then;
- one sentence stating why the behaviour is identical;
- anything you noticed but did not change (per the refactoring constraints);
- a final section headed exactly `Assumed, not verified`: every fact this change relies on that neither this brief nor the existing code settled, and that you did not confirm (an ambiguous requirement you resolved one way, a platform or library behaviour you expected, a value you chose). One item per line: what you assumed · why · what would confirm it. If there are none, write `Assumed, not verified: none`. Be specific: "edge cases" or "error handling" is not an item.

Every command you ran is quoted in the report with the lines it printed, verbatim, in a fenced block; a count, or a claim that a check passed, quotes the output line that shows it. A command you did not run is written `not run`, never described as run.

Your last message is the summary and the report file's path, and nothing follows it: the supervisor reads only the last message, and a message printed earlier and then followed by more work is lost.
