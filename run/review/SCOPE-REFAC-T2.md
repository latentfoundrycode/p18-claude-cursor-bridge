# SCOPE - REFAC-T2 (stage T2's refactoring pass)

## What the branch is
Stage T2's refactoring pass (bridge/cursor-bridge/workflow/phases/delegation-loop/refactoring-pass.md): removing duplication with the same functionality, one gate pass for the whole branch, one squash. There is no `docs/CHANGES.md` in this project and no behaviour entry: a refactoring changes no behaviour. The question for the reviewers: **is this behaviour-preserving?**

The base is origin/main 5e46e2d (TASK-044's merge, PR #129); the stage's change is 112bfd3..5e46e2d (TASK-041, TASK-043, BUG-041, TASK-042, TASK-044). The candidates came from jscpd 5.4.1 over bridge and tests (148 clones, 1.65%), filtered to review-guard.py and the six test files the stage added, and refactor-scout's ranking against the 400-line budget, kept in run/supervisor/refactor-T2-candidates.md (gitignored) and recorded in docs/HARDENING.md, "Stage T2's refactoring pass". One brief, handoff/REFAC-004.md, in the production lane; the rest in the tests lane.

## Brief REFAC-004: Scope and Out of scope
Quoted from handoff/REFAC-004.md, whose whole text is in the diff:

> ## Scope
> Files and directories you may create or modify:
> - bridge/cursor-bridge/review-guard.py
> - docs/BUILDER_NOTES.md
> - handoff/REFAC-004-r1-report.md
>
> Do not modify anything else.

Its `## Out of scope` section names .env and secrets/; CI, pre-commit and `tools/`; other docs/ and handoff/ files, docs/diagrams/ included; every file under `tests/`; `bridge/cursor-bridge/MANIFEST.json`, which the supervisor regenerates after the run, and `VERSION`; the change logs; the command reference; `no_hooks_dir` and the `common` argument around it, a separate lead; every other line of review-guard.py, its look-alikes by line; and every other file under `bridge/`. Read it in the diff for its exact words.

## The commits
1. `supervisor: REFAC-T2's tests lane` (9af848a), the supervisor's test-infrastructure lane (step 3b). `flagged_round(tmp_path, **launch)` takes the launch's arguments, five sites in tests/test_bug039.py: two of them asserted only the exit code and now also read GATE-INTEGRITY, which those runs already print, so they are stricter and nothing is weakened. One `watch_git(monkeypatch)` in tests/test_bug039.py, tests/test_bug041.py importing it and `start_of`. tests/test_dependency_scan.py imports `frozen_block` from tests/test_release_t_floor.py. Evidence: the collected set identical, 3,541, before and after; `refactor-check.py --lane tests` "PURE", 104 changed lines at that commit; the five files that read these helpers, 119 passed.
2. `supervisor: REFAC-004's brief, and the void path's branches pinned before it (R-042)` (6a4170c). The brief, and four characterization tests in tests/test_bug039.py, `void_path_call` and `test_bug039_void_path_*`, for three branches of `record_flagged_launch` no test named: a launch before the snapshot reads no record; no entry with a snapshot still writes; no entry without one writes nothing; an entry with no time and no snapshot writes nothing. They passed on the guard as it stood, before the builder's edit. `void_path_call` stubs `guard.load_rounds` and `guard.write_rounds`.
3. `REFAC-004: review-guard.py reads the rounds record once when it records a flagged launch, and four dead lines go` (142f2a6), the builder (composer-2.5, run 2026-11-03T02:53:39Z, exit 0). `record_flagged_launch`: the snapshot comparison stays first and before any read; one isfile check, one load_rounds, one lookup; a write still follows no entry where a snapshot was given and does not where none was. The dead lines: a local `import tempfile`; `rounds_data` and `rpath` set to None; a second `id_part, rnd` unpack. MANIFEST.json regenerated. Evidence: scope-check "SCOPE CLEAN"; `refactor-check.py 6a4170c` "PURE", 29 changed lines at that commit; the builder's assumptions list reads none.
4. `supervisor: the void path's tests, Review A's two considers on REFAC-004 (R-042)` (c44891a): the entry's time empty, None or missing, parametrized; of two entries for one round the first decides and alone takes the void, which the guard's own records never hold and the old and new function agree on. Tests only.
5. `REFAC-T2: the pass's records` (cd66977): docs/HARDENING.md (the pass's section), docs/INVENTORY.md (the jscpd row), docs/PROJECT_STATUS.md written as at this pull request's merge (the project's rule, ISS-009) with the Last accepted line it replaces moved to docs/archive/STATUS_HISTORY.md, project.json's stage.

## The purity bases, and a deviation from the pass's item 3
`refactor-check.py main` reads this branch as IMPURE, and at HEAD so does `refactor-check.py 6a4170c`, by commit 4. That is expected and is the record of a deviation: item 3 asks characterization tests to go through a gate on `main` before the branch is cut, and these went on the branch, so that this one gate pass reads them with the change they protect. The purity readings that hold are each at its own commit: the tests lane `refactor-check.py origin/main --lane tests` PURE at 9af848a, 104 lines; the production lane `refactor-check.py 6a4170c` PURE at 142f2a6, 29 lines. The void-path tests of commit 2 passed on the old guard. Review A judged the deviation acceptable and none of the five blocking classes. Named in docs/HARDENING.md.

## Evidence already taken
- Review A, refactoring mode: APPROVE, no blocking finding. It ran the old and the new `record_flagged_launch` on 13,340 cases in a scratch folder, with no difference in return, exception type, what was written, or the record's and hash copy's final bytes.
- security-auditor, since the diff touches the guard's void path: PASS, 0 blocking, 0 advisory. It ran the real `cmd_verify` from 6a4170c and from c44891a end to end on 25 scenarios in temporary repositories with no difference in return, exception type, printed lines or record. Its stated limits: a writer was injected at the `load_rounds` boundary, not raced as a second process, and no later-round name ran end to end. One thing the second read gave is gone, by the brief's design: the old code's chance of noticing a process still writing during `verify`, between the two reads, in a gap with no git command and no spawn, after GATE-INTEGRITY has printed. docs/HARDENING.md records it. Check whether you read that as a behaviour change.
- Mutation: because the production lane moved the guard, seven mutants were re-anchored (TASK-043's m05, m10, m11, m12, m19; TASK-044's m39, m40), m09's list extended, and every mutants file the change could reach run again, cut none: REFAC-T2 5 of 5 killed (run/supervisor/REFAC-T2-mutants.json, r1 to r5, which model the new form: the comparison after the read; no entry with a snapshot writing nothing; no entry without one writing; an empty time voiding; the second entry instead of the first), TASK-043 40 of 40, BUG-041 9 of 9, TASK-044 47 of 47, TASK-042 35 of 35. Exit 0 each. Those runs were on c44891a, before the records.
- The full suite on cd66977, through the launcher with the pull request's variables (run 2026-11-03T05:05:33Z): "3507 passed, 41 skipped in 1666.59s", exit 0. That is 3,548 tests: the 3,541 of TASK-044's merge and the seven new void-path test ids.

## Out of scope
- The scout's T2 (a shared `launched_round` over 21 sites) was dropped. Optimization: none. Beyond budget: none.
- Leads recorded, not taken: `no_hooks_dir(common)` ignoring its argument (28 sites); stage T1's `rule` and `numbered_rule`; stage B6's and B5's leads.
- Stage T2's review, TASK-045, the demonstration and project end are later work, not this diff's defect.

## Tests the supervisor wrote, each with the paragraph it enforces
Commits 1, 2 and 4 are all tests by the supervisor. The `test_bug039_void_path_*` tests carry `enforces: handoff/REFAC-004.md` with R-042 and D-003 in their docstrings. The mutants files are under run/supervisor/ (gitignored), named above.

## Expected bookkeeping files in the diff
docs/HARDENING.md, docs/INVENTORY.md, docs/PROJECT_STATUS.md, docs/archive/STATUS_HISTORY.md, project.json, handoff/REFAC-004.md, handoff/REFAC-004-r1-report.md, bridge/cursor-bridge/MANIFEST.json, and run/review/ (this file, the diff, the assumptions file).
