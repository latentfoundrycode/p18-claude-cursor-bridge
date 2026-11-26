---
record: brief
header: 1
id: "TASK-088"
round: 2
satisfies: [R-110]
scope: ["bridge/cursor-bridge/bridge_env.py", "bridge/cursor-bridge/bridge-run.py", "bridge/cursor-bridge/plan-check.py", "bridge/cursor-bridge/MANIFEST.json", "tests/test_improve_satisfies_reader.py", "docs/cli-reference.json", "docs/CLI_REFERENCE.md", "docs/BUILDER_NOTES.md", "handoff/TASK-088-r2-report.md"]
merge_unit: null
blocking_class: null
---
# TASK-088 (round 2): One reader for a brief's Satisfies ids

Round cause: round 1 was refused by the security audit (blocking, security: text quoted from the brief reached the launcher's refusal and plan-check's line with its control bytes raw) and by Review A (blocking, behaviour: `none` followed by a full stop, comma, semicolon or parenthesis was not recognised; a second loop found the `Satisfies` line for the refusal's text; plan-check's disagreement line printed the lists by repr, non-ASCII kept). The supervisor's rulings on Review A's should-fix items are Requirements R2 to R4 below.

Satisfies: R-110

## Objective
Round 1's work stands in the tree: `bridge_env.brief_satisfies_ids`, the set comparison, the launcher's two refusal texts and plan-check's two `BRIEF` lines. This round corrects it. Read `handoff/TASK-088.md` (round 1's brief) whole first: its Context, its Requirements 1 to 8, its Constraints and its Done stand, except where this brief changes them. Read `handoff/TASK-088-r1-report.md`, your round-1 report.

## Scope
Files and directories you may create or modify:
- bridge/cursor-bridge/bridge_env.py
- bridge/cursor-bridge/bridge-run.py
- bridge/cursor-bridge/plan-check.py
- bridge/cursor-bridge/MANIFEST.json
- tests/test_improve_satisfies_reader.py
- docs/cli-reference.json
- docs/CLI_REFERENCE.md
- docs/BUILDER_NOTES.md
- handoff/TASK-088-r2-report.md

Do not modify anything else.

Limits on these paths: as round 1's brief. `tests/test_improve_satisfies_reader.py` is the supervisor's acceptance file: read it whole and run it, **do not edit it**.

## Out of scope
As round 1's brief, and also `tests/test_records_migrate.py` (the supervisor changed one expectation in it, `test_r062_a_satisfies_id_named_twice_is_written_once`: the reader names each id once).

## Requirements (this round; round 1's Requirements 1 to 8 stand where these do not change them)
R1. **One escape for text from a brief.** Every piece of text that comes from a brief and is printed in a refusal of the launcher or in a `BRIEF` line of plan-check (the quoted `Satisfies` line, the header's list, the prose's list) goes through one function of `bridge_env.py` that escapes non-ASCII characters and also the C0 control characters (0x00 to 0x1F) and DEL (0x7F), each as a backslash escape (`\x1b` and the like), so that no control byte reaches the terminal. Today's `_ascii_record_quote` and the launcher's `_ascii_refusal` escape only non-ASCII (`backslashreplace`); ESC, BEL and backspace pass through raw. The launcher's `_ascii_refusal` stays where it is.

R2. **`none` is matched as a word.** The line's value reads `none` where its first word is `none` in any letter case, the word ending at a word boundary, so `none.`, `none,`, `none;`, `none(R-105)` count; leading `*`, `_` or backtick marks before it (as in `**none**`) are allowed; `nonetheless` and a `none` that is not the first word are no `none`. The acceptance tests list the forms.

R3. **The ids beside a `none` are returned** (the supervisor's ruling, Requirement 1 as written): `ids` are the R-ids on the line and the bullets whether or not the line reads `none`; `none_carries_ids` says that a `none` carries them. A header-less brief's `brief_satisfies` reads as on the checkpoint (`Satisfies: none (R-105 ...)` gives `['R-105']`).

R4. **The order of the refusals** (Requirement 6): the `none` refusal stands where `satisfies` stands in the order of the keys checked, so a brief whose header's `id` or `round` disagrees is told that first, as on the checkpoint; it precedes a `satisfies` disagreement and every key after `satisfies`. With `keys` that omit `satisfies` (the review guard's call) there is no `none` refusal, as in round 1.

R5. **One locator of the line.** `bridge_env.brief_satisfies_line(body)` returns `None` where the brief has no `Satisfies:` line (the first line `FIELD_RX` matches as `Satisfies`, as today), else the tuple `(index, line, value)`: the line's index in `body.splitlines()`, the line with its surrounding whitespace stripped, and the field's value with its trailing whitespace stripped. `brief_satisfies_ids` and the refusal's quoted line both take the line from it, looked up through the module at call time (the acceptance test monkeypatches it); `_brief_satisfies_prose_line` and every other loop that finds the line go.

R6. **A field written as a bullet ends the bullets.** The scan of the bullet lines beneath the line ends at a line `FIELD_RX` matches (another field of the brief, bulleted or not), as at any line that is neither a bullet nor blank.

R7. **One wording of each remedy.** plan-check's two new lines take their remedy text from the same place in `bridge_env.py` as the launcher's refusals (no second copy of the sentence in `plan-check.py`); plan-check may call public functions of `bridge_env.py` for it (name them without a leading underscore where plan-check calls them).

## Acceptance criteria
- [ ] Every test of `tests/test_improve_satisfies_reader.py` passes, the file unedited (it now holds round 2's tests, headed "round 2"). The supervisor's run on round 1's code, 2026-11-26: 13 failed, 24 passed. Failing: `test_task088_r2_a_control_byte_in_a_none_line_is_escaped_at_the_launcher`, `test_task088_r2_a_control_byte_in_a_none_line_is_escaped_by_plan_check`, `test_task088_r2_plan_checks_disagreement_line_prints_the_lists_in_ascii`, `test_task088_r2_a_field_written_as_a_bullet_ends_the_bullets[ids-then-a-field-bullet]` and `[none-then-a-field-bullet]`, `test_task088_r2_none_is_matched_as_a_word[full-stop-then-a-bullet]`, `[comma]`, `[semicolon]`, `[parenthesis]` and `[bold]`, `test_task088_r2_the_ids_beside_a_none_are_returned`, `test_task088_r2_one_locator_finds_the_line_for_the_reader_and_the_refusal`, `test_task088_r2_a_wrong_id_is_told_before_a_none_that_carries_ids`. Passing and to keep passing: `[upper-case]`, both `test_task088_r2_none_inside_another_word_or_later_is_no_none` cases, and every round-1 test.
- [ ] Every test file of round 1's Done steps 6 and 7, and the further files your round-1 search found, passes or skips by its own condition, unedited.
- [ ] `brief_satisfies_line` is the only code of `bridge_env.py` that finds a brief's `Satisfies` line; `brief_satisfies_ids` the only code that reads its ids (both named in the report with their lines, and every caller with theirs).
- [ ] No text from a brief reaches a launcher refusal or a plan-check `BRIEF` line without the one escape (R1), named in the report with each call.
- [ ] The command reference, MANIFEST, `bridge-check`, VERSION and ASCII checks as in round 1's brief.

## Constraints
Round 1's brief's Constraints stand, among them: run the tests with `python -m pytest` directly, never through `bridge-run.py`; no script of your own; scratch checks only as `tests/test_task088_scratch_*.py`, deleted; no path of this computer in anything you write (`<Workspace>`, `<tmp>`, `~`). **Mutation: name the code points, run nothing**: for round 1's M1 to M12 and these, N1 the control-byte escape removed, N2 `none` matched as a whole whitespace word again, N3 the ids beside a `none` dropped, N4 the `none` refusal checked before `id`, N5 a field bullet read as a row, N6 the locator bypassed by a second loop; each with the function and lines after your change and the test id you expect to catch it.

## Done
Your report is `handoff/TASK-088-r2-report.md`, written as you go, in round 1's form: the files you changed, a summary paragraph, one line for each of R1 to R7 naming the functions and lines that meet it, the mutation code points, every command you ran with its output quoted verbatim, the commit its counts belong to and whether the tree held uncommitted changes, and the last section headed exactly `Assumed, not verified` (one item per line: what you assumed · why · what would confirm it; or `Assumed, not verified: none`).

Run from the Workspace root, each on its own, synchronously in the foreground, with no environment change. Steps 1 and 2 before your first edit; steps 3 to 12 after your last edit, in this order:
1. `git status --short` (expect the supervisor's checkpoint clean)
2. `python -m pytest -p no:cacheprovider -q tests/test_improve_satisfies_reader.py` (quote the summary line and the failing ids)
3. to 12. Round 1's brief's Done steps 3 to 12, the same commands, with step 6 and step 7 also naming `tests/test_records_migrate.py` once (it is in step 7 already), and your round-1 search's further files in one more command of the same form.

Your last message is the summary and the report file's path, and nothing follows it.
