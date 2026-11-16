---
record: brief
header: 1
id: "TASK-064"
round: 2
satisfies: [R-083]
scope: ["bridge/cursor-bridge/bridge_env.py", "bridge/cursor-bridge/conformance-check.py", "bridge/cursor-bridge/MANIFEST.json", "tests/test_program_branch_rule.py", "tests/test_conformance_check.py", "docs/BUILDER_NOTES.md", "handoff/TASK-064-r2-report.md"]
merge_unit: null
blocking_class: null
---
# TASK-064 round 2: a reply the reader does not recognise is cannot read, the rules read page by page, a pending check last in every order (R-083)

Round cause: security

## Objective
Fix the following confirmed defects in round 1's reader, and nothing else.

This is round 2 of TASK-064. Round 1 built the GitHub reader in `bridge/cursor-bridge/bridge_env.py` (lines 3836-4305 as of round 1's tree), the conformance row and the guard's auto-merge line and closing word; all of that stays as it is except what G1 to G8 below change. Review A and the security audit of round 1 found that some replies the reader does not recognise come back as none or as an older passed entry, that the rules list is read as one page, and that one reply raises a traceback. The supervisor commits round 1's tree together with this brief and the new tests before your run, so the line numbers below hold when you start.

**The confirmed defects** (each reproduced in process by a reviewer on round 1's tree, each now a red test):
1. `_rules_contexts` (3972-4003) skips a rule of type `required_status_checks` whose `parameters` is missing, null or a dict without a list `required_status_checks` (`continue` at 3984 and 3988), and skips a rule whose `type` is missing or not a string (3980), so beside a branch with no classic protection such a reply answers none. None sends `ready` to the weaker proof; DESIGN forbids that substitution, and the brief's security context says a reply the reader does not recognise is never none.
2. `branch_rule` reads the rules with one call and no `per_page` (4025). GitHub's rules endpoint returns a bare list, thirty rules a page by default, with no count; a required-status-checks rule on a later page is dropped, giving none or a value with contexts missing.
3. `_last_by` (4175-4193) drops the not-completed rank when `by_id` is set: `by_id` is true when any member of the group, a pending one included, lacks a parseable `started_at`, and the id-only key `(ident, index)` then ranks a completed check above a pending one of lower id, so `ci_class` answers passed where R7 keeps the pending check.
4. `latest_of_each` ranks a run whose `run_number`, `run_attempt` or `id` is not an integer, and a status with no parseable `updated_at`, below every well-formed entry (`_int_rank` at 4159, the status key at 4190), so an older success is kept beside a newer failure. Round 1's brief allowed two readings here ("makes the reading cannot read, or ranks as the closed lists say"); the supervisor rules the first (G4).
5. `_parse_time` (4165-4172) returns a naive datetime for a time with no zone, and comparing it with an aware one raises `TypeError` out of `latest_of_each`.

**Two hardenings the supervisor takes from the audit's advisories** (G6), and **one wrong text** (G7): the none row of the conformance check says "branch protection exists" for a default branch nothing protects.

**The reproduction tests:** `tests/test_program_branch_rule.py`, the section headed `# ---------------------------------------------------------------- round 2 (Review A and the security audit of round 1)`, at the end of the file. On round 1's tree, `python -m pytest -q -rfE tests/test_program_branch_rule.py` gives the result quoted under Constraints, "Known failures"; every case in the file must pass.

Satisfies: R-083 - One reader of a repository's branch rule, and the proof that CI passed as a program (T-CONTEXT, C7): `bridge_env.py` reads a branch's required check contexts, from the classic protection and from the rules that apply to the branch, each with the app its rule names, the branch's name percent-encoded in the path, by GET through `gh api`, each returning the value, none, or cannot read with the reason, none only for the reply of a branch with no protection, matched exactly, and for a success from either source that names no required check, cannot read wherever a source answers anything else that is not a success; [...]. (Full text: its row in `docs/REQUIREMENTS.md`. This brief serves the reader's handling of replies it does not recognise, the rules read whole, the order of a head's entries, and the conformance row's none text.)

## Scope
Files you may create or modify:
- bridge/cursor-bridge/bridge_env.py
- bridge/cursor-bridge/conformance-check.py
- bridge/cursor-bridge/MANIFEST.json
- tests/test_program_branch_rule.py
- tests/test_conformance_check.py
- docs/BUILDER_NOTES.md
- handoff/TASK-064-r2-report.md

Limits on these files:
- `bridge/cursor-bridge/bridge_env.py`: only the GitHub section (from the comment `# ---------------------------------------------------------------- GitHub reads (R-083)` at line 3836 to the end of `ci_class` at 4305), and only as G1 to G6 and G8 say. `ci_class`, `repo_settings`, `_gh_get`'s call (its arguments, time limit, stdin, window flag), `_clip_reason`, `_gh_reason`, `_answer`, `_unprotected`, `_protection_contexts` and `_read_list` keep their behaviour.
- `bridge/cursor-bridge/conformance-check.py`: only the detail text of the none row (line 933), as G7 says.
- `tests/test_program_branch_rule.py` is the supervisor's acceptance file. It is in Scope only so that its new section counts as this round's; you read and run it and **edit nothing in it**.
- `tests/test_conformance_check.py`: round 1's case `test_r083_the_required_check_row_follows_the_branch_rule` asserts only `N6 needs the gate job required` for none and may stay as it is; you may add cases below round 1's two R-083 cases; change no other case.
- `bridge/cursor-bridge/MANIFEST.json` changes only by being regenerated with `python tools/make-manifest.py` (Done). Never edit it by hand.
- `bridge/cursor-bridge/VERSION` is outside Scope; it reads `2026.11.12a`. Restore it with `git restore bridge/cursor-bridge/VERSION` right after the manifest (Done), and edit it in no other way.
- `handoff/TASK-064-r2-report.md` is your report. Round 1's report, `handoff/TASK-064-r1-report.md`, is the supervisor's record now; do not edit it.

Do not modify anything else.

## Out of scope
- .env and anything under secrets/
- CI configuration
- docs/ and handoff/, except the files the Scope section names. Every record under docs/ is the supervisor's.
- `bridge/cursor-bridge/review-guard.py` (round 1's auto-merge line and closing word stand), `tests/test_review_guard.py`, `tests/test_release_s_records_gate.py`, `tests/fixtures/github/` (no new or changed recorded reply: the new cases build their replies in the test), and every other program and test file.
- `ci_class`: an unknown `status` of a check or run stays pending, as DESIGN says ("pending ... whatever its state is called"); not changed in this round.
- The audit's other advisories (the race of an entry added between two pages of a list over a hundred entries, the worst-case length of the page bound, the cause not printed by review-guard's `except Exception`): the supervisor records them.
- Any mutation script. The mutants file and the mutation run are the supervisor's, after your run.

## Context
**The design that binds this round** is round 1's: `docs/DESIGN.md`, "Change: the program release", the bullet group **The review guard, `review-guard.py`, and the rule's reader in `bridge_env.py`** (*The rule's reader*, *C7*), "Security and secret handling" (bullet **GitHub reads**) and "Failure modes"; the brief `handoff/TASK-064.md` (round 1), its Requirements R1-R8 and its Security context, all of which stand except where this brief rules otherwise.

**The new cases** build the replies they need in the test, from the recorded shapes, through the same stand-in `gh` (`STANDIN` in the file) by a fixture `crafted({route: body or (body, gh_exit)})`; the routes are written as for `github` (a path with `OWNER/REPO`, the query sorted with `per_page` and `page` aside, then `#<page>`, bare meaning page 1). A path with no route answers GitHub's 404 `Not Found` with exit 1. Read the section whole: it fixes what each ruling below means.

**The code as of round 1's tree** (`bridge/cursor-bridge/bridge_env.py`): `_page_path(path, page)` at 4078 adds `per_page=100&page=<n>`; `_read_list(path, key, cwd)` at 4096 reads a list that states `total_count`; `_GH_PER_PAGE = 100` and `_GH_MAX_PAGES = 100` at 3843-3844; `branch_rule` at 4006; `_rules_contexts` at 3972; `pull_refs` at 4060 (its number test at 4062-4065); `head_state` at 4131; `_int_rank` 4159; `_parse_time` 4165; `_last_by` 4175; `latest_of_each` 4219. `conformance-check.py`'s none row at line 933: `add("MISSING", "Required check on the default branch", "branch protection exists but requires no status check; N6 needs the gate job required")`.

**External service (the trait External services).** Unchanged from round 1: each call `GH_API_TIMEOUT` = 30 seconds, retry limit 0, GET only. Done means passing on the recorded replies and the replies the supervisor's cases build; no test of yours and no command you run calls the real GitHub, and you add no fixture file. GitHub documents `per_page` (at most 100) and `page` for the rules endpoint, which returns a bare JSON list.

**Security context.** As round 1: ASVS level 2; GitHub's reply is outside input (INVENTORY, Decisions, "The bridge's threat model as a whole"); a reply the reader cannot read or does not recognise is cannot read, never none and never a pass, and no exception from a reply escapes as a traceback.

**Development data.** As round 1: run the programs only from tests, on the recorded or built replies and scratch folders under `tmp_path`; never run them against this repository's folder or its GitHub repository; never install anything.

**Host.** Windows 11; Python as on the owner's interpreter. Do not run `gh` yourself.

## Diagrams
As round 1 (`docs/diagrams/D-002-components.md`, element `bridge_env`; `docs/diagrams/D-004-context-dfd.md`, `ext_github` to `p_review_guard`): the fix adds no import between bridge programs and no new call kind; every call stays a GET of a path. If the fix cannot be done within the diagrams, stop and report the conflict.

## Requirements
Use the labels G1-G8 in your report.

1. **G1. A rule the reader does not recognise is cannot read.** In the rules reply, a rule entry that is not an object, or whose `type` is missing or not a string, is cannot read (source `rules`). A rule whose `type` is `required_status_checks` is read only from a `parameters` object holding a list `required_status_checks`; a missing or null `parameters`, a `parameters` without that key, a null or non-list value, is cannot read (source `rules`), never skipped. A rule of any other string type is still skipped, whatever its `parameters` (GitHub's other rule types carry other parameters or none). Tests: the 8 ids of `test_r083_r2_a_rule_whose_shape_is_not_recognised_is_cannot_read_never_none`; round 1's `test_r083_a_success_that_names_no_required_check_is_none` (three ids) stays green.
2. **G2. The rules are read page by page.** The rules endpoint is asked with `per_page=100` and `page=<n>` (reuse `_page_path`), from page 1, until a page returns fewer than 100 rules; each page must be a JSON list (anything else is cannot read, source `rules`); a page that is not a success is cannot read (source `rules`), page 1 or a later one; the loop is bounded by `_GH_MAX_PAGES`, and a full page at the bound is cannot read (the list was not read whole). The rules of every page read are united as today. The classic protection is still read first and once, and a protection that cannot be read still answers cannot read without reading the rules (round 1's `test_r083_every_call_is_one_plain_get_with_no_retry` stays green). Tests: `test_r083_r2_the_rules_are_asked_a_hundred_a_page_and_read_to_a_short_page`, `test_r083_r2_a_full_page_of_rules_whose_next_page_cannot_be_read_is_cannot_read`.
3. **G3. A check that is not completed ranks after every completed one, in every order.** In `_last_by` for checks (the `started_at` ordering), the first part of every key is the not-completed rank (completed before not completed), whatever the start times. The id-only fallback is decided from the **completed** members of the group only: where one of the completed lacks a parseable `started_at`, the completed are ordered by `id` alone; otherwise by `started_at` then `id`. The not-completed members are ordered among themselves by `id` (then their position), never by comparing a missing time with a present one. Statuses keep their own order (G4). Tests: `test_r083_r2_a_pending_check_ranks_after_every_completed_one_whatever_their_start_times`; round 1's `test_r083_of_several_checks_of_one_name_in_a_latest_run_the_last_is_kept` and `test_r083_checks_no_run_made_are_kept_by_name_and_app_the_pending_after_the_completed` stay green.
4. **G4. An entry whose rank cannot be read makes the head cannot read.** `head_state` answers cannot read, with that list as `source` and a reason naming the field, where a workflow run lacks an integer `run_number`, `run_attempt` or `id` (a bool is not an integer), a check run lacks an integer `id`, or a commit status lacks an `updated_at` that `_parse_time` reads (G5). A check's `started_at` may be missing or unreadable (G3's id-only order covers it). `latest_of_each` keeps its interface and still raises nothing on any input (G5); it is not asked to answer cannot read. Tests: the 8 ids of `test_r083_r2_an_entry_without_the_fields_its_order_needs_is_cannot_read`, and `test_r083_r2_the_well_formed_entries_still_read_as_a_value`.
5. **G5. A time with no zone is not a time.** `_parse_time` returns None for a string `datetime.fromisoformat` cannot read and for a time with no zone (`tzinfo` None); a trailing `Z` is read as UTC as today, and a numeric offset is accepted. Nothing in `latest_of_each` compares a naive datetime with an aware one. Tests: the 2 ids of `test_r083_r2_a_time_with_no_zone_beside_one_with_a_zone_raises_nothing`.
6. **G6. A head and a pull request number are checked before any call.** `head_state` answers cannot read (source `checks`) and makes no call unless `sha` is 40 or 64 lowercase hexadecimal digits (`[0-9a-f]`, matched whole). `pull_refs` answers cannot read and makes no call unless `number` is a non-bool int of 1 or more, or a string of ASCII digits only (`str.isdigit` accepts other scripts' digits; it is not enough alone). Tests: the 9 ids of `test_r083_r2_a_head_that_is_not_a_commit_sha_is_cannot_read_and_asks_nothing`, `test_r083_r2_a_sha_of_sixty_four_digits_is_a_head`, the 6 ids of `test_r083_r2_a_pull_request_number_that_is_not_ascii_digits_is_cannot_read_and_asks_nothing`; round 1's head and pull cases stay green.
7. **G7. The none row says what is true for both causes.** The detail of the conformance check's none row becomes, with the branch's name: `no required status check on <branch>; N6 needs the gate job required` (the verdict stays MISSING). Tests: the 2 ids of `test_r083_r2_the_none_row_is_true_for_both_causes_of_none`.
8. **G8. `_gh_get`'s docstring** says what it returns: `(True, "", body)` or `(False, reason, body or None)`. No behaviour change.

You may add cases of your own to `tests/test_conformance_check.py` below round 1's R-083 cases; each names `R-083`. The supervisor's new cases cover G1 to G7; add one only where you find a gap, and say which.

## Acceptance criteria
- [ ] Every case in `tests/test_program_branch_rule.py` passes: round 1's 53 and the round-2 section's cases (the red ones named under Constraints, "Known failures", turn green; the others stay green).
- [ ] `python -m pytest -q tests/test_review_guard.py tests/test_release_s_records_gate.py tests/test_conformance_check.py` passes whole.
- [ ] `python -m pytest -q tests/test_task032_supervisor_guard.py tests/test_bug039.py tests/test_tests_windowless.py` passes whole.
- [ ] Each defect is fixed at the mechanism named in the Objective: `_rules_contexts` refuses the unrecognised shapes; `branch_rule` reads the rules to a short page; `_last_by` puts the not-completed rank first in every key and decides the id-only fallback from the completed; `head_state` refuses an entry whose rank fields cannot be read; `_parse_time` returns None for a naive time.
- [ ] `ci_class`, `repo_settings`, `_gh_get`'s call, `_read_list`, `review-guard.py` and every other line outside the Scope limits are byte-identical to round 1's tree.
- [ ] No exception from a GitHub reply escapes as a traceback, and none is swallowed into a value (ASVS L2).
- [ ] `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet` prints `RESULT: SOURCES MATCH`; `python tools/dump-cli.py --check` exits 0; `git status --short` does not list `bridge/cursor-bridge/VERSION` at the end.
- [ ] `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks` passes.
- [ ] R-083 is met for this reading: no stand-in, placeholder or "later" text in the program.

## Constraints
- Fix the causes; never suppress a test's symptom. No retry, no broad `try/except`, no widened tolerance, no `sleep`, no special case for a test's values (no test of the context `late check`, the rule ids, or the shas the cases use).
- Do not edit `tests/test_program_branch_rule.py` or anything under `tests/fixtures/github/`.
- **Known failures.** On round 1's tree, `python -m pytest -q -rfE tests/test_program_branch_rule.py` gives the result in `run/agent/TASK-064-r2-known.out`, quoted here: `31 failed, 62 passed in 38.09s`. The 31 red are every id of the round-2 section except these 9, which pass on round 1's tree and must still pass: `checks-not-a-list` and `rule-not-an-object` of the unrecognised-rule case, the empty sha of the head case, `test_r083_r2_a_sha_of_sixty_four_digits_is_a_head`, `test_r083_r2_the_well_formed_entries_still_read_as_a_value`, and the four pull numbers `17 3`, `-1`, the empty string and `True`; round 1's 53 pass. Every case in the file must pass after your change. If a case fails that this change did not cause, report it by its test id with its failure lines and fix none.
- **If you believe a defect's cause is different from the one named, stop, do not change code, and report why in your summary.** Likewise if an existing case requires the reader to answer none or a value for a shape G1 or G4 rules cannot read: stop and report it by its test id.
- Prefer reuse: `_gh_get` stays the one call helper, `_page_path` builds every paged path, `_answer` every result. Write the minimum that meets the acceptance criteria (the frozen `minimal-code.mdc` is in force). This never overrides a security requirement stated above.
- Numbers from a reply are read as JSON gives them and checked for their type, never sliced from text; times with the date parser.
- Do not add dependencies; standard-library imports only, in `bridge_env.py` only where needed.
- Do not read or write any file outside this workspace (the folder you were started in).
- No secret is needed or used.
- If the brief, the rules, or the tooling got in your way, append one dated line describing it to `docs/BUILDER_NOTES.md`; do the same for anything you learned about a defect or a pitfall.
- In any Markdown you write, never break a line inside a paragraph or a list item.
- **Windowless launches.** In tests a launch needs no `creationflags` argument (`tests/conftest.py` makes every launch windowless); where a test does write one, that line carries the literal text `CREATE_NO_WINDOW`. Any string in a test that holds Python launch code is written in concatenated parts. Every subprocess call in a test has a timeout.
- **Run every command synchronously, in the foreground, and wait for it to end.** Start nothing in the background and leave no process running.
- **Do NOT run the full `tests/` tree.** Run only the test files the Done section names, exactly as written there, with no `PYTHONPATH` or other environment change.
- Do not refactor code outside the functions the requirements name.
- No value in this increment is the owner's (rule 52).
- ASCII program text and ASCII output, as the file's conventions are.
- These git commands are not yours to run: `commit`, `push`, `switch`, `checkout`, `merge`, `rebase`, `reset`, `stash`, `branch -d`, `worktree`. You read with `git status`, `git diff` and `git log` only. The single exception is `git restore bridge/cursor-bridge/VERSION`, at Done step 3. Never run `git -h`, `git help` or `git <cmd> --help` (on Git for Windows they open a browser window).
- Every verification command is written in the Done section in full; run exactly those, from the Workspace root. The mutation check is the supervisor's, after your run: write no mutation script and leave none in the diff. You may mutate by hand in process to test a case; if you do, list each mutation and what caught it.

## Done
Your report is the file `handoff/TASK-064-r2-report.md`. Write it as you go. It names no computer path and no user name: write `<Workspace>` for the repository folder and `<tmp>` for a temporary folder, including in quoted command output.

When you finish, it holds:
- a list of every file you changed;
- a one-paragraph summary of what you did;
- for each of G1 to G8, one sentence on what changed, naming the functions and their lines as the file stands after your change;
- one sentence per defect of the Objective (1 to 5) stating how the change addresses its named cause;
- every command of the list below with its output;
- a section headed exactly `Assumed, not verified`, as the report's last section: one item per line, what you assumed · why · what would confirm it, or `Assumed, not verified: none`. Examples: whether GitHub's rules endpoint ever returns a page of exactly 100 rules as the last page; whether a real check run ever lacks `started_at`; whether a status's `updated_at` ever carries a numeric offset.

Run these from the Workspace root, in this order, after your last edit, each synchronously in the foreground, with no `PYTHONPATH` or other environment change:
1. `git status --short`
2. `python tools/make-manifest.py`
3. `git restore bridge/cursor-bridge/VERSION`
4. `git status --short` (`bridge/cursor-bridge/VERSION` must not be listed; if it is, report it)
5. `python bridge/cursor-bridge/bridge-check.py --root bridge --sources --quiet`
6. `python tools/dump-cli.py --check`
7. `python -m pytest -q -rfE tests/test_program_branch_rule.py`
8. `python -m pytest -q tests/test_review_guard.py tests/test_release_s_records_gate.py tests/test_conformance_check.py`
9. `python -m pytest -q tests/test_task032_supervisor_guard.py tests/test_bug039.py tests/test_tests_windowless.py`
10. `python bridge/cursor-bridge/windowless-check.py bridge/cursor-bridge .cursor/hooks`
11. `git rev-parse HEAD` and `git status --short`

Quoting rules:
- Every command you ran is quoted in the report with the lines it printed, verbatim, in a fenced block; each pytest summary line verbatim; never restate a count in prose.
- A command you did not run is written `not run`, never described as run.
- Write the report's results after step 11, naming the commit its counts belong to and whether the working tree then held uncommitted changes.

Your last message is the summary and the report file's path, and nothing follows it.
