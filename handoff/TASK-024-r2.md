# TASK-024 round 2: Calibration aware of conditional workflows (program), corrections after review

## Objective
This is round 2 of TASK-024. It corrects round 1 in place. The base is the round-1 brief, `handoff/TASK-024.md`: read it first, whole. Every requirement, constraint and decision in it still stands, except where this brief corrects it, and each correction quotes the round-1 text it replaces. Round 1 built the grading in `bridge/cursor-bridge/conformance-check.py` (`calibration_workflows_grades`, used by `main()`): an unwritten product type or sub-type makes the `Workflows line` row MISSING, an unwritten trait adds an `Unwritten trait` NOTE, and `not yet classified` past intake adds a `Workflows classification` NOTE. Review A found that the program's grades are right, but the tests do not meet round-1 Requirement 11. Four cases depend on the real open list without a copy or an asserted precondition. The multi-part case has two parts instead of three. The escape-character case has no escape character. Several rows are checked only by substring. Two escapes and the exact `intake` comparison are not covered by any test. Round 2 fixes those tests and corrects the docstring of `calibration_workflows_grades`. It also adds a test that ties that function's findings to `check_status`'s findings, so the function's own per-part parse cannot drift from it unnoticed. The program's grading logic and the printed output of every round-1 case stay the same.

Satisfies:
- R-027: Calibration is aware of conditional workflows. It applies a conditional workflow to running projects of that product type by phase, reopening no gate. The applied text takes effect from a project's next design phase or change cycle.
- R-033: The workflow check runs at every bridge release (CI) and at every calibration.

## Scope
One brief carries one increment's scope; work that needs a second scope is a second brief, never a second section here.
Files and directories you may create or modify:
- bridge/cursor-bridge/conformance-check.py
- bridge/cursor-bridge/MANIFEST.json
- tests/test_calibrate_program.py
- tests/test_workflows_line_check.py (only `test_r015_conformance_bridge_line_unwritten_is_missing_and_trait_note`, its new order check included)
- tests/test_b2_least_confident.py (no further change is expected; if one seems needed, stop and report it)
- docs/cli-reference.json
- docs/CLI_REFERENCE.md
- docs/BUILDER_NOTES.md
- handoff/TASK-024-r2-report.md

Do not modify anything else.

## Out of scope
- .env and anything under secrets/
- CI configuration (.github/)
- docs/ and handoff/, except the files the Scope section names. In particular, do not change `handoff/TASK-024.md` (the round-1 brief) or `handoff/TASK-024-r1-report.md` (the round-1 report).
- bridge/cursor-bridge/workflow-check.py, inventory-check.py, and everything under bridge/cursor-bridge/workflow/ (the open list and the registry): read them, do not change them, not even to make a test easier
- bridge/cursor-bridge/VERSION and CHANGELOG.md, and docs/CHANGES.md
- tests/test_conformance_check.py and its `make_workspace` helper, tests/conftest.py, and every other test file not listed in Scope
- bridge/commands/ (the text half is TASK-023's, already merged)
- **A shared loader.** `judge_workflows_line` and `calibration_workflows_grades` each load workflow-check.py and the tables with the same preamble. Do not merge them into one shared loader. That is a lead for the stage-close refactoring pass, not this round's work.
- **The way `calibration_workflows_grades` collects its findings.** Its per-part parse stays as round 1 wrote it (Requirement 10).
- The `project.json` phase NOTE in `main()` (conformance-check.py lines 665-670). It prints the status file's Phase value without escaping it. That predates this task, and the supervisor records it as a separate hardening lead: do not change it. Requirement 5 tells you how to test around it.

## Context
**What round 1 built, as it stands on this branch:**
- `calibration_workflows_grades(path, text)` in bridge/cursor-bridge/conformance-check.py, lines 374-454. It has its own loading preamble, copied from `judge_workflows_line` (lines 321-371). It reads the Phase word from the first `Phase: ` line, calls `mod.check_status(path, text, tables)` once (line 422), and keeps the `f` findings from that call. Then it walks the `Workflows: ` lines again with `mod.prefix_of`. For each classified part it calls `mod.check_head` and `mod.check_traits` again to collect the FLAG findings, and for each unclassified part past intake it adds the classification NOTE (lines 425-447). This yields the NOTE rows in status-file order. It returns `("MISSING", detail, notes)`, `("OK", "", notes)`, or `("not-checked", [reasons], [])` (lines 399, 411, 414, 454).
- Its docstring (line 377) says "workflows_verdict is OK or MISSING". That is wrong: the function also returns `not-checked`, with a list of ASCII reasons as the second value and an empty notes list. The `else` branch in `main()` relies on that (line 640: `add("MISSING", "Workflows line", "not checked: " + "; ".join(wdetail))`).
- `main()` calls it only when `judge_workflows_line` returned `valid` (lines 632-642). A valid judgment means that `check_status` gave no finding other than `f` and `FLAG`: the judge drops those two codes and calls any other finding malformed (lines 363-369). The findings are tuples `(code, shown_path, name, reason)`.
- `check_status` in workflow-check.py (lines 674-700) walks the `Workflows: ` lines in file order. For each part it calls `check_head` and then `check_traits`, and it skips a body that is exactly `not yet classified`. Because `calibration_workflows_grades` repeats that loop for its FLAG findings, the two could drift. Requirement 11's test guards against that.
- Rows print as `"  %-8s %s%s" % (verdict, floor, ("  - " + detail) if detail else "")` (line 913). `verdict(out, floor)` (tests/test_conformance_check.py) returns `(verdict, "<floor>  - <detail>")` for the first row whose floor starts with `floor`. When this brief says "the exact row", build the expected whole line with that format, or compare the `verdict(...)` pair in full. Never use a substring.

**The round-1 row texts, unchanged in round 2** (verdict, floor, detail):
- `("OK", "Workflows line", "")`
- `("MISSING", "Workflows line", "names an unwritten workflow: " + "; ".join("<name> - <reason>" for each f finding))`
- `("NOTE", "Unwritten trait", "<trait name> - trait not yet written; flagged, work continues (non-fatal)")`
- `("NOTE", "Workflows classification", "unclassified past intake (Phase: <first word>); calibration step 4b classifies it, the project running on the main workflow alone meanwhile")`

Every name and Phase word in them goes through `field(mod, value)`, that is `ascii_text(mod.escape_field(value))`. `escape_field` (workflow-check.py line 129) keeps only printable ASCII. Every other character becomes `\xNN`, `\uNNNN` or `\UNNNNNNNN`, so `chr(0x1B)` becomes the four characters `\x1b` and `chr(0xDC)` becomes `\xdc`. `ascii_text` alone would leave a raw ESC in the output, because ESC is ASCII. Only an ESC character in a test tells the two apart.

**tests/test_calibrate_program.py as round 1 left it:** cases (a)-(j), one test each. The helper `rows_for_floor(out, floor)` returns the whole printed lines whose verdict is OK, MISSING or NOTE and that contain `floor`. Cases (e) `test_r027_r033_unwritten_product_type`, (f) `test_r027_r033_unwritten_sub_type`, (g) `test_r027_r033_unwritten_trait_on_written_names` and (h) `test_r027_r033_multipart_mixed` run the Workspace program against the real open list. They depend on `Website Development`, `CLI Software` and `Personal data` being unwritten there, and they neither copy the list nor assert that precondition. Case (i) `test_r027_r033_unwritten_finding_output_is_escaped_ascii` is already built the right way: it uses `_bridge_copy`, edits the copy's open list (`| Website Development | has-screens | no |`), asserts `load_tables` gives no errors and `check_status` gives `f`, then runs `program=folder / "conformance-check.py"`. Its name, `"Z" + chr(0xDC) + "test; comma"`, contains no escape character, though.

**Helpers to reuse** (tests/test_workflows_line_check.py, already imported by tests/test_calibrate_program.py):
- `_bridge_copy(tmp_path)` creates `tmp_path / "bin"`. It cannot be called twice in one test.
- `_load_copy(folder)` returns the copy's workflow-check.py as a module, writing no bytecode.
- `_unwritten_copy(tmp_path)` marks every `| yes |` in the copy's open list `| no |` and asserts the `f` and `FLAG` precondition for the bridge line.
- `conformance(root, program=...)` runs the program with `--offline`, windowless.
- `workspace(tmp_path, status_text)` builds `tmp_path / "proj"`.
- `HEAD` (`Phase: building`), `BRIDGE_LINE`, `ARROW`, `VALID`.
- `make_workspace` writes a `project.json` whose phase is `building`. A status file with another Phase therefore also prints an unrelated `project.json` NOTE that contains the status file's phase.

**The open list's rows** (bridge/cursor-bridge/workflow/open-list.md, read only), with their `Written` column:
- the product type `Website Development` (line 28): `no`
- the sub-type `CLI Software` of `Own-Computer Software Development` (line 47): `no`
- the trait `Personal data` (line 71): `no`
- `Web App Development`, `Local Web App`, `Own-Computer Software Development`, `Host Extension Development`, `Claude Code Extension`, `Installable`: `yes`

A test must not rely on any of these states unless it sets them on its own copy and asserts them.

**Corrections to the round-1 brief.** Round 1's Requirements are numbered 1-13. Its Context is not numbered, so its paragraphs are cited here by their bold headings.
- Round-1 Requirement 11 said "Each such test asserts its precondition (that `check_status` gives the expected `f` / `FLAG` finding on the copy), so it cannot pass vacuously when a release writes the entry", and listed (e)-(h) without saying they need such a copy. Round 2 makes it explicit: (e), (f), (g) and (h) each run on a bridge copy with the precondition asserted (Requirements 1-2 below).
- Round-1 Requirement 11 (h) said "a multi-part file mixing a written part, an unwritten-trait part and an unclassified part past intake: one row per Requirement, in order". Round 2 spells out the three parts and the exact rows, counts and order (Requirement 2).
- Round-1 Requirement 11 (i) said "a non-ASCII and an escape-character name in an unwritten finding reach the output escaped". Round 2 requires `chr(0x1B)` in the name (Requirement 3).
- Round-1 Requirement 11 said "The cases, each asserting the exact row(s) and the exit code". Round 2 states the full row for (c), (d), (f) and (g) (Requirements 1 and 4).
- Round-1 Requirement 7, first bullet, said "Every name, reason and Phase word printed goes through workflow-check's `escape_field` and then the existing `ascii_text`". Round 2 adds a test for the Phase word and for a trait name (Requirements 5-6).
- Round-1 Requirement 3, second bullet, said "If that word is exactly `intake`, a `not yet classified` part is OK". Round 2 adds a test for the word "exactly" (Requirement 7).
- Round-1 Requirement 9 said "then an `Unwritten trait` NOTE naming `Installable`". Round 2 adds the order check (Requirement 8).
- Round-1 Requirement 6 said "The new grades come from a separate function ... Any new loading of workflow-check.py keeps today's guarantees". That still holds, and round 1's implementation of that separate function stays. Round 2 corrects only its docstring (Requirement 9), keeps its per-part parse unchanged (Requirement 10), and adds a test tying its findings to `check_status` (Requirement 11).
- Round-1 Done named `handoff/TASK-024-r1-report.md`. Round 2's report is `handoff/TASK-024-r2-report.md`.
- The round-1 Context paragraph **The open list as it stands** said "a test that relies on one must assert that precondition". It stands, and the **open list's rows** above replace its list.

**Security context.** The status file is project-written text and is untrusted input to this program. The trust boundary lies between that text (and the open-list tables) and the console output, which ends up in calibration reports and in `PROJECT_STATUS.md`. The project's ASVS level is 5.0.0 L2 (docs/INVENTORY.md). The rule `.cursor/rules/secure-coding.mdc` is already in force for you.

**Development data** (docs/INVENTORY.md Decisions row): "Development data: the dev build is the Workspace sources under `bridge/`; a session in the repo always runs the *installed* bridge (`~/.claude`), never the one being edited, and installs reach running projects only through the owner's install run sheet". For you this means:
- Run the programs from `bridge/cursor-bridge/` in this Workspace, or from copies under a test's temporary folder.
- Never run anything under the home folder's `.claude`.
- Never point the program at another project's Workspace.
- The bridge's own docs/PROJECT_STATUS.md may be read, never written.

## Diagrams
None. The build plan names no diagram for this increment.

## Requirements
Every test you add or change names R-027 and R-033 in its name or docstring. Every new expectation is an exact row (see Context), plus a count where this brief gives one, plus the exit code.

1. **Cases (e), (f) and (g) on bridge copies.** Each test builds a copy with `_bridge_copy(tmp_path)` and edits the copy's open list so that the named entry's `Written` cell reads `no`. It then asserts the precondition on the copy, by loading it with `_load_copy` and calling `load_tables` and `check_status` on the test's status text: `load_tables` gives no errors, and `check_status` gives exactly the findings listed below. Then it runs `conformance(..., program=folder / "conformance-check.py")`.
   - (e) Status line `Workflows: Website Development; traits: none` after `HEAD`. Precondition: exactly one finding, `f` for `Website Development` with reason `product type is not written`. Expect the exact row `("MISSING", "Workflows line", "names an unwritten workflow: Website Development - product type is not written")` and exit 1.
   - (f) Status line `Workflows: Own-Computer Software Development → CLI Software; traits: none` (with `ARROW`). Precondition: exactly one finding, `f` for `CLI Software` with reason `sub-type is not written`. Expect the exact row `("MISSING", "Workflows line", "names an unwritten workflow: CLI Software - sub-type is not written")` and exit 1.
   - (g) Status line `Workflows: Web App Development → Local Web App; traits: Personal data`. Precondition: exactly one finding, `FLAG` for `Personal data`. Expect the exact rows `("OK", "Workflows line", "")` and `("NOTE", "Unwritten trait", "Personal data - trait not yet written; flagged, work continues (non-fatal)")`, exactly one `Unwritten trait` row, the OK row printed before it, and exit 0.
2. **Case (h): three parts, on a bridge copy.** The status file is `HEAD` followed by these three lines, in this order:
   - `Workflows: tool: Host Extension Development → Claude Code Extension; traits: Installable` (a written part)
   - `Workflows: app: Web App Development → Local Web App; traits: Personal data` (an unwritten-trait part)
   - `Workflows: side: not yet classified` (an unclassified part past intake)

   The copy marks `Personal data` `no`. Precondition on the copy: `check_status` gives exactly one finding, `FLAG` for `Personal data`. This also asserts that every other name in the file is written there. Expect:
   - exactly one `Workflows line` row, the exact `("OK", "Workflows line", "")`
   - exactly one `Unwritten trait` row, the exact `("NOTE", "Unwritten trait", "Personal data - trait not yet written; flagged, work continues (non-fatal)")`
   - exactly one `Workflows classification` row, the exact `("NOTE", "Workflows classification", "unclassified past intake (Phase: building); calibration step 4b classifies it, the project running on the main workflow alone meanwhile")`
   - those three rows in that order in the output
   - exit 0
3. **Case (i): a real escape character.** The name that the copy's open list gives the unwritten product type contains both `chr(0xDC)` and `chr(0x1B)`. Keep the round-1 precondition (`load_tables` gives no errors, `check_status` gives `f`), extended to assert that the `f` finding's name is that exact name. Expect:
   - the exact MISSING row, with the name escaped as `escape_field` escapes it
   - `"\\xdc" in out` and `"\\x1b" in out`
   - `chr(0x1B) not in out`
   - `out.isascii()`
   - exit 1
4. **Cases (c) and (d): full rows.** (c), `Phase: building`, and (d), `Phase: building (Stage 2)`, each expect the exact rows `("OK", "Workflows line", "")` and then `("NOTE", "Workflows classification", "unclassified past intake (Phase: building); calibration step 4b classifies it, the project running on the main workflow alone meanwhile")`, exactly one classification row, the OK row first, and exit 0. Each test keeps its current status text.
5. **The Phase word is escaped.** Add a case whose status file has `Phase: ` followed by a first word that contains both `chr(0xFC)` and `chr(0x1B)`, then `Workflows: not yet classified`. Expect:
   - the exact `("OK", "Workflows line", "")` row
   - exactly one `Workflows classification` row, the exact row with that word escaped as `escape_field` escapes it
   - no raw `chr(0x1B)` in that row, and the row is ASCII

   Make the ESC and ASCII assertions on that row only, not on the whole output. The unrelated `project.json` phase NOTE (Out of scope) prints the status file's phase without escaping it. This case runs on the Workspace program: no copy is needed, because it depends on no table entry.
6. **An unwritten trait's name is escaped.** Add a case on a bridge copy whose open list renames the trait `Personal data` (its row stays `no`) to a name containing both `chr(0xDC)` and `chr(0x1B)`. Use no comma and no leading or trailing space in the name. The status line is `Workflows: Web App Development → Local Web App; traits: <that name>`. Precondition on the copy: `load_tables` gives no errors, and `check_status` gives exactly one finding, `FLAG` with that exact name. Expect:
   - the exact `("OK", "Workflows line", "")` row
   - exactly one `Unwritten trait` row, the exact row with the name escaped
   - `chr(0x1B) not in out` and `out.isascii()`
   - exit 0

   If renaming the trait makes the copy's tables fail to load, stop and report it. Do not choose another table edit.
7. **The `intake` comparison is exact.** Add a case, parametrised over at least `Phase: intakes` and `Phase: intake-review`, each followed by `Workflows: not yet classified`. Each expects:
   - the exact `("OK", "Workflows line", "")` row
   - exactly one `Workflows classification` row, the exact row with `(Phase: intakes)` or `(Phase: intake-review)`
   - exit 0

   Case (b) (`Phase: intake`, no classification row) stays as it is.
8. **The bridge-line test's order check.** In tests/test_workflows_line_check.py, `test_r015_conformance_bridge_line_unwritten_is_missing_and_trait_note` gains an assertion that the `Unwritten trait` NOTE line comes after the MISSING `Workflows line` line in the output. You may also make its trait assertion an exact-row comparison. Change nothing else in that file. If any other test there would have to change, stop and report it.
9. **The docstring of `calibration_workflows_grades`** says what the function returns: `OK`, `MISSING` or `not-checked`. The second value is the detail for MISSING, empty for OK, and the list of ASCII reasons for not-checked. The notes are the `(floor, detail)` NOTE rows in status-file order, empty for not-checked. Keep it ASCII.
10. **The per-part parse stays.** `calibration_workflows_grades` keeps round 1's way of collecting its findings:
    - the `f` findings come from its one `mod.check_status` call;
    - the walk over the `Workflows: ` lines with `mod.prefix_of` stays, with `mod.check_head` and `mod.check_traits` called per classified part for the FLAG findings, and the classification NOTE added per unclassified part past intake.
    - The NOTE rows stay in status-file order. Each part's rows stand where the part stands in the file: an unclassified part's `Workflows classification` row comes after the `Unwritten trait` rows of the parts above it and before those of the parts below it.
    - The round-1 row texts (Context), the return contract and the not-checked paths are unchanged.

    Apart from the docstring (Requirement 9), this function needs no code change in round 2.
11. **A test that ties the grades to `check_status`.** This test guards the per-part parse against drifting from `check_status`. Add it on `_unwritten_copy(tmp_path)` (whose own precondition is already asserted). Its status file is `HEAD` followed by these lines, in this order, so that the unclassified part sits between two trait parts:
    - `Workflows: tool: Host Extension Development → Claude Code Extension; traits: Installable`
    - `Workflows: side: not yet classified`
    - `Workflows: app: Web App Development → Local Web App; traits: Personal data`

    Call the copy's `calibration_workflows_grades` in-process, by loading the copy's conformance-check.py as a module so that it finds the copy's workflow-check.py beside it. Alternatively, run the copy and read the printed rows. Then compare with `check_status` on the copy and the same text:
    - The verdict is MISSING, and the `f` findings in its detail equal check_status's `f` findings: the detail is exactly `"names an unwritten workflow: " + "; ".join("%s - %s" % (name, reason))` over check_status's `f` findings, in check_status's order, with names and reasons escaped as `field` does.
    - The grades' FLAG names and reasons, in order (the `Unwritten trait` notes as `"<name> - <reason>"`), equal check_status's `FLAG` findings, in order.
    - The full notes list is exactly `[Unwritten trait Installable, Workflows classification (Phase: building), Unwritten trait Personal data]`, in that order.

    If you load conformance-check.py in-process, do it with `sys.dont_write_bytecode` set and restored, as `_load_copy` does.
12. **Everything else stays.** `judge_workflows_line` is unchanged. Every round-1 case not named here keeps its expectations: (a), (b) and (j), and the `not-yet-classified` test in tests/test_workflows_line_check.py. tests/test_b2_least_confident.py needs no change. The module docstring's Workflows bullet (lines 41-44) is already right; leave it.
13. **Command reference and manifest.** No command-line option changes. Run `python tools/dump-cli.py --check`, and if it fails, regenerate with `python tools/dump-cli.py` and run `--check` again until it passes. Then regenerate the manifest with `python tools/make-manifest.py --version 2026.10.25a`, after your last change to conformance-check.py.

## Acceptance criteria
- [ ] Cases (e), (f), (g) and (h) run on bridge copies whose open list sets the named entry `no`. Each asserts its `check_status` precondition on the copy, and none of them reads the Workspace's open list for an unwritten entry.
- [ ] Case (h) has three parts and asserts the exact OK row, exactly one exact `Unwritten trait` row and exactly one exact `Workflows classification` row, in that order, with exit 0.
- [ ] Case (i)'s name contains `chr(0x1B)`. The output holds `\x1b` and `\xdc`, holds no raw ESC, and is ASCII.
- [ ] Cases (c), (d), (f) and (g) compare full rows. No assertion about a new row uses a substring.
- [ ] Removing `field()` from the Phase word, or from the trait name, makes a test fail.
- [ ] Changing the intake comparison to `phase.startswith("intake")` or `"intake" in phase` makes a test fail.
- [ ] The bridge-line test in tests/test_workflows_line_check.py checks that the `Unwritten trait` NOTE follows the MISSING row, and nothing else in that file changed.
- [ ] `calibration_workflows_grades`'s docstring names the `not-checked` return and its list of reasons.
- [ ] `calibration_workflows_grades` keeps round 1's per-part parse (`prefix_of`, `check_head`, `check_traits`). Its NOTE rows stay in status-file order, and the round-1 row texts are unchanged.
- [ ] The test of Requirement 11 shows that, on the three-part file, the grades' FLAG names and reasons in order equal check_status's FLAG findings in order, and the `f` findings equal check_status's `f` findings. It fails if every `Unwritten trait` row is put before the classification row.
- [ ] No shared loader was introduced, and `judge_workflows_line` is unchanged.
- [ ] `python -m pytest tests/test_calibrate_program.py tests/test_workflows_line_check.py tests/test_conformance_check.py tests/test_b2_least_confident.py -q --no-header -p no:cacheprovider` passes.
- [ ] `python tools/dump-cli.py --check` passes. bridge/cursor-bridge/MANIFEST.json is regenerated and matches the changed files.
- [ ] Every requirement under "Satisfies" is fully met (no stand-in, placeholder, "coming soon" or "arrives in a later stage" text), and at least one test names each requirement ID (in its name, docstring, or a comment) so the trace is checkable.
- [ ] No new Semgrep high findings; no new dependency.

## Constraints
- Do not add dependencies.
- Do not read or write any file outside this workspace (the folder you were started in). Everything you need is inside it; everything you produce goes inside it.
- If the brief, the rules, or the tooling got in your way (an instruction that contradicted another, a check that fired wrongly, a step that cost time for no reason), append one dated line describing it to `docs/BUILDER_NOTES.md`. Do not try to fix the tooling. Do the same for anything you learned about a defect or a pitfall (a cause you found, a platform quirk that cost you a round): one dated line, so the supervisor can carry it forward.
- In any Markdown you write, never break a line inside a paragraph or a list item; one paragraph is one line. Line breaks only between blocks.
- This increment talks to no external service. `conformance-check.py` keeps `--offline` in every test run, as the existing helper does.
- Any console process your code launches on Windows is created windowless (`creationflags=subprocess.CREATE_NO_WINDOW` in Python, `0` on other platforms). Capturing output does not prevent the window. A window is allowed only when it serves the user (they watch it or type into it); then write the reason at the call site as `windowless: visible-ok <reason>`. Start processes only through the existing `conformance()` helper, which already does this.
- Never start a server, a watcher or a daemon that outlives a test. A process a test starts is waited for and its pipes are drained (`subprocess.run` with `capture_output=True`, as the existing helpers do).
- Do not refactor code outside the scope, even if it looks wrong. Inside conformance-check.py, change only the docstring of `calibration_workflows_grades`.
- Never run the product, a migration, a seed or a test against the owner's live data. The development data is the Workspace sources under `bridge/` and copies of them under a test's temporary folder (see Context). Never run the installed bridge under the home folder, and never point a program at another project.
- The installed tables are never edited and never monkeypatched on disk. Every table edit is made on a copy under the test's temporary folder.
- No value in this brief is marked as the owner's. The grades are the supervisor's decision recorded in docs/INVENTORY.md ("TASK-024's grades"). If the work seems to need a different grade or a different row text, stop and report it.
- Follow existing conventions in the files you touch: ASCII output, `add(verdict, floor, detail)`, the existing test helpers.
- These git commands are not yours to run: `commit`, `push`, `switch`, `checkout`, `merge`, `rebase`, `reset`, `stash`, `branch -d`, `worktree`. You read with `git status`, `git diff` and `git log` only.
- The one value parsed here is the Phase line's first word. Take it with `str.split()` on the text after the exact `Phase: ` prefix, and compare it with the exact string `intake`. No number is parsed.
- Reports and notes never paste computer paths or user names. This includes paths that pytest prints for temporary folders. Write `<temporary folder>`, `<home>` or `<Workspace>` instead.
- **Verification commands**, each run from the Workspace root (the folder you were started in), in this order after your last code change:
  - `python tools/dump-cli.py --check` (if it fails: `python tools/dump-cli.py`, then `--check` again)
  - `python tools/make-manifest.py --version 2026.10.25a`
  - `python -m pytest tests/test_calibrate_program.py tests/test_workflows_line_check.py tests/test_conformance_check.py tests/test_b2_least_confident.py -q --no-header -p no:cacheprovider`

  Write in the report what each command printed (its summary lines).
- **Mutation check, by hand, in your own run.** Mutate the code in conformance-check.py in-process: edit it, run the relevant tests, restore it. Cover at least:
  - `field()` removed from the Phase word
  - `field()` removed from the trait name
  - the intake comparison made `phase.startswith("intake")`
  - the intake comparison made `"intake" in phase`
  - every `Unwritten trait` row emitted before every `Workflows classification` row
  - the NOTE rows printed before the `Workflows line` row
  - the sub-type's `f` finding dropped
  - the per-part FLAG collection drifting from `check_status`, e.g. a part's FLAG findings skipped or duplicated

  List each mutation in the report with the test that caught it. A mutation that no test catches is a gap you close with a test before you finish. No mutation script and no mutated code land in the diff.
- Prefer reuse over new code: the existing `calibration_workflows_grades`, the loaded module's `check_status` and `escape_field`, the existing `ascii_text`/`field` helpers, and the existing test helpers. Write the minimum that meets the acceptance criteria. This never overrides a security, observability, or accessibility requirement stated above.

## Done
Your report is the file `handoff/TASK-024-r2-report.md`, which you write as you go (what you did, what you changed, what you ran and what it printed, what you could not do), so that nothing of it is lost when your run ends early. When you finish, it holds:
- a list of every file you changed;
- a one-paragraph summary of what you did;
- for each of Requirements 1-11, the test (by name) or the code change that meets it;
- the mutation list;
- a section headed exactly `Assumed, not verified`: every fact this change relies on that neither this brief nor the existing code settled, and that you did not confirm. One item per line: what you assumed · why · what would confirm it.

Some examples of what belongs in that section: the `Written` state of a name a test uses without asserting it on a copy (cases (a) and (j) rely on written entries); that the per-part parse gives the same findings as `check_status` on files other than the one Requirement 11 tests; that an ESC character in an open-list cell survives `load_tables`, if you did not assert it; and any requirement here you resolved one way. Write `Assumed, not verified: none` only if that is true. The reviewers check this section against the code and the tests. Round 1 wrote "none" and left out at least two such facts. Be specific: "edge cases" or "error handling" is not an item.

Your last message is the summary and the report file's path, and nothing follows it: the supervisor reads only the last message, and a message printed earlier and then followed by more work is lost.
