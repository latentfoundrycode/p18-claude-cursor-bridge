# TASK-006 round 5: the workflow check — the fourth review's corrections

## Objective
Round 4 (`handoff/TASK-006-r4-report.md`) settled the third review. In the fourth review, Review A and the security auditor independently found that the check reads code fences more simply than Markdown does: a fence opened with four backticks is closed by a line of three, and a backtick line with text after it closes a fence, so a heading Markdown displays (a trait's `## Set`) can sit unseen between two such tricks. The auditor also found that R4-2's error rule on the `os.path.isjunction` branch can never run (CPython's `isjunction` catches its own errors), and Review A that a root whose layer folders cannot be examined is checked as empty. This round corrects all three. **`handoff/TASK-006.md`, `-r2.md`, `-r3.md` and `-r4.md` still hold in full**; this file changes only what it says, and where they differ this file wins.

Satisfies: R-014, R-033 (unchanged).

## Scope
Files you may modify:
- bridge/cursor-bridge/workflow-check.py
- bridge/cursor-bridge/MANIFEST.json (regenerated with `python tools/make-manifest.py` after your last edit under `bridge/`)
- docs/BUILDER_NOTES.md
- handoff/TASK-006-r5-report.md

Do not modify anything else; `.github/workflows/tests.yml` does not change.

## Written by the supervisor; do not edit
`tests/test_workflow_check.py` and everything under `tests/fixtures/workflows/` were extended for this round and are committed with this file. Do not edit, move, rename or add to them, nor `tests/test_release_b_ci_floor.py`. If a supervisor test contradicts a brief, stop, change no test, and report the contradiction.

## Corrections (each is a requirement)

### R5-1. A layer path is examined with os.lstat (replaces R4-1's `os.path.lexists`)
In `collect`, `os.lstat(ROOT/types)` and `os.lstat(ROOT/traits)` decide: `FileNotFoundError` or `NotADirectoryError` means nothing is there, and the layer is skipped with nothing reported; any other `OSError` is an input the check cannot read, reported as an `ERROR:` line for that path (the reason is the error's `strerror`, or `cannot be examined`), so the run ends `RESULT: not checked` with exit 2 like any unreadable input. A path that `lstat` succeeds on goes on to the link test as before (R3-3: a dangling link is reported, never walked).

### R5-2. One link rule on every Python (replaces R3-7 and R4-2)
`is_link(path)` no longer uses `os.path.isjunction`. It calls `os.lstat(path)` once: `FileNotFoundError` or `NotADirectoryError` → `False`; any other `OSError` → `True` (fail closed); otherwise `True` when `stat.S_ISLNK(st_mode)` is true, or, on Windows, when `st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT` is non-zero; else `False`. The result is then the same on Python 3.11 and 3.12. Every caller of `is_link` keeps its place.

### R5-3. Fences as CommonMark reads them (replaces R4-3)
- An **opening fence** is a line of zero to three spaces, then a run of at least three backticks or at least three tildes, then anything (the info string). For a backtick run, the info string must not contain a backtick, or the line is not a fence.
- Inside an open fence, a **closing fence** is a line of zero to three spaces, then a run of the opening fence's character, at least as long as the opening run, then only spaces or tabs to the end of the line. Every other line inside the fence, a shorter run, the other character, or a run with text after it included, is content and changes nothing.
- R3-6 stands: a fence still open at the end of the file is one `form` finding, and every heading after its opening is hidden.

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

Your report is the file `handoff/TASK-006-r5-report.md`, written as you go, in the form `TASK-006.md`'s Done section describes, with a section headed exactly `Assumed, not verified` (one item per line: what you assumed · why · what would confirm it; or `Assumed, not verified: none`). Your last message is the summary and the report file's path, and nothing follows it.
