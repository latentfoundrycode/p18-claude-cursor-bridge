# SCOPE — BUG-016 (stage B1's review round 3, the fixes)

No builder run: the supervisor wrote the tests and the records (N4 permits tests; governance records are the supervisor's, §15 condition 3). There is no handoff/BUG-016.md; the commission is below.

## Scope (the commission)

Stage B1's review round 3 (snapshot STAGE-B1, 2dbf9d6; the five squash commits 9e181e6, fba63bc, 6743b25, 4d0f77b, 1b8c8da):

- **Blocking (convergent: Review B REJECT, Review A should-fix on the same item):** on main (1b8c8da, PR #44) `docs/PROJECT_STATUS.md` described its own pull request before the gate (BUG-015 "before its gate" on its branch; Last accepted and Remote sync at the previous main commit; Next the gate already run); REQUIREMENTS' R-001 evidence named BUG-015 without its commit. The class of round 1's blocking item and round 2's consider (ISS-009): the file is written inside each pull request before its gate, and a squash puts it on main unchanged. Required: the file written as it reads at this pull request's merge, and a mechanical guard.
- **Review A's considers:** the status file at its cap; the owner's run-parameter values not fixed in a test (rule 52) and INVENTORY's row repeating them; `node-version: "22"` floating in the key's job (record under rule 6, no workflow change); DESIGN_CRITIQUE's stale "R-039"; round 2's settle path leaving two jobs where one is required.
- **Review A of BUG-016** (APPROVE 0/1/5), taken in commit 3f56316: the guard only for pull requests into main (GITHUB_BASE_REF); a pull request into main whose number cannot be read fails rather than skips; In flight `none` alone and Increment beginning `none`; the status's run-parameter line a pointer only; the convention's costs recorded; round 2's settle path annotated. Not taken: a check of the free-prose Next line.

## Out of scope

- Any program under `bridge/`, and `.github/workflows/tests.yml` (the Node pin and the job split are recorded leads, a later builder increment).
- Stage B1's review round 4, its demonstration and reflection items, which follow this merge.
- Design for later increments is not this diff's defect.

## Tests the supervisor wrote, and what each enforces

In `tests/test_release_b_bootstrap.py`; each satisfies R-001:

- `test_r001_status_names_its_own_merge` with `_own_pull_request` and `_position_faults` — docs/BUILD_PLAN.md, stage B1's demonstration (a fresh session resumes from PROJECT_STATUS.md alone): in CI, the status file names the pull request being judged first on its Last accepted line, Increment begins `none`, In flight is `none`. It skips locally and for a pull request into another branch. `test_r001_status_position_parse` is its negative test.
- `test_r001_run_parameters_owner_values` — rule 52 (a value the owner chose is fixed in a test): the owner's four answers in docs/RUN_PARAMETERS.md.

Evidence that the guard runs in CI rather than skipping: this branch's first CI run (39262697130, on 57a36a6, which still carried main's old status file) failed `test_r001_status_names_its_own_merge` alone, on ubuntu-latest and windows-latest; the run on c8f2e40 passed.

Mutation driver (supervisor-side, gitignored, not in the diff): `run/supervisor/bug016_mutants.py <scratch>` — copies docs/, tests/, project.json to a scratch folder, sets GITHUB_REF=refs/pull/45/merge and GITHUB_BASE_REF=main, applies seven record mutants one at a time (four run parameters flipped; Last accepted without PR #45; In flight naming a branch before its gate; In flight naming a builder), restores and checks the bytes; each must be killed by the test it names. Result: 7 of 7.

## Expected bookkeeping and record files in the diff

`docs/PROJECT_STATUS.md` (rewritten as at this pull request's merge, its spent sections pruned), `docs/HARDENING.md`, `docs/REQUIREMENTS.md`, `docs/INVENTORY.md`, `docs/DESIGN_CRITIQUE.md`, and `run/review/` (these review files, removed before the merge).
