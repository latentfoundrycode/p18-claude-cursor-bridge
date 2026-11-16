---
record: brief
header: 1
id: "TASK-064"
round: 4
satisfies: [R-083]
scope: ["bridge/cursor-bridge/bridge_env.py", "bridge/cursor-bridge/MANIFEST.json", "tests/test_program_branch_rule.py", "docs/BUILDER_NOTES.md", "handoff/TASK-064-r4-report.md"]
merge_unit: null
blocking_class: "safety mechanism"
---
# TASK-064 round 4: a list read in pages is one view of GitHub, or the head is cannot read (R-083)

Round cause: defect

Blocking class: safety mechanism - Review B, round 2 (PR #174): a workflow-runs list whose first page states 101 runs and whose second page states 102 (a run created between the two reads) reaches head_state as a value of 101 runs without the new run, and latest_of_each keeps an older passed run for that workflow, a false pass

## Objective
Fix the following confirmed defect, and nothing else.

This is round 4 of TASK-064. Rounds 1 to 3 built and hardened the GitHub reader in `bridge/cursor-bridge/bridge_env.py`; Review A and the security audit approved round 3; all of it stays as it is except what I1 below changes. The supervisor commits round 3's tree together with this brief and the new tests before your run, so the line numbers below hold when you start.

**Root cause, in one sentence:** `_read_list` (lines 4103-4135 as of round 3's tree) keeps the `total_count` of the first page it reads (4121-4122) and ends the reading as soon as it holds that many distinct entries (4131-4132), so a list that grew, shrank or changed between two page reads is taken as whole at the first page's count, and an entry created between the reads is never seen.

**Evidence:**
1. Review B's reproduction on round 3's tree, through the `GH_COMMAND` stand-in: page 1 of the workflow runs states 101 and holds 100 passed runs; page 2 states 102 (a new run was created at the front, shifting the list down by one) and holds the hundredth run again and the 101st. `head_state` answers a value of 101 runs without the new one; every run it returns classes passed.
2. The supervisor's reproduction on round 3's tree (the same shape, the new run in progress): `head_state` answers a value, the new run is absent, and `latest_of_each` keeps the older run 101, `ci_class` passed, where the workflow's latest run is pending.

**The design rule the supervisor rules (I1):** a list read in pages is one view of GitHub. Every page of it states the same `total_count` as its first page, and the reading ends holding exactly that many distinct entries; a page that states another count, or entries beyond the count, means the list changed while it was read, and the head is cannot read. This closes the family (a count that grows, a count that shrinks, more entries than stated, on any of the three lists), not the one shape of Review B's reply.

**The reproduction tests:** `tests/test_program_branch_rule.py`, the section headed `# ---------------------------------------------------------------- round 4 (Review B of PR #174, its second round): one view`, at the end of the file. On round 3's tree, `python -m pytest -q -rfE tests/test_program_branch_rule.py` gives `13 failed, 143 passed in 34.80s`: the red are the round-4 section's growth, shrink, more-entries and Review B cases; its positive control (`test_r083_r4_pages_that_agree_read_as_a_value`, 3 ids) and every case of the earlier sections pass and must still pass.

Satisfies: R-083 - One reader of a repository's branch rule, and the proof that CI passed as a program (T-CONTEXT, C7): [...] a head's workflow runs, checks and commit statuses, of which only the latest of each source counts [...]. (Full text: its row in `docs/REQUIREMENTS.md`. This brief serves the reader's refusal of a head list that changed while it was read in pages.)

## Scope
Files you may create or modify:
- bridge/cursor-bridge/bridge_env.py
- bridge/cursor-bridge/MANIFEST.json
- tests/test_program_branch_rule.py
- docs/BUILDER_NOTES.md
- handoff/TASK-064-r4-report.md

Limits on these files:
- `bridge/cursor-bridge/bridge_env.py`: only `_read_list` (4103-4135). Its name, its arguments and its return shape (the entries and None, or None and a reason) stay. Nothing else in the file changes: `head_state`, `_rank_reason`, `_entry_marker`, `_page_path`, `latest_of_each`, `_last_by`, `_parse_time`, `ci_class`, `branch_rule` and its rules paging, the call helper and every other function stay byte-identical to round 3's tree.
- `tests/test_program_branch_rule.py` is the supervisor's acceptance file, in Scope only so that its new section counts as this round's; read and run it and **edit nothing in it**.
- `bridge/cursor-bridge/MANIFEST.json` changes only by being regenerated with `python tools/make-manifest.py` (Done). `bridge/cursor-bridge/VERSION` is outside Scope: restore it with `git restore bridge/cursor-bridge/VERSION` right after (Done).
- `handoff/TASK-064-r4-report.md` is your report. The earlier reports are the supervisor's records; do not edit them.

Do not modify anything else.

## Out of scope
- .env and anything under secrets/
- CI configuration
- docs/ and handoff/, except the files the Scope section names. Every record under docs/ is the supervisor's.
- `bridge/cursor-bridge/conformance-check.py`, `bridge/cursor-bridge/review-guard.py` and every other program and test file; `tests/fixtures/github/`.
- The rules endpoint's paging in `branch_rule` (its replies state no count): the supervisor's records.
- Reading a list twice, retrying, or waiting: a list that changed while it was read is cannot read, and the caller asks again later.
- Any mutation script. The mutation run is the supervisor's, after your run.

## Context
**The design that binds this round** is the earlier rounds': `docs/DESIGN.md`, "Change: the program release", the bullet group **The review guard, `review-guard.py`, and the rule's reader in `bridge_env.py`**; "Security and secret handling" (bullet **GitHub reads**); the briefs `handoff/TASK-064.md` (R6), `handoff/TASK-064-r2.md` and `handoff/TASK-064-r3.md`, which stand except where this brief rules otherwise; and the inventory's row "GitHub's replies are outside input to the rule's reader" (`docs/INVENTORY.md`, Decisions).

**What `_read_list` does now** (round 3's tree): it asks page 1, 2, ... (`_page_path`, `per_page=100`) up to `_GH_MAX_PAGES`; it refuses a failed call, a body that is not an object, a `total_count` that is not a non-negative non-bool integer and a list that is not a list; it keeps the first page's count; it skips an entry whose `_entry_marker` it has seen; it returns when it holds at least the count, and refuses a page that added no entry and a reading that reached the page bound. All of that stays except the rule I1 changes.

**Why a count can change between pages:** GitHub lists a head's workflow runs newest first and its check runs and statuses as they stand at each call; a run, a check or a status created between two page reads raises the count stated by the later page and shifts the list, so the later page repeats an entry already read and the new entry sits on a page already read.

**External service, security context, development data, host:** as in the earlier rounds. No test of yours and no command you run calls the real GitHub; do not run `gh` yourself.

## Diagrams
As the earlier rounds (`docs/diagrams/D-002-components.md`, element `bridge_env`): the fix adds no import and no call.

## Requirements
Use the label I1 in your report.

1. **I1. A list read in pages is one view.** `_read_list` returns a reason (so `head_state` answers cannot read with that list as `source`) where a page after the first states a `total_count` other than the first page's, or where the distinct entries read exceed the first page's count (on one page or across pages); the reason says the list changed while it was read. It returns the entries only when they number exactly the count every page stated. Nothing else changes: a list read whole on pages that agree is the value it is today, with the same calls. Tests: every id of the round-4 section; the earlier page-by-page cases (`test_r083_the_captured_head_keeps_every_entry`, and every case naming pages, a total count or a page bound) stay green.

## Acceptance criteria
- [ ] Every case in `tests/test_program_branch_rule.py` passes: the red ids of the round-4 section turn green and every other id stays green.
- [ ] `python -m pytest -q tests/test_review_guard.py tests/test_release_s_records_gate.py tests/test_conformance_check.py` passes whole.
- [ ] The defect is fixed at the mechanism named: `_read_list` compares every page's count with the first page's and the entries read with that count, as I1 states; no special case for a test's values.
- [ ] Every function other than `_read_list` is byte-identical to round 3's tree; no exception from a reply escapes, and none is swallowed into a value.
- [ ] `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` prints `RESULT: SOURCES MATCH`; `python tools/dump-cli.py --check` exits 0; `git status --short` does not list `bridge/cursor-bridge/VERSION` at the end.
- [ ] `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks` passes.

## Constraints
- Fix the cause; never suppress a test's symptom. No retry, no re-read, no wait, no broad `try/except`, no special case for the values the tests use.
- Do not edit `tests/test_program_branch_rule.py` or anything under `tests/fixtures/github/`.
- **Known failures:** on round 3's tree, `13 failed, 143 passed in 34.80s` in `tests/test_program_branch_rule.py` (the round-4 section). None in the other files the Done section runs. If a case fails that this change did not cause, report it by its test id with its failure lines and fix none.
- **If you believe the real cause is different from the one named, stop, do not change code, and report why in your summary.** Likewise if an existing case requires `_read_list` to answer the entries for pages whose counts differ: stop and report it by its test id.
- Write the minimum that meets the acceptance criteria (the frozen `minimal-code.mdc` is in force).
- Do not add dependencies or imports. Do not read or write any file outside this workspace. No secret is needed or used.
- If the brief, the rules, or the tooling got in your way, append one dated line to `docs/BUILDER_NOTES.md`; likewise for anything you learned about a defect or a pitfall.
- In any Markdown you write, never break a line inside a paragraph or a list item.
- **Run every command synchronously, in the foreground, and wait for it to end.** Start nothing in the background and leave no process running.
- **Do NOT run the full `tests/` tree.** Run only the test files the Done section names, exactly as written there, with no `PYTHONPATH` or other environment change.
- ASCII program text and ASCII output.
- These git commands are not yours to run: `commit`, `push`, `switch`, `checkout`, `merge`, `rebase`, `reset`, `stash`, `branch -d`, `worktree`. You read with `git status`, `git diff` and `git log` only. The single exception is `git restore bridge/cursor-bridge/VERSION`, at Done step 3. Never run `git -h`, `git help` or `git <cmd> --help` (on Git for Windows they open a browser window).
- Every verification command is written in the Done section in full; run exactly those, from the Workspace root. Write no mutation script and leave none in the diff.

## Done
Your report is the file `handoff/TASK-064-r4-report.md`. Write it as you go. It names no computer path and no user name: write `<Workspace>` for the repository folder and `<tmp>` for a temporary folder, including in quoted command output.

When you finish, it holds:
- a list of every file you changed;
- a one-paragraph summary of what you did;
- for I1, one sentence on what changed, naming the function and its lines as the file stands after your change, and one sentence stating how the change addresses the named cause;
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
