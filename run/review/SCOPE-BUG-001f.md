# SCOPE-BUG-001f — stage B1's review fixes (PR #21), round 6

Stage B1's stage review (2026-10-16) returned REJECT from Review A and Review B. This branch carries the fixes; once it merges, the stage review runs again on B1's whole change. Review this branch's diff, `run/review/REVIEW-BUG-001f.diff` (`git diff origin/main...HEAD`), whole.

## Round 6: what changed since round 5's reviewed head (78d0aad)
Round 5: Review A APPROVE (0/1/3), Review B REJECT (2/0/0), on the same two gaps: the job pin left the workflow's top level open (a workflow-level `defaults: run: shell: "true {0}"` skipped the Socket step with every test green; a workflow `env:` could set a registry, NODE_OPTIONS or BASH_ENV), and a reusable-workflow job with `secrets: inherit` passed the one-secret rule. `run/review/DELTA-BUG-001f.diff` (`git diff 78d0aad HEAD`, review files left out) shows exactly what changed; docs/DESIGN_CRITIQUE.md, "BUG-001 round 5 — disposition". The new commits:
- edcd387 — the supervisor's tests: `WORKFLOW_PIN`, the whole workflow verbatim (generated from it; compare it yourself), and `test_r002_workflow_is_the_pinned_one`; `FLOOR_JOB` is now its `security-floor` job; the one-secret rule refuses a job that passes secrets on; the deferral docstring notes its rule differs from completion-check's register convention. Mutation driver: 56 mutants, all killed by the named assertion (round 6 added: a workflow default shell, a workflow env preloading code, a reusable workflow inheriting the secrets). Stage tests 30; full suite 951 passed, 20 skipped.
- b1c9ada — records only: round 5's record (an increment that changes the workflow regenerates the pin in the same diff, TASK-006 the first); HARDENING's lead on the pattern checks.
- 61be677 — round 5's review files removed.
The builder's change (c8653a5) is unchanged since round 1. With the whole workflow pinned, any change to `.github/workflows/tests.yml` fails a test unless the same diff changes the pin; a bypass of a pattern check that the pin or the one-secret rule already stops is not a defect of this diff.

## Round 5 (for reference): what changed since round 4's reviewed head (7bd48c3)
Round 4: Review A APPROVE (0/3/5, nothing weaker than main); Review B REJECT (4/0/0: an early `exit 0` in the Semgrep step; `code=0` after OSV's status; a secret handed to a third-party action step; `npm --prefix /x install` beside the key). The reviewers disagreed on whether further bypasses of the structural test block; the supervisor settled it (docs/DESIGN_CRITIQUE.md, "BUG-001 round 4 — disposition"): **the floor job is now pinned verbatim instead of pattern-matched**. `run/review/DELTA-BUG-001e.diff` (`git diff 7bd48c3 HEAD`, review files left out) shows exactly what changed. The new commits:
- 534eda8 — the supervisor's tests: `test_r002_floor_job_is_the_pinned_one` (the `security floor` job equals the committed `FLOOR_JOB`, every step verbatim — generated from the workflow, compare it with `.github/workflows/tests.yml` yourself); `test_r002_one_step_holds_a_secret` (exactly one step in the whole workflow refers to a repository secret, the Socket scan); the pattern checks kept as a second line and tightened (chained commands split; npm options with a separate value, `cit`, `update`; case-insensitive expression names, `github['token']`; the job token apart from the step-env rule); a deferral names the owner and a date in either order. The mutation driver counts a kill only when the named assertion fired; 53 mutants, all killed. Full suite 950 passed, 20 skipped.
- 692eef5 — records only: round 4's record and the decision; a HARDENING lead on the pattern checks' remaining reach.
- 72ed2ac — round 4's review files removed.
The builder's change (c8653a5) is unchanged since round 1. Check the delta first, then the whole. A further bypass of a pattern check that the pin or the one-secret rule already stops is not a defect of this diff.

## Round 4 (for reference): what changed since round 3's reviewed head (babdb04)
Round 3: Review A APPROVE (0/3/4), Review B REJECT (2/0/0: `${{ format('{0}', secrets.X) }}` evaded the round-3 secret pattern, a weakening against main; `--ignore-scripts` then `--ignore-scripts=false` on a continued line passed). `run/review/DELTA-BUG-001d.diff` (`git diff babdb04 HEAD`, review files left out) shows exactly what changed; `docs/DESIGN_CRITIQUE.md` ("BUG-001 round 3 — disposition") maps each change to its finding. The new commits:
- 8e189ff — the supervisor's tests: the secret pattern reads each expression to its closing `}}` and keeps the bare `secrets.X` / `secrets['X']` form, plus `github.token`; commands are read with backslash continuations joined; `--ignore-scripts false` refused; an env setting npm's ignore-scripts config fails only on a value other than `true`; npm options before the command, `npm exec`, `npm it`; a Deferred decision cell may read `no — the owner, <date>`, and the docstring says the project narrows the template. Self-tests for each new form. Mutation driver: 47 mutants, all killed by an assertion. Full suite 947 passed, 20 skipped.
- c4307b5 — records only: round 3's critique record (and the correction of round 2's overstatement).
- 3fd3514 — round 3's review files removed.
The builder's change (c8653a5) is unchanged since round 1. Check the delta first, then the whole.

## Round 3 (for reference): what changed since round 2's reviewed head (824a91a)
Round 2: Review A APPROVE (0/2/5), Review B REJECT (1/0/0: `--ignore-scripts --ignore-scripts=false` passed). `run/review/DELTA-BUG-001c.diff` (`git diff 824a91a HEAD`, the review files left out) shows exactly what changed, and `docs/DESIGN_CRITIQUE.md` ("BUG-001 round 2 — disposition") says which finding each change answers. The new commits:
- 5b4da6e — the supervisor's tests: an npm install line's one mention of the setting must be the bare `--ignore-scripts`, no env at any level sets npm's ignore-scripts config, npm's install and clean-install aliases are all checked; the secret pattern matches any expression reading the secrets context (`toJSON(secrets)` included); a Deferred row follows the template (`no` in its decision cell, the owner named with a date in the row); `uvx`, `pnpm dlx`, `yarn dlx`, `bunx`; a self-test of the secret and install patterns. The mutation driver holds 41 mutants, all killed, and counts only an assertion as a kill (a crash is reported, not counted).
- 74c98df — records only: the round-2 critique record; HARDENING's npm lead notes its settle changes the pin test.
- f482c53 — round 2's review files removed.
The builder's change (c8653a5) is unchanged since round 1. Check the delta first, then the whole.

## Round 2 (for reference): what changed since round 1's reviewed head (47fb624)
Round 1: both reviewers APPROVE (Review A 0/1/6, Review B 0/4/1). The supervisor took the findings on the branch; `run/review/DELTA-BUG-001b.diff` (`git diff 47fb624 HEAD`, the review files left out) shows exactly what changed, and `docs/DESIGN_CRITIQUE.md` ("BUG-001 round 1 — disposition") says which finding each change answers. The new commits:
- 17d8850 — the supervisor's tests tightened: `--ignore-scripts` matched whole, a secret in any expression form (`secrets.X`, `secrets['X']`), the install pattern widened, the CLI held at its recorded 1.7.0, `pull_request` types must include opened/synchronize/reopened, a deferral needs the owner named with a date in its decision cell. The mutation driver now holds 35 mutants, all killed (six new).
- f913754 — records only: HARDENING's npm lead (scan-time exposure), the runner-image date marked unconfirmed, the status file names PR #21, the critique record.
- c413ef9 — round 1's review files removed.
The builder's change (c8653a5) is unchanged since round 1. Check the delta first, then the whole.

## What each commit is
- 49f92f9 — the supervisor's status edit at the resume of 2026-10-16 and the re-resolved roster (full profile). Records.
- d26d082 — tests written by the supervisor (rule N4 lets the supervisor write tests): `tests/test_release_b_bootstrap.py`, `tests/test_release_b_ci_floor.py`. Two of them (`test_r002_each_scanner_decides_its_step`, `test_r002_no_install_runs_beside_a_secret`) failed on the checkpoint's workflow and pass after the fix.
- af7384d — the checkpoint with the builder's brief `handoff/BUG-001.md`.
- c8653a5 — the builder's work (grok-4.7-medium), accepted: `.github/workflows/tests.yml` and its report `handoff/BUG-001-r1-report.md`.
- 63ece58 — a supervisor test-lane fix (ISS-006): `tests/test_roster_check.py` runs roster-check from the temporary roster's folder, so it no longer reads the Workspace's live run log.
- 66880e2 — records only: `docs/PROJECT_STATUS.md`, `docs/INVENTORY.md`, `docs/DESIGN_CRITIQUE.md`, `docs/HARDENING.md` (new), `docs/REQUIREMENTS.md`, `project.json`.

## The brief's Scope (handoff/BUG-001.md)
Files the builder may create or modify: `.github/workflows/tests.yml`, `docs/BUILDER_NOTES.md`, `handoff/BUG-001-r1-report.md`. In the workflow, only the `Socket` step of job `security-floor` and the one new step. Out of scope for the builder: tests/, requirements.lock, .semgrep.yml, osv-scanner.toml, socket.yml, docs/ and handoff/ beyond the named files, every other step, trigger, pin, permission and version.

**scope-check:** at inspection, before any later commit of the supervisor's, the builder's changes were exactly `.github/workflows/tests.yml` plus its report: `SCOPE CLEAN`. On the branch head it reports `SCOPE DRIFT` on the supervisor's own later commits (63ece58, 66880e2): its records list lacks `docs/DESIGN_CRITIQUE.md`, `docs/HARDENING.md` and `project.json`, and it does not recognise the supervisor's test commits (recorded for the maintainer as FB-009). Check this claim from the commits: the builder made no commit; c8653a5 holds its two files only.

## The tests the supervisor wrote, and the paragraph each enforces
- `test_release_b_ci_floor.py`: triggers (pull_request on open/update/reopen and push to main, no path filters; BUILD_PLAN stage B1 Demonstration); each scanner's exit decides its step (R-002); no install or fetch beside a secret in any expression form, npm with exactly one bare --ignore-scripts and no env switching it, the CLI at its recorded 1.7.0 (R-002, secure-coding.snapshot.md V14); the lock's exact admitted closure (R-002; supervisor.md step 5b); `; true` / `; exit 0` in the disabler guard; --no-banner in every job (V14); self-tests of the disabler, secret and install patterns. The whole workflow is pinned verbatim (`WORKFLOW_PIN`), and exactly one step may refer to a secret, the Socket scan; no job passes secrets on.
- `test_release_b_bootstrap.py`: the Deferred table read by rows (BUILD_PLAN TASK-001 Done when; a settled decision, an open question or a row without the owner and a date fails; a deferral whose decision cell begins `no` and whose row names the owner with a date passes — the project narrows the template's `<yes — the question · no>`); project.json's phase equals the status file's (R-001).
- Mutation driver (the supervisor's, not in the diff: run/supervisor/mutate_ci_floor.py): 56 mutants, each killed only when its named assertion fires — the stage review's and every round's findings, including the whole-workflow pin (an early `exit 0` in Semgrep, `code=0` after OSV, a workflow default shell, a workflow env) and the one-secret rule (an action handed a secret, a reusable workflow inheriting the secrets).

## Expected bookkeeping and records in the diff
`handoff/BUG-001.md`, `handoff/BUG-001-r1-report.md`, the records listed under 66880e2, `docs/ROSTER.resolved.json`, `run/review/` (these files).

## Settled — do not re-raise unless you find it wrong
- Three PR #16 run logs still show 5 characters of the Socket key (38241764324, 38244794839, 38309209568; a count over every run since 2026-10-12 found no other). Deleting them and replacing the key are the owner's, asked with a run sheet on 2026-10-16; the records say so.
- Socket reads requirements.lock: its supported-file list (api.socket.dev/v0/report/supported) has `requirements{.bazel,}.lock` for PyPI.
- The full-tree Semgrep audit ran on 2026-10-16 (1.176.1, CI's four rulesets, 189 rules, 139 files): one finding, the shim's `chmod 0o755` in bridge-install.py, accepted in INVENTORY Decisions.
- Owner decisions: Semgrep OSS engine with no token; SOCKET_ORG_SLUG = latent-foundry; merge authority supervisor; `security floor` required on main.

Design for later increments and stages is not this diff's defect. Grade findings Blocking, Should fix or Consider, with file and line.
