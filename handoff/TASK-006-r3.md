# TASK-006 round 3: the workflow check — the second review's corrections

## Objective
Round 2 (`handoff/TASK-006-r2-report.md`) settled the first review. The second review (Review A APPROVE 0/2/4, Review B REJECT 1/2/0, the security auditor PASS with two advisories) found a few remaining ways for input to escape the check or the output's escaping. This round corrects them. **`handoff/TASK-006.md` and `handoff/TASK-006-r2.md` still hold in full**; this file changes only what it says, and where they differ this file wins.

Satisfies: R-014, R-033 (unchanged).

## Scope
Files you may modify:
- bridge/cursor-bridge/workflow-check.py
- bridge/cursor-bridge/MANIFEST.json (regenerated with `python tools/make-manifest.py` after your last edit under `bridge/`)
- docs/BUILDER_NOTES.md
- handoff/TASK-006-r3-report.md

Do not modify anything else; `.github/workflows/tests.yml` does not change.

## Written by the supervisor; do not edit
`tests/test_workflow_check.py` and everything under `tests/fixtures/workflows/` were extended for this round and are committed with this file. Do not edit, move, rename or add to them, nor `tests/test_release_b_ci_floor.py`. If a supervisor test contradicts a brief, stop, change no test, and report the contradiction.

## Corrections (each is a requirement)

### R3-1. A usage error's message is escaped too (R2-10 and R2-11)
The message a command-line usage error writes to standard error (argparse's message, which may quote an argument) is escaped exactly as R2-11 escapes a printed field, so an argument holding a newline or an escape character cannot start a new line or a terminal sequence on either stream. The usage line argparse prints may stay as it is. The last line on standard output stays `RESULT: not checked`, exit 2.

### R3-2. The separator row has the header's cell count (R2-9)
The separator row must have exactly as many cells as the header row; a separator with fewer or more cells is the exit-2 error `table after <heading> has no separator row` (or a reason naming the cell count).

### R3-3. A link is reported wherever it stands (R2-4)
A link under `ROOT/types/` or `ROOT/traits/` is `FAIL (form)` at its own path wherever it stands, including inside a `types/<t>/` folder whose name is not a product-type key (which keeps its one `d` finding as well). A link at `ROOT/types` or `ROOT/traits` itself, including a dangling one (a link whose target does not exist), is `FAIL (form)` at that path and is never walked; test for the link before testing whether the path is a folder.

### R3-4. A change word with punctuation attached (R2-1)
Before the first word is compared with the change words, trailing punctuation from the set `:;,.-` is stripped from it. So `## Set: intake.delivery-kind`, `## Add: intake.questions`, `## Replace: design` and `## Adds. intake.questions` are change headings that fail as `form`, while `## Settings`, `## Setup`, `## Add-ons` and `## Additional notes` stay prose. Add `adding` and `setting` to the change words (so `## Adding intake.questions` and `## Setting intake.budget-kind` fail as `form`).

### R3-5. A part name has no surrounding whitespace (R2-6)
An attempted part with leading or trailing whitespace, or made only of whitespace, is invalid: `FAIL (form)`, the line not checked further. So `Workflows: app : …` and `Workflows:  : …` fail, and `app` and `app ` can never count as two parts.

### R3-6. An unclosed fence, and headings with leading spaces or a tab (Requirement 7)
- A fenced code block still open at the end of a conditional-workflow file is `FAIL (form)` (name `-`): every heading after its opening line would otherwise be hidden.
- A heading candidate is a line outside a fence that matches `^ {0,3}##[ \t]` (up to three leading spaces, two `#`, then a space or a tab), not only a line starting `## `. Such a line is a change heading by R2-1's and R3-4's rule applied to its words; a change heading must still match one of the four forms exactly (no leading space, a single space after `##`), so ` ## Set at x` and `##\tSet at x` fail as `form`. A section still ends at the next heading candidate. `###` and deeper headings stay prose.

### R3-7. Links are detected on a Python without `os.path.isjunction` (R2-4)
Where `os.path.isjunction` does not exist and the system is Windows, a path is a link when `os.lstat(path).st_file_attributes` has `stat.FILE_ATTRIBUTE_REPARSE_POINT` set (a junction or any other reparse point); an `OSError` from `lstat` makes the path count as a link. The check never falls back to "not a link" in silence. Keep this test in round 2's function `is_link(path)`, under that name: the supervisor's test calls it directly with `os.path.isjunction` removed.

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

Your report is the file `handoff/TASK-006-r3-report.md`, written as you go, in the form `TASK-006.md`'s Done section describes, with a section headed exactly `Assumed, not verified` (one item per line: what you assumed · why · what would confirm it; or `Assumed, not verified: none`). Your last message is the summary and the report file's path, and nothing follows it.
