# SCOPE for TASK-078 (Review B, round 1)

TASK-078 is stage P3's text increment, written by the supervisor; there is no brief and no builder (docs/BUILD_PLAN.md, the heading TASK-078: "Author: supervisor (text; no wording test)"). It writes the sentences stage P3's merged programs need, in the bridge's governance texts, and retires the passages the design's rule budget names. Branch task-078 from main 96972bc (TASK-072's merge, PR #195). This is the review guard's first round for TASK-078 (snapshot TASK-078-r1); the round is below every ceiling.

REVIEW-TASK-078-r1.diff is `git diff origin/main..HEAD` against main 96972bc, the review files excepted. Read the commit messages (git log origin/main..HEAD, the full bodies): cae3029 widens the plan's Scope; dc27025 is the text, with its word counts per file, the sentences added and the passages retired; e06dae8 is round 2 after Review A's REJECT; the records commit flips the rows and writes HARDENING and the status file.

## What the change must satisfy
- docs/BUILD_PLAN.md under the heading TASK-078: Scope, Scope notes (with the widening sentence) and Done when, every item.
- docs/REQUIREMENTS.md rows R-088, R-089, R-090, R-091, R-092, R-095, R-097 and R-098, each row's text clause; the Evidence cells' `text:` entries name a heading that stands in the file named.
- docs/DESIGN.md, Change: the program release: J3, J7, C3, C12, C17/C22, C20/F1, F3, the paragraph on the sentences the program items need, and the rule budget (KP-050's Correction to a pointer, KP-041, the policy's temporary-mutation clause, step 4's ten-minute clause and the nosemgrep word).
- docs/HARDENING.md, every line naming TASK-078: TASK-082's leads 1 and 4, Stage P2's demonstration note on a push-scan hit read at its place, TASK-077's note "For TASK-078 and the install".

## Read the texts against the programs they describe
in-flight.py (its usage and refusals), ROUND_CAUSES in bridge_env.py, mutation-run.py's exit 5, records-migrate.py's `cannot read` reasons and exit 3 messages, inventory-check.py's RUN PARAMETERS empty line, evaluate-reports.py's `security` subcommand (what it reads and what it leaves to the reader: it writes `alerts off` beside a green kind and never reads a project's inventory), review-guard.py's `ready` and `snapshot` (the Round cause: line read from the SCOPE file), conformance-check.py's Weekly scan: reading (row[0]). A sentence that claims more than the program does, or contradicts another instruction text, is a finding.

## The supervisor's rulings
- The Scope widened at the checkpoint for run-parameters.md and secret-sentinel.md (two HARDENING leads) and three kept tests whose pins the change rewrites.
- Pinned sentences kept word for word where a test outside the Scope pins them (step 4's pointer to step 1b; calibration's "three commands"), and in step 8 and the sentinel, the reading of a push-scan hit added as a new sentence after each pinned one.
- tests/test_allowlist.py gains a test of calibration's and the evaluation's commands: in-flight.py allowed; `evaluate-reports.py security` denied by no rule and refused by no guard, with no allow rule (TASK-077's decision; settings.bridge.json outside the Scope).
- Of step 4's two ten-minute clauses, the one HARDENING quotes is retired; the other is accurate and stays.
- D-004's flow to each project's origin remote is the stage close's (the plan's Diagrams: none).

## Evidence
- The rulebook (tests/test_release_s_budgets.py's method): 149,846 words before, 149,453 after; at most 149,746 asked. The digest unchanged (tests/test_session_start.py green).
- trace-check.py --moves on a scratch clone: 12 files, 1,036 passages, 38 excused, RESULT: OK; the pinned mode: 424 passages, 0 dropped, RESULT: OK (run/agent/TASK-078-trace.out, in the commit message).
- The 62 test files that read the edited texts, stripped: 2267 passed, 37 skipped; after round 2, the eight it touched: 330 passed, 20 skipped.
- workflow-check.py OK; MANIFEST regenerated; completion-check.py --mode plan OK (98 built, 2 deferred, 5 planned); inventory-check.py OK; plan-check.py OK.
- Review A: round 1 REJECT (B1, step 1b dropped `alerts off` as a finding, behaviour against R-052), round 2 APPROVE.

## Expected in the diff
docs/BUILD_PLAN.md (the widening), the twelve bridge texts, MANIFEST.json, docs/TRACE_MOVES.md, tests/test_allowlist.py, tests/test_bug042.py, tests/test_release_t_floor.py, docs/REQUIREMENTS.md, docs/HARDENING.md (TASK-078's section and a bullet under TASK-072's), docs/PROJECT_STATUS.md (as at this pull request's merge), and run/review/ (these files).
