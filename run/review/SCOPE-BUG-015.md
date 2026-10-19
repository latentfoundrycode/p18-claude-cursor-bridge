# SCOPE — BUG-015 (stage B1's review round 2, the fixes)

No builder run: the supervisor wrote the tests and the records (N4 permits tests; governance records are the supervisor's, §15 condition 3). There is no handoff/BUG-015.md; the commission is below.

## Scope (the commission)

Stage B1's review round 2 (snapshot STAGE-B1, the four squash commits 9e181e6, fba63bc, 6743b25 and 4d0f77b): Review B APPROVE with a should-fix and a consider; Review A REJECT, Blocking 1 / Should fix 4 / Consider 3. This change answers them:

- **Blocking (a test claiming more than it checks):** three bootstrap tests in `tests/test_release_b_bootstrap.py` checked a word anywhere in a file, where their docstrings claimed a record. Six record mutants passed them (the R-038 Decisions row deleted, the decision-6 row deleted, the baseline row rewritten as not met, `Installer verification:` deleted, `Merge authority:` blanked, the register's R-038 row deleted). The tests must read the register's ID column, the Decisions table's rows (first cell; Settled cell with a date and who decided; the baseline as met) and the five run parameters of supervisor.md's template (each on one line, with one of its values), each reader with a negative test.
- **Records:** INVENTORY's `--no-banner` row brought to the 2026-10-18 outcome (both reviewers); the status file's position lines; `project.json`'s `version` equal to the bridge's (`bridge/cursor-bridge/VERSION`); the status's list of B1's change naming all four commits; R-001's evidence naming BUG-001 and BUG-015; HARDENING's record of round 2, including the job-boundary should-fix recorded under standing rule 6 with its settle path.
- **Review A of this change** (APPROVE 0/2/4): its two should-fix items (the register reader's negative test; the settle path keeping the required check `security floor`) and considers 1, 3 and 4 (the driver judging each kill by the test it names; the failure message for a second Decisions row; the Decisions reader's decider, date and "met" checks under the negative test) are in the diff; consider 2 is kept (the baseline's Settled cell names the maintainer: rule 51's record of who decided).

## Review B, round 1, and how it was settled

REJECT on one item: `docs/PROJECT_STATUS.md` recorded the full suite as 1617 passed, 24 skipped, a run taken before the register's negative test was added. The suite was rerun on the committed tree (1618 passed, 24 skipped, as Review B found) and the line corrected in commit 334d18d. Review B found the rest of the change sound. This round reads the whole diff again.

## Out of scope

- Any program under `bridge/` or `.github/`. The job-boundary lead (the Socket key's job also runs Semgrep's open dependency ranges) is recorded, not fixed: rule 6 classes it with the earlier lead "an unpinned dependency is a risk of BUG-001's kind at scan time"; BUG-001's keyless `--ignore-scripts` install still holds. Its settle path is a later builder increment.
- Stage B1's review round 3, its demonstration and its reflection items, which follow this merge.
- Design for later increments is not this diff's defect.

## Tests the supervisor wrote, and what each enforces

All in `tests/test_release_b_bootstrap.py`; each enforces docs/BUILD_PLAN.md TASK-001 "Done when" and satisfies R-001:

- `test_r001_requirements_register_complete` + `_register_faults`, `test_r001_requirements_register_parse`: the register carries R-001..R-038 each once in its ID column.
- `test_r001_inventory_decisions_recorded` + `_decision_faults`, `test_r001_inventory_decisions_parse`: decision 6 and R-038 recorded as owner-answered with the date in INVENTORY Decisions, and the baseline-measurement precondition recorded as met.
- `test_r001_run_parameters_authoritative` + `_parameter_faults`, `test_r001_run_parameters_parse`: RUN_PARAMETERS.md holds the five parameters of supervisor.md's run-parameters template, each with an allowed value.

Mutation driver (supervisor-side, gitignored, not in the diff): `run/supervisor/bug015_mutants.py <scratch>` copies docs/, tests/ and project.json to a scratch folder, applies the six record mutants above one at a time, runs the test file there, restores and checks the bytes; each mutant must be killed by the test it names. Result: 6 of 6 killed, each by its named test.

## Expected bookkeeping and record files in the diff

`docs/HARDENING.md`, `docs/INVENTORY.md`, `docs/PROJECT_STATUS.md`, `docs/REQUIREMENTS.md`, `project.json`, and `run/review/` (these review files, removed before the merge).
