# SCOPE: TASK-064, one reader of GitHub's replies, the auto-merge line and the closing word (R-083, R-084), PR #174

Round cause: security

TASK-064 ran two builder rounds; this review reads the whole increment against origin/main (cc560c1): `run/review/REVIEW-TASK-064-r1.diff`.

## Where the increment ends

The ruled behaviour, cumulative over the two briefs (handoff/TASK-064.md, round 1, requirements R1 to R14; handoff/TASK-064-r2.md, round 2, G1 to G8):

1. `bridge_env.py` holds the one reader of GitHub's replies. Every call is `GH_COMMAND + ["api", <path>]` (default `["gh"]`), a plain GET (no method other than GET, no field, no input, no `--paginate`), with `GH_API_TIMEOUT` = 30 seconds, no retry, windowless, standard input closed; both read at call time. Nothing raises to the caller.
2. Every reading answers `value`, `none` or `cannot read` (with a reason and the source that failed). A reply the reader cannot read or does not recognise is cannot read: never none, never a pass, never hidden by the other source.
3. `branch_rule(repo, branch)`: the branch percent-encoded in both paths; the union of the classic protection's checks and contexts and every `required_status_checks` rule's checks, each with its app id. None only for the classic endpoint's `Branch not protected` 404 (matched exactly) beside a readable rules reply, or for successes that name no required check. A rule entry that is not an object, has no string type, or (of type `required_status_checks`) lacks a `parameters` object holding a list of checks is cannot read; other string types are skipped. The rules are asked a hundred a page until a short page, at most `_GH_MAX_PAGES` pages, a full page at the bound or a failed later page cannot read.
4. `repo_settings(repo)`: a boolean `allow_auto_merge` and a non-empty `default_branch`, or cannot read. `pull_refs(repo, number)`: the base ref and the head sha; the number a non-bool int of 1 or more or a string of ASCII digits, checked before any call.
5. `head_state(repo, sha)`: the sha 40 or 64 lowercase hex digits, checked before any call; check runs (`filter=all`), statuses and workflow runs each read page by page to the `total_count` its reply states; a list not read whole, a run without integer `run_number`, `run_attempt` or `id`, a check without an integer `id`, or a status without a zoned `updated_at` makes the head cannot read.
6. `latest_of_each(state)`: a run by workflow and event, the latest by run number then attempt; a check a run made only where its run is a latest run; checks by name (and app where no run made them), a not-completed check after every completed one in every order, the completed by start time then id, by id alone where one of the completed has no readable start time, the not-completed among themselves by id; a status by context, the latest by `updated_at`. A time with no zone is no time. It raises nothing.
7. `ci_class(item, kind)`: passed, pending, skipped or failed by closed lists; an unknown conclusion or state is failed; a check or run not completed is pending (DESIGN: "pending ... whatever its state is called").
8. `conformance-check.py`: the default branch's row through `branch_rule`: value OK with up to four contexts; none MISSING `no required status check on <branch>; N6 needs the gate job required`; cannot read a NOTE beginning `cannot read the branch rule (` naming `review-guard.py ready answers CANNOT CHECK`; a loaded bridge_env with no `branch_rule` a NOTE.
9. `review-guard.py`: `premerge` and `premerge-records` print, on their success path after the record and the merge line, `auto-merge is on for this repository`, `auto-merge is off for this repository` or `auto-merge setting not read`, the verdict and exit unchanged and no `--auto`; `snapshot_rewritten` returns `deleted` for a deleted snapshot and `rewritten` for a rewritten one, and the closing GATE-INTEGRITY line of `verify` and `premerge` says which; no branch or exit changes.

Out of scope (both briefs): `review-guard.py ready`, its record and any caller of `pull_refs`, `head_state`, `latest_of_each` or `ci_class` outside `bridge_env.py` (TASK-083); `bridge-run.py`, `permission-guard.py` and every other program; the docstrings' exit lists (J14); CI configuration.

## The threat model

GitHub's reply is outside input (docs/INVENTORY.md, Decisions, the row "The bridge's threat model as a whole", and the new row "GitHub's replies are outside input to the rule's reader" this pull request adds). The reader decides a merge gate from TASK-083 on, so a reply read wrong is a defeated safety mechanism. Outside the model: GitHub's own correctness for well-formed replies; the owner's `gh` login. Round 2's security audit advisories are recorded in docs/HARDENING.md as leads (a superseded check whose `check_suite.id` is not an integer kept beside the newer one, which TASK-083's `ready` must meet by counting a context passed only where every kept entry of it passed, R-083's own text; a rule type GitHub does not have skipped; equal-time statuses ordered by an unchecked id).

No round was above the ceiling; there is no class line.

## The tests

- `tests/test_program_branch_rule.py` is the supervisor's: round 1's 53 cases on GitHub's replies recorded from this repository (`tests/fixtures/github/`, 23 files, each naming whether it was captured or built and from what), then the section "round 2 (Review A and the security audit of round 1)" on replies built in the case through the same stand-in `gh`, then the section of cases the mutation run asked for. Every case runs through a stand-in `gh` set in `bridge_env.GH_COMMAND`; no test calls GitHub.
- The builder's cases: `tests/test_conformance_check.py` (the row's value, none and cannot-read cases; a bridge_env without `branch_rule`), `tests/test_review_guard.py` and `tests/test_release_s_records_gate.py` (no auto-merge line on a premerge that is not a success).
- The mutants file `run/supervisor/TASK-064-mutants.json` (43 single-line mutants over the reader, the conformance row and the guard's lines, each listing every test it fails; generator `run/supervisor/make_064_mutants.py`): 43 of 43 killed. The new tests against 203023c (main's code with the acceptance tests): 103 fail on the old code, 2 pass there (the fixtures' own check; verify's word for a rewritten snapshot, kept), 2 not run (two non-ASCII ids the engine could not select, both red on round 1's tree).

## Expected bookkeeping and record files in the diff

`docs/BUILDER_NOTES.md`; the builders' reports `handoff/TASK-064-r1-report.md`, `-r2-report.md`; the briefs `handoff/TASK-064.md`, `-r2.md`; the supervisor's records `docs/CHANGES.md` (TASK-064's entry and BUG-045's Review B entry carried from PR #173, which premerge kept from that pull request's records), `docs/HARDENING.md`, `docs/INVENTORY.md`, `docs/REQUIREMENTS.md` (R-084 built; R-083 stays planned until TASK-083), `docs/PROJECT_STATUS.md` (as it reads at this pull request's merge); `bridge/cursor-bridge/MANIFEST.json` (the three programs' hashes); `tests/fixtures/github/`; `run/review/`.
