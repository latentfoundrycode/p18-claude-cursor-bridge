# SCOPE - TASK-043: BUG-039, the review guard's flagged round (R-042, R-055) (pull request #126)

A fix of a confirmed defect in `bridge/cursor-bridge/review-guard.py`, the gate's own guard, built by the builder under three numbered briefs: `handoff/TASK-043.md`, `handoff/TASK-043-r2.md`, `handoff/TASK-043-r3.md`, read together, each standing except where a later one says otherwise. The confirmed causes and their evidence are `docs/debug/BUG-039.md`. Your question: does this repair the named cause at the named mechanism, or does it make the symptom disappear?

The branch's commits, in order:
- the supervisor's reproduction tests and the bug record; 6da8cc5 the fix brief and the rewritten snapshot's shapes test (the checkpoint, the code before any of the fix).
- 1ea1030: the builder's round 1.
- ec69dc9: round 2's brief, the tests round 1's reviews asked for, the record.
- ec84164: the builder's round 2.
- b61a494: round 3's brief and the tests round 2's reviews asked for.
- 05ef737: the supervisor's two test edits after round 3's reviews.
- 9d7c74a: the builder's round 3.
- 438acca: records, D-003 and D-004 as built, the deviations closed.
- this round's review files, committed last.

## Scope (the plan's, quoted)
bridge/cursor-bridge/review-guard.py; bridge/cursor-bridge/MANIFEST.json; tests/test_bug039.py; docs/BUILDER_NOTES.md; docs/debug/BUG-039.md; docs/diagrams/DEVIATIONS.md (the three D-003 rows and D-004's `p_review_guard` -> `ds_checkout` row removed); docs/diagrams/D-003-review-round-states.md (the labels that say the behaviour is a deviation redrawn as built, `diagram-specialist`'s as-built variant; D-004's file is unchanged, its `p_review_guard` -> `ds_checkout` edge carrying no deviation clause); docs/cli-reference.json; docs/CLI_REFERENCE.md; handoff/TASK-043-r<N>-report.md

Beyond the list, each with its reason:
- tests/test_release_t_pitfalls.py: R-054's test counted D-004's last DEVIATIONS row, which this increment removes; the count is re-taken to zero. The plan's line missed it (HARDENING, TASK-043).
- docs/diagrams/D-004-context-dfd.md, against the plan's "unchanged": the fix made the guard's empty hooks folder a store of its own, outside the repository, so it is drawn, as `ds_gh_empty` is (the security audit's A8, round 3). The edge the plan names carries no change.
- docs/diagrams/D-003-review-round-states.md beyond "labels": a self-loop on `flagged_gate_integrity` and the transitions the code has and the first draft lacked, drawn as built on the diagram specialist's reading of the code. TASK-044's per-transition tests grow with them.

## Out of scope (the briefs', quoted from handoff/TASK-043-r3.md)
.env and anything under secrets/; CI configuration; docs/ and handoff/, except the files the Scope section names; every test file under tests/ (for the builder: tests are the supervisor's); `bridge/cursor-bridge/VERSION` (its content stays `2026.10.30d`) and `bridge/cursor-bridge/CHANGELOG.md`; `bridge/cursor-bridge/bridge_env.py` and every other program under `bridge/cursor-bridge/`; every part of `review-guard.py` other than the places the briefs name. Stated limits, recorded on the supervisor's side: a record tampered with and later restored byte for byte; a `git` or `gh` program found in the current folder where the shell allows that search.

Later increments are later work, not this diff's defect: BUG-041, the guard's deleted snapshot (below); TASK-042 the weekly scan in this repository; TASK-044 the tests that name D-002, D-003 and D-004 and the index's Enforced-by cells, so `diagram-check.py --mode code`'s 13 TESTS lines are expected here; TASK-045 the stamp. `--strip` and the guard as fixed apply only from release T's install: this session runs the installed guard, which does not hold R-042's rule, so BUG-039's flagged-round rule is applied by hand (P10, INVENTORY Decisions).

## The project's threat model, as docs/INVENTORY.md's Decisions record it for what the diff changes
None is recorded for review-guard.py. Its boundaries are `docs/diagrams/D-004-context-dfd.md` and KP-032 (`bridge/cursor-bridge/Known-Pitfalls.md`): a guard against what a reviewer does in passing, not a sandbox. Its inputs under `.git/bridge/` and `run/review/` are untrusted. The inventory's new row records one ruling: a snapshot deleted during the run is BUG-041, not this increment.

## The tests the supervisor wrote first
tests/test_bug039.py, 50 tests by node id, each docstring naming the paragraph it enforces (R-042, D-003, D-004, and the brief's Requirement or the reviewer's finding). By site of docs/debug/BUG-039.md: site 1 the early returns void the launch, a snapshot rewritten to any shape stays a clean flag; site 2 the void regardless of exit, a voided launch admitted by no path, a tampered record, the tamper line; site 3 premerge through the helper; site 4 a re-snapshot keeps the flag; site 5 flags kept when a later git step fails; site 6 the hooks folder outside the repository; site 7 the exit line's bound. Invariants hold on the checkpoint too and are outside `new_tests`.

The mutants file is run/supervisor/TASK-043-mutants.json (gitignored, not in the diff), written by run/supervisor/task043_mutants.py, which asserts each mutant's `old` text occurs once in its file: 40 mutants, none alike, each a named weakening of one line of the fix, one running tests/test_task032_supervisor_guard.py beside the file.

## Bookkeeping and records expected in the diff
- docs/PROJECT_STATUS.md as at this pull request's merge (ISS-009), the line it replaces archived in docs/archive/STATUS_HISTORY.md.
- docs/INVENTORY.md: the ceiling's Features row gains BUG-039's rule; one Decisions row.
- docs/HARDENING.md: TASK-043's section, the findings not taken.
- docs/REQUIREMENTS.md: R-042's Evidence names tests/test_bug039.py.
- handoff/TASK-043-r1-report.md, -r2-report.md, -r3-report.md: the builder's reports. Rounds 1 and 2 read `Assumed, not verified: none`, which Review A found wrong (recorded).
- run/review/: this round's files.

## Before this round
- New tests against the checkpoint 6da8cc5 (`mutation-run.py --checkpoint`, run/agent/TASK-043-checkpoint4.out, not in the diff): exit 0, 41 listed tests failing, none passing, none not run.
- Round 1: Review A REJECT, audit FAIL. Fixed by round 2's brief. Round 2: Review A REJECT, audit FAIL. Fixed by round 3's brief.
- Round 3: Review A (fix mode) APPROVE, 0 Blocking, 0 Should fix, each cause reproduced with real holds. Security audit PASS with findings, none blocking. Its A1, a snapshot deleted during the run: unchanged code, no check flags it, so R-042's words stand; one `rm` on an ordinary layout, so it does not join the tail: BUG-041, before release T's stamp. Check that ruling: you may disagree with it.
- The other findings of round 3, convergent ones marked, are in docs/HARDENING.md's TASK-043 section. Both reviewers named one test gap, the tamper line unpinned, which 05ef737 closed.
- Slips of the supervisor's, each caught and fixed: the test edit first split an existing test (the secret scan's reviewer caught it); a mutant's list missed that test (the first mutation run erred on it).
- Mutation run on the code as it stands (run/agent/TASK-043-mutation2.out, not in the diff): "counts: run=1 cached=39 killed=40 survived=0 not applied=0 error=0 expected survive=0", exit 0. Cuts: none. Estimate: about 50,000 processes.
- Full suite on 9d7c74a's tree before the test edits: 3438 passed, 42 skipped. Full suite with this pull request's variables on 438acca, P7's `--key-file` form: see the line below. CI runs the suite on the head.
- diagram-check --mode design: OK. --mode code: the 13 expected TESTS lines, no IMPORT or SCHEMA failure. bridge-check --sources: 145 OK. trace-check: OK, 424 passages, 0 dropped. inventory-check: OK. plan-check: OK. windowless-check: 0 FAIL.

P7's suite, on 438acca (run/agent/TASK-043-suite4.out, not in the diff): "3440 passed, 41 skipped in 1615.58s", exit 0; no skip names tests/test_bug039.py.

## The round
The guard's count is 0 before this snapshot and 1 once it opens, so this is Review B's first read. The launcher's count of builder rounds is 3, the ceiling: a further builder round would be above it and would need a `Blocking class:` line. So grade every finding by the five blocking classes first (behaviour against the brief or the register, security, data integrity, a defeated safety mechanism the increment relies on, a failing test), and say for each which class it is or that it is none; a finding outside the five goes to docs/HARDENING.md and merges with the increment.

Never run review-guard.py snapshot, verify or premerge in this Workspace itself: each on a temporary git repository, as tests/test_bug039.py does.
