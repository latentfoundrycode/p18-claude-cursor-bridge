---
record: brief
header: 1
id: "TASK-069"
round: 3
satisfies: [R-089]
scope: ["bridge/cursor-bridge/pace-report.py", "bridge/cursor-bridge/MANIFEST.json", "docs/BUILDER_NOTES.md", "handoff/TASK-069-r3-report.md"]
merge_unit: null
blocking_class: null
---
# TASK-069 round 3: review passes and round causes in the pace report (R-089)

Round cause: defect - bridge/cursor-bridge/pace-report.py:743-757 and 790-797, a `PR-<n>` the subject reader finds in a squash subject is read as a name that subject names, so `PR-2: follow-up (#1)` folds PR-1 into PR-2 and marks PR-2 merged though no commit closes `(#2)` (behaviour); bridge/cursor-bridge/pace-report.py:596-598, a pass line whose cause is a word outside the round causes' list is dropped whole, where the plan reads it as a pass of its round with the cause `unstated` (behaviour)

## Objective
This is round 3 of TASK-069, the review ceiling's round. Round 2's code is accepted and committed; Review B's round 1 found the two behaviour defects above. The supervisor's two new cases are at the end of the acceptance file, after the comment that names `Round 3 (TASK-069-r3)`, each named `test_r089_r3_...`. Make the two corrections below, keep every test green, and edit nothing in the acceptance file. Round 1's brief, `handoff/TASK-069.md`, and round 2's, `handoff/TASK-069-r2.md`, stay in force for everything this brief does not change.

Satisfies: R-089 - as round 1's brief.

## Scope
Files you may create or modify:
- bridge/cursor-bridge/pace-report.py
- bridge/cursor-bridge/MANIFEST.json
- docs/BUILDER_NOTES.md
- handoff/TASK-069-r3-report.md

Limits on these files: `pace-report.py`, the two corrections alone; `MANIFEST.json` only through its generator, as round 1. Every other file is read only, among them `review-guard.py`, `bridge_env.py`, the command reference and every test file (`tests/test_program_pace_rounds.py` is the supervisor's). The help text does not change, so the command reference is not regenerated.

## Out of scope
As round 1's brief. Nothing beyond the two corrections: no refactoring, no other finding (the supervisor records the rest in `docs/HARDENING.md`, among them its TASK-069 leads 1 to 9), no option, no environment variable, no new dependency.

## Corrections
1. **A pull request is merged by its closing number alone (behaviour).** A name of the form `PR-<n>` that the subject reader returns from a squash subject is never a name that subject names: not for choosing the name a `PR-<n>` folds into (the loop over `commits` that builds `fold` and `own`, in `_pace_names`), not for occupying a commit in untracked mode, and not for marking a name merged (the loop over `commits` that builds `merge_dt`). `PR-<n>` is merged only by a commit of `refs/heads/main` whose subject closes with `(#<n>)`, as the plan says. So `PR-2: follow-up (#1)` names no counted name: it counts and merges `PR-1`, which starts at its commit, and `PR-2`, counted from its pass line, stays started and not merged. Case: `test_r089_r3_a_pull_request_is_merged_by_its_closing_number_alone`.
2. **A pass line with a word outside the causes is `unstated`, not dropped (behaviour).** In `_parse_pass_line`, a cause that is not in `bridge_env.ROUND_CAUSES` is read as `unstated` (the plan: "`unstated` for a row, a round or a pass line that names none or names a word outside the list"); the line stays a pass of its name, reviewer kind and round, and a record of that round for the cause line and the week. Every other refusal of the parser stands (stamp, name, round number, reviewer kind). Case: `test_r089_r3_a_pass_line_naming_a_word_outside_the_causes_is_unstated`.

## Context
The acceptance file gained two cases, `test_r089_r3_...`, after the comment that names `Round 3 (TASK-069-r3)`. On round 2's code they are expected to fail: the first reads Started and Merged for the week as the subject's PR-2 fold gives them, the second finds no cause line and no review-a pass. The supervisor's red run's output is quoted in the commit that added them ("TASK-069 r3: Review B's two findings as tests").

## Acceptance criteria
- [ ] Every test in `tests/test_program_pace_rounds.py` passes, and every test of round 1's Done list passes.
- [ ] Corrections 1 and 2 met, each named in the report with its function and lines.
- [ ] Every line added ASCII.

## Constraints
Round 1's Constraints all stand. Mutations by hand, in process, each reverted, listed by label with the pytest line that shows a test failing, else `not run`: (H1) the subject reader's `PR-<n>` read again as a name the subject names in the merge loop alone; (H2) a cause outside the list dropping the pass line again. Prefer the smallest change.

## Done
Your report is `handoff/TASK-069-r3-report.md`, in round 1's form (files changed; summary; each correction with its function and lines; every command of round 1's Done list with its output, verbatim, in fenced blocks; the mutations H1 and H2; a last section headed exactly `Assumed, not verified`). It is ASCII only: no dash, quote or other character above 127. It names no computer path: `<Workspace>` for the repository folder, `<tmp>` for a temporary folder.

Run round 1's Done list, in order, from the Workspace root, after your last edit, each in the foreground, with no environment change; quote the last run. Every pytest summary line quoted verbatim; never restate a count in prose. Your last message is the summary and the report file's path, and nothing follows it.
