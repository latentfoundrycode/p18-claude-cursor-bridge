---
record: brief
header: 1
id: "TASK-084"
round: 2
satisfies: [R-105]
scope: ["bridge/cursor-bridge/bridge_env.py", "bridge/cursor-bridge/MANIFEST.json", "tests/test_program_merge_unit_one.py", "docs/BUILDER_NOTES.md", "handoff/TASK-084-r2-report.md"]
merge_unit: null
blocking_class: null
---
# TASK-084 round 2: A merge unit of one increment is refused with its cause (R-105)

Round cause: behaviour - bridge/cursor-bridge/bridge_env.py:993, `_merge_unit_field_line_words` takes as the bullet only a hyphen or an asterisk followed by one space, where the prose reader `MERGE_UNIT_RE` allows the bullet class followed by any white space, so a line of two IDs after a bullet and a tab, beside a header listing one, is answered by the rule (the header) instead of keeping `header: disagrees merge_unit` (supervisor's test, failing; Review A B1); scope - bridge/cursor-bridge/bridge_env.py:991, a second new function where the brief allows one, and the bullet class written again as a literal of its own beside the constant (Review A, ISS-021)

## Objective
This is round 2 of TASK-084. Round 1's code is committed ("checkpoint before TASK-084-r2", `git log` shows it) with the supervisor's two added cases in the acceptance file. Round 1 met most of the brief; this round makes the minimum changes the corrections below name, keeps every test green, and edits nothing in the acceptance file. Round 1's brief, `handoff/TASK-084.md`, stays in force for everything this brief does not change.

Satisfies: R-105 - a brief that names a merge unit of one increment is refused with its cause (F7); the full text stands in round 1's brief.

## Scope
Files and directories you may create or modify:
- bridge/cursor-bridge/bridge_env.py
- bridge/cursor-bridge/MANIFEST.json
- tests/test_program_merge_unit_one.py
- docs/BUILDER_NOTES.md
- handoff/TASK-084-r2-report.md

Limits on these files: `bridge_env.py`: round 1's rule pattern (`MERGE_UNIT_ONE_LINE_RE`, which you may rename), the helper `_merge_unit_field_line_words` (removed), and `brief_merge_unit_one_side`; nothing else, the two constants and `MERGE_UNIT_RE` as round 1 left them. `MANIFEST.json` only as regenerated. `tests/test_program_merge_unit_one.py` is the supervisor's, read only. `docs/BUILDER_NOTES.md`: a new dated line at the file's end only. `bridge-run.py` is not in this round's Scope: its round-1 lines stand as they are.

Do not modify anything else.

## Out of scope
As round 1's brief. In particular: no reader of a brief changed, `brief_header_refusal` untouched, no option, no environment variable, no new dependency, no module docstring changed; the supervisor's mutants file is not yours.

## Corrections
1. **One new function (scope; Review A).** Remove `_merge_unit_field_line_words`. `brief_merge_unit_one_side` is the one new function of the increment, its one caller the launcher, as round 1 has it.
2. **The line side read as the reader reads it, from the rule's one pattern (behaviour; Review A B1, the supervisor's test).** Both the line side's "one" and its "two or more as written" come from the rule's one compiled pattern, matched against each line after `strip()` as today: a line that begins, after the optional bullet mark exactly as `MERGE_UNIT_RE` allows it (the bullet constant followed by `\s+`, so a tab or any white space after the bullet counts), with the words `Merge unit:` and holds after the colon either exactly one word of the ID form and nothing else (the line names one) or two or more words of any form, words being what white space separates (the line names two or more). One way, which the reviewer suggested: two alternatives after the colon and its white space in the one pattern, the first capturing one word of the ID form followed by white space and the end of the line, the second matching a run of non-white-space, white space, and a non-white-space character; then which group matched says which side holds. The rule's pattern stays written inline in its `re.compile` call, names both constants, holds the words `Merge unit:` in a literal of its own, holds no character class of the ID form or of the bullet mark in a literal of its own, and repeats no group (no quantifier on a group but the bullet's optional one). No string literal anywhere in your new code holds the bullet class or the ID class: they come from the two constants.
3. **The report (records; Review A should-fix).** Your `Assumed, not verified` list names every fact the change relies on that you did not confirm (round 1 wrote none where its bullet check assumed one space). Write step 9's output after the report is otherwise complete, so that its `git status --short` shows the report itself.

## Context
The acceptance file `tests/test_program_merge_unit_one.py` (the supervisor's, committed at the round-2 checkpoint) gained two cases: `bullet-tab`, a line of one ID after a hyphen and a tab beside `merge_unit: null`, refused for the line (green on round 1's code); and `two-line-tab-bullet-one-header`, a line of two IDs after an asterisk and a tab beside a header listing one, which keeps `header: disagrees merge_unit` (red on round 1's code: the rule answers it, the side being the header). Their reader values stand in `RECORDED`. At the checkpoint the file gives 1 failed, 61 passed, the failure `test_r105_a_side_naming_two_or_more_as_written_keeps_the_disagreement[two-line-tab-bullet-one-header]`.

Every form round 1's brief names stays as it is: refused by the rule for its side, kept as `header: disagrees merge_unit`, or passing. A brief with two such lines, one of one ID and one of two, counts as naming two or more as round 1 counts it.

Threat model: as round 1's brief (`docs/INVENTORY.md` Decisions, "The bridge's threat model as a whole"). A brief is a file in the checkout, outside input once an agent has worked there; the rule adds a refusal and removes none.

## Acceptance criteria
- [ ] Every test in `tests/test_program_merge_unit_one.py` passes, none skipped, and every test of round 1's Done list passes.
- [ ] Corrections 1 to 3 met, each named in the report with its function and lines.
- [ ] Round 1's requirements and choices stand where this brief does not change them.
- [ ] Every line added ASCII; no option, environment variable or dependency.

## Constraints
Round 1's brief's Constraints all stand (foreground commands only, named test files only with the Done commands, no `python -c` or script of your own, no git command that writes, never point the launcher at the checkout, ASCII, the report's form, no line of your report or notes beginning with the words that open a merge-unit or blocking-class line; if an acceptance test and this brief seem to disagree, stop and report it, editing neither the test nor the product around it). Mutations by hand, in process, each reverted, listed by label with the pytest line that shows a test failing, else `not run`: (H1) the bullet followed by exactly one space again; (H2) the two-or-more alternative removed, so that no line names two or more; (H3) the side named wrongly. Prefer the smallest change; refactor nothing else.

## Done
Your report is `handoff/TASK-084-r2-report.md`, written as you go, in round 1's form (files changed, the report itself among them; summary; each correction in one sentence with the function and lines; every command below with its output, verbatim, in fenced blocks, each pytest summary line quoted; the mutations H1 to H3, each with the FAILED line and the summary line, else `not run`; a last section headed exactly `Assumed, not verified`). It names no computer path: `<Workspace>` for the repository folder, `~` for the home folder.

Run these from the Workspace root, in this order, after your last edit, each in the foreground, with no `PYTHONPATH` or other environment change; run them again in order if you edit anything after them, and quote the last run:
1. `python tools/make-manifest.py`
2. `python tools/dump-cli.py --check` (expect the reference current)
3. `python -m pytest -p no:cacheprovider -q tests/test_program_merge_unit_one.py`
4. `python -m pytest -p no:cacheprovider -q tests/test_header_plan.py tests/test_header_plan_r2.py tests/test_header_plan_r3.py tests/test_header_reader.py tests/test_header_currency.py`
5. `python -m pytest -p no:cacheprovider -q tests/test_task032_supervisor_launcher.py tests/test_task032_supervisor_guard.py tests/test_program_launcher_forms.py`
6. `python -m pytest -p no:cacheprovider -q tests/test_bug032.py tests/test_bug044.py tests/test_records_migrate.py tests/test_dump_cli.py`
7. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` (expect the sources to match)
8. `git diff --stat HEAD`
9. `git rev-parse HEAD` and `git status --short`

Every pytest summary line quoted verbatim; never restate a count in prose. Your last message is the summary and the report file's path, and nothing follows it.
