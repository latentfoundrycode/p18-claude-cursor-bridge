---
record: brief
header: 1
id: "TASK-069"
round: 2
satisfies: [R-089]
scope: ["bridge/cursor-bridge/review-guard.py", "bridge/cursor-bridge/pace-report.py", "bridge/cursor-bridge/bridge_env.py", "bridge/cursor-bridge/MANIFEST.json", "docs/cli-reference.json", "docs/CLI_REFERENCE.md", "tests/test_pace_report.py", "docs/BUILDER_NOTES.md", "handoff/TASK-069-r2-report.md"]
merge_unit: null
blocking_class: null
---
# TASK-069 round 2: review passes and round causes in the pace report (R-089)

Round cause: defect - bridge/cursor-bridge/pace-report.py:763-768 and 1099-1102, a PR-<n>'s start at its commit's time is taken as a known start for the Mean days column, so every untagged records pull request adds a 0 and pulls the mean towards zero (behaviour); bridge/cursor-bridge/pace-report.py:723-724, `_pace_names` counts every pass-line name, so a stage review or a design critique starts an increment and enters the cause line, while the guard's STAGE- records are excluded (behaviour)

## Objective
This is round 2 of TASK-069. Round 1's code is committed (the commit "TASK-069 r1: the builder's work (rejected) and the round-2 tests") with the supervisor's six new cases at the end of the acceptance file, after the comment that names `Round 2 (TASK-069-r2)`, each named `test_r089_r2_...`. Make the corrections below, keep every test green, and edit nothing in the acceptance file. Round 1's brief, `handoff/TASK-069.md`, stays in force for everything this brief does not change.

Satisfies: R-089 - as round 1's brief.

## Scope
Files you may create or modify:
- bridge/cursor-bridge/review-guard.py
- bridge/cursor-bridge/pace-report.py
- bridge/cursor-bridge/bridge_env.py
- bridge/cursor-bridge/MANIFEST.json
- docs/cli-reference.json
- docs/CLI_REFERENCE.md
- tests/test_pace_report.py
- docs/BUILDER_NOTES.md
- handoff/TASK-069-r2-report.md

Limits on these files: as round 1's brief. `review-guard.py`: correction 5 alone. `bridge_env.py`: only where a correction needs a shared helper. `tests/test_pace_report.py`: only the ISS-013 case's docstring (correction 6); no assertion changes. `tests/test_program_pace_rounds.py`, `tests/test_review_guard_ceiling.py`, `tests/test_d003_review_round_states.py`, `tests/test_program_in_flight.py` and `tests/test_release_s_launcher.py` are the supervisor's, read only. The generated files only through their generators, as round 1.

## Out of scope
As round 1's brief. Nothing beyond the corrections: no refactoring, no other finding of the reviews (the supervisor records the rest in `docs/HARDENING.md`), no option, no environment variable, no new dependency. `bridge-run.py` keeps its own reading of a brief's `Round cause:` line unchanged.

## Corrections
1. **A pull request's own start is no known start for the days (behaviour).** A `PR-<n>` that has no launcher row, guard round or pass line starts at its commit's time for the Started column only. The Mean days column, and every other reading of a known start, takes a start only from a launcher row, a guard round or a pass line, so such a pull request adds nothing to the days. Case: `test_r089_r2_a_pull_request_s_own_start_is_no_known_start_for_the_days`, and the ISS-013 case's empty days cell.
2. **A stage review or a design critique is no counted name, from any source (behaviour).** A name that begins `STAGE-` or `DESIGN-` (a stage review, or a design critique: neither merges anything of its own) is no counted name whatever its source, the guard's rounds record or a pass line, exactly as the guard's `STAGE-` records already are: it starts nothing, merges nothing, and its rounds enter no cause line. Its passes still count in the passes lines, by the same rules as any name's (a guard round of it is a `review-b` pass; a pass line counts where the guard holds no round of that name and number). The over-ceiling stage list keeps its present rule. Case: `test_r089_r2_a_stage_review_or_a_design_critique_is_no_counted_name`.
3. **The PR-<n> rule holds in both modes (the supervisor's ruling).** With `handoff/` untracked, a squash closing `(#<n>)` whose subject names no ID the reader finds is merged as `PR-<n>`, as with `handoff/` tracked. Say so in the docstring, which now says the opposite ("every ID the reader finds, as before"), and in the report. Case: `test_r089_r2_with_handoff_untracked_a_pull_request_is_counted_too` (already green; keep it).
4. **The in-flight log's bound is in bytes (data integrity of the stated bound).** Read the log in binary, at most the stated number of bytes plus one, then decode with `errors="replace"`, so the docstring's "at most 8388608 bytes" is true; and a pass line's stamp matches ASCII digits only (`[0-9]`, never `\d`), the form `in-flight.py` writes. Case for the digits: `test_r089_r2_a_stamp_of_other_digits_is_no_pass_line` (already green; keep it).
5. **The guard's read of the round's cause is bounded and linear (security hardening).** `review-guard.py` reads the round's SCOPE file within a byte bound (for example 1 MiB, stated in the docstring), and finds the cause line without a regular expression that can backtrack: the first line that begins `Round cause:`, the text after it stripped of spaces and tabs, then the same longest-cause-first and separator rule as round 1. A file over the bound, unreadable or with no such line gives `unstated`; the snapshot is never refused for it. Case: `test_r089_r2_a_long_scope_line_never_stalls_the_snapshot` (a line of 200,000 spaces between two words: under 20 seconds, cause `unstated`).
6. **The ISS-013 case's docstring.** In `tests/test_pace_report.py`, `test_r044_iss013_form_merges_nothing_with_plan_check`'s docstring no longer says the subject counts no merge: say that it merges no increment and is counted as its pull request, `PR-61` (R-089). Its assertions stay as round 1 left them.

## Context
The acceptance file gained six cases, `test_r089_r2_...`, after the comment that names `Round 2 (TASK-069-r2)`. On round 1's code: "4 failed, 2 passed" (the untracked-mode case and the stamp case already hold; keep them holding). The failures: Mean days `7` where TASK-701's `14` is the only known start; Started `2` and a cause line from the STAGE- and design pass lines; the ISS-013 days cell `0` where it is empty; the long SCOPE line took 68 seconds.

## Acceptance criteria
- [ ] Every test in `tests/test_program_pace_rounds.py` passes, and every test of round 1's Done list passes.
- [ ] Corrections 1 to 6 met, each named in the report with its function and lines.
- [ ] Every line added ASCII.

## Constraints
Round 1's Constraints all stand. Mutations by hand, in process, each reverted, listed by label with the pytest line that shows a test failing, else `not run`: (H1) the commit-time start fed to the days again; (H2) the STAGE-/DESIGN- exclusion dropped for pass-line names; (H3) the guard's cause read without its byte bound and with round 1's regular expression; (H4) `\d` in the stamp's pattern. Prefer the smallest change.

## Done
Your report is `handoff/TASK-069-r2-report.md`, in round 1's form (files changed; summary; each correction with its function and lines; every command of round 1's Done list with its output, verbatim, in fenced blocks; the mutations H1 to H4; a last section headed exactly `Assumed, not verified`). It names no computer path: `<Workspace>` for the repository folder, `<tmp>` for a temporary folder.

Run round 1's Done list, in order, from the Workspace root, after your last edit, each in the foreground, with no environment change; quote the last run. Every pytest summary line quoted verbatim; never restate a count in prose. Your last message is the summary and the report file's path, and nothing follows it.
