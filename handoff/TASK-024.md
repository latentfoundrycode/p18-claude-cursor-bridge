# TASK-024: Calibration aware of conditional workflows (program)

## Objective
Calibration runs `conformance-check.py` (bridge/commands/calibrate-bridge.md, step 1b), and that program already loads `workflow-check.py` and judges the status file's `Workflows:` lines through `judge_workflows_line`. It drops two kinds of finding, though. The first is workflow-check's code `f`: a product type or sub-type the open list marks not written. The second is code `FLAG`: a trait not written. So a line that names an unwritten workflow reads OK. It also accepts `Workflows: not yet classified` whatever the project's phase. This increment closes exactly that gap and nothing else in the program changes. Calibration then learns from the program which running project names a workflow the bridge has not written, which trait is unwritten, and which project is still unclassified past intake. That gives step 4b (the conditional-workflows step that TASK-023 wrote) what it needs. The grades are the supervisor's decision, recorded in docs/INVENTORY.md's Decisions row "TASK-024's grades". In short: an unwritten type or sub-type is MISSING; an unwritten trait is a NOTE and work continues; `not yet classified` is OK at intake and a NOTE past it, never MISSING, because step 4b has a project past intake run on the main workflow alone while its line reads `not yet classified`.

Satisfies:
- R-027: Calibration is aware of conditional workflows. It applies a conditional workflow to running projects of that product type by phase, reopening no gate. The applied text takes effect from a project's next design phase or change cycle.
- R-033: The workflow check runs at every bridge release (CI) and at every calibration.

## Scope
One brief carries one increment's scope; work that needs a second scope is a second brief, never a second section here.
Files and directories you may create or modify:
- bridge/cursor-bridge/conformance-check.py
- bridge/cursor-bridge/MANIFEST.json
- tests/test_calibrate_program.py (new)
- tests/test_workflows_line_check.py (only the change named in Requirement 9)
- tests/test_b2_least_confident.py (only the change named in Requirement 10)
- docs/cli-reference.json
- docs/CLI_REFERENCE.md
- docs/BUILDER_NOTES.md
- handoff/TASK-024-r1-report.md

Do not modify anything else.

## Out of scope
- .env and anything under secrets/
- CI configuration (.github/)
- docs/ and handoff/, except the files the Scope section names
- bridge/cursor-bridge/workflow-check.py, inventory-check.py, and everything under bridge/cursor-bridge/workflow/ (the open list and the registry): read them, do not change them, not even to make a test easier
- bridge/cursor-bridge/VERSION and CHANGELOG.md, and docs/CHANGES.md
- tests/test_conformance_check.py and its `make_workspace` helper, tests/conftest.py, and every other test file not listed in Scope
- bridge/commands/ (the text half is TASK-023's, already merged)

## Context
**What exists, in bridge/cursor-bridge/conformance-check.py:**
- `judge_workflows_line(path, text)` (lines 319-369). It loads `workflow-check.py` from beside the real file (`os.path.realpath(__file__)`), with `sys.dont_write_bytecode` set to True and restored in a `finally`. It reads the open list and registry through `mod.read_utf8(mod.DEFAULT_OPEN)` / `mod.read_utf8(mod.DEFAULT_REGISTRY)`, loads them with `mod.load_tables(...)`, runs `mod.check_status(path, text, tables)`, drops findings whose code is `"f"` or `"FLAG"` (line 361), returns `("missing", [])` when a finding reads `status file has no Workflows line`, then adds `mod.check_placement(path, text)`.
- It returns `(outcome, rows)`, where outcome is `valid`, `missing`, `malformed` or `not-checked`. For malformed, rows are `(name, reason)`; for not-checked they are reasons. Every printed field goes through the inner helpers `ascii_text(value)` (ASCII with `backslashreplace`) and `field(mod, value)` (`ascii_text(mod.escape_field(value))`).
- `main()` (lines 544-556) prints its rows through `add(verdict, floor, detail)`, and only when `docs/PROJECT_STATUS.md` is a file:
  - `("OK", "Workflows line")`
  - `("MISSING", "Workflows line", "missing: docs/PROJECT_STATUS.md has no Workflows line")`
  - `("MISSING", "Workflows line", "malformed: " + "; ".join("%s - %s" % (name, reason) ...))`
  - `("MISSING", "Workflows line", "not checked: " + "; ".join(rows))`
- Output lines are `"  %-8s %s%s" % (verdict, floor, "  - " + detail)`. Exit 1 when any MISSING, else 0. A NOTE does not change the exit code.
- The module docstring's Workflows bullet (lines 41-42) reads: "the Workflows: line in docs/PROJECT_STATUS.md: missing, malformed, or not right after Phase: is MISSING (R-015);".

**What exists, in bridge/cursor-bridge/workflow-check.py (read only):**
- Findings are tuples `(code, shown_path, name, reason)`.
- `check_head` (lines 603-641) gives `("f", path, <Workflow name>, "product type is not written")` and `("f", path, <Sub-workflow name>, "sub-type is not written")`, and only when the head is otherwise well formed.
- `check_traits` (lines 644-671) gives `("FLAG", path, <trait name>, "trait not yet written; flagged, work continues (non-fatal)")`.
- `check_status` (lines 674-700) reads only lines that start with exactly `Workflows: `. Its multi-part grammar is `Workflows: <part>: <body>` (`prefix_of`, from about line 578). It skips a body that is exactly `not yet classified`.
- `check_placement` (lines 703-731): the Phase line is the first line that starts with exactly `Phase: `, with text split only at a line feed (`file_lines`).
- `escape_field(value)` (line 129) is the escape every judge applies.

**The phase values** (bridge/cursor-bridge/Glossary.md, entry **Phase**): intake, design, mockups, planning, configuration, building, done, changing. The intake value is the lowercase word `intake`. Real status files can carry more after the value, e.g. `Phase: building (Stage 2)`.

**The open list as it stands** (bridge/cursor-bridge/workflow/open-list.md, column `Written`): a few entries are `no`; a test that relies on one must assert that precondition (see below).
- Written `yes`: `Host Extension Development`, `Claude Code Extension`, `Installable`, `Web App Development`, `Local Web App`, `Own-Computer Software Development`, `Local Service Software`.
- Written `no`: e.g. `Website Development`, `CLI Software` (a sub-type of the written `Own-Computer Software Development`), and the trait `Personal data`.

**The bridge's own status file** (docs/PROJECT_STATUS.md, read only) holds `Phase: building` followed by `Workflows: Host Extension Development → Claude Code Extension; traits: Installable`. All three names are written.

**The calibration text this program serves:** bridge/commands/calibrate-bridge.md, step 1b ("Every `MISSING` becomes a calibration item ...; a `NOTE` is recorded in `PROJECT_STATUS.md`") and step 4b, the paragraph that ends "A project past intake is never paused for its classification: ... its line reads `not yet classified`, which the check accepts, ... and the project runs on the main workflow alone until the line is written."

**Existing tests and the approach to reuse** (tests/test_workflows_line_check.py):
- `_bridge_copy(tmp_path)` copies `inventory-check.py`, `conformance-check.py`, `workflow-check.py` and the `workflow/` folder into a temporary folder.
- `_unwritten_copy(tmp_path)` additionally rewrites the copy's open list so every `| yes |` reads `| no |`, and asserts as a precondition that `check_status` now gives `f` and `FLAG` for the bridge line.
- `conformance(root, program=...)` runs a copy with `--offline`. `workspace(tmp_path, status_text)` builds a conformant workspace via tests/test_conformance_check.py's `make_workspace` and writes the status file. `verdict(out, floor)` (from tests/test_conformance_check.py) returns the first row whose floor starts with the given text.
- Build test fixtures the same way: a copy under the test's temporary folder whose open list is edited, with the precondition asserted. Never edit the installed tables. The existing helpers may be imported from `test_workflows_line_check` and `test_conformance_check`, as tests/test_b2_least_confident.py already does.
- tests/conftest.py's autouse `home_of_the_tests` points HOME/USERPROFILE at a temporary folder. Its `program` fixture loads a bridge program by name.

**Tests this change must keep green, unchanged:**
- In tests/test_workflows_line_check.py, every test except the one case named in Requirement 9. In particular `test_r015_a_valid_line_is_judged_valid_with_no_rows` (the judge on an unwritten copy returns `("valid", [])` for the bridge line and for `not yet classified`), `test_r015_conformance_no_status_file_no_check` (with no status file, `"workflows" not in out.lower()`), and every test that reads `verdict(out, "Workflows line")` as `("OK", "Workflows line")` on a `Phase: building` + `Workflows: not yet classified` file.
- tests/test_conformance_check.py, test_conformance_check_a4.py, test_a4_review_fixes.py, test_a4_followups.py and test_hotfix25a_conformance_semgrep.py, all of which build on `make_workspace`. Its status file (`Phase: building`, `Workflows: not yet classified`) will now also print the `Workflows classification` NOTE. They assert exit 0 / CONFORMANT, which a NOTE does not change.
- tests/test_b2_least_confident.py, except the one change in Requirement 10.

**Security context.** The status file is project-written text and is untrusted input to this program. The trust boundary is between that text (and the open-list tables) and the console output, which ends up in calibration reports and in `PROJECT_STATUS.md`. The project's ASVS level is 5.0.0 L2 (docs/INVENTORY.md). The rule `.cursor/rules/secure-coding.mdc` is already in force for you.

**Development data** (docs/INVENTORY.md Decisions row): "Development data: the dev build is the Workspace sources under `bridge/`; a session in the repo always runs the *installed* bridge (`~/.claude`), never the one being edited, and installs reach running projects only through the owner's install run sheet". For you this means:
- Run the programs from `bridge/cursor-bridge/` in this Workspace, or from copies under a test's temporary folder.
- Never run anything under the home folder's `.claude`.
- Never point the program at another project's Workspace.
- The bridge's own docs/PROJECT_STATUS.md may be read, never written.

## Diagrams
None. The build plan names no diagram for this increment.

## Requirements
1. **Unwritten type or sub-type.** When the line is otherwise valid (the existing judge's outcome is `valid`) and workflow-check gives one or more `f` findings, the row is `("MISSING", "Workflows line", "names an unwritten workflow: " + "; ".join("<name> - <reason>"))`, one item per `f` finding in check_status's order. Name and reason are the finding's own, e.g. `names an unwritten workflow: Website Development - product type is not written`. The exit code is then 1.
2. **Unwritten trait.** When the line is otherwise valid and workflow-check gives `FLAG` findings, the `Workflows line` row keeps its verdict (OK if nothing else is wrong; MISSING under Requirement 1 if an `f` is also present). After it comes one `("NOTE", "Unwritten trait", "<trait name> - <reason>")` row per `FLAG` finding, in check_status's order. The reason is the finding's own text, which says work continues.
3. **`not yet classified`.**
   - The Phase value is read as check_placement reads it: the first line that starts with exactly `Phase: `, text split only at a line feed. Take the first whitespace-separated word after the prefix, or the empty string when there is none.
   - If that word is exactly `intake`, a `not yet classified` part is OK.
   - Otherwise, each part whose body is exactly `not yet classified` gives one `("NOTE", "Workflows classification", "unclassified past intake (Phase: <first word>); calibration step 4b classifies it, the project running on the main workflow alone meanwhile")` row, and the `Workflows line` row stays OK.
   - It is never MISSING.
   - Parts are judged per part in a multi-part file (`Workflows: <part>: ...`): classified parts are graded by Requirements 1-2, and each unclassified part adds its own NOTE row. A missing Phase line is already a placement finding (malformed, MISSING) under today's code, and stays so.
4. **Precedence.** When the existing judge's outcome is `missing`, `malformed` or `not-checked`, today's single row is printed exactly as today and no row from Requirements 1-3 is added. When there is no `docs/PROJECT_STATUS.md` file, no row about the Workflows line is printed under any floor name, as today.
5. **Order.** The `Workflows line` row (OK or MISSING) is printed before any `Unwritten trait` or `Workflows classification` row. Neither NOTE floor name contains the words "Workflows line", so `verdict(out, "Workflows line")` and every test that reads the floor's first row see the same row as before.
6. **The judge's contract stays.** `judge_workflows_line(path, text)` keeps its `(outcome, rows)` return and its behaviour for every case its tests pin, including dropping `f` and `FLAG` and `("valid", [])` for `not yet classified`. The new grades come from a separate function, or from information that only `main()` reads; the choice is yours, as long as no existing test of the judge changes. Any new loading of workflow-check.py keeps today's guarantees: loaded from beside the real file, no bytecode written, `sys.dont_write_bytecode` restored in a `finally`, and a load failure reported as today's `not checked` row, never as a traceback.
7. **What is printed.**
   - Every name, reason and Phase word printed goes through workflow-check's `escape_field` and then the existing `ascii_text`, as `field(mod, value)` does today.
   - Of the status file's content, only the Phase line's first word and the workflow and trait names of the findings are printed. Part prefixes and other lines are not printed, so the per-part NOTE rows of Requirement 3 carry no part name.
   - The program still writes nothing.
8. **The docstring.** The module docstring's Workflows bullet (lines 41-42) states what is now reported:
   - missing, malformed or misplaced: MISSING (R-015)
   - a line naming an unwritten product type or sub-type: MISSING
   - an unwritten trait: a NOTE `Unwritten trait`
   - `not yet classified` past intake: a NOTE `Workflows classification` (calibration step 4b; R-027, R-033)

   Keep it ASCII, like the rest of the docstring.
9. **tests/test_workflows_line_check.py.** Only the `bridge-line` case of `test_r015_conformance_valid_line_is_ok` changes. On its unwritten copy it now expects the `Workflows line` row MISSING, naming `Host Extension Development - product type is not written` and `Claude Code Extension - sub-type is not written`, then an `Unwritten trait` NOTE naming `Installable`, and exit 1. The `not-yet-classified` case keeps its present assertions (OK, exit 0, CONFORMANT) word for word. You may split the parametrisation to do this. If any other test or case in that file would have to change, stop and report it instead of changing it.
10. **tests/test_b2_least_confident.py.** One change only. In `plain_notes(tmp_path)`, after `make_workspace(root)`, overwrite that baseline workspace's `docs/PROJECT_STATUS.md` with a status file written inside the test:
    - the minimal file's lines (`# Project Status`, `Bridge version: <VERSION>`, `Phase: building`)
    - then `Workflows: Host Extension Development → Claude Code Extension; traits: Installable` right after the `Phase:` line (the file already has `ARROW` and `VERSION`)

    The baseline's NOTE list then compares like with like against the classified shaped files. `plain_notes`' docstring may be updated to say so. Do not filter a NOTE out, do not touch `make_workspace` or tests/test_conformance_check.py, and change no other line of the file. If anything else there must change, stop and report it.
11. **tests/test_calibrate_program.py** (new). Every test names R-027 and R-033 in its name or docstring. Status files are built inside the test under its temporary folder, never a real project's file, except the last case, which only reads the bridge's own file. Tables with unwritten entries come from a bridge copy under the test's temporary folder whose open list is edited, as `_unwritten_copy` does. Each such test asserts its precondition (that `check_status` gives the expected `f` / `FLAG` finding on the copy), so it cannot pass vacuously when a release writes the entry. The installed tables are never edited and never monkeypatched on disk. The cases, each asserting the exact row(s) and the exit code:
    - (a) a classified project whose line names written workflows only: `Workflows line` OK, no `Unwritten trait` or `Workflows classification` row;
    - (b) `not yet classified` at `Phase: intake`: OK and no `Workflows classification` row;
    - (c) `not yet classified` at `Phase: building`: `Workflows line` OK, then the `Workflows classification` NOTE with `(Phase: building)`;
    - (d) a value with more after its first word (e.g. `Phase: building (Stage 2)`): only `building` is printed;
    - (e) a line naming an unwritten product type: MISSING with the detail of Requirement 1;
    - (f) a line naming a written type and an unwritten sub-type: MISSING naming the sub-type;
    - (g) an unwritten trait on otherwise written names: `Workflows line` OK, the `Unwritten trait` NOTE, exit 0;
    - (h) a multi-part file mixing a written part, an unwritten-trait part and an unclassified part past intake: one row per Requirement, in order;
    - (i) a non-ASCII and an escape-character name in an unwritten finding reach the output escaped (ASCII only, as `test_r015_conformance_output_is_ascii` checks);
    - (j) the bridge's own docs/PROJECT_STATUS.md, judged by the program's grading as it reads that file: `Workflows line` OK and no `Unwritten trait` or `Workflows classification` row. Run conformance-check.py on a temporary workspace whose status file is a copy of that file's text, or call the grading function in-process on the text; never write the real file.
12. **Windowless.** No new subprocess is expected. Any process a test or the program starts carries `creationflags=subprocess.CREATE_NO_WINDOW` on Windows (`0` elsewhere), as this file's `gh` and `git` calls and the existing tests' `conformance()` do.
13. **Command reference and manifest.** No command-line option changes. The docstring is the program's usage in the command reference, so after Requirement 8:
    - run `python tools/dump-cli.py --check`; if it fails, regenerate with `python tools/dump-cli.py` and run `--check` again until it passes;
    - regenerate the manifest with `python tools/make-manifest.py --version 2026.10.25a` (VERSION already reads `2026.10.25a`, so its rewrite is identical).

## Acceptance criteria
- [ ] A conformant workspace whose line names an unwritten product type or sub-type prints `MISSING  Workflows line  - names an unwritten workflow: <name> - <reason>` and exits 1.
- [ ] An unwritten trait leaves `Workflows line` OK and prints an `Unwritten trait` NOTE naming the trait and that work continues; exit 0 if nothing else is missing.
- [ ] `Workflows: not yet classified` is OK with no extra row at `Phase: intake`. Past intake it prints a `Workflows classification` NOTE with the Phase's first word, escaped, and is never MISSING. Multi-part files are graded per part.
- [ ] The `Workflows line` row precedes every new NOTE row. Neither NOTE floor name contains "Workflows line". With no status file, nothing about the Workflows line is printed.
- [ ] `judge_workflows_line`'s outcome and rows are unchanged for every case its tests pin.
- [ ] Every value printed goes through `escape_field` and `ascii_text`; the program writes nothing; the output stays ASCII.
- [ ] The bridge's own docs/PROJECT_STATUS.md yields `Workflows line` OK and no new NOTE row.
- [ ] tests/test_workflows_line_check.py: only the `bridge-line` case of `test_r015_conformance_valid_line_is_ok` changed, and the whole file passes.
- [ ] tests/test_b2_least_confident.py: only `plain_notes` changed, as Requirement 10 says, and the whole file passes.
- [ ] tests/test_calibrate_program.py covers cases (a)-(j) of Requirement 11, and its tests name R-027 and R-033.
- [ ] The full suite passes: `python -m pytest tests -q --no-header -p no:cacheprovider`.
- [ ] `python tools/dump-cli.py --check` passes. bridge/cursor-bridge/MANIFEST.json is regenerated and matches the changed files.
- [ ] Every requirement under "Satisfies" is fully met (no stand-in, placeholder, "coming soon" or "arrives in a later stage" text), and at least one test names each requirement ID (in its name, docstring, or a comment) so the trace is checkable.
- [ ] No new Semgrep high findings; no new dependency.

## Constraints
- Do not add dependencies.
- Do not read or write any file outside this workspace (the folder you were started in). Everything you need is inside it; everything you produce goes inside it.
- If the brief, the rules, or the tooling got in your way (an instruction that contradicted another, a check that fired wrongly, a step that cost time for no reason), append one dated line describing it to `docs/BUILDER_NOTES.md`. Do not try to fix the tooling. Do the same for anything you learned about a defect or a pitfall (a cause you found, a platform quirk that cost you a round): one dated line, so the supervisor can carry it forward.
- In any Markdown you write, never break a line inside a paragraph or a list item; one paragraph is one line. Line breaks only between blocks.
- This increment talks to no external service. `conformance-check.py` keeps `--offline` in every test run, as the existing tests do.
- Any console process your code launches on Windows is created windowless (`creationflags=subprocess.CREATE_NO_WINDOW` in Python, `0` on other platforms). Capturing output does not prevent the window. A window is allowed only when it serves the user (they watch it or type into it); then write the reason at the call site as `windowless: visible-ok <reason>`.
- Never start a server, a watcher or a daemon that outlives a test. A process a test starts is waited for and its pipes are drained (`subprocess.run` with `capture_output=True`, as the existing helpers do).
- Do not refactor code outside the scope, even if it looks wrong. Inside conformance-check.py, change only the Workflows-line judgment, its use in `main()`, and the docstring bullet.
- Never run the product, a migration, a seed or a test against the owner's live data. The development data is the Workspace sources under `bridge/`, and copies of them under a test's temporary folder (see Context). Never run the installed bridge under the home folder, and never point a program at another project.
- No value in this brief is marked as the owner's. The grades are the supervisor's decision recorded in docs/INVENTORY.md ("TASK-024's grades"). If the work seems to need a different grade, stop and report it.
- Follow existing conventions in the files you touch: ASCII output, `add(verdict, floor, detail)`, the existing test helpers.
- These git commands are not yours to run: `commit`, `push`, `switch`, `checkout`, `merge`, `rebase`, `reset`, `stash`, `branch -d`, `worktree`. You read with `git status`, `git diff` and `git log` only.
- The one value parsed here is the Phase line's first word. Take it with `str.split()` on the text after the exact `Phase: ` prefix and compare it with the exact string `intake`. No number is parsed.
- Reports and notes never paste computer paths or user names. Write `<temporary folder>` or `<home>` instead.
- **Verification commands**, each run from the Workspace root (the folder you were started in):
  - the full suite, if your environment allows it: `python -m pytest tests -q --no-header -p no:cacheprovider`
  - otherwise, at least the changed test files and every file that builds on `make_workspace`: `python -m pytest tests/test_calibrate_program.py tests/test_workflows_line_check.py tests/test_b2_least_confident.py tests/test_conformance_check.py tests/test_conformance_check_a4.py tests/test_a4_review_fixes.py tests/test_a4_followups.py tests/test_hotfix25a_conformance_semgrep.py tests/test_dump_cli.py -q --no-header -p no:cacheprovider`
  - `python tools/dump-cli.py --check` (and `python tools/dump-cli.py` to regenerate if it fails)
  - `python tools/make-manifest.py --version 2026.10.25a`

  Say in the report which suite you ran and what it printed.
- **Mutation check, by hand, in your own run.** Mutate the new code in conformance-check.py in-process: edit it, run the relevant tests, restore it. Cover at least:
  - the `f` findings dropped again;
  - `FLAG` made MISSING;
  - the intake comparison inverted, or made a prefix match;
  - the whole Phase value printed instead of its first word;
  - the NOTE rows printed before the `Workflows line` row;
  - the escape removed from a printed name.

  List each mutation in the report with the test that caught it. No mutation script and no mutated code land in the diff.
- Prefer reuse over new code: the loaded workflow_check module's `check_status`, `file_lines`, `escape_field`, and the existing `ascii_text`/`field` helpers and test helpers. Write the minimum that meets the acceptance criteria. This never overrides a security, observability, or accessibility requirement stated above.

## Done
Your report is the file `handoff/TASK-024-r1-report.md`, which you write as you go (what you did, what you changed, what you ran and what it printed, what you could not do), so that nothing of it is lost when your run ends early. When you finish, it holds:
- a list of every file you changed;
- a one-paragraph summary of what you did;
- the mutation list;
- a section headed exactly `Assumed, not verified`: every fact this change relies on that neither this brief nor the existing code settled, and that you did not confirm. Examples: an ambiguous requirement you resolved one way, a platform or library behaviour you expected, a value you chose. One item per line: what you assumed · why · what would confirm it. If there are none, write `Assumed, not verified: none`. Be specific: "edge cases" or "error handling" is not an item.

Your last message is the summary and the report file's path, and nothing follows it: the supervisor reads only the last message, and a message printed earlier and then followed by more work is lost.
