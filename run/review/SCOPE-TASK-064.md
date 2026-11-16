# SCOPE: TASK-064, one reader of GitHub's replies, the auto-merge line and the closing word (R-083, R-084), PR #174

Round cause: defect

TASK-064 ran four builder rounds; this review reads the whole increment against origin/main (cc560c1): `run/review/REVIEW-TASK-064-r4.diff`. This is the gate's fourth Review B round, a re-review after CI: the third round approved round 4's tree (snapshot TASK-064-r3, head 5ae2cdb), the review files were removed (c03e165), and CI failed at c03e165 on one older case whose expected docstring phrase R-084 had replaced. The supervisor changed that one assertion; no program changed and no builder ran. The only change since c03e165 outside run/review/ is that line of `tests/test_bug042.py`.

## The class line of the round above the ceiling

The re-review is the supervisor's fix, with no builder run; its line is confirmed against the head the previous round's CI ran on, c03e165:

Blocking class: failing test - CI red on PR #174 at c03e165 (bridge programs, ubuntu-latest: 1 failed, 6465 passed, 66 skipped; windows-latest: 1 failed, 6493 passed, 38 skipped): tests/test_bug042.py::test_bug042_the_guard_s_docstrings_name_the_deleted_snapshot asserts snapshot_rewritten's docstring holds "or the file is gone while the copy stands", the phrase round 1 replaced with "'deleted' when the snapshot file is gone while the copy stands"

Confirm or deny it against c03e165 (`git show c03e165:tests/test_bug042.py` and `git show c03e165:bridge/cursor-bridge/review-guard.py`, run in a temporary folder), never against the fixed code: the case fails there and passes after the one-line change, and what it guards (the function's docstring names the deleted snapshot) still holds.

## Where the increment ends

The ruled behaviour, cumulative over the four briefs (handoff/TASK-064.md, round 1, R1 to R14; handoff/TASK-064-r2.md, round 2, G1 to G8; handoff/TASK-064-r3.md, round 3, H1; handoff/TASK-064-r4.md, round 4, I1):

1. `bridge_env.py` holds the one reader of GitHub's replies. Every call is `GH_COMMAND + ["api", <path>]` (default `["gh"]`), a plain GET (no method other than GET, no field, no input, no `--paginate`), with `GH_API_TIMEOUT` = 30 seconds, no retry, windowless, standard input closed; both read at call time. Nothing raises to the caller.
2. Every reading answers `value`, `none` or `cannot read` (with a reason and the source that failed). A reply the reader cannot read or does not recognise is cannot read: never none, never a pass, never hidden by the other source.
3. `branch_rule(repo, branch)`: the branch percent-encoded in both paths; the union of the classic protection's checks and contexts and every `required_status_checks` rule's checks, each with its app id. None only for the classic endpoint's `Branch not protected` 404 (matched exactly) beside a readable rules reply, or for successes that name no required check. A rule entry that is not an object, has no string type, or (of type `required_status_checks`) lacks a `parameters` object holding a list of checks is cannot read; other string types are skipped. The rules are asked a hundred a page until a short page, at most `_GH_MAX_PAGES` pages, a full page at the bound or a failed later page cannot read.
4. `repo_settings(repo)`: a boolean `allow_auto_merge` and a non-empty `default_branch`, or cannot read. `pull_refs(repo, number)`: the base ref and the head sha; the number a non-bool int of 1 or more or a string of ASCII digits, checked before any call.
5. `head_state(repo, sha)`: the sha 40 or 64 lowercase hex digits, checked before any call; check runs (`filter=all`), statuses and workflow runs each read page by page; (round 4, I1) a list read in pages is one view of GitHub: every page states the first page's `total_count` and the reading ends with exactly that many distinct entries, else `the list changed while it was read` and the head is cannot read with that list as source; a list not read whole is cannot read; (round 3, H1) every field `latest_of_each` groups or ranks by is checked for its type (a run's integer `id`, `run_number`, `run_attempt`, `workflow_id`, `check_suite_id` and non-empty `event`; a check's integer `id`, non-empty `name`, a `check_suite` and an `app` object each with an integer `id`; a status's non-empty `context`, integer `id` and zoned `updated_at`; a bool is never an integer), else cannot read, the list as source, the reason naming the field.
6. `latest_of_each(state)`: a run by workflow and event, the latest by run number then attempt; a check a run made only where its run is a latest run; checks by name (and app where no run made them), a not-completed check after every completed one in every order, the completed by start time then id, by id alone where one of the completed has no readable start time, the not-completed among themselves by id; a status by context, the latest by `updated_at`. A time with no zone is no time. It raises nothing.
7. `ci_class(item, kind)`: passed, pending, skipped or failed by closed lists; an unknown conclusion or state is failed; a check or run not completed is pending.
8. `conformance-check.py`: the default branch's row through `branch_rule`: value OK with up to four contexts; none MISSING `no required status check on <branch>; N6 needs the gate job required`; cannot read a NOTE beginning `cannot read the branch rule (` naming `review-guard.py ready answers CANNOT CHECK`; a loaded bridge_env with no `branch_rule` a NOTE.
9. `review-guard.py`: `premerge` and `premerge-records` print, on their success path after the record and the merge line, `auto-merge is on for this repository`, `auto-merge is off for this repository` or `auto-merge setting not read`, the verdict and exit unchanged and no `--auto`; `snapshot_rewritten` returns `deleted` for a deleted snapshot and `rewritten` for a rewritten one, its docstring saying which, and the closing GATE-INTEGRITY line of `verify` and `premerge` says which; no branch or exit changes.

Out of scope (every brief): `review-guard.py ready`, its record and any caller of `pull_refs`, `head_state`, `latest_of_each` or `ci_class` outside `bridge_env.py` (TASK-083); `bridge-run.py`, `permission-guard.py` and every other program; the docstrings' exit lists (J14); CI configuration. Out of I1: reading a list twice, retrying or waiting; the rules endpoint's paging (its replies state no count).

## The threat model

GitHub's reply is outside input (docs/INVENTORY.md, Decisions, the row "The bridge's threat model as a whole", and the row "GitHub's replies are outside input to the rule's reader" this pull request adds). The reader decides a merge gate from TASK-083 on, so a reply read wrong is a defeated safety mechanism. Outside the model: GitHub's own correctness for well-formed replies; the owner's `gh` login. The leads recorded in docs/HARDENING.md under TASK-064 are outside this round's blocking scope unless a reviewer shows one reaching a false result through a reply in ordinary use.

## The tests

- `tests/test_program_branch_rule.py` is the supervisor's acceptance file (156 cases: round 1's 53 on GitHub's recorded replies, `tests/fixtures/github/`; the sections of rounds 2, 3 and 4 and the mutation run's cases), every case through a stand-in `gh` in `bridge_env.GH_COMMAND`; no test calls GitHub.
- The builder's cases: `tests/test_conformance_check.py`, `tests/test_review_guard.py` and `tests/test_release_s_records_gate.py`.
- `tests/test_bug042.py` (BUG-042's, on main before this increment): its docstring case now asks for R-084's phrase.
- The mutants file `run/supervisor/TASK-064-mutants.json` (54 single-line mutants): 54 of 54 killed on round 4's tree. The new tests against 203023c: of 162 ids, 158 fail on the old code, 2 pass there (kept), 2 not run (two non-ASCII ids).

## Expected bookkeeping and record files in the diff

`docs/BUILDER_NOTES.md`; the builders' reports `handoff/TASK-064-r1-report.md` to `-r4-report.md`; the briefs `handoff/TASK-064.md`, `-r2.md`, `-r3.md`, `-r4.md`; the supervisor's records `docs/CHANGES.md` (TASK-064's entry and BUG-045's Review B entry carried from PR #173), `docs/HARDENING.md`, `docs/INVENTORY.md`, `docs/REQUIREMENTS.md` (R-084 built; R-083 stays planned until TASK-083), `docs/PROJECT_STATUS.md`; `bridge/cursor-bridge/MANIFEST.json`; `tests/fixtures/github/`; `run/review/`. The records do not yet name this CI failure; it goes to the next records pull request, since the records cannot change after the reviews.
