# ASSUMPTIONS: TASK-064, the builders' "Assumed, not verified" lists with the supervisor's dispositions

The accept commits' messages carry the same lists under `Assumptions:`. Extra places to look, never the review's scope.

## Round 1 (handoff/TASK-064-r1-report.md)

- `per_page` is 100 and the page loop stops at 100 pages. Disposition: accepted (GitHub's documented maximum `per_page`).
- A negative `total_count` is cannot read. Disposition: accepted.
- The none row's detail for an unprotected branch. Disposition: settled by round 2's G7.
- A page adding no entry is cannot read, duplicates matched by `id` or JSON text. Disposition: accepted.
- `repo_settings("{owner}/{repo}")` answers cannot read in a checkout with no remote. Disposition: accepted: the existing child-process premerge tests, which now call the real `gh`, ran green; GH_REPO and GH_HOST are unset locally and in CI (Review A of round 1 checked).
- The combined-status endpoint honours `page` and `per_page`. Disposition: accepted (documented).
- Times compared after a trailing `Z` becomes `+00:00`. Disposition: settled by round 2's G5 (a time with no zone is no time).
- A non-integer `run_number`, `run_attempt` or `id` ranks below every integer. Disposition: settled by round 2's G4 (cannot read).
- A non-zero `gh` exit carries the reply's body on standard output. Disposition: contract, confirmed by the supervisor's capture of 2026-11-16 (`protection-release-none.json`).
- `default_branch` required for a value. Disposition: accepted (fails closed).
- An `app_id` or `integration_id` of another type is cannot read. Disposition: accepted.

## Round 2 (handoff/TASK-064-r2-report.md)

- GitHub's rules endpoint returns a last page of exactly 100 rules followed by an empty page. Disposition: accepted (GitHub answers an empty list past the end; a full page at the bound is cannot read).
- A real check run lacking `started_at`. Disposition: accepted (G3 orders the completed by id alone).
- A status `updated_at` with a numeric offset. Disposition: accepted (`fromisoformat` reads it with its zone).

## Round 3 (handoff/TASK-064-r3-report.md)

- A list entry that is not an object keeps round 2's reason text. Disposition: accepted (cannot read either way).
- A bool is refused on every new integer field. Disposition: test (the supervisor's `a-bool` case of the round-3 section; mutant h07).

## Round 4 (handoff/TASK-064-r4-report.md)

- The builder listed none. The one fact the fix rests on, that GitHub's `total_count` equals the list's length on all three endpoints: accepted (every captured reply in `tests/fixtures/github/` holds it; Review A of round 4).
