# TASK-006 round 6: the workflow check — the fifth review's corrections

## Objective
Round 5 (`handoff/TASK-006-r5-report.md`) settled the fourth review. In the fifth review Review B blocked on table rows: `cells_of` strips every pipe at a row's ends, so a row ending `||` (or starting `||`) loses an empty cell and a row with the wrong cell count passes, where Requirement 3 and R3-2 require exit 2. Review A and the security auditor independently found that the check splits a file into lines at characters Markdown does not treat as line ends (form feed, vertical tab, NEL, U+2028 and others), so two fence lines joined to text by such a character can hide a heading Markdown displays. This round corrects both. **`handoff/TASK-006.md` and `-r2.md` to `-r5.md` still hold in full**; this file changes only what it says, and where they differ this file wins.

Satisfies: R-014, R-033 (unchanged).

## Scope
Files you may modify:
- bridge/cursor-bridge/workflow-check.py
- bridge/cursor-bridge/MANIFEST.json (regenerated with `python tools/make-manifest.py` after your last edit under `bridge/`)
- docs/BUILDER_NOTES.md
- handoff/TASK-006-r6-report.md

Do not modify anything else; `.github/workflows/tests.yml` does not change.

## Written by the supervisor; do not edit
`tests/test_workflow_check.py` and everything under `tests/fixtures/workflows/` were extended for this round and are committed with this file. Do not edit, move, rename or add to them, nor `tests/test_release_b_ci_floor.py`. If a supervisor test contradicts a brief, stop, change no test, and report the contradiction.

## Corrections (each is a requirement)

### R6-1. A table row loses exactly one pipe at each end (Requirement 3, R3-2)
`cells_of(line)` strips the line's surrounding whitespace, then removes **one** leading `|` and, if present, **one** trailing `|`, then splits on `|` and strips each cell. A row such as `| a | b ||` therefore has three cells (the last empty) and `|| a | b |` has three (the first empty); against a two-column header each is "table row cell count differs from its header", exit 2, `RESULT: not checked`. The same function serves the header and the separator row, so a separator ending `||` fails its width check (R3-2) the same way.

### R6-2. Lines end only where Markdown ends them (Requirement 7, R5-3)
Wherever the check splits a file's text into lines (`heading_spans`, `parse_table`, and any other place it does), it splits only at a line feed. The text is read with universal newlines, so carriage returns are already line feeds; `str.splitlines()`, which also splits at form feed, vertical tab, `\x1c` to `\x1e`, NEL (`\x85`), U+2028 and U+2029, is no longer used for this. A line that holds such a character is one line, read as the rest of R5-3 says (a line beginning `a` then a form feed then three backticks is not a fence).

## Acceptance criteria
- [ ] `python -m pytest tests/test_workflow_check.py -q` passes (the supervisor's tests, extended for every correction above).
- [ ] `python -m pytest tests -q` passes in full.
- [ ] `python bridge/cursor-bridge/workflow-check.py bridge/cursor-bridge/workflow tests/fixtures/workflows/pass` exits 0 with `RESULT: OK`.
- [ ] `windowless-check.py` and `bridge-check.py --sources` pass.

## Done
Run each from the repository root, in this order, and paste each command with its exit code and the relevant output into your report:
1. `python bridge/cursor-bridge/workflow-check.py bridge/cursor-bridge/workflow tests/fixtures/workflows/pass`
2. `python -m pytest tests/test_workflow_check.py -q`
3. `python -m pytest tests -q`
4. `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge`
5. `python tools/make-manifest.py`, then `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`
6. `git diff --stat`

Your report is the file `handoff/TASK-006-r6-report.md`, written as you go, in the form `TASK-006.md`'s Done section describes, with a section headed exactly `Assumed, not verified` (one item per line: what you assumed · why · what would confirm it; or `Assumed, not verified: none`). Your last message is the summary and the report file's path, and nothing follows it.
