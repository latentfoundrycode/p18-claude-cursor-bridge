# TASK-008: The Workflows status line: enforced

## Objective
Every project's status file (`docs/PROJECT_STATUS.md`) now carries a `Workflows:` line per part, beside `Phase:`. It names the part's product type, sub-type and traits, in a grammar the supervisor's instructions define. `bridge/cursor-bridge/workflow-check.py` (TASK-006) already validates those lines against the open list. This increment makes the two programs the supervisor runs on every project's records enforce the line too: `inventory-check.py` (run at every accepted increment) and `conformance-check.py` (run at every calibration and reflection point). Each reports a missing line, a malformed line, and lines that do not stand together right after the `Phase:` line. One rule lives in one place. So both programs judge the grammar by loading `workflow-check.py` and calling its existing `check_status`. The placement rule is one new function in `workflow-check.py`, called only by these two programs. `workflow-check.py`'s own command-line behaviour does not change.

Satisfies:
- R-015 — The status file records a `Workflows:` line per part (product type, sub-type, traits) beside the `Phase:` line.

## Scope
Files you may create or modify:
- bridge/cursor-bridge/inventory-check.py
- bridge/cursor-bridge/conformance-check.py
- bridge/cursor-bridge/workflow-check.py (only to add the one function of Requirement 1; nothing else in it changes)
- bridge/cursor-bridge/MANIFEST.json (regenerated with `python tools/make-manifest.py` after your last edit under `bridge/`)
- docs/BUILDER_NOTES.md
- handoff/TASK-008-r1-report.md

Do not modify anything else.

## Written by the supervisor; do not edit
These files are committed with this brief. Do not edit, move, rename or add to them:
- `tests/test_workflows_line_check.py` (names R-015). It covers a valid line, a missing line, a malformed line and a misplaced line, through both programs. It also calls `check_placement` directly, loading `workflow-check.py` through `tests/conftest.py`'s `load_program`.
- `tests/test_conformance_check.py`. Its `make_workspace` status file now carries `Workflows: not yet classified`, so the conformant workspace stays conformant.
- `tests/test_workflow_check.py` and everything under `tests/fixtures/workflows/`. They must pass unchanged. That is how `workflow-check.py`'s behaviour is shown to be unchanged.

Suppose a supervisor test contradicts this brief, or cannot pass without breaking a requirement below. Then stop, change no test, and report the contradiction: the test name, the brief requirement, and what each says.

## Out of scope
- .env and anything under secrets/
- CI configuration (`.github/workflows/`)
- docs/ and handoff/, except the files the Scope section names
- Everything under `bridge/` except the four files in Scope. In particular these stay unedited: `bridge/commands/supervisor.md`, `workflow/open-list.md`, `workflow/extension-points.md`, `CHANGELOG.md`, `VERSION`.
- In `workflow-check.py`, everything except adding `check_placement`: its module docstring (which is its `--help` text), `main`, `check_status`, every other function, its finding codes, its output and its exit codes.
- The other checks of `inventory-check.py` and `conformance-check.py`. That includes `inventory-check.py`'s status-length cap, which counts lines with `str.splitlines()` and stays as it is: it does not read the `Workflows:` line.
- Checking that several parts' lines come "in the order of the project's parts". Nothing records that order elsewhere, so it is not checkable.

## Context
The repository root is the folder you were started in. Paths are relative to it.

**The line's grammar.** Quoted from `bridge/commands/supervisor.md`, section "Project state", lines 1817–1828:

`Workflows: [<part>: ]<Workflow name>[ → <Sub-workflow name>]; traits: <Trait name>[, <Trait name>…]`

- "the product type is named by its **Workflow name**, the sub-type by its **Sub-workflow name** and each trait by its **Name**, spelled exactly as `~/.claude/cursor-bridge/workflow/open-list.md` spells them; every name on the line is in the open list;"
- "exactly one product type and at most one of its sub-types; ` → <Sub-workflow name>` (the arrow is `→`) is left out when the part has no sub-type;"
- "the traits follow `; traits: `, separated by a comma and a space, in the order the open list gives them; a part with no trait reads `; traits: none`;"
- "`<part>: `, the part's name and a colon, follows `Workflows: ` only when the project has more than one part; a project with one part has one line without it; a part's name contains no `:`, `;` or `→`;"
- "with several parts, the lines stand together right after `Phase:`, one per part, in the order of the project's parts;"
- "until intake has classified a part, its line reads `not yet classified` in place of the names (`Workflows: not yet classified` in a project with one part)."

In the template (`supervisor.md` lines 1788–1791) the line follows `Phase: <…>` directly. Example, the bridge itself: `Workflows: Host Extension Development → Claude Code Extension; traits: Installable`.

**What `workflow-check.py` already provides.** These are module-level names in `bridge/cursor-bridge/workflow-check.py`, quoted. Importing the file runs no check: its `main` runs only under `if __name__ == "__main__":`.
- `HERE = os.path.dirname(os.path.abspath(__file__))`, `DEFAULT_OPEN = os.path.join(HERE, "workflow", "open-list.md")`, `DEFAULT_REGISTRY = os.path.join(HERE, "workflow", "extension-points.md")`.
- `def file_lines(text):` splits text only at a line feed. A final line feed adds no empty line. Form feed, vertical tab, `\x1c`–`\x1e`, NEL, U+2028 and U+2029 stay inside a line.
- `def read_utf8(path):` returns `(text, shown_path, reason)`. `reason` is `None` on success. Otherwise `text` is `None` and `reason` is plain language.
- `def load_tables(open_text, open_path, reg_text, reg_path):` returns `(tables, errors)`. `errors` is a list of `(path, reason)`. `tables` is `None` when `errors` is non-empty.
- `def check_status(path, text, tables):` returns findings, each a 4-tuple `(code, shown_path, name, reason)`. These are its exact reason strings, with the code each carries:
  - `form`, name `-`: `status file has no Workflows line`. This one means the line is **missing**.
  - `form`: `Workflows line breaks the part-prefix rule`
  - `e`: `two Workflows lines name the same part`
  - `form`: `Workflows line must contain '; traits: ' exactly once`
  - `form`: `empty name in the Workflows head`
  - `unknown`: `name is not in the open list`
  - `e`: `part must name exactly one product type`
  - `e`: `part must name at most one sub-type`
  - `e`: `sub-type is not of the line's product type`
  - `form`: `Workflows head is not the product type, then at most its sub-type`
  - `form`: `traits are not joined by a comma and one space`
  - `unknown`: `not a trait name`
  - `form`: `trait repeated`
  - `form`: `traits are not in the open list's order`
  - `f`: `product type is not written` and `sub-type is not written`
  - `FLAG`: `trait not yet written; flagged, work continues (non-fatal)`
- `def escape_field(value):` keeps printable characters and turns every other character into `\xNN`, `\uNNNN` or `\UNNNNNNNN`.
- `def slash(path):` turns `\` into `/`.

`tests/conftest.py` shows the loading pattern, quoted:

```python
spec = importlib.util.spec_from_file_location(name.replace("-", "_"), path)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
```

**Why codes `f` and `FLAG` are not "malformed".** An unwritten product type or sub-type (`f`) is `workflow-check.py`'s "pause the project at intake" rule, and an unwritten trait (`FLAG`) is a non-fatal flag. Neither is a fault in the line's form. Today every type, sub-type and trait in the open list is unwritten. So the bridge's own line, `Workflows: Host Extension Development → Claude Code Extension; traits: Installable`, produces two `f` findings and one `FLAG`, and it must count as **valid** here.

**TASK-006's review lesson (binding).** Any code that reads the `Workflows:` or `Phase:` line splits a status file's text into lines exactly as `file_lines` does: only at a line feed, with the file read using universal newlines. Never use `str.splitlines()` for this. A line that holds a form feed or U+2028 is one line.

**The two programs today.**
- `inventory-check.py`: command line `python inventory-check.py [--inventory docs/INVENTORY.md] [--status docs/PROJECT_STATUS.md] [--changes docs/CHANGES.md] [--max-lines 120] [--max-chars 12000]`, run from the Workspace root.
  - It reads files with its own `read(path)`: `open(path, encoding="utf-8-sig", errors="replace")`. That is universal newlines, with any byte-order mark dropped.
  - It collects failure strings in `fails` and notes in `notes`. It prints `note: …` lines first, then each failure.
  - The last line is `RESULT: OK` or `RESULT: <n> problem(s)`, where `<n>` counts the failure lines that do not start with four spaces.
  - It exits `0`, or `1` when there is any failure.
  - When the status file does not exist it adds the note `status: <path> not found (skipped)`.
  - `tests/test_text_consistency.py` imports this file as a module (for `looks_secret`), so nothing new may run at import time.
- `conformance-check.py`: command line `python conformance-check.py [<project root or Workspace>] [--screens] [--installable] [--offline] [--quiet]`.
  - It resolves the Workspace `ws` and collects rows with `add(verdict, floor, detail="")`, where `verdict` is `OK`, `MISSING` or `NOTE`.
  - It prints each row as `"  %-8s %s%s" % (verdict, floor, ("  - " + detail) if detail else "")`. `--quiet` hides `OK` rows.
  - It exits `1` when any row is `MISSING` (last line `RESULT: <n> floor(s) missing - …`), otherwise `0` (`RESULT: CONFORMANT`). It exits `2` for "not a workspace".
  - Its `read(path)` is like inventory-check's but returns `None` on `OSError`. The records section (lines 419–432) checks `docs/PROJECT_STATUS.md` among the records.
  - Its docstring says "ASCII-only on purpose (cp1252 consoles). Never writes." The tests run it with `--offline` (`tests/test_conformance_check.py`, `run()`).
- Both programs already define `NO_WINDOW = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0` and pass it to every `subprocess.run`. This increment launches no new process.

**Where the rule files are.** `workflow-check.py`, `workflow/open-list.md` and `workflow/extension-points.md` sit beside `inventory-check.py` and `conformance-check.py`, in `bridge/cursor-bridge/` and in the installed `~/.claude/cursor-bridge/`. All three are in `MANIFEST.json`, so they install together. Each program finds them beside itself (`os.path.dirname(os.path.abspath(__file__))`), never in the checked project.

**The manifest.** Any change under `bridge/` regenerates `bridge/cursor-bridge/MANIFEST.json` with `python tools/make-manifest.py`, run after your last edit under `bridge/`. It takes the version from the newest heading in `bridge/cursor-bridge/CHANGELOG.md`, so `VERSION` is rewritten unchanged. CI's `bridge-check.py --root bridge --sources --quiet` fails if the manifest does not match the tree. Loading `workflow-check.py` writes a `__pycache__` beside it. make-manifest skips `__pycache__`, and so does the install check.

**Security context.** The surface is reading local Markdown files: the project's status file and the bridge's own open list and registry. There is no network access, no secret and no write.
- Trust boundary: the status file is project-authored text. It is never executed, imported or evaluated.
- The only code loaded is `workflow-check.py` from the program's own folder (the bridge's own source). It is never loaded from the checked project.
- A bad input never causes a traceback.
- No ASVS level is recorded for the bridge. There is no `.cursor/rules/` folder in this repository, so the constraints below are the whole set.

**Development data** (copied from `docs/INVENTORY.md` Decisions): "Development data: the dev build is the Workspace sources under `bridge/`; a session in the repo always runs the *installed* bridge (`~/.claude`), never the one being edited, and installs reach running projects only through the owner's install run sheet." For this increment, run the programs and tests from this repository's sources only, never from `~/.claude` and never on another project. The one read of this repository's own records is the read-only `inventory-check.py` run in Done step 1. `tests/conftest.py` already redirects `HOME`/`USERPROFILE` for every test.

## Diagrams
None. The build plan names no diagram for this increment (INVENTORY Decisions: no diagram index for release B).

## Requirements

### workflow-check.py: one new function
1. Add exactly one module-level function to `bridge/cursor-bridge/workflow-check.py`:

   `def check_placement(path, text):`

   - `path` is the status file's path (a string). `text` is its contents, already read.
   - It returns a list of findings in `check_status`'s shape. Each is a 4-tuple `("place", slash(path), "-", reason)`.
   - It splits `text` with `file_lines`.
   - A **Workflows line** is a line that starts with exactly `Workflows: `, as in `check_status`.
   - The **Phase line** is the first line that starts with exactly `Phase: `.
   - The rules, in this order:
     1. No Workflows line: return `[]`. The missing line is `check_status`'s finding, not this one's.
     2. Workflows lines but no Phase line: return exactly `[("place", slash(path), "-", "status file has no Phase line")]`.
     3. With the Phase line at index `p` and `k` Workflows lines in the file, the lines at indexes `p+1` to `p+k` must all be Workflows lines. Equivalently, every Workflows line stands in one unbroken run directly after the Phase line. If so, return `[]`. Otherwise return exactly `[("place", slash(path), "-", "Workflows lines do not stand together right after the Phase line")]`. That is one finding per file, however many lines are out of place.

   `check_placement` has a docstring stating that rule and naming R-015. It is called by `inventory-check.py` and `conformance-check.py` only. `workflow-check.py`'s `main`, its module docstring and every existing function stay byte-for-byte as they are. `tests/test_workflow_check.py` passes unchanged.

### The shared judgement (both programs)
2. Each program judges the status file in this order:
   1. Load `workflow-check.py` from its own folder with `importlib.util.spec_from_file_location`, inside the check and never at import time.
   2. Read the open list and registry at that module's `DEFAULT_OPEN` and `DEFAULT_REGISTRY` with its `read_utf8`.
   3. Build the tables with its `load_tables`.
   4. Run its `check_status(path, text, tables)` and its `check_placement(path, text)` on the status text.

   The status text is the text the program already reads with its own `read` (universal newlines, BOM dropped). The outcome is exactly one of four:
   - **not checked**: `workflow-check.py` is absent or raises while loading, the open list or registry cannot be read, or `load_tables` returns errors. This is a failure, never a note and never silence. No exception escapes and no traceback is printed.
   - **missing**: no line of `file_lines(text)` starts with `Workflows: `, which is exactly when `check_status` returns its `status file has no Workflows line` finding.
   - **malformed**: otherwise, if any finding remains after dropping every `check_status` finding whose code is `f` or `FLAG`. The remaining `check_status` findings come first, in their order, then `check_placement`'s finding if any.
   - **valid**: no finding remains.
3. Every field printed from a finding (`name`, `reason`) and every reason in a not-checked line goes through `workflow-check.py`'s `escape_field`. Then each non-ASCII character becomes its backslash escape (`\xNN`, `\uNNNN`, `\UNNNNNNNN`, as Python's `"backslashreplace"` error handler writes it). Both programs' output stays ASCII.
4. When the status file does not exist, neither program checks the line or prints anything about it. inventory-check keeps its existing note. conformance-check's records row already reports the missing file.

### inventory-check.py
5. The check runs right after the status-length cap (check 1) and before SHAPE, whenever the `--status` file exists. Each line below is one entry of `fails`, so it counts as one problem in the `RESULT:` line and makes the exit code `1`:
   - missing: `WORKFLOWS LINE: missing: <status> has no Workflows line`. Here `<status>` is the `--status` argument as given, with `\` turned into `/`.
   - malformed: one line per remaining finding: `WORKFLOWS LINE: malformed: <name> - <reason>`.
   - not checked: one line per cause: `WORKFLOWS LINE: not checked: <reason>`. For a `read_utf8` or `load_tables` error, `<reason>` is `<path>: <reason>`. For a module that cannot be loaded, it is `<path to workflow-check.py>: cannot be loaded (<exception class name>)`.
   - valid: no `WORKFLOWS LINE:` line at all.
6. The module docstring (the usage text) gains a numbered check, `6. WORKFLOWS LINE`, stating in one or two lines what it checks (missing, malformed, not right after `Phase:`; R-015). It also says the grammar is `workflow-check.py`'s, and that unwritten types and traits are that program's concern, not a failure here. Nothing else in the existing checks, options, output or exit codes changes.

### conformance-check.py
7. When `docs/PROJECT_STATUS.md` exists in the Workspace, add exactly one row with floor name `Workflows line`, among the records rows (after the loop over the record files):
   - valid: `add("OK", "Workflows line")`
   - missing: `add("MISSING", "Workflows line", "missing: docs/PROJECT_STATUS.md has no Workflows line")`
   - malformed: `add("MISSING", "Workflows line", "malformed: " + "; ".join(<"<name> - <reason>" for each remaining finding>))`
   - not checked: `add("MISSING", "Workflows line", "not checked: " + "; ".join(<each cause, worded as in Requirement 5>))`

   So the printed line begins `  MISSING  Workflows line  - missing: `, `  MISSING  Workflows line  - malformed: ` or `  MISSING  Workflows line  - not checked: `, or reads `  OK       Workflows line`. Exit codes, the summary line and `--quiet` behave as for every other row.
8. The module docstring's list of what it checks gains one item for the `Workflows:` line in `docs/PROJECT_STATUS.md`: missing, malformed, or not right after `Phase:` is MISSING (R-015). Nothing else in the program changes.

### The manifest
9. `bridge/cursor-bridge/MANIFEST.json` is regenerated with `python tools/make-manifest.py` after your last edit under `bridge/`. Its only changes are the three program hashes and the `generated` stamp.

## Acceptance criteria
- [ ] `python -m pytest tests/test_workflows_line_check.py -q` passes (the supervisor's tests, which name R-015).
- [ ] `python -m pytest tests/test_workflow_check.py tests/test_conformance_check.py -q` passes. `workflow-check.py`'s command-line behaviour is unchanged, and the conformant workspace stays conformant.
- [ ] `python -m pytest tests -q` passes in full.
- [ ] Against today's open list, a status file whose line is `Workflows: Host Extension Development → Claude Code Extension; traits: Installable` or `Workflows: not yet classified`, directly after `Phase: building`, is valid in both programs.
- [ ] A status file with no `Workflows:` line gives `WORKFLOWS LINE: missing: …` (inventory-check, exit 1) and `MISSING  Workflows line  - missing: …` (conformance-check, exit 1).
- [ ] A malformed line (for example one without `; traits: `, or naming a name not in the open list) gives `WORKFLOWS LINE: malformed: …` and `MISSING  Workflows line  - malformed: …`.
- [ ] A line not directly after `Phase:` (another line in between, or above `Phase:`) gives the malformed output with the reason `Workflows lines do not stand together right after the Phase line`. A status file with Workflows lines and no Phase line gives `status file has no Phase line`.
- [ ] A line separated from `Phase:` only by a form feed or U+2028 inside one line is judged with `file_lines` (the TASK-006 lesson). No new code splits a status file with `str.splitlines()`.
- [ ] If `workflow-check.py` or a rule file cannot be loaded, the check fails with a `not checked:` line or row. There is no traceback.
- [ ] Both programs' output stays ASCII.
- [ ] `windowless-check.py` and `bridge-check.py --sources` pass.
- [ ] R-015 is fully met: no stand-in, placeholder or "arrives in a later stage" text. The supervisor's test names R-015, and the new docstrings name it too.

## Constraints
- Do not add dependencies: standard library only.
- Do not read or write any file outside this workspace (the folder you were started in). Everything you need is inside it; everything you produce goes inside it.
- If the brief, the rules, or the tooling got in your way, append one dated line describing it to `docs/BUILDER_NOTES.md`. That covers an instruction that contradicted another, a check that fired wrongly, or a step that cost time for no reason. Do not try to fix the tooling. Do the same for anything you learned about a defect or a pitfall (a cause you found, a platform quirk that cost you a round): one dated line, so the supervisor can carry it forward.
- In any Markdown you write, never break a line inside a paragraph or a list item; one paragraph is one line. Line breaks only between blocks.
- Any console process your code launches on Windows is created windowless (`creationflags=subprocess.CREATE_NO_WINDOW`, `0` elsewhere; both programs already define `NO_WINDOW`). This increment should launch none.
- Never start a server, a watcher or a daemon that outlives a test.
- Do not refactor code outside the scope, even if it looks wrong. That includes the existing `splitlines()` uses in both programs that do not read the `Workflows:` or `Phase:` line.
- Never run the product, a migration, a seed or a test against the owner's live data. See the Development data paragraph in Context. Never run a program against `~/.claude` or another project.
- Follow existing conventions in the files you touch: the house style of each program, ASCII output, a final `RESULT:` line, and `backslashreplace` on stdout/stderr.
- These git commands are not yours to run: `commit`, `push`, `switch`, `checkout`, `merge`, `rebase`, `reset`, `stash`, `branch -d`, `worktree`. You read with `git status`, `git diff` and `git log` only.
- One rule, one place. The grammar is judged only by `workflow-check.py`'s `check_status`, and the placement only by the new `check_placement`. Neither program re-implements any part of either. If reuse turns out to need any other change to `workflow-check.py`, stop and report it rather than making it.
- No number is parsed from any input. The status file's content is never executed, imported or evaluated.
- Do not edit `tests/test_workflows_line_check.py`, `tests/test_conformance_check.py`, `tests/test_workflow_check.py` or anything under `tests/fixtures/workflows/` (see "Written by the supervisor; do not edit").
- Every verification command the Done section asks you to run is written there in full. Run exactly those.
- Prefer reuse over new code (the functions of `workflow-check.py` quoted in Context, the standard library), and write the minimum that meets the acceptance criteria.

## Done
Run each of these from the repository root (the folder you were started in), in this order. Paste each command with its exit code and the relevant output lines into your report:
1. `python bridge/cursor-bridge/inventory-check.py` (read-only, on this repository's own records). Expected: no `WORKFLOWS LINE:` line. Report its exit code and `RESULT:` line whatever they are, and do not change any record to alter them.
2. `python -m pytest tests/test_workflows_line_check.py -q`
3. `python -m pytest tests/test_workflow_check.py tests/test_conformance_check.py -q`
4. `python -m pytest tests -q`
5. `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge`
6. `python tools/make-manifest.py`, then `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`
7. `git diff --stat`. Expected files: the three programs, the manifest, your report, and possibly `docs/BUILDER_NOTES.md`.

Your report is the file `handoff/TASK-008-r1-report.md`, which you write as you go: what you did, what you changed, what you ran and what it printed, and what you could not do. That way nothing of it is lost when your run ends early. When you finish, it holds:
- a list of every file you changed;
- a one-paragraph summary of what you did;
- a section headed exactly `Assumed, not verified`. List every fact this change relies on that neither this brief nor the existing code settled, and that you did not confirm. Examples: how you placed the new row among conformance-check's records rows, the exception classes you treat as "cannot be loaded", or a platform behaviour you expected. One item per line: what you assumed · why · what would confirm it. If there are none, write `Assumed, not verified: none`. Be specific: "edge cases" or "error handling" is not an item.

Your last message is the summary and the report file's path, and nothing follows it: the supervisor reads only the last message, and a message printed earlier and then followed by more work is lost.
