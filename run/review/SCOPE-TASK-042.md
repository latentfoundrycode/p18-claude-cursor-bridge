# SCOPE - TASK-042: the weekly dependency scan in this repository (R-052) (pull request #128)

A second GitHub workflow beside the gate's, plus its structural test. Supervisor-authored by the plan, so there is no builder run and no brief: `cursor-configurator` wrote the workflow from the frozen block of `bridge/agents/cursor-configurator.md` (TASK-041, on main), and the tests came first. Your question: does the workflow do what docs/BUILD_PLAN.md's TASK-042 says, and do the tests hold it there?

The branch's commits, in order:
- 36a2113: the workflow, the tests, tests/test_release_b_ci_floor.py and D-004 as built.
- c286542: the supervisor's tightened assertions after Review A and the audit.
- cfa7872: the records.
- this round's review files, committed last.

## Scope (the plan's, quoted)
.github/workflows/dependency-scan.yml; tests/test_dependency_scan.py; tests/test_release_b_ci_floor.py (`test_r002_workflow_is_the_only_one` widened to the two files; the pin, one-secret and trigger tests still read `tests.yml` alone, the new file's secret-freedom being `tests/test_dependency_scan.py`'s); docs/diagrams/D-004-context-dfd.md (`p_dependency_scan`'s `designed` labels, its element-map row and the note's sentence redrawn as in the tree, `diagram-specialist`'s as-built variant)

## Beyond that list, kept and named
- D-004's two edge labels: `workflow_dispatch` beside the schedule, and `rules` off the scan's edge, since the scan runs no Semgrep; within the Done when's "redrawn as in the tree".
- docs/DESIGN.md's sentence on the job's token, corrected in the records (the audit's A4): the automatic token is used only by the checkout's own fetch and removed before the next step.

## Done when (the plan's, in short; read docs/BUILD_PLAN.md, "### TASK-042" for the whole)
The file equals the frozen block but for its one fill-in, `--lockfile=requirements.txt:requirements.lock`; the test asserts the frozen part, the lockfile list, the two pins, the permissions, the two triggers, `persist-credentials: false`, the exit handling and no secret; the test is red on the checkpoint and green after; `test_r002_workflow_is_the_only_one` rewritten to the two files and red on the checkpoint; D-004 redrawn, `diagram-check.py --mode design` OK; the pull request's own CI green.

The new workflow runs on no pull-request event, so CI does not exercise it here, and that is by design: GitHub runs a schedule or a dispatch only for a file on the default branch.

Later increments are later work, not this diff's defect: TASK-044 the `workflow_dispatch` run that is this workflow's proof, the tests that name D-002 and D-003 and the index's Enforced-by cells, so `diagram-check.py --mode code`'s 12 TESTS lines are expected here (it printed 13 before this diff; D-004 now has its enforcing test); R-052 stays planned in docs/REQUIREMENTS.md until TASK-044, so the register is rightly unchanged by this diff; TASK-045 the stamp. The evaluation's reading of this workflow's runs is TASK-041's text, on main; a lead on it is in docs/HARDENING.md.

## The project's threat model, as docs/INVENTORY.md's Decisions record it for what the diff changes
Row 159's weekly scan: `contents: read`, no token handed to a step, no secret, so a run has nothing to leak; pull requests from forks get no secrets. The fork-listing lead is the one a reviewer could reach and it is recorded, not taken (below). You may disagree with that ruling.

## The tests the supervisor wrote first
tests/test_dependency_scan.py, 11 tests, each docstring naming the paragraph it enforces (R-052, D-004, KP-005, rule 14, docs/BUILD_PLAN.md TASK-042), all prefixed `test_r052_`: `the_file_is_the_frozen_block_with_its_fill_in`, `the_lockfile_list_is_the_floors`, `the_pins_are_the_floors`, `every_action_is_pinned_by_commit`, `contents_read_and_nothing_else`, `the_two_triggers_and_no_other`, `the_checkout_keeps_no_credentials`, `no_secret_and_no_token`, `a_finding_fails_the_run_and_every_exit_is_named`, `the_scanner_is_checked_before_it_runs_and_cannot_be_skipped`; and `no_patterns_catch_their_forms`, a precondition that passes on the checkpoint too and is outside `new_tests`. tests/test_release_b_ci_floor.py: `test_r002_workflow_is_the_only_one` rewritten to the two files (enforces the same requirement as it did, R-002, widened by R-052). This is a test edit that widens an allowed set by one named file: check it against the anti-gaming list.

The mutants file is run/supervisor/TASK-042-mutants.json (gitignored, not in the diff), written by run/supervisor/task042_mutants.py, which asserts each mutant's `old` text occurs once in its file: 35 mutants, none alike, each a named weakening of the workflow, the frozen block or the floor's pins. No mutant can exercise `test_r002_workflow_is_the_only_one`'s third-file direction, a mutant being unable to add a file; Review A and the audit each ran it by hand and it fails.

## Bookkeeping and records expected in the diff
- docs/PROJECT_STATUS.md as at this pull request's merge (ISS-009), the line it replaces archived in docs/archive/STATUS_HISTORY.md.
- docs/INVENTORY.md: a Features row, "The weekly dependency scan".
- docs/HARDENING.md: TASK-042's section, the findings not taken.
- docs/DESIGN.md: the one sentence named above.
- docs/diagrams/D-004-context-dfd.md, drawn as built by the diagram specialist.
- run/review/: this round's files.

## Before this round
- New tests against the checkpoint a1420ba (`mutation-run.py --checkpoint`, run/agent/TASK-042-checkpoint2.out, not in the diff): exit 0, the 11 listed tests failing, none passing, none not run, re-run after c286542.
- Review A: APPROVE, 0 blocking, 0 should fix. Security audit: PASS, advisories only, none of the five. The asset's SHA-256 was checked against the release's own `osv-scanner_SHA256SUMS` and the checkout's commit against its `v5` tag (the audit).
- Their advisories are in docs/HARDENING.md, TASK-042: the evaluation's `gh run list` reads any event and branch, a text item for the next edit of evaluate-reports.md (A1); the second workflow's one guard is a test a diff could delete, both changes standing in one diff for the reviewers (A3); `osv-scanner.toml`'s content is read by no test (A5). A2, narrow assertions, is taken in c286542. Held by the frozen-block equality alone, as the floor's own pin test holds the floor: another `--config`, `--allow-no-lockfiles`, the binary downloaded again after its check, a `container:` at a mutable tag, `set +e` before the check.
- Assumed, not verified offline (Review A): OSV-Scanner exits non-zero when its advisory query fails, not only on a finding. Recorded.
- Mutation run on the code as it stands (run/agent/TASK-042-mutation.out, not in the diff): "counts: run=35 cached=0 killed=35 survived=0 not applied=0 error=0 expected survive=0", exit 0. Cuts: none. Estimate: at most 36 pytest processes, no test launching a process.
- P7's suite, on cfa7872 (run/agent/TASK-042-suite.out, not in the diff): "3459 passed, 41 skipped in 1606.01s", exit 0; no skip names tests/test_dependency_scan.py.
- diagram-check --mode design: OK. --mode code: the 12 expected TESTS lines, no IMPORT or SCHEMA failure. inventory-check: OK. plan-check: OK. windowless-check: 0 FAIL. No workflow text under bridge/ changed, so the traceability check has nothing new to read.

## The round
The guard's count is 0 before this snapshot and 1 once it opens, so this is Review B's first read. The launcher's count of builder rounds is 0, there being no builder. This round is below the ceiling; grade every finding by the five blocking classes all the same (behaviour against the brief or the register, security, data integrity, a defeated safety mechanism the increment relies on, a failing test), and say for each which class it is or that it is none.

Never run review-guard.py snapshot, verify or premerge in this Workspace itself.
