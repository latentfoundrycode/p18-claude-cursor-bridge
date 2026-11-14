# SCOPE for TASK-058 (Review B, round 1)

TASK-058 is the bridge's own records checked by its tests (R-101), supervisor-authored, tests only, no builder run, no program changed. Branch task-058 from main 4f4a9b3 (PR #160's merge, TASK-057). This is the review guard's first round for TASK-058, below the code gate's ceiling: there is no Blocking class line.

Where the increment ends: one new test file and the records. Stage P1's close (the refactoring pass, the stage review, the demonstration, the reflection items) follows; it is not this diff's defect. The HARDENING entry also corrects one sentence of TASK-057's entry, on Review B's round-2 consider of PR #160.

Read the commit messages (git log, the full bodies) for the quoted lines.

## The plan entry, quoted (docs/BUILD_PLAN.md, TASK-058)
Scope: tests/test_program_own_records.py
Scope notes: tests/test_program_own_records.py: new
Satisfies: R-101
Done when: `tests/test_program_own_records.py` (names R-101) runs `inventory-check.py` over this repository's records and asserts exit 0, and asserts `header_agrees` for every headed record of the repository through `bridge_env`'s readers, the merged briefs the fallback refuses named as release B2 named them; each test is shown strong once by a scratch copy with one header key changed (red), the run quoted in the accept commit; R-101 reads built in the records commit.

## The supervisor's tests, each with the clause it enforces
- tests/test_program_own_records.py (new; names R-101): test_r101_inventory_check_passes_over_this_repository_s_records (inventory-check.py exits 0 with RESULT: OK); test_r101_every_headed_record_agrees_with_its_prose_through_its_own_reader (every record records_migrate.enumerate_records finds, read by its own check's reader, agrees; the only header-less records are release B2's three refused briefs).

## The mutants
run/supervisor/TASK-058-mutants.json (6 mutants, one header key per record kind in a scratch copy: the inventory, a brief, the status file, the register, the plan, the run parameters). counts: run=2 cached=4 killed=6 survived=0 not applied=0 error=0 expected survive=0

## Evidence
- Review A: round 1 APPROVE, four noted items recorded as HARDENING leads
- the new file, stripped, through the launcher: 2 passed in 0.54s
- the register's grammar tests, the status test, the release S rows and release B2's records tests after the records; completion-check.py --mode plan OK (78 built, 2 deferred, 24 planned); inventory-check.py OK.

## Expected bookkeeping and records in the diff
docs/REQUIREMENTS.md, docs/HARDENING.md, docs/PROJECT_STATUS.md (as at PR #161's merge), and run/review/ (these files).
