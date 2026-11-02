# SCOPE - BUG-041: the review guard, a snapshot deleted after it was taken (R-042) (pull request #127)

A fix of a confirmed defect in `bridge/cursor-bridge/review-guard.py`, the gate's own guard, built by the builder under one brief: `handoff/BUG-041.md`. The confirmed cause and its evidence are `docs/debug/BUG-041.md`. Your question: does this repair the named cause at the named mechanism, or does it make the symptom disappear?

The branch's commits, in order:
- 2b99397: the fix brief, the reproduction tests and the bug record (the checkpoint, the code before the fix).
- 3bc2934: the supervisor's three stronger assertions after Review A.
- 5855f52: the builder's run, the guard, the manifest and its report.
- the records commit: D-003 as built, the bug record's corrected sentence, the register, the inventory, HARDENING and the status file.
- this round's review files, committed last.

## Scope (the brief's, quoted)
bridge/cursor-bridge/review-guard.py; bridge/cursor-bridge/MANIFEST.json; docs/cli-reference.json; docs/CLI_REFERENCE.md; docs/BUILDER_NOTES.md; handoff/BUG-041-r1-report.md. The diff in review-guard.py is two functions, `load_snapshot` and `snapshot_rewritten`.

## Out of scope (the brief's, quoted)
.env and anything under secrets/; CI configuration; docs/ and handoff/, except the files the Scope section names; every test file under tests/ (for the builder: tests are the supervisor's); `docs/debug/BUG-041.md`, every file under `docs/diagrams/`, `docs/BUILD_PLAN.md`, `docs/REQUIREMENTS.md` and `docs/HARDENING.md`: the supervisor's records; `bridge/cursor-bridge/VERSION` (its content stays `2026.10.30d`) and `bridge/cursor-bridge/CHANGELOG.md`; `bridge/cursor-bridge/bridge_env.py` and every other program under `bridge/cursor-bridge/`; every part of `review-guard.py` other than `load_snapshot` and `snapshot_rewritten`, its module docstring included. These limits stay, recorded on the supervisor's side: the snapshot and its hash copy both deleted; a reviewer running the guard's own snapshot; the next snapshot on the same tree taking what was left as its baseline after the flag.

Later increments are later work, not this diff's defect: TASK-042 the weekly scan in this repository; TASK-044 the tests that name D-002, D-003 and D-004 and the index's Enforced-by cells, so `diagram-check.py --mode code`'s TESTS lines are expected here, and D-003's new `no_record` self-loop is in its list; TASK-045 the stamp. The guard as fixed applies only from release T's install: this session runs the installed guard, so BUG-039's flagged-round rule is applied by hand (P10, INVENTORY Decisions).

## The project's threat model, as docs/INVENTORY.md's Decisions record it for what the diff changes
A new Decisions row records it, from KP-032: what a reviewer does in passing in the checkout is inside it (a deletion, a rewrite, a planted hook, a moved ref); a deliberate reach past that is outside it and recorded (acts on the hash copies outside the checkout, a reviewer running the guard's own `snapshot`, `.git` relocated or a `commondir` planted, a snapshot's ACL denied). A second new row holds R-050's grading of a convergent finding by hand ahead of the install. Check both rulings: you may disagree with either, and the relocated `.git` lead in docs/HARDENING.md most of all, since a reviewer can reach it.

## The tests the supervisor wrote first
tests/test_bug041.py, 8 tests by node id, each docstring naming the paragraph it enforces (R-042, D-003, and the brief's Requirement): `test_bug041_a_deleted_snapshot_is_a_flag_and_voids_the_launch`, `test_bug041_negative_a_deleted_snapshot_restores_nothing_and_runs_no_git`, `test_bug041_premerge_refuses_a_deleted_snapshot_as_a_flag`, `test_bug041_negative_the_voided_launch_stays_voided_under_the_next_snapshot`, `test_bug041_negative_a_launch_before_the_round_is_not_voided`; invariants, which hold on the checkpoint too and are outside `new_tests`: `test_bug041_negative_a_snapshot_never_taken_stays_a_cannot_verify`, `test_bug041_negative_the_snapshot_and_its_copy_both_gone_stays_a_cannot_verify`, `test_bug041_negative_a_standing_snapshot_is_unchanged`.

The mutants file is run/supervisor/BUG-041-mutants.json (gitignored, not in the diff), written by run/supervisor/bug041_mutants.py, which asserts each mutant's `old` text occurs once in its file: 9 mutants, none alike, each a named weakening of one line of the fix.

## Bookkeeping and records expected in the diff
- docs/PROJECT_STATUS.md as at this pull request's merge (ISS-009), the line it replaces archived in docs/archive/STATUS_HISTORY.md.
- docs/INVENTORY.md: the ceiling's Features row gains BUG-041; two Decisions rows.
- docs/HARDENING.md: BUG-041's section, the findings not taken, and Review B's note on TASK-043, which that head could not carry.
- docs/REQUIREMENTS.md: R-042's Evidence names tests/test_bug041.py.
- docs/debug/BUG-041.md; docs/diagrams/D-003-review-round-states.md, drawn as built by the diagram specialist: labels name the deletion, one self-loop on `no_record`, the stated limits.
- handoff/BUG-041.md and handoff/BUG-041-r1-report.md (Assumed, not verified: none).
- run/review/: this round's files.

## Before this round
- New tests against the checkpoint 2b99397 (`mutation-run.py --checkpoint`, run/agent/BUG-041-checkpoint2.out, not in the diff): exit 0, the 5 listed tests failing, none passing, none not run, re-run after 3bc2934.
- Review A (fix mode): APPROVE, no blocking finding, the cause reproduced on temporary repositories. Security audit: PASS with findings, none blocking.
- Both named four items, each recorded and not taken here (docs/HARDENING.md, BUG-041): the snapshot restored between the load and the check gives a KeyError, failing closed; a hash copy that is not UTF-8 gives a traceback, exit 1, no mark; `snapshot_rewritten`'s docstring; the record's recovery sentence, which is corrected in this diff.
- Review A's three test findings are fixed in 3bc2934: without them mutant m04 would have survived.
- Slips of the supervisor's, each caught and fixed: that weak test; the record's sentence; a commit mixing the test fix with the bug record, which scope-check read as drift, undone unpushed and split.
- Mutation run on the code as it stands (run/agent/BUG-041-mutation.out, not in the diff): "counts: run=9 cached=0 killed=9 survived=0 not applied=0 error=0 expected survive=0", exit 0. Cuts: none. Estimate: about 550 processes.
- Full suite on the builder's tree before the test edits (run/agent/BUG-041-suite.out, not in the diff): 3447 passed, 42 skipped. CI runs the suite on the head.
- P7's suite, on 71e17f5 (run/agent/BUG-041-suite2.out, not in the diff): "3448 passed, 41 skipped in 1606.07s", exit 0; no skip names tests/test_bug041.py.
- diagram-check --mode design: OK. --mode code: the 13 expected TESTS lines, no IMPORT or SCHEMA failure. inventory-check: OK. plan-check: OK. windowless-check: 0 FAIL. No workflow text changed, so the traceability check has nothing new to read.

## The round
The guard's count is 0 before this snapshot and 1 once it opens, so this is Review B's first read. The launcher's count of builder rounds is 1. This round is below the ceiling; grade every finding by the five blocking classes all the same (behaviour against the brief or the register, security, data integrity, a defeated safety mechanism the increment relies on, a failing test), and say for each which class it is or that it is none.

Never run review-guard.py snapshot, verify or premerge in this Workspace itself: each on a temporary git repository, as tests/test_bug041.py does.
