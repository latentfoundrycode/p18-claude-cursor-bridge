---
record: brief
header: 1
id: REFAC-006
round: 1
satisfies: [R-059, R-060]
scope: ["bridge/cursor-bridge/conformance-check.py", "bridge/cursor-bridge/completion-check.py", "bridge/cursor-bridge/MANIFEST.json", "docs/BUILDER_NOTES.md", "handoff/REFAC-006-r1-report.md"]
merge_unit: null
blocking_class: null
---
# REFAC-006: stage H1's two repeats go from conformance-check.py and completion-check.py

## Objective
Refactoring — remove duplication / simplify **without any change in behaviour**.

This brief carries the second half of stage H1's refactoring pass of release B2 (the refactor scout's items 4 and 6): two repeats that TASK-048 and TASK-049 added to two bridge programs, and the manifest regenerated after them. Behaviour stays exactly the same: every printed line, every exit code. Line numbers below are as the files stand on branch `refactor/h1` at `1f124de` (the REFAC-005 commit), before your edit.

**Item 1, `bridge/cursor-bridge/conformance-check.py`, `main`, lines 1287-1296.** The Development data verdict is decided along two paths, and the identical OK line and the identical MISSING line (with its long detail) are each written twice. Today's lines 1287-1296 read exactly:

```python
            # development data kept apart from live data: a Decisions row says how
            if inv_dev_from_header is not None:
                if inv_dev_from_header:
                    add("OK", "Development data kept apart")
                else:
                    add("MISSING", "Development data kept apart", "no Decisions row `Development data: ...` saying where the live data lives and how a development build is kept from it (rule 55; the design states it, every brief carries it); a product that has live data gets one increment that makes its development build refuse the installed data")
            elif bridge_env.inventory_development_data(inv_body_for_dev):
                add("OK", "Development data kept apart")
            else:
                add("MISSING", "Development data kept apart", "no Decisions row `Development data: ...` saying where the live data lives and how a development build is kept from it (rule 55; the design states it, every brief carries it); a product that has live data gets one increment that makes its development build refuse the installed data")
```

They become: the comment line 1287 unchanged; one boolean, `dev_ok = bool(inv_dev_from_header) if inv_dev_from_header is not None else bridge_env.inventory_development_data(inv_body_for_dev)` (the conditional expression evaluates `bridge_env.inventory_development_data` only when `inv_dev_from_header is None`, exactly as the `elif` does today; keep that property); then one `if dev_ok:` with the `add("OK", "Development data kept apart")` line and one `else:` with the `add("MISSING", ...)` line, each written once, its text byte-identical to today's. The indentation stays that of the block (twelve spaces for the comment, the assignment and the `if`/`else`, sixteen for the `add` calls). Line 1297 (blank) and line 1298 (`    # --- every adapter of a listed provider ...`) stay byte-identical. Facts checked for this brief: `inv_dev_from_header` starts as `None` (line 1243) and is set only at line 1266 (`inv_dev_from_header = inv_hdr.get("development_data", "")`); `bridge_env.inventory_development_data(text)` (bridge_env.py lines 2993-3001) returns a string, `""` or the row's first cell stripped, and its one call in conformance-check.py, line 1293, uses that return for truthiness only. So `dev_ok` may be a string on the second path; it is only ever tested by `if dev_ok:`, never printed or compared.

**Item 2, `bridge/cursor-bridge/completion-check.py`, `main`, lines 198-235.** When any plan carries a header, a second loop (lines 223-233) re-reads every plan file and re-runs `bridge_env.plan_header_findings` on it; its `if fatal or hdr is None: continue` can fire only on `hdr is None`, since the first loop (lines 205-220) has already returned 2 on any fatal finding. Today's lines 221-235 read exactly:

```python
        if has_build_plan_header:
            disagree = False
            for p in plans:
                text = read(p)
                fatal, _, hdr = bridge_env.plan_header_findings(p, text, None)
                if fatal or hdr is None:
                    continue
                for rid in bridge_env.plan_r_ids_outside_headers(text):
                    if rid not in header_union:
                        disagree = True
                        break
                if disagree:
                    break
            if disagree:
                fails.append("HEADER DISAGREES: satisfies")
```

It becomes: the first loop keeps, for each plan whose `hdr is not None`, its `text` in a list (one new local, for example `headed_texts`, initialised beside `satisfied`, `header_union` and `has_build_plan_header`); the disagreement loop iterates that list, calling `bridge_env.plan_r_ids_outside_headers(text)` on each as today, in the same plan order, with no second `read(p)` and no second `bridge_env.plan_header_findings` call. Everything else stays byte-identical: line 198 to line 210 (the glob, the first loop's read, its `plan_header_findings` call, `if fatal:`, `print(fatal[0])`, `return 2`), the header and body branches of the first loop apart from the one added append, `if has_build_plan_header:`, `disagree = False`, the line `                    if rid not in header_union:` at its present indentation (twenty spaces; a mutant anchors on it, so if the loop's nesting would change that indentation, keep the nesting that keeps it), `disagree = True`, the `break` lines, `if disagree:` and `fails.append("HEADER DISAGREES: satisfies")`, and the UNPLANNED loop (lines 236-238) and everything after it.

**Item 3, `bridge/cursor-bridge/MANIFEST.json`:** regenerated once, after your last source edit, by `python tools/make-manifest.py --version 2026.11.09a`. The version stays `2026.11.09a`.

**Callers to update:** none outside the two functions; both items change code inside `main` of each program only. No public signature changes, and no new function.

Satisfies: no new requirement. This keeps as they are R-059 (the build plan's header read first by its readers, completion-check among them) and R-060 (the tabular records' headers read first by their readers, conformance-check's inventory reading among them), built by TASK-048 and TASK-049.

## Scope
Files and directories you may create or modify:
- bridge/cursor-bridge/conformance-check.py
- bridge/cursor-bridge/completion-check.py
- bridge/cursor-bridge/MANIFEST.json
- docs/BUILDER_NOTES.md
- handoff/REFAC-006-r1-report.md

Do not modify anything else.

## Out of scope
- .env and anything under secrets/
- CI configuration, pre-commit configuration, anything under `tools/` (you run `tools/make-manifest.py`; you do not edit it)
- docs/ and handoff/, except the files the Scope section names; `docs/diagrams/` included: this change needs no diagram change (see Diagrams)
- every file under `tests/`: no test file may be edited, renamed or created (`refactor-check.py` fails the branch on any test edit). The working tree may already show test files as modified by the supervisor before your run; leave them exactly as they are
- `bridge/cursor-bridge/bridge_env.py`: `inventory_development_data`, `plan_header_findings`, `plan_r_ids_outside_headers` and everything else in it stay as they are
- `bridge/cursor-bridge/VERSION`: it must still read `2026.11.09a` after `make-manifest.py` rewrites it; make-manifest writes it with an LF line ending, so `git status` may show it modified with no content change: report it, do not try to restore it
- `run/supervisor/TASK-048-mutants.json`, `run/supervisor/TASK-049-mutants.json` and everything else under `run/`: the supervisor's, gitignored; they anchor exact text in these files and the supervisor re-anchors them after your run
- `docs/CHANGES.md` and `bridge/cursor-bridge/CHANGELOG.md`: a refactoring has no change entry
- `docs/cli-reference.json` and `docs/CLI_REFERENCE.md`: no command changes
- every other line of the two programs not named in the Objective, and every other file under `bridge/`

## Context
**What the code is today** (branch `refactor/h1`, head `1f124de`). Both product files have CRLF line endings on every line; keep them, and add no trailing whitespace. The facts in the Objective were checked against the code for this brief; you re-check them (Requirements 1) before you edit.

**Byte-identical neighbours.** The supervisor's mutants anchor exact text in these files: `run/supervisor/TASK-048-mutants.json` (mutants c03, r10 and f03, in completion-check.py's plan block) and `run/supervisor/TASK-049-mutants.json` (mutants f05 and r20, in conformance-check.py above the Development data block). Every line you do not need to change stays byte-identical, in particular the lines next to each change: in conformance-check.py lines 1282-1287 (the Spending limit verdict and the comment) and 1297-1298; in completion-check.py lines 198-220 apart from the one added append and initialisation, and lines 221-222, 229-238 as they read today.

**The one behaviour difference not defended.** Today the disagreement loop reads each plan file a second time; after this change it uses the text of the first read. The two differ only if a plan file changes on disk between the two reads within one run of the program. The program does not defend that case (it is a one-shot check over files that nothing writes during its run), so this is not a behaviour change this brief protects; do not add anything for it.

**How the tests reach this code.** The test files in the Constraints load the Workspace sources (the programs by path, `bridge_env` from `bridge/cursor-bridge/`) and run them against folders under pytest's `tmp_path`. `tests/test_conformance_check.py` (lines 365, 386, 389), `tests/test_header_tables.py` (lines 205-206) and `tests/test_header_tables_r2.py` (line 153) read the `Development data kept apart` verdict on both paths; `tests/test_conformance_check_a4.py`, `tests/test_conformance_windowless.py` and `tests/test_b2_least_confident.py` run conformance-check.py on other fixtures. `tests/test_completion_check.py`, `tests/test_header_plan.py` (which also asserts by syntax tree that completion-check calls `bridge_env.plan_r_ids_outside_headers`, line 621), `tests/test_header_plan_r2.py` (a syntax-tree check of the `bridge_env` attributes completion-check uses, line 298), `tests/test_header_plan_r3.py` and `tests/test_bug038.py` run completion-check.py; `tests/test_header_status.py` and `tests/test_header_currency.py` cover the header readings of both.

**The manifest.** `MANIFEST.json` holds a normalized sha256 (CRLF folded to LF, BOM dropped) of every file under `bridge/`. After your source edits it is stale for the two programs; `tools/make-manifest.py --version 2026.11.09a` rewrites `VERSION` (to `2026.11.09a` and a line feed) and the manifest, whose `generated` stamp changes. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` then compares the tree with it and prints `RESULT: SOURCES MATCH bridge 2026.11.09a`.

**Security context.** These are logic surfaces (record parsing in two checks): `.cursor/rules/secure-coding.mdc` is in force for you, and the project's ASVS level is 2 (`docs/INVENTORY.md`, Decisions). The trust boundary here is the records a session or a builder writes (`docs/INVENTORY.md`, `docs/BUILD_PLAN*.md`), which these programs read; this change moves no boundary: every header check (the inventory header's reading, `plan_header_findings` with its `return 2` on a fatal finding) runs on the same input as today.

**Development data** (`docs/INVENTORY.md`, Decisions): "the dev build is the Workspace sources under `bridge/`; a session in the repo always runs the *installed* bridge (`~/.claude`), never the one being edited, and installs reach running projects only through the owner's install run sheet". For you: the tests run the Workspace sources against pytest's temporary folders. Never run conformance-check.py or completion-check.py yourself against this repository's own records, and never run `bridge-install.py`.

## Diagrams
`docs/diagrams/D-002-components.md` — the elements `conformance_check`, `completion_check` and `bridge_env`. Each program keeps its existing import of `bridge_env` and gains no other; no edge is added or removed, so the diagram does not change. `docs/diagrams/D-005-header-schemas.md` (the header schemas) is untouched: no schema or reader of a header changes. **If the task cannot be done within them, stop and report the conflict (an objection) instead of deviating.**

## Requirements
1. **Checks first, before any edit; paste each command and its output in the report.** From the Workspace root, run `git grep -n -e inventory_development_data -e inv_dev_from_header -- bridge/cursor-bridge/conformance-check.py` and `git grep -n -e plan_header_findings -e plan_r_ids_outside_headers -e headed_texts -- bridge/cursor-bridge/completion-check.py`, and confirm: `inv_dev_from_header` is assigned only at lines 1243 and 1266; `inventory_development_data` is called once, at line 1293, as an `elif` condition; in completion-check.py `plan_header_findings` is called at lines 207 and 225 only and `plan_r_ids_outside_headers` at line 228 only; the name you choose for the new list is not already used in the file. Where a check does not hold, leave that item undone, say so in the report, and go on with the other.
2. **Item 1.** conformance-check.py lines 1288-1296 become the one `dev_ok` assignment and the one `if`/`else` the Objective states; the comment line 1287 stays; each `add(...)` text stays byte-identical.
3. **Item 2.** completion-check.py's first plan loop keeps the text of each headed plan; the disagreement loop iterates those texts with no second read and no second `plan_header_findings` call; every line the Objective names as staying, stays byte-identical.
4. **Item 3.** After your last edit to a source file, run `python tools/make-manifest.py --version 2026.11.09a` once, then the bridge-check command in the Constraints.
5. No other line of the two programs changes. Each file keeps its CRLF line endings and gains no trailing whitespace.

## Acceptance criteria
- [ ] Behaviour is identical: the same printed lines and exit codes for every input (the one undefended case is a plan file changed on disk during a run, see Context).
- [ ] The named test files pass before and after the edit with the **same** test set: the same count passed, none failed, none newly skipped; both summary lines quoted in the report. None edited.
- [ ] Each item is done, or reported as not applicable with the reason.
- [ ] In conformance-check.py the string `"Development data kept apart"` appears exactly three times (the ImportError line 1275, the one OK line, the one MISSING line), and `rule 55; the design states it` once; `inventory_development_data` is called once, and only when `inv_dev_from_header is None`.
- [ ] In completion-check.py `bridge_env.plan_header_findings` is called once, `read(p)` appears once, and `bridge_env.plan_r_ids_outside_headers` is called once; `fails.append("HEADER DISAGREES: satisfies")` and `                    if rid not in header_union:` are present byte-identical.
- [ ] No public signature changed; no new function, no new import.
- [ ] `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge` ends with `0 FAIL` and exit 0.
- [ ] `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` prints `RESULT: SOURCES MATCH bridge 2026.11.09a`.
- [ ] `python bridge/cursor-bridge/refactor-check.py HEAD --max-lines 400` prints a line starting `PURE:` (the base is the commit you were launched on: the branch already holds the supervisor's tests-lane commit, which a base of `origin/main` would count as a test edit).
- [ ] `git diff --stat` shows only the three Scope product files (plus the report, if you wrote one the builder-notes line, and `bridge/cursor-bridge/VERSION` if make-manifest's LF rewrite shows it, reported as such); `bridge/cursor-bridge/bridge_env.py`, every file under `tests/` you did not find already modified, `docs/CHANGES.md` and `bridge/cursor-bridge/CHANGELOG.md` unchanged; no mutation script in the diff.

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
- Every verification command is written here in full. Run exactly these, each from the Workspace root (the folder you were started in), each in the foreground, never in the background; run pytest directly as written, never through a launcher:
  - At the start: `git status --short` and `git rev-parse HEAD`, pasted into the report (they show which test files, if any, were already modified before your run).
  - Before the edit, and again after the last edit: `python -m pytest -p no:cacheprovider -q -rs tests/test_conformance_check.py tests/test_conformance_check_a4.py tests/test_conformance_windowless.py tests/test_b2_least_confident.py tests/test_completion_check.py tests/test_bug038.py tests/test_header_tables.py tests/test_header_tables_r2.py tests/test_header_plan.py tests/test_header_plan_r2.py tests/test_header_plan_r3.py tests/test_header_status.py tests/test_header_currency.py`
  - After the last source edit, in this order: `python tools/make-manifest.py --version 2026.11.09a`; `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`; `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge`; `python bridge/cursor-bridge/refactor-check.py HEAD --max-lines 400`.
  - At the end: `git status --short`, `git diff --stat` and `git rev-parse HEAD`, pasted into the report.
  - Do not run the whole `tests/` tree or any other test file (a builder of this release that ran the whole tree reached its limit, ISS-030); the supervisor runs the full suite after your run. If a test fails before your edit, stop and report it; do not fix it. If `refactor-check.py` prints IMPURE naming only test files that `git status --short` already showed modified at the start, quote it, say so, and touch nothing.
- Mutation checking is the supervisor's in this task: it re-anchors and re-runs its mutants after your run. Run no mutation, write no mutation script, and let none land in the diff.
- Prefer reuse over new code and write the minimum that meets the acceptance criteria (the frozen `minimal-code.mdc` is in force). This never overrides a security, observability, or accessibility requirement stated above.
- **Refactoring constraints.** Do not edit any test file. Do not add an entry to `docs/CHANGES.md`. Do not "improve" behaviour, messages, edge cases, or defaults you notice along the way; report them in your summary instead. Do not introduce an abstraction beyond what the listed duplicates need: the new names are the local `dev_ok` in conformance-check.py's `main` and one local list in completion-check.py's `main`; no helper function, nothing new in `bridge_env`.
- **No computer path in the report.** Where quoted output holds the repository's absolute folder, write `<the Workspace>` in its place; paste no other absolute path of this machine.

## Done
Your report is the file `handoff/REFAC-006-r1-report.md`, which you write as you go (what you did, what you changed, what you ran and what it printed, what you could not do) so that nothing of it is lost when your run ends early. When you finish, it holds:
- a list of every file you changed;
- a one-paragraph summary of what you did;
- for each of items 1, 2 and 3: done, or not applicable with the reason; the Requirements 1 grep commands with their output as the evidence;
- the before and after outputs of the pytest command, with both summary lines;
- the outputs of make-manifest, bridge-check, windowless-check and refactor-check, each line that shows the result quoted;
- `git status --short`, `git diff --stat` and `git rev-parse HEAD` at the start and at the end, and whether the working tree held uncommitted changes then (say whether `bridge/cursor-bridge/VERSION` shows as modified, and that you left it);
- one sentence stating why the behaviour is identical;
- anything you noticed but did not change (per the refactoring constraints);
- a final section headed exactly `Assumed, not verified`: every fact this change relies on that neither this brief nor the existing code settled, and that you did not confirm (an ambiguous requirement you resolved one way, a platform or library behaviour you expected, a value you chose). One item per line: what you assumed · why · what would confirm it. If there are none, write `Assumed, not verified: none`. Be specific: "edge cases" or "error handling" is not an item.

Every command you ran is quoted in the report with the lines it printed, verbatim (with `<the Workspace>` in place of the repository's folder), in a fenced block; a count, or a claim that a check passed, quotes the output line that shows it. A command you did not run is written `not run`, never described as run.

Your last message is the summary and the report file's path, and nothing follows it: the supervisor reads only the last message, and a message printed earlier and then followed by more work is lost.
