# TASK-006 round 4: the workflow check — the third review's corrections

## Objective
Round 3 (`handoff/TASK-006-r3-report.md`) settled the second review. The third review (Review A REJECT 1/0/3, Review B APPROVE 0/0/0, the security auditor PASS with two advisories) found that R3-7's fallback, as the brief worded it, counts a path that does not exist as a link: on a Windows Python without `os.path.isjunction`, a root with no `types/` or `traits/` folder (the bridge's own workflow folder among them) fails as `form`. Review A and the auditor found it independently. This round corrects it and makes fences consistent with headings. **`handoff/TASK-006.md`, `-r2.md` and `-r3.md` still hold in full**; this file changes only what it says, and where they differ this file wins.

Satisfies: R-014, R-033 (unchanged).

## Scope
Files you may modify:
- bridge/cursor-bridge/workflow-check.py
- bridge/cursor-bridge/MANIFEST.json (regenerated with `python tools/make-manifest.py` after your last edit under `bridge/`)
- docs/BUILDER_NOTES.md
- handoff/TASK-006-r4-report.md

Do not modify anything else; `.github/workflows/tests.yml` does not change.

## Written by the supervisor; do not edit
`tests/test_workflow_check.py` and everything under `tests/fixtures/workflows/` were extended for this round and are committed with this file. Do not edit, move, rename or add to them, nor `tests/test_release_b_ci_floor.py`. If a supervisor test contradicts a brief, stop, change no test, and report the contradiction.

## Corrections (each is a requirement)

### R4-1. A path that does not exist is nothing there, not a link (replaces R3-7's last clause)
In `collect`, a layer path `ROOT/types` or `ROOT/traits` for which `os.path.lexists` is false is skipped: there is nothing to walk and nothing to report. (`os.path.lexists` is true for a dangling link or junction, so R3-3's dangling-link finding stands.) In `is_link`'s Windows fallback, `FileNotFoundError` and `NotADirectoryError` from `os.lstat` return `False`; any other `OSError` still returns `True` (fail closed).

### R4-2. One rule for errors in both branches of `is_link` (R3-7)
On the `os.path.isjunction` branch, an `OSError` returns `True` (a path the check cannot classify is not walked), matching the fallback's rule; `FileNotFoundError` and `NotADirectoryError` return `False` there too.

### R4-3. A fence may be indented up to three spaces (Requirement 7, R3-6)
A fence line is a line matching `^ {0,3}` followed by three backticks (as CommonMark reads it), not only one starting at column 0; an opening fence is closed by the next such line. So a heading between an indented fence pair stays hidden as Markdown hides it, and an indented closing fence closes a block, so a change heading after it is read. R3-6's unclosed-fence finding applies to the new rule.

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

Your report is the file `handoff/TASK-006-r4-report.md`, written as you go, in the form `TASK-006.md`'s Done section describes, with a section headed exactly `Assumed, not verified` (one item per line: what you assumed · why · what would confirm it; or `Assumed, not verified: none`). Your last message is the summary and the report file's path, and nothing follows it.
