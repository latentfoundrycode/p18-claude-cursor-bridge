# SCOPE-BUG-001b — stage B1's review fixes (PR #21), round 2

Stage B1's stage review (2026-10-16) returned REJECT from Review A and Review B. This branch carries the fixes; once it merges, the stage review runs again on B1's whole change. Review this branch's diff, `run/review/REVIEW-BUG-001b.diff` (`git diff origin/main...HEAD`), whole.

## Round 2: what changed since round 1's reviewed head (47fb624)
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
- `test_release_b_ci_floor.py`: triggers (pull_request and push to main, no path filters; BUILD_PLAN stage B1 Demonstration); each scanner's exit decides its step (R-002); no install beside a secret and npm with --ignore-scripts (R-002, secure-coding.snapshot.md V14); the lock's exact admitted closure (R-002; supervisor.md step 5b); `; true` / `; exit 0` in the disabler guard; --no-banner in every job (V14).
- `test_release_b_bootstrap.py`: the Deferred table read by rows (BUILD_PLAN TASK-001 Done when; a settled decision or an undated deferral fails, TASK-027's dated deferral passes); project.json's phase equals the status file's (R-001).
- Mutation driver (the supervisor's, not in the diff: run/supervisor/mutate_ci_floor.py): 29 mutants, all killed — including each of the stage review's findings (a removed push trigger, a path filter, OSV ending in `exit 0`, `; true` after a scanner, a scanner merely echoed, an extra lock entry, a settled or undated Deferred row, the install back beside the key).

## Expected bookkeeping and records in the diff
`handoff/BUG-001.md`, `handoff/BUG-001-r1-report.md`, the records listed under 66880e2, `docs/ROSTER.resolved.json`, `run/review/` (these files).

## Settled — do not re-raise unless you find it wrong
- Three PR #16 run logs still show 5 characters of the Socket key (38241764324, 38244794839, 38309209568; a count over every run since 2026-10-12 found no other). Deleting them and replacing the key are the owner's, asked with a run sheet on 2026-10-16; the records say so.
- Socket reads requirements.lock: its supported-file list (api.socket.dev/v0/report/supported) has `requirements{.bazel,}.lock` for PyPI.
- The full-tree Semgrep audit ran on 2026-10-16 (1.176.1, CI's four rulesets, 189 rules, 139 files): one finding, the shim's `chmod 0o755` in bridge-install.py, accepted in INVENTORY Decisions.
- Owner decisions: Semgrep OSS engine with no token; SOCKET_ORG_SLUG = latent-foundry; merge authority supervisor; `security floor` required on main.

Design for later increments and stages is not this diff's defect. Grade findings Blocking, Should fix or Consider, with file and line.
