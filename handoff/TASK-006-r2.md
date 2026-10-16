# TASK-006 round 2: the workflow check — the review's corrections

## Objective
Round 1 (`handoff/TASK-006-r1-report.md`) built `bridge/cursor-bridge/workflow-check.py`. Its review (Review A, Review B and the security auditor) found that a misspelt change heading, a trait list without its separator, an unreadable folder and a byte-order mark each let a wrong conditional workflow or status line pass, plus smaller defects. This round corrects them. **`handoff/TASK-006.md` still holds in full** (read it first: objective, context, requirements 1–15, constraints, done); this file changes only what it says, and where the two differ this file wins.

Satisfies: R-014, R-033 (unchanged).

## Scope
Files you may modify:
- bridge/cursor-bridge/workflow-check.py
- bridge/cursor-bridge/MANIFEST.json (regenerated with `python tools/make-manifest.py` after your last edit under `bridge/`)
- docs/BUILDER_NOTES.md
- handoff/TASK-006-r2-report.md

Do not modify anything else. In particular `.github/workflows/tests.yml` does not change in this round.

## Written by the supervisor; do not edit
`tests/test_workflow_check.py` and everything under `tests/fixtures/workflows/` were extended for this round and are committed with this file. Do not edit, move, rename or add to them, nor `tests/test_release_b_ci_floor.py`. If a supervisor test contradicts this file or `TASK-006.md`, stop, change no test, and report the contradiction (test name, requirement, what each says).

## Corrections (each is a requirement)

### R2-1. A misspelt change word is a malformed change heading (replaces Requirement 7's first sentence)
A **change heading** is a line outside a fenced code block that starts with `## ` and whose words (split on whitespace, after `## `) satisfy either:
- the first word, compared case-insensitively, is one of `add`, `adds`, `added`, `set`, `sets`, `replace`, `replaces`, `replaced`, `replacing`; or
- the second word, compared case-insensitively, is `at`.

Every change heading must match exactly one of Requirement 7's four forms (case-sensitive, single spaces, no trailing space); any other change heading is `FAIL (form)`, with name `-`. So `## Adds at intake.questions`, `## add at intake.questions`, `## Sets at intake.budget-kind`, `## Replacing interface` and `## Append at intake.questions` all fail as `form`, while `## Settings`, `## Setup`, `## Additional notes`, `## Notes` and `## Replacement history` stay prose and are not checked. A misspelt heading's section is not read as a change.

### R2-2. A byte-order mark is not part of the text
Read every input (the open list, the registry, every conditional-workflow file, every status file) with `encoding="utf-8-sig"`, so a leading UTF-8 byte-order mark is dropped and a change heading or `Workflows:` line on the first line is read. A file that is not valid UTF-8 still exits 2 (Requirement 3).

### R2-3. An unreadable folder stops the check (Requirement 3, completed)
Walking `ROOT/types/` and `ROOT/traits/`, a folder that cannot be listed is an `ERROR: <path>: <reason>` line and the run exits 2 with `RESULT: not checked`, never a silent skip. (With `os.walk`, pass an `onerror` that records it.)

### R2-4. Links are not followed (Requirement 6, completed)
A symbolic link or a Windows junction under `ROOT/types/` or `ROOT/traits/`, to a file or a folder, is `FAIL (form)` with its own path and name `-` or its file name, and is never opened or walked into (`os.path.islink`, and `os.path.isjunction` where Python provides it; `os.walk(..., followlinks=False)` alone does not stop a junction on Windows). The check therefore reads no file outside the folder it was given and cannot loop on a link to a parent.

### R2-5. The trait separator is exactly `, ` (Requirement 11.5, made exact)
After `; traits: `, the text is `none` or trait Names joined by exactly `, ` (a comma and one space). Split on `, `; a name that still contains `,`, or that has leading or trailing whitespace, or is empty, is `FAIL (form)` (name `-` or the raw text), not `unknown`. So `Has screens,Installable` and `Has screens,  Installable` fail as `form`. Do not strip the traits text before reading it, except that the line's own trailing newline is not part of it.

### R2-6. The part prefix is looked for in the head only (Requirement 11.1, made exact)
The **head text** is the rest of the line after `Workflows: ` up to the first `; traits: ` (or the whole rest if there is none). A line **attempts a prefix** when its head text contains `: `. Then:
- the attempted part is the text before the first `: ` of the head text; it must be non-empty and contain no `;`, `→` or `:`, else `FAIL (form)`;
- in a file with one `Workflows:` line, any attempted prefix (valid or not) is `FAIL (form)`;
- in a file with several, a line with no attempted prefix, or an invalid one, is `FAIL (form)`;
- a line failing any of these is not checked further (no `unknown`, `e` or `f` from it).

So the single line `Workflows: bad;part: Web App Development; traits: none` gives one `form` finding only, and `Workflows: Web App Development; traits: none` attempts no prefix.

### R2-7. An empty head segment is form only (Requirement 11.4)
An empty name in the head (an empty segment around `→` or around a `,`) is `FAIL (form)`, never `unknown`; the line's other findings stand.

### R2-8. One flag per unwritten trait
A trait repeated on a line gives the `form` finding and no second `FLAG (trait)` line: each distinct unwritten trait is flagged once per line.

### R2-9. The separator row is checked (Requirement 3)
The second line of every table must be the separator: every cell, stripped, consists of `-` characters with optional `:` at either end and at least one `-`. Otherwise the check cannot run: `ERROR: <path>: table after <heading> has no separator row` and exit 2.

### R2-10. A usage error ends with the RESULT line
A command-line usage error (an unknown option, `--status` without a file) exits 2 and the last line printed on standard output is `RESULT: not checked`; argparse's own message may stay on standard error.

### R2-11. Printed fields carry no control characters
Every field the program prints from input (a path, a name, a heading target, a part, a reason that quotes input) is escaped before printing: each character for which `str.isprintable()` is false is replaced by `\xNN` (two lowercase hex digits) when its code point is below 256, else by `\uNNNN` (four lowercase hex digits, or `\UNNNNNNNN` above `0xFFFF`). Printable characters, `→` included, are printed as they are. A tab, an escape (`\x1b`), a bell, a carriage return and a newline inside a name are thereby printed as `\x09`, `\x1b`, `\x07`, `\x0d`, `\x0a`, and no input can start a new output line (which GitHub Actions would read as a workflow command).

### R2-12. Heading sections in linear time
`heading_spans` (or its replacement) finds each section's end from the next heading's index, not by re-scanning the list of headings for every heading: a file of tens of thousands of headings is read in time proportional to its size.

### R2-13. The docstring of `read_utf8` says what it returns
It returns three values (text, shown path, reason); its docstring says so.

### R2-14. The two delivery point keys (the constraint's wording, corrected)
The constraint "Do not hard-code any key, name, point or module from the tables" excepts, beside the delivery-kind list, the two point keys Requirement 9 names (`project-end.delivery`, `intake.delivery-kind`): keep them as named constants, as round 1 did.

## Acceptance criteria
- [ ] `python -m pytest tests/test_workflow_check.py -q` passes (the supervisor's tests, extended for every correction above).
- [ ] `python -m pytest tests -q` passes in full (the workflow pin is unchanged, since the workflow does not change this round).
- [ ] `python bridge/cursor-bridge/workflow-check.py bridge/cursor-bridge/workflow tests/fixtures/workflows/pass` exits 0 with `RESULT: OK`.
- [ ] `windowless-check.py` and `bridge-check.py --sources` pass.

## Done
Run each of these from the repository root, in this order, and paste each command with its exit code and the relevant output into your report:
1. `python bridge/cursor-bridge/workflow-check.py bridge/cursor-bridge/workflow tests/fixtures/workflows/pass`
2. `python -m pytest tests/test_workflow_check.py -q`
3. `python -m pytest tests -q`
4. `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge`
5. `python tools/make-manifest.py`, then `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`
6. `git diff --stat`

Your report is the file `handoff/TASK-006-r2-report.md`, written as you go, in the form `TASK-006.md`'s Done section describes: the files you changed, a one-paragraph summary, what you ran and what it printed, and a section headed exactly `Assumed, not verified` (one item per line: what you assumed · why · what would confirm it; or `Assumed, not verified: none`). Your last message is the summary and the report file's path, and nothing follows it.
