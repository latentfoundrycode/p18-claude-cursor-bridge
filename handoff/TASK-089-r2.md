---
record: brief
header: 1
id: "TASK-089"
round: 2
satisfies: [R-111]
scope: ["bridge/cursor-bridge/bridge_env.py", "bridge/cursor-bridge/plan-check.py", "bridge/cursor-bridge/bridge-run.py", "bridge/cursor-bridge/records-migrate.py", "bridge/cursor-bridge/MANIFEST.json", "docs/cli-reference.json", "docs/CLI_REFERENCE.md", "docs/BUILDER_NOTES.md", "handoff/TASK-089-r2-report.md"]
merge_unit: null
blocking_class: null
---
# TASK-089 (round 2): Plan headings take the bridge's other increment prefixes

Round cause: round 1's work stands and meets Requirements 1 to 7 of round 1's brief; the security audit (advisory, behaviour: `bridge_env.py` `_plan_normalize_field` and plan-check's `ids_in` and `unreadable` read a plan id out of a longer word, so `Depends on: HOTFIX-004` gives `FIX-004` and `Parent: DEBUG-001` gives `BUG-001`, the new short prefixes making it likely) and Review A (behaviour: the grammar-style mapping of a `task-` branch with fewer than three digits no longer keeps the rest's letter case, `task-03x` giving `TASK-03X` where the checkpoint gave `TASK-03x`, against round 1's Requirement 2 "task- behaviour unchanged"; records: the report did not quote the three repository reads whole, and its `Assumed, not verified` list read none) send it back. Review A's one blocking item was a supervisor test edit, corrected at this checkpoint.

Satisfies: R-111

## Objective
Round 1's work stands in the tree: `PLAN_ID_PREFIXES`, the composed `PLAN_ID_PATTERN`, `_PLAN_BRANCH_RX`, `_PLAN_MERGE_BRANCH`, `_cand_from_plan_branch`, the readers that use them, and plan-check's brief files and DEPENDS message. This round corrects two things. Read `handoff/TASK-089.md` (round 1's brief) whole first: its Context, its Requirements 1 to 7, its Constraints and its Done stand, except where this brief changes them. Read `handoff/TASK-089-r1-report.md`, your round-1 report.

## Scope
Files and directories you may create or modify:
- bridge/cursor-bridge/bridge_env.py
- bridge/cursor-bridge/plan-check.py
- bridge/cursor-bridge/bridge-run.py
- bridge/cursor-bridge/records-migrate.py
- bridge/cursor-bridge/MANIFEST.json
- docs/cli-reference.json
- docs/CLI_REFERENCE.md
- docs/BUILDER_NOTES.md
- handoff/TASK-089-r2-report.md

Do not modify anything else.

Limits on these paths: as round 1's brief. `tests/test_improve_plan_prefixes.py` is the supervisor's acceptance file: read it whole and run it, **do not edit it**. It now holds round 2's tests below the comment line that ends `round 2`.

## Out of scope
As round 1's brief, and also `tests/test_task033_supervisor.py`, `tests/test_plan_check.py` and `tests/test_task032_supervisor_launcher.py`: the supervisor changed expectations in each (the plan pattern a test passes is `bridge_env.PLAN_ID_PATTERN`; the ISS-013 subject and `BUG-018: x (#61)` merge BUG-018 under the plan pattern; the history regression compares TASK ids). They pass on round 1's code; keep them passing.

## Requirements (this round; round 1's Requirements 1 to 7 stand where these do not change them)
R1. **An id is read only where it stands as a word of its own.** Wherever a plan id is picked out of a longer text by search, findall or substitution rather than matched whole, it counts only where the character before it is not a letter or a digit (and the start of the text counts): the header's `parent` and `depends_on` reading in `_plan_normalize_field` (round 1: `_PLAN_TASK_RX.findall`), and plan-check's `ids_in` and `unreadable` (`ID_RX.findall` and `ID_RX.sub`). So `HOTFIX-004`, `DEBUG-001` and `SUBTASK-001` name no id: plan-check reports each value as unreadable as written (`DEPENDS: TASK-002 has an unreadable Depends On value 'HOTFIX-004' ...`) and names no dependency or parent read out of it; `_plan_normalize_field("depends_on", "TASK-001, HOTFIX-004")` gives `["TASK-001"]`; a `parent` value naming no id is returned as written, as on the checkpoint. `PLAN_ID_PATTERN`'s value stays exactly as round 1's Requirement 1 fixes it (the boundary is added where the pattern is used, through one shared compiled pattern or helper in `bridge_env.py`, which plan-check imports rather than spelling its own). A match of the whole value (`fullmatch`, `HEAD_RX`, the subject, parenthesis, trailer and merge forms, the brief file name read under a prefix glob) is unchanged.

R2. **The grammar-style branch mapping answers `task-` exactly as on the checkpoint, and every prefix the same way.** In the grammar style (the launcher's reading, `_branch_name_to_id` through `_grammar_merge_id`), a branch name that begins with one of the five prefixes and a hyphen, in any letter case, maps first, as round 1 does, to the prefix upper-cased with the digits and optional letter it begins with (`bug-001-x` gives `BUG-001`, `Bug-001a` gives `BUG-001a`); failing that, to the prefix upper-cased followed by the rest of the name as written, where that fullmatches the id pattern given (`task-03x` gives `TASK-03x` and `task-12-fix` gives `TASK-12-fix`, as on the checkpoint; `bug-12-fix` gives `BUG-12-fix`); failing that, the forms after it as on the checkpoint (the name as written, upper-cased, its first part upper-cased: `hotfix-004` gives `HOTFIX-004`). The plan style is unchanged from round 1. The acceptance tests list the forms.

R3. **The report quotes what it ran.** The three repository reads of round 1's Requirement 7 are quoted whole, before and after (the records-migrate `--check` listing included, however long), each pair stated identical or each differing line named; every failing test of a Done step is named by id with its failure lines.

R4. **`Assumed, not verified` is real.** It names every fact your change relies on that the brief, the code and the tests did not settle (for example, what the boundary does at a `_`, an em dash or a non-ASCII letter before an id; a branch name with a slash; a value whose id is followed by letters), or states for each example of round 1's brief why it is settled.

## Acceptance criteria
- [ ] Every test of `tests/test_improve_plan_prefixes.py` passes, the file unedited (91 tests). The supervisor's run on round 1's code, 2026-11-27: 8 failed, 83 passed. Failing: `test_task089_r2_an_id_inside_a_longer_word_is_read_whole_by_plan_check`, `test_task089_r2_the_headers_field_reading_keeps_a_longer_word_whole[hotfix]`, `[task-and-hotfix]`, `[subtask]` and `[debug-parent]`, `test_task089_r2_the_grammar_style_maps_a_branch_of_each_prefix_as_task[task-03x]`, `[task-12-fix]` and `[bug-12-fix]`. Passing and to keep passing: every round-1 test, the other round-2 cases (among them `[two-ids]`, `[bug-parent]`, every plan-style branch case and `test_task089_r2_a_leading_id_wins_over_the_closing_parenthesis`, the supervisor's ruling that a subject's leading ids win over its closing parenthesis for every prefix, as for TASK on the checkpoint).
- [ ] Every test file of round 1's Done steps 8 to 11 passes or skips by its own condition, unedited, the three files under Out of scope among them.
- [ ] The three repository reads identical before and after (R3).
- [ ] The command reference, MANIFEST, `bridge-check`, VERSION and ASCII checks as in round 1's brief.

## Constraints
Round 1's brief's Constraints stand, among them: run the tests with `python -m pytest -p no:cacheprovider -q` directly, never through `bridge-run.py`, never the whole `tests/` tree; no script of your own; scratch checks only as `tests/test_task089_scratch_*.py`, deleted; no path of this computer in anything you write (`<Workspace>`, `<tmp>`, `~`); the three repository reads are the only programs run against this repository. **Mutation: name the code points, run nothing**: for round 1's M1 to M8 (correct M4's catching test: the grammar style is not plan-check's path; name a test of `test_task089_r2_the_grammar_style_maps_a_branch_of_each_prefix_as_task`) and these, N1 the boundary dropped from `_plan_normalize_field`, N2 the boundary dropped from plan-check's `ids_in`, N3 the boundary dropped from `unreadable`, N4 the rest-as-written step of R2 removed, N5 the digit form of R2 tried after the rest-as-written step; each with the function and lines after your change and the test id you expect to catch it.

## Done
Your report is `handoff/TASK-089-r2-report.md`, written as you go, in round 1's form: the files you changed, a summary paragraph, one line for each of R1 to R4 naming the functions and lines that meet it, the mutation code points, every command you ran with its output quoted verbatim, the commit its counts belong to and whether the tree held uncommitted changes, and the last section headed exactly `Assumed, not verified` (one item per line: what you assumed, why, what would confirm it).

Run from the Workspace root, each on its own, synchronously in the foreground, with no environment change. Steps 1 to 3 before your first edit; steps 4 onward after your last edit, in this order:
1. `git status --short` (expect the supervisor's checkpoint clean)
2. `python -m pytest -p no:cacheprovider -q tests/test_improve_plan_prefixes.py` (quote the summary line and the failing ids)
3. The three repository reads of round 1's Requirement 7, quoted whole.
4. onward: round 1's brief's Done steps from `python tools/dump-cli.py` to its last step, the same commands, its test-file steps naming the same files (the three files under Out of scope are among them), with the three repository reads again quoted whole.

Your last message is the summary and the report file's path, and nothing follows it.
