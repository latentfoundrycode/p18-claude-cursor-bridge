---
record: brief
header: 1
id: "TASK-064"
round: 3
satisfies: [R-083]
scope: ["bridge/cursor-bridge/bridge_env.py", "bridge/cursor-bridge/MANIFEST.json", "tests/test_program_branch_rule.py", "docs/BUILDER_NOTES.md", "handoff/TASK-064-r3-report.md"]
merge_unit: null
blocking_class: "safety mechanism"
---
# TASK-064 round 3: every field the latest reading groups or ranks by is of its type, or the head is cannot read (R-083)

Round cause: defect

Blocking class: safety mechanism - Review B, round 1 (PR #174): a workflow-runs reply missing workflow_id reaches head_state as a value, and latest_of_each groups a failed run and a later successful run under one empty key and keeps only the success, a false pass

## Objective
Fix the following confirmed defect, and nothing else.

This is round 3 of TASK-064. Rounds 1 and 2 built and hardened the GitHub reader in `bridge/cursor-bridge/bridge_env.py`; Review A and the security audit approved round 2; all of it stays as it is except what H1 below changes. The supervisor commits round 2's tree together with this brief and the new tests before your run, so the line numbers below hold when you start.

**Root cause, in one sentence:** `head_state` (lines 4138-4158 as of round 2's tree) refuses an entry only where a field it ranks by cannot be read (`_rank_reason`, 4189-4209: a run's `run_number`, `run_attempt` and `id`, a check's `id`, a status's `updated_at`), and not where a field `latest_of_each` (4253 onward) **groups** by cannot be read, so a run with no `workflow_id`, a check with no `name` or with a `check_suite` or `app` whose `id` is not an integer, or a status with no `context`, is grouped under an empty or wrong key, and a newer failure can be dropped for an older success.

**Evidence:**
1. Review B's reproduction on round 2's tree, through the `GH_COMMAND` stand-in: runs 10 (failed) and 20 (passed), neither carrying `workflow_id`: `head_state` answers a value, `latest_of_each` keeps run 20 alone, `ci_class` passed.
2. Round 2's security audit (advisory then): an old passed check whose `check_suite.id` is the string "8", beside a newer failed check of the latest suite 9, is kept beside it from a value answer; and two statuses of one context at one `updated_at`, the newer without an integer `id`, rank the older first.

**The design rule the supervisor rules (H1):** every field `latest_of_each` groups or ranks by is checked for its type in `head_state`, and an entry that fails the check makes the head cannot read, as round 2 did for the ranking fields. This closes the family, not the one field: a later field added to the grouping is added to the same check.

**The reproduction tests:** `tests/test_program_branch_rule.py`, the section headed `# ---------------------------------------------------------------- round 3 (Review B of PR #174): every field the latest reading groups by`, at the end of the file. On round 2's tree, `python -m pytest -q -rfE tests/test_program_branch_rule.py` gives `30 failed, 101 passed in 27.79s`: the 30 red are every id of the round-3 section; round 1's, round 2's and the mutation section's 101 pass and must still pass.

Satisfies: R-083 - One reader of a repository's branch rule, and the proof that CI passed as a program (T-CONTEXT, C7): [...] a head's workflow runs, checks and commit statuses, of which only the latest of each source counts (a run by its workflow and event, by run number then attempt; a check a workflow run made only where its run, found by the check suite both name, is a latest run, and of its name there the last one [...]; a check no workflow run made by its name and app; a status by its context) [...]. (Full text: its row in `docs/REQUIREMENTS.md`. This brief serves the reader's refusal of a head entry whose grouping fields cannot be read.)

## Scope
Files you may create or modify:
- bridge/cursor-bridge/bridge_env.py
- bridge/cursor-bridge/MANIFEST.json
- tests/test_program_branch_rule.py
- docs/BUILDER_NOTES.md
- handoff/TASK-064-r3-report.md

Limits on these files:
- `bridge/cursor-bridge/bridge_env.py`: only `_rank_reason` (4189-4209) and, if you need it, the two lines in `head_state` that call it (4154-4156). You may rename `_rank_reason` if its new name says more (then change its one call). Nothing else in the file changes: `latest_of_each`, `_last_by`, `_parse_time`, `ci_class`, `branch_rule`, the call helper and every other function stay byte-identical to round 2's tree.
- `tests/test_program_branch_rule.py` is the supervisor's acceptance file, in Scope only so that its new section counts as this round's; read and run it and **edit nothing in it**.
- `bridge/cursor-bridge/MANIFEST.json` changes only by being regenerated with `python tools/make-manifest.py` (Done). `bridge/cursor-bridge/VERSION` is outside Scope: restore it with `git restore bridge/cursor-bridge/VERSION` right after (Done).
- `handoff/TASK-064-r3-report.md` is your report. The earlier reports are the supervisor's records; do not edit them.

Do not modify anything else.

## Out of scope
- .env and anything under secrets/
- CI configuration
- docs/ and handoff/, except the files the Scope section names. Every record under docs/ is the supervisor's.
- `bridge/cursor-bridge/conformance-check.py`, `bridge/cursor-bridge/review-guard.py` and every other program and test file; `tests/fixtures/github/` (the recorded replies already carry every field H1 checks).
- `latest_of_each`'s own handling of a state not read by `head_state`: it keeps its interface and raises nothing, as now; it is not asked to answer cannot read.
- A rule type GitHub does not have (round 2's G1 stands) and `pull_refs`' reading of `"0"`: the supervisor's records.
- Any mutation script. The mutation run is the supervisor's, after your run.

## Context
**The design that binds this round** is the earlier rounds': `docs/DESIGN.md`, "Change: the program release", the bullet group **The review guard, `review-guard.py`, and the rule's reader in `bridge_env.py`**; "Security and secret handling" (bullet **GitHub reads**); the briefs `handoff/TASK-064.md` (R6, R7) and `handoff/TASK-064-r2.md` (G4), which stand except where this brief rules otherwise; and the inventory's row "GitHub's replies are outside input to the rule's reader" (`docs/INVENTORY.md`, Decisions).

**What `latest_of_each` reads** (round 2's tree, 4253 onward): a run's `workflow_id` and `event` (its group), `run_number`, `run_attempt`, `id` (its rank) and `check_suite_id` (to find its checks); a check's `check_suite.id` (to find its run), `name` and `app.id` (its group), `status`, `started_at` and `id` (its rank); a status's `context` (its group), `updated_at` and `id` (its rank). `status`, `conclusion` and `state` are read by `ci_class`, whose closed lists already class an unknown or missing value as pending or failed; `started_at` may be missing (round 2's G3).

**The recorded replies** (`tests/fixtures/github/`): every check run carries `check_suite.id` and `app.id` as integers and a `name`; every workflow run carries `workflow_id`, `event`, `check_suite_id`, `run_number`, `run_attempt` and `id`; every status carries `context`, `id` and `updated_at`. GitHub's documentation gives each of these on every entry.

**External service, security context, development data, host:** as in the earlier rounds. No test of yours and no command you run calls the real GitHub; do not run `gh` yourself.

## Diagrams
As the earlier rounds (`docs/diagrams/D-002-components.md`, element `bridge_env`): the fix adds no import and no call.

## Requirements
Use the label H1 in your report.

1. **H1. Every grouping and ranking field is checked for its type.** `head_state` answers cannot read, with that list as `source` and a reason naming the field (for a nested field, its object's name is enough, for example `check_suite.id is not an integer`, or `app is not an object`), where:
   - a **workflow run** lacks an integer `id`, `run_number`, `run_attempt`, `workflow_id` or `check_suite_id`, or a non-empty string `event`;
   - a **check run** lacks an integer `id`, a non-empty string `name`, a `check_suite` object with an integer `id`, or an `app` object with an integer `id`;
   - a **commit status** lacks a non-empty string `context`, an integer `id`, or an `updated_at` that `_parse_time` reads (round 2's G4 and G5).
   A bool is never an integer; a missing key, a null and a value of another type are all "lacks". An entry that is not an object is cannot read as today. Nothing else changes: a check's `started_at` may still be missing, and the answer for a head whose entries all pass is unchanged. Tests: every id of the round-3 section; round 2's `test_r083_r2_an_entry_without_the_fields_its_order_needs_is_cannot_read` (8 ids) and `test_r083_r2_the_well_formed_entries_still_read_as_a_value` stay green, and so do the recorded-reply cases (`test_r083_a_head_s_checks_statuses_and_runs_on_the_recorded_replies`, `test_r083_the_captured_head_keeps_every_entry`, the page-by-page cases).

## Acceptance criteria
- [ ] Every case in `tests/test_program_branch_rule.py` passes: the 30 red ids of the round-3 section turn green and the 101 others stay green.
- [ ] `python -m pytest -q tests/test_review_guard.py tests/test_release_s_records_gate.py tests/test_conformance_check.py` passes whole.
- [ ] The defect is fixed at the mechanism named: the type check in `head_state` covers every field `latest_of_each` groups or ranks by, as H1 lists them; no special case for a test's values.
- [ ] Every function other than `_rank_reason` (and the two lines that call it) is byte-identical to round 2's tree; no exception from a reply escapes, and none is swallowed into a value.
- [ ] `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` prints `RESULT: SOURCES MATCH`; `python tools/dump-cli.py --check` exits 0; `git status --short` does not list `bridge/cursor-bridge/VERSION` at the end.
- [ ] `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks` passes.

## Constraints
- Fix the cause; never suppress a test's symptom. No retry, no broad `try/except`, no special case for the values the tests use.
- Do not edit `tests/test_program_branch_rule.py` or anything under `tests/fixtures/github/`.
- **Known failures:** on round 2's tree, `30 failed, 101 passed in 27.79s` in `tests/test_program_branch_rule.py` (the round-3 section). None in the other files the Done section runs. If a case fails that this change did not cause, report it by its test id with its failure lines and fix none.
- **If you believe the real cause is different from the one named, stop, do not change code, and report why in your summary.** Likewise if an existing case requires `head_state` to answer a value for an entry H1 rules cannot read: stop and report it by its test id.
- Prefer reuse: one check function for the three lists, `_answer` for the result. Write the minimum that meets the acceptance criteria (the frozen `minimal-code.mdc` is in force).
- Do not add dependencies or imports. Do not read or write any file outside this workspace. No secret is needed or used.
- If the brief, the rules, or the tooling got in your way, append one dated line to `docs/BUILDER_NOTES.md`; likewise for anything you learned about a defect or a pitfall.
- In any Markdown you write, never break a line inside a paragraph or a list item.
- **Run every command synchronously, in the foreground, and wait for it to end.** Start nothing in the background and leave no process running.
- **Do NOT run the full `tests/` tree.** Run only the test files the Done section names, exactly as written there, with no `PYTHONPATH` or other environment change.
- ASCII program text and ASCII output.
- These git commands are not yours to run: `commit`, `push`, `switch`, `checkout`, `merge`, `rebase`, `reset`, `stash`, `branch -d`, `worktree`. You read with `git status`, `git diff` and `git log` only. The single exception is `git restore bridge/cursor-bridge/VERSION`, at Done step 3. Never run `git -h`, `git help` or `git <cmd> --help` (on Git for Windows they open a browser window).
- Every verification command is written in the Done section in full; run exactly those, from the Workspace root. Write no mutation script and leave none in the diff.

## Done
Your report is the file `handoff/TASK-064-r3-report.md`. Write it as you go. It names no computer path and no user name: write `<Workspace>` for the repository folder and `<tmp>` for a temporary folder, including in quoted command output.

When you finish, it holds:
- a list of every file you changed;
- a one-paragraph summary of what you did;
- for H1, one sentence on what changed, naming the function and its lines as the file stands after your change, and one sentence stating how the change addresses the named cause;
- every command of the list below with its output;
- a section headed exactly `Assumed, not verified`, as the report's last section: one item per line, what you assumed · why · what would confirm it, or `Assumed, not verified: none`.

Run these from the Workspace root, in this order, after your last edit, each synchronously in the foreground, with no `PYTHONPATH` or other environment change:
1. `git status --short`
2. `python tools/make-manifest.py`
3. `git restore bridge/cursor-bridge/VERSION`
4. `git status --short` (`bridge/cursor-bridge/VERSION` must not be listed; if it is, report it)
5. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`
6. `python tools/dump-cli.py --check`
7. `python -m pytest -q -rfE tests/test_program_branch_rule.py`
8. `python -m pytest -q tests/test_review_guard.py tests/test_release_s_records_gate.py tests/test_conformance_check.py`
9. `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks`
10. `git rev-parse HEAD` and `git status --short`

Quoting rules:
- Every command you ran is quoted in the report with the lines it printed, verbatim, in a fenced block; each pytest summary line verbatim; never restate a count in prose.
- A command you did not run is written `not run`, never described as run.
- Write the report's results after step 10, naming the commit its counts belong to and whether the working tree then held uncommitted changes.

Your last message is the summary and the report file's path, and nothing follows it.
