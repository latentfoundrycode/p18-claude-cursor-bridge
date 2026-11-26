---
record: brief
header: 1
id: "TASK-088"
round: 3
satisfies: [R-110]
scope: ["bridge/cursor-bridge/bridge_env.py", "bridge/cursor-bridge/bridge-run.py", "bridge/cursor-bridge/plan-check.py", "bridge/cursor-bridge/MANIFEST.json", "tests/test_improve_satisfies_reader.py", "docs/cli-reference.json", "docs/CLI_REFERENCE.md", "docs/BUILDER_NOTES.md", "handoff/TASK-088-r3-report.md"]
merge_unit: null
blocking_class: null
---
# TASK-088 (round 3): One reader for a brief's Satisfies ids

Round cause: round 2 was refused by Review A and by the security audit, both blocking and both reproduced: (behaviour; safety mechanism) the launcher's `none` refusal is reached only inside a `satisfies` disagreement, so a headed brief whose header lists the same ids as its `none` line agrees as a set and launches, and `Satisfies: none` with `- R-105` beneath, header `[R-105]`, was refused on main and now launches; (behaviour) `none` followed by a colon, a hyphen, an em dash, a slash, a closing parenthesis or an exclamation mark is not read as `none`, because the word's end was built as a list of following characters instead of a word boundary. Review A's should-fix (one wording of the disagreement's remedy) rides along.

Satisfies: R-110

## Objective
Round 2's work stands in the tree and is right but for these points. Read `handoff/TASK-088.md` (round 1's brief) and `handoff/TASK-088-r2.md` (round 2's) whole first: their Requirements, Constraints and Done stand except where this brief changes them. Read `handoff/TASK-088-r2-report.md`. This is round 3, the last the ceiling allows: change only what the three items below need.

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
- handoff/TASK-088-r3-report.md

Do not modify anything else.

Limits on these paths: as round 1's brief. `tests/test_improve_satisfies_reader.py` is the supervisor's acceptance file: read it whole and run it, **do not edit it**.

## Out of scope
As round 2's brief. The security audit's advisories (the launcher's `_ascii_refusal`, plan-check's pre-existing Scope line, the literal backslash in `ascii_brief_quote`) are recorded for later and are not this round's.

## Requirements (this round)
S1. **The `none` refusal whatever the header's list.** In `brief_header_refusal`, walk the brief's keys in the order the header's agreement checks them (`id`, `round`, `satisfies`, `scope`, `merge_unit`, `blocking_class`), filtered by `keys` when given. At `id` and `round` and every key after `satisfies`, return `header: disagrees <key>` where that key disagrees, as today. At `satisfies`, where `satisfies` is checked (keys is None or names it): return the `none` refusal where the fallback's `none_carries_ids` is True, whether or not the lists agree as sets; else the set-disagreement refusal where they disagree; else go on. So `id` and `round` still come first (round 2's R4), a `none` that carries ids is refused whatever the header lists (round 1's Requirement 5, R-110), and with keys that omit `satisfies` (the review guard) nothing changes.

S2. **`none` ends at a word boundary.** The line's value reads `none` where, after any leading `*`, `_` or backtick marks, its first word is `none` in any letter case followed by a word boundary in the sense of Python's `re` `\b` (end of the value or a character that is not a letter, digit or underscore). `none:`, `none-`, `none` followed by an em dash, `none/`, `none)`, `none!` count, as do round 2's forms; `nonetheless` does not.

S3. **One wording of the disagreement's remedy.** plan-check's disagreement line and the launcher's set-disagreement refusal are composed from one message function of `bridge_env.py`, so plan-check's line carries the same remedy words (`the header and the prose name the same rows`) and both lists through the one escape; the launcher's refusal still begins `header: disagrees satisfies`.

## Acceptance criteria
- [ ] Every test of `tests/test_improve_satisfies_reader.py` passes, the file unedited. The supervisor's run on round 2's code, 2026-11-26, is in Done step 2's expectation: the round-3 tests fail there (`test_task088_r3_a_none_that_carries_ids_is_refused_whatever_the_headers_list` in its three cases, `test_task088_r3_none_ends_at_a_word_boundary` in its six, `test_task088_r3_plan_checks_disagreement_line_carries_the_launchers_remedy`), every other test passes and keeps passing.
- [ ] Every test file of round 1's Done steps 6 and 7, and the further files round 1's search found, passes or skips by its own condition, unedited.
- [ ] Round 2's acceptance criteria stand (one locator, one reader, one escape).

## Constraints
Round 1's and round 2's Constraints stand: tests with `python -m pytest` directly, never through `bridge-run.py`; no script of your own; scratch checks only as `tests/test_task088_scratch_*.py`, deleted; no path of this computer in anything you write. **Mutation: name the code points, run nothing**: for P1 the `none` refusal reached only on a disagreement again, P2 `none` matched by a list of following characters again, P3 plan-check's disagreement line without the remedy; each with the function and lines after your change and the test id you expect to catch it; and update round 2's code points where your change moved them.

## Done
Your report is `handoff/TASK-088-r3-report.md`, written as you go, in round 2's form (files changed, a summary paragraph, one line for each of S1 to S3, the mutation code points, every command with its output quoted verbatim, the commit its counts belong to and whether the tree held uncommitted changes, and the last section headed exactly `Assumed, not verified`).

Run from the Workspace root, each on its own, synchronously in the foreground, with no environment change. Steps 1 and 2 before your first edit; steps 3 to 12 after your last edit:
1. `git status --short` (expect the supervisor's checkpoint clean)
2. `python -m pytest -p no:cacheprovider -q tests/test_improve_satisfies_reader.py` (quote the summary line and the failing ids)
3. to 12. Round 1's brief's Done steps 3 to 12, the same commands, and round 1's search's further files in one more command of the same form.

Your last message is the summary and the report file's path, and nothing follows it.
