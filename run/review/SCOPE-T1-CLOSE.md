# SCOPE - T1-CLOSE, round 1 (stage T1's close records, release T)

This is a records pull request (PR #124, "Records: stage T1's close (R-042 R-047 R-050)"), below the ceiling, round 1. The supervisor wrote everything; no builder ran, so there is no brief and no builder assumption (run/review/ASSUMPTIONS-T1-CLOSE-r1.md says none). The diff is run/review/REVIEW-T1-CLOSE-r1.diff (`git diff origin/main...HEAD` before these review files).

## What it is
Stage T1 of release T closed on 2026-11-02. Its stage review ran two rounds: round 1 rejected and was fixed by BUG-040 (PR #123); round 2 (snapshot STAGE-T1-r2) had Review A approving in its three parts and Review B rejecting on one finding, which the supervisor denied on the record (docs/HARDENING.md, "Stage T1's review, round 2"). This pull request records that round, the stage's live demonstration and the reflection items, and takes Review A's two records Should fix items and the tests part's C4.

## The commits
- a13781d, a supervisor test: tests/test_bug040.py::test_bug040_b1_the_lift_line_reads_as_the_behaviour_class. Step 8 (bridge/cursor-bridge/workflow/phases/delegation-loop/merge.md) holds the overtaken re-review's class line; bridge_env.read_blocking_class_line, the guard's reader, reads it as the class `behaviour`. It enforces R-042 (the ceiling's lifts) and R-045 (T17). It characterizes behaviour main already has, so it passes on main by design; it fails if the line drifts from the reader's grammar or the class leaves the five.
- 892f382, records only: docs/HARDENING.md (three sections: the round, the demonstration, least confident), docs/REQUIREMENTS.md (R-042's, R-047's and R-050's Evidence name BUG-040's tests), docs/INVENTORY.md (the build-phase row describes merge.md's mechanics, R-045, R-046, and settings.bridge.json's three allow rules), docs/PROJECT_STATUS.md as at this pull request's merge (ISS-009) with docs/archive/STATUS_HISTORY.md's moved-out block, project.json's stage.
- The commit after it, Review A's fixes: HARDENING's quotation of R-050's note and its description of Review B's reading; the status file's Next naming TASK-045 for the stamp.

## Expected in the diff
The six records files, tests/test_bug040.py, and nothing else. Outside git and not in the diff: the Documents files (ISS-024, FB-071 to FB-074, the Project Summary).

## Owner decisions in force
- Native model profile (docs/RUN_PARAMETERS.md, docs/ROSTER.json): builder composer-2.5, Review A claude-opus-5-5, Review B grok-4.7-medium, until 2026-11-16 UTC.
- The releases after T and their order, E and F unproven until a practical project, release G's key: docs/INVENTORY.md, Decisions, the three rows of 2026-11-02. They are the owner's words recorded, not this review's to judge; the status file's Next restores the order.
- `--strip` and BUG-039's rule apply only from release T's install (P10); D2's part bounds and the stage-review tag are applied by hand until then.

## What to check
1. Each record says what happened, as the run's outputs show (run/agent/demo-t1-suite.out, run/agent/demo-t1-0nn-checkpoint.out, run/agent/T1-CLOSE-suite.out; `trace-check.py`, `diagram-check.py`, `inventory-check.py`, `completion-check.py --mode plan` read live).
2. The split decision in HARDENING rests on the register's own text: R-050's row in docs/REQUIREMENTS.md and decide.md's and merge.md's class-line sentences.
3. Every test the Evidence cells name exists; the inventory row matches merge.md and settings.bridge.json.
4. The status file as at the merge, within 12,000 characters, and the moved-out block word for word.
5. The new test is sound and not vacuous.
6. No key, computer path or account name in a public file.

Design for later stages is not this diff's defect. Write no file anywhere in the checkout; put any scratch file or test cache in the system temporary folder.
