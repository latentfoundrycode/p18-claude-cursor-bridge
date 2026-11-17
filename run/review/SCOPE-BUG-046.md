# SCOPE: BUG-046, the guard's `gh api` merge refusal read as gh reads it (R-082)

Round cause: security

BUG-046 ran three builder rounds; this review reads the whole increment against origin/main (f3fa7b4): `run/review/REVIEW-BUG-046-r1.diff`.

Blocking class: safety mechanism (round 3, at the ceiling; its class line confirmed by Review A against round 2's code, the tree of 2c653de).

## Where the increment ends

The ruled behaviour, cumulative over the three briefs (handoff/BUG-046.md, F1 to F4; handoff/BUG-046-r2.md, G1 to G5; handoff/BUG-046-r3.md, K1 to K4), as it stands after round 3:

1. In `_check_word_list`'s `gh api` walk (bridge/cursor-bridge/permission-guard.py), each word of the command is decoded once: every `%XX` replaced by its character, repeated until the text no longer changes (`_percent_decoded`).
2. A merge mutation's name (`MERGE_MUTATIONS`, case kept) in a word or in its decoding: refused, "gh api with a merge mutation".
3. A body the guard cannot read, whatever the endpoint (F1): an `--input` option in any form, or a word beginning `@` or holding `=@`: refused. The old `graphql`-only condition is gone. A raw field (`-f`) whose value begins `@` is refused with it (an accepted over-refusal).
4. The merge endpoint, whatever the method, a read included (F2 as round 3 rebuilt it, K1): a word whose decoded, lower-cased text holds both `pulls` and `merge`: refused, "gh api on a pull request's merge endpoint". No cut at `?` or `#`, no dot-segment resolution, no pattern; the method loop and `WRITE_METHODS` deleted (rounds 1 and 2); `import posixpath` deleted (K3). An ordinary word holding both names is refused with it (an accepted over-refusal: HARDENING, BUG-046, ruling 1).
5. `tests/test_permission_guard.py`: the allowed case `gh api repos/o/r/pulls/12/merge` moved to the refused list (F3). The docstring's two passages on `gh api` (F4).
6. Every other refusal unchanged: the `&` refusal, the alias refusals, `gh pr merge`'s reading (TASK-083).

Out of scope (all three briefs; HARDENING, BUG-046, leads): REST `POST repos/<o>/<r>/merges` and `PATCH .../git/refs/heads/<b>`; the GraphQL `mergeBranch`, `updateRef`, `updateRefs`, `createCommitOnBranch`; `gh.cmd`, `gh.com` and gh named by path; the decoding's cost on nested `%25` (bounded by the hook's time limit); gh's placeholders filled from `GH_REPO` or the current branch (`{owner}`, `{repo}`, `:owner`, `:repo`, `{branch}`), which split the two names between the environment and the word (both round-3 reviewers; outside the threat model: ruling 2). Grade a finding there as a lead.

## The threat model

docs/INVENTORY.md, Decisions, the permission guard's threat model: inside it, a command that names a refused action (here, a merge outside the gate) in its own words under any quoting, chain, wrapper, prefix, assignment or launcher the guard reads; outside it, a deliberate reach that hides the action from that reading, as a command or value a program takes from an option, its configuration or the environment. A `gh api` call GitHub would route to a pull request's merge endpoint, or a GraphQL merge mutation, written in the command's own words and passing the guard, is a defeated safety mechanism.

## The tests

- `tests/test_bug046.py`: the supervisor's sections above the marker (the first reproduction, round 1's findings, round 2's findings, each with ordinary controls that must pass), and the builder's below it (rounds 1 to 3). Every case runs under Bash and PowerShell through the guard as a child process; no test calls GitHub or gh.
- `tests/test_permission_guard.py`: F3's moved case.
- The mutants file `run/supervisor/BUG-046-mutants.json` (12 single-line mutants, generator `run/supervisor/make_046_mutants.py`): 12 of 12 killed. The new tests once against the checkpoint 3d6e4eb: of 144 test ids, 96 fail on the old code and 48 pass there (32 ordinary controls, 16 refusals f3fa7b4 already made by its PUT-only pattern).

## Expected bookkeeping and record files in the diff

The briefs `handoff/BUG-046.md`, `-r2.md`, `-r3.md`; the builders' reports `handoff/BUG-046-report.md`, `-r2-report.md`, `-r3-report.md`; `docs/debug/BUG-046.md`; `docs/BUILDER_NOTES.md`; `docs/cli-reference.json` and `docs/CLI_REFERENCE.md` (generated from the guard's docstring); `bridge/cursor-bridge/MANIFEST.json`; the supervisor's records `docs/CHANGES.md`, `docs/HARDENING.md` (with TASK-083's gate end), `docs/INVENTORY.md` (reflected through), `docs/PROJECT_STATUS.md` (as it reads at this pull request's merge); `run/review/`.
